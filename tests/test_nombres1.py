"""Un nombre de usuario es único sin distinguir mayúsculas: si existe `emi`, nadie
registra ni crea un estudio con `Emi` o `EMI`. Las cuentas viejas que ya difieren
sólo en mayúsculas siguen entrando cada una con su nombre exacto, y el arranque
promueve sólo la que coincide exacto con ADMIN_USERNAMES.
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


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _sembrar(username, clave):
    async with AsyncSessionLocal() as s:
        s.add(User(username=username, password=main.hash_password(clave), name=username,
                   email=f"{uuid.uuid4().hex}@ejemplo.com", is_verified=True, roles=[]))
        await s.commit()


async def _fila(username):
    async with AsyncSessionLocal() as s:
        return (await s.execute(select(User).where(User.username == username))).scalars().first()


async def _borrar(username):
    async with AsyncSessionLocal() as s:
        await s.execute(delete(Organization).where(Organization.owner_username == username))
        await s.execute(delete(User).where(User.username == username))
        await s.commit()


def _formas(n):
    return {"n": n, "N": n.upper(), "C": n[0].upper() + n[1:], "x": n[:3] + n[3:].upper()}


@pytest.fixture
def nombre(monkeypatch):
    monkeypatch.setattr(limiter, "enabled", False)
    monkeypatch.delenv("ADMIN_USERNAMES", raising=False)
    monkeypatch.setattr(main, "_email_verification_enabled", lambda: False)
    n = f"n1_{uuid.uuid4().hex[:8]}"
    yield n
    for variante in set(_formas(n).values()):
        _run(_borrar(variante))


# (la que existe, la que se pide, si la que existe está en ADMIN_USERNAMES)
OTRAS_MAYUSCULAS = [
    ("{n}", "{N}", False),
    ("{n}", "{C}", False),
    ("{N}", "{n}", False),
    ("{C}", "{x}", False),
    ("{n}", "{N}", True),
    ("{n}", "{n}", False),
]


@pytest.mark.parametrize("ruta", ["/auth/register", "/api/organizations/create"])
@pytest.mark.parametrize("existe,pedido,en_lista", OTRAS_MAYUSCULAS,
                         ids=["mayusculas", "capitalizada", "existe_en_mayusculas", "mezcla", "de_la_lista", "exacto"])
def test_un_nombre_que_existe_con_otras_mayusculas_no_se_registra(monkeypatch, nombre, ruta, existe, pedido, en_lista):
    formas = _formas(nombre)
    existe, pedido = existe.format(**formas), pedido.format(**formas)
    _run(_sembrar(existe, "Vieja#123"))
    if en_lista:
        monkeypatch.setenv("ADMIN_USERNAMES", existe)
    cuerpo = {"username": pedido, "password": "SecureP@ss1", "email": f"{uuid.uuid4().hex}@ejemplo.com",
              "name": "Estudio" if ruta == "/api/organizations/create" else pedido}
    r = TestClient(main.app).post(ruta, json=cuerpo)
    assert r.status_code == 400, r.text[:200]
    assert r.json()["detail"] == "Usuario ya existe"
    if pedido != existe:
        assert _run(_fila(pedido)) is None


def _entrar(c, username, clave):
    c.cookies.clear()
    return c.post("/auth/login", json={"username": username, "password": clave})


# Las cuentas sembradas y la de la lista van como datos: el arranque y el login tienen que
# encontrar sólo la exacta, aunque la base devuelva primero la otra o la exacta no exista.
@pytest.mark.parametrize("sembradas,de_la_lista", [
    ((str.lower, str.upper), str.lower),
    ((str.lower, str.upper), str.upper),
    ((str.lower,), str.upper),
], ids=["minusculas", "mayusculas", "sola_y_la_lista_en_mayusculas"])
def test_dos_cuentas_viejas_que_difieren_en_mayusculas_siguen_entrando(monkeypatch, nombre, sembradas, de_la_lista):
    claves = {nombre: "Minus#123", nombre.upper(): "Mayus#456"}
    existen = {f(nombre): claves[f(nombre)] for f in sembradas}
    for username, clave in existen.items():
        _run(_sembrar(username, clave))
    monkeypatch.setattr(main, "login_attempts", {})
    c = TestClient(main.app)
    for username in claves:
        for clave in existen.values():
            r = _entrar(c, username, clave)
            if existen.get(username) != clave:
                assert r.status_code == 401, (username, r.status_code)
                continue
            assert r.status_code == 200, r.text[:200]
            me = c.get("/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
            assert me.json()["username"] == username

    admin = de_la_lista(nombre)
    monkeypatch.setenv("ADMIN_USERNAMES", admin)
    with TestClient(main.app):
        pass
    for username in claves:
        fila = _run(_fila(username))
        roles = main.roles_de({"roles": fila.roles}) if fila else []
        assert roles.count("admin") == (1 if fila and username == admin else 0), (username, roles)
