"""
Novedades ARCA
--------------
Consume el feed XML público de ARCA/AFIP y lo expone como JSON con caché
en memoria (TTL configurable).

Fuente oficial (descubierta en el JS de la home de arca.gob.ar):
    https://servicioscf.afip.gob.ar/publico/sitio/contenido/novedad/listadoxml.aspx
"""
from __future__ import annotations

import logging
import os
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)

ARCA_NOVEDADES_XML_URL = (
    os.environ.get("ARCA_NOVEDADES_XML_URL")
    or "https://servicioscf.afip.gob.ar/publico/sitio/contenido/novedad/listadoxml.aspx"
)
ARCA_NOVEDADES_WEB_URL = (
    os.environ.get("ARCA_NOVEDADES_WEB_URL")
    or "https://servicioscf.afip.gob.ar/publico/sitio/contenido/novedad/listado.aspx"
)
# TTL default: 15 min (900 s). La home de ARCA no cambia cada minuto.
TTL_SECONDS = max(60, int(os.environ.get("ARCA_NOVEDADES_TTL_SECONDS", str(15 * 60))))
REQUEST_TIMEOUT = max(3, min(20, int(os.environ.get("ARCA_NOVEDADES_TIMEOUT_SECONDS", "8"))))

_cache: Optional[Dict[str, Any]] = None
_cache_ts: float = 0.0


def _safe_text(element: Optional[ET.Element]) -> str:
    if element is None:
        return ""
    # CDATA se lee como text; strip para evitar espacios sucios.
    return (element.text or "").strip()


def _parse_items(xml_text: str) -> List[Dict[str, str]]:
    """Parsea el XML de ARCA y devuelve una lista de novedades."""
    items: List[Dict[str, str]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.warning("ARCA novedades: XML inválido: %s", e)
        return items

    for item in root.findall("item"):
        titulo = _safe_text(item.find("titulo"))
        link = _safe_text(item.find("link"))
        imagen = _safe_text(item.find("imagen"))
        if titulo:
            items.append({
                "titulo": titulo,
                "link": link or ARCA_NOVEDADES_WEB_URL,
                "imagen": imagen or "",
            })
    return items


async def fetch_arca_novedades(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Retorna las últimas novedades de ARCA con caché.

    Estructura de retorno:
        {
            "ok": bool,
            "items": [{"titulo": str, "link": str, "imagen": str}, ...],
            "fuente": str,
            "fuente_web": str,
            "cache": "hit" | "miss",
            "cache_age_seconds": int | None,
        }
    """
    global _cache, _cache_ts

    now = time.time()
    if (
        not force_refresh
        and _cache is not None
        and (now - _cache_ts) < TTL_SECONDS
    ):
        age = int(now - _cache_ts)
        return {
            **_cache,
            "cache": "hit",
            "cache_age_seconds": age,
            "cache_ttl_seconds": TTL_SECONDS,
        }

    items: List[Dict[str, str]] = []
    ok = False
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(ARCA_NOVEDADES_XML_URL, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            items = _parse_items(r.text)
            ok = len(items) > 0
    except Exception as e:
        logger.warning("ARCA novedades: error al consultar fuente: %s", e)
        ok = False

    out: Dict[str, Any] = {
        "ok": ok,
        "items": items[:5],  # solo las últimas 5
        "fuente": ARCA_NOVEDADES_XML_URL,
        "fuente_web": ARCA_NOVEDADES_WEB_URL,
        "cache": "miss",
        "cache_age_seconds": 0,
        "cache_ttl_seconds": TTL_SECONDS,
    }

    if ok:
        _cache = {
            "ok": out["ok"],
            "items": out["items"],
            "fuente": out["fuente"],
            "fuente_web": out["fuente_web"],
        }
        _cache_ts = now

    return out
