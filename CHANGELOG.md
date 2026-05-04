# CHANGELOG

Historial de cambios visibles para el dueño del producto. Cualquier AI o humano que cierre una sesión de trabajo agrega una entrada acá.

Formato corto: fecha, 1–3 líneas, prefijo.

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
