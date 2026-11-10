"""AISLAMIENTO-2: los roles guardados como texto no dan admin por una parte.

La columna roles es JSON: puede quedar un texto en vez de una lista (una
carga a mano, una migración). Con texto, «"admin" in roles» busca dentro de
la palabra y «administrador» contaba como admin, en require_admin y en
require_role. Un texto vale como un único rol, entero.

El usuario entra con su sesión de verdad (cookie con el token), así la prueba
recorre lo mismo que en producción: base, get_current_user y el control.
"""
import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from proyecto_maria import main
from datetime import datetime, timedelta, timezone

from proyecto_maria.auth.dependencies import firmar_token


def create_access_token(datos):
    return firmar_token({**datos, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)})
from proyecto_maria.auth.roles import require_role
from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import User

USUARIO = "roles_texto_ais2"
RUTA_ADMIN = "/api/dev/stats"


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _borrar():
    async with AsyncSessionLocal() as s:
        await s.execute(delete(User).where(User.username == USUARIO))
        await s.commit()


async def _crear(roles):
    await _borrar()
    async with AsyncSessionLocal() as s:
        s.add(User(username=USUARIO, password="x", name="Roles", email=f"{USUARIO}@ejemplo.com",
                   plan="premium", billing_status="active", is_verified=True, roles=roles))
        await s.commit()


@pytest.fixture(autouse=True)
def _limpio(monkeypatch):
    monkeypatch.delenv("ADMIN_USERNAMES", raising=False)
    yield
    _run(_borrar())


def _pedir_como(roles):
    _run(_crear(roles))
    client = TestClient(main.app)
    client.cookies.set("access_token", create_access_token({"sub": USUARIO}))
    return client.get(RUTA_ADMIN)


@pytest.mark.parametrize("roles", ["administrador", "no es admin", {"admin": False}])
def test_roles_que_no_son_la_lista_admin_no_entran(roles):
    r = _pedir_como(roles)
    assert r.status_code == 403, f"roles={roles!r}: {r.status_code} {r.text[:200]}"


@pytest.mark.parametrize("roles", [["admin"], ["operador", "admin"], "admin"])
def test_el_rol_admin_entero_entra(roles):
    r = _pedir_como(roles)
    assert r.status_code == 200, f"roles={roles!r}: {r.status_code} {r.text[:200]}"


@pytest.mark.parametrize("roles", ["administrador", "operador_admin", {"admin": 1}])
def test_require_role_no_cuenta_admin_por_una_parte(roles):
    checker = require_role("auditor")
    with pytest.raises(main.HTTPException) as e:
        _run(checker({"username": USUARIO, "roles": roles}))
    assert e.value.status_code == 403


def test_require_role_con_el_rol_en_texto_entra():
    usuario = {"username": USUARIO, "roles": "auditor"}
    assert _run(require_role("auditor")(usuario)) == usuario
