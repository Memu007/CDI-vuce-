#!/usr/bin/env python3
"""Cuenta, sin correr ningún guion, las anclas de los sabotajes que ya no están.

uso: python scripts/testing/anclas_perdidas.py [revisión]      (por omisión HEAD)

Lee de esa revisión scripts/testing/sabotaje_*.sh y scripts/testing/sabotajes/*.sh,
sigue cada llamada hasta el reemplazo que la aplica (un heredoc de Python o
`node -e`) y cuenta cuántas veces está el texto viejo en su archivo de esa misma
revisión. Un `for` sobre palabras conocidas se recorre una vuelta por valor, y
un `case`, por la rama de su valor.

Límites: las ramas de un `if` se cuentan todas, también las que piden Postgres;
un `while` y un bucle dentro de una función se recorren una sola vez; dentro de
una función que aplica un cambio no se miran sus `if` ni sus `case`, así que un
ancla que el guion tolera que falte se cuenta como perdida; un ancla que sólo
aparece después de un reemplazo anterior del guion se cuenta como perdida. Lo
que no se puede saber sin ejecutar el guion, y lo que cambia `sed`, sale como
«no medido», con el motivo. Un sabotaje que no reemplaza texto (pisa o borra un
archivo) sólo deja fila, «sin ancla», si pasa por una función del guion. Los
guiones que no son `.sh` no se leen.
"""
import bisect
import fnmatch
import functools
import re
import signal
import subprocess
import sys
from collections import Counter

CORTES = " \t\n;&|()<>"
HEREDOC = re.compile(r"<<(-?)[ \t]*(['\"]?)\\?(\w+)\2")
ESCAPE = re.compile(
    r"\\(?:x([0-9a-fA-F]{1,2})|u([0-9a-fA-F]{1,4})|U([0-9a-fA-F]{1,8})|([0-7]{1,3})|(.))", re.S)
ANSI_C = {"n": "\n", "t": "\t", "\\": "\\", "'": "'", '"': '"', "r": "\r", "e": "\x1b",
          "a": "\a", "b": "\b", "f": "\f", "v": "\v"}
CLAVES = {"if", "then", "else", "elif", "do", "!", "while", "until", "{", "time"}
DECLARAN = {"local", "export", "readonly", "declare"}
BLOQUES = {"for", "while", "until", "select", "case"}
VARIAS = object()  # una expansión que puede dar cualquier cantidad de palabras


class NoMedible(Exception):
    clase = "no medido"


class SinAncla(NoMedible):
    clase = "sin ancla"


class Palabra:
    """Trozos (tipo, dato). Tipos: lit, var (entre comillas), suelta (variable sin
    comillas), pos ($1), arit ($((…))), lista (los elementos de NOMBRE=(…)) y raro."""

    def __init__(self, linea):
        self.linea = linea
        self.partes = []
        self.crudo = ""

    def literal(self, texto):
        if self.partes and self.partes[-1][0] == "lit":
            self.partes[-1] = ("lit", self.partes[-1][1] + texto)
        else:
            self.partes.append(("lit", texto))


class Sentencia:
    def __init__(self, palabras, define=None, pedidos=0, tubo=False, patron=None):
        self.palabras = palabras
        self.define = define  # nombre, si es la cabecera `nombre() {`
        self.patron = patron  # las alternativas, si es el `a|b)` que abre una rama de `case`
        self.pedidos = pedidos  # heredocs abiertos en el renglón hasta esta sentencia
        self.tubo = tubo  # termina en `|`
        self.heredoc = None

    def sin_claves(self):
        palabras = self.palabras
        while palabras and palabras[0].crudo in CLAVES:
            palabras = palabras[1:]
        return palabras

    def orden(self):
        """Las palabras de la orden: sin las claves ni las NOMBRE=valor de adelante."""
        palabras = self.sin_claves()
        while palabras and re.match(r"[A-Za-z_]\w*=", palabras[0].crudo):
            palabras = palabras[1:]
        return palabras


class Lector:
    """Parte un guion de bash en sentencias y palabras, sin ejecutarlo."""

    def __init__(self, texto):
        self.t = texto
        self.i = 0
        self.pendientes = []
        self.inicios = [0] + [m.end() for m in re.finditer("\n", texto)]

    def sentencias(self):
        t, actual, renglon, hondo = self.t, [], [], 0
        while self.i < len(t):
            c = t[self.i]
            if t.startswith("\\\n", self.i):
                self.i += 2
            elif c in " \t":
                self.i += 1
            elif c == "#":
                self.i = self._fin_de_linea()
            elif c in "<>":
                if actual and actual[-1].crudo.isdigit() and t[self.i - 1].isdigit():
                    actual.pop()  # el número pegado a una redirección es su descriptor
                self._redireccion()
            elif c in "\n;&|()":
                define = c == "(" and len(actual) == 1 and re.match(r"\(\s*\)", t[self.i:])
                tubo = c == "|" and not t.startswith("||", self.i)
                self.i += define.end() if define else 2 if c == "|" and not tubo else 1
                if c == ")" and not hondo:
                    # Sin paréntesis abierto cierra un patrón de `case`: no es una orden.
                    while renglon and renglon[-1].tubo:
                        actual = renglon.pop().palabras + actual
                    if [p.crudo for p in actual[:1]] == ["case"]:
                        renglon.append(Sentencia(actual[:3]))
                        actual = actual[3:]
                    renglon.append(Sentencia([], patron=[
                        p.partes[0][1] if [tipo for tipo, _ in p.partes] == ["lit"] else "*"
                        for p in actual]))
                    actual = []
                hondo = max(0, hondo + (c == "(" and not define) - (c == ")"))
                if actual:
                    nombre = actual[0].crudo if define else None
                    renglon.append(Sentencia(actual, nombre, len(self.pendientes), tubo))
                actual = []
                if c == "\n":
                    yield from self._con_sus_heredocs(renglon)
                    renglon = []
            else:
                actual.append(self._palabra())
        yield from renglon + ([Sentencia(actual)] if actual else [])

    def _con_sus_heredocs(self, renglon):
        """Le da cada cuerpo de heredoc a la sentencia del renglón que lo abrió."""
        cuerpos, dados = self._saltar_heredocs(), 0
        for sentencia in renglon:
            if sentencia.pedidos > dados:
                sentencia.heredoc = "".join(cuerpos[dados:dados + 1])
                dados = sentencia.pedidos
        return renglon

    def _fin_de_linea(self):
        fin = self.t.find("\n", self.i)
        return len(self.t) if fin < 0 else fin

    def _redireccion(self):
        m = HEREDOC.match(self.t, self.i)
        if m and not self.t.startswith("<<<", self.i):
            self.pendientes.append((m.group(3), bool(m.group(1))))
            self.i = m.end()
            return
        while self.i < len(self.t) and self.t[self.i] in "<>&":
            self.i += 1
        while self.i < len(self.t) and self.t[self.i] in " \t":
            self.i += 1
        if self.i < len(self.t) and self.t[self.i] not in CORTES:
            self._palabra()

    def _saltar_heredocs(self):
        cuerpos = []
        for marca, con_tabs in self.pendientes:
            desde = self.i
            while self.i < len(self.t):
                fin = self._fin_de_linea()
                renglon = self.t[self.i:fin]
                if (renglon.lstrip("\t") if con_tabs else renglon) == marca:
                    cuerpos.append(self.t[desde:self.i])
                    self.i = min(fin + 1, len(self.t))
                    break
                self.i = min(fin + 1, len(self.t))
        self.pendientes = []
        return cuerpos

    def _palabra(self):
        t, desde = self.t, self.i
        p = Palabra(bisect.bisect_right(self.inicios, desde))
        while self.i < len(t) and t[self.i] not in CORTES:
            c = t[self.i]
            if c == "\\":
                if t[self.i + 1:self.i + 2] != "\n":
                    p.literal(t[self.i + 1:self.i + 2])
                self.i += 2
            elif c == "'":
                fin = t.index("'", self.i + 1)
                p.literal(t[self.i + 1:fin])
                self.i = fin + 1
            elif c == '"':
                self._comillas_dobles(p)
            elif c == "$":
                self._dolar(p, suelto=True)
            elif c == "`":
                self.i = t.index("`", self.i + 1) + 1
                p.partes.append(("raro", "`"))
            elif c == "=" and t.startswith("=(", self.i):
                p.literal("=")
                self.i += 2
                p.partes.append(("lista", self._elementos()))
            else:
                p.literal(c)
                self.i += 1
        p.crudo = t[desde:self.i]
        return p

    def _elementos(self):
        """Las palabras de NOMBRE=( … ), hasta el paréntesis que cierra."""
        elementos = []
        while self.t[self.i] != ")":
            if self.t[self.i] in " \t\n":
                self.i += 1
            elif self.t[self.i] == "#":
                self.i = self._fin_de_linea()
            else:
                elementos.append(self._palabra())
        self.i += 1
        return elementos

    def _comillas_dobles(self, p):
        t = self.t
        self.i += 1
        p.literal("")
        while t[self.i] != '"':
            c = t[self.i]
            if c == "\\" and t[self.i + 1] in '$`"\\\n':
                if t[self.i + 1] != "\n":
                    p.literal(t[self.i + 1])
                self.i += 2
            elif c == "$":
                self._dolar(p, suelto=False)
            elif c == "`":
                self.i = t.index("`", self.i + 1) + 1
                p.partes.append(("raro", "`"))
            else:
                p.literal(c)
                self.i += 1
        self.i += 1

    def _dolar(self, p, suelto):
        t, i = self.t, self.i
        simple = re.compile(r"\$(?:([A-Za-z_]\w*)|([0-9])|([@#*]))").match(t, i)
        if suelto and t.startswith("$'", i):
            self._ansi_c(p)
        elif t.startswith("$((", i):
            fin = t.index("))", i)
            p.partes.append(("arit", t[i + 3:fin]))
            self.i = fin + 2
        elif t.startswith("$(", i):
            self.i = i + 2
            self._fin_de_sustitucion()
            p.partes.append(("raro", "$("))
        elif t.startswith("${", i):
            fin = self._fin_de_llave(i + 2)
            dentro = t[i + 2:fin]
            if re.fullmatch(r"[A-Za-z_]\w*", dentro):
                p.partes.append(("suelta" if suelto else "var", dentro))
            else:
                p.partes.append(("pos" if dentro.isdigit() else "raro", dentro))
            self.i = fin + 1
        elif simple:
            nombre, numero, signo = simple.groups()
            p.partes.append(("suelta" if suelto else "var", nombre) if nombre else
                            ("pos", numero) if numero else ("raro", signo))
            self.i = simple.end()
        else:
            p.literal("$")
            self.i = i + 1

    def _ansi_c(self, p):
        """$'…': los escapes dan bytes, que juntos se leen como UTF-8."""
        t, crudo = self.t, bytearray()
        self.i += 2
        while t[self.i] != "'":
            m = ESCAPE.match(t, self.i)
            hexa, corto, largo, octal, otro = m.groups() if m else [None] * 5
            if hexa or octal:
                crudo.append(int(hexa or octal, 16 if hexa else 8) & 255)
            elif corto or largo:
                crudo += chr(int(corto or largo, 16)).encode()
            else:
                crudo += (ANSI_C.get(otro, "\\" + otro) if m else t[self.i]).encode()
            self.i = m.end() if m else self.i + 1
        self.i += 1
        p.literal(crudo.decode("utf-8", "replace"))

    def _fin_de_llave(self, i):
        t, hondo = self.t, 1
        while True:
            if t[i] == "\\":
                i += 1
            elif t.startswith("${", i):
                hondo += 1
                i += 1
            elif t[i] == "}":
                hondo -= 1
                if not hondo:
                    return i
            i += 1

    def _fin_de_sustitucion(self):
        """Deja self.i después del `)` que cierra un `$(` ya abierto."""
        t, hondo = self.t, 1
        while hondo:
            c = t[self.i]
            if c == "\\":
                self.i += 2
            elif c == "'":
                self.i = t.index("'", self.i + 1) + 1
            elif c == '"':
                self._comillas_dobles(Palabra(0))
            elif c == "<" and HEREDOC.match(t, self.i) and not t.startswith("<<<", self.i):
                self._redireccion()
            elif c == "\n":
                self.i += 1
                self._saltar_heredocs()
            else:
                hondo += (c == "(") - (c == ")")
                self.i += 1


def cuenta(expresion, entorno):
    """El valor de una cuenta de bash con enteros, variables, $#, +, - y *; None si no se sabe."""
    expresion = re.sub(r"\$\(\((.*)\)\)", r"\1", expresion)
    piezas = re.findall(r"\d+|[A-Za-z_]\w*|\$#|[-+*]", expresion)
    if "".join(piezas) != expresion.replace(" ", ""):
        return None
    total, signo, producto = 0, 1, None
    for pieza in piezas + ["+"]:
        if pieza in "+-" and producto is not None:
            total, signo, producto = total + signo * producto, 1 if pieza == "+" else -1, None
        elif pieza in "+-":
            return None
        elif pieza != "*":
            valor = entorno.get("@") if pieza == "$#" else entorno.get(pieza, pieza)
            valor = len(valor) if pieza == "$#" and valor is not None and VARIAS not in valor else valor
            if not re.fullmatch(r"\d+", str(valor)):
                return None
            producto = int(valor) * (1 if producto is None else producto)
    return total


def posicional(entorno, numero):
    argumentos = entorno.get("@")
    if argumentos is None or not numero or VARIAS in argumentos[:numero]:
        return None
    return argumentos[numero - 1] if numero <= len(argumentos) else ""


def lista(dentro, entorno):
    """Lo que dan "$@", "${NOMBRE[@]}" y "${@:desde:cuantos}"; None si no es una lista."""
    argumentos = entorno.get("@")
    if dentro in "@*" and argumentos is not None:
        return list(argumentos)
    corte = re.fullmatch(r"@:([^:]+)(?::(.+))?", dentro)
    if corte and argumentos is not None and VARIAS not in argumentos:
        desde = cuenta(corte.group(1), entorno)
        cuantos = cuenta(corte.group(2), entorno) if corte.group(2) else len(argumentos)
        if desde and cuantos is not None:
            return argumentos[desde - 1:desde - 1 + cuantos]
    nombre = re.fullmatch(r"(\w+)\[@\]", dentro)
    if nombre and isinstance(entorno.get(nombre.group(1)), list):
        return list(entorno[nombre.group(1)])
    return [VARIAS] if corte or nombre or dentro in "@*" else None


def recortar(dentro, entorno):
    """Lo que dan ${NOMBRE%patrón}, %%, # y ##; None si no se conoce el valor."""
    m = re.fullmatch(r"([A-Za-z_]\w*)(##?|%%?)(.*)", dentro, re.S)
    valor = entorno.get(m.group(1)) if m else None
    if not isinstance(valor, str):
        return None
    al_final, el_mas_largo = m.group(2)[0] == "%", len(m.group(2)) == 2
    cortes = range(len(valor) + 1)
    for i in cortes if al_final == el_mas_largo else reversed(cortes):
        if fnmatch.fnmatchcase(valor[i:] if al_final else valor[:i], m.group(3)):
            return valor[:i] if al_final else valor[i:]
    return valor


def cierre(sentencias, desde):
    """El lugar del `done` o `esac` que cierra el bloque abierto justo antes de `desde`."""
    abiertos = 1
    for lugar in range(desde, len(sentencias)):
        s = sentencias[lugar]
        crudos = [p.crudo for p in s.palabras]
        abiertos += sum(c in BLOQUES for c in crudos[:len(crudos) - len(s.sin_claves()) + 1])
        abiertos -= crudos[:1] in (["done"], ["esac"])
        if not abiertos:
            return lugar
    return len(sentencias)


def rama(cuerpo, valor):
    """Las sentencias de un `case` que corren con ese valor; todas si no se conoce."""
    if not isinstance(valor, str):
        return cuerpo
    elegida, hondo, corre = [], 0, False
    for s in cuerpo:
        if s.patron is not None and not hondo:
            if corre:
                break
            corre = any(fnmatch.fnmatchcase(valor, patron) for patron in s.patron)
        else:
            crudos = [p.crudo for p in s.palabras[:1]]
            hondo += (crudos == ["case"]) - (crudos == ["esac"])
            elegida += [s] * corre
    return elegida


def expandir(palabra, entorno):
    """Las palabras que da una palabra del guion; None es un valor que no se conoce."""
    sola = [parte for parte in palabra.partes if parte != ("lit", "")]
    if len(sola) == 1 and sola[0][0] == "raro":
        varias = lista(sola[0][1], entorno)
        if varias is not None:
            return varias
    trozos = []
    for tipo, dato in palabra.partes:
        if tipo in ("var", "suelta"):
            dato = entorno.get(dato)
        elif tipo == "pos":
            dato = posicional(entorno, int(dato))
        elif tipo == "arit":
            dato = cuenta(dato, entorno)
            dato = dato if dato is None else str(dato)
        elif tipo == "raro":
            tipo, dato = "lit", recortar(dato, entorno)
        if tipo in ("raro", "lista") or not isinstance(dato, str):
            return [None] if '"' in palabra.crudo or "'" in palabra.crudo else [VARIAS]
        trozos.append(dato)
    if len(palabra.partes) == 1 and palabra.partes[0][0] == "suelta":
        return trozos[0].split()
    return ["".join(trozos)]


def expandir_todas(palabras, entorno):
    return [valor for palabra in palabras for valor in expandir(palabra, entorno)]


def asignar(palabras, entorno):
    """Guarda las NOMBRE=valor con que empieza la sentencia y devuelve las palabras que siguen."""
    if palabras and palabras[0].crudo in DECLARAN:
        palabras = [palabra for palabra in palabras[1:] if not palabra.crudo.startswith("-")]
    for lugar, palabra in enumerate(palabras):
        tipo, dato = palabra.partes[0] if palabra.partes else ("", "")
        m = re.match(r"([A-Za-z_]\w*)=", dato) if tipo == "lit" else None
        if not m:
            return palabras[lugar:]
        resto = Palabra(palabra.linea)
        resto.crudo = palabra.crudo
        resto.partes = [("lit", dato[m.end():])] + palabra.partes[1:]
        if palabra.partes[1:2] and palabra.partes[1][0] == "lista":
            entorno[m.group(1)] = expandir_todas(palabra.partes[1][1], entorno)
        else:
            entorno[m.group(1)] = expandir(resto, entorno)[0]
    return []


def recibido(partes, locales):
    """Si alguno de los trozos sale de lo que la función recibe cuando la llaman."""
    for tipo, dato in partes:
        if tipo == "lista":
            if any(recibido(palabra.partes, locales) for palabra in dato):
                return True
        elif tipo == "pos" or tipo in ("var", "suelta") and dato in locales:
            return True
        elif tipo == "raro" and (
                dato in ("@", "*") or dato.startswith("@:") or dato.split("[")[0] in locales):
            return True
    return False


UNO = re.compile(
    r"\bp, viejo, nuevo = sys\.argv\[1:4?\]|\[p, viejo, nuevo\] = process\.argv\.slice\(1\)"
    r"|\bp = sys\.argv\[1\].* viejo, nuevo = sys\.argv\[2\], sys\.argv\[3\]"
    r"|\bp = \"[^\"]+\".* viejo, nuevo = sys\.argv\[1\], sys\.argv\[2\]")
PARES = re.compile(
    r"\bp = sys\.argv\[1\].*(pares = sys\.argv\[2:\]|zip\(sys\.argv\[2::2\], sys\.argv\[3::2\]\))"
    r"|\bp, pares = sys\.argv\[1\], sys\.argv\[2:\]|\bp, \*pares = sys\.argv\[1:\]")


def reemplazos(cuerpo, argumentos):
    """Qué hace el programa que reemplaza con lo que recibe: archivo y (viejo, nuevo, veces)."""
    plano = re.sub(r"\s+", " ", cuerpo)
    fijo = re.search(r'\bp = "([^"]+)"', plano)
    if fijo:
        argumentos = [fijo.group(1)] + argumentos
    if VARIAS in argumentos or None in argumentos[:1]:
        raise NoMedible("el archivo o las anclas salen de algo que sólo se sabe al ejecutar")
    archivo, resto = argumentos[0], argumentos[1:]
    if PARES.search(plano):
        return archivo, [(viejo, nuevo, 1) for viejo, nuevo in zip(resto[::2], resto[1::2])]
    if not UNO.search(plano) or len(resto) < 2:
        raise NoMedible("el programa que reemplaza lee sus argumentos de otra forma")
    veces = 2 if "n != 2" in plano else 1
    if "veces = int(sys.argv[4])" in plano and len(resto) > 2:
        if not re.fullmatch(r"\d+", str(resto[2])):
            raise NoMedible("las veces que se espera el ancla no son un número conocido")
        veces = int(resto[2])
    return archivo, [(resto[0], resto[1], veces)]


def programa(sentencia):
    """El texto del programa que la sentencia corre (heredoc de Python o `node -e`) y el
    lugar de su primer argumento entre las palabras de la orden."""
    palabras = sentencia.orden()
    crudos = [palabra.crudo for palabra in palabras]
    if sentencia.heredoc and crudos and re.search(r"PY|python", crudos[0]):
        return sentencia.heredoc, crudos.index("-") + 1 if "-" in crudos else 0
    if crudos[:2] == ["node", "-e"] and len(palabras) > 2 and palabras[2].partes[0][0] == "lit":
        return palabras[2].partes[0][1], 3
    return "", 0


class Guion:
    def __init__(self, ruta, leer):
        self.ruta = ruta
        self.funciones = {}   # nombre -> sentencias del cuerpo
        self.sueltas = []     # las de afuera de las funciones que aplican
        self._cargar(ruta, leer)
        self.aplican = self._las_que_aplican()

    def _cargar(self, ruta, leer):
        texto = leer(ruta)
        if texto is None:
            sys.exit(f"no está {ruta}, que un guion incluye")
        abiertas = []  # [nombre, llaves sin cerrar] de cada función que sigue abierta
        for s in Lector(texto).sentencias():
            crudos = [p.crudo for p in s.palabras]
            define = s.define or (crudos[1] if crudos[:1] == ["function"] and crudos[1:] else None)
            if define:
                abiertas.append([define, crudos.count("{")])
                self.funciones[define] = []
                continue
            if abiertas:
                abiertas[-1][1] += crudos[:len(crudos) - len(s.sin_claves())].count("{")
                abiertas[-1][1] -= crudos[:1] == ["}"]
                if crudos[:1] == ["}"] and abiertas[-1][1] <= 0:
                    abiertas.pop()
                    continue
            abierta = abiertas[-1][0] if abiertas else None
            incluido = crudos[:1] in (["source"], ["."]) and re.search(r"/(_\w+\.sh)\"?$", crudos[-1])
            if incluido:
                self._cargar(ruta.rsplit("/", 1)[0] + "/" + incluido.group(1), leer)
            elif abierta:
                self.funciones[abierta].append(s)
            self.sueltas.append((abierta, s))

    def _aplica(self, nombre, conocidas):
        """Las sentencias de la función que aplican un cambio con lo que ella recibe."""
        locales, aplican = set(), []
        for s in self.funciones[nombre]:
            palabras = s.sin_claves()
            orden = palabras[0].crudo if palabras else ""
            if orden == "local":
                locales |= {p.crudo.split("=")[0] for p in palabras[1:] if recibido(p.partes, locales)}
            elif ".replace(" in programa(s)[0]:
                aplican.append(s)
            elif orden == '"$@"' or orden in conocidas and any(
                    recibido(p.partes, locales) for p in palabras[1:]):
                aplican.append(s)
        return aplican

    def _las_que_aplican(self):
        aplican = {}
        while True:
            nuevas = {n: s for n in self.funciones if n not in aplican and (s := self._aplica(n, aplican))}
            if not nuevas:
                return aplican
            aplican.update(nuevas)

    def _seguir(self, nombre, argumentos, entorno, vueltas=0):
        """De la llamada a la función hasta el reemplazo: archivo y (viejo, nuevo, veces)."""
        if vueltas > 6 or len(self.aplican[nombre]) > 1:
            raise NoMedible(f"«{nombre}» aplica más de un cambio o se llama en círculo")
        propio = dict(entorno) | {"@": argumentos}
        for s in self.funciones[nombre]:
            palabras = asignar(s.sin_claves(), propio)
            orden = palabras[0].crudo if palabras else ""
            if orden == "shift":
                cuantos = cuenta(palabras[1].crudo, propio) if palabras[1:] else 1
                if cuantos is None or VARIAS in propio["@"][:cuantos]:
                    raise NoMedible(f"no se sabe cuántos argumentos saca el shift de «{nombre}»")
                propio["@"] = propio["@"][cuantos:]
            elif s is self.aplican[nombre][0]:
                return self._aplicar(s, expandir_todas(palabras, propio), entorno, vueltas)
        raise NoMedible("no se llegó al reemplazo")

    def _aplicar(self, sentencia, valores, entorno, vueltas):
        cuerpo, desde = programa(sentencia)
        if cuerpo:
            if not desde:
                raise NoMedible("no se sabe dónde empiezan los argumentos del programa que reemplaza")
            return reemplazos(cuerpo, valores[desde:])
        if not isinstance(valores[0], str):
            raise NoMedible("no se sabe qué orden aplica el cambio")
        if valores[0] not in self.aplican:
            raise SinAncla(f"el cambio lo hace «{valores[0]}», que no reemplaza texto")
        return self._seguir(valores[0], valores[1:], entorno, vueltas + 1)

    def llamadas(self):
        """Por cada llamada a una función que aplica: (línea, archivo, cambios) o (línea, NoMedible)."""
        return self._correr([s for dentro_de, s in self.sueltas if dentro_de not in self.aplican], {})

    def _correr(self, sentencias, entorno):
        lugar = 0
        while lugar < len(sentencias):
            palabras = asignar(sentencias[lugar].sin_claves(), entorno)
            orden = palabras[0].crudo if palabras else ""
            lugar += 1
            if orden in ("for", "case"):
                fin = cierre(sentencias, lugar)
                yield from self._bloque(palabras, sentencias[lugar:fin], entorno)
                lugar = fin + 1
            elif orden == "sed" and len([p for p in palabras[1:] if not p.crudo.startswith("-")]) > 1:
                yield palabras[0].linea, NoMedible(
                    "arma el cambio con sed, que busca una expresión regular")
            elif orden in self.aplican:
                try:
                    recibe = expandir_todas(palabras[1:], entorno)
                    yield (palabras[0].linea, *self._seguir(orden, recibe, entorno))
                except NoMedible as motivo:
                    yield palabras[0].linea, motivo

    def _bloque(self, cabecera, cuerpo, entorno):
        """Un `case` corre la rama de su valor; un `for` sobre palabras conocidas, una vuelta por cada una."""
        if cabecera[0].crudo == "case":
            valor = (expandir(cabecera[1], entorno) or [""])[0] if cabecera[1:] else None
            yield from self._correr(rama(cuerpo, valor), entorno)
            return
        valores = expandir_todas(cabecera[3:], entorno)
        if not valores or not all(isinstance(valor, str) for valor in valores):
            valores = [None]
        for valor in valores:
            # Un `for ((…))` no nombra una variable que se pueda seguir.
            entorno.update({palabra.crudo: valor for palabra in cabecera[1:2]})
            yield from self._correr(cuerpo, entorno)


def medir(guion, leer):
    """Una fila por ancla: (guion, línea, archivo, viejo, veces esperadas, veces que está)
    o, si no se pudo medir, (guion, línea, NoMedible)."""
    vistas = set()
    for fila in _filas(guion, leer):
        # Una llamada dentro de un bucle da la misma fila en cada vuelta: se cuenta una vez.
        clave = fila if len(fila) > 3 else (*fila[:2], str(fila[2]))
        if clave not in vistas:
            vistas.add(clave)
            yield fila


def _filas(guion, leer):
    for linea, *resto in guion.llamadas():
        if len(resto) == 1:
            yield guion.ruta, linea, resto[0]
            continue
        archivo, cambios = resto
        texto, a_ciegas = leer(archivo), False
        for viejo, nuevo, veces in cambios:
            if not viejo or a_ciegas:
                yield guion.ruta, linea, NoMedible(
                    "depende de un reemplazo anterior que no se conoce" if a_ciegas
                    else "el ancla queda vacía" if viejo == ""
                    else "el ancla sale de algo que sólo se sabe al ejecutar")
                continue
            hay = -1 if texto is None else texto.count(viejo)
            yield guion.ruta, linea, archivo, viejo, veces, hay
            # El par siguiente de la misma llamada se busca sobre el texto ya cambiado.
            a_ciegas = hay > 0 and nuevo is None
            if hay > 0 and nuevo is not None:
                texto = texto.replace(viejo, nuevo)


CLASES = ["perdida, una línea", "perdida, varias líneas", "otra cantidad", "no medido", "sin ancla",
          "está"]


def clase(fila):
    if len(fila) == 3:
        return fila[2].clase
    viejo, veces, hay = fila[3:]
    if hay > 0:
        return "está" if hay == veces else "otra cantidad"
    return "perdida, una línea" if "\n" not in viejo.strip("\n") else "perdida, varias líneas"


def resumen(revision, guiones, filas):
    por_guion = Counter((fila[0], clase(fila)) for fila in filas)
    total = Counter(clase(fila) for fila in filas)
    sin_medir = sum(1 for fila in filas if len(fila) == 3)
    print(f"revisión {revision}: {len(guiones)} guiones, {len(filas) - sin_medir} anclas medidas"
          f" y {sin_medir} llamadas sin medir")
    for nombre in CLASES:
        con = sum(1 for g in guiones if por_guion[g, nombre])
        print(f"  {nombre:<24}{total[nombre]:>5}   guiones: {con}")
    distintas = {fila[2:4] for fila in filas if clase(fila) == "perdida, una línea"}
    print(f"  perdidas de una línea sin repetir (archivo y texto): {len(distintas)}")
    for motivo, veces in Counter(str(fila[2]) for fila in filas if len(fila) == 3).most_common():
        print(f"  {veces:>5}  {motivo}")
    sin_filas = [g for g in guiones if not any(por_guion[g, nombre] for nombre in CLASES)]
    print(f"  guiones sin ninguna fila: {len(sin_filas)}" + "".join(f"\n    {g}" for g in sin_filas))
    print("\nguion: " + " | ".join(CLASES))
    for g in guiones:
        if any(por_guion[g, nombre] for nombre in CLASES[:-1]):
            print(f"  {g}: " + " | ".join(str(por_guion[g, nombre]) for nombre in CLASES))


def detalle(filas):
    for fila in filas:
        if len(fila) == 3:
            print(f"\n{clase(fila).upper()}  {fila[0]}:{fila[1]}  {fila[2]}")
        elif clase(fila) != "está":
            guion, linea, archivo, viejo, veces, hay = fila
            cuanto = "el archivo no está" if hay < 0 else f"está {hay}, se esperaba {veces}"
            print(f"\n{clase(fila).upper()}  {guion}:{linea}  {archivo}  ({cuanto})\n    {viejo!r}")


def main():
    revision = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    # Con la salida cortada (`| head`) termina callado, sin traza.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    def git(*orden):
        return subprocess.run(("git", *orden), capture_output=True, text=True, encoding="utf-8")

    @functools.lru_cache(maxsize=None)
    def leer(ruta):
        salida = git("show", f"{revision}:{ruta}")
        return salida.stdout if salida.returncode == 0 else None

    listado = git("ls-tree", "--full-tree", "-r", "--name-only", revision, "scripts/testing/")
    if listado.returncode:
        sys.exit(listado.stderr.strip())
    guiones = sorted(n for n in listado.stdout.split("\n") if re.fullmatch(
        r"scripts/testing/(sabotaje_[^/]+|sabotajes/[^_/][^/]*)\.sh", n))
    if not guiones:
        sys.exit(f"no hay guiones de sabotaje en {revision}")
    filas = [fila for ruta in guiones for fila in medir(Guion(ruta, leer), leer)]
    resumen(revision, guiones, filas)
    detalle(filas)


if __name__ == "__main__":
    main()
