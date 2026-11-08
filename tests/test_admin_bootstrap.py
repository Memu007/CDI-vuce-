"""Tests para el bootstrap de admin via ADMIN_USERNAMES en startup.

Verifica que cuando la app arranca, los usuarios definidos en ADMIN_USERNAMES
reciben el rol de admin por su username; un email no lo da.
"""
import pytest
import os
import asyncio
from fastapi.testclient import TestClient

from proyecto_maria.main import app, _admin_usernames
from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import User
from sqlalchemy import select, delete


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def _ensure_user(username, email, roles=None):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        if not user:
            user = User(
                username=username,
                password="hashed",
                email=email,
                name="Test",
                plan="premium",
                billing_status="active",
                is_verified=True,
                roles=roles or []
            )
            session.add(user)
        else:
            user.roles = roles or []
            user.email = email
        await session.commit()

async def _get_user_roles(username):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        return user.roles if user else []

@pytest.fixture(autouse=True)
def setup_users():
    _run_async(_ensure_user("admin_by_uname", "uname@test.com"))
    _run_async(_ensure_user("admin_by_email", "email@test.com"))
    _run_async(_ensure_user("admin_idempotent", "idem@test.com", roles=["admin"]))
    
    yield
    
    async def _cleanup():
        async with AsyncSessionLocal() as session:
            await session.execute(delete(User).where(User.username.in_(["admin_by_uname", "admin_by_email", "admin_idempotent"])))
            await session.commit()
    _run_async(_cleanup())


def test_bootstrap_admin_promotes_by_username(monkeypatch):
    """Setear ADMIN_USERNAMES=admin_by_uname → startup → user.roles incluye 'admin'."""
    monkeypatch.setenv("ADMIN_USERNAMES", "admin_by_uname")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DISABLE_DB_INIT", "true")
    
    # Run the app's lifespan to trigger the startup block
    with TestClient(app):
        pass
        
    roles = _run_async(_get_user_roles("admin_by_uname"))
    assert "admin" in roles


ADMIN_EMAIL = "jefe@estudio.test"


@pytest.mark.parametrize("en_admin_usernames, cuenta_previa", [
    (ADMIN_EMAIL, False),
    ("Jefe@Estudio.TEST", False),
    (f"  {ADMIN_EMAIL}  ", False),
    (ADMIN_EMAIL, True),
], ids=["tal_cual", "mayusculas", "espacios", "de_una_cuenta_borrada"])
def test_lo_que_puso_el_usuario_en_su_perfil_no_da_admin(monkeypatch, en_admin_usernames, cuenta_previa):
    """Quien pone en su perfil, como email o como nombre, algo de ADMIN_USERNAMES sigue sin admin al reiniciar."""
    from proyecto_maria.main import get_current_user

    async def _cuenta_borrada():
        async with AsyncSessionLocal() as session:
            session.add(User(username="se_fue_boot", password="x", email=ADMIN_EMAIL, roles=[]))
            await session.commit()
            await session.execute(delete(User).where(User.username == "se_fue_boot"))
            await session.commit()

    if cuenta_previa:
        _run_async(_cuenta_borrada())
    monkeypatch.setenv("ADMIN_USERNAMES", en_admin_usernames)
    monkeypatch.setenv("DISABLE_DB_INIT", "true")
    app.dependency_overrides[get_current_user] = lambda: {"username": "admin_by_email", "roles": []}
    try:
        r = TestClient(app).put("/api/user/profile", json={"email": ADMIN_EMAIL, "name": ADMIN_EMAIL})
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert r.status_code == 200, r.text[:200]

    with TestClient(app):
        pass

    assert "admin" not in _run_async(_get_user_roles("admin_by_email"))


def test_bootstrap_admin_idempotent(monkeypatch):
    """Correr con admin_idempotent que ya tiene el rol no duplica 'admin' en el array."""
    monkeypatch.setenv("ADMIN_USERNAMES", "admin_idempotent")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DISABLE_DB_INIT", "true")
    
    # It starts with exactly one "admin"
    roles_before = _run_async(_get_user_roles("admin_idempotent"))
    assert roles_before == ["admin"]
    
    with TestClient(app):
        pass
        
    roles_after = _run_async(_get_user_roles("admin_idempotent"))
    # Should still only have one "admin", not ["admin", "admin"]
    assert roles_after == ["admin"]
