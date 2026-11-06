"""MARIA-1c: lo que la factura trae pero no se pudo leer se avisa.

El lector marca en `operacion.campos_sin_leer` el flete, el seguro o el país
del vendedor que venían en la factura pero no se pudieron leer (antes
quedaban en 0 o vacíos sin aviso). Un dato que no estaba no se marca.
Las dos copias del lector, con Gemini falso.
"""
import pathlib
import re

import pytest

from tests.test_maria1a_lectura_factura import COPIAS, _leer


def _factura(**operacion):
    return {"operacion": {"numero_factura": "F-1", **operacion},
            "items": [{"descripcion": "a", "cantidad": 2, "valor_unitario": 3, "peso_kg": 1, "origen": "CN"}]}


@pytest.mark.parametrize("copia", COPIAS)
def test_flete_y_seguro_ilegibles_se_marcan(monkeypatch, copia):
    r = _leer(monkeypatch, copia, _factura(flete="12x3", seguro="350 USD/kg"))
    op = r["operacion"]
    assert op["campos_sin_leer"] == ["flete", "seguro"]
    assert op["flete"] == 0 and op["seguro"] == 0


@pytest.mark.parametrize("copia", COPIAS)
def test_pais_del_vendedor_ilegible_se_marca(monkeypatch, copia):
    r = _leer(monkeypatch, copia, _factura(vendedor_pais="Narnia"))
    assert r["operacion"]["campos_sin_leer"] == ["vendedor_pais"]


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("operacion", [
    {},                                                    # no estaban
    {"flete": 0, "seguro": "", "vendedor_pais": None},     # vacíos en la factura
    {"flete": "1,250.50", "seguro": 35, "vendedor_pais": "CHN"},  # se leyeron
    {"vendedor_pais": "N/A"},                              # «no aplica»
], ids=["ausentes", "vacios", "leidos", "no_aplica"])
def test_lo_que_no_estaba_o_se_leyo_no_se_marca(monkeypatch, copia, operacion):
    r = _leer(monkeypatch, copia, _factura(**operacion))
    assert r["operacion"]["campos_sin_leer"] == []


