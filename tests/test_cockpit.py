"""Cockpit de operaciones: listado, filtro por estado y update de estado/canal.

Usa override de get_current_user (no toca la sesion real) e inserta una
operacion directo en la DB de tests.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main
from proyecto_maria.database.models import Operation, Client


@pytest.fixture(scope="module", autouse=True)
def _init_db_once():
    with TestClient(main.app) as _:
        pass


def _override_user(username="cockpit_user"):
    main.app.dependency_overrides[main.get_current_user] = lambda: {
        "username": username, "roles": [], "effective_owner": username,
        "plan": "premium", "billing_status": "active",
    }


@pytest.fixture()
def client():
    _override_user()
    yield TestClient(main.app)
    main.app.dependency_overrides.pop(main.get_current_user, None)


async def _seed_operation(owner, estado="borrador"):
    """Inserta una operacion directo en la DB de tests."""
    async for session in main.get_async_session():
        op = Operation(
            id=str(uuid.uuid4()),
            owner_username=owner,
            op_code="OP_TEST_" + uuid.uuid4().hex[:6],
            total_items=3,
            total_value=1000.0,
            estado=estado,
        )
        session.add(op)
        await session.commit()
        return op.id


@pytest.mark.asyncio
async def test_listado_vacio_devuelve_counts(client):
    resp = client.get("/api/operations")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "counts" in data and "borrador" in data["counts"]


@pytest.mark.asyncio
async def test_listado_incluye_operacion_creada(client):
    op_id = await _seed_operation("cockpit_user")
    resp = client.get("/api/operations")
    assert resp.status_code == 200
    ids = [o["id"] for o in resp.json()["operaciones"]]
    assert op_id in ids


@pytest.mark.asyncio
async def test_update_estado_ok(client):
    op_id = await _seed_operation("cockpit_user")
    resp = client.patch(f"/api/operations/{op_id}/estado", json={"estado": "oficializada"})
    assert resp.status_code == 200
    assert resp.json()["estado"] == "oficializada"


@pytest.mark.asyncio
async def test_update_canal_ok(client):
    op_id = await _seed_operation("cockpit_user")
    resp = client.patch(f"/api/operations/{op_id}/estado", json={"canal": "rojo"})
    assert resp.status_code == 200
    assert resp.json()["canal"] == "rojo"


@pytest.mark.asyncio
async def test_update_estado_invalido_400(client):
    op_id = await _seed_operation("cockpit_user")
    resp = client.patch(f"/api/operations/{op_id}/estado", json={"estado": "inexistente"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_no_puede_tocar_operacion_de_otro(client):
    # operacion de OTRO owner -> 404 (aislamiento multi-tenant)
    op_id = await _seed_operation("otro_despachante")
    resp = client.patch(f"/api/operations/{op_id}/estado", json={"estado": "liberada"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_listado_no_ve_operaciones_de_otro(client):
    op_id = await _seed_operation("otro_despachante_2")
    resp = client.get("/api/operations")
    ids = [o["id"] for o in resp.json()["operaciones"]]
    assert op_id not in ids


def test_listado_sin_auth_401():
    main.app.dependency_overrides.pop(main.get_current_user, None)
    resp = TestClient(main.app).get("/api/operations")
    assert resp.status_code == 401
