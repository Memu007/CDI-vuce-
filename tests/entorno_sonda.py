"""Sonda que corre en un proceso aparte con el ENVIRONMENT dado: arranca la app
y escribe en la última línea, como JSON, qué puertas de desarrollo abre."""

import asyncio
import json
import sys

import dotenv

# Un .env local no completa las variables que la prueba deja afuera a propósito.
dotenv.load_dotenv = lambda *a, **k: False

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
                   password=m.hash_password("Clave-sonda-1"), is_verified=True,
                   billing_status="trial", payment_method_last4="4242"))
        await s.commit()
        return (await s.execute(select(User.password).where(User.username == "sonda"))).scalar_one()
    return await _consultar(crear)


def _vuce_simulado():
    from proyecto_maria.core.vuce_connector import VuceClient
    try:
        VuceClient()._request("/ncm/01012100")
        return "responde"
    except Exception as e:
        return type(e).__name__


def main():
    with TestClient(m.app) as c:
        demo = asyncio.run(_consultar(lambda s: _escalar(s, select(User.username).where(
            User.username.in_(["demo", "premium", "basico"])))))
        guardada = asyncio.run(_crear_usuario())
        entrada = c.post("/auth/login", json={"username": "sonda", "password": "Clave-sonda-1"})
        sesion = entrada.json()
        cookies = {h.split("=", 1)[0]: "; secure" in h.lower() for h in entrada.headers.get_list("set-cookie")}
        bearer = {"Authorization": f"Bearer {sesion['access_token']}"}
        cobro = c.post("/api/billing/simulate-charge", headers=bearer).status_code
        c.cookies.clear()
        csrf = c.post("/api/ruta-que-no-existe", headers={"Cookie": "access_token=x"}).status_code
        docs = [c.get(p).status_code for p in ("/docs", "/redoc", "/openapi.json")]
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
                                   "cobro": cobro,
                                   "cookies": cookies, "csrf": csrf, "docs": docs,
                                   "vuce": _vuce_simulado()}))


async def _escalar(s, q):
    return list((await s.execute(q)).scalars().all())


if __name__ == "__main__":
    main()
