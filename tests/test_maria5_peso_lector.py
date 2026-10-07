"""MARIA-5, D22 (a): el lector le pide a Gemini el peso de una unidad y el de
la línea, y usa el que venga. Si viene sólo el total, lo divide por la
cantidad: el TXT multiplica el unitario por la cantidad y no se cuenta dos
veces. Las dos copias del lector, con Gemini falso.
"""
import pathlib

import pytest

from tests.test_maria1a_lectura_factura import COPIAS, _leer


def _leido(monkeypatch, copia, **peso):
    factura = {"operacion": {"numero_factura": "F-5"},
               "items": [dict({"descripcion": "Notebook", "cantidad": 10, "valor_unitario": 500, "origen": "CN"}, **peso)]}
    item = _leer(monkeypatch, copia, factura)["items"][0]
    return item["peso_unitario"], item["peso_total"]


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("peso, esperado", [
    ({"peso_total_linea": 25}, (2.5, 25)),
    ({"peso_unitario": 2.5}, (2.5, 25)),
    ({"peso_unitario": 2.5, "peso_total_linea": 25}, (2.5, 25)),
    ({"peso_total_linea": "25,0"}, (2.5, 25)),
    ({}, (0, 0)),
    ({"peso_total_linea": "N/A"}, (0, 0)),
])
def test_el_peso_que_venga_queda_por_unidad(monkeypatch, copia, peso, esperado):
    unitario, total = _leido(monkeypatch, copia, **peso)
    assert (unitario, total) == pytest.approx(esperado)


@pytest.mark.parametrize("copia", COPIAS)
def test_sin_cantidad_el_total_no_se_divide(monkeypatch, copia):
    factura = {"operacion": {}, "items": [{"descripcion": "Notebook", "valor_unitario": 500,
                                           "peso_total_linea": 25, "origen": "CN"}]}
    item = _leer(monkeypatch, copia, factura)["items"][0]
    assert item["peso_unitario"] == 0


@pytest.mark.parametrize("copia", COPIAS)
def test_el_total_leido_llega_al_txt_igual(monkeypatch, copia):
    """Factura con 10 unidades y 25 kg de la línea: el TXT declara 25 kg."""
    from tests.test_generar_maria_txt import _gen
    factura = {"operacion": {}, "items": [{"descripcion": "Notebook de prueba", "cantidad": 3,
                                           "valor_unitario": 500, "peso_total_linea": 10, "origen": "CN"}]}
    item = dict(_leer(monkeypatch, copia, factura)["items"][0], pieza="84713012")
    item.pop("peso_total")
    assert "QARTKGRNET=10.000" in _gen("OP_LECTOR", [item])


def test_el_prompt_pide_las_dos_cosas_en_las_dos_copias():
    texto = (pathlib.Path(__file__).resolve().parents[1] / "proyecto_maria" / "pdf_extractor.py").read_text()
    assert texto.count("- peso_unitario: Peso neto de UNA unidad") == 2
    assert texto.count("- peso_total_linea:") == 2
    assert "- peso_kg: Peso en kg" not in texto
