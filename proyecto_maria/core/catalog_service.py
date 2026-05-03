"""
CatalogService — Catalogo de productos por proveedor, persistido en Postgres.

Migrado desde un archivo JSON (product_catalog.json) que se perdia con cada
deploy de Railway. Ahora todas las operaciones son async contra la tabla
`vendor_catalog_products` (ver `database/models.py::VendorCatalogProduct`).

Contrato publico (usado desde `main.py` endpoints /api/catalog/*):
- get_vendor(db, vendor_name, owner_username)
- get_vendor_by_id(db, vendor_id, owner_username)
- list_vendors(db, owner_username)
- match_items(db, items, vendor_name, owner_username)
- save_products(db, vendor_name, productos_in, owner_username)
- update_product(db, vendor_id, product_key, updates, owner_username)
- delete_product(db, vendor_id, product_key, owner_username)
- delete_vendor(db, vendor_id, owner_username)

Los shapes de retorno son compatibles con la version JSON anterior, salvo
que `productos` ya no es un dict keyed por `product_key` sino que se arma
on-demand al construir get_vendor/get_vendor_by_id.
"""

from __future__ import annotations
import re
import unicodedata
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func as sa_func, delete as sa_delete, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

# Import lazy para evitar ciclos
from proyecto_maria.database.models import VendorCatalogProduct


# Umbral de similitud para fuzzy match (0-1). No lo subimos mucho porque
# descripciones de facturas tienen ruido (marcas, codigos) y perdemos matches.
FUZZY_THRESHOLD = 0.80

# Patron valido para vendor_id (slug generado por _vendor_key).
_VENDOR_ID_RE = re.compile(r"^[a-z0-9_]{1,60}$")


def is_valid_vendor_id(vendor_id: str) -> bool:
    """True si vendor_id matchea el formato de slug generado por _vendor_key."""
    return bool(vendor_id) and bool(_VENDOR_ID_RE.match(vendor_id))


# -----------------------------------------------------------------
# Utilidades de normalizacion (son las mismas que en la version JSON,
# las exponemos al exterior para que otros modulos como client_memory
# las reusen).
# -----------------------------------------------------------------

def _normalize(text: str) -> str:
    """Normaliza texto para usar como clave de catalogo."""
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _vendor_key(vendor_name: str) -> str:
    """Genera la clave del proveedor (slug)."""
    return re.sub(r"\s+", "_", _normalize(vendor_name))[:60]


# Stop-words minimas (ES + EN + PT)
_STOPWORDS = frozenset({
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas",
    "y", "o", "u", "en", "del", "al", "su", "sus", "lo",
    "mi", "tu", "se", "es", "por", "con", "para", "sin",
    "of", "the", "a", "an", "and", "or", "in", "on", "at", "to", "for",
    "by", "is", "as", "be", "it", "no", "so", "we", "us",
    "do", "da", "dos", "das", "no", "na", "nos", "nas", "com", "sem",
    "para", "por",
})


def _word_set(text: str) -> set:
    """Palabras significativas: 2+ chars y fuera de la lista de stop-words."""
    return {
        w for w in _normalize(text).split()
        if len(w) >= 2 and w not in _STOPWORDS
    }


def _similarity(a: str, b: str) -> float:
    """Similitud Jaccard entre palabras clave de dos descripciones."""
    sa, sb = _word_set(a), _word_set(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


# -----------------------------------------------------------------
# Helpers internos para convertir filas de DB a dict compatible con
# el shape antiguo (JSON).
# -----------------------------------------------------------------

def _row_to_dict(row: VendorCatalogProduct) -> dict:
    """Convierte una fila a dict con el shape que esperan endpoints."""
    return {
        "descripcion_original": row.descripcion or "",
        "ncm": row.ncm,
        "origen": row.origen,
        "unidad_medida": (row.extra or {}).get("unidad_medida") if row.extra else None,
        "precio_ref": row.valor_unitario,
        "usos": row.usos or 0,
        "ultima_vez": row.ultima_vez.strftime("%Y-%m-%d") if row.ultima_vez else None,
    }


async def _fetch_vendor_rows(
    db: AsyncSession,
    owner_username: Optional[str],
    vendor_id: str,
) -> list[VendorCatalogProduct]:
    """Todas las filas de un vendor para un owner dado. Lista vacia si no hay."""
    if not owner_username:
        return []
    stmt = select(VendorCatalogProduct).where(
        VendorCatalogProduct.owner_username == owner_username,
        VendorCatalogProduct.vendor_id == vendor_id,
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _rows_to_productos_dict(rows: list[VendorCatalogProduct]) -> dict:
    """Construye el dict {product_key: product_dict} a partir de filas."""
    return {row.product_key: _row_to_dict(row) for row in rows}


def _vendor_data_shell(
    vendor_id: str,
    vendor_nombre: str,
    owner_username: Optional[str],
    rows: list[VendorCatalogProduct],
) -> dict:
    """Shape compatible con el JSON antiguo, con productos inflados."""
    ultima = max(
        (r.ultima_vez for r in rows if r.ultima_vez is not None),
        default=None,
    )
    return {
        "nombre": vendor_nombre,
        "owner_username": owner_username,
        "productos": _rows_to_productos_dict(rows),
        "ultima_actualizacion": ultima.isoformat() if ultima else None,
    }


# -----------------------------------------------------------------
# Consultas publicas
# -----------------------------------------------------------------

async def get_vendor(
    db: AsyncSession,
    vendor_name: str,
    owner_username: Optional[str] = None,
) -> Optional[dict]:
    """Retorna el catalogo del proveedor por nombre (slug por dentro)."""
    vendor_id = _vendor_key(vendor_name)
    rows = await _fetch_vendor_rows(db, owner_username, vendor_id)
    if not rows:
        return None
    nombre = rows[0].vendor_nombre or vendor_name
    return _vendor_data_shell(vendor_id, nombre, owner_username, rows)


async def get_vendor_by_id(
    db: AsyncSession,
    vendor_id: str,
    owner_username: Optional[str] = None,
) -> Optional[dict]:
    """Retorna el catalogo del proveedor por slug/id."""
    if not is_valid_vendor_id(vendor_id):
        return None
    rows = await _fetch_vendor_rows(db, owner_username, vendor_id)
    if not rows:
        return None
    nombre = rows[0].vendor_nombre or vendor_id
    return _vendor_data_shell(vendor_id, nombre, owner_username, rows)


async def list_vendors(
    db: AsyncSession,
    owner_username: Optional[str] = None,
) -> list[dict]:
    """Lista proveedores del despachante, con totales agregados."""
    if not owner_username:
        return []
    stmt = (
        select(
            VendorCatalogProduct.vendor_id,
            sa_func.max(VendorCatalogProduct.vendor_nombre).label("nombre"),
            sa_func.count(VendorCatalogProduct.id).label("total_productos"),
            sa_func.coalesce(sa_func.sum(VendorCatalogProduct.usos), 0).label("usos_totales"),
            sa_func.max(VendorCatalogProduct.ultima_vez).label("ultima_vez"),
        )
        .where(VendorCatalogProduct.owner_username == owner_username)
        .group_by(VendorCatalogProduct.vendor_id)
    )
    rows = (await db.execute(stmt)).all()
    result = [
        {
            "vendor_id": r.vendor_id,
            "nombre": r.nombre or r.vendor_id,
            "total_productos": int(r.total_productos or 0),
            "usos_totales": int(r.usos_totales or 0),
            "ultima_vez": r.ultima_vez.isoformat() if r.ultima_vez else None,
        }
        for r in rows
    ]
    return sorted(result, key=lambda x: x["usos_totales"], reverse=True)


async def match_items(
    db: AsyncSession,
    items: list[dict],
    vendor_name: str,
    owner_username: Optional[str] = None,
) -> dict:
    """
    Intenta hacer match de cada item contra el catalogo del proveedor.

    Mismo contrato de retorno que la version JSON: vendor_known, vendor_id,
    vendor_nombre, items_matched, tasa_reconocimiento, items_nuevos.
    """
    vendor_id = _vendor_key(vendor_name)
    rows = await _fetch_vendor_rows(db, owner_username, vendor_id)

    vendor_known = bool(rows)
    vendor_nombre = (rows[0].vendor_nombre if rows else vendor_name) or vendor_name

    productos = _rows_to_productos_dict(rows)

    matched_items = []
    n_matched = 0

    for idx, item in enumerate(items):
        desc = item.get("descripcion", "") or ""
        result = {
            "idx": idx,
            "descripcion": desc,
            "pieza_original": item.get("pieza", ""),
            "match_type": "none",
            "match_score": 0.0,
            "ncm": None,
            "origen": None,
            "unidad_medida": None,
            "producto_key": None,
        }

        desc_key = _normalize(desc)
        if desc_key in productos:
            prod = productos[desc_key]
            result.update({
                "match_type": "exact",
                "match_score": 1.0,
                "ncm": prod.get("ncm"),
                "origen": prod.get("origen"),
                "unidad_medida": prod.get("unidad_medida"),
                "producto_key": desc_key,
            })
            n_matched += 1
        else:
            best_score = 0.0
            best_key = None
            for prod_key in productos.keys():
                score = _similarity(desc, prod_key)
                if score > best_score:
                    best_score = score
                    best_key = prod_key

            if best_score >= FUZZY_THRESHOLD and best_key:
                prod = productos[best_key]
                result.update({
                    "match_type": "fuzzy",
                    "match_score": round(best_score, 3),
                    "ncm": prod.get("ncm"),
                    "origen": prod.get("origen"),
                    "unidad_medida": prod.get("unidad_medida"),
                    "producto_key": best_key,
                })
                n_matched += 1

        matched_items.append(result)

    tasa = round(n_matched / max(len(items), 1), 3)

    return {
        "vendor_known": vendor_known,
        "vendor_id": vendor_id,
        "vendor_nombre": vendor_nombre,
        "items_matched": matched_items,
        "tasa_reconocimiento": tasa,
        "items_nuevos": len(items) - n_matched,
        "total_items": len(items),
    }


# -----------------------------------------------------------------
# Escritura publica
# -----------------------------------------------------------------

async def save_products(
    db: AsyncSession,
    vendor_name: str,
    productos_in: list[dict],
    owner_username: Optional[str] = None,
) -> dict:
    """
    Guarda o actualiza productos en el catalogo del proveedor del despachante.

    Upsert por (owner_username, vendor_id, product_key): si existe, suma 1 a
    usos y actualiza campos; si no, crea nuevo.
    """
    if not owner_username:
        return {
            "vendor_id": "",
            "vendor_nombre": vendor_name,
            "productos_nuevos": 0,
            "productos_actualizados": 0,
            "total_en_catalogo": 0,
            "owner_username": owner_username,
        }

    vendor_id = _vendor_key(vendor_name)

    saved = 0
    updated = 0

    for prod in productos_in:
        desc = (prod.get("descripcion") or "").strip()
        ncm = (prod.get("ncm") or prod.get("pieza") or "").strip()
        origen = (prod.get("origen") or "").strip()

        if not desc:
            continue

        product_key = _normalize(desc)
        if not product_key:
            continue

        unidad = prod.get("unidad_medida")
        precio = prod.get("valor_unitario")
        try:
            precio = float(precio) if precio not in (None, "") else None
        except (TypeError, ValueError):
            precio = None

        extra_blob = {"unidad_medida": unidad} if unidad else None

        existing_stmt = select(VendorCatalogProduct).where(
            VendorCatalogProduct.owner_username == owner_username,
            VendorCatalogProduct.vendor_id == vendor_id,
            VendorCatalogProduct.product_key == product_key,
        )
        existing = (await db.execute(existing_stmt)).scalar_one_or_none()

        if existing is None:
            row = VendorCatalogProduct(
                owner_username=owner_username,
                vendor_id=vendor_id,
                vendor_nombre=vendor_name,
                product_key=product_key,
                descripcion=desc,
                ncm=ncm or None,
                origen=origen or None,
                valor_unitario=precio,
                peso_unitario=None,
                usos=1,
                extra=extra_blob,
            )
            db.add(row)
            saved += 1
        else:
            existing.vendor_nombre = vendor_name
            existing.descripcion = desc
            if ncm:
                existing.ncm = ncm
            if origen:
                existing.origen = origen
            if precio is not None:
                existing.valor_unitario = precio
            if extra_blob:
                merged = dict(existing.extra or {})
                merged.update(extra_blob)
                existing.extra = merged
            existing.usos = (existing.usos or 0) + 1
            existing.ultima_vez = datetime.now(timezone.utc)
            updated += 1

    await db.commit()

    total_stmt = (
        select(sa_func.count(VendorCatalogProduct.id))
        .where(
            VendorCatalogProduct.owner_username == owner_username,
            VendorCatalogProduct.vendor_id == vendor_id,
        )
    )
    total = (await db.execute(total_stmt)).scalar_one() or 0

    return {
        "vendor_id": vendor_id,
        "vendor_nombre": vendor_name,
        "productos_nuevos": saved,
        "productos_actualizados": updated,
        "total_en_catalogo": int(total),
        "owner_username": owner_username,
    }


# Campos editables en update_product (lista blanca defensiva).
_EDITABLE_FIELDS = (
    "descripcion_original",
    "ncm",
    "origen",
    "unidad_medida",
    "precio_ref",
)


async def update_product(
    db: AsyncSession,
    vendor_id: str,
    product_key: str,
    updates: dict,
    owner_username: Optional[str] = None,
) -> Optional[dict]:
    """Actualiza un producto individual. Si cambia la descripcion y la nueva
    clave normalizada difiere, mueve la fila (y falla si hay colision)."""
    if not is_valid_vendor_id(vendor_id) or not owner_username:
        return None

    stmt = select(VendorCatalogProduct).where(
        VendorCatalogProduct.owner_username == owner_username,
        VendorCatalogProduct.vendor_id == vendor_id,
        VendorCatalogProduct.product_key == product_key,
    )
    row = (await db.execute(stmt)).scalar_one_or_none()
    if row is None:
        return None

    new_desc = row.descripcion or ""
    if "descripcion_original" in updates and updates["descripcion_original"] is not None:
        val = str(updates["descripcion_original"]).strip()
        if val:
            new_desc = val

    if "ncm" in updates and updates["ncm"] is not None:
        row.ncm = str(updates["ncm"]).strip() or None
    if "origen" in updates and updates["origen"] is not None:
        row.origen = str(updates["origen"]).strip() or None
    if "precio_ref" in updates and updates["precio_ref"] is not None:
        try:
            row.valor_unitario = float(updates["precio_ref"])
        except (TypeError, ValueError):
            pass
    if "unidad_medida" in updates and updates["unidad_medida"] is not None:
        merged = dict(row.extra or {})
        merged["unidad_medida"] = str(updates["unidad_medida"]).strip() or None
        row.extra = merged

    new_key = product_key
    if new_desc:
        candidate = _normalize(new_desc)
        if candidate and candidate != product_key:
            colision_stmt = select(VendorCatalogProduct).where(
                VendorCatalogProduct.owner_username == owner_username,
                VendorCatalogProduct.vendor_id == vendor_id,
                VendorCatalogProduct.product_key == candidate,
            )
            colision = (await db.execute(colision_stmt)).scalar_one_or_none()
            if colision is not None:
                return None
            row.product_key = candidate
            new_key = candidate

    row.descripcion = new_desc
    row.ultima_vez = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)

    return {**_row_to_dict(row), "_key": new_key}


async def delete_product(
    db: AsyncSession,
    vendor_id: str,
    product_key: str,
    owner_username: Optional[str] = None,
) -> bool:
    """Borra un producto individual. Devuelve True si existia."""
    if not is_valid_vendor_id(vendor_id) or not owner_username:
        return False

    stmt = sa_delete(VendorCatalogProduct).where(
        VendorCatalogProduct.owner_username == owner_username,
        VendorCatalogProduct.vendor_id == vendor_id,
        VendorCatalogProduct.product_key == product_key,
    )
    result = await db.execute(stmt)
    await db.commit()
    return (result.rowcount or 0) > 0


async def delete_vendor(
    db: AsyncSession,
    vendor_id: str,
    owner_username: Optional[str] = None,
) -> bool:
    """Borra un proveedor completo del catalogo del despachante."""
    if not is_valid_vendor_id(vendor_id) or not owner_username:
        return False

    stmt = sa_delete(VendorCatalogProduct).where(
        VendorCatalogProduct.owner_username == owner_username,
        VendorCatalogProduct.vendor_id == vendor_id,
    )
    result = await db.execute(stmt)
    await db.commit()
    return (result.rowcount or 0) > 0


# -----------------------------------------------------------------
# Shim de compatibilidad: clase CatalogService con metodos de clase
# que delegan a las funciones async. Esto es SOLO para que codigo
# legacy que haga `CatalogService.list_vendors(...)` sincrono no
# explote al importar, pero NO debe usarse desde handlers async
# nuevos. Todos los handlers nuevos deben llamar directo a las
# funciones async de este modulo.
# -----------------------------------------------------------------

class CatalogService:
    """DEPRECATED: usar las funciones async a nivel de modulo.

    Dejamos la clase para no romper imports legacy (scripts o tests
    viejos que hacen `from ... import CatalogService`). Todos los
    metodos levantan NotImplementedError; si alguno se llama, es que
    quedo codigo legacy sin migrar.
    """

    @classmethod
    def _legacy(cls, name: str):
        raise NotImplementedError(
            f"CatalogService.{name} ya no existe. Usar "
            f"proyecto_maria.core.catalog_service.{name} (async, recibe db)."
        )

    @classmethod
    def get_vendor(cls, *a, **k): return cls._legacy("get_vendor")
    @classmethod
    def get_vendor_by_id(cls, *a, **k): return cls._legacy("get_vendor_by_id")
    @classmethod
    def list_vendors(cls, *a, **k): return cls._legacy("list_vendors")
    @classmethod
    def match_items(cls, *a, **k): return cls._legacy("match_items")
    @classmethod
    def save_products(cls, *a, **k): return cls._legacy("save_products")
    @classmethod
    def update_product(cls, *a, **k): return cls._legacy("update_product")
    @classmethod
    def delete_product(cls, *a, **k): return cls._legacy("delete_product")
    @classmethod
    def delete_vendor(cls, *a, **k): return cls._legacy("delete_vendor")
