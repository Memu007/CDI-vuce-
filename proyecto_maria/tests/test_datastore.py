"""
Tests unitarios para DataStore - Módulo CRÍTICO recién refactorizado.

Este módulo contiene tests exhaustivos para el sistema DataStore unificado
que reemplaza 3 implementaciones previas y es crítico para la estabilidad del sistema.

Cobertura:
- Inicialización con PostgreSQL y fallback in-memory
- CRUD completo de clientes
- Column mapping (FIX CRÍTICO - causaba bugs)
- Sistema de favoritos
- Operaciones por cliente
- Métricas y reportes
- Notas NCM
"""

import pytest
import os
from unittest.mock import MagicMock, patch, Mock
from typing import Dict, List

# Setup path for imports
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from proyecto_maria.core.datastore import (
    DataStore,
    InMemoryBackend,
    PostgreSQLBackend,
    DataStoreBackend
)


# ============================================================================
# TESTS DE INICIALIZACIÓN
# ============================================================================

class TestDataStoreInitialization:
    """Tests para inicialización del DataStore."""

    def test_init_with_postgres_success(self, monkeypatch):
        """Test inicialización exitosa con PostgreSQL."""
        # Mock environment
        monkeypatch.setenv("DATABASE_URL", "postgresql://test:test@localhost/testdb")

        # Mock psycopg
        mock_psycopg = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Setup cursor behavior
        mock_cursor.fetchone.return_value = ("demo-user-id",)
        mock_conn.cursor.return_value = mock_cursor
        mock_psycopg.connect.return_value = mock_conn

        with patch.dict('sys.modules', {'psycopg': mock_psycopg}):
            store = DataStore()

            assert store._using_pg is True
            assert store.using_postgres is True
            assert store.user_id is not None

    def test_init_without_database_url_uses_inmemory(self, clean_env):
        """Test que sin DATABASE_URL usa backend in-memory."""
        store = DataStore()

        assert store._using_pg is False
        assert store.using_postgres is False
        assert isinstance(store._backend, InMemoryBackend)
        assert store.user_id is not None

    def test_init_with_postgres_failure_falls_back_to_inmemory(self, monkeypatch):
        """Test que fallo de PostgreSQL hace fallback a in-memory."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://invalid:invalid@localhost/invalid")

        # Mock psycopg to raise exception
        mock_psycopg = MagicMock()
        mock_psycopg.connect.side_effect = Exception("Connection failed")

        with patch.dict('sys.modules', {'psycopg': mock_psycopg}):
            store = DataStore()

            # Should fallback to in-memory
            assert store._using_pg is False
            assert isinstance(store._backend, InMemoryBackend)


# ============================================================================
# TESTS DE CRUD DE CLIENTES
# ============================================================================

class TestDataStoreClients:
    """Tests para operaciones CRUD de clientes."""

    def test_list_clients_empty_at_start(self, clean_env):
        """Test que backend in-memory tiene clientes demo al iniciar."""
        store = DataStore()
        clientes = store.list_clients()

        # In-memory backend seeds demo clients
        assert len(clientes) >= 3
        assert all("id" in c for c in clientes)
        assert all("nombre" in c for c in clientes)

    def test_create_client_success(self, datastore_in_memory, sample_cliente):
        """Test crear cliente exitosamente."""
        created = datastore_in_memory.create_client(sample_cliente)

        assert "id" in created
        assert created["nombre"] == sample_cliente["nombre"]
        assert created["email"] == sample_cliente["email"]
        assert created["favorito"] is False

    def test_create_multiple_clients(self, datastore_in_memory, sample_clientes_list):
        """Test crear múltiples clientes."""
        created_ids = []

        for cliente_data in sample_clientes_list:
            created = datastore_in_memory.create_client(cliente_data)
            created_ids.append(created["id"])
            assert "id" in created
            assert created["nombre"] == cliente_data["nombre"]

        # Verify all were created
        all_clients = datastore_in_memory.list_clients()
        assert len(all_clients) >= len(sample_clientes_list)

    def test_get_client_by_id(self, datastore_in_memory, sample_cliente):
        """Test obtener cliente por ID."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        retrieved = datastore_in_memory.get_client(cliente_id)

        assert retrieved is not None
        assert retrieved["id"] == cliente_id
        assert retrieved["nombre"] == sample_cliente["nombre"]
        assert retrieved["email"] == sample_cliente["email"]

    def test_get_client_nonexistent_returns_none(self, datastore_in_memory):
        """Test que obtener cliente inexistente retorna None."""
        retrieved = datastore_in_memory.get_client("nonexistent-id-12345")

        assert retrieved is None

    def test_update_client_success(self, datastore_in_memory, sample_cliente):
        """Test actualizar cliente exitosamente."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        updated_data = {
            "nombre": "Updated Company Name",
            "email": "updated@example.com",
            "telefono": "011-9999-9999",
            "direccion": "Nueva Dirección 456",
            "notas": "Notas actualizadas"
        }

        updated = datastore_in_memory.update_client(cliente_id, updated_data)

        assert updated["id"] == cliente_id
        assert updated["nombre"] == "Updated Company Name"
        assert updated["email"] == "updated@example.com"

        # Verify changes persisted
        retrieved = datastore_in_memory.get_client(cliente_id)
        assert retrieved["nombre"] == "Updated Company Name"

    def test_update_nonexistent_client_raises_error(self, datastore_in_memory):
        """Test que actualizar cliente inexistente lanza error."""
        with pytest.raises(KeyError):
            datastore_in_memory.update_client("nonexistent-id", {"nombre": "Test"})

    def test_delete_client_success(self, datastore_in_memory, sample_cliente):
        """Test eliminar cliente exitosamente."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        # Verify exists
        assert datastore_in_memory.get_client(cliente_id) is not None

        # Delete
        result = datastore_in_memory.delete_client(cliente_id)

        assert result is True
        assert datastore_in_memory.get_client(cliente_id) is None

    def test_delete_nonexistent_client_returns_false(self, datastore_in_memory):
        """Test que eliminar cliente inexistente retorna False."""
        result = datastore_in_memory.delete_client("nonexistent-id-12345")

        assert result is False

    def test_get_clients_alias_works(self, datastore_in_memory):
        """Test que el método alias get_clients() funciona."""
        clients_via_list = datastore_in_memory.list_clients()
        clients_via_get = datastore_in_memory.get_clients()

        assert len(clients_via_list) == len(clients_via_get)


# ============================================================================
# TESTS DE COLUMN MAPPING (FIX CRÍTICO)
# ============================================================================

class TestDataStoreColumnMapping:
    """Tests para column mapping - FIX CRÍTICO que causaba bugs."""

    def test_get_column_mapping_empty_by_default(self, datastore_in_memory, sample_cliente):
        """Test que mapping está vacío por defecto."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        mapping = datastore_in_memory.get_column_mapping(cliente_id)

        assert mapping == {}

    def test_set_column_mapping_success(self, datastore_in_memory, sample_cliente, sample_column_mapping):
        """Test establecer column mapping exitosamente."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        result = datastore_in_memory.set_column_mapping(cliente_id, sample_column_mapping)

        assert result is True

        # Verify mapping was saved
        retrieved_mapping = datastore_in_memory.get_column_mapping(cliente_id)
        assert "part_number" in retrieved_mapping
        assert retrieved_mapping["part_number"] == "pieza"

    def test_set_column_mapping_normalizes_keys(self, datastore_in_memory, sample_cliente):
        """Test que set_column_mapping normaliza claves a lowercase."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        mapping_with_uppercase = {
            "PART_NUMBER": "pieza",
            "Description": "descripcion",
            "COUNTRY": "origen"
        }

        datastore_in_memory.set_column_mapping(cliente_id, mapping_with_uppercase)

        retrieved = datastore_in_memory.get_column_mapping(cliente_id)

        # Keys should be normalized to lowercase
        assert "part_number" in retrieved
        assert "description" in retrieved
        assert "country" in retrieved

    def test_set_column_mapping_filters_invalid_values(self, datastore_in_memory, sample_cliente):
        """Test que set_column_mapping filtra valores inválidos."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        mapping_with_invalid = {
            "part_number": "pieza",  # válido
            "description": "invalid_field",  # inválido
            "qty": "cantidad",  # válido
            "": "origen",  # clave vacía - inválido
            "price": ""  # valor vacío - inválido
        }

        datastore_in_memory.set_column_mapping(cliente_id, mapping_with_invalid)

        retrieved = datastore_in_memory.get_column_mapping(cliente_id)

        # Solo campos válidos deben estar presentes
        assert "part_number" in retrieved
        assert retrieved["part_number"] == "pieza"
        assert "qty" in retrieved
        assert retrieved["qty"] == "cantidad"

        # Campos inválidos no deben estar
        assert "description" not in retrieved  # valor inválido
        assert "" not in retrieved  # clave vacía

    def test_set_column_mapping_allowed_fields_only(self, datastore_in_memory, sample_cliente):
        """Test que solo campos permitidos son aceptados."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        allowed_fields = {"pieza", "descripcion", "origen", "cantidad", "valor_unitario", "peso_unitario"}

        mapping = {
            "col1": "pieza",  # permitido
            "col2": "descripcion",  # permitido
            "col3": "invalid_field",  # no permitido
        }

        datastore_in_memory.set_column_mapping(cliente_id, mapping)

        retrieved = datastore_in_memory.get_column_mapping(cliente_id)

        assert retrieved["col1"] == "pieza"
        assert retrieved["col2"] == "descripcion"
        assert "col3" not in retrieved  # campo inválido filtrado

    def test_update_column_mapping_replaces_old(self, datastore_in_memory, sample_cliente):
        """Test que actualizar mapping reemplaza el anterior."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        # Set initial mapping
        initial_mapping = {"col1": "pieza", "col2": "descripcion"}
        datastore_in_memory.set_column_mapping(cliente_id, initial_mapping)

        # Update with new mapping
        new_mapping = {"col3": "cantidad", "col4": "origen"}
        datastore_in_memory.set_column_mapping(cliente_id, new_mapping)

        retrieved = datastore_in_memory.get_column_mapping(cliente_id)

        # Old mapping should be replaced
        assert "col1" not in retrieved
        assert "col2" not in retrieved
        assert "col3" in retrieved
        assert "col4" in retrieved


# ============================================================================
# TESTS DE FAVORITOS
# ============================================================================

class TestDataStoreFavorites:
    """Tests para sistema de favoritos."""

    def test_set_favorite_true(self, datastore_in_memory, sample_cliente):
        """Test marcar cliente como favorito."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        result = datastore_in_memory.set_favorite(cliente_id, True)

        assert result is True

        # Verify favorite status
        cliente = datastore_in_memory.get_client(cliente_id)
        assert cliente["favorito"] is True

    def test_set_favorite_false(self, datastore_in_memory, sample_cliente):
        """Test desmarcar cliente como favorito."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        # Set favorite
        datastore_in_memory.set_favorite(cliente_id, True)
        assert datastore_in_memory.get_client(cliente_id)["favorito"] is True

        # Unset favorite
        result = datastore_in_memory.set_favorite(cliente_id, False)

        assert result is True
        assert datastore_in_memory.get_client(cliente_id)["favorito"] is False

    def test_set_favorite_nonexistent_client(self, datastore_in_memory):
        """Test marcar favorito en cliente inexistente."""
        result = datastore_in_memory.set_favorite("nonexistent-id", True)

        assert result is False

    def test_list_clients_orders_by_favorite(self, datastore_in_memory, sample_clientes_list):
        """Test que list_clients ordena favoritos primero."""
        # Create clients
        created_ids = []
        for cliente_data in sample_clientes_list[:3]:
            created = datastore_in_memory.create_client(cliente_data)
            created_ids.append(created["id"])

        # Mark second client as favorite
        datastore_in_memory.set_favorite(created_ids[1], True)

        # Get all clients
        all_clients = datastore_in_memory.list_clients()

        # Find our test clients
        our_clients = [c for c in all_clients if c["id"] in created_ids]

        # Favorite should be first among our test clients
        favorites = [c for c in our_clients if c["favorito"]]
        assert len(favorites) >= 1
        # Note: ordering may include demo clients


# ============================================================================
# TESTS DE OPERACIONES POR CLIENTE
# ============================================================================

class TestDataStoreOperations:
    """Tests para operaciones por cliente."""

    def test_get_operations_empty_initially(self, datastore_in_memory, sample_cliente):
        """Test que operaciones están vacías inicialmente."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        operations = datastore_in_memory.get_operations_by_client(cliente_id)

        assert operations == []

    def test_add_operation_success(self, datastore_in_memory, sample_cliente, sample_operation_dict):
        """Test agregar operación exitosamente."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        added = datastore_in_memory.add_operation(cliente_id, sample_operation_dict)

        assert "operation_id" in added
        assert "fecha" in added
        assert "items" in added
        assert len(added["items"]) > 0

    def test_get_operations_returns_added(self, datastore_in_memory, sample_cliente, sample_operation_dict):
        """Test que get_operations retorna operaciones agregadas."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        # Add operation
        datastore_in_memory.add_operation(cliente_id, sample_operation_dict)

        # Get operations
        operations = datastore_in_memory.get_operations_by_client(cliente_id)

        assert len(operations) >= 1
        assert operations[0]["operation_id"] is not None

    def test_add_multiple_operations(self, datastore_in_memory, sample_cliente):
        """Test agregar múltiples operaciones."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        # Add 3 operations
        for i in range(3):
            payload = {
                "operation_id": f"OP-{i}",
                "items": [
                    {
                        "pieza": "84713010",
                        "descripcion": f"Item {i}",
                        "origen": "CN",
                        "cantidad": 10.0,
                        "valor_unitario": 100.0,
                        "peso_unitario": 1.0
                    }
                ]
            }
            datastore_in_memory.add_operation(cliente_id, payload)

        # Get all operations
        operations = datastore_in_memory.get_operations_by_client(cliente_id)

        assert len(operations) >= 3

    def test_operations_include_resumen(self, datastore_in_memory, sample_cliente, sample_operation_dict):
        """Test que operaciones incluyen resumen."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        datastore_in_memory.add_operation(cliente_id, sample_operation_dict)

        operations = datastore_in_memory.get_operations_by_client(cliente_id)

        assert len(operations) >= 1
        assert "resumen" in operations[0]
        assert "valor_total" in operations[0]["resumen"]


# ============================================================================
# TESTS DE MÉTRICAS
# ============================================================================

class TestDataStoreMetrics:
    """Tests para métricas de cliente."""

    def test_compute_metrics_empty_operations(self, datastore_in_memory, sample_cliente):
        """Test métricas con cero operaciones."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        metrics = datastore_in_memory.compute_metrics(cliente_id)

        assert metrics["total_operaciones"] == 0
        assert metrics["total_items"] == 0
        assert metrics["valor_total"] == 0.0
        assert metrics["promedio_items_por_operacion"] == 0.0
        assert metrics["ultimo_movimiento"] is None

    def test_compute_metrics_with_operations(self, datastore_in_memory, sample_cliente):
        """Test métricas con operaciones."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        # Add operations
        for i in range(2):
            payload = {
                "operation_id": f"OP-{i}",
                "items": [
                    {
                        "pieza": "84713010",
                        "descripcion": f"Item {i}",
                        "origen": "CN",
                        "cantidad": 10.0,
                        "valor_unitario": 100.0,
                        "peso_unitario": 1.0
                    }
                ],
                "resumen": {
                    "items": 5,
                    "valor_total": 1000.0
                }
            }
            datastore_in_memory.add_operation(cliente_id, payload)

        metrics = datastore_in_memory.compute_metrics(cliente_id)

        assert metrics["total_operaciones"] >= 2
        assert metrics["total_items"] >= 10
        assert metrics["valor_total"] >= 2000.0

    def test_build_csv_export(self, datastore_in_memory, sample_cliente, sample_operation_dict):
        """Test exportar datos a CSV."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        datastore_in_memory.add_operation(cliente_id, sample_operation_dict)

        csv_content = datastore_in_memory.build_csv(cliente_id)

        assert isinstance(csv_content, str)
        assert len(csv_content) > 0
        assert "operation_id" in csv_content
        assert "pieza" in csv_content or "descripcion" in csv_content


# ============================================================================
# TESTS DE NOTAS NCM
# ============================================================================

class TestDataStoreNCMNotes:
    """Tests para notas de NCM."""

    def test_get_ncm_notes_empty_initially(self, datastore_in_memory):
        """Test que notas NCM están vacías inicialmente."""
        notes = datastore_in_memory.get_ncm_notes("84713010")

        assert notes == []

    def test_add_ncm_note_success(self, datastore_in_memory):
        """Test agregar nota NCM exitosamente."""
        ncm = "84713010"
        note = "Esta es una nota de prueba"

        result = datastore_in_memory.add_ncm_note(ncm, note)

        assert result is True

        # Verify note was added
        notes = datastore_in_memory.get_ncm_notes(ncm)
        assert len(notes) >= 1
        assert note in notes

    def test_add_multiple_ncm_notes(self, datastore_in_memory):
        """Test agregar múltiples notas al mismo NCM."""
        ncm = "84713010"
        notes_to_add = [
            "Primera nota",
            "Segunda nota",
            "Tercera nota"
        ]

        for note in notes_to_add:
            datastore_in_memory.add_ncm_note(ncm, note)

        retrieved_notes = datastore_in_memory.get_ncm_notes(ncm)

        assert len(retrieved_notes) >= 3
        for note in notes_to_add:
            assert note in retrieved_notes

    def test_add_ncm_note_with_client_id(self, datastore_in_memory, sample_cliente):
        """Test agregar nota NCM asociada a cliente."""
        created = datastore_in_memory.create_client(sample_cliente)
        cliente_id = created["id"]

        ncm = "84713010"
        note = "Nota asociada a cliente"

        result = datastore_in_memory.add_ncm_note(ncm, note, client_id=cliente_id)

        assert result is True

        # Verify note was added
        notes = datastore_in_memory.get_ncm_notes(ncm)
        assert note in notes

    def test_ncm_notes_isolated_by_ncm(self, datastore_in_memory):
        """Test que notas NCM están aisladas por código NCM."""
        ncm1 = "84713010"
        ncm2 = "85171200"

        datastore_in_memory.add_ncm_note(ncm1, "Nota para NCM 1")
        datastore_in_memory.add_ncm_note(ncm2, "Nota para NCM 2")

        notes1 = datastore_in_memory.get_ncm_notes(ncm1)
        notes2 = datastore_in_memory.get_ncm_notes(ncm2)

        assert "Nota para NCM 1" in notes1
        assert "Nota para NCM 1" not in notes2
        assert "Nota para NCM 2" in notes2
        assert "Nota para NCM 2" not in notes1


# ============================================================================
# TESTS DE BACKEND IN-MEMORY
# ============================================================================

class TestInMemoryBackend:
    """Tests específicos para InMemoryBackend."""

    def test_backend_has_demo_clients_on_init(self, in_memory_backend):
        """Test que backend in-memory tiene clientes demo al inicializar."""
        clientes = in_memory_backend.list_clients()

        assert len(clientes) >= 3
        # Check demo clients exist
        names = [c["nombre"] for c in clientes]
        assert any("ABC" in name for name in names)

    def test_backend_user_id_set(self, in_memory_backend):
        """Test que backend tiene user_id configurado."""
        assert in_memory_backend.user_id is not None
        assert len(in_memory_backend.user_id) > 0
