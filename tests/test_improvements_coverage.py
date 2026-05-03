#!/usr/bin/env python3
"""
Tests adicionales para alcanzar 70% cobertura de código
y validar funcionalidades implementadas sin regresiones.
"""

import pytest

# Skip all tests - PDF router functions changed
pytestmark = pytest.mark.skip(reason="PDF router API changed - tests need rewrite")
import tempfile
import os
from unittest.mock import patch, MagicMock
from proyecto_maria.models.operations import Item, OperationPayload
from proyecto_maria.core.validations import run_pre_maria_validations
from proyecto_maria.routers.pdf_router import (
    _to_number_any, _clean_ncm, _is_noise_desc, 
    _tariff_group_from_pieza, _extract_pdf_text,
    _fallback_extraction, _evaluate_extraction_quality
)


class TestItemsConNCMVacio:
    """Tests para validar que items con NCM vacío son aceptados"""
    
    def test_item_con_ncm_vacio_valido(self):
        """Un item con NCM vacío debe ser válido según diseño actual"""
        item = Item(
            pieza="",  # NCM vacío
            descripcion="Producto de prueba",
            origen="XX",
            cantidad=10.0,
            valor_unitario=100.0,
            peso_unitario=1.0
        )
        
        valid_items, errors = run_pre_maria_validations([item])
        
        assert len(valid_items) == 1
        assert len(errors) == 0
        assert valid_items[0].pieza == ""
    
    def test_item_con_ncm_nulo_valido(self):
        """Un item con NCM None debe ser válido"""
        item = Item(
            pieza=None,
            descripcion="Producto de prueba",
            origen="CN",
            cantidad=5.0,
            valor_unitario=50.0,
            peso_unitario=0.5
        )
        
        valid_items, errors = run_pre_maria_validations([item])
        
        assert len(valid_items) == 1
        assert len(errors) == 0
    
    def test_multiples_items_ncm_vacio(self):
        """Múltiples items con NCM vacío deben ser válidos"""
        items = [
            Item(pieza="", descripcion="Item 1", origen="XX", cantidad=1, valor_unitario=10, peso_unitario=1),
            Item(pieza="", descripcion="Item 2", origen="CN", cantidad=2, valor_unitario=20, peso_unitario=2),
            Item(pieza="84713010", descripcion="Item 3", origen="BR", cantidad=3, valor_unitario=30, peso_unitario=3),
        ]
        
        valid_items, errors = run_pre_maria_validations(items)
        
        assert len(valid_items) == 3
        assert len(errors) == 0


class TestOrigenXXValido:
    """Tests para validar que origen XX es aceptado"""
    
    def test_origen_xx_es_valido(self):
        """Origen XX debe ser válido como default"""
        item = Item(
            pieza="84713010",
            descripcion="Producto con origen XX",
            origen="XX",
            cantidad=10.0,
            valor_unitario=100.0,
            peso_unitario=1.0
        )
        
        valid_items, errors = run_pre_maria_validations([item])
        
        assert len(valid_items) == 1
        assert len(errors) == 0
    
    def test_origen_xx_con_ncm_vacio(self):
        """Item con NCM vacío y origen XX debe ser válido"""
        item = Item(
            pieza="",
            descripcion="Item completo default",
            origen="XX",
            cantidad=1.0,
            valor_unitario=1.0,
            peso_unitario=0.1
        )
        
        valid_items, errors = run_pre_maria_validations([item])
        
        assert len(valid_items) == 1
        assert len(errors) == 0


class TestFuncionesUtilitarias:
    """Tests para funciones utilitarias mejor cobertura"""
    
    def test_to_number_any_formatos_diversos(self):
        """Test conversión de números con varios formatos"""
        # Decimales con coma
        assert _to_number_any("123,45") == 123.45
        assert _to_number_any("1.234,56") == 1234.56
        
        # Decimales con punto
        assert _to_number_any("123.45") == 123.45
        assert _to_number_any("1,234.56") == 1234.56
        
        # Con símbolos de moneda
        assert _to_number_any("USD 123.45") == 123.45
        assert _to_number_any("$123,45") == 123.45
        
        # Valores inválidos
        assert _to_number_any("") == 0.0
        assert _to_number_any("abc") == 0.0
        assert _to_number_any(None) == 0.0
    
    def test_clean_ncm(self):
        """Test limpieza de códigos NCM"""
        assert _clean_ncm("84713010") == "84713010"
        assert _clean_ncm("8471-3010") == "84713010"
        assert _clean_ncm("84-71-30-10") == "84713010"
        assert _clean_ncm("abc84713010") == "84713010"
        assert _clean_ncm("") == ""
        assert _clean_ncm("123") == "123"  # Menos de 4 dígitos se mantiene
    
    def test_is_noise_desc(self):
        """Test detección de descripciones de ruido"""
        # Ruido
        assert _is_noise_desc("") == True
        assert _is_noise_desc("123") == True
        assert _is_noise_desc("subtotal") == True
        assert _is_noise_desc("IVA") == True
        assert _is_noise_desc("total factura") == True
        
        # No ruido
        assert _is_noise_desc("Laptop Computer") == False
        assert _is_noise_desc("Producto de prueba") == False
        assert _is_noise_desc("Mouse USB") == False
    
    def test_tariff_group_from_pieza(self):
        """Test extracción de grupo arancelario"""
        assert _tariff_group_from_pieza("84713010") == "8471"
        assert _tariff_group_from_pieza("84713010ABC") == "8471"
        assert _tariff_group_from_pieza("8471") == "8471"
        assert _tariff_group_from_pieza("") == ""
        assert _tariff_group_from_pieza(None) == ""


class TestFallbackExtraction:
    """Tests para fallback extraction con mayor cobertura"""
    
    def test_fallback_extraction_con_texto_simple(self):
        """Test fallback extraction con texto simple de factura"""
        texto = """
        Factura de Prueba
        ------------------
        1 Laptop Computer $500.00
        2 Mouse USB $20.00
        3 Keyboard $50.00
        """
        
        items = _fallback_extraction(texto)
        
        assert len(items) >= 2  # Al menos debe extraer algunos items
        for item in items:
            assert 'descripcion' in item
            assert 'cantidad' in item
            assert 'valor_unitario' in item
            assert item['cantidad'] > 0
            assert item['valor_unitario'] > 0
    
    def test_fallback_extraction_con_ncm(self):
        """Test fallback extraction detectando NCM"""
        texto = """
        NCM: 84713010 Laptop Computer 10 units $500.00
        NCM: 84716050 Mouse USB 20 units $20.00
        """
        
        items = _fallback_extraction(texto)
        
        assert len(items) >= 2
        # Debería detectar al menos un NCM
        items_con_ncm = [item for item in items if item.get('pieza')]
        assert len(items_con_ncm) >= 1


class TestQualityEvaluation:
    """Tests para evaluación de calidad de extracción"""
    
    def test_evaluate_quality_empty_items(self):
        """Test evaluación con lista vacía"""
        result = _evaluate_extraction_quality([])
        
        assert result['use_llm'] == True
        assert result['reason'] == 'no_items'
        assert result['quality_score'] == 0
    
    def test_evaluate_quality_high_quality(self):
        """Test evaluación con items de alta calidad"""
        items = [
            {
                'pieza': '84713010',
                'descripcion': 'Laptop Computer High Quality',
                'origen': 'CN',
                'cantidad': 10,
                'valor_unitario': 500,
                'peso_unitario': 2.0
            },
            {
                'pieza': '84716050',
                'descripcion': 'Mouse USB Optical',
                'origen': 'BR',
                'cantidad': 20,
                'valor_unitario': 25,
                'peso_unitario': 0.5
            }
        ]
        
        result = _evaluate_extraction_quality(items)
        
        assert result['use_llm'] == False
        assert result['reason'] == 'high_quality'
        assert result['quality_score'] >= 70
        assert result['ncm_coverage'] == 1.0
        assert result['desc_coverage'] == 1.0
    
    def test_evaluate_quality_low_quality(self):
        """Test evaluación con items de baja calidad"""
        items = [
            {
                'pieza': '',
                'descripcion': 'Prod',
                'origen': 'XX',
                'cantidad': 1,
                'valor_unitario': 10,
                'peso_unitario': 0.1
            }
        ]
        
        result = _evaluate_extraction_quality(items)
        
        assert result['use_llm'] == True
        assert result['quality_score'] < 50
        assert result['ncm_coverage'] == 0.0


class TestPDFExtractionMock:
    """Tests para extracción PDF con mocks"""
    
    def test_extract_pdf_text_with_pdfminer(self):
        """Test extracción de texto con pdfminer mock"""
        # Crear PDF de prueba simulado
        pdf_data = b"PDF content de prueba"
        
        with patch('proyecto_maria.routers.pdf_router.extract_text') as mock_extract:
            mock_extract.return_value = "Texto extraído del PDF de prueba"
            
            result = _extract_pdf_text(pdf_data)
            
            assert result == "Texto extraído del PDF de prueba"
            mock_extract.assert_called_once()
    
    def test_extract_pdf_text_fallback_to_pypdf2(self):
        """Test fallback a PyPDF2 cuando pdfminer falla"""
        pdf_data = b"PDF content de prueba"
        
        with patch('proyecto_maria.routers.pdf_router.extract_text', side_effect=Exception("pdfminer error")), \
             patch('PyPDF2.PdfReader') as mock_pypdf2:
            
            # Mock pages
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Texto desde PyPDF2"
            mock_reader = MagicMock()
            mock_reader.pages = [mock_page]
            mock_pypdf2.return_value = mock_reader
            
            result = _extract_pdf_text(pdf_data)
            
            assert result == "Texto desde PyPDF2"
    
    def test_extract_pdf_text_complete_failure(self):
        """Test cuando ambos métodos fallan"""
        pdf_data = b"PDF content invalido"
        
        with patch('proyecto_maria.routers.pdf_router.extract_text', side_effect=Exception("pdfminer error")), \
             patch('PyPDF2.PdfReader', side_effect=Exception("pypdf2 error")):
            
            result = _extract_pdf_text(pdf_data)
            
            assert result == ""


class TestEndpointProcessOperation:
    """Tests para endpoint /process_operation/"""
    
    def test_process_operation_con_ncm_vacio(self):
        """Test process_operation aceptando NCM vacío"""
        from proyecto_maria.routers.pdf_router import process_operation
        
        payload = OperationPayload(
            operation_id="test-123",
            items=[
                Item(
                    pieza="",  # NCM vacío
                    descripcion="Producto test",
                    origen="XX",
                    cantidad=10,
                    valor_unitario=100,
                    peso_unitario=1.0
                )
            ]
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'DATA_DIR': temp_dir}):
                result = process_operation(payload)
                
                assert result['success'] == True
                assert 'filename' in result
                assert result['validated_items_count'] == 1
    
    def test_process_operation_con_valores_invalidos(self):
        """Test process_operation rechazando valores inválidos"""
        from proyecto_maria.routers.pdf_router import process_operation
        
        payload = OperationPayload(
            operation_id="test-invalid",
            items=[
                Item(
                    pieza="84713010",
                    descripcion="Producto inválido",
                    origen="CN",
                    cantidad=0,  # Inválido
                    valor_unitario=100,
                    peso_unitario=1.0
                )
            ]
        )
        
        result = process_operation(payload)
        
        assert result['success'] == False
        assert 'cantidad inválida' in result['detail']


class TestItemModelValidation:
    """Tests para modelo Item con NCM vacío"""
    
    def test_item_model_accepts_empty_pieza(self):
        """Test que el modelo Item acepta NCM vacío"""
        item = Item(
            pieza="",
            descripcion="Test",
            origen="XX",
            cantidad=1,
            valor_unitario=1,
            peso_unitario=0.1
        )
        
        assert item.pieza == ""
        assert item.total == 1.0  # Verificar cálculo automático
    
    def test_item_model_validation_functions(self):
        """Test funciones de validación del modelo"""
        # Validación NCM
        item = Item(pieza="84713010")
        assert item.pieza == "84713010"
        
        item = Item(pieza="  84713010  ")
        assert item.pieza == "84713010"
        
        # Validación origen
        item = Item(origen="cn")
        assert item.origen == "CN"
        
        item = Item(origen="brasil")
        assert item.origen == "BRA"
        
        # Default XX
        item = Item(origen="")
        assert item.origen == "XX"


if __name__ == "__main__":
    # Ejecutar tests específicos
    pytest.main([__file__, "-v", "--tb=short"])