# Sprint 25 días — bitácora

> Plan completo: `/Users/Emi/.windsurf/plans/sprint-25dias-v4-equipo-83b3aa.md`
> Meta: 5 despachantes activos + 2–3 pagando + producto completo (MP real, multi-puesto, VUCE scraping, proforma).
> Inicio: 2026-05-26.

Cualquier asistente (Cursor, Antigravity, Cascade, Claude) que continúe este sprint, lee este archivo + `HANDOFF.md` + `CHANGELOG.md` y arranca desde donde quedó.

## Día 1 — 2026-05-26

### Hecho

- **T1** fix de los 2 tests rojos preexistentes:
  - `tests/test_pdf_avg_functional.py::test_excel_generation_with_empty_ncm_fields`: el test asumía `os.path.exists(filename)` en CWD; `create_maria_excel` devuelve solo el filename y guarda en `CDI/data/`. Test ajustado para construir el `output_path` absoluto.
  - `tests/test_regression_phase0.py::test_pdf_upload_rejects_non_pdf`: aceptar 401 además de 400/422 (desde Wave 1 el endpoint pide auth, el rechazo llega antes de validar el archivo).
  - **Resultado:** `2 passed` en `pytest -xvs`.
- **T2** smoke E2E manual:
  - `/health` → 200 ✓
  - `BASE_URL=... bash scripts/testing/smoke_friccion.sh` → OK ✓
  - `/` y `/web` → 200 (landing) ✓
  - `/v2` → 404 (no hay ruta directa, normal: `/v2/...` se accede via static mount o redirect post-login)
  - `/landing_nueva` → ❌ 500 (archivo `landing_nueva.html` no existe). **Fix aplicado:** redirect 307 a `/`.
  - `/upload_pdf/public` sin auth → 401 ✓ (esperado post-Wave 1).
- Creados `docs/sprint_25_progress.md` (este archivo) y `docs/discovery_guion.md`.

### Fricciones detectadas (para fix con tiempo)

- `/landing_nueva` daba 500. **Resuelto** con redirect 307 a `/`.
- Plantilla `templates/landing_nueva.html` no existe pero el handler la pedía. La ruta queda como alias histórico para no romper bookmarks.

### Día 1 cerrado · resto de tareas hechas

- **T3** cartel de bienvenida en `/v2` (`#welcomeCard` en `dashboard_v2.html`):
  - 3 pasos: subir PDF / revisar items / generar TXT y cargar al Kit SIM 7.0 (ARCA / Malvina).
  - Aparece solo en el primer login. Persiste en `localStorage.cdi_welcome_seen`.
  - Tracking: `welcome_card_shown` y `welcome_card_dismissed`.
  - CSS: `.welcome-card` en `app_v2.css` (estilo Apple minimal).
  - JS: `setupWelcomeCard()` en `app_v2.js`, llamado en bootstrap.
- **T4** copy de `landing.html` actualizado para mencionar **Kit SIM 7.0 (ARCA / Malvina)** explícitamente:
  - Hero: "...te devuelvo el TXT listo para pegar en tu **Kit SIM 7.0** (ARCA · Malvina)".
  - Step final: "TXT al Kit SIM" (antes "MARIA sale").
  - Meta description y OG description actualizadas igual.
  - `landing_legacy.html` no tocado (no se sirve, solo referencia).
- **Trial 14d → 15d** en backend (`main.py`): `register` ahora arranca con `trial_ends_at = now + 15d` cuando el user carga tarjeta. Comentarios actualizados. La lógica de `simulate-charge` sigue extendiendo +30d por ciclo mensual (otro concepto).
- **Naming "Kit María" → "Kit SIM"** en landing, dashboard y discovery_guion.md (decisión de PM: queda más limpio).

## Día 6 · T10 (tests E2E billing autoservicio)

**Decisión PM:** antes de cobrar real, red de tests sobre el flujo de billing. Si esto se rompe en silencio mientras vendemos, el dolor es enorme (chargebacks, users sin acceso, etc).

### Cobertura (13 tests)

`tests/test_billing_autoservicio.py`:

- **Cambio de password** (4 tests):
  - OK con pass actual correcta + login con la nueva funciona.
  - 401 con pass actual incorrecta.
  - 400 con pass nueva < 8 chars.
  - 400 con pass nueva igual a actual.
- **Cancelar plan** (3 tests):
  - Desde trial → 200 + `canceled` + `service_until` mantiene `trial_ends_at`.
  - Desde `none` (sin tarjeta cargada) → 409.
  - Cancelar dos veces → la segunda 409.
- **Reactivar plan** (3 tests):
  - Cancelado con período vigente → 200 + `active` + `needs_checkout=False` (sin re-cobro).
  - Sin haber cancelado → 409.
  - Período ya vencido → 200 + `past_due` + `needs_checkout=True` (front debe abrir checkout).
- **Auth obligatoria** (3 tests): `change-password`, `cancel`, `reactivate` → 401 sin cookie.

### Fix de infraestructura de tests

- `conftest.py` migrado de `sqlite:///:memory:` a archivo temporal en `/tmp`. Razón: SQLite in-memory crea una DB separada por cada conexión async; los tests con multi-sesión rompían con "no such table".
- Listener de evento `connect` aplica `PRAGMA journal_mode=WAL` + `PRAGMA busy_timeout=30000` al arrancar cada conexión SQLite. Razón: bcrypt en threadpool tarda ~300ms y, sin WAL + busy_timeout, otra request concurrente disparaba `database is locked`.

### Fuera de scope

- **Integración real MP sandbox.** Requiere `MP_ACCESS_TOKEN=TEST-...` y red. Queda en smoke manual.
- **Webhook de pagos**: ya cubierto por `test_mp_webhook_signature.py` (Día 2).

## Día 5 · T9 (settings + billing autoservicio)

**Decisión PM:** extender el `profileModal` existente en vez de crear pantalla nueva. Menos navegación, menos código duplicado, mismo lugar donde el user ya entra a tocar CUIT/defaults.

### Backend (3 endpoints)

- `POST /api/user/change-password` (`main.py` ~1387): requiere `current_password` + `new_password`, valida ambos en threadpool. 401 si la actual no coincide. 400 si la nueva tiene < 8 chars o es igual a la actual.
- `POST /api/billing/cancel` (~1423): `billing_status='canceled'` pero **NO** corta servicio. Mantiene `trial_ends_at` como fecha hasta cuando el user ya pagó. 409 si el estado actual no es trial/active.
- `POST /api/billing/reactivate` (~1455): si `trial_ends_at` está en el futuro → vuelve a `active` sin cobrar. Si ya venció → marca `past_due` + responde `needs_checkout: true`.

### Frontend (profile.js + dashboard_v2.html)

- Modal de perfil tiene 2 nuevas secciones plegables (`<details>`):
  - **Seguridad**: 2 inputs (pass actual + nueva) + botón "Cambiar contraseña".
  - **Plan y facturación**: estado label, fecha relevante (cambia copy según estado), PM `brand ···· last4`, y 3 botones contextuales:
    - `trial`/`active` → muestra Cancelar.
    - `past_due`/`none` → muestra Activar.
    - `canceled` → muestra Reactivar.
- `loadBilling()` pega a `/api/billing/me` (ya existía) en paralelo con `loadProfile()` al abrir el modal.
- Cancelación pasa por `CDI.confirm` (modal blocking) para evitar mistaps.
- Telemetría: `password_changed`, `billing_canceled`, `billing_reactivated`.

### Email change pendiente

Scope cortado. Requiere flow de re-verify (mandar nuevo email, link de confirmación, manejar el periodo en que tiene 2 emails). 1-2h de trabajo extra. Lo dejo para Día 6 si hay tiempo.

## Día 4 · T8 (pricing en landing) + T7 bloqueado

### T8 hecho (landing pricing)

- Nueva sección `#precio` en `landing.html` entre Capacidades y Seguridad.
- Tarjeta única: $15.000 ARS/mes, 6 bullets de qué incluye, CTA "Empezar 15 días gratis".
- CTA dispara `openAuth('register')` + telemetría `pricing_cta_clicked`.
- Topbar nav agregado link a `#precio`.
- Fix copy residual: "trial de 14 días" → "15 días" en form de registro.
- CSS: `.pricing-card` + `.pricing-list` con check verde, en `static/v2/landing.css`.
- Verificado live: `curl /` devuelve la sección con `15.000`.

### T7 BLOQUEADO (validación TXT Kit SIM)

**Por qué bloqueado:** no hay TXT de referencia validado por un despachante real. Busqué en todo el repo, en home directories, sólo aparecen .txt de docs (CLAUDE_BRIEF, FILE_LOCATIONS, robots, etc) — ninguno es output del Kit SIM.

**Mini-checklist para cuando llegue el TXT** (no perder tiempo después):

1. Comparar header/cabecera DDT byte a byte contra el output de `maria_generator.py`.
2. Verificar campos posicionales: `CDDTAGR`, `CDDIMP`, `DDTITEMS`, separadores, paddings (espacios vs ceros).
3. Encoding: ¿UTF-8 o latin-1? El generador hoy usa UTF-8.
4. Salto de línea: `\r\n` (Windows/MARIA) vs `\n`.
5. Contar items y validar totales (FOB, peso, unidades) coinciden con la factura.
6. Si hay diff → ajustar `maria_generator.py` y regenerar test.

**Para vos:** pedile a 1 despachante un TXT de un despacho real (anonimizado si querés) que él haya cargado OK en su Kit SIM. Con eso, T7 se cierra en 2-3h. Sin eso, no avanzo.

## Día 3 · T6-UI (banner billing en dashboard v2)

- **HTML** `#billingBanner` arriba de fake-source-banner en `dashboard_v2.html`. Estructura: icono + texto + CTA + close.
- **JS** `renderBillingBanner(user)` en `app_v2.js` (línea ~566). Llamada desde `loadCurrentUser` cuando llega `/auth/current_user`.
- **Estados:**
  - `trial` con días > 0 → soft (azul) "X días de prueba gratis. Activá el plan cuando quieras."
  - `past_due` → urgente (naranja con pulse) "Tu prueba gratis terminó. Activá el plan ahora."
  - `active` / `canceled` / `none` → oculto.
- **Click CTA** → `POST /api/billing/checkout` → `window.location.href = init_point` (redirige a MP).
- **Telemetría:** `billing_banner_shown`, `billing_cta_clicked`, `billing_banner_dismissed`.
- **Verificado live:** `curl /static/v2/app_v2.js` sirve la función nueva.

## Día 2 · T6-lite (MercadoPago real, backend solo)

**Decisión de PM:** NO hacer T6-full (subscripciones recurrentes con pre-approval, retries, chargebacks). Para MVP basta con cobro one-shot mensual + webhook validado.

- **CRÍTICO de seguridad:** `_verify_mp_webhook_signature()` HMAC-SHA256. Antes el webhook era abierto: cualquiera podía hitearlo con un body falso y activar premium gratis.
- **Webhook ahora sincroniza billing completo** al recibir `payment.approved`: `plan`, `billing_status='active'`, `trial_ends_at=now+30d`, `payment_provider='mercadopago'`, `payment_customer_id`.
- **Nuevo endpoint** `POST /api/billing/checkout` autenticado (username sale del JWT, no del body). Reemplazo seguro de `/api/payments/create-preference`.
- **Env nuevas** que **vos tenés que setear en Railway** antes de cobrar real:
  - `MP_ACCESS_TOKEN` (Production token de tu cuenta MP)
  - `MP_WEBHOOK_SECRET` (Secret del webhook que MP genera en el panel)
  - `MP_PLAN_PRICE_ARS` (default 15000, podés cambiarlo)
- **UI del checkout: NO HECHA hoy.** Día 3.
- **Tests:** `tests/test_mp_webhook_signature.py` (5 casos) + smoke regresión phase0 (7 verdes, 2 rojos preexistentes ajenos).

## Día 2 · T5-lite (multi-puesto / equipo, infra preparada)

**Decisión de PM:** NO hacer T5-full ahora (4-6h, riesgo alto, sin demanda validada). Hacer T5-lite (1h, sin riesgo).

- **DB:** nueva columna `users.team_owner_username VARCHAR(50) NULL` con FK self-ref a `users.username` e índice. Default NULL = el user es su propio team. En `database/models.py`.
- **Migración:** `_migrate_add_user_team_owner_column()` idempotente, corre en startup y vía `POST /api/dev/run-migrations` (label `user_team_owner`). SQLite y PostgreSQL.
- **API:** `get_current_user` ahora devuelve también `team_owner_username` (NULL hoy) y `effective_owner` (= username hoy). Esto deja el camino preparado para que endpoints futuros filtren por `effective_owner` sin tener que volver a leer el user de DB.
- **Refactor de queries: NO HECHO.** Las 71 referencias a `owner_username == user["username"]` siguen igual. Cambio postergado a T5-full, on-demand cuando un cliente real diga "mi asistente carga ops bajo mi CUIT".
- **Riesgo:** cero. Columna nueva opcional, ningún path la lee con valor != NULL todavía.
- **Tests:** `test_regression_phase0.py::TestPDFEndpoint` y `TestUserProfile` siguen verdes (2 passed).
- **Bug preexistente NO causado por mí:** `tests/test_regression_phase0.py::TestBackupRestore::*` (2 tests) fallan también en `main` antes de mi cambio. Verificado con `git stash`. No bloquea el sprint.
- Commit + push pendiente al final del Día 1.

### Para vos (paralelo)

- Mensaje a 4 contactos directos pidiendo 30 min discovery.
- A 1 contacto, pedile **además** acceso a Kit SIM 7.0 + 1 TXT real para Día 5 validación.
- 5 mensajes a 2do grado pidiendo presentaciones.
- Material disponible: `docs/discovery_guion.md` (8 preguntas), plantilla WhatsApp/email.

---

## Próximos días

### Día 2–4 (semana 1) — multi-puesto / equipo

- T5 tabla `team_members` + migración idempotente.
- T6 endpoints invite/list/delete + email de invitación.
- T7 pantalla `/v2/team` + badge "Operador de [Despachante]".

### Día 5–6 — validar TXT en Kit SIM real

- T8 sesión 1h con despachante: cargar TXT en Kit SIM 7.0.
- T9 ajustes a `maria_generator.py` según diferencias detectadas.

### Día 7

- Cierre Sem 1, smoke completo, tag `sprint25-sem1` propuesto.
