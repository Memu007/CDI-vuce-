"""
Calculadora de Valor en Plaza para Importaciones
Calcula el valor final de un producto importado incluyendo todos los tributos

CONCEPTOS:
- FOB (Free On Board): Valor del producto en origen (USD)
- CIF (Cost, Insurance, Freight): FOB + Flete + Seguro
- Derechos de Importación: Impuesto según NCM (variable, ej: 41%)
- IVA: 21% sobre (CIF + Derechos)
- Tasa Estadística: 3% sobre FOB
- Valor en Plaza: Precio final del producto en Argentina
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Tasas fijas de Argentina (2025)
IVA_RATE = 0.21  # 21%
TASA_ESTADISTICA_RATE = 0.03  # 3%
FLETE_DEFAULT_RATE = 0.04  # 4% estimado
SEGURO_DEFAULT_RATE = 0.01  # 1% estimado

# Tasas de derechos por NCM (ejemplos comunes)
# En producción esto vendría de la base de datos o API de Tarifar
NCM_DERECHOS_DEFAULT = {
    # Electrónica
    "84713010": 0.41,  # Laptops - 41%
    "85171200": 0.41,  # Teléfonos móviles - 41%
    "85258000": 0.35,  # Cámaras digitales - 35%

    # Autopartes
    "87089900": 0.35,  # Partes de vehículos - 35%
    "40111000": 0.18,  # Neumáticos - 18%

    # Textiles
    "61091000": 0.35,  # Camisetas - 35%
    "64039900": 0.35,  # Calzado - 35%

    # Maquinaria
    "84314900": 0.14,  # Partes de maquinaria - 14%
    "73089000": 0.14,  # Estructuras metálicas - 14%

    # Químicos
    "29094900": 0.06,  # Productos químicos - 6%
    "39021000": 0.14,  # Polipropileno - 14%
}

# Preferencias arancelarias MERCOSUR (Brasil, Paraguay, Uruguay)
MERCOSUR_COUNTRIES = ["BR", "PY", "UY"]
MERCOSUR_DISCOUNT = 1.0  # 100% descuento en derechos


def get_ncm_rate(ncm: str, origen: str = "XX") -> float:
    """
    Obtener tasa de derechos de importación según NCM y origen

    Args:
        ncm: Código NCM (6-8 dígitos)
        origen: Código de país ISO2 (BR, CN, US, etc.)

    Returns:
        Tasa de derechos (0.0 a 1.0)
    """
    # Preferencia MERCOSUR
    if origen.upper() in MERCOSUR_COUNTRIES:
        logger.info(f"🇧🇷 Origen MERCOSUR ({origen}) - Derechos 0%")
        return 0.0

    # Buscar NCM completo
    ncm_clean = ncm.strip()[:8]  # Máximo 8 dígitos

    if ncm_clean in NCM_DERECHOS_DEFAULT:
        rate = NCM_DERECHOS_DEFAULT[ncm_clean]
        logger.info(f"📋 NCM {ncm_clean}: Derechos {rate * 100}%")
        return rate

    # Buscar por primeros 6 dígitos
    ncm_6 = ncm_clean[:6]
    for ncm_key, rate in NCM_DERECHOS_DEFAULT.items():
        if ncm_key.startswith(ncm_6):
            logger.info(f"📋 NCM {ncm_6}* (aproximado): Derechos {rate * 100}%")
            return rate

    # Default: 35% (promedio común)
    logger.warning(f"⚠️ NCM {ncm_clean} no encontrado - usando 35% default")
    return 0.35


def calcular_valor_plaza(
    ncm: str,
    origen: str,
    fob_unitario: float,
    cantidad: float = 1.0,
    flete_percent: Optional[float] = None,
    seguro_percent: Optional[float] = None
) -> Dict:
    """
    Calcular valor en plaza de un producto importado

    Args:
        ncm: Código NCM del producto
        origen: País de origen (ISO2)
        fob_unitario: Valor FOB unitario en USD
        cantidad: Cantidad de unidades
        flete_percent: % de flete (opcional, default 4%)
        seguro_percent: % de seguro (opcional, default 1%)

    Returns:
        Dict con breakdown completo de costos

    Example:
        >>> calcular_valor_plaza("84713010", "CN", 500.0, 10)
        {
            "fob_total": 5000.0,
            "derechos_importacion": 2050.0,
            "iva": 1480.5,
            "tasa_estadistica": 150.0,
            ...
        }
    """
    # Validaciones
    if fob_unitario <= 0:
        raise ValueError("FOB unitario debe ser mayor a 0")

    if cantidad <= 0:
        raise ValueError("Cantidad debe ser mayor a 0")

    # 1. FOB Total
    fob_total = fob_unitario * cantidad

    # 2. Flete y Seguro
    flete_rate = flete_percent if flete_percent is not None else FLETE_DEFAULT_RATE
    seguro_rate = seguro_percent if seguro_percent is not None else SEGURO_DEFAULT_RATE

    flete = fob_total * flete_rate
    seguro = fob_total * seguro_rate

    # 3. CIF (Cost, Insurance, Freight)
    cif = fob_total + flete + seguro

    # 4. Derechos de Importación
    derechos_rate = get_ncm_rate(ncm, origen)
    derechos = cif * derechos_rate

    # 5. Base Imponible para IVA
    base_iva = cif + derechos

    # 6. IVA (21%)
    iva = base_iva * IVA_RATE

    # 7. Tasa Estadística (3% sobre FOB)
    tasa_estadistica = fob_total * TASA_ESTADISTICA_RATE

    # 8. Total Tributos
    tributos_totales = derechos + iva + tasa_estadistica

    # 9. Valor Final (CIF + Tributos)
    valor_final = cif + tributos_totales

    # 10. Valor Unitario Final
    valor_unitario_final = valor_final / cantidad

    # Calcular porcentajes
    porcentaje_tributos = (tributos_totales / fob_total) * 100 if fob_total > 0 else 0
    porcentaje_derechos = (derechos / fob_total) * 100 if fob_total > 0 else 0

    # Info sobre MERCOSUR
    es_mercosur = origen.upper() in MERCOSUR_COUNTRIES
    ahorro_mercosur = 0.0
    if es_mercosur and derechos_rate == 0.0:
        # Calcular cuánto ahorró
        derechos_sin_mercosur = cif * 0.35  # Promedio sin preferencia
        ahorro_mercosur = derechos_sin_mercosur

    return {
        # Valores base
        "fob_unitario": round(fob_unitario, 2),
        "cantidad": cantidad,
        "fob_total": round(fob_total, 2),

        # Logística
        "flete": round(flete, 2),
        "flete_percent": round(flete_rate * 100, 1),
        "seguro": round(seguro, 2),
        "seguro_percent": round(seguro_rate * 100, 1),

        # CIF
        "cif": round(cif, 2),

        # Tributos
        "derechos_importacion": round(derechos, 2),
        "derechos_percent": round(derechos_rate * 100, 1),
        "iva": round(iva, 2),
        "iva_percent": 21.0,
        "tasa_estadistica": round(tasa_estadistica, 2),
        "tasa_estadistica_percent": 3.0,
        "tributos_totales": round(tributos_totales, 2),

        # Valores finales
        "valor_final": round(valor_final, 2),
        "valor_unitario_final": round(valor_unitario_final, 2),

        # Breakdown
        "breakdown": {
            "base_imponible": round(base_iva, 2),
            "porcentaje_tributos": round(porcentaje_tributos, 1),
            "porcentaje_derechos": round(porcentaje_derechos, 1),
            "incremento_vs_fob": round((valor_final / fob_total - 1) * 100, 1) if fob_total > 0 else 0
        },

        # Info de origen
        "origen": origen.upper(),
        "es_mercosur": es_mercosur,
        "ahorro_mercosur": round(ahorro_mercosur, 2) if es_mercosur else 0.0,

        # Metadata
        "ncm": ncm,
        "ncm_rate_used": round(derechos_rate * 100, 1)
    }


def comparar_origenes(
    ncm: str,
    fob_unitario: float,
    cantidad: float,
    origenes: list = None
) -> Dict:
    """
    Comparar valor en plaza desde diferentes orígenes
    Útil para decidir mejor país de importación

    Args:
        ncm: Código NCM
        fob_unitario: Valor FOB unitario
        cantidad: Cantidad
        origenes: Lista de países a comparar (default: CN, BR, US, DE)

    Returns:
        Dict con comparación de costos por origen
    """
    if origenes is None:
        origenes = ["CN", "BR", "US", "DE", "VN"]

    resultados = []

    for origen in origenes:
        calculo = calcular_valor_plaza(ncm, origen, fob_unitario, cantidad)
        resultados.append({
            "origen": origen,
            "es_mercosur": calculo["es_mercosur"],
            "valor_final": calculo["valor_final"],
            "tributos_totales": calculo["tributos_totales"],
            "ahorro_mercosur": calculo["ahorro_mercosur"]
        })

    # Ordenar por valor final (menor a mayor)
    resultados.sort(key=lambda x: x["valor_final"])

    # Calcular ahorro vs origen más caro
    if resultados:
        mas_caro = resultados[-1]["valor_final"]
        for r in resultados:
            r["ahorro_vs_mas_caro"] = round(mas_caro - r["valor_final"], 2)
            r["ahorro_percent"] = round((mas_caro - r["valor_final"]) / mas_caro * 100, 1) if mas_caro > 0 else 0

    return {
        "ncm": ncm,
        "fob_unitario": fob_unitario,
        "cantidad": cantidad,
        "origenes_comparados": resultados,
        "mejor_origen": resultados[0]["origen"] if resultados else None,
        "peor_origen": resultados[-1]["origen"] if resultados else None,
        "diferencia_maxima": round(resultados[-1]["valor_final"] - resultados[0]["valor_final"], 2) if len(resultados) >= 2 else 0
    }


# ==================== DATOS DE PRUEBA ====================

EJEMPLOS_CALCULO = {
    "laptop_china": {
        "ncm": "84713010",
        "origen": "CN",
        "fob_unitario": 500.0,
        "cantidad": 10,
        "descripcion": "Laptop Dell Inspiron 15 desde China"
    },
    "laptop_brasil": {
        "ncm": "84713010",
        "origen": "BR",
        "fob_unitario": 500.0,
        "cantidad": 10,
        "descripcion": "Laptop Dell Inspiron 15 desde Brasil (MERCOSUR)"
    },
    "celular_vietnam": {
        "ncm": "85171200",
        "origen": "VN",
        "fob_unitario": 300.0,
        "cantidad": 50,
        "descripcion": "Samsung Galaxy S21 desde Vietnam"
    },
    "neumaticos_brasil": {
        "ncm": "40111000",
        "origen": "BR",
        "fob_unitario": 80.0,
        "cantidad": 100,
        "descripcion": "Neumáticos desde Brasil (MERCOSUR - ahorro)"
    },
    "repuesto_china": {
        "ncm": "84314900",
        "origen": "CN",
        "fob_unitario": 25.0,
        "cantidad": 200,
        "descripcion": "Repuesto de maquinaria desde China"
    }
}


def test_calculadora():
    """
    Función de prueba para verificar cálculos
    Ejecutar con: python -c "from proyecto_maria.core.calculator import test_calculadora; test_calculadora()"
    """
    print("=" * 80)
    print("🧮 TEST DE CALCULADORA DE VALOR EN PLAZA")
    print("=" * 80)

    for key, ejemplo in EJEMPLOS_CALCULO.items():
        print(f"\n📦 {key.upper()}: {ejemplo['descripcion']}")
        print("-" * 80)

        resultado = calcular_valor_plaza(
            ncm=ejemplo["ncm"],
            origen=ejemplo["origen"],
            fob_unitario=ejemplo["fob_unitario"],
            cantidad=ejemplo["cantidad"]
        )

        print(f"  FOB Total:           USD {resultado['fob_total']:>12,.2f}")
        print(f"  + Flete ({resultado['flete_percent']}%):      USD {resultado['flete']:>12,.2f}")
        print(f"  + Seguro ({resultado['seguro_percent']}%):     USD {resultado['seguro']:>12,.2f}")
        print(f"  = CIF:               USD {resultado['cif']:>12,.2f}")
        print(f"")
        print(f"  + Derechos ({resultado['derechos_percent']}%):  USD {resultado['derechos_importacion']:>12,.2f}")
        print(f"  + IVA (21%):         USD {resultado['iva']:>12,.2f}")
        print(f"  + Tasa Est. (3%):    USD {resultado['tasa_estadistica']:>12,.2f}")
        print(f"  = TRIBUTOS TOTALES:  USD {resultado['tributos_totales']:>12,.2f}")
        print(f"")
        print(f"  💰 VALOR FINAL:      USD {resultado['valor_final']:>12,.2f}")
        print(f"  💰 Unitario Final:   USD {resultado['valor_unitario_final']:>12,.2f}")
        print(f"")
        print(f"  📊 Tributos / FOB:   {resultado['breakdown']['porcentaje_tributos']}%")
        print(f"  📊 Incremento:       {resultado['breakdown']['incremento_vs_fob']}%")

        if resultado['es_mercosur']:
            print(f"  🇧🇷 MERCOSUR: Ahorro USD {resultado['ahorro_mercosur']:,.2f} en derechos")

    # Test de comparación
    print("\n" + "=" * 80)
    print("🌍 COMPARACIÓN DE ORÍGENES - Laptop $500")
    print("=" * 80)

    comparacion = comparar_origenes(
        ncm="84713010",
        fob_unitario=500.0,
        cantidad=10
    )

    for origen_data in comparacion["origenes_comparados"]:
        mercosur_tag = "🇧🇷" if origen_data["es_mercosur"] else "  "
        print(f"{mercosur_tag} {origen_data['origen']}: USD {origen_data['valor_final']:>10,.2f}  "
              f"(Ahorro: {origen_data['ahorro_percent']:>5.1f}%)")

    print(f"\n✅ Mejor origen: {comparacion['mejor_origen']}")
    print(f"❌ Peor origen: {comparacion['peor_origen']}")
    print(f"💰 Diferencia: USD {comparacion['diferencia_maxima']:,.2f}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_calculadora()
