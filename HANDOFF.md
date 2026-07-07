# HANDOFF — CDI (vuce / CDI-app)

> Estado vivo del proyecto. **La próxima AI o persona que entre lo lee primero.**
> Última actualización: 2026-06-20 · Hardening de Pilar B (Cotizaciones) y tests E2E completados.

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

> Nota: el usuario `basico` de demo se eliminó; el plan único activo es Premium.

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

- Popups v2: las confirmaciones usan el modal visual de CDI (`CDI.confirm`) en vez de carteles nativos del navegador.
- Eliminación de clientes: borra operaciones, ítems, notas NCM e historial de productos del cliente manteniendo aislamiento por usuario.
- Telemetría: eventos UI persistidos en SQL (`telemetry_events`) + JSONL; el frontend usa `/api/session/state` para reducir bloqueos por extensiones.
- Seguridad Wave 1: fallback de auth en `proyecto_maria/auth/jwt_utils.py` solo entrega usuario fake si `ENVIRONMENT=testing` Y hay `PYTEST_CURRENT_TEST`. El fake user tiene `roles=["operador"]/plan=premium`. CORS prod falla cerrado sin `ALLOWED_ORIGINS`. `/upload_*/public` requieren auth.
- Seguridad Wave 2: `pdf_extractor.py` encierra el texto del PDF en `<<<DOCUMENTO>>>` y le dice al modelo que ignore instrucciones dentro. Cap de input al LLM (`PDF_LLM_MAX_INPUT_CHARS=60000`) y de items (≤2000). Sanitización estricta de cada item antes de persistir (NCM acepta dígitos + letra de control, origen ISO, strings sin chars de control). Multi-tenant verificado: 71 referencias a `owner_username` con helper `_get_owned_client`.
- NCM completo: el campo de posición arancelaria ahora acepta 8 dígitos NCM + 3 SIM + letra (ej: `8471.30.00.900 R`). Columna DB ampliada a VARCHAR(20), migración `_migrate_widen_pieza_column` para PostgreSQL. `formatNcm` y `isValidNcm` actualizados en frontend.
- Agrupación de ítems (unidades clasificatorias): se pueden asociar 2+ ítems con mismo NCM y origen en un grupo. En el TXT MARÍA se exportan como un solo [ART] (valores sumados, descripción concatenada). Campos nuevos `grupo_id` (Integer) y `unidad` (String(10)) en `OperationItem`. Endpoints `/api/operacion/{id}/agrupar` y `/desagrupar`. Botón "Asociar ítems" en barra de batch de pantalla NCM. Chip "Grupo N" para desagrupar con clic.
- Seguridad Wave 3: cuota diaria de IA por usuario (`proyecto_maria/core/ai_quota.py`, `AI_DAILY_PDF_LIMIT=50/día/usuario`) aplicada en `POST /upload_pdf/public`. XSS audit de v2 OK (todos los `innerHTML` con dato externo escapan vía `CDI.escapeHtml`). Pendiente no urgente: sacar `unsafe-inline` de CSP `script-src` y CSRF header custom.
- Panel KPIs Wave 1 (`/dev/dashboard`): demo vs PDF, auto-detect OK / sin match, activación (usuarios únicos por acción + cuentas DB).
- Endpoints: `GET /api/clientes/by-cuit/{cuit}`, `POST /api/ui/event`, alias `POST /api/session/state`, `GET /api/dev/wave1-kpis`, `GET /api/admin/cohort-retention` (Fase 0 PMF).
- Smoke local: `./scripts/testing/smoke_friccion.sh` y `./scripts/testing/smoke_quotes.sh` (con server arriba).
- **Modal de perfil (2026-06-21):** scroll arreglado con `overflow-y: auto` en el modal + `position: sticky` en header/footer. Antes las secciones expandibles (defaults, seguridad, plan) tapaban los campos de abajo. Email ahora es editable con validación backend.
- **Tour de bienvenida (2026-06-21):** 7 slides (antes 6). Slide nuevo 6 explica que en el perfil se configuran CUIT y defaults de operación, y que se aplican solos a cada operación nueva.
- **Landing (2026-06-21):** CTA en el hero abre registro directo (no solo scroll a precio). Sección "Cómo funciona" con 5 pasos. Sacada jerga "Gemini Vision". Credenciales demo solo visibles en localhost. Placeholder de login genérico. Pricing menciona recarga de operaciones extra.
- **Página pública de estado (2026-06-21):** el link público que se comparte con el cliente ahora muestra un timeline con el estado en vivo de la operación (Borrador → Oficializada → Canal → Liberada). El estado se lee en vivo de la tabla Operation, no del snapshot congelado. El presupuesto (ítems, alícuotas, total) sigue siendo foto fija.
- **Auditoría de seguridad pre-producción (2026-06-21):** 9 fixes aplicados: CSRF enforce en prod, upload PDF + Excel/CSV con magic bytes (`validate_file_upload` en `/upload_pdf/public`, `/upload_excel/`, `/upload_excel_v2/`, `/api/clientes/import`, `/api/ncm/import-historial`), mock email sin body en logs, CSP header, XSS en página pública y clientes.js, defense-in-depth en ClientService, log de filename sanitizado. JWT secret guard ya existía (falso positivo). Pendiente fase 2: reset password, refresh token, PDF bomb limit, pip-audit, sacar `unsafe-inline` de CSP `style-src`.
- **Librerías actualizadas por pip-audit (2026-06-21):** PyJWT 2.4→2.13, python-multipart 0.0.22→0.0.32, jinja2 3.1.2→3.1.6, FastAPI 0.135→0.138 + starlette 0.52→1.3.1, pydantic 2.7→2.13. ~20 CVEs tapados. Smoke test OK. Pendiente: aiohttp, pillow, pyopenssl (menos críticas, no bloquean prod).
- **Pentest OWASP Top 10 (2026-06-21):** 4 fixes aplicados: password policy (min 8 + número/símbolo), session fixation (jti UUID en JWT), prompt injection NCM (delimitadores), CSP unificado (sacado unsafe-inline de script-src, eliminado CSP duplicado de main.py). Hallazgo #3 (email duplicado) era falso positivo — ya existía chequeo en main.py:2630-2652. `unsafe-inline` restaurado temporalmente en script-src (40+ handlers inline en 4 templates). Pendiente fase 2: reset password, refresh token, PDF bomb limit, sacar unsafe-inline de CSP style-src y script-src (requiere migrar inline scripts/styles).
- **Re-pentest v2 verificado (2026-06-21):** 14/14 tests verificados independientemente por PM con curl. Password policy, session fixation (jti), CSRF, cookies (HttpOnly+Secure+SameSite), uploads (magic bytes + path traversal), JWT alg:none, SQLi, CORS, CSP+HSTS, force browsing, email duplicado, rate limiting — todos PASS. Discrepancia menor: rate limiting devuelve 401 en 4to (login_attempts) y 429 en 5to (slowapi), no 429 en 4to como reportó la programadora. Session fixation parcial: token viejo sigue funcionando (sin blacklist). 2 pendientes para Railway: prompt injection NCM (requiere GEMINI_API_KEY) y XSS endpoint público (requiere flujo completo).
- **Pentest Railway final (2026-06-21):** 17/17 PASS. Seguridad en Railway CERRADA. Rate limiting fixeado: X-Forwarded-For (commit 75667cb) + Gunicorn workers 4→1 (commit 2c0cb37 por PM). Nota: si se necesitan más workers en el futuro, setear REDIS_URL en Railway para usar RedisStorage (rate_limit.py ya lo soporta) — MemoryStorage con 1 worker es el actual.
- **Seguridad pre-prod: CERRADA.** Fase 2 documentada: blacklist jti, reset password, refresh token, PDF bomb limit, migrar inline scripts (landing→dashboard_v2→public_quote→dashboard legacy), sacar unsafe-inline de script-src y style-src, actualizar aiohttp/pillow/pyopenssl, prompt injection NCM test real, XSS endpoint público test real.
- **Prompt injection NCM verificado en Railway (2026-06-21):** 3/3 PASS. Inyección clásica, jailbreak con cierre de delimitador, data exfiltration — todos ignorados por la IA. Delimitadores `<user_input>` funcionan.
- **XSS endpoint público verificado a nivel código (2026-06-21):** `escapeHtml()` en `public_quote.html` escapa todos los campos dinámicos. `canal` usa innerHTML sin escapar pero está validado contra lista fija `["verde", "naranja", "rojo"]`. Test end-to-end pendiente por Tarifar 503.
- **Verificación visual Railway (2026-06-21):** Puppeteer en landing, login, registro, quote público — 0 violaciones CSP. Password policy verificado desde navegador. Headers confirmados.
- **Fase 2 — Blacklist jti + password policy (2026-06-22):** `active_jti` (VARCHAR(32)) en `users` + migración idempotente. `create_access_token` devuelve `(token, jti)`. Login/register/verify guardan jti activo. `get_current_user` rechaza tokens con jti != active_jti (401 "Token revocado"). Reset/change password setean `active_jti = None`. Backward compat: NULL = no bloquear. Password policy (min 8 + número/símbolo) aplicada también en reset-password y change-password. Test: login→token A→login→token B→token A da 401, token B da 200. Smoke OK.
- **Pentest externo Opus 4.8 (2026-06-22):** 0 críticos / 0 altos / 1 medio / 2 bajos. **M1 (fixeado):** `/api/billing/simulate-charge` gateado en prod — devuelve 404 salvo `ENABLE_SIMULATE_CHARGE=true`. Cierra bypass de billing (auto-activarse sin pago real). **L1 (fixeado):** `/dev/dashboard` HTML ahora exige `require_admin` (401 sin auth, 403 sin rol admin); los datos `/api/dev/*` ya estaban protegidos. **L2 (no se toca):** enumeration en `/auth/register` es trade-off de UX. Verificado local en modo prod: dev/dashboard 401, simulate-charge 404. **Pendiente:** verificar ambos en Railway post-deploy + borrar usuarios de prueba `pentest_ma1` y `pentest_idor2` (+ 2 clientes CUITs 20111111112/20111111113).
- **SEGURIDAD CERRADA (2026-06-22):** Score 9/10. Fase 2 versión chica completada: blacklist jti + password policy en reset/change + deps transitivas actualizadas + pentest externo Opus 4.8 (M1 + L1 fixeados y verificados en Railway). 36 tests locales + 17 Railway + 3 prompt injection + verificación visual + 8 blacklist jti + 2 Opus fixes = todos PASS. Pendientes fase 2 grande: refresh token, migrar inline scripts (sacar unsafe-inline), test XSS end-to-end cuando Tarifar esté activo.
- **Datos de carátula fase 1 (2026-07-06):** pantalla Revisión ahora muestra "Domicilio del establecimiento" y "Fecha inicio de actividades" en sección Importador (se auto-pueblan desde la ficha del cliente al elegir importador, con hint verde). Campo nuevo "Gastos anteriores a FOB (USD)" en Costos adicionales (numérico, opcional). Sin cambios en DB. Fase 2 (exportación EC01, art 736, integración MARIA) pendiente.
- **Extracción de domicilio desde PDF (2026-07-06):** la IA ahora extrae `comprador_domicilio` desde la factura (ambos prompts de Gemini en `pdf_extractor.py`). `comprador_fecha_inic_activ` y `gastos_anteriores_fob` NO se extraen del PDF — no figuran en facturas reales; el primero viene de la ficha del cliente / ARCA a futuro; el segundo es campo manual. Prioridad: si el cliente activo tiene domicilio en su ficha, gana sobre el del PDF (`applyClienteActivo` en `review.js`).
- **Identificador correlativo de operación (2026-07-07):** las operaciones nuevas usan `op_code` correlativo `OP-NNNNNN` por despachante, generado por `_next_op_code` en `main.py`. Aplica a `create_manual_operation` y `save_client_operation`. Las viejas conservan su código actual (MANUAL_..., OP_..., NULL). Limitación conocida: sin lock de concurrencia — si dos ops del mismo owner se crean en el mismo instante podrían repetir número (riesgo bajo para uso individual).
- **Cliente VUCE CI oficial (2026-06-30):** `proyecto_maria/core/vuce_ci_client.py` consulta la API pública interna de `www.vuce.gob.ar` (Central de Información), sin CUIT ni certificado digital — el propio sitio genera un token anónimo (`POST /auth/generate`) que se reusa. Devuelve el código SIM completo (11 dígitos + letra, ej. `3926.90.90.100H`), aranceles reales (AEC/DII/TE/IVA) e intervenciones reales (SENASA, ANMAT, etc. con flag `opcional` tal cual lo define VUCE, sin filtrar por palabras clave). Conectado a `vuce_connector.py` como fuente prioritaria cuando `VUCE_CI_ENABLED=true` (default `false`, comportamiento actual sin cambios). `_BASE_URL` apunta hoy a `qa.ci.vuce.gob.ar` porque es lo que usa la propia www.vuce.gob.ar en producción — no se encontró un dominio "prod" distinto. Campo "DIE" del endpoint de tributos NO se mapea (valor distinto a AEC en una prueba real, significado no confirmado — ver comentario en el código). **Propagación a UI (2026-06-30):** `ncm_service.py` (`merge_datos_inteligente` + `get_ncm_completo`) ahora propagan `codigo_sim` y `sim_alternativas` al response final. `ncm.js` (`renderVucePreview`) muestra el `codigo_sim` cuando está disponible, en vez del NCM de 8 dígitos. Verificado con NCM 3926.90.90: llega `3926.90.90.100H` + 32 alternativas.

### Pendiente / frágil

- VUCE en `modo_fake=true` por default. Para prod real hay que conectar API real o cliente HTTP a Tarifar.
- Sin `GEMINI_API_KEY` la subida de PDF falla.
- No hay UI para asignar rol admin — los dueños se auto-asignan el rol en producción usando la variable de entorno `ADMIN_USERNAMES` al arrancar. `/dev/dashboard` ahora exige `require_admin` (fix 2026-06-22).
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
- **Ola 4 — Billing real con MercadoPago (MVP cerrado):**
  - Plan único **Premium** ($45.000 ARS/mes, 15 ops/mes, clientes ilimitados, 3 usuarios). Trial 14 días sin tarjeta. Top-up $10.000 ARS por 10 ops. **(2026-06-22: precio 30.000→45.000 y ops 10→15. Verificar que el panel de MercadoPago tenga $45.000 para que el cobro real coincida.)**
  - Servicio `proyecto_maria/services/billing_service.py` con Checkout API manual (preference mensual). Soporte a suscripciones MP (preapproval) preparado para cuando haya `preapproval_plan_id`.
  - Endpoints: `GET /api/billing/plans`, `POST /api/billing/checkout` (con selector de plan), `POST /api/billing/topup`, webhook `/api/payments/webhook` actualizado.
  - Middleware `require_active_billing` aplica límite de ops/mes en creación de operaciones y límite de clientes al crear cliente.
  - UI: selector de plan en registro, uso del mes en perfil, botón de top-up, banner de trial vencido, **modal de pago cuando backend devuelve 402**.
  - Smoke local con checkout real de MercadoPago genera preference `live` OK. Pendiente: smoke real de pago + webhook en deploy con dominio público.
- **Ola 4 — Seguridad y robustez (post-MVP, cerrado):**
  - Webhook MP: códigos HTTP correctos (401 firma, 400 error recuperable, 500 bug), logging estructurado, deduplicación por `last_payment_id`.
  - Plan strict: registro rechaza `basic` con HTTP 400. `get_plan()` levanta error en vez de caer silencioso a premium.
  - Top-up limitado a 100 créditos extra; expiran a 30 días. Créditos vencidos se limpian automáticamente.
  - Trial cron: al iniciar la app, usuarios con trial vencido pasan a `past_due`.
  - Static files: CustomStaticFiles rechaza `.env`, `*.db`, `*.jsonl`, logs/ y secrets/.
- **Iteración C — Bug Fixes & UX (Cerrada):**
  - **Compatibilidad Postgres**: Reemplazo de `func.strftime` (SQLite) por `sqlalchemy.extract` en dashboard de retención.
  - **Auth y Billing**: Protección en `get_current_user` con fallback automático a Premium ante un plan nulo/inválido o error en `get_plan()`.
  - **UX**: Formulario y link de "Olvidé mi contraseña" integrados en `landing.html` con anti-enumeración de correos.
  - **Robustez Pilar B**: Tests añadidos en presupuestos públicos validando reordenamiento de alícuotas por NCM y correcto fallback a HTTP 503 con `tarifar_unavailable`. Exception handler global actualizado para no ofuscar 4xx/5xx controlados.
  - **Tour V2**: Tour rediseñado a v2: 6 slides, iconos SVG, animaciones (icon-pop, breathing, shimmer, text-rise), callouts en slide 4 (naranja) y 5 (rosa), track deslizante, reflow JS para redisparar animaciones.
- **Ola 4 — Pre-lanzamiento completo (listo para deploy):**
  - Test suite pre-lanzamiento: 148 tests de bloques 1–3 + 1 regresión manual + 3 tests API clientes con billing vencido.
  - Fix crítico dual JWT secret: `config.py` ahora lee `JWT_SECRET_KEY → SECRET_KEY → JWT_SECRET` con `AliasChoices`, alineado con `main.py`.
  - Suite completa: **439 passed, 102 skipped**; cobertura 40%.
  - Hotfixes de producción: modal 402 abre perfil, `/api/clientes` funciona en `past_due`/trial vencido, `saveOperationToHistory` no crashea ante 402.
  - Pendiente: smoke real de pago + webhook con nuevas credenciales de MercadoPago.
- **Plan 03 cerrado (Ola 2):** endpoint `/api/clientes/search?q=` para búsqueda server-side; picker con debounce; botón **+ Nuevo cliente** en review con mini formulario inline para alta rápida de cliente desde la operación.
- **Fix urgente tabla NCM:** ahora muestra **Valor unitario** y **Peso unitario** junto con Ref./Descripción/Origen/Cant/Código NCM.
- **Fix Asistente NCM (2026-06-21):** el overlay del Asistente NCM no abría porque `importClientesModal` en `dashboard_v2.html` tenía un `</div>` faltante que hacía que el navegador anidara `ncmOverlay` dentro del modal oculto. Arreglado. Además: delegación de eventos en `tbody` para clicks del botón Asistente, animación de apertura/cierre más fluida, cálculo de días de trial corregido (`* 60` extra), y modal 402 con parámetros correctos (`acceptText`/`kind`).
- **TODO próxima sesión:** optimizar velocidad de sugerencias NCM — cachear modelo Gemini en memoria (hoy se reinicializa en cada llamada), cachear historial NCM con recarga lazy, y pre-normalizar keys del historial al cargar.
- **Multi-tenant NCM + import planilla maestra (2026-06-21):** historial NCM pasa de shared (`ncm_historial.json`) a por-owner (`ncm_historial_{username}.json`). Nuevo endpoint `POST /api/ncm/import-historial` + botón "Importar planilla NCM" + modal en pantalla NCM para subir CSV/Excel con descripción+NCM. Duplicados actualizan NCM sin incrementar count.
- **Guía KIT Maria + validación previa (2026-06-21):** panel colapsable "¿Cómo cargar en KIT Maria?" en pantalla Ready con 4 pasos. `validate_for_kit_maria()` valida reglas específicas (NCM ≥8 dígitos, descripción ≥10 chars, peso > 0, incoterm válido, moneda válida) antes de generar el TXT. Advertencias no bloquean, errores sí. Advertencias agrupadas por tipo (1 línea por tipo, no por item).
- **Organizaciones paso 4 (2026-06-21):** UI completa. Landing con botón "Crear cuenta de estudio" y form dedicado. Registro con ?invite=TOKEN muestra banner del estudio. Dashboard con sección "Mi estudio" en perfil: miembros, invitar (link copiable), remover. Fixes: validate invitation y registro con invite_token comparaban fechas con/sin tz (SQLite no guarda tz) → datetime.utcnow(). Link de estudio visible en login y sección de precios. Texto auth-hint agrandado. Próximo: panel admin interno.
- **Precio actualizado (2026-06-21):** de $30.000 a $45.000/mes en landing, dashboard y simulador. Trial unificado a 14 días.
- **Fix banner trial (2026-06-21):** el banner azul de "15 días de prueba" quedaba pegado al contenido de abajo porque tenía margen inferior 0. Versión final con margen 0.25rem arriba/abajo y padding interno reducido para que sea más compacto.
- **Fix select de plan en landing (2026-06-21):** el texto del plan en el modal de registro se cortaba ("Premium — 14 días gratis - luego $30.000/mes - 10..."). Se acortó el texto, se estilizó el select igual que los inputs y se amplió el modal de 380px a 400px.
- **Fix tour de bienvenida (2026-06-21):** el tour no aparecía al registrar usuario sin verificación de email (default beta). Faltaba setear flag `cdi_force_tour_after_signup` en sessionStorage en el camino directo al dashboard. Fix en `landing.html`.
- **UX modal de perfil + topbar (2026-06-21):** 6 fixes de UI. (1) Botón "Crear cliente" duplicado en review eliminado — solo el banner azul de arriba. (2) Banner de importador nuevo ahora aparece también para importadores sin CUIT argentino. (3) Pill de usuario en topbar más visible (borde + nombre + iniciales en azul). (4) Modal de perfil más rápido (120ms, sin blur). (5) Scroll del modal arreglado con grid + overflow:hidden — botones Guardar/Cancelar siempre visibles. (6) Email editable en perfil con validación de formato y chequeo de duplicados en backend.
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

---

## 11. TODO siguiente sesión

- **Tests flakies (`test_api_clientes_billing.py`)**: Durante la ejecución de la suite completa, este test falla con `sqlite3.OperationalError: no such table: users`. Si se corre el archivo aislado, **pasa todo en verde**. Hay que resolver el estado sucio de la base de SQLite async entre tests concurrentes en `conftest.py` (probablemente por uso de lifespan en testclient o fixtures asíncronas).
- **Avanzar con Fase 3 / Pilar A**: Una vez aprobados los resultados de PMF del cohort retention y el Pilar B, iniciar el Pilar A (API Pública para sistemas corporativos).