"""Tests para los modelos Pydantic de operaciones."""

import pytest
from pydantic import ValidationError
from proyecto_maria.models.operations import Item, OperationPayload


class TestItemModel:
    """Tests para el modelo Item."""

    def test_item_creation_valid(self):
        """Test creación de Item con datos válidos."""
        item = Item(
            pieza="84713010",
            descripcion="Computadora portatil",
            origen="CN",
            peso_unitario=2.5,
            cantidad=2.0,
            valor_unitario=1500.0,
            marca="DELL",
            modelo="LATITUDE",
            version="5420"
        )

        assert item.pieza == "84713010"
        assert item.descripcion == "Computadora portatil"
        assert item.origen == "CN"
        assert item.peso_unitario == 2.5
        assert item.cantidad == 2.0
        assert item.valor_unitario == 1500.0
        assert item.marca == "DELL"
        assert item.modelo == "LATITUDE"
        assert item.version == "5420"

    def test_item_creation_minimal(self):
        """Test creación de Item con campos mínimos requeridos."""
        item = Item(
            pieza="84713010",
            descripcion="Producto básico",
            origen="CN",
            peso_unitario=1.0,
            cantidad=1.0,
            valor_unitario=100.0
        )

        assert item.pieza == "84713010"
        assert item.descripcion == "Producto básico"
        assert item.origen == "CN"
        assert item.peso_unitario == 1.0
        assert item.cantidad == 1.0
        assert item.valor_unitario == 100.0
        assert item.marca is None
        assert item.modelo is None
        assert item.version is None

    def test_item_creation_with_optional_fields(self):
        """Test creación de Item con campos opcionales."""
        item = Item(
            pieza="84713010",
            descripcion="Producto con marca",
            origen="BR",
            peso_unitario=5.5,
            cantidad=2.0,
            valor_unitario=250.75,
            marca="SAMSUNG",
            modelo="GALAXY",
            version="S23"
        )

        assert item.marca == "SAMSUNG"
        assert item.modelo == "GALAXY"
        assert item.version == "S23"

    def test_item_validation_types(self):
        """Test validación de tipos de datos."""
        # pieza debe ser string
        with pytest.raises(ValidationError):
            Item(
                pieza=84713010,  # int en lugar de str
                descripcion="Test",
                origen="CN",
                peso_unitario=1.0,
                cantidad=1.0,
                valor_unitario=100.0
            )

        # cantidad debe ser float
        with pytest.raises(ValidationError):
            Item(
                pieza="84713010",
                descripcion="Test",
                origen="CN",
                peso_unitario=1.0,
                cantidad="1.0",  # str en lugar de float
                valor_unitario=100.0
            )

        # valor_unitario debe ser float
        with pytest.raises(ValidationError):
            Item(
                pieza="84713010",
                descripcion="Test",
                origen="CN",
                peso_unitario=1.0,
                cantidad=1.0,
                valor_unitario="100.0"  # str en lugar de float
            )

    def test_item_model_dump(self):
        """Test que el modelo se puede convertir a diccionario."""
        item = Item(
            pieza="84713010",
            descripcion="Test item",
            origen="US",
            peso_unitario=3.0,
            cantidad=2.0,
            valor_unitario=500.0,
            marca="TEST"
        )

        data = item.model_dump()
        expected = {
            "pieza": "84713010",
            "descripcion": "Test item",
            "origen": "US",
            "peso_unitario": 3.0,
            "cantidad": 2.0,
            "valor_unitario": 500.0,
            "marca": "TEST",
            "modelo": None,
            "version": None,
            "otros": None,
            "separador": None,
            "ventaja": None
        }

        assert data == expected


class TestOperationPayloadModel:
    """Tests para el modelo OperationPayload."""

    def test_operation_payload_creation_valid(self):
        """Test creación de OperationPayload con datos válidos."""
        items = [
            Item(
                pieza="84713010",
                descripcion="Producto 1",
                origen="CN",
                peso_unitario=2.0,
                cantidad=2.0,
                valor_unitario=1500.0
            ),
            Item(
                pieza="85414010",
                descripcion="Producto 2",
                origen="TW",
                peso_unitario=0.1,
                cantidad=10.0,
                valor_unitario=5.0
            )
        ]

        payload = OperationPayload(
            operation_id="TEST-001",
            items=items
        )

        assert payload.operation_id == "TEST-001"
        assert len(payload.items) == 2
        assert payload.items[0].pieza == "84713010"
        assert payload.items[1].pieza == "85414010"

    def test_operation_payload_empty_items(self):
        """Test creación de OperationPayload con lista vacía de items."""
        payload = OperationPayload(
            operation_id="TEST-EMPTY",
            items=[]
        )

        assert payload.operation_id == "TEST-EMPTY"
        assert len(payload.items) == 0

    def test_operation_payload_single_item(self):
        """Test creación de OperationPayload con un solo item."""
        item = Item(
            pieza="12345678",
            descripcion="Producto único",
            origen="US",
            peso_unitario=1.0,
            cantidad=1.0,
            valor_unitario=100.0
        )

        payload = OperationPayload(
            operation_id="TEST-SINGLE",
            items=[item]
        )

        assert payload.operation_id == "TEST-SINGLE"
        assert len(payload.items) == 1
        assert payload.items[0].descripcion == "Producto único"

    def test_operation_payload_validation_operation_id_required(self):
        """Test que operation_id es requerido y no puede estar vacío."""
        # operation_id vacío debería lanzar ValidationError
        with pytest.raises(ValidationError):
            OperationPayload(
                operation_id="",  # vacío
                items=[]
            )

    def test_operation_payload_model_dump(self):
        """Test que OperationPayload se puede convertir a diccionario."""
        items = [
            Item(
                pieza="84713010",
                descripcion="Test item",
                origen="CN",
                peso_unitario=1.0,
                cantidad=1.0,
                valor_unitario=100.0
            )
        ]

        payload = OperationPayload(
            operation_id="TEST-DUMP",
            items=items
        )

        data = payload.model_dump()
        assert data["operation_id"] == "TEST-DUMP"
        assert len(data["items"]) == 1
        assert data["items"][0]["pieza"] == "84713010"