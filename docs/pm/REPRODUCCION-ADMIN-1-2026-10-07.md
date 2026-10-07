# Reproducción de ADMIN-1 — 2026-10-07

**Veredicto: aceptada sobre `ac25dbc`** (base `cb8f509`). Cierra S2 de
`AUDITORIA-2026-10-06.md`.

## Lo que corrió la PM

Worktree limpio en `ac25dbc`, Python 3.12, `GEMINI_API_KEY=test-key`,
`ENVIRONMENT=test`, terceros simulados.

| Qué | Salida |
|---|---|
| Rojo antes: la prueba nueva con el producto de `cb8f509` | `AssertionError: [('GET', '/api/admin/cohort-retention'), ('GET', '/api/admin/errors/insights'), …` (rutas de admin abiertas a un usuario común) |
| Focal: `tests/test_admin_solo_admin.py` | `14 passed, 7 warnings in 2.24s` |
| `python -m compileall -q proyecto_maria` | ok |
| Suite completa | `694 passed, 102 skipped, 23 warnings in 65.67s` |

Coincide con el informe (694/102/0). El 2026-10-06 la PM ya había visto el
rojo en vivo: usuario común, `clear-old` → 200.

## Subagente de la PM (Opus alto)

**El control se sostiene.** En vivo, con un usuario común recién registrado:
GET a todas las rutas de admin y de dev → 403; POST a `clear-old`,
`cache/refresh` y `run-migrations` → 403 con y sin token CSRF, 401 sin sesión.
Variantes de ruta (barra final, `%2F`, `//`, mayúsculas, `/./`, `/../`): 307
que termina en 403, o 404. El admin entra igual que antes. Ninguna pantalla de
usuario común llama a esas rutas.

**Puntos ciegos de la prueba** (reproducidos en copias del código; hoy no hay
ninguna ruta real así):

| # | Qué no ve la prueba de recorrido | Qué se hace |
|---|---|---|
| 1 | Una app montada aparte bajo `/api/admin/…` (`app.mount`) | se suma a ADMIN-2 |
| 2 | Una ruta cruda de Starlette con `include_in_schema=False` bajo `/api/dev/` | se suma a ADMIN-2 |
| 3 | Una función global fuera de los prefijos y sin `tags=["admin"]` | ya lo dijo la Dev: no hay forma automática honesta; queda escrito junto a `require_admin` |

Leído, fuera de la pieza: la telemetría sin sesión (`/api/ui/event`,
`/api/session/state`) ensucia los KPI del admin. Es S5: ABUSO-1.

## No corrido por la PM

- El script de sabotajes de la Dev (`scripts/testing/sabotajes/admin1.sh`):
  crea worktrees. El subagente hizo su propio sabotaje (router con
  `get_current_user`) y la prueba se puso roja nombrando las rutas.

Contexto de la Dev 1 al entregar: ~25 % (250 mil tokens).
