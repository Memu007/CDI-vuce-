"""
Tests para Feature #1: Auto-completado Inteligente
Tests para ClientService: detect_client_from_text, get_frequent_products, autocomplete_items
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from proyecto_maria.services.client_service import ClientService


@pytest.mark.asyncio
class TestClientDetection:
    """Tests para detección de cliente desde texto"""

    async def test_detect_client_by_cuit_success(self):
        """Detectar cliente por CUIT con formato XX-XXXXXXXX-X"""
        mock_client = MagicMock()
        mock_client.id = "client-123"
        mock_client.name = "ACME SA"
        mock_client.cuit = "20123456789"

        with patch('proyecto_maria.services.client_service.AsyncSessionLocal') as mock_session:
            mock_execute = AsyncMock()
            mock_execute.return_value.scalar_one_or_none.return_value = mock_client
            mock_session.return_value.__aenter__.return_value.execute = mock_execute

            text = "Factura para ACME SA - CUIT: 20-12345678-9"
            result = await ClientService.detect_client_from_text(text)

            assert result is not None
            assert result["client_id"] == "client-123"
            assert result["nombre"] == "ACME SA"
            assert result["confidence"] == 0.95
            assert result["match_type"] == "cuit"

    async def test_detect_client_by_name_success(self):
        """Detectar cliente por nombre de empresa"""
        mock_client = MagicMock()
        mock_client.id = "client-456"
        mock_client.name = "Importadora Argentina"
        mock_client.is_active = True

        with patch('proyecto_maria.services.client_service.AsyncSessionLocal') as mock_session:
            # Primera query (CUIT) no encuentra nada
            mock_execute_cuit = AsyncMock()
            mock_execute_cuit.return_value.scalar_one_or_none.return_value = None

            # Segunda query (nombre) encuentra cliente
            mock_execute_name = AsyncMock()
            mock_execute_name.return_value.scalars.return_value.all.return_value = [mock_client]

            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.execute.side_effect = [mock_execute_cuit.return_value, mock_execute_name.return_value]

            text = "Envío para Importadora Argentina desde China"
            result = await ClientService.detect_client_from_text(text)

            assert result is not None
            assert result["client_id"] == "client-456"
            assert result["nombre"] == "Importadora Argentina"
            assert result["confidence"] == 0.80
            assert result["match_type"] == "name"

    async def test_detect_client_not_found(self):
        """No detectar cliente cuando no hay match"""
        with patch('proyecto_maria.services.client_service.AsyncSessionLocal') as mock_session:
            mock_execute = AsyncMock()
            mock_execute.return_value.scalar_one_or_none.return_value = None
            mock_execute.return_value.scalars.return_value.all.return_value = []
            mock_session.return_value.__aenter__.return_value.execute = mock_execute

            text = "Texto sin datos de cliente"
            result = await ClientService.detect_client_from_text(text)

            assert result is None

    async def test_detect_client_cuit_without_hyphens(self):
        """Detectar CUIT sin guiones"""
        mock_client = MagicMock()
        mock_client.id = "client-789"
        mock_client.name = "Tech SA"
        mock_client.cuit = "20987654321"

        with patch('proyecto_maria.services.client_service.AsyncSessionLocal') as mock_session:
            mock_execute = AsyncMock()
            mock_execute.return_value.scalar_one_or_none.return_value = mock_client
            mock_session.return_value.__aenter__.return_value.execute = mock_execute

            text = "CUIT: 20987654321"
            result = await ClientService.detect_client_from_text(text)

            assert result is not None
            assert result["client_id"] == "client-789"
            assert result["confidence"] == 0.95


@pytest.mark.asyncio
class TestFrequentProducts:
    """Tests para productos frecuentes"""

    async def test_get_frequent_products_success(self):
        """Obtener productos frecuentes ordenados por uso"""
        mock_products = [
            MagicMock(
                ncm="84713010",
                descripcion="LAPTOP LENOVO",
                peso_unitario_avg=2.5,
                origen_frecuente="CN",
                valor_unitario_avg=500.0,
                cantidad_avg=10.0,
                veces_usado=15,
                ultima_vez=datetime(2025, 9, 25)
            ),
            MagicMock(
                ncm="85171200",
                descripcion="CELULAR SAMSUNG",
                peso_unitario_avg=0.3,
                origen_frecuente="KR",
                valor_unitario_avg=300.0,
                cantidad_avg=20.0,
                veces_usado=8,
                ultima_vez=datetime(2025, 9, 20)
            )
        ]

        with patch('proyecto_maria.services.client_service.AsyncSessionLocal') as mock_session:
            mock_execute = AsyncMock()
            mock_execute.return_value.scalars.return_value.all.return_value = mock_products
            mock_session.return_value.__aenter__.return_value.execute = mock_execute

            result = await ClientService.get_frequent_products("client-123")

            assert len(result) == 2
            assert result[0]["ncm"] == "84713010"
            assert result[0]["descripcion"] == "LAPTOP LENOVO"
            assert result[0]["veces_usado"] == 15
            assert result[1]["ncm"] == "85171200"
            assert result[1]["veces_usado"] == 8

    async def test_get_frequent_products_empty(self):
        """Cliente sin productos frecuentes"""
        with patch('proyecto_maria.services.client_service.AsyncSessionLocal') as mock_session:
            mock_execute = AsyncMock()
            mock_execute.return_value.scalars.return_value.all.return_value = []
            mock_session.return_value.__aenter__.return_value.execute = mock_execute

            result = await ClientService.get_frequent_products("client-new")

            assert result == []

    async def test_get_frequent_products_limit(self):
        """Respetar límite de productos frecuentes"""
        mock_products = [MagicMock() for _ in range(5)]

        with patch('proyecto_maria.services.client_service.AsyncSessionLocal') as mock_session:
            mock_execute = AsyncMock()
            mock_execute.return_value.scalars.return_value.all.return_value = mock_products
            mock_session.return_value.__aenter__.return_value.execute = mock_execute

            result = await ClientService.get_frequent_products("client-123", limit=5)

            assert len(result) == 5


@pytest.mark.asyncio
class TestAutocompleteItems:
    """Tests para auto-completado de ítems"""

    async def test_autocomplete_exact_match(self):
        """Auto-completar con match exacto de descripción"""
        items = [
            {
                "descripcion": "LAPTOP LENOVO THINKPAD",
                "ncm": "",
                "peso_unitario": None,
                "origen": ""
            }
        ]

        frequent_products = [
            {
                "ncm": "84713010",
                "descripcion": "LAPTOP LENOVO",
                "peso_unitario_avg": 2.5,
                "origen_frecuente": "CN",
                "valor_unitario_avg": 500.0,
                "cantidad_avg": 10.0,
                "veces_usado": 10,
                "ultima_vez": None
            }
        ]

        with patch.object(ClientService, 'get_frequent_products', return_value=frequent_products):
            result = await ClientService.autocomplete_items("client-123", items)

            assert len(result) == 1
            # Verificar que se completó con datos del historial
            completed = result[0]
            assert "suggested_ncm" in completed or completed.get("ncm") == "84713010"

    async def test_autocomplete_no_match(self):
        """Auto-completar sin match en historial"""
        items = [
            {
                "descripcion": "PRODUCTO COMPLETAMENTE NUEVO",
                "ncm": "12345678",
                "peso_unitario": 1.0,
                "origen": "US"
            }
        ]

        with patch.object(ClientService, 'get_frequent_products', return_value=[]):
            result = await ClientService.autocomplete_items("client-123", items)

            assert len(result) == 1
            # Item original sin cambios
            assert result[0]["ncm"] == "12345678"

    async def test_autocomplete_partial_match(self):
        """Auto-completar con similaridad parcial"""
        items = [
            {
                "descripcion": "NOTEBOOK LENOVO",
                "ncm": "",
                "peso_unitario": None,
                "origen": ""
            }
        ]

        frequent_products = [
            {
                "ncm": "84713010",
                "descripcion": "LAPTOP LENOVO THINKPAD",
                "peso_unitario_avg": 2.5,
                "origen_frecuente": "CN",
                "valor_unitario_avg": 500.0,
                "cantidad_avg": 10.0,
                "veces_usado": 5,
                "ultima_vez": None
            }
        ]

        with patch.object(ClientService, 'get_frequent_products', return_value=frequent_products):
            result = await ClientService.autocomplete_items("client-123", items)

            assert len(result) == 1
            # Debería sugerir datos por similaridad
            completed = result[0]
            assert completed["descripcion"] == "NOTEBOOK LENOVO"

    async def test_autocomplete_multiple_items(self):
        """Auto-completar múltiples ítems"""
        items = [
            {"descripcion": "LAPTOP HP", "ncm": "", "peso_unitario": None, "origen": ""},
            {"descripcion": "CELULAR SAMSUNG", "ncm": "", "peso_unitario": None, "origen": ""},
            {"descripcion": "PRODUCTO NUEVO", "ncm": "99999999", "peso_unitario": 1.0, "origen": "US"}
        ]

        frequent_products = [
            {
                "ncm": "84713010",
                "descripcion": "LAPTOP",
                "peso_unitario_avg": 2.5,
                "origen_frecuente": "CN",
                "valor_unitario_avg": 500.0,
                "cantidad_avg": 10.0,
                "veces_usado": 10,
                "ultima_vez": None
            },
            {
                "ncm": "85171200",
                "descripcion": "CELULAR",
                "peso_unitario_avg": 0.3,
                "origen_frecuente": "KR",
                "valor_unitario_avg": 300.0,
                "cantidad_avg": 20.0,
                "veces_usado": 8,
                "ultima_vez": None
            }
        ]

        with patch.object(ClientService, 'get_frequent_products', return_value=frequent_products):
            result = await ClientService.autocomplete_items("client-123", items)

            assert len(result) == 3
            # Los dos primeros deberían tener sugerencias
            # El tercero debería mantener sus datos originales


@pytest.mark.asyncio
class TestUpdateProductHistory:
    """Tests para actualización de historial"""

    async def test_update_product_history_new_product(self):
        """Crear nueva entrada en historial"""
        items = [
            {
                "ncm": "84713010",
                "descripcion": "LAPTOP LENOVO",
                "peso_unitario": 2.5,
                "origen": "CN",
                "valor_unitario_fob": 500.0,
                "cantidad": 10
            }
        ]

        with patch('proyecto_maria.services.client_service.AsyncSessionLocal') as mock_session:
            mock_execute = AsyncMock()
            mock_execute.return_value.scalar_one_or_none.return_value = None  # No existe
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.execute = mock_execute
            mock_session_instance.add = MagicMock()
            mock_session_instance.commit = AsyncMock()

            await ClientService.update_product_history("client-123", items)

            # Verificar que se agregó nuevo producto
            mock_session_instance.add.assert_called_once()
            mock_session_instance.commit.assert_called_once()

    async def test_update_product_history_existing_product(self):
        """Actualizar entrada existente en historial"""
        mock_history = MagicMock()
        mock_history.veces_usado = 5
        mock_history.peso_unitario_avg = 2.0
        mock_history.valor_unitario_avg = 400.0
        mock_history.cantidad_avg = 8.0

        items = [
            {
                "ncm": "84713010",
                "descripcion": "LAPTOP LENOVO",
                "peso_unitario": 2.5,
                "origen": "CN",
                "valor_unitario_fob": 500.0,
                "cantidad": 10
            }
        ]

        with patch('proyecto_maria.services.client_service.AsyncSessionLocal') as mock_session:
            mock_execute = AsyncMock()
            mock_execute.return_value.scalar_one_or_none.return_value = mock_history
            mock_session_instance = mock_session.return_value.__aenter__.return_value
            mock_session_instance.execute = mock_execute
            mock_session_instance.commit = AsyncMock()

            await ClientService.update_product_history("client-123", items)

            # Verificar que se actualizó
            assert mock_history.veces_usado == 6  # 5 + 1
            mock_session_instance.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
