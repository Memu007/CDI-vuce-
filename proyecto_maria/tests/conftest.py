"""
Fixtures compartidos para la suite de tests de MARIA.

Este archivo contiene fixtures de pytest que son reutilizados
en múltiples archivos de test.
"""

import pytest
import os
import tempfile
from typing import Dict, List
from unittest.mock import Mock, MagicMock

# Setup path for imports
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from proyecto_maria.core.datastore import DataStore, InMemoryBackend, PostgreSQLBackend
from proyecto_maria.models.operations import Item, OperationPayload


# ============================================================================
# FIXTURES PARA DATASTORE
# ============================================================================

@pytest.fixture
def clean_env():
    """Clean environment variables before test."""
    old_db_url = os.environ.get("DATABASE_URL")
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    yield
    if old_db_url:
        os.environ["DATABASE_URL"] = old_db_url


@pytest.fixture
def mock_postgres_conn():
    """Mock de conexión PostgreSQL."""
    conn = MagicMock()
    cursor = MagicMock()

    # Mock cursor methods
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    cursor.execute.return_value = None

    conn.cursor.return_value = cursor
    conn.commit.return_value = None

    return conn


@pytest.fixture
def in_memory_backend():
    """Fixture para backend in-memory."""
    return InMemoryBackend(user_id="test-user-123")


@pytest.fixture
def datastore_in_memory(clean_env):
    """Fixture para DataStore con backend in-memory."""
    return DataStore()


@pytest.fixture
def sample_cliente() -> Dict:
    """Cliente de ejemplo para tests."""
    return {
        "nombre": "Test Company S.A.",
        "email": "test@example.com",
        "telefono": "011-1234-5678",
        "direccion": "Calle Test 123, Buenos Aires",
        "notas": "Cliente de prueba"
    }


@pytest.fixture
def sample_clientes_list() -> List[Dict]:
    """Lista de clientes de ejemplo."""
    return [
        {
            "nombre": "Cliente Uno S.A.",
            "email": "uno@example.com",
            "telefono": "011-1111-1111",
            "direccion": "Calle 1, CABA",
            "notas": "Primer cliente"
        },
        {
            "nombre": "Cliente Dos LTDA",
            "email": "dos@example.com",
            "telefono": "011-2222-2222",
            "direccion": "Calle 2, CABA",
            "notas": "Segundo cliente"
        },
        {
            "nombre": "Cliente Tres SRL",
            "email": "tres@example.com",
            "telefono": "011-3333-3333",
            "direccion": "Calle 3, CABA",
            "notas": "Tercer cliente"
        }
    ]


# ============================================================================
# FIXTURES PARA OPERACIONES Y ITEMS
# ============================================================================

@pytest.fixture
def sample_item() -> Item:
    """Item válido de ejemplo."""
    return Item(
        pieza="84713010",
        descripcion="Laptop Dell Inspiron 15",
        origen="CN",
        peso_unitario=2.5,
        cantidad=10.0,
        valor_unitario=800.0
    )


@pytest.fixture
def sample_items_list() -> List[Item]:
    """Lista de items válidos de ejemplo."""
    return [
        Item(
            pieza="84713010",
            descripcion="Laptop Dell Inspiron 15",
            origen="CN",
            peso_unitario=2.5,
            cantidad=10.0,
            valor_unitario=800.0
        ),
        Item(
            pieza="85171200",
            descripcion="Smartphone Samsung Galaxy",
            origen="VN",
            peso_unitario=0.3,
            cantidad=25.0,
            valor_unitario=350.0
        ),
        Item(
            pieza="73269090",
            descripcion="Tornillos de acero inoxidable",
            origen="BR",
            peso_unitario=0.05,
            cantidad=1000.0,
            valor_unitario=0.5
        )
    ]


@pytest.fixture
def sample_operation_payload(sample_items_list) -> OperationPayload:
    """Payload de operación válido."""
    return OperationPayload(
        operation_id="TEST-OP-001",
        items=sample_items_list
    )


@pytest.fixture
def invalid_items_list() -> List[Item]:
    """Lista de items inválidos para tests de validación."""
    items = []

    # Item con pieza vacía (debería fallar validación de Pydantic)
    try:
        items.append(Item(
            pieza="",
            descripcion="Item sin NCM",
            origen="XX",
            peso_unitario=1.0,
            cantidad=1.0,
            valor_unitario=100.0
        ))
    except Exception:
        pass

    return items


# ============================================================================
# FIXTURES PARA PDF PROCESSING
# ============================================================================

@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Sample PDF content as bytes (minimal valid PDF)."""
    # Minimal valid PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Invoice) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
308
%%EOF
"""
    return pdf_content


@pytest.fixture
def sample_pdf_text() -> str:
    """Sample PDF text content for testing extraction."""
    return """
COMMERCIAL INVOICE

Invoice No: INV-2025-001
Date: 2025-09-30

Item  Description                   NCM         Quantity  Unit Price  Total
1     Laptop Dell Inspiron         84713010    10        800.00      8000.00
2     Smartphone Samsung Galaxy    85171200    25        350.00      8750.00
3     Wireless Mouse Logitech      84716060    50        25.00       1250.00

Total: USD 18,000.00

Origin: China
"""


@pytest.fixture
def mock_gemini_response() -> Dict:
    """Mock response from Gemini API."""
    return {
        "items": [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell Inspiron",
                "origen": "CN",
                "cantidad": 10.0,
                "valor_unitario": 800.0,
                "peso_unitario": 2.5
            },
            {
                "pieza": "85171200",
                "descripcion": "Smartphone Samsung Galaxy",
                "origen": "CN",
                "cantidad": 25.0,
                "valor_unitario": 350.0,
                "peso_unitario": 0.3
            }
        ]
    }


# ============================================================================
# FIXTURES PARA AUTH
# ============================================================================

@pytest.fixture
def mock_user_operador() -> Dict:
    """Mock de usuario con rol operador."""
    return {
        "sub": "user-123",
        "username": "test_operador",
        "email": "operador@example.com",
        "roles": ["operador"],
        "plan": "premium"
    }


@pytest.fixture
def mock_user_admin() -> Dict:
    """Mock de usuario con rol admin."""
    return {
        "sub": "admin-456",
        "username": "test_admin",
        "email": "admin@example.com",
        "roles": ["admin", "operador"],
        "plan": "premium"
    }


@pytest.fixture
def mock_auth_dependency(mock_user_operador):
    """Mock para dependency de autenticación."""
    def _mock_auth():
        return mock_user_operador
    return _mock_auth


# ============================================================================
# FIXTURES PARA COLUMN MAPPING
# ============================================================================

@pytest.fixture
def sample_column_mapping() -> Dict:
    """Mapeo de columnas de ejemplo."""
    return {
        "part_number": "pieza",
        "description": "descripcion",
        "country": "origen",
        "qty": "cantidad",
        "unit_price": "valor_unitario",
        "weight": "peso_unitario"
    }


@pytest.fixture
def invalid_column_mapping() -> Dict:
    """Mapeo de columnas inválido."""
    return {
        "part_number": "invalid_field",  # No existe en schema
        "description": "descripcion",
        "": "origen",  # Clave vacía
        "qty": "",  # Valor vacío
    }


# ============================================================================
# FIXTURES PARA NCM CATALOG
# ============================================================================

@pytest.fixture
def sample_ncm_csv(tmp_path):
    """Crea archivo CSV temporal con datos NCM."""
    csv_path = tmp_path / "ncm_test.csv"
    csv_content = """codigo,descripcion,alicuota
84713010,Computadoras portátiles,0.0
85171200,Teléfonos móviles,0.0
73269090,Artículos de ferretería,16.0
84716060,Dispositivos de entrada,2.0
"""
    csv_path.write_text(csv_content, encoding="utf-8")
    return csv_path


@pytest.fixture
def sample_ncm_notes(tmp_path):
    """Crea archivo JSON temporal con notas NCM."""
    import json
    notes_path = tmp_path / "ncm_notes.json"
    notes = {
        "84713010": ["Incluye laptops y notebooks", "Requiere certificación CE"],
        "85171200": ["Smartphones y teléfonos inteligentes", "Verificar homologación ENACOM"]
    }
    notes_path.write_text(json.dumps(notes), encoding="utf-8")
    return notes_path


# ============================================================================
# FIXTURES PARA TESTING DE ENDPOINTS
# ============================================================================

@pytest.fixture
def temp_data_dir(tmp_path):
    """Directorio temporal para archivos generados durante tests."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    generated_dir = data_dir / "generated"
    generated_dir.mkdir()

    old_data_dir = os.environ.get("DATA_DIR")
    os.environ["DATA_DIR"] = str(data_dir)

    yield data_dir

    if old_data_dir:
        os.environ["DATA_DIR"] = old_data_dir
    else:
        del os.environ["DATA_DIR"]


# ============================================================================
# FIXTURES PARA OPERACIONES
# ============================================================================

@pytest.fixture
def sample_operation_dict() -> Dict:
    """Diccionario de operación de ejemplo."""
    return {
        "operation_id": "OP-TEST-001",
        "items": [
            {
                "pieza": "84713010",
                "descripcion": "Laptop",
                "origen": "CN",
                "cantidad": 5.0,
                "valor_unitario": 1000.0,
                "peso_unitario": 2.5
            }
        ],
        "resumen": {
            "grupos": 1,
            "items": 1,
            "valor_total": 5000.0
        }
    }


@pytest.fixture
def mock_operations_list() -> List[Dict]:
    """Lista de operaciones mock para historial."""
    return [
        {
            "operation_id": "OP_1",
            "fecha": "2025-09-25T10:00:00Z",
            "resumen": {
                "grupos": 2,
                "items": 5,
                "valor_total": 15000.0
            },
            "items": []
        },
        {
            "operation_id": "OP_2",
            "fecha": "2025-09-26T15:30:00Z",
            "resumen": {
                "grupos": 1,
                "items": 3,
                "valor_total": 8500.0
            },
            "items": []
        }
    ]
