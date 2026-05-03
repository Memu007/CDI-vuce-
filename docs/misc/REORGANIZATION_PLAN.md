# 📁 PLAN DE REORGANIZACIÓN DEL PROYECTO

**Objetivo:** Organizar archivos sueltos en carpetas lógicas sin romper funcionalidad

---

## 📊 ANÁLISIS ACTUAL

**Archivos en raíz:** ~100 archivos sueltos
**Problema:** Difícil navegar y encontrar archivos

---

## 🎯 ESTRUCTURA PROPUESTA

```
CDI/
├── README.md                    ← Mantener en raíz (entrada principal)
├── Dockerfile                   ← Mantener (deployment)
├── docker-compose.yml           ← Mantener (deployment)
├── cloudbuild.yaml             ← Mantener (CI/CD)
├── requirements.txt            ← Mantener (dependencies)
├── pytest.ini                  ← Mantener (test config)
├── .env, .env.example          ← Mantener (config)
├── .gitignore, .dockerignore   ← Mantener (git)
├── firebase.json, .firebaserc  ← Mantener (firebase)
│
├── docs/                       ← NUEVA: Toda la documentación
│   ├── deployment/            ← Deployment docs
│   ├── testing/               ← Testing reports
│   ├── security/              ← Security reports
│   ├── guides/                ← Guías de uso
│   └── project/               ← Docs del proyecto
│
├── scripts/                    ← NUEVA: Scripts de bash
│   ├── deployment/            ← Deploy scripts
│   ├── setup/                 ← Setup scripts
│   └── testing/               ← Test scripts
│
├── debug/                      ← NUEVA: Scripts de debug viejos
│   ├── test_*.py              ← Tests antiguos de debug
│   └── debug_*.py             ← Scripts de debug
│
├── config/                     ← NUEVA: Archivos de configuración
│   ├── ecosystem.config.js
│   ├── package.json
│   └── otros configs
│
├── proyecto_maria/             ← Código fuente (sin cambios)
└── tests/                      ← Tests oficiales (sin cambios)
```

---

## 📦 ARCHIVOS A MOVER

### 1. DOCS/ - Documentación (50 archivos)

#### docs/deployment/
- DEPLOYMENT_GUIDE.md
- DEPLOYMENT_QUICK_START.md
- PRE_DEPLOYMENT_CHECKLIST.md
- GOOGLE_CLOUD_DEPLOYMENT.md
- LOGGING_AND_MONITORING_GUIDE.md
- PRE_PRODUCTION_TESTING_PLAN.md

#### docs/testing/
- FINAL_TEST_REPORT.md
- TESTING_SUMMARY.md
- INTEGRATION_TESTS_SUMMARY.md
- REPORTE_TESTING_E2E.md
- LOAD_TEST_FINAL_RESULTS.md
- GUIA_TESTING_5_USUARIOS.md
- TEST_REPORT_TARIFAR_VUCE.txt
- testing_report.md

#### docs/security/
- SECURITY_FINAL_EXECUTIVE_SUMMARY.md
- SECURITY_VALIDATION_REPORT.md
- SECURITY_INTEGRATION_TESTING_REPORT.md
- SECURITY_INTEGRATION_TESTING_REPORT_ITERATION_2.md
- SECURITY_INTEGRATION_TESTING_REPORT_ITERATION_3.md
- BLUE_TEAM_SECURITY_FIXES.md
- PENTEST_RED_TEAM_REPORT.md
- FINAL_ATTACK_RETEST_REPORT.md
- SECURITY-IMPROVEMENTS.md

#### docs/audits/
- AUDITORIA_COMPLETA_FINAL.md
- AUDITORIA_PRE_TESTING_5_USUARIOS.md
- VERIFICACION_FINAL_COMPLETADA.md

#### docs/guides/
- 00_INDEX.md
- 01_PROYECTO.md
- 02_ESTADO_ACTUAL.md
- 03_HISTORIAL.md
- 04_COMO_USAR.md
- 05_ROADMAP.md
- INSTRUCCIONES_CAMBIO_AI.md
- INSTRUCCIONES_SCRIPT_AI.md
- README_CAMBIAR_AI.md
- RESUMEN_CAMBIO_AI.md
- RESUMEN_FINAL_CAMBIO_AI.md

#### docs/fixes/
- FIX-EXCEL-DOWNLOAD.md
- FIX_ERROR_422_EXCEL_DOWNLOAD.md
- FIX_NUCLEAR_APLICADO.md
- AHORA_PROBAR_Y_VER_ERROR_REAL.md
- SERVIDOR_REINICIADO_PROBAR_AHORA.md

#### docs/features/
- CAMBIOS-LANDING.md
- INTEGRACION-LOGIN-LANDING.md
- IMPLEMENTACION_COMPLETA_EVIDENCIA.md
- RESUMEN_IMPLEMENTACION_FINAL.md
- SISTEMA_ERROR_TRACKING.md

#### docs/misc/
- CLEANUP_PLAN.md
- MCP_INSTALLATION_REPORT.md
- MCP_TOOLS_INSTALADOS.md

---

### 2. SCRIPTS/ - Scripts de bash (15 archivos)

#### scripts/deployment/
- deploy-cloud-run.sh
- test-docker-local.sh

#### scripts/setup/
- install_fase1.sh
- install_mcp_tools.sh
- setup_postgres.sh
- setup_redis.sh

#### scripts/testing/
- smoke.sh
- smoke_test.sh
- test.sh
- test_all_features.sh
- test_calculator.sh

#### scripts/utils/
- cambiar_ai.sh
- cambiar_modelo_ai.sh
- rotate_logs.sh
- backup_data.py

#### scripts/run/
- dev.sh
- prod.sh
- start.sh
- start_server.sh

---

### 3. DEBUG/ - Scripts de debug viejos (30 archivos)

Todos los archivos `test_*.py` y `debug_*.py` que NO están en /tests/:
- debug_endpoint_simulation.py
- debug_fac_vernol.py
- debug_facturas_sistematico.py
- debug_gemini_pdf.py
- debug_pdf_extraction.py
- diagnostico_pdf.py
- test_cascade_simulation.py
- test_contexto_pdfs_confusos.py
- test_endpoint_llm.py
- test_factura_china.py
- test_fallback_cascade.py
- test_gemini_extraction.py
- test_gemini_final.py
- test_gemini_forensics.py
- test_gemini_now.py
- test_improved_prompt.py
- test_llm_direct.py
- test_llm_mejorado.py
- test_ocr_vernol.py
- test_pdf_extraction.py
- test_quick_fallback.py
- test_redis_integration.py
- test_redis_performance.py
- test_robust_multicapa.py
- test_separacion_descripcion.py
- test_simple_ncm.py
- pdf_extractor.py
- ejemplo_uso.py
- run_tests.py

#### debug/test_data/
- test_factura.pdf
- prueba_formato_diferente.xlsx
- test_facturas.xlsx

---

### 4. CONFIG/ - Configuración (5 archivos)

- ecosystem.config.js
- package.json
- package-lock.json
- docker-compose.yml → Ya está en raíz, dejar ahí
- e2e_tests.js

---

### 5. ARCHIVOS A MANTENER EN RAÍZ

**Esenciales para desarrollo:**
- README.md
- Dockerfile
- .dockerignore
- cloudbuild.yaml
- requirements.txt
- requirements-db.txt
- pytest.ini
- .env
- .env.example
- ENV.example
- .gitignore
- .firebaserc
- firebase.json
- __init__.py
- main.py
- main_clean.py
- locustfile.py
- sentry_integration.py
- server_simple_mejorado.py

**¿Consideraciones especiales?**
- cost_analysis_report.json → ¿Mover a docs/misc/?
- env_database.txt, env_logging.txt → ¿Mover a config/ o eliminar?
- test_ncm_browser.js → ¿Mover a debug/?

---

## ⚠️ ARCHIVOS QUE REQUIEREN DECISIÓN

### Posiblemente eliminar (ya obsoletos):
- ENV.example (duplicado de .env.example)
- main_clean.py (¿duplicado de main.py?)
- server_simple_mejorado.py (¿versión vieja?)
- env_database.txt, env_logging.txt (¿necesarios?)

### Posiblemente consolidar:
- Multiple security reports → Mantener solo último?
- Multiple iteration reports → Archivar viejos?

---

## 🔧 ACTUALIZACIONES NECESARIAS

Después de mover archivos, actualizar referencias en:

1. **README.md** - Links a documentación movida
2. **Scripts de deployment** - Paths a otros scripts
3. **Documentación** - Links internos entre docs

---

## ✅ VERIFICACIÓN POST-REORGANIZACIÓN

Después de mover, verificar:
- [ ] Scripts de deployment siguen funcionando
- [ ] Tests siguen corriendo
- [ ] Links en documentación funcionan
- [ ] No hay imports rotos en Python

---

## 🎯 RESULTADO ESPERADO

**Raíz limpia:**
~20 archivos esenciales (vs 100 actuales)

**Fácil navegación:**
- ¿Documentación? → docs/
- ¿Scripts? → scripts/
- ¿Tests oficiales? → tests/
- ¿Debug viejo? → debug/

**Nada roto:**
- Deployment funciona
- Tests corren
- Development workflow igual

---

## ❓ DECISIONES PENDIENTES

1. **¿Eliminar archivos obsoletos?** (ENV.example, main_clean.py, etc)
2. **¿Archivar reports viejos?** (iteration 1, 2 de security)
3. **¿Mover google-cloud-cli-darwin-x86_64.tar.gz?** (55MB)
4. **¿Qué hacer con test_ncm_browser.js?**

---

## 🚀 PRÓXIMOS PASOS

1. **Revisar plan** - ¿Algo que no se deba mover?
2. **Aprobar cambios** - ¿Proceder con reorganización?
3. **Ejecutar movimientos** - Mover archivos a nuevas carpetas
4. **Actualizar referencias** - Arreglar links y paths
5. **Verificar** - Testear que nada se rompió
6. **Commit** - Commitear reorganización

---

**¿Apruebas este plan de reorganización?**

Responde:
- **Si** → Procedo con la reorganización completa
- **Si pero...** → Dime qué modificar del plan
- **No** → Cancelamos la reorganización
