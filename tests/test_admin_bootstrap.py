"""Tests para el bootstrap de admin via ADMIN_USERNAMES en startup.

Verifica que cuando la app arranca, los usuarios definidos en ADMIN_USERNAMES
reciben el rol de admin, ya sea buscándolos por username o por email.
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


def test_bootstrap_admin_promotes_by_email(monkeypatch):
    """Setear ADMIN_USERNAMES=email@test.com → startup → user.roles incluye 'admin'."""
    monkeypatch.setenv("ADMIN_USERNAMES", "email@test.com")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DISABLE_DB_INIT", "true")
    
    with TestClient(app):
        pass
        
    roles = _run_async(_get_user_roles("admin_by_email"))
    assert "admin" in roles


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
