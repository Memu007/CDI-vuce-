"""Regresión de los bloqueos de la pantalla Validación de MARIA."""

import pytest

from proyecto_maria.core.validations import run_smart_validations
from proyecto_maria.models.operations import Item


def _item(**overrides):
    values = {
        "pieza": "8471.30.00.900 R",
        "descripcion": "Modulo de prueba de validacion",
        "origen": "310",
        "cantidad": 2,
        "valor_unitario": 125,
        "peso_unitario": 0.5,
    }
    values.update(overrides)
    return Item(**values)


@pytest.mark.parametrize(
    ("field", "label"),
    [
        ("cantidad", "cantidad"),
        ("valor_unitario", "valor unitario"),
        ("peso_unitario", "peso unitario"),
    ],
)
def test_smart_validation_blocks_mandatory_values_invalidos(field, label):
    result = run_smart_validations([_item(**{field: 0})])

    assert any(label in error.lower() and "mayor a cero" in error.lower() for error in result["errores"])


def test_smart_validation_keeps_warning_non_blocking_for_ncm_8471():
    result = run_smart_validations([_item()])

    assert result["errores"] == []
    assert any("computadoras" in warning.lower() for warning in result["advertencias"])
