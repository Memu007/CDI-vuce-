# CHANGELOG

Historial de cambios visibles para el dueño del producto. Cualquier AI o humano que cierre una sesión de trabajo agrega una entrada acá.

Formato corto: fecha, 1–3 líneas, prefijo.

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
