"""Tests de perfil de usuario y billing/me.

Cubren endpoints de main.py que no estaban testeados,
para llegar al threshold de cobertura >=38%."""
import pytest


def test_get_user_profile(auth_override, client):
    """GET /api/user/profile devuelve los datos del usuario logueado."""
    r = client.get("/api/user/profile")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["profile"]["username"] == "test_user"
    assert "email" in data["profile"]
    assert "plan" in data["profile"]


def test_update_user_profile_name(auth_override, client):
    """PUT /api/user/profile actualiza el nombre."""
    r = client.put("/api/user/profile", json={"name": "Nombre Test Actualizado"})
    assert r.status_code == 200
    assert r.json()["profile"]["name"] == "Nombre Test Actualizado"


def test_update_user_profile_cuit_valido(auth_override, client):
    """PUT /api/user/profile guarda CUIT normalizado (solo dígitos)."""
    r = client.put("/api/user/profile", json={"cuit": "20-111-22233-3"})
    assert r.status_code == 200
    assert r.json()["profile"]["cuit"] == "20111222333"


def test_update_user_profile_cuit_invalido_400(auth_override, client):
    """CUIT con != 11 dígitos → 400."""
    r = client.put("/api/user/profile", json={"cuit": "123"})
    assert r.status_code == 400


def test_update_user_profile_cuit_vacio_limpia(auth_override, client):
    """CUIT vacío limpia el campo."""
    r = client.put("/api/user/profile", json={"cuit": ""})
    assert r.status_code == 200


def test_update_user_profile_email_valido(auth_override, client):
    """PUT con email válido lo actualiza."""
    r = client.put("/api/user/profile", json={"email": "nuevo@test.com"})
    assert r.status_code == 200
    assert r.json()["profile"]["email"] == "nuevo@test.com"


def test_update_user_profile_email_invalido_400(auth_override, client):
    """PUT con email inválido → 400."""
    r = client.put("/api/user/profile", json={"email": "no-es-email"})
    assert r.status_code == 400


def test_update_user_profile_defaults(auth_override, client):
    """PUT con defaults de aduana/puerto/destinación."""
    r = client.put("/api/user/profile", json={
        "default_aduana_codigo": "073",
        "default_puerto_destino": "ARBUE",
        "default_tipo_destinacion": "IC04",
    })
    assert r.status_code == 200
    profile = r.json()["profile"]
    assert profile["default_aduana_codigo"] == "073"
    assert profile["default_puerto_destino"] == "ARBUE"
    assert profile["default_tipo_destinacion"] == "IC04"


def test_billing_me(auth_override, client):
    """GET /api/billing/me devuelve estado de billing."""
    r = client.get("/api/billing/me")
    assert r.status_code == 200
    data = r.json()
    assert "billing_status" in data
    assert "plan" in data


def test_user_profile_requires_auth(client):
    """GET /api/user/profile sin auth → 401."""
    r = client.get("/api/user/profile")
    assert r.status_code == 401


def test_billing_me_requires_auth(client):
    """GET /api/billing/me sin auth → 401."""
    r = client.get("/api/billing/me")
    assert r.status_code == 401


def test_simulate_charge_sin_metodo_pago(auth_override, client):
    """POST /api/billing/simulate-charge con billing_status=active → 409 (no cobrable)."""
    r = client.post("/api/billing/simulate-charge")
    # El usuario de test tiene billing_status=active, no es cobrable
    assert r.status_code == 409


def test_simulate_charge_sin_metodo_pago_trial(auth_override, client):
    """POST /api/billing/simulate-charge con trial pero sin método de pago → 400."""
    from proyecto_maria.database.connection import get_async_session
    from proyecto_maria.database.models import User
    from sqlalchemy import select
    import asyncio

    async def _set_trial():
        async for db in get_async_session():
            res = await db.execute(select(User).where(User.username == "test_user"))
            u = res.scalars().first()
            if u:
                u.billing_status = "trial"
                u.payment_method_last4 = None
                await db.commit()
            return
    asyncio.new_event_loop().run_until_complete(_set_trial())

    r = client.post("/api/billing/simulate-charge")
    assert r.status_code == 400

    # Restaurar a active
    async def _set_active():
        async for db in get_async_session():
            res = await db.execute(select(User).where(User.username == "test_user"))
            u = res.scalars().first()
            if u:
                u.billing_status = "active"
                await db.commit()
            return
    asyncio.new_event_loop().run_until_complete(_set_active())


def test_billing_me_devuelve_plan(auth_override, client):
    """GET /api/billing/me devuelve plan y límites."""
    r = client.get("/api/billing/me")
    assert r.status_code == 200
    data = r.json()
    assert "plan" in data
    assert "ops_limit" in data
    assert "clients_limit" in data
