"""EXCEL-2c: el carril liviano mira la forma del libro, no sólo sus bytes.

Un libro de pocos KB puede pedir una fila lejana, muchas columnas, miles de
estilos o de textos: openpyxl tarda segundos en leerlo y no debe hacerlo en
los hilos livianos. Antes de leer se miden la fila y la columna máximas (por
las celdas, las filas y la <dimension>), los elementos de styles.xml y los
del sst; por encima de un tope, el libro va al carril pesado.
"""
import io
import re
import zipfile

import pytest

from proyecto_maria.security import file_security as fs
from tests.test_excel2 import _subir
from tests.test_excel2b import hilos  # noqa: F401  (fixture)
from tests.test_maria1b_devolucion import FILAS, _libro_normal

HOJA = "xl/worksheets/sheet1.xml"


def _normal():
    return _libro_normal({"Factura": FILAS})


def _cambiar(libro, cambios, extra=()):
    origen = zipfile.ZipFile(io.BytesIO(libro))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for info in origen.infolist():
            datos = origen.read(info)
            if info.filename in cambios:
                datos = cambios[info.filename](datos)
            z.writestr(info.filename, datos)
        for nombre, datos in extra:
            z.writestr(nombre, datos)
    return buf.getvalue()


def _con_filas(xml):
    """El libro normal con `xml` al final de sheetData."""
    return _cambiar(_normal(), {HOJA: lambda d: d.replace(b"</sheetData>", xml.encode() + b"</sheetData>")})


def _con_dimension(ref):
    return _cambiar(_normal(), {HOJA: lambda d: re.sub(rb'<dimension ref="[^"]*"\s*/>',
                                                       f'<dimension ref="{ref}"/>'.encode(), d)})


def _con_estilos(k):
    return _cambiar(_normal(), {"xl/styles.xml": lambda d: d.replace(b"</cellXfs>", b"<xf/>" * k + b"</cellXfs>")})


def _con_textos(k):
    """El libro normal con un sst de `k` entradas <si><t>x</t></si>."""
    tipos = (b'<Override PartName="/xl/sharedStrings.xml" ContentType="application/'
             b'vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/></Types>')
    relacion = (b'<Relationship Id="rIdS" Type="http://schemas.openxmlformats.org/officeDocument/'
                b'2006/relationships/sharedStrings" Target="sharedStrings.xml"/></Relationships>')
    sst = (b'<?xml version="1.0"?><sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
           + b"<si><t>x</t></si>" * k + b"</sst>")
    return _cambiar(_normal(), {"[Content_Types].xml": lambda d: d.replace(b"</Types>", tipos),
                                "xl/_rels/workbook.xml.rels": lambda d: d.replace(b"</Relationships>", relacion)},
                    extra=[("xl/sharedStrings.xml", sst)])


def _celda(ref):
    return f'<c r="{ref}" t="inlineStr"><is><t>x</t></is></c>'


# Cada forma, justo en el tope (liviano) y uno más (pesado). Los topes por
# defecto: 20 000 filas, 64 columnas, 5 000 elementos de estilos y 40 000
# del sst (dos por texto: <si> y <t>).
FORMAS = {
    "fila con r": (lambda: _con_filas(f'<row r="20000">{_celda("C20000")}</row>'),
                   lambda: _con_filas(f'<row r="20001">{_celda("C20001")}</row>')),
    "celda con r en una fila sin r": (lambda: _con_filas(f"<row>{_celda('C20000')}</row>"),
                                      lambda: _con_filas(f"<row>{_celda('C20001')}</row>")),
    "filas sin r": (lambda: _con_filas("<row/>" * 19_998), lambda: _con_filas("<row/>" * 19_999)),
    "dimension alta": (lambda: _con_dimension("A1:F20000"), lambda: _con_dimension("A1:F20001")),
    "columna con r": (lambda: _con_filas(f'<row r="3">{_celda("BL3")}</row>'),
                      lambda: _con_filas(f'<row r="3">{_celda("BM3")}</row>')),
    "celdas sin r": (lambda: _con_filas('<row r="3">' + "<c/>" * 64 + "</row>"),
                     lambda: _con_filas('<row r="3">' + "<c/>" * 65 + "</row>")),
    "dimension ancha": (lambda: _con_dimension("A1:BL2"), lambda: _con_dimension("A1:BM2")),
}


@pytest.mark.parametrize("forma", list(FORMAS))
def test_la_forma_del_libro_decide_el_carril(forma):
    justo, pasado = FORMAS[forma]
    assert fs._abrir_excel(justo(), ".xlsx") == (1, False)
    assert fs._abrir_excel(pasado(), ".xlsx") == (1, True)


def test_un_libro_normal_sigue_en_el_carril_liviano():
    assert fs._abrir_excel(_normal(), ".xlsx") == (1, False)


def test_muchos_estilos_van_al_carril_pesado():
    # El libro normal ya tiene unos cien elementos en styles.xml.
    assert fs._abrir_excel(_con_estilos(4_000), ".xlsx") == (1, False)
    assert fs._abrir_excel(_con_estilos(5_000), ".xlsx") == (1, True)


def test_muchos_textos_van_al_carril_pesado():
    # El sst suma su propio elemento <sst>: 19 999 textos son 39 999.
    assert fs._abrir_excel(_con_textos(19_999), ".xlsx") == (1, False)
    assert fs._abrir_excel(_con_textos(20_000), ".xlsx") == (1, True)


@pytest.mark.parametrize("libro", [
    lambda: _con_filas('<row r="x"/>'),
    lambda: _con_filas('<row r="inf"/>'),
    lambda: _con_filas('<row r="3"><c r="1A"/></row>'),
    lambda: _con_dimension("x!"),
], ids=["fila", "fila infinita", "celda", "dimension"])
def test_una_referencia_que_no_se_lee_va_al_carril_pesado(libro):
    """No se rechaza por eso: la lectura dirá si el libro sirve."""
    assert fs._abrir_excel(libro(), ".xlsx") == (1, True)


def test_la_dimension_ancha_no_rechaza_el_libro():
    """Excel guarda a veces A1:XFD1048576 aunque la hoja tenga seis
    columnas: lleva al carril pesado, no al rechazo de las 256 columnas."""
    assert fs._abrir_excel(_con_dimension("A1:XFD1048576"), ".xlsx") == (1, True)


def test_las_celdas_sin_r_cuentan_para_las_256_columnas():
    with pytest.raises(fs.ExcelDemasiadoGrande):
        fs._abrir_excel(_con_filas('<row r="3">' + "<c/>" * 257 + "</row>"), ".xlsx")
    assert fs._abrir_excel(_con_filas('<row r="3">' + "<c/>" * 256 + "</row>"), ".xlsx") == (1, True)


# ------------------------------------------------------------ los topes

_TOPES = {
    "EXCEL_LIVIANO_FILAS": ("2", lambda: _con_filas("<row/>")),
    "EXCEL_LIVIANO_COLUMNAS": ("6", lambda: _con_filas(f'<row r="3">{_celda("G3")}</row>')),
    "EXCEL_LIVIANO_ESTILOS": ("150", lambda: _con_estilos(100)),
    "EXCEL_LIVIANO_TEXTOS": ("10", lambda: _con_textos(5)),
}


@pytest.mark.parametrize("variable", list(_TOPES))
def test_el_tope_se_lee_del_entorno(monkeypatch, variable):
    valor, libro = _TOPES[variable]
    assert fs._abrir_excel(libro(), ".xlsx") == (1, False)
    monkeypatch.setenv(variable, valor)
    assert fs._abrir_excel(libro(), ".xlsx") == (1, True)


@pytest.mark.parametrize("valor", ["1e-9", "0.5", "inf", "nan", "-0", "0", "-3", "x"])
@pytest.mark.parametrize("variable", list(_TOPES))
def test_un_tope_que_no_sirve_vale_el_de_defecto(monkeypatch, variable, valor):
    _, libro = _TOPES[variable]
    monkeypatch.setenv(variable, valor)
    assert fs._abrir_excel(libro(), ".xlsx") == (1, False)
    assert fs._abrir_excel(FORMAS["fila con r"][1](), ".xlsx") == (1, True)


# ------------------------------------------------- de punta a punta: los hilos

def test_la_subida_con_una_fila_lejana_lee_en_los_hilos_pesados(hilos):  # noqa: F811
    _subir(FORMAS["fila con r"][1]())
    assert [q for q, _ in hilos] == ["validar", "leer"], hilos
    assert hilos[0][1].startswith("validar-excel-liviano"), hilos
    assert hilos[1][1].startswith("lectura-excel_"), hilos
