"""Lightweight NCM catalog loader/searcher.

This module does not depend on AFIP. It simply loads local CSV/JSON files so
we can perform lookups while we wait for the official integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import csv
import json
import unicodedata

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_CSV = DATA_DIR / "ncm_mercosur.csv"
DEFAULT_NOTES = DATA_DIR / "ncm_notas.json"


@dataclass
class NCMItem:
    codigo: str
    descripcion: str
    alicuota: str | None = None
    notas: list[str] | None = None

    def to_dict(self) -> dict:
        return {
            "codigo": self.codigo,
            "descripcion": self.descripcion,
            "alicuota": self.alicuota,
            "notas": self.notas or [],
        }


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()


def _load_notes(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


@lru_cache(maxsize=1)
def load_catalog(csv_path: Path = DEFAULT_CSV, notes_path: Path = DEFAULT_NOTES) -> list[NCMItem]:
    items: list[NCMItem] = []
    notes = _load_notes(notes_path)

    if not csv_path.exists():
        return items

    with csv_path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            codigo = (row.get("codigo") or row.get("ncm") or "").strip()
            if not codigo:
                continue
            descripcion = (row.get("descripcion") or row.get("detalle") or "").strip()
            alicuota = (row.get("alicuota") or row.get("derecho") or "").strip() or None
            item = NCMItem(
                codigo=codigo.replace(".", ""),
                descripcion=descripcion,
                alicuota=alicuota,
                notas=notes.get(codigo.replace(".", "")),
            )
            items.append(item)
    return items


def find_by_code(code: str) -> NCMItem | None:
    code_norm = (code or "").replace(".", "").strip()
    if not code_norm:
        return None
    for item in load_catalog():
        if item.codigo == code_norm:
            return item
    return None


def search_term(term: str, limit: int = 10) -> list[NCMItem]:
    term_norm = _normalize(term)
    if not term_norm:
        return []

    results: list[NCMItem] = []
    catalog = load_catalog()
    for item in catalog:
        if term_norm in _normalize(item.codigo) or term_norm in _normalize(item.descripcion):
            results.append(item)
            if len(results) >= limit:
                break
    return results


