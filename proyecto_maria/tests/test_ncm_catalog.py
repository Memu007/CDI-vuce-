import json
from pathlib import Path

import pytest

from proyecto_maria.core import ncm_catalog


@pytest.fixture(autouse=True)
def reset_cache():
    ncm_catalog.load_catalog.cache_clear()  # type: ignore[attr-defined]


def test_load_catalog_returns_items(tmp_path: Path):
    csv_path = tmp_path / "ncm.csv"
    notes_path = tmp_path / "notes.json"
    csv_path.write_text("codigo,descripcion\n010121,Equinos\n", encoding="utf-8")
    notes_path.write_text(json.dumps({"010121": ["Nota 1"]}), encoding="utf-8")

    items = ncm_catalog.load_catalog(csv_path, notes_path)

    assert len(items) == 1
    assert items[0].descripcion == "Equinos"
    assert items[0].notas == ["Nota 1"]


def test_find_by_code(tmp_path: Path):
    csv_path = tmp_path / "ncm.csv"
    csv_path.write_text("codigo,descripcion\n38151210,Aditivos\n", encoding="utf-8")

    item = ncm_catalog.load_catalog(csv_path)[0]
    found = ncm_catalog.find_by_code("38151210")

    assert found is not None
    assert found.descripcion == item.descripcion


def test_search_term(tmp_path: Path):
    csv_path = tmp_path / "ncm.csv"
    csv_path.write_text("codigo,descripcion\n84195000,Intercambiador de calor\n", encoding="utf-8")

    results = ncm_catalog.search_term("intercambiador")

    assert len(results) == 1
    assert results[0].codigo == "84195000"


