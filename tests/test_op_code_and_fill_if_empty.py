import pytest
import uuid
import asyncio
from fastapi.testclient import TestClient
from proyecto_maria import main
from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import Client as ClientModel, User as DBUser
from proyecto_maria.main import get_current_user
from sqlalchemy import select


@pytest.fixture()
def client(auth_override):
    return TestClient(main.app)


def _fake_user(username, email):
    return {
        "username": username,
        "name": username,
        "email": email,
        "cuit": "",
        "plan": "premium",
        "is_verified": True,
        "billing_status": "active",
        "trial_ends_at": None,
        "default_aduana_codigo": "",
        "default_puerto_destino": "",
        "default_tipo_destinacion": "",
        "team_owner_username": None,
        "effective_owner": username,
    }


def _client_for_user(user_dict):
    """Crea un TestClient con override de autenticación para un usuario específico."""
    c = TestClient(main.app)
    c.app.dependency_overrides[get_current_user] = lambda: user_dict
    return c


def _ensure_user_exists(username, email):
    async def _ensure():
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(DBUser).where(DBUser.username == username))
            u = res.scalars().first()
            if not u:
                u = DBUser(
                    username=username,
                    password="dummy_password_hash",
                    name=username,
                    email=email,
                    plan="premium",
                    billing_status="active",
                    is_verified=True,
                )
                session.add(u)
                await session.commit()
    asyncio.run(_ensure())


def _create_client(client, nombre, cuit, **kwargs):
    payload = {"nombre": nombre, "cuit": cuit}
    payload.update(kwargs)
    r = client.post("/api/clientes", json=payload)
    assert r.status_code == 200, r.text
    return r.json()["cliente"]["id"]


def _save_operation(client, client_id, op_code, domicilio="", fecha=""):
    body = {
        "operation_id": op_code,
        "source": "pdf_v2",
        "currency": "USD",
        "comprador_domicilio": domicilio,
        "comprador_fecha_inic_activ": fecha,
        "resumen": {
            "items": 1,
            "valor_total": 100,
            "peso_total": 10,
            "ncms_unicos": 1,
            "numero_factura": "FAC-001",
            "fecha_emision": "2026-01-01",
        },
        "items": [{
            "pieza": "3926.90.90",
            "ncm": "3926.90.90",
            "descripcion": "Plastic part",
            "origen": "CN",
            "cantidad": 1,
            "valor_unitario": 100,
            "peso_unitario": 10,
        }],
    }
    r = client.post(f"/api/clientes/{client_id}/operaciones", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def test_op_code_correlativo_sequential():
    """Dos operaciones del mismo usuario deben recibir OP-000001 y OP-000002."""
    uid = f"op_user_{uuid.uuid4().hex[:8]}"
    _ensure_user_exists(uid, f"{uid}@test.cdi")
    c = _client_for_user(_fake_user(uid, f"{uid}@test.cdi"))
    cid = _create_client(c, "Correlativo A", "30111111111")
    op1 = _save_operation(c, cid, "OP-TEST-01")
    op2 = _save_operation(c, cid, "OP-TEST-02")
    assert op1["op_code"] == "OP-000001"
    assert op2["op_code"] == "OP-000002"


def test_op_code_isolated_by_user():
    """Cada usuario arranca su correlativo en OP-000001."""
    uid_a = f"op_user_a_{uuid.uuid4().hex[:8]}"
    uid_b = f"op_user_b_{uuid.uuid4().hex[:8]}"
    _ensure_user_exists(uid_a, f"{uid_a}@test.cdi")
    _ensure_user_exists(uid_b, f"{uid_b}@test.cdi")

    c_a = _client_for_user(_fake_user(uid_a, f"{uid_a}@test.cdi"))
    cid_a = _create_client(c_a, "User A client", "30222222222")
    op_a = _save_operation(c_a, cid_a, "OP-USER-A")
    assert op_a["op_code"] == "OP-000001"

    c_b = _client_for_user(_fake_user(uid_b, f"{uid_b}@test.cdi"))
    cid_b = _create_client(c_b, "User B client", "30333333333")
    op_b = _save_operation(c_b, cid_b, "OP-USER-B")
    assert op_b["op_code"] == "OP-000001"


def test_fill_if_empty_populates_client_profile(client):
    """Cliente con ficha vacía recibe domicilio y fecha de la carátula."""
    cid = _create_client(client, "Ficha Vacia", "30444444444")
    _save_operation(
        client, cid, "OP-FILL-01",
        domicilio="Av. Siempre Viva 742",
        fecha="2020-05-15",
    )

    async def _check():
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(ClientModel).where(ClientModel.id == cid))
            c = res.scalars().first()
            assert c.address == "Av. Siempre Viva 742"
            assert c.fecha_inic_activ == "2020-05-15"
    asyncio.run(_check())


def test_fill_if_empty_does_not_overwrite(client):
    """Cliente con ficha ya llena no se pisa."""
    cid = _create_client(
        client, "Ficha Llena", "30555555555",
        direccion="Domicilio Original 123",
        fecha_inic_activ="2019-01-01",
    )
    _save_operation(
        client, cid, "OP-FILL-02",
        domicilio="Nuevo Domicilio 999",
        fecha="2023-12-31",
    )

    async def _check():
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(ClientModel).where(ClientModel.id == cid))
            c = res.scalars().first()
            assert c.address == "Domicilio Original 123"
            assert c.fecha_inic_activ == "2019-01-01"
    asyncio.run(_check())
