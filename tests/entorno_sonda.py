"""Sonda que corre en un proceso aparte con el ENVIRONMENT dado: arranca la app
y escribe en la última línea, como JSON, qué puertas de desarrollo abre."""

import asyncio
import json
import sys

from fastapi.testclient import TestClient
from sqlalchemy import select
from starlette.requests import Request

import proyecto_maria.main as m
from proyecto_maria.database.connection import get_async_session
from proyecto_maria.database.models import PasswordResetToken, User


async def _consultar(fn):
    async for s in get_async_session():
        return await fn(s)


async def _crear_usuario():
    async def crear(s):
        s.add(User(username="sonda", email="sonda@example.com", name="Sonda",
                   password=m.hash_password("Clave-sonda-1"), is_verified=True))
        await s.commit()
        return (await s.execute(select(User.password).where(User.username == "sonda"))).scalar_one()
    return await _consultar(crear)


def main():
    with TestClient(m.app) as c:
        demo = asyncio.run(_consultar(lambda s: _escalar(s, select(User.username).where(
            User.username.in_(["demo", "premium", "basico"])))))
        guardada = asyncio.run(_crear_usuario())
        sesion = c.post("/auth/login", json={"username": "sonda", "password": "Clave-sonda-1"}).json()
        cobro = c.post("/api/billing/simulate-charge",
                       headers={"Authorization": f"Bearer {sesion['access_token']}"}).status_code
        # Al final: si la puerta abre, cambia la clave guardada.
        login_hash = c.post("/auth/login", json={"username": "sonda", "password": guardada}).status_code
        c.post("/auth/request-password-reset", json={"email": "sonda@example.com"})
        token = asyncio.run(_consultar(lambda s: _escalar(s, select(PasswordResetToken.token))))
    pedido = Request({"type": "http", "headers": [(b"x-signature", b"ts=1,v1=cualquiera"),
                                                   (b"x-request-id", b"r")], "query_string": b""})
    firma = m._verify_mp_webhook_signature(pedido, b"{}")
    sys.stdout.flush()
    print("\nSONDA " + json.dumps({"demo": sorted(demo), "login_hash": login_hash,
                                   "token": token[0] if token else None, "firma": firma,
                                   "cobro": cobro}))


async def _escalar(s, q):
    return list((await s.execute(q)).scalars().all())


if __name__ == "__main__":
    main()
