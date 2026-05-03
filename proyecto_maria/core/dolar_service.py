"""
Cotizaciones USD (AR) con cache en memoria. Fuente: dolarapi.com (publico, sin API key).

TTL: 15 min (configurar con DOLAR_CACHE_TTL_SECONDS).
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# Cache simple modulo-level (un solo proceso uvicorn; suficiente para el dashboard)
_cache: Optional[Dict[str, Any]] = None
_cache_ts: float = 0.0

DOLARAPI_BASE = (os.environ.get("DOLARAPI_BASE") or "https://dolarapi.com/v1/dolares").rstrip(
    "/"
)
TTL = max(60, int(os.environ.get("DOLAR_CACHE_TTL_SECONDS", str(15 * 60))))


async def _fetch_casa(
    client: httpx.AsyncClient, slug: str
) -> Optional[Dict[str, Any]]:
    url = f"{DOLARAPI_BASE}/{slug}"
    try:
        r = await client.get(url, timeout=httpx.Timeout(10.0))
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("dolarapi %s: %s", slug, e)
        return None


def _to_public_row(raw: Optional[Dict[str, Any]], key: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    return {
        "key": key,
        "nombre": raw.get("nombre") or key,
        "compra": raw.get("compra"),
        "venta": raw.get("venta"),
        "fecha_actualizacion": raw.get("fechaActualizacion"),
        "casa": raw.get("casa"),
    }


async def get_dolar_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    """Retorna ofical + blue (y bolsa MEP) con cache 15 min."""
    global _cache, _cache_ts
    now = time.time()
    if (
        not force_refresh
        and _cache is not None
        and (now - _cache_ts) < TTL
    ):
        remaining = max(0, int(TTL - (now - _cache_ts)))
        return {**_cache, "cache": "hit", "cache_ttl_remaining_sec": remaining}

    async with httpx.AsyncClient() as client:
        oficial, blue, bolsa = await _gather_cotizaciones(client)

    out: Dict[str, Any] = {
        "ok": bool(oficial or blue or bolsa),
        "oficial": _to_public_row(oficial, "oficial"),
        "blue": _to_public_row(blue, "blue"),
        "mep": _to_public_row(bolsa, "mep"),
        "fuente": "dolarapi.com",
        "cache_ttl_seconds": TTL,
        "cache": "miss",
    }
    if out["ok"]:
        _cache = {
            "ok": out["ok"],
            "oficial": out["oficial"],
            "blue": out["blue"],
            "mep": out["mep"],
            "fuente": out["fuente"],
            "cache_ttl_seconds": out["cache_ttl_seconds"],
        }
        _cache_ts = now
    return out


async def _gather_cotizaciones(
    client: httpx.AsyncClient,
) -> Tuple[Optional[dict], Optional[dict], Optional[dict]]:
    """Paraleliza 3 GETs a dolarapi."""
    t1 = asyncio.create_task(_fetch_casa(client, "oficial"))
    t2 = asyncio.create_task(_fetch_casa(client, "blue"))
    t3 = asyncio.create_task(_fetch_casa(client, "bolsa"))
    a, b, c = await asyncio.gather(t1, t2, t3, return_exceptions=True)
    for x in (a, b, c):
        if isinstance(x, Exception):
            logger.debug("dolar gather: %s", x)
    return (
        a if isinstance(a, dict) else None,
        b if isinstance(b, dict) else None,
        c if isinstance(c, dict) else None,
    )
