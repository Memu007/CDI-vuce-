"""Tests E2E del flujo de billing autoservicio (T9, Sprint 25 Día 5).

Cubre los 3 endpoints nuevos + cambio de password:
- POST /api/user/change-password (OK + 401 con pass actual mala + 400 short)
- POST /api/billing/cancel (OK desde trial/active + 409 desde none/canceled)
- POST /api/billing/reactivate (vigente → active, vencido → past_due+needs_checkout)

NO testea integración real con MercadoPago (sandbox requerido). Eso vive en
manual smoke. Acá nos concentramos en la lógica de estado autoservicio.
"""
import os
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("EMAIL_VERIFICATION_REQUIRED", "false")

from proyecto_maria.main import app  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _init_db_once():
    """Dispara el lifespan una vez para crear tablas (la conftest global usa un
    archivo temporal compartido, así múltiples conexiones ven los datos)."""
    with TestClient(app) as _:
        pass
    yield


@pytest.fixture
def client():
    """TestClient con rate limiter apagado y cookies aisladas por test."""
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    return TestClient(app)


# Tarjeta Luhn-valida y no-vencida que aceptan billing_sim.validate_and_detect.
TEST_CARD = {
    "cardholder": "Test User",
    "number": "4242 4242 4242 4242",
    "exp": "12/30",
    "cvc": "123",
}


def _register(client, username: str, with_card: bool = True):
    """Helper: registra un user (con o sin tarjeta) y deja la cookie en el client."""
    payload = {
        "username": username,
        "password": "originalpass123",
        "email": f"{username}@test.cdi",
        "name": f"User {username}",
    }
    if with_card:
        payload["payment_method"] = TEST_CARD
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code in (200, 201), f"register fallo: {resp.status_code} {resp.text}"
    return resp.json()


def _get_billing(client) -> dict:
    """Helper: lee el estado actual de billing del user logueado."""
    resp = client.get("/api/billing/me")
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------- Cambio de password ----------


def test_change_password_ok(client):
    """Cambio de pass con la actual correcta → 200 + login con la nueva funciona."""
    _register(client, "userpass1", with_card=False)
    resp = client.post("/api/user/change-password", json={
        "current_password": "originalpass123",
        "new_password": "nuevapass456",
    })
    assert resp.status_code == 200, resp.text
    assert resp.json()["success"] is True

    # Logout (limpiar cookie) + login con la pass nueva debe funcionar.
    client.cookies.clear()
    login = client.post("/auth/login", json={
        "username": "userpass1",
        "password": "nuevapass456",
    })
    assert login.status_code == 200, login.text


def test_change_password_wrong_current_returns_401(client):
    """Si la pass actual es incorrecta → 401 (defensa session-hijack)."""
    _register(client, "userpass2", with_card=False)
    resp = client.post("/api/user/change-password", json={
        "current_password": "passwordIncorrecta",
        "new_password": "nuevapass456",
    })
    assert resp.status_code == 401
    assert "incorrecta" in resp.json()["detail"].lower()


def test_change_password_too_short_returns_400(client):
    """Pass nueva con < 8 chars → 400."""
    _register(client, "userpass3", with_card=False)
    resp = client.post("/api/user/change-password", json={
        "current_password": "originalpass123",
        "new_password": "abc",
    })
    assert resp.status_code == 400
    assert "8 caracteres" in resp.json()["detail"]


def test_change_password_same_as_current_returns_400(client):
    """Pass nueva == actual → 400 (no es un cambio real)."""
    _register(client, "userpass4", with_card=False)
    resp = client.post("/api/user/change-password", json={
        "current_password": "originalpass123",
        "new_password": "originalpass123",
    })
    assert resp.status_code == 400


# ---------- Cancelar plan ----------


def test_cancel_from_trial_keeps_service_until_trial_end(client):
    """Cancelar desde trial → status='canceled' pero trial_ends_at se mantiene."""
    _register(client, "cancel1", with_card=True)
    before = _get_billing(client)
    assert before["billing_status"] == "trial"
    assert before["trial_ends_at"] is not None
    trial_end_before = before["trial_ends_at"]

    resp = client.post("/api/billing/cancel")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["billing_status"] == "canceled"
    # Servicio sigue activo hasta esa fecha (clave: NO corta al toque).
    assert body["service_until"] == trial_end_before


def test_cancel_from_none_returns_409(client):
    """Sin plan activo (registro sin tarjeta) → 409, nada que cancelar."""
    _register(client, "cancel2", with_card=False)
    
    # Mockear billing_status a "none" en la DB para este test (Ola 4 registra trial por defecto)
    import asyncio
    from sqlalchemy.future import select
    from proyecto_maria.database.connection import get_async_session
    from proyecto_maria.database.models import User

    async def _set_billing_status_none():
        async for db in get_async_session():
            res = await db.execute(select(User).where(User.username == "cancel2"))
            u = res.scalars().first()
            assert u is not None
            u.billing_status = "none"
            await db.commit()
            return

    asyncio.new_event_loop().run_until_complete(_set_billing_status_none())
    
    resp = client.post("/api/billing/cancel")
    assert resp.status_code == 409


def test_cancel_twice_returns_409(client):
    """Cancelar dos veces seguidas → la segunda 409 (ya canceled)."""
    _register(client, "cancel3", with_card=True)
    first = client.post("/api/billing/cancel")
    assert first.status_code == 200
    second = client.post("/api/billing/cancel")
    assert second.status_code == 409


# ---------- Reactivar plan ----------


def test_reactivate_with_active_period_returns_active(client):
    """Cancelar y reactivar mientras el trial sigue vigente → vuelve a active."""
    _register(client, "react1", with_card=True)
    cancel = client.post("/api/billing/cancel")
    assert cancel.status_code == 200

    resp = client.post("/api/billing/reactivate")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["billing_status"] == "active"
    assert body["needs_checkout"] is False


def test_reactivate_when_not_canceled_returns_409(client):
    """Reactivar sin haber cancelado → 409."""
    _register(client, "react2", with_card=True)
    resp = client.post("/api/billing/reactivate")
    assert resp.status_code == 409


def test_reactivate_after_period_expired_returns_past_due_and_needs_checkout(client):
    """Si trial_ends_at ya venció al reactivar → past_due + needs_checkout=True.

    Forzamos trial_ends_at al pasado vía DB direct para no esperar 15 días.
    """
    _register(client, "react3", with_card=True)
    cancel = client.post("/api/billing/cancel")
    assert cancel.status_code == 200

    # Vencer el período manualmente en DB.
    import asyncio
    from sqlalchemy.future import select
    from proyecto_maria.database.connection import get_async_session
    from proyecto_maria.database.models import User

    async def _expire_trial():
        async for db in get_async_session():
            res = await db.execute(select(User).where(User.username == "react3"))
            u = res.scalars().first()
            assert u is not None
            u.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=1)
            await db.commit()
            return

    asyncio.new_event_loop().run_until_complete(_expire_trial())

    resp = client.post("/api/billing/reactivate")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["billing_status"] == "past_due"
    assert body["needs_checkout"] is True


# ---------- Auth obligatoria en todos los endpoints ----------


def test_change_password_requires_auth(client):
    """Sin cookie → 401 (no se filtra info de hash)."""
    client.cookies.clear()
    resp = client.post("/api/user/change-password", json={
        "current_password": "x",
        "new_password": "yyyyyyyy",
    })
    assert resp.status_code == 401


def test_cancel_requires_auth(client):
    client.cookies.clear()
    resp = client.post("/api/billing/cancel")
    assert resp.status_code == 401


def test_reactivate_requires_auth(client):
    client.cookies.clear()
    resp = client.post("/api/billing/reactivate")
    assert resp.status_code == 401
