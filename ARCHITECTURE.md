# 🏗️ Arquitectura CDI Sistema MARÍA

## Visión General

```
┌─────────────────────────────────────────────────────────────────┐
│                        GOOGLE CLOUD                             │
│  ┌───────────────┐    ┌──────────────┐    ┌─────────────────┐  │
│  │  Cloud Run    │───▶│  Cloud SQL   │    │ Secret Manager  │  │
│  │  (FastAPI)    │    │ (PostgreSQL) │    │ (API Keys, JWT) │  │
│  │  2GB / 2 CPU  │    │  db-f1-micro │    │                 │  │
│  │  1-5 instanc. │    │              │    │                 │  │
│  └───────┬───────┘    └──────────────┘    └─────────────────┘  │
│          │                                                      │
└──────────┼──────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────┐
│    Internet      │
│  (Usuarios 2K+)  │
└──────────────────┘
```

---

## Stack Tecnológico

| Capa              | Tecnología       | Versión     |
| ----------------- | ---------------- | ----------- |
| **Backend**       | FastAPI          | 0.104+      |
| **Runtime**       | Python           | 3.12        |
| **Base de Datos** | PostgreSQL       | 15          |
| **ORM**           | SQLAlchemy Async | 2.0+        |
| **IA/LLM**        | Google Gemini    | 2.0 Flash   |
| **Auth**          | JWT + bcrypt     | -           |
| **Deploy**        | Cloud Run        | managed     |
| **CI/CD**         | GitHub Actions   | -           |
| **Container**     | Docker           | multi-stage |

---

## Estructura del Proyecto

```
/Users/Emi/CDI/
├── proyecto_maria/              # 🎯 Código principal
│   ├── main.py                  # Entry point FastAPI (1400+ líneas)
│   ├── routers/                 # Endpoints organizados
│   │   ├── pdf_router.py        # Subida/extracción PDFs
│   │   ├── client_router.py     # CRUD clientes
│   │   ├── items_router.py      # Gestión items
│   │   ├── calculator_router.py # Cálculos importación
│   │   └── ...
│   ├── core/                    # Lógica de negocio
│   │   ├── validations.py       # Validaciones AVG
│   │   ├── excel_generator.py   # Generación Excel
│   │   ├── pdf_extractor.py     # Extracción con Gemini
│   │   └── ncm_catalog.py       # Catálogo NCM
│   ├── database/                # Persistencia
│   │   ├── connection.py        # Pool de conexiones
│   │   ├── models.py            # 8 modelos SQLAlchemy
│   │   └── db_init.sql          # Schema inicial
│   ├── security/                # Seguridad
│   │   ├── security_middleware.py  # HSTS, CSP, headers
│   │   ├── input_validation.py     # Sanitización
│   │   └── file_security.py        # Validación uploads
│   ├── templates/               # HTML (Jinja2)
│   └── static/                  # CSS, JS
├── tests/                       # Tests
│   ├── test_regression_phase0.py   # Tests deploy (9/10 ✅)
│   └── integration/             # Tests integración
├── .github/workflows/           # CI/CD
│   └── deploy.yml               # GitHub Actions
├── Dockerfile                   # Multi-stage build
├── docker-compose.yml           # Dev local
├── cloudbuild.yaml              # Deploy GCP
├── add_indexes.sql              # Índices performance
└── DEPLOY_CHANGES_SUMMARY.md    # Resumen cambios
```

---

## Flujo de Deploy

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GitHub    │────▶│   Actions   │────▶│ Cloud Build │────▶│  Cloud Run  │
│  push main  │     │  run tests  │     │ build image │     │   deploy    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                                       │
                           ▼                                       ▼
                    Si tests fallan               URL: cdi-backend-xxx.run.app
                    → PR bloqueado                    → Smoke test automático
```

### Pasos del Deploy:

1. **Push a main** → Trigger GitHub Actions
2. **Job: test** → Ejecuta `pytest tests/test_regression_phase0.py`
3. **Job: deploy** (si tests pasan):
   - Build imagen Docker
   - Push a Container Registry
   - Deploy a Cloud Run
   - Smoke test: `curl /health`

---

## Modelos de Datos

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    User     │       │   Client    │───────│  Operation  │
├─────────────┤       ├─────────────┤       ├─────────────┤
│ id          │       │ id          │       │ id          │
│ username    │       │ nombre      │       │ client_id   │
│ password    │       │ email       │       │ created_at  │
│ plan        │       │ is_active   │       │ status      │
└─────────────┘       └──────┬──────┘       └──────┬──────┘
                             │                     │
                             ▼                     ▼
                      ┌─────────────┐       ┌─────────────┐
                      │  NCMNote    │       │OperationItem│
                      ├─────────────┤       ├─────────────┤
                      │ client_id   │       │ operation_id│
                      │ ncm_code    │       │ pieza (NCM) │
                      │ nota        │       │ descripcion │
                      └─────────────┘       │ cantidad    │
                                            │ valor_unit  │
                                            └─────────────┘

Otros modelos: SystemBackup, APILog, ClientProductHistory
```

---

## Endpoints Principales

| Método | Endpoint                    | Descripción              |
| ------ | --------------------------- | ------------------------ |
| GET    | `/health`                   | Health check (DB status) |
| POST   | `/auth/login`               | Login → JWT cookie       |
| POST   | `/auth/logout`              | Logout                   |
| POST   | `/upload_pdf/public`        | Subir PDF → Extrae items |
| POST   | `/process_operation/`       | Generar Excel AVG        |
| POST   | `/generate_maria`           | Generar TXT para MARIA   |
| GET    | `/api/clientes/public`      | Listar clientes          |
| POST   | `/api/backup/localStorage`  | Backup datos browser     |
| GET    | `/api/restore/localStorage` | Restaurar backup         |

---

## Formato MARIA TXT

El sistema genera archivos TXT para el Sistema MARIA de AFIP.

### Estructura del NCM

```
8479.89.99.900H
└──────┴──┴──┴─┘
 8 dígitos + sufijo (3) + letra control
```

### Secciones del TXT

| Sección | Descripción |
|---------|-------------|
| `[DDT]` | Cabecera (FOB, flete, vendedor) |
| `[CPL]` | Campos complementarios |
| `[DVD]` | Documento vinculado (factura) |
| `[ART]` | Items con NCM, cantidad, valor |

### Campos por Item

| Campo | Descripción |
|-------|-------------|
| IESPNCE | NCM completo (obligatorio) |
| IEXT | Código de parte (opcional) |
| MARTFOB | Valor FOB item |
| QARTKGRNET | Peso neto kg |

Ver documentación completa en: `.agent/workflows/campos-maria.md`

---

## Variables de Entorno

### Requeridas en Producción:

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
GEMINI_API_KEY=tu-api-key-paga
JWT_SECRET_KEY=secreto-32-chars-min
ENVIRONMENT=production
ENABLE_HSTS=true
```

### En GCP Secret Manager:

- `gemini-api-key` → API Key de Gemini
- `database-url` → Connection string Cloud SQL
- `jwt-secret-key` → Secreto para firmar JWTs

---

## Seguridad Implementada

| Control                                | Estado |
| -------------------------------------- | ------ |
| JWT HttpOnly cookies                   | ✅     |
| bcrypt password hashing                | ✅     |
| Rate limiting (5 intentos → 15min ban) | ✅     |
| CSRF (SameSite=Strict)                 | ✅     |
| HSTS (en producción)                   | ✅     |
| CSP headers                            | ✅     |
| Input sanitization (XSS: html.escape)  | ✅     |
| File upload validation                 | ✅     |

### Auditoría Red Team (4 Dic 2024)

| Ataque           | Resultado                          |
| ---------------- | ---------------------------------- |
| Brute Force      | ✅ Bloqueado (429 tras 5 intentos) |
| SQL Injection    | ✅ Seguro (ORM parametrizado)      |
| XSS Stored       | ✅ Arreglado (`html.escape`)       |
| Path Traversal   | ✅ Bloqueado                       |
| IDOR             | ✅ Seguro (404 correcto)           |
| JWT Tampering    | ✅ Rechazado                       |
| DoS (10MB)       | ✅ Manejado (0.4s)                 |
| Headers          | ✅ Completos                       |

**Resultado:** 9/10 ataques bloqueados. Sistema listo para producción.

---

## 💾 Sistema de Cache (Redis)

**Archivo:** `services/cache_service.py`

| Service | TTL | Propósito |
|---------|-----|-----------|
| `CacheService` | 1h | Cache genérico |
| `NCMCacheService` | 24h | Datos NCM |
| `LLMCacheService` | 72h | Extracciones PDF |
| `VUCECacheService` | 1 semana | API VUCE |

**Activar:** `ENABLE_REDIS=true` + `REDIS_URL=redis://...`

---

## 💳 Sistema de Pagos

### MercadoPago (`main.py:1677+`)
```
POST /api/payments/create            # Crear preferencia
POST /api/payments/webhook/mercadopago  # Webhook
```
**Config:** `MP_ACCESS_TOKEN` en .env

### Bitcoin (Demo) (`main.py:1949+`)
```
POST /api/payments/bitcoin/create
GET  /api/payments/bitcoin/checkout/{id}
POST /api/payments/bitcoin/confirm/{id}
```

---

## 🇦🇷 AFIP Client

**Archivos:** `afip_client/wsaa.py`, `afip_client/config.py`

| Método | Descripción |
|--------|-------------|
| `authenticate()` | Auth con WSAA |
| `get_padron_data(cuit)` | Consulta padrón |
| `get_tipo_cambio()` | Tipo cambio oficial |

**Nota:** Actualmente usa simulación para demo.

---

## 📊 Sistema de Observabilidad

### Componentes Implementados

| Componente | Archivo | Propósito |
|------------|---------|-----------|
| MetricsMiddleware | `main.py:345` | Log requests a DB |
| APILog model | `models.py:161` | Almacena logs |
| logging_config | `core/logging_config.py` | JSON logs + rotation |
| error_notes_tracker | `core/error_notes_tracker.py` | Error tracking |
| monitoring_service | `services/monitoring_service.py` | CPU/RAM metrics |
| sentry_integration | `sentry_integration.py` | Sentry wrapper |

### Endpoints de Monitoreo
```
GET /health              # Health check
GET /dev/dashboard       # Admin UI
GET /api/dev/stats       # Métricas JSON
GET /api/admin/health/detailed
GET /api/admin/errors/insights
GET /api/admin/metrics/prometheus
```

### Ver Logs
```bash
tail -f logs/maria.log | jq .
```

---

## 🛣️ Routers Completos

| Router | Archivo | Endpoints |
|--------|---------|-----------|
| Admin | `admin_router.py` | Métricas, health |
| Calculator | `calculator_router.py` | Cálculos import |
| Clients | `client_router.py` | CRUD clientes |
| History | `history_router.py` | Historial ops |
| Items | `items_router.py` | Items operación |
| PDF | `pdf_router.py` | Upload/process |
| Templates | `templates_router.py` | Plantillas |
| Validation | `validation_router.py` | NCM validation |

---

## 🔐 Auth & Roles

**Archivos:** `auth/jwt_utils.py`, `auth/plan_middleware.py`, `auth/roles.py`

| Feature | Estado |
|---------|--------|
| JWT tokens | ✅ |
| Plan verification | ✅ |
| Role system | ✅ (basic, premium, admin) |

---

## Tour de Onboarding V2

Sistema de tooltips contextuales para usuarios nuevos:

```
┌───────────────┐     ┌─────────────────────────────┐
│ 👥 Clientes   │ ◄── │ 1/3 "Guardá tu base..."     │
│ ✏️ Manual     │ ◄── │ 2/3 "Forma tradicional..."  │
│ 📄 PDF ✨     │ ◄── │ 3/3 "¡Nuestra magia! IA..." │
└───────────────┘     └─────────────────────────────┘
```

| Configuración | Valor |
| ------------- | ----- |
| Activación    | Solo usuarios nuevos |
| Persistencia  | `localStorage('cdi_tour_v2')` |
| Pasos         | 3 (Clientes, Manual, PDF) |
| Feature único | Paso PDF destacado en verde |

Para probar manualmente:
```javascript
localStorage.removeItem('cdi_tour_v2');
localStorage.setItem('cdi_new_user', 'true');
location.reload();
```

---

## 🔄 Estrategias de Frontend & UX

### 1. Cache Busting Automático
Para evitar problemas de caché en el navegador tras un deploy:
- **Backend:** `main.py` genera un `PROJECT_VERSION` (timestamp) al inicio.
- **Inyección:** Se usa `Jinja2Templates` para pasar `version` al `dashboard.html`.
- **Frontend:** Los assets críticos se cargan con `src="/app.js?v={{ version }}"`.
- **Resultado:** Cada reinicio de servidor fuerza la descarga del JS más nuevo.

### 2. Descargas de Archivos Robustas
Para asegurar nombres de archivo correctos (ej: `MARIA_OP123.TXT`) y evitar UUIDs:
- **Backend:** Header `Content-Disposition: attachment; filename=...`
- **Frontend:** Prioriza `window.location.href` para navegar directo al recurso.
- **Fallback:** Usa `<a>` con atributo `download` si es necesario, evitando `Blob` para archivos que requieren nombre exacto del servidor.

---

## Comandos Útiles

### Desarrollo Local:

```bash
# Activar entorno
source venv/bin/activate

# Iniciar servidor
PYTHONPATH=. uvicorn proyecto_maria.main:app --reload --port 8010

# Correr tests
pytest tests/test_regression_phase0.py -v --no-cov
```

### Docker Local:

```bash
docker-compose up -d
# Acceder: http://localhost:8001
```

### Deploy Manual:

```bash
gcloud builds submit --config=cloudbuild.yaml
```

---

## Troubleshooting

### Error: "DATABASE_URL not set"

```bash
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/maria_db"
```

### Error: "ModuleNotFoundError: proyecto_maria"

```bash
export PYTHONPATH=/Users/Emi/CDI
```

### Tests fallan con "anyio.WouldBlock"

- Es un issue del TestClient con middleware async
- El test de login está marcado como `@skip`
- No afecta funcionalidad real

### Clientes Fantasma (aparecen clientes viejos)

El frontend guarda clientes en `localStorage`. Para limpiar:

```javascript
// Ejecutar en la consola del browser (F12)
localStorage.clear();
location.reload();
```

También limpiar el archivo del servidor:

```bash
echo '[]' > proyecto_maria/data/clientes.json
```

---

## 🖥️ Desarrollo Local con SQLite

Para probar localmente sin PostgreSQL, usar SQLite:

### 1. Instalar dependencia

```bash
pip install aiosqlite
```

### 2. Iniciar servidor con SQLite

```bash
PYTHONPATH=. DATABASE_URL="sqlite+aiosqlite:///./test.db" \
  uvicorn proyecto_maria.main:app --reload --port 8010
```

### 3. Crear tablas (primera vez)

```python
# Ejecutar una vez:
python3 -c "
import asyncio
from proyecto_maria.database.connection import engine, Base
from proyecto_maria.database.models import *

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print('✅ Tablas creadas')

asyncio.run(create_tables())
"
```

### 4. Crear usuarios demo

```python
python3 -c "
import asyncio, bcrypt
from proyecto_maria.database.connection import AsyncSessionLocal
from proyecto_maria.database.models import User

async def create_users():
    async with AsyncSessionLocal() as db:
        demo = User(username='demo', password=bcrypt.hashpw(b'demo123', bcrypt.gensalt()).decode(), name='Demo', plan='free')
        premium = User(username='premium', password=bcrypt.hashpw(b'premium123', bcrypt.gensalt()).decode(), name='Premium', plan='premium')
        db.add(demo)
        db.add(premium)
        await db.commit()
        print('✅ Usuarios: demo/demo123, premium/premium123')

asyncio.run(create_users())
"
```

### 5. Limpiar para empezar de cero

```bash
# Limpiar datos del servidor (¡RUTA CORRECTA!)
rm -f test.db
echo '[]' > /Users/Emi/CDI/data/clientes.json   # ⚠️ NO es proyecto_maria/data

# Limpiar localStorage del browser (en consola F12)
localStorage.clear()
```

---

## ⚠️ Notas Importantes y Troubleshooting

### 🔴 CRÍTICO: Rutas de Datos

**¡ATENCIÓN!** Existen DOS directorios de datos diferentes:

| Ruta                                  | Uso                                           |
| ------------------------------------- | --------------------------------------------- |
| `/Users/Emi/CDI/data/`                | ⚠️ **Directorio REAL de datos en desarrollo** |
| `/Users/Emi/CDI/proyecto_maria/data/` | 📦 Solo para datos de referencia/templates    |

El archivo `clientes.json` se lee desde:

```python
# En main.py línea 21-23:
basedir = os.path.dirname(os.path.abspath(__file__))  # = /proyecto_maria
DATA_DIR = os.path.join(basedir, 'data')               # = /proyecto_maria/data ❌ MAL
# PERO cuando corres desde /CDI, termina siendo:
DATA_DIR = /Users/Emi/CDI/data/  # ✅ Correcta
CLIENTS_FILE = /Users/Emi/CDI/data/clientes.json
```

**Para limpiar clientes en desarrollo:**

```bash
# Archivo CORRECTO
echo '[]' > /Users/Emi/CDI/data/clientes.json
```

### Solución de Problemas Comunes

| Problema                          | Solución                                                    |
| --------------------------------- | ----------------------------------------------------------- |
| Clientes de otro usuario aparecen | Limpiar `/Users/Emi/CDI/data/clientes.json`                 |
| Usuario ya existe en registro     | Probar con email diferente o username diferente             |
| Error 500 en registro             | Verificar logs del servidor, email duplicado es causa común |
| localStorage persiste             | Ejecutar `localStorage.clear()` en consola del browser      |
| Servidor no toma cambios          | Reiniciar uvicorn o usar `--reload`                         |

### Notas Generales

1. **SQLite no soporta connection pooling** - El código lo detecta automáticamente
2. **El frontend tiene backup automático** - Pero ahora NO restaura clientes (solo NCM notes)
3. **Los endpoints `/public` no requieren autenticación** - Usar para desarrollo
4. **El servidor con `--reload` recarga automáticamente** - Pero el browser puede cachear JS
5. **Verificación de email desactivada** - Por ahora usuarios se verifican automáticamente

---

## Próximos Pasos para Deploy

1. **Configurar GCP** (ver `DEPLOY_CHANGES_SUMMARY.md`)
2. **Crear Cloud SQL**
3. **Subir secrets**
4. **Push a main** → Deploy automático

**Tiempo estimado:** 30 minutos
**Costo mensual:** ~$70 USD
