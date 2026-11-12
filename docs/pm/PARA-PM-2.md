# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D191 (a): entregado en `f1809e9` (sólo arnés). La primera puerta no se cumple: 29 de 30

| qué | SHA |
|---|---|
| base (tu cabeza) | `3ff4e77` |
| anclas de `sabotaje_maria9.sh` a la forma de hoy | `c9d1d95` |
| el 2 y el 3 mutan la guarda del aviso, como el ancla vieja — **el que se entrega** | `f1809e9` |
| informe | el commit siguiente |

**Resultado.** El guion vuelve a correr entero: antes cortaba en el segundo
sabotaje con `PATRON NO ENCONTRADO`. Sobre `f1809e9` da **29 `ROJO` y una
`FALLA`** y sale 1:

```
FALLA  endpoint_sin_procedencia: quedó verde
FALLAN 1 sabotajes
```

Es el sabotaje 30. Con su ancla de hoy no da rojo, y como pediste no lo
arreglé en el guion: vuelve como D192. Producto: **+0/−0**. Arnés: +13/−13.

**Lo que tenés que saber antes de aceptar:**

1. **El 30 no es un hueco del producto, es una prueba que dejó de
   distinguir.** Lo medí: detalle en D192.
2. **El 7 no es un cambio de ancla: le cambié el sentido.** Su mutación
   vieja es hoy la línea del producto. Es D193 y se revierte borrando tres
   líneas.
3. **El mensaje de `c9d1d95` dice algo inexacto** («nueve vuelven a mutar el
   mismo punto»): para el 2 y el 3 no era el mismo punto. Lo encontró
   `/code-review`, lo corregí en `f1809e9` y el mensaje viejo queda como está
   porque ya estaba subido.

## Decisiones

**D192. El sabotaje 30 (`endpoint_sin_procedencia`) queda verde.** La
mutación vieja le pasaba a `usa_el_sufijo_de_la_operacion` los ítems del
pedido en vez de los que ya tienen la procedencia de la operación. Antes eso
importaba porque la función agrupaba renglones por procedencia para saber
cuáles iban juntos. Desde `fe95a49b` ya no agrupa: sólo mira si cada ítem o
sub-ítem trae su sufijo. Con cualquiera de las dos listas contesta lo mismo.

Lo que medí, cada mutación sola sobre el producto de `3ff4e77` (el mismo de
`f1809e9`):

| mutación en `main.py`, `/generate_maria` | las cuatro pruebas de MARIA-9 | otras pruebas |
|---|---|---|
| `usa_el_sufijo_de_la_operacion(items)` → `(request.items)` (la del guion) | 138 passed | no corrido |
| `items = _items_con_procedencia(request)` → `items = request.items` | 138 passed | ocho archivos que nombran la procedencia: **22 failed**, 344 passed, 2 xfailed |
| `generate_maria_txt(… items=items …)` → `items=request.items` | sin rojos | con `test_maria3_antes_de_generar.py` y `test_punta_a_punta1.py`: **15 failed** (12 y 3), 265 passed, 2 xfailed |
| `_supuestos_maria(request, items, gastos)` → `(request, request.items, gastos)` | sin rojos | los mismos dos archivos: **2 failed** (los dos en `test_maria3…`), 278 passed, 2 xfailed |

O sea: que el endpoint pierda la procedencia de la operación lo agarran
`test_maria3_antes_de_generar.py` (19 casos) y `test_punta_a_punta1.py` (3).
Lo que ya no agarra nadie es lo que dice el nombre de
`test_el_endpoint_agrupa_con_la_procedencia_de_la_operacion`: esa prueba hoy
pasa con procedencia o sin ella, porque dos ítems con su sufijo propio
generan igual estén o no agrupados.

Dos lugares del endpoint reciben `items` y no tienen prueba que distinga si
les llega la lista con procedencia o la del pedido:
`validate_for_kit_maria(items)` y `_cuentas_del_valor(request, items)`. Por
lectura, ninguna de las dos funciones mira la procedencia, así que hoy no
cambia nada. No lo corrí: son mutantes equivalentes, no hay rojo posible.

- (a) Sacar el sabotaje 30 del guion y dejar la prueba como está. El guion
  pasa a decir «los 29».
- (b) Sacar el sabotaje 30 y también la prueba, que ya no prueba lo que dice.
- (c) Dejar todo como está: el guion sale 1 hasta que se decida.

**Recomiendo (b).** La regla que cuidaban el sabotaje y la prueba ya no
existe en el producto, y la procedencia en el endpoint la cubren otras 22
pruebas. Con (a) queda una prueba con un nombre que promete algo que no
mira. No lo hice yo porque borrar una prueba no es actualizar un ancla.
Con (a) o (b) hay que tocar también el comentario `# 30.` y el texto «los
30» del final del guion.

**D193. El sabotaje 7 cambió de sentido.** Antes: «un ítem que sale entero
no cuenta», quitando `n not in juntos or` de la condición. Esa línea mutada
es, letra por letra, la que el producto tiene hoy: SUFIJOS-1 decidió que un
ítem entero lleva su sufijo propio, y el caso `item_entero_con_propio` pasó
a esperar lo contrario (`eec344f`). No hay ancla nueva posible para la
mutación vieja.

Lo dejé mutando al revés: `elif sin_propio(item.get("sufijo")):` →
`elif True:` («un ítem o renglón con su propio usa igual el de la
operación»), con el caso renombrado a `con_propio_usa_el_general`. Espera el
mismo id de prueba que antes y da rojo (6 failed, por `assert 1 == 0`).

En contra, y lo dijeron los dos revisores: esto es un sabotaje nuevo, no un
ancla actualizada, y lo que pone rojo es más o menos la unión de lo que ya
ponen rojo el 3 y el 9.

- (a) Queda así.
- (b) Se saca el 7 del guion.

**Recomiendo (a), sin mucha fuerza.** Es la única mutación del guion que
rompe la función misma hacia el lado de «siempre lo usa» (el 3 y el 9 rompen
a quienes la llaman). Si preferís un guion sin superposición, (b) no pierde
cobertura de pruebas.

## Para reproducir

```bash
git fetch origin claude/dev-maria && git checkout --detach f1809e9
bash scripts/testing/sabotaje_maria9.sh f1809e9 <tu venv>
#   29 líneas «ROJO», una «FALLA  endpoint_sin_procedencia: quedó verde»,
#   «FALLAN 1 sabotajes», sale 1. Tardó 6 min 1 s acá.
python docs/pm/herramientas/chequeo-6.py 3ff4e77 f1809e9
#   producto +0/−0, arnés +13/−13, avisos: 0
```

## Anclas: vieja, nueva y qué prueba se pone roja

Las pruebas son de `tests/test_maria9_sufijo_operacion.py` (2 a 10 y 30) y
`tests/test_maria9_kilos.py` (24 a 28). Cada ancla nueva aparece una sola vez
en su archivo y es código, no comentario. «generador» es
`proyecto_maria/core/maria_generator.py`.

| # | caso | archivo | ancla vieja → mutación vieja | ancla nueva → mutación nueva | prueba que se pone roja |
|---|---|---|---|---|---|
| 2 | `sin_aviso` | generador | `if usa_el_sufijo_de_la_operacion(items, iva_adicional):` → `if False:` | `if usa_el_general:` → `if False:` | `test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[item_entero]` |
| 3 | `aviso_siempre` | generador | la misma → `if True:` | la misma → `if True:` | `…[renglones_con_propio]` |
| 7 | `con_propio_usa_el_general` (antes `item_entero_no_cuenta`) | generador | `elif n not in juntos or sin_propio(item.get("sufijo")):` → `elif sin_propio(item.get("sufijo")):` | `elif sin_propio(item.get("sufijo")):` → `elif True:` | `…[item_entero_con_propio]` (el mismo caso; **la mutación cambió de sentido: D193**) |
| 8 | `renglon_sin_propio_no_cuenta` | generador | la misma del 7 → `elif n not in juntos:` | `elif sin_propio(item.get("sufijo")):` → `elif False:` | `…[un_renglon_sin_propio]` |
| 9 | `api_exige_el_general` | `main.py` | `if not sbt_raw and usa_el_sufijo_de_la_operacion(items, request.iva_adicional):` → `if not sbt_raw:` | `if not sbt_raw and usa_el_general:` → `if not sbt_raw:` | `test_por_api_los_renglones_con_propio_generan[]` |
| 10 | `api_sin_falta` | `main.py` | la misma del 9 → `if False:` | la misma del 9 → `if False:` | `test_por_api_sin_ninguno_falta_el_sufijo` |
| 24 | `nombra_a_todos` | generador | `if min(valores).quantize(Decimal("0.01"), ROUND_HALF_UP) <= 0]` → `if False]` | la misma terminada en `}` → `if False}` | `test_el_error_nombra_sólo_los_renglones_chicos[uno_al_final]` |
| 27 | `sin_chico_nombra_al_primero` | generador | `chicos = chicos or [lugar_en_el_pedido[id(r)] for r in renglones]` → `… or [lugar_en_el_pedido[id(renglones[0])]]` | `if i in solos or not en_cero <= solos]` → `if i in solos or (i == 0 and not en_cero <= solos)]` | `…[todos_iguales]` |
| 28 | `mira_despues_del_ajuste` | generador | `for r, *valores in zip(renglones, *propios)` → `… zip(renglones, cantidades_sub, estadisticas_sub)` | `enumerate(zip(*propios))` → `enumerate(zip(cantidades_sub, estadisticas_sub))` | `…[el_cero_cae_en_el_mas_grande]` |
| 30 | `endpoint_sin_procedencia` | `main.py` | la misma del 9 → `… usa_el_sufijo_de_la_operacion(request.items, request.iva_adicional):` | `usa_el_general = usa_el_sufijo_de_la_operacion(items)` → `… (request.items)` | **ninguna: queda verde. D192** |

Los otros 20 sabotajes no se tocaron y dan `ROJO` igual. Además cambió un
comentario: el del 8 decía «un renglón sin propio no cuenta» y ahora dice
«un ítem o renglón sin propio no cuenta», que es lo que hace la mutación.

## Puertas

| puerta | resultado |
|---|---|
| `sabotaje_maria9.sh f1809e9` entero, desde worktree limpio | **No cumplida.** 29 `ROJO`, 1 `FALLA` (el 30), `FALLAN 1 sabotajes`, sale 1 |
| tabla ancla vieja / ancla nueva / prueba roja | arriba |
| un sabotaje sin rojo vuelve como D | D192 |
| `chequeo-6` entero, producto +0/−0 | cumplida, abajo |

Salida del guion sobre `f1809e9`, entera, con cada línea cortada a 110
columnas:

```
Preparing worktree (detached HEAD f1809e9)
ROJO   analiza_siempre: ================== 7 failed, 131 passed, 5 warnings in 9.87s ===================
ROJO   sin_aviso: ================== 7 failed, 131 passed, 3 warnings in 9.50s ===================
ROJO   aviso_siempre: ================== 6 failed, 132 passed, 3 warnings in 9.80s ===================
ROJO   aviso_con_otro_texto: ================== 7 failed, 131 passed, 3 warnings in 9.80s ===================
ROJO   propio_malo_usa_el_general: ================== 1 failed, 137 passed, 3 warnings in 9.72s ==============
ROJO   subitem_sin_propio_no_cuenta: ================== 2 failed, 136 passed, 3 warnings in 9.82s ============
ROJO   con_propio_usa_el_general: ================== 6 failed, 132 passed, 3 warnings in 9.36s ===============
ROJO   renglon_sin_propio_no_cuenta: ================== 7 failed, 131 passed, 3 warnings in 10.02s ===========
ROJO   api_exige_el_general: ================== 2 failed, 136 passed, 4 warnings in 10.14s ==================
ROJO   api_sin_falta: ================== 1 failed, 137 passed, 3 warnings in 9.70s ===================
VERDE  pantalla sin sabotaje
ROJO   subitem_no_reconocido: FALLA: el del sub-ítem: no sale bajo el sub-ítem 2 del ítem 1 (sale como error d
ROJO   operacion_no_reconocida: FALLA: el de la operación: no sale bajo el campo del sufijo de la operación (s
ROJO   item_ignorado: FALLA: el del ítem 2: no sale bajo el sub-ítem 1 del ítem 2
ROJO   todo_al_campo: FALLA: el error de un sub-ítem que no existe se pierde
ROJO   tope_generador_120_no_pasa: ================== 2 failed, 136 passed, 3 warnings in 9.55s ==============
ROJO   tope_generador_121_pasa: ================== 1 failed, 137 passed, 3 warnings in 9.43s =================
ROJO   tope_endpoint_120_no_pasa: ================== 1 failed, 137 passed, 3 warnings in 9.44s ===============
ROJO   tope_endpoint_121_pasa: ================== 1 failed, 137 passed, 3 warnings in 9.23s ==================
ROJO   codigo_de_tres_cifras: ================== 1 failed, 137 passed, 3 warnings in 9.69s ===================
ROJO   codigo_de_una_letra: ================== 1 failed, 137 passed, 3 warnings in 9.77s ===================
ROJO   punto_y_coma_no_separa: ================== 1 failed, 137 passed, 3 warnings in 9.47s ==================
ROJO   unidad_con_codigo_avisada: ================== 2 failed, 136 passed, 3 warnings in 9.15s ===============
ROJO   unidad_desconocida_sin_aviso: ================== 4 failed, 134 passed, 3 warnings in 9.49s ============
ROJO   nombra_a_todos: ================== 4 failed, 134 passed, 3 warnings in 9.05s ===================
ROJO   kilos_en_cero_pasan: ================== 7 failed, 131 passed, 3 warnings in 9.10s ===================
ROJO   siempre_plural: ================== 2 failed, 136 passed, 3 warnings in 9.13s ===================
ROJO   sin_chico_nombra_al_primero: ================== 2 failed, 136 passed, 3 warnings in 9.74s =============
ROJO   mira_despues_del_ajuste: ================== 3 failed, 135 passed, 3 warnings in 9.09s =================
ROJO   no_mira_los_kilos: ================== 4 failed, 134 passed, 3 warnings in 9.51s ===================
FALLA  endpoint_sin_procedencia: quedó verde
FALLAN 1 sabotajes

real	6m0.909s
```

`chequeo-6`:

```
chequeo-6 3ff4e77..f1809e9: avisos para mirar, no un veredicto
producto +0/−0
arnés +13/−13
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Autorrevisión

Los dos revisores miraron `c9d1d95`. `f1809e9` son las tres líneas que
salieron de sus hallazgos; no las volvió a mirar un subagente (ver «Qué no
se corrió»).

| quién | modelo y esfuerzo | hallazgo | gravedad | qué hice |
|---|---|---|---|---|
| `adversario-sonnet-medio` | Sonnet, medio | `test_el_endpoint_agrupa_con_la_procedencia_de_la_operacion` ya no depende de la procedencia | baja | D192 |
| | | el 7 pone rojo casi lo mismo que el 3 y el 9 juntos | informativa | D193 |
| | | el comentario del 8 no decía lo que hace hoy la mutación | baja | corregido en `f1809e9` |
| | | el ancla que había elegido para el 2 y el 3 también existe una vez en `main.py`; no rompe nada porque `reemplazar` cuenta por archivo | informativa | el ancla nueva está 0 veces en `main.py` |
| `/code-review high` | el de la sesión, alto | el 30 no cambia el comportamiento; si se saca, quedan viejos `# 30.` y «los 30» | media | D192 |
| | | el 7 es un sabotaje nuevo, no un ancla actualizada | baja | D193 |
| | | el 2 y el 3 mutaban la asignación de `usa_el_general`, que además decide qué sufijos se validan, y no la guarda del aviso | baja | corregido en `f1809e9`, con el rojo de cada uno probado a mano antes |

El revisor de `/code-review` corrió el guion entero sobre `c9d1d95` con otro
entorno virtual y le dio lo mismo que a mí: 29 `ROJO`, 1 `FALLA`, sale 1.

Rojos del 2 y el 3 con el ancla de `f1809e9`, a mano, uno por vez, con las
cuatro pruebas del guion:

```
if usa_el_general: -> if False:   7 failed, 131 passed   cae …[item_entero]
if usa_el_general: -> if True:    6 failed, 132 passed   cae …[renglones_con_propio]
```

## Supuestos reversibles

1. El 30 quedó con el ancla de hoy en vez de con la vieja: así el guion corre
   los 30 y dice cuál falla, en vez de cortar con `PATRON NO ENCONTRADO`.
2. El 27 conserva la intención vieja («nombra sólo al primero») y no la
   mutación más corta (sacar `or not en_cero <= solos`), que pone rojos los
   mismos dos casos.
3. El 7, en D193.

## Qué no se corrió

- La suite completa: el cambio es un guion de arnés y no toca producto ni
  pruebas.
- Un segundo `/code-review` sobre `f1809e9`: son tres líneas, dos de ellas la
  corrección que propuso el propio revisor. Las cubre la corrida entera del
  guion sobre ese SHA.
- La mutación del guion para el 30 contra otros archivos de prueba: la
  función mutada no mira la procedencia.

## Riesgos

- Mientras D192 no se decida, `sabotaje_maria9.sh` sale 1.

## Sigue

El conteo estático de anclas de una línea perdidas en todos los guiones de
sabotaje («apenas entregues»). Va como D194 en el próximo informe, que
conserva este entero.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 3ff4e77, ya integrada), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. D145 (a) aceptada. D191 (a) entregado en f1809e9 (informe en el commit siguiente), esperando veredicto: la primera puerta no se cumple (29 de 30, el 30 queda verde); abiertas D192 (qué hacer con el sabotaje 30 y su prueba) y D193 (el sabotaje 7 cambió de sentido). Sigue, sin esperar el veredicto: el conteo estático de anclas de una línea perdidas en scripts/testing/sabotaje_*.sh y sabotajes/*.sh, como D194, con el comando que lo mide y sin arreglar ningún guion; ese informe conserva entero el de D191. Próxima D libre después: D195. Una devolución de la PM va primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
