# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D248 (c): entregada en `3fcc9c4`. El caso 20 de `sabotaje_maria8.sh` ahora ataca la herencia del sufijo de la operación; el guion sigue en 38 `ROJO` y 0 `FALLA`

| qué | SHA |
|---|---|
| base (informe de D247 (a)) | `ee3ccfd` |
| pruebas: sale el caso 20 viejo y entra `sin_herencia`. **Lo que se entrega** | `3fcc9c4` |
| tu rama, traída (`3a6ae61`: D247 (a) aceptada, D249 (a)) | `a6e3bc8` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +17/−14`: sólo `scripts/testing/sabotaje_maria8.sh`.

Leí la aceptación de D247 (a) y D249 (a) con la familia entera: va después de
los 6 vencidos, y sólo toco `tests/test_sufijos2.py` y `sabotajes/sufijos2.sh`.

## Nada para decidir

Dos supuestos reversibles:

1. **Seguí tu sugerencia: los tres lugares donde se hereda van como datos del
   mismo caso.** Para eso `caso` acepta más de un texto esperado. Si no lo
   querés: se deja sólo el `reemplazar` del renglón y un texto; `caso` con un
   solo texto se comporta igual que antes.
2. **Es un caso, no tres: la cuenta queda en 38.** Tu acta eligió (c) «sin
   cambiar la cuenta». El costo está en «Riesgos», punto 1. Partirlo en tres
   casos (40) son unas 6 líneas, si lo preferís.

## Lo que cambió

Salió el caso 20 viejo (`pide_sufijo_operacion`), que atacaba un control que
ya no existe. Entró este:

```bash
# 20. sin sufijo propio, el renglón, el ítem entero y el sub-ítem a mano dejan
# de heredar el de la operación: una prueba por lugar
reemplazar $F 'f" del renglón {lugar_en_el_pedido[id(renglon)]}")[0] or sufijo_de_la_operacion()' 'f" del renglón {lugar_en_el_pedido[id(renglon)]}")[0]'
reemplazar $F '                          or sufijo_de_la_operacion())' '                          )'
reemplazar $F 'f" del ítem {n_item}, sub-ítem {n}")[0] or sufijo_de_la_operacion()' 'f" del ítem {n_item}, sub-ítem {n}")[0]'
caso "sin_herencia" "FAILED $T::test_sin_sufijo_propio_el_renglon_lleva_el_de_la_operacion" \
  "FAILED $T::test_un_renglon_solo_sale_como_antes" \
  "FAILED $T::test_un_grupo_a_mano_y_los_subitems_a_mano_no_se_mezclan"
```

Son los tres únicos usos de `… or sufijo_de_la_operacion()` del producto
(`maria_generator.py` 1701, 1726 y 1799). Las tres anclas son código y están
una sola vez.

`caso` cambió en tres puntos:

- acepta varios textos esperados y exige todos;
- si faltan, la `FALLA` nombra todos los que faltan, no sólo el primero;
- llamado sin texto esperado corta con `falta el texto esperado` (antes
  buscaba un texto vacío, que siempre está, y daba `ROJO`).

Los otros 37 casos pasan un solo texto y dan lo mismo que antes.

## Resultado, contra tu criterio

| criterio | resultado sobre `3fcc9c4` |
|---|---|
| el 20 sale y entra «el renglón sin sufijo propio deja de heredar el de la operación» | hecho; se llama `sin_herencia` |
| `ROJO` por `test_sin_sufijo_propio_el_renglon_lleva_el_de_la_operacion` | `ROJO   sin_herencia: 4 failed, 42 passed`; el texto esperado incluye esa prueba |
| el guion sigue en 38 `ROJO` y 0 `FALLA` | 38 `ROJO`, 0 `FALLA`; `OK: los 38 sabotajes dan rojo por la razón esperada`; `rc=0` |
| las anclas no empeoran (5 y 1) | `perdida, una línea 5 guiones: 4`; `perdida, varias líneas 1 guiones: 1` |
| sugerencia: ítem entero y sub-ítem como datos del caso | adentro, sin tocar otro guion |

Cada lugar sacado solo, sobre `3fcc9c4`, corriendo el archivo del guion:

| lugar (línea) | resultado | pruebas en rojo |
|---|---|---|
| renglón (1701) | `2 failed, 44 passed` | `test_sin_sufijo_propio_el_renglon_lleva_el_de_la_operacion`, `test_el_pedido_de_la_pantalla_sale_en_un_item` |
| ítem entero (1726) | `1 failed, 45 passed` | `test_un_renglon_solo_sale_como_antes` |
| sub-ítem a mano (1799) | `1 failed, 45 passed` | `test_un_grupo_a_mano_y_los_subitems_a_mano_no_se_mezclan` |

Cada una de las tres pruebas esperadas da rojo sólo por su lugar.

El guion mismo, en copias recortadas (caso 0 y caso 20), con cada falta
provocada:

| copia | salida |
|---|---|
| entera | `ROJO   sin_herencia: 4 failed, 42 passed`; `rc=0` |
| sin el cambio del renglón | `FALLA  sin_herencia: rojo, pero sin «FAILED …::test_sin_sufijo_propio_el_renglon_lleva_el_de_la_operacion»`; `rc=1` |
| sin el del ítem entero | `FALLA` sin «…::test_un_renglon_solo_sale_como_antes»; `rc=1` |
| sin el del sub-ítem | `FALLA` sin «…::test_un_grupo_a_mano_y_los_subitems_a_mano_no_se_mezclan»; `rc=1` |
| sin ítem ni sub-ítem | una `FALLA` que nombra las dos; `rc=1` |
| `caso` sin texto esperado | `2: falta el texto esperado`; `rc=1` |

## Revisión adversarial

Pieza chica de arnés: un adversario, Sonnet, esfuerzo medio, sobre `22ac41c`
(la versión anterior al ajuste de abajo), en un árbol descartable.

| qué probó | resultado |
|---|---|
| el guion entero | 38 `ROJO`, 0 `FALLA` |
| cada lugar solo | 2 / 1 / 1 failed; cada prueba roja sólo por su lugar; el rojo es `ValueError … falta el sufijo de valor`, no un error de sintaxis |
| los tres juntos | 4 failed: las tres esperadas y `test_el_pedido_de_la_pantalla_sale_en_un_item` |
| anclas en las dos revisiones | 5 y 1 |
| el `caso` nuevo sobre los otros 37 | no los afloja |
| las anclas | código, una vez cada una; la del ítem entero comparte texto con `sabotaje_sufijos1.sh`, que trabaja en otro árbol: no se pisan |
| una cuarta herencia sin atacar | no hay |

Sin defectos. Marcó un hueco de cobertura que ya aceptaste:
`test_con_todos_los_sufijos_propios_no_hace_falta_el_de_la_operacion` queda
sin sabotaje. No corrió la suite entera, otros guiones ni `chequeo-6`.

## `/code-review high ee3ccfd..22ac41c`

Sin errores de corrección. Seis observaciones:

| observación | qué hice |
|---|---|
| el caso aplica los tres cambios juntos y no obliga a que cada lugar lo agarre su propia prueba | queda como riesgo 1. El comentario y el mensaje del commit decían que sí lo obligaba: corregidos |
| las pruebas del ítem entero y del sub-ítem dan rojo porque la generación corta con «falta el sufijo», no porque miren el valor heredado | riesgo 2, medido |
| `caso` sin texto esperado daba `ROJO` | arreglado |
| `caso` cortaba en el primer texto que faltaba | arreglado: nombra todos |
| el ancla del ítem entero es genérica (espacios y `or sufijo_de_la_operacion())`) | queda. Si deja de ser única, el guion corta con `PATRON NO ENCONTRADO`: falla a la vista |
| `test_con_todos_los_sufijos_propios…` sin sabotaje | ya aceptado por vos |

**`3fcc9c4` no volvió a pasar por subagente ni por `/code-review`.** Es
`22ac41c` con esos arreglos: tres puntos de `caso` y la redacción del
comentario. Lo comprobé con las copias recortadas de arriba y con todas las
puertas corridas de nuevo sobre ese SHA.

## Comandos

```bash
VENV=/ruta/a/tu/venv
git diff ee3ccfd 3fcc9c4 --stat | tail -1           # 1 file changed, 17 insertions(+), 14 deletions(-)
bash scripts/testing/sabotaje_maria8.sh 3fcc9c4 $VENV > /tmp/m8.log; echo $?    # 0   (unos 5 min)
grep -c '^ROJO ' /tmp/m8.log                        # 38
grep -c '^FALLA' /tmp/m8.log                        # 0
grep sin_herencia /tmp/m8.log                       # ROJO   sin_herencia: … 4 failed, 42 passed …
$VENV/bin/python scripts/testing/anclas_perdidas.py 3fcc9c4 | sed -n 2,3p
#     perdida, una línea          5   guiones: 4
#     perdida, varias líneas      1   guiones: 1

# cada lugar solo
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
git worktree add -q --detach /tmp/wt-d248 3fcc9c4 && cd /tmp/wt-d248
for linea in 1701 1726 1799; do
  sed -i "${linea}s/ or sufijo_de_la_operacion()//" proyecto_maria/core/maria_generator.py
  git diff --stat | tail -1                         # 1 file changed, 1 insertion(+), 1 deletion(-)
  env -u DATABASE_URL -u ENVIRONMENT $VENV/bin/python -m pytest -q --no-cov -p no:cacheprovider --timeout=120 \
      tests/test_maria8_subitems_por_posicion.py | grep -E '^FAILED|failed'
  git checkout -q -- .
done
cd - && git worktree remove --force /tmp/wt-d248
#   1701: 2 failed, 44 passed     1726: 1 failed, 45 passed     1799: 1 failed, 45 passed
```

Corrí cada uno una vez, con la salida a un archivo; esas son sus líneas. El
árbol descartable lo armé en mi carpeta de trabajo, no en `/tmp/wt-d248`.

## Puertas

Sobre `3fcc9c4`, árbol limpio.

| puerta | salida |
|---|---|
| `sabotaje_maria8.sh 3fcc9c4` | `VERDE  sin sabotaje: 46 passed`; 38 `ROJO`, 0 `FALLA`; `OK: los 38 sabotajes dan rojo por la razón esperada`; `rc=0` |
| `tests/test_anclas_perdidas.py tests/test_maria8_subitems_por_posicion.py tests/test_maria9_sufijo_operacion.py` | `100 passed` |
| `anclas_perdidas.py 3fcc9c4` | `103 guiones, 2492 anclas medidas y 11 llamadas sin medir`; 5 y 1; `rc=0` |
| `chequeo-6.py ee3ccfd 3fcc9c4` | abajo, `avisos: 0` |

**No corrido:** la suite entera (cambió un guion, ningún producto ni prueba),
`compileall`, las pantallas, `e2e_maria.sh`, `smoke_friccion.sh`,
`ataque_aislamiento.sh`, Postgres, los demás guiones de sabotaje y
`/security-review`.

## `chequeo-6`

```
chequeo-6 ee3ccfd..3fcc9c4: avisos para mirar, no un veredicto
producto +0/−0
arnés +17/−14
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

1. **Que cada prueba responde sólo por su lugar está medido, no obligado por
   el guion.** El caso saca las tres herencias juntas y pide las tres pruebas
   en rojo. Si mañana alguien cambia una de esas pruebas y pasa a dar rojo por
   el lugar de otra, el guion sigue diciendo `ROJO`. Lo midieron de a uno el
   adversario, el revisor y yo. Obligarlo son tres casos (40).
2. **En el ítem entero y el sub-ítem, lo que se prueba es que se hereda algo,
   no qué.** Haciendo que cada lugar herede un valor fijo equivocado en vez
   del de la operación, el archivo que corre este guion ve sólo el del
   renglón (2 pruebas en rojo); el del ítem entero y el del sub-ítem quedan
   verdes ahí. Los agarra `tests/test_maria9_sufijo_operacion.py` (4 y 4 en
   rojo) y, para el ítem entero, `tests/test_maria9_bordes.py` (5). No sale un
   TXT malo sin que una prueba lo vea; no lo ve este guion.
3. El ancla genérica del ítem entero (arriba): falla a la vista.
4. `test_con_todos_los_sufijos_propios_no_hace_falta_el_de_la_operacion` sin
   sabotaje: aceptado por vos.
5. `3fcc9c4` sin segunda revisión independiente (arriba).

## Líneas para COLA-LIMPIEZA

- `sabotaje_maria8.sh`: el `38` del último `echo` está escrito a mano. Si se
  agrega o se saca un caso y no se toca, el guion miente la cuenta. Contarlos.

## Archivos de producto que toqué

Ninguno.

## Sigo con

El primer vencido, `scripts/testing/sabotaje_maria1d.sh` (anclas perdidas en
:97 y :117). Antes de reescribir miro si la protección que atacaba cada una
sigue existiendo; si no, vuelve como D250. Después maria5, valor1b, doc1.py,
maria7 y guardar2, uno por pieza; después D249 (a).

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `3a6ae61`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`, D247 (a) sobre `4a58c68`. Entregada sin veredicto: **D248 (c) sobre `3fcc9c4`** (base `ee3ccfd`; sólo `scripts/testing/sabotaje_maria8.sh`, arnés +17/−14; 38 `ROJO`, 0 `FALLA`; anclas 5 y 1; el caso 20 es `sin_herencia`, con los tres lugares como datos y `caso` aceptando varios textos esperados). Si vuelve con devolución, va primero. **Pieza activa: el vencido `scripts/testing/sabotaje_maria1d.sh`** (anclas perdidas en :97, de varias líneas, caso `endpoint_sin_caratula`, y :117, caso `procedencia_rara_sin_aviso`); después, uno por pieza: maria5 (193, 227), valor1b (102, 114 están dos veces), doc1.py, maria7 (97), guardar2 (74); al arreglar cada uno saco mi línea de `docs/pm/herramientas/sabotajes-conocidos.txt`. Después **D249 (a)**, decidida por la PM: sólo `tests/test_sufijos2.py` y `scripts/testing/sabotajes/sufijos2.sh`, criterio entero en `docs/pm/PARA-DEV-2.md` (la familia de fragmentos «…» de `limpiar_sufijo`, un sabotaje por cambio, `sufijos2.sh` entero en `ROJO` con la cuenta exacta, `sabotaje_sufijos1.sh` en 46, anclas 5 y 1). D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D250. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
