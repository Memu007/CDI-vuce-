# HANDOFF — CDI (vuce / CDI-app)

> Estado vivo del proyecto. **La próxima AI o persona que entre lo lee primero.**
> Última actualización: 2026-05-02 · Wave 1 cerrada · subido a GitHub `Memu007/CDI-vuce-`.

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
- Subida de PDF → extracción → revisión → NCM → generación TXT MARIA.
- Cliente activo (clientes guardados se eligen, no se "pisan" por el PDF).
- Auto-detect importador por CUIT (cuando NO hay cliente activo).
- Banner en revisión: "este importador no está en tu lista" con 3 opciones (crear y usar / asignar a existente / no por ahora). Pre-check `by-cuit` evita duplicados.
- Panel "operación huérfana" en pantalla Listo: si terminás el TXT sin cliente activo, ofrece crear / asignar / más tarde (rescate al final).
- Telemetría: eventos UI persistidos en SQL (`telemetry_events`) + JSONL.
- Panel KPIs Wave 1 (`/dev/dashboard`): demo vs PDF, auto-detect OK / sin match, activación (usuarios únicos por acción + cuentas DB).
- Endpoints: `GET /api/clientes/by-cuit/{cuit}`, `POST /api/ui/event`, alias `POST /api/session/state`, `GET /api/dev/wave1-kpis`.
- Smoke local: `./scripts/testing/smoke_friccion.sh` (con server arriba).

### Pendiente / frágil

- VUCE en `modo_fake=true` por default. Para prod real hay que conectar API real o cliente HTTP a Tarifar.
- Sin `GEMINI_API_KEY` la subida de PDF falla.
- No hay rol admin formal — cualquier usuario logueado ve `/dev/dashboard`.
- Catálogo de proveedor en disco (`product_catalog.json`) se reinicia con cada deploy. El histórico por cliente (DB) sí persiste.
- Sin tests de regresión completos (solo smoke + un par de pytest).

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
