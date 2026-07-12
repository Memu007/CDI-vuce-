"""El flag VUCE CI conserva alternativas SIM y fallback sin datos falsos."""

from __future__ import annotations

import pytest

from proyecto_maria.core.vuce_connector import VuceClient, VuceConfig


# Cobertura transversal: el mismo camino se prueba con 20 NCM de capítulos
# distintos. La respuesta es un double de VUCE CI: ninguna de estas entradas
# se publica ni se presenta como dato oficial fuera del test.
NCM_CASES = [
    "02013000", "04022110", "09011110", "10063021", "15079011",
    "17011400", "19053100", "21069090", "27101932", "30049099",
    "33049990", "39269099", "40111000", "44191100", "61091000",
    "73181500", "84151011", "84713011", "85011011", "94036000",
]


@pytest.mark.parametrize("ncm", NCM_CASES)
def test_vuce_ci_enabled_usa_resultado_oficial_y_conserva_sim_alternativas(
    monkeypatch, ncm
):
    monkeypatch.setenv("VUCE_CI_ENABLED", "true")
    expected = {
        "ncm": ncm,
        "codigo_sim": f"{ncm[:4]}.{ncm[4:6]}.{ncm[6:]}.000A",
        "sim_alternativas": [{"codigo_sim": f"{ncm[:4]}.{ncm[4:6]}.{ncm[6:]}.001B"}],
        "source": "vuce_ci_oficial",
    }
    monkeypatch.setattr(
        "proyecto_maria.core.vuce_ci_client.fetch_ncm_completo",
        lambda queried: expected if queried == ncm else None,
    )
    monkeypatch.setattr(
        "proyecto_maria.core.ncm_scraper.fetch_ncm_scrape",
        lambda _ncm: pytest.fail("No debe usar fallback si VUCE CI respondió"),
    )

    result = VuceClient(VuceConfig(mode="scrape"))._scrape_response(f"ncm/{ncm}", None)

    assert result == expected
    assert result["source"] == "vuce_ci_oficial"
    assert len(result["sim_alternativas"]) == 1


def test_vuce_ci_enabled_fallback_si_la_fuente_no_responde(monkeypatch):
    monkeypatch.setenv("VUCE_CI_ENABLED", "true")
    monkeypatch.setattr("proyecto_maria.core.vuce_ci_client.fetch_ncm_completo", lambda _ncm: None)
    monkeypatch.setattr(
        "proyecto_maria.core.ncm_scraper.fetch_ncm_scrape",
        lambda ncm: {"ncm": ncm, "source": "scrape:arancel"},
    )

    result = VuceClient(VuceConfig(mode="scrape"))._scrape_response("ncm/84713011", None)

    assert result == {"ncm": "84713011", "source": "scrape:arancel"}
