---
trigger: always_on
---

# Reglas del proyecto CDI / VUCE

Este repo tiene UNA fuente de verdad para las reglas que aplican a CUALQUIER asistente (Cursor, Antigravity, Cascade, Claude Code, Codex, Copilot, Aider).

## Leé en este orden

1. **`AGENTS.md`** (raíz del repo) — instrucciones generales: cómo hablarle al humano, equipo virtual de 6 roles, qué tenés permitido y qué no, cómo dejar el repo después de tu sesión.
2. **`HANDOFF.md`** — estado actual del producto, stack, qué funciona, qué es frágil.
3. **`CHANGELOG.md`** — últimas 2-3 entradas para saber qué cambió.
4. **`.cursor/rules/`** — rules detalladas:
   - `explicar-sin-asumir-tecnico.mdc` — castellano llano, sin jerga.
   - `utilidad-ahorro-tokens.mdc` — respuestas concisas.
   - `equipo-virtual.mdc` — 6 roles (PM, Tech Lead, Backend, Frontend, QA, Security/DevOps). Indicar al inicio de cada respuesta no-trivial los roles consultados entre corchetes.
   - `persistencia-github-al-dia.mdc` — después de cada cambio: `HANDOFF` + `CHANGELOG` + commit + push.

## Lo crítico en 5 líneas

- Castellano llano, conclusión arriba, sin yes-man.
- Antes de plan grande, ofrecer versión chica.
- Para tareas no-triviales, simular equipo virtual y mostrar roles consultados.
- Después de cada cambio: actualizar `HANDOFF.md` §6 + `CHANGELOG.md`, commit y push.
- Nunca tocar `.env*`, ni hacer `git push --force`, ni borrar `docs/archive/`.
