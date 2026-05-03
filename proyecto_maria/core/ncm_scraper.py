"""
NCM Scraper: datos publicos de alicuotas/licencias/regimen.

Fuentes en orden de preferencia:
1. tarifar.com (datos consolidados de Arancel Externo Comun + AFIP)
2. arancel.com.ar (fallback si tarifar rate-limitea)

Si ambas fallan o el parser no reconoce el HTML, devuelve None y el caller
(ncm_service / vuce_connector) hace fallback al mock. De esta forma la UI
nunca se rompe aunque cambie el HTML de una fuente.

Uso:
    from proyecto_maria.core.ncm_scraper import fetch_ncm_scrape
    data = fetch_ncm_scrape("39269099")
    if data:
        print(data["source"], data["alicuotas"])

Notas:
- Rate limit local simple (min `NCM_SCRAPER_MIN_INTERVAL_MS` entre requests).
- User-Agent identificable (no intentamos parecer un navegador).
- Solo datos publicos. No se evita ningun paywall/login.
- Temporal hasta conseguir credenciales de VUCE/Tarifar oficiales.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------
_USER_AGENT = os.getenv(
    "NCM_SCRAPER_USER_AGENT",
    "CDI-NCM-Bot/1.0 (+https://cdi.local; contacto: soporte@cdi.local)",
)
_TIMEOUT = int(os.getenv("NCM_SCRAPER_TIMEOUT", "8"))
_MIN_INTERVAL_MS = int(os.getenv("NCM_SCRAPER_MIN_INTERVAL_MS", "1000"))

# Rate limiter muy simple: lock global + timestamp ultima request
_RATE_LOCK = threading.Lock()
_LAST_REQUEST_TS = 0.0


def _rate_limited_get(url: str) -> Optional[str]:
    """GET con rate limit global. Devuelve texto o None si falla."""
    global _LAST_REQUEST_TS
    with _RATE_LOCK:
        now = time.time()
        elapsed_ms = (now - _LAST_REQUEST_TS) * 1000.0
        if elapsed_ms < _MIN_INTERVAL_MS:
            time.sleep((_MIN_INTERVAL_MS - elapsed_ms) / 1000.0)
        _LAST_REQUEST_TS = time.time()
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": _USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "es-AR,es;q=0.9",
            },
            timeout=_TIMEOUT,
            allow_redirects=True,
        )
        if resp.status_code != 200:
            logger.warning("[ncm_scraper] %s devolvio %s", url, resp.status_code)
            return None
        return resp.text
    except requests.RequestException as err:
        logger.warning("[ncm_scraper] error al consultar %s: %s", url, err)
        return None


# --------------------------------------------------------------------------
# Normalizacion de NCM
# --------------------------------------------------------------------------
_NCM_DOTS_RE = re.compile(r"[^0-9]")


def _norm_ncm(ncm: str) -> str:
    """Normaliza a 8 digitos limpios."""
    clean = _NCM_DOTS_RE.sub("", str(ncm or ""))
    return clean[:8]


def _ncm_with_dots(ncm: str) -> str:
    """Formato `XXXX.XX.XX` usado por tarifar/arancel."""
    c = _norm_ncm(ncm)
    if len(c) < 8:
        return c
    return f"{c[:4]}.{c[4:6]}.{c[6:8]}"


# --------------------------------------------------------------------------
# Parsers (defensivos: nunca lanzan, devuelven dict parcial o None)
# --------------------------------------------------------------------------
_PCT_PATTERNS = [
    (
        "arancel_base",
        [
            r"Derecho\s+de\s+Importaci[oó]n\s*Extrazona[^%<>]*?([0-9]+(?:[.,][0-9]+)?)\s*%",
            r"Arancel\s+Externo\s+Com[uú]n[^%<>]*?([0-9]+(?:[.,][0-9]+)?)\s*%",
            r"AEC[^%<>]*?([0-9]+(?:[.,][0-9]+)?)\s*%",
            r"DI[E]?[^%<>]*?([0-9]+(?:[.,][0-9]+)?)\s*%",
        ],
    ),
    (
        "arancel_mercosur",
        [
            r"Intrazona[^%<>]*?([0-9]+(?:[.,][0-9]+)?)\s*%",
            r"Mercosur[^%<>]*?([0-9]+(?:[.,][0-9]+)?)\s*%",
        ],
    ),
    (
        "iva",
        [
            r"IVA(?:\s*General)?[^%<>]*?([0-9]+(?:[.,][0-9]+)?)\s*%",
        ],
    ),
    (
        "estadistica",
        [
            r"Estad[ií]stica[^%<>]*?([0-9]+(?:[.,][0-9]+)?)\s*%",
            r"Tasa\s+Estad[ií]stica[^%<>]*?([0-9]+(?:[.,][0-9]+)?)\s*%",
        ],
    ),
    (
        "derechos_exportacion",
        [
            r"Derechos?\s+de\s+Exportaci[oó]n[^%<>]*?([0-9]+(?:[.,][0-9]+)?)\s*%",
            r"DE\b[^%<>]*?([0-9]+(?:[.,][0-9]+)?)\s*%",
        ],
    ),
]


def _to_float(raw: str) -> Optional[float]:
    try:
        return float(raw.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def _extract_alicuotas(html: str) -> Dict[str, float]:
    """Extrae alicuotas buscando patrones texto → %. Devuelve solo las encontradas.

    Limpia tags HTML antes de correr regex para soportar estructuras como
    `<td>Derecho de Importacion</td><td>18%</td>`.
    """
    text = _WHITE_RE.sub(" ", _TAGS_RE.sub(" ", html or ""))
    out: Dict[str, float] = {}
    for key, patterns in _PCT_PATTERNS:
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
            if not m:
                continue
            val = _to_float(m.group(1))
            if val is not None and 0 <= val <= 100:
                out[key] = val
                break
    return out


_DESC_PATTERNS = [
    # h1/h2 con clase/sin clase, como "Descripción: ..."
    r"<h1[^>]*>\s*(?:Descripci[oó]n[:\s]*)?([^<]{5,300})</h1>",
    r"<h2[^>]*>\s*(?:Descripci[oó]n[:\s]*)?([^<]{5,300})</h2>",
    r'<(?:div|span|td)[^>]*class="[^"]*descripcion[^"]*"[^>]*>\s*([^<]{5,300})',
    r"Descripci[oó]n\s*[:\-]\s*([^<\n\r]{5,300})",
]

_TAGS_RE = re.compile(r"<[^>]+>")
_WHITE_RE = re.compile(r"\s+")


def _clean_text(raw: str) -> str:
    no_tags = _TAGS_RE.sub(" ", raw or "")
    return _WHITE_RE.sub(" ", no_tags).strip()


def _extract_descripcion(html: str) -> Optional[str]:
    for pat in _DESC_PATTERNS:
        m = re.search(pat, html, re.IGNORECASE | re.DOTALL)
        if m:
            text = _clean_text(m.group(1))
            if 5 <= len(text) <= 300:
                return text
    return None


_LICENCIA_KEYWORDS = [
    ("SENASA", "Servicio Nacional de Sanidad y Calidad Agroalimentaria"),
    ("ANMAT", "Administraci\u00f3n Nacional de Medicamentos, Alimentos y Tecnolog\u00eda M\u00e9dica"),
    ("ENACOM", "Ente Nacional de Comunicaciones"),
    ("INTI", "Instituto Nacional de Tecnolog\u00eda Industrial"),
    ("INAL", "Instituto Nacional de Alimentos"),
    ("INAME", "Instituto Nacional de Medicamentos"),
    ("DGA", "Direcci\u00f3n General de Aduanas"),
    ("INASE", "Instituto Nacional de Semillas"),
    ("SEDRONAR", "Secretar\u00eda de Programaci\u00f3n para la Prevenci\u00f3n de la Drogadicci\u00f3n"),
    ("RENPRE", "Registro Nacional de Precursores Qu\u00edmicos"),
]


def _extract_licencias(html: str) -> List[Dict[str, Any]]:
    """Busca referencias a organismos de intervencion previa conocidos."""
    out: List[Dict[str, Any]] = []
    for codigo, desc in _LICENCIA_KEYWORDS:
        if re.search(rf"\b{re.escape(codigo)}\b", html):
            out.append({
                "codigo": codigo,
                "descripcion": desc,
                "requerida": True,
            })
    return out


# --------------------------------------------------------------------------
# Parsers por fuente
# --------------------------------------------------------------------------
def _parse_tarifar(html: str, ncm: str) -> Optional[Dict[str, Any]]:
    if not html or "tarifar" not in html.lower() and "posicion" not in html.lower():
        # Heuristica debil: si no parece la pagina esperada, probemos igual
        pass
    alicuotas = _extract_alicuotas(html)
    descripcion = _extract_descripcion(html)
    # Necesitamos al menos alicuota base o descripcion para considerarlo valido
    if not alicuotas and not descripcion:
        return None
    return {
        "ncm": ncm,
        "descripcion": descripcion or "",
        "alicuotas": {
            "arancel_base": alicuotas.get("arancel_base", 0.0),
            "arancel_mercosur": alicuotas.get("arancel_mercosur", 0.0),
            "iva": alicuotas.get("iva", 21.0),
            "estadistica": alicuotas.get("estadistica", 3.0),
            "derechos_exportacion": alicuotas.get("derechos_exportacion", 0.0),
        },
        "licencias": _extract_licencias(html),
        "regimen_especial": "General",
        "unidad_medida": "KG",
        "origen_preferencial": ["Brasil", "Paraguay", "Uruguay"],
        "vigente": True,
        "fuente": "scrape:tarifar",
        "source": "scrape:tarifar",
    }


def _parse_arancel(html: str, ncm: str) -> Optional[Dict[str, Any]]:
    alicuotas = _extract_alicuotas(html)
    descripcion = _extract_descripcion(html)
    if not alicuotas and not descripcion:
        return None
    return {
        "ncm": ncm,
        "descripcion": descripcion or "",
        "alicuotas": {
            "arancel_base": alicuotas.get("arancel_base", 0.0),
            "arancel_mercosur": alicuotas.get("arancel_mercosur", 0.0),
            "iva": alicuotas.get("iva", 21.0),
            "estadistica": alicuotas.get("estadistica", 3.0),
            "derechos_exportacion": alicuotas.get("derechos_exportacion", 0.0),
        },
        "licencias": _extract_licencias(html),
        "regimen_especial": "General",
        "unidad_medida": "KG",
        "origen_preferencial": ["Brasil", "Paraguay", "Uruguay"],
        "vigente": True,
        "fuente": "scrape:arancel",
        "source": "scrape:arancel",
    }


# --------------------------------------------------------------------------
# API publica
# --------------------------------------------------------------------------
def fetch_ncm_scrape(ncm: str) -> Optional[Dict[str, Any]]:
    """Intenta obtener datos reales de NCM desde fuentes publicas.

    Devuelve un dict con las llaves usadas por el sistema (ncm, alicuotas,
    licencias, regimen_especial, unidad_medida, vigente, fuente, source)
    o None si ninguna fuente devolvio algo parseable.

    El caller (ncm_service / vuce_connector) decide el fallback.
    """
    ncm_clean = _norm_ncm(ncm)
    if not ncm_clean or len(ncm_clean) < 6:
        return None

    ncm_dot = _ncm_with_dots(ncm_clean)

    # Fuente 1: tarifar.com
    url1 = f"https://www.tarifar.com/posicion/{ncm_dot}"
    html1 = _rate_limited_get(url1)
    if html1:
        result = _parse_tarifar(html1, ncm_clean)
        if result:
            return result

    # Fuente 2: arancel.com.ar
    url2 = f"https://www.arancel.com.ar/ncm/{ncm_clean}"
    html2 = _rate_limited_get(url2)
    if html2:
        result = _parse_arancel(html2, ncm_clean)
        if result:
            return result

    return None


__all__ = ["fetch_ncm_scrape"]
