# Reproducción de FUGA-HILOS (2026-11-13)

Entrega de la Técnica: base `d1ee0b71`, arreglo `07e0b2b9` (sólo `tests/`),
merge de mi rama `4174cfae`, informe `d9dd73bc`. Revisado por la PM principal
en un worktree en `d9dd73bc` y en la unión `f1403811` (mi rama `1de18f9d` +
MARIA `9ed8b9a9` + `d9dd73bc`). Veredicto: **aceptada e integrada**.

| qué | salida |
|---|---|
| `chequeo-6.py d1ee0b71 07e0b2b9` | producto +0/−0, arnés +71/−127, historia vacía, 0 AVISO: igual que el informe |
| `git diff --name-only d1ee0b71 d9dd73bc` fuera de `tests/` y `docs/pm/` | nada |
| `git grep new_event_loop d9dd73bc -- tests/` | sólo `tests/conftest.py:131`, la fixture que cierra su bucle |
| subconjunto de 8 archivos (los 5 de `_sql` de `guardar1` más `admin2`, `permisos2`, `cobro_corte1`), arreglo | `337 passed`, 0 `async_generator_athrow` |
| el mismo subconjunto con `_sql` de `guardar1` devuelto a `new_event_loop().run_until_complete` | `337 passed`, 393 `async_generator_athrow` (el informe: 393 hilos de aiosqlite) |
| pytest entero sobre la unión `f1403811`, con un plugin mío que deja 1075 hilos quietos desde el arranque (lo que la base acumulaba): la suite no depende de tener hilos libres | `6126 passed, 110 skipped, 3 xfailed`, rc=0, 19 min; 0 `async_generator_athrow`. Son los 6112 del informe más los 14 de `test_cuit_perfil.py` de MARIA |
| censo de hilos al cerrar la sesión (plugin mío que mide antes de la limpieza de huérfanas de `conftest.py`), los 5 archivos de `_sql` de `guardar1` | arreglo: `210 passed`, 2 hilos, 0 de aiosqlite. Sabotaje de arriba: `210 passed`, 395 hilos, 393 de aiosqlite (el informe: 395 y 393) |
| «Event loop is closed» en esa corrida | 3 avisos, en `clientes_crud`, `prelaunch_block1` y `separadores1b`: otros tests que los del informe, como dice la Dev |

**Riesgo, sin test.** Ningún caso se pone rojo si un ayudante de `tests/`
vuelve a `new_event_loop().run_until_complete`: la puerta 4 pedía una
medición, no una guarda. Va como pieza siguiente (FUGA-HILOS-GUARDA, sólo
tests).

**Riesgo de producto, no medido.** El mismo patrón (salir de `async for … in
get_async_session()` sin agotarlo) en `main.py:11688` (webhook de Mercado
Pago, 8 `return`), `main.py:1986` (`api_logs`, en cada pedido registrado) y
`main.py:1695` (arranque). Nadie midió su efecto en el pool de Postgres. Va a
la cola como riesgo; tocarlo es producto con dinero y pide revisión fuerte.

No corrido: Postgres, el censo de hilos de la suite entera (el informe: 1123 → 10), adversarios (pieza sin adversarios).
