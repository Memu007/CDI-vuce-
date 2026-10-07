import os
from pathlib import Path

import pandas as pd
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from proyecto_maria import main
from proyecto_maria.main import app


@pytest.fixture()
def main_client(monkeypatch, auth_override):
    # Ensure each test can tweak env vars safely
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    # auth_override autentica /upload_excel/ sin tocar la DB.
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

    response = main_client.post("/upload_excel_v2/", files=files)

    assert response.status_code == 413
    body = response.json()
    assert "too large" in body["detail"].lower() or "excede" in body["detail"].lower()


def test_upload_excel_rejects_invalid_extension(main_client):
    files = {
        "file": ("payload.txt", b"dummy", "text/plain"),
    }

    response = main_client.post("/upload_excel_v2/", files=files)

    assert response.status_code == 400
    assert "invalid file extension" in response.json()["detail"].lower() or "Solo se permiten" in response.json()["detail"]


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
    # Las descargas viven en la carpeta propia de cada usuario, no sueltas en
    # DATA_DIR: antes cualquier usuario logueado podia bajarse el MARIA.TXT de
    # otro adivinando el numero de factura. Ver tests/test_download_aislamiento.py.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(main, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(main, "DOWNLOADS_DIR", str(tmp_path / "descargas"))

    carpeta_del_usuario = main._user_downloads_dir("test")
    existing = Path(carpeta_del_usuario) / "generated.xlsx"
    existing.write_text("dummy")

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
