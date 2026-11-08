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
from tests.test_abuso1 import CLAVE, _ip, _login, reloj  # noqa: F401


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


@pytest.mark.parametrize("pasos,quedan", [
    (["otra"] * 4, 1),
    (["nadie"] * 4, 1),
    (["otra", "otra", "propia", "propia"], 3),
    (["propia", "nadie", "propia", "otra"], 3),
    (["propia"] * 4, 5),
    (["otra"] * 3 + ["propia"] * 2 + [16], 2),
    (["propia"] * 5 + [16, "propia", 16], 5),
    (["propia"] * 5 + [16, "otra", 16], 4),
    (["propia"] * 3 + [23 * 60, "propia", "propia", 61], 5),
    (["propia@otra_ip"] * 5 + ["otra"] * 4, 1),
    (["otra", "otra", "propia", "propia", "bien"], 3),
    (["propia", "propia", 23 * 60, "otra", "otra", 61], 1),
    (["propia", "otra", 24 * 60 + 1], 5),
    (["propia", "propia", 24 * 60 - 1], 5),
    (["otra", "otra", 24 * 60 - 1], 3),
    (["propia@email"] * 3 + ["otra"], 4),
], ids=["otra_cuenta", "usuario_inexistente", "mitad_y_mitad", "intercalados", "solo_propios",
        "bloqueo_vencido", "mas_propios_que_la_ip", "ajeno_tras_el_bloqueo",
        "fallos_propios_de_mas_de_un_dia", "fallos_propios_desde_otra_ip",
        "dos_logins_seguidos", "propios_vencidos_con_la_ip_viva", "los_dos_olvidan_al_dia",
        "la_cuenta_recuerda_un_dia", "la_ip_recuerda_un_dia", "fallos_con_el_email"])
def test_login_correcto_perdona_solo_los_fallos_de_su_cuenta(cuentas, pasos, quedan, reloj):
    """Fallos (un número son minutos que pasan; `@otra_ip`, desde otra IP;
    `@email`, con el email en vez del usuario; `bien`, un login correcto más)
    y un login correcto en la cuenta propia; después se cuentan los 401 hasta el 429: son los cinco del tope menos los
    fallos que la IP todavía recuerda fuera de lo propio no vencido."""
    real, lejos, c = _ip(), _ip(), TestClient(app)
    reloj()
    for paso in pasos:
        if isinstance(paso, int):
            reloj(paso * 60)
            continue
        if paso == "bien":
            r = _login(c, cuentas["propia"], CLAVE, real)
            assert r.status_code == 200, (paso, r.status_code, r.text)
            continue
        cuenta, _, como = paso.partition("@")
        usuario = cuentas[cuenta] + ("@ejemplo.test" if como == "email" else "")
        r = _login(c, usuario, "mal", lejos if como == "otra_ip" else real)
        assert r.status_code == 401, (paso, r.status_code, r.text)
    r = _login(c, cuentas["propia"], CLAVE, real)
    assert r.status_code == 200, (r.status_code, r.text)
    codigos = [_login(c, cuentas["otra"], "mal", real).status_code for _ in range(6)]
    assert codigos == [401] * quedan + [429] * (6 - quedan), codigos


def _filas():
    async def _leer():
        async with conn.AsyncSessionLocal() as s:
            r = await s.execute(text("select clave, cuenta, bloqueado_hasta, vence from limites_auth"))
            return {clave: resto for clave, *resto in r.all()}
    return asyncio.run(_leer())


def test_un_login_correcto_no_cambia_otras_claves(cuentas):
    """El login correcto borra la fila de su cuenta en su IP y resta eso de la
    IP, sin tocar el resto de la fila ni otras claves: otras IPs, otras
    cuentas, recuperar, registro, reset y cambio de clave."""
    from proyecto_maria.core import limites_auth
    real, lejos, c = _ip(), _ip(), TestClient(app)
    propia, otra = cuentas["propia"], cuentas["otra"]
    for cuenta, ip in [(propia, lejos), (otra, real), (propia, real), (propia, real)]:
        assert _login(c, cuenta, "mal", ip).status_code == 401
    ajenas = [f"recuperar:cuenta:{propia}", f"reset:cuenta:{propia}", f"recuperar:ip:{real}",
              f"registro:h:{real}", f"registro:d:{real}", f"reset:{real}", f"pwd:{propia}"]

    async def _sumar():
        async with conn.AsyncSessionLocal() as s:
            for clave in ajenas * 3:
                await limites_auth.contar(s, clave, 3600)
    asyncio.run(_sumar())
    suyas = {f"login:{real}", f"cuenta:{propia}:login:{real}"}
    antes = {k: v for k, v in _filas().items() if k not in suyas}
    assert set(antes) == {f"login:{lejos}", f"cuenta:{propia}:login:{lejos}",
                          f"cuenta:{otra}:login:{real}", *ajenas}
    ip = _filas()[f"login:{real}"]
    assert _login(c, propia, CLAVE, real).status_code == 200
    despues = _filas()
    assert despues.pop(f"login:{real}") == [ip[0] - 2, *ip[1:]]
    assert despues == antes


def test_descontar_no_deja_la_ip_en_negativo(reloj):
    """La fila de la cuenta se escribe después que la de la IP y puede
    vencer un instante más tarde: lo que perdona no baja la IP de cero."""
    from proyecto_maria.core import limites_auth

    async def _correr():
        async with conn.AsyncSessionLocal() as s:
            for _ in range(5):
                await limites_auth.sumar_fallo(s, "login:ip", exacta=True)
            reloj(1)
            for _ in range(5):
                await limites_auth.sumar_fallo(s, "cuenta:a:login:ip", exacta=True)
            reloj(24 * 3600 - 0.5)
            await limites_auth.sumar_fallo(s, "login:ip", exacta=True)
            await limites_auth.descontar(s, "login:ip", "cuenta:a:login:ip")
            return (await s.execute(text("select cuenta from limites_auth where clave = 'login:ip'"))).scalar()
    reloj()
    assert asyncio.run(_correr()) == 0
