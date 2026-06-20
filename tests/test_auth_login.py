"""Tests para el bug P0 de login: JWT sub debe ser user.username, no el input.

Cubre:
- Login con username → JWT.sub == username → /api/auth/current_user 200
- Login con email → JWT.sub == username (NO email) → /api/auth/current_user 200
- Email inexistente → 401
- Password incorrecta → 401
- Rate limit después de 5 fails → 429
"""
import pytest
import jwt as pyjwt
import asyncio

from proyecto_maria.main import app, login_attempts, hash_password, SECRET_KEY, ALGORITHM
from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import User
from sqlalchemy import select, delete


# ── helpers ──────────────────────────────────────────────────────────

def _run_async(coro):
    """Ejecuta una coroutine en un loop nuevo (compatible con Python 3.12+)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _ensure_login_test_user(username="logintest", email="logintest@example.com",
                                   password="Correct1!"):
    """Crea (o actualiza) un usuario de prueba con contraseña bcrypt."""
    hashed = hash_password(password)
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        if user:
            user.password = hashed
            user.email = email
            user.is_verified = True
        else:
            user = User(
                username=username,
                password=hashed,
                email=email,
                name="Login Test User",
                plan="premium",
                billing_status="active",
                is_verified=True,
            )
            session.add(user)
        await session.commit()


async def _cleanup_login_test_user(username="logintest"):
    async with AsyncSessionLocal() as session:
        await session.execute(delete(User).where(User.username == username))
        await session.commit()


# ── fixtures ─────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clean_rate_limits():
    """Limpiar rate limits entre tests para que no interfieran."""
    login_attempts.clear()
    yield
    login_attempts.clear()


@pytest.fixture(autouse=True)
def _setup_user():
    """Crea el usuario de prueba antes de cada test y lo limpia después."""
    _run_async(_ensure_login_test_user())
    yield
    _run_async(_cleanup_login_test_user())


# ── tests ────────────────────────────────────────────────────────────
# Usamos el fixture `client` del conftest.py que ya tiene TestClient
# configurado (rate limiter deshabilitado, ENVIRONMENT=testing).
# IMPORTANTE: limpiamos dependency_overrides para que get_current_user
# sea el real (no el fake del auth_override).

def test_login_with_username(client):
    """Login con username → JWT.sub == username → current_user 200."""
    # Limpiar overrides para usar auth real
    app.dependency_overrides.clear()

    resp = client.post("/auth/login", json={
        "username": "logintest",
        "password": "Correct1!",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    token = data["access_token"]

    # Decodificar JWT y verificar sub == username (no email)
    payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "logintest"

    # Usar el token para llamar a /auth/current_user
    resp2 = client.get(
        "/auth/current_user",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["username"] == "logintest"


def test_login_with_email(client):
    """Login con email → JWT.sub == username (NO email) → current_user 200.

    ESTE ES EL CASO DEL BUG: antes generaba sub=email y get_current_user
    buscaba por User.username → 401.
    """
    app.dependency_overrides.clear()

    resp = client.post("/auth/login", json={
        "username": "logintest@example.com",  # email en el campo username
        "password": "Correct1!",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    token = data["access_token"]

    # JWT.sub DEBE ser el username, no el email
    payload = pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "logintest", (
        f"JWT sub debería ser 'logintest' pero es '{payload['sub']}'"
    )

    # La respuesta JSON también debe devolver el username real
    assert data["user"]["username"] == "logintest"

    # Verificar que el token funciona con get_current_user
    resp2 = client.get(
        "/auth/current_user",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 200, resp2.text
    assert resp2.json()["username"] == "logintest"


def test_login_email_inexistente(client):
    """Login con un email que no existe → 401."""
    app.dependency_overrides.clear()

    resp = client.post("/auth/login", json={
        "username": "noexiste@phantom.com",
        "password": "whatever",
    })
    assert resp.status_code == 401


def test_login_password_incorrecta(client):
    """Login con password equivocada → 401."""
    app.dependency_overrides.clear()

    resp = client.post("/auth/login", json={
        "username": "logintest",
        "password": "WrongPassword!",
    })
    assert resp.status_code == 401


def test_login_rate_limit_after_5_fails(client):
    """Después de 5 intentos fallidos, el 6º devuelve 429."""
    app.dependency_overrides.clear()

    for i in range(5):
        resp = client.post("/auth/login", json={
            "username": "logintest",
            "password": f"wrong_{i}",
        })
        assert resp.status_code == 401, f"Intento {i+1} debería ser 401"

    # 6º intento: bloqueado
    resp = client.post("/auth/login", json={
        "username": "logintest",
        "password": "wrong_5",
    })
    assert resp.status_code == 429, (
        f"6º intento debería ser 429 pero es {resp.status_code}"
    )
