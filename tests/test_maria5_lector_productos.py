"""MARIA-5, punto 3 (revisión de MARIA-1d): las dos copias del lector tratan
igual la descripción, la versión y el código de parte de cada producto.

Antes, en la copia de PDF directo (la que usa producción), «None» o «N/A»
quedaban escritos y un 0 quedaba vacío; la versión no se leía. Gemini falso.
"""
import pytest

from tests.test_maria1a_lectura_factura import COPIAS, _leer


def _producto(**campos):
    base = {"cantidad": 2, "valor_unitario": 3, "peso_kg": 1, "origen": "CN"}
    return {"operacion": {"numero_factura": "F-5"}, "items": [dict(base, **campos)]}


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("vacio", ["None", "null", "N/A", " none ", None])
def test_el_vacio_no_queda_escrito(monkeypatch, copia, vacio):
    item = _leer(monkeypatch, copia, _producto(
        descripcion="Equipo de prueba", version=vacio, codigo_parte=vacio))["items"][0]
    assert item["descripcion"] == "Equipo de prueba"
    assert item.get("codigo_parte", "") == ""


@pytest.mark.parametrize("copia", COPIAS)
def test_descripcion_vacia_escrita_queda_vacia(monkeypatch, copia):
    item = _leer(monkeypatch, copia, _producto(descripcion="N/A", version="None"))["items"][0]
    assert item["descripcion"] == ""


@pytest.mark.parametrize("copia", COPIAS)
def test_un_cero_no_se_pierde(monkeypatch, copia):
    item = _leer(monkeypatch, copia, _producto(descripcion=0, codigo_parte=0))["items"][0]
    assert (item["descripcion"], item["codigo_parte"]) == ("0", "0")


@pytest.mark.parametrize("copia", COPIAS)
def test_la_version_se_suma_a_la_descripcion(monkeypatch, copia):
    item = _leer(monkeypatch, copia, _producto(
        descripcion="Válvula esférica", version="DN15 PN10", codigo_parte=" VX-15 "))["items"][0]
    assert (item["descripcion"], item["codigo_parte"]) == ("Válvula esférica DN15 PN10", "VX-15")


@pytest.mark.parametrize("copia", COPIAS)
def test_solo_la_version(monkeypatch, copia):
    item = _leer(monkeypatch, copia, _producto(descripcion=None, version="Negra"))["items"][0]
    assert item["descripcion"] == "Negra"


def test_las_dos_copias_dan_lo_mismo(monkeypatch):
    factura = _producto(descripcion=" Bomba ", version="1HP", codigo_parte=12345)
    claves = ("descripcion", "codigo_parte")
    a, b = ({k: _leer(monkeypatch, c, factura)["items"][0].get(k) for k in claves} for c in COPIAS)
    assert a == b
