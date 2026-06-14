import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

NEWS_MOCK = {
    "ok": True,
    "items": [
        {"titulo": "Novedad A", "link": "https://example.com/a", "imagen": "https://example.com/a.jpg"},
    ],
    "fuente": "https://example.com/feed.xml",
    "fuente_web": "https://example.com/novedades",
}


def test_arca_novedades_endpoint_returns_news(client: TestClient):
    """GET /api/arca/novedades devuelve novedades formateadas."""
    with patch("proyecto_maria.core.arca_news.fetch_arca_novedades", new_callable=AsyncMock) as m:
        m.return_value = NEWS_MOCK
        r = client.get("/api/arca/novedades")
        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert len(data["items"]) == 1
        assert data["items"][0]["titulo"] == "Novedad A"


def test_arca_novedades_endpoint_public_no_auth(client: TestClient):
    """El endpoint de novedades debe ser público (no require auth)."""
    with patch("proyecto_maria.core.arca_news.fetch_arca_novedades", new_callable=AsyncMock) as m:
        m.return_value = {**NEWS_MOCK, "items": []}
        r = client.get("/api/arca/novedades")
        assert r.status_code == 200
        assert r.json()["ok"] is True


def test_arca_news_parser_extracts_items():
    """El parser XML de arca_news extrae titulo/link/imagen correctamente."""
    from proyecto_maria.core.arca_news import _parse_items

    xml = """<?xml version="1.0" encoding="utf-8"?>
    <banners>
        <item><titulo><![CDATA[Prueba 1]]></titulo><link>https://a</link><imagen>https://img/a.jpg</imagen></item>
        <item><titulo>Prueba 2</titulo><link>https://b</link></item>
    </banners>
    """
    items = _parse_items(xml)
    assert len(items) == 2
    assert items[0]["titulo"] == "Prueba 1"
    assert items[0]["imagen"] == "https://img/a.jpg"
    assert items[1]["titulo"] == "Prueba 2"


def test_arca_news_parser_handles_bad_xml():
    """El parser no revienta con XML inválido."""
    from proyecto_maria.core.arca_news import _parse_items
    assert _parse_items("no soy xml") == []
