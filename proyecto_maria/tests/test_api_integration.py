"""Tests de integración para la API FastAPI."""

import os
import pytest
from fastapi.testclient import TestClient
from main import app


class TestAPIIntegration:
    """Tests de integración para la API completa."""

    @pytest.fixture
    def client(self):
        """Fixture que proporciona un cliente de test para la API."""
        return TestClient(app)

    @pytest.fixture
    def cleanup_excel_files(self):
        """Fixture para limpiar archivos Excel después de cada test."""
        yield
        # Cleanup: eliminar archivos Excel generados durante los tests
        for file in os.listdir('.'):
            if file.startswith('MARIA_') and file.endswith('.xlsx'):
                try:
                    os.remove(file)
                except OSError:
                    pass  # Ignorar si no se puede eliminar

    def test_root_endpoint(self, client):
        """Test del endpoint raíz."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "Optimizador MARIA funcionando" in data["status"]

    def test_process_operation_success(self, client, cleanup_excel_files):
        """Test procesamiento exitoso de operación."""
        payload = {
            "operation_id": "API-TEST-001",
            "items": [
                {
                    "ncm": "84713010",
                    "description": "Computadora portatil",
                    "quantity": 2.0,
                    "unit": "UN",
                    "unit_fob_value": 1500.0,
                    "origin_country": "CN"
                },
                {
                    "ncm": "85414010",
                    "description": "Diodos LED",
                    "quantity": 100.0,
                    "unit": "UN",
                    "unit_fob_value": 0.5
                }
            ]
        }

        response = client.post("/process_operation/", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura de respuesta
        assert "message" in data
        assert "filename" in data
        assert "validated_items_count" in data

        # Verificar contenido
        assert "Operación procesada y Excel generado exitosamente" in data["message"]
        assert data["filename"].endswith(".xlsx")
        assert "MARIA_API-TEST-001" in data["filename"]
        assert data["validated_items_count"] == 2

        # Verificar que el archivo Excel se creó
        assert os.path.exists(data["filename"])

    def test_process_operation_validation_errors(self, client):
        """Test procesamiento con errores de validación."""
        payload = {
            "operation_id": "API-TEST-ERRORS",
            "items": [
                {
                    "ncm": "",  # NCM vacío
                    "description": "Producto inválido",
                    "quantity": 1.0,
                    "unit": "UN",
                    "unit_fob_value": 100.0
                },
                {
                    "ncm": "84713010",
                    "description": "Producto con valores negativos",
                    "quantity": -5.0,  # negativo
                    "unit": "UN",
                    "unit_fob_value": 500.0
                }
            ]
        }

        response = client.post("/process_operation/", json=payload)

        assert response.status_code == 400
        data = response.json()

        # Verificar que hay errores
        assert "detail" in data
        assert "errors" in data["detail"]
        assert len(data["detail"]["errors"]) == 2

        # Verificar mensajes de error
        errors = data["detail"]["errors"]
        assert any("El código NCM es obligatorio" in error for error in errors)
        assert any("La cantidad y el valor FOB deben ser mayores a cero" in error for error in errors)

    def test_process_operation_mixed_valid_invalid(self, client, cleanup_excel_files):
        """Test procesamiento con mezcla de items válidos e inválidos."""
        payload = {
            "operation_id": "API-TEST-MIXED",
            "items": [
                {
                    "ncm": "84713010",
                    "description": "Producto válido",
                    "quantity": 2.0,
                    "unit": "UN",
                    "unit_fob_value": 1500.0
                },
                {
                    "ncm": "",  # inválido
                    "description": "Producto inválido",
                    "quantity": 1.0,
                    "unit": "UN",
                    "unit_fob_value": 100.0
                },
                {
                    "ncm": "85414010",
                    "description": "Producto válido 2",
                    "quantity": 50.0,
                    "unit": "UN",
                    "unit_fob_value": 2.5
                }
            ]
        }

        response = client.post("/process_operation/", json=payload)

        # Debería fallar porque hay items inválidos
        assert response.status_code == 400
        data = response.json()
        assert "errors" in data["detail"]
        assert len(data["detail"]["errors"]) == 1  # Solo el item inválido

    def test_process_operation_empty_items(self, client):
        """Test procesamiento con lista vacía de items."""
        payload = {
            "operation_id": "API-TEST-EMPTY",
            "items": []
        }

        response = client.post("/process_operation/", json=payload)

        assert response.status_code == 500  # Error interno por no hay items válidos
        data = response.json()
        assert "No hay ítems válidos para generar el Excel" in str(data["detail"])

    def test_process_operation_single_item(self, client, cleanup_excel_files):
        """Test procesamiento con un solo item."""
        payload = {
            "operation_id": "API-TEST-SINGLE",
            "items": [
                {
                    "ncm": "12345678",
                    "description": "Producto único",
                    "quantity": 1.0,
                    "unit": "UN",
                    "unit_fob_value": 1000.0,
                    "origin_country": "US"
                }
            ]
        }

        response = client.post("/process_operation/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["validated_items_count"] == 1
        assert os.path.exists(data["filename"])

    def test_process_operation_invalid_json(self, client):
        """Test envío de JSON inválido."""
        # Enviar JSON malformado
        response = client.post(
            "/process_operation/",
            data='{"operation_id": "TEST", "items": [invalid json}',
            headers={"Content-Type": "application/json"}
        )

        # FastAPI debería manejar el error de parsing JSON
        assert response.status_code == 422  # Unprocessable Entity

    def test_process_operation_missing_fields(self, client):
        """Test envío de payload con campos faltantes."""
        # Payload sin operation_id
        payload = {
            "items": [
                {
                    "ncm": "84713010",
                    "description": "Test",
                    "quantity": 1.0,
                    "unit": "UN",
                    "unit_fob_value": 100.0
                }
            ]
        }

        response = client.post("/process_operation/", json=payload)

        assert response.status_code == 422  # Validation error

    def test_process_operation_invalid_item_data(self, client):
        """Test envío de datos de item inválidos."""
        payload = {
            "operation_id": "API-TEST-INVALID",
            "items": [
                {
                    "ncm": "84713010",
                    "description": "Producto válido",
                    "quantity": "not_a_number",  # string en lugar de float
                    "unit": "UN",
                    "unit_fob_value": 100.0
                }
            ]
        }

        response = client.post("/process_operation/", json=payload)

        assert response.status_code == 422  # Validation error de Pydantic

    def test_excel_file_content_via_api(self, client, cleanup_excel_files):
        """Test que el Excel generado vía API tiene el contenido correcto."""
        import pandas as pd

        payload = {
            "operation_id": "API-CONTENT-TEST",
            "items": [
                {
                    "ncm": "84713010",
                    "description": "Test product",
                    "quantity": 3.0,
                    "unit": "UN",
                    "unit_fob_value": 250.0,
                    "origin_country": "CN"
                }
            ]
        }

        response = client.post("/process_operation/", json=payload)
        assert response.status_code == 200

        filename = response.json()["filename"]

        # Leer el archivo Excel y verificar contenido
        df = pd.read_excel(filename, engine='openpyxl')
        assert len(df) == 1
        assert df.iloc[0]['ncm'] == "84713010"
        assert df.iloc[0]['total_fob_value'] == 750.0  # 3.0 * 250.0

    def test_api_handles_special_characters(self, client, cleanup_excel_files):
        """Test que la API maneja caracteres especiales correctamente."""
        payload = {
            "operation_id": "TEST-Ñ-Á-É-Í-Ó-Ú",
            "items": [
                {
                    "ncm": "84713010",
                    "description": "Producto con ñames & símbolos @#$%",
                    "quantity": 1.0,
                    "unit": "UN",
                    "unit_fob_value": 100.0
                }
            ]
        }

        response = client.post("/process_operation/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert os.path.exists(data["filename"])
