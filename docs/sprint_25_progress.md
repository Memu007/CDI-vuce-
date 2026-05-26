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
  - 3 pasos: subir PDF / revisar items / generar TXT y cargar al Kit María SIM 7.0 (ARCA / Malvina).
  - Aparece solo en el primer login. Persiste en `localStorage.cdi_welcome_seen`.
  - Tracking: `welcome_card_shown` y `welcome_card_dismissed`.
  - CSS: `.welcome-card` en `app_v2.css` (estilo Apple minimal).
  - JS: `setupWelcomeCard()` en `app_v2.js`, llamado en bootstrap.
- **T4** copy de `landing.html` actualizado para mencionar **Kit María SIM 7.0 (ARCA / Malvina)** explícitamente:
  - Hero: "...te devuelvo el TXT listo para pegar en tu **Kit María SIM 7.0** (ARCA · Malvina)".
  - Step final: "TXT al Kit SIM" (antes "MARIA sale").
  - Meta description y OG description actualizadas igual.
  - `landing_legacy.html` no tocado (no se sirve, solo referencia).
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
