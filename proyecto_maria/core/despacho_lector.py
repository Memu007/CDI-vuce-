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

import io
import re
import unicodedata

# Igual que el lector de facturas: pypdf tarda más que lineal con una página
# de contenido enorme (RENDIMIENTO-1b).
_MAX_CONTENIDO_PAGINA = 512 * 1024
_MAX_PAGINAS = 200

AVISO_SIN_TEXTO = (
    "El PDF no tiene texto que se pueda leer: parece escaneado. Pedí el "
    "despacho en PDF del sistema o cargá los productos a mano."
)
AVISO_NO_ES_DESPACHO = (
    "No encontré ningún ítem («Nº Item»). Revisá que sea el PDF del despacho "
    "oficializado."
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


def _rotulos_de_linea(linea: str) -> list[tuple[int, str]] | None:
    """Los rótulos de la línea, con su columna, de izquierda a derecha. None si
    la línea no es de rótulos: tiene que estar hecha sólo de rótulos (así una
    descripción que dice «TIPO» o «UNIDAD» sigue siendo descripción) y tener
    dos o más, o abrir un ítem o un subítem."""
    plano = _plano(linea)
    encontrados = []
    for rotulo, patron in _PATRONES:
        for m in patron.finditer(plano):
            encontrados.append((m.start(), m.end(), rotulo))
            plano = plano[:m.start()] + "\0" * (m.end() - m.start()) + plano[m.end():]
    if not encontrados or re.search(r"[A-Z0-9]", plano):
        return None
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
    inicios = [c for c, _ in columnas]
    trozos = []
    for m in re.finditer(r"\S+(?: \S+)*", linea):
        a, b = m.start(), m.end()
        for col in inicios:
            if a + 1 < col < b and linea[col - 1] == " ":
                trozos.append((a, linea[a:col].strip()))
                a = col
        trozos.append((a, linea[a:b].strip()))
    valores: dict[str, str] = {}
    for inicio, texto in trozos:
        if not texto:
            continue
        # La columna es la del último rótulo que empieza a la izquierda (con
        # dos de margen: un número alineado a la derecha puede asomar).
        elegida = None
        for col, rotulo in columnas:
            if col <= inicio + 2:
                elegida = rotulo
        if elegida is None:
            elegida = columnas[0][1]
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
    from pypdf import PdfReader

    avisos = []
    try:
        reader = PdfReader(io.BytesIO(data))
        paginas = list(reader.pages)
    except Exception:
        return "", ["No pude abrir el PDF."]
    if len(paginas) > _MAX_PAGINAS:
        avisos.append(f"El PDF tiene {len(paginas)} hojas: leí las primeras {_MAX_PAGINAS}.")
        paginas = paginas[:_MAX_PAGINAS]
    textos = []
    for n, pagina in enumerate(paginas, start=1):
        try:
            contenido = pagina.get_contents()
            if contenido is not None and len(contenido.get_data()) > _MAX_CONTENIDO_PAGINA:
                avisos.append(f"No leí la hoja {n}: es demasiado pesada.")
                continue
            textos.append(pagina.extract_text(extraction_mode="layout") or "")
        except Exception:
            avisos.append(f"No pude leer la hoja {n}.")
    return "\n".join(textos), avisos


def _nuevo_bloque(tipo: str, numero: str | None) -> dict:
    return {"tipo": tipo, "numero": numero, "campos": {}, "descripcion": [],
            "sufijos": [], "hay_sufijos": False, "avisos": [],
            "descripcion_cerrada": False, "subitems": []}


def leer_texto(texto: str) -> dict:
    """Renglones del catálogo a partir del texto del despacho."""
    lineas = [l.rstrip() for l in texto.splitlines()]
    avisos: list[str] = []
    caratula: dict[str, str] = {}
    items: list[dict] = []
    bloque = None  # el ítem o subítem que se está leyendo
    item = None
    en_sufijos = False

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


def leer_despacho(data: bytes) -> dict:
    """Renglones del catálogo de un PDF de despacho. No guarda nada."""
    texto, avisos = texto_del_pdf(data)
    if not texto.strip():
        return {"renglones": [], "divisa": None, "sin_texto": True,
                "avisos": avisos + [AVISO_SIN_TEXTO]}
    resultado = leer_texto(texto)
    resultado["avisos"] = avisos + resultado["avisos"]
    resultado["sin_texto"] = False
    return resultado


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


def renglon_para_catalogo(renglon) -> tuple[dict | None, list[str]]:
    """Lo que se guarda de un renglón revisado, o lo que le falta. Un renglón
    sirve con su posición SIM (o el NCM de 8 dígitos) y su descripción; el
    origen, si viene, tiene que ser un país de la tabla."""
    from proyecto_maria.core.maria_generator import pais_reconocido
    from proyecto_maria.services.client_memory import ncm_para_historial

    if not isinstance(renglon, dict):
        return None, ["El renglón no tiene la forma esperada."]
    problemas = []
    posicion = str(renglon.get("posicion_sim") or "").strip().upper()
    ncm = ncm_para_historial(posicion) if _POSICION.match(posicion) else None
    if not ncm:
        problemas.append("Falta la posición SIM o no tiene sus 8 dígitos.")
    descripcion = re.sub(r"\s+", " ", str(renglon.get("descripcion") or "")).strip()
    if not descripcion:
        problemas.append("Falta la descripción.")
    elif len(descripcion) > _MAX_DESCRIPCION:
        problemas.append(f"La descripción pasa de {_MAX_DESCRIPCION} caracteres.")
    origen = str(renglon.get("origen") or "").strip().upper() or None
    if origen and not (len(origen) == 2 and origen.isalpha() and pais_reconocido(origen)):
        problemas.append(f"No reconozco el origen «{origen}»: usá el código de dos letras.")
    cantidad = _numero_del_renglon(renglon.get("cantidad"), "La cantidad", problemas)
    unitario = _numero_del_renglon(renglon.get("valor_unitario"), "El valor unitario", problemas)
    kilo = _numero_del_renglon(renglon.get("kilo_neto"), "El kilo neto", problemas)
    if problemas:
        return None, problemas
    # El catálogo guarda el peso por unidad: el kilo neto del renglón dividido
    # la cantidad, si están los dos.
    peso = kilo / cantidad if kilo and cantidad else None
    return {"ncm": ncm, "descripcion": descripcion, "origen": origen,
            "valor_unitario": unitario or None, "cantidad": cantidad or None,
            "peso_unitario": peso}, []
