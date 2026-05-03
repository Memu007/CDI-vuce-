"""
Tests para Feature #6: Calculadora de Valor en Plaza
Tests para core/calculator.py
"""

import pytest
from proyecto_maria.core.calculator import (
    calcular_valor_plaza,
    comparar_origenes,
    get_ncm_rate,
    EJEMPLOS_CALCULO,
    NCM_DERECHOS_DEFAULT,
    MERCOSUR_COUNTRIES,
    IVA_RATE,
    TASA_ESTADISTICA_RATE
)


class TestGetNCMRate:
    """Tests para obtención de tasas NCM"""

    def test_get_rate_mercosur_brazil(self):
        """MERCOSUR Brasil = 0% derechos"""
        rate = get_ncm_rate("84713010", "BR")
        assert rate == 0.0

    def test_get_rate_mercosur_paraguay(self):
        """MERCOSUR Paraguay = 0% derechos"""
        rate = get_ncm_rate("85171200", "PY")
        assert rate == 0.0

    def test_get_rate_mercosur_uruguay(self):
        """MERCOSUR Uruguay = 0% derechos"""
        rate = get_ncm_rate("40111000", "UY")
        assert rate == 0.0

    def test_get_rate_laptop_china(self):
        """Laptop desde China = 41%"""
        rate = get_ncm_rate("84713010", "CN")
        assert rate == 0.41

    def test_get_rate_celular_usa(self):
        """Celular desde USA = 41%"""
        rate = get_ncm_rate("85171200", "US")
        assert rate == 0.41

    def test_get_rate_neumaticos_vietnam(self):
        """Neumáticos desde Vietnam = 18%"""
        rate = get_ncm_rate("40111000", "VN")
        assert rate == 0.18

    def test_get_rate_quimicos(self):
        """Productos químicos = 6%"""
        rate = get_ncm_rate("29094900", "DE")
        assert rate == 0.06

    def test_get_rate_ncm_6_digitos(self):
        """Buscar por primeros 6 dígitos si no encuentra NCM completo"""
        # NCM 847130XX debería matchear con 84713010 (laptops)
        rate = get_ncm_rate("84713099", "CN")
        assert rate == 0.41

    def test_get_rate_unknown_ncm(self):
        """NCM desconocido = 35% default"""
        rate = get_ncm_rate("99999999", "CN")
        assert rate == 0.35

    def test_get_rate_case_insensitive_country(self):
        """Origen case insensitive"""
        rate1 = get_ncm_rate("84713010", "br")
        rate2 = get_ncm_rate("84713010", "BR")
        rate3 = get_ncm_rate("84713010", "Br")
        assert rate1 == rate2 == rate3 == 0.0


class TestCalcularValorPlaza:
    """Tests para cálculo de valor en plaza"""

    def test_calculo_laptop_china(self):
        """Laptop desde China: FOB $500 x 10 unidades"""
        result = calcular_valor_plaza(
            ncm="84713010",
            origen="CN",
            fob_unitario=500.0,
            cantidad=10
        )

        assert result["ncm"] == "84713010"
        assert result["origen"] == "CN"
        assert result["cantidad"] == 10
        assert result["fob_unitario"] == 500.0
        assert result["fob_total"] == 5000.0

        # Flete 4% + Seguro 1%
        assert result["flete"] == pytest.approx(200.0, rel=0.01)  # 5000 * 0.04
        assert result["seguro"] == pytest.approx(50.0, rel=0.01)  # 5000 * 0.01

        # CIF = FOB + Flete + Seguro
        assert result["cif"] == pytest.approx(5250.0, rel=0.01)

        # Derechos 41%
        assert result["derechos_rate"] == 0.41
        assert result["derechos"] == pytest.approx(2152.5, rel=0.01)  # 5250 * 0.41

        # IVA 21% sobre (CIF + Derechos)
        base_iva = 5250.0 + 2152.5
        assert result["iva"] == pytest.approx(base_iva * 0.21, rel=0.01)

        # Tasa estadística 3% sobre FOB
        assert result["tasa_estadistica"] == pytest.approx(150.0, rel=0.01)  # 5000 * 0.03

        # Valor total
        assert "valor_total" in result
        assert result["valor_total"] > 0

    def test_calculo_laptop_brazil_mercosur(self):
        """Laptop desde Brasil (MERCOSUR) = 0% derechos"""
        result = calcular_valor_plaza(
            ncm="84713010",
            origen="BR",
            fob_unitario=500.0,
            cantidad=10
        )

        assert result["derechos_rate"] == 0.0
        assert result["derechos"] == 0.0
        assert result["origen"] == "BR"

        # Verificar que el valor total es menor que desde China
        result_china = calcular_valor_plaza("84713010", "CN", 500.0, 10)
        assert result["valor_total"] < result_china["valor_total"]

    def test_calculo_neumaticos_vietnam(self):
        """Neumáticos desde Vietnam: 18% derechos"""
        result = calcular_valor_plaza(
            ncm="40111000",
            origen="VN",
            fob_unitario=100.0,
            cantidad=50
        )

        assert result["fob_total"] == 5000.0
        assert result["derechos_rate"] == 0.18
        assert result["derechos"] == pytest.approx(result["cif"] * 0.18, rel=0.01)

    def test_calculo_con_flete_custom(self):
        """Cálculo con flete personalizado"""
        result = calcular_valor_plaza(
            ncm="84713010",
            origen="CN",
            fob_unitario=500.0,
            cantidad=10,
            flete_percent=0.10  # 10% flete (mayor al default)
        )

        assert result["flete"] == pytest.approx(500.0, rel=0.01)  # 5000 * 0.10
        assert result["flete_percent"] == 0.10

    def test_calculo_con_seguro_custom(self):
        """Cálculo con seguro personalizado"""
        result = calcular_valor_plaza(
            ncm="84713010",
            origen="CN",
            fob_unitario=500.0,
            cantidad=10,
            seguro_percent=0.02  # 2% seguro
        )

        assert result["seguro"] == pytest.approx(100.0, rel=0.01)  # 5000 * 0.02
        assert result["seguro_percent"] == 0.02

    def test_calculo_una_unidad(self):
        """Cálculo con una sola unidad"""
        result = calcular_valor_plaza(
            ncm="85171200",
            origen="CN",
            fob_unitario=300.0,
            cantidad=1
        )

        assert result["cantidad"] == 1
        assert result["fob_total"] == 300.0
        assert result["valor_unitario"] == result["valor_total"]

    def test_valores_positivos(self):
        """Todos los valores deben ser positivos"""
        result = calcular_valor_plaza(
            ncm="84713010",
            origen="CN",
            fob_unitario=500.0,
            cantidad=10
        )

        assert result["fob_total"] > 0
        assert result["flete"] >= 0
        assert result["seguro"] >= 0
        assert result["cif"] > 0
        assert result["derechos"] >= 0
        assert result["iva"] >= 0
        assert result["tasa_estadistica"] >= 0
        assert result["valor_total"] > 0
        assert result["valor_unitario"] > 0

    def test_estructura_resultado(self):
        """Verificar estructura completa del resultado"""
        result = calcular_valor_plaza(
            ncm="84713010",
            origen="CN",
            fob_unitario=500.0,
            cantidad=10
        )

        # Campos obligatorios
        required_fields = [
            "ncm", "origen", "cantidad",
            "fob_unitario", "fob_total",
            "flete", "flete_percent",
            "seguro", "seguro_percent",
            "cif",
            "derechos", "derechos_rate",
            "iva", "iva_rate",
            "tasa_estadistica", "tasa_estadistica_rate",
            "valor_total", "valor_unitario"
        ]

        for field in required_fields:
            assert field in result, f"Campo faltante: {field}"


class TestCompararOrigenes:
    """Tests para comparación de orígenes"""

    def test_comparar_5_origenes(self):
        """Comparar 5 orígenes (CN, BR, US, DE, VN)"""
        result = comparar_origenes(
            ncm="84713010",
            fob_unitario=500.0,
            cantidad=10
        )

        assert "comparacion" in result
        assert len(result["comparacion"]) == 5

        # Verificar que incluye los 5 países
        origenes = [calc["origen"] for calc in result["comparacion"]]
        assert "CN" in origenes
        assert "BR" in origenes
        assert "US" in origenes
        assert "DE" in origenes
        assert "VN" in origenes

    def test_comparar_orden_por_precio(self):
        """Verificar que está ordenado de menor a mayor precio"""
        result = comparar_origenes(
            ncm="84713010",
            fob_unitario=500.0,
            cantidad=10
        )

        valores = [calc["valor_total"] for calc in result["comparacion"]]

        # Verificar orden ascendente
        for i in range(len(valores) - 1):
            assert valores[i] <= valores[i + 1]

    def test_comparar_brasil_mas_barato(self):
        """Brasil (MERCOSUR) debería ser el más barato"""
        result = comparar_origenes(
            ncm="84713010",  # Laptop 41%
            fob_unitario=500.0,
            cantidad=10
        )

        # Brasil debería ser el primero (más barato)
        mas_barato = result["comparacion"][0]
        assert mas_barato["origen"] == "BR"

        # Verificar ahorro vs más caro
        mas_caro = result["comparacion"][-1]
        ahorro = mas_caro["valor_total"] - mas_barato["valor_total"]
        assert ahorro > 0
        assert result["ahorro_mejor_opcion"] == ahorro

    def test_comparar_recomendacion(self):
        """Verificar que incluye recomendación"""
        result = comparar_origenes(
            ncm="84713010",
            fob_unitario=500.0,
            cantidad=10
        )

        assert "recomendacion" in result
        assert result["recomendacion"]["origen"] == "BR"  # MERCOSUR es lo mejor
        assert result["recomendacion"]["motivo"] == "MERCOSUR (0% derechos)"

    def test_comparar_con_flete_custom(self):
        """Comparación con flete personalizado"""
        result = comparar_origenes(
            ncm="84713010",
            fob_unitario=500.0,
            cantidad=10,
            flete_percent=0.08
        )

        # Todos deberían tener el mismo flete
        for calc in result["comparacion"]:
            assert calc["flete_percent"] == 0.08


class TestEjemplos:
    """Tests para ejemplos pre-configurados"""

    def test_ejemplos_calculo_existe(self):
        """Verificar que EJEMPLOS_CALCULO existe"""
        assert EJEMPLOS_CALCULO is not None
        assert isinstance(EJEMPLOS_CALCULO, dict)
        assert len(EJEMPLOS_CALCULO) > 0

    def test_ejemplos_estructura(self):
        """Verificar estructura de ejemplos"""
        for key, ejemplo in EJEMPLOS_CALCULO.items():
            assert isinstance(ejemplo, dict)
            # Ejemplos deberían tener al menos ncm, origen, fob_unitario
            if "comparacion" not in ejemplo:
                assert "ncm" in ejemplo or "origen" in ejemplo


class TestConstantes:
    """Tests para constantes y configuración"""

    def test_iva_rate(self):
        """IVA = 21%"""
        assert IVA_RATE == 0.21

    def test_tasa_estadistica_rate(self):
        """Tasa estadística = 3%"""
        assert TASA_ESTADISTICA_RATE == 0.03

    def test_mercosur_countries(self):
        """Países MERCOSUR: BR, PY, UY"""
        assert "BR" in MERCOSUR_COUNTRIES
        assert "PY" in MERCOSUR_COUNTRIES
        assert "UY" in MERCOSUR_COUNTRIES
        assert len(MERCOSUR_COUNTRIES) == 3

    def test_ncm_derechos_default_exists(self):
        """Verificar que existen tasas NCM por default"""
        assert len(NCM_DERECHOS_DEFAULT) >= 12
        assert "84713010" in NCM_DERECHOS_DEFAULT  # Laptops
        assert "85171200" in NCM_DERECHOS_DEFAULT  # Celulares
        assert "40111000" in NCM_DERECHOS_DEFAULT  # Neumáticos


class TestEdgeCases:
    """Tests para casos extremos"""

    def test_calculo_cantidad_cero(self):
        """Cantidad = 0 debería retornar valores en 0"""
        result = calcular_valor_plaza(
            ncm="84713010",
            origen="CN",
            fob_unitario=500.0,
            cantidad=0
        )

        assert result["fob_total"] == 0.0
        assert result["valor_total"] == 0.0

    def test_calculo_fob_cero(self):
        """FOB = 0 debería retornar valores en 0"""
        result = calcular_valor_plaza(
            ncm="84713010",
            origen="CN",
            fob_unitario=0.0,
            cantidad=10
        )

        assert result["fob_total"] == 0.0
        assert result["valor_total"] >= 0  # Podría tener IVA sobre derechos

    def test_calculo_flete_cero(self):
        """Flete = 0% es válido"""
        result = calcular_valor_plaza(
            ncm="84713010",
            origen="CN",
            fob_unitario=500.0,
            cantidad=10,
            flete_percent=0.0
        )

        assert result["flete"] == 0.0
        assert result["cif"] == result["fob_total"]  # CIF = FOB si flete y seguro = 0

    def test_calculo_ncm_vacio(self):
        """NCM vacío debería usar tasa default"""
        result = calcular_valor_plaza(
            ncm="",
            origen="CN",
            fob_unitario=500.0,
            cantidad=10
        )

        assert result["derechos_rate"] == 0.35  # Default

    def test_calculo_origen_vacio(self):
        """Origen vacío no debería ser MERCOSUR"""
        result = calcular_valor_plaza(
            ncm="84713010",
            origen="",
            fob_unitario=500.0,
            cantidad=10
        )

        assert result["derechos_rate"] > 0  # No es MERCOSUR


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
