# Reproducción de FUGA-HILOS-GUARDA (2026-11-13)

Entrega de la Técnica: base `7bae88f5`, guarda `a58d45d5` (sólo
`tests/conftest.py`), informe `7e36ba88`. Revisado por la PM principal en
worktrees en `7e36ba88`. Veredicto: **aceptada**.

| qué | salida |
|---|---|
| `chequeo-6.py 7bae88f5 a58d45d5` | producto +0/−0, arnés +37/−0, historia vacía, 0 avisos: igual que el informe |
| `git diff --name-only 7bae88f5 7e36ba88` fuera de `docs/pm/` | sólo `tests/conftest.py` |
| negativo mío: `_sql` de `guardar1` devuelto a `new_event_loop().run_until_complete` (un ayudante real, no el archivo de prueba de la Dev); salida entera guardada | `28 passed, 3 warnings, 12 errors in 64.36s`; 12 líneas «dejó», una por error. Las 6 líneas `IntegrityError` de esa salida están dentro de «Captured log call» de tests que hacen fallar el historial a propósito: pytest muestra el log porque el reporte es error; sin sabotaje (`28 passed`) no se muestran |
| el mismo archivo sin sabotaje | `28 passed`, 0 «dejó» |
| negativo mío, otra forma: `async for … break` sobre `get_async_session` en `new_event_loop()` + `run_until_complete` + `close()`, sin `shutdown_asyncgens` | rojo: «…dejó 1 conexión(es)… ['Thread-10 (_connection_worker_thread)']» |
| negativo mío: `aiosqlite.connect` en un test async, guardada en una lista del módulo | rojo: «…dejó 1 conexión(es)… ['Thread-6 …']» |
| `aiosqlite.connect` sin cerrar en un test async, descartada o en una variable local; `async for … break` dentro de `asyncio.run` | verde. Por el efecto es lo correcto: aiosqlite 0.22 para el hilo en `Connection.__del__` al soltar la conexión, y `asyncio.run` cierra el generador con `shutdown_asyncgens`. El informe da rojo para «aiosqlite.connect directo»; su archivo está fuera del repo, así que no sé si la retenía. Sin defecto |
| negativo mío: 12 archivos corridos de a uno (que el primer test de un archivo no cargue con conexiones de fixtures o del arranque): `guardar1`, `org1`, `sesion1`, `cobro_corte1`, `clientes_crud`, `admin2`, `permisos2`, `catalogo3`, `prelaunch_block1`, `estudio1`, `generar_maria_txt`, `cuit_perfil` | los 12 verdes (28, 87, 44, 98, 40, 4, 25, 107, 44, 26, 60, 14 passed), 0 errors |
| pytest entero sobre `7e36ba88` | `6126 passed, 110 skipped, 3 xfailed, 107 warnings in 1149.00s`, rc=0; 0 «dejó»; 8 «Event loop is closed», los mismos que sin la guarda |

**Riesgo, sin camino hoy: la guarda depende de la versión de aiosqlite.**
Reconoce las conexiones por el nombre del hilo (`(_connection_worker_thread)`).
Ese nombre no lo pone aiosqlite: es el que Python le da a un `Thread` con
`target` (`core.py:90` de 0.22.1, `Thread(target=_connection_worker_thread,
…)`), así que también puede cambiar con una versión nueva. En 0.19, 0.20 y 0.21 (miré los tres
paquetes) la conexión es ella misma el hilo (`class Connection(Thread)`) y se
llama `Thread-N`: la guarda no ve nada y no avisa. `requirements.txt:94` pide
`aiosqlite>=0.19.0`; la CI y mi venv instalan la última (0.22.1), así que hoy
funciona. Un venv viejo o una versión nueva la dejan ciega en silencio. Pasa a
la pieza siguiente de la Técnica (GUARDA-VERSION).

**Riesgo, sin camino hoy:** una fixture de módulo o de sesión que abra una
conexión de aiosqlite y la deje abierta haría rojo al primer test que la usa,
con un mensaje que culpa al test. Hoy no hay ninguna (pytest entero y los 12
archivos sueltos, verdes). A la cola de limpieza.

**D230** (los `get_db` de `main.py:173` y `auth/dependencies.py:21` no
cierran `get_async_session`): leída la causa en el informe y el código, no
reproducida su contraprueba. Mirado en `connection.py:86-107`: el `finally: session.close()` corre aunque
tarde, y el pool deshace lo abierto al devolver la conexión; si es así, hoy
el efecto es el retraso, no datos a medias (leído, no medido). **Ahora no,
decidido por la PM; la pieza (a) va a Emi con recomendación de sí.** Una
sola entrada en «Riesgos que esperan a Emi» de la cola, junto con los otros
tres `async for`. El caso de `test_cobro_corte1` que se rompe queda para esa
pieza.

No corrido: Postgres, la contraprueba de D230, el experimento aislado de
D230, aiosqlite 0.19 a 0.21 corriendo (sólo leí sus paquetes), adversarios
(pieza sin adversarios).
