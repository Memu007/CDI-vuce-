# HANDOFF — CDI (vuce / CDI-app)

> Estado vivo del proyecto. **La próxima AI o persona que entre lo lee primero.**
> Última actualización: 2026-06-15 · Ola 3 cerrada: Plan 04 Catálogo unificado (versión chica) · tag `v0.3-wave3` puesto.

---

## 1. Qué es esto

**CDI** es una app web para despachantes de aduana argentinos. Lee la factura del proveedor en PDF, ofrece autocomplete de NCM contra VUCE, y devuelve un archivo MARIA listo para pegar en el sistema aduanero. La premisa de producto es:

> "El despachante mantiene el control. La AI recomienda; el humano confirma. El TXT MARIA es 100% trazable a lo que el usuario aprobó en pantalla."

---

## 2. Cómo correrlo localmente (3 pasos)

```bash
cd ~/Desktop/CDI-app
source venv/bin/activate                         # solo la primera vez: python3 -m venv venv && pip install -r requirements.txt
PYTHONPATH=. uvicorn proyecto_maria.main:app --host 127.0.0.1 --port 8000 --reload
```

Abrir en navegador: <http://127.0.0.1:8000/>

| URL | Para qué |
|-----|----------|
| `/` | Landing (login / registro) |
| `/dashboard` | App v2 (default) |
| `/dashboard?v=1` | App v1 legacy (cookie-based) |
| `/dev/dashboard` | Panel interno · KPIs Wave 1 (requiere login) |
| `/docs` | Swagger / OpenAPI |

Usuarios demo (creados al primer arranque, NO en `ENVIRONMENT=production`):

| Usuario | Pass | Plan |
|---------|------|------|
| `demo` | `demo123` | Premium |
| `premium` | `premium123` | Premium |
| `basico` | `basico123` | Basic |

---

## 3. Stack

| Capa | Tecnología |
|------|------------|
| Backend | Python 3.11 · FastAPI · Uvicorn / Gunicorn |
| DB | SQLite local (`proyecto_maria/maria_data.db`) · PostgreSQL en Railway (via `DATABASE_URL`) |
| ORM | SQLAlchemy async |
| Migraciones | Inline en `main.py` (`_migrate_*`), idempotentes. **No** se usa Alembic en este repo. |
| PDF | Gemini Vision (con fallback texto / OCR) |
| VUCE | `proyecto_maria/core/vuce_connector.py` (HTTP retry + backoff; `modo_fake=true` por default) |
| Auth | JWT en cookie HttpOnly (`samesite="lax"`) |
| Frontend v2 | `templates/dashboard_v2.html` + `static/v2/` (vanilla JS, sin framework) |
| Telemetría | `POST /api/ui/event` → `logs/ui_events.jsonl` + tabla `telemetry_events` |
| Deploy | Dockerfile + Railway |

---

## 4. Variables de entorno

`.env.example` está commiteado. **Nunca** commitear `.env` ni `.env.afip` (ya excluidos).

Mínimo para correr local:

```
JWT_SECRET_KEY=algo-largo-aleatorio-min-32-chars
GEMINI_API_KEY=...                  # opcional; sin esto, /upload_pdf devuelve 503
ENVIRONMENT=development
EMAIL_VERIFICATION_REQUIRED=false   # en beta cerrada queda así
```

Producción (Railway): ver `docs/deployment/RAILWAY_SETUP.md`.

---

## 5. Estructura de carpetas

```
CDI-app/
├── proyecto_maria/
│   ├── main.py                  # FastAPI app (~4000 líneas, ~90 endpoints)
│   ├── templates/               # landing.html, dashboard_v2.html, dev_dashboard.html
│   ├── static/v2/
│   │   ├── app_v2.js            # router + state + telemetría
│   │   ├── app_v2.css           # design system
│   │   └── screens/             # upload, review, ncm, finalize, clientes, ...
│   ├── core/                    # maria_generator, vuce_connector, dolar_service, etc.
│   ├── database/                # models.py + connection.py
│   └── pdf_extractor.py
├── docs/
│   ├── wave1_*.md               # plan Wave 1 + activación + entrevistas + fase 2
│   ├── deployment/              # RAILWAY_SETUP, DEPLOY*, etc.
│   ├── audits/                  # AUDIT_MULTITENANT, etc.
│   └── archive/                 # handoffs y docs viejos (no usar como fuente de verdad)
├── scripts/
│   └── testing/smoke_friccion.sh
├── tests/
├── plans/
├── HANDOFF.md                   # ← este archivo
├── AGENTS.md                    # instrucciones para AIs (Cursor, Claude Code, Antigravity)
├── CHANGELOG.md                 # qué cambió y cuándo
├── README.md                    # intro corta para humanos
└── .gitignore
```

**Carpetas que NO van al repo** (ver `.gitignore`): `venv/`, `viejo/`, `logs/`, `data/`, `*.db`, `.env*`, PDFs de clientes (`ejemplos/*.pdf`, `.agent/ejemplos/*.pdf`).

---

## 6. Estado actual (qué está vivo, qué no)

### Funciona

- Landing → registro → login → app v2.
- Onboarding: al alta nueva aparece automáticamente una bienvenida con tarjetas explicando el producto (PDF, clientes, reconocimiento, autocatálogo). Se cierra una vez y no molesta. El botón `Ver tour` la vuelve a abrir.
- Registro: soporta modo prueba acotado por variables `REGISTER_TEST_EMAILS` + `REGISTER_TEST_EMAIL_REPLACE=true` para reusar emails de test sin afectar usuarios reales.
- Subida de PDF → extracción → revisión → NCM → generación TXT MARIA.
- Importador de clientes: botón "Importar" en pantalla Clientes acepta CSV/Excel, detecta columnas comunes y de PreMaría, salta duplicados por CUIT y entrena el autocatálogo si vienen `descripcion` + `ncm`. Endpoint `POST /api/clientes/import`.
- Carga manual: botón "Cargar manualmente" en upload para crear operaciones sin PDF/Excel. Elige cliente, tipea productos (descripción, cantidad, precio, NCM opcional) y va a Revisión igual que si viniera de PDF. El autocatálogo aprende los NCM cargados a mano.
- Extracción de CUIT argentino: se normaliza a 11 dígitos sin prefijo país (`AR306...` pasa a `306...`).
- Cliente por operación, sin selección global persistente: PDF arranca limpio, detecta por CUIT o propone crear/asignar. Excel pide elegir cliente puntualmente solo si se quiere usar mapeo personalizado.
- Auto-detect importador por CUIT (cuando NO hay cliente activo).
- Banner en revisión: "este importador no está en tu lista" con 3 opciones (crear y usar / asignar a existente / no por ahora). Aparece aunque falte CUIT si hay razón social; si hay CUIT, pre-check `by-cuit` evita duplicados. Al resolver, muestra tarjeta verde persistente.
- Panel final de cliente no reconocido: si terminás el TXT sin cliente activo, ofrece crear / asignar / más tarde. El alta corta prellena razón social, CUIT y domicilio si vienen de la factura, asocia la operación al historial y muestra confirmación visible.
- Popups v2: las confirmaciones usan el modal visual de CDI (`CDI.confirm`) en vez de carteles nativos del navegador.
- Eliminación de clientes: borra operaciones, ítems, notas NCM e historial de productos del cliente manteniendo aislamiento por usuario.
- Telemetría: eventos UI persistidos en SQL (`telemetry_events`) + JSONL; el frontend usa `/api/session/state` para reducir bloqueos por extensiones.
- Seguridad Wave 1: fallback de auth en `proyecto_maria/auth/jwt_utils.py` solo entrega usuario fake si `ENVIRONMENT=testing` Y hay `PYTEST_CURRENT_TEST` (no se puede activar por accidente en Railway). El fake user tiene `roles=["operador"]/plan=basic`. CORS prod falla cerrado sin `ALLOWED_ORIGINS`. `/upload_*/public` requieren auth.
- Seguridad Wave 2: `pdf_extractor.py` encierra el texto del PDF en `<<<DOCUMENTO>>>` y le dice al modelo que ignore instrucciones dentro. Cap de input al LLM (`PDF_LLM_MAX_INPUT_CHARS=60000`) y de items (≤2000). Sanitización estricta de cada item antes de persistir (NCM solo dígitos, origen ISO, strings sin chars de control). Multi-tenant verificado: 71 referencias a `owner_username` con helper `_get_owned_client`.
- Seguridad Wave 3: cuota diaria de IA por usuario (`proyecto_maria/core/ai_quota.py`, `AI_DAILY_PDF_LIMIT=50/día/usuario`) aplicada en `POST /upload_pdf/public`. XSS audit de v2 OK (todos los `innerHTML` con dato externo escapan vía `CDI.escapeHtml`). Pendiente no urgente: sacar `unsafe-inline` de CSP `script-src` y CSRF header custom.
- Panel KPIs Wave 1 (`/dev/dashboard`): demo vs PDF, auto-detect OK / sin match, activación (usuarios únicos por acción + cuentas DB).
- Endpoints: `GET /api/clientes/by-cuit/{cuit}`, `POST /api/ui/event`, alias `POST /api/session/state`, `GET /api/dev/wave1-kpis`.
- Smoke local: `./scripts/testing/smoke_friccion.sh` (con server arriba).

### Pendiente / frágil

- VUCE en `modo_fake=true` por default. Para prod real hay que conectar API real o cliente HTTP a Tarifar.
- Sin `GEMINI_API_KEY` la subida de PDF falla.
- No hay rol admin formal — cualquier usuario logueado ve `/dev/dashboard`.
- Catálogo de proveedor en disco (`product_catalog.json`) se reinicia con cada deploy. El histórico por cliente (DB) sí persiste. **Fix reciente (Plan 04 v0):** al subir Excel con `cliente_id`, el mapeo de columnas ahora se detecta y guarda en `Client.column_mapping` (antes se usaba pero no se persistía).
- Generador MARIA TXT: validado contra un golden file real del despachante (op 001790125). Hay test de regresión golden anonimizado en `tests/test_generar_maria_txt.py` + `tests/fixtures/maria_golden_anon.TXT` (33 tests del generador). Resto del repo: solo smoke + pytest parcial.
- **Novedades ARCA:** widget en Upload con endpoint `/api/arca/novedades` (público, cache 15 min). Fuente real de ARCA/AFIP.
- **Ola 2 CERRADA** (tag `v0.2-wave2`):
  - Plan 02: drawer de clientes con 6 KPIs, badge `N ops`, orden por último movimiento, export CSV, expand de operaciones.
  - Plan 03: alta rápida de cliente desde review (buscador server-side + mini formulario inline).
  - Fix urgente: tabla NCM ahora muestra **Valor unitario** y **Peso unitario**.
- **Ola 3 CERRADA — Plan 04 Catálogo unificado (versión chica):**
  - Fase 0: persistencia de mapeo de columnas al subir Excel; nuevos endpoints `/api/clientes/{id}/catalogo/*`; pestaña "Catálogo" en drawer con columnas reconocidas + productos aprendidos; autofill de peso unitario e icono 📚 para matches de cliente.
  - Fase 1: edición inline de NCM/origen/peso y botón "Olvidar" para productos aprendidos.
  - Fix: `extract_items_from_excel` acepta `peso_unitario = 0` para que el autofill de peso del catálogo del cliente pueda dispararse en la segunda operación.
  - Smoke end-to-end navegador pasa: cliente nuevo → aprender producto → segunda planilla con origen XX y peso 0 → review muestra origen CN y peso 1.5 con `__autofillSource: 'cliente'` → NCM muestra chip 📚.
  - **Mejora de seguridad aduanera (países):** Agregados oficialmente Vietnam (337), Tailandia (335), Indonesia (316) y Malasia (326). Se valida estrictamente el país de origen/destino (bloqueando "XX" y no reconocidos con HTTP 400) para evitar fallas ante AFIP.
- **Mantenimiento resuelto:**
  - Dependencias vulnerables de producción actualizadas en `requirements.txt`: `requests>=2.32.4`, `pdfminer.six>=20251107`, `starlette>=0.47.2` + `fastapi>=0.115.0`.
  - Verificado con `pip-audit`: solo queda `pytest 8.4.2` (dev-only, pendiente por conflictos con `pytest-asyncio`).
  - Suite completa: **280 passed** (los 70 tests de billing, checkout y maria generator pasan completamente verdes; persisten advertencias/errores de loop preexistentes en security/seo). Smokes pasan.
- **Mantenimiento pendiente:**
  - `pytest>=9.0.3` (dev-only, bajo riesgo).
- **Plan 03 cerrado (Ola 2):** endpoint `/api/clientes/search?q=` para búsqueda server-side; picker con debounce; botón **+ Nuevo cliente** en review con mini formulario inline para alta rápida de cliente desde la operación.
- **Fix urgente tabla NCM:** ahora muestra **Valor unitario** y **Peso unitario** junto con Ref./Descripción/Origen/Cant/Código NCM.
- **Plan 02 cerrado (Ola 2):** drawer de clientes con 6 KPIs (operaciones/ítems/promedio/origen frecuente/valor/última), orden por último movimiento, badge `N ops`, export CSV backend, expand de operaciones. Smoke headless de Plan 02 pasa.
- **Fix reciente:** corregido `exportClientCsv is not defined` que rompía la apertura del drawer al hacer click en Exportar CSV (`clientes.js`).
- **Tests:** suite completa **280 passed, 102 skipped**; 24 errores preexistentes por compatibilidad de `pytest-asyncio` en `tests/security/test_security.py` y `tests/test_seo.py` (no relacionados con cambios recientes). Smoke `smoke_friccion.sh` pasa local.
- **Ola 1 cerrada:** Cockpit + S1/S3 + upload.js race fix + Novedades ARCA + UX Plan 01.
- **Leak conocido `[SBT]`:** el sufijo `CSBTSVL` por default trae `AA(VOWYNNS)` (cliente del sample). Para otros clientes sale ese dato ajeno. Ya es parámetro (`sbt_sufijo_valor`) pero falta la regla real por importador (qué son `AB(...)` y `CA00`) → pendiente de confirmar con el despachante.
- Pendiente despachante: confirmar si `DDDTVENEMB` (fecha embarque) es obligatorio para el Kit SIM.

---

## 7. Wave 1 (lo último que se hizo)

Decisiones de producto (mayo 2026):

1. **Respetar al cliente activo.** Si el despachante ya eligió cliente, un PDF con CUIT distinto no lo reemplaza solo. Antes había "swap silencioso" — se sacó porque generaba sorpresa.
2. **Atajo "crear y usar"** para importadores nuevos en revisión.
3. **Telemetría persistida** para tomar decisiones con datos, no solo soporte cualitativo.
4. **Activación con varias definiciones** (no una sola), documentadas en `docs/wave1_activation_definitions.md`.

Documentación PM:

- `docs/wave1_invitation.md` — guion Loom + email + FAQ + 5 estudios.
- `docs/wave1_activation_definitions.md` — opciones A–F de "usuario activado".
- `docs/wave1_interview_kit.md` — para 3–5 entrevistas cortas.
- `docs/wave1_phase2_gate.md` — checklist para abrir Fase 2.

---

## 8. Convenciones del repo

### Commits

Prefijos en el subject (compatibles con Conventional Commits, sin estricto):

- `feat:` nueva funcionalidad para el usuario final.
- `fix:` arreglo de un bug.
- `chore:` mantenimiento (deps, configs, archivar docs).
- `docs:` cambios en documentación.
- `refactor:` cambio interno sin tocar comportamiento.
- `test:` agregar / arreglar tests.

Ejemplo: `feat: banner crear-y-usar importador en review`

### Branches

- `main` es la rama de prod (lo que va a Railway).
- Si un cambio es grande / arriesgado, abrir una branch tipo `wave2-feedback-pre-dashboard`. Si no, commits directos a `main` mientras seas vos solo.

### Tags (puntos fijos)

- `v0.1-wave1` → estado al 2 may 2026 (Wave 1 cerrada). Si algo se rompe, podés volver a este punto: `git checkout v0.1-wave1`.
- Próximo tag esperado: `v0.2-wave2` cuando se cierre la siguiente iteración.

---

## 9. Cómo dejar el repo después de cada sesión (humano o AI)

Antes de cerrar:

1. Actualizar la sección 6 (estado actual) si cambió algo.
2. Agregar entrada en `CHANGELOG.md` con la fecha y 1–3 líneas de qué cambió.
3. Commit con prefijo claro.
4. Si es un hito importante (cierre de Wave / decisión grande), poner un tag.
5. `git push`.

---

## 10. Para el próximo dev / próxima AI

Empezá leyendo, en este orden:

1. **`HANDOFF.md`** (este archivo) — contexto general.
2. **`AGENTS.md`** — qué tenés permitido / qué no, cómo dejar el repo.
3. **`CHANGELOG.md`** — últimas 2–3 entradas alcanzan para saber qué se tocó.
4. **`docs/wave1_*.md`** si vas a tocar tema importador / telemetría / activación.

Si vas a deployar / debug Railway: `docs/deployment/RAILWAY_SETUP.md`.

Si te perdés: pedí explícitamente al humano un overview en castellano antes de tocar código.
