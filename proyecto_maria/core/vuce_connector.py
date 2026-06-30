import os
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

import requests

class SourceUnavailableError(Exception):
    def __init__(self, ncm: str):
        self.ncm = ncm
        super().__init__(f"Fuente arancelaria no disponible para NCM {ncm}")

logger = logging.getLogger(__name__)

# Cache en memoria (proceso-local). El cache persistente vive en la tabla
# `ncm_cache` (ver `database/models.py`) y lo consulta `ncm_service`.
VUCE_CACHE: Dict[str, Any] = {}


def _resolve_mode(env_mode: str, env_fake: str) -> str:
    """Decide el modo efectivo de los connectors.

    Soporta retrocompatibilidad: si `VUCE_FAKE_MODE=true` (o vacio) y no hay
    `VUCE_MODE` explicito, quedamos en `fake`. Si hay `VUCE_MODE`, gana.
    Valores validos: `fake`, `scrape`, `api`.
    """
    mode = (os.getenv(env_mode, "") or "").strip().lower()
    if mode in ("fake", "scrape", "api"):
        return mode
    # Retrocompat: si no hay VUCE_MODE, usar FAKE flag
    fake_flag = (os.getenv(env_fake, "true") or "true").strip().lower()
    return "fake" if fake_flag == "true" else "scrape"


@dataclass
class VuceConfig:
    """Configuracion del connector VUCE.

    Modos (`mode`):
    - `fake`:   respuesta simulada (sin red). Default hasta tener credenciales.
    - `scrape`: datos reales via scraping publico (`core/ncm_scraper.py`).
    - `api`:    API oficial VUCE (requiere `VUCE_API_KEY`). Hoy: placeholder.

    El flag legacy `VUCE_FAKE_MODE` sigue funcionando si `VUCE_MODE` no esta
    seteado, para no romper despliegues viejos.
    """
    base_url: str = os.getenv("VUCE_BASE_URL", "https://sandbox.vuce.gob.ar/api")
    api_key: Optional[str] = os.getenv("VUCE_API_KEY")
    timeout: int = int(os.getenv("VUCE_TIMEOUT", "10"))
    mode: str = field(default_factory=lambda: _resolve_mode("VUCE_MODE", "VUCE_FAKE_MODE"))

    @property
    def fake_mode(self) -> bool:
        # Compat con codigo viejo que lee `config.fake_mode`
        return self.mode == "fake"


CONFIG = VuceConfig()


class VuceClient:
    def __init__(self, config: VuceConfig = CONFIG):
        self.config = config

    def _request(self, path: str, params: Optional[dict] = None) -> Dict[str, Any]:
        mode = self.config.mode
        is_production = os.getenv("ENVIRONMENT", "development") == "production"

        if mode == "fake":
            if is_production:
                logger.error("[vuce] Intento de usar modo fake en produccion abortado.")
                raise SourceUnavailableError(ncm=path.split("/")[-1])
            return self._fake_response(path, params)
        if mode == "scrape":
            data = self._scrape_response(path, params)
            if data:
                return data
            # Fallback a Error 503 en lugar de fake (Fisura C M&A)
            logger.warning("[vuce] scrape vacio, lanzando SourceUnavailableError para %s", path)
            raise SourceUnavailableError(ncm=path.split("/")[-1])
        # mode == "api"
        return self._real_request(path, params)

    def _scrape_response(self, path: str, params: Optional[dict]) -> Optional[Dict[str, Any]]:
        """Consulta fuentes publicas. Orden:
        1. VUCE CI (oficial, da codigo SIM completo) si `VUCE_CI_ENABLED=true`.
        2. tarifar.com / arancel.com.ar (scraper HTML existente, default hoy).
        """
        ncm = path.split("/")[-1]
        if os.getenv("VUCE_CI_ENABLED", "false").strip().lower() == "true":
            from .vuce_ci_client import fetch_ncm_completo  # import tardio para evitar ciclos
            try:
                data = fetch_ncm_completo(ncm)
                if data:
                    return data
            except Exception as err:
                logger.warning("[vuce] VUCE CI fallo, sigo con scraper HTML: %s", err)
        from .ncm_scraper import fetch_ncm_scrape  # import tardio para evitar ciclos
        return fetch_ncm_scrape(ncm)

    def _real_request(self, path: str, params: Optional[dict]) -> Dict[str, Any]:
        """Consulta a la API oficial VUCE. TODO: activar cuando llegue la key."""
        if not self.config.api_key:
            raise ValueError(
                "VUCE_API_KEY requerida para VUCE_MODE=api. "
                "Configurar en .env o usar VUCE_MODE=scrape|fake."
            )
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        resp = requests.get(url, headers=headers, params=params, timeout=self.config.timeout)
        resp.raise_for_status()
        data = resp.json()
        # Nos aseguramos de marcar la fuente aunque el backend no lo haga
        data.setdefault("fuente", "vuce_api_real")
        return data

    def _fake_response(self, path: str, params: Optional[dict]) -> Dict[str, Any]:
        ncm = path.split('/')[-1]
        
        # Base de datos simulada más realista
        fake_database = {
            "28320000": {
                "ncm": "28320000",
                "descripcion": "SULFATOS; ALUMBRES; PEROXOSULFATOS (PERSULFATOS)",
                "alicuotas": {
                    "arancel_base": 8.0,
                    "arancel_mercosur": 0.0,
                    "iva": 21.0,
                    "estadistica": 3.0,
                    "derechos_exportacion": 0.0
                },
                "licencias": [
                    {"codigo": "SENASA", "descripcion": "Servicio Nacional de Sanidad Animal", "requerida": True},
                    {"codigo": "ANMAT", "descripcion": "Administración Nacional de Medicamentos", "requerida": True}
                ],
                "regimen_especial": "Insumo Industrial",
                "unidad_medida": "KG",
                "origen_preferencial": ["Brasil", "Paraguay", "Uruguay"],
                "vigente": True,
                "fuente": "vuce_fake"
            },
            "39269099": {
                "ncm": "39269099", 
                "descripcion": "Las demás manufacturas de plástico y manufacturas de las demás materias",
                "alicuotas": {
                    "arancel_base": 16.0,
                    "arancel_mercosur": 0.0,
                    "iva": 21.0,
                    "estadistica": 3.0,
                    "derechos_exportacion": 0.0
                },
                "licencias": [],
                "regimen_especial": "General",
                "unidad_medida": "KG", 
                "origen_preferencial": ["Brasil", "Paraguay", "Uruguay"],
                "vigente": True,
                "fuente": "vuce_fake"
            },
            "84715000": {
                "ncm": "84715000",
                "descripcion": "Unidades de proceso digitales (CPU)",
                "alicuotas": {
                    "arancel_base": 0.0,
                    "arancel_mercosur": 0.0,
                    "iva": 21.0,
                    "estadistica": 3.0,
                    "derechos_exportacion": 0.0
                },
                "licencias": [
                    {"codigo": "ENACOM", "descripcion": "Ente Nacional de Comunicaciones", "requerida": True}
                ],
                "regimen_especial": "Informática y Telecomunicaciones",
                "unidad_medida": "U",
                "origen_preferencial": ["Brasil", "Paraguay", "Uruguay", "China"],
                "vigente": True,
                "fuente": "vuce_fake"
            }
        }
        
        # Si existe en la base simulada, usarla
        if ncm in fake_database:
            return fake_database[ncm]
        
        # Generar datos simulados basados en el NCM
        prefix = ncm[:2] if len(ncm) >= 2 else "00"
        
        # Mapeo de capítulos arancelarios comunes
        chapter_mapping = {
            "28": {"desc": "Productos químicos inorgánicos", "arancel": 8.0, "rest": [{"codigo": "SENASA", "descripcion": "Servicio Nacional de Sanidad Animal", "requerida": True}]},
            "39": {"desc": "Plástico y sus manufacturas", "arancel": 16.0, "rest": []},
            "84": {"desc": "Máquinas y aparatos mecánicos", "arancel": 14.0, "rest": [{"codigo": "INAL", "descripcion": "Instituto Nacional de Alimentos", "requerida": False}]},
            "85": {"desc": "Máquinas y material eléctrico", "arancel": 0.0, "rest": [{"codigo": "ENACOM", "descripcion": "Ente Nacional de Comunicaciones", "requerida": True}]},
            "73": {"desc": "Manufacturas de fundición, hierro o acero", "arancel": 12.0, "rest": []},
            "90": {"desc": "Instrumentos de óptica, fotografía, medida", "arancel": 0.0, "rest": [{"codigo": "ANMAT", "descripcion": "Administración Nacional de Medicamentos", "requerida": True}]},
        }
        
        chapter_info = chapter_mapping.get(prefix, {"desc": "Producto industrial", "arancel": 10.0, "rest": []})
        
        return {
            "ncm": ncm,
            "descripcion": f"{chapter_info['desc']} - NCM {ncm}",
            "alicuotas": {
                "arancel_base": chapter_info["arancel"],
                "arancel_mercosur": 0.0,
                "iva": 21.0,
                "estadistica": 3.0,
                "derechos_exportacion": 0.0
            },
            "licencias": chapter_info["rest"],
            "regimen_especial": "General",
            "unidad_medida": "KG",
            "origen_preferencial": ["Brasil", "Paraguay", "Uruguay"],
            "vigente": True,
            "fuente": "vuce_fake"
        }

    def get_ncm_details(self, ncm: str) -> Dict[str, Any]:
        if ncm in VUCE_CACHE:
            return VUCE_CACHE[ncm]
        data = self._request(f"ncm/{ncm}")
        VUCE_CACHE[ncm] = data
        return data

CLIENT = VuceClient()

def get_ncm_data(ncm: str) -> Dict[str, Any]:
    return CLIENT.get_ncm_details(ncm)

