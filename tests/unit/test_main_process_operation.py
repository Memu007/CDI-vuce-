import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main


@pytest.fixture()
def main_client(auth_override):
    # auth_override autentica /process_operation/ sin tocar la DB.
    return TestClient(main.app)


def test_process_operation_success_main(monkeypatch, main_client):
    payload = {
        "operation_id": "op-123",
        "items": [
            {
                "pieza": "84713010",
                "descripcion": "Laptop",
                "origen": "CN",
                "cantidad": 1,
                "valor_unitario": 100.0,
                "peso_unitario": 2.0,
            }
        ],
    }

    monkeypatch.setattr(main, "run_pre_maria_validations", lambda items: (items, []))
    monkeypatch.setattr(main, "create_maria_excel", lambda items, op_id: "AVG_TEST.xlsx")

    response = main_client.post("/process_operation/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["validated_items_count"] == 1
    assert data["filename"] == "AVG_TEST.xlsx"


def test_process_operation_validation_error(monkeypatch, main_client):
    payload = {
        "operation_id": "op-err",
        "items": [],
    }

    monkeypatch.setattr(
        main, "run_pre_maria_validations", lambda items: (items, ["invalid"])
    )

    response = main_client.post("/process_operation/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["errors"]



