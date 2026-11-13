# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## GUARDA-VERSION, vuelta 2: si alguien rompe la guarda, un dato del caso nuevo da rojo y dice cuál

| | SHA |
|---|---|
| base (tu rama integrada con `merge`) | `703066b1` |
| conftest sin la línea fija | `f0ec76d1` |
| caso nuevo `tests/test_guarda_conexiones.py` | `1be2477b` |
| informe | el commit `docs:` que trae este archivo |

**Resultado:** cumplo los dos defectos y el comportamiento pedido, salvo el
tope de espera del cierre, que no cubro (abajo, en «Riesgos»).
**Nada para decidir.** Hay un supuesto reversible: saqué la línea del resumen.
`producto +0/−0`, arnés `+85/−6`. No hay D nueva.

**Cómo funciona.** Hay un solo caso, `test_guarda_de_conexiones`, con cuatro
datos. Cada dato corre una sesión de pytest aparte, por `subprocess`, cuyo
`conftest.py` carga el `tests/conftest.py` real con `importlib`. Adentro van
un test que deja una conexión guardada en una lista del módulo (tu ejemplo) y
lo que pide cada dato:

| dato | qué rompe si cambia | espera |
|---|---|---|
| veredicto del cierre | `if vivos:` | rc=1, «dejó 1 conexión(es) de aiosqlite abiertas» |
| foto antes de los fixtures | la foto se toma en `pytest_runtest_setup` tryfirst, antes de los fixtures | la fuga dentro de un fixture async también da «dejó 1» |
| la culpa es de quien la deja | la foto de cada test | primero un test con fuga y después uno limpio: «test_deja_una_abierta dejó 1», y nunca «test_abre_y_cierra dejó» |
| chequeo de arranque | `_guarda_ve_una_conexion` | con `_HILO_AIOSQLITE` cambiado sólo adentro: rc=4, «La guarda de conexiones no ve una conexión abierta», y ningún `passed` |

**Por qué no usé `pytester`, tu sugerencia.** Con `runpytest` en el mismo
proceso, la conexión que deja el test de adentro queda viva en el proceso de
afuera, y la guarda de afuera marca al caso de afuera. `runpytest_subprocess`
es lo mismo que hice yo, pero además hay que activar el plugin. El costo es el
mismo: lo paga sólo la corrida que incluye este archivo.

### Supuesto reversible

Saqué `pytest_terminal_summary` (−6). Si la línea saliera del resultado del
chequeo y alguien sacara el chequeo, la línea desaparecería sin que nadie lo
note. La evidencia que cambia es el dato «chequeo de arranque»: sin el bloque,
ese dato da rojo (sabotaje 6). Si querés la línea calculada, la agrego.

### Sabotajes, un rojo por parte

Cada uno se corrió sobre `tests/conftest.py` en un worktree descartable,
corriendo el archivo nuevo. Copio de `<S>/sab_guarda.log`:

| # | sabotaje | resultado |
|---|---|---|
| 1 | `if vivos:` → `if vivos and False:` | rc=1, `3 failed, 1 passed`: veredicto, foto, culpa |
| 2 | sin `pytest_runtest_setup` (renombrada) | rc=1, `3 failed, 1 passed`: los mismos tres |
| 3 | la foto después de los fixtures (`wrapper=True`, `yield` antes del stash) | rc=1, `1 failed, 3 passed`: `[foto antes de los fixtures]` |
| 4 | la foto vacía (`= set()`) | rc=1, `1 failed, 3 passed`: `[la culpa es de quien la deja]` |
| 5 | `_HILO_AIOSQLITE = "(_worker_thread)"` | rc=4. La corrida entera aborta al arrancar: `Exit: La guarda de conexiones no ve una conexión abierta de aiosqlite 0.22.1: busca hilos que terminen en '(_worker_thread)'. Ajustá _hilos_de_aiosqlite a esta versión.` |
| 6 | `if not _guarda_ve_una_conexion():` → `if False:` | rc=1, `1 failed, 3 passed`: `[chequeo de arranque]` |
| 7 | `_TOPE_CIERRE = 0` | **rc=0, `4 passed`**: no cubierto |

En el 5 el rojo no sale del caso nuevo: el chequeo de arranque frena antes la
suite de afuera, y dice qué se rompió. El dato «chequeo de arranque» cubre que
ese chequeo exista (6).

El 4 dio verde en la primera versión de los datos (el tercero era sólo un test
limpio). Por eso el tercer dato es ahora «fuga y después uno limpio».

### Puertas, sobre `1be2477b`

| puerta | salida |
|---|---|
| suite completa, worktree limpio | `6130 passed, 110 skipped, 3 xfailed, 107 warnings in 1091.23s (0:18:11)`, rc=0 |
| el archivo nuevo solo | `4 passed, 3 warnings in 22.34s`, rc=0, 24 s de reloj |
| lo que suma a la suite | ~22 s: los 4 pytest anidados del archivo. No corrí la suite sin el archivo para restar |
| `chequeo-6.py 703066b1 1be2477b` | abajo, entero |
| `compileall -q proyecto_maria tests/conftest.py tests/test_guarda_conexiones.py` | rc=0 |

```
chequeo-6 703066b1..1be2477b: avisos para mirar, no un veredicto
producto +0/−0
arnés +85/−6
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

Contra `64106289` (la pieza entera): `arnés +111/−1`, `avisos: 0`.

### Comandos

```bash
python -m pytest -q --no-cov -p no:cacheprovider tests/test_guarda_conexiones.py
# 4 passed
sed -i 's/    if vivos:/    if vivos and False:/' tests/conftest.py
python -m pytest -q --no-cov -p no:cacheprovider tests/test_guarda_conexiones.py
# 3 failed, 1 passed; cada FAILED dice el dato; después: git checkout tests/conftest.py
```

### Riesgos y no corrido

- **El tope no está cubierto.** Con `_TOPE_CIERRE = 0` todo sigue verde: el
  hilo de una conexión bien cerrada ya terminó antes del teardown. Para que
  dé rojo haría falta un cierre lento a propósito, o sea una espera fija, y
  eso está prohibido. Si el tope bajara, el riesgo sería una falsa alarma,
  no una fuga sin ver.
- No corrí aiosqlite 0.19 ni 0.20 (0.21 lo corriste vos), ni Postgres.
- Sin adversarios ni `/code-review`, como pide la pieza.
- Los datos dependen de que el `asyncio_mode = auto` de adentro sea el mismo
  que el de afuera (`pytest.ini` del repo). Si cambiara, el caso no se
  enteraría.

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica. GUARDA-VERSION vuelta 2 entregada: f0ec76d1 (conftest sin línea fija) + 1be2477b (test_guarda_conexiones.py, 4 datos) sobre 703066b1, informe en el commit docs siguiente. Después espera a Emi (punto 14, D182, D206). Próxima D: D231. Sin advisor, nunca main, sin secretos, test_conexiones1.py no se sube.
