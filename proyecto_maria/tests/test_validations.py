"""Tests para las funciones de validación."""

import pytest
from models.operations import Item
from core.validations import run_pre_maria_validations


class TestRunPreMariaValidations:
    """Tests para la función run_pre_maria_validations."""

    def test_valid_items_pass_all_validations(self):
        """Test que items válidos pasan todas las validaciones."""
        valid_items = [
            Item(
                ncm="84713010",
                description="Producto válido 1",
                quantity=2.0,
                unit="UN",
                unit_fob_value=1500.0
            ),
            Item(
                ncm="85414010",
                description="Producto válido 2",
                quantity=10.5,
                unit="KG",
                unit_fob_value=25.75,
                origin_country="CN"
            )
        ]

        result_valid, result_errors = run_pre_maria_validations(valid_items)

        assert len(result_valid) == 2
        assert len(result_errors) == 0
        assert result_valid[0].ncm == "84713010"
        assert result_valid[1].ncm == "85414010"

    def test_empty_ncm_generates_error(self):
        """Test que NCM vacío genera error de validación."""
        invalid_items = [
            Item(
                ncm="",  # NCM vacío
                description="Producto inválido",
                quantity=1.0,
                unit="UN",
                unit_fob_value=100.0
            )
        ]

        result_valid, result_errors = run_pre_maria_validations(invalid_items)

        assert len(result_valid) == 0
        assert len(result_errors) == 1
        assert "El código NCM es obligatorio" in result_errors[0]
        assert "ítem 1" in result_errors[0]

    def test_negative_values_generate_error(self):
        """Test que valores negativos generan error de validación."""
        invalid_items = [
            Item(
                ncm="84713010",
                description="Producto con cantidad negativa",
                quantity=-1.0,  # negativo
                unit="UN",
                unit_fob_value=100.0
            ),
            Item(
                ncm="85414010",
                description="Producto con FOB negativo",
                quantity=5.0,
                unit="UN",
                unit_fob_value=-50.0  # negativo
            ),
            Item(
                ncm="39269090",
                description="Producto con ambos negativos",
                quantity=-2.0,  # negativo
                unit="UN",
                unit_fob_value=-100.0  # negativo
            )
        ]

        result_valid, result_errors = run_pre_maria_validations(invalid_items)

        assert len(result_valid) == 0
        assert len(result_errors) == 3

        # Verificar que cada error mencione el problema correcto
        assert "La cantidad y el valor FOB deben ser mayores a cero" in result_errors[0]
        assert "ítem 1" in result_errors[0]
        assert "84713010" in result_errors[0]

        assert "La cantidad y el valor FOB deben ser mayores a cero" in result_errors[1]
        assert "ítem 2" in result_errors[1]

        assert "La cantidad y el valor FOB deben ser mayores a cero" in result_errors[2]
        assert "ítem 3" in result_errors[2]

    def test_zero_values_generate_error(self):
        """Test que valores cero generan error de validación."""
        invalid_items = [
            Item(
                ncm="84713010",
                description="Producto con cantidad cero",
                quantity=0.0,  # cero
                unit="UN",
                unit_fob_value=100.0
            ),
            Item(
                ncm="85414010",
                description="Producto con FOB cero",
                quantity=5.0,
                unit="UN",
                unit_fob_value=0.0  # cero
            )
        ]

        result_valid, result_errors = run_pre_maria_validations(invalid_items)

        assert len(result_valid) == 0
        assert len(result_errors) == 2
        assert "La cantidad y el valor FOB deben ser mayores a cero" in result_errors[0]
        assert "La cantidad y el valor FOB deben ser mayores a cero" in result_errors[1]

    def test_mixed_valid_and_invalid_items(self):
        """Test con mezcla de items válidos e inválidos."""
        mixed_items = [
            Item(  # Válido
                ncm="84713010",
                description="Producto válido",
                quantity=2.0,
                unit="UN",
                unit_fob_value=1500.0
            ),
            Item(  # NCM vacío - inválido
                ncm="",
                description="Producto inválido 1",
                quantity=1.0,
                unit="UN",
                unit_fob_value=100.0
            ),
            Item(  # Valores negativos - inválido
                ncm="85414010",
                description="Producto inválido 2",
                quantity=-5.0,
                unit="UN",
                unit_fob_value=50.0
            ),
            Item(  # Válido
                ncm="39269090",
                description="Producto válido 2",
                quantity=10.0,
                unit="KG",
                unit_fob_value=25.0,
                origin_country="BR"
            )
        ]

        result_valid, result_errors = run_pre_maria_validations(mixed_items)

        # Solo 2 items válidos deben pasar
        assert len(result_valid) == 2
        assert result_valid[0].ncm == "84713010"
        assert result_valid[1].ncm == "39269090"

        # 2 items inválidos deben generar errores
        assert len(result_errors) == 2
        assert "ítem 2" in result_errors[0]  # NCM vacío
        assert "ítem 3" in result_errors[1]  # Valores negativos

    def test_empty_items_list(self):
        """Test con lista vacía de items."""
        result_valid, result_errors = run_pre_maria_validations([])

        assert len(result_valid) == 0
        assert len(result_errors) == 0

    def test_single_item_validation(self):
        """Test validación de un solo item."""
        single_item = [
            Item(
                ncm="84713010",
                description="Producto único",
                quantity=1.0,
                unit="UN",
                unit_fob_value=1000.0
            )
        ]

        result_valid, result_errors = run_pre_maria_validations(single_item)

        assert len(result_valid) == 1
        assert len(result_errors) == 0
        assert result_valid[0].ncm == "84713010"

    def test_whitespace_only_ncm(self):
        """Test que NCM con solo espacios se considera vacío."""
        invalid_items = [
            Item(
                ncm="   ",  # Solo espacios
                description="Producto con NCM vacío",
                quantity=1.0,
                unit="UN",
                unit_fob_value=100.0
            )
        ]

        result_valid, result_errors = run_pre_maria_validations(invalid_items)

        assert len(result_valid) == 0
        assert len(result_errors) == 1
        assert "El código NCM es obligatorio" in result_errors[0]

    def test_return_types(self):
        """Test que la función devuelve los tipos correctos."""
        items = [
            Item(
                ncm="84713010",
                description="Test",
                quantity=1.0,
                unit="UN",
                unit_fob_value=100.0
            )
        ]

        result_valid, result_errors = run_pre_maria_validations(items)

        assert isinstance(result_valid, list)
        assert isinstance(result_errors, list)
        assert all(isinstance(item, Item) for item in result_valid)
        assert all(isinstance(error, str) for error in result_errors)
