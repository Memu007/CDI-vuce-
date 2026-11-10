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
import functools
import hashlib
import math
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

# Tope común del catálogo, la memoria del cliente y el historial, medido en NFC
# como guarda la memoria: lo que entra en una entra en las otras.
MAX_DESCRIPCION = 2000


def validar_largo(texto: str, que: str = "La descripción") -> None:
    if len(unicodedata.normalize("NFC", texto)) > MAX_DESCRIPCION:
        raise ValueError(f"{que} pasa de {MAX_DESCRIPCION} caracteres.")


_MEDIO_PAR = re.compile("[\ud800-\udfff]")  # no se puede escribir en UTF-8
AVISO_MEDIO_PAR = "Hay un carácter que no se puede guardar."
AVISO_NO_ES_OBJETO = "Cada producto tiene que ser un objeto."


def texto_para_guardar(valor, que: str = "La descripción") -> str:
    """El texto como se guarda: sin NUL ni espacios en los bordes; None es vacío.
    ValueError con el motivo para el usuario si no se puede guardar."""
    if valor is None:
        return ""
    if not isinstance(valor, str):
        raise ValueError(f"{que} tiene que ser texto.")
    valor = valor.replace("\x00", "").strip()
    if _MEDIO_PAR.search(valor):
        raise ValueError(AVISO_MEDIO_PAR)
    validar_largo(valor, que)
    return valor


# Tope de la columna del NCM; se cuenta como se guarda, sin normalizar.
MAX_NCM = 20


def ncm_para_guardar(valor) -> str:
    ncm = texto_para_guardar(valor, "El NCM")
    if len(ncm) > MAX_NCM:
        raise ValueError(f"El NCM pasa de {MAX_NCM} caracteres.")
    return ncm


def origen_para_guardar(valor) -> tuple[str, str]:
    """(origen, aviso): ("", aviso) si no es un país de la tabla; «XX» es el
    «sin origen» de la factura. ValueError si no se puede guardar como texto."""
    origen = texto_para_guardar(valor, "El origen")
    if not origen or origen.upper() == "XX":
        return "", ""
    # Import local: despacho_lector importa de este módulo.
    from proyecto_maria.core.despacho_lector import origen_para_catalogo
    guardado, aviso = origen_para_catalogo(origen)
    return ("", aviso) if aviso else (guardado or "", "")


# Patron valido para vendor_id (slug generado por _vendor_key).
_VENDOR_ID_RE = re.compile(r"^[a-z0-9_~]{1,60}$")


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
    if not text.isascii():
        text = unicodedata.normalize("NFD", text)
        text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def _sufijo(texto: str) -> str:
    """Resumen de las letras y cifras no latinas que _normalize descarta (CJK,
    kana, griego): «º» y «ª» no cuentan; «µ» llega como «μ» y sí."""
    fuera = "".join(
        c for c in unicodedata.normalize("NFC", texto)
        if c > "\u024f" and (unicodedata.category(c)[0] == "L" or unicodedata.category(c) == "Nd")
        if not _normalize(c) and not unicodedata.name(c, "").startswith("LATIN")
    )
    if not fuera:
        return ""
    return hashlib.sha256(fuera.casefold().encode("utf-8", "surrogatepass")).hexdigest()[:16]


def _compatible(texto: str) -> str:
    """NFKC salvo en «ºª№™℠», para que «Nº» siga igual a «N°» y «Bolt™» a «Bolt»;
    las unidades como «㎜» sí pasan a «mm»."""
    if texto.isascii() or unicodedata.is_normalized("NFKC", texto):
        return texto
    return unicodedata.normalize("NFC", "".join(
        c if c in "ºª№™℠" else unicodedata.normalize("NFKC", c)
        for c in texto
    ))


# La memoria del cliente la pide para cada fila guardada, una vez por ítem del pedido.
@functools.lru_cache(maxsize=4096)
def clave_de_producto(descripcion: str) -> str:
    """Clave del producto en el catálogo: lo que se lee igual da la misma."""
    return _clave(_compatible(descripcion))


def _clave(descripcion: str) -> str:
    """Lo que normaliza a vacío (CJK, emoji) usa un resumen del texto: entra en
    el índice único y «~» no sale de _normalize."""
    clave = _normalize(descripcion)
    sufijo = _sufijo(descripcion) if clave else ""
    if clave:
        return f"{clave}~{sufijo}" if sufijo else clave
    texto = " ".join(unicodedata.normalize("NFC", descripcion).lower().split())
    return "~" + hashlib.sha256(texto.encode("utf-8", "surrogatepass")).hexdigest()[:40]


def parecido(clave_a: str, clave_b: str) -> float:
    """Parecido entre dos claves de producto: con letras no latinas distintas
    no se parecen; si sólo una las tiene, a lo sumo llegan a parecidas."""
    if clave_a == clave_b:
        return 1.0
    base_a, _, sufijo_a = clave_a.partition("~")
    base_b, _, sufijo_b = clave_b.partition("~")
    if sufijo_a == sufijo_b:
        return _similarity(base_a, base_b)
    if sufijo_a and sufijo_b:
        return 0.0
    return min(_similarity(base_a, base_b), FUZZY_THRESHOLD)


_MAX_VENDOR_ID = 60


def _vendor_key(vendor_name: str) -> str:
    """Clave del proveedor; "" si el nombre no tiene nada. Si no entra en 60,
    el final es un resumen del total: dos nombres largos parecidos no se pisan."""
    nombre = (vendor_name or "").replace("\x00", "").strip()
    if not nombre:
        return ""
    clave = _clave(nombre).replace(" ", "_")
    if len(clave) <= _MAX_VENDOR_ID:
        return clave
    return clave[:39] + "~" + hashlib.sha256(clave.encode("utf-8")).hexdigest()[:20]


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
    rows = await _fetch_vendor_rows(db, owner_username, vendor_id) if vendor_id else []
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
    rows = await _fetch_vendor_rows(db, owner_username, vendor_id) if vendor_id else []

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

        desc_key = clave_de_producto(desc)
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
                score = parecido(desc_key, prod_key)
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

def _producto_valido(prod) -> Optional[tuple]:
    """(descripción, ncm, origen, unidad, precio, aviso), o None sin descripción.
    ValueError si un campo no se guarda; un origen no reconocido va vacío con aviso."""
    if not isinstance(prod, dict):
        raise ValueError(AVISO_NO_ES_OBJETO)
    desc = texto_para_guardar(prod.get("descripcion"))
    if not desc:
        return None
    ncm = ncm_para_guardar(prod.get("ncm")) or ncm_para_guardar(prod.get("pieza"))
    origen, aviso = origen_para_guardar(prod.get("origen"))
    unidad = texto_para_guardar(prod.get("unidad_medida"), "La unidad")
    return desc, ncm, origen, unidad, _precio(prod.get("valor_unitario")), aviso


def _producto_del_lote(numerado: tuple) -> Optional[tuple]:
    """_producto_valido con el número y la descripción en el error y en el aviso,
    para que la pantalla diga qué producto no se aprendió entero."""
    n, prod = numerado
    desc = prod.get("descripcion") if isinstance(prod, dict) else None
    desc = desc.replace("\x00", "").strip() if isinstance(desc, str) else ""
    cual = f"Producto {n}" + (f" («{desc[:60]}»)" if desc and not _MEDIO_PAR.search(desc) else "")
    try:
        valido = _producto_valido(prod)
    except ValueError as e:
        raise ValueError(f"{cual}: {e}") from None
    if valido is None:
        return None
    *campos, aviso = valido
    return (*campos, f"{cual}: {aviso}" if aviso else "")


def _precio(valor) -> Optional[float]:
    # JSON no escribe NaN ni infinito: guardado, rompería la lectura del catálogo.
    try:
        precio = float(valor)
    except (TypeError, ValueError, OverflowError):
        return None
    return precio if math.isfinite(precio) else None


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
            "avisos": [],
        }

    vendor_name = texto_para_guardar(vendor_name, "El proveedor")
    vendor_id = _vendor_key(vendor_name)
    if not vendor_id:
        raise ValueError("Falta el nombre del proveedor.")
    # Todo el lote se valida antes de escribir: uno malo no deja la mitad guardada.
    validos = [p for p in map(_producto_del_lote, enumerate(productos_in, 1)) if p]

    saved = 0
    updated = 0

    for desc, ncm, origen, unidad, precio, _aviso in validos:
        product_key = clave_de_producto(desc)
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
        "avisos": [p[5] for p in validos if p[5]],
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

    # None es «no cambia»; todos los textos se validan antes de tocar la fila.
    textos = {campo: texto_para_guardar(updates.get(campo), que) for campo, que in (
        ("descripcion_original", "La descripción"),
        ("unidad_medida", "La unidad"),
    ) if updates.get(campo) is not None}
    aviso = ""
    if updates.get("origen") is not None:
        origen, aviso = origen_para_guardar(updates["origen"])
        if not aviso:
            textos["origen"] = origen
    if updates.get("ncm") is not None:
        textos["ncm"] = ncm_para_guardar(updates["ncm"])

    new_desc = textos.get("descripcion_original") or row.descripcion or ""
    if "ncm" in textos:
        row.ncm = textos["ncm"] or None
    if "origen" in textos:
        row.origen = textos["origen"] or None
    precio = _precio(updates.get("precio_ref"))
    if precio is not None:
        row.valor_unitario = precio
    if "unidad_medida" in textos:
        merged = dict(row.extra or {})
        merged["unidad_medida"] = textos["unidad_medida"] or None
        row.extra = merged

    new_key = product_key
    # Sólo una descripción nueva mueve la clave: una fila con clave de antes
    # sigue editable por la clave que tiene.
    if new_desc != (row.descripcion or ""):
        candidate = clave_de_producto(new_desc)
        if candidate != product_key:
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

    return {**_row_to_dict(row), "_key": new_key, **({"aviso": aviso} if aviso else {})}


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
