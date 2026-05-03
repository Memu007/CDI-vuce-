"""Tests para el generador de Excel."""

import os
import pandas as pd
import pytest
from proyecto_maria.models.operations import Item
from proyecto_maria.core.excel_generator import create_maria_excel


class TestCreateMariaExcel:
    """Tests para la función create_maria_excel."""

    @pytest.fixture
    def sample_items(self):
        """Fixture que proporciona items de prueba."""
        return [
            Item(
                pieza="84713010",
                descripcion="Computadora portatil",
                origen="CN",
                peso_unitario=2.5,
                cantidad=2.0,
                valor_unitario=1500.0,
                marca="DELL",
                modelo="LATITUDE",
                version="5420"
            ),
            Item(
                pieza="85414010",
                descripcion="Diodos LED",
                origen="TW",
                peso_unitario=0.001,
                cantidad=100.0,
                valor_unitario=0.5,
                marca="EVERLIGHT",
                modelo="2835"
            ),
            Item(
                pieza="39269090",
                descripcion="Plástico ABS",
                origen="BR",
                peso_unitario=1.0,
                cantidad=50.0,
                valor_unitario=2.5,
                marca="SABIC"
            )
        ]

    def test_excel_generation_success(self, sample_items, cleanup_excel_files):
        """Test generación exitosa de Excel con items válidos."""
        operation_id = "TEST-EXCEL-001"

        filename = create_maria_excel(sample_items, operation_id)

        # Verificar que el archivo se creó
        assert os.path.exists(filename)
        assert filename.endswith('.xlsx')
        assert 'AVG_TEST-EXCEL-001' in filename

    def test_excel_content_correct(self, sample_items, cleanup_excel_files):
        """Test que el contenido del Excel es correcto."""
        operation_id = "TEST-CONTENT"

        filename = create_maria_excel(sample_items, operation_id)

        # Leer el archivo Excel generado con tipos explícitos
        df = pd.read_excel(filename, engine='openpyxl', dtype={'ncm': str})

        # Verificar número de filas
        assert len(df) == 3

        # Verificar columnas
        expected_columns = [
            'Pieza', 'Descripcion', 'Origen', 'Peso Unitario', 'Cantidad',
            'Valor Unitario', 'Marca', 'Modelo', 'Version', 'otros ',
            'separador', 'ventaja ', 'TOTAL'
        ]
        assert list(df.columns) == expected_columns

        # Verificar contenido de la primera fila
        assert str(df.iloc[0]['Pieza']) == "84713010"
        assert df.iloc[0]['Descripcion'] == "Computadora portatil"
        assert df.iloc[0]['Origen'] == "CN"
        assert df.iloc[0]['Peso Unitario'] == 2.5
        assert df.iloc[0]['Cantidad'] == 2.0
        assert df.iloc[0]['Valor Unitario'] == 1500.0
        assert df.iloc[0]['Marca'] == "DELL"
        assert df.iloc[0]['TOTAL'] == 3000.0  # 2.0 * 1500.0

        # Verificar contenido de la segunda fila
        assert str(df.iloc[1]['Pieza']) == "85414010"
        assert df.iloc[1]['Descripcion'] == "Diodos LED"
        assert df.iloc[1]['Origen'] == "TW"
        assert df.iloc[1]['Peso Unitario'] == 0.001
        assert df.iloc[1]['Cantidad'] == 100.0
        assert df.iloc[1]['Valor Unitario'] == 0.5
        assert df.iloc[1]['Marca'] == "EVERLIGHT"
        assert df.iloc[1]['TOTAL'] == 50.0  # 100.0 * 0.5

        # Verificar contenido de la tercera fila
        assert str(df.iloc[2]['Pieza']) == "39269090"
        assert df.iloc[2]['Descripcion'] == "Plástico ABS"
        assert df.iloc[2]['Origen'] == "BR"
        assert df.iloc[2]['Peso Unitario'] == 1.0
        assert df.iloc[2]['Cantidad'] == 50.0
        assert df.iloc[2]['Valor Unitario'] == 2.5
        assert df.iloc[2]['Marca'] == "SABIC"
        assert df.iloc[2]['TOTAL'] == 125.0  # 50.0 * 2.5

    def test_empty_items_raises_error(self):
        """Test que lista vacía de items genera error."""
        with pytest.raises(ValueError, match="No hay ítems válidos para generar el Excel"):
            create_maria_excel([], "TEST-EMPTY")

    def test_filename_format(self, sample_items, cleanup_excel_files):
        """Test que el nombre del archivo sigue el formato correcto."""
        operation_id = "TESTFORMAT001"

        filename = create_maria_excel(sample_items, operation_id)

        # Verificar formato: AVG_{operation_id_sin_espacios}_{timestamp}.xlsx
        assert filename.startswith('AVG_TESTFORMAT001_')
        assert filename.endswith('.xlsx')

        # Verificar que contiene timestamp
        parts = filename.split('_')
        assert len(parts) >= 3
        timestamp_part = parts[-1].replace('.xlsx', '')
        # Timestamp debe tener al menos 6 caracteres (HHMMSS) y como máximo 15 (YYYYMMDD_HHMMSS)
        assert 6 <= len(timestamp_part) <= 15
        # Debe contener solo dígitos
        assert timestamp_part.isdigit()

    def test_single_item_excel(self, cleanup_excel_files):
        """Test generación de Excel con un solo item."""
        single_item = [
            Item(
                pieza="12345678",
                descripcion="Producto único",
                origen="US",
                peso_unitario=1.0,
                cantidad=1.0,
                valor_unitario=1000.0
            )
        ]

        filename = create_maria_excel(single_item, "TEST-SINGLE")

        # Verificar archivo creado
        assert os.path.exists(filename)

        # Verificar contenido
        df = pd.read_excel(filename, engine='openpyxl', dtype={'Pieza': str})
        assert len(df) == 1
        assert str(df.iloc[0]['Pieza']) == "12345678"
        assert df.iloc[0]['TOTAL'] == 1000.0  # 1.0 * 1000.0

    def test_total_calculation(self, cleanup_excel_files):
        """Test que el cálculo de TOTAL es correcto."""
        items = [
            Item(
                pieza="84713010",
                descripcion="Producto 1",
                origen="CN",
                peso_unitario=1.0,
                cantidad=3.0,
                valor_unitario=200.0
            ),
            Item(
                pieza="85414010",
                descripcion="Producto 2",
                origen="TW",
                peso_unitario=0.5,
                cantidad=2.0,
                valor_unitario=1500.0
            )
        ]

        filename = create_maria_excel(items, "TEST-CALC")

        df = pd.read_excel(filename, engine='openpyxl', dtype={'Pieza': str})

        # Verificar cálculos
        assert df.iloc[0]['TOTAL'] == 600.0   # 3.0 * 200.0
        assert df.iloc[1]['TOTAL'] == 3000.0  # 2.0 * 1500.0

    def test_column_order_preserved(self, sample_items, cleanup_excel_files):
        """Test que el orden de columnas se preserva correctamente."""
        filename = create_maria_excel(sample_items, "TEST-ORDER")

        df = pd.read_excel(filename, engine='openpyxl')

        # Verificar orden exacto de columnas
        expected_order = [
            'Pieza', 'Descripcion', 'Origen', 'Peso Unitario', 'Cantidad',
            'Valor Unitario', 'Marca', 'Modelo', 'Version', 'otros ',
            'separador', 'ventaja ', 'TOTAL'
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
