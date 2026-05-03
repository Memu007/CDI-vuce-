# AGENTS.md — instrucciones para asistentes de IA

> **Esta es la fuente de verdad para CUALQUIER asistente** (Cursor, Antigravity, Cascade/Windsurf, Claude Code, Codex, GitHub Copilot, Aider, etc.) que tome este repo. Lo lee este archivo primero, después `HANDOFF.md`.
>
> Cada IDE tiene su propio archivo wrapper que apunta acá:
>
> - Cursor → `.cursor/rules/*.mdc`
> - Cascade/Windsurf → `.windsurf/rules/leeme-primero.md`
> - Claude Code → `CLAUDE.md`
> - GitHub Copilot → `.github/copilot-instructions.md`
> - Aider y otros → `CONVENTIONS.md`
>
> **Si modificás reglas, modificalas acá o en `.cursor/rules/`. Los wrappers son cortos y no duplican contenido.**

## 1. Antes de tocar nada

Leer en este orden:

1. `HANDOFF.md` — estado actual, stack, qué está vivo, qué es frágil.
2. `CHANGELOG.md` — últimas 2–3 entradas para saber qué cambió recientemente.
3. `.cursor/rules/` (si está) — preferencias del usuario para esta tarea.

Si el pedido del humano contradice algo de `HANDOFF.md`, **avisar antes de implementar** y pedir confirmación.

## 2. Cómo hablarle al humano (importante)

El usuario es **dueño del producto, no programador**. Tiene reglas explícitas en `.cursor/rules/explicar-sin-asumir-tecnico.mdc` y `.cursor/rules/utilidad-ahorro-tokens.mdc`. Resumen:

- Castellano llano primero. Términos técnicos solo si los aclarás la primera vez.
- Conclusión arriba, detalle abajo, sin relleno.
- Antes de un plan grande, ofrecer la versión chica.
- Si hay decisión con trade-off, presentarlo en negocio, no en complejidad O(n).
- Sin yes-man: si el plan tiene un problema, decirlo en castellano y proponer alternativa.

## 2.bis. Equipo virtual de 6 roles

Para tareas no-triviales, asumir un equipo y consultar SOLO los roles relevantes + PM. Indicar al inicio de la respuesta entre corchetes los roles consultados. Detalle completo en `.cursor/rules/equipo-virtual.mdc`.

Roles disponibles:

- **PM** (siempre): prioriza, traduce a negocio, corta over-engineering.
- **Tech Lead**: arquitectura y decisiones grandes.
- **Backend**: FastAPI, SQLAlchemy, AFIP, VUCE, Python.
- **Frontend**: HTML/CSS/JS vanilla en `proyecto_maria/static/v2`.
- **QA**: smoke tests, edge cases, riesgo a prod.
- **Security/DevOps**: secrets, validación, CUIT, Railway, deploy.

Para ediciones triviales (typo, color, texto de 1-2 líneas) NO usar el equipo, responder directo.

## 3. Qué tenés permitido

- Editar código en cualquier carpeta del repo **excepto** las marcadas como "no tocar" abajo.
- Crear nuevos endpoints / pantallas / migraciones siguiendo el patrón existente.
- Agregar tests en `tests/`.
- Actualizar `HANDOFF.md`, `CHANGELOG.md`, `docs/`.

## 4. Qué NO tenés permitido (sin confirmación explícita del humano)

- **Forzar push** (`git push --force`) a `main`.
- Tocar `.env`, `.env.afip` o cualquier secret. Esos archivos no están en git por algo.
- Borrar archivos en `docs/archive/` — son referencias históricas para auditoría.
- Cambiar `.gitignore` para incluir secrets, bases de datos o PDFs de clientes.
- Hacer commits sin mensaje claro o sin prefijo (`feat:` / `fix:` / `chore:` / `docs:` / `refactor:` / `test:`).
- Borrar tags. Si hay que sacar uno, avisar.
- Mergear branches sin que el humano lo apruebe.

## 5. Carpetas que NO se tocan (read-only para IAs)

- `viejo/` — material legacy, no se sube a git, no se usa como fuente de verdad.
- `venv/` — entorno Python local, no commitear.
- `docs/archive/` — handoffs y docs viejos. Solo lectura.
- `.git/` — obvio.

## 6. Cómo dejar el repo después de tu sesión

Antes de declararte "listo":

1. ¿Tocaste código? Hacé commit con prefijo.
2. ¿Cambiaste comportamiento del producto? Actualizá `HANDOFF.md` sección 6 ("Estado actual").
3. ¿Agregaste / sacaste un endpoint o columna de DB? Actualizá `HANDOFF.md` sección 5 (Estructura) o 6 (Estado).
4. **Siempre**: agregar 1–3 líneas en `CHANGELOG.md` con la fecha.
5. Si hubo un hito (cierre de feature, fin de Wave, fix grande): proponer un tag al humano (no lo crees vos sin avisar).
6. `git push` (sin force).

## 7. Si la sesión queda incompleta

Documentá en `HANDOFF.md` sección "## TODO siguiente sesión" (creala si no existe), o en `CHANGELOG.md` debajo de la entrada parcial, qué quedó pendiente. Sé explícito: archivo, función, qué falta, por qué.

## 8. Smoke test rápido

Si tocaste backend, antes de declarar "listo":

```bash
PYTHONPATH=. uvicorn proyecto_maria.main:app --host 127.0.0.1 --port 8000 &
sleep 4
BASE_URL=http://127.0.0.1:8000 ./scripts/testing/smoke_friccion.sh
kill %1
```

Si falla, no declares la tarea cerrada.

## 9. Cuando hay duda

Preguntá al humano. Mejor 1 pregunta corta ahora que un cambio que hay que rehacer.
