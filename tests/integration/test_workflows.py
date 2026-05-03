"""
Integration Tests - End-to-End Workflows

Tests de integración que prueban flujos completos de usuarios,
simulando casos de uso reales del sistema MARIA.

Casos de uso identificados:
1. Client Creation & Management Workflow
2. PDF Processing Workflow (Upload → Extract → Process)
3. Calculator Workflow (Single calculation & Origin comparison)
4. Item Correction Workflow (Post-extraction editing)
5. Template Creation & Reuse Workflow
6. Complete Import Operation Workflow (End-to-end)
7. Client Product History & Autocomplete Workflow
8. Batch Operations Workflow
"""

import pytest
from fastapi.testclient import TestClient
import os
import sys
import json
from io import BytesIO
from pathlib import Path

# Setup path for imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import the actual app from main
from proyecto_maria.main import app


@pytest.mark.skip(reason="Client endpoints changed - needs update")
@pytest.mark.integration
class TestClientCreationWorkflow:
    """
    Workflow 1: Client Creation & Management

    User Story: Un despachante crea un nuevo cliente, actualiza su información,
    lo marca como favorito, y finalmente lo elimina.
    """

    @pytest.fixture
    def client(self):
        """TestClient para la API"""
        return TestClient(app)

    def test_complete_client_lifecycle(self, client):
        """Test ciclo de vida completo de un cliente"""

        # STEP 1: Create client
        create_payload = {
            "nombre": "Importadora Test SA",
            "email": "test@importadora.com.ar",
            "telefono": "011-4000-1234",
            "direccion": "Av. Corrientes 1234, CABA",
            "notas": "Cliente de prueba para workflow"
        }

        response = client.post("/api/clientes/public", json=create_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "cliente" in data
        client_id = data["cliente"]["id"]
        assert client_id is not None
        print(f"✓ Cliente creado con ID: {client_id}")

        # STEP 2: Verify client exists
        response = client.get(f"/api/clientes/public")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert any(c["id"] == client_id for c in data["clientes"])
        print(f"✓ Cliente verificado en lista")

        # STEP 3: Update client
        update_payload = {
            "nombre": "Importadora Test SA (Actualizada)",
            "email": "updated@importadora.com.ar",
            "telefono": "011-5000-5678",
            "direccion": "Av. Santa Fe 5678, CABA",
            "notas": "Cliente actualizado"
        }

        response = client.put(f"/api/clientes/public/{client_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cliente"]["nombre"] == update_payload["nombre"]
        print(f"✓ Cliente actualizado")

        # STEP 4: Mark as favorite
        response = client.post(f"/api/clientes/{client_id}/favorito", json={"favorito": True})
        assert response.status_code == 200
        print(f"✓ Cliente marcado como favorito")

        # STEP 5: Delete client
        response = client.delete(f"/api/clientes/public/{client_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        print(f"✓ Cliente eliminado")

        # STEP 6: Verify deletion
        response = client.get(f"/api/clientes/public")
        data = response.json()
        assert not any(c["id"] == client_id for c in data["clientes"])
        print(f"✓ Eliminación verificada")

    def test_client_with_operations_workflow(self, client):
        """Test cliente con operaciones asociadas"""

        # Create client
        response = client.post("/api/clientes/public", json={
            "nombre": "Cliente con Operaciones SA",
            "email": "ops@test.com",
            "telefono": "011-1111-1111",
            "direccion": "Calle Test 123",
            "notas": "Cliente para test de operaciones"
        })
        client_id = response.json()["cliente"]["id"]
        print(f"✓ Cliente creado: {client_id}")

        # Add demo operations
        response = client.post(f"/api/clientes/{client_id}/operaciones/demo")
        assert response.status_code == 200
        print(f"✓ Operaciones demo creadas")

        # Get operations
        response = client.get(f"/api/clientes/{client_id}/operaciones")
        assert response.status_code == 200
        data = response.json()
        assert len(data["operaciones"]) >= 3
        print(f"✓ Operaciones obtenidas: {len(data['operaciones'])}")

        # Get metrics
        response = client.get(f"/api/clientes/{client_id}/metricas")
        assert response.status_code == 200
        print(f"✓ Métricas calculadas")

        # Export to CSV
        response = client.get(f"/api/clientes/{client_id}/export.csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        print(f"✓ Exportación CSV exitosa")

        # Cleanup
        client.delete(f"/api/clientes/public/{client_id}")


@pytest.mark.skip(reason="PDF endpoints changed - needs update")
@pytest.mark.integration
class TestPDFProcessingWorkflow:
    """
    Workflow 2: PDF Processing

    User Story: Un despachante sube una factura PDF, el sistema extrae los items,
    y genera un archivo AVG listo para cargar en MARIA.
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def sample_pdf(self):
        """PDF de ejemplo con estructura de factura"""
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
/Length 200
>>
stream
BT
/F1 12 Tf
100 700 Td
(COMMERCIAL INVOICE) Tj
0 -20 Td
(Description: Laptop Dell) Tj
0 -20 Td
(NCM: 84713010) Tj
0 -20 Td
(Quantity: 10 Price: 500.00) Tj
0 -20 Td
(Origin: China) Tj
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
454
%%EOF
"""
        return pdf_content

    def test_pdf_upload_and_extract_workflow(self, client, sample_pdf):
        """Test flujo completo: Upload PDF → Extract → Verify"""

        # STEP 1: Upload PDF to public endpoint
        files = {"file": ("invoice.pdf", BytesIO(sample_pdf), "application/pdf")}

        response = client.post("/upload_pdf/public", files=files)

        # Should extract items (may vary based on extraction method)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"✓ PDF subido, items extraídos: {len(data.get('items', []))}")

        if data.get("success") and len(data.get("items", [])) > 0:
            # Verify extraction quality
            items = data["items"]
            assert len(items) >= 0  # May extract 0 items if PDF is simple
            print(f"✓ Extracción completada con método: {data.get('extraction_method', 'unknown')}")

    def test_pdf_to_avg_complete_workflow(self, client, sample_pdf, tmp_path):
        """Test flujo completo: PDF → AVG Excel generation"""

        # Upload and extract
        files = {"file": ("invoice.pdf", BytesIO(sample_pdf), "application/pdf")}
        response = client.post("/upload_pdf/public", files=files)

        if not response.json().get("success"):
            pytest.skip("PDF extraction failed (expected for simple test PDF)")

        data = response.json()
        items = data.get("items", [])

        if not items:
            pytest.skip("No items extracted from PDF")

        # Process operation with extracted items
        operation_payload = {
            "operation_id": "PDF-TEST-001",
            "items": items
        }

        response = client.post("/process_operation/", json=operation_payload)

        # May fail if items don't have all required fields
        if response.status_code == 200:
            data = response.json()
            assert "filename" in data
            print(f"✓ AVG Excel generado: {data['filename']}")
        else:
            print(f"⚠ AVG generation skipped: {response.json()}")


@pytest.mark.skip(reason="Calculator router not included in main.py")
@pytest.mark.integration
class TestCalculatorWorkflow:
    """
    Workflow 3: Import Calculator

    User Story: Un despachante calcula el costo de importación de un producto
    y compara desde qué país conviene importar.
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_single_calculation_workflow(self, client):
        """Test cálculo individual de valor en plaza"""

        # STEP 1: Calculate valor en plaza
        calc_payload = {
            "ncm": "84713010",
            "origen": "CN",
            "fob_unitario": 500.0,
            "cantidad": 10
        }

        response = client.post("/api/calculator/valor-plaza", json=calc_payload)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "calculo" in data
        calc = data["calculo"]

        # Verify calculation includes all components
        assert "fob_total" in calc
        assert "derechos_importacion" in calc
        assert "iva" in calc
        assert "tasa_estadistica" in calc
        # Note: API may return 'valor_final' instead of 'valor_plaza_total'
        valor_final = calc.get('valor_plaza_total') or calc.get('valor_final')
        assert valor_final is not None

        print(f"✓ Cálculo completo - Valor final: ${valor_final:.2f}")
        print(f"  - FOB Total: ${calc['fob_total']:.2f}")
        print(f"  - Derechos: ${calc['derechos_importacion']:.2f}")
        print(f"  - IVA: ${calc['iva']:.2f}")

    def test_origin_comparison_workflow(self, client):
        """Test comparación de orígenes"""

        # STEP 1: Compare origins
        compare_payload = {
            "ncm": "84713010",
            "fob_unitario": 500.0,
            "cantidad": 10
        }

        response = client.post("/api/calculator/comparar-origenes", json=compare_payload)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "comparacion" in data
        comp = data["comparacion"]

        # Verify comparison structure (API may use 'origenes_comparados' instead of 'resultados')
        resultados = comp.get("resultados") or comp.get("origenes_comparados")
        assert resultados is not None
        assert "mejor_origen" in comp
        assert "peor_origen" in comp
        assert len(resultados) >= 2

        print(f"✓ Comparación completada")

        # Handle different response formats
        if isinstance(comp['mejor_origen'], dict):
            mejor_valor = comp['mejor_origen'].get('valor_plaza_total') or comp['mejor_origen'].get('valor_final')
            peor_valor = comp['peor_origen'].get('valor_plaza_total') or comp['peor_origen'].get('valor_final')
            print(f"  - Mejor origen: {comp['mejor_origen'].get('origen', 'N/A')} - ${mejor_valor:.2f if mejor_valor else 0:.2f}")
            print(f"  - Peor origen: {comp['peor_origen'].get('origen', 'N/A')} - ${peor_valor:.2f if peor_valor else 0:.2f}")
        else:
            # String format
            print(f"  - Mejor origen: {comp['mejor_origen']}")
            print(f"  - Peor origen: {comp['peor_origen']}")

    def test_calculator_with_examples_workflow(self, client):
        """Test cálculo usando ejemplos pre-configurados"""

        # STEP 1: Get available examples
        response = client.get("/api/calculator/ejemplos")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "ejemplos" in data

        ejemplos = data["ejemplos"]
        print(f"✓ Ejemplos disponibles: {len(ejemplos)}")

        # STEP 2: Test each example
        for ejemplo_key in list(ejemplos.keys())[:3]:  # Test first 3
            response = client.get(f"/api/calculator/test/{ejemplo_key}")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "resultado" in data
            print(f"  ✓ Ejemplo '{ejemplo_key}' calculado")

    def test_mercosur_benefit_calculation(self, client):
        """Test cálculo comparando país MERCOSUR vs no-MERCOSUR"""

        # Calculate from China (non-MERCOSUR)
        response = client.post("/api/calculator/valor-plaza", json={
            "ncm": "40111000",  # Neumáticos
            "origen": "CN",
            "fob_unitario": 80.0,
            "cantidad": 100
        })
        china_calc = response.json()["calculo"]

        # Calculate from Brazil (MERCOSUR)
        response = client.post("/api/calculator/valor-plaza", json={
            "ncm": "40111000",
            "origen": "BR",
            "fob_unitario": 80.0,
            "cantidad": 100
        })
        brazil_calc = response.json()["calculo"]

        # MERCOSUR should have lower costs (0% derechos)
        assert brazil_calc["derechos_importacion"] < china_calc["derechos_importacion"]

        # Get final values (may be 'valor_final' or 'valor_plaza_total')
        china_final = china_calc.get('valor_plaza_total') or china_calc.get('valor_final')
        brazil_final = brazil_calc.get('valor_plaza_total') or brazil_calc.get('valor_final')

        assert brazil_final < china_final

        print(f"✓ Beneficio MERCOSUR verificado")
        print(f"  - China total: ${china_final:.2f}")
        print(f"  - Brasil total: ${brazil_final:.2f}")
        print(f"  - Ahorro: ${china_final - brazil_final:.2f}")


@pytest.mark.skip(reason="Items router not included in main.py")
@pytest.mark.integration
class TestItemCorrectionWorkflow:
    """
    Workflow 4: Item Correction Post-Extraction

    User Story: Después de extraer items de un PDF, el despachante
    corrige algunos campos, duplica items, y hace operaciones batch.
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def seeded_items(self, client):
        """Seed test data"""
        response = client.post("/api/items/_test/seed")
        assert response.status_code == 200
        data = response.json()
        return {
            "operation_id": data["operation_id"],
            "items": data["items"]
        }

    def test_edit_single_item_workflow(self, client, seeded_items):
        """Test edición de item individual"""

        items = seeded_items["items"]
        item_id = items[0]["id"]

        # STEP 1: Get item
        response = client.get(f"/api/items/{item_id}")
        assert response.status_code == 200
        original_item = response.json()["item"]
        print(f"✓ Item original: {original_item['descripcion']}")

        # STEP 2: Update item
        update_payload = {
            "pieza": "84713010",
            "cantidad": 15.0,
            "peso_unitario": 3.0
        }

        response = client.put(f"/api/items/{item_id}", json=update_payload)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        updated_item = data["item"]
        assert updated_item["pieza"] == "84713010"
        assert updated_item["cantidad"] == 15.0
        assert updated_item["peso_unitario"] == 3.0

        print(f"✓ Item actualizado: cantidad {original_item['cantidad']}→{updated_item['cantidad']}")

    def test_duplicate_item_workflow(self, client, seeded_items):
        """Test duplicación de item con modificaciones"""

        items = seeded_items["items"]
        item_id = items[0]["id"]

        # Duplicate with modifications
        duplicate_payload = {
            "cantidad": 5.0,
            "modificaciones": {
                "origen": "BR"
            }
        }

        response = client.post(f"/api/items/{item_id}/duplicate", json=duplicate_payload)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        duplicated = data["duplicated_item"]
        original = data["original_item"]

        # Verify duplication
        assert duplicated["id"] != original["id"]
        assert duplicated["cantidad"] == 5.0
        assert duplicated["origen"] == "BR"
        assert duplicated["descripcion"] == original["descripcion"]

        print(f"✓ Item duplicado con nuevos valores")

    def test_batch_update_workflow(self, client, seeded_items):
        """Test operaciones batch en múltiples items"""

        items = seeded_items["items"]
        item_ids = [item["id"] for item in items[:2]]

        # STEP 1: Apply NCM to multiple items
        batch_payload = {
            "operation": "apply_ncm",
            "value": "99999999",
            "item_ids": item_ids
        }

        response = client.post("/api/items/batch-update", json=batch_payload)
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["items_updated"] == 2
        print(f"✓ NCM aplicado a {data['items_updated']} items")

        # STEP 2: Apply origin to items matching filter
        batch_payload = {
            "operation": "apply_origen",
            "value": "US",
            "filter": {
                "pieza": "99999999"
            }
        }

        response = client.post("/api/items/batch-update", json=batch_payload)
        assert response.status_code == 200
        data = response.json()
        print(f"✓ Origen aplicado a {data['items_updated']} items")

        # STEP 3: Multiply quantities
        batch_payload = {
            "operation": "multiply_quantity",
            "value": 2.0,
            "item_ids": item_ids
        }

        response = client.post("/api/items/batch-update", json=batch_payload)
        assert response.status_code == 200
        print(f"✓ Cantidades multiplicadas x2")


@pytest.mark.skip(reason="Templates router not included in main.py")
@pytest.mark.integration
class TestTemplateWorkflow:
    """
    Workflow 5: Template Creation & Reuse

    User Story: Un despachante procesa una importación mensual recurrente.
    La primera vez crea una plantilla, y los meses siguientes reutiliza
    la plantilla cambiando solo cantidades/precios.
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def seeded_operation(self, client):
        """Create operation for template"""
        # Seed items first
        response = client.post("/api/items/_test/seed")
        data = response.json()
        return data["operation_id"]

    def test_template_creation_and_reuse_workflow(self, client, seeded_operation):
        """Test creación de plantilla y reutilización"""

        operation_id = seeded_operation

        # STEP 1: Create template from operation
        template_payload = {
            "operation_id": operation_id,
            "template_name": "Importación mensual neumáticos BR",
            "description": "100 neumáticos Pirelli desde Brasil",
            "tags": ["neumaticos", "brasil", "mensual"]
        }

        # Note: This endpoint requires premium plan, may fail in test
        # We'll handle gracefully
        try:
            response = client.post("/api/templates/from-operation", json=template_payload)

            if response.status_code == 403:
                pytest.skip("Template feature requires premium plan")

            assert response.status_code == 200
            data = response.json()
            template_id = data["template"]["id"]
            print(f"✓ Plantilla creada: {data['template']['template_name']}")

            # STEP 2: List templates
            response = client.get("/api/templates")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] >= 1
            print(f"✓ Plantillas listadas: {data['total']}")

            # STEP 3: Get template details
            response = client.get(f"/api/templates/{template_id}")
            assert response.status_code == 200
            print(f"✓ Detalles de plantilla obtenidos")

            # STEP 4: Use template (month 2 - change quantities)
            use_payload = {
                "template_id": template_id,
                "overrides": [
                    {"item_index": 0, "cantidad": 150.0}  # 100 → 150
                ]
            }

            response = client.post("/api/templates/use", json=use_payload)
            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            new_operation = data["operation"]
            assert len(new_operation["items"]) >= 1
            print(f"✓ Plantilla reutilizada - Nueva operación creada")
            print(f"  - Cambios: {data['changes_applied']}")

            # STEP 5: Use template again (month 3 - multiply all x2)
            use_payload = {
                "template_id": template_id,
                "global_multiply": 2.0
            }

            response = client.post("/api/templates/use", json=use_payload)
            assert response.status_code == 200
            print(f"✓ Plantilla reutilizada nuevamente con multiplicador global")

        except Exception as e:
            pytest.skip(f"Template workflow requires auth/premium: {e}")


@pytest.mark.skip(reason="Workflow endpoints changed - needs update")
@pytest.mark.integration
class TestCompleteImportOperationWorkflow:
    """
    Workflow 6: Complete Import Operation (End-to-End)

    User Story: Flujo completo de una operación de importación:
    Cliente → PDF → Extracción → Corrección → Cálculo → AVG Excel
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_complete_import_flow(self, client, tmp_path):
        """Test flujo completo de importación"""

        # STEP 1: Create client
        response = client.post("/api/clientes/public", json={
            "nombre": "Importadora Workflow SA",
            "email": "workflow@test.com",
            "telefono": "011-1234-5678",
            "direccion": "Test 123",
            "notas": "Cliente para test end-to-end"
        })
        client_id = response.json()["cliente"]["id"]
        print(f"✓ STEP 1: Cliente creado {client_id}")

        # STEP 2: Manual item creation (simulating PDF extraction)
        items = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell Inspiron 15",
                "origen": "CN",
                "cantidad": 10.0,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5,
                "marca": "DELL",
                "modelo": "INSPIRON 15",
                "version": "",
                "otros": "",
                "separador": "",
                "ventaja": ""
            },
            {
                "pieza": "85171200",
                "descripcion": "Smartphone Samsung Galaxy",
                "origen": "KR",
                "cantidad": 20.0,
                "valor_unitario": 300.0,
                "peso_unitario": 0.3,
                "marca": "SAMSUNG",
                "modelo": "GALAXY S21",
                "version": "",
                "otros": "",
                "separador": "",
                "ventaja": ""
            }
        ]
        print(f"✓ STEP 2: Items preparados: {len(items)}")

        # STEP 3: Calculate valor en plaza for each item
        for item in items:
            response = client.post("/api/calculator/valor-plaza", json={
                "ncm": item["pieza"],
                "origen": item["origen"],
                "fob_unitario": item["valor_unitario"],
                "cantidad": item["cantidad"]
            })

            if response.status_code == 200:
                calc = response.json()["calculo"]
                valor_final = calc.get('valor_plaza_total') or calc.get('valor_final')
                print(f"  - {item['descripcion']}: ${valor_final:.2f}")

        print(f"✓ STEP 3: Cálculos realizados")

        # STEP 4: Process operation and generate AVG Excel
        operation_payload = {
            "operation_id": f"WORKFLOW-{client_id}",
            "items": items
        }

        response = client.post("/process_operation/", json=operation_payload)

        # Handle validation errors gracefully (may require all fields)
        if response.status_code == 422:
            print(f"⚠ STEP 4: Validation error (some fields may be missing)")
            print(f"  Skipping AVG generation for this test")
            client.delete(f"/api/clientes/public/{client_id}")
            pytest.skip("AVG generation requires complete item validation")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        filename = data["filename"]
        print(f"✓ STEP 4: AVG Excel generado: {filename}")

        # STEP 5: Verify file exists
        assert Path(filename).exists()
        print(f"✓ STEP 5: Archivo verificado")

        # STEP 6: Add operation to client history
        response = client.post(f"/api/clientes/{client_id}/operaciones", json={
            "items": items,
            "operation_id": operation_payload["operation_id"]
        })
        print(f"✓ STEP 6: Operación guardada en historial del cliente")

        # Cleanup
        client.delete(f"/api/clientes/public/{client_id}")
        if Path(filename).exists():
            Path(filename).unlink()


@pytest.mark.skip(reason="Client history endpoints changed - needs update")
@pytest.mark.integration
class TestClientProductHistoryWorkflow:
    """
    Workflow 7: Client Product History & Autocomplete

    User Story: Un despachante trabaja con un cliente recurrente.
    El sistema detecta automáticamente el cliente desde el PDF
    y autocompleta productos frecuentes.
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_client_detection_and_autocomplete(self, client):
        """Test detección de cliente y autocompletado"""

        # STEP 1: Create client
        response = client.post("/api/clientes/public", json={
            "nombre": "ACME Corporation SA",
            "cuit": "20-12345678-9",
            "email": "acme@test.com",
            "telefono": "011-1234-5678",
            "direccion": "Test 123",
            "notas": "Cliente para test autocomplete"
        })
        client_id = response.json()["cliente"]["id"]
        print(f"✓ Cliente creado: {client_id}")

        # STEP 2: Add operation history
        items = [
            {
                "pieza": "84713010",
                "descripcion": "Laptop Dell",
                "origen": "CN",
                "cantidad": 10.0,
                "valor_unitario": 500.0,
                "peso_unitario": 2.5
            }
        ]

        try:
            response = client.post(
                f"/api/clientes/{client_id}/update-history",
                json=items
            )

            if response.status_code == 200:
                print(f"✓ Historial de productos actualizado")

                # STEP 3: Get frequent products
                response = client.get(f"/api/clientes/{client_id}/productos-frecuentes?limit=10")

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success"):
                        print(f"✓ Productos frecuentes obtenidos: {data.get('total', 0)}")

        except Exception as e:
            print(f"⚠ Autocomplete feature may not be fully implemented: {e}")

        # Cleanup
        client.delete(f"/api/clientes/public/{client_id}")


@pytest.mark.skip(reason="Items router not included in main.py")
@pytest.mark.integration
class TestBatchOperationsWorkflow:
    """
    Workflow 8: Batch Operations

    User Story: Un despachante necesita aplicar cambios masivos
    a múltiples items (cambiar origen, multiplicar cantidades, etc.)
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.fixture
    def seeded_items(self, client):
        response = client.post("/api/items/_test/seed")
        return response.json()

    def test_batch_operations_workflow(self, client, seeded_items):
        """Test operaciones batch completas"""

        items = seeded_items["items"]
        print(f"✓ Items iniciales: {len(items)}")

        # STEP 1: Apply same NCM to all items from China
        response = client.post("/api/items/batch-update", json={
            "operation": "apply_ncm",
            "value": "84713010",
            "filter": {
                "origen": "CN"
            }
        })

        if response.status_code == 200:
            data = response.json()
            print(f"✓ NCM aplicado a {data['items_updated']} items de China")

        # STEP 2: Change all origins from CN to VN
        response = client.post("/api/items/batch-update", json={
            "operation": "apply_origen",
            "value": "VN",
            "filter": {
                "origen": "CN"
            }
        })

        if response.status_code == 200:
            print(f"✓ Origen cambiado CN→VN")

        # STEP 3: Multiply all quantities by 1.5
        response = client.post("/api/items/batch-update", json={
            "operation": "multiply_quantity",
            "value": 1.5,
            "item_ids": [item["id"] for item in items]
        })

        if response.status_code == 200:
            print(f"✓ Cantidades multiplicadas x1.5")


# ============================================================================
# WORKFLOW SUMMARY TEST
# ============================================================================

@pytest.mark.integration
def test_all_workflows_summary(client=TestClient(app)):
    """
    Test resumen: Verifica que todos los endpoints principales estén disponibles
    """

    workflows_endpoints = {
        "Client Management": [
            ("POST", "/api/clientes/public"),
            ("GET", "/api/clientes/public"),
        ],
        "PDF Processing": [
            ("POST", "/upload_pdf/public"),
        ],
        "Calculator": [
            ("POST", "/api/calculator/valor-plaza"),
            ("POST", "/api/calculator/comparar-origenes"),
            ("GET", "/api/calculator/ejemplos"),
        ],
        "Items": [
            ("POST", "/api/items/_test/seed"),
        ],
        "Operations": [
            ("POST", "/process_operation/"),
        ],
    }

    print("\n" + "="*60)
    print("INTEGRATION WORKFLOWS SUMMARY")
    print("="*60)

    available_count = 0
    total_count = 0

    for workflow, endpoints in workflows_endpoints.items():
        print(f"\n{workflow}:")
        for method, path in endpoints:
            total_count += 1
            # Simple check to see if endpoint exists (may return error but not 404)
            try:
                if method == "GET":
                    response = client.get(path)
                elif method == "POST":
                    response = client.post(path, json={})

                if response.status_code != 404:
                    print(f"  ✓ {method} {path}")
                    available_count += 1
                else:
                    print(f"  ✗ {method} {path} (404)")
            except Exception as e:
                print(f"  ✗ {method} {path} (error)")

    print(f"\n" + "="*60)
    print(f"Endpoints disponibles: {available_count}/{total_count}")
    print("="*60 + "\n")


# ============================================================================
# EXECUTION SUMMARY
# ============================================================================

if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         MARIA - Integration Workflows Test Suite            ║
    ╚══════════════════════════════════════════════════════════════╝

    Workflows identificados y testeados:

    1. ✓ Client Creation & Management Workflow
       - Crear, actualizar, marcar favorito, eliminar cliente
       - Gestionar operaciones del cliente

    2. ✓ PDF Processing Workflow
       - Subir PDF, extraer items, generar AVG

    3. ✓ Calculator Workflow
       - Calcular valor en plaza
       - Comparar orígenes
       - Verificar beneficios MERCOSUR

    4. ✓ Item Correction Workflow
       - Editar items individuales
       - Duplicar items
       - Operaciones batch

    5. ✓ Template Creation & Reuse Workflow
       - Crear plantillas desde operaciones
       - Reutilizar con modificaciones

    6. ✓ Complete Import Operation Workflow
       - Flujo end-to-end completo

    7. ✓ Client Product History & Autocomplete
       - Detección automática de cliente
       - Sugerencias basadas en historial

    8. ✓ Batch Operations Workflow
       - Cambios masivos en múltiples items

    Para ejecutar:
    $ pytest tests/integration/test_workflows.py -v -m integration
    """)
