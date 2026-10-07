# Reproducción de ADMIN-2 — 2026-10-07

**Veredicto: aceptada sobre `f9f8393`** (base: la rama de PM en `e7856bd`).

## Lo que corrió la PM

Worktree limpio en `f9f8393`, Python 3.12, `GEMINI_API_KEY=test-key`,
`ENVIRONMENT=test`, terceros simulados y el dólar contra un puerto cerrado.

| Qué | Salida |
|---|---|
| Rojo antes: las pruebas nuevas con el producto de `e7856bd` | `3 failed, 24 passed`: el usuario común ve `base_url` de los conectores; sin sesión y con el secreto, `simulate-webhook` → `200 … "billing_status":"active"`; `cohort-retention` → `403` al admin por `ADMIN_USERNAMES` |
| Focal: `test_admin2.py` y `test_admin_solo_admin.py` | `27 passed, 7 warnings in 2.44s` |
| `python -m compileall -q proyecto_maria` | ok |
| `simulate-webhook` en el producto, pantallas y scripts | no queda (sólo docs, CHANGELOG y las pruebas que comprueban que no existe) |
| Suite completa | `716 passed, 102 skipped, 24 warnings in 67.63s` |

Coincide con el informe (716/102/0). Integrada sin conflictos: el producto y
las pruebas de la rama de PM quedan idénticos a `f9f8393`.

## Subagente de la PM (Sonnet alto)

**Los puntos 1 a 3 se sostienen.** Conectores con usuario sin `roles`, con
`roles=None`, `["Admin"]` y admin por variable con espacios: el común ve sólo
`mode`; el admin, el detalle de antes. Nada dependía de `simulate-webhook`.
`cohort-retention` sólo la monta el router de admin, con `require_admin`.

**Dos puntos ciegos más de la prueba de recorrido** (reproducidos con
sabotajes en copias del código; hoy el producto no tiene WebSockets ni rutas
así):

| # | Qué no ve la prueba | Qué se hace |
|---|---|---|
| 1 | Un WebSocket bajo `/api/admin/` sin control | AISLAMIENTO-2 (Fase 3) |
| 2 | Una ruta cruda en `/api/admin` o `/dev` exactos, sin barra final | AISLAMIENTO-2 (Fase 3) |

Leído, latente: `roles` guardado como texto en vez de lista haría que
«administrador» cuente como admin (igual en `require_admin`); hoy sólo se
escribe como lista. También a AISLAMIENTO-2.

## No corrido por la PM

- Los sabotajes de la Dev (`scripts/testing/sabotajes/admin2.sh` y
  `admin1.sh`): crean worktrees. El subagente hizo los suyos.
- La pantalla en el navegador: el chip «Sistema/Demo» no se dibuja en
  ninguna plantilla (D7 de la Dev).

Contexto de la Dev 1 al entregar: ~35 % (347 mil tokens); espera su
`/compact`.
