"""Cliente Tarifar con simulación avanzada para cálculos arancelarios.

Soporta dos modos:
- FAKE: Simula cálculos (para desarrollo sin API key)
- REAL: Consulta API de Tarifar (requiere API_KEY)

Simula un sistema completo de cálculo de aranceles, impuestos y costos de importación
basado en NCM, origen, valor FOB y peso.
"""

import os
import time
import random
import requests
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from .vuce_connector import get_ncm_data, _resolve_mode


@dataclass
class TarifarConfig:
    """Configuracion del connector Tarifar.

    Modos (`mode`):
    - `fake`:   calculo simulado local (default hoy).
    - `scrape`: hoy identico a `fake` (Tarifar no expone scraping publico
      distinto del de NCM que ya hace `ncm_scraper`). Reservado para futuro.
    - `api`:    API pago de Tarifar (requiere `TARIFAR_API_KEY`).

    El flag legacy `TARIFAR_FAKE_MODE` sigue vigente si `TARIFAR_MODE` no
    esta seteado.
    """
    base_url: str = os.getenv("TARIFAR_BASE_URL", "https://api.tarifar.com")
    api_key: Optional[str] = os.getenv("TARIFAR_API_KEY")
    timeout: int = int(os.getenv("TARIFAR_TIMEOUT", "10"))
    mode: str = field(default_factory=lambda: _resolve_mode("TARIFAR_MODE", "TARIFAR_FAKE_MODE"))

    @property
    def fake_mode(self) -> bool:
        # Compat: hoy `scrape` tampoco implementa API real, asi que se comporta
        # como fake a nivel de calculos de aranceles. La parte NCM la hace
        # el scraper a traves de `vuce_connector`.
        return self.mode in ("fake", "scrape")


@dataclass
class TarifarItem:
    ncm: str
    descripcion: str
    origen: str
    cantidad: float
    valor_unitario_fob: float
    peso_unitario: float
    

@dataclass
class TarifarResult:
    item: TarifarItem
    valor_total_fob: float
    peso_total: float
    aranceles: Dict[str, float]
    impuestos: Dict[str, float]
    tasas: Dict[str, float]
    costo_total: float
    detalle_calculo: Dict[str, Any]
    warnings: List[str]


def _aggregate_sources(item_sources: List[str]) -> str:
    """Combina las fuentes NCM de cada item en una sola etiqueta.

    Reglas:
    - Si todos los items tienen datos de scrape → devuelve la mas frecuente
      (`scrape:tarifar`, `scrape:arancel`, etc.).
    - Si al menos uno vino por API oficial y el resto scrape → `api:vuce`
      (la parte oficial manda para comunicar confianza).
    - Si alguno es fake o vacio → degrada a `tarifar_scrape_partial` para que
      la UI muestre "Mercado" pero con caveat.
    - Sin items → `tarifar_fake`.
    """
    if not item_sources:
        return "tarifar_fake"
    has_fake = any(("fake" in s) or (not s) for s in item_sources)
    has_api = any(("api" in s) or ("oficial" in s) for s in item_sources)
    has_scrape = any("scrape" in s for s in item_sources)
    if has_api and not has_fake:
        return "api:vuce"
    if has_scrape and not has_fake:
        # Devolver el scrape mas frecuente para preservar info del origen
        from collections import Counter
        c = Counter(s for s in item_sources if "scrape" in s)
        return c.most_common(1)[0][0]
    if has_scrape and has_fake:
        return "tarifar_scrape_partial"
    return "tarifar_fake"


def _safe_float(value, default, min_val=0.0, max_val=100.0):
    """
    Convierte a float con validación de rango segura.

    Args:
        value: Valor a convertir (puede ser str, int, float, None, etc.)
        default: Valor por defecto si conversión falla
        min_val: Valor mínimo permitido
        max_val: Valor máximo permitido

    Returns:
        float: Valor convertido y validado dentro del rango [min_val, max_val]

    Examples:
        >>> _safe_float("20.5", 15.0, 0.0, 50.0)
        20.5
        >>> _safe_float("-5", 15.0, 0.0, 50.0)
        0.0
        >>> _safe_float("999", 15.0, 0.0, 50.0)
        50.0
        >>> _safe_float("abc", 15.0, 0.0, 50.0)
        15.0
    """
    try:
        val = float(value)
        return max(min_val, min(max_val, val))
    except (ValueError, TypeError):
        return default


class TarifarClient:
    """Cliente para cálculos arancelarios automatizados."""

    def __init__(self, config: TarifarConfig = None):
        self.config = config or TarifarConfig()
        self._cache = {}
        self._request_count = 0

    def calcular_aranceles(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula aranceles e impuestos para una lista de items.

        Modos:
        - FAKE (default): Simula cálculos localmente
        - REAL: Consulta API de Tarifar con API key
        """
        if self.config.fake_mode:
            return self._calcular_aranceles_fake(items)
        else:
            return self._calcular_aranceles_real(items)

    def _calcular_aranceles_fake(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculo local de aranceles e impuestos.

        El calculo en si corre siempre local (el scraper publico no expone una
        calculadora). Pero las alicuotas provienen de `get_ncm_data` que, en
        `VUCE_MODE=scrape`, devuelve datos reales. En ese caso etiquetamos la
        respuesta como `scrape_based` para que la UI muestre "Mercado" y no
        "Muestra".
        """
        time.sleep(random.uniform(0.3, 0.8))  # Simular latencia al usuario
        self._request_count += 1

        results = []
        totales = {
            "valor_fob_total": 0.0,
            "peso_total": 0.0,
            "aranceles_total": 0.0,
            "impuestos_total": 0.0,
            "tasas_total": 0.0,
            "costo_total": 0.0
        }

        item_sources: List[str] = []
        for item_data in items:
            result = self._calcular_item_individual(item_data)
            results.append(result)

            totales["valor_fob_total"] += result.valor_total_fob
            totales["peso_total"] += result.peso_total
            totales["aranceles_total"] += sum(result.aranceles.values())
            totales["impuestos_total"] += sum(result.impuestos.values())
            totales["tasas_total"] += sum(result.tasas.values())
            totales["costo_total"] += result.costo_total

            # Registrar la fuente real del NCM que uso el calculo
            ncm_src = (result.detalle_calculo.get("ncm_info") or {}).get("source") or ""
            if ncm_src:
                item_sources.append(ncm_src)

        avg_arancel_rate = (totales["aranceles_total"] / totales["valor_fob_total"] * 100) if totales["valor_fob_total"] > 0 else 0

        # Determinar la fuente agregada: si todos los items vinieron de scrape o
        # api, exponemos el mejor de ellos; si alguno fue fake, degradamos.
        aggregate_source = _aggregate_sources(item_sources)

        return {
            "success": True,
            "items": [self._result_to_dict(r) for r in results],
            "totales": totales,
            "estadisticas": {
                "items_procesados": len(items),
                "tasa_arancelaria_promedio": round(avg_arancel_rate, 2),
                "valor_cif_estimado": totales["costo_total"],
                "ahorro_mercosur": self._calcular_ahorro_mercosur(results)
            },
            "metadata": {
                "fecha_calculo": datetime.now().isoformat(),
                "tipo_cambio_usd": 385.50,  # Simulado (pendiente hookear a /api/financials)
                "source": aggregate_source,
                "version_arancel": "2024.09"
            }
        }

    def _calcular_aranceles_real(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Modo REAL: Consulta API de Tarifar.

        NOTA: Requiere API key y conocimiento de endpoints reales.
        Este es un template que deberá actualizarse cuando obtengamos
        la documentación oficial de Tarifar.
        """
        if not self.config.api_key:
            raise ValueError("TARIFAR_API_KEY requerida para modo real. Configurar en .env o usar fake_mode=true")

        self._request_count += 1

        try:
            # PLACEHOLDER: Endpoints reales de Tarifar (actualizar con documentación)
            url = f"{self.config.base_url}/v1/calcular"  # Endpoint estimado

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }

            # Transformar items al formato esperado por Tarifar API
            payload = {
                "items": [
                    {
                        "ncm": item.get("pieza", item.get("ncm")),
                        "descripcion": item.get("descripcion", ""),
                        "origen": item.get("origen", "CN"),
                        "cantidad": item.get("cantidad", 1),
                        "valor_fob_unitario": item.get("valor_unitario", 0),
                        "peso_kg_unitario": item.get("peso_unitario", 1)
                    }
                    for item in items
                ]
            }

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.config.timeout
            )

            response.raise_for_status()
            data = response.json()

            # Agregar metadata de fuente real
            data["metadata"] = data.get("metadata", {})
            data["metadata"]["source"] = "tarifar_api_real"
            data["metadata"]["fecha_calculo"] = datetime.now().isoformat()

            return data

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ValueError("API Key de Tarifar inválida o expirada")
            elif e.response.status_code == 429:
                raise ValueError("Límite de requests de Tarifar excedido")
            else:
                raise ValueError(f"Error API Tarifar: {e.response.status_code} - {e.response.text}")

        except requests.exceptions.Timeout:
            raise ValueError("Timeout consultando API de Tarifar")

        except Exception as e:
            raise ValueError(f"Error inesperado llamando Tarifar API: {str(e)}")

    def _calcular_item_individual(self, item_data: Dict[str, Any]) -> TarifarResult:
        """Calcula aranceles para un item individual."""
        
        # Crear item
        item = TarifarItem(
            ncm=item_data.get("pieza", item_data.get("ncm", "")),
            descripcion=item_data.get("descripcion", ""),
            origen=item_data.get("origen", "CN"),
            cantidad=float(item_data.get("cantidad", 1)),
            valor_unitario_fob=float(item_data.get("valor_unitario", item_data.get("fob_unitario", 0))),
            peso_unitario=float(item_data.get("peso_unitario", 1))
        )
        
        # Obtener datos de NCM desde VUCE
        ncm_data = get_ncm_data(item.ncm)
        
        # Calcular valores base
        valor_total_fob = item.cantidad * item.valor_unitario_fob
        peso_total = item.cantidad * item.peso_unitario
        
        # Determinar si aplica preferencia arancelaria
        es_mercosur = item.origen.upper() in ["BR", "PY", "UY", "BRASIL", "PARAGUAY", "URUGUAY"]
        
        # Calcular aranceles
        arancel_base = ncm_data.get("alicuotas", {}).get("arancel_base", 10.0)
        arancel_aplicable = 0.0 if es_mercosur else arancel_base
        
        aranceles = {
            "arancel_extrazona": arancel_aplicable / 100 * valor_total_fob,
            "derecho_exportacion": ncm_data.get("alicuotas", {}).get("derechos_exportacion", 0.0) / 100 * valor_total_fob
        }
        
        # Base imponible para IVA (FOB + Aranceles + Flete + Seguro)
        # Extraer y validar parámetros de flete/seguro (con defaults y límites)
        flete_pct = _safe_float(item_data.get("flete_pct"), default=15.0, min_val=0.0, max_val=50.0)
        seguro_pct = _safe_float(item_data.get("seguro_pct"), default=0.5, min_val=0.0, max_val=10.0)

        flete_estimado = valor_total_fob * (flete_pct / 100)
        seguro_estimado = valor_total_fob * (seguro_pct / 100)
        base_iva = valor_total_fob + sum(aranceles.values()) + flete_estimado + seguro_estimado
        
        # Calcular impuestos
        impuestos = {
            "iva": base_iva * (ncm_data.get("alicuotas", {}).get("iva", 21.0) / 100),
            "ingresos_brutos": base_iva * 0.025,  # 2.5% estimado
            "ganancias": base_iva * 0.06 if valor_total_fob > 1000 else 0.0  # 6% si > USD 1000
        }
        
        # Calcular tasas
        tasas = {
            "estadistica": valor_total_fob * (ncm_data.get("alicuotas", {}).get("estadistica", 3.0) / 100),
            "inal": 15.0 if any("INAL" in lic.get("codigo", "") for lic in ncm_data.get("licencias", [])) else 0.0,
            "senasa": 25.0 if any("SENASA" in lic.get("codigo", "") for lic in ncm_data.get("licencias", [])) else 0.0,
            "anmat": 50.0 if any("ANMAT" in lic.get("codigo", "") for lic in ncm_data.get("licencias", [])) else 0.0
        }
        
        # Costo total
        costo_total = valor_total_fob + sum(aranceles.values()) + sum(impuestos.values()) + sum(tasas.values()) + flete_estimado + seguro_estimado
        
        # Generar warnings
        warnings = []
        if not item.ncm:
            warnings.append("NCM no especificado")
        if valor_total_fob == 0:
            warnings.append("Valor FOB es cero")
        if item.origen.upper() not in ["AR", "BR", "PY", "UY", "CN", "US", "DE", "IT", "ES"]:
            warnings.append(f"País de origen '{item.origen}' no reconocido")
        if len(ncm_data.get("licencias", [])) > 0:
            licencias = [lic.get("codigo") for lic in ncm_data.get("licencias", [])]
            warnings.append(f"Requiere licencias: {', '.join(licencias)}")
        
        # Detalle del cálculo
        detalle = {
            "base_calculo": {
                "valor_fob": valor_total_fob,
                "peso_kg": peso_total,
                "flete_estimado": flete_estimado,
                "seguro_estimado": seguro_estimado,
                "base_iva": base_iva
            },
            "tasas_aplicadas": {
                "arancel_base_pct": arancel_base,
                "arancel_aplicado_pct": arancel_aplicable,
                "iva_pct": ncm_data.get("alicuotas", {}).get("iva", 21.0),
                "estadistica_pct": ncm_data.get("alicuotas", {}).get("estadistica", 3.0)
            },
            "preferencias": {
                "es_mercosur": es_mercosur,
                "ahorro_arancel": (arancel_base - arancel_aplicable) / 100 * valor_total_fob if es_mercosur else 0.0
            },
            "ncm_info": {
                "descripcion_oficial": ncm_data.get("descripcion", ""),
                "regimen_especial": ncm_data.get("regimen_especial", "General"),
                "unidad_medida": ncm_data.get("unidad_medida", "KG"),
                "source": (
                    ncm_data.get("source")
                    or ncm_data.get("fuente")
                    or ""
                ),
            }
        }
        
        return TarifarResult(
            item=item,
            valor_total_fob=valor_total_fob,
            peso_total=peso_total,
            aranceles=aranceles,
            impuestos=impuestos,
            tasas=tasas,
            costo_total=costo_total,
            detalle_calculo=detalle,
            warnings=warnings
        )
    
    def _calcular_ahorro_mercosur(self, results: List[TarifarResult]) -> Dict[str, float]:
        """Calcula el ahorro por preferencias arancelarias MERCOSUR."""
        ahorro_total = 0.0
        items_con_preferencia = 0
        
        for result in results:
            ahorro_item = result.detalle_calculo["preferencias"]["ahorro_arancel"]
            if ahorro_item > 0:
                ahorro_total += ahorro_item
                items_con_preferencia += 1
        
        return {
            "ahorro_total_usd": round(ahorro_total, 2),
            "items_con_preferencia": items_con_preferencia,
            "porcentaje_items": round((items_con_preferencia / len(results) * 100) if results else 0, 1)
        }
    
    def _result_to_dict(self, result: TarifarResult) -> Dict[str, Any]:
        """Convierte TarifarResult a diccionario."""
        return {
            "item": {
                "ncm": result.item.ncm,
                "descripcion": result.item.descripcion,
                "origen": result.item.origen,
                "cantidad": result.item.cantidad,
                "valor_unitario_fob": result.item.valor_unitario_fob,
                "peso_unitario": result.item.peso_unitario
            },
            "calculo": {
                "valor_total_fob": round(result.valor_total_fob, 2),
                "peso_total": round(result.peso_total, 2),
                "aranceles": {k: round(v, 2) for k, v in result.aranceles.items()},
                "impuestos": {k: round(v, 2) for k, v in result.impuestos.items()},
                "tasas": {k: round(v, 2) for k, v in result.tasas.items()},
                "costo_total": round(result.costo_total, 2)
            },
            "detalle": result.detalle_calculo,
            "warnings": result.warnings
        }
    
    def get_simulacion_origen(self, ncm: str, valor_fob: float, cantidad: float = 1.0) -> Dict[str, Any]:
        """Simula costos para diferentes países de origen."""
        time.sleep(random.uniform(0.2, 0.4))
        
        origenes = ["CN", "US", "DE", "BR", "PY", "UY", "IT", "ES", "JP", "KR"]
        simulaciones = {}
        
        for origen in origenes:
            item_data = {
                "pieza": ncm,
                "descripcion": f"Producto simulado {ncm}",
                "origen": origen,
                "cantidad": cantidad,
                "valor_unitario": valor_fob,
                "peso_unitario": 1.0
            }
            
            result = self._calcular_item_individual(item_data)
            simulaciones[origen] = {
                "pais": self._get_pais_name(origen),
                "costo_total": round(result.costo_total, 2),
                "aranceles": round(sum(result.aranceles.values()), 2),
                "impuestos": round(sum(result.impuestos.values()), 2),
                "es_mercosur": result.detalle_calculo["preferencias"]["es_mercosur"],
                "ranking": 0  # Se calculará después
            }
        
        # Ordenar por costo total y asignar ranking
        sorted_origins = sorted(simulaciones.items(), key=lambda x: x[1]["costo_total"])
        for i, (origen, data) in enumerate(sorted_origins):
            simulaciones[origen]["ranking"] = i + 1
        
        mejor_opcion = sorted_origins[0]
        
        return {
            "success": True,
            "ncm": ncm,
            "valor_fob": valor_fob,
            "cantidad": cantidad,
            "simulaciones": simulaciones,
            "recomendacion": {
                "mejor_origen": mejor_opcion[0],
                "pais": mejor_opcion[1]["pais"],
                "costo_total": mejor_opcion[1]["costo_total"],
                "ahorro_vs_china": round(simulaciones["CN"]["costo_total"] - mejor_opcion[1]["costo_total"], 2)
            },
            "metadata": {
                "fecha_simulacion": datetime.now().isoformat(),
                "source": "tarifar_fake"
            }
        }
    
    def _get_pais_name(self, codigo: str) -> str:
        """Convierte código de país a nombre."""
        paises = {
            "CN": "China",
            "US": "Estados Unidos", 
            "DE": "Alemania",
            "BR": "Brasil",
            "PY": "Paraguay",
            "UY": "Uruguay",
            "IT": "Italia",
            "ES": "España",
            "JP": "Japón",
            "KR": "Corea del Sur",
            "AR": "Argentina"
        }
        return paises.get(codigo.upper(), codigo)
    
    def get_stats(self) -> Dict[str, Any]:
        """Estadísticas del cliente Tarifar."""
        return {
            "calculos_realizados": self._request_count,
            "items_en_cache": len(self._cache),
            "ultimo_acceso": datetime.now().isoformat(),
            "modo_fake": self.config.fake_mode
        }


# Cliente global
CLIENT = TarifarClient()

def calcular_aranceles(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Función de conveniencia para cálculos arancelarios."""
    return CLIENT.calcular_aranceles(items)

def simular_origenes(ncm: str, valor_fob: float, cantidad: float = 1.0) -> Dict[str, Any]:
    """Función de conveniencia para simulación de orígenes."""
    return CLIENT.get_simulacion_origen(ncm, valor_fob, cantidad)

