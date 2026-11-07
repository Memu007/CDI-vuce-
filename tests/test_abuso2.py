"""Contador de fallos del login por IP: un login correcto perdona sólo los
fallos de su propia cuenta, no los que la IP hizo con otras.

El tope de recuperar usuario contado por cuenta vive en Postgres, donde dos
emails que Python escribe distinto pueden ser el mismo para `lower()`:
`scripts/testing/abuso2_postgres.py`.
"""
import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

import proyecto_maria.database.connection as conn
from proyecto_maria.main import app
from tests.test_abuso1 import CLAVE, _ip, _login


@pytest.fixture(scope="module")
def cuentas():
    nombres = []
    with TestClient(app) as c:
        for _ in range(2):
            u = "ab2_" + uuid.uuid4().hex[:8]
            r = c.post("/auth/register", headers={"X-Forwarded-For": _ip()},
                       json={"username": u, "password": CLAVE, "email": f"{u}@ejemplo.test", "name": "Ab"})
            assert r.status_code == 200, r.text
            nombres.append(u)
    return {"propia": nombres[0], "otra": nombres[1], "nadie": "nadie_" + uuid.uuid4().hex[:6]}


@pytest.fixture(autouse=True)
def _limites_limpios(monkeypatch):
    """Sin el 5/minuto de slowapi: queda sólo el bloqueo por fallos."""
    monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
    from proyecto_maria.core.rate_limit import limiter
    antes = limiter.enabled
    limiter.enabled = False

    async def _vaciar():
        async with conn.AsyncSessionLocal() as s:
            await s.execute(text("delete from limites_auth"))
            await s.commit()
    asyncio.run(_vaciar())
    yield
    limiter.enabled = antes


@pytest.mark.parametrize("fallos,quedan", [
    (["otra"] * 4, 1),
    (["nadie"] * 4, 1),
    (["otra", "otra", "propia", "propia"], 3),
    (["propia", "nadie", "propia", "otra"], 3),
    (["propia"] * 4, 5),
], ids=["otra_cuenta", "usuario_inexistente", "mitad_y_mitad", "intercalados", "solo_propios"])
def test_login_correcto_perdona_solo_los_fallos_de_su_cuenta(cuentas, fallos, quedan):
    """Tras los fallos, un login correcto en la cuenta propia; después se
    cuentan los 401 hasta el 429: son los cinco del tope menos los fallos que
    la IP hizo fuera de la cuenta propia."""
    real, c = _ip(), TestClient(app)
    for quien in fallos:
        r = _login(c, cuentas[quien], "mal", real)
        assert r.status_code == 401, (quien, r.status_code, r.text)
    r = _login(c, cuentas["propia"], CLAVE, real)
    assert r.status_code == 200, (r.status_code, r.text)
    codigos = [_login(c, cuentas["otra"], "mal", real).status_code for _ in range(6)]
    assert codigos == [401] * quedan + [429] * (6 - quedan), codigos
