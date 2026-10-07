"""ADMIN-2: conectores sin detalle para el usuario común y sin simulate-webhook."""
import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from proyecto_maria import main
from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import User

COMUN = {"username": "comun_admin2", "roles": ["operador"], "effective_owner": "comun_admin2",
         "plan": "premium", "billing_status": "active"}
ADMIN = {"username": "admin_admin2", "roles": ["admin"], "effective_owner": "admin_admin2",
         "plan": "premium", "billing_status": "active"}

# Lo que sólo el admin ve de /api/system/connectors.
DETALLE = {"base_url", "has_api_key", "has_cuit", "has_cert", "note"}


def _conectores(usuario):
    main.app.dependency_overrides[main.get_current_user] = lambda: dict(usuario)
    try:
        r = TestClient(main.app).get("/api/system/connectors")
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)
    assert r.status_code == 200, r.text[:200]
    return r.json()


def test_conectores_usuario_comun_sin_detalle():
    data = _conectores(COMUN)
    # El chip de la barra superior sólo lee el mode de cada conector.
    assert set(data) == {"vuce", "tarifar", "afip"}, data
    for nombre, conector in data.items():
        assert set(conector) == {"mode"}, (nombre, conector)
        assert conector["mode"]


def test_conectores_admin_con_detalle():
    data = _conectores(ADMIN)
    assert "ncm_scraper" in data
    assert DETALLE <= set(data["vuce"]) | set(data["tarifar"]) | set(data["afip"])
    assert "base_url" in data["vuce"] and "has_cert" in data["afip"]


def test_conectores_admin_por_admin_usernames_con_detalle(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAMES", COMUN["username"])
    assert "ncm_scraper" in _conectores(COMUN)


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.fixture
def cuenta_en_trial():
    nombre = "trial_admin2"

    async def _crear():
        async with AsyncSessionLocal() as s:
            await s.execute(delete(User).where(User.username == nombre))
            s.add(User(username=nombre, password="x", email="trial_admin2@example.test",
                       name="Trial", plan="premium", billing_status="trial", is_verified=True))
            await s.commit()

    async def _estado():
        async with AsyncSessionLocal() as s:
            u = (await s.execute(select(User).where(User.username == nombre))).scalars().first()
            return u.billing_status

    async def _borrar():
        async with AsyncSessionLocal() as s:
            await s.execute(delete(User).where(User.username == nombre))
            await s.commit()

    _run(_crear())
    yield nombre, (lambda: _run(_estado()))
    _run(_borrar())


def test_simulate_webhook_ya_no_existe_sin_sesion(cuenta_en_trial, monkeypatch):
    """Sin sesión y con el secreto, nadie pasa una cuenta a active sin pagar."""
    nombre, estado = cuenta_en_trial
    monkeypatch.setattr(main, "MP_WEBHOOK_SECRET", "secreto-de-prueba-admin2")
    r = TestClient(main.app).post(
        "/api/payments/simulate-webhook",
        json={"username": nombre, "action": "subscription"},
        headers={"X-Webhook-Secret": "secreto-de-prueba-admin2"},
    )
    assert r.status_code in (404, 405), f"{r.status_code} {r.text[:200]}"
    assert estado() == "trial"
