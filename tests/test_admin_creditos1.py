"""Créditos que carga un admin: la regla de acreditar y el registro de cada carga."""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

from proyecto_maria.database.connection import AsyncSessionLocal, engine
from proyecto_maria.database.models import CreditoAdmin
from proyecto_maria.services import billing_service

AHORA = datetime(2026, 11, 21, 12, 0, tzinfo=timezone.utc)
ANTES = AHORA - timedelta(days=3)


def _cuenta(extra, vence):
    return SimpleNamespace(extra_ops_remaining=extra, extra_ops_expires_at=vence, last_topup_at=ANTES)


class _Reloj(datetime):
    @classmethod
    def now(cls, tz=None):
        return AHORA


# (extra, vencimiento, n, entra, vigentes_antes, extra después)
_CARGAS = [
    (0, None, 10, True, 0, 10),
    (None, None, 1, True, 0, 1),
    (90, AHORA + timedelta(days=5), 10, True, 90, 100),
    (91, AHORA + timedelta(days=5), 10, False, 91, 91),
    (5, AHORA - timedelta(seconds=1), 10, True, 0, 10),
    (95, AHORA - timedelta(days=1), 100, True, 0, 100),
    (0, None, 101, False, 0, 0),
]


@pytest.mark.parametrize("extra,vence,n,entra,antes,despues", _CARGAS)
def test_acreditar_extra(monkeypatch, extra, vence, n, entra, antes, despues):
    monkeypatch.setattr(billing_service, "datetime", _Reloj)
    cuenta = _cuenta(extra, vence)
    assert billing_service.acreditar_extra(cuenta, n, AHORA) == (entra, antes)
    assert (cuenta.extra_ops_remaining or 0) == despues
    if entra:
        assert cuenta.extra_ops_expires_at == AHORA + timedelta(days=30)
        assert cuenta.last_topup_at == AHORA
    else:
        assert cuenta.last_topup_at == ANTES


def test_recarga_entra_sin_n_sigue_siendo_una_recarga():
    assert billing_service.recarga_entra(_cuenta(100 - billing_service.TOPUP_OPS, None)) == (
        True, 100 - billing_service.TOPUP_OPS)
    assert billing_service.recarga_entra(_cuenta(101 - billing_service.TOPUP_OPS, None))[0] is False


async def _registrar(**fila):
    async with AsyncSessionLocal() as db:
        db.add(CreditoAdmin(**fila))
        await db.commit()


async def _filas(pedido):
    async with AsyncSessionLocal() as db:
        return (await db.execute(select(CreditoAdmin).where(CreditoAdmin.pedido == pedido))).scalars().all()


async def _borrar(pedido):
    async with AsyncSessionLocal() as db:
        for fila in (await db.execute(select(CreditoAdmin).where(CreditoAdmin.pedido == pedido))).scalars():
            await db.delete(fila)
        await db.commit()


def test_el_pedido_se_registra_una_sola_vez():
    pedido = str(uuid.uuid4())
    fila = dict(pedido=pedido, admin="adm", cuenta="org:1", usuario="u", cantidad=10, vigentes_antes=0)
    try:
        asyncio.run(_registrar(**fila))
        with pytest.raises(IntegrityError):
            asyncio.run(_registrar(**{**fila, "cuenta": "otra", "cantidad": 5}))
        [guardada] = asyncio.run(_filas(pedido))
        assert (guardada.cuenta, guardada.cantidad, guardada.admin) == ("org:1", 10, "adm")
        assert guardada.cargado_en is not None
    finally:
        asyncio.run(_borrar(pedido))


def test_la_tabla_no_tiene_claves_foraneas():
    async def mirar():
        async with engine.connect() as conn:
            return await conn.run_sync(lambda c: inspect(c).get_foreign_keys("creditos_admin"))
    assert asyncio.run(mirar()) == []
