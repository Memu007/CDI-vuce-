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

## Vuelta 2

Entrega: `f0ec76d1` (saca la línea fija del resumen, −6) y `1be2477b`
(`tests/test_guarda_conexiones.py`, +85: un caso con cuatro datos que corre
pytest aparte con el `conftest.py` real), informe `bb83ecc6`, merge
`9661f5d3`, que ya trae mi rama (`32dfcd5b`): la unión es `9661f5d3`.
Revisado en un worktree en `9661f5d3`.

| qué | salida |
|---|---|
| `chequeo-6.py 703066b1 1be2477b` | producto +0/−0, arnés +85/−6, historia vacía, 0 avisos: igual que el informe |
| `chequeo-6.py 64106289 1be2477b` | producto +0/−0, arnés +111/−1, historia vacía, 0 avisos |
| `tests/test_guarda_conexiones.py` | `4 passed, 5 warnings in 23.84s`, rc=0 |
| mi ejemplo guardado: `pytest_runtest_setup` sin la foto (`pass`) | `3 failed, 1 passed`: rojos «veredicto del cierre», «foto antes de los fixtures», «la culpa es de quien la deja» |
| negativo mío: `or reporte.failed` → `or True` (el cierre nunca juzga) | `3 failed, 1 passed`: los mismos tres |
| negativo mío: la foto vacía (`= set()`) | `1 failed, 3 passed`: rojo «la culpa es de quien la deja» |
| negativo mío: sin `tryfirst` | `4 passed`: verde, y es correcto (el hook de un conftest ya corre antes que el de pytest) |
| negativo mío: `trylast=True` (la foto después de los fixtures) | `1 failed, 3 passed`: rojo sólo «foto antes de los fixtures» |
| negativo mío: sin el chequeo de arranque (`if False:`) | `1 failed, 3 passed`: rojo sólo «chequeo de arranque» |
| `git diff --name-only 32dfcd5b 9661f5d3` | `docs/pm/PARA-PM.md`, `tests/conftest.py`, `tests/test_guarda_conexiones.py` |
| pytest entero sobre `9661f5d3` | `6130 passed, 110 skipped, 3 xfailed, 108 warnings in 1134.62s (0:18:54)`, rc=0, 0 «dejó» |
| aiosqlite que instala la CI | `requirements.txt:94` `>=0.19.0` sin tope: hoy 0.22.1, la misma del venv donde la suite da verde |

**Aceptada e integrada** (merge `0bd0d3d6`). Cada parte rota da rojo: el
reconocimiento, la foto, su orden y el veredicto del cierre. El rojo nombra
el dato que cae, no la parte rota. Sin foto o sin veredicto caen los mismos
tres datos, porque el cierre juzga con la foto. Para separarlos alcanza el
nombre del dato más el diff que rompió: **decidido por la PM** que eso cumple
«dice cuál». El pytest de adentro usa su propia base (`mkstemp` por proceso).

- Supuesto aceptado: sacar la línea del resumen. No mostrar nada cumple «sale
  de lo que se vio».
- Riesgo aceptado: `_TOPE_CIERRE = 0` da verde, y si el tope baja, lo que
  aparece son falsas alarmas: ninguna fuga queda escondida.
- Riesgo anotado: el caso escribe `asyncio_mode = auto` adentro. Si el
  `pytest.ini` cambia, hay que cambiarlo también ahí.
- Tiempo: el archivo suma 23.84 s acá (22.34 s en el informe), en una CI que
  ya se corta a los 20 min (punto 14, ya preguntado a Emi).

No corrido: los sabotajes 1–6 del informe (corrí los seis míos de arriba),
aiosqlite 0.19 y 0.20, Postgres y adversarios (pieza sin adversarios).
