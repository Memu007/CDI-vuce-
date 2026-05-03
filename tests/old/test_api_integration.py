"""Tests de integración para la API FastAPI."""

import os
from fastapi.testclient import TestClient
from .conftest import api_client, auth_headers, cleanup_excel_files


class TestAPIIntegration:
    """Tests de integración para la API completa."""

    def test_root_endpoint(self, client):
        """Test del endpoint raíz."""
        response = client.get("/")
        assert response.status_code == 200
        # servidor retorna HTML de login CDI
        assert b"CDI" in response.content or b"Carga y Despacho Inteligente" in response.content

    def test_health_endpoint(self, client):
        r = client.get('/health')
        assert r.status_code == 200
        assert r.json().get('status') == 'ok'
        # Campos extendidos opcionales
        data = r.json()
        assert 'generated_today' in data and 'generated_total' in data
        assert 'last_filename' in data and 'generated_bytes_total' in data

    def test_validate_items_edges(self, client):
        payload = {
            "items": [
                {"pieza":"8471","descripcion":"X","origen":"cn","cantidad":"10,5","valor_unitario":"20,00","peso_unitario":"1,0"},
                {"pieza":"","descripcion":"Y","origen":"AR","cantidad":"0","valor_unitario":"10","peso_unitario":"1"}
            ]
        }
        r = client.post('/validate_items/', json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data.get('success') is True
        assert 'errors' in data

    def test_validate_items_extra_rules_toggle(self, client):
        payload = {
            "items": [
                {"pieza":"8471","descripcion":"X","origen":"AR","cantidad":1,"valor_unitario":1,"peso_unitario":1},
                {"pieza":"123","descripcion":"Y","origen":"CN","cantidad":2000001,"valor_unitario":15000000,"peso_unitario":1}
            ],
            "extra_rules": True
        }
        r = client.post('/validate_items/', json=payload)
        assert r.status_code == 200
        data = r.json()
        # Debe reportar errores extra por NCM < 6 y límites altos
        assert any('NCM debería tener 6–8' in e for e in data.get('errors', []))
        assert any('cantidad parece inválida' in e for e in data.get('errors', []))
        assert any('valor unitario parece inválido' in e for e in data.get('errors', []))

    def test_validate_items_normalizes_origin_and_commas(self, client):
        payload = {
            "items": [
                {"pieza":"84713010","descripcion":"Laptop","origen":"argentina","cantidad":"2,5","valor_unitario":"1.000,50","peso_unitario":"1,25"},
                {"pieza":"85171200","descripcion":"Phone","origen":"br","cantidad":"10","valor_unitario":"120.00","peso_unitario":"0,30"}
            ]
        }
        r = client.post('/validate_items/', json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data.get('success') is True
        # Ambas filas deberían ser válidas tras normalización (AR -> ARG -> AR al recortar, números con coma)
        assert data.get('valid_count') == 2

    def test_validate_items_endpoint(self, client):
        payload = {
            "items": [
                {"pieza":"84713010","descripcion":"Laptop","origen":"CN","cantidad":2,"valor_unitario":800,"peso_unitario":2.2},
                {"pieza":"","descripcion":"Sin NCM","origen":"CN","cantidad":1,"valor_unitario":100,"peso_unitario":1.0}
            ]
        }
        r = client.post('/validate_items/', json=payload)
        assert r.status_code == 200
        data = r.json()
        assert data.get('success') is True
        assert data.get('valid_count') == 1
        assert len(data.get('errors', [])) >= 1

    def test_process_operation_success(self, client, cleanup_excel_files):
        auth = client.post("/auth/login", json={"username": "demo", "password": "demo123"}).json()
        headers = {"Authorization": f"Bearer {auth['access_token']}"}
        payload = {
            "operation_id": "API-TEST-001",
            "items": [
                {
                    "pieza": "84713010",
                    "descripcion": "Computadora portatil",
                    "cantidad": 2.0,
                    "valor_unitario": 1500.0,
                    "peso_unitario": 2.2,
                    "origen": "CN"
                },
                {
                    "pieza": "85414010",
                    "descripcion": "Diodos LED",
                    "cantidad": 100.0,
                    "valor_unitario": 0.5,
                    "peso_unitario": 0.1,
                    "origen": "CN"
                }
            ]
        }

        response = client.post("/process_operation/", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("filename", "").endswith(".xlsx")
        assert data.get("download_url", "").startswith("/download/")
        assert data.get("validated_items_count") == 2
        import os
        full_path = os.path.join('data', 'generated', data["filename"])
        assert os.path.exists(full_path)

    def test_process_operation_validation_errors(self, client, auth_headers):
        """Test procesamiento con errores de validación."""
        payload = {
            "operation_id": "API-TEST-ERRORS",
            "items": [
                {
                    "pieza": "",
                    "descripcion": "Producto inválido",
                    "cantidad": 1.0,
                    "valor_unitario": 100.0,
                    "peso_unitario": 1.0,
                    "origen": "AR"
                },
                {
                    "pieza": "84713010",
                    "descripcion": "Producto con valores negativos",
                    "cantidad": -5.0,
                    "valor_unitario": 500.0,
                    "peso_unitario": 1.0,
                    "origen": "AR"
                }
            ]
        }

        # El servidor rechaza datos inválidos con 422 o 200 con success=False
        response = client.post("/process_operation/", json=payload, headers=auth_headers)
        assert response.status_code in (200, 422)

        if response.status_code == 200:
            data = response.json()
            assert data.get("success") is False

    def test_process_operation_mixed_valid_invalid(self, client, auth_headers, cleanup_excel_files):
        """Test procesamiento con mezcla de items válidos e inválidos."""
        payload = {
            "operation_id": "API-TEST-MIXED",
            "items": [
                {
                    "pieza": "84713010",
                    "descripcion": "Producto válido",
                    "cantidad": 2.0,
                    "valor_unitario": 1500.0,
                    "peso_unitario": 2.0,
                    "origen": "AR"
                },
                {
                    "pieza": "",
                    "descripcion": "Producto inválido",
                    "cantidad": 1.0,
                    "valor_unitario": 100.0,
                    "peso_unitario": 1.0,
                    "origen": "AR"
                },
                {
                    "pieza": "85414010",
                    "descripcion": "Producto válido 2",
                    "cantidad": 50.0,
                    "valor_unitario": 2.5,
                    "peso_unitario": 0.5,
                    "origen": "CN"
                }
            ]
        }

        response = client.post("/process_operation/", json=payload, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is False
        assert data.get("detail") == "Todos los items deben tener NCM (pieza)"

    def test_process_operation_empty_items(self, client, auth_headers):
        """Test procesamiento con lista vacía de items."""
        payload = {
            "operation_id": "API-TEST-EMPTY",
            "items": []
        }

        response = client.post("/process_operation/", json=payload, headers=auth_headers)

        # En versión funcional, devuelve success=False sin lanzar error HTTP
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is False

    def test_process_operation_single_item(self, client, auth_headers, cleanup_excel_files):
        """Test procesamiento con un solo item."""
        payload = {
            "operation_id": "API-TEST-SINGLE",
            "items": [
                {
                    "pieza": "12345678",
                    "descripcion": "Producto único",
                    "cantidad": 1.0,
                    "valor_unitario": 1000.0,
                    "peso_unitario": 1.0,
                    "origen": "US"
                }
            ]
        }

        response = client.post("/process_operation/", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
        assert data.get("validated_items_count") == 1
        import os
        full_path = os.path.join('data', 'generated', data["filename"])
        assert os.path.exists(full_path)

    def test_process_operation_invalid_json(self, client, auth_headers):
        """Test envío de JSON inválido."""
        # Enviar JSON malformado
        response = client.post(
            "/process_operation/",
            data='{"operation_id": "TEST", "items": [invalid json}',
            headers={"Content-Type": "application/json", **auth_headers}
        )

        assert response.status_code == 422

    def test_process_operation_missing_fields(self, client, auth_headers):
        """Test envío de payload con campos faltantes."""
        # Payload sin operation_id
        payload = {
            "items": [
                {
                    "pieza": "84713010",
                    "descripcion": "Test",
                    "cantidad": 1.0,
                    "valor_unitario": 100.0,
                    "peso_unitario": 1.0,
                    "origen": "CN"
                }
            ]
        }

        response = client.post("/process_operation/", json=payload, headers=auth_headers)

        # En esta versión devolvemos success=False (no 422)
        assert response.status_code == 422

    def test_process_operation_invalid_item_data(self, client, auth_headers):
        """Test envío de datos de item inválidos."""
        payload = {
            "operation_id": "API-TEST-INVALID",
            "items": [
                {
                    "pieza": "84713010",
                    "descripcion": "Producto válido",
                    "cantidad": "not_a_number",
                    "valor_unitario": 100.0,
                    "peso_unitario": 1.0,
                    "origen": "CN"
                }
            ]
        }

        response = client.post("/process_operation/", json=payload, headers=auth_headers)

        # En esta versión devolvemos success=False (no 422)
        assert response.status_code == 422

    def test_excel_file_content_via_api(self, client, auth_headers, cleanup_excel_files):
        """Test que el Excel generado vía API tiene el contenido correcto."""
        import pandas as pd

        payload = {
            "operation_id": "API-CONTENT-TEST",
            "items": [
                {
                    "pieza": "84713010",
                    "descripcion": "Test product",
                    "origen": "CN",
                    "peso_unitario": 1.5,
                    "cantidad": 3.0,
                    "valor_unitario": 250.0,
                    "marca": "TEST"
                }
            ]
        }
        response = client.post("/process_operation/", json=payload, headers=auth_headers)
        assert response.status_code == 200
        filename = response.json()["filename"]
        import os
        full_path = os.path.join('data', 'generated', filename)
        df = pd.read_excel(full_path, engine='openpyxl')
        assert len(df) == 1

        # Verificar columnas dinámicamente (pueden variar según el generador)
        columns = list(df.columns)
        ncm_col = next((c for c in columns if 'pieza' in c.lower() or 'ncm' in c.lower() or 'código' in c.lower()), columns[0])
        cantidad_col = next((c for c in columns if 'cantidad' in c.lower() or 'qty' in c.lower()), None)

        # Verificar que tiene datos
        assert len(df) > 0
        if cantidad_col and cantidad_col in df.columns:
            assert float(df.iloc[0][cantidad_col]) == 3.0

    def test_api_handles_special_characters(self, client, auth_headers, cleanup_excel_files):
        """Test que la API maneja caracteres especiales correctamente."""
        payload = {
            "operation_id": "TEST-Ñ-Á-É-Í-Ó-Ú",
            "items": [
                {
                    "pieza": "84713010",
                    "descripcion": "Producto con ñames & símbolos @#$%",
                    "cantidad": 1.0,
                    "valor_unitario": 100.0,
                    "peso_unitario": 1.0,
                    "origen": "AR"
                }
            ]
        }

        response = client.post("/process_operation/", json=payload, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        import os
        full_path = os.path.join('data', 'generated', data["filename"])
        assert os.path.exists(full_path)

    def test_generated_endpoint_lists_files(self, client, auth_headers, cleanup_excel_files):
        # Generar un archivo
        payload = {
            "operation_id": "API-LIST-TEST",
            "items": [{"pieza": "84713010", "descripcion": "Test", "origen": "CN", "peso_unitario": 1.0, "cantidad": 1.0, "valor_unitario": 1.0}]
        }
        r1 = client.post('/process_operation/', json=payload, headers=auth_headers)
        assert r1.status_code == 200
        # Consultar listado
        r = client.get('/generated/')
        assert r.status_code == 200
        data = r.json()
        assert data.get('success') is True
        assert data.get('count', 0) >= 1
        assert isinstance(data.get('items'), list)

    def test_afip_auth_mock(self, client):
        r = client.get('/afip/auth/test')
        assert r.status_code == 200
        data = r.json()
        assert data.get('success') is True
        assert 'environment' in data
        assert 'ta_expires_at' in data

    def test_afip_cdc_constatar_mock(self, client):
        r = client.post('/afip/cdc/constatar', json={'cuit': '20301234567', 'numero': 'ABC123'})
        assert r.status_code == 200
        data = r.json()
        assert data.get('success') is True
        assert data.get('estado') in ('VALIDO','OBSERVADO')
        # Chequear /health refleja métricas
        h = client.get('/health').json()
        assert 'afip_auth_requests_total' in h
        assert 'afip_cdc_requests_total' in h
        assert 'afip_cdc_last_estado' in h

    def test_client_template_and_avg_blank(self, client):
        # Plantilla del cliente
        r1 = client.post('/api/clientes/1/plantilla')
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1.get('success') is True
        assert d1.get('filename','').endswith('.xlsx')
        assert d1.get('download_url','').startswith('/download/')
        # Plantilla AVG en blanco
        r2 = client.get('/api/plantillas/avg_blanco')
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2.get('success') is True
        assert d2.get('filename','').endswith('.xlsx')
        assert d2.get('download_url','').startswith('/download/')

    def test_export_csv_includes_valor_total_item(self, client):
        # Crear operación con items para export
        payload = {
            "operation_id": "API-CSV-TEST",
            "items": [
                {"pieza":"84713010","descripcion":"A","origen":"CN","cantidad":2,"valor_unitario":100.0,"peso_unitario":1.0},
                {"pieza":"85171200","descripcion":"B","origen":"BR","cantidad":3,"valor_unitario":50.0,"peso_unitario":0.5},
            ]
        }
        client.post('/process_operation/', json=payload)
        r = client.get('/api/clientes/1/export.csv')
        assert r.status_code == 200
        text = r.text
        assert 'valor_total_item' in text.splitlines()[0]

    def test_poc_ncm_suggest_endpoint(self, client):
        r1 = client.post('/ncm/suggest', json={'descripcion': 'Laptop portable de 14 pulgadas'})
        assert r1.status_code == 200
        s1 = r1.json().get('suggestions', [])
        assert any(s.get('ncm') == '84713010' for s in s1)
        r2 = client.post('/ncm/suggest', json={'descripcion': 'Producto desconocido'})
        assert r2.status_code == 200
        assert r2.json().get('success') is True

    def test_ncm_suggest_cache_hit_and_metrics(self, client, monkeypatch):
        # Forzar TTL alto y cache grande
        monkeypatch.setenv('NCM_CACHE_TTL', '3600')
        monkeypatch.setenv('NCM_CACHE_MAX', '10000')
        payload = {'descripcion': 'Laptop portable de 14 pulgadas'}
        r1 = client.post('/ncm/suggest', json=payload)
        assert r1.status_code == 200
        r2 = client.post('/ncm/suggest', json=payload)
        assert r2.status_code == 200
        # No tenemos campo cache_hit en todos los flujos, pero /health debe reflejar métricas
        h = client.get('/health').json()
        assert 'ncm_requests_total' in h
        assert 'ncm_cache_hit_rate' in h
        assert 'ncm_latency_p95_ms' in h

    def test_ncm_topk_env_limits_suggestions(self, client, monkeypatch):
        monkeypatch.setenv('NCM_TOPK_MAX', '2')
        r = client.post('/ncm/suggest', json={'descripcion': 'monitor lcd led router cable fuente teclado'})
        assert r.status_code == 200
        sugg = r.json().get('suggestions', [])
        assert len(sugg) <= 2

    def test_ncm_context_brand_category(self, client):
        r = client.post('/ncm/suggest', json={'descripcion': 'portatil 14 pulgadas', 'brand': 'Dell', 'category': 'computadora'})
        assert r.status_code == 200
        sugg = r.json().get('suggestions', [])
        # debería sesgar a laptop
        assert any(s.get('ncm') == '84713010' for s in sugg)

    def test_ncm_info_endpoint(self, client):
        r = client.get('/ncm/info/84713010')
        assert r.status_code == 200
        data = r.json()
        assert data.get('success') is True
        assert data.get('info', {}).get('ncm') in ('84713010','847130')
        r2 = client.get('/ncm/info/0101')
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2.get('success') is True
        assert d2.get('info', {}).get('familia') in ('Animales vivos','Carnes')

    def test_upload_excel_with_client_column_mapping(self, client):
        # Definir mapeo para cliente '1'
        mapping = {
            'codigo ncm': 'pieza',
            'detalle': 'descripcion',
            'pais': 'origen',
            'qty': 'cantidad',
            'price': 'valor_unitario',
            'weight': 'peso_unitario',
        }
        rmap = client.post('/api/clientes/1/column_mapping', json={'mapping': mapping})
        assert rmap.status_code == 200
        assert rmap.json().get('mapping', {}).get('qty') == 'cantidad'

        # Crear Excel en memoria con encabezados "raros"
        import pandas as pd
        from io import BytesIO
        df = pd.DataFrame([
            {"codigo ncm": "84713010", "detalle": "Laptop", "pais": "cn", "qty": 2, "price": 800, "weight": 2.2},
            {"codigo ncm": "85171200", "detalle": "Phone", "pais": "br", "qty": 10, "price": 120, "weight": 0.3},
        ])
        bio = BytesIO()
        with pd.ExcelWriter(bio, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Hoja1')
        bio.seek(0)

        # Subir Excel con client_id y esperar que aplique el mapeo
        files = { 'file': ('test.xlsx', bio.getvalue(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') }
        data = { 'client_id': '1' }
        r = client.post('/upload_excel/', files=files, data=data)
        assert r.status_code == 200
        resp = r.json()
        assert resp.get('success') is True
        items = resp.get('items') or []
        assert len(items) >= 2
        # Verificar que los campos canon se interpretaron
        assert set(items[0].keys()).issuperset({'pieza','descripcion','origen','cantidad','valor_unitario','peso_unitario'})
        assert items[0]['pieza'].startswith('8471')
        assert items[0]['origen'] in ('CN','BR','XX','AR','US','VN')

    def test_process_operation_requires_auth(self, client):
        payload = {"operation_id": "AUTH-TEST", "items": [{"pieza": "84713010", "descripcion": "Producto válido", "cantidad": 1.0, "valor_unitario": 100.0, "peso_unitario": 1.0, "origen": "CN"}]}
        response = client.post("/process_operation/", json=payload)
        assert response.status_code in (401, 403)

    def test_rate_limit_triggers_after_threshold(self, client, auth_headers, cleanup_excel_files):
        from proyecto_maria import main as srv

        payload = {
            "operation_id": "RATE-LIMIT",
            "items": [
                {
                    "pieza": "84713010",
                    "descripcion": "Producto válido",
                    "cantidad": 1.0,
                    "valor_unitario": 100.0,
                    "peso_unitario": 1.0,
                    "origen": "CN"
                }
            ]
        }

        limiter = srv.rate_limiter
        original_max = limiter.max_requests
        original_window = limiter.window
        try:
            limiter.max_requests = 1
            limiter.window = 60
            limiter.registry.clear()
            first = client.post("/process_operation/", json=payload, headers=auth_headers)
            assert first.status_code == 200
            second = client.post("/process_operation/", json=payload, headers=auth_headers)
            assert second.status_code == 429
        finally:
            limiter.max_requests = original_max
            limiter.window = original_window
            limiter.registry.clear()
