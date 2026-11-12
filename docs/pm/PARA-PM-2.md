# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Vuelta de D191: entregada en `4723280` (sólo arnés). El guion sale 0 con 29

| qué | SHA |
|---|---|
| base (tu cabeza al devolver, integrada en `9ecbdb6`) | `c8247e9` |
| la prueba, con el nombre de lo que mira | `3dbf198` |
| el guion sin el sabotaje 30 | `63066ce` |
| el comentario de la prueba, dos correcciones de la autorrevisión — **el que se entrega** | `5f9a16e`, `4723280` |
| tu cabeza de ahora, integrada después de `4723280` (sólo trae `NOW.md`) | `b1ecf97` |
| informe | el commit siguiente |

**Resultado.** `sabotaje_maria9.sh 4723280` entero, desde su worktree limpio:
29 `ROJO`, «OK: los 29 sabotajes dan rojo por la razón esperada», sale 0, en
336 s. Producto: **+0/−0**. Arnés de la vuelta: +4/−10.

**Nada para decidir.** Hice D192 (a) y D193 (a) como las decidiste.

**Lo que tenés que saber antes de aceptar:**

1. **La prueba se llama ahora
   `test_por_api_con_sufijo_en_cada_renglon_no_pide_el_de_la_operacion`.** El
   cuerpo no cambió: sólo el nombre y el comentario (tres líneas por cinco).
2. **El comentario lo escribí tres veces, y la del medio estaba mal.** En
   `5f9a16e` puse que el endpoint «rearma» el renglón con la procedencia de
   la operación. `/code-review` mostró que la prueba no mira eso: con los
   ítems del pedido tal cual llegan sigue en verde. `4723280` lo deja en lo
   que sí comprueba. El mensaje de `5f9a16e` queda como está; el rojo que
   cita es cierto, la frase del comentario no.
3. **Con las mutaciones del guion que la ponen roja, la prueba renombrada no
   cae sola.** De las seis que mediste, la ponen roja la del 7 y la del 9, y
   con las dos cae también `test_por_api_los_renglones_con_propio_generan[]`,
   que pregunta lo mismo con tres renglones; el 9 del guion ya espera a esa
   otra. Los otros 23 sabotajes no los medí contra ella. Lo único que la
   distingue lo encontró el subagente con una mutación inventada: si el
   endpoint le borra el sufijo al renglón que toma la procedencia de la
   operación, es la única del archivo que se pone roja (abajo). No reabro
   D192: es el dato, por si lo querés en la cola de limpieza como un dato más
   de `_pedido_de_renglones`.

## Para reproducir

```bash
git fetch origin claude/dev-maria && git checkout --detach 4723280
bash scripts/testing/sabotaje_maria9.sh 4723280 <tu venv>
#   29 líneas «ROJO», «OK: los 29 sabotajes dan rojo por la razón esperada», sale 0
python -m pytest -q --no-cov tests/test_maria9_sufijo_operacion.py
#   27 passed (en f1809e95: 27 passed)
python docs/pm/herramientas/chequeo-6.py c8247e9 4723280
#   producto +0/−0, avisos: 0
```

El rojo de la prueba renombrada con la mutación del 9, en un worktree
descartable:

```bash
sed -i 's/if not sbt_raw and usa_el_general:/if not sbt_raw:/' proyecto_maria/main.py
python -m pytest -q --no-cov \
  tests/test_maria9_sufijo_operacion.py::test_por_api_con_sufijo_en_cada_renglon_no_pide_el_de_la_operacion
#   1 failed, «assert 400 == 200»
```

## Puertas

| puerta | resultado |
|---|---|
| `sabotaje_maria9.sh 4723280` entero, desde un worktree limpio: «OK: los 29…» y sale 0 | cumplida, abajo |
| `tests/test_maria9_sufijo_operacion.py` entero da los mismos `passed` que en `f1809e95` | cumplida: 27 passed antes de tocar nada (mismo producto y misma prueba que `f1809e95`) y 27 passed en `4723280` |
| la prueba renombrada se pone roja con la mutación del 9 | cumplida, abajo |
| la prueba y el guion en commits separados | la prueba en `3dbf198`, `5f9a16e` y `4723280`; el guion en `63066ce` |
| `chequeo-6` entero, producto +0/−0 | cumplida, abajo |

Salida del guion sobre `4723280`, entera, con cada línea cortada a 110
columnas:

```
Preparing worktree (detached HEAD 4723280)
ROJO   analiza_siempre: ================== 7 failed, 131 passed, 5 warnings in 9.52s ===================
ROJO   sin_aviso: ================== 7 failed, 131 passed, 3 warnings in 8.96s ===================
ROJO   aviso_siempre: ================== 6 failed, 132 passed, 3 warnings in 9.33s ===================
ROJO   aviso_con_otro_texto: ================== 7 failed, 131 passed, 3 warnings in 8.74s ===================
ROJO   propio_malo_usa_el_general: ================== 1 failed, 137 passed, 3 warnings in 8.65s ==============
ROJO   subitem_sin_propio_no_cuenta: ================== 2 failed, 136 passed, 3 warnings in 8.91s ============
ROJO   con_propio_usa_el_general: ================== 6 failed, 132 passed, 3 warnings in 9.01s ===============
ROJO   renglon_sin_propio_no_cuenta: ================== 7 failed, 131 passed, 3 warnings in 8.98s ============
ROJO   api_exige_el_general: ================== 2 failed, 136 passed, 3 warnings in 8.96s ===================
ROJO   api_sin_falta: ================== 1 failed, 137 passed, 3 warnings in 9.05s ===================
VERDE  pantalla sin sabotaje
ROJO   subitem_no_reconocido: FALLA: el del sub-ítem: no sale bajo el sub-ítem 2 del ítem 1 (sale como error d
ROJO   operacion_no_reconocida: FALLA: el de la operación: no sale bajo el campo del sufijo de la operación (s
ROJO   item_ignorado: FALLA: el del ítem 2: no sale bajo el sub-ítem 1 del ítem 2
ROJO   todo_al_campo: FALLA: el error de un sub-ítem que no existe se pierde
ROJO   tope_generador_120_no_pasa: ================== 2 failed, 136 passed, 3 warnings in 9.29s ==============
ROJO   tope_generador_121_pasa: ================== 1 failed, 137 passed, 3 warnings in 9.63s =================
ROJO   tope_endpoint_120_no_pasa: ================== 1 failed, 137 passed, 3 warnings in 9.47s ===============
ROJO   tope_endpoint_121_pasa: ================== 1 failed, 137 passed, 3 warnings in 8.65s ==================
ROJO   codigo_de_tres_cifras: ================== 1 failed, 137 passed, 3 warnings in 9.07s ===================
ROJO   codigo_de_una_letra: ================== 1 failed, 137 passed, 4 warnings in 8.80s ===================
ROJO   punto_y_coma_no_separa: ================== 1 failed, 137 passed, 4 warnings in 9.43s ==================
ROJO   unidad_con_codigo_avisada: ================== 2 failed, 136 passed, 3 warnings in 9.66s ===============
ROJO   unidad_desconocida_sin_aviso: ================== 4 failed, 134 passed, 3 warnings in 9.19s ============
ROJO   nombra_a_todos: ================== 4 failed, 134 passed, 4 warnings in 9.60s ===================
ROJO   kilos_en_cero_pasan: ================== 7 failed, 131 passed, 4 warnings in 9.62s ===================
ROJO   siempre_plural: ================== 2 failed, 136 passed, 3 warnings in 9.72s ===================
ROJO   sin_chico_nombra_al_primero: ================== 2 failed, 136 passed, 3 warnings in 9.37s =============
ROJO   mira_despues_del_ajuste: ================== 3 failed, 135 passed, 3 warnings in 9.70s =================
ROJO   no_mira_los_kilos: ================== 4 failed, 134 passed, 4 warnings in 9.42s ===================
OK: los 29 sabotajes dan rojo por la razón esperada
```

La prueba renombrada, sola, sobre `4723280` con
`if not sbt_raw and usa_el_general:` → `if not sbt_raw:` en
`proyecto_maria/main.py`:

```
E   AssertionError: {"detail":"Falta el sufijo de valor SBT. Es un dato obligatorio y específico del importador. Consultar al despachante."}
E   assert 400 == 200
E    +  where 400 = <Response [400 Bad Request]>.status_code
FAILED tests/test_maria9_sufijo_operacion.py::test_por_api_con_sufijo_en_cada_renglon_no_pide_el_de_la_operacion
======================== 1 failed, 3 warnings in 3.45s =========================
```

El archivo entero con cada mutación, una por vez:

```
# sin mutar
======================== 27 passed, 3 warnings in 6.91s ========================
# la del 9: if not sbt_raw and usa_el_general: -> if not sbt_raw:
FAILED tests/test_maria9_sufijo_operacion.py::test_por_api_los_renglones_con_propio_generan[]
FAILED tests/test_maria9_sufijo_operacion.py::test_por_api_con_sufijo_en_cada_renglon_no_pide_el_de_la_operacion
=================== 2 failed, 25 passed, 3 warnings in 6.72s ===================
# la del 7: elif sin_propio(item.get("sufijo")): -> elif True:
FAILED tests/test_maria9_sufijo_operacion.py::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[renglones_con_propio]
FAILED tests/test_maria9_sufijo_operacion.py::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[renglones_y_subitems_con_propio]
FAILED tests/test_maria9_sufijo_operacion.py::test_los_avisos_anticipan_el_error_sólo_si_alguien_lo_usa[item_entero_con_propio]
FAILED tests/test_maria9_sufijo_operacion.py::test_por_api_los_renglones_con_propio_generan[]
FAILED tests/test_maria9_sufijo_operacion.py::test_por_api_los_avisos_anticipan_el_error
FAILED tests/test_maria9_sufijo_operacion.py::test_por_api_con_sufijo_en_cada_renglon_no_pide_el_de_la_operacion
=================== 6 failed, 21 passed, 3 warnings in 7.15s ===================
# la del subagente: {**it, "pais_procedencia": procedencia} -> {…, "sufijo": None}
FAILED tests/test_maria9_sufijo_operacion.py::test_por_api_con_sufijo_en_cada_renglon_no_pide_el_de_la_operacion
=================== 1 failed, 26 passed, 3 warnings in 7.37s ===================
```

`chequeo-6`, contra tu cabeza (trae también D191 (a), que no integraste) y
contra la unión (sólo esta vuelta):

```
chequeo-6 c8247e9..4723280: avisos para mirar, no un veredicto
producto +0/−0
arnés +16/−22
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0

chequeo-6 9ecbdb6..4723280: avisos para mirar, no un veredicto
producto +0/−0
arnés +4/−10
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Autorrevisión

| quién | modelo y esfuerzo | hallazgo | gravedad | qué hice |
|---|---|---|---|---|
| `adversario-sonnet-medio` | Sonnet, medio | la mezcla de procedencias del caso no cambia lo que contesta el endpoint: con la mutación del 30 viejo todo sigue verde | informativa | es D192, ya decidida |
| | | mutación que sólo detecta la prueba renombrada: `"sufijo": None` al rearmar el renglón en `_items_con_procedencia` | informativa | reproducida: 1 failed, 26 passed. Punto 3 de arriba |
| | | el cliente de la prueba se sigue llamando `maria9_procedencia` | baja | queda: es un dato del cuerpo, que no se toca |
| | | sin referencias vivas al nombre viejo, a `endpoint_sin_procedencia` ni a «los 30» fuera de `docs/pm/` y `docs/archive/`; los `# N.` van del 1 al 29; 25 `caso` + 4 `caso_pantalla` = 29; `$F`, `$M` y `$T` siguen en uso | sin hallazgo | — |
| `/code-review high` | el de la sesión, alto | el comentario de `5f9a16e` afirmaba un rearmado que ninguna aserción mira | baja | corregido en `4723280` |
| | | la prueba renombrada y `…los_renglones_con_propio_generan[]` son dos casos para una causa | baja | punto 3 de arriba; no reabro D192 |
| | | el «29» del mensaje final es un literal a mano, no una cuenta | baja | queda: el patrón es anterior y está en otros guiones (`sabotaje_maria3.sh:239`). Riesgo, abajo |

El revisor de `/code-review` corrió el guion entero sobre `5f9a16e`, en un
clon suyo y con el entorno virtual `/tmp/cdi-pm/venv`: 29 `ROJO`, sale 0. No
se lo indiqué yo; después miré y bajo `/tmp/cdi-pm` no hay ningún archivo
modificado en los últimos 90 minutos. `4723280` es una corrección de
comentario encima de eso; no la miró un subagente.

## Supuestos reversibles

1. El nombre nuevo sigue la forma de los otros casos por API del archivo
   (`test_por_api_…`). Si preferís otro, es una línea.
2. No toqué los datos del caso ni le sumé aserciones: pediste nombre y
   comentario.

## Qué no se corrió

- La suite completa: la vuelta cambia un nombre, un comentario y saca un
  sabotaje. No toca producto.
- Los otros guiones de sabotaje.
- Un segundo `/code-review` sobre `4723280`: es el comentario que pidió
  corregir el primero.

## Riesgos

- El «29» del final del guion se edita a mano. Si alguien suma o saca un
  `caso` sin tocarlo, el mensaje miente. Hoy coincide. Arreglarlo es
  limpieza de algo ya escrito, fuera de esta vuelta.
- `docs/pm/` y `docs/archive/` pueden seguir nombrando el sabotaje 30 o el
  nombre viejo de la prueba: son tuyos o de sólo lectura, no los miré.

## Sigue

D194, el conteo estático de anclas de una línea perdidas en los guiones de
sabotaje, medido sobre el SHA de esta vuelta.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza b1ecf97, ya integrada), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. D145 (a) aceptada. D192 (a) y D193 (a) decididas por la PM. La vuelta de D191 está entregada en 4723280 (informe en el commit siguiente), esperando veredicto: el guion sale 0 con 29, nada para decidir. Sigue, sin esperar el veredicto: D194, el conteo estático de anclas de una línea perdidas en scripts/testing/sabotaje_*.sh y sabotajes/*.sh, con el comando que lo mide y sin arreglar ningún guion, medido sobre el SHA de esta vuelta. Próxima D libre después: D195. Una devolución de la PM va primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
