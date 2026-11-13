# Reproducción de GUARDA-VERSION (2026-11-13)

Entrega de la Técnica: base `64106289`, test `95e7a835` (sólo
`tests/conftest.py`), informe `3f39ff36`. Revisado por la PM principal en un
worktree en `3f39ff36`, con aiosqlite 0.22.1 en el venv y 0.21.0 instalado
aparte (`pip --target`, usado con `PYTHONPATH`). Veredicto:
**devolución por la causa** (abajo).

| qué | salida |
|---|---|
| `chequeo-6.py 64106289 95e7a835` | producto +0/−0, arnés +32/−1, historia vacía, 0 avisos: igual que el informe |
| `git diff --name-only 64106289 3f39ff36` | `docs/pm/PARA-PM.md`, `tests/conftest.py` |
| puerta 1: `tests/test_valor1.py` con 0.21.0 | rc=4, `Exit: La guarda de conexiones no ve una conexión abierta de aiosqlite 0.21.0: busca hilos que terminen en '(_connection_worker_thread)'. Ajustá _hilos_de_aiosqlite a esta versión.` |
| puerta 1: el mismo archivo con 0.22.1 | `guarda de conexiones: vio la conexión de prueba de aiosqlite 0.22.1`, `76 passed, 3 warnings in 18.00s` |
| puerta 2: `_HILO_AIOSQLITE = "(_worker_thread)"` | rc=4, el mismo mensaje con `'(_worker_thread)'`; 0 líneas «vio la conexión» en esa salida |
| negativo mío: un test async que guarda `aiosqlite.connect(":memory:")` en una lista del módulo, con la guarda entera | `…dejó 1 conexión(es) de aiosqlite abiertas después de 5 s: ['Thread-7 (_connection_worker_thread)']…`, `1 passed, 3 warnings, 1 error in 5.07s` |
| el mismo test con `if vivos:` cambiado por `if vivos and False:` en `pytest_runtest_makereport` | `guarda de conexiones: vio la conexión de prueba de aiosqlite 0.22.1`, `1 passed, 3 warnings in 5.06s`: **verde** |
| negativo mío: sin el bloque `if not _guarda_ve_una_conexion()`, con 0.21.0 | `guarda de conexiones: vio la conexión de prueba de aiosqlite 0.21.0`, `76 passed, 3 warnings in 18.16s`: la línea dice que vio y no se chequeó nada |
| pytest entero | no lo corrí sobre `3f39ff36`: va sobre el SHA de la vuelta, en la unión. El de la Técnica: `6126 passed, 110 skipped, 3 xfailed` |

**Causa.** Lo que queda en el repo prueba que la guarda *reconoce* una
conexión (el chequeo de arranque), no que una fuga termine en rojo. El
cierre (`pytest_runtest_makereport`) y la foto de antes del test
(`pytest_runtest_setup`) se pueden romper con todo verde. Además, la línea
del resumen es un texto fijo, no el resultado del chequeo. El pedido decía
«por la versión instalada o porque alguien la rompe»: la segunda mitad no
está.

**Devolución.** Comportamiento: romper cualquier parte de la guarda da rojo
en la suite normal y dice cuál. Familia, como datos de un caso:
reconocimiento, foto de antes y veredicto del cierre. La evidencia que se
muestra sale de lo que se vio. Hay que informar el tiempo que suma.
`pytester` en archivo propio va como sugerencia. Para la vuelta guardo un
ejemplo que no le di.

No corrido: pytest entero sobre `3f39ff36`, aiosqlite 0.19 y 0.20,
Postgres, adversarios (pieza sin adversarios).
