"""WSAA client con simulación avanzada para demo.

El cliente real interactuará con el Web Service de Autenticación y Autorización (WSAA) de AFIP.
Esta versión simula respuestas realistas para demostración.
"""

from __future__ import annotations

import time
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .config import AFIPSettings


@dataclass
class WSAAResponse:
    token: str
    sign: str
    expiration: str
    service: str = "ws_sr_padron_a5"
    source: str = "wsaa_fake"


class WSAAClient:
    """Cliente WSAA con simulación avanzada para demo."""

    def __init__(self, settings: AFIPSettings | None = None) -> None:
        self.settings = settings or AFIPSettings.from_env()
        self._token_cache = {}
        self._request_count = 0

    def authenticate(self, service: str = "ws_sr_padron_a5") -> WSAAResponse:
        """Autenticación simulada con AFIP WSAA."""
        
        # Simular latencia de red realista
        time.sleep(random.uniform(0.1, 0.3))
        self._request_count += 1
        
        # Cache simple por servicio
        cache_key = f"{service}_{self.settings.afip_service or 'default'}"
        if cache_key in self._token_cache:
            cached = self._token_cache[cache_key]
            if datetime.now() < cached["expires_dt"]:
                return cached["response"]
        
        # Generar token simulado realista
        expires_dt = datetime.now() + timedelta(hours=12)
        token_response = WSAAResponse(
            token=f"afip_token_{service}_{int(time.time())}_{random.randint(1000, 9999)}",
            sign=f"afip_sign_{random.randint(100000, 999999)}",
            expiration=expires_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            service=service
        )
        
        # Cachear por 11 horas
        self._token_cache[cache_key] = {
            "response": token_response,
            "expires_dt": expires_dt
        }
        
        return token_response

    def get_padron_data(self, cuit: str) -> Dict[str, Any]:
        """Consulta datos del padrón de contribuyentes AFIP."""
        time.sleep(random.uniform(0.2, 0.5))
        
        # Base de datos simulada de contribuyentes
        fake_padron = {
            "20123456789": {
                "cuit": "20-12345678-9",
                "razon_social": "IMPORTADORA DEMO S.A.",
                "estado": "ACTIVO",
                "actividades": [
                    {"codigo": "620200", "descripcion": "Servicios de consultoria en informatica"},
                    {"codigo": "511000", "descripcion": "Comercio al por mayor de productos agricolas"}
                ],
                "impuestos": ["IVA", "GANANCIAS", "AUTONOMOS"],
                "categoria_iva": "RESPONSABLE_INSCRIPTO",
                "domicilio": {
                    "direccion": "AV. CORRIENTES 1234 PISO 5",
                    "localidad": "CABA",
                    "provincia": "CIUDAD AUTONOMA DE BUENOS AIRES",
                    "codigo_postal": "1043"
                },
                "ultimo_update": "2024-09-25",
                "email": "demo@importadora.com.ar",
                "telefono": "011-4000-1234"
            },
            "27345678901": {
                "cuit": "27-34567890-1", 
                "razon_social": "RODRIGUEZ MARIA ELENA",
                "estado": "ACTIVO",
                "actividades": [
                    {"codigo": "471110", "descripcion": "Venta al por menor en hipermercados"}
                ],
                "impuestos": ["IVA", "GANANCIAS"],
                "categoria_iva": "RESPONSABLE_INSCRIPTO", 
                "domicilio": {
                    "direccion": "SANTA FE 5678",
                    "localidad": "ROSARIO",
                    "provincia": "SANTA FE", 
                    "codigo_postal": "2000"
                },
                "ultimo_update": "2024-09-20",
                "email": "mrodriguez@email.com",
                "telefono": "0341-555-6789"
            },
            "30567890123": {
                "cuit": "30-56789012-3",
                "razon_social": "EXPORTADORA TECNOLOGIA S.R.L.", 
                "estado": "ACTIVO",
                "actividades": [
                    {"codigo": "464200", "descripcion": "Venta al por mayor de productos textiles"},
                    {"codigo": "620100", "descripcion": "Programacion informatica"}
                ],
                "impuestos": ["IVA", "GANANCIAS"],
                "categoria_iva": "RESPONSABLE_INSCRIPTO",
                "domicilio": {
                    "direccion": "TUCUMAN 890",
                    "localidad": "CORDOBA",
                    "provincia": "CORDOBA",
                    "codigo_postal": "5000"
                },
                "ultimo_update": "2024-09-23",
                "email": "info@exportecnologia.com.ar", 
                "telefono": "0351-444-5555"
            }
        }
        
        # Limpiar CUIT (quitar guiones)
        clean_cuit = cuit.replace("-", "")
        
        if clean_cuit in fake_padron:
            return {
                "success": True,
                "data": fake_padron[clean_cuit],
                "source": "afip_padron_fake",
                "consulta_timestamp": datetime.now().isoformat()
            }
        else:
            # Generar datos simulados para CUITs no conocidos
            return {
                "success": True,
                "data": {
                    "cuit": cuit,
                    "razon_social": f"CONTRIBUYENTE DEMO {clean_cuit[-4:]} S.A.",
                    "estado": "ACTIVO",
                    "actividades": [
                        {"codigo": "999999", "descripcion": "Actividad comercial general"}
                    ],
                    "impuestos": ["IVA"],
                    "categoria_iva": "RESPONSABLE_INSCRIPTO",
                    "domicilio": {
                        "direccion": f"DIRECCION DEMO {random.randint(100, 9999)}",
                        "localidad": "CIUDAD DEMO",
                        "provincia": "PROVINCIA DEMO",
                        "codigo_postal": f"{random.randint(1000, 9999)}"
                    },
                    "ultimo_update": datetime.now().strftime("%Y-%m-%d"),
                    "email": f"demo{clean_cuit[-4:]}@empresa.com.ar",
                    "telefono": f"011-{random.randint(4000, 4999)}-{random.randint(1000, 9999)}"
                },
                "source": "afip_padron_fake",
                "consulta_timestamp": datetime.now().isoformat()
            }

    def get_tipo_cambio(self, moneda: str = "USD") -> Dict[str, Any]:
        """Obtiene tipo de cambio oficial de AFIP/BCRA."""
        time.sleep(random.uniform(0.1, 0.2))
        
        # Simulación de tipos de cambio con variación realista
        base_rates = {
            "USD": {"base_compra": 365.50, "base_venta": 385.50},
            "EUR": {"base_compra": 398.20, "base_venta": 418.20}, 
            "BRL": {"base_compra": 65.30, "base_venta": 68.30},
            "UYU": {"base_compra": 8.95, "base_venta": 9.25},
            "CLP": {"base_compra": 0.38, "base_venta": 0.40}
        }
        
        if moneda in base_rates:
            # Agregar variación pequeña para simular fluctuación
            variation = random.uniform(-0.02, 0.02)  # ±2%
            base_data = base_rates[moneda]
            compra = base_data["base_compra"] * (1 + variation)
            venta = base_data["base_venta"] * (1 + variation)
        else:
            compra = venta = 1.0
        
        return {
            "success": True,
            "moneda": moneda,
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M:%S"),
            "tipo_cambio": {
                "compra": round(compra, 2),
                "venta": round(venta, 2)
            },
            "fuente": "BCRA",
            "source": "afip_tc_fake",
            "consulta_timestamp": datetime.now().isoformat()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del cliente AFIP para monitoreo."""
        return {
            "requests_realizadas": self._request_count,
            "tokens_cacheados": len(self._token_cache),
            "ultimo_acceso": datetime.now().isoformat(),
            "configurado": self.settings.is_configured() if self.settings else False,
            "servicio": self.settings.afip_service if self.settings else "default"
        }

    def raw_login(self) -> Any:
        """Placeholder para llamada de login de bajo nivel."""
        raise NotImplementedError("WSAA raw_login pendiente implementación real")