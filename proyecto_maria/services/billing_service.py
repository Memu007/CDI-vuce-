"""
Servicio de billing real con MercadoPago.

Soporta dos modos:
1. Suscripciones (preapproval) cuando hay `MP_PREAPPROVAL_PLAN_ID_*` configurado.
2. Checkout API (preference mensual) como fallback.

Planes CDI:
- basic: $15.000 ARS/mes, 4 ops/mes, 10 clientes, 1 usuario.
- premium: $30.000 ARS/mes, ops ilimitadas, clientes ilimitados, 3 usuarios.

Top-up: $10.000 ARS por 10 ops adicionales.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Tuple

import mercadopago


# Lectura dinámica de envs para que tests con monkeypatch funcionen sin recargar módulo.
def _access_token() -> str:
    return os.environ.get("MP_ACCESS_TOKEN", "")


def _is_sandbox() -> bool:
    return _access_token().startswith("TEST-") or os.environ.get("MP_SANDBOX", "true").lower() in ("1", "true", "yes")


def get_frontend_url() -> str:
    url = os.environ.get("FRONTEND_URL", "").rstrip("/")
    if url:
        return url
    return "http://127.0.0.1:8000"


def _preapproval_plan_id(plan_id: str) -> str | None:
    if plan_id == "basic":
        return os.environ.get("MP_PREAPPROVAL_PLAN_ID_BASIC", "") or None
    if plan_id == "premium":
        return os.environ.get("MP_PREAPPROVAL_PLAN_ID_PREMIUM", "") or None
    return None


TOPUP_PRICE_ARS = float(os.environ.get("MP_TOPUP_PRICE_ARS", "10000"))
TOPUP_OPS = int(os.environ.get("MP_TOPUP_OPS", "10"))


# Planes internos. Precios y límites deben coincidir con lo configurado en MP.
# Ola 4 MVP: se ofrece un único plan Premium de $30.000 ARS/mes, 10 ops/mes.
PLANS: dict[str, dict[str, Any]] = {
    "premium": {
        "name": "Premium",
        "price": 30000,
        "ops": 10,
        "clients": None,  # ilimitados
        "users": 3,
    },
}


def is_configured() -> bool:
    """True si hay token de MP configurado."""
    return bool(_access_token())


def _get_sdk():
    token = _access_token()
    if not token:
        raise RuntimeError("MP_ACCESS_TOKEN no configurado")
    return mercadopago.SDK(token)


def get_plan(plan_id: str) -> dict[str, Any]:
    # Ola 4 MVP: solo existe Premium. Cualquier otro id cae a Premium.
    plan = PLANS.get(plan_id)
    if not plan and PLANS:
        return list(PLANS.values())[0]
    if not plan:
        raise ValueError(f"Plan desconocido: {plan_id}")
    return plan


def plans_public() -> list[dict[str, Any]]:
    """Lista de planes seguros para exponer al frontend."""
    return [
        {
            "id": plan_id,
            "name": p["name"],
            "price": p["price"],
            "ops": p["ops"],
            "clients": p["clients"],
            "users": p["users"],
        }
        for plan_id, p in PLANS.items()
    ]



def can_create_operation(user) -> Tuple[bool, str | None]:
    """Chequea si el usuario puede crear una operación según su plan.

    Devuelve (ok, razón).
    """
    status = getattr(user, "billing_status", "none")
    if status not in ("trial", "active"):
        return False, "No tenés una suscripción activa o trial vigente."

    plan_id = getattr(user, "plan", "basic") or "basic"
    plan = get_plan(plan_id)
    ops_limit = plan["ops"]

    # Premium (u otros ilimitados)
    if ops_limit is None:
        return True, None

    used = int(getattr(user, "ops_used_this_period", 0) or 0)
    extra = int(getattr(user, "extra_ops_remaining", 0) or 0)
    if used >= ops_limit:
        if extra <= 0:
            return False, f"Alcanzaste el límite de {ops_limit} operaciones del plan {plan['name']}. Comprá un top-up o actualizá a Premium."
        # Consumimos un crédito extra
        return True, None
    return True, None


def record_operation_created(user):
    """Incrementa contadores y consume extra_ops si hace falta."""
    plan_id = getattr(user, "plan", "basic") or "basic"
    plan = get_plan(plan_id)
    ops_limit = plan["ops"]

    used = int(getattr(user, "ops_used_this_period", 0) or 0)
    extra = int(getattr(user, "extra_ops_remaining", 0) or 0)

    if ops_limit is None:
        user.ops_used_this_period = used + 1
        return

    if used < ops_limit:
        user.ops_used_this_period = used + 1
    elif extra > 0:
        user.extra_ops_remaining = extra - 1
        user.ops_used_this_period = used + 1
    else:
        raise RuntimeError("Límite de operaciones excedido")


def create_checkout(user, plan_id: str) -> dict[str, Any]:
    """Genera checkout MP para el plan elegido.

    Usa preapproval si hay plan_id de MP configurado; sino preference.
    """
    plan = get_plan(plan_id)
    email = getattr(user, "email", None) or ""
    username = getattr(user, "username", "")

    external_reference = f"{username}:{plan_id}"
    base_url = get_frontend_url()
    back_url = f"{base_url}/v2?billing=success"

    mp_preapproval_plan_id = _preapproval_plan_id(plan_id)
    sdk = _get_sdk()

    if mp_preapproval_plan_id:
        preapproval_data = {
            "preapproval_plan_id": mp_preapproval_plan_id,
            "payer_email": email,
            "external_reference": external_reference,
            "back_url": f"{base_url}/v2?billing=success_preapproval",
            "status": "authorized",
        }
        if base_url.startswith("https://"):
            preapproval_data["notification_url"] = f"{base_url}/api/payments/webhook"

        resp = sdk.preapproval().create(preapproval_data)
        if resp.get("status") not in (200, 201):
            raise RuntimeError(f"MP rechazó preapproval: {resp.get('response', {})}")

        result = resp["response"]
        return {
            "mode": "sandbox" if _is_sandbox() else "live",
            "type": "subscription",
            "preapproval_id": result.get("id"),
            "init_point": result.get("init_point") or result.get("sandbox_init_point"),
            "external_reference": external_reference,
        }

    # Fallback: preference de pago único mensual.
    preference_data = {
        "items": [
            {
                "title": f"CDI · Plan {plan['name']}",
                "quantity": 1,
                "unit_price": plan["price"],
                "currency_id": "ARS",
            }
        ],
        "external_reference": external_reference,
        "back_urls": {
            "success": back_url,
            "failure": f"{base_url}/v2?billing=failure",
            "pending": f"{base_url}/v2?billing=pending",
        },
    }
    if email:
        preference_data["payer"] = {"email": email}
    if base_url.startswith("https://"):
        preference_data["auto_return"] = "approved"
        preference_data["notification_url"] = f"{base_url}/api/payments/webhook"

    resp = sdk.preference().create(preference_data)
    if resp.get("status") != 201:
        raise RuntimeError(f"MP rechazó preference: {resp.get('response', {})}")

    result = resp["response"]
    return {
            "mode": "sandbox" if _is_sandbox() else "live",
            "type": "checkout",
            "preference_id": result.get("id"),
            "init_point": result.get("sandbox_init_point") if _is_sandbox() else result.get("init_point"),
        "external_reference": external_reference,
    }


def create_topup_checkout(user) -> dict[str, Any]:
    """Genera una preference de pago único para top-up de 10 ops."""
    email = getattr(user, "email", None) or ""
    username = getattr(user, "username", "")
    external_reference = f"{username}:topup"
    base_url = get_frontend_url()

    sdk = _get_sdk()
    preference_data = {
        "items": [
            {
                "title": "CDI · Pack 10 operaciones adicionales",
                "quantity": 1,
                "unit_price": TOPUP_PRICE_ARS,
                "currency_id": "ARS",
            }
        ],
        "external_reference": external_reference,
        "back_urls": {
            "success": f"{base_url}/v2?billing=topup_success",
            "failure": f"{base_url}/v2?billing=failure",
            "pending": f"{base_url}/v2?billing=pending",
        },
        "auto_return": "approved",
    }
    if email:
        preference_data["payer"] = {"email": email}
    if base_url.startswith("https://"):
        preference_data["notification_url"] = f"{base_url}/api/payments/webhook"

    resp = sdk.preference().create(preference_data)
    if resp.get("status") != 201:
        raise RuntimeError(f"MP rechazó topup: {resp.get('response', {})}")

    result = resp["response"]
    return {
        "mode": "sandbox" if _is_sandbox() else "live",
        "type": "topup",
        "preference_id": result.get("id"),
        "init_point": result.get("sandbox_init_point") if _is_sandbox() else result.get("init_point"),
        "external_reference": external_reference,
    }


def process_payment(payment_info: dict[str, Any]) -> dict[str, Any] | None:
    """Procesa un pago aprobado de MP y devuelve datos para actualizar DB.

    Determina si es pago de plan o top-up a partir del external_reference.
    """
    if payment_info.get("status") != "approved":
        return None

    external_ref = payment_info.get("external_reference", "")
    if ":" not in external_ref:
        return None

    username, kind = external_ref.split(":", 1)
    payer_id = str(payment_info.get("payer", {}).get("id", "") or "")
    payment_id = str(payment_info.get("id", "") or "")
    now = datetime.now(timezone.utc)

    base_update = {
        "username": username,
        "payment_provider": "mercadopago",
        "payment_customer_id": payer_id or payment_id,
        "payment_method_last4": _last4_from_payment(payment_info),
        "payment_method_brand": _brand_from_payment(payment_info),
    }

    if kind == "topup":
        return {
            **base_update,
            "action": "topup",
            "extra_ops_remaining": TOPUP_OPS,
            "last_topup_at": now,
        }

    if kind in PLANS:
        return {
            **base_update,
            "action": "subscription",
            "plan": kind,
            "billing_status": "active",
            "trial_ends_at": now + timedelta(days=30),
            "ops_used_this_period": 0,
            "billing_period_started_at": now,
        }

    return None


def _last4_from_payment(payment_info: dict[str, Any]) -> str | None:
    card = payment_info.get("card", {})
    last4 = card.get("last_four_digits") or card.get("last4")
    if last4:
        return str(last4)
    return None


def _brand_from_payment(payment_info: dict[str, Any]) -> str | None:
    card = payment_info.get("card", {})
    return card.get("payment_method", {}).get("name") or card.get("network")
