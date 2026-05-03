"""Tests para el conector VUCE."""

import pytest
from proyecto_maria.core.vuce_connector import VuceClient, VuceConfig, VUCE_CACHE, get_ncm_data

@pytest.fixture(autouse=True)
def clear_cache():
    VUCE_CACHE.clear()
    yield

class TestVuceConnector:
    def test_default_client_fake_mode(self):
        data = get_ncm_data("7306")
        assert data["ncm"] == "7306"
        assert data["fuente"] == "fake"
        assert "alicuotas" in data

    def test_reads_from_cache(self):
        cli = VuceClient(VuceConfig(fake_mode=True))
        first = cli.get_ncm_details("8471")
        second = cli.get_ncm_details("8471")
        assert first is second

    def test_real_mode_success(self, monkeypatch):
        capture = {}
        def fake_get(url, **kwargs):
            capture["url"] = url
            class _Resp:
                def __init__(self):
                    self.status_code = 200
                def json(self):
                    return {"ncm": "0101", "fuente": "vuce"}
                def raise_for_status(self):
                    pass
            return _Resp()
        monkeypatch.setattr("requests.get", fake_get)
        cfg = VuceConfig(base_url="https://example.com/api", fake_mode=False)
        cli = VuceClient(cfg)
        data = cli.get_ncm_details("0101")
        assert data["ncm"] == "0101"
        assert capture["url"].endswith("ncm/0101")

    def test_real_mode_error(self, monkeypatch):
        class Boom(Exception):
            pass
        def fake_get(*args, **kwargs):
            raise Boom()
        monkeypatch.setattr("requests.get", fake_get)
        cfg = VuceConfig(base_url="https://example.com", fake_mode=False)
        cli = VuceClient(cfg)
        with pytest.raises(Boom):
            cli.get_ncm_details("0202")
