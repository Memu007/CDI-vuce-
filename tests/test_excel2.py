"""EXCEL-2 (2026-10-07): lo que el Excel todavía no leía, el CSV del historial
de NCM, el aviso de mapeo, abrir un libro armado (D26 a) y, de paso, montos
que no son números y los otros CUIT.
"""
import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main
from tests.test_maria1b_controles import _entorno, _errores, _generar  # noqa: F401
from tests.test_maria1b_devolucion import EXPORT


# ------------------------------------------- de paso: montos que no son números

ENORME = 10 ** 400  # un entero JSON: float() da OverflowError


@pytest.mark.parametrize("item, mensaje", [
    ({"cantidad": ENORME}, "Cantidad inválida"),
    ({"valor_unitario": ENORME}, "Valor inválido"),
    ({"peso_kg": ENORME}, "Peso inválido"),
    ({"cantidad": [1]}, "Cantidad inválida"),
    ({"valor_unitario": {"x": 1}}, "Valor inválido"),
])
def test_un_monto_que_no_es_un_numero_da_400(item, mensaje):
    assert mensaje in _errores(_generar(item=item))


@pytest.mark.parametrize("sub", [{"cantidad": ENORME}, {"valor_unitario": [5000]}])
def test_un_monto_de_subitem_que_no_es_un_numero_da_400(sub):
    subitems = [{"cantidad": 1, "valor_unitario": 5000, "sufijo": "AA(DEMO)-CA00-", **sub}]
    assert "sub-ítem 1" in _errores(_generar(item={"subitems": subitems}))


@pytest.mark.parametrize("cambio", [{"cantidad": ENORME}, {"valor_unitario": [1]}])
def test_la_exportacion_con_un_monto_que_no_es_un_numero_da_400(cambio):
    pedido = {**EXPORT, "items": [{**EXPORT["items"][0], **cambio}]}
    r = TestClient(main.app).post("/generate_maria_export", json=pedido)
    assert r.status_code == 400, r.text[:300]


# ------------------------------------------- de paso: los otros CUIT, sólo 0-9

@pytest.mark.parametrize("campo, valor", [
    ("cuit_agr", "２０１１１１１１１１２"),
    ("cuit_agr", "20111111١١2"),
    ("vendedor_id", "２０９９９９９９９９１"),
])
def test_cuit_del_despachante_o_id_del_vendedor_con_digitos_raros_no_deja_generar(campo, valor):
    errores = _errores(_generar(**{campo: valor}))
    assert "0-9" in errores, errores


def test_un_id_del_vendedor_extranjero_con_letras_sigue_pasando():
    r = _generar(vendedor_id="91320000MA1K3F2X5P")
    assert r.status_code == 200, r.text[:300]
