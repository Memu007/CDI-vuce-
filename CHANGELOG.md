# CHANGELOG

Historial de cambios visibles para el dueño del producto. Cualquier AI o humano que cierre una sesión de trabajo agrega una entrada acá.

Formato corto: fecha, 1–3 líneas, prefijo.

---

## 2026-06-01 · Sprint 25 días — Día 5 (T9 settings + billing autoservicio)

- **feat (api):** 3 endpoints nuevos autenticados:
  - `POST /api/user/change-password` (valida pass actual, mín 8 chars, hash en threadpool).
  - `POST /api/billing/cancel` (marca `canceled`, mantiene servicio hasta `trial_ends_at`).
  - `POST /api/billing/reactivate` (vuelve a `active` o redirige a checkout si el período venció).
- **feat (ux):** modal de perfil ahora tiene 2 secciones nuevas plegables:
  - **Seguridad**: cambio de password con validación inline.
  - **Plan y facturación**: estado, fecha relevante (trial vence / próximo cobro / servicio hasta), método de pago (last4 + brand), botones contextuales (Activar / Cancelar / Reactivar) con `CDI.confirm` para cancelar.
- **feat (telemetry):** `password_changed`, `billing_canceled`, `billing_reactivated`.
- **email change:** scope cortado por PM. Requería re-verify y complicaba T9. Pendiente.

---

## 2026-05-27 · Sprint 25 días — Día 4 (T8 pricing + T7 bloqueado)

- **feat (landing):** nueva sección `#precio` con tarjeta de plan único ($15.000 ARS/mes alineado con `MP_PLAN_PRICE_ARS`). 6 bullets de qué incluye, CTA "Empezar 15 días gratis" abre el form de registro.
- **fix (copy):** "Empezar trial de 14 días" → "15 días" en el botón de registro de la landing (residual del cambio del Día 1).
- **feat (telemetry):** evento `pricing_cta_clicked` para medir conversión landing → registro desde precio.
- **decisión PM:** T7 (validación de TXT contra Kit SIM 7.0 real) **bloqueado** hasta que un despachante pase un TXT bueno validado. No hay TXT de referencia en repo ni en home. Cambios al generador a ojo = ruleta rusa.

---

## 2026-05-27 · Sprint 25 días — Día 3 (T6-UI, banner billing en dashboard)

- **feat (ux):** banner de billing en dashboard v2 (`#billingBanner`). Muestra días de trial restantes (soft, azul) o trial vencido (urgente, naranja con pulse). CTA "Activar plan" llama `POST /api/billing/checkout` y redirige al `init_point` de MP.
- **feat (telemetry):** eventos `billing_banner_shown`, `billing_cta_clicked`, `billing_banner_dismissed` para medir conversión del trial al pago.
- **css:** `.billing-banner` + variante `.is-urgent` en `app_v2.css`. Estilo Apple minimal igual que welcome card y fake-source-banner.

---

## 2026-05-27 · Sprint 25 días — Día 2 (T6-lite, MercadoPago real)

- **security (CRÍTICO):** webhook `/api/payments/webhook` ahora valida firma HMAC-SHA256 con `MP_WEBHOOK_SECRET`. Antes cualquiera podía hitear el endpoint y activar premium gratis. En prod sin secret → rechaza todo.
- **fix (billing consistency):** webhook MP ahora sincroniza `billing_status='active'`, `trial_ends_at=now+30d`, `payment_provider='mercadopago'` y `payment_customer_id`. Antes solo cambiaba `plan` y dejaba el billing inconsistente.
- **feat (api):** nuevo `POST /api/billing/checkout` autenticado (saca `username` del JWT, no del body). Reemplaza al inseguro `/api/payments/create-preference` que aceptaba cualquier username del cliente. El viejo queda intacto para no romper landing legacy (no se sirve).
- **env:** nuevas vars `MP_WEBHOOK_SECRET` (HMAC) y `MP_PLAN_PRICE_ARS` (default 15000).
- **tests:** `tests/test_mp_webhook_signature.py` con 5 casos: firma válida, secret incorrecto, headers faltantes, sin secret en prod (rechaza), sin secret en dev (pasa).

---

## 2026-05-26 · Sprint 25 días — Día 2 (T5-lite)

- **feat (db):** nueva columna `users.team_owner_username VARCHAR(50) NULL` (FK self-ref + índice). Migración idempotente `_migrate_add_user_team_owner_column` corre en startup y `POST /api/dev/run-migrations`. Soporta SQLite y PostgreSQL.
- **feat (api):** `get_current_user` ahora devuelve `team_owner_username` y `effective_owner` (= username hoy, porque la columna está NULL para todos). Camino preparado para multi-puesto sin refactor invasivo.
- **decisión (PM):** T5-full (refactor de 71 queries para filtrar por `effective_owner`) postergado a on-demand cuando un cliente real lo pida. Discovery todavía no validó el caso de uso multi-user.

---

## 2026-05-26 · Sprint 25 días — Día 1 (T1–T4)

- **fix (tests):** `test_excel_generation_with_empty_ncm_fields` ahora arma el path absoluto en `CDI/data/`. `test_pdf_upload_rejects_non_pdf` acepta 401 además de 400/422 (Wave 1 cambió a auth obligatoria).
- **fix:** `/landing_nueva` ya no devuelve 500. Ahora redirige 307 a `/`.
- **feat (ux):** cartel de bienvenida en `/v2` con 3 pasos (subir PDF → revisar → generar TXT al Kit SIM). Persiste dismiss en `localStorage.cdi_welcome_seen`.
- **docs:** copy de `landing.html` actualizado: hero menciona "Kit SIM 7.0 (ARCA · Malvina)" y step final "TXT al Kit SIM".
- **fix (billing):** trial gratis pasó de 14 a 15 días en `register` (`User.trial_ends_at = now + 15d`). Decisión de PM.
- **docs (naming):** "Kit María SIM 7.0" → "Kit SIM 7.0" en landing, dashboard y discovery_guion. Más limpio para venderlo.
- **docs:** creados `docs/sprint_25_progress.md` (bitácora del sprint, handoff-friendly) y `docs/discovery_guion.md` (8 preguntas + plantillas WhatsApp/email).

---

## 2026-05-22 · Seguridad Wave 3 (rate limit IA + audit XSS)

- **security (ai-cost):** nuevo módulo `proyecto_maria/core/ai_quota.py` con cuota diaria por usuario. `POST /upload_pdf/public` ahora levanta 429 si el usuario excede `AI_DAILY_PDF_LIMIT` (default 50/día). Corta abuso / facturazo de tokens Gemini.
- **safe (xss):** auditoría de `innerHTML` en `static/v2/screens/{clientes,catalogo,review,ncm_notes}.js`. Todos los datos de usuario o IA (nombre, CUIT, descripción, NCM, notas, etc.) ya pasan por `CDI.escapeHtml(...)`. Sin cambios; queda documentado.
- **pendiente (no urgente):** sacar `'unsafe-inline'` de CSP `script-src` y agregar header CSRF custom — quedan para después de feedback de la prueba (cambios invasivos en frontend).

---

## 2026-05-22 · Seguridad Wave 2 (prompt-injection + multi-tenant check)

- **security (ai):** `proyecto_maria/pdf_extractor.py` ahora encierra el texto del PDF entre `<<<DOCUMENTO>>>...<<<FIN_DOCUMENTO>>>` y le aclara al modelo que todo lo de adentro es DATO crudo, no instrucciones. Defensa contra prompt-injection vía PDF malicioso.
- **security (ai):** cap duro del texto enviado al LLM (`PDF_LLM_MAX_INPUT_CHARS`, default 60k chars) para evitar DoS por tokens / facturazos de API.
- **security (ai):** validación estricta del JSON que devuelve el modelo antes de persistir: `pieza` solo dígitos (6-8); `origen` solo letras ISO; strings se limpian de chars de control; máximo 2000 items por factura. Defensa en profundidad si el modelo igual se "deja convencer".
- **safe (multitenant):** revisión rápida de endpoints `/api/clientes`, `/api/ncm/notas`, `/api/catalog/*`: todos usan `Depends(get_current_user)` y filtran por `owner_username` (71 referencias en `main.py`, helper `_get_owned_client` consistente). Sin cambios; queda documentado.

---

## 2026-05-16 · Seguridad Wave 1 (pre-prueba)

- **security (auth):** el fallback de `proyecto_maria/auth/jwt_utils.py` que devolvía un `admin` fake cuando `ENVIRONMENT=testing` ahora exige además estar dentro de pytest real (`PYTEST_CURRENT_TEST`). Si por error Railway recibe esa variable, se devuelve 401, no admin.
- **security (auth):** el usuario fake de tests baja de `roles=["admin"]/plan=premium` a `roles=["operador"]/plan=basic` (mínimo privilegio).
- **safe:** los routers que usan `require_role`/`require_plan` viven en `routers/_deprecated/` y NO están enchufados en `main.py`; el riesgo era latente, no activo.
- **verificado:** sin leaks de `JWT_SECRET_KEY`, `GEMINI_API_KEY` ni `MP_ACCESS_TOKEN` en historial de git; `.env*` ignorado correctamente; CORS ya falla cerrado en prod si `ALLOWED_ORIGINS` está vacío; `/upload_pdf/public` y `/upload_excel/public` ya requieren auth (el sufijo `public` queda solo por compat del frontend).

---

## 2026-05-07 · Popups unificados en v2

- **fix (ux):** todos los carteles de confirmación de la app v2 ahora usan el modal visual de CDI en vez del cartel nativo del navegador.
- **safe:** se verificó que no queden `window.confirm`, `window.alert` ni `window.prompt` en `static/v2`; la versión clásica v1 no se tocó.

---

## 2026-05-07 · UX eliminar cliente y telemetría

- **ux (clientes):** eliminar cliente ahora usa un modal propio de la app, no el cartel nativo del navegador.
- **fix (telemetría):** el frontend usa `/api/session/state` y silencia la telemetría si el navegador o una extensión la bloquea, sin afectar el flujo.

---

## 2026-05-07 · Fix guardado de operación al cliente

- **fix (historial):** cuando una operación no se podía guardar al historial del cliente, fallaba en silencio. Ahora muestra toast con el error real y lo loguea.
- **fix (backend):** `POST /api/clientes/{id}/operaciones` ahora devuelve HTTP 500 con detalle en vez de `{success: false}` mudo.
- **safe:** la generación del MARIA.TXT no se ve afectada; el guardado al historial sigue siendo best-effort pero ahora visible.

---

## 2026-05-04 · Importador de clientes (migración desde PreMaría y otras apps)

- **feat (clientes):** botón "Importar" en Clientes acepta CSV y Excel, detecta solo formato simple o de PreMaría por nombres de columna.
- **feature:** salta duplicados por CUIT (mismo owner) y, si vienen `descripcion` + `ncm`, alimenta el autocatálogo del cliente.
- **safe:** muestra resumen post-import (creados / duplicados / productos aprendidos / errores). Endpoint `POST /api/clientes/import`.

---

## 2026-05-04 · Carga manual de operaciones

- **feat (upload):** nuevo botón "Cargar manualmente" para crear operaciones sin PDF/Excel.
- **feature:** elegís cliente, completás productos (descripción, cantidad, precio, NCM opcional), y se guarda como operación `draft`.
- **safe:** al guardar se redirige a Revisión igual que si viniera de PDF. El autocatálogo aprende los NCMs cargados a mano.

---

## 2026-05-04 · Tour wizard con slides de bienvenida

- **ux (onboarding):** al alta nueva se abre automáticamente un wizard de 5 slides explicando el producto paso a paso (PDF, revisión, clientes, autocatálogo, MARIA.TXT).
- **safe:** si el usuario la cierra, no se repite. El botón `Ver tour` la vuelve a abrir.
- **feature:** navegación con `Siguiente`/`Anterior`, dots de progreso y `Empezar operación` en la última slide.

---

## 2026-05-04 · Fix eliminar clientes

- **fix (clientes):** al eliminar cliente ahora también se limpia su historial de productos asociado para evitar errores 500.
- **fix (clientes):** el historial de operaciones devuelve error claro si algo falla, sin mostrar stacktrace.

---

## 2026-05-04 · Modo prueba para reusar email de registro

- **feat (registro):** se agregó modo controlado por variables `REGISTER_TEST_EMAILS` y `REGISTER_TEST_EMAIL_REPLACE=true` para liberar emails de prueba y re-registrarlos.
- **safe:** el comportamiento normal sigue bloqueando emails duplicados; no se tocaron `.env` ni secrets.

---

## 2026-05-04 · Confirmación visible al crear cliente

- **ux (cliente):** al crear o asignar cliente desde PDF no reconocido ahora queda una tarjeta verde visible en Revisar/Listo, además del toast.
- **ux (estética):** la tarjeta usa el mismo lenguaje visual que los banners livianos de la app.
- **ux (review):** el banner de crear/asignar cliente no reconocido ahora resalta más sin volverse invasivo.
- **ux (review):** ajuste fino de padding y separación para que el banner no quede recortado/aplastado.

---

## 2026-05-04 · Rules más livianas

- **docs:** `AGENTS.md` quedó como resumen maestro corto para no sobrecargar asistentes.
- **rules:** nueva regla `copiloto-producto` concentra trato, negocio primero y no asumir decisiones sensibles.

---

## 2026-05-04 · Regla modo tranquilo

- **docs:** nueva regla compartida `modo-tranquilo-calidad`: calidad sobre velocidad, cambios chicos, revisar y probar antes de seguir.
- **rules:** `AGENTS.md` suma el principio para que lo sigan todos los asistentes.

---

## 2026-05-04 · CUIT argentino sin prefijo país

- **fix (extracción):** el prompt de Gemini ahora aclara que el CUIT argentino tiene exactamente 11 dígitos y no debe incluir prefijos como `AR`.
- **fix (normalización):** si la extracción trae `AR306121238201`, backend/frontend lo limpian a `306121238201`.

---

## 2026-05-04 · Cliente por operación, sin selección global

- **refactor (cliente):** el cliente ya no queda persistido globalmente entre operaciones. PDF arranca limpio y usa detección por CUIT o rescate crear/asignar.
- **feat (excel):** Excel ahora pide elegir cliente puntualmente para usar mapeo personalizado; si se cancela, permite seguir con mapeo genérico.

---

## 2026-05-04 · PDF no arrastra cliente anterior

- **fix (cliente):** al subir un PDF nuevo se limpia el cliente activo anterior antes de redetectar por CUIT. Si el CUIT existe, se activa el cliente correcto; si no, queda listo para crear/asignar.
- **fix (review):** si el PDF trae razón social del importador pero no trae CUIT válido, igual aparece la opción de crear/asignar cliente.
- **safe:** este ajuste quedó reemplazado por el selector puntual de Excel de la entrada siguiente.

---

## 2026-05-04 · Alta corta de cliente al final del PDF

- **feat (ready):** el panel final para cliente no reconocido ahora explica que puede guardarse desde la factura para que la próxima vez se detecte solo.
- **feat (cliente):** alta corta prellenada con razón social, CUIT y domicilio si viene de la factura; al guardar crea el cliente, lo activa y asocia la operación.
- **ux:** el panel final se agrandó y resalta más para que el despachante no lo pase por alto.

---

## 2026-05-04 · Fix creación de clientes sin email en Railway

- **fix (backend):** la migración de `clients.email` nullable ahora también corre en Postgres/Railway. Esto evita el `500` al crear un cliente desde el PDF cuando solo tenemos razón social + CUIT.
- **fix (errores):** `POST /api/clientes` ahora captura errores de integridad de base y devuelve mensaje legible en vez de un 500 mudo.

---

## 2026-05-03 · Reglas de trabajo: equipo virtual + persistencia GitHub

- **docs:** dos reglas nuevas para todos los asistentes (Cursor / Antigravity / Cascade):
  - **Equipo virtual de 6 roles** (PM, Tech Lead, Backend, Frontend, QA, Security/DevOps). Cada respuesta no-trivial empieza indicando los roles consultados entre corchetes.
  - **Persistencia GitHub al día**: después de cada cambio significativo, actualizar `HANDOFF.md` + `CHANGELOG.md`, commit y push. La fuente de verdad es GitHub para que cualquier asistente continúe donde se quedó otro.
- **wrappers para todos los IDEs**: `AGENTS.md` es ahora la fuente de verdad oficial. Wrappers cortos creados para que cada asistente las encuentre en su archivo nativo:
  - `.cursor/rules/*.mdc` (Cursor)
  - `.windsurf/rules/leeme-primero.md` (Cascade / Windsurf)
  - `CLAUDE.md` (Claude Code)
  - `.github/copilot-instructions.md` (GitHub Copilot)
  - `CONVENTIONS.md` (Aider y otros)

---

## 2026-05-03 · Rescate de cliente (banner + panel huérfana)

- **feat (review):** banner de importador no reconocido suma tercera opción **Asignar a uno existente** que abre un picker de tus clientes. Si elegís uno sin CUIT, le sumamos automáticamente el CUIT del PDF (siempre que no choque con otro cliente).
- **feat (ready):** panel **"operación huérfana"** en pantalla Listo. Si terminás el TXT MARIA sin cliente activo, aparece un panel discreto con tres opciones: crear cliente nuevo (form prellenado), asignar a uno existente, o más tarde. La operación queda guardada al historial del cliente elegido.
- **fix (data integrity):** pre-check `by-cuit` antes de **POST** y **PUT** de clientes (el backend no valida duplicados de CUIT). Si ya existe, ofrecemos usar ese.
- **fix (idempotencia):** `saveOperationToHistory` ahora respeta `state.operationSavedFor` para no duplicar la operación si la pantalla Listo se re-renderiza (back→forward, panel huérfana asignando cliente).
- **feat (componente):** `cliente_picker.js` nuevo, reusable (~200 líneas). Modal con búsqueda en vivo, ESC cierra, fallback a `GET /api/clientes` si el cache está vacío.
- **telemetría:** `importador_assign_existing_*`, `importador_cuit_attached_to_existing`, `importador_create_blocked_by_cuit_match`, `op_orphan_panel_shown/create_clicked/assign_clicked/dismissed/resolved`.
- Backend intacto.

---

## 2026-05-03 · Hints contextuales just-in-time

- **feat (hints):** 3 micro-tooltips que aparecen UNA sola vez en el momento exacto que cada feature se activa, con datos reales del usuario:
  - **🧠 Memoria activada** — al asignar el primer NCM: "Guardamos este NCM para [Cliente] · [Proveedor]".
  - **📌 Nota guardada** — al agregar la primera nota NCM: se ata al cliente activo.
  - **✨ Auto-catálogo en acción** — la primera vez que aparece el banner de autocompletado.
- **chore:** motor `CDI.hint(id, opts)` reusable en `proyecto_maria/static/v2/screens/hints.js`. Persistencia por usuario en `localStorage` (key `cdi_hint_<id>_v1`).
- **telemetría:** `hint_shown` y `hint_closed` (`reason: cta|x|timeout|outside`) van a `telemetry_events`.
- **a11y:** respeto `prefers-reduced-motion` + responsive móvil.
- Para resetear y volver a verlos: `CDI.resetHints()` en consola del navegador.

---

## 2026-05-03 · Tour v2 — polish UX

- **feat (tour):** rediseño del tour de bienvenida. "Ver tour" del footer ahora arranca directo el paso 1 (saltea el cartelito, respeta la intención), cierra drawers abiertos antes, flechita que apunta al botón destacado, puntitos de progreso (● ● ○), ESC cierra, "Saltar" siempre visible. Sube z-index a 9600 para no quedar tapado en ninguna pantalla.
- **fix (css):** eliminado bloque CSS duplicado y truncado de `.ncm-autofill-banner` (arrastrado desde `f4dd88b`) que rompía el parseo de todos los estilos del tour.
- **a11y:** respeto `prefers-reduced-motion` — sin animaciones si el sistema las bajó.
- Archivos tocados: `proyecto_maria/static/v2/screens/tour.js`, `proyecto_maria/static/v2/app_v2.css`, `proyecto_maria/templates/dashboard_v2.html`.

---

## 2026-05-02 · Wave 1 cerrada + repo unificado

- **chore (repo):** unificado el proyecto en `~/Desktop/CDI-app/` (antes había tres clones que divergían). Subido a GitHub privado `Memu007/CDI-vuce-`. `.gitignore` ajustado: nunca van `.env`, `.env.afip`, `*.db`, `venv/`, `viejo/`, ni PDFs de clientes.
- **feat (importador):** auto-detect por CUIT cuando NO hay cliente activo (`GET /api/clientes/by-cuit/{cuit}`). Si el PDF trae un importador nuevo + nombre, en revisión aparece atajo "crear y usar".
- **feat (telemetría):** tabla `telemetry_events` + migración idempotente. `POST /api/ui/event` y alias `POST /api/session/state` persisten en SQL + JSONL.
- **feat (panel PM):** `GET /api/dev/wave1-kpis` y bloque Wave 1 en `/dev/dashboard` con sección "Activación" (usuarios únicos por acción + cuentas DB).
- **docs:** `wave1_invitation`, `wave1_activation_definitions`, `wave1_interview_kit`, `wave1_phase2_gate`.
- **fix (registro):** `minlength` del campo password alineado a 8 (antes 6, inconsistente con backend).
- **chore (handoff):** creado `HANDOFF.md`, `AGENTS.md` y este `CHANGELOG.md`. Tag `v0.1-wave1` puesto en este commit.

Tag: `v0.1-wave1`.

---

## Antes del 2026-05-02

Ver `docs/archive/` para handoffs y notas previas. La rama `main` arrancó limpia el 2026-05-02 con el commit `chore: estado inicial CDI-app + Wave 1 (...)` (`1d731d9`). El repo viejo `Memu007/CDI` quedó congelado como referencia, no se sigue actualizando.
