"""DESPACHO-1b: leer los productos de un despacho oficializado (2026-10-28).

Sale del texto del PDF del sistema del despachante, sin IA: por renglón (ítem
o subítem), posición SIM, descripción, sufijos de valor, origen, unidad,
cantidad, valor unitario y kilo neto. La forma está en
`docs/pm/DESPACHOS-FORMA.md`.

- Se lee por rótulo, no por posición en la hoja: el rótulo va en una línea y
  su valor debajo, en la misma columna. Otro programa de despachantes puede
  ordenar las columnas de otra manera.
- Lo que no se encuentra queda en `faltantes`; nada se rellena ni se adivina.
- Nunca arma una operación ni un TXT: devuelve los renglones para que la
  persona los revise antes de guardarlos en el catálogo del cliente.
- Un PDF escaneado no tiene texto: se avisa y no se devuelve ningún renglón.

Supuestos (los despachos de muestra no traían subítems con su rótulo):
- Cada subítem empieza con el rótulo «Nº Subitem» y trae su propio valor,
  descripción y sufijos. La posición y el origen son del ítem.
- La unidad, la cantidad y el valor unitario son los de «VALOR MERCADERIA»
  («Unidad», «Cantidad Unidades», «Unitario en Divisa»), en la divisa del FOB.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import json
import logging
import math
import os
import re
import signal
import sys
import threading
import unicodedata
import weakref
from bisect import bisect_left, bisect_right
from pathlib import Path

# Topes de la lectura: cada uno corta antes de gastar, y lo que pasa de uno se
# avisa o rechaza el despacho; nunca se lee a medias sin decirlo.
# Igual que el lector de facturas: pypdf tarda más que lineal con una página
# de contenido enorme (RENDIMIENTO-1b).
_MAX_CONTENIDO_PAGINA = 512 * 1024
_MAX_PAGINAS = 200
# Cada flujo del PDF descomprimido (contenido, fuentes, mapas de caracteres).
# Generoso: una fuente incrustada puede pesar unos MB.
_MAX_FLUJO = 8 * 1024 * 1024
_TOPES = {clave: _MAX_FLUJO for clave in (
    "maximum_declared_stream_length", "array_based_stream_maximum_output_length",
    "zlib_maximum_output_length", "lzw_maximum_output_length",
    "run_length_maximum_output_length", "brotli_maximum_output_length",
    "jbig2_maximum_output_length", "stream_decoding_work_maximum_length")}
# Texto de todas las hojas juntas. Un despacho de 200 hojas tiene menos de 1 MB.
_MAX_TEXTO = 4 * 1024 * 1024
# Una línea de un despacho tiene menos de 300 caracteres y menos de 10 rótulos.
_MAX_LARGO_LINEA = 2000
_MAX_COLUMNAS = 40
# Memoria del proceso que lee el PDF (`leer_despacho_aparte`). Una lectura
# normal usa menos de 100 MB.
_MAX_MEMORIA_HIJO = 256 * 1024 * 1024
_HIJOS_A_LA_VEZ = 2
_SALIDA_DEMASIADO_PESADO = 3
# Tiempo de CPU del proceso que lee, medido entre hoja y hoja. Cada hoja
# cuesta según sus operaciones de texto, no según lo que pesa el PDF: 20 hojas
# que comparten un contenido de 500 KB pesan 50 KB y costaban 23 s. Un
# despacho de 200 hojas llenas cuesta menos de 3 s.
_MAX_CPU_LECTURA = 10.0
# Extraer el texto puede usar esta parte del tope. El resto queda para
# entender lo que se leyó: si extraer se lo lleva entero, se pierden los
# productos de las hojas que sí se leyeron.
_PARTE_PARA_EXTRAER = 0.8

AVISO_SIN_TEXTO = (
    "El PDF no tiene texto que se pueda leer: parece escaneado. Pedí el "
    "despacho en PDF del sistema o cargá los productos a mano."
)
AVISO_NO_ES_DESPACHO = (
    "No encontré ningún ítem («Nº Item»). Revisá que sea el PDF del despacho "
    "oficializado."
)
AVISO_SIN_MEMORIA = (
    "El PDF es demasiado pesado para leerlo. Pedí el despacho en PDF del "
    "sistema o cargá los productos a mano."
)
AVISO_OCUPADO = (
    "Ya estoy leyendo otro despacho tuyo. Esperá a que termine y probá de nuevo."
)

CAMPOS = ("posicion_sim", "descripcion", "sufijos", "origen", "unidad",
          "cantidad", "valor_unitario", "kilo_neto")

# Rótulos que se reconocen en una línea. Los de la carátula y el encabezado de
# hoja están para no confundir su línea de valores con la descripción.
_ROTULOS = (
    # Ítem y subítem
    "Nº Item", "Nº Subitem", "Tipo", "Posición SIM / Código AFIP",
    "NALADISA / GATT", "Lista", "Estado",
    "Total Kg. Neto", "Origen Pais / Provincia", "Pais de Procedencia / Destino",
    "Unidad / Estado", "Cantidad Unidades Estadísticas", "Información Adicional",
    # VALOR MERCADERIA
    "Unitario en Divisa", "Unidad", "Cantidad Unidades",
    "Ajuste a Incluir en Divisa", "Ajuste a Deducir en Divisa",
    # VALOR EN ADUANA
    "FOB Total en Divisa", "FOB Total en Dólar", "Valor en Aduana en Divisa",
    "Valor en Aduana en Dólar",
    # Carátula y encabezado de cada hoja
    "Aduana", "Oficialización", "Año / Ad. / Tipo / NºReg. / DC", "Fojas",
    "Importador / Exportador", "CUIT Nº", "Despachante de Aduana",
    "Agente de Transporte Aduanero", "Vendedor", "Vía",
    "Documento de Transporte", "Identificador Manifiesto",
    "Nombre del Transporte", "Bandera", "Puerto de Embarque", "Fecha Arribo",
    "Marcas y Números", "Embalaje", "Total Bultos", "Peso Bruto", "Depósito",
    "Vto. Embarque", "Plazo", "Motivo / Nº Autorización",
    "Aduana Destino / Salida", "Cond. Venta", "FOB Total", "Divisa",
    "Flete Total", "Seguro Total",
)
_INICIO_ITEM = "Nº Item"
_INICIO_SUBITEM = "Nº Subitem"

# Títulos de sección: cortan la descripción.
_TITULOS = ("DECLARACION DE LA MERCADERIA", "VALOR MERCADERIA",
            "VALOR EN ADUANA", "CONCEPTOS", "LIQUIDACION")
_FIN_DESCRIPCION = ("VALOR MERCADERIA", "VALOR EN ADUANA", "CONCEPTOS",
                    "LIQUIDACION")
# Pie y encabezado de hoja que no son rótulo/valor.
_BASURA_DE_HOJA = ("GENERADO POR DUX", "FIRMA Y SELLO", "SUBREGIMEN")

_SUFIJOS_TITULO = re.compile(r"^SUFIJOS DE VALOR\s*:?\s*(.*)$", re.IGNORECASE)
# AA(ACME) = MARCA · AI(XZ 400 B) = CODIGO · PB00 = Ninguno
_SUFIJO = re.compile(r"^([A-Z]{2})(?:\((.*?)\)|(\d{2}))\s*=\s*(.*?)\s*$")
_NUMERO_AR = re.compile(r"^\d{1,3}(?:\.\d{3})+(?:,\d+)?$|^\d+(?:,\d+)?$")
_POSICION = re.compile(r"^\d{4}\.?\d{2}\.?\d{2}(?:\.?\d{3}[A-Z])?$")
_CARACTER_ROTO = re.compile(r"\w\?\w|�")
_MEDIO_PAR = re.compile("[\ud800-\udfff]")  # no se puede escribir en UTF-8


def _plano(texto: str) -> str:
    """Mayúsculas sin tildes, con el mismo largo que el original: cada
    carácter sigue en su columna."""
    salida = []
    for c in texto:
        base = unicodedata.normalize("NFKD", c)[:1] or c
        salida.append(base if base.isascii() else "?")
    return "".join(salida).upper()


def _patron_rotulo(rotulo: str) -> re.Pattern:
    partes = []
    for c in rotulo:
        if c == " ":
            partes.append(" ")
        elif c.isascii():
            partes.append(re.escape(c.upper()))
        else:
            # Una letra con tilde o «º» puede salir rota, como otra o no salir.
            partes.append(".?")
    return re.compile(r"(?<![A-Z0-9])" + "".join(partes) + r"(?![A-Z0-9])")


# Los largos primero: «Unidad / Estado» antes que «Unidad».
_PATRONES = sorted(((r, _patron_rotulo(r)) for r in _ROTULOS),
                   key=lambda par: -len(par[0]))


class _NoEsDespacho(Exception):
    """El texto pasa de un tope: no se lee y se avisa por qué."""


def _rotulos_de_linea(linea: str) -> list[tuple[int, str]] | None:
    """Los rótulos de la línea, con su columna, de izquierda a derecha. None si
    la línea no es de rótulos: tiene que estar hecha sólo de rótulos (así una
    descripción que dice «TIPO» o «UNIDAD» sigue siendo descripción) y tener
    dos o más, o abrir un ítem o un subítem."""
    plano = _plano(linea)
    encontrados = []
    for rotulo, patron in _PATRONES:
        # Se tapan todos los de este rótulo de una vez: tapar de a uno
        # rearmaba la línea por cada uno (cuadrático con miles de rótulos).
        # Dos del mismo rótulo no pueden estar pegados (el patrón lo impide),
        # así que da lo mismo.
        cortes = [(m.start(), m.end()) for m in patron.finditer(plano)]
        if not cortes:
            continue
        partes, desde = [], 0
        for inicio, fin in cortes:
            encontrados.append((inicio, fin, rotulo))
            partes += [plano[desde:inicio], "\0" * (fin - inicio)]
            desde = fin
        plano = "".join(partes) + plano[desde:]
    if not encontrados or re.search(r"[A-Z0-9]", plano):
        return None
    if len(encontrados) > _MAX_COLUMNAS:
        raise _NoEsDespacho(f"Una línea tiene más de {_MAX_COLUMNAS} rótulos: no parece un despacho.")
    encontrados.sort()
    nombres = {r for _, _, r in encontrados}
    if len(encontrados) < 2 and not nombres & {_INICIO_ITEM, _INICIO_SUBITEM}:
        return None
    # «Divisa» se repite: se nombra por el rótulo que tiene a la izquierda.
    columnas = []
    for i, (inicio, _, rotulo) in enumerate(encontrados):
        if rotulo == "Divisa" and i > 0:
            rotulo = "Divisa " + encontrados[i - 1][2]
        columnas.append((inicio, rotulo))
    return columnas


def _valores_por_columna(linea: str, columnas: list[tuple[int, str]]) -> dict[str, str]:
    """Reparte la línea de valores entre los rótulos de arriba según la columna
    en la que empieza cada valor. Los valores se separan por dos o más
    espacios; uno que pisa la columna siguiente se corta donde ella empieza,
    si ahí hay un espacio."""
    # Las columnas vienen ordenadas: se buscan con bisect y no recorriéndolas
    # todas por cada valor (con miles de rótulos, eso trababa la lectura).
    inicios = [c for c, _ in columnas]
    trozos = []
    for m in re.finditer(r"\S+(?: \S+)*", linea):
        a, b = m.start(), m.end()
        for col in inicios[bisect_right(inicios, a + 1):bisect_left(inicios, b)]:
            if a + 1 < col and linea[col - 1] == " ":
                trozos.append((a, linea[a:col].strip()))
                a = col
        trozos.append((a, linea[a:b].strip()))
    valores: dict[str, str] = {}
    for inicio, texto in trozos:
        if not texto:
            continue
        # La columna es la del último rótulo que empieza a la izquierda (con
        # dos de margen: un número alineado a la derecha puede asomar).
        k = bisect_right(inicios, inicio + 2) - 1
        elegida = columnas[max(k, 0)][1]
        valores[elegida] = (valores[elegida] + " " + texto) if elegida in valores else texto
    return valores


def numero_ar(texto) -> float | None:
    """`1.234,56` → 1234.56. None si no tiene esa forma: no se adivina si un
    punto es de miles o decimal."""
    t = str(texto or "").strip()
    if not _NUMERO_AR.match(t):
        return None
    return float(t.replace(".", "").replace(",", "."))


def origen_iso2(texto) -> str | None:
    """«310», «310 CHINA», «CHINA» o «CN» → «CN». None si no se reconoce o si
    el código y el nombre dicen países distintos."""
    from proyecto_maria.core.maria_generator import _codigo_de_la_tabla
    from proyecto_maria.pdf_extractor import _iso2_por_codigo_maria, _origen_desde_factura

    t = re.sub(r"\s+", " ", str(texto or "")).strip(" -/")
    if not t:
        return None
    m = re.match(r"^(\d{3})\b[\s\-/]*(.*)$", t)
    if m:
        codigo, nombre = m.group(1), m.group(2).strip()
        por_codigo = (_iso2_por_codigo_maria().get(int(codigo))
                      if _codigo_de_la_tabla(codigo) else None)
        por_nombre = _origen_desde_factura(nombre) if nombre else None
        if por_codigo and por_nombre and por_codigo != por_nombre:
            return None
        return por_codigo or por_nombre or None
    return _origen_desde_factura(t) or None


def parsear_sufijo(linea: str) -> dict | None:
    m = _SUFIJO.match(linea.strip())
    if not m:
        return None
    codigo, libre, lista, significado = m.groups()
    if libre is not None:
        return {"codigo": codigo, "valor": libre, "texto": f"{codigo}({libre})",
                "significado": significado}
    return {"codigo": codigo, "valor": lista, "texto": f"{codigo}{lista}",
            "significado": significado}


def texto_del_pdf(data: bytes) -> tuple[str, list[str]]:
    """Texto de todas las páginas, con las columnas en su lugar. Sólo pypdf
    (pdfminer se cuelga con un PDF armado, RENDIMIENTO-1b), sin OCR."""
    texto, avisos, _ = _hojas_del_pdf(data)
    return texto, avisos


class _DemasiadoTrabajo(BaseException):
    """Se gastó el tope de CPU en medio de una hoja. No hereda de Exception
    para que el `except Exception` de cada hoja no se la trague."""


@contextlib.contextmanager
def _tope_de_cpu(segundos: float):
    """Corta con `_DemasiadoTrabajo` cuando el proceso gastó `segundos` de CPU,
    aunque sea en medio de una hoja: una sola hoja puede costar minutos. Una
    señal sólo se atiende en el hilo principal; en otro hilo queda el control
    entre hojas."""
    if threading.current_thread() is not threading.main_thread() or not hasattr(signal, "setitimer"):
        yield
        return
    leyendo = True

    def cortar(*_):
        if leyendo:
            raise _DemasiadoTrabajo

    anterior = signal.signal(signal.SIGPROF, cortar)
    # Se repite: si la señal cae en un finalizador, Python ignora la excepción.
    signal.setitimer(signal.ITIMER_PROF, max(segundos, 0.001), 0.05)
    try:
        yield
    finally:
        leyendo = False
        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.signal(signal.SIGPROF, anterior)


def _hojas_del_pdf(data: bytes, limite_cpu_s: float = _MAX_CPU_LECTURA) -> tuple[str, list[str], bool]:
    """Texto, avisos y si quedó alguna hoja sin leer por pesada o rota. Deja
    de leer cuando el proceso gastó `limite_cpu_s` segundos de CPU."""
    import time

    from pypdf import apply_configuration

    avisos = []
    salteadas = False
    textos: list[str] = []
    hasta = time.process_time() + limite_cpu_s
    try:
        with apply_configuration(**_TOPES), _tope_de_cpu(limite_cpu_s):
            salteadas = _leer_hojas(data, hasta, textos, avisos)
    except _DemasiadoTrabajo:
        avisos.append(f"El PDF da demasiado trabajo: leí hasta la hoja {len(textos)}.")
        salteadas = True
    return "\n".join(textos), avisos, salteadas


def _leer_hojas(data: bytes, hasta: float, textos: list[str], avisos: list[str]) -> bool:
    """Suma a `textos` el texto de cada hoja que leyó y a `avisos` lo que no.
    Devuelve si quedó alguna hoja sin leer."""
    import time

    from pypdf import PdfReader
    from pypdf.errors import LimitReachedError

    salteadas = False
    try:
        reader = PdfReader(io.BytesIO(data))
        paginas = list(reader.pages)
    except MemoryError:
        raise
    except Exception:
        avisos.append("No pude abrir el PDF.")
        return True
    if len(paginas) > _MAX_PAGINAS:
        avisos.append(f"El PDF tiene {len(paginas)} hojas: leí las primeras {_MAX_PAGINAS}.")
        paginas = paginas[:_MAX_PAGINAS]
    largo = 0
    for n, pagina in enumerate(paginas, start=1):
        if time.process_time() > hasta:
            avisos.append(f"El PDF da demasiado trabajo: leí hasta la hoja {n - 1}.")
            salteadas = True
            break
        try:
            contenido = pagina.get_contents()
            if contenido is not None and len(contenido.get_data()) > _MAX_CONTENIDO_PAGINA:
                raise LimitReachedError("contenido de la hoja")
            texto = _MEDIO_PAR.sub("\ufffd", pagina.extract_text(extraction_mode="layout") or "")
        except MemoryError:
            raise
        except LimitReachedError:
            avisos.append(f"No leí la hoja {n}: es demasiado pesada.")
            salteadas = True
            continue
        except Exception:
            avisos.append(f"No pude leer la hoja {n}.")
            salteadas = True
            continue
        largo += len(texto)
        if largo > _MAX_TEXTO:
            avisos.append("El texto de la primera hoja es demasiado largo: no leí ninguna." if n == 1
                          else f"El texto del PDF es demasiado largo: leí hasta la hoja {n - 1}.")
            salteadas = True
            break
        textos.append(texto)
    return salteadas


def _nuevo_bloque(tipo: str, numero: str | None) -> dict:
    return {"tipo": tipo, "numero": numero, "campos": {}, "descripcion": [],
            "sufijos": [], "hay_sufijos": False, "avisos": [],
            "descripcion_cerrada": False, "subitems": []}


def leer_texto(texto: str) -> dict:
    """Renglones del catálogo a partir del texto del despacho."""
    try:
        return _leer_texto(texto)
    except _NoEsDespacho as e:
        return {"renglones": [], "divisa": None, "avisos": [str(e)]}


def _leer_texto(texto: str) -> dict:
    lineas = [l.rstrip() for l in texto.splitlines()]
    if any(len(l) > _MAX_LARGO_LINEA for l in lineas):
        raise _NoEsDespacho(f"Una línea pasa de {_MAX_LARGO_LINEA} caracteres: no parece un despacho.")
    avisos: list[str] = []
    caratula: dict[str, str] = {}
    items: list[dict] = []
    bloque = None  # el ítem o subítem que se está leyendo
    item = None
    en_sufijos = False
    hay_mas = False  # quedaron ítems sin leer por el tope de renglones

    i = 0
    while i < len(lineas):
        linea = lineas[i]
        plano = _plano(linea).strip()
        i += 1
        if not plano:
            continue
        if any(b in plano for b in _BASURA_DE_HOJA):
            en_sufijos = False
            continue

        columnas = _rotulos_de_linea(linea)
        if columnas:
            en_sufijos = False
            # El valor es la próxima línea con texto, si no es otra de rótulos.
            j = i
            while j < len(lineas) and not lineas[j].strip():
                j += 1
            valores = {}
            if j < len(lineas) and not _rotulos_de_linea(lineas[j]):
                valores = _valores_por_columna(lineas[j], columnas)
                i = j + 1
            nombres = [r for _, r in columnas]
            # Se corta antes de un ítem nuevo, para no separar un ítem de sus
            # subítems; los de un ítem con muchos se cortan al final.
            if _INICIO_ITEM in nombres and sum(len(it["subitems"]) or 1 for it in items) >= MAX_RENGLONES:
                hay_mas = True
                break
            if _INICIO_ITEM in nombres:
                item = _nuevo_bloque("item", valores.get(_INICIO_ITEM))
                items.append(item)
                bloque = item
            elif _INICIO_SUBITEM in nombres and item is not None:
                bloque = _nuevo_bloque("subitem", valores.get(_INICIO_SUBITEM))
                item["subitems"].append(bloque)
            destino = caratula if bloque is None else bloque["campos"]
            for rotulo, valor in valores.items():
                destino.setdefault(rotulo, valor)
            continue

        if bloque is None:
            continue

        m = _SUFIJOS_TITULO.match(linea.strip())
        if m:
            en_sufijos = True
            bloque["hay_sufijos"] = True
            bloque["descripcion_cerrada"] = True
            linea = m.group(1)
            if not linea.strip():
                continue
        if en_sufijos:
            sufijo = parsear_sufijo(linea)
            if sufijo:
                bloque["sufijos"].append(sufijo)
                continue
            en_sufijos = False
            if "=" in linea:
                bloque["avisos"].append(f"No entendí este sufijo: «{linea.strip()}».")
                continue

        if any(plano.startswith(t) for t in _TITULOS):
            if any(plano.startswith(t) for t in _FIN_DESCRIPCION):
                bloque["descripcion_cerrada"] = True
            continue
        if not bloque["descripcion_cerrada"]:
            bloque["descripcion"].append(re.sub(r"\s+", " ", linea.strip()))

    if not items:
        return {"renglones": [], "divisa": None,
                "avisos": [AVISO_NO_ES_DESPACHO] if texto.strip() else []}

    divisa = (caratula.get("Divisa FOB Total") or "").strip() or None
    if divisa is None:
        avisos.append("No encontré la divisa del FOB en la carátula: el valor unitario va sin divisa.")
    renglones = []
    for it in items:
        if it["subitems"]:
            for sub in it["subitems"]:
                renglones.append(_renglon(sub, padre=it))
        else:
            renglones.append(_renglon(it))
    if hay_mas or len(renglones) > MAX_RENGLONES:
        avisos.append(f"El despacho tiene más de {MAX_RENGLONES} ítems y subítems: "
                      f"leí sólo los primeros {MAX_RENGLONES}.")
        renglones = renglones[:MAX_RENGLONES]
    return {"renglones": renglones, "divisa": divisa, "avisos": avisos}


def _renglon(bloque: dict, padre: dict | None = None) -> dict:
    campos = bloque["campos"]
    avisos = list(bloque["avisos"])
    heredados = []

    def leer(rotulo, de=campos):
        valor = (de.get(rotulo) or "").strip()
        return valor or None

    posicion = leer("Posición SIM / Código AFIP")
    origen_leido = leer("Origen Pais / Provincia")
    if padre is not None:
        if posicion is None and leer("Posición SIM / Código AFIP", padre["campos"]):
            posicion = leer("Posición SIM / Código AFIP", padre["campos"])
            heredados.append("posicion_sim")
        if origen_leido is None and leer("Origen Pais / Provincia", padre["campos"]):
            origen_leido = leer("Origen Pais / Provincia", padre["campos"])
            heredados.append("origen")
    if posicion is not None:
        posicion = posicion.split()[0]
        if not _POSICION.match(posicion):
            avisos.append(f"La posición «{posicion}» no tiene la forma de una posición SIM.")
            posicion = None

    origen = origen_iso2(origen_leido) if origen_leido else None
    if origen_leido and origen is None:
        avisos.append(f"No reconocí el origen «{origen_leido}».")

    def numero(rotulo, nombre):
        crudo = leer(rotulo)
        if crudo is None:
            return None
        valor = numero_ar(crudo)
        if valor is None:
            avisos.append(f"No pude leer {nombre}: «{crudo}».")
        elif not valor < _MAX_NUMERO:  # el mismo tope que guardar; también el infinito
            avisos.append(f"{nombre[0].upper()}{nombre[1:]} pasa del máximo: «{crudo[:40]}».")
            return None
        return valor

    unidad = leer("Unidad")
    if padre is None and any("SUBITEM" in (leer(r) or "").upper()
                             for r in ("Unidad", "Unidad / Estado")):
        avisos.append("El ítem dice SUBITEM pero no encontré sus subítems.")
        if unidad and unidad.upper() == "SUBITEM":
            unidad = None
    descripcion = " ".join(d for d in bloque["descripcion"] if d) or None
    if descripcion and _CARACTER_ROTO.search(descripcion):
        avisos.append("La descripción tiene caracteres que no se pudieron leer (?): revisala.")
    if bloque["hay_sufijos"] and not bloque["sufijos"]:
        avisos.append("Encontré «Sufijos de valor» pero ningún sufijo.")

    renglon = {
        "item": (padre or bloque)["numero"],
        "subitem": bloque["numero"] if padre is not None else None,
        "posicion_sim": posicion,
        "descripcion": descripcion,
        "sufijos": bloque["sufijos"],
        "origen": origen,
        "origen_leido": origen_leido,
        "unidad": unidad,
        "cantidad": numero("Cantidad Unidades", "la cantidad"),
        "valor_unitario": numero("Unitario en Divisa", "el valor unitario"),
        "kilo_neto": numero("Total Kg. Neto", "el kilo neto"),
        "heredados": heredados,
        "avisos": avisos,
    }
    renglon["faltantes"] = [c for c in CAMPOS
                            if renglon[c] is None or (c == "sufijos" and not renglon[c])]
    return renglon


def leer_despacho(data: bytes, limite_cpu_s: float = _MAX_CPU_LECTURA) -> dict:
    """Renglones del catálogo de un PDF de despacho. No guarda nada. El tope
    de CPU cubre extraer el texto y entenderlo."""
    import time

    inicio = time.process_time()
    texto, avisos, salteadas = _hojas_del_pdf(data, limite_cpu_s * _PARTE_PARA_EXTRAER)
    if not texto.strip():
        # Si quedaron hojas sin leer, no se sabe si es escaneado.
        return {"renglones": [], "divisa": None, "sin_texto": not salteadas,
                "avisos": avisos if salteadas else avisos + [AVISO_SIN_TEXTO]}
    try:
        with _tope_de_cpu(limite_cpu_s - (time.process_time() - inicio)):
            resultado = leer_texto(texto)
    except _DemasiadoTrabajo:
        return {"renglones": [], "divisa": None, "sin_texto": False,
                "avisos": avisos + ["El PDF da demasiado trabajo: no pude leer sus productos."]}
    resultado["avisos"] = avisos + resultado["avisos"]
    resultado["sin_texto"] = False
    return resultado


def validar_pdf(data: bytes, limite_cpu_s: float = _MAX_CPU_LECTURA) -> dict:
    """Lo que mira la subida de un PDF: si está encriptado y cuántas hojas
    tiene. Uno que no se abre da {"error": el motivo}; uno que gasta
    `limite_cpu_s` de CPU, `_DemasiadoTrabajo`."""
    from pypdf import PdfReader

    try:
        with _tope_de_cpu(limite_cpu_s):
            pdf = PdfReader(io.BytesIO(data))
            if pdf.is_encrypted:
                return {"encriptado": True, "paginas": 0}  # contar hojas de uno encriptado ya falla
            return {"encriptado": False, "paginas": len(pdf.pages)}
    except (MemoryError, SystemError) as e:
        # Bajo el tope de memoria, una función en C de pypdf puede fallar con SystemError.
        raise MemoryError from e
    except Exception as e:
        return {"error": str(e)}


def texto_plano_del_pdf(data: bytes, limite_cpu_s: float = _MAX_CPU_LECTURA) -> dict:
    """{"texto": `extraer_texto_pdf_seguro`}, con los topes por flujo del lector."""
    from pypdf import apply_configuration

    from proyecto_maria.pdf_extractor import extraer_texto_pdf_seguro

    with apply_configuration(**_TOPES), _tope_de_cpu(limite_cpu_s):
        return {"texto": extraer_texto_pdf_seguro(data)}


# Lo que puede hacer el proceso aparte, y cómo se lo nombra si se cae.
_MODOS = {"leer": (leer_despacho, "el lector de despachos"),
          "validar": (validar_pdf, "el validador de PDF"),
          "texto": (texto_plano_del_pdf, "el lector de texto del PDF")}


class PdfDemasiadoPesado(Exception):
    """El proceso que lee pasó del tope de memoria o, al validar o sacar el
    texto, del de CPU."""


class LectorOcupado(Exception):
    """El mismo usuario ya tiene una lectura en curso."""


class SinLugar(TimeoutError):
    """Se acabó el tiempo esperando un lugar, antes de empezar con el PDF."""


_SEMAFOROS: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()
# Las claves (usuarios) con una lectura en curso, por loop.
_LEYENDO: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


_FINAL_DE_ERRORES = 2000

# Validar PDFs al subirlos: lugares propios, aparte de los de leer despachos.
_VALIDANDO_A_LA_VEZ = 2
# Por loop: (semáforo, {clave: [candado, pedidos de esa clave en curso]}).
_VALIDANDO: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


async def _escribir(entrada, data: bytes) -> None:
    try:
        entrada.write(data)
        await entrada.drain()
    except (BrokenPipeError, ConnectionResetError):
        pass  # el lector salió antes de leer todo: lo dice su código de salida
    finally:
        entrada.close()


async def _final(flujo, tope: int) -> bytes:
    """Los últimos `tope` bytes del flujo, sin juntarlo entero."""
    final = b""
    while bloque := await flujo.read(64 * 1024):
        final = (final + bloque)[-tope:]
    return final


async def leer_despacho_aparte(data: bytes, limite_s: float, clave: str | None = None,
                               limite_cpu_s: float = _MAX_CPU_LECTURA) -> dict:
    """`leer_despacho` en otro proceso, con la memoria topeada y un tiempo
    máximo. Si pasa del tiempo, el proceso se mata (un hilo no se puede
    cortar desde afuera) y levanta TimeoutError; si pasa de la memoria,
    PdfDemasiadoPesado. Como mucho `_HIJOS_A_LA_VEZ` a la vez: la espera
    cuenta dentro del tiempo máximo. Con `clave`, una sola lectura por clave
    a la vez: la segunda levanta LectorOcupado, así un usuario no ocupa todos
    los lugares. Es por proceso de la app: con varios procesos, cada uno
    tiene los suyos."""
    loop = asyncio.get_running_loop()
    semaforo = _SEMAFOROS.get(loop)
    if semaforo is None:
        semaforo = _SEMAFOROS[loop] = asyncio.Semaphore(_HIJOS_A_LA_VEZ)
    leyendo = _LEYENDO.setdefault(loop, set())
    if clave is not None:
        if clave in leyendo:
            raise LectorOcupado(AVISO_OCUPADO)
        leyendo.add(clave)
    try:
        return await _leer_aparte(data, limite_s, semaforo, limite_cpu_s)
    finally:
        leyendo.discard(clave)


async def validar_pdf_aparte(data: bytes, limite_s: float, clave: str | None = None,
                             modo: str = "validar") -> dict:
    """`validar_pdf` (con el modo «texto», `texto_plano_del_pdf`) en otro
    proceso, con los topes de memoria y de CPU del lector
    (PdfDemasiadoPesado). Espera un lugar hasta `limite_s` (SinLugar) y
    después el proceso tiene `limite_s` entero (TimeoutError): la espera no
    se le cobra al archivo. Como mucho `_VALIDANDO_A_LA_VEZ` a la vez.
    Con `clave`, las de una misma clave van de a una y esperan su turno: diez
    PDFs pesados de un usuario ocupan un solo lugar y no frenan a otro."""
    loop = asyncio.get_running_loop()
    estado = _VALIDANDO.get(loop)
    if estado is None:
        estado = _VALIDANDO[loop] = (asyncio.Semaphore(_VALIDANDO_A_LA_VEZ), {})
    semaforo, filas = estado
    hasta = loop.time() + limite_s
    if clave is None:
        return await _leer_aparte(data, limite_s, semaforo, _MAX_CPU_LECTURA, modo, hasta)
    fila = filas.setdefault(clave, [asyncio.Lock(), 0])
    fila[1] += 1
    try:
        try:
            await asyncio.wait_for(fila[0].acquire(), timeout=limite_s)
        except TimeoutError:
            raise SinLugar from None
        try:
            return await _leer_aparte(data, limite_s, semaforo, _MAX_CPU_LECTURA, modo, hasta)
        finally:
            fila[0].release()
    finally:
        fila[1] -= 1
        if not fila[1]:
            del filas[clave]


async def _leer_aparte(data: bytes, limite_s: float, semaforo, limite_cpu_s: float,
                       modo: str = "leer", hasta: float | None = None) -> dict:
    """Sin `hasta`, la espera por un lugar cuenta dentro de `limite_s`. Con
    `hasta`, se espera un lugar hasta ese momento y el proceso tiene `limite_s`."""
    entorno = {k: os.environ[k] for k in ("PATH", "HOME", "LANG", "LC_ALL", "PYTHONUSERBASE")
               if k in os.environ}
    # El lector de facturas carga el .env al importarse: el hijo no lo lee.
    entorno["PYTHON_DOTENV_DISABLED"] = "1"

    async def correr():
        proceso = await asyncio.create_subprocess_exec(
            sys.executable, "-m", __name__, repr(float(limite_cpu_s)), modo,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, cwd=str(Path(__file__).resolve().parents[2]),
            env=entorno)
        try:
            _, salida, errores = await asyncio.gather(
                _escribir(proceso.stdin, data), proceso.stdout.read(),
                _final(proceso.stderr, _FINAL_DE_ERRORES))
            await proceso.wait()
        finally:
            if proceso.returncode is None:
                proceso.kill()
                await proceso.wait()
        return proceso.returncode, salida, errores

    loop = asyncio.get_running_loop()
    espera_aparte = hasta is not None
    hasta = hasta if espera_aparte else loop.time() + limite_s
    try:
        await asyncio.wait_for(semaforo.acquire(), timeout=hasta - loop.time())
    except TimeoutError:
        raise SinLugar from None
    try:
        corrida = limite_s if espera_aparte else hasta - loop.time()
        codigo, salida, errores = await asyncio.wait_for(correr(), timeout=corrida)
    finally:
        semaforo.release()
    if codigo == _SALIDA_DEMASIADO_PESADO:
        raise PdfDemasiadoPesado(AVISO_SIN_MEMORIA)
    final = errores.decode("utf-8", "replace")
    quien = _MODOS[modo][1]
    if codigo != 0:
        raise RuntimeError(f"{quien} salió con {codigo}: {final}")
    try:
        resultado = json.loads(salida)
    except ValueError as e:
        raise RuntimeError(f"{quien} no devolvió JSON: {final}") from e
    if not isinstance(resultado, dict):
        raise RuntimeError(f"{quien} no devolvió un resultado")
    return resultado


def _main() -> int:
    """El proceso aparte, en uno de los `_MODOS`: el PDF por la entrada, el
    resultado en JSON por la salida. Sale con `_SALIDA_DEMASIADO_PESADO` si
    pasa del tope de memoria o, al validar o sacar el texto, del de CPU."""
    try:
        import resource
        _, duro = resource.getrlimit(resource.RLIMIT_AS)
        tope = _MAX_MEMORIA_HIJO if duro == resource.RLIM_INFINITY else min(_MAX_MEMORIA_HIJO, duro)
        resource.setrlimit(resource.RLIMIT_AS, (tope, duro))
    except (ImportError, ValueError, OSError) as e:
        print(f"lector de despachos sin tope de memoria: {e}", file=sys.stderr)
    logging.getLogger("pypdf").setLevel(logging.ERROR)  # un aviso por objeto roto
    try:
        limite_cpu_s = float(sys.argv[1]) if len(sys.argv) > 1 else _MAX_CPU_LECTURA
        modo = sys.argv[2] if len(sys.argv) > 2 else "leer"
        data = sys.stdin.buffer.read()
        resultado = _MODOS[modo][0](data, limite_cpu_s)
        sys.stdout.write(json.dumps(resultado, ensure_ascii=False))
        sys.stdout.flush()
    except (MemoryError, _DemasiadoTrabajo):
        return _SALIDA_DEMASIADO_PESADO
    return 0


# --- Guardar en el catálogo -------------------------------------------------

MAX_RENGLONES = 500
_MAX_DESCRIPCION = 2000
_MAX_NUMERO = 1e12


def _numero_del_renglon(valor, nombre, problemas):
    if valor is None or valor == "":
        return None
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        problemas.append(f"{nombre} no es un número.")
        return None
    if not (0 <= valor < _MAX_NUMERO):  # también descarta NaN e infinito
        problemas.append(f"{nombre} tiene que ser un número positivo.")
        return None
    return float(valor)


def origen_para_catalogo(valor) -> tuple[str | None, str | None]:
    """El origen que se guarda en el catálogo (None si no vino) o por qué no
    sirve: tiene que ser el código de dos letras de un país de la tabla."""
    from proyecto_maria.core.maria_generator import pais_reconocido

    if not isinstance(valor, (str, type(None))):
        return None, "El origen tiene que ser el código de dos letras."
    escrito = (valor or "").strip()
    if _MEDIO_PAR.search(escrito):
        # No se repite en el mensaje: no se puede mandar en la respuesta.
        return None, "El origen tiene un carácter que no se puede guardar."
    # Se mira antes de pasar a mayúsculas («ıt» sería «IT») y pais_reconocido
    # normaliza con NFKD («ＢＲ» o «ÉS» pasarían): sólo dos letras ASCII.
    if escrito and not (len(escrito) == 2 and escrito.isascii() and escrito.isalpha()
                        and pais_reconocido(escrito)):
        return None, f"No reconozco el origen «{escrito}»: usá el código de dos letras."
    return escrito.upper() or None, None


def renglon_para_catalogo(renglon) -> tuple[dict | None, list[str]]:
    """Lo que se guarda de un renglón revisado, o lo que le falta. Un renglón
    sirve con su posición SIM (o el NCM de 8 dígitos) y su descripción; el
    origen, si viene, tiene que ser un país de la tabla."""
    from proyecto_maria.services.client_memory import ncm_para_historial

    if not isinstance(renglon, dict):
        return None, ["El renglón no tiene la forma esperada."]
    problemas = []
    posicion = str(renglon.get("posicion_sim") or "").strip().upper()
    # La misma regla que el resto del catálogo: «8471.49.00», «84714900» y
    # «8471.49.00.100D» son el mismo NCM.
    ncm = ncm_para_historial(posicion)
    if not ncm:
        problemas.append("Falta la posición SIM o no tiene sus 8 dígitos.")
    descripcion = re.sub(r"\s+", " ", str(renglon.get("descripcion") or "")).strip()
    if not descripcion:
        problemas.append("Falta la descripción.")
    elif len(unicodedata.normalize("NFC", descripcion)) > _MAX_DESCRIPCION:  # se guarda en NFC
        problemas.append(f"La descripción pasa de {_MAX_DESCRIPCION} caracteres.")
    if _MEDIO_PAR.search(descripcion):
        problemas.append("La descripción tiene un carácter que no se puede guardar.")
    origen, problema = origen_para_catalogo(renglon.get("origen"))
    if problema:
        problemas.append(problema)
    cantidad = _numero_del_renglon(renglon.get("cantidad"), "La cantidad", problemas)
    unitario = _numero_del_renglon(renglon.get("valor_unitario"), "El valor unitario", problemas)
    kilo = _numero_del_renglon(renglon.get("kilo_neto"), "El kilo neto", problemas)
    if problemas:
        return None, problemas
    # El catálogo guarda el peso por unidad: el kilo neto del renglón dividido
    # la cantidad, si están los dos.
    peso = kilo / cantidad if kilo and cantidad else None
    if peso is not None and not (math.isfinite(peso) and peso < _MAX_NUMERO):
        # Una cantidad ínfima da un peso infinito, que no se puede mostrar.
        return None, ["El peso por unidad no se puede calcular: revisá la cantidad y el kilo neto."]
    return {"ncm": ncm, "descripcion": descripcion, "origen": origen,
            "valor_unitario": unitario or None, "cantidad": cantidad or None,
            "peso_unitario": peso}, []


if __name__ == "__main__":
    sys.exit(_main())
