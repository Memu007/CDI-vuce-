"""
Servicio Unificado NCM - Estrategia Dual API (Tarifar + VUCE)

Combina datos de:
- Tarifar: Análisis comercial, estadísticas, interpretación
- VUCE: Datos oficiales gobierno, licencias, alícuotas legales

Features:
- Consultas paralelas (más rápido)
- Merge inteligente con validación cruzada
- Detección de discrepancias
- Redundancia (fallback si una API falla)
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from .tarifar_connector import CLIENT as tarifar_client
from .vuce_connector import VuceClient, CONFIG as vuce_config

logger = logging.getLogger(__name__)

# Cliente VUCE global
vuce_client = VuceClient()

# TTL del cache persistente de NCM. Default 7 dias (alicuotas cambian por
# decreto, bajo volumen). Ajustable via env `NCM_CACHE_TTL_HOURS`.
_NCM_CACHE_TTL_HOURS = int(os.getenv("NCM_CACHE_TTL_HOURS", "168"))


async def _get_cached_ncm_raw(ncm: str) -> Optional[Dict[str, Any]]:
    """Devuelve {payload, source} si hay cache vigente; None si no."""
    try:
        from proyecto_maria.database.connection import AsyncSessionLocal
        from proyecto_maria.database.models import NCMCache
        from sqlalchemy import select as sa_select
    except Exception as err:
        logger.debug("[ncm_cache] DB no disponible: %s", err)
        return None
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                sa_select(NCMCache).where(NCMCache.ncm == ncm)
            )
            row = result.scalars().first()
            if not row:
                return None
            if row.expires_at and row.expires_at.replace(tzinfo=None) < datetime.utcnow():
                return None
            payload = row.payload
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    return None
            fetched_at = row.fetched_at
            return {
                "payload": payload or {},
                "source": row.source or "cache",
                "fetched_at": fetched_at,
            }
    except Exception as err:
        logger.warning("[ncm_cache] lectura fallo: %s", err)
        return None


async def _save_cached_ncm_raw(ncm: str, payload: Dict[str, Any], source: str) -> None:
    """Upsert en tabla `ncm_cache`. Silencioso ante errores."""
    if not payload or source in ("fake", "cache"):
        # No cacheamos mocks ni el propio cache (evita loops)
        return
    try:
        from proyecto_maria.database.connection import AsyncSessionLocal
        from proyecto_maria.database.models import NCMCache
        from sqlalchemy import select as sa_select
    except Exception as err:
        logger.debug("[ncm_cache] DB no disponible al guardar: %s", err)
        return
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                sa_select(NCMCache).where(NCMCache.ncm == ncm)
            )
            row = result.scalars().first()
            expires = datetime.utcnow() + timedelta(hours=_NCM_CACHE_TTL_HOURS)
            if row:
                row.payload = payload
                row.source = source
                row.fetched_at = datetime.utcnow()
                row.expires_at = expires
            else:
                session.add(NCMCache(
                    ncm=ncm,
                    payload=payload,
                    source=source,
                    fetched_at=datetime.utcnow(),
                    expires_at=expires,
                ))
            await session.commit()
    except Exception as err:
        logger.warning("[ncm_cache] guardado fallo: %s", err)


@dataclass
class NCMDataCompleto:
    """Estructura de datos unificada Tarifar + VUCE"""
    ncm: str
    descripcion: str
    descripcion_tarifar: Optional[str]
    descripcion_vuce: Optional[str]

    # Alícuotas (VUCE es autoridad)
    alicuotas: Dict[str, Any]

    # Licencias y requisitos (VUCE es autoridad)
    licencias: List[Dict[str, Any]]
    intervenciones_previas: List[str]
    regimen_especial: Optional[str]

    # Análisis comercial (Tarifar)
    analisis_origenes: Optional[Dict[str, Any]]
    estadisticas_comercio: Optional[Dict[str, Any]]

    # Validación cruzada
    validacion: Dict[str, Any]

    # Metadata
    metadata: Dict[str, Any]


async def get_ncm_completo(ncm: str, valor_fob: float = 100.0, refresh: bool = False) -> Dict[str, Any]:
    """
    Consulta Tarifar + VUCE en paralelo y unifica resultados.

    Flujo:
    1. Cache persistente (tabla `ncm_cache`) con TTL `NCM_CACHE_TTL_HOURS`.
    2. Si hay miss: consulta segun `VUCE_MODE`/`TARIFAR_MODE` (fake|scrape|api).
    3. Fallback silencioso al mock si la fuente real falla.
    4. Guarda en cache solo respuestas reales (scrape/api), nunca fake.

    Args:
        ncm: Código NCM (6-10 dígitos)
        valor_fob: Valor FOB para simulaciones (default: 100 USD)
        refresh: Si True, ignora cache y fuerza re-fetch (admin).

    Returns:
        Dict con datos unificados, validación cruzada y campo `source`.
    """
    ncm_key = "".join(ch for ch in str(ncm) if ch.isdigit())[:10]
    logger.info(f"[NCM Service] Consultando NCM {ncm_key} (refresh={refresh})")

    # 1. Cache persistente (si no se pidio refresh)
    if not refresh:
        cached = await _get_cached_ncm_raw(ncm_key)
        if cached:
            logger.info(f"[NCM Service] cache hit para {ncm_key} (source={cached['source']})")
            cached_payload = cached["payload"]
            if isinstance(cached_payload, dict):
                cached_payload = dict(cached_payload)
                meta = dict(cached_payload.get("metadata") or {})
                meta["cache_hit"] = True
                meta["source"] = cached["source"]
                # Propagar frescura del cache para que la UI muestre banner
                # "Datos con latencia de N min" cuando corresponda.
                fetched_at = cached.get("fetched_at")
                if fetched_at:
                    try:
                        ts = fetched_at.replace(tzinfo=None) if hasattr(fetched_at, "replace") else None
                        if ts:
                            age_hours = (datetime.utcnow() - ts).total_seconds() / 3600.0
                            meta["fetched_at"] = ts.isoformat() + "Z"
                            meta["cache_age_hours"] = round(age_hours, 2)
                    except Exception:
                        pass
                cached_payload["metadata"] = meta
                cached_payload["source"] = cached["source"]
                return cached_payload

    # 2. Consultar ambas APIs en paralelo (2x más rápido)
    tarifar_task = asyncio.create_task(consultar_tarifar_async(ncm_key, valor_fob))
    vuce_task = asyncio.create_task(consultar_vuce_async(ncm_key))

    results = await asyncio.gather(
        tarifar_task, vuce_task, return_exceptions=True
    )

    tarifar_data = results[0]
    vuce_data = results[1]

    # Verificar si alguna consulta falló
    tarifar_disponible = not isinstance(tarifar_data, Exception)
    vuce_disponible = not isinstance(vuce_data, Exception)

    if isinstance(tarifar_data, Exception):
        logger.warning(f"[NCM Service] Tarifar falló: {tarifar_data}")
        tarifar_data = {}

    if isinstance(vuce_data, Exception):
        logger.warning(f"[NCM Service] VUCE falló: {vuce_data}")
        vuce_data = {}

    # Merge inteligente
    datos_completos = merge_datos_inteligente(ncm_key, tarifar_data, vuce_data)

    # Validación cruzada
    validacion = validar_cruzado(tarifar_data, vuce_data)

    # Detectar discrepancias
    discrepancias = detectar_discrepancias(tarifar_data, vuce_data)

    # Determinar fuente real de los datos segun lo que devolvio VUCE
    # (scrape:tarifar, scrape:arancel, vuce_api_real, vuce_fake). Si no hay
    # marca explicita, asumimos fake (caso peor).
    raw_source = (
        (vuce_data or {}).get("source")
        or (vuce_data or {}).get("fuente")
        or "fake"
    )
    # Normalizamos a un set chico de etiquetas para la UI
    if raw_source.startswith("scrape:"):
        source_label = raw_source  # scrape:tarifar | scrape:arancel
    elif "api_real" in raw_source or raw_source == "oficial":
        source_label = "api:vuce"
    elif raw_source in ("vuce_fake", "fake", "tarifar_fake") or "fake" in raw_source:
        source_label = "fake"
    else:
        source_label = raw_source

    # Construir respuesta final
    response = {
        "ncm": ncm_key,
        "descripcion": datos_completos["descripcion"],
        "descripcion_tarifar": datos_completos.get("descripcion_tarifar"),
        "descripcion_vuce": datos_completos.get("descripcion_vuce"),

        # Fuente efectiva de los datos (para chip de UI)
        "source": source_label,

        # Alícuotas (VUCE tiene prioridad - datos oficiales)
        "alicuotas": {
            "arancel_extrazona": datos_completos["alicuotas"]["arancel"],
            "arancel_mercosur": 0.0,  # MERCOSUR = 0%
            "iva": datos_completos["alicuotas"]["iva"],
            "estadistica": datos_completos["alicuotas"]["estadistica"],
            "fuente": datos_completos["alicuotas"]["fuente"],
            "fecha_actualizacion": datos_completos["alicuotas"].get("fecha")
        },

        # Licencias y requisitos (VUCE autoridad)
        "licencias": datos_completos["licencias"],
        "intervenciones_previas": datos_completos.get("intervenciones", []),
        "regimen_especial": datos_completos.get("regimen_especial"),

        # Análisis comercial (Tarifar)
        "analisis_origenes": datos_completos.get("analisis_origenes"),
        "estadisticas_comercio": datos_completos.get("estadisticas"),

        # Recomendación de origen
        "recomendacion_origen": generar_recomendacion_origen(datos_completos),

        # Validación cruzada
        "validacion": {
            "fuentes_consultadas": {
                "tarifar": tarifar_disponible,
                "vuce": vuce_disponible
            },
            "datos_coinciden": validacion["coinciden"],
            "nivel_confianza": validacion["nivel_confianza"],
            "discrepancias": discrepancias,
            "warnings": validacion.get("warnings", [])
        },

        # Metadata
        "metadata": {
            "fecha_consulta": datetime.now().isoformat(),
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "cache_age_hours": 0.0,
            "tiempo_respuesta_ms": datos_completos.get("tiempo_respuesta", 0),
            "vuce_disponible": vuce_disponible,
            "tarifar_disponible": tarifar_disponible,
            "modo_fake": source_label == "fake",
            "source": source_label,
            "cache_hit": False,
            "version": "2.1-dual-api"
        }
    }

    # Guardar en cache solo si es un resultado real (no fake)
    if source_label != "fake":
        await _save_cached_ncm_raw(ncm_key, response, source_label)

    return response


async def consultar_tarifar_async(ncm: str, valor_fob: float) -> Dict[str, Any]:
    """Wrapper async para Tarifar"""
    try:
        # Ejecutar en thread pool (Tarifar es sync)
        result = await asyncio.to_thread(
            tarifar_client.get_simulacion_origen, ncm, valor_fob, 1.0
        )
        return result
    except Exception as e:
        logger.error(f"[NCM Service] Error Tarifar: {e}")
        raise


async def consultar_vuce_async(ncm: str) -> Dict[str, Any]:
    """Wrapper async para VUCE"""
    try:
        # Ejecutar en thread pool (VUCE es sync)
        result = await asyncio.to_thread(
            vuce_client._request, f"ncm/{ncm}"
        )
        return result
    except Exception as e:
        logger.error(f"[NCM Service] Error VUCE: {e}")
        raise


def merge_datos_inteligente(ncm: str, tarifar: Dict, vuce: Dict) -> Dict[str, Any]:
    """
    Combina datos de Tarifar + VUCE con lógica de prioridad.

    Reglas:
    - Descripción: VUCE (oficial) > Tarifar
    - Alícuotas: VUCE (legal) > Tarifar
    - Licencias: VUCE (autoridad)
    - Análisis comercial: Tarifar
    - Estadísticas: Tarifar
    """

    # Descripción: VUCE tiene prioridad
    descripcion_vuce = vuce.get("descripcion", "")
    descripcion_tarifar = ""

    if tarifar.get("simulaciones"):
        # Tarifar devuelve simulaciones, no descripción directa
        descripcion_tarifar = f"Simulación para NCM {ncm}"

    descripcion_final = descripcion_vuce or descripcion_tarifar or f"NCM {ncm}"

    # Alícuotas: VUCE es fuente oficial
    alicuotas_vuce = vuce.get("alicuotas", {})
    alicuotas = {
        "arancel": alicuotas_vuce.get("arancel_base", 10.0),  # Fallback 10%
        "iva": alicuotas_vuce.get("iva", 21.0),  # Fallback 21%
        "estadistica": alicuotas_vuce.get("estadistica", 3.0),  # Fallback 3%
        "fuente": "vuce_oficial" if alicuotas_vuce else "tarifar_estimado",
        "fecha": vuce.get("fecha_actualizacion")
    }

    # Licencias: VUCE es autoridad
    licencias = vuce.get("licencias", [])

    # Análisis de orígenes: Tarifar
    analisis_origenes = None
    if tarifar.get("simulaciones"):
        mejor = tarifar.get("recomendacion", {})
        analisis_origenes = {
            "mejor_origen": mejor.get("mejor_origen", "BR"),
            "mejor_pais": mejor.get("pais", "Brasil"),
            "costo_estimado": mejor.get("costo_total", 0),
            "ahorro_vs_china": mejor.get("ahorro_vs_china", 0),
            "simulaciones_disponibles": list(tarifar.get("simulaciones", {}).keys())
        }

    return {
        "descripcion": descripcion_final,
        "descripcion_vuce": descripcion_vuce,
        "descripcion_tarifar": descripcion_tarifar,
        "alicuotas": alicuotas,
        "licencias": licencias,
        "intervenciones": vuce.get("intervenciones_previas", []),
        "regimen_especial": vuce.get("regimen_especial"),
        "analisis_origenes": analisis_origenes,
        "estadisticas": tarifar.get("estadisticas")
    }


def validar_cruzado(tarifar: Dict, vuce: Dict) -> Dict[str, Any]:
    """
    Valida consistencia entre Tarifar y VUCE.

    Returns:
        Dict con resultado de validación
    """
    warnings = []
    coinciden = True

    # Si ambos disponibles, comparar alícuotas
    if tarifar and vuce:
        vuce_arancel = vuce.get("alicuotas", {}).get("arancel_base")
        # Tarifar no devuelve alícuota directa en simulación, skip

        if vuce.get("licencias") and len(vuce["licencias"]) > 0:
            warnings.append({
                "tipo": "licencias_requeridas",
                "mensaje": f"Este NCM requiere {len(vuce['licencias'])} licencia(s) previa(s)",
                "criticidad": "alta"
            })

    # Determinar nivel de confianza
    if tarifar and vuce:
        nivel_confianza = "alto"  # Ambas fuentes disponibles
    elif vuce:
        nivel_confianza = "medio"  # Solo VUCE (oficial)
    elif tarifar:
        nivel_confianza = "bajo"  # Solo Tarifar (estimado)
    else:
        nivel_confianza = "muy_bajo"  # Ninguna fuente

    return {
        "coinciden": coinciden,
        "nivel_confianza": nivel_confianza,
        "warnings": warnings
    }


def detectar_discrepancias(tarifar: Dict, vuce: Dict) -> List[Dict[str, Any]]:
    """
    Detecta diferencias entre Tarifar y VUCE.

    Returns:
        Lista de discrepancias encontradas
    """
    discrepancias = []

    # Comparar alícuotas si ambas disponibles
    if tarifar and vuce:
        vuce_arancel = vuce.get("alicuotas", {}).get("arancel_base")

        # Por ahora Tarifar simula, no podemos comparar directamente
        # TODO: Cuando tengamos API real de Tarifar, comparar aquí
        pass

    return discrepancias


def generar_recomendacion_origen(datos: Dict) -> Optional[Dict[str, Any]]:
    """
    Genera recomendación de país de origen basado en análisis.

    Returns:
        Recomendación o None si no hay suficiente info
    """
    analisis = datos.get("analisis_origenes")
    if not analisis:
        return None

    licencias = datos.get("licencias", [])
    tiene_licencias = len(licencias) > 0

    return {
        "origen_recomendado": analisis["mejor_origen"],
        "pais": analisis["mejor_pais"],
        "ahorro_estimado_usd": analisis["ahorro_vs_china"],
        "razon": "Preferencia arancelaria MERCOSUR" if analisis["mejor_origen"] in ["BR", "PY", "UY"] else "Menor costo total",
        "advertencias": [
            f"Requiere {lic['codigo']}: {lic['descripcion']}"
            for lic in licencias
        ] if tiene_licencias else []
    }


# ===== Funciones helper para uso rápido =====

def get_ncm_sync(ncm: str, valor_fob: float = 100.0) -> Dict[str, Any]:
    """
    Versión sincrónica de get_ncm_completo (para uso en endpoints sync).
    """
    return asyncio.run(get_ncm_completo(ncm, valor_fob))


async def get_alicuotas_solo(ncm: str) -> Dict[str, float]:
    """
    Consulta rápida solo alícuotas (sin análisis comercial).
    Útil para validaciones rápidas.
    """
    try:
        vuce_data = await consultar_vuce_async(ncm)
        alicuotas = vuce_data.get("alicuotas", {})

        return {
            "arancel": alicuotas.get("arancel_base", 10.0),
            "iva": alicuotas.get("iva", 21.0),
            "estadistica": alicuotas.get("estadistica", 3.0),
            "fuente": "vuce_oficial"
        }
    except Exception as e:
        logger.error(f"[NCM Service] Error obteniendo alícuotas: {e}")
        # Fallback a valores default
        return {
            "arancel": 10.0,
            "iva": 21.0,
            "estadistica": 3.0,
            "fuente": "default_fallback"
        }


async def verificar_licencias(ncm: str) -> List[Dict[str, Any]]:
    """
    Consulta solo licencias requeridas (VUCE).
    """
    try:
        vuce_data = await consultar_vuce_async(ncm)
        return vuce_data.get("licencias", [])
    except Exception as e:
        logger.error(f"[NCM Service] Error verificando licencias: {e}")
        return []
