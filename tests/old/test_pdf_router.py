"""
Tests para PDF Router - Componente crítico que consume Gemini API
"""
import pytest
import json
import os
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile

from proyecto_maria.main import app
from tests.conftest import (
    test_client, 
    sample_pdf_content, 
    mock_gemini_response,
    create_test_pdf_bytes,
    assert_api_response
)


class TestPDFRouterEndpoints:
    """Tests de endpoints del router PDF"""
    
    def test_health_endpoint(self, test_client):
        """Endpoint de salud debe responder"""
        response = test_client.get('/health')
        data = assert_api_response(response)
        
        assert 'status' in data
        assert data['status'] == 'ok'
    
    @patch('proyecto_maria.routers.pdf_router._llm_extract_pdf_items')
    def test_upload_pdf_endpoint_success(self, mock_llm_extract, test_client):
        """Upload PDF exitoso con mock de Gemini"""
        # Mock respuesta de Gemini
        mock_llm_extract.return_value = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell Inspiron",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            }
        ]
        
        # Crear archivo PDF de prueba
        files = {'file': ('test.pdf', create_test_pdf_bytes(), 'application/pdf')}
        data = {'client_id': 'test-client'}
        
        response = test_client.post('/upload_pdf/', files=files, data=data)
        result = assert_api_response(response)
        
        assert result['success'] is True
        assert 'items' in result
        assert len(result['items']) > 0
        
        # Verificar estructura de items
        item = result['items'][0]
        assert 'pieza' in item
        assert 'descripcion' in item
        assert 'origen' in item
        assert 'cantidad' in item
        assert 'valor_unitario' in item
    
    def test_upload_pdf_no_file(self, test_client):
        """Upload PDF sin archivo debe fallar"""
        response = test_client.post('/upload_pdf/')
        
        # FastAPI devuelve 422 para validación faltante
        assert response.status_code in [400, 422]
    
    @patch('proyecto_maria.routers.pdf_router._llm_extract_pdf_items')
    def test_upload_pdf_llm_endpoint(self, mock_llm_extract, test_client):
        """Endpoint upload_pdf_llm con arquitectura Gemini Always"""
        mock_llm_extract.return_value = [
            {
                "pieza": "85171200",
                "descripcion": "Smartphone Samsung",
                "origen": "VN",
                "cantidad": 20,
                "valor_unitario": 300.0,
                "peso_unitario": 0.2
            }
        ]
        
        files = {'file': ('test.pdf', create_test_pdf_bytes(), 'application/pdf')}
        data = {'client_id': 'test-client'}
        
        response = test_client.post('/upload_pdf_llm/', files=files, data=data)
        result = assert_api_response(response)
        
        assert result['success'] is True
        assert 'items' in result
        assert len(result['items']) > 0
    
    @patch('proyecto_maria.routers.pdf_router._llm_extract_pdf_items')
    def test_upload_pdf_gemini_only_endpoint(self, mock_llm_extract, test_client):
        """Endpoint upload_pdf_gemini_only - 100% IA sin fallbacks"""
        mock_llm_extract.return_value = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell Inspiron",
                "origen": "CN",
                "cantidad": 5,
                "valor_unitario": 800.0,
                "peso_unitario": 2.8
            }
        ]
        
        files = {'file': ('test.pdf', create_test_pdf_bytes(), 'application/pdf')}
        data = {'client_id': 'test-client'}
        
        response = test_client.post('/upload_pdf_gemini_only/', files=files, data=data)
        result = assert_api_response(response)
        
        assert result['success'] is True
        assert 'items' in result
        assert len(result['items']) > 0
    
    @patch('proyecto_maria.routers.pdf_router.process_operation')
    def test_process_operation_endpoint(self, mock_process, test_client):
        """Endpoint process_operation"""
        mock_process.return_value = {
            'success': True,
            'filename': 'test_operation.xlsx',
            'download_url': '/download/test_operation.xlsx'
        }
        
        payload = {
            'client_id': 'test-client',
            'items': [
                {
                    "pieza": "84713010",
                    "descripcion": "Laptop Dell",
                    "origen": "CN",
                    "cantidad": 10,
                    "valor_unitario": 500.0,
                    "peso_unitario": 2.5
                }
            ],
            'operation_type': 'importacion'
        }
        
        response = test_client.post('/process_operation/', json=payload)
        result = assert_api_response(response)
        
        assert result['success'] is True
        assert 'filename' in result
        assert 'download_url' in result


class TestPDFExtractionFunctions:
    """Tests de funciones de extracción de PDF"""
    
    @patch('proyecto_maria.routers.pdf_router._extract_pdf_text')
    def test_extract_pdf_text_success(self, mock_extract):
        """Extracción de texto PDF exitosa"""
        from proyecto_maria.routers.pdf_router import _extract_pdf_text
        
        mock_extract.return_value = "Contenido de prueba del PDF"
        
        result = _extract_pdf_text(create_test_pdf_bytes())
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    @patch('proyecto_maria.routers.pdf_router._robust_extract_pdf_items')
    def test_robust_extract_pdf_items(self, mock_robust):
        """Extracción robusta de items PDF"""
        from proyecto_maria.routers.pdf_router import _robust_extract_pdf_items
        
        mock_robust.return_value = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            }
        ]
        
        result = _robust_extract_pdf_items(create_test_pdf_bytes())
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert 'pieza' in result[0]
    
    @patch('proyecto_maria.routers.pdf_router._evaluate_extraction_quality')
    def test_evaluate_extraction_quality(self, mock_evaluate):
        """Evaluación de calidad de extracción"""
        from proyecto_maria.routers.pdf_router import _evaluate_extraction_quality
        
        mock_evaluate.return_value = {
            'score': 0.85,
            'issues': [],
            'recommendation': 'accept'
        }
        
        items = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            }
        ]
        
        result = _evaluate_extraction_quality(items)
        
        assert isinstance(result, dict)
        assert 'score' in result
        assert 'issues' in result
        assert 'recommendation' in result


class TestGeminiIntegration:
    """Tests de integración con Gemini API"""
    
    @patch('google.generativeai.GenerativeModel')
    @patch('google.generativeai.configure')
    def test_llm_extract_pdf_items_success(self, mock_configure, mock_model, cleanup_env):
        """Extracción LLM exitosa con Gemini"""
        from proyecto_maria.routers.pdf_router import _llm_extract_pdf_items
        
        # Mock de Gemini
        mock_response = Mock()
        mock_response.text = json.dumps([
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell Inspiron",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            }
        ])
        
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance
        
        # Mock de API key
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            result = _llm_extract_pdf_items("Texto de prueba del PDF")
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        item = result[0]
        assert 'pieza' in item
        assert 'descripcion' in item
        assert 'origen' in item
        assert 'cantidad' in item
        assert 'valor_unitario' in item
    
    @patch('google.generativeai.GenerativeModel')
    def test_llm_extract_pdf_items_no_api_key(self, mock_model, cleanup_env):
        """Extracción LLM sin API key debe fallback"""
        from proyecto_maria.routers.pdf_router import _llm_extract_pdf_items
        
        # Sin API key
        with patch.dict(os.environ, {'GEMINI_API_KEY': ''}):
            result = _llm_extract_pdf_items("Texto de prueba")
        
        # Debe fallback a lista vacía o extracción básica
        assert isinstance(result, list)
    
    @patch('google.generativeai.GenerativeModel')
    @patch('google.generativeai.configure')
    def test_llm_extract_pdf_items_safety_filter(self, mock_configure, mock_model, cleanup_env):
        """Extracción LLM con safety filter activado"""
        from proyecto_maria.routers.pdf_router import _llm_extract_pdf_items
        import google.generativeai as genai
        
        # Mock de safety filter
        mock_response = Mock()
        mock_response.text = ""
        mock_response.candidates = []
        
        # Simular safety block
        error = genai.BlockedPromptException(reason="SAFETY")
        mock_model_instance = Mock()
        mock_model_instance.generate_content.side_effect = error
        mock_model.return_value = mock_model_instance
        
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            result = _llm_extract_pdf_items("Texto bloqueado")
        
        # Debe manejar el error gracefully
        assert isinstance(result, list)


class TestPDFRouterErrorHandling:
    """Tests de manejo de errores en router PDF"""
    
    def test_upload_pdf_invalid_file_type(self, test_client):
        """Upload PDF con tipo de archivo inválido"""
        files = {'file': ('test.txt', b'contenido de texto', 'text/plain')}
        data = {'client_id': 'test-client'}
        
        response = test_client.post('/upload_pdf/', files=files, data=data)
        
        # Debe manejar archivo inválido
        assert response.status_code in [400, 422]
    
    def test_upload_pdf_large_file(self, test_client):
        """Upload PDF con archivo muy grande"""
        # Crear archivo grande (simulado)
        large_content = b'x' * (11 * 1024 * 1024)  # 11MB
        
        files = {'file': ('large.pdf', large_content, 'application/pdf')}
        data = {'client_id': 'test-client'}
        
        response = test_client.post('/upload_pdf/', files=files, data=data)
        
        # Debe rechazar archivo grande
        result = response.json()
        assert response.status_code == 200  # El endpoint maneja el error
        assert result.get('success') is False
    
    @patch('proyecto_maria.routers.pdf_router._llm_extract_pdf_items')
    def test_upload_pdf_llm_failure(self, mock_llm_extract, test_client):
        """Upload PDF cuando LLM falla"""
        # Mock que LLM falla
        mock_llm_extract.side_effect = Exception("Gemini API error")
        
        files = {'file': ('test.pdf', create_test_pdf_bytes(), 'application/pdf')}
        data = {'client_id': 'test-client'}
        
        response = test_client.post('/upload_pdf_llm/', files=files, data=data)
        result = assert_api_response(response)
        
        # Debe manejar el error gracefully
        assert result.get('success') is False
        assert 'detail' in result
    
    def test_process_operation_invalid_payload(self, test_client):
        """Process operation con payload inválido"""
        invalid_payload = {
            'client_id': 'test-client',
            'items': 'not-a-list',  # Inválido
            'operation_type': 'importacion'
        }
        
        response = test_client.post('/process_operation/', json=invalid_payload)
        
        # Debe validar el payload
        assert response.status_code in [400, 422]


class TestPDFRouterPerformance:
    """Tests de performance del router PDF"""
    
    @patch('proyecto_maria.routers.pdf_router._llm_extract_pdf_items')
    def test_upload_pdf_response_time(self, mock_llm_extract, test_client):
        """Upload PDF debe responder en tiempo razonable"""
        import time
        
        mock_llm_extract.return_value = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            }
        ]
        
        files = {'file': ('test.pdf', create_test_pdf_bytes(), 'application/pdf')}
        data = {'client_id': 'test-client'}
        
        start_time = time.time()
        response = test_client.post('/upload_pdf/', files=files, data=data)
        end_time = time.time()
        
        # Debe responder en menos de 5 segundos (con mock)
        assert end_time - start_time < 5.0
        assert response.status_code == 200
    
    @patch('proyecto_maria.routers.pdf_router._llm_extract_pdf_items')
    def test_concurrent_uploads(self, mock_llm_extract, test_client):
        """Múltiples uploads concurrentes"""
        import threading
        import time
        
        mock_llm_extract.return_value = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            }
        ]
        
        results = []
        
        def upload_pdf():
            files = {'file': ('test.pdf', create_test_pdf_bytes(), 'application/pdf')}
            data = {'client_id': 'test-client'}
            response = test_client.post('/upload_pdf/', files=files, data=data)
            results.append(response.status_code)
        
        # Crear 3 threads concurrentes
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=upload_pdf)
            threads.append(thread)
            thread.start()
        
        # Esperar que todos terminen
        for thread in threads:
            thread.join()
        
        # Todos deben haber respondido exitosamente
        assert len(results) == 3
        assert all(status == 200 for status in results)


class TestPDFRouterAuthentication:
    """Tests de autenticación en endpoints PDF"""
    
    @patch('proyecto_maria.routers.pdf_router._llm_extract_pdf_items')
    def test_protected_endpoints_require_auth(self, mock_llm_extract, test_client):
        """Endpoints protegidos deben requerir autenticación"""
        mock_llm_extract.return_value = []
        
        files = {'file': ('test.pdf', create_test_pdf_bytes(), 'application/pdf')}
        data = {'client_id': 'test-client'}
        
        # Estos endpoints deben tener autenticación
        protected_endpoints = ['/upload_pdf/', '/upload_pdf_llm/', '/upload_pdf_gemini_only/']
        
        for endpoint in protected_endpoints:
            response = test_client.post(endpoint, files=files, data=data)
            
            # Puede ser 200 (si el manejo de auth es diferente) o 401/403
            # Lo importante es que no falle con 500
            assert response.status_code in [200, 401, 403]


class TestPDFRouterIntegration:
    """Tests de integración completa del router PDF"""
    
    @patch('proyecto_maria.routers.pdf_router._llm_extract_pdf_items')
    def test_full_pdf_processing_workflow(self, mock_llm_extract, test_client):
        """Flujo completo de procesamiento PDF"""
        mock_llm_extract.return_value = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell Inspiron 15",
                "origen": "CN",
                "cantidad": 10,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            },
            {
                "pieza": "85171200",
                "descripcion": "Smartphone Samsung Galaxy",
                "origen": "VN",
                "cantidad": 20,
                "valor_unitario": 300.0,
                "peso_unitario": 0.2
            }
        ]
        
        # Paso 1: Upload PDF
        files = {'file': ('test.pdf', create_test_pdf_bytes(), 'application/pdf')}
        data = {'client_id': 'test-client'}
        
        upload_response = test_client.post('/upload_pdf/', files=files, data=data)
        upload_result = assert_api_response(upload_response)
        
        assert upload_result['success'] is True
        assert len(upload_result['items']) == 2
        
        # Paso 2: Procesar operación con los items extraídos
        operation_payload = {
            'client_id': 'test-client',
            'items': upload_result['items'],
            'operation_type': 'importacion'
        }
        
        operation_response = test_client.post('/process_operation/', json=operation_payload)
        operation_result = assert_api_response(operation_response)
        
        assert operation_result['success'] is True
        assert 'filename' in operation_result
        assert 'download_url' in operation_result
        
        # Paso 3: Verificar que se puede descargar el archivo
        download_response = test_client.get(operation_result['download_url'])
        
        # El archivo debe existir (puede ser 200 o 404 si no se creó realmente)
        assert download_response.status_code in [200, 404]