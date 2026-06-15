import pytest
from fastapi.testclient import TestClient
from proyecto_maria import main

@pytest.fixture()
def client(auth_override):
    return TestClient(main.app)

def test_manual_operation_null_client_id(client):
    """Verifica que enviar client_id = null no crashea con 500, sino que devuelve 400."""
    res = client.post(
        "/api/operations/manual",
        json={
            "client_id": None,
            "items": [{"descripcion": "A", "cantidad": 1, "valor_unitario": 10}]
        }
    )
    assert res.status_code == 400
    assert "Falta client_id" in res.json()["detail"]
