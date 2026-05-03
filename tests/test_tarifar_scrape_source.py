"""Tests de integracion logica de TarifarClient con VUCE en modo scrape.

Verifica que cuando `get_ncm_data` devuelve datos con `source=scrape:*`, la
calculadora de Tarifar los propaga correctamente al metadata agregado en vez
de marcar la respuesta como `tarifar_fake`.

No tocamos red ni DB: monkeypatcheamos `get_ncm_data` en el modulo para simular
respuestas de la VUCE.
"""

from __future__ import annotations

from proyecto_maria.core import tarifar_connector
from proyecto_maria.core.tarifar_connector import (
    TarifarClient,
    TarifarConfig,
    _aggregate_sources,
)


def _ncm_response(source: str, ncm: str = "39269099") -> dict:
    return {
        "ncm": ncm,
        "descripcion": "Test NCM",
        "alicuotas": {
            "arancel_base": 16.0,
            "arancel_mercosur": 0.0,
            "iva": 21.0,
            "estadistica": 3.0,
            "derechos_exportacion": 0.0,
        },
        "licencias": [],
        "regimen_especial": "General",
        "unidad_medida": "KG",
        "origen_preferencial": ["BR", "PY", "UY"],
        "vigente": True,
        "fuente": source,
        "source": source,
    }


def _item(ncm: str = "39269099") -> dict:
    return {
        "pieza": ncm,
        "descripcion": "Test",
        "origen": "CN",
        "cantidad": 10,
        "valor_unitario": 50.0,
        "peso_unitario": 1.0,
    }


def test_aggregate_sources_all_scrape_returns_most_common():
    assert _aggregate_sources(["scrape:tarifar", "scrape:tarifar", "scrape:arancel"]) == "scrape:tarifar"


def test_aggregate_sources_mixed_scrape_and_fake_degrades_to_partial():
    assert _aggregate_sources(["scrape:tarifar", "fake", "scrape:arancel"]) == "tarifar_scrape_partial"


def test_aggregate_sources_all_fake_returns_fake():
    assert _aggregate_sources(["fake", "vuce_fake", ""]) == "tarifar_fake"


def test_aggregate_sources_empty_returns_fake():
    assert _aggregate_sources([]) == "tarifar_fake"


def test_aggregate_sources_api_beats_scrape_when_no_fake():
    assert _aggregate_sources(["api:vuce", "scrape:tarifar"]) == "api:vuce"


def test_calcular_aranceles_propaga_source_scrape(monkeypatch):
    """Cuando VUCE devuelve scrape:tarifar, el metadata final no debe decir fake."""
    monkeypatch.setattr(
        tarifar_connector,
        "get_ncm_data",
        lambda ncm: _ncm_response("scrape:tarifar", ncm),
    )
    # Evitar los sleeps del modo fake para que el test sea rapido
    monkeypatch.setattr(tarifar_connector.time, "sleep", lambda *_args, **_kw: None)

    client = TarifarClient(config=TarifarConfig(mode="scrape"))
    result = client.calcular_aranceles([_item(), _item()])

    assert result["success"] is True
    assert result["metadata"]["source"] == "scrape:tarifar", (
        "La fuente agregada debe reflejar el scraping, no tarifar_fake"
    )
    # El chip de la UI se basa en esta key; que no diga fake
    assert "fake" not in result["metadata"]["source"]


def test_calcular_aranceles_propaga_source_partial_cuando_mezcla(monkeypatch):
    """Si un item vino de scrape y otro fake, la etiqueta debe ser partial."""
    calls = {"count": 0}

    def fake_ncm(ncm):
        calls["count"] += 1
        return _ncm_response("scrape:tarifar" if calls["count"] == 1 else "fake", ncm)

    monkeypatch.setattr(tarifar_connector, "get_ncm_data", fake_ncm)
    monkeypatch.setattr(tarifar_connector.time, "sleep", lambda *_a, **_k: None)

    client = TarifarClient(config=TarifarConfig(mode="scrape"))
    result = client.calcular_aranceles([_item("39269099"), _item("84715000")])
    assert result["metadata"]["source"] == "tarifar_scrape_partial"


def test_calcular_aranceles_todo_fake_sigue_siendo_fake(monkeypatch):
    monkeypatch.setattr(
        tarifar_connector,
        "get_ncm_data",
        lambda ncm: _ncm_response("vuce_fake", ncm),
    )
    monkeypatch.setattr(tarifar_connector.time, "sleep", lambda *_a, **_k: None)

    client = TarifarClient(config=TarifarConfig(mode="fake"))
    result = client.calcular_aranceles([_item()])
    assert result["metadata"]["source"] == "tarifar_fake"
