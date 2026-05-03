# GitHub Copilot — instrucciones del proyecto CDI/VUCE

Este repo tiene UNA fuente de verdad para las reglas que aplican a CUALQUIER asistente (Cursor, Antigravity, Cascade, Claude Code, Codex, Copilot, Aider).

## Antes de sugerir código

Leer:

1. **`AGENTS.md`** (raíz) — instrucciones generales para asistentes IA.
2. **`HANDOFF.md`** — estado actual, stack, qué funciona.
3. **`.cursor/rules/`** — rules detalladas (equipo virtual, persistencia, comunicación).

## Reglas críticas

- El usuario es **dueño del producto, no programador**. Castellano llano, sin jerga innecesaria.
- Para tareas no-triviales, asumir un **equipo virtual de 6 roles** (PM, Tech Lead, Backend, Frontend, QA, Security/DevOps) y mostrar al inicio entre corchetes los roles consultados, ej: `[PM + Backend + QA]`.
- Después de cada cambio significativo: `HANDOFF.md` §6 + `CHANGELOG.md` + commit + push (sin `--force`).

## Stack del proyecto

- Backend: FastAPI + SQLAlchemy + PostgreSQL (Railway) / SQLite (local).
- Frontend v2: HTML + CSS + JS vanilla en `proyecto_maria/static/v2/`.
- Pantallas: `screens/*.js` con patrón módulo + `CDI.registerScreen()`.
- Auth: JWT por cookie.
- Telemetría: `CDI.track()` → `/api/ui/event` → tabla `telemetry_events`.

## NO tocar

- `.env`, `.env.afip` (gitignored, contienen secrets).
- `docs/archive/` (referencias históricas read-only).
- `viejo/`, `venv/`.
