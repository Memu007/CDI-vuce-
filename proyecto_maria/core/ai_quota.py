"""Cuota diaria de uso de IA por usuario.

Defensa contra abuso / facturazo de tokens en endpoints que llaman al LLM
(hoy: subida de PDF -> Gemini). Funciona en memoria, sin Redis: en una
deployment multi-worker cada worker tiene su propio contador, asi que
el limite real puede ser N*limit. Para una beta es defensa razonable
contra abuso obvio; cuando haya Redis se migra el storage.

Variables:
- `AI_DAILY_PDF_LIMIT`: PDFs por usuario por dia (default 50).
- `AI_DAILY_MIGRATION_LIMIT`: archivos ambiguos por usuario por dia (default 10).

Uso:
    from proyecto_maria.core.ai_quota import enforce_pdf_quota
    enforce_pdf_quota(user["username"])
"""

from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from fastapi import HTTPException

# Storage en memoria: {(username, yyyy-mm-dd): count}
_counter: dict[tuple[str, str], int] = {}
_lock = threading.Lock()


def _today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _get_limit() -> int:
    try:
        return max(1, int(os.getenv("AI_DAILY_PDF_LIMIT", "50")))
    except (TypeError, ValueError):
        return 50


def _get_migration_limit() -> int:
    try:
        return max(1, int(os.getenv("AI_DAILY_MIGRATION_LIMIT", "10")))
    except (TypeError, ValueError):
        return 10


def enforce_pdf_quota(username: str | None) -> None:
    """Suma 1 al contador del usuario para hoy. Si excede, levanta 429.

    Si `username` viene vacio, no aplicamos cuota (caso edge: testing).
    """
    if not username:
        return
    limit = _get_limit()
    key = (username, _today_key())
    with _lock:
        current = _counter.get(key, 0)
        if current >= limit:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Limite diario de procesamiento de PDFs alcanzado "
                    f"({limit}/dia). Probá mañana o pedí ampliación."
                ),
            )
        _counter[key] = current + 1


def enforce_migration_quota(username: str | None) -> None:
    """Limita el fallback Gemini del migrador sin mezclarlo con PDFs."""

    if not username:
        return
    limit = _get_migration_limit()
    key = (f"migration:{username}", _today_key())
    with _lock:
        current = _counter.get(key, 0)
        if current >= limit:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Limite diario de analisis inteligente de migraciones "
                    f"alcanzado ({limit}/dia)."
                ),
            )
        _counter[key] = current + 1


def current_usage(username: str) -> dict:
    """Devuelve {used, limit, remaining} del dia para este usuario."""
    limit = _get_limit()
    used = _counter.get((username, _today_key()), 0)
    return {"used": used, "limit": limit, "remaining": max(0, limit - used)}


def reset_for_tests() -> None:
    """Solo para tests: vacia el contador."""
    with _lock:
        _counter.clear()
