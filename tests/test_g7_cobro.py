"""G7 · Cobro — evidencia ejecutable de los criterios G7.1, G7.2 y G7.4.

Cada test demuestra un eslabón del ciclo de cobro con la transición de estado
observable vía `GET /api/billing/me`, igual que se pidió para G1: el comando
prueba el criterio, no lo afirma.

Qué NO toca esto (por diseño y por la regla "no tocar la cuenta real de MP"):
- G7.1 usa el webhook de MP con el SDK **mockeado** (mismo patrón que
  `test_webhook_ipn.py`). Demuestra la pata "pago aprobado → active" sin gateway.
  La pata "crear el preapproval real en el sandbox de MP" necesita credenciales
  de MP y queda fuera: es el límite que la PM se reserva levantar.
- G7.3 (corte por señal de impago) no se demuestra acá porque hoy no existe como
  código: se analiza por separado en el informe.
"""
import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("EMAIL_VERIFICATION_REQUIRED", "false")

from proyecto_maria import main  # noqa: E402
from proyecto_maria.main import app  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _init_db_once():
    """Dispara el lifespan una vez para crear tablas (conftest usa un archivo
    temporal compartido, así todas las conexiones ven los mismos datos)."""
    with TestClient(app) as _:
        pass
    yield


@pytest.fixture
def client():
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    return TestClient(app)


TEST_CARD = {
    "cardholder": "Test User",
    "number": "4242 4242 4242 4242",
    "exp": "12/30",
    "cvc": "123",
}


def _register(client, username: str):
    payload = {
        "username": username,
        "password": "originalpass123",
        "email": f"{username}@test.cdi",
        "name": f"User {username}",
        "payment_method": TEST_CARD,
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code in (200, 201), f"register falló: {resp.status_code} {resp.text}"
    return resp.json()


def _me(client) -> dict:
    resp = client.get("/api/billing/me")
    assert resp.status_code == 200, resp.text
    return resp.json()


def _mock_sdk_approved(username: str, plan: str = "premium"):
    """SDK de MP mockeado que devuelve un pago aprobado para {username}:{plan}."""
    sdk = MagicMock()
    sdk.payment.return_value.get.return_value = {
        "status": 200,
        "response": {
            "id": "999000111",
            "status": "approved",
            "external_reference": f"{username}:{plan}",
            "payer": {"id": "payer_g7"},
            "transaction_amount": 45000.00,  # el precio del plan (COBRO-MP-1)
            "currency_id": "ARS",
        },
    }
    return sdk


async def _set_trial_ends_at(username: str, when: datetime):
    from sqlalchemy.future import select
    from proyecto_maria.database.connection import get_async_session
    from proyecto_maria.database.models import User

    async for db in get_async_session():
        res = await db.execute(select(User).where(User.username == username))
        u = res.scalars().first()
        assert u is not None
        u.trial_ends_at = when
        await db.commit()
        return


# ---------------------------------------------------------------------------
# G7.1 — Cobro: webhook de pago aprobado lleva al usuario a `active` (+30 d).
# ---------------------------------------------------------------------------
def test_g7_1_cobro_aprobado_activa_el_plan(client, monkeypatch):
    """trial --(webhook payment approved)--> active con trial_ends_at a +30 d.

    SDK de MP mockeado: no se toca ninguna cuenta real ni webhook a producción.
    """
    monkeypatch.setenv("MP_WEBHOOK_SECRET", "test-secret")
    main.MP_WEBHOOK_SECRET = "test-secret"
    main.MP_ACCESS_TOKEN = "test-token"

    uname = "g7_cobro_001"
    _register(client, uname)

    antes = _me(client)
    assert antes["billing_status"] == "trial", antes

    with patch.object(main.mercadopago, "SDK", return_value=_mock_sdk_approved(uname)):
        wh = client.post(f"/api/payments/webhook?id=999000111&topic=payment")
        assert wh.status_code == 200, wh.text
        assert wh.json()["success"] is True

    despues = _me(client)
    assert despues["billing_status"] == "active", despues
    # trial_ends_at debe quedar ~+30 d (proceso setea now + 30 días).
    fin = datetime.fromisoformat(despues["trial_ends_at"])
    if fin.tzinfo is None:  # la API puede devolverlo naive (SQLite)
        fin = fin.replace(tzinfo=timezone.utc)
    delta_dias = (fin - datetime.now(timezone.utc)).days
    assert 29 <= delta_dias <= 30, f"trial_ends_at a {delta_dias} días, esperaba ~30"


# ---------------------------------------------------------------------------
# G7.2 — Corte por vencimiento: trial vencido → 402 al crear una operación.
# ---------------------------------------------------------------------------
def test_g7_2_corte_por_vencimiento_devuelve_402(client):
    """Un usuario cuyo trial venció recibe 402 PLAN_LIMIT_EXCEEDED. Sin MP:
    se adelanta trial_ends_at en la base descartable."""
    import asyncio

    uname = "g7_corte_002"
    _register(client, uname)
    assert _me(client)["billing_status"] == "trial"

    # Vencer el trial en la base (ayer).
    asyncio.new_event_loop().run_until_complete(
        _set_trial_ends_at(uname, datetime.now(timezone.utc) - timedelta(days=1))
    )

    resp = client.post("/api/operations/manual", json={"client_id": "x", "items": []})
    assert resp.status_code == 402, resp.text
    detail = resp.json()["detail"]
    # Desde VUCE-3 la razón del 402 es distinguible: trial vencido -> TRIAL_EXPIRED.
    assert detail["code"] == "TRIAL_EXPIRED", detail
    assert detail["billing_status"] == "past_due", detail


def test_g7_2_control_trial_vigente_no_corta(client):
    """Control: la MISMA llamada con el trial vigente NO da 402. Prueba que el
    corte de G7.2 lo causa el vencimiento, no el endpoint en sí (acá el gate
    deja pasar y falla recién la validación del body → 400)."""
    uname = "g7_control_002b"
    _register(client, uname)
    assert _me(client)["billing_status"] == "trial"

    resp = client.post("/api/operations/manual", json={"client_id": "x", "items": []})
    assert resp.status_code != 402, resp.text
    assert resp.status_code == 400, resp.text  # gate OK; body vacío → 400


# ---------------------------------------------------------------------------
# G7.4 — Reactivación: tras el corte, un nuevo cobro vuelve a `active`.
# ---------------------------------------------------------------------------
def test_g7_4_reactivacion_tras_corte_vuelve_a_active(client):
    """past_due --(simulate-charge = cobro exitoso sin gateway)--> active."""
    import asyncio

    uname = "g7_react_004"
    _register(client, uname)

    # Llevarlo a past_due: vencer el trial y disparar el gate con una operación.
    asyncio.new_event_loop().run_until_complete(
        _set_trial_ends_at(uname, datetime.now(timezone.utc) - timedelta(days=1))
    )
    corte = client.post("/api/operations/manual", json={"client_id": "x", "items": []})
    assert corte.status_code == 402, corte.text
    assert _me(client)["billing_status"] == "past_due"

    # Nuevo cobro exitoso (simulate-charge: no llama a ningún gateway).
    charge = client.post("/api/billing/simulate-charge")
    assert charge.status_code == 200, charge.text
    body = charge.json()
    assert body["billing_status"] == "active", body

    despues = _me(client)
    assert despues["billing_status"] == "active", despues
