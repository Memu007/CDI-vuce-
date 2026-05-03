# Handoff — CDI (vuce) · Proyecto despachante de aduana

> Generado: 22 abr 2026. Carpeta canónica: `~/Desktop/CDI (vuce)/`

---

## 1. ¿Qué es este proyecto?

**CDI** es una app web para despachantes de aduana. Lee facturas de proveedores (PDF), extrae productos, sugiere y valida códigos NCM vía VUCE, y genera el archivo MARIA (declaración de importación) listo para pegar en el sistema aduanero.

---

## 2. Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11 · FastAPI · Uvicorn |
| DB | SQLite (dev) / PostgreSQL (prod) · SQLAlchemy async · Alembic |
| PDF | Gemini Vision (fallback OCR) |
| VUCE / Tarifar | `vuce_connector.py` (HTTP con retry + expo backoff) |
| Auth | JWT en HttpOnly cookie (`samesite="strict"`) |
| Frontend v2 | `dashboard_v2.html` + `static/v2/app_v2.{js,css}` + `screens/*.js` |
| Frontend v1 | `dashboard.html` + `static/app.js` (legacy, opt-in `?v=1`) |
| Deploy | Docker · Cloud Run · Railway |

---

## 3. Cómo correr localmente

```bash
cd ~/Desktop/CDI\ \(vuce\)
python3 -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port 8000 --log-level warning
```

Abrís en Cursor con `Cmd+Shift+P` → `Simple Browser: Show` → `http://127.0.0.1:8000/dashboard`

| URL | Qué muestra |
|---|---|
| `http://127.0.0.1:8000/` | Landing canónica |
| `http://127.0.0.1:8000/dashboard` | **App v2 (default)** — stepper Apple-style |
| `http://127.0.0.1:8000/dashboard?v=1` | App v1 legacy |
| `http://127.0.0.1:8000/docs` | Swagger / OpenAPI |
| `http://127.0.0.1:8000/api/dolar` | Cotizaciones BNA + Blue + MEP (JSON) |

### Usuarios demo (creados al startup)

| Usuario | Contraseña | Plan |
|---|---|---|
| `premium` | `premium123` | Premium |
| `demo` | `demo123` | Premium |
| `basico` | `basico123` | Basic |

---

## 4. Variables de entorno (.env)

```
SECRET_KEY=...           # JWT signing key
DATABASE_URL=sqlite+aiosqlite:///./cdi_dev.db
GEMINI_API_KEY=...       # PDF Vision extraction
ALLOW_PDF_DEMO_MODE=true # Activar modo demo sin API key
DOLAR_CACHE_TTL_SECONDS=900  # Cache dólar (default 15 min)
IS_PRODUCTION=false
```

---

## 5. Estructura de archivos clave

```
CDI (vuce)/
├── proyecto_maria/
│   ├── main.py                  # FastAPI app (3.980 líneas, 86+ routes)
│   ├── templates/
│   │   ├── dashboard_v2.html    # 64 KB — UI nueva "tipo Apple" (DEFAULT)
│   │   ├── dashboard.html       # UI legacy (opt-in ?v=1)
│   │   └── landing.html
│   ├── static/
│   │   ├── v2/
│   │   │   ├── app_v2.js        # Core v2 (CDI.state, router, screens)
│   │   │   ├── app_v2.css       # 104 KB — design system completo
│   │   │   ├── topbar_financials.js
│   │   │   └── screens/
│   │   │       ├── upload.js    # Paso 1: subida de PDF
│   │   │       ├── review.js    # Paso 2: revisión de datos
│   │   │       ├── ncm.js       # Paso 3: asignación NCM con spotlight
│   │   │       ├── finalize.js  # Paso 4/5: generar MARIA
│   │   │       ├── clientes.js  # Drawer de clientes + KPIs + operaciones
│   │   │       ├── catalogo.js  # Catálogo de productos por proveedor
│   │   │       ├── enrich.js    # Enriquecimiento masivo de NCM
│   │   │       ├── semaforo.js  # Semáforo de validación
│   │   │       ├── calculadora.js # Calculadora de costos de importación
│   │   │       ├── ncm_notes.js # Notas por NCM
│   │   │       └── profile.js   # Perfil de usuario
│   │   └── app.js               # JS legacy (v1)
│   ├── core/
│   │   ├── maria_generator.py   # Genera el TXT MARIA
│   │   ├── vuce_connector.py    # VUCE HTTP con retry + expo backoff
│   │   ├── ncm_service.py       # Cache NCM unificado
│   │   ├── dolar_service.py     # BNA + Blue + MEP con cache 15 min
│   │   ├── catalog_service.py   # Catálogo por tenant (fuzzy match)
│   │   ├── intervenciones.py    # LNA / LA / Antidumping por NCM
│   │   ├── rate_limit.py        # slowapi + límites dinámicos
│   │   ├── error_handling.py    # Exception handler sanitizado
│   │   └── validations.py       # Pre-MARIA + smart validations
│   ├── database/
│   │   ├── models.py            # ORM: User, Client, Operation, APILog, etc.
│   │   ├── connection.py        # get_async_session, init_db
│   │   └── __init__.py
│   ├── pdf_extractor.py         # Gemini Vision + texto + OCR fallback
│   └── security/
│       └── security_middleware.py
├── plans/                       # Planes de trabajo (01-04)
├── docs/                        # Guías, auditorías, roadmap
├── tests/                       # Pytest (test_dolar, smoke tests)
└── handoff.md                   # Este archivo
```

---

## 6. Feature flag v1 / v2

El endpoint `GET /dashboard` usa una cookie `cdi_ui`:

- **Default**: sirve `dashboard_v2.html` (la UI nueva).
- `?v=1`: setea cookie `cdi_ui=v1` → sirve la v1 legacy por sesión.
- `?v=2`: borra la cookie → vuelve a la v2.

Cambiado el 22-abr-2026; antes era al revés (v1 default, v2 opt-in).

---

## 7. Endpoints principales que consume la v2

| Endpoint | Auth | Descripción |
|---|---|---|
| `POST /auth/login` | No | Login → cookie JWT HttpOnly |
| `POST /auth/register` | No | Registro (5/min rate limit) |
| `GET /api/financials` | No | BNA + Blue + MEP + estado AFIP |
| `GET /api/dolar` | No | Cotizaciones con cache 15 min (JSON rico) |
| `GET /api/system/connectors` | Sí | Estado VUCE, Tarifar, Gemini |
| `POST /upload_pdf/public` | Sí | Extracción de factura PDF |
| `GET /api/ncm/{ncm}/completo` | Sí | Datos VUCE + alícuotas + intervenciones |
| `POST /api/ncm/sugerir` | Sí | Sugerencias NCM (historial + IA) |
| `POST /api/ncm/enrich-items` | Sí | Enriquecimiento masivo de ítems |
| `POST /api/ncm/calcular` | Sí | Cálculo arancelario (Tarifar) |
| `POST /api/validate/smart` | Sí | Validaciones pre-MARIA (semáforo) |
| `POST /api/catalog/match` | Sí | Match fuzzy de descripción → catálogo |
| `GET /api/catalog/proveedores` | Sí | Lista de proveedores en catálogo |
| `POST /generate_maria` | Sí | Genera archivo TXT MARIA |
| `GET /api/clientes` | Sí | Lista de clientes del tenant |
| `POST /api/clientes` | Sí | Alta de cliente |
| `GET /api/clientes/{id}/operaciones` | Sí | Historial de operaciones |
| `GET /api/clientes/{id}/metricas` | Sí | KPIs del cliente |
| `GET /api/ncm/notas` | Sí | Notas por NCM |

---

## 8. Sprints completados (historial)

### Sprint 1 — "El flujo core deja de mentir"
- PDF: pipeline unificado (texto → Vision → OCR), NCM preservation, multi-página.
- VUCE: cache en memoria, `arancel_mercosur`, propagación NCM a ítems.
- Alembic: baseline de la DB, migraciones versionadas.

### Sprint 2 — "El producto se adapta al despachante"
- MARIA configurable: Aduana, Destinación, PSAD, IEXT año por usuario via `maria_defaults`.
- Memoria NCM por cliente: historial de productos para autofill.
- Multi-factura: múltiples `[DVD]` en un solo TXT MARIA.
- Intervenciones VUCE: clasificación LNA / LA / Antidumping por prefijo NCM.

### Sprint 3 — "Production-ready antes de invitar externos"
- JWT solo cookie (HttpOnly, secure, samesite=strict).
- Rate limits en endpoints críticos (slowapi).
- Exception handler sanitizado (tracebacks solo en dev).
- Tenant isolation: `Client.owner_username`, catálogo por usuario.
- DB: índices, FK `ondelete`, migraciones Alembic.
- Dólar en vivo: `dolar_service.py` (BNA + Blue + MEP, cache 15 min).
- UX: semáforo de intervenciones NCM en modal, normalización fechas `DD/MM/AAAA`, sessionStorage para drafts.

### Sprint 4+ — "UI v2 como default"
- `dashboard_v2.html` + `static/v2/` promovida a default (`GET /dashboard`).
- v1 legacy pasa a opt-in con `?v=1`.
- `dolar_service.py` portado a CDI (vuce) (antes solo en backup).
- `/api/dolar` agregado (endpoint dedicado para cotizaciones).
- `/api/financials` refactorizado para usar `dolar_service` (incluye MEP).

---

## 9. Deuda técnica conocida

| Item | Prioridad |
|---|---|
| `admin`/`admin` como usuario admin — no existe en esta DB (usar `demo`/`demo123`) | Alta |
| `IS_PRODUCTION` flag — algunos checks de seguridad dependen de esta var | Alta |
| VUCE en `modo_fake=True` por defecto — necesita API key real para producción | Alta |
| Gemini Vision apagado sin `GEMINI_API_KEY` — la subida de PDF devuelve 503 sin esa key | Alta |
| Tests de regresión parciales — solo `test_dolar_and_financials.py` y smoke tests | Media |
| Migraciones Alembic — la carpeta `migrations/versions/` no existe en CDI (vuce); la DB se inicializa con `init_db()` + scripts en `scripts/migrate_add_owner.py` | Media |
| `mercadopago` import en main.py (~línea 3460) — posible dep no instalada si no está en requirements | Baja |

---

## 10. Carpetas en el equipo

| Carpeta | Estado | Descripción |
|---|---|---|
| `~/Desktop/CDI (vuce)/` | **ACTIVA** ← esta | Proyecto completo con v2 como default |
| `~/CDI/` | Origen | De donde se copió CDI (vuce). Igual en contenido. |
| `~/Desktop/cdi-vuce-backup-20260419/` | Backup | Sprints 1/2/3 + tenant isolation, **sin v2 UI**. Útil para referencia de dolar_service, migrations. |
| `~/cid 2/` | Vacío/Viejo | Sin v2. |

---

## 11. Para el próximo dev / próxima sesión

1. Abrir `~/Desktop/CDI (vuce)/` en Cursor como workspace.
2. Correr el server: `python3 -m uvicorn proyecto_maria.main:app --host 127.0.0.1 --port 8000 --log-level warning`
3. Ir a `http://127.0.0.1:8000/dashboard` y loguearse con `demo` / `demo123`.
4. La v2 "tipo Apple" es lo que se ve por defecto.
5. Revisar deuda técnica de la tabla de arriba antes de invitar usuarios reales.

---

## 12. Próximos pasos recomendados (prioridad PM)

1. **Configurar `GEMINI_API_KEY`** para que la subida de PDF funcione en producción.
2. **Crear usuario admin** con `roles=["admin"]` en la DB.
3. **Setear `IS_PRODUCTION=true`** y probar que todos los guards de seguridad aplican.
4. **Smoke test end-to-end**: subir un PDF real → revisar → asignar NCM → generar MARIA.
5. Portar migraciones Alembic del backup a CDI (vuce) (opcional si no se usa PostgreSQL aún).
