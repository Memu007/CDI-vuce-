"""COBRO-MP-1: el aviso de pago de Mercado Pago se aplica una sola vez.

Pasos 1 y 3 del plan (PARA-PM.md):
1. Cada pago se aplica una vez: alternar dos pagos viejos reales (el ataque
   de D8, por el aviso IPN sin firma) no renueva ni suma recargas.
3. Un pago de plan extiende el período desde su fin, si la cuenta sigue
   activa, en vez de fijar 30 días desde hoy.

Mercado Pago simulado: ni el SDK real ni internet.
"""
import json
from datetime import datetime, timedelta, timezone

import pytest

from tests.test_prelaunch_block2 import _get_user, _register, _set_user, _unique, client  # noqa: F401

PAGOS: dict = {}


class _Pagos:
    def get(self, pid):
        return {"status": 200, "response": PAGOS[str(pid)]}


class _SDK:
    def __init__(self, token):
        pass

    def payment(self):
        return _Pagos()


@pytest.fixture(autouse=True)
def _mp(monkeypatch):
    import proyecto_maria.main as main_mod
    monkeypatch.setattr(main_mod, "MP_WEBHOOK_SECRET", "secreto-de-prueba")
    monkeypatch.setattr(main_mod, "IS_PRODUCTION", False)
    monkeypatch.setattr(main_mod, "MP_ACCESS_TOKEN", "TEST-fake")
    monkeypatch.setattr(main_mod.mercadopago, "SDK", _SDK)
    PAGOS.clear()


def _pago(pid: str, referencia: str, monto: float = 45000.0) -> str:
    PAGOS[pid] = {"id": pid, "status": "approved", "external_reference": referencia,
                  "transaction_amount": monto, "currency_id": "ARS", "payer": {"id": "payer-1"}}
    return pid


def _aviso_ipn(client, pid: str):
    """El aviso IPN, sin firma: cualquiera lo puede mandar sin sesión."""
    client.cookies.clear()
    return client.post(f"/api/payments/webhook?topic=payment&id={pid}")


def _fin(usuario: dict) -> datetime:
    fin = usuario["trial_ends_at"]
    if isinstance(fin, str):
        fin = datetime.fromisoformat(fin)
    return fin if fin.tzinfo else fin.replace(tzinfo=timezone.utc)


def test_alternar_dos_pagos_viejos_no_renueva(client):
    """El ataque de D8: con dos pagos reales ya aplicados, alternarlos dejaba
    la cuenta vencida otra vez activa 30 días y con el contador en 0."""
    usuario = _unique("mp1_alt")
    _register(client, usuario)
    a = _pago(f"pa-{usuario}", f"{usuario}:premium")
    b = _pago(f"pb-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, a).status_code == 200
    assert _aviso_ipn(client, b).status_code == 200

    vencida = datetime.now(timezone.utc) - timedelta(days=40)
    _set_user(usuario, billing_status="past_due", trial_ends_at=vencida, ops_used_this_period=999)
    for pid in (a, b, a, b):
        r = _aviso_ipn(client, pid)
        assert r.status_code == 200, r.text[:300]
    despues = _get_user(usuario)
    assert despues["billing_status"] == "past_due", despues
    assert despues["ops_used_this_period"] == 999, despues


def test_una_recarga_reenviada_no_suma_operaciones(client):
    usuario = _unique("mp1_rec")
    _register(client, usuario)
    t = _pago(f"pt-{usuario}", f"{usuario}:topup", monto=10000.0)
    u = _pago(f"pu-{usuario}", f"{usuario}:premium")
    for pid in (t, u):
        assert _aviso_ipn(client, pid).status_code == 200
    extra = _get_user(usuario)["extra_ops_remaining"]
    for pid in (t, u, t):
        assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["extra_ops_remaining"] == extra


def test_el_pago_aplicado_queda_registrado(client):
    from proyecto_maria.database.models import PagoMercadoPagoAplicado  # noqa: F401
    from tests.test_prelaunch_block2 import asyncio
    from proyecto_maria.database.connection import AsyncSessionLocal
    from sqlalchemy.future import select

    usuario = _unique("mp1_reg")
    _register(client, usuario)
    pid = _pago(f"pr-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, pid).status_code == 200

    async def _leer():
        async with AsyncSessionLocal() as db:
            fila = (await db.execute(select(PagoMercadoPagoAplicado).where(
                PagoMercadoPagoAplicado.payment_id == pid))).scalar_one()
            return fila.cuenta, fila.tipo, float(fila.monto), fila.moneda
    assert asyncio.new_event_loop().run_until_complete(_leer()) == (usuario, "premium", 45000.0, "ARS")


def test_pagar_con_la_cuenta_activa_extiende_desde_el_fin(client):
    """Pagar antes de que venza no pierde los días que quedaban."""
    usuario = _unique("mp1_ext")
    _register(client, usuario)
    fin_actual = datetime.now(timezone.utc) + timedelta(days=20)
    _set_user(usuario, billing_status="active", plan="premium", trial_ends_at=fin_actual)
    pid = _pago(f"pe-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, pid).status_code == 200
    nuevo = _fin(_get_user(usuario))
    assert abs((nuevo - (fin_actual + timedelta(days=30))).total_seconds()) < 120, nuevo


def test_pagar_con_la_cuenta_vencida_cuenta_desde_hoy(client):
    usuario = _unique("mp1_ven")
    _register(client, usuario)
    _set_user(usuario, billing_status="past_due", trial_ends_at=datetime.now(timezone.utc) - timedelta(days=10))
    pid = _pago(f"pv-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, pid).status_code == 200
    despues = _get_user(usuario)
    assert despues["billing_status"] == "active"
    falta = _fin(despues) - datetime.now(timezone.utc)
    assert timedelta(days=29) < falta <= timedelta(days=30), falta
