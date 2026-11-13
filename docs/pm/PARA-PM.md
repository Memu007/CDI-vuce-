# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## FUGA-HILOS (D229 a): los ayudantes de tests/ cierran el bucle y el generador de la sesión

| | SHA |
|---|---|
| base | `d1ee0b71` |
| test | `07e0b2b9` |
| merge de tu rama (`1de18f9d`, sólo `docs/pm`) | `4174cfae` |
| informe | el commit `docs:` que trae este archivo |

**Resultado: cumple las cuatro puertas.** Nada para decidir.

- En la suite entera, el censo de hilos baja de 1123 a 10.
- Los «Task was destroyed but it is pending» con `async_generator_athrow` bajan de 1113 a 0.
- Los `passed` son los mismos: 6112.
- No toca el producto: `producto +0/−0`, arnés `+71/−127`.

### Causa
Los ayudantes hacían `asyncio.new_event_loop().run_until_complete(...)` con un `return` dentro de `async for db in get_async_session()`. Pasaban dos cosas:
- **El bucle nuevo nunca se cerraba.** El generador de la sesión quedaba suspendido y la conexión aiosqlite seguía abierta, con su `_connection_worker_thread` vivo.
- **El cierre llegaba tarde.** Al recolectar el generador, Python agendaba su `aclose()` en un bucle que ya no corría. Ese es el «Task was destroyed… async_generator_athrow».

### Arreglo (sólo en `tests/`, 22 archivos)
- **`asyncio.run(...)` en lugar de `new_event_loop().run_until_complete(...)`.** `asyncio.run` cierra los generadores pendientes (`shutdown_asyncgens`), el ejecutor y el bucle.
- **Envoltorios borrados.** Los envoltorios `_run`, `_run_async` y `_correr`, que sólo armaban y cerraban un bucle, ahora son llamadas directas a `asyncio.run`. Están en `admin2`, `admin_bootstrap`, `auth_login`, `nombres1`, `permisos2`, `roles_texto` y `cobro_corte1`.
- **Lo que queda.** En `tests/` el único `new_event_loop` es la fixture `event_loop` de `conftest.py:131`, que cierra su bucle.

### Puertas

**Suite entera** (`pytest -q --no-cov --timeout=120 -p no:cacheprovider`). El censo es `threading.enumerate()` en `pytest_sessionfinish`, antes de la limpieza de huérfanas de `conftest.py`.

| puerta | base `d1ee0b71` | arreglo `07e0b2b9` |
|---|---|---|
| 1. hilos vivos al final | 1123 (1113 `_connection_worker_thread`) | 10 |
| 2. resultado | `6112 passed, 110 skipped, 3 xfailed, 105 warnings in 1109.22s (0:18:29)` | `6112 passed, 110 skipped, 3 xfailed, 107 warnings in 1077.91s (0:17:57)` |
| 3. «Task was destroyed but it is pending» / `async_generator_athrow` | 1113 / 1113 | 0 / 0 |

**Puerta 4: el sabotaje.** `_sql` de `tests/test_guardar1.py` devuelto a `asyncio.new_event_loop().run_until_complete(_run())`. Ese ayudante lo usan cinco archivos: `guardar1`, `guardar2`, `catalogo3`, `catalogo_largo1` y `catalogo_largo2`. El subconjunto es esos cinco archivos.

| | arreglo | sabotaje |
|---|---|---|
| resultado | `210 passed, 3 warnings in 67.66s` | `210 passed, 5 warnings in 68.42s` |
| hilos vivos al final | 2 | 395 (393 `_connection_worker_thread`) |
| `async_generator_athrow` | 0 | 393 |

**Quién deja los 10 hilos que quedan en la suite entera.** Los nombres salen de `threading.enumerate()` al final de una corrida de los nueve archivos a los que el censo los atribuye: `593 passed, 25 skipped`.

| hilos | quién |
|---|---|
| 8 | Pools de módulo del producto, que viven todo el proceso. Son `lectura-excel` (2) y `lectura-excel-liviano` (2), en `main.py:3949` y `:3968`; `lectura-pdf` (1), en `main.py:3932`; `validar-excel` (2) y `validar-excel-liviano` (1), en `file_security.py:485` y `:504`. El censo los atribuye al primer test que los ve: `excel2` (2) y uno cada uno en `abuso1`, `cliente1c`, `clientes_plan04`, `despacho1b`, `excel1_lectura` y `excel1_rendimiento`. |
| 1 | `MainThread`, el proceso mismo. |
| 1 | Un `_DummyThread`: un hilo que no arrancó `threading` y al que Python registró al verlo. Aparece en `test_recent_changes_validation`. |

Ninguno es de aiosqlite.

### Lo que encontré y no cambié
- **Warnings «Event loop is closed».** La suite entera da 2 en la base y 3 en el arreglo: son `PytestUnhandledThreadExceptionWarning`, «Exception in thread … (_connection_worker_thread) … RuntimeError: Event loop is closed». Cada corrida los atribuye a tests distintos:
  - en la base, a `cliente1b` y `excel2`;
  - en el arreglo, a `cobro_mp2`, `maria3_antes_de_generar` y `org1`.

  Corridos solos, esos tres archivos del arreglo dan `345 passed, 3 warnings` y ningún «Event loop is closed». Lo leo como intermitente de orden y de recolección, de la misma familia que ya estaba en la base. No lo diagnostiqué más.
- **Riesgo en el producto (fuera de la pieza, sin tocar).** El mismo patrón, salir de `async for … in get_async_session()` sin agotar el generador, está en tres lugares de `main.py`:
  - **`main.py:11688`, el webhook de Mercado Pago:** 8 `return` dentro del `async for`.
  - **`main.py:1986`, el registro en `api_logs`:** un `break` en la línea 1998. Corre en cada pedido registrado.
  - **`main.py:1695`, al arrancar:** un `break` en la línea 1757.

  En producción el bucle sigue vivo, así que el generador lo cierra la recolección más tarde y la sesión se devuelve con retraso. No medí su efecto en el pool de Postgres.
- **Lo no corrido.** Adversarios y `/code-review` no se corrieron: es una pieza sin adversarios. Tampoco se corrió `ataque_aislamiento.sh` ni `smoke_friccion.sh`, porque no toca el producto.

### chequeo-6 `d1ee0b71 07e0b2b9`
```
chequeo-6 d1ee0b71..07e0b2b9: avisos para mirar, no un veredicto
producto +0/−0
arnés +71/−127
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

### Comandos para reproducir
Desde un worktree en `07e0b2b9`, con `GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares`:

```bash
grep -rn --include='*.py' new_event_loop tests/
# → sólo tests/conftest.py:131 (la fixture event_loop, que cierra su bucle)

F="tests/test_guardar1.py tests/test_guardar2.py tests/test_catalogo3.py tests/test_catalogo_largo1.py tests/test_catalogo_largo2.py"
python -m pytest -q --no-cov --timeout=120 -p no:cacheprovider $F 2>&1 | grep -c async_generator_athrow
# → 0 (y 210 passed)

sed -i 's/return asyncio.run(_run())/return asyncio.new_event_loop().run_until_complete(_run())/' tests/test_guardar1.py
python -m pytest -q --no-cov --timeout=120 -p no:cacheprovider $F 2>&1 | grep -c async_generator_athrow
# → 393 (sabotaje; después: git checkout tests/test_guardar1.py)

python -m pytest -q --no-cov --timeout=120 -p no:cacheprovider 2>&1 | grep -c async_generator_athrow
# → 0 en 07e0b2b9, 1113 en d1ee0b71; última línea 6112 passed, 110 skipped, 3 xfailed
```

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; entregué FUGA-HILOS (test 07e0b2b9, merge 4174cfae); censo 1123→10, athrow 1113→0, 6112 passed, sabotaje 2→395 hilos; riesgo main.py:11688/1986/1695 sin tocar; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM; nada se publica sin el «dale» de Emi para el SHA, nunca main, sin secretos; próxima D: D230.
