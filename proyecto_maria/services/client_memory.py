"""Memoria de NCM por cliente.

Cada vez que un despachante guarda una operacion, aprendemos: "este cliente +
este producto (NCM + descripcion parecida) = X". La proxima vez que aparezca
un producto parecido de ese mismo cliente, lo sugerimos con alta confianza.

Principios:
- `save_client_operation` guarda primero la operacion y despues, en otro
  commit, la memoria: si la memoria falla, la operacion queda (GUARDAR-1).
- Match por NCM exacto primero, despues fuzzy por descripcion normalizada
  (Jaccard >= 0.80). El umbral es el mismo que el catalogo de proveedores.
- Promedios incrementales (media movil simple) para peso, valor unitario y
  cantidad. Asi cada operacion refina la estimacion sin guardar todos los
  valores historicos.
"""

from __future__ import annotations

import logging
import math
import unicodedata
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import ClientProductHistory
from ..core.catalog_service import _normalize, _similarity  # reuso de normalizador

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 0.80
# Lo que se guarda como promedio: más grande no es un valor de verdad.
_MAX_VALOR = 1e12
_MEDIO_PAR = re.compile("[\ud800-\udfff]")  # no se puede escribir en UTF-8


def valor_para_promedio(valor) -> Optional[float]:
    """El número que entra a un promedio, o None. Infinito, NaN, negativo o
    desmedido no entra: un infinito guardado rompe el catálogo al mostrarlo."""
    if valor is None or isinstance(valor, bool):
        return None
    try:
        valor = float(valor)
    except (TypeError, ValueError, OverflowError):  # 10**400 no entra en un float
        return None
    if not math.isfinite(valor) or valor <= 0 or valor >= _MAX_VALOR:
        return None
    return valor


def _finito(valor) -> Optional[float]:
    return valor if valor is not None and math.isfinite(valor) else None


def _usos(promedio, veces, veces_usado) -> int:
    """Cuántos usos trajeron el valor de `promedio`. Un infinito guardado
    antes cuenta como vacío: si no, ningún valor nuevo lo arregla."""
    if valor_para_promedio(promedio) is None:
        return 0
    if veces is None:  # fila de antes de contar por valor
        return max(veces_usado or 1, 1)
    return max(veces, 0)


def sumar_al_promedio(promedio, veces, veces_usado, nuevo) -> tuple[Optional[float], int]:
    """El promedio y su cuenta después de sumar `nuevo`. Un uso sin valor no
    lo mueve ni se cuenta: sin valor, después 2, después 4 da 3."""
    n = _usos(promedio, veces, veces_usado)
    nuevo = valor_para_promedio(nuevo)
    if nuevo is None:
        return (promedio if n else None), n
    if not n:
        return nuevo, 1
    return (promedio * n + nuevo) / (n + 1), n + 1


def _misma_descripcion(desc: str) -> str:
    """La descripción entera para comparar: sin mayúsculas ni espacios de más."""
    return re.sub(r"\s+", " ", desc or "").strip().casefold()


def _norm_desc(desc: str) -> str:
    return _normalize(desc or "")[:200]


# Largo de client_product_history.ncm (String(10)). En Postgres, guardar algo
# más largo rompe el commit entero (GUARDAR-1).
NCM_HISTORIAL_MAX = 10


def ncm_para_historial(ncm) -> Optional[str]:
    """La forma del NCM que guarda el historial del cliente.

    Lo que entra queda igual. La posición SIM completa (`84714900100D`,
    `8471.49.00.100D`) no entra: se guarda su NCM de 8 dígitos, que es lo que
    se sugiere después y lo que guarda «confirmar NCM». None si no hay ni eso.
    """
    ncm = str(ncm or "").strip()
    if not ncm:
        return None
    if len(ncm) <= NCM_HISTORIAL_MAX:
        return ncm
    digitos = re.sub(r"\D", "", ncm)
    return digitos[:8] if len(digitos) >= 8 else None


async def upsert_client_product_history(
    db: AsyncSession,
    owner_username: str,
    client_id: str,
    ncm: str,
    descripcion: str,
    origen: Optional[str] = None,
    valor_unitario: Optional[float] = None,
    cantidad: Optional[float] = None,
    peso_unitario: Optional[float] = None,
    solo_mismo_ncm: bool = False,
) -> Optional[ClientProductHistory]:
    """Crea o actualiza la entrada de memoria de producto del cliente.

    Con `solo_mismo_ncm` no se usa el respaldo por descripción del paso 2: una
    descripción parecida con otro NCM queda como otro producto.

    Returns:
        La entrada (nueva o actualizada). None si faltan campos obligatorios.
    """
    ncm = ncm_para_historial(ncm) or ""
    descripcion = (descripcion or "").replace("\x00", "").strip()

    if not ncm or not descripcion or not client_id or not owner_username:
        return None
    if _MEDIO_PAR.search(descripcion) or _MEDIO_PAR.search(str(origen or "")):
        return None

    desc_norm = _norm_desc(descripcion)

    existing: Optional[ClientProductHistory] = None
    # El mismo NCM es el mismo sin mirar puntos ni espacios: el despacho lo
    # guarda «39269090» y una operación puede traer «3926.90.90».
    ncm_sin_puntos = func.replace(func.replace(ClientProductHistory.ncm, ".", ""), " ", "")
    q = sa_select(ClientProductHistory).where(
        ClientProductHistory.owner_username == owner_username,
        ClientProductHistory.client_id == client_id,
        ncm_sin_puntos == re.sub(r"\D", "", ncm),
    )
    if solo_mismo_ncm:
        # Es el mismo producto sólo con la misma descripción entera: la
        # normalizada se corta en 200 y dos textos largos distintos quedaban
        # en una fila.
        buscada = _misma_descripcion(descripcion)
        for row in (await db.execute(q)).scalars().all():
            if _misma_descripcion(row.descripcion) == buscada:
                existing = row
                break
        rows = []
    else:
        # 1) Intento match exacto por NCM + owner + client
        result = await db.execute(q)
        rows = result.scalars().all()

    if rows:
        # Si hay varias filas con el mismo NCM, elegir la de descripcion mas parecida.
        best_score = -1.0
        for row in rows:
            score = _similarity(desc_norm, row.descripcion_normalizada or "")
            if score > best_score:
                best_score = score
                existing = row
        # Si la mejor similitud es baja, tratamos como nuevo producto distinto
        # aunque comparta NCM (ej: "tornillo M6" vs "tornillo M8" con mismo NCM).
        if best_score < FUZZY_THRESHOLD:
            existing = None

    # 2) Si no pego por NCM, fallback fuzzy por descripcion en el universo del cliente
    if existing is None and not solo_mismo_ncm:
        q_all = sa_select(ClientProductHistory).where(
            ClientProductHistory.owner_username == owner_username,
            ClientProductHistory.client_id == client_id,
        )
        result_all = await db.execute(q_all)
        candidates = result_all.scalars().all()

        best_score = 0.0
        best_row = None
        for row in candidates:
            score = _similarity(desc_norm, row.descripcion_normalizada or "")
            if score > best_score:
                best_score = score
                best_row = row
        if best_row is not None and best_score >= FUZZY_THRESHOLD:
            existing = best_row

    now = datetime.now(timezone.utc)

    if existing is not None:
        # Cada promedio cuenta sólo los usos que trajeron ese valor.
        usado = existing.veces_usado
        peso, existing.veces_peso = sumar_al_promedio(
            existing.peso_unitario_avg, existing.veces_peso, usado, peso_unitario)
        existing.peso_unitario_avg = peso or 0.0
        existing.valor_unitario_avg, existing.veces_valor = sumar_al_promedio(
            existing.valor_unitario_avg, existing.veces_valor, usado, valor_unitario)
        existing.cantidad_avg, existing.veces_cantidad = sumar_al_promedio(
            existing.cantidad_avg, existing.veces_cantidad, usado, cantidad)
        existing.veces_usado = max(usado or 1, 1) + 1
        if origen and (origen or "").strip():
            existing.origen_frecuente = (origen or "").strip()[:3]
        existing.ultima_vez = now
        # Si la descripcion normalizada estaba vacia (datos viejos), completarla.
        if not existing.descripcion_normalizada:
            existing.descripcion_normalizada = desc_norm
        return existing

    entry = ClientProductHistory(
        id=str(uuid.uuid4()),
        owner_username=owner_username,
        client_id=client_id,
        ncm=ncm,
        descripcion=descripcion,
        descripcion_normalizada=desc_norm,
        peso_unitario_avg=valor_para_promedio(peso_unitario) or 0.0,
        origen_frecuente=(origen or "XX").strip()[:3] or "XX",
        valor_unitario_avg=valor_para_promedio(valor_unitario),
        cantidad_avg=valor_para_promedio(cantidad),
        veces_peso=1 if valor_para_promedio(peso_unitario) else 0,
        veces_valor=1 if valor_para_promedio(valor_unitario) else 0,
        veces_cantidad=1 if valor_para_promedio(cantidad) else 0,
        veces_usado=1,
        primera_vez=now,
        ultima_vez=now,
    )
    db.add(entry)
    return entry


async def lookup_client_memory(
    db: AsyncSession,
    owner_username: str,
    client_id: str,
    descripcion: str,
) -> Optional[dict]:
    """Busca en la memoria del cliente un producto parecido a `descripcion`.

    Returns:
        dict con {ncm, descripcion, origen_frecuente, veces_usado, confidence}
        o None si no hay match suficiente.
    """
    if not client_id or not owner_username or not descripcion:
        return None

    desc_norm = _norm_desc(descripcion)
    q = sa_select(ClientProductHistory).where(
        ClientProductHistory.owner_username == owner_username,
        ClientProductHistory.client_id == client_id,
    )
    result = await db.execute(q)
    candidates = result.scalars().all()

    best_score = 0.0
    best_row: Optional[ClientProductHistory] = None
    for row in candidates:
        score = _similarity(desc_norm, row.descripcion_normalizada or "")
        if score > best_score:
            best_score = score
            best_row = row

    if best_row is None or best_score < FUZZY_THRESHOLD:
        return None

    return {
        "ncm": best_row.ncm,
        "descripcion": best_row.descripcion,
        "origen": best_row.origen_frecuente,
        # Un infinito guardado antes no se puede mandar en JSON: daba 500.
        "peso_unitario_avg": _finito(best_row.peso_unitario_avg),
        "valor_unitario_avg": _finito(best_row.valor_unitario_avg),
        "cantidad_avg": _finito(best_row.cantidad_avg),
        "veces_usado": best_row.veces_usado,
        "ultima_vez": best_row.ultima_vez.isoformat() if best_row.ultima_vez else None,
        "confidence": round(best_score, 3),
    }
