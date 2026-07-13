"""Preview seguro para migrar clientes desde CSV o Excel.

Este modulo es deliberadamente independiente de FastAPI y de la base de datos:
recibe bytes, analiza el archivo y devuelve estructuras JSON-serializables. La
confirmacion/persistencia debe vivir en otra capa y consumir ``staged_records``.

La migracion chica solo reconoce datos de la ficha del cliente. En particular,
ninguna columna de peso se acepta, aun si un mapeador externo (por ejemplo
Gemini) intenta asignarla.
"""

from __future__ import annotations

import hashlib
import inspect
import io
import re
import unicodedata
import zipfile
from collections import defaultdict
from collections.abc import Awaitable, Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, TypeAlias

import pandas as pd


MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_UNCOMPRESSED_XLSX_BYTES = 100 * 1024 * 1024
MAX_SHEETS = 50
MAX_ROWS = 50_000
SAMPLE_ROWS_FOR_HEADER_MAPPER = 5

CANONICAL_FIELDS = frozenset(
    {"nombre", "cuit", "direccion", "email", "telefono", "fecha_inic_activ"}
)
_FIELD_LIMITS = {
    "nombre": 200,
    "cuit": 32,
    "direccion": 500,
    "email": 254,
    "telefono": 50,
    "fecha_inic_activ": 32,
}

_COLUMN_ALIASES = {
    "nombre": (
        "nombre",
        "nombrecliente",
        "razonsocial",
        "razon",
        "cliente",
        "importador",
        "comprador",
        "denominacion",
        "company",
        "companyname",
        "customer",
        "customername",
        "name",
    ),
    "cuit": (
        "cuit",
        "cuitcuil",
        "cuitdni",
        "cuitcliente",
        "cuitimportador",
        "identificaciontributaria",
        "nroidtributaria",
        "documentotributario",
        "taxid",
        "taxnumber",
    ),
    "direccion": (
        "direccion",
        "direccionfiscal",
        "domicilio",
        "domiciliofiscal",
        "domicilioreal",
        "calle",
        "address",
        "billingaddress",
    ),
    "email": (
        "email",
        "emailcliente",
        "mail",
        "correo",
        "correoelectronico",
        "emailaddress",
    ),
    "telefono": (
        "telefono",
        "telefonocliente",
        "tel",
        "celular",
        "movil",
        "phone",
        "phonenumber",
        "mobile",
    ),
    "fecha_inic_activ": (
        "fechainicioactividades",
        "inicioactividades",
        "fechadealta",
        "fechaalta",
        "activitystartdate",
    ),
}

_FORBIDDEN_HEADER_PREFIXES = ("peso", "weight")
_EMPTY_STRINGS = frozenset({"", "nan", "none", "null", "n/a", "na", "s/d", "-"})
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

HeaderMapping: TypeAlias = Mapping[str, str]
HeaderMapperResult: TypeAlias = HeaderMapping | Awaitable[HeaderMapping]


class MigrationInputError(ValueError):
    """Error de archivo o formato que una ruta FastAPI puede devolver como 400."""


class HeaderMapper(Protocol):
    """Contrato opcional para interpretar encabezados ambiguos.

    El callback recibe encabezados y hasta cinco filas de muestra, y debe
    devolver ``{encabezado_original: campo_canonico}``. La salida se filtra por
    ``CANONICAL_FIELDS`` y nunca puede mapear encabezados de peso.
    """

    def __call__(
        self, headers: list[str], sample_rows: list[dict[str, str]]
    ) -> HeaderMapperResult: ...


@dataclass(frozen=True)
class _Sheet:
    name: str
    frame: pd.DataFrame


def normalize_header(value: Any) -> str:
    """Normaliza un encabezado para compararlo sin tildes ni puntuacion."""

    text = unicodedata.normalize("NFKD", str(value or "").strip().lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", text)


def normalize_cuit(value: Any) -> str | None:
    """Devuelve un CUIT argentino valido de 11 digitos o ``None``.

    Acepta CUIT con guiones/espacios y numeros que Excel haya representado con
    un sufijo ``.0``. Tambien valida el digito verificador modulo 11.
    """

    text = _cell_text(value, limit=64)
    if not text:
        return None
    if re.fullmatch(r"\d{11}\.0+", text):
        text = text.split(".", 1)[0]
    digits = re.sub(r"\D", "", text)
    if len(digits) != 11:
        return None
    multipliers = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
    remainder = sum(int(digit) * factor for digit, factor in zip(digits[:10], multipliers)) % 11
    verifier = 11 - remainder
    if verifier == 11:
        verifier = 0
    elif verifier == 10:
        return None
    return digits if verifier == int(digits[-1]) else None


def detect_client_columns(headers: Iterable[Any]) -> dict[str, str]:
    """Detecta ``{campo_canonico: encabezado_original}`` por aliases conocidos."""

    normalized: dict[str, str] = {}
    for header in headers:
        original = str(header or "").strip()
        normalized.setdefault(normalize_header(original), original)

    mapping: dict[str, str] = {}
    for canonical, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            original = normalized.get(normalize_header(alias))
            if original and not _is_forbidden_header(original):
                mapping[canonical] = original
                break
    return mapping


def sanitize_header_mapping(headers: Iterable[Any], mapping: HeaderMapping | None) -> dict[str, str]:
    """Filtra la salida de un mapeador externo con una allowlist estricta.

    Se admite el contrato recomendado ``{source: canonical}`` y, para facilitar
    integraciones, tambien ``{canonical: source}``. El resultado siempre queda
    como ``{canonical: source}``.
    """

    if not isinstance(mapping, Mapping):
        return {}
    originals = {str(header or "").strip(): str(header or "").strip() for header in headers}
    normalized_originals = {normalize_header(header): header for header in originals}
    safe: dict[str, str] = {}

    for raw_key, raw_value in mapping.items():
        key = str(raw_key or "").strip()
        value = str(raw_value or "").strip()
        if value in CANONICAL_FIELDS:
            source, canonical = key, value
        elif key in CANONICAL_FIELDS:
            source, canonical = value, key
        else:
            continue
        source = originals.get(source) or normalized_originals.get(normalize_header(source), "")
        if not source or _is_forbidden_header(source) or canonical in safe:
            continue
        safe[canonical] = source
    return safe


def analyze_migration_file(
    content: bytes,
    filename: str,
    *,
    existing_clients: Iterable[Any] = (),
    header_mapper: HeaderMapper | None = None,
) -> dict[str, Any]:
    """Analiza CSV/XLS/XLSX y construye un preview sin escribir en la DB.

    ``existing_clients`` puede contener diccionarios u objetos ORM. Solo se usa
    para comparar por CUIT y clasificar los registros. ``header_mapper`` es
    opcional y debe ser sincrono en esta funcion; para callbacks async usar
    :func:`analyze_migration_file_async`.
    """

    sheets = _read_sheets(content, filename)
    mappings: dict[str, dict[str, str]] = {}
    sheet_summaries: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    omitted: list[dict[str, Any]] = []
    total_rows = 0

    for sheet in sheets:
        mapping = detect_client_columns(sheet.frame.columns)
        if ("cuit" not in mapping or "nombre" not in mapping) and header_mapper:
            request_headers, samples = _mapper_payload(sheet.frame)
            external = header_mapper(request_headers, samples)
            if inspect.isawaitable(external):
                raise TypeError("header_mapper async: use analyze_migration_file_async")
            for canonical, source in sanitize_header_mapping(sheet.frame.columns, external).items():
                mapping.setdefault(canonical, source)

        mappings[sheet.name] = mapping
        sheet_summaries.append(
            {
                "name": sheet.name,
                "rows": int(len(sheet.frame)),
                "recognized": bool("cuit" in mapping or "nombre" in mapping),
                "columns": mapping,
            }
        )
        total_rows += int(len(sheet.frame))
        if total_rows > MAX_ROWS:
            raise MigrationInputError(f"El archivo supera el limite de {MAX_ROWS} filas")

        if "cuit" not in mapping:
            for offset in range(len(sheet.frame)):
                omitted.append(_omitted(sheet.name, offset + 2, "missing_cuit_column"))
            continue
        _collect_rows(sheet, mapping, rows, omitted)

    return _build_preview(
        content=content,
        filename=filename,
        total_rows=total_rows,
        sheets=sheet_summaries,
        mappings=mappings,
        rows=rows,
        omitted=omitted,
        existing_clients=existing_clients,
    )


async def analyze_migration_file_async(
    content: bytes,
    filename: str,
    *,
    existing_clients: Iterable[Any] = (),
    header_mapper: HeaderMapper | None = None,
) -> dict[str, Any]:
    """Version async para FastAPI cuando el mapeador opcional llama a Gemini."""

    if header_mapper is None:
        return analyze_migration_file(content, filename, existing_clients=existing_clients)

    sheets = _read_sheets(content, filename)
    external_mappings: dict[tuple[str, ...], dict[str, str]] = {}
    for sheet in sheets:
        detected = detect_client_columns(sheet.frame.columns)
        if "cuit" in detected and "nombre" in detected:
            continue
        request_headers, samples = _mapper_payload(sheet.frame)
        result = header_mapper(request_headers, samples)
        if inspect.isawaitable(result):
            result = await result
        external_mappings[tuple(request_headers)] = sanitize_header_mapping(sheet.frame.columns, result)

    def cached_mapper(headers: list[str], _samples: list[dict[str, str]]) -> HeaderMapping:
        # Si dos hojas tienen los mismos headers, el mismo mapeo seguro es
        # igualmente valido. Los encabezados de peso ya fueron excluidos.
        return external_mappings.get(tuple(headers), {})

    return analyze_migration_file(
        content,
        filename,
        existing_clients=existing_clients,
        header_mapper=cached_mapper,
    )


def _read_sheets(content: bytes, filename: str) -> list[_Sheet]:
    if not isinstance(content, (bytes, bytearray)) or not content:
        raise MigrationInputError("El archivo esta vacio")
    if len(content) > MAX_FILE_BYTES:
        raise MigrationInputError(f"El archivo supera el limite de {MAX_FILE_BYTES // (1024 * 1024)} MB")

    suffix = Path(filename or "").suffix.lower()
    try:
        if suffix == ".csv":
            return [_Sheet(name="CSV", frame=_read_csv(bytes(content)))]
        if suffix in {".xlsx", ".xls"}:
            if suffix == ".xlsx":
                _validate_xlsx_archive(bytes(content))
            workbook = pd.read_excel(
                io.BytesIO(content),
                sheet_name=None,
                dtype=str,
                keep_default_na=False,
            )
            if len(workbook) > MAX_SHEETS:
                raise MigrationInputError(f"El archivo supera el limite de {MAX_SHEETS} hojas")
            return [
                _Sheet(name=str(name), frame=_clean_frame(frame))
                for name, frame in workbook.items()
                if not frame.empty
            ] or [_Sheet(name="Hoja 1", frame=pd.DataFrame())]
    except MigrationInputError:
        raise
    except ImportError as exc:
        raise MigrationInputError("Falta la dependencia para leer este formato de Excel") from exc
    except Exception as exc:
        raise MigrationInputError(f"No se pudo leer el archivo: {str(exc)[:160]}") from exc
    raise MigrationInputError("Formato no soportado. Usa .csv, .xls o .xlsx")


def _read_csv(content: bytes) -> pd.DataFrame:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = content.decode(encoding)
            frame = pd.read_csv(
                io.StringIO(text),
                dtype=str,
                keep_default_na=False,
                sep=None,
                engine="python",
            )
            return _clean_frame(frame)
        except Exception as exc:
            last_error = exc
    raise MigrationInputError(f"No se pudo interpretar el CSV: {str(last_error)[:120]}")


def _validate_xlsx_archive(content: bytes) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            if sum(item.file_size for item in archive.infolist()) > MAX_UNCOMPRESSED_XLSX_BYTES:
                raise MigrationInputError("El Excel descomprimido es demasiado grande")
    except MigrationInputError:
        raise
    except zipfile.BadZipFile as exc:
        raise MigrationInputError("El archivo XLSX no es valido") from exc


def _clean_frame(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned.columns = [str(column or "").strip() for column in cleaned.columns]
    return cleaned.fillna("")


def _mapper_payload(frame: pd.DataFrame) -> tuple[list[str], list[dict[str, str]]]:
    headers = [str(header) for header in frame.columns if not _is_forbidden_header(header)]
    samples: list[dict[str, str]] = []
    for _, row in frame.head(SAMPLE_ROWS_FOR_HEADER_MAPPER).iterrows():
        samples.append({header: _cell_text(row.get(header), limit=120) for header in headers})
    return headers, samples


def _collect_rows(
    sheet: _Sheet,
    mapping: Mapping[str, str],
    rows: list[dict[str, Any]],
    omitted: list[dict[str, Any]],
) -> None:
    for offset, (_, source) in enumerate(sheet.frame.iterrows(), start=2):
        values = {
            field: _field_text(field, source.get(column, ""))
            for field, column in mapping.items()
            if field in CANONICAL_FIELDS
        }
        raw_cuit = values.get("cuit", "")
        cuit = normalize_cuit(raw_cuit)
        if not cuit:
            reason = "missing_cuit" if not raw_cuit else "invalid_cuit"
            omitted.append(_omitted(sheet.name, offset, reason, raw_cuit))
            continue
        values["cuit"] = cuit
        invalid_fields: list[str] = []
        if not values.get("nombre"):
            invalid_fields.append("nombre")
        if values.get("email") and not _EMAIL_RE.fullmatch(values["email"]):
            invalid_fields.append("email")
        rows.append(
            {
                **{field: values.get(field, "") for field in CANONICAL_FIELDS},
                "source_rows": [{"sheet": sheet.name, "row": offset}],
                "invalid_fields": invalid_fields,
            }
        )


def _build_preview(
    *,
    content: bytes,
    filename: str,
    total_rows: int,
    sheets: list[dict[str, Any]],
    mappings: dict[str, dict[str, str]],
    rows: list[dict[str, Any]],
    omitted: list[dict[str, Any]],
    existing_clients: Iterable[Any],
) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["cuit"]].append(row)

    existing_by_cuit: dict[str, list[dict[str, str]]] = defaultdict(list)
    for client in existing_clients or ():
        normalized = _existing_client(client)
        if normalized["cuit"]:
            existing_by_cuit[normalized["cuit"]].append(normalized)

    new_clients: list[dict[str, Any]] = []
    found_existing: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    staged: list[dict[str, Any]] = []

    file_hash = hashlib.sha256(content).hexdigest()
    for cuit in sorted(grouped):
        merged, upload_conflicts = _merge_upload_rows(grouped[cuit])
        record_id = hashlib.sha256(f"{file_hash}:{cuit}".encode()).hexdigest()[:24]
        base: dict[str, Any] = {
            "record_id": record_id,
            "cuit": cuit,
            "nombre": merged["nombre"],
            "direccion": merged["direccion"],
            "email": merged["email"],
            "telefono": merged["telefono"],
            "fecha_inic_activ": merged["fecha_inic_activ"],
            "source_rows": merged["source_rows"],
        }
        invalid_fields = sorted(set(merged["invalid_fields"]))
        matches = existing_by_cuit.get(cuit, [])

        if len(matches) > 1:
            record = {
                **base,
                "status": "conflict",
                "action": "review",
                "ready": False,
                "reason": "multiple_existing_clients",
                "existing_ids": [match["id"] for match in matches if match["id"]],
                "conflicting_fields": {},
            }
            conflicts.append(record)
        elif upload_conflicts or invalid_fields:
            record = {
                **base,
                "status": "conflict",
                "action": "review",
                "ready": False,
                "reason": "conflicting_upload_rows" if upload_conflicts else "invalid_fields",
                "conflicting_fields": upload_conflicts,
                "invalid_fields": invalid_fields,
            }
            conflicts.append(record)
        elif not matches:
            record = {**base, "status": "new", "action": "create", "ready": True}
            new_clients.append(record)
        else:
            existing = matches[0]
            field_conflicts: dict[str, dict[str, str]] = {}
            fillable: list[str] = []
            for field in ("nombre", "direccion", "email", "telefono", "fecha_inic_activ"):
                incoming_value = base[field]
                existing_value = existing[field]
                if incoming_value and not existing_value:
                    fillable.append(field)
                elif incoming_value and existing_value and not _same_field(field, incoming_value, existing_value):
                    field_conflicts[field] = {"incoming": incoming_value, "existing": existing_value}
            if field_conflicts:
                record = {
                    **base,
                    "status": "conflict",
                    "action": "review",
                    "ready": False,
                    "reason": "existing_data_differs",
                    "existing_id": existing["id"],
                    "conflicting_fields": field_conflicts,
                    "fillable_fields": fillable,
                }
                conflicts.append(record)
            else:
                action = "fill_empty" if fillable else "skip"
                record = {
                    **base,
                    "status": "existing",
                    "action": action,
                    "ready": True,
                    "existing_id": existing["id"],
                    "fillable_fields": fillable,
                }
                found_existing.append(record)
        staged.append(record)

    summary = {
        "new": len(new_clients),
        "existing": len(found_existing),
        "conflicts": len(conflicts),
        "omitted": len(omitted),
        "staged": len(staged),
        # Alias explicitos para que el contrato HTTP sea autoexplicativo.
        "new_clients": len(new_clients),
        "existing_clients": len(found_existing),
        "total_rows": total_rows,
    }
    return {
        "filename": Path(filename or "archivo").name,
        "file_sha256": file_hash,
        "sheets": sheets,
        "total_rows": total_rows,
        "column_mappings": mappings,
        "summary": summary,
        "new_clients": new_clients,
        "existing_clients": found_existing,
        "conflicts": conflicts,
        "omitted": omitted,
        "staged_records": staged,
    }


def _merge_upload_rows(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, list[str]]]:
    merged = {
        "cuit": rows[0]["cuit"],
        "nombre": "",
        "direccion": "",
        "email": "",
        "telefono": "",
        "fecha_inic_activ": "",
        "source_rows": [],
        "invalid_fields": [],
    }
    conflicts: dict[str, list[str]] = {}
    for row in rows:
        merged["source_rows"].extend(row["source_rows"])
        merged["invalid_fields"].extend(row["invalid_fields"])
        for field in ("nombre", "direccion", "email", "telefono", "fecha_inic_activ"):
            value = row[field]
            if not value:
                continue
            if not merged[field]:
                merged[field] = value
            elif not _same_field(field, merged[field], value):
                values = conflicts.setdefault(field, [merged[field]])
                if value not in values:
                    values.append(value)
    return merged, conflicts


def _existing_client(client: Any) -> dict[str, str]:
    aliases = {
        "id": ("id", "client_id"),
        "nombre": ("nombre", "name", "razon_social"),
        "cuit": ("cuit",),
        "direccion": ("direccion", "address"),
        "email": ("email",),
        "telefono": ("telefono", "phone"),
        "fecha_inic_activ": ("fecha_inic_activ",),
    }
    result: dict[str, str] = {}
    for field, candidates in aliases.items():
        value: Any = ""
        for candidate in candidates:
            if isinstance(client, Mapping) and candidate in client:
                value = client.get(candidate)
                break
            if hasattr(client, candidate):
                value = getattr(client, candidate)
                break
        result[field] = _field_text(field if field in CANONICAL_FIELDS else "nombre", value)
    result["cuit"] = normalize_cuit(result["cuit"]) or ""
    return result


def _same_field(field: str, left: str, right: str) -> bool:
    if field == "email":
        return left.casefold() == right.casefold()
    if field == "telefono":
        return re.sub(r"\D", "", left) == re.sub(r"\D", "", right)
    return normalize_header(left) == normalize_header(right)


def _field_text(field: str, value: Any) -> str:
    text = _cell_text(value, limit=_FIELD_LIMITS.get(field, 500))
    if field == "fecha_inic_activ" and text:
        for date_format in (
            "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%d-%m-%Y",
            "%d/%m/%y", "%d-%m-%y",
        ):
            try:
                return datetime.strptime(text, date_format).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return ""
    return text.casefold() if field == "email" else text


def _cell_text(value: Any, *, limit: int) -> str:
    if value is None:
        return ""
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", str(value)).strip()
    return "" if text.casefold() in _EMPTY_STRINGS else text[:limit]


def _is_forbidden_header(header: Any) -> bool:
    normalized = normalize_header(header)
    return normalized.startswith(_FORBIDDEN_HEADER_PREFIXES)


def _omitted(sheet: str, row: int, reason: str, cuit: str = "") -> dict[str, Any]:
    return {
        "sheet": sheet,
        "row": row,
        "reason": reason,
        "cuit": _cell_text(cuit, limit=32),
        "status": "omitted",
        "action": "skip",
        "ready": False,
    }
