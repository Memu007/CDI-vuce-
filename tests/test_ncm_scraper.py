"""Tests del NCM scraper (tarifar.com + fallback arancel.com.ar).

No dependemos de `requests_mock` para evitar sumar una dependencia de testing
extra: parcheamos `proyecto_maria.core.ncm_scraper._rate_limited_get` con
`monkeypatch`. Asi testeamos parsers, fallback chain y normalizacion sin
tocar la red real.
"""

from __future__ import annotations

import pytest

from proyecto_maria.core import ncm_scraper
from proyecto_maria.core.ncm_scraper import (
    _extract_alicuotas,
    _extract_descripcion,
    _extract_licencias,
    _ncm_with_dots,
    _norm_ncm,
    fetch_ncm_scrape,
)


# ---------------------------------------------------------------------------
# Fixtures HTML minimos representativos del formato esperado
# ---------------------------------------------------------------------------
HTML_TARIFAR_OK = """
<html><body>
    <h1>Aparatos para inyeccion de plastico</h1>
    <table>
        <tr><td>Derecho de Importacion Extrazona</td><td>18%</td></tr>
        <tr><td>Intrazona</td><td>0%</td></tr>
        <tr><td>IVA General</td><td>21%</td></tr>
        <tr><td>Tasa Estadistica</td><td>3%</td></tr>
    </table>
    <p>Requiere intervencion SENASA para productos alimenticios.</p>
</body></html>
"""

HTML_ARANCEL_OK = """
<html><body>
    <div class="descripcion">Maquinas herramienta controladas por CNC</div>
    <p>AEC 14%</p>
    <p>IVA 21%</p>
</body></html>
"""

HTML_BROKEN = "<html><body><p>nd</p></body></html>"


# ---------------------------------------------------------------------------
# Helpers puros
# ---------------------------------------------------------------------------
def test_norm_ncm_strips_dots_and_letters():
    assert _norm_ncm("8544.42.00") == "85444200"
    assert _norm_ncm("8544-42-00") == "85444200"
    assert _norm_ncm("  8544420000abc  ") == "85444200"
    assert _norm_ncm(None) == ""


def test_ncm_with_dots_formats_8_digits():
    assert _ncm_with_dots("85444200") == "8544.42.00"
    # Menos de 8 → devuelve limpio sin formatear
    assert _ncm_with_dots("8544") == "8544"


def test_extract_alicuotas_parses_common_patterns():
    ali = _extract_alicuotas(HTML_TARIFAR_OK)
    assert ali.get("arancel_base") == 18.0
    assert ali.get("arancel_mercosur") == 0.0
    assert ali.get("iva") == 21.0
    assert ali.get("estadistica") == 3.0


def test_extract_alicuotas_empty_on_no_match():
    assert _extract_alicuotas("<html><body>sin datos</body></html>") == {}


def test_extract_descripcion_from_h1():
    assert _extract_descripcion(HTML_TARIFAR_OK).startswith("Aparatos para inyeccion")


def test_extract_descripcion_from_div_class():
    assert "Maquinas herramienta" in _extract_descripcion(HTML_ARANCEL_OK)


def test_extract_licencias_detects_senasa():
    licencias = _extract_licencias(HTML_TARIFAR_OK)
    codigos = {l["codigo"] for l in licencias}
    assert "SENASA" in codigos
    assert all(l["requerida"] is True for l in licencias)


def test_extract_licencias_empty_when_none_mentioned():
    assert _extract_licencias("<html><body>nada</body></html>") == []


# ---------------------------------------------------------------------------
# Flujo fetch_ncm_scrape con monkeypatch sobre _rate_limited_get
# ---------------------------------------------------------------------------
def _patch_get(monkeypatch, responses):
    """Parchea `_rate_limited_get` para devolver respuestas segun URL prefix.

    responses: lista de (matcher_substring, html | None).
    """
    def fake_get(url: str):
        for matcher, html in responses:
            if matcher in url:
                return html
        return None
    monkeypatch.setattr(ncm_scraper, "_rate_limited_get", fake_get)


def test_fetch_scrape_tarifar_hit(monkeypatch):
    _patch_get(monkeypatch, [("tarifar.com", HTML_TARIFAR_OK)])
    data = fetch_ncm_scrape("84771000")
    assert data is not None
    assert data["source"] == "scrape:tarifar"
    assert data["ncm"] == "84771000"
    assert data["alicuotas"]["arancel_base"] == 18.0
    # Al menos una licencia detectada
    assert any(l["codigo"] == "SENASA" for l in data["licencias"])


def test_fetch_scrape_fallback_to_arancel(monkeypatch):
    # Tarifar devuelve HTML no parseable; arancel responde ok
    _patch_get(monkeypatch, [
        ("tarifar.com", HTML_BROKEN),
        ("arancel.com.ar", HTML_ARANCEL_OK),
    ])
    data = fetch_ncm_scrape("84771000")
    assert data is not None
    assert data["source"] == "scrape:arancel"
    assert "Maquinas herramienta" in data["descripcion"]


def test_fetch_scrape_returns_none_when_all_fail(monkeypatch):
    _patch_get(monkeypatch, [
        ("tarifar.com", HTML_BROKEN),
        ("arancel.com.ar", HTML_BROKEN),
    ])
    assert fetch_ncm_scrape("84771000") is None


def test_fetch_scrape_returns_none_when_network_fails(monkeypatch):
    # Simulamos red caida en ambas fuentes
    monkeypatch.setattr(ncm_scraper, "_rate_limited_get", lambda _url: None)
    assert fetch_ncm_scrape("84771000") is None


def test_fetch_scrape_rejects_short_ncm(monkeypatch):
    monkeypatch.setattr(ncm_scraper, "_rate_limited_get", lambda _url: HTML_TARIFAR_OK)
    assert fetch_ncm_scrape("123") is None


# ---------------------------------------------------------------------------
# Connector modes (fake | scrape | api)
# ---------------------------------------------------------------------------
def test_vuce_mode_fake(monkeypatch):
    monkeypatch.setenv("VUCE_MODE", "fake")
    monkeypatch.delenv("VUCE_FAKE_MODE", raising=False)
    from proyecto_maria.core.vuce_connector import VuceConfig, VuceClient
    cfg = VuceConfig()
    assert cfg.mode == "fake"
    client = VuceClient(cfg)
    data = client._request("ncm/84771000")
    # El fake siempre responde (fuente marcada con "fake")
    assert "fuente" in data or data  # defensivo


def test_vuce_mode_scrape_falls_back_to_fake_on_empty(monkeypatch):
    monkeypatch.setenv("VUCE_MODE", "scrape")
    monkeypatch.setattr(
        "proyecto_maria.core.ncm_scraper.fetch_ncm_scrape",
        lambda _ncm: None,
    )
    from proyecto_maria.core.vuce_connector import VuceConfig, VuceClient
    cfg = VuceConfig()
    assert cfg.mode == "scrape"
    client = VuceClient(cfg)
    data = client._request("ncm/84771000")
    # Debe caer al fake y devolver algo (no romper UI)
    assert data is not None


def test_vuce_mode_api_without_key_raises(monkeypatch):
    monkeypatch.setenv("VUCE_MODE", "api")
    monkeypatch.delenv("VUCE_API_KEY", raising=False)
    from proyecto_maria.core.vuce_connector import VuceConfig, VuceClient
    cfg = VuceConfig()
    assert cfg.mode == "api"
    client = VuceClient(cfg)
    with pytest.raises(ValueError, match="VUCE_API_KEY"):
        client._request("ncm/84771000")


def test_vuce_fake_mode_legacy_flag_still_works(monkeypatch):
    # Sin VUCE_MODE, se respeta VUCE_FAKE_MODE=true
    monkeypatch.delenv("VUCE_MODE", raising=False)
    monkeypatch.setenv("VUCE_FAKE_MODE", "true")
    from proyecto_maria.core.vuce_connector import VuceConfig
    cfg = VuceConfig()
    assert cfg.mode == "fake"
    assert cfg.fake_mode is True
