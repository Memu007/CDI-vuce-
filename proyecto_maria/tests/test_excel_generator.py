"""Tests para el generador de Excel."""

import os
import pandas as pd
import pytest
from models.operations import Item
from core.excel_generator import create_maria_excel


class TestCreateMariaExcel:
    """Tests para la función create_maria_excel."""

    @pytest.fixture
    def sample_items(self):
        """Fixture que proporciona items de prueba."""
        return [
            Item(
                ncm="84713010",
                description="Computadora portatil",
                quantity=2.0,
                unit="UN",
                unit_fob_value=1500.0,
                origin_country="CN"
            ),
            Item(
                ncm="85414010",
                description="Diodos LED",
                quantity=100.0,
                unit="UN",
                unit_fob_value=0.5,
                origin_country="TW"
            ),
            Item(
                ncm="39269090",
                description="Plástico ABS",
                quantity=50.0,
                unit="KG",
                unit_fob_value=2.5
            )
        ]

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

    def test_excel_generation_success(self, sample_items, cleanup_excel_files):
        """Test generación exitosa de Excel con items válidos."""
        operation_id = "TEST-EXCEL-001"

        filename = create_maria_excel(sample_items, operation_id)

        # Verificar que el archivo se creó
        assert os.path.exists(filename)
        assert filename.endswith('.xlsx')
        assert 'MARIA_TEST-EXCEL-001' in filename

    def test_excel_content_correct(self, sample_items, cleanup_excel_files):
        """Test que el contenido del Excel es correcto."""
        operation_id = "TEST-CONTENT"

        filename = create_maria_excel(sample_items, operation_id)

        # Leer el archivo Excel generado
        df = pd.read_excel(filename, engine='openpyxl', dtype={'Pieza': str})

        # Verificar número de filas
        assert len(df) == 3

        # Verificar columnas
        expected_columns = [
            'ncm', 'description', 'quantity', 'unit', 'unit_fob_value',
            'total_fob_value', 'origin_country'
        ]
        assert list(df.columns) == expected_columns

        # Verificar contenido de la primera fila
        assert df.iloc[0]['ncm'] == "84713010"
        assert df.iloc[0]['description'] == "Computadora portatil"
        assert df.iloc[0]['quantity'] == 2.0
        assert df.iloc[0]['unit'] == "UN"
        assert df.iloc[0]['unit_fob_value'] == 1500.0
        assert df.iloc[0]['total_fob_value'] == 3000.0  # 2.0 * 1500.0
        assert df.iloc[0]['origin_country'] == "CN"

        # Verificar contenido de la segunda fila
        assert df.iloc[1]['ncm'] == "85414010"
        assert df.iloc[1]['description'] == "Diodos LED"
        assert df.iloc[1]['quantity'] == 100.0
        assert df.iloc[1]['unit'] == "UN"
        assert df.iloc[1]['unit_fob_value'] == 0.5
        assert df.iloc[1]['total_fob_value'] == 50.0  # 100.0 * 0.5

        # Verificar contenido de la tercera fila (sin origin_country)
        assert df.iloc[2]['ncm'] == "39269090"
        assert df.iloc[2]['description'] == "Plástico ABS"
        assert df.iloc[2]['quantity'] == 50.0
        assert df.iloc[2]['unit'] == "KG"
        assert df.iloc[2]['unit_fob_value'] == 2.5
        assert df.iloc[2]['total_fob_value'] == 125.0  # 50.0 * 2.5
        assert pd.isna(df.iloc[2]['origin_country'])  # Debe ser NaN

    def test_empty_items_raises_error(self):
        """Test que lista vacía de items genera error."""
        with pytest.raises(ValueError, match="No hay ítems válidos para generar el Excel"):
            create_maria_excel([], "TEST-EMPTY")

    def test_filename_format(self, sample_items, cleanup_excel_files):
        """Test que el nombre del archivo sigue el formato correcto."""
        operation_id = "TEST FORMAT 001"

        filename = create_maria_excel(sample_items, operation_id)

        # Verificar formato: MARIA_{operation_id_sin_espacios}_{timestamp}.xlsx
        assert filename.startswith('MARIA_TEST_FORMAT_001_')
        assert filename.endswith('.xlsx')

        # Verificar que contiene timestamp (14 dígitos: YYYYMMDD_HHMMSS)
        parts = filename.split('_')
        assert len(parts) >= 3
        timestamp_part = parts[-1].replace('.xlsx', '')
        assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS tiene 15 caracteres

    def test_single_item_excel(self, cleanup_excel_files):
        """Test generación de Excel con un solo item."""
        single_item = [
            Item(
                ncm="12345678",
                description="Producto único",
                quantity=1.0,
                unit="UN",
                unit_fob_value=100.0
            )
        ]

        filename = create_maria_excel(single_item, "TEST-SINGLE")

        # Verificar archivo creado
        assert os.path.exists(filename)

        # Verificar contenido
        df = pd.read_excel(filename, engine='openpyxl', dtype={'Pieza': str})
        assert len(df) == 1
        assert df.iloc[0]['ncm'] == "12345678"
        assert df.iloc[0]['total_fob_value'] == 100.0  # 1.0 * 100.0

    def test_total_fob_calculation(self, cleanup_excel_files):
        """Test que el cálculo de total_fob_value es correcto."""
        items = [
            Item(
                ncm="84713010",
                description="Producto 1",
                quantity=3.5,
                unit="UN",
                unit_fob_value=200.75
            ),
            Item(
                ncm="85414010",
                description="Producto 2",
                quantity=0.25,
                unit="KG",
                unit_fob_value=15000.0
            )
        ]

        filename = create_maria_excel(items, "TEST-CALC")

        df = pd.read_excel(filename, engine='openpyxl', dtype={'Pieza': str})

        # Verificar cálculos
        assert df.iloc[0]['total_fob_value'] == 701.75  # 3.5 * 200.75
        assert df.iloc[1]['total_fob_value'] == 3750.0   # 0.25 * 15000.0

    def test_column_order_preserved(self, sample_items, cleanup_excel_files):
        """Test que el orden de columnas se preserva correctamente."""
        filename = create_maria_excel(sample_items, "TEST-ORDER")

        df = pd.read_excel(filename, engine='openpyxl', dtype={'Pieza': str})

        # Verificar orden exacto de columnas
        expected_order = [
            'ncm', 'description', 'quantity', 'unit', 'unit_fob_value',
            'total_fob_value', 'origin_country'
        ]

        assert list(df.columns) == expected_order

    def test_operation_id_with_spaces(self, sample_items, cleanup_excel_files):
        """Test que los espacios en operation_id se convierten a guiones bajos."""
        operation_id = "TEST WITH SPACES AND MORE"

        filename = create_maria_excel(sample_items, operation_id)

        # Verificar que los espacios se convierten a guiones bajos
        assert 'TEST_WITH_SPACES_AND_MORE' in filename
        assert ' ' not in filename

    def test_return_value_is_filename(self, sample_items, cleanup_excel_files):
        """Test que la función devuelve el nombre del archivo generado."""
        operation_id = "TEST-RETURN"

        filename = create_maria_excel(sample_items, operation_id)

        assert isinstance(filename, str)
        assert filename.endswith('.xlsx')
        assert os.path.exists(filename)
