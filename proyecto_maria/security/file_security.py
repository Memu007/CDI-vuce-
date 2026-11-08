"""
File Security Module

Prevents:
- Path Traversal (CWE-22)
- Command Injection (CWE-78)
- Malicious File Upload (CWE-434)
"""

import math
import os
import re
import io
import struct
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, UploadFile
try:
    import magic  # python-magic
except ImportError:
    magic = None

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'pdf': ['.pdf'],
    'excel': ['.xlsx', '.xls'],
    'csv': ['.csv']
}

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    'pdf': ['application/pdf'],
    'excel': [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel'
    ],
    'csv': ['text/csv', 'text/plain']
}

# Maximum file sizes (bytes)
MAX_FILE_SIZES = {
    'pdf': 50 * 1024 * 1024,  # 50MB
    'excel': 10 * 1024 * 1024,  # 10MB
    'csv': 5 * 1024 * 1024  # 5MB
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent command injection and path traversal.

    Args:
        filename: Original filename from user

    Returns:
        Safe filename with only alphanumeric chars, dots, dashes, underscores

    Example:
        >>> sanitize_filename("../../etc/passwd")
        'etcpasswd'
        >>> sanitize_filename("test'; rm -rf /'; echo '.pdf")
        'test_rm_-rf__echo_.pdf'
    """
    # Remove any path components
    filename = os.path.basename(filename)

    # Replace dangerous characters with underscore
    # Allow only: a-z, A-Z, 0-9, dot, dash, underscore
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Remove leading dots (hidden files)
    safe_filename = safe_filename.lstrip('.')

    # Limit length
    if len(safe_filename) > 255:
        name, ext = os.path.splitext(safe_filename)
        safe_filename = name[:250] + ext

    return safe_filename


def validate_file_path(base_dir: str, filename: str) -> Path:
    """
    Validate file path to prevent path traversal attacks.

    Args:
        base_dir: Base directory where files are stored
        filename: Filename (will be sanitized)

    Returns:
        Validated absolute Path object

    Raises:
        HTTPException: If path is outside base directory

    Example:
        >>> validate_file_path("/data", "file.pdf")
        PosixPath('/data/file.pdf')
        >>> validate_file_path("/data", "../../../etc/passwd")
        HTTPException: 403 Forbidden - Access denied
    """
    # Sanitize filename first
    safe_filename = sanitize_filename(filename)

    # Resolve absolute paths
    base = Path(base_dir).resolve()
    requested = (base / safe_filename).resolve()

    # Verify file is within base directory
    if not str(requested).startswith(str(base)):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Invalid file path"
        )

    return requested


def _abrir_pdf(contents: bytes) -> tuple:
    """(¿encriptado?, cantidad de páginas). Con pypdf, sucesor de PyPDF2."""
    from pypdf import PdfReader
    pdf = PdfReader(io.BytesIO(contents))
    if pdf.is_encrypted:
        return True, 0  # contar páginas de uno encriptado ya falla
    return False, len(pdf.pages)


def partes_del_xlsx(z) -> tuple:
    """(libro, sus relaciones, textos compartidos o None): las rutas que usa
    openpyxl, que las busca por [Content_Types].xml y no por nombre fijo
    (renombrar sharedStrings.xml o poner un xl/workbook.xml señuelo no saltea
    los topes; revisión de EXCEL-2)."""
    from xml.etree import ElementTree as ET
    from openpyxl.packaging.manifest import Manifest
    from openpyxl.packaging.relationship import get_rels_path
    from openpyxl.reader.excel import _find_workbook_part
    from openpyxl.xml.constants import SHARED_STRINGS
    if z.getinfo("[Content_Types].xml").file_size > 2**20:
        raise ExcelDemasiadoGrande("El índice del Excel es demasiado grande.")
    _sin_dtd(z, ["[Content_Types].xml"])
    manifiesto = Manifest.from_tree(ET.fromstring(z.read("[Content_Types].xml")))
    libro = _find_workbook_part(manifiesto).PartName[1:]
    textos = manifiesto.find(SHARED_STRINGS)
    return libro, get_rels_path(libro), (textos.PartName[1:] if textos is not None else None)


def sheets_del_libro(z) -> list:
    """[(nombre, r:id, ruta dentro del zip, es_de_grafico)] de cada <sheet>
    de xl/workbook.xml que tiene relación, en el orden del libro."""
    import posixpath
    from xml.etree import ElementTree as ET
    ns_main = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    ns_rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    libro, relaciones, _ = partes_del_xlsx(z)
    for parte in (libro, relaciones):
        if z.getinfo(parte).file_size > 2**20:
            raise ExcelDemasiadoGrande("El índice del Excel es demasiado grande.")
    _sin_dtd(z, (libro, relaciones))
    carpeta = posixpath.dirname(libro)
    destinos = {}
    for r in ET.fromstring(z.read(relaciones)):
        destino = r.get("Target") or ""
        destino = destino.lstrip("/") if destino.startswith("/") else posixpath.normpath(posixpath.join(carpeta, destino))
        destinos[r.get("Id")] = (destino, "chartsheet" in (r.get("Type") or ""))
    hojas = []
    for h in ET.fromstring(z.read(libro)).iter(f"{ns_main}sheet"):
        rid = h.get(f"{ns_rel}id")
        if rid in destinos:
            hojas.append((h.get("name") or "", rid, destinos[rid][0], destinos[rid][1]))
    return hojas


def _sin_dtd(z, partes=None) -> None:
    """Un .xlsx de verdad no trae DTD ni entidades. Con una entidad, 5 KB se
    expandían a millones de etiquetas al abrir el libro y pasaban todos los
    topes (revisión de la devolución de EXCEL-2). Tampoco UTF-16, donde el
    «<!ENTITY» no se ve con bytes ASCII."""
    nombres = partes if partes is not None else [
        n for n in z.namelist() if n.lower().endswith((".xml", ".rels", ".vml"))]
    for nombre in nombres:
        with z.open(nombre) as f:
            cola = b""
            primero = True
            while True:
                bloque = f.read(2**20)
                if not bloque:
                    break
                if primero:
                    inicio = bloque.lstrip(b"\xef\xbb\xbf \t\r\n")[:4]
                    if inicio.startswith((b"\xff\xfe", b"\xfe\xff")) or b"\x00" in inicio:
                        raise ExcelDemasiadoGrande("El Excel tiene una parte en una codificación que no se lee. "
                                                   "Guardalo de nuevo desde Excel.")
                    primero = False
                trozo = cola + bloque
                if b"<!DOCTYPE" in trozo or b"<!ENTITY" in trozo:
                    raise ExcelDemasiadoGrande("El Excel trae declaraciones que un libro de Excel no tiene. "
                                               "Guardalo de nuevo desde Excel o cargá los productos a mano.")
                cola = trozo[-9:]


def hojas_del_xlsx(z) -> list:
    """[(nombre, ruta dentro del zip)] de las hojas de cálculo de un .xlsx
    abierto con zipfile, en el orden del libro, sin abrirlo con openpyxl.
    Las hojas de gráfico no cuentan: pandas lee la primera hoja de cálculo.
    Como openpyxl, es hoja toda relación de una <sheet> que no sea de
    gráfico, sea cual sea su Type: una con un Type raro no se medía ni se
    sacaba de la copia (devolución de EXCEL-2)."""
    return [(nombre, ruta) for nombre, _rid, ruta, grafico in sheets_del_libro(z) if not grafico]


def tope_de_entorno(nombre: str, defecto: float, escala: int = 1) -> int:
    """Lee un tope del entorno (en MB con escala 1024*1024, o en elementos) y
    devuelve el entero. Usa el de defecto si no se lee, si no es finito o si
    el entero da 0 o menos: con tope 0 no entra ningún archivo (devolución de
    EXCEL-2b). 1e308 MB es finito, pero en bytes no."""
    try:
        valor = float(os.getenv(nombre, "") or defecto) * escala
    except (TypeError, ValueError):
        valor = 0.0
    tope = int(valor) if math.isfinite(valor) else 0
    if tope <= 0:
        return int(defecto * escala)
    return tope


def _mb_de_entorno(nombre: str, defecto: float) -> int:
    return tope_de_entorno(nombre, defecto, 1024 * 1024)


def _elementos_de_entorno() -> int:
    """EXCEL_MAX_ELEMENTOS_ESTILOS, 500.000 por defecto: unos 300 MB y 6 s
    al abrir. Un libro real con 40.000 formatos y sus fuentes ya tiene
    220.000 (revisión de la devolución de EXCEL-2)."""
    return tope_de_entorno("EXCEL_MAX_ELEMENTOS_ESTILOS", 500_000)


def _mas_elementos_que(z, parte: str, tope: int) -> bool:
    """Cuenta las etiquetas que abren leyendo de a 1 MB, sin
    armar el árbol, y corta apenas pasa el tope. Puede contar de más (un «<x»
    dentro de un CDATA), nunca de menos."""
    import re
    # Cualquier etiqueta que abre, con el prefijo que sea: con «<ñ:xf/>» el
    # patrón de sólo letras ASCII no contaba nada (revisión de la devolución).
    abre = re.compile(rb"<[^/!?\s>]")
    n, cola = 0, b""
    with z.open(parte) as f:
        while True:
            bloque = f.read(2**20)
            if not bloque:
                return False
            trozo = cola + bloque
            n += len(abre.findall(trozo))
            if n > tope:
                return True
            # El último byte puede ser un «<» cuya letra viene en el bloque
            # que sigue: se guarda sólo si es «<», para no contarlo dos veces.
            cola = trozo[-1:] if trozo.endswith(b"<") else b""


# Los topes de Excel. openpyxl mira al abrir si el formato de cada formato de
# celda es de fecha, con una expresión cuadrática en los «[» que retiene el GIL.
_FORMATO_MAX_LARGO, _FORMATO_MAX_CORCHETES, _MAX_FORMATOS_DE_CELDA = 255, 32, 65_490


_FORMATOS_QUE_EXCEL_NO_GUARDA = (
    "El Excel tiene formatos de celda que Excel no guarda (demasiados o demasiado "
    "largos). Guardalo de nuevo desde Excel o cargá los productos a mano.")


def _formato_caro(codigo: str) -> bool:
    return len(codigo) > _FORMATO_MAX_LARGO or codigo.count("[") > _FORMATO_MAX_CORCHETES


def _formatos_que_excel_no_guarda(z, parte: str) -> bool:
    from xml.etree import ElementTree as ET
    en_celdas, celdas = 0, 0
    with z.open(parte) as f:
        for evento, e in ET.iterparse(f, events=("start", "end")):
            nombre = e.tag.rpartition("}")[2]
            if evento == "start":
                en_celdas += nombre == "cellXfs"
                continue
            if nombre == "numFmt":
                if _formato_caro(e.get("formatCode", "")):
                    return True
            elif nombre == "xf" and en_celdas:
                celdas += 1
                if celdas > _MAX_FORMATOS_DE_CELDA:
                    return True
            elif nombre == "cellXfs":
                en_celdas -= 1
            e.clear()
    return False


def _contar_hojas_xlsx(contents: bytes) -> tuple[int, bool]:
    """Devuelve (hojas, caro): caro si la forma del libro pide el carril pesado.
    Cuenta las hojas desde xl/workbook.xml y mira, antes de abrir el libro,
    cuánto pesan los textos compartidos y la primera hoja: openpyxl los lee
    enteros al abrir, y un libro armado (millones de textos vacíos, una hoja
    enorme) tardaba minutos y usaba gigas de memoria (D26 a, EXCEL-2)."""
    import zipfile
    from openpyxl.xml.constants import ARC_CORE, ARC_CUSTOM, ARC_STYLE
    with zipfile.ZipFile(io.BytesIO(contents)) as z:
        _sin_dtd(z)
        hojas = hojas_del_xlsx(z)
        _, _, textos = partes_del_xlsx(z)
        nombres = set(z.namelist())
        # openpyxl lee entero el .rels de cada hoja, aun sin abrirla
        # (revisión de la devolución de EXCEL-2): uno normal pesa bytes.
        for nombre in nombres:
            if nombre.lower().endswith(".rels") and z.getinfo(nombre).file_size > 2**20:
                raise ExcelDemasiadoGrande("Una parte del Excel es demasiado grande. Guardalo de nuevo "
                                           "desde Excel o cargá los productos a mano.")
        tope_textos = _mb_de_entorno("EXCEL_MAX_TEXTOS_MB", 10)
        if textos and textos in nombres and z.getinfo(textos).file_size > tope_textos:
            raise ExcelDemasiadoGrande(
                f"El Excel tiene demasiados textos (más de {tope_textos // 2**20} MB). "
                "Dejá sólo la hoja de la factura o cargá los productos a mano.")
        # Lo demás que openpyxl lee entero al abrir, con el mismo tope en MB y
        # otro en elementos: cada uno ocupa medio KB en memoria, y 10 MB de
        # <xf/> (17 KB comprimido) llegaban a 1,4 GB (devolución de EXCEL-2).
        tope_elementos = _elementos_de_entorno()
        for parte in (ARC_STYLE, ARC_CORE, ARC_CUSTOM):
            if parte in nombres and (z.getinfo(parte).file_size > tope_textos
                                     or _mas_elementos_que(z, parte, tope_elementos)):
                raise ExcelDemasiadoGrande(
                    "Una parte del Excel es demasiado grande. Guardalo de nuevo desde Excel o "
                    "cargá los productos a mano.")
        if ARC_STYLE in nombres and _formatos_que_excel_no_guarda(z, ARC_STYLE):
            raise ExcelDemasiadoGrande(_FORMATOS_QUE_EXCEL_NO_GUARDA)
        if hojas and hojas[0][1] not in nombres:
            raise ValueError("falta la primera hoja dentro del archivo")
        # 10 MB son unas 9.400 filas de 20 columnas con texto, o 3.100 de 60
        # (lo midió la revisión). Con 27 MB sin
        # <dimension>, 8 subidas así delante dejaban a una normal en 504; con
        # 10 MB, la normal da 200 en ~20 s (devolución de EXCEL-2).
        tope_hoja = _mb_de_entorno("EXCEL_MAX_PRIMERA_HOJA_MB", 10)
        if hojas and z.getinfo(hojas[0][1]).file_size > tope_hoja:
            raise ExcelDemasiadoGrande(
                f"La primera hoja del Excel es demasiado grande (más de {tope_hoja // 2**20} MB): "
                "tiene muchas columnas o filas con formato aunque estén vacías. Dejá sólo los "
                "productos de la factura.")
        # Una celda en la última columna (XFD) hace que pandas rellene cada
        # fila hasta 16.384 columnas: 2.000 filas así (15 KB comprimido)
        # llegaban a 943 MB (revisión de la devolución de EXCEL-2).
        columna, fila, ancho = _medida_hoja(z.read(hojas[0][1])) if hojas else (0, 0, 0)
        if columna > _EXCEL_MAX_COLUMNAS:
            raise ExcelDemasiadoGrande(
                f"La primera hoja del Excel usa una columna más allá de la {_EXCEL_MAX_COLUMNAS}. "
                "Dejá sólo las columnas de los productos de la factura.")
        # Con pocos KB, una fila lejana o miles de estilos o textos ya cuestan
        # segundos al leer: eso no va a los hilos livianos.
        caro = (fila > tope_de_entorno("EXCEL_LIVIANO_FILAS", 20_000)
                or ancho > tope_de_entorno("EXCEL_LIVIANO_COLUMNAS", 64)
                or (ARC_STYLE in nombres
                    and _mas_elementos_que(z, ARC_STYLE, tope_de_entorno("EXCEL_LIVIANO_ESTILOS", 5_000)))
                or (bool(textos) and textos in nombres
                    and _mas_elementos_que(z, textos, tope_de_entorno("EXCEL_LIVIANO_TEXTOS", 40_000))))
        return len(hojas), caro


# Las columnas que puede usar la primera hoja (IV, el límite del Excel viejo).
_EXCEL_MAX_COLUMNAS = 256
_EXCEL_MAX_RANGOS = 64_000


def _medida_hoja(xml: bytes) -> tuple[int, float, int]:
    """(columna, fila, ancho) máximos; sin «r», la fila o celda es la siguiente, como en
    openpyxl. «ancho» suma la <dimension>, que Excel guarda a veces como A1:XFD1048576.
    Rechaza la hoja con más de _EXCEL_MAX_RANGOS rangos entre sus sqref, celdas
    combinadas y vínculos."""
    from xml.etree import ElementTree as ET
    from openpyxl.utils.cell import coordinate_to_tuple, range_boundaries
    columna = fila = ancho = fila_actual = columna_actual = rangos = 0
    # XML normaliza comillas, espacios y entidades en los atributos. No se
    # conserva el árbol de la hoja ni se expanden filas hasta esa columna.
    with io.BytesIO(xml) as fuente:
        for evento, elemento in ET.iterparse(fuente, events=("start", "end")):
            if evento == "end":
                elemento.clear()
                continue
            etiqueta = elemento.tag.rsplit("}", 1)[-1]
            # openpyxl arma un objeto por rango de cada sqref (formato condicional, validación,
            # selección), combinada o vínculo: 300 000 en 1.4 MB tardan segundos al abrir.
            rangos += len(elemento.get("sqref", "").split(None, _EXCEL_MAX_RANGOS))
            rangos += etiqueta in ("mergeCell", "hyperlink")
            if rangos > _EXCEL_MAX_RANGOS:
                raise ExcelDemasiadoGrande(
                    "La primera hoja del Excel tiene demasiados rangos con formato condicional, "
                    "validación, celdas combinadas o vínculos. Sacáselos o cargá los productos a mano.")
            try:
                if etiqueta == "row":
                    columna_actual = 0
                    r = elemento.get("r")
                    fila_actual = fila_actual + 1 if r is None else int(float(r))
                    fila = max(fila, fila_actual)
                elif etiqueta == "c":
                    if elemento.get("r"):
                        f, columna_actual = coordinate_to_tuple(elemento.get("r"))
                        fila = max(fila, f)
                    else:
                        columna_actual += 1
                    columna = max(columna, columna_actual)
                    if columna > _EXCEL_MAX_COLUMNAS:
                        break
                elif etiqueta == "dimension":
                    _, _, ultima_columna, ultima_fila = range_boundaries(elemento.get("ref", ""))
                    ancho = max(ancho, ultima_columna or 0)
                    fila = max(fila, ultima_fila or 0)
            except (TypeError, ValueError, OverflowError):
                fila = math.inf
    return columna, fila, max(ancho, columna)


def _formatos_xls_que_excel_no_guarda(contents: bytes) -> bool:
    """xlrd mira cada registro FORMAT (BIFF 0x041E y 0x001E) con la misma
    expresión cuadrática en los «[»: se cuentan antes, sin leer el libro."""
    from xlrd import compdoc
    datos = contents
    if contents[:8] == compdoc.SIGNATURE:
        doc = compdoc.CompDoc(contents, logfile=io.StringIO())
        datos = doc.get_named_stream("Workbook") or doc.get_named_stream("Book") or b""
    pos = 0
    while pos + 4 <= len(datos):
        tipo, largo = struct.unpack_from("<HH", datos, pos)
        pos += 4
        if tipo in (0x041E, 0x001E) and _formato_xls_caro(tipo, datos[pos:pos + largo]):
            return True
        pos += largo
    return False


def _formato_xls_caro(tipo: int, registro: bytes) -> bool:
    """En BIFF8 el FORMAT trae cuenta, bandera y texto, en UTF-16 si la bandera lo dice;
    de otra versión o si no cuadra, se cuentan los «[» de todos sus bytes."""
    if tipo == 0x041E and len(registro) >= 5:
        cuenta, bandera = struct.unpack_from("<HB", registro, 2)
        ancho = 2 if bandera & 1 else 1
        if len(registro) == 5 + ancho * cuenta:
            return _formato_caro(registro[5:].decode("utf-16-le" if ancho == 2 else "latin-1"))
    return registro.count(b"[") > _FORMATO_MAX_CORCHETES


def _contar_hojas_excel(contents: bytes, file_ext: str) -> tuple[int, bool]:
    if file_ext == '.xlsx':
        return _contar_hojas_xlsx(contents)
    # El formato binario .xls no puede abrirse con openpyxl.
    # Pandas usa xlrd y alcanza con validar que exista alguna hoja.
    import pandas as pd
    if _formatos_xls_que_excel_no_guarda(contents):
        raise ExcelDemasiadoGrande(_FORMATOS_QUE_EXCEL_NO_GUARDA)
    return len(pd.ExcelFile(io.BytesIO(contents), engine='xlrd').sheet_names), False


def _excel_max_descomprimido_bytes() -> int:
    """EXCEL_MAX_DESCOMPRIMIDO_MB, 100 por defecto (EXCEL-1)."""
    return _mb_de_entorno("EXCEL_MAX_DESCOMPRIMIDO_MB", 100)


def _excel_descomprimido_bytes(contents: bytes) -> int:
    """Cuánto ocupa un .xlsx descomprimido, leyendo sólo el índice del zip.

    Un .xlsx de 1 MB puede descomprimirse a gigas y llenar la memoria al
    abrirlo. zipfile no entrega más bytes que los que declara el índice, así
    que el índice no puede mentir para abajo (EXCEL-1).
    """
    import zipfile
    with zipfile.ZipFile(io.BytesIO(contents)) as z:
        return sum(info.file_size for info in z.infolist())


class ExcelDemasiadoGrande(Exception):
    """El .xlsx descomprimido pasa de EXCEL_MAX_DESCOMPRIMIDO_MB, o sus textos
    o su primera hoja pasan de su tope (D26 a). El mensaje es para la persona."""


# Validar un Excel usa su propio grupo de hilos: muchas subidas pesadas no le
# quitan los hilos compartidos al resto (sugerir NCM, validar PDF) (EXCEL-1).
_POOL_VALIDAR_EXCEL = None


def _pool_validar_excel():
    global _POOL_VALIDAR_EXCEL
    if _POOL_VALIDAR_EXCEL is None:
        from concurrent.futures import ThreadPoolExecutor
        try:
            hilos = max(1, int(os.getenv("EXCEL_VALIDATE_WORKERS", "2")))
        except (TypeError, ValueError):
            hilos = 2
        _POOL_VALIDAR_EXCEL = ThreadPoolExecutor(hilos, thread_name_prefix="validar-excel")
    return _POOL_VALIDAR_EXCEL


# Carril liviano (EXCEL-2b): un libro chico valida y se lee en hilos propios y
# no espera detrás de las subidas pesadas, que comparten el GIL y tardan.
_POOL_VALIDAR_EXCEL_LIVIANO = None


def _pool_validar_excel_carril(liviano: bool):
    global _POOL_VALIDAR_EXCEL_LIVIANO
    if not liviano:
        return _pool_validar_excel()
    if _POOL_VALIDAR_EXCEL_LIVIANO is None:
        from concurrent.futures import ThreadPoolExecutor
        try:
            hilos = max(1, int(os.getenv("EXCEL_VALIDATE_WORKERS", "2")))
        except (TypeError, ValueError):
            hilos = 2
        _POOL_VALIDAR_EXCEL_LIVIANO = ThreadPoolExecutor(hilos, thread_name_prefix="validar-excel-liviano")
    return _POOL_VALIDAR_EXCEL_LIVIANO


# Firmas de imagen: una parte que empieza así no es XML y el parser la
# rechaza en el primer byte, así que no puede ser una hoja disfrazada.
_FIRMAS_IMAGEN = (b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"GIF87a", b"GIF89a", b"BM",
                  b"II*\x00", b"MM\x00*", b"\xd7\xcd\xc6\x9a")
_LIVIANO_INDICE_MAX = 128 * 1024        # bytes del índice del zip que se leen en el loop
_LIVIANO_IMAGENES_MAX = 10 * 1024 * 1024  # bytes de imagen que se descuentan, como mucho
_LIVIANO_IMAGENES_LECTURAS = 20
_LIVIANO_CABEZA_COMPRIMIDA = 16 * 1024  # bytes comprimidos que se miran por cabeza


def _es_imagen(cabeza: bytes) -> bool:
    if cabeza.startswith(_FIRMAS_IMAGEN):
        return True
    return cabeza.startswith(b"\x01\x00\x00\x00") and cabeza[40:44] == b" EMF"


def _cabeza_de(contents: bytes, info) -> bytes:
    """Los primeros 44 bytes de una entrada, mirando a lo sumo 16 KiB de lo
    comprimido: zipfile la descomprimiría entera si no da bytes antes."""
    import zipfile
    import zlib
    local = info.header_offset
    if contents[local:local + 4] != b"PK\x03\x04":
        return b""
    nombre, extra = int.from_bytes(contents[local + 26:local + 28], "little"), \
        int.from_bytes(contents[local + 28:local + 30], "little")
    inicio = local + 30 + nombre + extra
    datos = contents[inicio:inicio + min(info.compress_size, _LIVIANO_CABEZA_COMPRIMIDA)]
    if info.compress_type == zipfile.ZIP_STORED:
        return datos[:44]
    return zlib.decompressobj(-15).decompress(datos, 44)


def _excel_liviano(contents: bytes, file_ext: str) -> bool:
    """¿Va al carril liviano por su tamaño? Se mide desde los bytes subidos:
    un .xls, por su tamaño; un .xlsx, por lo que declara descomprimido su
    índice, sin las imágenes reconocidas por su firma. El libro no puede
    declarar menos de lo que entrega: zipfile no lee más bytes que los del
    índice. Corre en el hilo del servidor, así que todo está acotado antes de
    abrir el zip; ante cualquier duda, carril pesado (EXCEL-2b)."""
    umbral = _mb_de_entorno("EXCEL_LIVIANO_MB", 2)
    if file_ext != ".xlsx":
        return len(contents) <= umbral
    import zipfile
    try:
        # El mismo fin de índice que busca zipfile: en los últimos 64 KiB.
        # Con un índice largo, o zip64, el índice no se lee acá.
        fin = contents.rfind(b"PK\x05\x06", max(0, len(contents) - (1 << 16) - 22))
        if fin < 0 or len(contents) - fin < 22:
            return False
        if contents[max(0, fin - 20):fin].startswith(b"PK\x06\x07"):
            return False
        if int.from_bytes(contents[fin + 12:fin + 16], "little") > _LIVIANO_INDICE_MAX:
            return False
        with zipfile.ZipFile(io.BytesIO(contents)) as z:
            entradas = z.infolist()
            resto = sum(info.file_size for info in entradas)
            if resto <= umbral:
                return True
            # Las imágenes no cuentan, pero sólo las que lo son por su firma:
            # una hoja con nombre de imagen sigue contando.
            candidatas = sorted(
                (info for info in entradas
                 if not info.filename.lower().endswith((".xml", ".rels", ".vml"))
                 and info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                 and not info.flag_bits & 0x1),
                key=lambda info: info.file_size, reverse=True)
            descontado = 0
            for info in candidatas[:_LIVIANO_IMAGENES_LECTURAS]:
                if descontado + info.file_size > _LIVIANO_IMAGENES_MAX:
                    continue
                try:
                    cabeza = _cabeza_de(contents, info)
                except Exception:
                    continue
                if _es_imagen(cabeza):
                    descontado += info.file_size
                    if resto - descontado <= umbral:
                        return True
        return False
    except Exception:
        return False


def _abrir_excel(contents: bytes, file_ext: str) -> tuple[int, bool]:
    """Mira cuánto ocupa descomprimido y recién entonces cuenta las hojas.
    Corre en otro hilo: un zip con miles de entradas también tarda (EXCEL-1)."""
    if file_ext == '.xlsx' and _excel_descomprimido_bytes(contents) > _excel_max_descomprimido_bytes():
        raise ExcelDemasiadoGrande()
    return _contar_hojas_excel(contents, file_ext)


def _pdf_validate_timeout_s() -> float:
    """Mal escrito, en 0 o negativo, vale 30 s (RENDIMIENTO-1b)."""
    try:
        valor = float(os.getenv("PDF_VALIDATE_TIMEOUT_S", "") or 30)
    except (TypeError, ValueError):
        return 30.0
    return valor if math.isfinite(valor) and valor > 0 else 30.0


async def validate_file_upload(
    file: UploadFile,
    file_type: str,
    max_size: Optional[int] = None
) -> bytes:
    """Valida y devuelve los bytes. Ver validar_con_carril."""
    return (await validar_con_carril(file, file_type, max_size))[0]


async def validar_con_carril(
    file: UploadFile,
    file_type: str,
    max_size: Optional[int] = None
) -> tuple:
    """
    Validate uploaded file for security.

    Checks:
    - File extension
    - MIME type (magic bytes)
    - File size
    - File content (for PDF/Excel)

    Args:
        file: Uploaded file
        file_type: Expected file type ('pdf', 'excel', 'csv')
        max_size: Maximum file size in bytes (optional, uses default)

    Returns:
        (contents, liviano): los bytes, y si un Excel va al carril liviano
        (_excel_liviano y la forma del libro); para otros tipos, False. Quien
        lee el Excel después usa ese mismo valor: no se vuelve a medir.

    Raises:
        HTTPException: If file is invalid
    """
    # Validate file type parameter
    if file_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {file_type}")

    # Check filename exists
    if not file.filename:
        raise HTTPException(400, "Filename is required")

    # Sanitize filename
    safe_filename = sanitize_filename(file.filename)

    # Check file extension
    file_ext = os.path.splitext(safe_filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS[file_type]:
        raise HTTPException(
            400,
            f"Invalid file extension. Expected {ALLOWED_EXTENSIONS[file_type]}, got {file_ext}"
        )

    # Read file contents
    contents = await file.read()

    # Check file size
    max_size = max_size or MAX_FILE_SIZES.get(file_type, 10 * 1024 * 1024)
    if len(contents) > max_size:
        raise HTTPException(
            413,
            f"File too large. Maximum size: {max_size / 1024 / 1024:.1f}MB"
        )

    # Check for empty file
    if len(contents) == 0:
        raise HTTPException(400, "File is empty")

    # Validate MIME type using magic bytes
    if magic is None:
        mime = None
    else:
        try:
            mime = magic.from_buffer(contents, mime=True)
        except Exception:
            mime = None

    if mime and mime not in ALLOWED_MIME_TYPES.get(file_type, []):
        raise HTTPException(
            400,
            f"Invalid file type. Expected {ALLOWED_MIME_TYPES[file_type]}, got {mime}"
        )

    # Additional validation for PDFs
    if file_type == 'pdf':
        try:
            # Abrir el PDF es sincrónico: va en otro hilo y con tiempo máximo,
            # para que un PDF pesado o armado no frene al resto (RENDIMIENTO-1).
            import asyncio
            try:
                encriptado, paginas = await asyncio.wait_for(
                    asyncio.to_thread(_abrir_pdf, contents),
                    timeout=_pdf_validate_timeout_s(),
                )
            except asyncio.TimeoutError:
                raise HTTPException(
                    400,
                    "No pudimos abrir el PDF: tardó demasiado. Probá con otro archivo.",
                )

            # Check if encrypted
            if encriptado:
                raise HTTPException(400, "Encrypted PDFs are not allowed")

            # Check if valid PDF (has pages)
            if paginas == 0:
                raise HTTPException(400, "PDF has no pages")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, f"Invalid PDF file: {str(e)}")

    # Additional validation for Excel
    liviano = False
    if file_type == 'excel':
        liviano = _excel_liviano(contents, file_ext)
        try:
            # Abrir el Excel es sincrónico: va en otro hilo y con tiempo máximo,
            # para que un archivo pesado no frene al resto (EXCEL-1).
            import asyncio
            try:
                hojas, caro = await asyncio.wait_for(
                    asyncio.get_running_loop().run_in_executor(
                        _pool_validar_excel_carril(liviano), _abrir_excel, contents, file_ext
                    ),
                    timeout=_pdf_validate_timeout_s(),
                )
            except ExcelDemasiadoGrande as e:
                raise HTTPException(
                    400,
                    str(e) or "El Excel es demasiado grande descomprimido. Probá con una "
                    "planilla con menos datos o cargá los productos a mano.",
                )
            except asyncio.TimeoutError:
                raise HTTPException(
                    400,
                    "No pudimos abrir el Excel: tardó demasiado. Probá con otro archivo.",
                )
            if hojas == 0:
                raise HTTPException(400, "Excel file has no sheets")
            liviano = liviano and not caro

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, f"Invalid Excel file: {str(e)}")

    # Reset file pointer for later use
    await file.seek(0)

    return contents, liviano


def get_safe_temp_filename(original_filename: str, prefix: str = "upload_") -> str:
    """
    Generate safe temporary filename.

    Args:
        original_filename: Original filename
        prefix: Prefix for temp file

    Returns:
        Safe temporary filename

    Example:
        >>> get_safe_temp_filename("invoice.pdf")
        'upload_1234567890_invoice.pdf'
    """
    import time
    import secrets

    # Sanitize original filename
    safe_name = sanitize_filename(original_filename)

    # Add timestamp and random token
    timestamp = int(time.time())
    token = secrets.token_hex(4)

    return f"{prefix}{timestamp}_{token}_{safe_name}"
