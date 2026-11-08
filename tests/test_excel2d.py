"""Un libro chico armado para costar segundos no traba el proceso.

openpyxl evalúa, al abrir, el formato de cada formato de celda (cellXfs) con
una expresión que crece con el cuadrado de los «[» y retiene el GIL: 120 000
«[» en 5 KB frenaban a todos los hilos 9 s. Antes de abrir, se rechaza un
formatCode de más de 255 caracteres o 32 «[», más de 65 490 formatos de celda
y más de 64 000 rangos en los sqref de la primera hoja. Las celdas
combinadas no tienen tope: rellenarlas cuesta lo mismo por fila.
"""
import re
import threading
import time
from xml.sax.saxutils import quoteattr

import pytest

from proyecto_maria.security import file_security as fs
from tests.test_excel2 import _subir
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


# Cada causa, justo en su tope y uno más. Con 65 490 formatos de celda el
# libro ya va al carril pesado (EXCEL_LIVIANO_ESTILOS). El libro normal ya
# trae un rango: el de la celda seleccionada.
CAUSAS = {
    "largo": (lambda: _con_formato("0" * 255), lambda: _con_formato("0" * 256), False),
    "corchetes": (lambda: _con_formato("[" * 32), lambda: _con_formato("[" * 33), False),
    "corchetes escritos como &#91;": (lambda: _con_referencias(32), lambda: _con_referencias(33), False),
    "formatos de celda": (lambda: _con_formato("0.00", 65_490), lambda: _con_formato("0.00", 65_491), True),
    "rangos": (lambda: _con_rangos(63_999), lambda: _con_rangos(64_000), False),
}


@pytest.mark.parametrize("causa", list(CAUSAS))
def test_un_formato_que_excel_no_guarda_se_rechaza(causa):
    justo, pasado, caro = CAUSAS[causa]
    assert fs._abrir_excel(justo(), ".xlsx") == (1, caro)
    with pytest.raises(fs.ExcelDemasiadoGrande, match="formato|rangos"):
        fs._abrir_excel(pasado(), ".xlsx")


@pytest.mark.parametrize("codigo", [
    "[$-409]d/m/yyyy h:mm AM/PM;@",
    "[Red][<=100]0.00;[Blue][>100]0.00;[Green]0;@",
    '#,##0.00 "USD";[Red]-#,##0.00 "USD"',
    "[h]:mm:ss",
])
def test_un_formato_de_excel_sigue_entrando(codigo):
    assert fs._abrir_excel(_con_formato(codigo), ".xlsx") == (1, False)


# Los libros del adversario: (libro, status, palabra del rechazo, segundos).
SUBIDAS = {
    "120 000 corchetes en un formato": (lambda: _con_formato("[" * 120_000), 400, "formato", 1),
    "2499 combinadas en 4998 filas": (lambda: _con_combinadas(4_998), 200, None, 3),
    "640 000 rangos de formato condicional": (lambda: _con_rangos(640_000), 400, "rangos", 1),
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
        r = _subir(libro)
    finally:
        listo.set()
        otro.join()
    assert r.status_code == status, r.text[:300]
    if palabra:
        assert palabra in r.json()["detail"]
    assert time.perf_counter() - inicio < segundos
    assert max(b - a for a, b in zip(pasos, pasos[1:])) < 0.5
