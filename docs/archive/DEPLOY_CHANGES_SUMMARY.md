# 📋 CDI MARÍA - Estado y Cambios

> **Este archivo es el contexto principal.** Léelo primero siempre.

---

## 🔧 Contexto Técnico

| Item | Valor |
|------|-------|
| **Proyecto** | Sistema para despachantes de aduana (importaciones) |
| **Ubicación** | `/Users/Emi/CDI/` |
| **Servidor** | `http://127.0.0.1:8010/` |
| **Usuarios** | Diseñado para 2000+ usuarios |
| **Backend** | FastAPI + Python 3.12 |
| **IA** | Google Gemini 2.0/2.5 Flash (Vision) |
| **DB Local** | SQLite (`test.db`) |
| **DB Prod** | PostgreSQL (Cloud SQL) |

### API Keys (en .env)

```bash
GEMINI_API_KEY="AIzaSy..."  # Para extraer PDFs
DATABASE_URL="sqlite+aiosqlite:///./test.db"
```

### Qué hace el sistema

1. **Sube PDF** de factura comercial
2. **Gemini Vision** extrae items (descripción, cantidad, precio, peso)
3. **Despachante** completa NCM manualmente
4. **Genera Excel AVG** para importar a MARIA
5. **Genera TXT MARIA** para AFIP

---

## 🆕 Cambios 6 Dic 2025

### ✨ Sugerir NCM con IA (DESHABILITADO - pendiente mejorar UI)
- Backend listo: `/api/ncm/sugerir`, `/api/ncm/guardar-uso`
- Historial se guarda en `data/ncm_historial.json`
- **Botón ✨ removido temporalmente** - el diseño interfería con la UI
- Para reactivar: agregar botón btn-suggest-ncm en app.js línea ~1783

### Historial de Operaciones
- Endpoint `/api/clientes/{id}/operaciones` funcional
- Endpoint `/api/clientes/{id}/metricas` agregado
- **CASCADE DELETE:** Eliminar cliente borra sus operaciones
- Modal historial muestra datos correctamente

### Notas por NCM (ARREGLADO)
- Backend completo: GET/POST/PUT/DELETE en `/api/ncm/notas`
- Guardado en `data/ncm_notas.json`
- Botón 📝 junto a cada campo NCM (naranja, visible)
- Modal para ver/agregar/editar notas
- **FIX:** Reactivada función `fetchNotasNCMThrottled` que estaba deshabilitada
- **FIX:** Validación de 4 dígitos mínimo antes de abrir modal

### Archivos Modificados
- `main.py` - Sanitización XSS con `html.escape()` en notas NCM
- `app.js` - Verificación automática de notas, botón 📝 pulsa rojo si hay notas
- `app.css` - Estilos botón morado y dropdown sugerencias

---

## 🎯 Estado Actual (6 Dic 2025)

| Componente | Estado |
|------------|--------|
| **Extracción PDF** | ✅ Multi-página, Gemini Vision |
| **NCM** | ✅ Vacío por defecto, con notas + sugerencias IA |
| **Sugerir NCM** | ✅ Historial + Gemini, botón ✨ |
| **Historial** | ✅ Por cliente, con métricas |
| **Excel AVG** | ✅ Permite NCM vacío |
| **MARIA TXT** | ✅ Requiere NCM, CPL/DVD/IEXT |

---

## 🆕 Cambios 5 Dic 2025

### Extracción PDF
- Multi-página: Gemini procesa hasta 10 páginas
- Código de Parte: Nuevo campo extraído
- NCM: Vacío por defecto (despachante completa)

### MARIA TXT
- Secciones `[CPL]` y `[DVD]` agregadas
- Flete/seguro proporcionales por item
- Campo `IEXT` con código de parte

### Validaciones
- Excel AVG permite NCM vacío
- MARIA TXT requiere NCM completo
- Código de Parte siempre opcional

### UI
- Columna "Cód.Parte" agregada
- Botón "Tributos" eliminado

### Archivos Modificados
- `pdf_extractor.py` - Multi-página, NCM vacío
- `maria_generator.py` - CPL, DVD, IEXT
- `excel_generator.py` - Columna Cod.Parte
- `app.js` - Validaciones, botón MARIA
- `dashboard.html` - Columna, sin Tributos
- `operations.py` - Campo codigo_parte

---

## 📅 Cambios 4 Dic 2025

### Deploy Prep
- Health check mejorado (verifica DB)
- Backup/restore endpoints
- Connection pooling (2000+ usuarios)
- HSTS configurable
- Cloud Build actualizado

### Seguridad
- Auditoría Red Team: 9/10 ataques bloqueados
- XSS arreglado con `html.escape`

---

## 🚀 Comandos Útiles

```bash
# Iniciar servidor (desarrollo)
cd /Users/Emi/CDI
set -a && source .env && set +a  # Cargar variables de .env
PYTHONPATH=. DATABASE_URL="sqlite+aiosqlite:///./test.db" \
uvicorn proyecto_maria.main:app --reload --port 8010

# Tests
pytest tests/test_regression_phase0.py -v --no-cov
```

---

## 📁 Archivos Clave

| Archivo | Descripción |
|---------|-------------|
| `main.py` | Entry point FastAPI |
| `pdf_extractor.py` | Extracción con Gemini |
| `maria_generator.py` | Genera TXT para MARIA |
| `excel_generator.py` | Genera Excel AVG |
| `.agent/workflows/campos-maria.md` | Formato MARIA AFIP |

---

## 🔗 Referencias

- **Formato MARIA:** `.agent/workflows/campos-maria.md`
- **Arquitectura técnica:** `ARCHITECTURE.md`
