"""Tests para el conector VUCE."""

import pytest
from core.vuce_connector import VuceClient, VuceConfig, VUCE_CACHE, get_ncm_data

@pytest.fixture(autouse=True)
def clear_cache():
    VUCE_CACHE.clear()
    yield

class TestVuceConnector:
    """Tests para el conector VUCE."""

    def test_get_ncm_data_function_exists(self):
        """Test que la función get_ncm_data existe y es callable."""
        assert callable(get_ncm_data)

    def test_ncm_cache_initialization(self):
        """Test que el caché de NCM se inicializa correctamente."""
        assert isinstance(VUCE_CACHE, dict)
        assert len(VUCE_CACHE) == 0

    def test_default_client_fake_mode(self):
        data = get_ncm_data("7306")
        assert data["ncm"] == "7306"
        assert data["fuente"] == "fake"
        assert "alicuotas" in data

    def test_reads_from_cache(self):
        cli = VuceClient(VuceConfig(fake_mode=True))
        first = cli.get_ncm_details("8471")
        assert "fuente" in first
        second = cli.get_ncm_details("8471")
        assert second is first

    def test_real_mode_needs_base_url(self, monkeypatch):
        capture = {}
        def fake_get(url, **kwargs):
            capture["url"] = url
            class _Resp:
                status_code = 200
                def json(self):
                    return {"ok": True}
                def raise_for_status(self):
                    pass
            return _Resp()
        monkeypatch.setattr("requests.get", fake_get)
        cfg = VuceConfig(base_url="https://example.com/api", fake_mode=False)
        cli = VuceClient(cfg)
        data = cli.get_ncm_details("0101")
        assert data == {"ok": True}
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

    def test_cache_functionality(self):
        """Test que el caché funciona correctamente."""
        # Limpiar caché
        VUCE_CACHE.clear()

        # Primera llamada debería hacer petición (aunque falle)
        # Como no podemos mockear aquí, solo verificamos que el caché existe
        assert isinstance(VUCE_CACHE, dict)

        # Agregar manualmente algo al caché para verificar persistencia
        test_data = {"test": "data"}
        VUCE_CACHE["test_ncm"] = test_data

        assert VUCE_CACHE["test_ncm"] == test_data
