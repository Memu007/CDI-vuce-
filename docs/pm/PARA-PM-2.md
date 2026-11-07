# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Rojo de `despacho1b`: **diagnosticado y entregado**. Prueba en `d69233c`, más este informe (2026-11-07)

| Qué | SHAs |
|---|---|
| Prueba | `d69233c` (sólo `tests/test_despacho1b.py`) |
| Producto | ninguno |
| Informe | el commit `docs:` que sigue a `d69233c` |
| Base | `9417c3b` |

**Causa.** Es la memoria de la suite, por el recolector de basura. No es el orden de los casos, no son hilos y no es el producto.
- `test_las_hojas_leidas_antes_del_corte_dan_sus_productos` llama a `leer_despacho` dentro del proceso de pytest, con `limite_cpu_s=1.0`. El corte de extraer llega a los 0,8 s, porque `_PARTE_PARA_EXTRAER = 0.8`. Para entender el texto quedan unos 0,2 s, y el caso gasta 50 ms a propósito.
- En la suite entera quedan millones de objetos vivos. Una pasada completa del recolector (generación 2) sobre esa memoria cuesta **0,608 s de CPU**, medido con `gc.callbacks` y 3 millones de objetos. Si esa pasada cae entre el corte y el final de `leer_texto`, se come el tope que queda. Sale exactamente tu rojo: renglones vacíos, «leí hasta la hoja 2» y «no pude leer sus productos».
- Por eso pasa solo y con su archivo, y en la suite a veces sí y a veces no: depende de si la pasada cae en esa ventana. Con memoria chica, cada pasada cuesta de 36 a 80 ms.
- Tu prueba con un hilo girando no lo reproducía porque la causa no es CPU de otros hilos.

**Por qué el producto no cambia.** En producción `leer_despacho` sólo corre en el proceso aparte (`_MODOS["leer"]`, lanzado por `_leer_aparte`), que arranca con poca memoria. Busqué los usos en `proyecto_maria/` y no hay otra llamada.

**Arreglo (sólo prueba).** El caso envuelve la llamada con `gc.freeze()` / `gc.unfreeze()`. Así lo que heredó de la suite no entra en la pasada, y las pasadas del propio lector siguen contando, como en el proceso aparte.

**Evidencia** (un fixture, justo antes del caso, deja vivos 3 millones de dicts con una lista cada uno; 6 corridas por brazo; lo corrí tres veces, la última con el bloque de «Comandos copiables» tal cual, y dio lo mismo):

| | resultado |
|---|---|
| sin memoria extra, sin arreglo | `1 passed` |
| 3 M objetos, sin arreglo | `3 failed`, `3 passed` |
| 3 M objetos, con arreglo | `6 passed` |
| 3 M objetos + `gc.freeze` desde afuera, sin arreglo | 6 de 6 lecturas con los 3 renglones (medido en el script) |

Las 6 corridas por brazo no son repetir hasta el verde: cambia una sola variable, la memoria. El rojo sin arreglo no sale siempre, porque depende de dónde cae la pasada del recolector.

**Para decidir: D106** (sale de `/code-review`, es producto y no lo toqué).
- Hoy el tiempo para entender el texto es lo que sobra del tope después de extraer. No tiene un mínimo propio.
- Si extraer se pasa del 80 % por más que el resto, `leer_texto` arranca con 1 ms y el aviso es «no pude leer sus productos», aunque las hojas se leyeron.
- En producción el tope es `_MAX_CPU_LECTURA = 10.0`, así que el resto son 2 s, y el proceso aparte tiene poca memoria.

Las opciones:
- (a) Queda así.
- (b) Pieza aparte: reservar `limite_cpu_s × 0,2` desde que terminó de verdad la extracción.

Recomiendo **(a)**: para gastar 2 s de más entre el corte y `leer_texto` haría falta algo que no vi pasar en el proceso aparte.

D99 sigue con Emi. D105 está en tu mano desde el informe de ABUSO-2. Próxima D libre: D107.

## Autorrevisión

| Quién (modelo, esfuerzo) | Hallazgo | Qué hice |
|---|---|---|
| adversario-sonnet-medio | 1. Con `_PARTE_PARA_EXTRAER = 1.0` o `0.99`, el caso da rojo con «no pude leer sus productos» y `[] == [3 renglones]`. Sigue distinguiendo el defecto, y el sabotaje de `despacho1b.sh` ya apunta a este caso | — |
| | 2. Nadie más usa `gc.freeze`, `unfreeze`, `disable` ni `collect` en `tests/` o `proyecto_maria/`. Si el lector falla, el `finally` descongela, y después del caso `gc.get_freeze_count()` da 0 | — |
| | 3. Forzó un `gc.collect()` justo antes de `leer_texto`, con 3 M objetos: con el arreglo da verde y sin el arreglo da rojo. Sin forzarlo, le dio verde 4 de 4 con y sin arreglo: el rojo no sale siempre. No verificó mi 3 de 6 | Lo reproduje. Su memoria estaba hecha al arrancar pytest, y así a mí tampoco me sale el rojo (6 de 6 verdes sin arreglo). Hecha justo antes del caso, otra vez 3 de 6 rojos sin arreglo y 6 de 6 verdes con él. Así quedó en «Comandos copiables» |
| | 4. En producción `leer_despacho` corre sólo por `leer_despacho_aparte` (`main.py:8735`), en un `sys.executable -m` aparte. Las llamadas en el mismo proceso son todas de tests | — |
| | 5. Otros hilos del proceso cuentan para `process_time` e `ITIMER_PROF` | Queda, R2. El hilo de `test_despacho1b.py:1019` se espera con `join` y el caso exige que no quede vivo |
| `/code-review high` | #1. Hilos (lo mismo que el 5) | R2 |
| | #2. Correr el caso en el proceso aparte con `_medir_aparte` en vez de congelar | No lo hice. Habría que pasar los 50 ms a `pdf_bombas` por variable de entorno: más código para la misma cobertura. Si lo preferís, es chico |
| | #3. `unfreeze` descongela también lo que congeló otro | Queda, R3. Hoy nadie congela |
| | #4. La basura con ciclos que había al congelar pasa a la generación vieja | Queda. Se libera en la próxima pasada completa, y para eso haría falta un `gc.collect()` que sólo suma tiempo |
| | #5. Reserva mínima para entender el texto | D106, arriba |

## Puertas (sobre `d69233c`)

| Puerta | Salida |
|---|---|
| `tests/test_despacho1b.py` | `283 passed in 50.28s` |
| `chequeo-6.py 9417c3b d69233c` | abajo, `avisos: 0` |
| grep de historia de §6 | vacío |
| Suite completa | **no corrida**. El cambio es un caso y no toca producto. El rojo no sale siempre en la suite, así que una corrida verde no prueba nada: la prueba es el A/B con la memoria cargada |

```
chequeo-6 9417c3b..d69233c: avisos para mirar, no un veredicto
producto +0/−0
arnés +8/−1
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

`producto +0/−0`.

## Riesgos

- **R1, baja.** Otros casos que llamen al lector con un tope chico dentro de pytest podrían tener el mismo problema. Revisé este archivo: `test_un_corte_por_cpu_en_la_primera_hoja_no_dice_que_es_escaneado` sólo pide que corte, y un recolector caro lo hace cortar antes, así que no da falso rojo. `test_el_tope_de_cpu_cubre_entender_el_texto` corre aparte.
- **R2, baja.** `process_time` e `ITIMER_PROF` también cuentan la CPU de otros hilos del proceso. Un hilo vivo que dejara otro caso podría gastar el resto del tope, y `gc.freeze` no cubre eso. Tu prueba con un hilo girando no dio rojo, y no encontré hilos que queden vivos.
- **R3, baja.** `gc.unfreeze` descongela todo. Si algún día un plugin congela memoria al arrancar, este caso se la descongela. Hoy nadie congela.
- D106, arriba.

## Comandos copiables

```bash
# desde la raíz, con el venv del proyecto
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
T=test_las_hojas_leidas_antes_del_corte_dan_sus_productos
# un fixture que, justo antes del caso, deja vivos 3 M dicts con una lista cada uno (6 M objetos).
# Tienen que ser recién creados: hechos al arrancar pytest, el recolector ya los pasó y el rojo no sale
mkdir -p /tmp/lastre && cat > /tmp/lastre/conftest_heap.py <<'E'
import gc, os, pytest
_LASTRE = []
@pytest.fixture(autouse=True)
def _heap_grande():
    n = int(os.environ.get("LASTRE", "0"))
    if n and not _LASTRE:
        _LASTRE.extend([{"a": [i]} for i in range(n)])
    yield
E
git show 9417c3b:tests/test_despacho1b.py > tests/_sin_arreglo_despacho1b.py
for f in _sin_arreglo_despacho1b test_despacho1b; do echo "== $f"; for i in 1 2 3 4 5 6; do rm -f test.db
  PYTHONPATH=/tmp/lastre LASTRE=3000000 python -m pytest -q --no-cov -p no:cacheprovider -W ignore -p conftest_heap \
    "tests/$f.py::$T" 2>&1 | tail -1; done; done
#   → sin arreglo, rojos y verdes mezclados (a mí, tres veces: 3 failed y 3 passed); con arreglo, 6 veces «1 passed»
rm tests/_sin_arreglo_despacho1b.py
python3 docs/pm/herramientas/chequeo-6.py 9417c3b d69233c
#   → producto +0/−0, avisos: 0
```
