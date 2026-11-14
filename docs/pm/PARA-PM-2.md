# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D251 (a): entregada en `9d580db`. `sabotaje_maria8.sh` da 43 de 43 en `ROJO`. Tres decisiones: D252, D253 y D254

| qué | SHA |
|---|---|
| base (informe de D250) | `01bc9df` |
| tu rama hasta `e41d2ea`, sólo `docs/pm/` y `.claude/` | `2b1a2da` |
| pruebas: renglones salteados, tres ítems y doce renglones; sabotajes 40 a 43 | `bd15730` |
| pruebas: los avisos en su orden y un dato de doce renglones, por el adversario 1 | `6ef4e62` |
| pruebas: de doce renglones, uno distinto en cada puesto, por el adversario 2 | `2032376` |
| pruebas: el aviso de los sub-ítems con cada renglón con su sufijo, por `/code-review` | `f87f776` |
| pruebas: ese aviso también en el caso del mismo sufijo, por el adversario 3. **Lo que se entrega** | `9d580db` |
| tu rama hasta `2fb54d0`, sólo `docs/pm/` | `471dd97` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +78/−14`: `tests/test_maria8_subitems_por_posicion.py`
(+59/−12) y `scripts/testing/sabotaje_maria8.sh` (+19/−2). No toqué ningún otro
archivo.

`/code-review high` corrió dos veces: sobre `01bc9df..2032376` y sobre
`01bc9df..9d580db`, el SHA que entrego. De la segunda no salió ningún commit.
`9d580db` pasó además por un adversario (el 4, abajo).

Las mediciones son sobre `9d580db`. Tu rama entró después y no toca ninguno de
los dos archivos.

## Decisiones

Sobre `9d580db` medí 99 cambios de las líneas de estos avisos: 82 dan rojo y
17 quedan en `77 passed`. Los 17 también quedan en verde contra el conjunto
ancho (`2320 passed, 1 xfailed` cada uno; qué archivos, abajo). Los reparto en
tres decisiones.

**D252. La lista de renglones de cada ítem tiene tres usos más que D251 no
nombra, y ninguna prueba los fija.** Tu texto dice «Esa lista la usan los dos
avisos». La usan además: el aviso de cada renglón, «Sufijo de valor del
renglón N: …» (`maria_generator.py:2230-2231`), y los dos conjuntos
`en_renglones` (`:2187` y `:1953`), que deciden si un renglón se nombra como
renglón de un ítem o como ítem suelto. Es la misma causa de D251: la única
prueba del aviso de cada renglón usa dos renglones seguidos. Filas 22, 34 a
37 y 52 a 54 de la tabla.

| cambio | qué vería el despachante |
|---|---|
| `:2231` `del renglón {ns.index(n) + 1}` (fila 22) | renglones de posición A, B, A y el sufijo del 3 mal escrito: el aviso dice «del renglón 2» |
| `:2230` `for n in ns[:4]` (fila 34) | cinco renglones en un ítem y el sufijo del 5 mal escrito: el aviso de ese renglón no sale |
| `:2230` `for n in range(ns[0], ns[-1] + 1)` (fila 35) | A, B, A y el sufijo del 2 mal escrito: su aviso sale dos veces, «del ítem 2» y «del renglón 2» |
| `:2187` `en_renglones` de corrido (fila 36) | ese mismo caso: el aviso del renglón 2 no sale |
| `:1953` ídem (fila 37) | en esas tres entradas no cambia nada. Por lectura, hace falta un renglón con `grupo_id` entre los de un ítem: no lo medí |
| `:2230` `ns[:2]`, `ns[1:2]`, `range(ns[0], ns[0] + len(ns))` (filas 52 a 54) | no medido en pantalla; por lectura, lo mismo que las filas 34 y 35 |

Las cuatro primeras filas están medidas sobre la lista de avisos que devuelve
`supuestos_declarados` (no abrí el navegador). Hoy el producto hace lo
correcto en las tres entradas: lo corrí.

- **(a)** Pieza chica aparte: el caso del aviso de cada renglón pasa a datos
  (renglón salteado, quinto renglón, renglón de otro ítem en el medio) y los
  cambios van a `sabotaje_maria8.sh`. La `:1953` se mide primero: si ninguna
  entrada real la distingue, queda como límite escrito.
- **(b)** Sólo el aviso de cada renglón (`:2230-2231`); los dos `en_renglones`
  quedan como límite.
- **(c)** Queda como límite escrito, sin pieza.

Recomiendo **(a)**. Ese aviso le dice al despachante en qué renglón se
corrigió un sufijo: si nombra otro renglón o no sale, corrige el que no es o
no se entera, y ninguna prueba lo ve. No lo metí en D251 porque tu criterio
nombra dos avisos y esto cambia un tercer caso.

**D253. Tres topes que quedan uno arriba de los datos.** Filas 10, 55 y 56:
`juntos[:3]` (los datos tienen tres ítems como mucho), `ns[:12]` y
`min(len(ns), 12)` (doce renglones como mucho).

- **(a)** Queda como límite escrito.
- **(b)** Un dato de cuatro ítems (`ABCDABCD`). Cierra `juntos[:3]` y deja
  abierto `juntos[:4]`.

Recomiendo **(a)**: a un tope arbitrario siempre se le puede poner otro más
alto que la prueba. Tu criterio pide «tres grupos o más» y «cinco renglones o
más», y los datos tienen tres y doce.

**D254. Seis cambios del adversario 4 que quedan en verde.** Filas 46 a 51.
Cinco le agregan una condición inventada al aviso «Sub-ítems: los renglones …
van en un solo ítem» (que no salga si un sufijo propio pasa de 80 caracteres,
si no es texto, si el de la operación es `None`, o si el del primer o el del
último renglón no se separa). El sexto cambia el orden con tres ítems cuando
el del medio no lleva el aviso del mismo sufijo. Leídos, no medidos en
pantalla.

- **(a)** Queda como límite escrito.
- **(b)** Una pieza más con unos seis datos.

Recomiendo **(a)**. Corrí cuatro rondas de adversario y cada una encontró
condiciones nuevas de este tipo: no es un agujero que se cierre con seis datos
más. El error que alguien sí cometería (meter el aviso de los sub-ítems
adentro del `try` del otro) da rojo: `2 failed, 75 passed`. Y con un sufijo
que no se separa el generador corta con un error que nombra el renglón (lo
corrí: «Sufijo de valor del renglón 2: «AA(» no se puede separar en
códigos…»). El adversario 4 lo dijo
así: «ninguna es un defecto de `9d580db`».

**Supuestos reversibles** (agregué sin que lo pidas; si sobran, se sacan):

1. `JUNTOS` lleva doce renglones y no cinco: con cinco, un tope de cinco a
   once quedaba en verde (filas 13 y 14).
2. `cuatro_renglones` pasó a `cinco_renglones`, y hay doce datos
   `de_doce_solo_el_N_distinto`, uno por puesto: sin ellos, comparar sólo
   algunos renglones del ítem quedaba en verde (filas 19 a 29).
3. Los textos enteros de los dos avisos están en dos ayudantes
   (`_aviso_de_que_van_juntos`, `_aviso_del_mismo_sufijo`) y los renglones los
   arma `_dichos`, no el producto: lo esperado no sale de lo que se prueba.
4. Los dos casos comparan la lista de los dos avisos de cada ítem, en orden.
   Por eso se pisan: el sabotaje 23 pone en rojo 34 pruebas y el 24, 33. La
   alternativa es una sola tabla con un caso; no la hice porque tu criterio
   pide los datos «en los casos que ya existen».
5. `JUNTOS` tiene un tercer campo y el dato `cada_renglon_su_sufijo`: fija que
   el aviso de los sub-ítems sale aunque cada renglón lleve su sufijo (fila
   33).
6. El sabotaje 23 nombra dos datos (`[seguidos]`, `[doce_renglones]`) en vez
   del nombre de la prueba sin dato.
7. Los sabotajes 40 y 41 esperan los mismos dos datos (`[salteados]`,
   `[tres_items]`): riesgo 2.

## Qué hay ahora

El archivo pasa de 61 a 77 pruebas; `sabotaje_maria8.sh`, de 39 a 43
sabotajes.

`test_los_avisos_dicen_que_renglones_van_juntos` pasa de una prueba a un caso
con 5 datos. Compara los dos avisos de cada ítem, con el texto entero:

| dato | posición de cada renglón | lo que dicen los avisos |
|---|---|---|
| `seguidos` | A, A, A, B | «1, 2 y 3» |
| `salteados` | A, B, A | «1 y 3», 2 sub-ítems |
| `tres_items` | A, B, C, C, A, B | «1 y 5», «2 y 6», «3 y 4» |
| `doce_renglones` | doce A | «1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 y 12» |
| `cada_renglon_su_sufijo` | A, B, A, B; los de B con sufijo distinto | de A los dos avisos; de B sólo el de los sub-ítems |

`test_los_avisos_dicen_si_todos_los_subitems_llevan_el_mismo_sufijo` pasa de
16 datos a 28: los 16 de D250 (con `cinco_renglones` en lugar de
`cuatro_renglones`) y los doce `de_doce_solo_el_N_distinto`. Ahora compara
también el aviso de los sub-ítems de los dos ítems.

Tu criterio:

1. **Los dos avisos con su texto entero:** renglones salteados (`salteados`,
   `tres_items`, `cada_renglon_su_sufijo`), tres ítems (`tres_items`) y un
   ítem de cinco renglones o más (`doce_renglones`, `cinco_renglones` y los
   doce de doce).
2. **La tabla de renglones no se escribe a mano:** la arma `_dichos`.
   `cinco_renglones` pasa; no hay `KeyError` posible porque ya no hay tabla.
3. **Tus cuatro mutaciones en `sabotaje_maria8.sh`:**
   - 40, `renglones_de_corrido`: `3 failed, 74 passed`; nombra `[salteados]` y
     `[tres_items]`.
   - 41, `cuenta_por_extremos`: `3 failed, 74 passed`; los mismos dos.
   - 42, `tope_dos_items`: `1 failed, 76 passed`; nombra `[tres_items]`.
   - 43, `renglones_tope_4`: `14 failed, 63 passed`; nombra
     `[doce_renglones]` y `[cinco_renglones]`.
4. **El guion entero:** 43 líneas `ROJO`, 0 `FALLA`, «OK: los 43 sabotajes dan
   rojo por la razón esperada», `rc=0`. **Anclas:** 0, 0 y 0; «está» 2514 (en
   D250, 2510). **`/code-review high`:** hasta `9d580db`.

## La base, medida

Con la prueba de `01bc9df`, tus cuatro cambios daban `61 passed` cada uno. Con
la de `9d580db` dan rojo (filas 1 a 4).

La tabla trae cada cambio nuevo que alguien probó contra estos avisos, con lo
que daba la prueba del commit donde se encontró y lo que da ahora. De los 56:
30 pasaron de verde a rojo, 9 ya daban rojo (filas 6, 11, 15 a 18 y 30 a 32) y
17 siguen en verde (D252, D253 y D254). Los otros 43 cambios, los del informe
de D250 menos tus cuatro, siguen todos en rojo. Sin ningún cambio,
`77 passed`.

| # | cambio en `maria_generator.py` | quién | antes | en `9d580db` |
|---|---|---|---|---|
| 1 | `:2225` `_enumerar(list(range(ns[0] + 1, ns[-1] + 2)))` (sabotaje 40) | del criterio | `01bc9df`: `61 passed` | `3 failed, 74 passed` |
| 2 | `:2242` `{ns[-1] - ns[0] + 1}` (sabotaje 41) | del criterio | `01bc9df`: `61 passed` | `3 failed, 74 passed` |
| 3 | `:2224` `for ns in juntos[:2]` (sabotaje 42) | del criterio | `01bc9df`: `61 passed` | `1 failed, 76 passed` |
| 4 | `:2225` `for n in ns[:4]` (sabotaje 43) | del criterio | `01bc9df`: `61 passed` | `14 failed, 63 passed` |
| 5 | `:2227` `con {ns[-1] - ns[0] + 1} sub-ítems` | mía | `01bc9df`: `61 passed` | `3 failed, 74 passed` |
| 6 | `:2227` `con 2 sub-ítems` | mía | `01bc9df`: `1 failed, 60 passed` | `30 failed, 47 passed` |
| 7 | `:2236` se comparan los sufijos de `range(ns[0], ns[-1] + 1)` | mía | `01bc9df`: `61 passed` | `3 failed, 74 passed` |
| 8 | `:2242` los renglones de corrido sólo en el aviso del mismo sufijo | mía | `01bc9df`: `61 passed` | `3 failed, 74 passed` |
| 9 | `:2227` los renglones de corrido sólo en el aviso de los sub-ítems | mía | `01bc9df`: `61 passed` | `3 failed, 74 passed` |
| 10 | `:2224` `for ns in juntos[:3]` | mía | `01bc9df`: `61 passed` | **`77 passed`** |
| 11 | `:2224` `for ns in juntos[1:]` | mía | `01bc9df`: `12 failed, 49 passed` | `34 failed, 43 passed` |
| 12 | `:2224` `sorted(juntos, key=lambda g: g[-1])` | mía | `01bc9df`: `61 passed` | `1 failed, 76 passed` |
| 13 | `:2225` `for n in ns[:5]` | mía | `01bc9df`: `61 passed` | `13 failed, 64 passed` |
| 14 | `:2225` `for n in ns[:11]` | mía | `01bc9df`: `61 passed` | `13 failed, 64 passed` |
| 15 | `:2225` `[n for n in ns]` | mía | `01bc9df`: `17 failed, 44 passed` | `33 failed, 44 passed` |
| 16 | `:942` `_enumerar` une todo con coma | mía | `01bc9df`: `17 failed, 44 passed` | `33 failed, 44 passed` |
| 17 | `:942` `_enumerar` une todo con « y » | mía | `01bc9df`: `17 failed, 44 passed` | `30 failed, 47 passed` |
| 18 | `:942` `_enumerar` pone «, y » antes del último | mía | `01bc9df`: `17 failed, 44 passed` | `33 failed, 44 passed` |
| 19 | `:2236` compara los sufijos de `ns[:4]` | adversario 1 | `bd15730`: `64 passed` | `8 failed, 69 passed` |
| 20 | `:2236` compara los de `ns[:5]` | adversario 1 | `bd15730`: `64 passed` | `7 failed, 70 passed` |
| 21 | `:2236` compara los de `ns[:11]` | adversario 1 | `bd15730`: `64 passed` | `1 failed, 76 passed` |
| 22 | `:2231` `del renglón {ns.index(n) + 1}` | adversario 1 | `bd15730`: `64 passed` | **`77 passed`** |
| 23 | los avisos del mismo sufijo salen todos juntos, después del último ítem | adversario 1 | `bd15730`: `64 passed` | `12 failed, 65 passed` |
| 24 | `:2236` compara `ns[:2] + ns[-1:]` | adversario 2 | `6ef4e62`: `65 passed` | `9 failed, 68 passed` |
| 25 | `:2236` compara `ns[:3] + ns[-1:]` | adversario 2 | `6ef4e62`: `65 passed` | `8 failed, 69 passed` |
| 26 | `:2236` compara `ns[:4] + ns[-1:]` | adversario 2 | `6ef4e62`: `65 passed` | `7 failed, 70 passed` |
| 27 | `:2236` compara `ns[:2] + ns[-2:]` | adversario 2 | `6ef4e62`: `65 passed` | `8 failed, 69 passed` |
| 28 | `:2236` compara `ns[:5] + ns[6:]` | adversario 2 | `6ef4e62`: `65 passed` | `1 failed, 76 passed` |
| 29 | `:2236` compara `ns[:3] + ns[4:]` | adversario 2 | `6ef4e62`: `65 passed` | `1 failed, 76 passed` |
| 30 | `:2236` compara `ns[1:]` | adversario 2 | `6ef4e62`: `1 failed, 64 passed` | `3 failed, 74 passed` |
| 31 | `:2236` compara `ns[::2]` | adversario 2 | `6ef4e62`: `2 failed, 63 passed` | `8 failed, 69 passed` |
| 32 | `:2236` compara `ns[1::2]` | adversario 2 | `6ef4e62`: `2 failed, 63 passed` | `9 failed, 68 passed` |
| 33 | `:2226` el aviso de los sub-ítems sale sólo si los renglones traen el mismo sufijo propio | `/code-review` | `2032376`: `76 passed` | `21 failed, 56 passed` |
| 34 | `:2230` `for n in ns[:4]` | `/code-review` | `2032376`: `76 passed` | **`77 passed`** |
| 35 | `:2230` `for n in range(ns[0], ns[-1] + 1)` | `/code-review` | `2032376`: `76 passed` | **`77 passed`** |
| 36 | `:2187` `en_renglones` con `range(ns[0], ns[-1] + 1)` | `/code-review` | `2032376`: `76 passed` | **`77 passed`** |
| 37 | `:1953` ídem | `/code-review` | `2032376`: `76 passed` | **`77 passed`** |
| 38 | `:2226` el de los sub-ítems sale sólo si todos traen sufijo propio | adversario 3 | `f87f776`: `77 passed` | `12 failed, 65 passed` |
| 39 | `:2226` sólo si alguno trae sufijo propio | adversario 3 | `f87f776`: `77 passed` | `8 failed, 69 passed` |
| 40 | `:2226` sólo si el primero trae sufijo propio | adversario 3 | `f87f776`: `77 passed` | `8 failed, 69 passed` |
| 41 | `:2226` sólo si el último trae sufijo propio | adversario 3 | `f87f776`: `77 passed` | `12 failed, 65 passed` |
| 42 | `:2226` sólo si algún propio no es igual al de la operación | adversario 3 | `f87f776`: `77 passed` | `5 failed, 72 passed` |
| 43 | `:2226` sólo si ningún propio es igual al de la operación | adversario 3 | `f87f776`: `77 passed` | `21 failed, 56 passed` |
| 44 | el de los sub-ítems de un ítem sin aviso del mismo sufijo sale al final de todo | adversario 3 | `f87f776`: `77 passed` | `18 failed, 59 passed` |
| 45 | después de un ítem sin aviso del mismo sufijo, los de los sub-ítems salen al final | adversario 3 | `f87f776`: `77 passed` | `18 failed, 59 passed` |
| 46 | `:2226` el de los sub-ítems no sale si un sufijo propio pasa de 80 caracteres | adversario 4 | `9d580db`: `77 passed` | **`77 passed`** |
| 47 | `:2226` no sale si un sufijo propio no es texto | adversario 4 | `9d580db`: `77 passed` | **`77 passed`** |
| 48 | `:2226` no sale si el sufijo de la operación es `None` | adversario 4 | `9d580db`: `77 passed` | **`77 passed`** |
| 49 | `:2226` no sale si el sufijo del primer renglón no se separa | adversario 4 | `9d580db`: `77 passed` | **`77 passed`** |
| 50 | `:2226` no sale si el del último renglón no se separa | adversario 4 | `9d580db`: `77 passed` | **`77 passed`** |
| 51 | con tres ítems, el de los sub-ítems del ítem del medio sin aviso del mismo sufijo sale primero de todo | adversario 4 | `9d580db`: `77 passed` | **`77 passed`** |
| 52 | `:2230` `for n in ns[:2]` | `/code-review`, segunda | `9d580db`: `77 passed` | **`77 passed`** |
| 53 | `:2230` `for n in ns[1:2]` | `/code-review`, segunda | `9d580db`: `77 passed` | **`77 passed`** |
| 54 | `:2230` `for n in range(ns[0], ns[0] + len(ns))` | `/code-review`, segunda | `9d580db`: `77 passed` | **`77 passed`** |
| 55 | `:2225` `for n in ns[:12]` | `/code-review`, segunda | `9d580db`: `77 passed` | **`77 passed`** |
| 56 | `:2242` `{min(len(ns), 12)}` | `/code-review`, segunda | `9d580db`: `77 passed` | **`77 passed`** |

La fila 33 es un agujero que abrí yo: con la prueba de `01bc9df` ese cambio
daba `1 failed, 60 passed`, y con la de `2032376`, `76 passed`. Lo encontró
`/code-review` y lo cerré en `f87f776`.

Los 17 verdes, además, contra el conjunto ancho (`tests/test_maria*.py`,
`tests/test_sufijo*.py`, `tests/test_avisos*.py`, `tests/test_excel3.py`,
`tests/test_orden1.py` y `tests/test_valor1c.py`): sin cambio y con cada uno,
`2320 passed, 1 xfailed`.

**Tres cosas que hice mal y corregí antes de entregar:**

- `bd15730` le sacó a la prueba algo que la base miraba (fila 33).
- Había decidido entregar con `/code-review` sólo hasta `2032376`. Tu criterio
  4 pide el SHA que entrego: lo corrí otra vez hasta `9d580db`.
- La primera medición «en pantalla» de la fila 37 mostraba el resultado del
  cambio anterior: dos cambios del mismo tamaño aplicados en el mismo segundo
  comparten el `.pyc`. Borré el `.pyc`, corrí con `python -B` y la tabla de
  D252 sale de esa segunda corrida. Las mediciones de la tabla grande no
  tienen ese problema: cada una tarda más de cinco segundos.

**Cuándo paré.** Cada ronda de revisión encontró cambios en verde: 5 el
adversario 1, 6 el adversario 2, 5 la primera `/code-review` (más la fila 10,
que yo ya tenía anotada), 8 el adversario 3. Los
cerré todos menos las filas 10, 22 y 34 a 37. La ronda sobre `9d580db`
(adversario 4 y segunda `/code-review`) encontró 11 más y ninguno es un
defecto del commit ni está en tu criterio: paré ahí y van como D. Cada vuelta
volvió a medir todos los cambios anotados, no sólo el nuevo.

## Revisión adversarial

| quién | modelo y esfuerzo | sobre | qué encontró | qué pasó |
|---|---|---|---|---|
| adversario 1 | Sonnet, alto | `bd15730` | filas 19 a 23 | `6ef4e62`; la 22 queda (D252) |
| adversario 2 | Sonnet, alto | `6ef4e62` | filas 24 a 29 (las 30 a 32 ya daban rojo) | `2032376` |
| `/code-review high` | — | `01bc9df..2032376` | 8 hallazgos (abajo) | 2 arreglados en `f87f776`; 6 al informe |
| adversario 3 | `adversario-sonnet-alto` | `f87f776` | filas 38 a 45 | `9d580db` |
| adversario 4 | `adversario-sonnet-alto` | `9d580db` | el commit hace lo que dice y no afloja nada; filas 46 a 51 | D254 |
| `/code-review high`, segunda | — | `01bc9df..9d580db` | 9 hallazgos (abajo) | ningún commit; al informe |

Los 8 de la primera `/code-review`:

1. `JUNTOS` le daba el mismo sufijo a todos los renglones de una posición:
   nada miraba que el aviso de los sub-ítems saliera con sufijos distintos.
   Arreglado (`cada_renglon_su_sufijo`, fila 33).
2. El aviso de cada renglón (`:2230`) sólo se prueba con dos renglones
   seguidos. D252 (filas 34 y 35).
3. Los dos `en_renglones` (`:2187`, `:1953`) no se miran con un renglón de
   otro ítem en el medio. D252 (filas 36 y 37).
4. `juntos[:3]` queda en verde. D253 (fila 10).
5. `.claude/skills/entregar/SKILL.md:28`: no dice si `/code-review` se corre
   otra vez después de un commit que nace de sus hallazgos. Documento tuyo:
   sólo aviso. Yo lo leí como «sí» y la corrí otra vez.
6. La línea 300 de la cola cita líneas del archivo de pruebas que se movieron.
   Línea propuesta para la cola (abajo).
7. `_dichos` tenía una rama que nadie usaba. Arreglado.
8. El número del último `echo` del guion se cambió a mano otra vez (39 → 43) y
   la línea 273 de la cola todavía dice `38`. Línea propuesta (abajo).

Los 9 de la segunda:

1. El aviso de cada renglón, otra vez, con tres cambios más. D252 (filas 52 a
   54).
2. `docs/pm/NOW.md:279`: la línea `/compact conservar` dice a la vez «run6 y
   run7 cerradas» y «al FIN de run6». Documento tuyo: sólo aviso; sigue así
   en `2fb54d0`.
3. `SKILL.md:28`, lo mismo que el 5 de arriba; la línea 29 quedó sin cortar.
4. Los sabotajes 40 y 41 esperan los mismos dos datos. No es un defecto (cada
   sabotaje aplica un solo cambio); es un límite: riesgo 2.
5. Los datos están justo en el tope que prueban. D253 (filas 55 y 56).
6. La línea 300 de la cola, lo mismo que el 6 de arriba: ahora los literales
   están en las líneas 235, 237, 450 y 453.
7. Los dos casos afirman lo mismo y se pisan. Supuesto 4.
8. `_dichos` con un solo número da « y 1» y repite lo que hace `_enumerar`.
   No hay dato de un renglón (un ítem de un renglón no lleva estos avisos) y
   la repetición es a propósito (supuesto 3). Queda.
9. El acta de D250 tenía una fila «todavía corre». Tu commit `1555917` la
   llenó; ya está en mi rama.

## Comandos

Corrí cada guion una vez, con la salida a un archivo, y leí las líneas del
archivo. `<venv>` es el entorno virtual.

```bash
env -u DATABASE_URL -u ENVIRONMENT scripts/testing/sabotaje_maria8.sh 9d580db <venv> > m8.log 2>&1; echo rc=$?   # rc=0
grep -c '^ROJO' m8.log     # 43
grep -c FALLA m8.log       # 0
grep 'renglones_de_corrido\|cuenta_por_extremos\|tope_dos_items\|renglones_tope_4\|^OK' m8.log
#   ROJO   renglones_de_corrido: … 3 failed, 74 passed …
#   ROJO   cuenta_por_extremos: … 3 failed, 74 passed …
#   ROJO   tope_dos_items: … 1 failed, 76 passed …
#   ROJO   renglones_tope_4: … 14 failed, 63 passed …
#   OK: los 43 sabotajes dan rojo por la razón esperada
<venv>/bin/python scripts/testing/anclas_perdidas.py 9d580db | head -4      # 0, 0 y 0
<venv>/bin/python docs/pm/herramientas/chequeo-6.py 01bc9df 9d580db         # avisos: 0
```

El primer verde de D252 (lo corrí como está, con el worktree en mi carpeta
temporal en vez de `/tmp` y `PY=<venv>/bin/python`):

```bash
git worktree add -q --detach /tmp/d252 9d580db && cd /tmp/d252
$PY - <<'PYEOF'
f = "proyecto_maria/core/maria_generator.py"; s = open(f, encoding="utf-8").read()
v = 'f" del renglón {n + 1}"'; assert s.count(v) == 1
open(f, "w", encoding="utf-8").write(s.replace(v, 'f" del renglón {ns.index(n) + 1}"'))
PYEOF
env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake $PY -m pytest -q --no-cov -p no:cacheprovider --timeout=120 tests/test_maria8_subitems_por_posicion.py | tail -1   # 77 passed
cd - && git worktree remove --force /tmp/d252
```

## Puertas

Sobre `9d580db`.

| puerta | resultado |
|---|---|
| `tests/test_maria8_subitems_por_posicion.py` | `77 passed` |
| `sabotaje_maria8.sh 9d580db` | `VERDE  sin sabotaje: … 77 passed`; 43 `ROJO`, 0 `FALLA`; «OK: los 43 sabotajes dan rojo por la razón esperada»; `rc=0` |
| sabotaje 23, `sin_aviso_juntos` | `34 failed, 43 passed` |
| sabotaje 24, `sin_aviso_sufijo` | `33 failed, 44 passed` |
| sabotaje 39, `aviso_operacion_sin_limpiar` | `3 failed, 74 passed` |
| sabotajes 40 a 43 | `3 failed, 74 passed`; `3 failed, 74 passed`; `1 failed, 76 passed`; `14 failed, 63 passed` |
| `anclas_perdidas.py 9d580db` | `103 guiones, 2514 anclas medidas y 11 llamadas sin medir`; perdida una línea 0, varias líneas 0, otra cantidad 0; no medido 5 (guiones: 2); sin ancla 6 (guiones: 1); está 2514 (guiones: 101) |
| `bash -n scripts/testing/sabotaje_maria8.sh` | `rc=0` |
| los 8 archivos que nombran estos avisos (los de D250) | `1192 passed, 1 xfailed` |
| el conjunto ancho, sin cambio | `2320 passed, 1 xfailed` |

**No corrido:** la suite entera, `compileall` (no hay producto), pantallas,
e2e, smoke, ataque de aislamiento, Postgres, los otros guiones de sabotaje y
`/security-review` (no hay producto).

## `chequeo-6`

```
chequeo-6 01bc9df..9d580db: avisos para mirar, no un veredicto
producto +0/−0
arnés +78/−14
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

1. **Los 17 verdes de D252, D253 y D254.** Medidos; no los cubre ninguna
   prueba del conjunto ancho.
2. **Los sabotajes 40 y 41 esperan los mismos dos datos.** Cada uno aplica un
   solo cambio, así que cada rojo es por su cambio. Lo que el guion no
   distingue es cuál de los dos avisos se rompió: los dos casos comparan los
   dos avisos juntos (supuesto 4).
3. **La `:1953` no está medida con una entrada que la distinga** (D252).
4. **El orden entre ítems** lo atrapan pocos datos: `tres_items` y el ítem
   vecino del caso del mismo sufijo.
5. Los guiones con que medí (`mut.py`, `medir.sh`, `medir_ancho.sh`,
   `tabla.py`, `pantalla.py`) están en mi carpeta temporal, no en el
   repositorio.
6. **Fuera de la pieza, visto al medir y no investigado:** para un mismo
   renglón que va junto con otros, un aviso dice «del renglón 3» y los del
   arancel dicen «del ítem 3» (`maria_generator.py:1955-1956` lo hace a
   propósito). Si te parece que confunde, es una pregunta para el
   despachante.

**Líneas que propongo para la cola de limpieza:**

- La línea 300 de la cola: los literales del sufijo sucio y del limpio están
  ahora en las líneas 235, 237, 450 y 453. Mejor nombrar las pruebas
  (`test_el_sufijo_del_renglon_se_limpia` y
  `test_los_avisos_dicen_si_se_limpio_el_sufijo_de_un_renglon`), que no
  envejecen.
- La línea 273 de la cola: el número del último `echo` de
  `sabotaje_maria8.sh` ahora es `43`. Un contador adentro de `caso` saca el
  número a mano.

## Archivos de producto que toqué

Ninguno.

## Sigo con

Nada asignado después de D251. D252, D253 y D254 esperan tu respuesta. D244,
D239 y «Holanda» esperan a Emi: no los toco.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `2fb54d0`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`, D247 (a) sobre `4a58c68`, D248 (c) sobre `3fcc9c4`, los vencidos `sabotaje_maria1d.sh` sobre `6e4e658`, `sabotaje_maria5.sh` sobre `c0505cc`, `sabotaje_valor1b.sh` sobre `70eb5dc`, `sabotaje_doc1.py` sobre `d4c6b73`, `sabotaje_maria7.sh` sobre `4477ae3` y `sabotajes/guardar2.sh` sobre `aeb994f` (no queda ningún vencido), D249 (a) sobre `50dabfa` y D250 (a) sobre `450f4cb`. Entregada sin veredicto: **D251 (a) sobre `9d580db`** (base `01bc9df`; sólo `tests/test_maria8_subitems_por_posicion.py`, de 61 a 77 pruebas, `JUNTOS` con 5 datos y `MISMO_SUFIJO` con 28, y `scripts/testing/sabotaje_maria8.sh`, de 39 a 43 sabotajes; arnés +78/−14; 43 `ROJO`, los 40 a 43 dan `3 failed, 74 passed`, `3 failed, 74 passed`, `1 failed, 76 passed` y `14 failed, 63 passed`; anclas 0, 0 y 0, «está» 2514; 99 cambios medidos, 82 rojos y 17 verdes, los 17 verdes también contra el conjunto ancho, `2320 passed, 1 xfailed`; `/code-review high` corrió sobre `01bc9df..2032376` y sobre `01bc9df..9d580db`; cuatro adversarios Sonnet alto). Si vuelve con devolución, va primero. **D252, D253 y D254 abiertas, mías, esperan a la PM:** D252, los otros tres usos de la lista de renglones de un ítem que ninguna prueba fija (`:2230-2231` el aviso de cada renglón, `:2187` y `:1953` `en_renglones`; filas 22, 34 a 37 y 52 a 54), recomendé (a) pieza chica; D253, tres topes uno arriba de los datos (filas 10, 55 y 56), recomendé (a) límite escrito; D254, seis cambios del adversario 4 (filas 46 a 51), recomendé (a) límite escrito. **Sin pieza activa:** nada asignado después de D251; las mediciones están en mi carpeta temporal `d251/` (`tabla.md`, `guion_9d580db.log`, `ancho_9d580db.txt`, `ancho4_9d580db.txt`, `ancho5_9d580db.txt`, `pantalla_9d580db.txt`). D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D255. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga, y su porqué se comprueba con `git show`, no se supone; que «nadie cubría» algo se mide antes de escribirlo, y con todas las pruebas que usan ese dato, no sólo las del guion (un adversario que corre cuatro archivos dice «hueco» donde otra prueba lo atrapa); `anclas_perdidas.py` mide un commit: el arreglo se commitea antes de medir; el SHA que se entrega pasa por subagente o `/code-review`, y si el gancho de parada ya subió el commit, lo que siga va en un commit nuevo; después de un commit nuevo o de corregir uno, las puertas corren otra vez sobre ese SHA; un ancla lleva sólo el texto que saca más lo mínimo que la ata a su lugar; la cuenta escrita a mano en el último `echo` de un guion se compara con sus líneas `ROJO`; una mutación se mide a mano con el archivo de pruebas entero, para ver que pone en rojo sólo lo suyo y por aserción; `anclas_perdidas.py` sólo lee los `.sh`; un worktree que aparece en `git worktree list` mientras corre un guion mío es de ese guion, no un resto; una espera de 110 vueltas de 5 s no alcanza para tres corridas de 4 minutos: se vuelve a esperar la marca de fin, no se relanza; mientras haya una D mía sin contestar, el informe siguiente la repite arriba; el dato que fija «qué pedazo se muestra» no tiene ese pedazo al principio de donde sale, o cortar el todo da lo mismo; `sabotaje_sufijos1.sh` recibe el venv como segundo argumento, no por `PY`; un riesgo que diría «cubierto» se mide antes de escribirlo; mover un dato para tapar un agujero se mide de los dos lados, con todos los cambios anotados otra vez; un ítem vecino en un caso de avisos lleva su propio aviso, o el recorrido de ítems queda sin mirar; el criterio para dejar de iterar se dice y se sostiene, y lo que queda va como D; dos cambios del mismo tamaño aplicados en el mismo segundo comparten el `.pyc`: una medición rápida corre con `python -B` y sin `.pyc`; lo que vería el despachante con un cambio se mide en pantalla antes de escribirlo en una D; regla de la PM: `/code-review high` se corre siempre, aunque sea sólo arnés, va hasta el SHA que se entrega, y un commit que nace de sus hallazgos pasa por el adversario; regla de la PM: en un vencido de sólo arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice, cualquier otro cambio sí. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
