#!/usr/bin/env python3
"""Mide en un diff lo que CLAUDE.md §6 pone en números.

Uso: chequeo-6.py <BASE> <SHA>           lo que cambió entre los dos
     chequeo-6.py --casos <BASE> <SHA>   los casos nuevos de CASOS de más de 80 líneas

La Dev pega la salida en el informe; la PM corre lo mismo. Imprime avisos y
sale 0: lo que no es un número (un caso por causa, un chequeo en un solo
lugar, el porqué de un comentario) sigue siendo a ojo.
- Una línea movida (su texto también se quitó en el diff) no cuenta como nueva.
- Un caso mide su cuerpo más lo de arriba que sólo él usa (constantes, ayudas).
  El tope de 80 es para casos nuevos; uno ya existente que se toca sólo se lista.
- El grep de historia es el de CLAUDE.md del checkout, no el del SHA.
- Lo que crece dentro de una función anidada cuenta para esa, no para la que la contiene.
- JS y TS se leen con typescript (chequeo-6-js.mjs): el del proyecto, o uno
  global por NODE_PATH.
"""
import ast
import bisect
import functools
import json
import re
import subprocess
import sys
import warnings
from pathlib import Path

# --- Configuración del proyecto (la completa la PM al instalar) ---
PRODUCTO = ("proyecto_maria/",)  # las del grep de «Sin historia» en CLAUDE.md §6
ARNES = ("scripts/testing/", "tests/")  # casos, ayudas de prueba y sabotajes
CASOS = ""                            # los casos son pytest, no JS/TS
FUNCION_CASO = "runCase"              # sin uso mientras CASOS esté vacío
SABOTAJES = "scripts/testing/sabotaje_*"  # guiones de sabotaje propios
# ------------------------------------------------------------------
CODIGO = re.compile(r"\.(py|ts|tsx|js|jsx|mjs)$")
NUEVA, LARGA, ARCHIVO, CASO, NETO = 60, 150, 800, 80, 20
ESPERA_FIJA = re.compile(r"waitForTimeout\(|\bsleep\(|setTimeout\(\s*(r|resolve)\s*,")
COMENTARIO = re.compile(r"^\s*(#(?!!)|//|/\*|\*)")
MARCAS = re.compile(r"^\s*(#+|//+|/\*+|\*/|\*|\"\"\"|''')|(\*/|\"\"\"|''')\s*$")
AYUDANTE = Path(__file__).with_name("chequeo-6-js.mjs")
avisos = []
warnings.filterwarnings("ignore", category=SyntaxWarning)  # escapes inválidos en código viejo del arnés


def git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout


@functools.lru_cache(maxsize=None)
def mostrar(sha: str, ruta: str) -> str:
    return git("show", f"{sha}:{ruta}")


def avisar(texto: str) -> None:
    avisos.append(texto)
    print(f"  AVISO {texto}")


def diff(base: str, sha: str) -> dict:
    """Por archivo: su ruta en la base (None si es nuevo), líneas agregadas {número: texto} y textos quitados."""
    archivos, actual, cabecera, viejo = {}, None, False, None
    salida = git("diff", "-U0", "--no-color", base, sha, "--", *(p.rstrip("/") for p in PRODUCTO + ARNES))
    for l in salida.splitlines():
        if l.startswith("diff --git"):
            actual, cabecera = None, True
        elif cabecera and l.startswith("--- "):
            viejo = None if l == "--- /dev/null" else l[6:]
        elif cabecera and l.startswith("+++ "):
            actual = None if l == "+++ /dev/null" else l[6:]
            if actual:
                archivos[actual] = {"viejo": viejo, "agregadas": {}, "quitadas": set()}
        elif actual and l.startswith("@@"):
            cabecera, n = False, int(re.match(r"@@ -\S+ \+(\d+)", l)[1])
        elif actual and not cabecera and l[:1] == "+":
            archivos[actual]["agregadas"][n] = l[1:]
            n += 1
        elif actual and not cabecera and l[:1] == "-":
            archivos[actual]["quitadas"].add(l[1:].strip())
    return archivos


def movida(textos: list[str], quitadas: set) -> bool:
    """Casi todas sus líneas con contenido también se quitaron: se movió, no se escribió."""
    llenas = [t.strip() for t in textos if len(t.strip()) > 3]
    return bool(llenas) and sum(t in quitadas for t in llenas) >= 0.8 * len(llenas)


def corridas(numeros):
    grupo = []
    for n in numeros:
        if grupo and n != grupo[-1] + 1:
            yield grupo
            grupo = []
        grupo.append(n)
    if grupo:
        yield grupo


def numeros(base: str, sha: str, rutas: tuple) -> tuple[int, int]:
    s = git("diff", "--shortstat", base, sha, "--", *(p.rstrip("/") for p in rutas))
    mas, menos = re.search(r"(\d+) insertion", s), re.search(r"(\d+) deletion", s)
    return int(mas[1]) if mas else 0, int(menos[1]) if menos else 0


def resumen(base: str, sha: str) -> None:
    mas, menos = numeros(base, sha, PRODUCTO)
    print(f"producto +{mas}/−{menos}")
    if mas - menos > NETO:
        avisar(f"producto suma {mas - menos} líneas netas: el informe dice por qué (§6: más de {NETO})")
    mas, menos = numeros(base, sha, ARNES)
    print(f"arnés +{mas}/−{menos}")


def historia(cambios: dict, quitadas: set) -> None:
    reglas = Path(git("rev-parse", "--show-toplevel").strip(), "CLAUDE.md").read_text()
    # El primer grep -E después de «Sin historia», aunque el punto ocupe varias líneas.
    regla = re.search(r"grep -E '([^'\n]+)'", reglas.partition("Sin historia")[2])
    if not regla:
        avisar("no encontré el grep de «Sin historia» en CLAUDE.md")
        return
    nuevas = [(r, n, t) for r, d in cambios.items() if r.startswith(PRODUCTO)
              for n, t in d["agregadas"].items() if t.strip() not in quitadas]
    hallado = subprocess.run(["grep", "-nE", regla[1]], input="".join(t + "\n" for _, _, t in nuevas),
                             capture_output=True, text=True).stdout if nuevas else ""
    print("historia (grep de §6, sin líneas movidas):" + ("" if hallado else " vacío"))
    for h in hallado.splitlines():
        r, n, t = nuevas[int(h.split(":", 1)[0]) - 1]
        avisar(f"historia en {r}:{n}: {t.strip()[:100]}")


def funciones_py(sha: str, ruta: str) -> tuple[list[dict], list[tuple[int, int]]]:
    """Funciones con nombre calificado, y los tramos de cada docstring."""
    funcs, docs = [], []

    def visitar(nodo, nombres):
        cuerpo = getattr(nodo, "body", None)
        if isinstance(cuerpo, list) and cuerpo and isinstance(cuerpo[0], ast.Expr) \
                and isinstance(getattr(cuerpo[0], "value", None), ast.Constant) and isinstance(cuerpo[0].value.value, str):
            docs.append((cuerpo[0].lineno, cuerpo[0].end_lineno))
        for hijo in ast.iter_child_nodes(nodo):
            propios = nombres
            if isinstance(hijo, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                propios = [*nombres, hijo.name]
                if not isinstance(hijo, ast.ClassDef):
                    funcs.append({"nombre": ".".join(propios), "desde": hijo.lineno, "hasta": hijo.end_lineno})
            visitar(hijo, propios)

    visitar(ast.parse(mostrar(sha, ruta)), [])
    return funcs, docs


def medir_js(sha: str, rutas: list[str]) -> dict:
    if not rutas:
        return {}
    r = subprocess.run(["node", str(AYUDANTE), sha, CASOS, FUNCION_CASO, *rutas], capture_output=True, text=True)
    if r.returncode:
        lineas = r.stderr.strip().splitlines() or ["sin salida"]
        motivo = next((l for l in lineas if "Error" in l or "Cannot find" in l), lineas[-1]).strip()[:120]
        avisar(f"no medí JS/TS en {sha} ({motivo}); hace falta typescript: el del proyecto, o uno global por NODE_PATH")
        return {}
    return json.loads(r.stdout)


def largos(funcs: list[dict]) -> dict:
    """Largo de cada función por nombre, en orden de aparición, para emparejarla con la base."""
    por = {}
    for f in funcs:
        por.setdefault(f["nombre"], []).append(f["hasta"] - f["desde"] + 1)
    return por


def padres(funcs: list[dict]) -> list:
    """Índice de la función que contiene directamente a cada una, o None."""
    out, abiertas = [None] * len(funcs), []
    for i in sorted(range(len(funcs)), key=lambda i: (funcs[i]["desde"], -funcs[i]["hasta"])):
        while abiertas and funcs[abiertas[-1]]["hasta"] < funcs[i]["desde"]:
            abiertas.pop()
        out[i] = abiertas[-1] if abiertas else None
        abiertas.append(i)
    return out


def revisar_funciones(ruta: str, ahora: list[dict], antes: dict, agregadas: dict, quitadas: set) -> None:
    """Una función crece por lo propio: lo que creció adentro de otra anidada es de esa otra."""
    vistos, crece, previos = {}, [0] * len(ahora), [None] * len(ahora)
    for i, f in enumerate(ahora):
        largo, tramo = f["hasta"] - f["desde"] + 1, range(f["desde"], f["hasta"] + 1)
        k = vistos[f["nombre"]] = vistos.get(f["nombre"], -1) + 1
        previo = antes.get(f["nombre"], [])[k:k + 1]
        if previo:
            previos[i], crece[i] = previo[0], largo - previo[0]
        elif sum(n in agregadas for n in tramo) >= 0.8 * largo:
            crece[i] = largo
            if largo > NUEVA and not movida([agregadas[n] for n in tramo if n in agregadas], quitadas):
                avisar(f"función nueva de {largo} líneas: {ruta}:{f['desde']} {f['nombre']} (§6: ~{NUEVA})")
    propio = crece[:]
    for i, p in enumerate(padres(ahora)):
        if p is not None:
            propio[p] -= crece[i]
    for i, f in enumerate(ahora):
        largo = f["hasta"] - f["desde"] + 1
        if previos[i] is not None and largo > LARGA and propio[i] > 0:
            avisar(f"creció una función de más de {LARGA}: {ruta}:{f['desde']} {f['nombre']} "
                   f"{previos[i]} → {largo}, {propio[i]} en su propio cuerpo (§6: lo nuevo va aparte)")


def revisar_comentarios(ruta: str, agregadas: dict, quitadas: set, docs: list) -> None:
    notas = [n for n in sorted(agregadas) if COMENTARIO.match(agregadas[n])]
    bloques = list(corridas(notas)) + [list(range(a, b + 1)) for a, b in docs
                                       if all(n in agregadas for n in range(a, b + 1))]
    for g in bloques:
        textos = [agregadas[n] for n in g]
        con_texto = sum(bool(MARCAS.sub("", t).strip()) for t in textos)
        if con_texto >= 3 and not movida(textos, quitadas):
            avisar(f"comentario nuevo de {con_texto} líneas: {ruta}:{g[0]} (§6: una o dos)")


def largo_caso(c: dict) -> int:
    return sum(b - a + 1 for a, b in [c["cuerpo"], *c["propias"]])


def detalle(c: dict) -> str:
    propias = largo_caso(c) - (c["cuerpo"][1] - c["cuerpo"][0] + 1)
    return f"cuerpo {largo_caso(c) - propias}" + (f" + propias {propias}" if propias else "")


def revisar_casos(casos: list[dict], previos: list[dict], agregadas: dict, quitadas: set) -> None:
    numeros_, antes = sorted(agregadas), {c["n"]: largo_caso(c) for c in previos}

    def tocado(a, b):
        i = bisect.bisect_left(numeros_, a)
        return i < len(numeros_) and numeros_[i] <= b

    tocados = [c for c in casos if any(tocado(a, b) for a, b in [c["cuerpo"], *c["propias"]])]
    nuevos = [c for c in tocados if c["n"] not in antes]
    print(f"casos nuevos de {Path(CASOS).name}: " + (", ".join(f"{c['n']} ({largo_caso(c)})" for c in nuevos) or "ninguno"))
    print("casos ya existentes tocados: " + (", ".join(
        f"{c['n']} ({antes[c['n']]} → {largo_caso(c)})" for c in tocados if c["n"] in antes) or "ninguno"))
    for c in nuevos:
        if largo_caso(c) > CASO:
            avisar(f"caso nuevo {c['n']}: {largo_caso(c)} líneas ({detalle(c)}; §6: ~{CASO})")
    for n in numeros_:
        t = agregadas[n]
        if ESPERA_FIJA.search(t) and t.strip() not in quitadas:
            avisar(f"¿espera fija nueva? {CASOS}:{n}: {t.strip()[:100]}")


def revisar_codigo(base: str, sha: str, cambios: dict, quitadas: set) -> None:
    codigo = {r: d for r, d in cambios.items() if CODIGO.search(r)}
    js = [r for r in codigo if not r.endswith(".py")]
    js_ahora = medir_js(sha, js)
    js_antes = medir_js(base, [codigo[r]["viejo"] for r in js if codigo[r]["viejo"]])
    print("archivos de producto:")
    for ruta, d in codigo.items():
        antes, ahora = (len(mostrar(base, d["viejo"]).splitlines()) if d["viejo"] else 0), len(mostrar(sha, ruta).splitlines())
        if ruta.startswith(PRODUCTO):
            print(f"  {ruta}: " + (f"{antes} → {ahora}" if d["viejo"] else f"nuevo, {ahora}"))
        if not d["viejo"] and ahora > ARCHIVO:
            avisar(f"archivo nuevo de {ahora} líneas: {ruta} (§6: ~{ARCHIVO})")
        if ruta.endswith(".py"):
            try:
                funcs, docs = funciones_py(sha, ruta)
                previas = largos(funciones_py(base, d["viejo"])[0]) if d["viejo"] else {}
            except SyntaxError as e:
                avisar(f"no pude leer {ruta}: {e}")
                continue
        elif ruta in js_ahora:
            funcs, docs = js_ahora[ruta]["funciones"], []
            previas = largos(js_antes.get(d["viejo"], {}).get("funciones", []))
        else:
            continue
        revisar_funciones(ruta, funcs, previas, d["agregadas"], quitadas)
        if ruta.startswith(PRODUCTO):
            revisar_comentarios(ruta, d["agregadas"], quitadas, docs)
    if CASOS in js_ahora:
        previos = js_antes.get(codigo[CASOS]["viejo"], {}).get("casos", [])
        revisar_casos(js_ahora[CASOS].get("casos", []), previos, codigo[CASOS]["agregadas"], quitadas)


def principal(base: str, sha: str) -> None:
    print(f"chequeo-6 {base}..{sha}: avisos para mirar, no un veredicto")
    cambios = diff(base, sha)
    quitadas = set().union(*(d["quitadas"] for d in cambios.values()))
    resumen(base, sha)
    historia(cambios, quitadas)
    revisar_codigo(base, sha, cambios, quitadas)
    nuevos = git("diff", "--name-only", "--diff-filter=A", base, sha, "--", SABOTAJES).split()
    if nuevos:
        print(f"sabotajes nuevos (§6: sólo donde §3 pide revisión más fuerte): {' '.join(nuevos)}")
    print(f"avisos: {len(avisos)}")


def casos_largos(base: str, sha: str) -> None:
    viejos = {c["n"] for c in medir_js(base, [CASOS]).get(CASOS, {}).get("casos", [])}
    casos = [c for c in medir_js(sha, [CASOS]).get(CASOS, {}).get("casos", []) if c["n"] not in viejos]
    largos_ = sorted((c for c in casos if largo_caso(c) > CASO), key=largo_caso, reverse=True)
    print(f"{CASOS}: {len(casos)} casos nuevos de {base} a {sha}; de más de {CASO} líneas: {len(largos_)}")
    for c in largos_:
        print(f"  caso {c['n']}: {largo_caso(c)} ({detalle(c)})")


def sin_configurar() -> list:
    """Una ruta que no está en el repositorio deja la medición vacía y sin avisos, como si todo estuviera bien."""
    return [p for p in (*PRODUCTO, *ARNES, CASOS) if p and not git("ls-files", "--", p.rstrip("/"))]


if __name__ == "__main__":
    if faltan := sin_configurar():
        sys.exit(f"chequeo-6: no están en el repositorio: {' '.join(faltan)}. Completá la configuración de arriba.")
    if sys.argv[1:2] == ["--casos"] and not CASOS:
        sys.exit("chequeo-6: --casos necesita CASOS en la configuración de arriba.")
    if len(sys.argv) == 4 and sys.argv[1] == "--casos":
        casos_largos(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 3:
        principal(sys.argv[1], sys.argv[2])
    else:
        sys.exit(__doc__)
