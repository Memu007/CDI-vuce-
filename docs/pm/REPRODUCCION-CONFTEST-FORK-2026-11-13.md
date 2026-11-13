# Reproducción de CONFTEST-FORK (2026-11-13)

Pieza de la Dev técnica: un hijo creado con `fork` heredaba el `atexit` del
conftest y, al salir normal, borraba la base de prueba del padre. Entregada
en `caad310a` (arreglo `f2d5580e`, test `a2d6c18a` + `caad310a`), informe
`3392daf4`. Base `fa6df9bc`. Diff fuera de `docs/pm`: `tests/conftest.py`
+4 y `tests/test_conftest_fork.py` +17. `chequeo-6 fa6df9bc caad310a`: igual
al informe (producto +0/−0, arnés +21/−0, historia vacía, 0 avisos).

Corrido por la PM en un worktree en `caad310a`, con el entorno de pytest de
siempre (`env -u DATABASE_URL -u ENVIRONMENT`, `--no-cov -p no:cacheprovider`).

| qué | salida |
|---|---|
| puerta 1, el test con el arreglo | `1 passed, 6 warnings in 0.08s` |
| puerta 1, con `tests/conftest.py` de `fa6df9bc` | `E   AssertionError: el hijo borró la base del padre`, `1 failed` |
| el test usa el mismo módulo que cargó pytest | `sys.modules` tiene un solo `tests.conftest` |
| puerta 2 con el arreglo | `/tmp/cdi_pytest_*` 4151 antes y 4151 después |
| negativo mío: la guarda siempre vuelve (nadie borra) | el test da `1 passed`, pero la cuenta sube 4151 → 4152 |
| negativo mío: guarda invertida (borra sólo el hijo) | `1 failed`; la cuenta no informa (la base la borra el hijo) |
| puerta 4, suite entera | `1 failed, 6110 passed, 110 skipped, 3 xfailed, 103 warnings in 1096.99s (0:18:16)`; el único rojo es `test_la_subida_cara_no_frena_a_nadie[9995 combinadas en 19 990 filas]` (D234), el mismo de la base de la Dev (`1 failed, 6109 passed`) |

**Lectura.** La puerta 1 distingue el defecto original. La 2 no lo distingue
(lo dice el informe), pero sí distingue un arreglo pasado de rosca: con la
guarda que nunca borra, el test sigue verde y sólo la cuenta de `/tmp` lo
muestra. Las dos juntas cubren los dos lados.

**No corrido por la PM:** la puerta 3 (pool a mano; la corrió la Dev, y los
hijos del pool salen con `os._exit`, que no corre `atexit`), la suite sobre
la base (la corrió la Dev; la comparo con su lista) y adversarios (la tarea
dice sin adversarios).
