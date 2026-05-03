"""
Calculator Router - Calculadora de Valor en Plaza
Endpoints para calcular costos de importación y tributos
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

from ..core.calculator import (
    calcular_valor_plaza,
    comparar_origenes,
    EJEMPLOS_CALCULO
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calculator", tags=["calculator"])


# ==================== MODELOS ====================

class CalculoRequest(BaseModel):
    """Request para calcular valor en plaza"""
    ncm: str = Field(..., description="Código NCM (6-8 dígitos)", example="84713010")
    origen: str = Field(..., description="País de origen (ISO2)", example="CN")
    fob_unitario: float = Field(..., gt=0, description="Valor FOB unitario en USD", example=500.0)
    cantidad: float = Field(default=1.0, gt=0, description="Cantidad de unidades", example=10)
    flete_percent: Optional[float] = Field(None, ge=0, le=1, description="% de flete (opcional)")
    seguro_percent: Optional[float] = Field(None, ge=0, le=1, description="% de seguro (opcional)")


class ComparacionRequest(BaseModel):
    """Request para comparar orígenes"""
    ncm: str = Field(..., example="84713010")
    fob_unitario: float = Field(..., gt=0, example=500.0)
    cantidad: float = Field(default=1.0, gt=0, example=10)
    origenes: Optional[List[str]] = Field(None, description="Lista de países a comparar", example=["CN", "BR", "US"])


# ==================== ENDPOINTS ====================

@router.post("/valor-plaza")
async def calcular_valor_plaza_endpoint(request: CalculoRequest):
    """
    Calcular valor en plaza de un producto importado

    Incluye todos los tributos:
    - Derechos de importación (según NCM)
    - IVA (21%)
    - Tasa estadística (3%)
    - Flete y seguro estimados

    **Ejemplo:**
    ```json
    {
      "ncm": "84713010",
      "origen": "CN",
      "fob_unitario": 500,
      "cantidad": 10
    }
    ```

    **Response incluye:**
    - Breakdown completo de costos
    - Valor final y unitario
    - Info de MERCOSUR (si aplica)
    """
    try:
        resultado = calcular_valor_plaza(
            ncm=request.ncm,
            origen=request.origen,
            fob_unitario=request.fob_unitario,
            cantidad=request.cantidad,
            flete_percent=request.flete_percent,
            seguro_percent=request.seguro_percent
        )

        return {
            "success": True,
            "calculo": resultado
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error en cálculo: {e}")
        raise HTTPException(status_code=500, detail="Error al calcular valor en plaza")


@router.post("/comparar-origenes")
async def comparar_origenes_endpoint(request: ComparacionRequest):
    """
    Comparar valor en plaza desde diferentes orígenes

    Útil para decidir desde qué país importar.
    Compara automáticamente: China, Brasil, USA, Alemania, Vietnam

    **Ejemplo:**
    ```json
    {
      "ncm": "84713010",
      "fob_unitario": 500,
      "cantidad": 10
    }
    ```

    **Response incluye:**
    - Lista ordenada por costo (menor a mayor)
    - Mejor y peor origen
    - Ahorro potencial por origen MERCOSUR
    """
    try:
        comparacion = comparar_origenes(
            ncm=request.ncm,
            fob_unitario=request.fob_unitario,
            cantidad=request.cantidad,
            origenes=request.origenes
        )

        return {
            "success": True,
            "comparacion": comparacion
        }

    except Exception as e:
        logger.error(f"Error en comparación: {e}")
        raise HTTPException(status_code=500, detail="Error al comparar orígenes")


@router.get("/ejemplos")
async def get_ejemplos():
    """
    Obtener ejemplos de cálculos pre-configurados

    Útil para testing y demostración.
    Incluye casos comunes: laptops, celulares, neumáticos, etc.
    """
    return {
        "success": True,
        "ejemplos": EJEMPLOS_CALCULO,
        "total": len(EJEMPLOS_CALCULO)
    }


@router.get("/test/{ejemplo_key}")
async def test_ejemplo(ejemplo_key: str):
    """
    Ejecutar cálculo de ejemplo

    **Ejemplos disponibles:**
    - laptop_china
    - laptop_brasil
    - celular_vietnam
    - neumaticos_brasil
    - repuesto_china
    """
    if ejemplo_key not in EJEMPLOS_CALCULO:
        raise HTTPException(
            status_code=404,
            detail=f"Ejemplo '{ejemplo_key}' no encontrado. Disponibles: {list(EJEMPLOS_CALCULO.keys())}"
        )

    ejemplo = EJEMPLOS_CALCULO[ejemplo_key]

    resultado = calcular_valor_plaza(
        ncm=ejemplo["ncm"],
        origen=ejemplo["origen"],
        fob_unitario=ejemplo["fob_unitario"],
        cantidad=ejemplo["cantidad"]
    )

    return {
        "success": True,
        "ejemplo": ejemplo_key,
        "descripcion": ejemplo["descripcion"],
        "input": {
            "ncm": ejemplo["ncm"],
            "origen": ejemplo["origen"],
            "fob_unitario": ejemplo["fob_unitario"],
            "cantidad": ejemplo["cantidad"]
        },
        "resultado": resultado
    }


@router.get("/ncm-rates")
async def get_ncm_rates():
    """
    Obtener tasas de derechos de importación conocidas

    Devuelve el catálogo de NCM con sus tasas configuradas.
    En producción esto vendría de Tarifar o base de datos.
    """
    from ..core.calculator import NCM_DERECHOS_DEFAULT

    rates_formatted = [
        {
            "ncm": ncm,
            "tasa_porcentaje": round(tasa * 100, 1),
            "tasa_decimal": tasa
        }
        for ncm, tasa in NCM_DERECHOS_DEFAULT.items()
    ]

    return {
        "success": True,
        "rates": rates_formatted,
        "total": len(rates_formatted),
        "nota": "Tasas de ejemplo. En producción usar API de Tarifar."
    }


@router.get("/mercosur-info")
async def get_mercosur_info():
    """
    Información sobre preferencias arancelarias MERCOSUR

    Países del MERCOSUR tienen 0% de derechos de importación
    desde Argentina (preferencia arancelaria).
    """
    from ..core.calculator import MERCOSUR_COUNTRIES, MERCOSUR_DISCOUNT

    return {
        "success": True,
        "mercosur": {
            "paises": MERCOSUR_COUNTRIES,
            "descuento_derechos": f"{MERCOSUR_DISCOUNT * 100}%",
            "beneficio": "Derechos de importación reducidos a 0%",
            "ejemplo": "Un producto con 41% de derechos desde China, desde Brasil es 0%"
        }
    }
