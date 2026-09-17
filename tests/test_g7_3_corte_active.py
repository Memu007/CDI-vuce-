"""VUCE-3.1 — Corte por vencimiento de usuarios `active`, con 7 días de gracia.

Antes de este fix, un usuario `active` cuyo período venció pasaba el gate para
siempre (medido en VUCE-2: `can_create_operation` deja pasar a `active` sin mirar
`trial_ends_at`, y el cron/gate sólo cortaban `trial`). Eso dejaba servicio
ilimitado gratis a un estudio que dejó de pagar.

Decisión (PM, 2026-09-17): corte por calendario, con 7 días de gracia para
`active` (0 para `trial`), y razón del 402 distinguible.

Rojo previo: contra el commit anterior, `test_active_vencido_pasada_la_gracia_da_402`
falla (el `active` vencido pasa). Verde después.
"""
import asyncio
import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("EMAIL_VERIFICATION_REQUIRED", "false")

from proyecto_maria import main  # noqa: E402
from proyecto_maria.main import app  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _init_db_once():
    with TestClient(app) as _:
        pass
    yield


@pytest.fixture
def client():
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    return TestClient(app)


TEST_CARD = {"cardholder": "Test User", "number": "4242 4242 4242 4242", "exp": "12/30", "cvc": "123"}


def _register(client, username):
    resp = client.post("/auth/register", json={
        "username": username, "password": "originalpass123",
        "email": f"{username}@test.cdi", "name": f"User {username}",
        "payment_method": TEST_CARD,
    })
    assert resp.status_code in (200, 201), resp.text


async def _set_billing(username, status, dias_vencido, pago_previo=False):
    """Fija billing_status y trial_ends_at (dias_vencido>0 = en el pasado).

    pago_previo=True setea payment_provider="mercadopago", como lo hace el webhook
    real de MP cuando un usuario pagó al menos una vez (así el 402 lo marca como
    renovación impaga y no como trial vencido; el registro con tarjeta deja
    "simulated")."""
    from sqlalchemy.future import select
    from proyecto_maria.database.connection import get_async_session
    from proyecto_maria.database.models import User

    async for db in get_async_session():
        res = await db.execute(select(User).where(User.username == username))
        u = res.scalars().first()
        assert u is not None
        u.billing_status = status
        u.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=dias_vencido)
        if pago_previo:
            u.payment_provider = "mercadopago"
            u.payment_customer_id = "cus_test_g73"
        await db.commit()
        return


def _op(client):
    return client.post("/api/operations/manual", json={"client_id": "x", "items": []})


def _billing_status(client):
    return client.get("/api/billing/me").json()["billing_status"]


# ---- Gate: los tres casos que pidió la PM ----

def test_active_dentro_de_la_gracia_pasa(client):
    """active vencido hace 3 días → dentro de la gracia de 7 → pasa el gate."""
    u = "g73_active_gracia"
    _register(client, u)
    asyncio.new_event_loop().run_until_complete(_set_billing(u, "active", dias_vencido=3))
    resp = _op(client)
    assert resp.status_code != 402, resp.text          # el gate deja pasar
    assert resp.status_code == 400, resp.text           # cae recién en el body vacío
    assert _billing_status(client) == "active"          # no lo tocó


def test_active_pasada_la_gracia_da_402(client):
    """active vencido hace 10 días → pasada la gracia → 402 y queda past_due.

    Este es el rojo previo: contra el commit anterior, pasaba."""
    u = "g73_active_corte"
    _register(client, u)
    asyncio.new_event_loop().run_until_complete(
        _set_billing(u, "active", dias_vencido=10, pago_previo=True)
    )
    resp = _op(client)
    assert resp.status_code == 402, resp.text
    detail = resp.json()["detail"]
    # Pagó antes (payment_customer_id) → renovación impaga, distinguible del plan.
    assert detail["code"] == "SUBSCRIPTION_PAST_DUE", detail
    assert detail["billing_status"] == "past_due", detail
    assert _billing_status(client) == "past_due"


def test_active_vigente_no_se_toca(client):
    """active con período futuro → pasa, sin transición."""
    u = "g73_active_vigente"
    _register(client, u)
    asyncio.new_event_loop().run_until_complete(_set_billing(u, "active", dias_vencido=-5))  # +5d
    resp = _op(client)
    assert resp.status_code != 402, resp.text
    assert _billing_status(client) == "active"


def test_trial_vencido_sin_gracia_da_402_con_codigo_propio(client):
    """trial vencido → 402 sin gracia, con code TRIAL_EXPIRED (distinguible)."""
    u = "g73_trial_corte"
    _register(client, u)
    asyncio.new_event_loop().run_until_complete(_set_billing(u, "trial", dias_vencido=1))
    resp = _op(client)
    assert resp.status_code == 402, resp.text
    detail = resp.json()["detail"]
    assert detail["code"] == "TRIAL_EXPIRED", detail
    assert detail["billing_status"] == "past_due", detail


# ---- Cron de arranque: misma regla ----

def test_cron_corta_active_pasada_la_gracia_y_respeta_la_gracia(client):
    """_check_expired_trials pasa a past_due al active vencido >7d y deja al de 3d."""
    corta = "g73_cron_corta"
    gracia = "g73_cron_gracia"
    _register(client, corta)
    _register(client, gracia)
    loop = asyncio.new_event_loop()
    loop.run_until_complete(_set_billing(corta, "active", dias_vencido=10))
    loop.run_until_complete(_set_billing(gracia, "active", dias_vencido=3))

    loop.run_until_complete(main._check_expired_trials())

    from sqlalchemy.future import select
    from proyecto_maria.database.connection import get_async_session
    from proyecto_maria.database.models import User

    async def _read():
        async for db in get_async_session():
            res = await db.execute(select(User).where(User.username.in_([corta, gracia])))
            return {u.username: u.billing_status for u in res.scalars().all()}

    estados = loop.run_until_complete(_read())
    assert estados[corta] == "past_due", estados
    assert estados[gracia] == "active", estados
