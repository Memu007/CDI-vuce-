"""CSRF double-submit cookie: middleware + cookies de sesion.

Usa el flujo real de register (deja access_token + csrf_token en el client)
porque el middleware solo actua cuando la sesion va por cookie.
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("EMAIL_VERIFICATION_REQUIRED", "false")

from proyecto_maria.main import app  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _init_db_once():
    # Dispara el lifespan para crear las tablas en el engine de tests.
    with TestClient(app) as _:
        pass


@pytest.fixture()
def cookie_client():
    client = TestClient(app)
    username = f"csrf_{uuid.uuid4().hex[:10]}"
    resp = client.post("/auth/register", json={
        "username": username,
        "password": "testpass123",
        "email": f"{username}@test.cdi",
        "name": username,
    })
    assert resp.status_code == 200, resp.text
    return client


def test_register_sets_csrf_cookie(cookie_client):
    assert cookie_client.cookies.get("csrf_token")


def test_report_only_no_bloquea_sin_header(cookie_client, monkeypatch):
    monkeypatch.delenv("CSRF_ENFORCE", raising=False)
    resp = cookie_client.post("/api/backup/localStorage", json={"x": 1})
    assert resp.status_code == 200


def test_enforce_bloquea_sin_header(cookie_client, monkeypatch):
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    resp = cookie_client.post("/api/backup/localStorage", json={"x": 1})
    assert resp.status_code == 403
    assert resp.json()["code"] == "csrf_failed"


def test_enforce_pasa_con_header_valido(cookie_client, monkeypatch):
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    token = cookie_client.cookies.get("csrf_token")
    resp = cookie_client.post(
        "/api/backup/localStorage",
        json={"x": 1},
        headers={"X-CSRF-Token": token},
    )
    assert resp.status_code == 200


def test_enforce_bloquea_header_invalido(cookie_client, monkeypatch):
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    resp = cookie_client.post(
        "/api/backup/localStorage",
        json={"x": 1},
        headers={"X-CSRF-Token": "token-falso"},
    )
    assert resp.status_code == 403


def test_enforce_no_afecta_bearer_sin_cookie(monkeypatch):
    # Sin cookie de sesion el middleware no aplica (no es atacable via CSRF).
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    client = TestClient(app)
    resp = client.post("/api/backup/localStorage", json={"x": 1})
    assert resp.status_code == 401  # rebota por auth, no por CSRF


def test_logout_borra_csrf_cookie(cookie_client):
    resp = cookie_client.post(
        "/auth/logout",
        headers={"X-CSRF-Token": cookie_client.cookies.get("csrf_token") or ""},
    )
    assert resp.status_code == 200
    assert not cookie_client.cookies.get("csrf_token")
