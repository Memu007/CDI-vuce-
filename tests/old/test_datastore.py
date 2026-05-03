"""
Tests para DataStore unificado - Componente crítico del proyecto MARIA
"""
import pytest
import os
import json
from unittest.mock import patch, Mock

from proyecto_maria.core.datastore import DataStore, InMemoryBackend, PostgreSQLBackend
from tests.conftest import (
    sample_client_data, 
    sample_items, 
    column_mapping_data,
    assert_valid_item
)


class TestDataStoreInitialization:
    """Tests de inicialización de DataStore"""
    
    def test_in_memory_fallback(self, cleanup_env):
        """DataStore debe usar in-memory cuando no hay DATABASE_URL"""
        with patch.dict(os.environ, {'DATABASE_URL': ''}):
            store = DataStore()
            assert not store.using_postgres
            assert isinstance(store._backend, InMemoryBackend)
            assert store.user_id is not None
    
    def test_postgresql_backend_fails_to_in_memory(self, cleanup_env):
        """DataStore debe fallback a in-memory si PostgreSQL falla"""
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://invalid'}):
            store = DataStore()
            assert not store.using_postgres
            assert isinstance(store._backend, InMemoryBackend)
    
    @patch('proyecto_maria.core.datastore.psycopg.connect')
    def test_postgresql_backend_success(self, mock_connect, cleanup_env):
        """DataStore debe usar PostgreSQL cuando puede conectar"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test'}):
            store = DataStore()
            assert store.using_postgres
            assert isinstance(store._backend, PostgreSQLBackend)


class TestClientOperations:
    """Tests de operaciones de clientes - CRUD completo"""
    
    def test_list_clients_empty(self, mock_datastore):
        """Listar clientes cuando no hay ninguno"""
        clients = mock_datastore.list_clients()
        assert isinstance(clients, list)
        # Debe tener clientes demo por defecto
        assert len(clients) >= 3
    
    def test_create_client(self, mock_datastore, sample_client_data):
        """Crear un nuevo cliente"""
        client = mock_datastore.create_client(sample_client_data)
        
        assert 'id' in client
        assert client['nombre'] == sample_client_data['nombre']
        assert client['email'] == sample_client_data['email']
        assert client['favorito'] is False  # Por defecto
    
    def test_get_client_existing(self, mock_datastore, sample_client_data):
        """Obtener un cliente existente"""
        created = mock_datastore.create_client(sample_client_data)
        retrieved = mock_datastore.get_client(created['id'])
        
        assert retrieved is not None
        assert retrieved['id'] == created['id']
        assert retrieved['nombre'] == sample_client_data['nombre']
    
    def test_get_client_nonexistent(self, mock_datastore):
        """Obtener un cliente que no existe"""
        client = mock_datastore.get_client('nonexistent-id')
        assert client is None
    
    def test_update_client(self, mock_datastore, sample_client_data):
        """Actualizar un cliente existente"""
        created = mock_datastore.create_client(sample_client_data)
        
        updated_data = {
            'nombre': 'Empresa Actualizada S.A.',
            'email': 'actualizado@test.com',
            'telefono': '011-9999-8888',
            'direccion': 'Nueva Dirección 456',
            'notas': 'Notas actualizadas'
        }
        
        updated = mock_datastore.update_client(created['id'], updated_data)
        
        assert updated['id'] == created['id']
        assert updated['nombre'] == 'Empresa Actualizada S.A.'
        assert updated['email'] == 'actualizado@test.com'
    
    def test_delete_client(self, mock_datastore, sample_client_data):
        """Eliminar un cliente existente"""
        created = mock_datastore.create_client(sample_client_data)
        client_id = created['id']
        
        # Eliminar
        result = mock_datastore.delete_client(client_id)
        assert result is True
        
        # Verificar que no existe
        deleted = mock_datastore.get_client(client_id)
        assert deleted is None
    
    def test_set_favorite(self, mock_datastore, sample_client_data):
        """Marcar cliente como favorito"""
        created = mock_datastore.create_client(sample_client_data)
        client_id = created['id']
        
        # Marcar como favorito
        result = mock_datastore.set_favorite(client_id, True)
        assert result is True
        
        # Verificar
        client = mock_datastore.get_client(client_id)
        assert client['favorito'] is True
        
        # Desmarcar
        result = mock_datastore.set_favorite(client_id, False)
        assert result is True
        
        client = mock_datastore.get_client(client_id)
        assert client['favorito'] is False
    
    def test_get_clients_alias(self, mock_datastore):
        """Verificar que get_clients es alias de list_clients"""
        list_result = mock_datastore.list_clients()
        get_result = mock_datastore.get_clients()
        
        assert list_result == get_result


class TestColumnMapping:
    """Tests de mapeo de columnas - Funcionalidad crítica que causaba bugs"""
    
    def test_get_column_mapping_empty(self, mock_datastore):
        """Obtener mapeo de columnas cuando no hay ninguno"""
        mapping = mock_datastore.get_column_mapping('test-client')
        assert isinstance(mapping, dict)
        assert len(mapping) == 0
    
    def test_set_column_mapping(self, mock_datastore, column_mapping_data):
        """Establecer mapeo de columnas"""
        client_id = 'test-client'
        
        result = mock_datastore.set_column_mapping(client_id, column_mapping_data)
        assert result is True
        
        # Verificar que se guardó
        mapping = mock_datastore.get_column_mapping(client_id)
        assert isinstance(mapping, dict)
        assert len(mapping) > 0
        
        # Verificar normalización (claves en minúscula)
        assert 'product code' in mapping or 'product code' in str(mapping).lower()
    
    def test_set_column_mapping_normalization(self, mock_datastore):
        """Verificar normalización de mapeo de columnas"""
        client_id = 'test-client'
        
        mapping_data = {
            'PRODUCT CODE': 'PIEZA',  # Mayúsculas
            'Description': 'DESCRIPCION',  # Mixto
            'Country ': 'origen',  # Espacio extra
            'quantity': 'CANTIDAD',  # Minúsculas
            'invalid_field': 'invalid_value',  # Inválido
            '': 'pieza',  # Vacío
        }
        
        result = mock_datastore.set_column_mapping(client_id, mapping_data)
        assert result is True
        
        mapping = mock_datastore.get_column_mapping(client_id)
        
        # Solo deben quedar campos válidos y normalizados
        assert len(mapping) <= 4  # Máximo 4 campos válidos
        
        # Verificar que los valores sean campos canónicos
        valid_values = {'pieza', 'descripcion', 'origen', 'cantidad', 'valor_unitario', 'peso_unitario'}
        for value in mapping.values():
            assert value in valid_values
    
    def test_column_mapping_persistence(self, mock_datastore, column_mapping_data):
        """Verificar que el mapeo persiste entre llamadas"""
        client_id = 'test-client'
        
        # Establecer mapeo
        mock_datastore.set_column_mapping(client_id, column_mapping_data)
        
        # Obtener en otra llamada
        mapping = mock_datastore.get_column_mapping(client_id)
        assert len(mapping) > 0


class TestOperations:
    """Tests de operaciones por cliente"""
    
    def test_add_operation(self, mock_datastore, sample_items):
        """Agregar una operación para un cliente"""
        client_id = 'test-client'
        
        payload = {
            'items': sample_items,
            'resumen': {
                'grupos': 2,
                'items': len(sample_items),
                'valor_total': sum(item['cantidad'] * item['valor_unitario'] for item in sample_items)
            }
        }
        
        operation = mock_datastore.add_operation(client_id, payload)
        
        assert 'operation_id' in operation
        assert 'fecha' in operation
        assert 'resumen' in operation
        assert 'items' in operation
        assert operation['items'] == sample_items
    
    def test_get_operations_by_client_empty(self, mock_datastore):
        """Obtener operaciones de cliente sin operaciones"""
        operations = mock_datastore.get_operations_by_client('nonexistent-client')
        assert isinstance(operations, list)
        assert len(operations) == 0
    
    def test_get_operations_by_client_with_operations(self, mock_datastore, sample_items):
        """Obtener operaciones de cliente con operaciones"""
        client_id = 'test-client'
        
        # Agregar operación
        payload = {'items': sample_items}
        mock_datastore.add_operation(client_id, payload)
        
        # Obtener operaciones
        operations = mock_datastore.get_operations_by_client(client_id)
        
        assert isinstance(operations, list)
        assert len(operations) >= 1
        
        operation = operations[0]
        assert 'operation_id' in operation
        assert 'fecha' in operation
        assert 'resumen' in operation


class TestNCMNotes:
    """Tests de notas NCM"""
    
    def test_get_ncm_notes_empty(self, mock_datastore):
        """Obtener notas de NCM cuando no hay ninguna"""
        notes = mock_datastore.get_ncm_notes('84713010')
        assert isinstance(notes, list)
        assert len(notes) == 0
    
    def test_add_ncm_note(self, mock_datastore):
        """Agregar una nota NCM"""
        ncm = '84713010'
        note = 'Nota de prueba para NCM'
        client_id = 'test-client'
        
        result = mock_datastore.add_ncm_note(ncm, note, client_id)
        assert result is True
        
        # Verificar que se guardó
        notes = mock_datastore.get_ncm_notes(ncm)
        assert isinstance(notes, list)
        assert len(notes) >= 1
        assert note in notes
    
    def test_get_ncm_notes_with_notes(self, mock_datastore):
        """Obtener notas de NCM cuando existen notas"""
        ncm = '84713010'
        notes_data = ['Nota 1', 'Nota 2', 'Nota 3']
        
        # Agregar notas
        for note in notes_data:
            mock_datastore.add_ncm_note(ncm, note)
        
        # Obtener notas
        notes = mock_datastore.get_ncm_notes(ncm)
        
        assert isinstance(notes, list)
        assert len(notes) >= len(notes_data)
        
        for note in notes_data:
            assert note in notes


class TestMetricsAndExport:
    """Tests de métricas y exportación"""
    
    def test_compute_metrics_empty_client(self, mock_datastore):
        """Calcular métricas para cliente sin operaciones"""
        metrics = mock_datastore.compute_metrics('nonexistent-client')
        
        assert isinstance(metrics, dict)
        assert 'total_operaciones' in metrics
        assert 'total_items' in metrics
        assert 'valor_total' in metrics
        assert 'promedio_items_por_operacion' in metrics
        assert 'ultimo_movimiento' in metrics
        
        assert metrics['total_operaciones'] == 0
        assert metrics['total_items'] == 0
        assert metrics['valor_total'] == 0.0
    
    def test_compute_metrics_with_operations(self, mock_datastore, sample_items):
        """Calcular métricas para cliente con operaciones"""
        client_id = 'test-client'
        
        # Agregar operación
        payload = {'items': sample_items}
        mock_datastore.add_operation(client_id, payload)
        
        # Calcular métricas
        metrics = mock_datastore.compute_metrics(client_id)
        
        assert isinstance(metrics, dict)
        assert metrics['total_operaciones'] >= 1
        assert metrics['total_items'] >= len(sample_items)
        assert metrics['valor_total'] > 0
    
    def test_build_csv_empty(self, mock_datastore):
        """Construir CSV para cliente sin operaciones"""
        csv_content = mock_datastore.build_csv('nonexistent-client')
        
        assert isinstance(csv_content, str)
        # Debe tener encabezados
        assert 'operation_id' in csv_content
        assert 'fecha' in csv_content
        assert 'pieza' in csv_content
    
    def test_build_csv_with_operations(self, mock_datastore, sample_items):
        """Construir CSV para cliente con operaciones"""
        client_id = 'test-client'
        
        # Agregar operación
        payload = {'items': sample_items}
        mock_datastore.add_operation(client_id, payload)
        
        # Construir CSV
        csv_content = mock_datastore.build_csv(client_id)
        
        assert isinstance(csv_content, str)
        assert len(csv_content) > 0
        
        # Debe contener los datos de los items
        lines = csv_content.strip().split('\n')
        assert len(lines) >= 2  # Encabezado + al menos 1 fila de datos


class TestDataStoreBackendSelection:
    """Tests de selección de backend"""
    
    def test_using_postgres_property(self, cleanup_env):
        """Verificar propiedad using_postgres"""
        # Test in-memory
        with patch.dict(os.environ, {'DATABASE_URL': ''}):
            store = DataStore()
            assert store.using_postgres is False
        
        # Test PostgreSQL (mock)
        with patch('proyecto_maria.core.datastore.psycopg.connect') as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn
            
            with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://test'}):
                store = DataStore()
                assert store.using_postgres is True


class TestEdgeCases:
    """Tests de casos extremos y errores"""
    
    def test_create_client_with_empty_data(self, mock_datastore):
        """Crear cliente con datos vacíos"""
        client = mock_datastore.create_client({})
        
        assert 'id' in client
        assert client.get('nombre', '') == ''
        assert client.get('email', '') == ''
        assert client['favorito'] is False
    
    def test_update_nonexistent_client(self, mock_datastore):
        """Actualizar cliente que no existe"""
        with pytest.raises((KeyError, Exception)):
            mock_datastore.update_client('nonexistent-id', {'nombre': 'Test'})
    
    def test_set_column_mapping_with_invalid_data(self, mock_datastore):
        """Establecer mapeo con datos inválidos"""
        client_id = 'test-client'
        
        # Datos completamente inválidos
        invalid_mapping = {
            '': '',
            'invalid': 'invalid_value'
        }
        
        result = mock_datastore.set_column_mapping(client_id, invalid_mapping)
        assert result is True  # No debe fallar
        
        # Pero debe quedar vacío
        mapping = mock_datastore.get_column_mapping(client_id)
        assert len(mapping) == 0
    
    def test_add_operation_with_empty_items(self, mock_datastore):
        """Agregar operación con items vacíos"""
        client_id = 'test-client'
        
        payload = {
            'items': [],
            'resumen': {'items': 0, 'valor_total': 0}
        }
        
        operation = mock_datastore.add_operation(client_id, payload)
        
        assert 'operation_id' in operation
        assert operation['items'] == []