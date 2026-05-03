# CLAUDE.md — instrucciones para Claude Code

Este repo tiene UNA fuente de verdad para las reglas que aplican a CUALQUIER asistente (Cursor, Antigravity, Cascade, Claude Code, Codex, Copilot, Aider).

## Leé esto antes de tocar nada

1. **`AGENTS.md`** (raíz del repo) — instrucciones generales: cómo hablarle al humano, equipo virtual de 6 roles, qué tenés permitido y qué no.
2. **`HANDOFF.md`** — estado actual, stack, qué funciona.
3. **`CHANGELOG.md`** — últimas 2-3 entradas.
4. **`.cursor/rules/`** — rules detalladas:
   - `explicar-sin-asumir-tecnico.mdc` — castellano llano.
   - `utilidad-ahorro-tokens.mdc` — respuestas concisas.
   - `equipo-virtual.mdc` — 6 roles a consultar (mostrar entre corchetes al inicio).
   - `persistencia-github-al-dia.mdc` — `HANDOFF` + `CHANGELOG` + commit + push después de cada cambio.

## Lo crítico

- El usuario es **dueño del producto, no programador**. Castellano llano, conclusión arriba, sin yes-man.
- Para tareas no-triviales, simular **equipo virtual** (PM, Tech Lead, Backend, Frontend, QA, Security/DevOps) y mostrar roles consultados.
- Después de cada cambio significativo: actualizar `HANDOFF.md` §6 + `CHANGELOG.md`, `git commit` y `git push origin main`.
- **NO TOCAR**: `.env*`, secrets, `docs/archive/`. **NO HACER**: `git push --force`.

## Smoke test si tocás backend

```bash
PYTHONPATH=. uvicorn proyecto_maria.main:app --host 127.0.0.1 --port 8000 &
sleep 4
BASE_URL=http://127.0.0.1:8000 ./scripts/testing/smoke_friccion.sh
kill %1
```
