"""ABUSO-1 (S4, S5, S6 y C9 de AUDITORIA-2026-10-06).

S5: las rutas de eventos (`/api/ui/event` y `/api/session/state`, sin sesión
obligatoria) guardaban cualquier cuerpo: cada pedido de 5 MB sumaba 5 MB a
`logs/ui_events.jsonl`, que ningún código lee, y una fila de 8000 caracteres
en `telemetry_events`. Ahora el cuerpo tiene un tope de 16 KB (lo que se pasa
da 413 y no se guarda) y el JSONL ya no se escribe.

Acá corre en SQLite; el mismo recorrido contra un servidor real, en Postgres y
en SQLite, está en `scripts/testing/abuso1_motores.py`.
"""
import asyncio
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

import proyecto_maria.database.connection as conn
import proyecto_maria.main as main_mod
from proyecto_maria.main import app

RUTAS = ("/api/ui/event", "/api/session/state")
TOPE = 16 * 1024
JSONL = os.path.join(main_mod.basedir, "logs", "ui_events.jsonl")
CLAVE = "Clave-sintetica-1!"


@pytest.fixture(scope="module", autouse=True)
def _tablas():
    with TestClient(app):
        pass
    yield


@pytest.fixture(autouse=True)
def _limites_limpios(monkeypatch):
    """Cada caso arranca con los contadores en cero y el limitador como lo
    dejó la app (otro módulo puede haberlo apagado)."""
    monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
    from proyecto_maria.core.rate_limit import limiter
    antes = limiter.enabled
    limiter.enabled = True
    limiter.reset()
    main_mod.login_attempts.clear()
    main_mod.reset_attempts.clear()
    yield
    limiter.reset()
    limiter.enabled = antes


def _filas(accion):
    async def _correr():
        async with conn.AsyncSessionLocal() as s:
            r = await s.execute(text(
                "select owner_username, length(props) from telemetry_events where action = :a"), {"a": accion})
            return [tuple(x) for x in r.all()]
    return asyncio.run(_correr())


def _tamano_jsonl():
    return os.path.getsize(JSONL) if os.path.exists(JSONL) else 0


def _cuerpo(accion, total):
    """Un evento JSON válido de exactamente `total` bytes."""
    base = '{"action":"%s","screen":"s","relleno":"' % accion
    return (base + "x" * (total - len(base) - 2) + '"}').encode()


@pytest.fixture(scope="module")
def token():
    u = "ab1t_" + uuid.uuid4().hex[:8]
    with TestClient(app) as c:
        r = c.post("/auth/register", json={"username": u, "password": CLAVE,
                                           "email": f"{u}@ejemplo.test", "name": "Ab"})
        assert r.status_code == 200, r.text
        return u, r.json()["access_token"]


def _accion():
    return "ab1_" + uuid.uuid4().hex[:10]


@pytest.mark.parametrize("ruta", RUTAS)
@pytest.mark.parametrize("con_sesion", (False, True))
def test_s5_evento_de_5mb_no_se_guarda(ruta, con_sesion, token):
    a = _accion()
    h = {"Content-Type": "application/json"}
    if con_sesion:
        h["Authorization"] = f"Bearer {token[1]}"
    antes = _tamano_jsonl()
    r = TestClient(app).post(ruta, content=_cuerpo(a, 5 * 1024 * 1024), headers=h)
    assert r.status_code == 413, (r.status_code, r.text[:200])
    assert _filas(a) == []
    assert _tamano_jsonl() == antes


@pytest.mark.parametrize("ruta", RUTAS)
def test_s5_sin_content_length_tambien_corta(ruta):
    """Un cuerpo por partes (sin Content-Length) se corta al pasar el tope."""
    a = _accion()
    cuerpo = _cuerpo(a, 1024 * 1024)

    def partes():
        for i in range(0, len(cuerpo), 4096):
            yield cuerpo[i:i + 4096]

    r = TestClient(app).post(ruta, content=partes(), headers={"Content-Type": "application/json"})
    assert r.status_code == 413, (r.status_code, r.text[:200])
    assert _filas(a) == []


@pytest.mark.parametrize("ruta", RUTAS)
def test_s5_el_tope_es_16kb(ruta, token):
    h = {"Content-Type": "application/json", "Authorization": f"Bearer {token[1]}"}
    justo, pasado = _accion(), _accion()
    r = TestClient(app).post(ruta, content=_cuerpo(justo, TOPE), headers=h)
    assert r.status_code == 200 and r.json()["ok"] is True, r.text
    assert [u for u, _ in _filas(justo)] == [token[0]]
    r = TestClient(app).post(ruta, content=_cuerpo(pasado, TOPE + 1), headers=h)
    assert r.status_code == 413, r.text
    assert _filas(pasado) == []


@pytest.mark.parametrize("ruta", RUTAS)
def test_s5_un_evento_chico_se_guarda_y_no_escribe_el_jsonl(ruta, token):
    a = _accion()
    antes = _tamano_jsonl()
    r = TestClient(app).post(ruta, json={"action": a, "screen": "s", "version": "v2"},
                             headers={"Authorization": f"Bearer {token[1]}"})
    assert r.status_code == 200 and r.json()["ok"] is True, r.text
    assert [u for u, _ in _filas(a)] == [token[0]]
    assert _tamano_jsonl() == antes
