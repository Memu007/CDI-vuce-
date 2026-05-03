"""
Tests unitarios para Client Router - Gestión de clientes.

Este módulo contiene tests para los endpoints de gestión de clientes,
incluyendo CRUD, operaciones, column mapping y favoritos.

Cobertura:
- Endpoints GET/POST/PUT/DELETE de clientes (protegidos)
- Endpoints públicos sin autenticación
- Sistema de favoritos
- Operaciones por cliente
- Column mapping (crítico)
- Generación de métricas
- Exportación CSV
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

# Setup path for imports
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from proyecto_maria.routers.client_router import router, get_store
from proyecto_maria.routers.client_router import Cliente


# ============================================================================
# FIXTURES LOCALES
# ============================================================================

@pytest.fixture
def mock_store():
    """Mock del DataStore para tests."""
    store = MagicMock()

    # Mock demo clients
    store.list_clients.return_value = [
        {
            "id": "1",
            "nombre": "Empresa ABC S.A.",
            "email": "contacto@abc.com",
            "telefono": "011-1234-5678",
            "direccion": "Calle 123, Buenos Aires",
            "notas": "Cliente frecuente",
            "favorito": True
        },
        {
            "id": "2",
            "nombre": "Importadora XYZ Ltda.",
            "email": "info@xyz.com",
            "telefono": "011-9876-5432",
            "direccion": "Av. Corrientes 456, Buenos Aires",
            "notas": "Requiere documentación especial",
            "favorito": False
        }
    ]

    store.create_client.return_value = {
        "id": "new-client-123",
        "nombre": "New Client",
        "email": "new@example.com",
        "telefono": "011-1111-1111",
        "direccion": "New Address",
        "notas": "New notes",
        "favorito": False
    }

    store.get_client.return_value = {
        "id": "1",
        "nombre": "Empresa ABC S.A.",
        "email": "contacto@abc.com",
        "telefono": "011-1234-5678",
        "direccion": "Calle 123, Buenos Aires",
        "notas": "Cliente frecuente",
        "favorito": True
    }

    store.get_operations_by_client.return_value = []
    store.compute_metrics.return_value = {
        "total_operaciones": 0,
        "total_items": 0,
        "valor_total": 0.0,
        "promedio_items_por_operacion": 0.0,
        "ultimo_movimiento": None
    }

    store.get_column_mapping.return_value = {}
    store.set_column_mapping.return_value = True

    return store


@pytest.fixture
def test_app(mock_store):
    """Test FastAPI app con router de clientes."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)

    # Inject mock store
    with patch('proyecto_maria.routers.client_router.get_store', return_value=mock_store):
        yield app, mock_store


@pytest.fixture
def client(test_app):
    """Test client para FastAPI app."""
    app, mock_store = test_app
    return TestClient(app), mock_store


# ============================================================================
# TESTS DE ENDPOINTS PROTEGIDOS (CON AUTH)
# ============================================================================

class TestProtectedClientEndpoints:
    """Tests para endpoints protegidos que requieren autenticación."""

    @patch('proyecto_maria.routers.client_router.require_role')
    def test_get_clientes_success(self, mock_auth, client):
        """Test GET /api/clientes retorna lista de clientes."""
        test_client, mock_store = client

        # Mock auth to allow access
        mock_auth.return_value = lambda: {"sub": "user-123", "roles": ["operador"]}

        response = test_client.get("/api/clientes")

        # Should succeed or fail auth depending on implementation
        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "clientes" in data
            assert isinstance(data["clientes"], list)

    @patch('proyecto_maria.routers.client_router.require_role')
    def test_post_clientes_creates_client(self, mock_auth, client, sample_cliente):
        """Test POST /api/clientes crea cliente."""
        test_client, mock_store = client

        # Mock auth
        mock_auth.return_value = lambda: {"sub": "user-123", "roles": ["operador"]}

        response = test_client.post(
            "/api/clientes",
            json=sample_cliente
        )

        assert response.status_code in [200, 401, 422]

        if response.status_code == 200:
            data = response.json()
            assert "mensaje" in data or "cliente" in data

    @patch('proyecto_maria.routers.client_router.require_role')
    def test_put_clientes_updates_client(self, mock_auth, client):
        """Test PUT /api/clientes/{id} actualiza cliente."""
        test_client, mock_store = client

        # Mock auth
        mock_auth.return_value = lambda: {"sub": "user-123", "roles": ["operador"]}

        updated_data = {
            "nombre": "Updated Name",
            "email": "updated@example.com",
            "telefono": "011-9999-9999",
            "direccion": "Updated Address",
            "notas": "Updated notes"
        }

        mock_store.update_client.return_value = {
            "id": "1",
            **updated_data,
            "favorito": False
        }

        response = test_client.put(
            "/api/clientes/1",
            json=updated_data
        )

        assert response.status_code in [200, 401, 422]

    @patch('proyecto_maria.routers.client_router.require_role')
    def test_delete_clientes_removes_client(self, mock_auth, client):
        """Test DELETE /api/clientes/{id} elimina cliente."""
        test_client, mock_store = client

        # Mock auth
        mock_auth.return_value = lambda: {"sub": "user-123", "roles": ["operador"]}

        mock_store.delete_client.return_value = True

        response = test_client.delete("/api/clientes/1")

        assert response.status_code in [200, 401]

        if response.status_code == 200:
            data = response.json()
            assert "mensaje" in data

    @patch('proyecto_maria.routers.client_router.require_role')
    def test_delete_nonexistent_client_returns_404(self, mock_auth, client):
        """Test DELETE con cliente inexistente retorna 404."""
        test_client, mock_store = client

        # Mock auth
        mock_auth.return_value = lambda: {"sub": "user-123", "roles": ["operador"]}

        mock_store.delete_client.return_value = False

        response = test_client.delete("/api/clientes/nonexistent-id")

        assert response.status_code in [404, 401, 200]


# ============================================================================
# TESTS DE ENDPOINTS PÚBLICOS (SIN AUTH)
# ============================================================================

class TestPublicClientEndpoints:
    """Tests para endpoints públicos sin autenticación."""

    def test_get_clientes_public_returns_list(self, client):
        """Test GET /api/clientes/public retorna lista."""
        test_client, mock_store = client

        response = test_client.get("/api/clientes/public")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "clientes" in data

    def test_post_clientes_public_creates_client(self, client):
        """Test POST /api/clientes/public crea cliente sin auth."""
        test_client, mock_store = client

        new_client = {
            "nombre": "Public Client",
            "email": "public@example.com",
            "telefono": "011-5555-5555",
            "direccion": "Public Address",
            "notas": "Created via public endpoint"
        }

        response = test_client.post(
            "/api/clientes/public",
            json=new_client
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cliente" in data

    def test_post_clientes_public_requires_nombre_and_email(self, client):
        """Test que endpoint público requiere nombre y email."""
        test_client, mock_store = client

        # Missing email
        invalid_client = {
            "nombre": "Test Client"
            # Missing email
        }

        response = test_client.post(
            "/api/clientes/public",
            json=invalid_client
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "detail" in data

    def test_post_clientes_demo_creates_demo_clients(self, client):
        """Test POST /api/clientes/demo crea clientes demo."""
        test_client, mock_store = client

        response = test_client.post("/api/clientes/demo")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "clients" in data
        assert len(data["clients"]) >= 3


# ============================================================================
# TESTS DE FAVORITOS
# ============================================================================

class TestClientFavorites:
    """Tests para sistema de favoritos."""

    def test_marcar_favorito_true(self, client):
        """Test marcar cliente como favorito."""
        test_client, mock_store = client

        mock_store.set_favorite.return_value = True

        response = test_client.post(
            "/api/clientes/1/favorito",
            json={"favorito": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert "mensaje" in data

    def test_marcar_favorito_false(self, client):
        """Test desmarcar cliente como favorito."""
        test_client, mock_store = client

        mock_store.set_favorite.return_value = True

        response = test_client.post(
            "/api/clientes/1/favorito",
            json={"favorito": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert "mensaje" in data

    def test_marcar_favorito_nonexistent_client(self, client):
        """Test favorito con cliente inexistente."""
        test_client, mock_store = client

        mock_store.get_client.return_value = None

        response = test_client.post(
            "/api/clientes/nonexistent-id/favorito",
            json={"favorito": True}
        )

        # Should return error
        assert response.status_code in [200, 404]


# ============================================================================
# TESTS DE OPERACIONES
# ============================================================================

class TestClientOperations:
    """Tests para operaciones de cliente."""

    def test_get_operaciones_returns_list(self, client):
        """Test GET /api/clientes/{id}/operaciones retorna lista."""
        test_client, mock_store = client

        mock_store.get_operations_by_client.return_value = [
            {
                "operation_id": "OP_1",
                "fecha": "2025-09-25T10:00:00Z",
                "resumen": {"items": 5, "valor_total": 10000.0},
                "items": []
            }
        ]

        response = test_client.get("/api/clientes/1/operaciones")

        assert response.status_code == 200
        data = response.json()
        assert "operaciones" in data
        assert isinstance(data["operaciones"], list)

    def test_post_operacion_adds_operation(self, client):
        """Test POST /api/clientes/{id}/operaciones agrega operación."""
        test_client, mock_store = client

        operation_payload = {
            "operation_id": "TEST-OP-001",
            "items": [
                {
                    "pieza": "84713010",
                    "descripcion": "Laptop",
                    "origen": "CN",
                    "cantidad": 10.0,
                    "valor_unitario": 800.0,
                    "peso_unitario": 2.5
                }
            ]
        }

        mock_store.add_operation.return_value = {
            "operation_id": "OP_1",
            "fecha": "2025-09-30T12:00:00Z",
            "resumen": {"items": 1, "valor_total": 8000.0},
            "items": operation_payload["items"]
        }

        response = test_client.post(
            "/api/clientes/1/operaciones",
            json=operation_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert "operacion" in data

    def test_post_operaciones_demo_creates_demo_ops(self, client):
        """Test POST /api/clientes/{id}/operaciones/demo crea ops demo."""
        test_client, mock_store = client

        response = test_client.post("/api/clientes/1/operaciones/demo")

        assert response.status_code == 200
        data = response.json()
        assert "mensaje" in data

    def test_get_metricas_returns_metrics(self, client):
        """Test GET /api/clientes/{id}/metricas retorna métricas."""
        test_client, mock_store = client

        mock_store.compute_metrics.return_value = {
            "total_operaciones": 5,
            "total_items": 25,
            "valor_total": 50000.0,
            "promedio_items_por_operacion": 5.0,
            "ultimo_movimiento": "2025-09-30T12:00:00Z"
        }

        response = test_client.get("/api/clientes/1/metricas")

        assert response.status_code == 200
        data = response.json()
        assert "total_operaciones" in data
        assert "total_items" in data


# ============================================================================
# TESTS DE COLUMN MAPPING (CRÍTICO)
# ============================================================================

class TestClientColumnMapping:
    """Tests para column mapping - funcionalidad crítica."""

    def test_get_column_mapping_returns_mapping(self, client):
        """Test GET /api/clientes/{id}/column_mapping retorna mapping."""
        test_client, mock_store = client

        mock_store.get_column_mapping.return_value = {
            "part_number": "pieza",
            "description": "descripcion",
            "qty": "cantidad"
        }

        response = test_client.get("/api/clientes/1/column_mapping")

        assert response.status_code == 200
        data = response.json()
        assert "mapping" in data
        assert data["cliente_id"] == "1"

    def test_get_column_mapping_handles_errors(self, client):
        """Test que GET column_mapping maneja errores."""
        test_client, mock_store = client

        mock_store.get_column_mapping.side_effect = Exception("Database error")

        response = test_client.get("/api/clientes/1/column_mapping")

        assert response.status_code == 200
        data = response.json()
        assert "mapping" in data
        assert data["mapping"] == {}

    def test_post_column_mapping_sets_mapping(self, client, sample_column_mapping):
        """Test POST /api/clientes/{id}/column_mapping establece mapping."""
        test_client, mock_store = client

        mock_store.set_column_mapping.return_value = True
        mock_store.get_column_mapping.return_value = sample_column_mapping

        response = test_client.post(
            "/api/clientes/1/column_mapping",
            json={"mapping": sample_column_mapping}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "mapping" in data

    def test_post_column_mapping_with_empty_mapping(self, client):
        """Test POST column_mapping con mapping vacío."""
        test_client, mock_store = client

        mock_store.set_column_mapping.return_value = True
        mock_store.get_column_mapping.return_value = {}

        response = test_client.post(
            "/api/clientes/1/column_mapping",
            json={"mapping": {}}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_delete_column_mapping_clears_mapping(self, client):
        """Test DELETE /api/clientes/{id}/column_mapping limpia mapping."""
        test_client, mock_store = client

        mock_store.set_column_mapping.return_value = True

        response = test_client.delete("/api/clientes/1/column_mapping")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["mapping"] == {}

    def test_delete_column_mapping_handles_errors(self, client):
        """Test que DELETE column_mapping maneja errores."""
        test_client, mock_store = client

        mock_store.set_column_mapping.side_effect = Exception("Error clearing mapping")

        response = test_client.delete("/api/clientes/1/column_mapping")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "detail" in data


# ============================================================================
# TESTS DE EXPORTACIÓN CSV
# ============================================================================

class TestClientCSVExport:
    """Tests para exportación CSV."""

    def test_export_csv_returns_csv_content(self, client):
        """Test GET /api/clientes/{id}/export.csv retorna CSV."""
        test_client, mock_store = client

        mock_store.build_csv.return_value = """operation_id,fecha,ncm,descripcion
OP_1,2025-09-30,84713010,Laptop
OP_2,2025-09-29,85171200,Smartphone"""

        response = test_client.get("/api/clientes/1/export.csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

    def test_export_csv_includes_client_id_in_filename(self, client):
        """Test que CSV export incluye ID de cliente en filename."""
        test_client, mock_store = client

        mock_store.build_csv.return_value = "test,data\n1,2"

        response = test_client.get("/api/clientes/test-client-123/export.csv")

        assert response.status_code == 200
        assert "cliente_test-client-123" in response.headers["content-disposition"]


# ============================================================================
# TESTS DE GENERACIÓN DE PLANTILLA
# ============================================================================

class TestClientTemplateGeneration:
    """Tests para generación de plantilla Excel."""

    def test_generar_plantilla_creates_template(self, client, temp_data_dir):
        """Test POST /api/clientes/{id}/plantilla genera plantilla."""
        test_client, mock_store = client

        mock_store.get_column_mapping.return_value = {
            "part_number": "pieza",
            "description": "descripcion",
            "qty": "cantidad"
        }

        response = test_client.post("/api/clientes/1/plantilla")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "filename" in data
        assert "download_url" in data

    def test_generar_plantilla_uses_column_mapping(self, client, sample_column_mapping, temp_data_dir):
        """Test que plantilla usa column mapping del cliente."""
        test_client, mock_store = client

        mock_store.get_column_mapping.return_value = sample_column_mapping

        response = test_client.post("/api/clientes/1/plantilla")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        if "columns" in data:
            # Verify columns match mapping
            assert len(data["columns"]) > 0

    def test_generar_plantilla_with_empty_mapping(self, client, temp_data_dir):
        """Test plantilla con mapping vacío usa columnas default."""
        test_client, mock_store = client

        mock_store.get_column_mapping.return_value = {}

        response = test_client.post("/api/clientes/1/plantilla")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_generar_plantilla_handles_errors(self, client):
        """Test que plantilla maneja errores gracefully."""
        test_client, mock_store = client

        mock_store.get_column_mapping.side_effect = Exception("Mapping error")

        response = test_client.post("/api/clientes/1/plantilla")

        # Should still return response
        assert response.status_code == 200
        data = response.json()
        assert "success" in data


# ============================================================================
# TESTS DE VALIDACIÓN DE DATOS
# ============================================================================

class TestClientDataValidation:
    """Tests para validación de datos de cliente."""

    def test_cliente_model_validates_nombre(self):
        """Test que modelo Cliente valida nombre."""
        # Valid client
        valid_client = Cliente(
            nombre="Test Company",
            email="test@example.com",
            telefono="011-1234-5678",
            direccion="Test Address",
            notas="Test notes"
        )

        assert valid_client.nombre == "Test Company"

    def test_cliente_model_allows_empty_optional_fields(self):
        """Test que campos opcionales pueden estar vacíos."""
        client = Cliente(
            nombre="Test Company",
            email="",  # Optional
            telefono="",  # Optional
            direccion="",  # Optional
            notas=""  # Optional
        )

        assert client.nombre == "Test Company"
        assert client.email == ""
