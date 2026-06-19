"""Test de regresión para webhook de MercadoPago en modo IPN.

MercadoPago envía notificaciones IPN con query string `?id=...&topic=payment`
cuando el webhook avanzado con firma HMAC no está configurado.
"""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

import pytest
from proyecto_maria import main


def _mock_sdk(payment_id: str = "164743017608", external_ref: str = "test_user:premium", status: str = "approved"):
    sdk = MagicMock()
    sdk.payment.return_value.get.return_value = {
        "status": 200,
        "response": {
            "id": payment_id,
            "status": status,
            "external_reference": external_ref,
            "payer": {"id": "payer_123"},
            "transaction_amount": 30000.00,
        },
    }
    return sdk


@pytest.fixture()
def client(auth_override):
    return TestClient(main.app)


class TestWebhookIPN:
    def test_webhook_ipn_payment_approved(self, client, monkeypatch):
        """IPN topic=payment aprobado activa la cuenta."""
        monkeypatch.setenv("MP_WEBHOOK_SECRET", "test-secret")
        main.MP_WEBHOOK_SECRET = "test-secret"
        main.MP_ACCESS_TOKEN = "test-token"

        # Crear usuario
        uname = "webhook_ipn_user_001"
        client.post("/auth/register", json={
            "username": uname,
            "password": "Pass1234!",
            "email": f"{uname}@test.com",
        })

        with patch.object(main.mercadopago, "SDK", return_value=_mock_sdk(external_ref=f"{uname}:premium")):
            res = client.post(f"/api/payments/webhook?id=164743017608&topic=payment")
            assert res.status_code == 200, res.text
            data = res.json()
            assert data["success"] is True

        # Verificar billing status
        client.post("/auth/login", json={"username": uname, "password": "Pass1234!"})
        billing = client.get("/api/billing/me")
        assert billing.json()["billing_status"] == "active"

    def test_webhook_ipn_merchant_order_skipped(self, client, monkeypatch):
        """IPN topic=merchant_order se ignora sin llamar a MP."""
        monkeypatch.setenv("MP_WEBHOOK_SECRET", "test-secret")
        main.MP_WEBHOOK_SECRET = "test-secret"

        with patch.object(main.mercadopago, "SDK") as sdk_mock:
            res = client.post("/api/payments/webhook?id=41981065886&topic=merchant_order")
            assert res.status_code == 200
            assert res.json()["success"] is True
            sdk_mock.assert_not_called()

    def test_webhook_hmac_invalid_secret(self, client, monkeypatch):
        """Webhook con firma HMAC inválida sigue rechazado."""
        monkeypatch.setenv("MP_WEBHOOK_SECRET", "test-secret")
        main.MP_WEBHOOK_SECRET = "test-secret"

        body = '{"type":"payment","data":{"id":"123"}}'
        res = client.post(
            "/api/payments/webhook",
            content=body,
            headers={
                "content-type": "application/json",
                "x-signature": "ts=1,v1=fake",
                "x-request-id": "x",
            },
        )
        assert res.status_code == 401
