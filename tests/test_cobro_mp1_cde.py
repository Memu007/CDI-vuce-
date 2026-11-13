"""COBRO-MP-1, C y E (PARA-DEV.md, devolución del 2026-10-28).

C: desde past_due se puede cancelar. Si quedó una suscripción en Mercado
Pago, se cancela allá (si no, cobra cuando la tarjeta vuelve); la cuenta
queda «canceled» y no gana acceso por cancelar.

D13 (c): con una suscripción autorizada y la cuenta no vigente, el checkout
no la cancela por su cuenta: puede ser un pago recién hecho cuyo aviso
todavía no llegó. Contesta 409 y la salida es cancelar el plan.

E: reactivar una prueba que sólo hizo una recarga vuelve a la prueba con
sus días, como una prueba sin recarga. La recarga no es un plan pagado.

Mercado Pago simulado con la infraestructura de COBRO-MP-2.
"""
import json
import types
from datetime import datetime, timedelta, timezone

import pytest

from proyecto_maria.services import billing_service
from tests.test_cobro_mp1 import _org
from tests.test_cobro_mp2 import (  # noqa: F401
    CREADAS, PAGOS, PEDIDOS, SUS, _aviso_pago, _cerca, _fin, _leer, _mp, _pago, _suscripto,
)
from tests.test_prelaunch_block2 import _get_user, _register, _set_user, _unique, client  # noqa: F401


def _puts_cancelar(sid: str) -> list:
    return [p for p in PEDIDOS if p.method == "PUT" and p.url.path.endswith(f"/preapproval/{sid}")]


def _con_acceso(usuario: dict) -> bool:
    return billing_service.tiene_acceso(types.SimpleNamespace(
        billing_status=usuario["billing_status"], trial_ends_at=_fin(usuario)))


# --- C: cancelar desde past_due ---

@pytest.mark.parametrize("dias", [-10, 10], ids=["vencida", "con_dias"])
@pytest.mark.parametrize("con_suscripcion", [True, False], ids=["con_suscripcion", "sin_suscripcion"])
def test_desde_past_due_se_cancela_y_no_gana_acceso(client, dias, con_suscripcion):
    usuario, sid = _suscripto(client, "cde_pd", billing_status="past_due", dias=dias)
    if not con_suscripcion:
        _set_user(usuario, mp_preapproval_id=None)
    r = client.post("/api/billing/cancel")
    assert r.status_code == 200, f"past_due no se puede cancelar: {r.status_code} {r.text}"
    despues = _leer(usuario)
    assert despues["billing_status"] == "canceled", despues
    assert despues["mp_preapproval_id"] is None, despues
    if con_suscripcion:
        assert _puts_cancelar(sid), "cancelar desde past_due no cancela la suscripción en Mercado Pago"
        assert SUS[sid] == "cancelled"
    else:
        assert not _puts_cancelar(sid)
    assert not _con_acceso(despues), f"cancelar desde past_due da acceso: {despues}"


def test_past_due_cancelada_al_reactivar_va_al_checkout(client):
    _suscripto(client, "cde_pdre", billing_status="past_due", dias=10)
    assert client.post("/api/billing/cancel").status_code == 200
    r = client.post("/api/billing/reactivate")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["billing_status"] == "past_due", cuerpo
    assert cuerpo["needs_checkout"] is True, cuerpo


def test_si_mp_no_cancela_past_due_queda_como_estaba(client):
    from tests.test_cobro_mp2 import FALLA, _contesta_500
    usuario, sid = _suscripto(client, "cde_pd500", billing_status="past_due", dias=-3)
    FALLA["PUT"] = _contesta_500
    r = client.post("/api/billing/cancel")
    assert r.status_code == 503, r.text
    despues = _leer(usuario)
    assert despues["billing_status"] == "past_due", despues
    assert despues["mp_preapproval_id"] == sid


# --- E: reactivar una prueba que hizo una recarga ---

def _entrar(client, usuario: str) -> None:
    # el aviso de Mercado Pago llega sin sesión: _aviso_pago borra las cookies
    r = client.post("/auth/login", json={"username": usuario, "password": "SecureP@ss1"})
    assert r.status_code == 200, r.text


def _recargar(client, usuario: str) -> None:
    pid = _pago(f"rec-{usuario}", f"{usuario}:topup", monto=float(billing_service.TOPUP_PRICE_ARS))
    assert _aviso_pago(client, pid).status_code == 200
    assert _get_user(usuario)["extra_ops_remaining"], "la recarga no se aplicó"


def test_reactivar_una_prueba_con_recarga_vuelve_a_la_prueba(client):
    usuario = _unique("cde_prueba_rec")
    _register(client, usuario)
    _recargar(client, usuario)
    fin = _fin(_leer(usuario))
    _entrar(client, usuario)
    assert client.post("/api/billing/cancel").status_code == 200
    r = client.post("/api/billing/reactivate")
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    texto = json.dumps(cuerpo, ensure_ascii=False)
    assert cuerpo["billing_status"] == "trial", f"una prueba con recarga no vuelve a la prueba: {texto}"
    assert cuerpo["needs_checkout"] is False, texto
    assert "ya pagado" not in texto, texto
    despues = _leer(usuario)
    assert despues["billing_status"] == "trial", despues
    assert _cerca(_fin(despues), fin)


def test_un_plan_pagado_con_recarga_sigue_yendo_al_checkout(client):
    usuario = _unique("cde_plan_rec")
    _register(client, usuario)
    plan = _pago(f"plan-{usuario}", f"{usuario}:premium")
    assert _aviso_pago(client, plan).status_code == 200
    assert _get_user(usuario)["billing_status"] == "active"
    _recargar(client, usuario)
    _entrar(client, usuario)
    assert client.post("/api/billing/cancel").status_code == 200
    cuerpo = client.post("/api/billing/reactivate").json()
    assert cuerpo["billing_status"] == "canceled", cuerpo
    assert cuerpo["needs_checkout"] is True, cuerpo


def test_una_cuenta_vieja_pagada_sin_registro_sigue_yendo_al_checkout(client):
    # Pagó antes de que existiera mp_pagos_aplicados: no tiene filas.
    _suscripto(client, "cde_vieja")
    assert client.post("/api/billing/cancel").status_code == 200
    cuerpo = client.post("/api/billing/reactivate").json()
    assert cuerpo["billing_status"] == "canceled", cuerpo
    assert cuerpo["needs_checkout"] is True, cuerpo


def test_una_cuenta_vieja_pagada_con_un_pago_rechazado_sigue_yendo_al_checkout(client):
    # El aviso de un pago de antes del registro (el IPN va sin firma: lo
    # puede mandar cualquiera que sepa el id) deja una fila rechazada. Un
    # rechazo no dice nada del plan: decide payment_provider, como sin filas.
    usuario, _ = _suscripto(client, "cde_vieja_rech")
    viejo = _pago(f"viejo-{usuario}", f"{usuario}:premium")
    PAGOS[viejo]["date_approved"] = "2020-03-01T10:00:00.000-03:00"
    assert _aviso_pago(client, viejo).status_code == 200
    _entrar(client, usuario)
    assert client.post("/api/billing/cancel").status_code == 200
    cuerpo = client.post("/api/billing/reactivate").json()
    assert cuerpo["billing_status"] == "canceled", f"una cuenta pagada volvió como prueba: {cuerpo}"
    assert cuerpo["needs_checkout"] is True, cuerpo


def test_una_prueba_con_un_pago_de_plan_rechazado_vuelve_a_la_prueba(client):
    # La otra cara: un plan rechazado (monto que no cierra) tampoco es un plan.
    usuario = _unique("cde_prueba_rech")
    _register(client, usuario)
    pid = _pago(f"rech-{usuario}", f"{usuario}:premium", monto=1.0)
    assert _aviso_pago(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "trial", "el pago de 1 peso se aplicó"
    _entrar(client, usuario)
    assert client.post("/api/billing/cancel").status_code == 200
    cuerpo = client.post("/api/billing/reactivate").json()
    assert cuerpo["billing_status"] == "trial", f"un plan rechazado cuenta como plan: {cuerpo}"
    assert cuerpo["needs_checkout"] is False, cuerpo


# --- Cancelar una suscripción nueva abierta desde «canceled» ---

def test_cancelada_que_abrio_el_checkout_puede_cancelar_la_suscripcion_nueva(client):
    # Reactivar un plan pagado deja «canceled» hasta que se pague; si el
    # checkout ya creó la suscripción y el primer cobro no entra, cancelar
    # tiene que cancelarla en Mercado Pago (si no, cobra cuando la tarjeta
    # vuelve y la cuenta no tiene cómo frenarla).
    usuario, sid = _suscripto(client, "cde_canre")
    assert client.post("/api/billing/cancel").status_code == 200
    fin = _fin(_leer(usuario))
    assert client.post("/api/billing/reactivate").json()["needs_checkout"] is True
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 200, r.text
    nueva = r.json()["preapproval_id"]
    SUS[nueva] = "authorized"
    assert _leer(usuario)["mp_preapproval_id"] == nueva

    r = client.post("/api/billing/cancel")
    assert r.status_code == 200, f"la suscripción nueva no se puede cancelar: {r.status_code} {r.text}"
    despues = _leer(usuario)
    assert SUS[nueva] == "cancelled", "cancelar no cancela en Mercado Pago la suscripción del checkout"
    assert despues["billing_status"] == "canceled", despues
    assert despues["mp_preapproval_id"] is None, despues
    assert _cerca(_fin(despues), fin), f"cancelar otra vez movió el fin del período pagado: {despues}"


def test_cancelada_sin_suscripcion_no_se_cancela_otra_vez(client):
    usuario, sid = _suscripto(client, "cde_candos")
    assert client.post("/api/billing/cancel").status_code == 200
    pedidos = len(PEDIDOS)
    r = client.post("/api/billing/cancel")
    assert r.status_code == 409, r.text
    assert len(PEDIDOS) == pedidos, "cancelar dos veces vuelve a llamar a Mercado Pago"


@pytest.mark.parametrize("estado, con_suscripcion, abierta, corta", [
    ("canceled", True, True, False), ("canceled", False, False, False), ("active", True, True, False),
    ("past_due", True, True, True), ("none", True, True, True), ("none", False, False, True),
    (None, True, True, True), ("desconocido", True, True, True),
], ids=["cancelada_con_checkout", "cancelada_sin", "activa", "impaga", "sin_plan_con", "sin_plan_sin",
        "sin_estado", "desconocido"])
def test_billing_me_dice_si_hay_una_suscripcion_abierta(client, estado, con_suscripcion, abierta, corta):
    # Con una suscripción abierta el perfil muestra «Cancelar plan», sea cual
    # sea el estado: si no, el 409 del checkout no tiene salida. Con 20 días
    # pagos, cancelar sólo los conserva quien hoy tiene acceso.
    usuario, sid = _suscripto(client, "cde_me", billing_status=estado)
    if not con_suscripcion:
        _set_user(usuario, mp_preapproval_id=None)
    r = client.get("/api/billing/me")
    assert r.status_code == 200, r.text
    assert r.json().get("suscripcion_abierta") is abierta, r.json()
    assert r.json().get("cancelar_corta_acceso") is corta, r.json()


@pytest.mark.parametrize("de_la_org, de_la_fila, corta", [
    (("past_due", -10), ("trial", 10), True), (("active", 20), ("past_due", -30), False),
    (None, ("past_due", -30), True), (None, ("active", 20), False),
], ids=["org_impaga_fila_en_prueba", "org_activa_fila_impaga", "sin_org_impaga", "sin_org_activa"])
def test_cancelar_avisa_por_la_cuenta_que_da_el_acceso(client, de_la_org, de_la_fila, corta):
    # Con organización, el acceso y la pantalla salen de la organización, no
    # de la fila del usuario: el aviso de cancelar tiene que mirar la misma.
    usuario, sid = _suscripto(client, "cde_org", billing_status=de_la_fila[0], dias=de_la_fila[1])
    if de_la_org:
        estado, dias = de_la_org
        org_id = _org(usuario, billing_status=estado, plan="premium",
                      trial_ends_at=datetime.now(timezone.utc) + timedelta(days=dias))
        _set_user(usuario, organization_id=org_id)
    perfil = client.get("/api/billing/me").json()
    assert perfil.get("cancelar_corta_acceso") is corta, f"el perfil promete otra cosa: {perfil}"


# --- D13 (c): una autorizada vieja no se cancela desde el checkout ---

@pytest.mark.parametrize("billing_status, dias, corta", [
    ("past_due", -10, True), ("active", -1, True), ("active", -3, True), ("canceled", 20, False),
    ("none", 10, True), (None, 10, True), ("expired", -5, True), ("desconocido", 10, True),
], ids=["impaga", "renovacion_tardia", "vencida_en_gracia", "cancelada_vieja",
        "sin_plan", "sin_estado", "expired", "desconocido"])
def test_sin_cuenta_vigente_una_autorizada_frena_el_checkout_y_sale_cancelando(client, billing_status, dias, corta):
    usuario, sid = _suscripto(client, "cde_d13", billing_status=billing_status, dias=dias)
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 409, r.text
    assert "cancelá el plan primero" in r.json()["detail"], r.json()
    assert _puts_cancelar(sid) == [], PEDIDOS
    assert CREADAS == []
    assert SUS[sid] == "authorized"
    assert _leer(usuario)["mp_preapproval_id"] == sid

    # La salida que nombra el 409: cancelar desde el perfil y volver a pagar.
    # El perfil avisa antes lo que cancelar va a hacer con el acceso.
    perfil = client.get("/api/billing/me").json()
    assert perfil.get("cancelar_corta_acceso") is corta, f"el perfil promete otra cosa: {perfil}"
    r = client.post("/api/billing/cancel")
    assert r.status_code == 200, r.text
    assert SUS[sid] == "cancelled"
    despues = _leer(usuario)
    assert _con_acceso(despues) is not corta, f"cancelar dejó otro acceso (corta={corta}): {despues}"
    assert (r.json()["service_until"] is None) is corta, f"servicio hasta: {r.json()}"
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 200, r.text
    assert [t for t, _ in CREADAS] == ["preapproval"]
    assert _leer(usuario)["mp_preapproval_id"] == r.json()["preapproval_id"] != sid


# --- j: una suscripción que Mercado Pago no conoce no traba la cuenta ---

def test_si_mp_no_conoce_la_suscripcion_vieja_el_checkout_crea_la_nueva(client):
    usuario, sid = _suscripto(client, "cde_404", billing_status="past_due", dias=-10)
    del SUS[sid]  # Mercado Pago contesta 404
    r = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert r.status_code == 200, r.text
    assert [t for t, _ in CREADAS] == ["preapproval"]
    assert _leer(usuario)["mp_preapproval_id"] == r.json()["preapproval_id"] != sid


def test_si_mp_no_conoce_la_suscripcion_cancelar_sigue(client):
    usuario, sid = _suscripto(client, "cde_404c")
    del SUS[sid]
    r = client.post("/api/billing/cancel")
    assert r.status_code == 200, r.text
    assert _leer(usuario)["billing_status"] == "canceled"
    assert _leer(usuario)["mp_preapproval_id"] is None
