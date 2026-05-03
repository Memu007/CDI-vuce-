# 🚀 PLAN DE FEATURES VENDIBLES - PROYECTO MARÍA

**Fecha creación**: 2025-09-30
**Objetivo**: Implementar features de alto impacto para despachantes chicos/medianos
**Filosofía**: Sin over-engineering, 100% vibe coding, máximo ROI

---

## 📋 LISTA DE FEATURES PRIORIZADAS

### ✅ **Feature #1: Auto-completado Inteligente de Datos**
**Prioridad**: ALTA ⭐⭐⭐
**Tiempo estimado**: 2-3 horas
**Impacto**: 70% de datos pre-cargados automáticamente

#### Problema que resuelve
- Despachante procesa mismo cliente mes tras mes
- Mismos productos, mismo proveedor, mismos NCM
- Tipear todo de nuevo cada vez = pérdida de tiempo

#### Solución técnica
1. **Detección de cliente**:
   - Al subir PDF, buscar CUIT o nombre de empresa
   - Endpoint: `GET /api/clientes/detect?cuit={cuit}&nombre={nombre}`
   - Retorna: `{client_id, nombre, historial_ncm, proveedores_frecuentes}`

2. **Historial de productos por cliente**:
   - Guardar en DB: `client_id → {ncm, descripcion, peso_unitario_avg, origen_frecuente}`
   - Endpoint: `GET /api/clientes/{id}/productos-frecuentes`
   - Al extraer PDF, si detecta descripción similar → auto-completar NCM

3. **Sugerencias inteligentes**:
   - Si item tiene descripción pero no NCM → buscar en historial del cliente
   - Si proveedor conocido → pre-cargar origen
   - Calcular peso unitario promedio de últimas 5 operaciones

#### Endpoints a crear
```python
# 1. Detección automática de cliente
GET /api/clientes/detect?text={extracted_text}
Response: {
  "client_id": "123",
  "nombre": "Importadora ABC",
  "confidence": 0.85,
  "suggestions": {
    "ncm_frecuentes": ["84713010", "85171200"],
    "origen_frecuente": "CN",
    "peso_unitario_promedio": 2.5
  }
}

# 2. Productos frecuentes del cliente
GET /api/clientes/{id}/productos-frecuentes
Response: {
  "productos": [
    {
      "descripcion": "laptop dell",
      "ncm": "84713010",
      "peso_unitario_avg": 2.5,
      "origen_frecuente": "CN",
      "veces_usado": 15
    }
  ]
}

# 3. Auto-completar items
POST /api/items/autocomplete
Body: {
  "client_id": "123",
  "items": [
    {"descripcion": "laptop dell inspiron", "ncm": "", "peso_unitario": 0}
  ]
}
Response: {
  "items": [
    {
      "descripcion": "laptop dell inspiron",
      "ncm": "84713010",  # auto-completado
      "peso_unitario": 2.5,  # auto-completado
      "origen": "CN",  # auto-completado
      "confidence": 0.9
    }
  ]
}
```

#### Archivos a modificar
- `proyecto_maria/services/client_service.py` (agregar métodos de historial)
- `proyecto_maria/routers/client_router.py` (nuevos endpoints)
- `proyecto_maria/database/models.py` (tabla `client_product_history`)

---

### ✅ **Feature #2: Corrección Rápida Post-Extracción**
**Prioridad**: ALTA ⭐⭐⭐
**Tiempo estimado**: 3-4 horas
**Impacto**: Correcciones de 10 minutos a 1 minuto

#### Problema que resuelve
- PDF extrae 80% bien, pero 2-3 items necesitan ajuste
- Copiar/pegar/editar en Excel es lento
- Errores manuales al reescribir

#### Solución técnica
1. **Endpoint de actualización individual**:
   ```python
   PUT /api/items/{item_id}
   Body: {"ncm": "84713010", "cantidad": 15, "peso_unitario": 3.0}
   ```

2. **Operaciones batch**:
   ```python
   POST /api/items/batch-update
   Body: {
     "operation": "apply_ncm_to_all",
     "ncm": "84713010",
     "filter": {"descripcion_contains": "laptop"}
   }
   ```

3. **Duplicar item**:
   ```python
   POST /api/items/{item_id}/duplicate
   Body: {"cantidad": 5}  # cambiar solo cantidad
   ```

#### Frontend (referencia para frontend dev)
- Tabla editable con ag-grid o similar
- Click en celda → edit mode
- Botones: "Duplicar", "Aplicar NCM a similares", "Eliminar"
- Validación en tiempo real (NCM válido, cantidad > 0, etc.)

#### Archivos a modificar
- `proyecto_maria/routers/pdf_router.py` (endpoints de edición)
- Nuevo: `proyecto_maria/routers/items_router.py` (CRUD de items)

---

### ✅ **Feature #3: Validación Pre-envío con Alertas**
**Prioridad**: MEDIA ⭐⭐
**Tiempo estimado**: 2-3 horas
**Impacto**: Cero rechazos por errores evitables

#### Problema que resuelve
- AFIP rechaza después de enviar (pérdida de tiempo)
- Errores de NCM, permisos faltantes, valores incorrectos

#### Solución técnica
1. **Validador completo**:
   ```python
   POST /api/operations/validate
   Body: {
     "items": [...],
     "tipo_operacion": "importacion"
   }
   Response: {
     "valid": false,
     "errors": [
       {
         "item_id": 1,
         "type": "error",
         "message": "NCM 1234 no existe",
         "field": "ncm",
         "suggestion": "Usar 84713010"
       }
     ],
     "warnings": [
       {
         "item_id": 2,
         "type": "warning",
         "message": "Este NCM requiere permiso SENASA",
         "action": "Solicitar certificado sanitario"
       }
     ],
     "info": [
       {
         "item_id": 3,
         "type": "info",
         "message": "Origen BR = preferencia arancelaria MERCOSUR",
         "saving": "15% ahorro en derechos"
       }
     ]
   }
   ```

2. **Reglas de validación**:
   - NCM válido (existe en catálogo)
   - Permisos especiales (SENASA, ANMAT, etc.)
   - Preferencias arancelarias (MERCOSUR)
   - Valores sospechosos (muy bajos/altos)

#### Archivos a crear
- Nuevo: `proyecto_maria/core/validations_advanced.py`
- Modificar: `proyecto_maria/routers/pdf_router.py`

---

### ✅ **Feature #4: Plantilla "Despacho Express"**
**Prioridad**: MEDIA ⭐⭐
**Tiempo estimado**: 2 horas
**Impacto**: Despachos recurrentes en 30 segundos

#### Solución técnica
```python
# Guardar como plantilla
POST /api/operations/{id}/save-as-template
Body: {"template_name": "Importación mensual ABC"}

# Listar plantillas del cliente
GET /api/clientes/{id}/templates

# Usar plantilla
POST /api/operations/from-template
Body: {
  "template_id": "123",
  "overrides": {
    "items": [
      {"item_id": 1, "cantidad": 50, "valor_unitario": 600}
    ]
  }
}
```

#### Archivos a crear
- Nuevo: `proyecto_maria/models/templates.py`
- Modificar: `proyecto_maria/routers/client_router.py`

---

### ✅ **Feature #5: Exportación Multi-Formato**
**Prioridad**: BAJA ⭐
**Tiempo estimado**: 3 horas
**Impacto**: De 15 minutos a 1 click

#### Solución técnica
```python
POST /api/operations/{id}/export-all
Response: {
  "zip_url": "/download/export_op123_20250930.zip",
  "files": [
    "AVG_op123.xlsx",
    "Resumen_op123.pdf",
    "Datos_op123.csv",
    "SIMI_op123.txt"
  ]
}
```

#### Archivos a modificar
- `proyecto_maria/routers/pdf_router.py` (endpoint export)
- Usar: `pandas` (Excel/CSV), `reportlab` (PDF), `zipfile` (ZIP)

---

### ✅ **Feature #6: Calculadora Valor en Plaza**
**Prioridad**: ALTA ⭐⭐⭐
**Tiempo estimado**: 2-3 horas
**Impacto**: Justificación automática ante Aduana

#### Problema que resuelve
- Aduana cuestiona valores muy bajos
- Necesito calcular: FOB + tributos + costos = CIF

#### Solución técnica
```python
POST /api/calculator/valor-plaza
Body: {
  "ncm": "84713010",
  "origen": "CN",
  "fob_unitario": 500,
  "cantidad": 10
}
Response: {
  "fob_total": 5000,
  "derechos_importacion": 2050,  # 41% del NCM
  "iva": 1481,  # 21% de (FOB + derechos)
  "tasa_estadistica": 150,  # 3%
  "flete_estimado": 200,  # 4% aprox
  "seguro_estimado": 50,  # 1%
  "cif_total": 8931,
  "valor_plaza_unitario": 893.10,
  "breakdown": {
    "base_imponible": 7050,
    "tributos_totales": 3681,
    "porcentaje_tributos": "52.2%"
  }
}
```

#### Fórmulas
```python
def calcular_valor_plaza(ncm, origen, fob_unitario, cantidad):
    # 1. Obtener tasa de derechos según NCM
    derechos_rate = get_ncm_rate(ncm, origen)  # ej: 0.41 para 41%

    # 2. Calcular derechos
    fob_total = fob_unitario * cantidad
    derechos = fob_total * derechos_rate

    # 3. Base imponible para IVA
    base_iva = fob_total + derechos
    iva = base_iva * 0.21

    # 4. Tasa estadística
    tasa_estadistica = fob_total * 0.03

    # 5. Flete y seguro (estimados)
    flete = fob_total * 0.04
    seguro = fob_total * 0.01

    # 6. CIF total
    cif_total = fob_total + derechos + iva + tasa_estadistica + flete + seguro

    return {
        "fob_total": fob_total,
        "derechos_importacion": derechos,
        "iva": iva,
        "tasa_estadistica": tasa_estadistica,
        "flete_estimado": flete,
        "seguro_estimado": seguro,
        "cif_total": cif_total,
        "valor_plaza_unitario": cif_total / cantidad
    }
```

#### Archivos a crear
- Nuevo: `proyecto_maria/core/calculator.py`
- Nuevo: `proyecto_maria/routers/calculator_router.py`

---

## 📅 CRONOGRAMA DE IMPLEMENTACIÓN

### **Semana 1 (2025-09-30 → 2025-10-06)**
- **Día 1-2**: Feature #1 Auto-completado Inteligente (2-3h)
- **Día 3-4**: Feature #2 Corrección Rápida (3-4h)
- **Día 5**: Feature #6 Calculadora Valor Plaza (2-3h)

### **Semana 2 (2025-10-07 → 2025-10-13)**
- **Día 1**: Feature #3 Validación Pre-envío (2-3h)
- **Día 2**: Feature #4 Plantilla Express (2h)
- **Día 3**: Feature #5 Exportación Multi-Formato (3h)

**Total estimado**: 14-18 horas de desarrollo

---

## 🎯 CRITERIOS DE ÉXITO

### Feature #1 - Auto-completado
- ✅ Detecta cliente por CUIT/nombre con 80%+ precisión
- ✅ Auto-completa NCM en 70%+ de items conocidos
- ✅ Reduce tiempo de carga manual en 60%+

### Feature #2 - Corrección Rápida
- ✅ Edición in-place funcional
- ✅ Aplicar cambios batch (NCM a todos)
- ✅ Validación en tiempo real

### Feature #3 - Validación
- ✅ Detecta NCM inválidos 100%
- ✅ Identifica permisos especiales (SENASA, etc.)
- ✅ Sugiere optimizaciones (MERCOSUR)

### Feature #4 - Plantillas
- ✅ Guardar operación como template
- ✅ Reutilizar con cambios mínimos
- ✅ Generar despacho en <1 min

### Feature #5 - Exportación
- ✅ 4 formatos simultáneos (Excel, PDF, CSV, TXT)
- ✅ ZIP descargable
- ✅ Generación <5 segundos

### Feature #6 - Calculadora
- ✅ Cálculo correcto de tributos
- ✅ Estimación flete/seguro razonable
- ✅ Breakdown detallado de costos

---

## 🔧 STACK TÉCNICO A USAR

### Backend
- **FastAPI**: Endpoints REST
- **SQLAlchemy**: Queries de historial
- **Pandas**: Exportación Excel/CSV
- **ReportLab**: Generación PDF
- **Python zipfile**: Comprimir archivos

### Base de Datos (nuevas tablas)
```sql
-- Historial de productos por cliente
CREATE TABLE client_product_history (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    ncm VARCHAR(8),
    descripcion VARCHAR(200),
    peso_unitario_avg FLOAT,
    origen_frecuente VARCHAR(3),
    veces_usado INTEGER,
    ultima_vez TIMESTAMP
);

-- Templates de operaciones
CREATE TABLE operation_templates (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    template_name VARCHAR(100),
    items JSONB,
    created_at TIMESTAMP
);
```

---

## 📝 NOTAS PARA OTRAS IAs

### Contexto para continuidad
- **Objetivo**: Features vendibles con mínimo esfuerzo
- **Usuario**: Developer con escaso conocimiento técnico (necesita todo explicado y probado)
- **No hacer**: Over-engineering, arquitecturas complejas, asumir conocimiento previo
- **Sí hacer**:
  - Código simple, funcional, probado manualmente
  - **SIEMPRE incluir instancias de prueba** (curl, ejemplos, datos de test)
  - **SIEMPRE documentar cómo probar** cada feature
  - **SIEMPRE crear datos demo** para testing sin setup complejo

### Archivos clave modificados
1. `proyecto_maria/routers/client_router.py` (auto-completado)
2. `proyecto_maria/routers/pdf_router.py` (corrección, validación)
3. `proyecto_maria/core/calculator.py` (nuevo - calculadora)
4. `proyecto_maria/database/models.py` (nuevas tablas)

### Comandos útiles
```bash
# Crear migración DB
alembic revision -m "add client product history"

# Ejecutar servidor en desarrollo
PYTHONPATH=. uvicorn proyecto_maria.server_funcional:app --reload --port 8001

# Probar endpoint
curl -X POST http://localhost:8001/api/items/autocomplete \
  -H "Content-Type: application/json" \
  -d '{"client_id": "1", "items": [{"descripcion": "laptop"}]}'
```

---

## 📊 ESTADO DE IMPLEMENTACIÓN

### ✅ Completadas y Probadas
- **Feature #1**: Auto-completado Inteligente (1.5h) - ✅ Tests OK
- **Feature #6**: Calculadora Valor en Plaza (2h) - ✅ 7/7 tests pasaron

### ⏳ Pendientes
- Feature #2: Corrección Rápida Post-Extracción (~3-4h)
- Feature #3: Validación Pre-envío (~2-3h)
- Feature #4: Plantilla Despacho Express (~2h)
- Feature #5: Exportación Multi-Formato (~3h)

---

## 📈 PROGRESO GENERAL

**Completado**: 2/6 features (33%)
**Tiempo invertido**: 4 horas (3.5h código + 0.5h testing)
**Endpoints creados**: 10 (todos funcionando)
**Tests ejecutados**: 7/7 (100% pasaron)
**Bugs encontrados**: 0

---

**Estado**: ✅ Features #1 y #6 COMPLETADAS Y PROBADAS
**Última actualización**: 2025-09-30
**Siguiente paso**: Elegir Feature #2, #3 o #4 para próxima sesión
