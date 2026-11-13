# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL2D-RELOJ: el caso de la subida cara ya no depende de cuántos hilos tenga el proceso

| qué | SHA |
|---|---|
| base | `70d5f962` |
| test (`tests/test_excel2d.py`, +8/−1) | `c4a30b5a` |
| merge de tu rama (`51ffe4fb`) | `0ebac615` |
| informe | el commit `docs:` que trae este archivo |

**Resultado.** Las cuatro puertas en verde. Producto: ninguno tocado
(`producto +0/−0`). Los ~1100 hilos los deja **el arnés**, no el producto.

**Causa.** `_otro_hilo_listo()` recorre `/proc/self/task`, y eso cuesta según
la cantidad de hilos: 8,4 ms con 1000 y 26,4 ms con 3000. Con el GIL en
disputa, el testigo casi no marcaba, y `frenado` terminaba midiendo al
testigo. **Arreglo:** el recorrido se hace sólo después de un salto sin CPU
(`cpu < reloj/20`), y cuenta como un salto propio: después de él se agrega un
punto marcado `True`. El tope de 1 s no se tocó.

### Decisiones

**D229. Fuga de hilos del arnés.**
- (a) Pieza aparte (o cola de limpieza): que los ayudantes cierren la sesión.
  Son 28 usos de `asyncio.new_event_loop().run_until_complete` en 15
  archivos de `tests/`. Los ayudantes son como `_sql` en
  `tests/test_guardar1.py:44-50`.
- (b) Dejarlo así.
- **Recomiendo (a):** la fuga ya rompió un caso por cantidad de hilos, y
  `test_cobro_mp2` solo suma 358.

### Quién deja los hilos (puerta 4)

**Mecanismo.**
1. El ayudante hace `return` dentro de `async for db in get_async_session()`,
   en un bucle nuevo que después se abandona.
2. El generador queda suspendido. El `aclose` que agenda su finalizador nunca
   corre, porque ese bucle ya no gira.
3. La sesión no se cierra, y su conexión aiosqlite deja vivo un
   `_connection_worker_thread`. Esos hilos no son daemon: un script suelto
   así queda colgado al salir.
4. Lo mismo explica los «Task was destroyed but it is pending!
   … async_generator_athrow» del final de la suite.

**Por qué no es producto.**
- `main.py:11688` (webhook de MP) usa el mismo `return` dentro del
  `async for`. `main.py:174,1695,1986` y `auth/dependencies.py:22` usan
  `get_db` con `yield`.
- Con un bucle vivo, como uvicorn en Railway, el finalizador sí cierra la
  sesión. Medido abajo: no pierde hilos.
- No lo probé contra un uvicorn real durante horas. Lo que sí probé son el
  bucle vivo y `TestClient`.

**Medidas**

| prueba | salida |
|---|---|
| 20 llamadas como el arnés / cerrando el generador | `cerrando hilos 1 -> 1` · `como_el_arnes hilos 1 -> 21` |
| un bucle vivo, 20 `return` dentro del `async for`, más `sleep(0.5)` | `un bucle vivo, return dentro del async for: hilos 1 -> 1` |
| `TestClient`, 60 `/auth/register`, con un bucle y con un bucle por pedido | `hilos antes 1 después 1` en los dos |
| `test_catalogo_largo2.py -k una_entrada_mala`, censo por caso | 18, 31, 44, 57, 80, 103, 126, 139, 152, 165, 178: +13 por caso, +23 en las variantes `cambio-*` |

**Censo de la suite entera:** 6225 casos, rc=0. Al final hay n=1129 hilos en
`/proc` (py=1124), con un máximo de 1131. Casi todos son
`_connection_worker_thread`; además quedan 2 `lectura-excel`,
2 `lectura-excel-liviano`, 2 `validar-excel` y `MainThread`.

| hilos que suma | archivo |
|---|---|
| 358 | `test_cobro_mp2` |
| 245 | `test_catalogo_largo2` |
| 105 | `test_cobro_mp1_vuelta2` |
| 103 | `test_cobro_mp1_h` |
| 79 | `test_cobro_mp1` |
| 78 | `test_catalogo3` |
| 41 | `test_cobro_mp1_cde` |
| 34 | `test_catalogo_largo1` |
| 25 | `test_guardar1` |
| 17 | `test_cobro_mp1_i` |
| 13 | `test_guardar2` |
| 8 | `test_cobro_mp3` |

### Comandos para reproducir

Plugin que pone hilos dormidos, fuera del repo:

```bash
mkdir -p /tmp/hp && cat > /tmp/hp/hilos_plugin.py <<'PY'
import os, threading
_fin = threading.Event()
def pytest_sessionstart(session):
    for _ in range(int(os.environ.get("HILOS", "1075"))):
        threading.Thread(target=_fin.wait, daemon=True).start()
def pytest_sessionfinish(session):
    _fin.set()
PY
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
```

**Puerta 1.** Tiene que dar `7 passed` en los tres:
```bash
for h in 0 1000 3000; do HILOS=$h PYTHONPATH=/tmp/hp python -m pytest -q --no-cov -p hilos_plugin tests/test_excel2d.py -k no_frena | tail -1; done
```

**Rojo con el arreglo revertido.** Con 1000 hilos tiene que dar
`el otro hilo no avanzó mientras el proceso gastó 1.0x s de CPU`:
```bash
git checkout c4a30b5a~1 -- tests/test_excel2d.py && HILOS=1000 PYTHONPATH=/tmp/hp python -m pytest -q --no-cov -p hilos_plugin tests/test_excel2d.py -k no_frena | tail -3; git checkout c4a30b5a -- tests/test_excel2d.py
```

**Puerta 2.** Tiene que dar 21 ROJO por tanda y `sabotajes con falla: 0`:
```bash
for h in 0 1000 3000; do HILOS=$h PYTHONPATH=/tmp/hp PYTEST_ADDOPTS="-p hilos_plugin" scripts/testing/sabotajes/excel2d.sh c4a30b5a | tail -2; done
```

### Puertas

| puerta | salida |
|---|---|
| 1. 0 hilos | `7 passed … 2.77s` |
| 1. 1075 hilos | `7 passed … 2.63s` |
| 1. 3000 hilos | `7 passed … 2.74s` |
| 1. `test_excel2d.py` entero | `26 passed, 3 warnings in 4.57s` |
| rojo antes del arreglo, 0 hilos | `7 passed` (por eso no se veía) |
| rojo antes del arreglo, 1075 hilos | `E   AssertionError: el otro hilo no avanzó mientras el proceso gastó 1.09 s de CPU` · `1 failed, 6 passed` |
| rojo antes del arreglo, 3000 hilos | igual, con 1.10 s |
| 2. `excel2d.sh` con 0, 1000 y 3000 hilos | 21 ROJO por tanda, 63 en total · `sabotajes con falla: 0` · rc=0 en las tres |
| 3. suite entera sobre `c4a30b5a` | `=== 6112 passed, 110 skipped, 3 xfailed, 106 warnings in 1061.09s (0:17:41) ====` |
| 4. quién deja los hilos | el arnés (ver arriba) |

**Puerta 2: los ROJO que pedías**, iguales en las tres tandas:
- «ROJO  | cada combinada vuelve a asignarse aparte en pandas: dice «FAILED tests/test_excel2d.py::test_la_subida_cara_no_frena_a_nadie[9995 combinadas en 19 990 filas]» (17 s)»
- «ROJO  | las celdas rellenadas vuelven a copiarse en cada fila: dice «FAILED tests/test_excel2d.py::test_la_subida_cara_no_frena_a_nadie[2499 combinadas en 4998 filas]» (6 s)» (7 s con 3000 hilos)
- «ROJO  | la subida espera 4 s sin gastar CPU: dice «FAILED tests/test_excel2d.py::test_la_subida_cara_no_frena_a_nadie[2499 combinadas en 4998 filas]» (13 s)»

**Puerta 3.** Vos tuviste `1 failed, 6110 passed` sobre `caad310a`. La base
`70d5f962` suma 1 caso de `test_valor1.py` (MARIA) y 1 de `finalize.js`:
6110 + 1 + 1 = 6112. No corrí la suite sobre `70d5f962`.

`chequeo-6 70d5f962 c4a30b5a` (rc=0, entero):
```
chequeo-6 70d5f962..c4a30b5a: avisos para mirar, no un veredicto
producto +0/−0
arnés +8/−1
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

### Riesgos

- **El margen del sabotaje de espera.** Con 3000 hilos, el sabotaje de 4 s
  sin CPU todavía da rojo, con ~1,1 s contra un tope de 0,5. Si los hilos
  crecen mucho más, el margen baja. D229 (a) lo ataca de raíz.

### No corrido

- Adversarios y `/code-review`: sigue vigente «sin adversarios».
- La suite sobre la base `70d5f962`.
- Uvicorn real de larga vida.

### Archivos de producto tocados

Ninguno.

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main); PM session_01B7FVQspcEHF7PqNv797wNM. Entregué EXCEL2D-RELOJ (test c4a30b5a, merge 0ebac615). Sigue NAVEGADOR. D229 abierta (fuga de hilos del arnés). Próxima D: D230. Sin adversarios. Nada se publica sin el «dale» de Emi para el SHA. Sin secretos.
