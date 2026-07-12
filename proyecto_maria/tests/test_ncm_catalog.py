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
    csv_path.write_text("codigo,descripcion\n01012100,Equinos\n", encoding="utf-8")
    notes_path.write_text(json.dumps({"01012100": ["Nota 1"]}), encoding="utf-8")

    items = ncm_catalog.load_catalog(csv_path, notes_path)

    assert len(items) == 1
    assert items[0].descripcion == "Equinos"
    assert items[0].notas == ["Nota 1"]


def test_find_by_code(tmp_path: Path):
    csv_path = tmp_path / "ncm.csv"
    csv_path.write_text("codigo,descripcion\n38151210,Aditivos\n", encoding="utf-8")

    item = ncm_catalog.load_catalog(csv_path)[0]
    found = ncm_catalog.find_by_code("38151210", catalog=[item])

    assert found is not None
    assert found.descripcion == item.descripcion


def test_search_term(tmp_path: Path):
    csv_path = tmp_path / "ncm.csv"
    csv_path.write_text("codigo,descripcion\n84195000,Intercambiador de calor\n", encoding="utf-8")

    items = ncm_catalog.load_catalog(csv_path)
    results = ncm_catalog.search_term("intercambiador", catalog=items)

    assert len(results) == 1
    assert results[0].codigo == "84195000"


def test_parse_arca_nomenclador_conserva_texto_oficial_y_ncm_de_ocho_digitos():
    rows = ncm_catalog.parse_arca_nomenclador([
        "2@8471.30         @      @Máquinas automáticas portátiles\n",
        "2@8471.30.11.000U @000.00@De peso inferior a 350 g\n",
        "2@8471.30.12.000B @000.00@De peso inferior a 3,5 kg\n",
    ])

    assert rows == [{
        "codigo": "84713011",
        "descripcion": "Máquinas automáticas portátiles · De peso inferior a 350 g",
        "search_text": "Máquinas automáticas portátiles De peso inferior a 350 g",
    }, {
        "codigo": "84713012",
        "descripcion": "Máquinas automáticas portátiles · De peso inferior a 3,5 kg",
        "search_text": "Máquinas automáticas portátiles De peso inferior a 3,5 kg",
    }]


def test_catalogo_arca_busca_sinonimo_y_limita_a_cinco_resultados():
    result = ncm_catalog.search_term("notebook")

    assert len(result) == 5
    assert result[0].codigo.startswith("847130")
    assert result[0].source == "ARCA"

