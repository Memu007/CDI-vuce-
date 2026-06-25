# CHANGELOG

Historial de cambios visibles para el dueño del producto. Cualquier AI o humano que cierre una sesión de trabajo agrega una entrada acá.

Formato corto: fecha, 1–3 líneas, prefijo.

---

## 2026-06-25 · fix: NCM acepta posición arancelaria completa con letra

- **fix (backend):** `validate_ncm` ahora acepta 6, 8, 10 u 11 dígitos + letra de control opcional (ej: `84713010900R`). Antes rechazaba la letra y solo aceptaba 6 u 8 dígitos.
- **fix (db):** Columna `operation_items.pieza` ampliada de `VARCHAR(10)` a `VARCHAR(20)`. Migración `_migrate_widen_pieza_column` para PostgreSQL. Antes se truncaba el NCM al guardar (`[:10]`).
- **fix (frontend):** `formatNcm` preserva letra sufijo. `isValidNcm` acepta 8/10/11 dígitos + letra. `maskNcm` usa `inputmode=text` y `maxlength=17`. Mensajes de error actualizados.
- **fix (maria_gen):** Normaliza espacios en NCM con puntos (`8471.30.00.900 R` → `8471.30.00.900R`).
- **feat (agrupación):** Unidades clasificatorias — se pueden asociar 2+ ítems con mismo NCM y origen en un solo grupo. En el TXT MARÍA se exportan como un solo [ART] con valores sumados y descripción concatenada. Nuevo campo `grupo_id` en `OperationItem`, endpoints `/api/operacion/{id}/agrupar` y `/desagrupar`, botón "Asociar ítems" en barra de batch de NCM, chip "Grupo N" en cada ítem agrupado (clic para desagrupar).
- **fix (agrupación):** `buildMariaRequest` en finalize.js ahora envía `grupo_id` y `unidad` al generador. `save_client_operation` y upload persisten `grupo_id` y `unidad` en DB. Test: 3 items (2 agrupados) → 2 [ART], MARTFOB=140, QARTKGRNET=4, QARTUNTDCL=4.

---

- **feat (security):** Blacklist de tokens JWT via `active_jti` en tabla `users`. Al re-loguear o resetear/cambiar password, los tokens anteriores se invalidan inmediatamente (antes seguían funcionando 24hs). Backward compat: `active_jti=NULL` no bloquea usuarios pre-migración.
- **fix (security):** `/auth/reset-password` y `/api/user/change-password` ahora validan password policy (min 8 + número/símbolo). Antes aceptaban cualquier password.
- **test (security):** Pentest Railway: 8/8 PASS. Token viejo → 401, token nuevo → 200. Password débil en reset/change → 400.

---

## 2026-06-21 · Fixes de seguridad pre-producción

- **fix (security):** CSRF enforce ahora bloquea por defecto en producción (antes solo logueaba). En dev/test sigue en modo report-only.
- **fix (security):** `/upload_pdf/public` ahora usa `validate_file_upload` con magic bytes + validación de PDF real. Antes solo chequeaba extensión.
- **fix (security):** Mock email no imprime body completo en logs de producción. En dev sigue mostrando para debug.
- **fix (security):** CSP header agregado (`default-src 'self'`, `frame-ancestors 'none'`) + `X-Content-Type-Options: nosniff` + `X-Frame-Options: DENY`.
- **fix (security):** `public_quote.html` ahora escapa todos los campos dinámicos del snapshot antes de inyectarlos en el DOM (XSS).
- **fix (security):** `clientes.js` escapa mensaje de error del backend antes de inyectarlo en el DOM.
- **fix (security):** `ClientService` ahora acepta `owner_username` en get/get_clients/update/delete/detect (defense in depth — los endpoints de main.py ya filtraban con `_get_owned_client`).
- **fix (security):** Log de upload PDF usa `sanitize_filename` en vez de imprimir el nombre crudo del archivo.
- **fix (security):** Todos los uploads de Excel/CSV ahora usan `validate_file_upload` con magic bytes: `/upload_excel/`, `/upload_excel_v2/`, `/api/clientes/import`, `/api/ncm/import-historial`. Antes solo validaban extensión.
- **fix (deps):** Librerías actualizadas por pip-audit: PyJWT 2.4→2.13, python-multipart 0.0.22→0.0.32, jinja2 3.1.2→3.1.6, FastAPI 0.135→0.138 + starlette 0.52→1.3.1, pydantic 2.7→2.13. Tapa ~20 CVEs conocidos. Smoke test OK.
- **fix (security):** `file_security.py`: import de `python-magic` ahora es lazy (try/except) para que el fallback funcione cuando no está instalado. Agregado `python-magic>=0.4.27` a `requirements.txt`. Sin esto, todos los uploads crasheaban con 500.
- **fix (security):** Password policy: `/auth/register` ahora valida mínimo 8 caracteres + al menos 1 número o símbolo antes de hashear. Antes aceptaba password de 1 char o vacío.
- **fix (security):** Session fixation: `create_access_token` ahora agrega claim `jti` (UUID random) al JWT. Cada login genera un token único. Antes dos logins del mismo usuario devolvían el mismo token.
- **fix (security):** Prompt injection en `/api/ncm/sugerir`: input del usuario ahora va entre delimitadores `<user_input>` y el prompt indica ignorar instrucciones dentro.
- **fix (security):** CSP unificado: sacado `unsafe-inline` de `script-src` y CDNs no usados en `security_middleware.py`. Eliminado CSP duplicado de `main.py` que era pisado por el middleware. Ahora hay un solo CSP consistente.
- **fix (security):** `unsafe-inline` restaurado temporalmente en `script-src` — 40+ handlers inline en 4 templates legacy. TODO fase 2: migrar a JS externo.
- **test (security):** Re-pentest OWASP Top 10 v2 verificado independientemente por la PM: 14/14 tests confirmados. Password policy, session fixation (jti), CSRF, cookies, uploads, JWT alg:none, SQLi, CORS, CSP, HSTS, force browsing, email duplicado, rate limiting — todos PASS. 2 pendientes para Railway (prompt injection + XSS endpoint público). Session fixation parcial: token viejo sigue funcionando (fase 2: blacklist jti).
- **fix (security):** Rate limiting en Railway: `_get_forwarded_address` lee `X-Forwarded-For` (commit 75667cb). Gunicorn workers 4→1 en Dockerfile para que MemoryStorage funcione (commit 2c0cb37). Si se necesitan más workers, setear `REDIS_URL` en Railway.
- **test (security):** Pentest Railway final: 17/17 PASS. `/docs` 404, `/openapi.json` 404, HSTS, CSP, cookies Secure+HttpOnly+SameSite, CSRF 403, auth bypass 401, JWT alg:none 401, SQLi 401, IDOR 404, uploads 400, CORS bloqueado, force browsing 404, password policy 400, rate limiting 429, session fixation jti — todos verificados en Railway real.
- **test (security):** Prompt injection NCM verificado en Railway: 3/3 PASS (inyección clásica, jailbreak con cierre de delimitador, data exfiltration — todos ignorados por la IA). XSS endpoint público verificado a nivel código: `escapeHtml()` escapa todos los campos dinámicos. Test end-to-end pendiente por Tarifar 503.
- **test (security):** Verificación visual en Railway (Puppeteer): landing, login, registro, quote público — todos cargan sin violaciones CSP. Password policy verificado desde navegador. Headers de seguridad confirmados.
- **SEGURIDAD CERRADA (2026-06-21):** Score 8/10. 36 tests locales + 17 tests Railway + 3 prompt injection + verificación visual = todos PASS. Fase 2 documentada en HANDOFF.
- **feat (security):** Blacklist jti: columna `active_jti` en `users` + migración idempotente. `create_access_token` ahora devuelve `(token, jti)`. En cada login/register/verify, se guarda el jti activo. En `get_current_user`, si `active_jti` no es NULL y no coincide con el jti del token → 401 "Token revocado". Reset/change password setean `active_jti = None` (invalida todos los tokens viejos). Backward compat: NULL = no bloquear usuarios pre-migración.
- **fix (security):** Password policy aplicada también en `/auth/reset-password` y `/api/user/change-password` (min 8 + número/símbolo). Antes solo validaba en `/auth/register`.
- **fix (security):** Actualizadas deps transitivas con CVEs pendientes: `aiohttp>=3.9.0`, `Pillow>=10.3.0`, `pyOpenSSL>=24.0.0`. Pinneadas explícitamente en requirements.txt. Smoke OK, sin breaking changes.
- **fix (security):** Pentest externo (Opus 4.8) — 0 críticos/0 altos/1 medio/2 bajos. M1: `/api/billing/simulate-charge` gateado en prod (404 salvo `ENABLE_SIMULATE_CHARGE=true`) — cierra bypass de billing. L1: `/dev/dashboard` HTML ahora exige `require_admin` (401/403 sin admin); los datos `/api/dev/*` ya estaban protegidos. L2 (enumeration en register) se deja como trade-off de UX.
- **chore (billing):** Plan Premium actualizado a 15 ops/mes (antes 10). Precio sigue en $45.000 ARS. Actualizado en `billing_service.py`, landing, dashboard y doc de planes. Endpoint `/api/billing/plans` confirma price:45000, ops:15.

---

## 2026-06-21 · Fixes UX: revisión, perfil y topbar

- **feat (quotes):** página pública ahora muestra estado en vivo de la operación (Borrador → Oficializada → Canal → Liberada) con timeline visual. El despachante cambia el estado en el cockpit y el cliente lo ve al refrescar el link. El presupuesto sigue siendo foto fija. Auditorado por QA (OK).
- **fix (quotes):** bug latente en timeline — `const currentIdx` reasignado tiraba TypeError si llegaba un estado no reconocido. Cambiado a `let`.
- **feat (landing):** botones CTA en el hero — "Empezar 14 días gratis" y "Ver de qué se trata". Antes el usuario tenía que scrollear hasta precio para encontrar un botón.
- **fix (landing):** sacada jerga "Gemini Vision" de la card de capacidades. Ahora dice "Si el PDF es escaneado (una imagen, no texto), lo lee igual con IA".
- **fix (landing):** credenciales demo (demo/demo123) ahora solo se muestran en localhost. En producción no aparecen.
- **fix (landing):** CTA del hero ahora abre el registro directo (antes solo scrolleaba a precio). Más fluido: 1 click en vez de 2.
- **fix (landing):** placeholder del login cambiado de "emiliano" a "tu_usuario" — era un nombre de ejemplo demasiado específico.
- **feat (landing):** sección "Cómo funciona" con 5 pasos (Subir, Revisar, NCM, Validar, Descargar). Explica el flujo que el mockup del hero solo muestra visualmente.
- **fix (landing):** pricing card ahora menciona que se pueden recargar operaciones extra desde el dashboard.
- **fix (landing):** link "Cómo funciona" agregado al topbar — antes la sección existía pero no se podía saltar directo desde arriba.
- **fix (ux):** botón "Crear cliente" dejó de aparecer duplicado en revisión. Solo queda el banner azul de arriba.
- **fix (ux):** banner "Este importador no está en tus clientes" ahora aparece también para importadores extranjeros sin CUIT argentino.
- **feat (ux):** pill de usuario en topbar — unifica nombre + iniciales en azul en un botón visible con borde y hover. Antes era un círculo gris chico difícil de ver.
- **fix (perf):** modal de perfil más rápido: animación reducida a 120ms, `backdrop-filter: blur` eliminado del overlay (era costoso en GPU).
- **fix (ux):** modal de perfil: al expandir secciones (defaults, cambiar contraseña, plan) el contenido de abajo quedaba tapado. Reestructurado con CSS Grid + `overflow:hidden` en `.modal` para que el body scrollee de verdad y el footer quede fijo.
- **feat (perfil):** email ahora es editable en el modal de perfil. El backend valida formato y chequea que no esté en uso por otro usuario antes de guardar.
- **fix (backend):** registro `/auth/register` no validaba formato de email — aceptaba cualquier texto. Ahora valida con regex antes de crear el usuario. Frontend también valida antes de enviar.
- **feat (tour):** slide 7 nuevo en tour de bienvenida — explica que en el perfil se configuran CUIT y defaults de operación, y que se aplican solos a cada operación nueva.

---

## 2026-06-21 · Organizaciones (estudios) — paso 4: UI

- **feat (landing):** botón "Crear cuenta de estudio" en el popover de auth. Formulario con nombre del estudio, usuario admin, email y password. Envia a POST /api/organizations/create.
- **feat (landing):** si la URL trae ?invite=TOKEN, muestra banner "Te invitó [estudio X]" y envía el token al registrar. Valida con GET /api/invitations/{token}.
- **feat (dashboard):** sección "Mi estudio" en el modal de perfil. Muestra nombre del estudio, lista de miembros con badge admin, botón invitar (genera link copiable), y opción de remover miembros (solo admin).
- **fix (backend):** endpoint GET /api/invitations/{token} comparaba fechas con y sin zona horaria (SQLite no guarda tz). Cambiado a datetime.utcnow() sin tz.
- **fix (security):** link de invitación en profile.js se insertaba con innerHTML sin sanitizar (XSS potencial). Cambiado a createElement + textContent + validación de esquema http/https.
- **fix (backend):** registro con invite_token comparaba expires_at con datetime.now(timezone.utc) (con tz) pero SQLite no guarda tz. Cambiado a datetime.utcnow() sin tz, igual que validate_invitation.
- **fix (ux):** link "Crear cuenta de estudio" agregado al form de login del modal y a la sección de precios de la landing. Antes estaba escondido dentro del form de registro.
- **fix (ux):** texto auth-hint agrandado (t-11 → t-13) y mejor contraste para mejor legibilidad.

---

## 2026-06-21 · Fix observaciones audit paso 3

- **fix (backend):** `require_active_billing` ahora devuelve `billing_entity.billing_status` (no `db_user.billing_status`) en el error 402. Antes, si la org estaba past_due, el frontend recibía el status del user.
- **fix (backend):** webhook de MP ahora guarda `payment_provider`, `payment_customer_id`, `payment_method_last4/brand` en la org, igual que en el flujo de user individual.

---

## 2026-06-21 · Organizaciones (estudios) — paso 3: billing por organización + fixes audit

- **feat (backend):** billing ahora se lee de la `Organization` cuando el user tiene `organization_id`. Helper `_get_billing_entity` decide si usar org o user. `billing_me`, `require_active_billing`, `record_operation_created`, checkout y topup usan la entidad correcta.
- **feat (billing):** `external_reference` de MP ahora soporta formato `org:{org_id}:{plan}` para pagos de organización. Webhook actualiza la org, no el user individual.
- **feat (db):** 6 columnas nuevas en `organizations` (payment_provider, payment_customer_id, payment_method_last4/brand, last_topup_at, extra_ops_expires_at). Migración idempotente `_migrate_add_org_billing_columns`.
- **fix (security):** `create_organization` valida mínimo 8 chars de password (observación 1 del audit).
- **fix (qa):** registro con invite_token reutiliza el objeto invitation en lugar de hacer 2da query (observación 2 del audit).

---

## 2026-06-21 · Organizaciones (estudios) — paso 2: endpoints de invite + registro

- **feat (backend):** 5 endpoints nuevos para gestionar estudios: crear estudio (`POST /api/organizations/create`), ver mi org (`GET /api/organizations/mine`), invitar usuario (`POST /api/organizations/invite`), validar invitación (`GET /api/invitations/{token}`), remover miembro (`DELETE /api/organizations/members/{username}`). Registro existente acepta `invite_token` opcional para unirse a un estudio. Verificado end-to-end.

---

## 2026-06-21 · Organizaciones (estudios) — paso 1: modelos + migraciones

- **feat (backend):** nuevos modelos `Organization` (estudio con billing propio) e `Invitation` (token para invitar usuarios). Campo `organization_id` en `User` (nullable). 3 migraciones idempotentes que corren en startup. No cambia comportamiento existente.
- **chore (pricing):** precio actualizado de $30.000 a $45.000/mes en landing, dashboard y simulador de pagos. Trial unificado a 14 días.

---

## 2026-06-21 · Select de plan en landing

- **fix (ui):** el texto del plan en el modal de registro quedaba cortado ("Premium — 14 días gratis - luego $30.000/mes - 10..."). Se acortó a "Premium — 14 días gratis, luego $30.000/mes", se estilizó el select igual que los inputs y se amplió el modal de 380px a 400px.

---

## 2026-06-21 · Espacio del banner de trial

- **fix (ui):** ajuste fino del banner azul de "15 días de prueba": margen inferior en 0 lo dejaba pegado al contenido de abajo. Versión final con margen 0.25rem arriba/abajo y padding interno reducido para que sea más compacto.

---

## 2026-06-20 · Tour Mejorado v2

- **feat (ui):** Rediseño completo del tour de bienvenida a v2 con 6 slides, iconos SVG, barra de progreso interactiva, track deslizante, animaciones sutiles optimizadas y callouts para diferenciar el producto.

---

## 2026-06-20 · Iteración C: Bug Fixes & UX

- **fix (admin):** Reemplazo de `func.strftime` (SQLite-only) por `sqlalchemy.extract` en `/api/admin/cohort-retention` para compatibilidad con PostgreSQL en producción.
- **fix (auth):** `get_current_user` defensivo contra planes inválidos (legacy "trial", None, etc.) con fallback automático a Premium y log de warning.
- **feat (ui):** Link y formulario "Olvidé mi contraseña" migrados a `landing.html` con mensaje anti-enumeración.
- **test (pilar B):** 2 tests nuevos en `test_pilar_b_quotes.py` cubriendo reordenamiento de items de Tarifar (match por NCM) y fallback a 503.
- **fix (handler):** Exception handler global respeta 4xx/5xx controlados (503, 429) sin ofuscar; solo ofusca 500 no controlados.

---

## 2026-06-20 · Iteración A: Auth Fix & Bootstrap Admin

- **fix (auth):** Corregido bug crítico en `/auth/login` que usaba el input del usuario (ej: email) como claim `sub` del JWT en lugar del `username` canónico de la BD, causando errores 401 sistemáticos.
- **feat (admin):** Implementada promoción automática a rol `admin` durante el arranque de la app para los usuarios (por username o email) listados en la variable de entorno `ADMIN_USERNAMES`. Esto desbloquea el acceso del dueño en producción sin requerir acceso directo a la BD.

---
## 2026-06-20 · Hardening Pilar B + Tests E2E

- **feat (backend):** refactor en `quote_router.py` para usar `asyncio.to_thread` al llamar a Tarifar (evitando bloquear el event loop).
- **feat (backend):** refactor en la lógica de armado de presupuestos para enlazar resultados de Tarifar vía `NCM` (propiedad `pieza`) en lugar de posición en el índice, mejorando robustez contra reordenamientos del proveedor externo.
- **fix (backend):** agregado try/except sobre la llamada a Tarifar para devolver HTTP 503 Service Unavailable y abortar persistencia si falla.
- **test (backend):** añadida suite E2E completa en `tests/test_pilar_b_quotes.py` cubriendo los 8 casos de uso requeridos (auth, propiedad, expiración, rate-limit, validación estructural).

## 2026-06-20 · Fases 0, 1 y 2 (Métricas PMF y Presupuestos Públicos)

- **feat:** agregado endpoint `/api/admin/cohort-retention` para extracción de métricas de retención de cohortes en usuarios activos (Fase 0).
- **test:** implementado `scripts/testing/smoke_quotes.sh` para validación automática del flujo de Presupuestos Públicos en producción y local.
- **chore:** sanitización de endpoints (Swagger oculto en prod, borrado de código muerto en `_deprecated/`).
- **refactor:** unificación de autenticación centralizada en `auth/dependencies.py` para prevenir dependencias circulares.
- **fix:** refactor del conector aduanero para bloquear modo fake en producción y asegurar 503 o datos estáticos con disclaimer.
- **feat:** nuevo pilar de negocio (Presupuestos Públicos) con endpoint shareable, inyección de alícuotas y botón "Copiar link" en el Cockpit y Calculadora.

## 2026-06-19 · Refinamiento UX de Carga Manual

- **feat (ui):** añadido botón inteligente "Crear cliente" en la validación de Carga Manual. Si el usuario ingresa un importador no registrado, el sistema permite crearlo y auto-asignarlo con un clic directo sin abrir modales.
- **fix (ui):** se corrigió un bug lógico donde al seleccionar un cliente desde el panel lateral, el mensaje de error de validación en pantalla ("Falta: Cliente asignado") no se limpiaba dinámicamente.
## 2026-06-19 · Auditoría UX (Simulación 50 usuarios)

- **feat (ui/ux):** añadido botón "+ Agregar producto" en NCM para evitar el punto muerto de Carga Manual.
- **fix (ui/ux):** validación de fechas flexible. Ahora auto-completa años de 2 dígitos y acepta barras/guiones.
- **feat (ui/ux):** Incoterms convertidos a campo abierto con sugerencias (`datalist`) para no bloquear casos atípicos (CPT, CIP).
- **fix (ui/ux):** buffer de Deshacer (Ctrl+Z) invalidado automáticamente al editar celdas a mano, evitando pérdida de datos por colisión de historial.


## 2026-06-19 · Robustez de UX/UI y Persistencia de Estado

- **feat (ui/ux):** se incorporó `localStorage` para autoguardar la operación en curso cada 2.5 segundos si el usuario está a la mitad del flujo. También se sumó una alerta de `beforeunload` para evitar que recargar la página (F5) o cerrar la pestaña por error borre el trabajo de la pantalla.
- **fix (ui/ux):** se agregó una validación estricta para bloquear el avance ("Siguiente" deshabilitado) tanto en la pantalla de Revisión como en NCM si el usuario vacía la lista de ítems (`items.length === 0`).
- **fix (ui/ux):** si ocurre un error de red o timeout al clickear "Validar" en el último paso para exportar a MARIA, el estado interno ya no se pierde; ahora se muestra un botón para poder "Reintentar" directamente en pantalla.

## 2026-06-19 · Campos requeridos dinámicos en Carga Manual

- **feat (ui):** en la pantalla de Revisión, si la operación es de Carga Manual, ahora se marcan explícitamente como requeridos (`· requerido` y `Falta completar` en naranja) los campos básicos que antes el sistema intentaba inferir del PDF (Razón social del proveedor, Razón social del importador, Número de factura y Fecha de emisión). Esto bloquea el avance hasta que el usuario complete lo mínimo indispensable, igualando la UX de plataformas como Intercom.

## 2026-06-19 · Nuevo flujo de Carga Manual

- **feat (ui):** rediseñado el flujo de "Carga manual". Ahora, en lugar de abrir un modal restrictivo, se inicializa una operación en blanco y redirige directamente a la pantalla de Revisión con una fila vacía. Esto permite aprovechar la vista de grilla (Excel-like) a pantalla completa para una carga de datos mucho más ágil y cómoda. Se eliminó el código del modal antiguo.

## 2026-06-19 · Limpieza de elementos de prueba en UI

- **chore (ui):** eliminados botones de "SISTEMA DEMO" de la barra superior y accesos directos de carga de "Simular operación" y "Descargar plantilla en blanco" para simplificar la interfaz en producción.

## 2026-06-19 · Fix validación de longitud NCM y AI prompt

- **fix (ncm):** corregida validación visual en tabla para marcar en rojo NCMs ingresados que no tengan exactamente 8 dígitos, en lugar de mostrarlos como válidos.
- **fix (ai):** actualizado prompt de Gemini para que las sugerencias de NCM siempre devuelvan 8 dígitos y no posiciones a nivel subpartida de 6 dígitos.

## 2026-06-19 · Origen masivo en tabla NCM

- **feat (ncm):** añadida opción para aplicar un "Origen para todos" a múltiples ítems seleccionados en la pantalla de NCM, funcionando igual que la asignación masiva de NCM.

---

## 2026-06-19 · Fix selector de archivo doble

- **fix (upload):** evitado bug que causaba que el selector de archivos del sistema se abriera dos veces seguidas al hacer clic en "Seleccionar archivo" (se previno inicialización duplicada de listeners en `upload.js`).

---

## 2026-06-16 · Pre-lanzamiento: Testing Bloque 1 y 2

- **test (prelaunch):** `tests/test_prelaunch_block1.py` — 44 tests del core sin pagos: registro + trial 14 días, login/logout, subida Excel, generación MARIA TXT, operaciones manuales, clientes + catálogo + CSV, límite 10 ops, errores como JSON. **44/44 passed**.
- **test (prelaunch):** `tests/test_prelaunch_block2.py` — 37 tests de billing: checkout MP (sandbox + demo), webhook firma/deduplicación/aprobado/rechazado, límite 10 ops → HTTP 402, trial vencido → past_due, top-up $10k/10ops/máx100/30días, billing/me, planes solo premium. **37/37 passed**.
- **fix (tests):** patching correcto de constantes de módulo (`IS_PRODUCTION`, `MP_WEBHOOK_SECRET`, `MP_ACCESS_TOKEN`) con `monkeypatch.setattr` en lugar de `setenv` post-importación.
- **fix (tests):** datetimes naive de SQLite normalizados con `.replace(tzinfo=timezone.utc)` para comparar con aware datetimes.
- **chore:** suite acumulada **93 tests pre-lanzamiento** en verde.

---

## 2026-06-18 · Webhook MercadoPago: soporte IPN + smoke test producción

- **feat (webhook):** `/api/payments/webhook` ahora acepta notificaciones IPN clásicas de MercadoPago (`?id=...&topic=payment`) como fallback cuando no llega firma HMAC. Esto resuelve el problema real en producción donde MP envía IPN sin headers de firma.
- **security (webhook):** si no hay firma HMAC válida Y no hay query params IPN válidos (`id`+`topic`), se rechaza con 401. Un request con body JSON sin firma ni query es rechazado.
- **feat (billing):** endpoint temporal `/api/payments/simulate-webhook` para smoke test de webhook sin pago real (protegido con `MP_WEBHOOK_SECRET`).
- **test:** `tests/test_webhook_ipn.py` — 3 tests de regresión para IPN (payment aprobado, merchant_order skip, HMAC inválido).
- **fix (config):** agregada constante `IS_TESTING` para distinguir entorno de testing.
- **smoke real:** checkout live con MP genera preference OK; pago con tarjeta de prueba procesado; webhook IPN recibido en producción (200). Usuario pasa de `trial` a `active` correctamente.

---

## 2026-06-16 · Hotfixes pre-lanzamiento: navegación v2, facturación y clientes

- **fix (v2):** modal HTTP 402 "Tu plan venció" ahora abre el perfil correctamente vía `CDI.openProfileModal()`, sin caer en URL rota `/v2?screen=profile`.
- **fix (clientes):** `GET /api/clientes` devuelve 200 incluso si el usuario está en `past_due` o trial vencido; corregido `GROUP BY` para PostgreSQL.
- **fix (billing):** `get_current_user` y `require_active_billing` hacen `db.refresh()` tras mutar `billing_status`, evitando estados inconsistentes.
- **fix (finalize):** `saveOperationToHistory` no crashea ante HTTP 402; devuelve `reason: 'payment_required'` para que el flujo pueda mostrar el modal de pago.
- **test:** `tests/test_api_clientes_billing.py` cubre listado de clientes con `past_due` y trial vencido.

---

## 2026-06-16 · Pre-lanzamiento: Testing Bloque 3 — Seguridad y Producción

- **test (prelaunch):** `tests/test_prelaunch_block3.py` — 66 tests de seguridad (60 originales + 6 de regresión del fix). CustomStaticFiles bloquea .env/.db/.jsonl/logs/secrets con 403; IS_PRODUCTION previene demo users; webhook 401 con firma inválida/ausente; JWT rechaza clave errónea/expirado/malformado/alg-none; 11 endpoints sensibles 401 sin auth; logging no expone tarjetas; past_due/none/canceled → 402; rate limiter no hardcodeado. **66/66 passed**.
- **fix (security 🔴):** Bug dual JWT secret resuelto — `config.py` cambiado de `alias="JWT_SECRET"` a `validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY", "JWT_SECRET")`. Ahora `jwt_utils.py` y `main.py` usan la misma clave en el mismo orden de prioridad. Tokens emitidos por `/auth/login` son verificables por `decode_token`. Ver [`config.py`](proyecto_maria/config.py).
- **finding (low):** `plan` defaultea a `"premium"` si el JWT no incluye el claim — tokens legacy/malformados heredan el plan más alto. Sin impacto en prod (todos los tokens nuevos incluyen el claim), no se corrige en esta sesión.
- **chore:** Suite completa **439 passed, 102 skipped**. Cobertura 40%. Pre-lanzamiento: Bloque 1 (44) + Bloque 2 (37) + Bloque 3 (66) + regresión manual (1) = 148 tests de pre-lanzamiento.

---

## 2026-06-15 · Ola 4: Seguridad y robustez post-MVP

- **fix (webhook):** códigos HTTP correctos: 401 firma inválida, 400 usuario no existe (MP reintenta), 500 bug inesperado. Logging estructurado con payment_id/external_reference. Deduplicación por `last_payment_id` para no reprocesar el mismo pago.
- **fix (billing):** plan único Premium validado estrictamente; registro rechaza `basic` con 400. `extra_ops_remaining` limitado a 100 créditos y expira a 30 días. Créditos vencidos se limpian automáticamente antes de evaluar límite.
- **feat (ui):** frontend intercepta HTTP 402 y muestra modal "Tu plan venció" con CTA a pagar.
- **feat (cron):** al iniciar la app, usuarios con trial vencido pasan automáticamente a `past_due`.
- **fix (static):** CustomStaticFiles rechaza `.env`, `*.db`, `*.jsonl`, logs/ y secrets/.
- **chore (deps):** `pytest>=9.1.0`, `pytest-asyncio>=1.4.0`, cobertura mínima 38% (`pytest.ini`).
- **fix (ops):** prevención de crash 500 en `/api/operations/manual` cuando se envía `client_id` nulo explícitamente (se ataja con 400).
- **test:** nuevo archivo `tests/test_operations_manual.py` para asegurar que operaciones sin cliente retornan 400 en lugar de 500.
- **docs:** `docs/billing/planes_y_cobros.md` con tabla de precios, límites, flujo trial, top-up y variables de entorno.
- **fix:** consistencia total del plan único Premium — eliminados todos los fallbacks y referencias a `basic` en `main.py`, `billing_service.py`, `profile.js`, `app_v2.js`, `jwt_utils.py`, `landing.html`, `plan_middleware.py` y tests.
- **test:** suite completa **292 passed, 102 skipped**.

---

## 2026-06-15 · Ola 4: Billing real con MercadoPago (MVP)

- **feat (billing):** cobro real con MercadoPago. Plan único **Premium** ($30.000 ARS/mes, 10 ops/mes, clientes ilimitados, 3 usuarios). Trial 14 días sin tarjeta. Top-up $10k por 10 ops.
- **feat (api):** endpoints `GET /api/billing/plans`, `POST /api/billing/checkout` (con selector de plan), `POST /api/billing/topup`, webhook actualizado para suscripción y top-up.
- **feat (limits):** middleware `require_active_billing` valida estado y límite de ops/mes al crear operaciones; límite de clientes por plan al crear cliente.
- **feat (ux):** selector de plan en registro, plan actual y uso del mes en perfil, botón de top-up, muro de pago para trial vencido.
- **test + qa:** +11 tests en `tests/test_billing_ola4.py`; suite completa **291 passed, 102 skipped**. Smoke local con checkout real de MercadoPago genera preference `live` correctamente. Smoke real de pago + webhook queda pendiente para deploy con dominio público.

---

## 2026-06-15 · Robust Country Lookup & Testing Fixes

- **fix (maria):** Vietnam (337), Thailand (335), Indonesia (316), and Malaysia (326) added to the official MARIA country code list.
- **feat (maria):** Implemented strict validation of recognized countries in both import and export endpoints to prevent silent fallback to default countries. Added warning checks for unrecognized origins and the `"XX"` placeholder in smart validations.
- **fix (test):** Resolved environment import-time freezing of FRONTEND_URL, fixed missing DB user records under mocked auth in conftest.py, and updated checkout/autoservicio test parameters. All 70 billing, checkout, and maria generation tests are now completely green.

---

---

## 2026-06-14 · Plan 04: Catálogo unificado — versión chica (Ola 3)

- **fix (persistencia):** al subir un Excel con `cliente_id`, el backend ahora detecta y **persiste** el mapeo de columnas en `Client.column_mapping`. Antes se usaba para leer pero nunca se guardaba, por eso "se borraba al cerrar sesión".
- **feat (api):** nuevos endpoints `/api/clientes/{id}/catalogo/columnas` (GET/PUT/DELETE) y `/api/clientes/{id}/catalogo/productos` (GET/PUT/DELETE/learn). Los viejos `/column_mapping` siguen funcionando como aliases.
- **feat (ux):** pestaña "Mapeo Excel" renombrada a **"Catálogo"** en el drawer del cliente. Muestra columnas reconocidas con badge (completo/parcial/sin catálogo) y la lista de productos aprendidos del cliente.
- **feat (autofill):** en review, los ítems que matchean con el catálogo del cliente ahora también precargan el **peso unitario** y muestran el icono 📚 en el chip.
- **feat (ui):** productos aprendidos editables inline (NCM, origen, peso) y botón "Olvidar" con confirmación.
- **fix (excel):** `extract_items_from_excel` ahora acepta `peso_unitario = 0`, permitiendo que el autofill de peso desde el catálogo del cliente funcione en la segunda operación.
- **test + qa:** +5 tests de Plan 04 (aprendizaje de columnas, uso de mapping persistido, CRUD de catálogo, lookup de cliente). Smoke headless Plan 04 pasa (cliente → upload → catálogo aprendido → segunda planilla → autofill de origen/peso → chip 📚 en NCM). Suite completa **250 passed, 102 skipped**; 24 errores preexistentes por `pytest-asyncio`.

---

## 2026-06-14 · Maintenance: dependencias vulnerables de producción

- **chore (deps):** actualizado `requirements.txt` con mínimos seguros de dependencias vulnerables:
  - `requests>=2.32.4` (GHSA-9hjg-9r4m-mvj7)
  - `pdfminer.six>=20251107` (GHSA-wf5f-4jwr-ppcp)
  - `starlette>=0.47.2` y `fastapi>=0.115.0` (CVE-2024-47874, CVE-2025-54121)
- **docs:** actualizado `docs/maintenance/vulnerabilidades_pendientes.md` con estado resuelto/pendiente.
- **test + qa:** `pip-audit` sobre `requirements.txt` ya no reporta vulnerabilidades de producción. Queda `pytest 8.4.2` (dev-only). Suite completa **250 passed, 102 skipped**; smokes `smoke_friccion.sh`, Plan 04 y Plan 04 e2e pasan.

---

## 2026-06-21 · Fix tour de bienvenida no aparece al registrar sin verificación de email

- **fix (frontend):** el tour de bienvenida no aparecía para usuarios nuevos cuando `EMAIL_VERIFICATION_REQUIRED=false` (default beta). Faltaba setear `sessionStorage.setItem('cdi_force_tour_after_signup', '1')` en el camino sin verificación. Agregado en `landing.html`.

---

## 2026-06-21 · Agrupar advertencias KIT Maria

- **fix (backend):** `validate_for_kit_maria` ahora agrupa advertencias por tipo en vez de una línea por item. 1 item → "Item #5: ...", 2-3 → "Items #2, #7: ...", 4+ → "NCM sin letra... en 200 ítems." Evita ruido visual con operaciones grandes. Los errores siguen por item (necesita saber cuál corregir).

## 2026-06-21 · Guía KIT Maria + validación previa

- **feat (frontend):** panel colapsable "¿Cómo cargar este archivo en KIT Maria?" en pantalla Ready, con 4 pasos y íconos SVG. Usa `<details>` nativo, sin JS extra.
- **feat (backend):** `validate_for_kit_maria()` en `maria_generator.py` — valida reglas específicas de KIT Maria que `validate_items_for_maria` no cubre: NCM mínimo 8 dígitos, descripción mínimo 10 chars, peso > 0, incoterm válido, moneda válida. Devuelve errores (bloquean) y advertencias (no bloquean).
- **feat (backend):** endpoint `/generate_maria` ahora llama `validate_for_kit_maria` antes de generar. Si hay errores → 400. Si hay solo advertencias → 200 con `warnings` en la respuesta.
- **feat (frontend):** `finalize.js` muestra advertencias de KIT Maria en un panel sutil debajo del preview del TXT. No bloquea la descarga.

## 2026-06-21 · Fix multi-tenant NCM + importar planilla maestra

- **fix (backend):** historial NCM pasa de shared a por-owner — cada despachante tiene su propio `ncm_historial_{username}.json`. Elimina leak de knowledge entre despachantes.
- **feat (backend):** endpoint `POST /api/ncm/import-historial` para importar planilla maestra "descripción → NCM" desde CSV/Excel.
- **feat (frontend):** botón "Importar planilla NCM" + modal en pantalla NCM para subir planilla maestra.

## 2026-06-21 · Fix paywall NCM y banner de trial

- **fix (frontend):** cálculo de días restantes de trial tenía un `* 60` extra → un trial de 14 días mostraba "1 día" y el banner desaparecía prematuramente.
- **fix (frontend):** modal de "plan vencido" (HTTP 402) pasaba `confirmText`/`icon` en vez de `acceptText`/`kind` → el botón decía "Aceptar" en vez de "Ir a pagar".
- **fix (frontend):** botón "Asistente" NCM ahora usa delegación de eventos en `tbody` en lugar de listeners individuales por fila, para evitar que el listener se pierda al regenerar la tabla.
- **fix (frontend):** HTML de `importClientesModal` tenía un `</div>` faltante, haciendo que el navegador anidara `tourWelcomeModal` y `ncmOverlay` dentro del modal oculto. Esto explicaba que el botón "Asistente" respondiera pero el overlay no se mostrara.

- **docs:** creado `docs/maintenance/vulnerabilidades_pendientes.md` con dependencias vulnerables detectadas (`requests`, `pdfminer.six`, `starlette`) y plan de ataque.
- **tag:** `v0.2-wave2` apunta al cierre de Plan 02 y Plan 03.

---

## 2026-06-14 · Plan 03: Alta de cliente desde operación + fix tabla NCM (Ola 2)

- **feat (clientes):** endpoint `GET /api/clientes/search?q=` para búsqueda server-side por nombre o CUIT parcial.
- **feat (ux):** picker de clientes ahora busca en el servidor con debounce (≥2 caracteres) en lugar de cargar toda la lista.
- **feat (review):** botón **+ Nuevo cliente** en el banner de importador desconocido; abre mini formulario inline para crear/editar cliente sin salir de la pantalla.
- **fix (ncm):** tabla de asignación de NCM ahora muestra **Valor unitario** y **Peso unitario** además de las columnas previas. El origen ya se mostraba cuando el PDF lo extrae correctamente.
- **test + qa:** +5 tests de `/api/clientes/search`; smoke Plan 03 pasa (alta desde review); smoke tabla NCM pasa con PDF real. Suite completa **245 passed, 102 skipped**.

---

## 2026-06-14 · Plan 02: Clientes drawer polish (Ola 2)

- **feat (clientes):** endpoint `GET /api/clientes/search?q=` para búsqueda server-side por nombre o CUIT parcial.
- **feat (ux):** picker de clientes ahora busca en el servidor con debounce (≥2 caracteres) en lugar de cargar toda la lista.
- **feat (review):** botón **+ Nuevo cliente** en el banner de importador desconocido; abre mini formulario inline para crear/editar cliente sin salir de la pantalla.
- **fix (ncm):** tabla de asignación de NCM ahora muestra **Valor unitario** y **Peso unitario** además de las columnas previas. El origen ya se mostraba cuando el PDF lo extrae correctamente.
- **test + qa:** +5 tests de `/api/clientes/search`; smoke Plan 03 pasa (alta desde review); smoke tabla NCM pasa con PDF real. Suite completa **245 passed, 102 skipped**.

- **feat (clientes):** 6 mejoras en el drawer de clientes:
  1. Lista ordenada por favorito + último movimiento DESC + nombre ASC.
  2. Badges `· N ops` en cada tarjeta (usando `total_operaciones` del backend).
  3. 6 KPIs completos en el detalle: operaciones, ítems, promedio ítems/op, origen frecuente, valor total, última fecha. El backend de métricas ahora calcula `origen_frecuente` desde `OperationItem.origen`.
  4. Botón **Exportar CSV** conectado al endpoint backend (`/api/clientes/{id}/export.csv`).
  5. Lista de operaciones muestra las primeras 5 y botón **Ver todas / Mostrar menos**.
  6. Filtros `all/favs/recent` (preexistentes) verificados funcionando.
- **fix (clientes):** corregido error `exportClientCsv is not defined` que rompía la apertura del drawer al hacer click en Exportar CSV.
- **test + qa:** endpoint CSV testeado; smoke headless de Plan 02 pasa (drawer, KPIs, export, expand de operaciones). Suite completa **240 passed, 102 skipped**; 24 errores preexistentes por compatibilidad de `pytest-asyncio` en tests de seguridad/SEO.
- **chore:** inicialización de tablas en tests movida a `pytest_sessionstart` para no interferir con el loop de pytest-asyncio.

---

## 2026-06-14 · Novedades ARCA + cierre Ola 1

- **feat (datos vivos):** nuevo widget **Novedades ARCA** en la pantalla de Upload. Consume la fuente oficial de ARCA/AFIP (`https://servicioscf.afip.gob.ar/publico/sitio/contenido/novedad/listadoxml.aspx`), muestra las últimas 5 novedades con título/imagen/link y es colapsable. Endpoint nuevo: `GET /api/arca/novedades` (público, caché 15 min).
- **feat (ux flujo principal):** se verificó y completó el Plan 01 — máscara de fechas `DD/MM/AAAA` en review, preview VUCE al tipear NCM en el spotlight (descripción oficial + alícuotas), y botón Clientes en topbar.
- **test + qa:** +4 tests del backend ARCA; suite completa **260 passed, 102 skipped**. Smoke headless con Playwright verificó login, render de novedades reales y colapso del widget.
- **chore:** ajustado smoke test para soportar startup del server de 4s.

---

## 2026-06-14 · Fix race condition en pantalla Upload

- **fix (ui):** se eliminó el error `Cannot read properties of undefined (reading 'classList')` que aparecía al entrar a la pantalla de subida (`upload.js`). El `onEnter` ahora garantiza que el DOM esté inicializado antes de llamar a `setBusy`, y `setBusy` tiene guard ante referencias aún no cargadas.
- **verificado:** sintaxis JS OK, suite completa **256 passed, 102 skipped**.

---

## 2026-06-14 · Cockpit de operaciones + seguridad S1/S3 (Ola 1)

- **feat (cockpit):** nuevo tablero `Operaciones` en el dashboard v2 — lista todas las operaciones del despachante con estado editable (borrador → oficializada → canal → liberada), canal aduanero (verde/naranja/rojo), cliente, ítems, valor y fecha. Filtros por estado con contadores. Reemplaza el Excel de seguimiento. Endpoints `GET /api/operations` y `PATCH /api/operations/{id}/estado` (aislados por owner). Nuevas columnas `operations.estado` y `operations.canal` (migración idempotente).
- **fix (seguridad S1):** eliminados endpoints legacy de pagos sin auth (`/api/payments/create-preference` que aceptaba username del body → checkout cruzado; y los `/api/payments/bitcoin/*` demo). El checkout real sigue siendo `/api/billing/checkout` (autenticado).
- **fix (seguridad S3):** los 5 endpoints `/api/dev/*` (stats, kpis, run-migrations, etc.) ahora exigen rol admin vía nueva dependencia `require_admin` (env `ADMIN_USERNAMES` o rol en DB). El user `demo` es admin en dev.
- **verificado:** el dólar BNA/Blue del topbar ya funcionaba (módulo "datos vivos" OK).
- **test:** +27 tests nuevos (`test_seguridad_s1_s3.py`, `test_cockpit.py` con aislamiento multi-tenant). Suite: **256 passed, ~12s**.

---

## 2026-06-10 · MercadoPago real: vuelta del checkout cerrada (Bloque 5, parte 1)

- **feat (billing):** la preference de `/api/billing/checkout` ahora incluye `back_urls` (vuelve a `/v2?billing=success|failure|pending`), y con `FRONTEND_URL` https agrega `auto_return=approved` + `notification_url` al webhook. Antes el user pagaba y quedaba varado en MP.
- **feat (UI):** al volver del checkout, el dashboard muestra toast según resultado y refresca el estado de billing solo (el webhook activa el plan async). Telemetría: `billing_return_*`.
- **test:** 4 tests nuevos (`tests/test_billing_checkout.py`, MP mockeado). Suite: **229 passed, ~12s**.
- **pendiente (humano):** para probar sandbox real hacen falta credenciales `TEST-` de MP (`MP_ACCESS_TOKEN`) y en prod setear `MP_ACCESS_TOKEN`, `MP_WEBHOOK_SECRET` y `FRONTEND_URL` en Railway.

---

## 2026-06-10 · CSRF mínimo (Bloque 4) en modo report-only

- **feat (seguridad):** protección CSRF double-submit cookie. Al loguear/registrar se setea cookie `csrf_token`; el front v2 (helper `api()`) la reenvía como header `X-CSRF-Token` en POST/PUT/DELETE; un middleware valida que coincidan. Exentos: login/register/logout/verify-email, estáticos y webhook MP (validado por firma).
- **modo seguro:** arranca en **report-only** (loguea warning, no bloquea). Para bloquear de verdad: setear `CSRF_ENFORCE=true` en Railway después de revisar logs un par de días. Sesiones viejas reciben la cookie al pegar a `/auth/current_user`.
- **fix (infra tests):** `MetricsMiddleware` ya no escribe logs a la DB bajo pytest (causaba `database is locked` flaky en `test_security`). Suite: **225 passed, 0 errores, ~27s** (+7 tests nuevos en `tests/test_csrf.py`).

---

## 2026-06-09 · Suite de tests 100% verde (fix de los 7 rojos por auth)

- **test (infra):** arreglados los 7 tests rojos preexistentes que fallaban con `401 No autenticado` (`test_regression_phase0` backup/restore, `test_main_process_operation`, `test_main_upload`). No tocaban sesión y los endpoints ahora exigen auth.
- **fix (forma correcta):** en vez de debilitar los tests, se autentican vía override de la dependencia `get_current_user` (nuevo fixture `auth_override` en `tests/conftest.py`). No escribe en la DB → sin locks ni flakiness por orden de tests. Se descartó registrar usuarios reales porque generaba `database is locked` bajo SQLite/async.
- **resultado:** suite completa **218 passed, 102 skipped, 0 fallas, ~44s** (antes 211 passed + 7 failed, ~3min).

---

## 2026-06-08 · Red de tests confiable + fix de seguridad (secretos filtrados)

- **fix (infra tests):** la suite completa se colgaba por 2 scripts manuales de Gemini (`test_gemini_vision.py`, `test_simple_extraction.py`) que ejecutaban **llamadas reales a la API en el import** (durante la colección de pytest). Borrados esos + `test_gemini_extraction.py` (script manual, no test). Ahora la suite corre entera: **211 passed, 102 skipped, ~3min**, antes colgaba indefinidamente.
- **fix (red de seguridad):** agregado `pytest-timeout==2.4.0` + `--timeout=120 --timeout-method=thread` en `pytest.ini`. Mata cualquier test colgado en el futuro en vez de trabar todo.
- **🔴 SEGURIDAD (acción requerida del humano):** había **secretos de producción reales commiteados**: `GEMINI_API_KEY` (en los scripts borrados + `docs/deployment/RAILWAY_SETUP.md`) y `JWT_SECRET_KEY` (en RAILWAY_SETUP.md). Reemplazados por placeholders en el doc. **Quedan en el historial de git → hay que ROTAR ambas claves**: la API key de Gemini en Google Cloud y el JWT_SECRET_KEY en Railway (rotar JWT desloguea a todos los users).
- **pendiente (triaje):** al correr la suite completa por primera vez aparecieron 7 tests rojos preexistentes (no relacionados al generador MARIA): `test_regression_phase0` backup/restore (2), `test_main_process_operation` (2), `test_main_upload` (3). A revisar próxima sesión.

---

## 2026-06-07 · Sprint 25 días — Día 9 (validación contra golden file real)

- **validación (clave):** conseguimos un TXT MARIA **real y validado por el despachante** (op 001790125, importador VOWYNNS). Comparado campo por campo contra nuestro generador: **coincide en todo lo estructural** y confirma que los 7 fixes de T13 fueron correctos. Corrección importante: lo que antes llamamos "datos de otro cliente / sample falso" (fecha `13/07/2016`, domicilio `DR. SALVADOR MAZZA 1996`, procedencia `222`) eran **datos reales de VOWYNNS** usados como default global — el fix de T13 (no usarlos para todos) sigue siendo correcto. Y `PSAD`/`PSAD06`/`GANANCIASOP3`/`COMERC`/`IVAAD1` resultaron ser **constantes legítimas de MARIA, no bugs**.
- **test (CORE):** nuevo **test golden de regresión** (`test_golden_*`, 3 tests) que reproduce la operación real **anonimizada** (`tests/fixtures/maria_golden_anon.TXT`): se falsean CUITs/nombres/domicilio/`[SBT]`, se mantienen NCM/pesos/montos reales para validar cálculos. Incluye guard anti-leak que falla si algún dato real de VOWYNNS aparece en el fixture. Total suite generador: 33 tests.
- **fix:** `GTOS-POS-FOB` ahora usa formato `:.2f` (antes `str(flete+seguro)` podía dar `3271.6600000000003`).
- **refactor:** el sufijo `[SBT] CSBTSVL` es ahora parámetro `sbt_sufijo_valor` (default = legacy). **Leak conocido pendiente:** el default contiene `AA(VOWYNNS)` → para clientes que no sean VOWYNNS sale dato ajeno; la regla real por importador (qué son `AB(...)` y `CA00`) requiere confirmación del despachante.
- **pendiente despachante:** (1) qué significan `AB(...)` y `CA00` en `[SBT]` y si `AA()` es siempre el importador; (2) si `DDDTVENEMB` es obligatorio para el Kit SIM.

---

## 2026-06-04 · Sprint 25 días — Día 9 (T13 auditoría generador TXT)

- **fix (CRÍTICO, datos aduaneros):** el generador de EXPORTACIÓN (`maria_generator_export.py`) tenía el MISMO bug de país que ya arreglamos en importación (match exacto OR prefijo en una sola pasada → `China` caía en `Chile`). Ahora hace 2 pasadas, exacto primero.
- **fix (matching laxo):** el fallback por prefijo de 2 letras adivinaba mal países desconocidos (`Colombia`→`Corea` 220). Endurecido a prefijo de >=3 chars en ambos generadores.
- **fix (CRÍTICO, privacidad/datos):** si el cliente no tenía cargado domicilio o fecha de inicio de actividad, el TXT salía con los datos de OTRO cliente del sample (`DR. SALVADOR MAZZA 1996`, `13/07/2016`). Ahora si no hay dato real, el bloque `[CPL]` simplemente no se emite y el despachante lo completa en el Kit SIM. +2 tests de regresión.
- **fix (CRÍTICO, datos aduaneros):** la tabla de países tenía casi TODOS los códigos mal. Se reemplazó por la tabla **oficial AFIP "Códigos María"**. Ejemplos del error: `China`=218 (era México), `Alemania`=212 (era EEUU), `España`=210 (era Ecuador), `Japón`=217 (era Jamaica), `México`=214 (era Guyana). **El default "China" valía 218 = México**, así que toda operación sin país explícito declaraba México como origen. Ahora China=310, default=310. Tabla unificada: export importa la misma de import (single source of truth). Tests actualizados a los valores oficiales.
- **fix (datos aduaneros):** procedencia del item (`CARTPAYPRC`) ya no es un hardcode `222` (que con la tabla oficial es Perú, no EEUU como creía el sample). Ahora usa `pais_procedencia`/`procedencia` del item y, si no viene, asume el mismo país que el origen (caso más común). +2 tests.
- **fix (datos aduaneros):** unidad de medida (`CARTUNTDCL`/`CARTUNTEST`) ya no es `07` (UNIDAD) fijo para todo. Nuevo helper `get_unidad_codigo()` con la tabla oficial de unidades MARIA mapea kg=01, litro=05, par=08, etc. desde el campo `unidad`/`unidad_medida`/`um` del item; fallback a 07 si no viene. Aplica a import y export (en export el comentario decía "kilogramos" pero mandaba 07=UNIDAD). +2 tests.
- **fix (datos aduaneros):** fecha de embarque (`DDDTVENEMB`) ya no se inventa como hoy+365. Si no hay fecha real, la línea no se emite (el TXT es clave=valor, omitir es seguro) y el despachante la completa en el Kit SIM. +2 tests. **Riesgo a confirmar con despachante:** si ese campo fuera obligatorio para importar el TXT al Kit SIM, habría que volver a emitirlo (con placeholder visible) en vez de omitirlo.
- **T13 cerrado** salvo `[SBT]`: los sufijos del sample (`CSBTSVL=...`) quedan pendientes; requieren entender qué representan (idealmente con el despachante) antes de tocar un campo de valor aduanero.

---

## 2026-06-02 · Sprint 25 días — Día 8 (T12 tests core TXT + FIX bug país)

- **fix (CRÍTICO, datos aduaneros):** `get_pais_codigo()` devolvía el código de país EQUIVOCADO para nombres completos que comparten las 2 primeras letras. `China`→208 (Chile) y `España`→212 (Estados Unidos). El match por prefijo pegaba en el país equivocado antes del match exacto. Ahora hace 2 pasadas (exacto primero). **Esto metía el código INDEC errado en el TXT que el despachante carga en el Kit SIM.**
- **test (CORE):** `tests/test_generar_maria_txt.py` con 22 tests del corazón del producto: 18 unit de `generate_maria_txt` (secciones [DDT]/[ART]/[CPL]/[DVD]/[SBT], CRLF, total FOB, formato NCM, proporcional flete/seguro, defaults aduana, códigos país) + 4 E2E del endpoint `/generate_maria` (auth, validación, cuit del perfil).
- **fix (test infra):** `conftest.py` usa `StaticPool` (conexión SQLite única compartida) para eliminar `database is locked`. Bajó el tiempo de la suite de billing de ~35s a ~3s.
- **NO incluye:** extracción con Gemini Vision (requiere red + tokens), queda en smoke manual.

---

## 2026-06-02 · Sprint 25 días — Día 7 (T11 SEO landing)

- **feat (SEO):** landing completa para indexación de Google. Fix `<title>` (ahora menciona Aduana + MARIA + Kit SIM), agregada `<meta name="keywords">` con términos competitivos (software aduana, despachante, argentina), y **Schema.org JSON-LD** (`SoftwareApplication` con precio $15.000 ARS y provider Organization).
- **feat (SEO):** `<meta name="robots" content="noindex, nofollow">` en `dashboard_v2.html` (área privada no debe indexarse).
- **ya existían:** `/static/robots.txt` (bloquea /dashboard, /api/, /admin/) y `/static/sitemap.xml`. Verificados por tests.
- **test:** los 13 tests de `test_seo.py` (preexistentes, estaban en rojo) ahora pasan en verde.
- **fix (test infra):** `conftest.py` usa `PRAGMA busy_timeout` en vez de `journal_mode=WAL` (WAL requiere lock exclusivo y rompía al correr suites juntas).

---

## 2026-06-01 · Sprint 25 días — Día 6 (T10 tests E2E billing autoservicio)

- **test (CRÍTICO):** `tests/test_billing_autoservicio.py` con 13 tests E2E del flujo de billing autoservicio (registro → trial → cancel → reactivate → checkout) + cambio de password. Red de seguridad antes de cobrar real.
- **Cubre:** `change-password` (OK + 401 actual mala + 400 short + 400 same), `cancel` (OK + 409 desde none/canceled), `reactivate` (vigente → active sin cobrar, vencido → past_due+needs_checkout), auth obligatoria en los 3.
- **fix (test infra):** `conftest.py` usa archivo SQLite temporal en lugar de `:memory:` (multi-conexión async no comparte estado en memoria) y aplica PRAGMA `journal_mode=WAL` + `busy_timeout=30s` para evitar `database is locked` durante bcrypt en threadpool.
- **NO incluye:** integración real con MercadoPago sandbox (eso queda en smoke manual con TEST_ACCESS_TOKEN).

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
