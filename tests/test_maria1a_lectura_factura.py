"""MARIA-1a: la factura bien leída, en las DOS copias del lector con Gemini.

- El país de origen sale bien con códigos de dos y tres letras y con el
  nombre, contra la tabla oficial VUCE. Antes se cortaba a dos letras:
  `CHN` → `CH` (Suiza), `MEX` → `ME` (Montenegro).
- Cantidades y precios con coma bien leídos; `1,500` sólo es mil quinientos
  si la misma factura muestra el punto como decimal. Si no se puede saber,
  queda vacío (0): nada adivinado.
- Un dato que falta queda vacío: ni peso 0,5 ni cantidad 1 ni origen del
  vendedor.

Copias: «pymupdf» (con PyMuPDF instalado, convierte a imagen) y
«pdf_directo» (sin PyMuPDF, la que corre hoy en producción). Gemini es
falso: ni Gemini real ni internet.
"""
import io
import json
import sys
import types

import pytest

from proyecto_maria import pdf_extractor
from proyecto_maria.core.maria_generator import get_pais_codigo


def _pdf_en_blanco() -> bytes:
    from PyPDF2 import PdfWriter

    w = PdfWriter()
    w.add_blank_page(width=595, height=842)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def _fitz_falso():
    """PyMuPDF falso: un PDF de una página que se «convierte» a imagen."""

    class _Pix:
        def tobytes(self, fmt):
            return b"\xff\xd8\xff\xd9"

    class _Pagina:
        def get_pixmap(self, matrix=None):
            return _Pix()

    class _Doc:
        def __len__(self):
            return 1

        def __getitem__(self, i):
            return _Pagina()

        def close(self):
            pass

    return types.SimpleNamespace(open=lambda **kw: _Doc(), Matrix=lambda a, b: None)


def _leer(monkeypatch, copia, respuesta):
    """Corre el lector con un Gemini falso que devuelve `respuesta`."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("ENABLE_PDF_LLM_FALLBACK", "true")
    monkeypatch.setattr("time.sleep", lambda s: None)

    class _Modelo:
        def __init__(self, nombre):
            pass

        def generate_content(self, partes):
            return types.SimpleNamespace(text=json.dumps(respuesta))

    falso = types.SimpleNamespace(configure=lambda **kw: None, GenerativeModel=_Modelo)
    google = sys.modules.get("google") or types.ModuleType("google")
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setattr(google, "generativeai", falso, raising=False)
    monkeypatch.setitem(sys.modules, "google.generativeai", falso)
    # «pdf_directo»: sin PyMuPDF (import fitz falla), como en producción.
    monkeypatch.setitem(sys.modules, "fitz", _fitz_falso() if copia == "pymupdf" else None)

    resultado = pdf_extractor.process_pdf(_pdf_en_blanco())
    assert isinstance(resultado, dict), f"el lector no devolvió datos: {resultado!r}"
    return resultado


COPIAS = ["pymupdf", "pdf_directo"]

FACTURA_EN_INGLES = {
    "operacion": {"numero_factura": "INV-1", "vendedor_pais": "CHN", "flete": "1,250.50"},
    "items": [
        {"descripcion": "a", "cantidad": "1,500", "valor_unitario": "2.45", "peso_kg": "0.20", "origen": "CHN"},
        {"descripcion": "b", "cantidad": 1.5, "valor_unitario": 2.45, "origen": "MEX"},
        {"descripcion": "c", "cantidad": "3", "valor_unitario": "10", "peso_kg": 1, "origen": "China"},
        {"descripcion": "d", "cantidad": "2", "valor_unitario": "1", "peso_kg": 1, "origen": "P.R. China"},
        {"descripcion": "e", "cantidad": "1", "valor_unitario": "1", "peso_kg": 1, "origen": "Narnia"},
        {"descripcion": "f", "cantidad": "1", "valor_unitario": "1"},
    ],
}


FACTURA_PAISES = {
    "operacion": {"numero_factura": "INV-2", "vendedor_pais": "CHN"},
    "items": [
        {"descripcion": d, "cantidad": 1, "valor_unitario": 1, "peso_kg": 1, **({"origen": o} if o else {})}
        for d, o in [("a", "CHN"), ("b", "MEX"), ("c", "China"), ("d", "P.R. China"), ("e", "Narnia"), ("f", None)]
    ],
}


@pytest.mark.parametrize("copia", COPIAS)
def test_pais_de_origen_contra_la_tabla_oficial(monkeypatch, copia):
    r = _leer(monkeypatch, copia, FACTURA_PAISES)
    origenes = [i["origen"] for i in r["items"]]

    assert origenes == ["CN", "MX", "CN", "CN", "", ""]
    # El código MARIA que sale en el TXT: China 310, México 218 (tabla VUCE).
    assert get_pais_codigo(origenes[0]) == 310
    assert get_pais_codigo(origenes[1]) == 218
    assert r["operacion"]["vendedor_pais"] == "CN"


@pytest.mark.parametrize("copia", COPIAS)
def test_numeros_de_una_factura_en_ingles(monkeypatch, copia):
    r = _leer(monkeypatch, copia, FACTURA_EN_INGLES)
    a, b = r["items"][0], r["items"][1]

    assert a["cantidad"] == 1500          # «1,500» con el punto como decimal en la factura
    assert a["valor_unitario"] == 2.45
    assert a["peso_unitario"] == 0.2
    assert b["cantidad"] == 1.5           # número del JSON, tal cual
    assert b["valor_unitario"] == 2.45
    assert r["operacion"]["flete"] == 1250.5


@pytest.mark.parametrize("copia", COPIAS)
def test_numeros_de_una_factura_en_castellano(monkeypatch, copia):
    factura = {
        "operacion": {"numero_factura": "F-1", "vendedor_pais": "AR"},
        "items": [
            {"descripcion": "a", "cantidad": "1,5", "valor_unitario": "2,45", "peso_kg": "0,2", "origen": "CN"},
            {"descripcion": "b", "cantidad": "1.500", "valor_unitario": "1.234,56", "peso_kg": "3", "origen": "CN"},
        ],
    }
    a, b = _leer(monkeypatch, copia, factura)["items"]

    assert (a["cantidad"], a["valor_unitario"], a["peso_unitario"]) == (1.5, 2.45, 0.2)
    assert (b["cantidad"], b["valor_unitario"]) == (1500, 1234.56)


@pytest.mark.parametrize("copia", COPIAS)
def test_si_no_se_puede_saber_queda_vacio(monkeypatch, copia):
    """«1,500» sin otra pista en la factura: puede ser 1,5 o 1500. Vacío."""
    factura = {
        "operacion": {"numero_factura": "F-2"},
        "items": [{"descripcion": "a", "cantidad": "1,500", "valor_unitario": "100", "origen": "CN"}],
    }
    r = _leer(monkeypatch, copia, factura)
    (a,) = r["items"]

    assert a["cantidad"] == 0
    assert a["valor_unitario"] == 100
    assert r["operacion"]["vendedor_pais"] == ""


@pytest.mark.parametrize("copia", COPIAS)
def test_lo_que_falta_no_se_inventa(monkeypatch, copia):
    r = _leer(monkeypatch, copia, FACTURA_EN_INGLES)
    b, f = r["items"][1], r["items"][5]

    assert b["peso_unitario"] == 0        # antes 0,5
    assert f["peso_unitario"] == 0
    assert f["origen"] == ""              # antes, el país del vendedor


@pytest.mark.parametrize("copia", COPIAS)
def test_cantidad_que_falta_queda_vacia(monkeypatch, copia):
    factura = {"operacion": {}, "items": [{"descripcion": "a", "valor_unitario": "5", "origen": "CN"}]}
    (a,) = _leer(monkeypatch, copia, factura)["items"]
    assert a["cantidad"] == 0             # antes 1


def test_instrucciones_a_gemini_no_piden_estimar_el_peso():
    import inspect

    fuente = inspect.getsource(pdf_extractor._extract_with_gemini_vision)
    assert "estimar 0.5" not in fuente


def test_tabla_tres_letras_apunta_a_la_tabla_oficial():
    from proyecto_maria.core.maria_generator import PAISES_INDEC, pais_reconocido
    from proyecto_maria.core.paises_iso3 import ISO3_A_ISO2

    assert len(ISO3_A_ISO2) > 150
    for tres, dos in ISO3_A_ISO2.items():
        assert len(tres) == 3 and len(dos) == 2
        assert dos in PAISES_INDEC and pais_reconocido(dos), (tres, dos)
    assert ISO3_A_ISO2["CHN"] == "CN" and ISO3_A_ISO2["MEX"] == "MX"
    assert ISO3_A_ISO2["CHE"] == "CH" and ISO3_A_ISO2["MNE"] == "ME"


@pytest.mark.parametrize(
    "texto",
    ["12x3", "10 x 20", "1/2", "1 1/2", "3 5", "5 kg 200 g", "500 g", "5 lb", "2.5e3",
     "1e999", "(1,500.00)", "1,500.00-", "-3", "nan", "-1.5"],
)
def test_lo_que_no_es_un_numero_limpio_queda_vacio(texto):
    """Mejor vacío que un valor equivocado: «12x3» no es 123 ni «500 g» 500 kg."""
    for decimal in (None, ".", ","):
        assert pdf_extractor._numero_factura(texto, decimal) is None, (texto, decimal)


@pytest.mark.parametrize("valor", [float("nan"), float("inf"), -5, -0.5])
def test_numeros_del_json_invalidos_quedan_vacios(valor):
    assert pdf_extractor._numero_factura(valor, None) is None


@pytest.mark.parametrize(
    "texto, esperado",
    [("1.500,00", 1500), ("1,500.00", 1500), ("1'500.00", 1500), ("1 500,00", 1500),
     ("€ 1.500,00", 1500), ("USD 2.45", 2.45), ("0,125", 0.125), ("12,5", 12.5)],
)
def test_numeros_limpios_se_siguen_leyendo(texto, esperado):
    assert pdf_extractor._numero_factura(texto, None) == esperado


def test_na_no_es_namibia():
    """«NA» en una factura casi siempre es «no aplica»: no se adivina Namibia."""
    assert pdf_extractor._origen_desde_factura("NA") == ""
    assert pdf_extractor._origen_desde_factura("N/A") == ""


@pytest.mark.parametrize("copia", COPIAS)
def test_un_item_raro_no_tira_la_factura(monkeypatch, copia):
    factura = {"operacion": None,
               "items": ["basura", {"descripcion": "a", "cantidad": 2, "valor_unitario": 1, "origen": "CN"}]}
    r = _leer(monkeypatch, copia, factura)
    assert [i["descripcion"] for i in r["items"]] == ["a"]


def test_la_copia_pymupdf_pide_los_numeros_tal_cual():
    """Si se le pide a Gemini «arreglar» 1.000 → 1000 y 0,50 → 0.50, mezcla
    formatos y la pista decimal de la factura sale falsa."""
    import inspect

    fuente = inspect.getsource(pdf_extractor._extract_with_gemini_vision)
    assert "fix formato" not in fuente and "fix: 0,50" not in fuente
