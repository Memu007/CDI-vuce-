"""Memoria de NCM por cliente.

Cada vez que un despachante guarda una operacion, aprendemos: "este cliente +
este producto (NCM + descripcion parecida) = X". La proxima vez que aparezca
un producto parecido de ese mismo cliente, lo sugerimos con alta confianza.

Principios:
- Se usa la misma sesion de DB que `save_client_operation` para que todo quede
  en la misma transaccion (si la op se hace rollback, la memoria tambien).
- Match por NCM exacto primero, despues fuzzy por descripcion normalizada
  (Jaccard >= 0.80). El umbral es el mismo que el catalogo de proveedores.
- Promedios incrementales (media movil simple) para peso, valor unitario y
  cantidad. Asi cada operacion refina la estimacion sin guardar todos los
  valores historicos.
"""

from __future__ import annotations

import logging
import unicodedata
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import ClientProductHistory
from ..core.catalog_service import _normalize, _similarity  # reuso de normalizador

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 0.80


def _norm_desc(desc: str) -> str:
    return _normalize(desc or "")[:200]


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
) -> Optional[ClientProductHistory]:
    """Crea o actualiza la entrada de memoria de producto del cliente.

    Returns:
        La entrada (nueva o actualizada). None si faltan campos obligatorios.
    """
    ncm = (ncm or "").strip()
    descripcion = (descripcion or "").strip()

    if not ncm or not descripcion or not client_id or not owner_username:
        return None

    desc_norm = _norm_desc(descripcion)

    # 1) Intento match exacto por NCM + owner + client
    q = sa_select(ClientProductHistory).where(
        ClientProductHistory.owner_username == owner_username,
        ClientProductHistory.client_id == client_id,
        ClientProductHistory.ncm == ncm,
    )
    result = await db.execute(q)
    rows = result.scalars().all()

    existing: Optional[ClientProductHistory] = None
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
    if existing is None:
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
        n_prev = max(existing.veces_usado or 1, 1)
        n_new = n_prev + 1

        def _incr_avg(prev, new_value):
            """Promedio incremental. Si new_value es None o 0, no mueve el promedio."""
            if new_value is None or new_value <= 0:
                return prev
            prev = prev or 0.0
            return ((prev * n_prev) + new_value) / n_new

        existing.veces_usado = n_new
        existing.peso_unitario_avg = _incr_avg(existing.peso_unitario_avg, peso_unitario)
        existing.valor_unitario_avg = _incr_avg(existing.valor_unitario_avg, valor_unitario)
        existing.cantidad_avg = _incr_avg(existing.cantidad_avg, cantidad)
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
        peso_unitario_avg=float(peso_unitario or 0.0),
        origen_frecuente=(origen or "XX").strip()[:3] or "XX",
        valor_unitario_avg=float(valor_unitario or 0.0) or None,
        cantidad_avg=float(cantidad or 0.0) or None,
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
        "peso_unitario_avg": best_row.peso_unitario_avg,
        "valor_unitario_avg": best_row.valor_unitario_avg,
        "cantidad_avg": best_row.cantidad_avg,
        "veces_usado": best_row.veces_usado,
        "ultima_vez": best_row.ultima_vez.isoformat() if best_row.ultima_vez else None,
        "confidence": round(best_score, 3),
    }
