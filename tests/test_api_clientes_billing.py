import uuid
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from proyecto_maria import main
from proyecto_maria.database.connection import get_async_session
from proyecto_maria.database.models import User, Client
from sqlalchemy.future import select


def _unique(prefix="bug3"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _set_user(username: str, **kwargs):
    async def _run():
        async for db in get_async_session():
            res = await db.execute(select(User).where(User.username == username))
            u = res.scalars().first()
            if not u:
                return
            for k, v in kwargs.items():
                setattr(u, k, v)
            await db.commit()
    import asyncio
    asyncio.new_event_loop().run_until_complete(_run())


@pytest.fixture()
def client(auth_override):
    return TestClient(main.app)


class TestApiClientesBillingEdgeCases:
    """GET /api/clientes debe seguir funcionando aunque el billing esté vencido."""

    def test_api_clientes_past_due(self, client):
        uname = _unique("pastdue")
        res = client.post("/auth/register", json={
            "username": uname,
            "password": "SecureP@ss1",
            "email": f"{uname}@test.com",
        })
        assert res.status_code == 200

        client.post("/auth/login", json={"username": uname, "password": "SecureP@ss1"})
        _set_user(uname, billing_status="past_due")

        res = client.get("/api/clientes")
        assert res.status_code == 200, res.text
        data = res.json()
        assert "clientes" in data

    def test_api_clientes_trial_expired(self, client):
        uname = _unique("trialexp")
        res = client.post("/auth/register", json={
            "username": uname,
            "password": "SecureP@ss1",
            "email": f"{uname}@test.com",
        })
        assert res.status_code == 200

        client.post("/auth/login", json={"username": uname, "password": "SecureP@ss1"})
        past = datetime.now(timezone.utc) - timedelta(days=5)
        _set_user(uname, billing_status="trial", trial_ends_at=past)

        res = client.get("/api/clientes")
        assert res.status_code == 200, res.text
        data = res.json()
        assert "clientes" in data

    def test_api_clientes_trial_expired_with_clients(self, client):
        uname = _unique("trialclients")
        res = client.post("/auth/register", json={
            "username": uname,
            "password": "SecureP@ss1",
            "email": f"{uname}@test.com",
        })
        assert res.status_code == 200

        client.post("/auth/login", json={"username": uname, "password": "SecureP@ss1"})

        # Crear un cliente antes de vencer el trial
        rclient = client.post("/api/clientes", json={
            "cuit": "30612123820",
            "nombre": "Cliente Test",
        })
        assert rclient.status_code == 200

        past = datetime.now(timezone.utc) - timedelta(days=5)
        _set_user(uname, billing_status="trial", trial_ends_at=past)

        res = client.get("/api/clientes")
        assert res.status_code == 200, res.text
        data = res.json()
        assert len(data.get("clientes", [])) >= 1
