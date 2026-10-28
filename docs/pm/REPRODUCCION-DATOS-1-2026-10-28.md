# Reproducción de DATOS-1 (2026-10-28)

Entrega de la Dev MARIA en `c996ad4` (base `d01f95c`). Diff de producto:
`main.py` (`delete_cliente`, `/health`, manejadores de 500), `clientes.js`,
`finalize.js`, `CHANGELOG.md`.

## Lo que corrió la Dev

Suite sobre `c996ad4`: `3836 passed, 336 skipped, 2 xfailed, 0 failed`.
`datos1.sh`: 12 sabotajes en rojo. `datos1_postgres.py` en Postgres 16:
`fallas: 3` sobre `d01f95c`, `fallas: 0` después.

## Adversario (Sonnet alto, contexto nuevo, Postgres 16 propio)

Sin borrado que alcance a otro dueño, sin fuga del error de la base, y el
rollback deja todo como estaba. Lo que encontró:

1. **Reproducido por la PM** (worktree en `c996ad4`, SQLite): con
   `PublicQuoteModel.operation_id.in_(op_ids[:1])`, `tests/test_datos1.py`
   da `9 passed`, igual que el código real. El revisor, con un cliente de dos
   operaciones compartidas: el mutante da `DELETE -> 500` y los links siguen;
   el código real, `200` y links `[404, 404]`.
2. Mover el borrado de presupuestos después del de operaciones deja
   `test_datos1.py` en `9 passed` (SQLite no hace cumplir la clave
   foránea); sólo lo frena `datos1_postgres.py` (`fallas: 3`).
3. Tres casos en que el cliente no se borra bien, ninguno de la pieza: una
   fila de `api_logs` con `operation_id` (hoy nada la escribe), más de
   32 767 operaciones, y una operación con `owner_username` NULL, que queda
   con su presupuesto accesible.
4. Hipótesis por lectura: `system_backups` (`client_migration`) guarda los
   registros del cliente importado y el borrado no la toca.
5. Los 502 con `{err}` (`main.py:8687`, `:8897`) y `/api/validate/smart`
   con `detail: str(e)`: fuera de la D6, que era de los 500.

## Veredicto

Aceptada sobre `c996ad4`, con 1 y 2 como pruebas que se suman, 3 (NULL)
como D43 de la Dev, y el resto a riesgos. Se integra con la cadena.
