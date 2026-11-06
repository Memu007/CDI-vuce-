"""Memoria de NCM por cliente.

Cada vez que un despachante guarda una operacion, aprendemos: "este cliente +
este producto = X". La proxima vez que aparezca un producto parecido de ese
mismo cliente, lo sugerimos con alta confianza.

Principios:
- `save_client_operation` guarda primero la operacion y despues, en otro
  commit, la memoria: si la memoria falla, la operacion queda (GUARDAR-1).
- Un producto es el NCM de 8 dígitos y la descripción entera, sin mirar
  mayúsculas, espacios de más ni la forma Unicode. Todas las vías que
  escriben usan esa regla y la base no deja dos filas iguales (DESPACHO-1b).
  Sugerir sí busca por parecido de descripción (Jaccard >= 0.80).
- Promedios incrementales (media movil simple) para peso, valor unitario y
  cantidad. Asi cada operacion refina la estimacion sin guardar todos los
  valores historicos.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select as sa_select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import ClientProductHistory
from ..core.catalog_service import _normalize, _similarity, validar_largo  # reuso de normalizador

FUZZY_THRESHOLD = 0.80
# Lo que se guarda como promedio: más grande no es un valor de verdad.
_MAX_VALOR = 1e12
_MEDIO_PAR = re.compile("[\ud800-\udfff]")  # no se puede escribir en UTF-8
# Un número escrito con dígitos del 0 al 9: float() acepta «1_000» y «٣».
_DECIMAL = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def valor_para_promedio(valor) -> Optional[float]:
    """El número que entra a un promedio, o None. Infinito, NaN, negativo o
    desmedido no entra: un infinito guardado rompe el catálogo al mostrarlo."""
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, str):
        valor = valor.strip()
        if not _DECIMAL.fullmatch(valor):
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


def _norm_desc(desc: str) -> str:
    return _normalize(desc or "")[:200]


def tiene_medio_par(valor) -> bool:
    """Si algún texto de un JSON, claves incluidas, tiene medio par UTF-16."""
    if isinstance(valor, str):
        return bool(_MEDIO_PAR.search(valor))
    if isinstance(valor, list):
        return any(tiene_medio_par(v) for v in valor)
    if isinstance(valor, dict):
        return any(tiene_medio_par(k) or tiene_medio_par(v) for k, v in valor.items())
    return False


def tiene_digito_no_ascii(texto: str) -> bool:
    """«٣٩٢٦٩٠٩٠» o «３９２６»: Python los toma por dígitos y no son un NCM."""
    return any(c.isdigit() and not "0" <= c <= "9" for c in texto)


# Grupos de dígitos separados por un punto, un guion o un espacio, y la letra
# de la posición SIM al final.
_NCM = re.compile(r"[0-9]+(?:[.\- ][0-9]+)*[A-Z]?")


def ncm_para_historial(ncm) -> Optional[str]:
    """El NCM de 8 dígitos que guarda el historial, o None si no es un NCM.

    Entra el NCM con o sin puntos, con los dígitos de más de la posición
    (hasta 11) y la letra de la posición SIM completa (`8471.49.00.100D`).
    """
    if isinstance(ncm, bool) or not isinstance(ncm, (str, int)):
        return None
    ncm = str(ncm).strip().upper()
    if len(ncm) > 20 or not _NCM.fullmatch(ncm):
        return None
    digitos = re.sub(r"[^0-9]", "", ncm)
    if not 8 <= len(digitos) <= 11 or (ncm[-1].isalpha() and len(digitos) != 11):
        return None
    return digitos[:8]


def descripcion_del_producto(descripcion) -> str:
    """La descripción como se guarda: sin NUL, un espacio entre palabras y en
    NFC. ValueError con el motivo si no se puede guardar."""
    texto = re.sub(r"\s+", " ", str(descripcion or "").replace("\x00", "")).strip()
    if not texto:
        raise ValueError("Falta la descripción.")
    if _MEDIO_PAR.search(texto):
        raise ValueError("Hay un carácter que no se puede guardar.")
    texto = unicodedata.normalize("NFC", texto)
    validar_largo(texto)
    return texto


def clave_del_producto(ncm8: str, descripcion: str) -> str:
    """Lo que identifica al producto en la base: el índice único la usa."""
    misma = unicodedata.normalize("NFC", descripcion.casefold())
    return hashlib.sha256(f"{ncm8}\x1f{misma}".encode()).hexdigest()


def identidad_del_producto(ncm, descripcion) -> Optional[tuple[str, str, str]]:
    """(NCM de 8 dígitos, descripción como se guarda, clave), o None si el
    par no es un producto."""
    ncm8 = ncm_para_historial(ncm)
    try:
        descripcion = descripcion_del_producto(descripcion)
    except ValueError:
        return None
    if not ncm8:
        return None
    return ncm8, descripcion, clave_del_producto(ncm8, descripcion)


def orden_de_escritura(campos: dict) -> str:
    """Para escribir varios productos siempre en el mismo orden: dos pedidos
    que traban las mismas filas en orden inverso se bloquean en Postgres."""
    producto = identidad_del_producto(campos.get("ncm"), campos.get("descripcion"))
    return producto[2] if producto else ""


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
        La entrada (nueva o actualizada). None si el par no es un producto.
    """
    producto = identidad_del_producto(ncm, descripcion)
    if producto is None or not client_id or not owner_username:
        return None
    origen = str(origen or "").strip()
    try:
        validar_largo(origen, "El origen")
    except ValueError:
        return None
    if _MEDIO_PAR.search(origen):
        return None
    ncm, descripcion, clave = producto
    now = datetime.now(timezone.utc)

    # Dos pedidos a la vez con el mismo producto: el índice único deja entrar
    # uno y el otro espera a que termine para sumarle.
    insertar = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
    alta = (
        insertar(ClientProductHistory.__table__).values(
            id=str(uuid.uuid4()),
            owner_username=owner_username,
            client_id=client_id,
            ncm=ncm,
            descripcion=descripcion,
            descripcion_normalizada=_norm_desc(descripcion),
            clave=clave,
            peso_unitario_avg=valor_para_promedio(peso_unitario) or 0.0,
            origen_frecuente=origen or "XX",
            valor_unitario_avg=valor_para_promedio(valor_unitario),
            cantidad_avg=valor_para_promedio(cantidad),
            veces_peso=1 if valor_para_promedio(peso_unitario) else 0,
            veces_valor=1 if valor_para_promedio(valor_unitario) else 0,
            veces_cantidad=1 if valor_para_promedio(cantidad) else 0,
            veces_usado=1,
            primera_vez=now,
            ultima_vez=now,
        ).on_conflict_do_nothing(
            index_elements=["owner_username", "client_id", "clave"],
        ).returning(ClientProductHistory.id)
    )
    fila = sa_select(ClientProductHistory).where(
        ClientProductHistory.owner_username == owner_username,
        ClientProductHistory.client_id == client_id,
        ClientProductHistory.clave == clave,
    ).with_for_update().execution_options(populate_existing=True)
    # Mientras se espera la fila, otro pedido puede cambiarle la clave o
    # borrarla: entonces no aparece y se vuelve a insertar.
    for _ in range(3):
        insertada = (await db.execute(alta)).first() is not None
        existing = (await db.execute(fila)).scalar_one_or_none()
        if existing is not None:
            break
    else:
        raise RuntimeError("el producto cambió en cada intento de guardarlo")
    if insertada:
        return existing

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
    if origen:
        existing.origen_frecuente = origen
    existing.ultima_vez = now
    # Si la descripcion normalizada estaba vacia (datos viejos), completarla.
    if not existing.descripcion_normalizada:
        existing.descripcion_normalizada = _norm_desc(descripcion)
    return existing


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
