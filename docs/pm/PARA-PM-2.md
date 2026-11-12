# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## `sabotaje_maria3.sh` re-anclado: entregado en `29880ee` (sólo arnés). 30 de 30 en rojo, sale 0

| qué | SHA |
|---|---|
| base (tu cabeza anterior, ya integrada) | `3af35be` |
| un dato más en la prueba de procedencia («100») | `ff69c3d` |
| las siete anclas perdidas, sobre el código de hoy | `2cf7ddd` |
| el sabotaje del flete saca las tres validaciones | `d13f153` |
| tu cabeza `47ca0cd` integrada | `c26e21c` |
| arreglos de la autorrevisión (ids completos, comentario) | `e0ddb9e`, `29880ee` |
| su línea sale de `sabotajes-conocidos.txt` | `e4308e1` |
| **el que se entrega** | `29880ee` |
| informe | el commit siguiente |

**Resultado.** Las siete protecciones siguen existiendo en el código de hoy:
ninguna va como D de retirar. El guion entero sobre `29880ee` da 30 `ROJO`
y sale 0. `anclas_perdidas.py 29880ee` no da ninguna fila para el guion.
Producto: **+0/−0**.

Dos cosas que no eran re-anclar puro y por eso van como D:

- El sabotaje 18, anclado donde hoy vive la protección, quedaba verde:
  ningún caso distinguía «código de tres cifras que no está en la tabla».
  Agregué el dato «100» a la prueba (D196).
- El sabotaje 28 (flete) no estaba entre los siete, pero quedó verde apenas
  el guion pudo llegar hasta él: hoy el flete se valida en tres lugares al
  generar. Ahora saca los tres (D198).

## Decisiones

**D196. El dato «100» en `test_procedencia_no_reconocida_se_rechaza`.**
Sin él, el sabotaje 18 no tiene rojo: «99999» y «12» se rechazan por la
forma del código, antes de mirar la tabla. Con la mutación 18 y sin el dato:
`134 passed`. Con el dato: `2 failed` (`assert 200 == 400` en las dos rutas).
«100» no está en la tabla oficial (309 códigos; `grep -c '"code":"100"'` da
0); 999 sí está.
- (a) Queda el dato. **Recomiendo (a)**: es una línea, verde hoy, y es el
  único caso que prueba que un código con forma válida se busca en la tabla.
- (b) Lo saco, y el sabotaje 18 va como D de retirar.

**D197. `_codigo_de_la_tabla` quedó sin prueba que la distinga.** Es la
función que atacaban los sabotajes 18 y 24 viejos. Hoy la ruta de generar
pasa por `codigo_de_pais`, y `_codigo_de_la_tabla` la usa sólo
`despacho_lector.py:259`. Le saqué el chequeo de tabla en una copia y corrí
los 7 archivos de prueba que tocan el lector: `441 passed`. No corrí la
suite entera con esa mutación.
- (a) Pieza aparte: un caso del lector con un código que no está en la tabla
  y su sabotaje. **Recomiendo (a)**. El lector es de la Técnica: decidí vos
  quién.
- (b) Queda anotado como riesgo y no se hace nada.

**D198. El sabotaje 28 saca tres validaciones del flete a la vez.** Al
generar, alcanza con cualquiera de las tres para el 400 (generador, control
del pedido, conversión de importes del endpoint): con una o dos sacadas,
los casos de `/generate_maria` siguen verdes. El rojo prueba que alguna
funciona, no cuál. En `/generate_maria/avisos` hay una sola (la del endpoint); sacándola
sola fallan los dos casos de avisos, pero ningún sabotaje del guion los
nombra.
- (a) Queda así: es defensa repetida, y una sola rota no cambia lo que ve el
  usuario.
- (b) Un sabotaje más en este guion, de un ancla, que espere
  `[/generate_maria/avisos-flete-inf]`. Son tres líneas y la prueba ya
  existe. **Recomiendo (b)**, porque en avisos no hay segunda defensa.
- (c) Además de (b), una prueba directa del generador con flete inválido.
  No la recomiendo: detrás tiene otras dos capas.

## Supuestos (reversibles)

1. **Sabotaje 13.** En vez de sacar el parámetro `user`, cambia la
   dependencia por una que no mira la sesión. El cuerpo del endpoint usa
   `user["username"]`: sacando el parámetro daba un 500 por otra causa. Con
   el cambio, el rojo es `assert 200 == 401`.
2. **Sabotaje 16.** Hoy la fecha sale de `_fecha_leida`. La mutación hace
   que una copia del lector no pase por ahí. Una variante más fina
   (`str(raw)` dentro de `_fecha_leida`) queda verde, `136 passed`: «None»
   no es una fecha y sale vacía igual.
3. **Ids completos en los sabotajes 16 y 24.** Esperaban un prefijo del id,
   que también cumple otro parámetro. Ahora esperan `[None-pymupdf]` y
   `[/generate_maria/avisos-\u0662\u0662\u0662]`, escrito con la
   barra y la u, como lo imprime pytest.
4. **Saqué `reemplazar_si_esta`.** Su único uso era el control del pedido en
   el sabotaje 28, que ya está integrado: ahora es `reemplazar`, y si el
   ancla se pierde el guion frena.

## Qué cambió en cada sabotaje

| # | nombre | dónde está hoy la protección | rojo |
|---|---|---|---|
| 13 | `avisos_sin_sesion` | `user=Depends(get_current_user)` en `avisos_maria_endpoint`; la firma ganó `db` | 1 failed |
| 14 | `avisos_previos_distintos` | `_supuestos_maria(request, items, gastos)`; el ancla vieja incluía un comentario que ya no está | 1 failed |
| 16 | `fecha_none` | `'fecha_emision': fecha,` (dos copias, se cambia la primera) | 1 failed |
| 18 | `procedencia_fuera_de_la_tabla` | `codigo in _tabla_oficial()` en `codigo_de_pais` | 2 failed |
| 21 | `tabla_corta` | `_tabla_oficial()` arma un diccionario, no un `frozenset` | 9 failed |
| 24 | `cifras_raras` | `[0-9]{3}` en el patrón de `codigo_de_pais` | 4 failed |
| 27 | `avisos_gastos_500` | `except ValueError` después de `_importes_como_numeros(request)` | 14 failed |
| 28 | `flete_sin_validar` | generador, `controles_maria.py` y `_importes_como_numeros` | 4 failed |

## Para reproducir

```bash
bash scripts/testing/sabotaje_maria3.sh 29880ee <venv>
# VERDE sin sabotaje: 136 passed; 30 líneas ROJO;
# «OK: los 30 sabotajes dan rojo por la razón esperada»; sale 0
python scripts/testing/anclas_perdidas.py 29880ee | grep -c sabotaje_maria3
# 0
python docs/pm/herramientas/chequeo-6.py 3af35be 29880ee
# producto +0/−0, avisos: 0
```

## Puertas

| puerta | sobre | salida |
|---|---|---|
| guion entero | `29880ee` | `VERDE  sin sabotaje: 136 passed`; 30 `ROJO`; `OK: los 30 sabotajes dan rojo por la razón esperada`; `rc=0 segundos=230` |
| `anclas_perdidas.py` | `29880ee` | ninguna fila de `sabotaje_maria3.sh`. En el repo quedan: `perdida, una línea 14 (guiones: 7)`, `perdida, varias líneas 7 (guiones: 4)`, `otra cantidad 2 (guiones: 1)` |
| `chequeo-6.py 3af35be 29880ee` | | abajo, entera |
| rojo antes: guion viejo | `3af35be` | 12 `ROJO`, después `PATRON NO ENCONTRADO (0 veces) en proyecto_maria/main.py` en el sabotaje 13; `rc=1` |

```
chequeo-6 3af35be..29880ee: avisos para mirar, no un veredicto
producto +0/−0
arnés +21/−28
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

**Rojos intermedios, diagnosticados (no repetí hasta verde):**

- Sobre `2cf7ddd`: 29 `ROJO` y `FALLA flete_sin_validar: quedó verde`,
  `rc=1`. Causa: la tercera validación del flete. Arreglo: `d13f153`.
- Sobre `e4308e1`: 29 `ROJO` y `FALLA cifras_raras: rojo, pero sin «…»`,
  `rc=1`. Causa: mía. Al pasar al id completo, las tres cifras quedaron
  guardadas como caracteres y pytest las imprime escapadas. El rojo salía
  (4 failed), el texto esperado no. Arreglo: `29880ee`.

## Hallazgos de la autorrevisión

| quién | hallazgo | severidad | qué hice |
|---|---|---|---|
| adversario Sonnet, medio | Las 8 mutaciones sacan la protección que dice su comentario y el rojo sale por esa razón (corrió cada una a mano) | — | nada |
| adversario Sonnet, medio | 16: la mutación saltea `_fecha_leida` entera, no sólo el «None» | baja | supuesto 2 |
| adversario Sonnet, medio | 24: el id esperado era un prefijo | baja | arreglado |
| adversario Sonnet, medio | 28: hay una cuarta validación (`cuentas_del_valor`), que no da 400: su error queda en `valor.error` | — | nada; lo reproduje, sacar la cuarta no cambia los 4 rojos |
| `/code-review high` (revisores Fable, alto) | 28 saca tres a la vez | media | D198 |
| `/code-review high` | 24: prefijo | baja | arreglado |
| `/code-review high` | `_codigo_de_la_tabla` sin negativo | media | D197, medido |
| `/code-review high` | 16: la segunda copia del lector no tiene sabotaje (viene de antes) | baja | queda como riesgo; el id ahora nombra la copia |
| `/code-review high` | comentario nuevo de tres líneas | baja | arreglado: dos |

`/security-review`: no corrido. La pieza no toca producto.

## Qué no corrí y riesgos

- La suite entera: no. Es arnés, producto +0/−0. Corrí
  `tests/test_maria3_antes_de_generar.py` (136 passed) y el guion entero.
- Ningún otro guion vencido: van uno por pieza.
- La mutación 18 la probé contra los archivos de prueba que tocan países
  (1184 passed, 2 xfailed sin el dato «100»), no contra la suite entera.
- Riesgo: las anclas de 13, 14 y 27 son de dos o tres líneas y dependen de
  la línea vecina. Si cambia, el guion frena con `PATRON NO ENCONTRADO`; no
  pasa en verde.
- Riesgo: la segunda copia del lector (`pdf_directo`) no tiene sabotaje de
  la fecha.

Archivos de producto tocados: ninguno. Arnés:
`scripts/testing/sabotaje_maria3.sh`, `tests/test_maria3_antes_de_generar.py`
(un dato) y `docs/pm/herramientas/sabotajes-conocidos.txt` (una línea menos).

No hay pieza marcada «apenas entregues»: sigo con `catalogo_largo2`, como
dice tu canal, salvo que llegue una devolución o la tarea de comparación.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 47ca0cd, ya integrada), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. El re-anclaje de sabotaje_maria3.sh está entregado en 29880ee (informe en el commit siguiente), esperando veredicto: 30 de 30 en rojo, sale 0, sin filas en anclas_perdidas.py, producto +0/−0. Abiertas, las decide la PM: D196 (dato «100» en la prueba), D197 (_codigo_de_la_tabla sin prueba), D198 (el sabotaje del flete saca tres validaciones). Sigue, una pieza por guion: catalogo_largo2 y después valor1, maria8, maria1d, maria5, valor1b, doc1.py, maria7, guardar2; al entregar cada uno sale su línea de herramientas/sabotajes-conocidos.txt. Próxima D libre: D199. Una devolución de la PM o la tarea de comparación van primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
