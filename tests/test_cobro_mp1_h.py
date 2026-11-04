"""COBRO-MP-1, vuelta 3, h: el primer aviso de un pago no le cierra la
puerta al segundo.

Un pago de renovación llega dos veces: como `payment` y como
`subscription_authorized_payment` (el cobro). Si el que llega primero
todavía no sabe de qué cuenta es, no queda «rechazado» ni ocupa el
payment_id: 503, y Mercado Pago reintenta. La renovación se acredita una
vez, llegue en el orden que llegue (PARA-DEV.md, vuelta 2, h).

Mercado Pago simulado: ni el SDK real ni internet.
"""
from datetime import datetime, timedelta, timezone

import pytest

from tests.test_cobro_mp1 import (  # noqa: F401
    COBROS, PAGOS, SUSCRIPCIONES, _aviso_cobro, _aviso_ipn, _cobros, _fin, _leer_org, _leer_pago, _mp, _org,
    _renovacion, _sin_suscripciones,
)
from tests.test_prelaunch_block2 import _get_user, _register, _set_user, _unique, client  # noqa: F401


def _cuenta_vencida(client, tipo: str):
    """(usuario de la suscripción, referencia, lector del estado de la cuenta)."""
    usuario = _unique("h")
    _register(client, usuario)
    vencida = dict(billing_status="past_due", trial_ends_at=datetime.now(timezone.utc) - timedelta(days=3))
    if tipo == "usuario":
        _set_user(usuario, **vencida)
        return usuario, f"{usuario}:premium", lambda: _get_user(usuario)
    org_id = _org(usuario, **vencida)
    return usuario, f"org:{org_id}:premium", lambda: _leer_org(org_id)


def _renovacion_de(usuario: str, referencia: str, pago_dice: str, cobro_dice: str, estado_pago="approved"):
    # Un pago que dice su cuenta y no su suscripción se compara con el precio
    # del plan: la suscripción cobra ese mismo precio.
    monto = 45000.0 if pago_dice == "referencia" else 30000.0
    cobro, pid = _renovacion(usuario, monto=monto, estado_pago=estado_pago)
    pre = f"pre-{usuario}"
    SUSCRIPCIONES[pre]["external_reference"] = referencia
    SUSCRIPCIONES[pre]["auto_recurring"]["transaction_amount"] = monto
    if pago_dice == "metadata":
        PAGOS[pid]["metadata"] = {"preapproval_id": pre}
    elif pago_dice == "referencia":
        PAGOS[pid]["external_reference"] = referencia
    if cobro_dice == "nada":
        COBROS[cobro].pop("preapproval_id")
    return cobro, pid


def _acreditada_una_vez(leer, pid):
    cuenta = leer()
    assert cuenta["billing_status"] == "active", cuenta
    falta = _fin(cuenta) - datetime.now(timezone.utc)
    assert timedelta(days=29) < falta <= timedelta(days=30), f"no son 30 días desde hoy: {falta}"
    assert _leer_pago(pid).get("estado") == "aplicado", _leer_pago(pid)


@pytest.mark.parametrize("tipo", ["usuario", "organizacion"])
@pytest.mark.parametrize("orden", ["pago_primero", "cobro_primero"])
@pytest.mark.parametrize("pago_dice,cobro_dice", [
    ("nada", "suscripcion"), ("metadata", "suscripcion"), ("referencia", "suscripcion"),
    ("metadata", "nada"), ("referencia", "nada"),
], ids=["pago_sin_nada", "pago_con_metadata", "pago_con_referencia",
        "cobro_sin_suscripcion-pago_con_metadata", "cobro_sin_suscripcion-pago_con_referencia"])
def test_los_dos_avisos_de_una_renovacion_la_acreditan_una_vez(client, tipo, orden, pago_dice, cobro_dice):
    """Cada aviso que Mercado Pago reintenta (503) llega otra vez al final."""
    usuario, referencia, leer = _cuenta_vencida(client, tipo)
    cobro, pid = _renovacion_de(usuario, referencia, pago_dice, cobro_dice)
    avisos = [lambda: _aviso_ipn(client, pid), lambda: _aviso_cobro(client, cobro)]
    if orden == "cobro_primero":
        avisos.reverse()
    primero = avisos[0]()
    assert "rechazado" not in primero.json().get("skipped", ""), primero.json()
    if orden == "pago_primero" and pago_dice == "nada":
        # el pago solo no dice de quién es: no se anota nada
        assert primero.status_code == 503, primero.text[:300]
        assert _leer_pago(pid) == {}
        assert leer()["billing_status"] == "past_due"
    reintentar = [avisos[0]] if primero.status_code == 503 else []
    for aviso in [avisos[1], *reintentar]:
        r = aviso()
        assert r.status_code == 200, r.text[:300]
        assert "rechazado" not in r.json().get("skipped", ""), r.json()
    _acreditada_una_vez(leer, pid)


@pytest.mark.parametrize("tipo", ["usuario", "organizacion"])
def test_si_ningun_aviso_dice_de_quien_es_no_queda_rechazado(client, tipo):
    """Ni el cobro ni el pago dicen de qué cuenta es: los dos reintentan, y
    cuando el cobro lo dice se acredita."""
    usuario, referencia, leer = _cuenta_vencida(client, tipo)
    cobro, pid = _renovacion_de(usuario, referencia, "nada", "nada")
    for r in (_aviso_cobro(client, cobro), _aviso_ipn(client, pid)):
        assert r.status_code == 503, r.text[:300]
    assert _leer_pago(pid) == {}
    assert leer()["billing_status"] == "past_due"
    COBROS[cobro]["preapproval_id"] = f"pre-{usuario}"
    r = _aviso_cobro(client, cobro)
    assert r.status_code == 200 and r.json().get("skipped") is None, r.text[:300]
    _acreditada_una_vez(leer, pid)


@pytest.mark.parametrize("tipo", ["usuario", "organizacion"])
@pytest.mark.parametrize("pago_dice", ["nada", "metadata"], ids=["pago_sin_nada", "pago_con_metadata"])
@pytest.mark.parametrize("pendiente", ["pending", "in_process", "authorized"])
def test_un_cobro_con_el_pago_pendiente_no_se_pierde(client, tipo, pago_dice, pendiente):
    """El cobro llega con su pago todavía pendiente y después el pago se
    aprueba. Si el cobro contestara 200, no volvería: con un pago que solo no
    dice de quién es, la renovación se cobraría y no se acreditaría."""
    usuario, referencia, leer = _cuenta_vencida(client, tipo)
    cobro, pid = _renovacion_de(usuario, referencia, pago_dice, "suscripcion", estado_pago=pendiente)
    r = _aviso_cobro(client, cobro)
    assert r.status_code == 503, r.text[:300]
    assert _leer_pago(pid) == {}
    PAGOS[pid]["status"] = "approved"
    r = _aviso_ipn(client, pid)
    assert r.status_code == (200 if pago_dice == "metadata" else 503), r.text[:300]
    r = _aviso_cobro(client, cobro)
    assert r.status_code == 200, r.text[:300]
    _acreditada_una_vez(leer, pid)


def test_un_pago_sin_cuenta_que_otro_aviso_ya_aplico_no_reintenta_mas(client):
    """Después de que el cobro lo acreditó, el reintento del pago contesta
    200: si no, Mercado Pago lo reintentaría hasta rendirse."""
    usuario, referencia, leer = _cuenta_vencida(client, "usuario")
    cobro, pid = _renovacion_de(usuario, referencia, "nada", "suscripcion")
    assert _aviso_cobro(client, cobro).status_code == 200
    r = _aviso_ipn(client, pid)
    assert r.status_code == 200 and r.json().get("skipped") == "payment_id ya procesado", r.text[:300]
    _acreditada_una_vez(leer, pid)


@pytest.mark.parametrize("referencia", [None, "", 0, []], ids=["nula", "vacia", "cero", "lista"])
@pytest.mark.parametrize("aviso", ["pago", "cobro"])
def test_sin_referencia_ni_en_el_pago_ni_en_la_suscripcion_reintenta(client, aviso, referencia):
    """Antes: rechazado, y el otro aviso del mismo pago ya no entraba."""
    usuario, _, leer = _cuenta_vencida(client, "usuario")
    cobro, pid = _renovacion_de(usuario, referencia, "metadata", "suscripcion")
    PAGOS[pid]["external_reference"] = referencia
    r = _aviso_ipn(client, pid) if aviso == "pago" else _aviso_cobro(client, cobro)
    assert r.status_code == 503, r.text[:300]
    assert _leer_pago(pid) == {}
    assert leer()["billing_status"] == "past_due"


@pytest.mark.parametrize("referencia", [0, False, [], {}], ids=["cero", "falso", "lista", "objeto"])
@pytest.mark.parametrize("aviso", ["pago", "cobro"])
def test_una_referencia_vacia_de_otro_tipo_toma_la_de_la_suscripcion(client, aviso, referencia):
    usuario, buena, leer = _cuenta_vencida(client, "usuario")
    cobro, pid = _renovacion_de(usuario, buena, "metadata", "suscripcion")
    PAGOS[pid]["external_reference"] = referencia
    r = _aviso_ipn(client, pid) if aviso == "pago" else _aviso_cobro(client, cobro)
    assert r.status_code == 200 and r.json().get("skipped") is None, r.text[:300]
    _acreditada_una_vez(leer, pid)
