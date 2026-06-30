"""
Cliente de la Central de Informacion publica de VUCE (CIVUCE).

Esta es la API que usa internamente https://www.vuce.gob.ar (herramienta
publica y gratuita) para su buscador de posiciones arancelarias. NO requiere
CUIT, Clave Fiscal ni certificado digital: el propio frontend genera un
token anonimo (`POST /auth/generate` con un email generico) y lo reusa.

Permite, a diferencia de `ncm_scraper.py` (que scrapea HTML de tarifar.com /
arancel.com.ar y solo llega a 8 digitos), obtener:
- El listado completo de posiciones SIM (11 digitos + letra sufijo) de un
  NCM de 8 digitos, con su descripcion.
- Aranceles/tributos reales por posicion SIM (AEC, DIE, DII, TE, IVA, etc).
- Intervenciones/licencias reales por posicion SIM (SENASA, ANMAT, etc).

Uso:
    from proyecto_maria.core.vuce_ci_client import fetch_ncm_completo
    data = fetch_ncm_completo("39269099")
    if data:
        print(data["codigo_sim"], data["alicuotas"])

Notas:
- Datos publicos, mismo mecanismo que usa cualquier visitante del sitio.
- Rate limit local simple (min `VUCE_CI_MIN_INTERVAL_MS` entre requests).
- Si la API cambia o no responde, devuelve None y el caller debe hacer
  fallback (a `ncm_scraper` o al mock), igual que el resto de los conectores.
- Token anonimo cacheado en memoria de proceso; se regenera solo si una
  consulta devuelve 401/403.
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
_BASE_URL = os.getenv("VUCE_CI_BASE_URL", "https://qa.ci.vuce.gob.ar")
_TIMEOUT = int(os.getenv("VUCE_CI_TIMEOUT", "8"))
_MIN_INTERVAL_MS = int(os.getenv("VUCE_CI_MIN_INTERVAL_MS", "600"))
_AUTH_EMAIL = os.getenv("VUCE_CI_AUTH_EMAIL", "vuce@vuce.gob.ar")

_USER_AGENT = os.getenv(
    "VUCE_CI_USER_AGENT",
    "CDI-NCM-Bot/1.0 (+https://cdi.local; contacto: soporte@cdi.local)",
)

_RATE_LOCK = threading.Lock()
_LAST_REQUEST_TS = 0.0

_TOKEN_LOCK = threading.Lock()
_TOKEN: Optional[str] = None


def _rate_limited() -> None:
    global _LAST_REQUEST_TS
    with _RATE_LOCK:
        now = time.time()
        elapsed_ms = (now - _LAST_REQUEST_TS) * 1000.0
        if elapsed_ms < _MIN_INTERVAL_MS:
            time.sleep((_MIN_INTERVAL_MS - elapsed_ms) / 1000.0)
        _LAST_REQUEST_TS = time.time()


def _headers(token: Optional[str] = None) -> Dict[str, str]:
    h = {
        "User-Agent": _USER_AGENT,
        "Accept": "application/json",
    }
    if token:
        h["x-api-key"] = token
    return h


def _generate_token() -> Optional[str]:
    """Genera un token anonimo (igual al que genera el propio sitio web)."""
    _rate_limited()
    try:
        resp = requests.post(
            f"{_BASE_URL}/auth/generate",
            json={"email": _AUTH_EMAIL},
            headers=_headers(),
            timeout=_TIMEOUT,
        )
        if resp.status_code != 200:
            logger.warning("[vuce_ci] auth/generate devolvio %s", resp.status_code)
            return None
        data = resp.json()
        # El front guarda directamente `data` (string JWT) en localStorage.
        token = data if isinstance(data, str) else data.get("data")
        return token
    except requests.RequestException as err:
        logger.warning("[vuce_ci] error al generar token: %s", err)
        return None


def _get_token(force_refresh: bool = False) -> Optional[str]:
    global _TOKEN
    with _TOKEN_LOCK:
        if _TOKEN and not force_refresh:
            return _TOKEN
        _TOKEN = _generate_token()
        return _TOKEN


def _get(path: str, params: Dict[str, Any]) -> Optional[Any]:
    """GET autenticado con un retry automatico si el token vencio."""
    token = _get_token()
    if not token:
        return None
    for attempt in range(2):
        _rate_limited()
        try:
            resp = requests.get(
                f"{_BASE_URL}{path}",
                params=params,
                headers=_headers(token),
                timeout=_TIMEOUT,
            )
        except requests.RequestException as err:
            logger.warning("[vuce_ci] error al consultar %s: %s", path, err)
            return None
        if resp.status_code in (401, 403) and attempt == 0:
            token = _get_token(force_refresh=True)
            if not token:
                return None
            continue
        if resp.status_code != 200:
            logger.warning("[vuce_ci] %s devolvio %s", path, resp.status_code)
            return None
        try:
            return resp.json()
        except ValueError:
            return None
    return None


# --------------------------------------------------------------------------
# Normalizacion de NCM / codigo SIM
# --------------------------------------------------------------------------
_DIGITS_RE = re.compile(r"[^0-9]")


def _norm_ncm(ncm: str) -> str:
    clean = _DIGITS_RE.sub("", str(ncm or ""))
    return clean[:8]


def _ncm_with_dots(ncm: str) -> str:
    c = _norm_ncm(ncm)
    if len(c) < 8:
        return c
    return f"{c[:4]}.{c[4:6]}.{c[6:8]}"


def _is_full_sim_leaf(posicion: str) -> bool:
    """True si `posicion` es un codigo SIM completo (11 digitos + letra)."""
    sin_puntos = (posicion or "").replace(".", "")
    return len(sin_puntos) == 12 and sin_puntos[:11].isdigit() and sin_puntos[11:].isalpha()


# --------------------------------------------------------------------------
# API publica
# --------------------------------------------------------------------------
def fetch_sim_positions(ncm: str) -> List[Dict[str, Any]]:
    """Devuelve las posiciones SIM (11 digitos + letra) de un NCM de 8 digitos.

    Cada item: {"codigo_sim": "3926.90.90.999A", "descripcion": "...", "activo": 1}
    Lista vacia si no hay datos o la fuente no responde.
    """
    ncm_dot = _ncm_with_dots(ncm)
    if not ncm_dot or len(_norm_ncm(ncm)) < 6:
        return []
    data = _get("/bsearch/search", {"posicion": ncm_dot})
    if not data or not isinstance(data.get("data"), list):
        return []
    out = []
    for row in data["data"]:
        pos = row.get("posicion", "")
        if _is_full_sim_leaf(pos):
            out.append({
                "codigo_sim": pos,
                "descripcion": row.get("descripcion", ""),
                "activo": row.get("activo", 1),
            })
    return out


_CLUSTER_MAP = {
    "AEC": "arancel_base",
    "DII": "arancel_mercosur",
    "TE": "estadistica",
    "IVA": "iva",
}
# Nota: en una prueba real (NCM 3926.90.90.100H) "DIE" devolvio 35% mientras
# que "AEC" devolvio 18% para la misma posicion/operacion. Eso contradice la
# sinonimia AEC=DIE=Derecho de Importacion Extrazona que asume ncm_scraper.py
# (ver `_PCT_PATTERNS`). Hasta confirmar que significa "DIE" en este endpoint
# (podria ser un derecho especifico/antidumping, no el extrazona general), NO
# se mapea a ningun campo para evitar mostrar una alicuota incorrecta en una
# declaracion. Tampoco se usan "IVA AD", "Ganancias" ni "IIBB" (parecen ser
# para la Calculadora FOB de exportacion, no para alicuotas de importacion).


def fetch_aranceles(codigo_sim: str, operacion: str = "I") -> Dict[str, float]:
    """Tributos reales (AEC/DIE/DII/TE/IVA, etc) para una posicion SIM completa."""
    data = _get("/tributaciones/obtenerOperacion", {
        "posicion": codigo_sim,
        "operacion": operacion,
    })
    out: Dict[str, float] = {}
    if not data or not isinstance(data.get("data"), list):
        return out
    for row in data["data"]:
        desc = (row.get("descripcion") or "").strip().upper()
        key = _CLUSTER_MAP.get(desc)
        if not key:
            continue
        try:
            out[key] = float(row.get("valor", 0) or 0)
        except (TypeError, ValueError):
            continue
    return out


def fetch_intervenciones(codigo_sim: str, operacion: str = "I") -> List[Dict[str, Any]]:
    """Organismos que intervienen (SENASA, ANMAT, etc) para una posicion SIM.

    El endpoint devuelve TODOS los regimenes configurados para esa posicion,
    incluyendo los opcionales (`regimen.opcional == 1`, ej: regimenes de
    promocion a los que el importador puede adherirse pero no esta obligado).
    Si no se distingue esto, se le muestra al usuario organismos que en
    realidad no le aplican (se vio con NCM 3926.90.90.100H: aparecian RENAR
    y ANAC, que no tienen nada que ver con plastico). `requerida` queda en
    `False` para esos casos en vez de asumir que todo es obligatorio.
    """
    data = _get("/comex/intervenciones/posicion", {
        "posicion": codigo_sim,
        "operacion": operacion,
        "tipoRegimen": 1,
    })
    out: List[Dict[str, Any]] = []
    if not data or not isinstance(data.get("data"), list):
        return out
    for row in data["data"]:
        regimen_obj = row.get("regimen") or {}
        organismo = (row.get("organismo") or {}).get("nombre")
        regimen = regimen_obj.get("descripcion")
        if not organismo and not regimen:
            continue
        es_opcional = bool(regimen_obj.get("opcional"))
        activa = bool(row.get("activa", 1))
        out.append({
            "codigo": organismo or "VUCE",
            "descripcion": regimen or organismo,
            "requerida": activa and not es_opcional,
            "opcional": es_opcional,
        })
    return out


def fetch_ncm_completo(ncm: str, operacion: str = "I") -> Optional[Dict[str, Any]]:
    """Arma un dict de datos NCM compatible con `ncm_scraper.fetch_ncm_scrape`,
    pero con el codigo SIM completo (11 digitos + letra) y datos oficiales.

    Si el NCM tiene varias posiciones SIM, se usa la primera como
    representativa y se listan las demas en `sim_alternativas`.
    """
    ncm_clean = _norm_ncm(ncm)
    posiciones = fetch_sim_positions(ncm_clean)
    if not posiciones:
        return None

    principal = posiciones[0]
    codigo_sim = principal["codigo_sim"]
    aranceles = fetch_aranceles(codigo_sim, operacion)
    licencias = fetch_intervenciones(codigo_sim, operacion)

    return {
        "ncm": ncm_clean,
        "codigo_sim": codigo_sim,
        "sim_alternativas": posiciones[1:],
        "descripcion": principal.get("descripcion", ""),
        "alicuotas": {
            "arancel_base": aranceles.get("arancel_base", 0.0),
            "arancel_mercosur": aranceles.get("arancel_mercosur", 0.0),
            "iva": aranceles.get("iva", 21.0),
            "estadistica": aranceles.get("estadistica", 3.0),
            "derechos_exportacion": aranceles.get("derechos_exportacion", 0.0),
        },
        "licencias": licencias,
        "regimen_especial": "General",
        "unidad_medida": "KG",
        "vigente": True,
        "fuente": "vuce_ci_oficial",
        "source": "vuce_ci_oficial",
    }


__all__ = [
    "fetch_sim_positions",
    "fetch_aranceles",
    "fetch_intervenciones",
    "fetch_ncm_completo",
]
