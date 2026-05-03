"""
Billing simulado para el alta.

Valida datos de tarjeta (Luhn + expiry + CVC) sin cobrar nada ni llamar a
ningun gateway. Cuando se integre Stripe/MP real, reemplazar `validate_and_detect`
por la llamada correspondiente (Stripe SetupIntent o MP CardToken).

Expone:
- validate_and_detect(card: dict) -> dict con {brand, last4, customer_id}
- CardValidationError: raised cuando algun campo falla, con mensaje humano.
"""

from __future__ import annotations

import re
import uuid
from datetime import date


class CardValidationError(ValueError):
    """Falla de validacion de tarjeta con mensaje apto para mostrar al user."""


_BRAND_PREFIXES = [
    (re.compile(r"^4"), "visa"),
    (re.compile(r"^5[1-5]"), "master"),
    (re.compile(r"^2[2-7]"), "master"),
    (re.compile(r"^3[47]"), "amex"),
    (re.compile(r"^6011|^65"), "discover"),
]


def _detect_brand(digits: str) -> str:
    for rx, name in _BRAND_PREFIXES:
        if rx.search(digits):
            return name
    return "other"


def _passes_luhn(digits: str) -> bool:
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _parse_expiry(exp: str) -> tuple[int, int]:
    """Acepta 'MM/YY' o 'MM/YYYY'. Devuelve (month, year)."""
    s = (exp or "").strip().replace(" ", "")
    m = re.match(r"^(\d{2})\s*/\s*(\d{2}|\d{4})$", s)
    if not m:
        raise CardValidationError("Vencimiento invalido. Usar formato MM/YY.")
    month = int(m.group(1))
    year_raw = m.group(2)
    year = int(year_raw) if len(year_raw) == 4 else 2000 + int(year_raw)
    if not (1 <= month <= 12):
        raise CardValidationError("Mes de vencimiento invalido.")
    return month, year


def validate_and_detect(card: dict) -> dict:
    """Valida inputs de tarjeta y devuelve metadata segura para persistir.

    No guarda numero completo ni CVC en ningun lado.
    """
    if not isinstance(card, dict):
        raise CardValidationError("Datos de tarjeta faltantes.")

    cardholder = (card.get("cardholder") or "").strip()
    number_raw = (card.get("number") or "").strip()
    exp = (card.get("exp") or "").strip()
    cvc = (card.get("cvc") or "").strip()

    if len(cardholder) < 2:
        raise CardValidationError("Titular invalido.")

    digits = re.sub(r"\D", "", number_raw)
    if len(digits) < 13 or len(digits) > 19:
        raise CardValidationError("Numero de tarjeta invalido.")
    if not _passes_luhn(digits):
        raise CardValidationError("Numero de tarjeta invalido (no pasa Luhn).")

    brand = _detect_brand(digits)

    cvc_len_ok = (len(cvc) == 4) if brand == "amex" else (len(cvc) == 3)
    if not (cvc.isdigit() and cvc_len_ok):
        raise CardValidationError("CVC invalido.")

    month, year = _parse_expiry(exp)
    today = date.today()
    if (year, month) < (today.year, today.month):
        raise CardValidationError("La tarjeta esta vencida.")

    return {
        "brand": brand,
        "last4": digits[-4:],
        "customer_id": f"sim_cus_{uuid.uuid4().hex[:16]}",
    }
