"""
File Security Module

Prevents:
- Path Traversal (CWE-22)
- Command Injection (CWE-78)
- Malicious File Upload (CWE-434)
"""

import os
import re
import io
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
    manifiesto = Manifest.from_tree(ET.fromstring(z.read("[Content_Types].xml")))
    libro = _find_workbook_part(manifiesto).PartName[1:]
    textos = manifiesto.find(SHARED_STRINGS)
    return libro, get_rels_path(libro), (textos.PartName[1:] if textos is not None else None)


def hojas_del_xlsx(z) -> list:
    """[(nombre, ruta dentro del zip)] de las hojas de cálculo de un .xlsx
    abierto con zipfile, en el orden del libro, sin abrirlo con openpyxl.
    Las hojas de gráfico no cuentan: pandas lee la primera hoja de cálculo."""
    import posixpath
    from xml.etree import ElementTree as ET
    ns_main = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    ns_rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    libro, relaciones, _ = partes_del_xlsx(z)
    for parte in (libro, relaciones):
        if z.getinfo(parte).file_size > 2**20:
            raise ExcelDemasiadoGrande("El índice del Excel es demasiado grande.")
    carpeta = posixpath.dirname(libro)
    destinos = {}
    for r in ET.fromstring(z.read(relaciones)):
        if not (r.get("Type") or "").endswith("/worksheet"):
            continue
        destino = r.get("Target") or ""
        destino = destino.lstrip("/") if destino.startswith("/") else posixpath.normpath(posixpath.join(carpeta, destino))
        destinos[r.get("Id")] = destino
    hojas = []
    for h in ET.fromstring(z.read(libro)).iter(f"{ns_main}sheet"):
        if h.get(f"{ns_rel}id") in destinos:
            hojas.append((h.get("name") or "", destinos[h.get(f"{ns_rel}id")]))
    return hojas


def _mb_de_entorno(nombre: str, defecto: float) -> int:
    import math
    try:
        valor = float(os.getenv(nombre, "") or defecto)
    except (TypeError, ValueError):
        valor = defecto
    if not math.isfinite(valor) or valor <= 0:
        valor = defecto
    return int(valor * 1024 * 1024)


def _elementos_de_entorno() -> int:
    """EXCEL_MAX_ELEMENTOS_ESTILOS, 200.000 por defecto: unos 120 MB y 2,5 s
    al abrir. Excel no deja más de 64.000 formatos de celda."""
    import math
    try:
        valor = float(os.getenv("EXCEL_MAX_ELEMENTOS_ESTILOS", "") or 200_000)
    except (TypeError, ValueError):
        valor = 200_000.0
    return int(valor) if math.isfinite(valor) and valor > 0 else 200_000


def _mas_elementos_que(z, parte: str, tope: int) -> bool:
    """Cuenta las etiquetas que abren («<» y una letra) leyendo de a 1 MB, sin
    armar el árbol, y corta apenas pasa el tope. Puede contar de más (un «<x»
    dentro de un CDATA), nunca de menos."""
    import re
    abre = re.compile(rb"<[A-Za-z_]")
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


def _contar_hojas_xlsx(contents: bytes) -> int:
    """Cuenta las hojas desde xl/workbook.xml y mira, antes de abrir el libro,
    cuánto pesan los textos compartidos y la primera hoja: openpyxl los lee
    enteros al abrir, y un libro armado (millones de textos vacíos, una hoja
    enorme) tardaba minutos y usaba gigas de memoria (D26 a, EXCEL-2)."""
    import zipfile
    from openpyxl.xml.constants import ARC_CORE, ARC_CUSTOM, ARC_STYLE
    with zipfile.ZipFile(io.BytesIO(contents)) as z:
        hojas = hojas_del_xlsx(z)
        _, _, textos = partes_del_xlsx(z)
        nombres = set(z.namelist())
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
        if hojas and hojas[0][1] not in nombres:
            raise ValueError("falta la primera hoja dentro del archivo")
        tope_hoja = _mb_de_entorno("EXCEL_MAX_PRIMERA_HOJA_MB", 30)
        if hojas and z.getinfo(hojas[0][1]).file_size > tope_hoja:
            raise ExcelDemasiadoGrande(
                f"La primera hoja del Excel es demasiado grande (más de {tope_hoja // 2**20} MB). "
                "Dejá sólo los productos de la factura.")
        return len(hojas)


def _contar_hojas_excel(contents: bytes, file_ext: str) -> int:
    if file_ext == '.xlsx':
        return _contar_hojas_xlsx(contents)
    # El formato binario .xls no puede abrirse con openpyxl.
    # Pandas usa xlrd y alcanza con validar que exista alguna hoja.
    import pandas as pd
    return len(pd.ExcelFile(io.BytesIO(contents), engine='xlrd').sheet_names)


def _excel_max_descomprimido_bytes() -> int:
    """EXCEL_MAX_DESCOMPRIMIDO_MB, 100 por defecto (EXCEL-1)."""
    import math
    try:
        valor = float(os.getenv("EXCEL_MAX_DESCOMPRIMIDO_MB", "") or 100)
    except (TypeError, ValueError):
        valor = 100.0
    if not math.isfinite(valor) or valor <= 0:
        valor = 100.0
    return int(valor * 1024 * 1024)


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


def _abrir_excel(contents: bytes, file_ext: str) -> int:
    """Mira cuánto ocupa descomprimido y recién entonces cuenta las hojas.
    Corre en otro hilo: un zip con miles de entradas también tarda (EXCEL-1)."""
    if file_ext == '.xlsx' and _excel_descomprimido_bytes(contents) > _excel_max_descomprimido_bytes():
        raise ExcelDemasiadoGrande()
    return _contar_hojas_excel(contents, file_ext)


def _pdf_validate_timeout_s() -> float:
    """Mal escrito, en 0 o negativo, vale 30 s (RENDIMIENTO-1b)."""
    import math
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
        File contents as bytes

    Raises:
        HTTPException: If file is invalid

    Example:
        >>> contents = await validate_file_upload(uploaded_file, 'pdf')
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
    if file_type == 'excel':
        try:
            # Abrir el Excel es sincrónico: va en otro hilo y con tiempo máximo,
            # para que un archivo pesado no frene al resto (EXCEL-1).
            import asyncio
            try:
                hojas = await asyncio.wait_for(
                    asyncio.get_running_loop().run_in_executor(
                        _pool_validar_excel(), _abrir_excel, contents, file_ext
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

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, f"Invalid Excel file: {str(e)}")

    # Reset file pointer for later use
    await file.seek(0)

    return contents


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
