"""COBRO-MP-1, vuelta 3, i: lo que el aviso de pago deja en la cuenta y lo
que no deja pasar, cada cosa con su prueba (PARA-DEV.md, vuelta 2, i).

Mercado Pago simulado: ni el SDK real ni internet.
"""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from tests.test_cobro_mp1 import (  # noqa: F401
    PAGOS, SUSCRIPCIONES, _aviso_ipn, _fin, _leer_pago, _mp, _pago, _pago_de_suscripcion, _sin_suscripciones,
    _vencida,
)
from tests.test_prelaunch_block2 import _get_user, _register, _set_user, _unique, client  # noqa: F401


def _leer_usuario(usuario: str, *campos) -> dict:
    """Los campos que `_get_user` no devuelve."""
    from sqlalchemy.future import select

    from proyecto_maria.database.connection import get_async_session
    from proyecto_maria.database.models import User
    leido = {}

    async def _run():
        async for db in get_async_session():
            u = (await db.execute(select(User).where(User.username == usuario))).scalars().first()
            leido.update({c: getattr(u, c) for c in campos})
            return
    asyncio.new_event_loop().run_until_complete(_run())
    return leido


def _con_zona(fecha: datetime) -> datetime:
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


def _cerca(fecha, esperada: datetime) -> bool:
    return fecha is not None and abs((_con_zona(fecha) - esperada).total_seconds()) < 120


def _rechazado(pid: str, motivo: str):
    fila = _leer_pago(pid)
    assert fila.get("estado") == "rechazado" and motivo in (fila.get("motivo") or ""), fila


def test_pagar_el_plan_reinicia_la_cuota_del_periodo(client):
    """Sin esto, la cuenta paga y sigue bloqueada por la cuota del período
    anterior."""
    usuario = _unique("i_cuota")
    _register(client, usuario)
    _vencida(usuario)
    _set_user(usuario, ops_used_this_period=999,
              billing_period_started_at=datetime.now(timezone.utc) - timedelta(days=60))
    pid = _pago(f"pc-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["ops_used_this_period"] == 0, _get_user(usuario)
    inicio = _leer_usuario(usuario, "billing_period_started_at")["billing_period_started_at"]
    assert _cerca(inicio, datetime.now(timezone.utc)), inicio


def test_una_recarga_vence_a_los_30_dias(client):
    usuario = _unique("i_vence")
    _register(client, usuario)
    _set_user(usuario, extra_ops_remaining=0, extra_ops_expires_at=datetime.now(timezone.utc) - timedelta(days=5))
    pid = _pago(f"pt-{usuario}", f"{usuario}:topup", monto=10000.0)
    assert _aviso_ipn(client, pid).status_code == 200
    vence = _get_user(usuario)["extra_ops_expires_at"]
    if isinstance(vence, str):
        vence = datetime.fromisoformat(vence)
    assert _cerca(vence, datetime.now(timezone.utc) + timedelta(days=30)), vence


def test_pagar_durante_la_prueba_extiende_desde_el_fin(client):
    """La prueba gratis vigente también es tiempo pagado por adelantado: no
    se pierde al pagar."""
    usuario = _unique("i_trial")
    _register(client, usuario)
    fin = datetime.now(timezone.utc) + timedelta(days=20)
    _set_user(usuario, billing_status="trial", trial_ends_at=fin)
    pid = _pago(f"pp-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, pid).status_code == 200
    assert _cerca(_fin(_get_user(usuario)), fin + timedelta(days=30)), _get_user(usuario)


def test_el_tope_de_recargas_no_frena_un_plan(client):
    usuario = _unique("i_tope")
    _register(client, usuario)
    _vencida(usuario)
    _set_user(usuario, extra_ops_remaining=100, extra_ops_expires_at=datetime.now(timezone.utc) + timedelta(days=10))
    pid = _pago(f"pp-{usuario}", f"{usuario}:premium")
    assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "active", _get_user(usuario)
    assert _leer_pago(pid).get("estado") == "aplicado", _leer_pago(pid)


def test_una_suscripcion_de_monto_cero_no_se_aplica(client):
    usuario = _unique("i_cero")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago_de_suscripcion(usuario, 0.0)
    SUSCRIPCIONES[f"pre-1-{usuario}"]["auto_recurring"]["transaction_amount"] = 0
    assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"
    _rechazado(pid, "no tiene monto")


def test_un_link_con_precio_cero_se_compara_con_el_precio_de_hoy(client):
    """Un precio guardado de 0 no es un precio: un pago de 0 no activa."""
    usuario = _unique("i_link0")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pl-{usuario}", f"{usuario}:premium", monto=0.0)
    PAGOS[pid]["metadata"] = {"precio_esperado": 0}
    assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"
    _rechazado(pid, "el precio es 45000")


@pytest.mark.parametrize("moneda", ["ausente", None, ""])
def test_un_pago_sin_moneda_no_se_aplica(client, moneda):
    usuario = _unique("i_mon")
    _register(client, usuario)
    _vencida(usuario)
    pid = _pago(f"pm-{usuario}", f"{usuario}:premium")
    if moneda == "ausente":
        PAGOS[pid].pop("currency_id")
    else:
        PAGOS[pid]["currency_id"] = moneda
    assert _aviso_ipn(client, pid).status_code == 200
    assert _get_user(usuario)["billing_status"] == "past_due"
    _rechazado(pid, "no en ARS")


def test_se_guardan_los_ultimos_4_y_la_marca(client):
    usuario = _unique("i_tarj")
    _register(client, usuario)
    pid = _pago(f"pt-{usuario}", f"{usuario}:premium")
    PAGOS[pid]["card"] = {"last_four_digits": "123456789", "payment_method": {"name": "visa"}}
    assert _aviso_ipn(client, pid).status_code == 200
    tarjeta = _leer_usuario(usuario, "payment_method_last4", "payment_method_brand")
    assert tarjeta == {"payment_method_last4": "6789", "payment_method_brand": "visa"}, tarjeta
