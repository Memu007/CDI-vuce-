"""MARIA-9: el sufijo de la operación se valida sólo si algún producto lo usa.

Si todos los renglones o sub-ítems traen su sufijo propio, el de la
operación no sale en el TXT: un texto libre ahí («ROJO») no frena la
generación. Cuando algún producto lo toma y no se puede separar, los avisos
lo anticipan con el mismo texto que el error. Datos inventados con la forma
de la factura de lonas.
"""
import pytest

from proyecto_maria.core import maria_generator as mg
from tests.test_maria7_rechazos_24_10 import LONA, _gen, _pedido, _registrar_con_cuit, _valor
from tests.test_maria8_subitems_por_posicion import _bloques, _lonas

LIBRE = "ROJO"
ERROR_GENERAL = "Sufijo de valor de la operación: «ROJO» no se puede separar"


def _sin_sufijo(renglon):
    return {k: v for k, v in renglon.items() if k != "sufijo"}


def _subitems(*sufijos):
    return dict(LONA, subitems=[
        dict({"cantidad": 375, "valor_unitario": 1.85}, **({"sufijo": s} if s else {}))
        for s in sufijos])


# Cada caso: los productos y si alguno toma el sufijo de la operación.
FAMILIA = {
    "renglones_con_propio": (lambda: _lonas(), False),
    "subitems_con_propio": (lambda: [_subitems("AA(A)-", "AA(B)-")], False),
    "renglones_y_subitems_con_propio": (lambda: _lonas()[:2] + [
        dict(_subitems("AA(A)-", "AA(B)-"), pieza="39211390900F")], False),
    "un_renglon_sin_propio": (lambda: _lonas()[:2] + [_sin_sufijo(_lonas()[2])], True),
    "un_subitem_sin_propio": (lambda: [_subitems("AA(A)-", None)], True),
    "propio_que_queda_vacio": (lambda: [_subitems("AA(A)-", " - ")], True),
    "item_entero": (lambda: [dict(LONA)], True),
    # Un ítem que sale entero lleva el suyo (SUFIJOS-1): no usa el de la operación.
    "item_entero_con_propio": (lambda: [dict(LONA, sufijo="AA(A)-")], False),
    "renglones_con_propio_y_un_item_entero": (lambda: _lonas()[:2] + [
        dict(LONA, pieza="39211390900F")], True),
}


@pytest.mark.parametrize("caso", FAMILIA)
def test_el_de_la_operacion_frena_sólo_si_alguien_lo_usa(caso):
    productos, lo_usa = FAMILIA[caso]
    if lo_usa:
        with pytest.raises(ValueError, match=ERROR_GENERAL):
            _gen(productos(), sbt_sufijo_valor=LIBRE)
    else:
        assert "[SBT]" in _gen(productos(), sbt_sufijo_valor=LIBRE)


@pytest.mark.parametrize("caso", FAMILIA)
def test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa(caso):
    productos, lo_usa = FAMILIA[caso]
    avisos = mg.supuestos_declarados(productos(), sbt_sufijo_valor=LIBRE)
    errores = [a for a in avisos if a.startswith(ERROR_GENERAL)]
    assert len(errores) == (1 if lo_usa else 0), avisos
    if lo_usa:
        # Es el mismo texto que el error: la pantalla lo pone bajo el campo.
        with pytest.raises(ValueError) as error:
            _gen(productos(), sbt_sufijo_valor=LIBRE)
        assert errores == [str(error.value)]


def test_con_sus_propios_salen_los_propios_y_no_el_de_la_operacion():
    sbts = _bloques(_gen(_lonas(), sbt_sufijo_valor=LIBRE), "SBT")
    assert [s["CSBTSVL"] for s in sbts] == [mg.limpiar_sufijo(r["sufijo"])[0] for r in _lonas()]


def test_un_propio_que_no_se_separa_da_su_error_y_no_el_de_la_operacion():
    productos = [_subitems("AA(A)-", "AA(B")]
    with pytest.raises(ValueError, match=r"^Sufijo de valor del ítem 1, sub-ítem 2:"):
        _gen(productos, sbt_sufijo_valor=LIBRE)
    assert not any(a.startswith(ERROR_GENERAL)
                   for a in mg.supuestos_declarados(productos, sbt_sufijo_valor=LIBRE))


def test_un_de_la_operacion_valido_no_da_aviso_de_error():
    avisos = mg.supuestos_declarados([dict(LONA)], sbt_sufijo_valor="AA(MARCA)-")
    assert not any("no se puede separar" in a for a in avisos)


# ------------------------------------------------------------------ por API


def _pedido_de_renglones(sufijo_general, con_propio=True):
    pedido = _pedido()
    base = pedido["items"][0]
    pedido["items"] = [dict(base, cantidad=10 + k, descripcion=f"Lona de PVC {k}",
                            **({"sufijo": f"AA(MARCA)-AI(COLOR {k})-"} if con_propio else {}))
                       for k in range(3)]
    pedido["sbt_sufijo_valor"] = sufijo_general
    return pedido


@pytest.mark.parametrize("general", [LIBRE, ""])
def test_por_api_los_renglones_con_propio_generan(client, general):
    _registrar_con_cuit(client, f"maria9_api_{general or 'vacio'}")
    r = client.post("/generate_maria", json=_pedido_de_renglones(general))
    assert r.status_code == 200, r.text
    assert _valor(r.json()["content"], "CSBTSVL") == [f"AA(MARCA)-AI(COLOR {k})-" for k in range(3)]


def test_por_api_sin_propio_el_de_la_operacion_sigue_frenando(client):
    _registrar_con_cuit(client, "maria9_api_sin_propio")
    r = client.post("/generate_maria", json=_pedido_de_renglones(LIBRE, con_propio=False))
    assert r.status_code == 400, r.text
    assert ERROR_GENERAL in r.text


def test_por_api_sin_ninguno_falta_el_sufijo(client):
    _registrar_con_cuit(client, "maria9_api_falta")
    r = client.post("/generate_maria", json=_pedido_de_renglones("", con_propio=False))
    assert r.status_code == 400, r.text
    assert "Falta el sufijo de valor SBT" in r.text


def test_por_api_los_avisos_anticipan_el_error(client):
    _registrar_con_cuit(client, "maria9_api_avisos")
    pedido = dict(_pedido(), sbt_sufijo_valor=LIBRE)
    r = client.post("/generate_maria/avisos", json=pedido)
    assert r.status_code == 200, r.text
    assert sum(a.startswith(ERROR_GENERAL) for a in r.json()["avisos"]) == 1
    r = client.post("/generate_maria/avisos", json=_pedido_de_renglones(LIBRE))
    assert r.status_code == 200, r.text
    assert not any(a.startswith(ERROR_GENERAL) for a in r.json()["avisos"])


def test_por_api_con_sufijo_en_cada_renglon_no_pide_el_de_la_operacion(client):
    # Cada renglón trae su sufijo, también el que toma la procedencia de la
    # operación: el endpoint no pide el sufijo de la operación.
    _registrar_con_cuit(client, "maria9_procedencia")
    pedido = _pedido()
    lona = dict(pedido["items"][0], estado=2)
    pedido["items"] = [dict(lona, pais_procedencia="UY", sufijo="AA(A)-"),
                       dict(lona, sufijo="AA(B)-", descripcion="Lona de PVC azul")]
    r = client.post("/generate_maria", json=dict(pedido, procedencia="UY", sbt_sufijo_valor=""))
    assert r.status_code == 200, r.text
    assert _valor(r.json()["content"], "CSBTSVL") == ["AA(A)-", "AA(B)-"]
