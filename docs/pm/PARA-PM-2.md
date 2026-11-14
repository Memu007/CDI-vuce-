# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D250 (a): entregada en `450f4cb`. `sabotaje_maria8.sh` da 39 de 39 en `ROJO`. Una decisión: D251

| qué | SHA |
|---|---|
| base (informe de D249) | `5682f6e` |
| pruebas: la familia en un caso (10 datos) y el sabotaje 39 | `0c836bc` |
| pruebas: 3 datos más, por el adversario 1 | `39fa7aa` |
| pruebas: 3 datos más y el sabotaje 24 con dos datos nombrados, por `/code-review` | `4244a79` |
| pruebas: 1 dato más, por el adversario 2 | `c56b837` |
| pruebas: el ítem vecino, una vuelta mía y dos por el adversario 3 | `08a6024`, `f3aacc7`, `76745e5` |
| pruebas: el vecino con tres renglones, por el adversario 3. **Lo que se entrega** | `450f4cb` |
| tu rama, cuatro veces (hasta `0480d5f`), sólo `docs/pm/` | `a1f7ed6`, `a71217f`, `43def56`, `fb6ac78` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +50/−6`: `tests/test_maria8_subitems_por_posicion.py`
(+42/−4) y `scripts/testing/sabotaje_maria8.sh` (+8/−2). No toqué ningún otro
archivo.

El SHA que entrego pasó por un adversario (su cuarta pasada, abajo).
`/code-review high` corrió sobre `5682f6e..39fa7aa`, no sobre `450f4cb`: lo
digo en «Riesgos», 1.

Las mediciones son sobre `450f4cb`. Tu rama entró después y no toca ninguno de
los dos archivos.

## Decisiones

**D251. Cuatro cambios del producto que la prueba no ve.** Sobre `450f4cb`
medí 47 cambios de las líneas del aviso: 43 dan rojo y 4 quedan en
`61 passed`. Los cuatro también quedan en verde en los 8 archivos de `tests/`
que nombran estos avisos (`1176 passed, 1 xfailed` cada uno).

| cambio | qué vería el despachante |
|---|---|
| `:2225` `_enumerar(list(range(ns[0] + 1, ns[-1] + 2)))` | si van juntos los renglones 1 y 3 y el 2 es de otra posición, los dos avisos dicen «1, 2 y 3» |
| `:2242` `{ns[-1] - ns[0] + 1}` | en ese mismo caso, «los 3 sub-ítems» donde son 2 |
| `:2224` `for ns in juntos[:2]` | con tres ítems agrupados, el tercero se queda sin avisos |
| `:2225` `for n in ns[:4]` | con cinco renglones en un ítem, el aviso nombra cuatro |

Hoy el producto hace lo correcto: con los renglones 1 y 3 juntos y el 2 de
otra posición dice «los renglones 1 y 3» y «los 2 sub-ítems» (lo corrí). Lo
que falta es la prueba que lo fije.

- **(a)** Pieza chica aparte: un dato con renglones salteados (1 y 3 juntos, 2
  de otra posición) para los dos avisos del recorrido. Cubre los dos primeros.
  Los dos topes quedan como límite escrito: a un tope arbitrario siempre se le
  puede poner uno más alto que la prueba.
- **(b)** A la cola de limpieza, sin pieza.
- **(c)** Adentro de D250, como devolución.

Recomiendo **(a)**. Los dos primeros cambian un texto que el despachante lee y
ninguna prueba lo ve. No lo metí en D250 porque el criterio pide las entradas
del aviso (los sufijos), y esto pide cambiar cómo el caso arma los renglones:
tres veces en esta pieza moví el ítem vecino para tapar un agujero y abrí
otro (abajo), así que ese cambio va con su medición propia.

**Supuestos reversibles** (agregué sin que lo pidas; si sobran, se sacan):

1. Se compara el aviso entero, no un pedazo: si cambia la redacción, los 16
   datos dan rojo.
2. Cada dato lleva además un ítem vecino de tres renglones con un solo sufijo,
   y se compara la lista de los dos avisos, en orden. Las filas 31, 32 y 34
   a 42 de la tabla son cambios del recorrido de ítems que quedaban en verde
   hasta que el vecino quedó así.
3. Son 16 datos y no sólo los tres comportamientos que describiste: los
   otros salieron de cambios que quedaban en verde (tabla), míos y de los
   revisores.
4. El sabotaje 24 nombra dos datos (`[heredan]`, `[propios_iguales]`) en vez
   del nombre de la prueba sin dato: desde que es una familia, el nombre solo
   coincide con cualquiera de los 16.

## Qué hay ahora

Un caso, `test_los_avisos_dicen_si_todos_los_subitems_llevan_el_mismo_sufijo`,
con 16 datos: el sufijo propio de cada renglón, el de la operación y lo que el
aviso muestra entre «», o que no sale. El archivo pasa de 46 a 61 pruebas;
`sabotaje_maria8.sh`, de 38 a 39 sabotajes.

| dato | propios | de la operación | el aviso |
|---|---|---|---|
| `heredan` | ninguno (3 renglones) | `AA(MARCA)-` | sale, `AA(MARCA)-` |
| `propios_vacios_heredan` | `""`, `" "`, ninguno | `AA(MARCA)-` | sale, `AA(MARCA)-` |
| `dos_renglones` | ninguno (2) | `AA(MARCA)-` | sale, «1 y 2», «los 2» |
| `cuatro_renglones` | ninguno (4) | `AA(MARCA)-` | sale, «1, 2, 3 y 4», «los 4» |
| `heredan_uno_que_se_limpia` | ninguno | sucio | sale, el limpio |
| `uno_trae_el_limpio_y_el_resto_hereda` | limpio, ninguno, ninguno | sucio | sale, el limpio |
| `propios_iguales` | sucio, limpio, sucio | vacío | sale, el limpio |
| `espacios_al_borde` | `"AA(A) "`, ninguno, ninguno | `" AA(A)\t"` | sale, `AA(A)` |
| `largo` | ninguno | `AA(` + 100 X + `)-` | sale, cortado en 80 |
| `propios_iguales_sin_usar_el_de_la_operacion` | `AA(A)-` los tres | uno que no se separa | sale, `AA(A)-` |
| `solo_el_ultimo_distinto` | `AA(A)-`, `AA(A)-`, `AA(B)-` | `AA(A)-` | no sale |
| `uno_propio_y_el_resto_hereda_otro` | `AA(A)-`, ninguno, ninguno | `AA(B)-` | no sale |
| `uno_propio_y_el_resto_ninguno` | `AA(A)-`, ninguno, ninguno | vacío | no sale |
| `ninguno` | ninguno | vacío | no sale |
| `uno_propio_no_se_separa` | `AA(A)-`, uno que no se separa, `AA(A)-` | `AA(A)-` | no sale |
| `el_de_la_operacion_no_se_separa` | ninguno | uno que no se separa | no sale |

«Sucio» es `AA(MARCA)-AI(620G-BLUE.010 150CMX50M)-` y «limpio»,
`AA(MARCA)-AI(620G BLUE 010 150CMX50M)-`.

Tu criterio:

1. **La familia como datos de un caso:** la tabla de arriba. Diez salen (con
   el texto entero) y seis no.
2. **El sabotaje de la `:2235`:** es el 39, `aviso_operacion_sin_limpiar`. Da
   `ROJO   aviso_operacion_sin_limpiar: 3 failed, 58 passed` y nombra
   `[heredan_uno_que_se_limpia]`, `[uno_trae_el_limpio_y_el_resto_hereda]` y
   `[el_de_la_operacion_no_se_separa]`: los tres efectos que mediste.
3. **`sabotaje_maria8.sh` entero:** 39 líneas `ROJO`, 0 `FALLA`, «OK: los 39
   sabotajes dan rojo por la razón esperada», `rc=0`.
4. **Anclas:** 0, 0 y 0; «está» 2510 (en D249, 2509).

## La base, medida

Con la prueba de `5682f6e`, tu cambio de la `:2235` daba `46 passed`. Con la
de `450f4cb` da `3 failed, 58 passed`.

La tabla trae cada cambio que alguien probó contra el aviso, con lo que daba
la prueba del commit donde se encontró y lo que da ahora. De los 47: 37
pasaron de verde a rojo, 6 ya daban rojo (filas 4, 11, 18, 24, 33 y 43) y 4
siguen en verde (D251). Sin ningún cambio, `61 passed`.

| # | cambio en `maria_generator.py` | quién | antes | en `450f4cb` |
|---|---|---|---|---|
| 1 | `:2235` `or str(sbt_sufijo_valor or "").strip()` (el del criterio; sabotaje 39) | mía | `5682f6e`: `46 passed` | `3 failed, 58 passed` |
| 2 | `:2234` el propio sin limpiar: `str(items[n].get("sufijo") or "").strip()` | mía | `5682f6e`: `46 passed` | `1 failed, 60 passed` |
| 3 | se mira sólo el de la operación (sale la `:2234`) | mía | `5682f6e`: `46 passed` | `12 failed, 49 passed` |
| 4 | se mira sólo el propio (sale la `:2235`) | mía | `5682f6e`: `1 failed, 45 passed` | `8 failed, 53 passed` |
| 5 | `:2240` `== 1` por `>= 1` | mía | `5682f6e`: `46 passed` | `2 failed, 59 passed` |
| 6 | `:2240` sin `and "" not in de_cada_uno` | mía | `5682f6e`: `46 passed` | `1 failed, 60 passed` |
| 7 | `:2243` sin `[:80]` | mía | `5682f6e`: `46 passed` | `1 failed, 60 passed` |
| 8 | `:2243` `[:81]` | mía | `5682f6e`: `46 passed` | `1 failed, 60 passed` |
| 9 | `:2243` `[:79]` | mía | `5682f6e`: `46 passed` | `1 failed, 60 passed` |
| 10 | `:2242` `los 3 sub-ítems` | mía | `5682f6e`: `46 passed` | `2 failed, 59 passed` |
| 11 | `:2242` `{len(ns) + 1}` | mía | `5682f6e`: `1 failed, 45 passed` | `16 failed, 45 passed` |
| 12 | `:2239` `de_cada_uno = {"X"}` | mía | `5682f6e`: `46 passed` | `2 failed, 59 passed` |
| 13 | `:2234` sin `.strip()` | mía | `5682f6e`: `46 passed` | `1 failed, 60 passed` |
| 14 | `:2235` sin `.strip()` | mía | `5682f6e`: `46 passed` | `1 failed, 60 passed` |
| 15 | primero el de la operación y, si está vacío, el propio | mía | `5682f6e`: `46 passed` | `9 failed, 52 passed` |
| 16 | `:2245` `«Otra parte»` por `«Lo que decide el despachante»` | mía | `5682f6e`: `46 passed` | `16 failed, 45 passed` |
| 17 | `:2242` `1, 2 y 3` por `{cuales}` | mía | `5682f6e`: `46 passed` | `16 failed, 45 passed` |
| 18 | `:2234` sin `or ""`: `str(items[n].get("sufijo"))` | mía | `5682f6e`: `1 failed, 45 passed` | `8 failed, 53 passed` |
| 19 | `:2236` `for n in ns[:2]` | adversario 1 | `0c836bc`: `55 passed` | `1 failed, 60 passed` |
| 20 | `:2236` `for n in ns[:-1]` | adversario 1 | `0c836bc`: `55 passed` | `1 failed, 60 passed` |
| 21 | `:2236` `for n in range(len(items))` | adversario 1 | `0c836bc`: `55 passed` | `12 failed, 49 passed` |
| 22 | antes de la `:2233`, `limpiar_sufijo(…)` del de la operación aunque nadie lo herede | adversario 1 | `0c836bc`: `55 passed` | `2 failed, 59 passed` |
| 23 | `:2242` `{min(len(ns), 3)}` | adversario 1 | `0c836bc`: `55 passed` | `1 failed, 60 passed` |
| 24 | `:2240` `== 1` por `<= 1` | adversario 1 | `0c836bc`: `1 failed, 54 passed` | `2 failed, 59 passed` |
| 25 | `:2238` `except KeyError` | mía | `5682f6e`: `46 passed` | `2 failed, 59 passed` |
| 26 | `:2236` `for n in {m for g in juntos for m in g}` | `/code-review` | `39fa7aa`: `57 passed` | `12 failed, 49 passed` |
| 27 | `:2237` el conjunto `- {""}` | `/code-review` | `39fa7aa`: `57 passed` | `1 failed, 60 passed` |
| 28 | el `try` adentro del recorrido de renglones, con `pass` | `/code-review` | `39fa7aa`: `57 passed` | `1 failed, 60 passed` |
| 29 | hereda sólo el renglón cuyo propio es `None` (`""` no hereda) | adversario 2 | `4244a79`: `60 passed` | `1 failed, 60 passed` |
| 30 | hereda sólo el renglón cuyo propio es falso (`" "` no hereda) | adversario 2 | `4244a79`: `60 passed` | `1 failed, 60 passed` |
| 31 | junta los sufijos de cada ítem con los de los ítems anteriores | mía | `c56b837`: `61 passed` | `10 failed, 51 passed` |
| 32 | `:2224` `for ns in juntos[-1:]` | adversario 3 | `08a6024`: `61 passed` | `10 failed, 51 passed` |
| 33 | `:2224` `for ns in juntos[:1]` | adversario 3 | `08a6024`: `10 failed, 51 passed` | `16 failed, 45 passed` |
| 34 | `:2224` `for ns in reversed(juntos)` | adversario 3 | `08a6024`: `61 passed` | `10 failed, 51 passed` |
| 35 | `:2225` `for n in juntos[-1]` | adversario 3 | `08a6024`: `61 passed` | `10 failed, 51 passed` |
| 36 | `:2242` `{len(juntos[-1])}` | adversario 3 | `08a6024`: `61 passed` | `2 failed, 59 passed` |
| 37 | `:2239` `pass` por `de_cada_uno = set()` | adversario 3 | `08a6024`: `61 passed` | `2 failed, 59 passed` |
| 38 | `break` después del aviso | adversario 3 | `08a6024`: `61 passed` | `10 failed, 51 passed` |
| 39 | `else: break` si el ítem no lleva aviso | adversario 3 | `f3aacc7`: `61 passed` | `6 failed, 55 passed` |
| 40 | `elif len(de_cada_uno) > 1: break` | adversario 3 | `f3aacc7`: `61 passed` | `3 failed, 58 passed` |
| 41 | no avisa un sufijo que ya avisó en otro ítem | adversario 3 | `f3aacc7`: `61 passed` | `4 failed, 57 passed` |
| 42 | `:2224` `sorted(juntos, key=len, reverse=True)` | adversario 3 | `76745e5`: `61 passed` | `1 failed, 60 passed` |
| 43 | `:2224` `sorted(juntos, key=len)` | adversario 3 | `76745e5`: `9 failed, 52 passed` | `1 failed, 60 passed` |
| 44 | `:2224` `for ns in juntos[:2]` | adversario 3 | `76745e5`: `61 passed` | **`61 passed`** |
| 45 | `:2225` `for n in ns[:4]` | adversario 3 | no medido antes | **`61 passed`** |
| 46 | `:2225` `_enumerar(list(range(ns[0] + 1, ns[-1] + 2)))` | adversario 3 | no medido antes | **`61 passed`** |
| 47 | `:2242` `{ns[-1] - ns[0] + 1}` | adversario 3 | no medido antes | **`61 passed`** |

Las filas 13 y 14 (sacar un `.strip()`) seguían en `57 passed` en `39fa7aa`:
ahí las marcó `/code-review`. Las filas 45 a 47 no se midieron antes de
`450f4cb`. Las filas 19 a 47 no las medí contra la prueba de `5682f6e`.

Los cuatro verdes, además, contra los 8 archivos que nombran estos avisos
(`test_excel3`, `test_maria8_subitems_por_posicion`, `test_maria9_kilos`,
`test_maria9_sufijo_operacion`, `test_maria_subitems`, `test_orden1`,
`test_sufijos1`, `test_valor1c`): sin cambio y con cada uno,
`1176 passed, 1 xfailed`. Ningún otro `tests/*.py` ni `scripts/testing/*.js`
compara «van en un solo ítem» ni «llevan el mismo sufijo» (grep).

**Dos cosas que afirmé y eran falsas** (medidas después):

- Dije que sacar cualquiera de los dos `.strip()` daba lo mismo. No: con un
  espacio al borde y sin guion final cambia lo que se compara. Fila 13 y 14.
- Dije que juntar los sufijos de un ítem con los del anterior ya estaba
  cubierto de costado. No: en `c56b837` daba `61 passed` (fila 31).

**Tres veces tapé un agujero y abrí otro.** Moví el ítem vecino en
`08a6024` y quedaron 6 cambios en verde; lo arreglé en `f3aacc7` y quedaron 3;
en `76745e5`, 2; en `450f4cb` quedan los 4 de D251. Desde `76745e5` cada
vuelta volvió a medir todos los cambios anotados, no sólo el nuevo.

## Revisión adversarial

| quién | modelo y esfuerzo | sobre | qué encontró | qué pasó |
|---|---|---|---|---|
| adversario 1 | Sonnet, medio | `0c836bc` | filas 19 a 23 (la 24 ya daba rojo) | 3 datos y un renglón de otra posición, `39fa7aa` |
| `/code-review high` | — | `5682f6e..39fa7aa` | 9 hallazgos (abajo) | 5 arreglados en `4244a79`; 4 al informe |
| adversario 2 | Sonnet, medio | `4244a79` | filas 29 y 30 | 1 dato, `c56b837` |
| adversario 3, pasada 1 | `adversario-sonnet-medio` | `08a6024` | filas 32 y 34 a 38 | `f3aacc7` |
| adversario 3, pasada 2 | ídem | `f3aacc7` | filas 39 a 41 | `76745e5` |
| adversario 3, pasada 3 | ídem | `76745e5` | filas 42 y 44 | `450f4cb`; la 44 queda (D251) |
| adversario 3, pasada 4 | ídem | `450f4cb` | filas 45 a 47; nada perdido; el comentario del caso no dice nada falso | D251 |

Los 9 de `/code-review`:

1. Con un solo renglón de otra posición, juntar los renglones de todos los
   ítems agrupados daba verde. Arreglado (fila 26).
2. Faltaba «un propio, el resto ninguno, operación vacía». Arreglado
   (`uno_propio_y_el_resto_ninguno`, fila 27).
3. Ningún dato con espacios al borde. Arreglado (filas 13 y 14).
4. Ningún dato con un sufijo propio que no se separa. Arreglado
   (`uno_propio_no_se_separa`, fila 28).
5. El sabotaje 24 esperaba el nombre de la prueba sin dato. Arreglado
   (supuesto 4).
6. `SUCIO` y `LIMPIO` repiten literales de las pruebas vecinas. Queda: línea
   propuesta para la cola (abajo).
7. La tabla que arma «1, 2 y 3» está escrita a mano para 2, 3 y 4 renglones.
   Queda como límite (riesgo 3). La cuenta ya sale de los datos.
8. `docs/pm/NOW.md:279` dice «anclas 2 y 0» (al lado de D247) y el acta de
   D249 dice 0, 0 y 0. Documento tuyo: no lo toqué, y no sé si es un error o
   un dato de otra pieza.
9. `docs/pm/PARA-DEV-2.md:42` todavía dice «Va después de D249», y la cola
   tiene una línea del `.upper()` que el veredicto de D249 da por riesgo
   aceptado. Documentos tuyos: sólo aviso.

Dos puntos del adversario 3 que no son defectos: su cambio `vistos = set()`
sin usar no cambia nada, y su `except ValueError: continue` hace lo mismo que
el producto.

## Comandos

Corrí cada guion una vez, con la salida a un archivo, y leí las líneas del
archivo. `<venv>` es el entorno virtual.

```bash
env -u DATABASE_URL -u ENVIRONMENT scripts/testing/sabotaje_maria8.sh 450f4cb <venv> > m8.log 2>&1; echo rc=$?   # rc=0
grep -c '^ROJO' m8.log     # 39
grep -c FALLA m8.log       # 0
grep 'sin_aviso_sufijo\|aviso_operacion_sin_limpiar\|^OK' m8.log
#   ROJO   sin_aviso_sufijo: … 16 failed, 45 passed …
#   ROJO   aviso_operacion_sin_limpiar: … 3 failed, 58 passed …
#   OK: los 39 sabotajes dan rojo por la razón esperada
<venv>/bin/python scripts/testing/anclas_perdidas.py 450f4cb | head -4      # 0, 0 y 0
<venv>/bin/python docs/pm/herramientas/chequeo-6.py 5682f6e 450f4cb         # avisos: 0
```

El primer verde de D251 (lo corrí como está, con el worktree en mi carpeta
temporal en vez de `/tmp` y `PY=<venv>/bin/python`):

```bash
git worktree add -q --detach /tmp/d251 450f4cb && cd /tmp/d251
$PY - <<'PYEOF'
f = "proyecto_maria/core/maria_generator.py"; s = open(f, encoding="utf-8").read()
v = "cuales = _enumerar([n + 1 for n in ns])"; assert s.count(v) == 1
open(f, "w", encoding="utf-8").write(s.replace(v, "cuales = _enumerar(list(range(ns[0] + 1, ns[-1] + 2)))"))
PYEOF
env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake $PY -m pytest -q --no-cov -p no:cacheprovider --timeout=120 tests/test_maria8_subitems_por_posicion.py | tail -1   # 61 passed
cd - && git worktree remove --force /tmp/d251
```

## Puertas

Sobre `450f4cb`.

| puerta | resultado |
|---|---|
| `tests/test_maria8_subitems_por_posicion.py` | `61 passed` |
| `sabotaje_maria8.sh 450f4cb` | `VERDE  sin sabotaje: … 61 passed`; 39 `ROJO`, 0 `FALLA`; «OK: los 39 sabotajes dan rojo por la razón esperada»; `rc=0` |
| sabotaje 24, `sin_aviso_sufijo` | `16 failed, 45 passed` |
| sabotaje 39, `aviso_operacion_sin_limpiar` | `3 failed, 58 passed` |
| `anclas_perdidas.py 450f4cb` | `103 guiones, 2510 anclas medidas y 11 llamadas sin medir`; perdida una línea 0, varias líneas 0, otra cantidad 0; no medido 5 (guiones: 2); sin ancla 6 (guiones: 1); está 2510 (guiones: 101) |
| `bash -n scripts/testing/sabotaje_maria8.sh` | `rc=0` |
| los 8 archivos que nombran estos avisos | `1176 passed, 1 xfailed` |

**No corrido:** la suite entera, `-k 'sufijo or maria'` sobre `tests/`,
`compileall` (no hay producto), pantallas, e2e, smoke, ataque de aislamiento,
Postgres, los otros guiones de sabotaje y `/security-review` (no hay
producto).

## `chequeo-6`

```
chequeo-6 5682f6e..450f4cb: avisos para mirar, no un veredicto
producto +0/−0
arnés +50/−6
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

1. **`/code-review high` no corrió sobre el SHA que entrego.** Corrió sobre
   `5682f6e..39fa7aa`. Los seis commits de después tocan los mismos dos
   archivos y pasaron por adversarios (el último, `450f4cb`, por la cuarta
   pasada del adversario 3). Si tu regla «desde D250 se corre siempre» pide
   el SHA final, devolvelo y lo corro.
2. **Los cuatro verdes de D251.** Medidos; no los cubre ninguna prueba que
   nombre estos avisos.
3. **La tabla de renglones del caso** («1 y 2», «1, 2 y 3», «1, 2, 3 y 4»)
   está a mano: un dato con otra cantidad de renglones da `KeyError`, a la
   vista.
4. **El orden por tamaño** (filas 42 y 43) lo atrapa un solo dato cada uno:
   `dos_renglones` en un sentido y `cuatro_renglones` en el otro.
5. Los guiones con que medí (`mut.py`, `medir.sh`, `medir8.sh`, `tabla.py`)
   están en mi carpeta temporal, no en el repositorio.

**Líneas que propongo para la cola de limpieza:**

- `tests/test_maria8_subitems_por_posicion.py`: los literales del sufijo sucio
  y del limpio siguen escritos a mano en las líneas 235, 237, 403 y 406;
  usar `SUCIO` y `LIMPIO`.
- El aviso «Sub-ítems: los renglones … van en un solo ítem» se mira con un
  solo ítem agrupado y por un pedazo del texto
  (`test_los_avisos_dicen_que_renglones_van_juntos`). Leído, no medido.

## Archivos de producto que toqué

Ninguno.

## Sigo con

Nada asignado después de D250. D251 espera tu respuesta. D244, D239 y
«Holanda» esperan a Emi: no los toco.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `0480d5f`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`, D247 (a) sobre `4a58c68`, D248 (c) sobre `3fcc9c4`, los vencidos `sabotaje_maria1d.sh` sobre `6e4e658`, `sabotaje_maria5.sh` sobre `c0505cc`, `sabotaje_valor1b.sh` sobre `70eb5dc`, `sabotaje_doc1.py` sobre `d4c6b73` `sabotaje_maria7.sh` sobre `4477ae3` y `sabotajes/guardar2.sh` sobre `aeb994f` (no queda ningún vencido) y D249 (a) sobre `50dabfa`. Entregada sin veredicto: **D250 (a) sobre `450f4cb`** (base `5682f6e`; sólo `tests/test_maria8_subitems_por_posicion.py`, de 46 a 61 pruebas, un caso con 16 datos, y `scripts/testing/sabotaje_maria8.sh`, de 38 a 39 sabotajes; arnés +50/−6; 39 `ROJO`, el 39 `aviso_operacion_sin_limpiar` da `3 failed, 58 passed` y el 24 `16 failed, 45 passed`; anclas 0, 0 y 0, «está» 2510; 47 cambios medidos, 43 rojos y 4 verdes; `/code-review high` corrió sobre `5682f6e..39fa7aa` y no sobre el SHA final, dicho como riesgo 1; tres adversarios Sonnet medio, el tercero cuatro pasadas). Si vuelve con devolución, va primero. **D251 abierta, mía, espera a la PM:** cuatro cambios de `maria_generator.py` que quedan en `61 passed` (`:2225` renglones de corrido, `:2242` cuenta por extremos, `:2224` tope de dos ítems, `:2225` tope de cuatro renglones), también en los 8 archivos que nombran los avisos (`1176 passed, 1 xfailed`); opciones (a) pieza chica con un dato de renglones salteados, (b) cola, (c) devolución adentro de D250; recomendé (a). **Sin pieza activa:** nada asignado después de D250; las mediciones están en mi carpeta temporal `d250/` (`mano11.txt`, `ocho.txt`, `tabla.md`). D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D252. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga, y su porqué se comprueba con `git show`, no se supone; que «nadie cubría» algo se mide antes de escribirlo, y con todas las pruebas que usan ese dato, no sólo las del guion (un adversario que corre cuatro archivos dice «hueco» donde otra prueba lo atrapa); `anclas_perdidas.py` mide un commit: el arreglo se commitea antes de medir; el SHA que se entrega pasa por subagente o `/code-review`, y si el gancho de parada ya subió el commit, lo que siga va en un commit nuevo; después de un commit nuevo o de corregir uno, las puertas corren otra vez sobre ese SHA; un ancla lleva sólo el texto que saca más lo mínimo que la ata a su lugar; la cuenta escrita a mano en el último `echo` de un guion se compara con sus líneas `ROJO`; una mutación se mide a mano con el archivo de pruebas entero, para ver que pone en rojo sólo lo suyo y por aserción; `anclas_perdidas.py` sólo lee los `.sh`; un worktree que aparece en `git worktree list` mientras corre un guion mío es de ese guion, no un resto; una espera de 110 vueltas de 5 s no alcanza para tres corridas de 4 minutos: se vuelve a esperar la marca de fin, no se relanza; mientras haya una D mía sin contestar, el informe siguiente la repite arriba; el dato que fija «qué pedazo se muestra» no tiene ese pedazo al principio de donde sale, o cortar el todo da lo mismo; `sabotaje_sufijos1.sh` recibe el venv como segundo argumento, no por `PY`; un riesgo que diría «cubierto» se mide antes de escribirlo; mover un dato para tapar un agujero se mide de los dos lados, con todos los cambios anotados otra vez; un ítem vecino en un caso de avisos lleva su propio aviso, o el recorrido de ítems queda sin mirar; el criterio para dejar de iterar se dice y se sostiene, y lo que queda va como D; regla de la PM: desde D250 `/code-review` se corre siempre, aunque sea sólo arnés; regla de la PM: en un vencido de sólo arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice, cualquier otro cambio sí. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
