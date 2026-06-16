"""
Bloque 2 — Testing pre-lanzamiento: Billing y Pagos.
Objetivo: verificar que la plata cobra bien.

Cobertura:
 1. Checkout MP → genera preference (sandbox mockeada).
 2. Webhook pago aprobado: billing_status=active, trial extendido 30 días.
 3. Webhook deduplicación: mismo payment_id no se procesa dos veces.
 4. Webhook firma inválida → 401.
 5. Webhook pago fallado/rechazado → skipped.
 6. Límite 10 ops/mes en plan activo (via require_active_billing).
 7. Trial vencido → 402 (modal de pago).
 8. Top-up: acredita 10 ops, cobra $10k, máx 100 créditos, expiran 30 días.
 9. Billing /me devuelve datos correctos.
10. Clientes ilimitados en plan premium.
11. Users_limit = 3 en plan premium.
12. Planes públicos: solo premium.
"""
import asyncio
import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("EMAIL_VERIFICATION_REQUIRED", "false")

from proyecto_maria.main import app  # noqa: E402
from proyecto_maria.services import billing_service  # noqa: E402
from proyecto_maria.database.connection import get_async_session  # noqa: E402
from proyecto_maria.database.models import User  # noqa: E402
from sqlalchemy.future import select  # noqa: E402


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module", autouse=True)
def _init_db_once():
    """Asegura que las tablas existan (usa la misma DB temporal de conftest)."""
    with TestClient(app):
        pass
    yield


@pytest.fixture
def client():
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    return TestClient(app)


def _unique(prefix="b2"):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _register(client, username: str):
    """Registra usuario y deja cookie activa."""
    resp = client.post("/auth/register", json={
        "username": username,
        "password": "SecureP@ss1",
        "email": f"{username}@test.billing",
        "name": f"User {username}",
    })
    assert resp.status_code == 200, f"Register falló: {resp.text}"
    return resp.json()


def _billing(client) -> dict:
    resp = client.get("/api/billing/me")
    assert resp.status_code == 200, resp.text
    return resp.json()


# ──────────────────────────────────────────────────────────────────────
# Helpers DB
# ──────────────────────────────────────────────────────────────────────

def _set_user(username: str, **kwargs):
    """Modifica campos del user en DB directamente (para simular estados)."""
    async def _run():
        async for db in get_async_session():
            res = await db.execute(select(User).where(User.username == username))
            u = res.scalars().first()
            assert u is not None, f"Usuario {username} no existe en DB"
            for k, v in kwargs.items():
                setattr(u, k, v)
            await db.commit()
            return
    asyncio.new_event_loop().run_until_complete(_run())


def _get_user(username: str) -> dict:
    """Lee campos del user desde DB."""
    result = {}

    async def _run():
        async for db in get_async_session():
            res = await db.execute(select(User).where(User.username == username))
            u = res.scalars().first()
            assert u is not None
            result["billing_status"] = u.billing_status
            result["trial_ends_at"] = u.trial_ends_at
            result["extra_ops_remaining"] = u.extra_ops_remaining
            result["extra_ops_expires_at"] = u.extra_ops_expires_at
            result["ops_used_this_period"] = u.ops_used_this_period
            result["last_payment_id"] = u.last_payment_id
            result["plan"] = u.plan
            return
    asyncio.new_event_loop().run_until_complete(_run())
    return result


# ──────────────────────────────────────────────────────────────────────
# Fake MP SDK (para tests de checkout sin credenciales reales)
# ──────────────────────────────────────────────────────────────────────

class _FakePref:
    def __init__(self, captured):
        self._c = captured

    def create(self, data):
        self._c["data"] = data
        return {
            "status": 201,
            "response": {
                "id": "pref-test-123",
                "init_point": "https://mp.test/checkout",
                "sandbox_init_point": "https://sandbox.mp.test/checkout",
            },
        }


class _FakeSDK:
    captured = {}

    def __init__(self, token):
        _FakeSDK.captured["token"] = token

    def preference(self):
        return _FakePref(_FakeSDK.captured)


# ──────────────────────────────────────────────────────────────────────
# Helper webhook con firma HMAC válida
# ──────────────────────────────────────────────────────────────────────

def _signed_webhook_headers(body: dict, secret: str) -> dict:
    """Genera headers x-signature y x-request-id válidos para el webhook."""
    ts = str(int(datetime.now(timezone.utc).timestamp()))
    req_id = uuid.uuid4().hex
    data_id = str(body.get("data", {}).get("id", ""))
    manifest = f"id:{data_id};request-id:{req_id};ts:{ts};"
    v1 = hmac.new(
        secret.encode("utf-8"),
        manifest.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "x-signature": f"ts={ts},v1={v1}",
        "x-request-id": req_id,
        "content-type": "application/json",
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. CHECKOUT MP → genera preference
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestCheckout:

    def test_checkout_sin_mp_token_modo_demo(self, client, monkeypatch):
        """Sin MP_ACCESS_TOKEN → modo demo con init_point local."""
        _register(client, _unique("co_demo"))
        monkeypatch.delenv("MP_ACCESS_TOKEN", raising=False)
        resp = client.post("/api/billing/checkout", json={"plan": "premium"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "demo"
        assert data["init_point"].startswith("/api/payments/demo-checkout/")

    def test_checkout_sandbox_genera_preference(self, client, monkeypatch):
        """Con token sandbox → genera preference y devuelve sandbox_init_point."""
        _FakeSDK.captured = {}
        _register(client, _unique("co_sb"))
        monkeypatch.setenv("MP_ACCESS_TOKEN", "TEST-token-sandbox")
        monkeypatch.setattr(billing_service.mercadopago, "SDK", _FakeSDK)
        monkeypatch.delenv("FRONTEND_URL", raising=False)

        resp = client.post("/api/billing/checkout", json={"plan": "premium"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "sandbox"
        assert "preference_id" in data or "preapproval_id" in data
        pref = _FakeSDK.captured.get("data", {})
        assert pref.get("external_reference", "").endswith(":premium")

    def test_checkout_plan_invalido_400(self, client, monkeypatch):
        """Plan que no existe → 400."""
        _register(client, _unique("co_bad"))
        monkeypatch.delenv("MP_ACCESS_TOKEN", raising=False)
        resp = client.post("/api/billing/checkout", json={"plan": "enterprise"})
        assert resp.status_code == 400

    def test_checkout_sin_auth_401(self, client, monkeypatch):
        """Sin sesión → 401."""
        client.cookies.clear()
        resp = client.post("/api/billing/checkout", json={"plan": "premium"})
        assert resp.status_code == 401

    def test_checkout_prod_agrega_auto_return(self, client, monkeypatch):
        """En HTTPS prod → auto_return=approved y notification_url en preference."""
        _FakeSDK.captured = {}
        _register(client, _unique("co_prod"))
        monkeypatch.setenv("MP_ACCESS_TOKEN", "APP_USR-token-live")
        monkeypatch.setenv("MP_SANDBOX", "false")
        monkeypatch.setenv("FRONTEND_URL", "https://cdi.example.com")
        monkeypatch.setattr(billing_service.mercadopago, "SDK", _FakeSDK)

        resp = client.post("/api/billing/checkout", json={"plan": "premium"})
        assert resp.status_code == 200
        pref = _FakeSDK.captured.get("data", {})
        assert pref.get("auto_return") == "approved"
        assert pref.get("notification_url") == "https://cdi.example.com/api/payments/webhook"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2–5. WEBHOOK: aprobado, deduplicación, firma, rechazado
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestWebhook:

    def _wh_post(self, client, body, monkeypatch, secret="", is_prod=False, mp_token="TEST-fake", sdk_cls=None):
        """Helper: setea las constantes del módulo y postea al webhook."""
        import proyecto_maria.main as main_mod
        monkeypatch.setattr(main_mod, "MP_WEBHOOK_SECRET", secret)
        monkeypatch.setattr(main_mod, "IS_PRODUCTION", is_prod)
        monkeypatch.setattr(main_mod, "MP_ACCESS_TOKEN", mp_token)
        if sdk_cls:
            monkeypatch.setattr(main_mod.mercadopago, "SDK", sdk_cls)
        return client.post(
            "/api/payments/webhook",
            content=json.dumps(body),
            headers={"content-type": "application/json"},
        )

    def test_firma_invalida_401(self, client, monkeypatch):
        """Webhook con MP_WEBHOOK_SECRET seteado y firma incorrecta → 401."""
        body = {"type": "payment", "data": {"id": "pay-bad"}}
        # Con secret seteado y sin headers de firma → debe rechazar
        resp = self._wh_post(client, body, monkeypatch, secret="supersecret", is_prod=False)
        assert resp.status_code == 401

    def test_firma_valida_en_dev_sin_secret(self, client, monkeypatch):
        """En dev sin MP_WEBHOOK_SECRET → firma omitida (pasa), pero sin token → 400."""
        body = {"type": "payment", "data": {"id": "pay-dev-1"}}
        resp = self._wh_post(client, body, monkeypatch, secret="", is_prod=False, mp_token="")
        # Firma pasa, pero MP_ACCESS_TOKEN vacío → 400
        assert resp.status_code == 400

    def test_evento_no_payment_skipped(self, client, monkeypatch):
        """Evento que no es 'payment' → 200 skipped."""
        body = {"type": "plan", "data": {"id": "plan-1"}}
        resp = self._wh_post(client, body, monkeypatch, secret="", is_prod=False)
        assert resp.status_code == 200
        assert resp.json().get("skipped") is not None

    def test_pago_aprobado_activa_billing_y_extiende_30_dias(self, client, monkeypatch):
        """Pago aprobado → billing_status=active, trial_ends_at ~30 días."""
        uname = _unique("wh_ok")
        _register(client, uname)
        payment_id = f"pay-{uuid.uuid4().hex[:8]}"

        class FakePayment:
            def get(self, pid):
                return {
                    "status": 200,
                    "response": {
                        "id": pid,
                        "status": "approved",
                        "external_reference": f"{uname}:premium",
                        "payer": {"id": "payer-mp-1"},
                        "card": {"last_four_digits": "4242", "payment_method": {"name": "visa"}},
                    },
                }

        class FakeSDKOk:
            def __init__(self, token): pass
            def payment(self): return FakePayment()

        body = {"type": "payment", "data": {"id": payment_id}}
        resp = self._wh_post(client, body, monkeypatch, secret="", is_prod=False,
                             mp_token="TEST-fake", sdk_cls=FakeSDKOk)
        assert resp.status_code == 200, resp.text

        after = _get_user(uname)
        assert after["billing_status"] == "active"
        trial_end = after["trial_ends_at"]
        if trial_end.tzinfo is None:
            trial_end = trial_end.replace(tzinfo=timezone.utc)
        delta = trial_end - datetime.now(timezone.utc)
        assert 28 <= delta.days <= 31, f"trial_ends_at delta: {delta.days} días"

    def test_pago_aprobado_resetea_ops_periodo(self, client, monkeypatch):
        """Al cobrar suscripción, ops_used_this_period se resetea a 0."""
        uname = _unique("wh_ops")
        _register(client, uname)
        _set_user(uname, ops_used_this_period=8)
        payment_id = f"pay-{uuid.uuid4().hex[:8]}"

        class FakePaymentReset:
            def get(self, pid):
                return {
                    "status": 200,
                    "response": {
                        "id": pid,
                        "status": "approved",
                        "external_reference": f"{uname}:premium",
                        "payer": {"id": "payer-2"},
                    },
                }

        class FakeSDKReset:
            def __init__(self, token): pass
            def payment(self): return FakePaymentReset()

        body = {"type": "payment", "data": {"id": payment_id}}
        self._wh_post(client, body, monkeypatch, secret="", is_prod=False,
                      mp_token="TEST-fake", sdk_cls=FakeSDKReset)

        after = _get_user(uname)
        assert after["ops_used_this_period"] == 0

    def test_deduplicacion_mismo_payment_id_no_reprocesa(self, client, monkeypatch):
        """Mismo payment_id enviado dos veces → segunda vez skipped."""
        uname = _unique("wh_dup")
        _register(client, uname)
        payment_id = f"pay-{uuid.uuid4().hex[:8]}"

        class FakePayDup:
            def get(self, pid):
                return {
                    "status": 200,
                    "response": {
                        "id": pid,
                        "status": "approved",
                        "external_reference": f"{uname}:premium",
                        "payer": {"id": "payer-3"},
                    },
                }

        class FakeSDKDup:
            def __init__(self, token): pass
            def payment(self): return FakePayDup()

        import proyecto_maria.main as main_mod
        monkeypatch.setattr(main_mod, "MP_WEBHOOK_SECRET", "")
        monkeypatch.setattr(main_mod, "IS_PRODUCTION", False)
        monkeypatch.setattr(main_mod, "MP_ACCESS_TOKEN", "TEST-fake")
        monkeypatch.setattr(main_mod.mercadopago, "SDK", FakeSDKDup)

        body = {"type": "payment", "data": {"id": payment_id}}
        headers = {"content-type": "application/json"}
        r1 = client.post("/api/payments/webhook", content=json.dumps(body), headers=headers)
        assert r1.status_code == 200

        r2 = client.post("/api/payments/webhook", content=json.dumps(body), headers=headers)
        assert r2.status_code == 200
        assert r2.json().get("skipped") == "payment_id ya procesado"

    def test_pago_rechazado_no_activa_billing(self, client, monkeypatch):
        """Pago rejected → webhook skipped, billing sigue trial."""
        uname = _unique("wh_rej")
        _register(client, uname)

        class FakePayRej:
            def get(self, pid):
                return {
                    "status": 200,
                    "response": {
                        "id": pid,
                        "status": "rejected",
                        "external_reference": f"{uname}:premium",
                    },
                }

        class FakeSDKRej:
            def __init__(self, token): pass
            def payment(self): return FakePayRej()

        body = {"type": "payment", "data": {"id": f"pay-{uuid.uuid4().hex[:8]}"}}
        resp = self._wh_post(client, body, monkeypatch, secret="", is_prod=False,
                             mp_token="TEST-fake", sdk_cls=FakeSDKRej)
        assert resp.status_code == 200
        assert "skipped" in resp.json()

        after = _get_user(uname)
        assert after["billing_status"] == "trial"

    def test_pago_usuario_inexistente_400(self, client, monkeypatch):
        """Pago de usuario inexistente → 400 (MP reintenta)."""
        class FakePayNoUser:
            def get(self, pid):
                return {
                    "status": 200,
                    "response": {
                        "id": pid,
                        "status": "approved",
                        "external_reference": "usuarioquenoeexiste:premium",
                        "payer": {"id": "payer-x"},
                    },
                }

        class FakeSDKNoUser:
            def __init__(self, token): pass
            def payment(self): return FakePayNoUser()

        body = {"type": "payment", "data": {"id": f"pay-{uuid.uuid4().hex[:8]}"}}
        resp = self._wh_post(client, body, monkeypatch, secret="", is_prod=False,
                             mp_token="TEST-fake", sdk_cls=FakeSDKNoUser)
        assert resp.status_code == 400


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. LÍMITE 10 OPS/MES en plan activo (HTTP 402 real via API)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestLimiteOpsActivo:

    def test_plan_activo_permite_10_ops_y_bloquea_11(self, client):
        """Plan activo con 10 ops usadas → 402 en la siguiente."""
        uname = _unique("lim")
        _register(client, uname)
        _set_user(uname,
                  billing_status="active",
                  ops_used_this_period=10,
                  extra_ops_remaining=0)

        # Crear cliente para la operación
        rc = client.post("/api/clientes", json={"nombre": "LimClient"})
        assert rc.status_code == 200, rc.text
        cid = rc.json()["cliente"]["id"]

        resp = client.post("/api/operations/manual", json={
            "client_id": cid,
            "items": [{"descripcion": "Item", "cantidad": 1, "valor_unitario": 10}],
        })
        assert resp.status_code == 402
        detail = resp.json()["detail"]
        assert detail["code"] == "PLAN_LIMIT_EXCEEDED"

    def test_plan_activo_con_0_ops_crea_ok(self, client):
        """Plan activo recién renovado → puede crear operaciones."""
        uname = _unique("lim0")
        _register(client, uname)
        _set_user(uname, billing_status="active", ops_used_this_period=0)

        rc = client.post("/api/clientes", json={"nombre": "LimClient0"})
        cid = rc.json()["cliente"]["id"]

        resp = client.post("/api/operations/manual", json={
            "client_id": cid,
            "items": [{"descripcion": "A", "cantidad": 1, "valor_unitario": 10}],
        })
        assert resp.status_code == 200


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. TRIAL VENCIDO → 402
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTrialVencido:

    def test_trial_vencido_bloquea_operaciones_con_402(self, client):
        """Trial expirado → require_active_billing pasa a past_due y devuelve 402."""
        uname = _unique("tv")
        _register(client, uname)
        _set_user(uname,
                  billing_status="trial",
                  trial_ends_at=datetime.now(timezone.utc) - timedelta(days=1))

        rc = client.post("/api/clientes", json={"nombre": "TrialVencidoClient"})
        # Crear cliente también puede fallar si el billing bloquea
        # Lo importante es que la operación manual devuelva 402
        if rc.status_code == 200:
            cid = rc.json()["cliente"]["id"]
        else:
            # Si también bloquea clientes, salteamos el create
            cid = "dummy"

        resp = client.post("/api/operations/manual", json={
            "client_id": cid,
            "items": [{"descripcion": "A", "cantidad": 1, "valor_unitario": 10}],
        })
        assert resp.status_code == 402
        detail = resp.json()["detail"]
        assert "code" in detail

    def test_trial_vencido_marca_past_due_en_db(self, client):
        """Al detectar trial vencido, require_active_billing actualiza billing_status=past_due."""
        uname = _unique("tv2")
        _register(client, uname)
        _set_user(uname,
                  billing_status="trial",
                  trial_ends_at=datetime.now(timezone.utc) - timedelta(hours=1))

        rc = client.post("/api/clientes", json={"nombre": "TVCheck"})
        if rc.status_code == 200:
            cid = rc.json()["cliente"]["id"]
            client.post("/api/operations/manual", json={
                "client_id": cid,
                "items": [{"descripcion": "A", "cantidad": 1, "valor_unitario": 10}],
            })

        after = _get_user(uname)
        assert after["billing_status"] == "past_due"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. TOP-UP: 10 ops, $10k, máx 100, expiran 30 días
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestTopup:

    def test_topup_price_y_ops_config(self):
        """TOPUP_PRICE_ARS=$10k y TOPUP_OPS=10 según specs."""
        assert billing_service.TOPUP_PRICE_ARS == 10000
        assert billing_service.TOPUP_OPS == 10

    def test_topup_max_creditos_100(self):
        """EXTRA_OPS_MAX=100."""
        assert billing_service.EXTRA_OPS_MAX == 100

    def test_topup_checkout_sin_mp_400(self, client, monkeypatch):
        """Sin MP_ACCESS_TOKEN → topup falla (no hay modo demo para topup)."""
        _register(client, _unique("tu_no_token"))
        monkeypatch.delenv("MP_ACCESS_TOKEN", raising=False)
        resp = client.post("/api/billing/topup", json={})
        # Sin token → billing_service._get_sdk() lanza RuntimeError → 400
        assert resp.status_code == 400

    def test_topup_webhook_acredita_10_ops(self, client, monkeypatch):
        """Webhook topup aprobado → extra_ops_remaining += 10."""
        uname = _unique("tu_ok")
        _register(client, uname)
        _set_user(uname, billing_status="active", extra_ops_remaining=0)
        payment_id = f"pay-{uuid.uuid4().hex[:8]}"

        class FakePayTopup:
            def get(self, pid):
                return {
                    "status": 200,
                    "response": {
                        "id": pid,
                        "status": "approved",
                        "external_reference": f"{uname}:topup",
                        "payer": {"id": "payer-tu"},
                    },
                }

        class FakeSDKTopup:
            def __init__(self, token): pass
            def payment(self): return FakePayTopup()

        import proyecto_maria.main as main_mod
        monkeypatch.setattr(main_mod, "MP_WEBHOOK_SECRET", "")
        monkeypatch.setattr(main_mod, "IS_PRODUCTION", False)
        monkeypatch.setattr(main_mod, "MP_ACCESS_TOKEN", "TEST-fake")
        monkeypatch.setattr(main_mod.mercadopago, "SDK", FakeSDKTopup)

        body = {"type": "payment", "data": {"id": payment_id}}
        resp = client.post("/api/payments/webhook", content=json.dumps(body),
                           headers={"content-type": "application/json"})
        assert resp.status_code == 200, resp.text

        after = _get_user(uname)
        assert after["extra_ops_remaining"] == 10
        exp = after["extra_ops_expires_at"]
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        delta = exp - datetime.now(timezone.utc)
        assert 28 <= delta.days <= 31

    def test_topup_no_supera_max_100(self, client, monkeypatch):
        """Top-up no puede llevar extra_ops_remaining por encima de 100."""
        uname = _unique("tu_cap")
        _register(client, uname)
        _set_user(uname, billing_status="active", extra_ops_remaining=95)
        payment_id = f"pay-{uuid.uuid4().hex[:8]}"

        class FakePayCap:
            def get(self, pid):
                return {
                    "status": 200,
                    "response": {
                        "id": pid,
                        "status": "approved",
                        "external_reference": f"{uname}:topup",
                        "payer": {"id": "payer-cap"},
                    },
                }

        class FakeSDKCap:
            def __init__(self, token): pass
            def payment(self): return FakePayCap()

        import proyecto_maria.main as main_mod
        monkeypatch.setattr(main_mod, "MP_WEBHOOK_SECRET", "")
        monkeypatch.setattr(main_mod, "IS_PRODUCTION", False)
        monkeypatch.setattr(main_mod, "MP_ACCESS_TOKEN", "TEST-fake")
        monkeypatch.setattr(main_mod.mercadopago, "SDK", FakeSDKCap)

        body = {"type": "payment", "data": {"id": payment_id}}
        client.post("/api/payments/webhook", content=json.dumps(body),
                    headers={"content-type": "application/json"})

        after = _get_user(uname)
        assert after["extra_ops_remaining"] == 100  # cap: min(95+10, 100)

    def test_topup_creditos_expiran_30_dias(self):
        """process_payment para topup setea expiry a now+30d."""
        payment = {
            "id": "pay-exp-1",
            "status": "approved",
            "external_reference": "alice:topup",
            "payer": {"id": "payer-1"},
        }
        update = billing_service.process_payment(payment)
        assert update["action"] == "topup"
        delta = update["extra_ops_expires_at"] - datetime.now(timezone.utc)
        assert 29 <= delta.days <= 30


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. BILLING /me
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestBillingMe:

    def test_billing_me_devuelve_campos_correctos(self, client):
        """GET /api/billing/me incluye todos los campos de billing."""
        _register(client, _unique("bm"))
        data = _billing(client)
        assert "billing_status" in data
        assert "ops_used_this_period" in data
        assert "ops_limit" in data
        assert "extra_ops_remaining" in data
        assert "clients_limit" in data
        assert "users_limit" in data
        assert "plan" in data

    def test_billing_me_trial_inicial(self, client):
        """Usuario nuevo arranca en trial."""
        _register(client, _unique("bm_t"))
        data = _billing(client)
        assert data["billing_status"] == "trial"
        assert data["trial_ends_at"] is not None
        assert data["ops_used_this_period"] == 0
        assert data["ops_limit"] == 10
        assert data["plan"] == "premium"

    def test_billing_me_sin_auth_401(self, client):
        """Sin sesión → 401."""
        client.cookies.clear()
        resp = client.get("/api/billing/me")
        assert resp.status_code == 401


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10–11. PLAN PREMIUM: clientes ilimitados, 3 usuarios
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestPlanLimites:

    def test_plan_premium_clientes_ilimitados(self):
        """Plan premium define clients=None (ilimitado)."""
        plan = billing_service.get_plan("premium")
        assert plan["clients"] is None

    def test_plan_premium_users_limit_3(self):
        """Plan premium permite máximo 3 usuarios."""
        plan = billing_service.get_plan("premium")
        assert plan["users"] == 3

    def test_plan_premium_ops_limit_10(self):
        """Plan premium tiene límite de 10 ops/mes."""
        plan = billing_service.get_plan("premium")
        assert plan["ops"] == 10

    def test_plan_premium_precio_30k_ars(self):
        """Plan premium cuesta $30.000 ARS/mes."""
        plan = billing_service.get_plan("premium")
        assert plan["price"] == 30000

    def test_billing_me_clients_limit_none(self, client):
        """GET /api/billing/me devuelve clients_limit=None (ilimitado)."""
        _register(client, _unique("cl_lim"))
        data = _billing(client)
        assert data["clients_limit"] is None

    def test_billing_me_users_limit_3(self, client):
        """GET /api/billing/me devuelve users_limit=3."""
        _register(client, _unique("us_lim"))
        data = _billing(client)
        assert data["users_limit"] == 3


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 12. PLANES PÚBLICOS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestPlanesPublicos:

    def test_get_plans_devuelve_solo_premium(self, client):
        """GET /api/billing/plans → solo plan premium, sin basic."""
        resp = client.get("/api/billing/plans")
        assert resp.status_code == 200
        plans = resp.json()["plans"]
        ids = [p["id"] for p in plans]
        assert "premium" in ids
        assert "basic" not in ids
        assert len(ids) == 1

    def test_get_plans_tiene_campos_requeridos(self, client):
        """Cada plan en la lista incluye id, name, price, ops, clients, users."""
        resp = client.get("/api/billing/plans")
        for p in resp.json()["plans"]:
            assert "id" in p
            assert "name" in p
            assert "price" in p
            assert "ops" in p
            assert "clients" in p
            assert "users" in p

    def test_process_payment_suscripcion(self):
        """billing_service.process_payment para premium → action=subscription."""
        pay = {
            "id": "pay-sub-1",
            "status": "approved",
            "external_reference": "alice:premium",
            "payer": {"id": "payer-alice"},
        }
        update = billing_service.process_payment(pay)
        assert update["action"] == "subscription"
        assert update["plan"] == "premium"
        assert update["billing_status"] == "active"
        assert update["ops_used_this_period"] == 0
        delta = update["trial_ends_at"] - datetime.now(timezone.utc)
        assert 28 <= delta.days <= 31

    def test_process_payment_pending_ignorado(self):
        """Pago pending → process_payment devuelve None."""
        pay = {"id": "p1", "status": "pending", "external_reference": "alice:premium"}
        assert billing_service.process_payment(pay) is None

    def test_process_payment_referencia_invalida_none(self):
        """Referencia sin ':' → None."""
        pay = {"id": "p2", "status": "approved", "external_reference": "invalid"}
        assert billing_service.process_payment(pay) is None
