"""Test de regresión para la firma HMAC del webhook de MercadoPago.

Path crítico: si la validación falla, cualquiera puede activar premium gratis
hiteando POST /api/payments/webhook. Por eso queremos red mínima.
"""
import hashlib
import hmac
import json
import os
from unittest.mock import MagicMock


def _build_signed_request(secret: str, data_id: str = "12345", req_id: str = "abc-req-1", ts: str = "1700000000"):
    """Arma un request mock con firma válida para el secret dado."""
    body = json.dumps({"type": "payment", "data": {"id": data_id}}).encode("utf-8")
    manifest = f"id:{data_id};request-id:{req_id};ts:{ts};"
    v1 = hmac.new(secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).hexdigest()
    req = MagicMock()
    req.headers = {"x-signature": f"ts={ts},v1={v1}", "x-request-id": req_id}
    return req, body


def test_signature_valid_passes(monkeypatch):
    """Firma correcta → True."""
    monkeypatch.setenv("MP_WEBHOOK_SECRET", "test-secret-xyz")
    # Reimport para que el módulo levante el secret nuevo
    import importlib
    from proyecto_maria import main as m
    m.MP_WEBHOOK_SECRET = "test-secret-xyz"  # pisar global

    req, body = _build_signed_request("test-secret-xyz")
    assert m._verify_mp_webhook_signature(req, body) is True


def test_signature_wrong_secret_fails(monkeypatch):
    """Firma armada con otro secret → False."""
    from proyecto_maria import main as m
    m.MP_WEBHOOK_SECRET = "real-secret"

    req, body = _build_signed_request("attacker-secret")
    assert m._verify_mp_webhook_signature(req, body) is False


def test_signature_missing_headers_fails(monkeypatch):
    """Sin headers de firma → False."""
    from proyecto_maria import main as m
    m.MP_WEBHOOK_SECRET = "real-secret"

    req = MagicMock()
    req.headers = {}
    body = b'{"type":"payment","data":{"id":"123"}}'
    assert m._verify_mp_webhook_signature(req, body) is False


def test_signature_no_secret_in_prod_rejects(monkeypatch):
    """En prod sin secret seteado → rechaza siempre (defensa en profundidad)."""
    from proyecto_maria import main as m
    m.MP_WEBHOOK_SECRET = ""
    monkeypatch.setattr(m, "IS_PRODUCTION", True)

    req = MagicMock()
    req.headers = {"x-signature": "ts=1,v1=fake", "x-request-id": "x"}
    body = b'{"type":"payment","data":{"id":"123"}}'
    assert m._verify_mp_webhook_signature(req, body) is False


def test_signature_no_secret_in_dev_allows(monkeypatch):
    """En dev sin secret → True (para no frenar tests locales)."""
    from proyecto_maria import main as m
    m.MP_WEBHOOK_SECRET = ""
    monkeypatch.setattr(m, "IS_PRODUCTION", False)

    req = MagicMock()
    req.headers = {}
    body = b''
    assert m._verify_mp_webhook_signature(req, body) is True
