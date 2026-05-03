# 🧹 PLAN DE LIMPIEZA DEL PROYECTO CDI

**Fecha:** 2025-10-31
**Análisis completo del proyecto** para identificar archivos innecesarios, duplicados o viejos.

---

## 📊 RESUMEN EJECUTIVO

| Categoría | Archivos/Dirs | Espacio | Riesgo |
|-----------|---------------|---------|--------|
| Cache Python (__pycache__) | 17 dirs | ~10 MB | ✅ BAJO |
| Backups viejos (.tar.gz) | 2 archivos | 33 MB | ✅ BAJO |
| Reportes de tests | ~20 archivos | ~9 MB | ✅ BAJO |
| Coverage reports | 3 items | 7 MB | ✅ BAJO |
| Data backups (timestamped) | 20 dirs | 170 KB | ✅ BAJO |
| Archivos temporales/vacíos | 9 archivos | <1 KB | ✅ BAJO |
| Tests antiguos (/tests/old) | 1 dir | 163 KB | ⚠️ MEDIO |
| Google Cloud SDK | 1 dir | 68 MB | ⚠️ MEDIO |
| Google Cloud CLI (macOS) | 1 archivo | 55 MB | ⚠️ MEDIO |
| PostgreSQL data (pgdata) | 1 dir | 47 MB | 🔴 ALTO |

**TOTAL POTENCIAL DE LIMPIEZA: ~230 MB**

---

## 🎯 PLAN DE LIMPIEZA POR FASES

### ✅ FASE 1: LIMPIEZA SEGURA (~60 MB)
**Riesgo: BAJO** - Archivos regenerables automáticamente

#### 1.1 Cache de Python (10 MB)
```bash
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete
rm -rf .pytest_cache
```

**Qué elimina:**
- 17 directorios `__pycache__`
- Todos los archivos `.pyc` compilados
- Cache de pytest

**Por qué es seguro:** Se regeneran automáticamente al ejecutar Python.

#### 1.2 Coverage Reports (7 MB)
```bash
rm -rf htmlcov/
rm .coverage coverage.xml
```

**Qué elimina:**
- Directorio `htmlcov/` con reportes HTML
- Base de datos `.coverage`
- Reporte XML `coverage.xml`

**Por qué es seguro:** Se regeneran con `pytest --cov`.

#### 1.3 Backups Comprimidos Viejos (33 MB)
```bash
rm backup_fase0_completada_20250926_212157.tar.gz
rm backup_testing_framework_20250926_203624.tar.gz
```

**Qué elimina:**
- 2 backups de Septiembre 2025 (hace más de 1 mes)

**Por qué es seguro:** Código en git, backups obsoletos.

#### 1.4 Reportes de Tests (9 MB)
```bash
rm report_final.html report_load_test.html report_workers.html
rm test_*.html  # Varios reportes pequeños
rm FASE1_TEST_REPORT.json testing_report_1760755341240.json
rm redis_performance_report_20250930_185829.json
rm server.log
```

**Qué elimina:**
- 10+ reportes HTML de tests
- 3 reportes JSON
- Log del servidor

**Por qué es seguro:** Outputs regenerables, datos históricos.

#### 1.5 Archivos Vacíos/Temporales (<1 KB)
```bash
rm cost_analysis_gemini.py debug_gemini_direct.py list_gemini_models.py
rm test_fixed_prompt.py test_gemini_always.py test_gemini_confusion.py
rm test_gemini_with_pdf.py test_infrastructure.py test_nuevo_prompt.py
```

**Qué elimina:**
- 9 archivos Python vacíos o stubs (2 bytes cada uno)

**Por qué es seguro:** No contienen código útil.

#### 1.6 Backups Timestamped Antiguos (170 KB)
```bash
rm -rf backups/data_202510*/  # 20 directorios de backups viejos
```

**Qué elimina:**
- 20 backups timestamped de Octubre 20-26

**Por qué es seguro:** Backups antiguos, datos en BD.

#### 1.7 Data Generated & LocalStorage Backups (80 KB)
```bash
rm -rf data/generated/PLANTILLA_*.xlsx
rm data/localStorage_backup_*.json
```

**Qué elimina:**
- 8 archivos Excel generados
- 4 backups de localStorage

**Por qué es seguro:** Datos de test regenerables.

---

### ⚠️ FASE 2: LIMPIEZA MODERADA (~123 MB)
**Riesgo: MEDIO** - Requiere verificación antes de eliminar

#### 2.1 Tests Antiguos (163 KB)
```bash
rm -rf tests/old/
```

**Qué elimina:**
- Directorio `tests/old/` con 12 archivos de test antiguos

**VERIFICAR ANTES:**
- ✅ Que los tests nuevos cubran la funcionalidad
- ✅ Que no haya dependencias en código activo

#### 2.2 Google Cloud CLI para macOS (55 MB)
```bash
rm google-cloud-cli-darwin-x86_64.tar.gz
```

**Qué elimina:**
- Instalador de Google Cloud CLI para macOS

**VERIFICAR ANTES:**
- ✅ Que no necesites deployment en macOS
- ✅ Sistema es Linux, no macOS

#### 2.3 Google Cloud SDK Local (68 MB)
```bash
rm -rf google-cloud-sdk/
```

**Qué elimina:**
- SDK completo de Google Cloud (68 MB)

**VERIFICAR ANTES:**
- ✅ Si tienes `gcloud` instalado en sistema (`which gcloud`)
- ✅ Si scripts de deployment dependen de este directorio
- ⚠️ **NO ELIMINAR** si usas scripts locales que dependen de este path

---

### 🔴 FASE 3: LIMPIEZA CRÍTICA (47 MB)
**Riesgo: ALTO** - Solo con confirmación explícita

#### 3.1 PostgreSQL Data Directory (47 MB)
```bash
rm -rf proyecto_maria/pgdata/
```

**Qué elimina:**
- Datos de PostgreSQL local

**⚠️ SOLO ELIMINAR SI:**
- [ ] Usas BD en cloud/remota (no local)
- [ ] Tienes backup completo de datos
- [ ] pgdata está vacío o corrupto
- [ ] No usas PostgreSQL localmente

**🚨 NO ELIMINAR SI:**
- BD local está en uso
- Datos no están respaldados
- Desarrollo local depende de estos datos

---

## 📋 RECOMENDACIÓN DE EJECUCIÓN

### Opción A: LIMPIEZA CONSERVADORA (60 MB)
Ejecutar solo **FASE 1** - Todo es seguro y regenerable.

```bash
# Script de limpieza segura
./cleanup_safe.sh
```

### Opción B: LIMPIEZA COMPLETA (183 MB)
Ejecutar **FASE 1 + FASE 2** - Requiere verificación.

```bash
# Script de limpieza completa
./cleanup_full.sh
```

### Opción C: LIMPIEZA TOTAL (230 MB)
Ejecutar **TODAS LAS FASES** - Solo si pgdata no es necesario.

```bash
# Script de limpieza total (¡CUIDADO!)
./cleanup_total.sh
```

---

## 🛡️ ARCHIVOS PROTEGIDOS (NO TOCAR)

Estos archivos/directorios **NUNCA** se eliminarán:

- ✅ `/proyecto_maria/` - Código fuente activo
- ✅ `/tests/` - Tests activos (excepto `/tests/old`)
- ✅ `.env` - Configuración de entorno
- ✅ `requirements.txt` - Dependencias
- ✅ `pytest.ini` - Configuración de tests
- ✅ `.git/` - Historial de git
- ✅ `.gitignore` - Reglas de git
- ✅ Documentación principal (README, docs/)

---

## 📝 MEJORAS ADICIONALES

### Agregar a .gitignore
Si no están ya incluidos:

```gitignore
__pycache__/
*.pyc
.pytest_cache/
htmlcov/
.coverage
coverage.xml
*.log
*.bak
*.tmp
*~
.DS_Store
```

---

## ❓ ¿QUÉ OPCIÓN PREFIERES?

**Responde con:**
- `1` → Fase 1 solo (60 MB, SEGURO)
- `2` → Fase 1 + 2 (183 MB, verificar antes)
- `3` → Todo (230 MB, requiere confirmación de pgdata)
- `custom` → Dime qué eliminar específicamente

**O responde con preguntas si necesitas más info sobre algún archivo.**
