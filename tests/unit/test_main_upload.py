import os

import pandas as pd
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from proyecto_maria import main
from proyecto_maria.main import app


@pytest.fixture()
def main_client(monkeypatch):
    # Ensure each test can tweak env vars safely
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    return TestClient(app)


def test_upload_excel_rejects_large_files(main_client):
    """Upload should fail fast when payload exceeds MAX_UPLOAD_MB."""
    # 1 MB limit from fixture; make payload slightly bigger
    oversized_bytes = b"a" * (1 * 1024 * 1024 + 10)
    files = {
        "file": (
            "payload.xlsx",
            oversized_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    response = main_client.post("/upload_excel/", files=files)

    assert response.status_code == 413
    body = response.json()
    assert "excede" in body["detail"] or "excede" in body["detail"].lower()


def test_upload_excel_rejects_invalid_extension(main_client):
    files = {
        "file": ("payload.txt", b"dummy", "text/plain"),
    }

    response = main_client.post("/upload_excel/", files=files)

    assert response.status_code == 400
    assert "Solo se permiten archivos Excel" in response.json()["detail"]


def test_upload_excel_success_flow(monkeypatch, main_client):
    """Exercise main flow by stubbing heavy dependencies."""
    # Allow bigger uploads for this test
    monkeypatch.setenv("MAX_UPLOAD_MB", "5")

    # Fake DataFrame returned by pandas
    df = pd.DataFrame(
        {
            "pieza": ["84713010"],
            "descripcion": ["Laptop Pro"],
            "origen": ["CN"],
            "peso_unitario": [2.0],
            "cantidad": [1],
            "valor_unitario": [1000.0],
        }
    )
    monkeypatch.setattr(main.pd, "read_excel", lambda *_args, **_kwargs: df)

    created_filename = "generated.xlsx"
    monkeypatch.setattr(main, "run_pre_maria_validations", lambda items: (items, []))
    monkeypatch.setattr(main, "create_maria_excel", lambda items, op_id: created_filename)

    files = {
        "file": (
            "operation.xlsx",
            b"excel-bytes",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }

    response = main_client.post("/upload_excel/", files=files)
    assert response.status_code == 200

    data = response.json()
    assert data["filename"] == created_filename
    assert data["items_procesados"] == 1
    assert data["items_extraidos"] == 1


def test_get_max_upload_bytes_handles_invalid_env(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "not-a-number")
    assert main._get_max_upload_bytes() == 10 * 1024 * 1024


def test_extract_items_from_excel_standard_mapping():
    df = pd.DataFrame(
        {
            "pieza": ["84713010", "INVALID"],
            "descripcion": ["Laptop Ultra", ""],
            "origen": ["CN", "US"],
            "peso_unitario": [1.5, 0],
            "cantidad": [2, 0],
            "valor_unitario": [800.0, 0],
        }
    )

    items = main.extract_items_from_excel(df, "test.xlsx")

    assert len(items) == 1
    assert items[0].pieza == "84713010"
    assert items[0].cantidad == 2


@pytest.mark.asyncio
async def test_download_file_success_and_missing(tmp_path, monkeypatch):
    existing = tmp_path / "generated.xlsx"
    existing.write_text("dummy")

    # Ensure function looks at tmp directory
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main, "DATA_DIR", str(tmp_path))

    response = await main.download_file(existing.name, user={"username": "test"})
    assert response.path == str(existing.absolute())

    real_file_response = main.FileResponse

    def fake_file_response(*args, **kwargs):
        path = kwargs.get('path', args[0] if args else None)
        if path == "missing.xlsx":
            raise FileNotFoundError
        return real_file_response(*args, **kwargs)

    monkeypatch.setattr(main, "FileResponse", fake_file_response)
    with pytest.raises(HTTPException) as exc:
        await main.download_file("missing.xlsx", user={"username": "test"})
    assert exc.value.status_code == 404
