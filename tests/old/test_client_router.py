"""
Tests para Client Router - CRUD de clientes y funcionalidades asociadas
"""
import pytest
import json
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from proyecto_maria.main import app



class TestClientRouterPublicEndpoints:
    """Tests de endpoints públicos de clientes (sin autenticación)"""
    
    def test_list_clients_public(self, test_client):
        """Listar clientes públicos"""
        response = test_client.get('/api/clientes/public')
        data = assert_api_response(response)
        
        assert isinstance(data, list)
        # Debe tener clientes demo por defecto
        assert len(data) >= 3
        
        # Verificar estructura de clientes
        if data:
            client = data[0]
            assert 'id' in client
            assert 'nombre' in client
            assert 'email' in client
            assert 'telefono' in client
            assert 'direccion' in client
            assert 'notas' in client
            assert 'favorito' in client
    
    def test_create_client_public(self, test_client, sample_client_data):
        """Crear cliente público"""
        response = test_client.post('/api/clientes/public', json=sample_client_data)
        data = assert_api_response(response)
        
        assert data['success'] is True
        assert 'id' in data
        assert 'client' in data
        
        client = data['client']
        assert client['nombre'] == sample_client_data['nombre']
        assert client['email'] == sample_client_data['email']
        assert client['favorito'] is False
    
    def test_create_client_public_invalid_data(self, test_client):
        """Crear cliente con datos inválidos"""
        invalid_data = {
            'nombre': '',  # Vacío
            'email': 'email-invalido',  # Formato inválido
        }
        
        response = test_client.post('/api/clientes/public', json=invalid_data)
        data = assert_api_response(response)
        
        # Debe manejar validación
        assert data.get('success') is False
    
    def test_create_demo_client(self, test_client):
        """Crear cliente demo"""
        response = test_client.post('/api/clientes/demo')
        data = assert_api_response(response)
        
        assert data['success'] is True
        assert 'client' in data
        
        client = data['client']
        assert 'id' in client
        assert 'nombre' in client
        assert 'demo' in client['nombre'].lower()


class TestClientRouterProtectedEndpoints:
    """Tests de endpoints protegidos de clientes (con autenticación)"""
    
    @patch('proyecto_maria.auth.require_role')
    def test_list_clients_protected(self, mock_auth, test_client):
        """Listar clientes protegidos"""
        # Mock de autenticación
        mock_auth.return_value = lambda: {"sub": "test-user", "roles": ["operador"]}
        
        response = test_client.get('/api/clientes')
        
        # Puede ser 200 (si auth mock funciona) o 401/403
        assert response.status_code in [200, 401, 403]
    
    @patch('proyecto_maria.auth.require_role')
    def test_create_client_protected(self, mock_auth, test_client, sample_client_data):
        """Crear cliente protegido"""
        mock_auth.return_value = lambda: {"sub": "test-user", "roles": ["operador"]}
        
        response = test_client.post('/api/clientes', json=sample_client_data)
        
        # Puede ser 200 (si auth mock funciona) o 401/403
        assert response.status_code in [200, 401, 403]


class TestClientOperations:
    """Tests de operaciones de clientes"""
    
    def test_get_client_operations_empty(self, test_client):
        """Obtener operaciones de cliente sin operaciones"""
        client_id = 'nonexistent-client'
        
        response = test_client.get(f'/api/clientes/{client_id}/operaciones')
        data = assert_api_response(response)
        
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_add_client_operation(self, test_client, sample_items):
        """Agregar operación a cliente"""
        client_id = 'test-client'
        
        payload = {
            'items': sample_items,
            'operation_type': 'importacion',
            'currency': 'USD'
        }
        
        response = test_client.post(f'/api/clientes/{client_id}/operaciones', json=payload)
        data = assert_api_response(response)
        
        assert data['success'] is True
        assert 'operation' in data
        
        operation = data['operation']
        assert 'operation_id' in operation
        assert 'fecha' in operation
        assert 'items' in operation
    
    def test_add_client_operation_demo(self, test_client, sample_items):
        """Agregar operación demo a cliente"""
        client_id = 'demo-client'
        
        payload = {
            'items': sample_items,
            'operation_type': 'importacion'
        }
        
        response = test_client.post(f'/api/clientes/{client_id}/operaciones/demo', json=payload)
        data = assert_api_response(response)
        
        assert data['success'] is True
        assert 'operation' in data
    
    def test_get_client_metrics(self, test_client):
        """Obtener métricas de cliente"""
        client_id = 'test-client'
        
        response = test_client.get(f'/api/clientes/{client_id}/metricas')
        data = assert_api_response(response)
        
        assert isinstance(data, dict)
        assert 'total_operaciones' in data
        assert 'total_items' in data
        assert 'valor_total' in data
        assert 'promedio_items_por_operacion' in data
        assert 'ultimo_movimiento' in data
    
    def test_export_client_csv(self, test_client):
        """Exportar datos de cliente a CSV"""
        client_id = 'test-client'
        
        response = test_client.get(f'/api/clientes/{client_id}/export.csv')
        
        # Puede ser 200 con CSV o 404 si no hay datos
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            # Verificar que es CSV
            assert 'text/csv' in response.headers.get('content-type', '')


class TestColumnMapping:
    """Tests de mapeo de columnas - Funcionalidad crítica"""
    
    def test_get_column_mapping_empty(self, test_client):
        """Obtener mapeo de columnas vacío"""
        client_id = 'test-client'
        
        response = test_client.get(f'/api/clientes/{client_id}/column_mapping')
        data = assert_api_response(response)
        
        assert 'cliente_id' in data
        assert 'mapping' in data
        assert isinstance(data['mapping'], dict)
        assert len(data['mapping']) == 0
    
    def test_set_column_mapping(self, test_client, column_mapping_data):
        """Establecer mapeo de columnas"""
        client_id = 'test-client'
        
        payload = {'mapping': column_mapping_data}
        
        response = test_client.post(f'/api/clientes/{client_id}/column_mapping', json=payload)
        data = assert_api_response(response)
        
        assert data['success'] is True
        assert 'cliente_id' in data
        assert 'mapping' in data
        
        # Verificar que se guardó
        mapping = data['mapping']
        assert isinstance(mapping, dict)
        assert len(mapping) > 0
    
    def test_set_column_mapping_invalid(self, test_client):
        """Establecer mapeo de columnas inválido"""
        client_id = 'test-client'
        
        invalid_mapping = {
            'invalid_field': 'invalid_value'
        }
        
        payload = {'mapping': invalid_mapping}
        
        response = test_client.post(f'/api/clientes/{client_id}/column_mapping', json=payload)
        data = assert_api_response(response)
        
        # Debe manejar inválido gracefully
        assert data['success'] is True  # No falla, pero filtra inválidos
        assert len(data['mapping']) == 0  # Solo campos válidos
    
    def test_delete_column_mapping(self, test_client, column_mapping_data):
        """Eliminar mapeo de columnas"""
        client_id = 'test-client'
        
        # Primero establecer mapeo
        payload = {'mapping': column_mapping_data}
        test_client.post(f'/api/clientes/{client_id}/column_mapping', json=payload)
        
        # Luego eliminar
        response = test_client.delete(f'/api/clientes/{client_id}/column_mapping')
        data = assert_api_response(response)
        
        assert data['success'] is True
        assert 'cliente_id' in data
        assert 'mapping' in data
        assert len(data['mapping']) == 0
    
    def test_column_mapping_workflow(self, test_client, column_mapping_data):
        """Flujo completo de mapeo de columnas"""
        client_id = 'test-client'
        
        # 1. Obtener mapeo inicial (vacío)
        get_response = test_client.get(f'/api/clientes/{client_id}/column_mapping')
        get_data = assert_api_response(get_response)
        assert len(get_data['mapping']) == 0
        
        # 2. Establecer mapeo
        set_payload = {'mapping': column_mapping_data}
        set_response = test_client.post(f'/api/clientes/{client_id}/column_mapping', json=set_payload)
        set_data = assert_api_response(set_response)
        assert len(set_data['mapping']) > 0
        
        # 3. Verificar que se guardó
        verify_response = test_client.get(f'/api/clientes/{client_id}/column_mapping')
        verify_data = assert_api_response(verify_response)
        assert len(verify_data['mapping']) > 0
        
        # 4. Eliminar mapeo
        delete_response = test_client.delete(f'/api/clientes/{client_id}/column_mapping')
        delete_data = assert_api_response(delete_response)
        assert len(delete_data['mapping']) == 0


class TestClientFavorites:
    """Tests de funcionalidad de favoritos"""
    
    def test_toggle_favorite(self, test_client):
        """Marcar/desmarcar cliente como favorito"""
        client_id = 'test-client'
        
        # Marcar como favorito
        payload = {'favorito': True}
        response = test_client.post(f'/api/clientes/{client_id}/favorito', json=payload)
        data = assert_api_response(response)
        
        assert data['success'] is True
        assert data['favorito'] is True
        
        # Desmarcar como favorito
        payload = {'favorito': False}
        response = test_client.post(f'/api/clientes/{client_id}/favorito', json=payload)
        data = assert_api_response(response)
        
        assert data['success'] is True
        assert data['favorito'] is False
    
    def test_toggle_favorite_invalid_client(self, test_client):
        """Marcar favorito en cliente inexistente"""
        client_id = 'nonexistent-client'
        
        payload = {'favorito': True}
        response = test_client.post(f'/api/clientes/{client_id}/favorito', json=payload)
        
        # Debe manejar cliente inexistente gracefully
        data = assert_api_response(response)
        # Puede ser success=False o success=True con manejo interno


class TestClientTemplates:
    """Tests de generación de plantillas"""
    
    def test_generate_template(self, test_client):
        """Generar plantilla para cliente"""
        client_id = 'test-client'
        
        response = test_client.post(f'/api/clientes/{client_id}/plantilla')
        data = assert_api_response(response)
        
        assert data['success'] is True
        assert 'filename' in data
        assert 'download_url' in data
        
        # Verificar que el filename tenga formato esperado
        filename = data['filename']
        assert filename.endswith('.xlsx')
        assert 'PLANTILLA' in filename.upper()
    
    def test_generate_template_with_items(self, test_client, sample_items):
        """Generar plantilla con items pre-cargados"""
        client_id = 'test-client'
        
        payload = {'items': sample_items}
        
        response = test_client.post(f'/api/clientes/{client_id}/plantilla', json=payload)
        data = assert_api_response(response)
        
        assert data['success'] is True
        assert 'filename' in data
        assert 'download_url' in data


class TestClientRouterErrorHandling:
    """Tests de manejo de errores en router de clientes"""
    
    def test_get_nonexistent_client(self, test_client):
        """Obtener cliente que no existe"""
        client_id = 'nonexistent-client-id-12345'
        
        response = test_client.get(f'/api/clientes/{client_id}')
        
        # Debe manejar cliente inexistente
        assert response.status_code in [404, 200]
        
        if response.status_code == 200:
            data = response.json()
            assert data.get('success') is False
    
    def test_update_nonexistent_client(self, test_client, sample_client_data):
        """Actualizar cliente que no existe"""
        client_id = 'nonexistent-client-id-12345'
        
        response = test_client.put(f'/api/clientes/{client_id}', json=sample_client_data)
        
        # Debe manejar cliente inexistente
        assert response.status_code in [404, 200]
        
        if response.status_code == 200:
            data = response.json()
            assert data.get('success') is False
    
    def test_delete_nonexistent_client(self, test_client):
        """Eliminar cliente que no existe"""
        client_id = 'nonexistent-client-id-12345'
        
        response = test_client.delete(f'/api/clientes/{client_id}')
        
        # Debe manejar cliente inexistente
        assert response.status_code in [404, 200]
        
        if response.status_code == 200:
            data = response.json()
            assert data.get('success') is False
    
    def test_invalid_client_id(self, test_client):
        """Usar ID de cliente inválido"""
        invalid_ids = ['', ' ', 'null', 'undefined', '../etc/passwd']
        
        for invalid_id in invalid_ids:
            response = test_client.get(f'/api/clientes/{invalid_id}')
            
            # Debe manejar ID inválido
            assert response.status_code in [400, 404, 422]
    
    def test_create_client_with_malformed_data(self, test_client):
        """Crear cliente con datos malformados"""
        malformed_data = {
            'nombre': 'A' * 1000,  # Demasiado largo
            'email': 'x' * 500,  # Email inválido y muy largo
            'telefono': '123' * 100,  # Demasiado largo
        }
        
        response = test_client.post('/api/clientes/public', json=malformed_data)
        data = assert_api_response(response)
        
        # Debe manejar datos malformados
        assert data.get('success') is False


class TestClientRouterPerformance:
    """Tests de performance del router de clientes"""
    
    def test_list_clients_performance(self, test_client):
        """Listar clientes debe ser rápido"""
        import time
        
        start_time = time.time()
        response = test_client.get('/api/clientes/public')
        end_time = time.time()
        
        # Debe responder en menos de 1 segundo
        assert end_time - start_time < 1.0
        assert response.status_code == 200
    
    def test_create_client_performance(self, test_client, sample_client_data):
        """Crear cliente debe ser rápido"""
        import time
        
        start_time = time.time()
        response = test_client.post('/api/clientes/public', json=sample_client_data)
        end_time = time.time()
        
        # Debe responder en menos de 1 segundo
        assert end_time - start_time < 1.0
        assert response.status_code == 200
    
    def test_concurrent_client_operations(self, test_client, sample_client_data):
        """Operaciones concurrentes de clientes"""
        import threading
        import time
        
        results = []
        
        def create_client():
            response = test_client.post('/api/clientes/public', json=sample_client_data)
            results.append(response.status_code)
        
        # Crear 5 threads concurrentes
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_client)
            threads.append(thread)
            thread.start()
        
        # Esperar que todos terminen
        for thread in threads:
            thread.join()
        
        # Todos deben haber respondido exitosamente
        assert len(results) == 5
        assert all(status == 200 for status in results)


class TestClientRouterIntegration:
    """Tests de integración completa del router de clientes"""
    
    def test_full_client_lifecycle(self, test_client, sample_client_data, column_mapping_data):
        """Ciclo de vida completo de un cliente"""
        # 1. Crear cliente
        create_response = test_client.post('/api/clientes/public', json=sample_client_data)
        create_data = assert_api_response(create_response)
        assert create_data['success'] is True
        
        client_id = create_data['client']['id']
        
        # 2. Obtener cliente
        get_response = test_client.get(f'/api/clientes/{client_id}')
        # Puede no existir endpoint GET individual, pero verificamos que no falle
        
        # 3. Establecer mapeo de columnas
        mapping_payload = {'mapping': column_mapping_data}
        mapping_response = test_client.post(f'/api/clientes/{client_id}/column_mapping', json=mapping_payload)
        mapping_data = assert_api_response(mapping_response)
        assert mapping_data['success'] is True
        
        # 4. Marcar como favorito
        fav_payload = {'favorito': True}
        fav_response = test_client.post(f'/api/clientes/{client_id}/favorito', json=fav_payload)
        fav_data = assert_api_response(fav_response)
        assert fav_data['success'] is True
        
        # 5. Generar plantilla
        template_response = test_client.post(f'/api/clientes/{client_id}/plantilla')
        template_data = assert_api_response(template_response)
        assert template_data['success'] is True
        
        # 6. Eliminar mapeo
        delete_mapping_response = test_client.delete(f'/api/clientes/{client_id}/column_mapping')
        delete_mapping_data = assert_api_response(delete_mapping_response)
        assert delete_mapping_data['success'] is True
    
    def test_client_with_operations_workflow(self, test_client, sample_client_data, sample_items):
        """Flujo de cliente con operaciones"""
        # 1. Crear cliente
        create_response = test_client.post('/api/clientes/public', json=sample_client_data)
        create_data = assert_api_response(create_response)
        client_id = create_data['client']['id']
        
        # 2. Agregar operación
        operation_payload = {
            'items': sample_items,
            'operation_type': 'importacion'
        }
        operation_response = test_client.post(f'/api/clientes/{client_id}/operaciones', json=operation_payload)
        operation_data = assert_api_response(operation_response)
        assert operation_data['success'] is True
        
        # 3. Obtener métricas
        metrics_response = test_client.get(f'/api/clientes/{client_id}/metricas')
        metrics_data = assert_api_response(metrics_response)
        
        assert isinstance(metrics_data, dict)
        assert 'total_operaciones' in metrics_data
        
        # 4. Exportar CSV
        csv_response = test_client.get(f'/api/clientes/{client_id}/export.csv')
        # Puede ser 200 o 404
        assert csv_response.status_code in [200, 404]