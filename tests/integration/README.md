# Integration Tests - End-to-End Workflows

Tests de integración que prueban flujos completos de usuarios del sistema MARIA, simulando casos de uso reales.

## Workflows Identificados y Testeados

### 1. Client Creation & Management Workflow
**Casos de uso:**
- Crear un nuevo cliente
- Actualizar información del cliente
- Marcar cliente como favorito
- Gestionar operaciones del cliente
- Exportar datos a CSV
- Eliminar cliente

**Tests:**
- `test_complete_client_lifecycle` - Ciclo de vida completo
- `test_client_with_operations_workflow` - Cliente con operaciones asociadas

---

### 2. PDF Processing Workflow
**Casos de uso:**
- Subir factura PDF
- Extraer items automáticamente
- Generar archivo AVG para MARIA

**Tests:**
- `test_pdf_upload_and_extract_workflow` - Upload y extracción
- `test_pdf_to_avg_complete_workflow` - PDF → AVG completo

---

### 3. Calculator Workflow
**Casos de uso:**
- Calcular valor en plaza (FOB + tributos)
- Comparar costos desde diferentes orígenes
- Verificar beneficios MERCOSUR

**Tests:**
- `test_single_calculation_workflow` - Cálculo individual
- `test_origin_comparison_workflow` - Comparación de orígenes
- `test_calculator_with_examples_workflow` - Ejemplos pre-configurados
- `test_mercosur_benefit_calculation` - Verificar beneficio MERCOSUR

---

### 4. Item Correction Workflow
**Casos de uso:**
- Editar items después de extracción
- Duplicar items con modificaciones
- Operaciones batch (aplicar NCM a múltiples items)

**Tests:**
- `test_edit_single_item_workflow` - Edición individual
- `test_duplicate_item_workflow` - Duplicación con modificaciones
- `test_batch_update_workflow` - Operaciones batch

---

### 5. Template Creation & Reuse Workflow
**Casos de uso:**
- Guardar operación recurrente como plantilla
- Reutilizar plantilla cambiando cantidades/precios
- Ideal para importaciones mensuales

**Tests:**
- `test_template_creation_and_reuse_workflow` - Creación y reutilización

**Nota:** Requiere plan premium

---

### 6. Complete Import Operation Workflow
**Caso de uso:** Flujo end-to-end completo
- Cliente → Items → Cálculo → AVG Excel → Historial

**Tests:**
- `test_complete_import_flow` - Flujo completo de importación

---

### 7. Client Product History & Autocomplete Workflow
**Casos de uso:**
- Detectar cliente automáticamente desde PDF
- Autocompletar productos frecuentes
- Sugerencias basadas en historial

**Tests:**
- `test_client_detection_and_autocomplete` - Detección y autocompletado

---

### 8. Batch Operations Workflow
**Casos de uso:**
- Cambiar origen de múltiples items
- Aplicar NCM a grupo de productos
- Multiplicar cantidades globalmente

**Tests:**
- `test_batch_operations_workflow` - Operaciones masivas

---

## Ejecución

### Ejecutar todos los workflows
```bash
pytest tests/integration/test_workflows.py -v -m integration
```

### Ejecutar workflow específico
```bash
pytest tests/integration/test_workflows.py::TestClientCreationWorkflow -v
```

### Ejecutar con output detallado
```bash
pytest tests/integration/test_workflows.py -v -s
```

### Ver resumen de workflows disponibles
```bash
pytest tests/integration/test_workflows.py::test_all_workflows_summary -v -s
```

---

## Estructura de Tests

```
tests/integration/
├── __init__.py
├── README.md (este archivo)
└── test_workflows.py (16 tests en 8 workflows)
```

---

## Estadísticas

- **Workflows identificados:** 8
- **Tests creados:** 16
- **Endpoints testeados:** ~30+
- **Cobertura de funcionalidades:**
  - ✅ Gestión de clientes
  - ✅ Procesamiento de PDF
  - ✅ Calculadora de costos
  - ✅ Corrección de items
  - ✅ Plantillas (premium)
  - ✅ Operaciones completas
  - ✅ Autocompletado
  - ✅ Operaciones batch

---

## Fixtures Utilizados

Los tests utilizan fixtures de `conftest.py`:
- `client` - TestClient de FastAPI
- `sample_pdf` - PDF de ejemplo para testing
- `seeded_items` - Items pre-cargados para tests

---

## Notas Importantes

1. **Tests no destructivos:** Todos los tests limpian datos creados
2. **Auth mocking:** Algunos endpoints requieren autenticación (se usa bypass en tests)
3. **Archivos temporales:** Se crean archivos Excel que se eliminan automáticamente
4. **Premium features:** Template workflow requiere plan premium (puede fallar en tests básicos)

---

## Casos de Uso por Prioridad

### Alta Prioridad (Flujo crítico)
1. Complete Import Operation Workflow (end-to-end)
2. Client Creation & Management
3. PDF Processing Workflow

### Media Prioridad
4. Calculator Workflow
5. Item Correction Workflow
6. Batch Operations Workflow

### Baja Prioridad (Features avanzadas)
7. Template Creation & Reuse
8. Client Product History & Autocomplete

---

## Integración Continua

Estos tests están diseñados para ejecutarse en CI/CD:

```yaml
# .github/workflows/integration-tests.yml
- name: Run Integration Tests
  run: pytest tests/integration/ -v -m integration --tb=short
```

---

## Contribuir

Para agregar un nuevo workflow:

1. Identificar el caso de uso real
2. Crear clase `TestNombreWorkflow`
3. Implementar tests que simulen usuario real
4. Agregar documentación en este README
5. Actualizar estadísticas

**Template:**
```python
@pytest.mark.integration
class TestNuevoWorkflow:
    """
    Workflow N: Descripción

    User Story: [Historia de usuario]
    """

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_caso_completo(self, client):
        # STEP 1: Acción
        # STEP 2: Verificación
        pass
```

---

**Última actualización:** 2025-10-30
