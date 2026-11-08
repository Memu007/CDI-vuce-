"""Admin es sólo el rol guardado. ADMIN_USERNAMES no da admin por sí solo: el
arranque le pone el rol a la cuenta que ya existe con ese nombre, y el registro
no deja crear una cuenta nueva con un nombre de la lista.

Sin el rechazo, quien registraba primero un nombre de la lista que todavía no
existía quedaba admin al entrar.
"""
import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from proyecto_maria import main
from proyecto_maria.core.rate_limit import limiter
from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import Organization, User

RUTA_ADMIN = "/api/dev/stats"


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _fila(username):
    async with AsyncSessionLocal() as s:
        return (await s.execute(select(User).where(User.username == username))).scalars().first()


async def _borrar(username):
    async with AsyncSessionLocal() as s:
        await s.execute(delete(Organization).where(Organization.owner_username == username))
        await s.execute(delete(User).where(User.username == username))
        await s.commit()


async def _poner_roles(username, roles):
    async with AsyncSessionLocal() as s:
        u = (await s.execute(select(User).where(User.username == username))).scalars().first()
        u.roles = roles
        await s.commit()


@pytest.fixture
def nombre():
    limiter.enabled = False
    n = f"p2_{uuid.uuid4().hex[:8]}"
    yield n
    for variante in (n, n.upper(), n + "\n"):
        _run(_borrar(variante))


def _registrar(c, ruta, username):
    cuerpo = {"username": username, "password": "SecureP@ss1", "email": f"{username}@ejemplo.com"}
    cuerpo["name"] = "Estudio" if ruta == "/api/organizations/create" else username
    return c.post(ruta, json=cuerpo)


def _como(c, token):
    c.cookies.clear()
    c.cookies.set("access_token", token)
    return c.get(RUTA_ADMIN)


@pytest.mark.parametrize("ruta", ["/auth/register", "/api/organizations/create"])
@pytest.mark.parametrize("lista", ["{n}", "otro, {n} ,tercero"], ids=["solo", "en_una_lista"])
def test_un_nombre_de_admin_usernames_no_se_registra(monkeypatch, nombre, ruta, lista):
    monkeypatch.setenv("ADMIN_USERNAMES", lista.format(n=nombre))
    c = TestClient(main.app)
    r = _registrar(c, ruta, nombre)
    assert r.status_code == 400, r.text[:200]
    assert r.json()["detail"] == "Usuario ya existe"
    assert _run(_fila(nombre)) is None


@pytest.mark.parametrize("roles", [None, [], ["operador"], "administrador", {"admin": False}])
def test_la_cuenta_de_admin_usernames_sigue_siendo_admin_al_reiniciar(monkeypatch, nombre, roles):
    """La cuenta ya existía cuando su nombre entró en la lista; el rol lo pone el arranque."""
    monkeypatch.delenv("ADMIN_USERNAMES", raising=False)
    c = TestClient(main.app)
    r = _registrar(c, "/auth/register", nombre)
    assert r.status_code == 200, r.text[:200]
    token = r.json()["access_token"]
    _run(_poner_roles(nombre, roles))
    assert _como(c, token).status_code == 403

    monkeypatch.setenv("ADMIN_USERNAMES", nombre)
    for _ in range(2):
        with TestClient(main.app) as reiniciada:
            assert _como(reiniciada, token).status_code == 200
    assert main.roles_de({"roles": _run(_fila(nombre)).roles}).count("admin") == 1


@pytest.mark.parametrize("ruta", ["/auth/register", "/api/organizations/create"])
@pytest.mark.parametrize("pedido,lista,detalle", [
    ("{n}\n", "", "Username inválido"),
    ("{n}\r\n", "", "Username inválido"),
    ("\n{n}", "", "Username inválido"),
    ("{n} ", "", "Username inválido"),
    ("{n}é", "", "Username inválido"),
    ("{N}", "{n}", "Usuario ya existe"),
    ("{n}", "{N}", "Usuario ya existe"),
    ("{n}\n", "{n}", "Username inválido"),
], ids=["lf_final", "crlf_final", "lf_inicial", "espacio", "acento",
        "mayusculas", "lista_en_mayusculas", "lf_final_de_la_lista"])
def test_un_nombre_que_se_ve_como_otro_no_se_registra(monkeypatch, nombre, ruta, pedido, lista, detalle):
    monkeypatch.setenv("ADMIN_USERNAMES", lista.format(n=nombre, N=nombre.upper()))
    username = pedido.format(n=nombre, N=nombre.upper())
    c = TestClient(main.app)
    r = _registrar(c, ruta, username)
    assert r.status_code == 400, r.text[:200]
    assert r.json()["detail"].startswith(detalle)
    for variante in {username, nombre, nombre.upper()}:
        assert _run(_fila(variante)) is None
