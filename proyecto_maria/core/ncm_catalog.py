"""Catálogo NCM local de ARCA y buscador sin servicios externos.

El catálogo versionado se genera desde el nomenclador publicado por ARCA. La
búsqueda sirve para orientar al despachante hacia una NCM de ocho dígitos; la
posición SIM completa y su DC se siguen confirmando en VUCE.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from collections import defaultdict
import csv
import gzip
import json
import re
import unicodedata
from typing import Iterable


DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DEFAULT_CSV = DATA_DIR / "ncm_arca.csv.gz"
LEGACY_CSV = DATA_DIR / "ncm_mercosur.csv"
DEFAULT_METADATA = DATA_DIR / "ncm_arca_metadata.json"

_STOPWORDS = frozenset({
    "a", "al", "con", "de", "del", "el", "en", "la", "las", "los",
    "o", "para", "por", "sin", "un", "una", "unos", "unas", "y",
})

# Equivalencias comerciales frecuentes. Son ayudas de búsqueda, no nuevas
# clasificaciones: el resultado siempre conserva el texto oficial de ARCA.
_QUERY_EXPANSIONS = {
    "notebook": {"laptop", "portatil", "maquina", "automatica", "datos"},
    "laptop": {"notebook", "portatil", "maquina", "automatica", "datos"},
    "portatil": {"notebook", "laptop", "maquina", "automatica", "datos"},
    "celular": {"telefono", "smartphone", "movil"},
    "telefono": {"celular", "smartphone", "movil"},
    "smartphone": {"celular", "telefono", "movil"},
    "movil": {"celular", "telefono", "smartphone"},
    "mesa": {"mueble", "mobiliario"},
    "mueble": {"mesa", "mobiliario"},
    "remera": {"camiseta", "tshirt"},
    "camiseta": {"remera", "tshirt"},
    "tshirt": {"camiseta", "remera"},
    "motor": {"electrico", "corriente"},
    "electrico": {"motor", "corriente"},
    "tornillo": {"perno", "roscado"},
}


def normalize_text(value: str) -> str:
    """Normaliza mayúsculas, acentos y puntuación para buscar."""
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def _stem(word: str) -> str:
    """Plural español simple, suficiente para la búsqueda local."""
    if len(word) > 5 and word.endswith("ces"):
        return word[:-3] + "z"
    if len(word) > 5 and word.endswith("es"):
        return word[:-2]
    if len(word) > 4 and word.endswith("s"):
        return word[:-1]
    return word


def _tokens(value: str) -> frozenset[str]:
    return frozenset(
        _stem(word) for word in normalize_text(value).split()
        if len(word) >= 2 and word not in _STOPWORDS
    )


def _expanded_query_tokens(value: str) -> tuple[frozenset[str], frozenset[str]]:
    direct = _tokens(value)
    expanded = set(direct)
    for term in direct:
        expanded.update(_stem(normalize_text(alias)) for alias in _QUERY_EXPANSIONS.get(term, set()))
    return direct, frozenset(expanded)


def _clean_description(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip(" -\t")).strip()


def _is_generic(value: str) -> bool:
    text = normalize_text(value)
    return text in {"los demas", "las demas", "los demas productos"}


@dataclass
class NCMItem:
    codigo: str
    descripcion: str
    alicuota: str | None = None
    notas: list[str] | None = None
    source: str = "ARCA"
    updated_at: str = ""
    search_text: str = ""
    _search_tokens: frozenset[str] = field(default_factory=frozenset, repr=False)
    _search_normalized: str = field(default="", repr=False)
    _display_tokens: frozenset[str] = field(default_factory=frozenset, repr=False)
    _first_display_token: str = field(default="", repr=False)

    def to_dict(self) -> dict:
        return {
            "codigo": self.codigo,
            "descripcion": self.descripcion,
            "alicuota": self.alicuota,
            "notas": self.notas or [],
            "source": self.source,
            "updated_at": self.updated_at,
        }


def _load_notes(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _open_catalog(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8", newline="")
    return path.open(encoding="utf-8", newline="")


@lru_cache(maxsize=1)
def get_catalog_metadata(path: Path = DEFAULT_METADATA) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


@lru_cache(maxsize=3)
def load_catalog(
    csv_path: Path = DEFAULT_CSV,
    notes_path: Path = DATA_DIR / "ncm_notas.json",
) -> list[NCMItem]:
    """Carga el catálogo ARCA; conserva el CSV breve sólo como respaldo local."""
    selected_path = csv_path if csv_path.exists() else LEGACY_CSV
    if not selected_path.exists():
        return []

    notes = _load_notes(notes_path)
    default_meta = get_catalog_metadata() if selected_path == DEFAULT_CSV else {}
    items: list[NCMItem] = []
    with _open_catalog(selected_path) as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            codigo = re.sub(r"\D", "", row.get("codigo") or row.get("ncm") or "")[:8]
            if len(codigo) != 8:
                continue
            descripcion = (row.get("descripcion") or row.get("detalle") or "").strip()
            search_text = (row.get("search_text") or descripcion).strip()
            source = (row.get("source") or default_meta.get("source") or "ARCA").strip()
            updated_at = (row.get("updated_at") or default_meta.get("updated_at") or "").strip()
            alicuota = (row.get("alicuota") or row.get("derecho") or "").strip() or None
            normalized_search = normalize_text(search_text)
            normalized_description = normalize_text(descripcion)
            display_tokens = _tokens(normalized_description)
            items.append(NCMItem(
                codigo=codigo,
                descripcion=descripcion,
                alicuota=alicuota,
                notas=notes.get(codigo),
                source=source,
                updated_at=updated_at,
                search_text=search_text,
                _search_tokens=_tokens(normalized_search),
                _search_normalized=normalized_search,
                _display_tokens=display_tokens,
                _first_display_token=(
                    _stem(normalized_description.split()[0]) if normalized_description else ""
                ),
            ))
    return items


def find_by_code(code: str, catalog: list[NCMItem] | None = None) -> NCMItem | None:
    code_norm = re.sub(r"\D", "", code or "")[:8]
    if len(code_norm) != 8:
        return None
    return next((item for item in (catalog if catalog is not None else load_catalog()) if item.codigo == code_norm), None)


def search_term(term: str, limit: int = 5, catalog: list[NCMItem] | None = None) -> list[NCMItem]:
    """Busca NCM oficiales por código, palabras y coincidencias parciales."""
    limit = max(1, min(int(limit or 5), 5))
    raw = str(term or "").strip()
    if not raw:
        return []

    code_query = re.sub(r"\D", "", raw)
    direct_tokens, query_tokens = _expanded_query_tokens(raw)
    phrase = normalize_text(raw)

    # Una posición exacta no necesita ranking textual: evita que una parte de
    # su número se confunda con palabras o códigos de otros resultados.
    items = catalog if catalog is not None else load_catalog()
    if len(code_query) >= 8:
        exact = next((item for item in items if item.codigo == code_query[:8]), None)
        return [exact] if exact else []
    ranked: list[tuple[int, NCMItem]] = []

    for item in items:
        score = 0
        if code_query and len(code_query) >= 4:
            if item.codigo.startswith(code_query):
                score += 500

        if query_tokens:
            normalized_search = item._search_normalized or normalize_text(item.search_text)
            if phrase and normalized_search.startswith(phrase):
                score += 180
            elif phrase and phrase in normalized_search:
                score += 60
            display_tokens = item._display_tokens or _tokens(item.descripcion)
            if direct_tokens and all(
                any(candidate.startswith(token) for candidate in display_tokens)
                for token in direct_tokens
            ):
                score += 100
            first_display_token = item._first_display_token or (
                _stem(normalize_text(item.descripcion).split()[0]) if item.descripcion else ""
            )
            if first_display_token and any(first_display_token.startswith(token) for token in direct_tokens):
                score += 80
            for token in query_tokens:
                if token in item._search_tokens:
                    score += 36 if token in direct_tokens else 18
                elif len(token) >= 4 and any(
                    candidate.startswith(token)
                    for candidate in item._search_tokens
                ):
                    score += 9 if token in direct_tokens else 5

        if score:
            ranked.append((score, item))

    ranked.sort(key=lambda row: (-row[0], row[1].codigo))
    return [item for _, item in ranked[:limit]]


def parse_arca_nomenclador(lines: Iterable[str]) -> list[dict[str, str]]:
    """Convierte el nomenclador ARCA en filas buscables por NCM de 8 dígitos.

    El archivo oficial contiene niveles de capítulo, partida, NCM y SIM. Se
    preservan los textos oficiales de los niveles que llevan a cada NCM, sin
    crear descripciones nuevas.
    """
    prefixes: dict[str, list[str]] = defaultdict(list)
    direct: dict[str, list[str]] = defaultdict(list)

    for line in lines:
        fields = line.rstrip("\n").split("@")
        if len(fields) < 3:
            continue
        code_digits = re.sub(r"\D", "", fields[1])
        description = _clean_description(fields[-1])
        if len(code_digits) < 2 or not description:
            continue
        if len(code_digits) < 8:
            prefixes[code_digits].append(description)
            continue

        ncm = code_digits[:8]
        chapter = int(ncm[:2]) if ncm[:2].isdigit() else 0
        if not 1 <= chapter <= 97:
            continue
        direct[ncm].append(description)

    rows: list[dict[str, str]] = []
    for ncm in sorted(direct):
        context: list[str] = []
        for length in range(2, 8):
            context.extend(prefixes.get(ncm[:length], []))
        context.extend(direct[ncm])

        unique_context = []
        seen = set()
        for text in context:
            cleaned = _clean_description(text)
            key = normalize_text(cleaned)
            if cleaned and key and key not in seen:
                unique_context.append(cleaned)
                seen.add(key)

        meaningful = [text for text in unique_context if not _is_generic(text)]
        display_parts = meaningful[:3] or unique_context[:1]
        rows.append({
            "codigo": ncm,
            "descripcion": " · ".join(display_parts)[:500],
            "search_text": " ".join(unique_context)[:5000],
        })
    return rows
