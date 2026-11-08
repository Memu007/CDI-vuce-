"""Un libro chico armado para costar segundos no traba el proceso.

openpyxl y xlrd evalúan, al abrir, cada formato con una expresión que crece
con el cuadrado de los «[» y retiene el GIL: 120 000 «[» en 5 KB frenaban a
todos los hilos 9 s. Antes de abrir, se rechaza un formato de más de 32 «[»
(en un .xlsx, también de más de 255 caracteres), más de 65 490 formatos de
celda y más de 64 000 rangos en los sqref de la primera hoja. Las celdas
combinadas no tienen tope propio: el de filas las corta en ~1 s.
"""
import io
import re
import struct
import threading
import time
import tracemalloc
from xml.sax.saxutils import quoteattr

import pytest

from fastapi.testclient import TestClient

from proyecto_maria import main
from proyecto_maria.security import file_security as fs
from tests.test_excel2c import HOJA, _cambiar, _celda, _con_filas, _normal

ESTILOS = "xl/styles.xml"


def _con_formato(codigo, xfs=1):
    """El libro normal con un solo numFmt (164) y `xfs` formatos de celda que lo usan."""
    def cambiar(d):
        d = re.sub(rb"<numFmts[^>]*>.*?</numFmts>", b"", d, flags=re.S)
        d = d.replace(b"<fonts", b'<numFmts count="1"><numFmt numFmtId="164" formatCode='
                      + quoteattr(codigo).encode() + b"/></numFmts><fonts", 1)
        return re.sub(rb"<cellXfs[^>]*>.*?</cellXfs>",
                      f'<cellXfs count="{xfs}">'.encode() + b'<xf numFmtId="164"/>' * xfs + b"</cellXfs>",
                      d, flags=re.S)
    return _cambiar(_normal(), {ESTILOS: cambiar})


def _con_referencias(n):
    return _cambiar(_con_formato("0"), {ESTILOS: lambda d: d.replace(
        b'formatCode="0"', b'formatCode="' + b"&#91;" * n + b'"')})


def _tras_las_filas(libro, xml):
    return _cambiar(libro, {HOJA: lambda d: d.replace(b"</sheetData>", b"</sheetData>" + xml.encode())})


def _con_rangos(n):
    """Un formato condicional sobre `n` rangos de una celda."""
    rangos = " ".join(f"A{i}" for i in range(1, n + 1))
    return _tras_las_filas(_normal(), f'<conditionalFormatting sqref="{rangos}"><cfRule type="expression" '
                                      'priority="1"><formula>1</formula></cfRule></conditionalFormatting>')


def _con_combinadas(filas):
    """`filas` productos en la columna A, combinados de a dos filas hasta la F."""
    libro = _con_filas("".join(f'<row r="{i}">{_celda(f"A{i}")}</row>' for i in range(4, 4 + filas)))
    combinadas = [f'<mergeCell ref="A{i}:F{i + 1}"/>' for i in range(4, 3 + filas, 2)]
    return _tras_las_filas(libro, f'<mergeCells count="{len(combinadas)}">{"".join(combinadas)}</mergeCells>')


def _anidado(xfs):
    return _cambiar(_con_formato("0.00", xfs), {ESTILOS: lambda d: d.replace(
        b'<xf numFmtId="164"/>', b'<cellXfs/><xf numFmtId="164"/>', 1)})


def _xls(texto, registros=1, en_ole=True, cabecera=None):
    """Un .xls con `registros` FORMAT (BIFF8, 0x041E) de `texto`, en UTF-16 si no entra en
    latin-1; `cabecera` pisa (cuenta, bandera). xlwt corta cada registro en 8224 bytes, pero
    xlrd lee el largo de 16 bits."""
    xlwt = pytest.importorskip("xlwt")
    from xlwt.CompoundDoc import XlsDoc
    libro = xlwt.Workbook()
    libro.add_sheet("Factura").write(0, 0, "x")
    biff, salida = libro.get_biff_data(), bytearray()
    try:
        crudo, utf16 = texto.encode("latin-1"), 0
    except UnicodeEncodeError:
        crudo, utf16 = texto.encode("utf-16-le"), 1
    formato = struct.pack("<HHHHB", 0x041E, 5 + len(crudo), 200, *(cabecera or (len(texto), utf16))) + crudo
    pos = 0
    while pos < len(biff):
        tipo, largo = struct.unpack_from("<HH", biff, pos)
        registro = bytearray(biff[pos:pos + 4 + largo])
        if tipo == 0x0085:  # BOUNDSHEET guarda dónde empieza la hoja
            struct.pack_into("<I", registro, 4, struct.unpack_from("<I", registro, 4)[0]
                             + registros * len(formato))
        salida += registro + (formato * registros if pos == 0 else b"")
        pos += 4 + largo
    if not en_ole:
        return bytes(salida)
    with io.BytesIO() as buf:
        XlsDoc().save(buf, bytes(salida))
        return buf.getvalue()


# Cada causa, justo en su tope y uno más. Con 65 490 formatos de celda el
# libro ya va al carril pesado (EXCEL_LIVIANO_ESTILOS). El libro normal ya
# trae un rango: el de la celda seleccionada.
CAUSAS = {
    "largo": (lambda: _con_formato("0" * 255), lambda: _con_formato("0" * 256), False),
    "corchetes": (lambda: _con_formato("[" * 32), lambda: _con_formato("[" * 33), False),
    "corchetes escritos como &#91;": (lambda: _con_referencias(32), lambda: _con_referencias(33), False),
    "formatos de celda": (lambda: _con_formato("0.00", 65_490), lambda: _con_formato("0.00", 65_491), True),
    "formatos de celda tras un cellXfs sin hijos": (lambda: _anidado(65_490), lambda: _anidado(65_491), True),
    "rangos": (lambda: _con_rangos(63_999), lambda: _con_rangos(64_000), False),
    "corchetes en un .xls": (lambda: _xls("[" * 32), lambda: _xls("[" * 33), False),
    "corchetes en un .xls sin OLE": (lambda: _xls("[" * 32, en_ole=False), lambda: _xls("[" * 33, en_ole=False),
                                     False),
    "corchetes en UTF-16 en un .xls": (lambda: _xls("€" + "[" * 32), lambda: _xls("€" + "[" * 33), False),
    "largo en un .xls": (lambda: _xls("0" * 255), lambda: _xls("0" * 256), False),
    "corchetes en un FORMAT de .xls que no cuadra": (lambda: _xls("[" * 32, cabecera=(0, 1)),
                                                     lambda: _xls("[" * 33, cabecera=(0, 1)), False),
}


@pytest.mark.parametrize("causa", list(CAUSAS))
def test_un_formato_que_excel_no_guarda_se_rechaza(causa):
    justo, pasado, caro = CAUSAS[causa]
    tipo = ".xls" if ".xls" in causa else ".xlsx"
    assert fs._abrir_excel(justo(), tipo) == (1, caro)
    with pytest.raises(fs.ExcelDemasiadoGrande, match="formato|rangos"):
        fs._abrir_excel(pasado(), tipo)


@pytest.mark.parametrize("codigo", [
    "[$-409]d/m/yyyy h:mm AM/PM;@",
    "[Red][<=100]0.00;[Blue][>100]0.00;[Green]0;@",
    '#,##0.00 "USD";[Red]-#,##0.00 "USD"',
    "[h]:mm:ss",
    '0 "' + "字" * 40 + '"',  # en UTF-16, cada 字 lleva un byte 0x5B, el de «[»
], ids=["fecha", "colores", "moneda", "horas", "texto chino"])
def test_un_formato_de_excel_sigue_entrando(codigo):
    assert fs._abrir_excel(_con_formato(codigo), ".xlsx") == (1, False)
    assert fs._abrir_excel(_xls(codigo), ".xls") == (1, False)


def test_un_sqref_largo_se_parte_hasta_el_tope():
    # Partirlo entero arma 640 000 textos: ~46 MB de pico, contra ~27 MB.
    libro = _con_rangos(640_000)
    tracemalloc.start()
    try:
        with pytest.raises(fs.ExcelDemasiadoGrande, match="rangos"):
            fs._abrir_excel(libro, ".xlsx")
        pico = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert pico < 35_000_000, pico


# Los libros del adversario: (libro, status, palabra del rechazo, segundos).
SUBIDAS = {
    "120 000 corchetes en un formato": (lambda: _con_formato("[" * 120_000), 400, "formato", 1),
    "2499 combinadas en 4998 filas": (lambda: _con_combinadas(4_998), 200, None, 3),
    "9995 combinadas en 19 990 filas": (lambda: _con_combinadas(19_990), 400, "filas", 3),
    "640 000 rangos de formato condicional": (lambda: _con_rangos(640_000), 400, "rangos", 1),
    "tres formatos de 60 000 corchetes en un .xls": (lambda: _xls("[" * 60_000, 3), 400, "formato", 1),
}


@pytest.mark.parametrize("subida", list(SUBIDAS))
def test_la_subida_cara_no_frena_a_nadie(subida):
    libro, status, palabra, segundos = SUBIDAS[subida]
    libro = libro()
    assert len(libro) < 1_500_000
    # Otro hilo marca el paso: con el GIL retenido por openpyxl se quedaba 9 s.
    pasos, listo = [time.perf_counter()], threading.Event()

    def marcar():
        while not listo.is_set():
            time.sleep(0.01)
            pasos.append(time.perf_counter())
    otro = threading.Thread(target=marcar)
    otro.start()
    inicio = time.perf_counter()
    try:
        nombre = "factura.xls" if ".xls" in subida else "factura.xlsx"
        r = TestClient(main.app).post("/upload_excel_v2/", files={"file": (nombre, libro)})
    finally:
        listo.set()
        otro.join()
    assert r.status_code == status, r.text[:300]
    if palabra:
        assert palabra in r.json()["detail"]
    assert time.perf_counter() - inicio < segundos
    assert max(b - a for a, b in zip(pasos, pasos[1:])) < 0.5
