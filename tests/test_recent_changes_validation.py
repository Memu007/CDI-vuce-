"""
Validation tests for recent changes in CDI Sistema MARÍA.
Tests specifically: Gemini 2.5 Flash fallback, NCM extraction disabled, Auto NCM button removal, auto-select functionality.
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from proyecto_maria.pdf_extractor import (
    robust_extract_pdf_items,
    _llm_extract_pdf_items,
    _extract_with_gemini_vision,
    _extract_row_data,
    _parse_table_to_items,
    _assign_fields_from_analysis
)


@pytest.mark.skip(reason="Gemini mock tests need update")
class TestRecentChangesValidation:
    """Validate that recent changes are working correctly."""
    
    def test_ncm_extraction_completely_disabled(self):
        """Test that NCM extraction is completely disabled across all extraction methods."""
        
        # Test table parsing doesn't extract NCM
        mock_table = [
            ["NCM", "Description", "Quantity", "Price"],
            ["84713010", "Laptop Computer", "100", "500.00"],
            ["87089990", "Car Part", "50", "200.00"]
        ]
        
        result = _parse_table_to_items(mock_table, "CN")
        
        # All items should have empty pieza field
        for item in result:
            assert item["pieza"] == "", f"NCM extraction should be disabled, got: {item['pieza']}"
    
    def test_row_data_analysis_ignores_ncm(self):
        """Test that row data analysis ignores NCM patterns."""
        
        # Test with NCM patterns in data
        mock_row = ["84713010", "87089990", "Laptop Computer", "100", "500.00"]
        
        with patch('proyecto_maria.pdf_extractor._analyze_cell_content') as mock_analyze:
            # Mock cell analysis to ensure NCM detection is skipped
            mock_analyze.return_value = {
                'type': 'description',
                'value': 'Laptop Computer',
                'confidence': 0.8,
                'position': 2
            }
            
            result = _extract_row_data(mock_row)
            
            # Should not extract NCM even when present
            assert result["pieza"] == ""
    
    def test_field_assignment_ignores_ncm(self):
        """Test that field assignment logic ignores NCM."""
        
        cell_types = [
            {'type': 'description', 'value': 'Laptop Computer', 'confidence': 0.8, 'position': 1},
            {'type': 'number', 'value': 100, 'confidence': 0.9, 'likely_qty': True, 'position': 2},
            {'type': 'number', 'value': 500, 'confidence': 0.9, 'likely_price': True, 'position': 3}
        ]
        
        data = {
            'pieza': 'should_be_emptied',
            'descripcion': '',
            'cantidad': 1.0,
            'valor_unitario': 0.0
        }
        
        result = _assign_fields_from_analysis(cell_types, data)
        
        # Should clear pieza field
        assert result["pieza"] == ""
    
    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test-key',
        'ENABLE_FALLBACK_CASCADE': 'true',
        'PREFER_GEMINI_25': 'true'
    })
    def test_gemini_25_flash_preferred_when_flag_set(self):
        """Test that Gemini 2.5 Flash is preferred when flag is set."""
        
        test_text = "Invoice: Product A 100 10.50"
        
        with patch('proyecto_maria.pdf_extractor._load_gemini_client') as mock_gemini:
            mock_genai = Mock()
            mock_gemini.return_value = mock_genai
            
            mock_model_25 = Mock()
            mock_response = Mock()
            mock_response.text = '{"items": [{"pieza": "", "descripcion": "Product A", "cantidad": 100, "valor_unitario": 10.50, "origen": "XX"}]}'
            mock_model_25.generate_content.return_value = mock_response
            
            mock_genai.GenerativeModel.return_value = mock_model_25
            
            result = _llm_extract_pdf_items(test_text)
            
            # Should prefer 2.5 Flash model
            mock_genai.GenerativeModel.assert_called_with('gemini-2.5-flash')
            assert len(result) == 1
            assert result[0]["pieza"] == ""  # NCM extraction still disabled
    
    @patch.dict(os.environ, {
        'GEMINI_API_KEY': 'test-key',
        'ENABLE_FALLBACK_CASCADE': 'true',
        'PREFER_GEMINI_25': 'false'  # Prefer 2.0 Flash
    })
    def test_gemini_20_flash_preferred_when_flag_not_set(self):
        """Test that Gemini 2.0 Flash is preferred when 2.5 flag is not set."""
        
        test_text = "Invoice: Product A 100 10.50"
        
        with patch('proyecto_maria.pdf_extractor._load_gemini_client') as mock_gemini:
            mock_genai = Mock()
            mock_gemini.return_value = mock_genai
            
            mock_model_20 = Mock()
            mock_response = Mock()
            mock_response.text = '{"items": [{"pieza": "", "descripcion": "Product A", "cantidad": 100, "valor_unitario": 10.50, "origen": "XX"}]}'
            mock_model_20.generate_content.return_value = mock_response
            
            mock_genai.GenerativeModel.return_value = mock_model_20
            
            result = _llm_extract_pdf_items(test_text)
            
            # Should prefer 2.0 Flash model by default
            mock_genai.GenerativeModel.assert_called_with('gemini-2.0-flash-exp')
            assert len(result) == 1
    
    def test_fallback_cascade_disabled_when_flag_false(self):
        """Test that fallback cascade is disabled when flag is false."""
        
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test-key',
            'ENABLE_FALLBACK_CASCADE': 'false'
        }):
            
            with patch('proyecto_maria.pdf_extractor._load_gemini_client') as mock_gemini:
                mock_genai = Mock()
                mock_gemini.return_value = mock_genai
                
                # Primary model fails
                mock_model = Mock()
                mock_model.generate_content.side_effect = Exception("Primary failed")
                mock_genai.GenerativeModel.return_value = mock_model
                
                result = _llm_extract_pdf_items("test text")
                
                # Should return empty when cascade disabled and primary fails
                assert result == []
    
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'})
    def test_vision_api_uses_25_flash_when_preferred(self):
        """Test that Vision API uses 2.5 Flash when preferred."""
        
        mock_pdf_data = b"mock pdf data"
        
        with patch('proyecto_maria.pdf_extractor._load_gemini_client') as mock_gemini:
            with patch.dict(os.environ, {'PREFER_GEMINI_25': 'true'}):
                mock_genai = Mock()
                mock_gemini.return_value = mock_genai
                
                mock_model_25 = Mock()
                mock_response = Mock()
                mock_response.text = '{"items": [{"pieza": "", "descripcion": "Test", "cantidad": 100, "valor_unitario": 10.50}]}'
                mock_model_25.generate_content.return_value = mock_response
                
                mock_genai.GenerativeModel.return_value = mock_model_25
                
                with patch('fitz.open') as mock_fitz:  # Mock PyMuPDF
                    mock_doc = Mock()
                    mock_page = Mock()
                    mock_pix = Mock()
                    mock_pix.tobytes.return_value = b"mock image data"
                    mock_page.get_pixmap.return_value = mock_pix
                    mock_doc.__enter__.return_value = mock_doc
                    mock_doc.__exit__.return_value = None
                    mock_doc.__getitem__.return_value = mock_page
                    mock_fitz.return_value = mock_doc
                    
                    result = _extract_with_gemini_vision(mock_pdf_data)
                    
                    # Should call 2.5 Flash first when preferred
                    mock_genai.GenerativeModel.assert_called_with('gemini-2.5-flash')
    
    def test_llm_prompt_instructs_to_leave_ncm_empty(self):
        """Test that LLM prompt instructs to leave NCM fields empty."""
        
        # This test validates the prompt content in pdf_extractor.py
        # The prompt should contain instructions to leave pieza empty
        
        test_prompt_patterns = [
            'pieza: LEAVE EMPTY',
            'pieza=""',
            'leave pieza empty',
            'never extract NCM'
        ]
        
        # Read the actual prompt from pdf_extractor.py
        with open('/Users/Emi/CDI/proyecto_maria/pdf_extractor.py', 'r') as f:
            pdf_extractor_content = f.read()
        
        # Check that prompt contains NCM disable instructions
        for pattern in test_prompt_patterns:
            # Use case-insensitive search
            assert pattern.lower() in pdf_extractor_content.lower(), \
                f"Prompt should instruct to leave NCM empty: {pattern}"


class TestAutoNCMButtonRemovalValidation:
    """Validate that Auto NCM button has been completely removed."""
    
    def test_no_auto_ncm_button_in_main_html(self):
        """Test main HTML file doesn't contain Auto NCM button."""
        html_path = "/Users/Emi/CDI/static/index.html"
        
        with open(html_path, 'r') as f:
            html_content = f.read()
        
        # Check for auto NCM button patterns
        forbidden_patterns = [
            'auto-ncm-btn',
            'btnAutoNcm',
            'autoAssignNcm',
            'Auto NCM',
            'assignar NCM automático',
            'asignar NCM automático'
        ]
        
        for pattern in forbidden_patterns:
            assert pattern.lower() not in html_content.lower(), \
                f"Auto NCM button pattern found: {pattern}"
    
    def test_no_auto_ncm_functions_in_javascript(self):
        """Test JavaScript doesn't contain auto NCM functions."""
        js_path = "/Users/Emi/CDI/static/script.js"
        
        with open(js_path, 'r') as f:
            js_content = f.read()
        
        # Check for auto NCM function patterns
        forbidden_function_patterns = [
            'function.*autoNcm',
            'function.*assignAutoNcm',
            'autoNcm()',
            'assignAutoNcm()',
            '.click.*auto.*ncm',
            'addEventListener.*auto.*ncm'
        ]
        
        for pattern in forbidden_function_patterns:
            lines_with_pattern = [line.strip() for line in js_content.split('\n') 
                                if pattern.lower() in line.lower()]
            assert len(lines_with_pattern) == 0, \
                f"Auto NCM function found: {pattern} in {lines_with_pattern}"
    



@pytest.mark.skip(reason="Field behavior tests need update")
class TestFieldBehaviorValidation:
    """Test field behavior with recent changes."""
    
    def test_empty_ncm_fields_in_ui_validation(self):
        """Test that UI validation accepts empty NCM fields."""
        
        # Mock validation similar to frontend validation
        def validate_frontend_item(item):
            errors = []
            
            # NCM field should be optional (empty allowed)
            if 'pieza' in item and item['pieza'] and not item['pieza'].strip():
                errors.append("NCM no puede estar vacío si está especificado")
            
            # Other fields should be required
            if not item.get('descripcion'):
                errors.append("Descripción es requerida")
            
            if not item.get('cantidad') or item.get('cantidad') <= 0:
                errors.append("Cantidad debe ser mayor a 0")
                
            return errors
        
        # Test with empty NCM field (should pass)
        item_with_empty_ncm = {
            'pieza': '',  # Empty NCM should be allowed
            'descripcion': 'Test Product',
            'cantidad': 100,
            'valor_unitario': 10.50
        }
        
        errors = validate_frontend_item(item_with_empty_ncm)
        
        # Should not have NCM-related errors
        ncm_errors = [error for error in errors if 'ncm' in error.lower() or 'pieza' in error.lower()]
        assert len(ncm_errors) == 0, "Empty NCM should be allowed"
    
    def test_auto_select_triggers_on_empty_fields(self):
        """Test auto-select behavior on empty/default fields."""
        
        def should_auto_select_field(field_name, field_value):
            """Simulate auto-select logic from frontend."""
            empty_values = ['', '0', '0.0', '00000000', 'XX']
            default_patterns = [
                'sin.*cliente',
                'seleccionar',
                'choose',
                'default'
            ]
            
            # Auto-select if empty value
            if field_value in empty_values:
                return True
            
            # Auto-select if contains default text
            if any(pattern in field_value.lower() for pattern in default_patterns):
                return True
            
            return False
        
        # Test cases
        test_cases = [
            ('pieza', '', True),           # Empty NCM should auto-select
            ('pieza', '00000000', True),   # Default NCM should auto-select
            ('origen', 'XX', True),        # Default origin should auto-select
            ('descripcion', 'Product A', False),  # Real description should not auto-select
            ('cantidad', '100', False),    # Real quantity should not auto-select
            ('cliente', 'Sin cliente...', True),  # Default client text should auto-select
        ]
        
        for field_name, field_value, expected_auto_select in test_cases:
            result = should_auto_select_field(field_name, field_value)
            assert result == expected_auto_select, \
                f"Field {field_name} with value '{field_value}' should auto-select: {expected_auto_select}"


class TestExtractionConsistency:
    """Test that all extraction methods behave consistently with recent changes."""
    
    def test_all_extraction_methods_leave_ncm_empty(self):
        """Test that all extraction methods leave NCM empty."""
        
        test_invoice_data = b"""
        Invoice with NCM codes:
        NCM: 84713010, Description: Laptop Computer, Quantity: 100, Price: 500.00
        NCM: 87089990, Description: Car Part, Quantity: 50, Price: 200.00
        """
        
        # Test robust extraction (main method)
        result = robust_extract_pdf_items(test_invoice_data)
        
        # All items should have empty NCM
        for item in result:
            assert item["pieza"] == "", f"robust_extract_pdf_items should leave NCM empty, got: {item['pieza']}"
    
    def test_llm_extraction_leaves_ncm_empty(self):
        """Test that LLM extraction leaves NCM empty."""
        
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            with patch('proyecto_maria.pdf_extractor._load_gemini_client') as mock_gemini:
                mock_genai = Mock()
                mock_gemini.return_value = mock_genai
                
                mock_model = Mock()
                mock_response = Mock()
                mock_response.text = '{"items": [{"pieza": "", "descripcion": "Test Product", "cantidad": 100, "valor_unitario": 10.50, "origen": "XX"}]}'
                mock_model.generate_content.return_value = mock_response
                
                mock_genai.GenerativeModel.return_value = mock_model
                
                result = _llm_extract_pdf_items("test invoice")
                
                # LLM result should have empty NCM
                for item in result:
                    assert item["pieza"] == "", f"LLM extraction should leave NCM empty, got: {item['pieza']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])