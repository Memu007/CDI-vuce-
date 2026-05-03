# CONVENTIONS.md — para Aider y otros asistentes

Este repo tiene UNA fuente de verdad para las reglas. Cualquier asistente (Aider, Cursor, Antigravity, Cascade, Claude Code, Codex, Copilot) leé:

1. **`AGENTS.md`** (raíz) — instrucciones generales: cómo hablarle al humano, equipo virtual, qué tocás y qué no.
2. **`HANDOFF.md`** — estado actual, stack, qué funciona.
3. **`CHANGELOG.md`** — últimas 2-3 entradas.
4. **`.cursor/rules/`** — rules detalladas (equipo virtual, persistencia, comunicación, ahorro de tokens).

## Reglas mínimas

- **Idioma**: castellano llano. Conclusión arriba, detalle abajo. Sin yes-man.
- **Equipo virtual**: para tareas no-triviales, simular 6 roles (PM, Tech Lead, Backend, Frontend, QA, Security/DevOps) y mostrar al inicio entre corchetes los consultados.
- **Persistencia**: después de cada cambio significativo, actualizar `HANDOFF.md` + `CHANGELOG.md`, commit y push. Mensajes con prefijo (`feat:` / `fix:` / `chore:` / `docs:` / `refactor:` / `test:`).
- **Nunca**: `git push --force`, tocar `.env*` o `secrets`, borrar `docs/archive/`.
