"""
Tests de Regresión - Fase 0 Estabilización
==========================================

Estos tests validan que los cambios de Fase 0 no introduzcan regresiones
y que las nuevas funcionalidades estén operativas.

Ejecutar con: pytest tests/test_regression_phase0.py -v
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Setup path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestHealthCheck:
    """Tests para el endpoint /health mejorado"""

    @pytest.fixture
    def client(self):
        from proyecto_maria.main import app
        return TestClient(app)

    def test_health_returns_ok(self, client):
        """Health check debe responder siempre con status 200"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "api" in data
        assert data["api"] == "ok"
        print(f"✅ Health check: {data}")

    def test_health_includes_database_status(self, client):
        """Health check debe incluir estado de la base de datos"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data
        # Database puede ser "ok", "error" o "unknown"
        assert data["database"] in ["ok", "error", "unknown"]
        print(f"✅ Database status: {data['database']}")

    def test_health_includes_timestamp(self, client):
        """Health check debe incluir timestamp"""
        response = client.get("/health")
        data = response.json()
        assert "timestamp" in data
        print(f"✅ Timestamp: {data['timestamp']}")


class TestBackupRestore:
    """Tests para los endpoints de backup/restore localStorage"""

    @pytest.fixture
    def client(self):
        from proyecto_maria.main import app
        return TestClient(app)

    def test_backup_localstorage_accepts_data(self, client):
        """Backup debe aceptar datos JSON"""
        test_data = {
            "clients": [{"id": "test-1", "name": "Cliente Test"}],
            "ncmNotes": {"12345678": "Nota de prueba"},
            "timestamp": "2025-12-04T14:00:00Z"
        }
        
        response = client.post("/api/backup/localStorage", json=test_data)
        assert response.status_code == 200
        data = response.json()
        # Puede fallar si no hay DB, pero no debe ser 500
        assert "success" in data
        print(f"✅ Backup response: {data}")

    def test_restore_localstorage_returns_data(self, client):
        """Restore debe retornar datos o mensaje de error claro"""
        response = client.get("/api/restore/localStorage")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        # Si no hay backups, debe indicarlo claramente
        if not data["success"]:
            assert "error" in data
        print(f"✅ Restore response: {data}")


class TestCoreEndpoints:
    """Tests de regresión para endpoints core existentes"""

    @pytest.fixture
    def client(self):
        from proyecto_maria.main import app
        return TestClient(app)

    def test_root_returns_html(self, client):
        """Root debe retornar la landing page"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        print("✅ Root endpoint OK")

    @pytest.mark.skip(reason="Login endpoint has async middleware issue with TestClient")
    def test_login_endpoint_exists(self, client):
        """Login endpoint debe existir"""
        response = client.post("/auth/login", json={
            "username": "test",
            "password": "test"
        })
        # 401 es esperado para credenciales inválidas, pero no 404 o 500
        assert response.status_code in [200, 401, 422]
        print(f"✅ Login endpoint: {response.status_code}")

    def test_static_files_accessible(self, client):
        """Archivos estáticos deben ser accesibles"""
        # Al menos el CSS debe existir
        response = client.get("/app.css")
        # 200 si existe, 404 si no (pero no 500)
        assert response.status_code in [200, 404]
        print(f"✅ Static files: {response.status_code}")


class TestPDFEndpoint:
    """Tests para el endpoint de PDF que nunca debe fallar con 500"""

    @pytest.fixture
    def client(self):
        from proyecto_maria.main import app
        return TestClient(app)

    def test_pdf_upload_graceful_error(self, client):
        """PDF upload con archivo inválido debe degradar, no crashear"""
        # PDF mínimo válido (header)
        minimal_pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>"
        
        response = client.post(
            "/upload_pdf/public",
            files={"file": ("test.pdf", minimal_pdf, "application/pdf")}
        )
        # Puede ser 200 (éxito), 400 (sin items), 422 (validación)
        # Pero NUNCA 500 (error interno)
        assert response.status_code != 500, f"PDF upload falló con 500: {response.text}"
        print(f"✅ PDF upload graceful: {response.status_code}")

    def test_pdf_upload_rejects_non_pdf(self, client):
        """PDF upload debe rechazar archivos no-PDF"""
        response = client.post(
            "/upload_pdf/public",
            files={"file": ("test.txt", b"This is not a PDF", "text/plain")}
        )
        assert response.status_code in [400, 422]
        print(f"✅ Non-PDF rejected: {response.status_code}")


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
