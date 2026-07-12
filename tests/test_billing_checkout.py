"""/api/billing/checkout: modo demo, sandbox/live con back_urls (MP mockeado)."""
import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main


@pytest.fixture()
def client(auth_override):
    return TestClient(main.app)


class _FakePreference:
    def __init__(self, captured):
        self._captured = captured

    def create(self, data):
        self._captured["preference_data"] = data
        return {
            "status": 201,
            "response": {
                "id": "pref-123",
                "init_point": "https://mp.example/checkout",
                "sandbox_init_point": "https://sandbox.mp.example/checkout",
            },
        }


class _FakeSDK:
    captured = {}

    def __init__(self, token):
        _FakeSDK.captured["token"] = token

    def preference(self):
        return _FakePreference(_FakeSDK.captured)


def test_checkout_requiere_auth():
    resp = TestClient(main.app).post("/api/billing/checkout")
    assert resp.status_code == 401


def test_checkout_modo_demo_sin_credenciales(client, monkeypatch):
    monkeypatch.delenv("MP_ACCESS_TOKEN", raising=False)
    resp = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "demo"
    assert data["init_point"].startswith("/api/payments/demo-checkout/")


def test_checkout_sandbox_incluye_back_urls(client, monkeypatch):
    _FakeSDK.captured = {}
    monkeypatch.setenv("MP_ACCESS_TOKEN", "TEST-token-sandbox")
    monkeypatch.setattr(main.billing_service.mercadopago, "SDK", _FakeSDK)
    monkeypatch.delenv("FRONTEND_URL", raising=False)  # dev default: http://127.0.0.1:8000

    resp = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "sandbox"
    assert data["init_point"] == "https://sandbox.mp.example/checkout"

    pref = _FakeSDK.captured["preference_data"]
    assert pref["external_reference"] == "test_user:premium"
    assert pref["back_urls"]["success"].endswith("/dashboard?billing=success")
    assert pref["back_urls"]["failure"].endswith("/dashboard?billing=failure")
    # Sin https publica NO se manda auto_return (MP rechaza localhost)
    assert "auto_return" not in pref
    assert "notification_url" not in pref


def test_checkout_prod_https_agrega_auto_return(client, monkeypatch):
    _FakeSDK.captured = {}
    monkeypatch.setenv("MP_ACCESS_TOKEN", "APP_USR-token-live")
    monkeypatch.setenv("MP_SANDBOX", "false")
    monkeypatch.setattr(main.billing_service.mercadopago, "SDK", _FakeSDK)
    monkeypatch.setenv("FRONTEND_URL", "https://cdi.example.com")

    resp = client.post("/api/billing/checkout", json={"plan": "premium"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "live"
    assert data["init_point"] == "https://mp.example/checkout"

    pref = _FakeSDK.captured["preference_data"]
    assert pref["auto_return"] == "approved"
    assert pref["notification_url"] == "https://cdi.example.com/api/payments/webhook"
    assert pref["back_urls"]["success"] == "https://cdi.example.com/dashboard?billing=success"
