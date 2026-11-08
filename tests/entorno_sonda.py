"""Sonda que corre en un proceso aparte con el ENVIRONMENT dado: arranca la app
y escribe en la última línea, como JSON, qué puertas de desarrollo abre."""

import asyncio
import json
import os
import sys
import types

import dotenv

# Un .env local no completa las variables que la prueba deja afuera a propósito.
dotenv.load_dotenv = lambda *a, **k: False

from fastapi.testclient import TestClient
from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import Response

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


def _frontend_por_defecto():
    guardada = os.environ.pop("FRONTEND_URL", None)
    try:
        return m.get_frontend_url()
    except RuntimeError:
        return "rechaza"
    finally:
        if guardada is not None:
            os.environ["FRONTEND_URL"] = guardada


async def _limite_desde_127():
    from proyecto_maria.security import security_middleware as sm
    async def siguiente(_):
        return Response("ok")
    # Reloj quieto: la ventana es por minuto y los 11 pedidos no pueden partirse entre dos.
    sm.time = types.SimpleNamespace(time=lambda: 600.0)
    limite = sm.RateLimitByEndpointMiddleware(app=None)
    pedido = lambda: Request({"type": "http", "method": "POST", "path": "/upload_pdf", "headers": [],
                              "query_string": b"", "client": ("127.0.0.1", 1)})
    # El tope de las rutas pesadas es 10 por minuto: el pedido 11 pasa sólo con el pase.
    codigos = [(await limite.dispatch(pedido(), siguiente)).status_code for _ in range(11)]
    return codigos[-1]


def main():
    with TestClient(m.app) as c:
        demo = asyncio.run(_consultar(lambda s: _escalar(s, select(User.username).where(
            User.username.in_(["demo", "premium", "basico"])))))
        guardada = asyncio.run(_crear_usuario())
        entrada = c.post("/auth/login", json={"username": "sonda", "password": "Clave-sonda-1"})
        hsts = "strict-transport-security" in entrada.headers
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
                                   "vuce": _vuce_simulado(), "hsts": hsts,
                                   "frontend": _frontend_por_defecto(),
                                   "limite_127": asyncio.run(_limite_desde_127())}))


async def _escalar(s, q):
    return list((await s.execute(q)).scalars().all())


if __name__ == "__main__":
    main()
