# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Vencido `sabotaje_maria5.sh`: entregado en `c0505cc`. Vuelve a encontrar sus dos anclas y suma tu idea como caso 50; 50 `ROJO`, `rc=0`; anclas perdidas en 2 y 0

| qué | SHA |
|---|---|
| base (informe de maria1d) | `38a7ed2` |
| pruebas: dos anclas reescritas y mi línea fuera de `sabotajes-conocidos.txt` | `8b712b2` |
| pruebas: el caso 50, tu idea (supuesto 1) | `15d146a` |
| pruebas: un renglón de comentario del caso 50, por la revisión. **Lo que se entrega** | `c0505cc` |
| tu rama, traída hasta `2e936b5` | `3b645bf`, `56afd12` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +10/−3`: `scripts/testing/sabotaje_maria5.sh` y una
línea menos en `docs/pm/herramientas/sabotajes-conocidos.txt`.

**El SHA que entrego es `c0505cc`.** El adversario revisó `15d146a`. De ahí
a `c0505cc` cambia un solo renglón de comentario, que salió de esa revisión.
Ese renglón no volvió a pasar por un revisor: está copiado entero abajo
(«Revisión del SHA final») y el guion volvió a correr sobre `c0505cc`.

## Nada para decidir

Antes de reescribir comprobé que las dos protecciones siguen existiendo
(D195 (a)): no hay sabotaje para retirar ni D nueva. Dos supuestos
reversibles:

1. **Tu idea entró como caso 50, en un commit aparte.** Miré y se podía:
   `tests/test_maria5_caratula_vacia.py::test_los_avisos_antes_de_generar_tambien`
   ya corría en este guion y ningún caso la esperaba. El caso 50 deja los
   avisos previos sin supuestos y espera esa prueba. Si no lo querés, es
   revertir `15d146a` y `c0505cc` y quedan 49. Su límite está en el riesgo 1.
2. **Achiqué las dos anclas**, igual que en maria1d: sólo el texto que el
   caso saca.

## Lo que cambió

```diff
 # 26. el aviso del lector no llega a la pantalla
-reemplazar $M "        avisos = operacion_data.pop('avisos_peso', []) if isinstance(operacion_data, dict) else []" "        avisos = []"
+reemplazar $M "operacion_data.pop('avisos_peso', [])" "[]"
…
 # 33. la guarda existe pero el TXT no la usa
-reemplazar $G 'QARTKGRNET={peso_valido(peso_kg, idx):.3f}' 'QARTKGRNET={peso_kg:.3f}'
+reemplazar $G 'peso_valido(peso_kg, lugar_en_el_pedido.get(id(item), idx))' 'peso_kg'
…
+# 50. los avisos antes de generar salen sin los supuestos: lo que falta en la
+# carátula no se avisa ahí
+reemplazar $M "
+    supuestos = _supuestos_maria(request, items, gastos)" "
+    supuestos = []"
+caso previos_sin_supuestos "${T}caratula_vacia.py::test_los_avisos_antes_de_generar_tambien["
…
-echo "OK: los 49 sabotajes dan rojo por la razón esperada"
+echo "OK: los 50 sabotajes dan rojo por la razón esperada"
```

Por qué se habían perdido:

- **Caso 26.** El ancla era el renglón entero, con su
  `if isinstance(…) else []`. `e3c68dc` (MARIA-7, punto 8) pasó el `pop`
  adentro de un `if`.
- **Caso 33.** El ancla era la llamada dentro del renglón de `QARTKGRNET`.
  `67d5688` (MARIA-7) la sacó a `peso_neto = peso_valido(peso_kg, idx)` y
  `3f13b5b` (MARIA-8) le cambió el segundo argumento.

Los nombres y los textos esperados de los 49 casos anteriores no cambiaron.

El ancla del caso 50 empieza con un salto de línea y cuatro espacios:
`main.py` llama dos veces a `_supuestos_maria(request, items, gastos)`, y
la de generar tiene ocho espacios. Así cae sólo en la de los avisos previos.

## Resultado

| qué | antes, guion de `38a7ed2` | ahora, `c0505cc` |
|---|---|---|
| el guion | `VERDE`, 25 `ROJO` y corta: `PATRON NO ENCONTRADO (0 veces) en proyecto_maria/main.py: "        avisos = operacion_data.pop('avisos_peso', []) if isinstance(operacion_data, dict) else []"`; `rc=1` | `VERDE  sin sabotaje: 225 passed`; 50 `ROJO`, 0 `FALLA`; `OK: los 50 sabotajes dan rojo por la razón esperada`; `rc=0` |
| caso 26 | cortaba ahí | `ROJO   aviso_del_lector_perdido: 1 failed, 224 passed` |
| caso 33 | no llegaba a correr | `ROJO   guarda_sin_usar: 14 failed, 211 passed` |
| caso 50 | no existía | `ROJO   previos_sin_supuestos: 2 failed, 223 passed` |
| anclas perdidas | 4 de una línea, 0 de varias | `perdida, una línea 2 guiones: 2`; `perdida, varias líneas 0 guiones: 0` |
| mi línea en `sabotajes-conocidos.txt` | estaba | no está; quedan 4 `vencido` |

Que la protección sigue, medido a mano sobre el producto de `38a7ed2` (el
mismo de `c0505cc`) antes de tocar el guion, con
`tests/test_maria5_devolucion.py`:

| mutación | resultado | pruebas en rojo |
|---|---|---|
| ninguna | `64 passed` | |
| caso 26: el `pop` de `avisos_peso` por `[]` | `1 failed, 63 passed` | `test_el_aviso_del_lector_llega_a_la_pantalla`: `AssertionError: assert [] == ['Peso de «X»...o de prueba.']` |
| caso 33: la llamada a `peso_valido` por `peso_kg` | `9 failed, 55 passed` | `test_un_peso_imposible_no_llega_al_txt[peso0]` a `[peso7]` y `test_un_peso_enorme_dice_que_es_enorme`, las nueve con `Failed: DID NOT RAISE ValueError` |

Con los ocho archivos del guion el caso 33 da 14: los cinco que se suman son
de `test_los_mensajes_del_peso_dicen_la_razon`, en
`tests/test_devolucion2_maria5_ncm.py`, con el mismo mensaje.

### Tu idea, medida

| pregunta | cómo | resultado |
|---|---|---|
| ¿algún caso esperaba `test_los_avisos_antes_de_generar_tambien`? | `grep` en `scripts/testing/` | ninguno, en ningún guion |
| ¿alguno de los 49 la pone roja igual? | una copia del guion, fuera del repositorio, que corre sólo `test_maria5_caratula_vacia.py` y dice por caso si esa prueba falla | sólo el 10 (`none_en_el_servidor`), que espera otra prueba y saca otra cosa: que «None» escrito cuente como vacío. Los otros 48, no |
| ¿la mutación del caso 50 da rojo por la afirmación? | puesta a mano, los ocho archivos | `2 failed, 223 passed`: `[None]` y `[n/a]`, las dos con `AssertionError: assert ('vendedor' in '')` en `tests/test_maria5_caratula_vacia.py:63` |
| ¿y sin la mutación? | el `VERDE` del guion | `225 passed` |

## Revisión adversarial

Pieza chica de arnés. Dos pasadas, una por commit:

| SHA | quién | resultado |
|---|---|---|
| `8b712b2` (las dos anclas) | adversario Sonnet, esfuerzo medio | sin defectos; dos observaciones previas (riesgos 2 y 3) |
| `15d146a` (el caso 50) | adversario Sonnet, esfuerzo medio | sin defectos; una observación sobre el comentario, que arreglé en `c0505cc`, y otra que ya era el riesgo 1 |
| **`c0505cc` (lo que se entrega)** | nadie | un renglón de comentario; por qué no, abajo |

No corrí `/code-review`: el código que se entrega pasó por el adversario, que
es una de las dos que pediste.

### Adversario sobre `8b712b2`

En un worktree propio que retiró al terminar. No corrió el guion entero.

| qué probó | resultado |
|---|---|
| anclas | código, una sola vez. El 26 en `main.py:4685`, dentro de `if isinstance(operacion_data, dict):`; es el único `pop` de `avisos_peso`. El 33 en `maria_generator.py:1563`; los otros `peso_valido` son la definición (914) y el uso de los renglones (1098), con otros argumentos |
| caso 26 puesto a mano | `1 failed, 63 passed`; `assert [] == ['Peso de «X»...o de prueba.']`. Que la clave quede dentro de la operación no rompió ninguna otra prueba |
| caso 33 puesto a mano | `9 failed, 55 passed` en `test_maria5_devolucion.py`; `14 failed, 211 passed` con los ocho archivos, los 14 con `Failed: DID NOT RAISE ValueError` |
| `anclas_perdidas.py 8b712b2` | ninguna fila de `sabotaje_maria5.sh` |
| mensaje del commit | cierto, con `git show e3c68dc` y `git show 67d5688`. Sumó que el segundo argumento lo cambió `3f13b5b`; lo comprobé con `git show 3f13b5b` y está arriba |
| sacar la línea de `sabotajes-conocidos.txt` | corresponde |

### Revisión del SHA final

El adversario revisó `15d146a` en un worktree propio que retiró al terminar.
No corrió el guion entero.

| qué probó | resultado | lo reproduje |
|---|---|---|
| el ancla del caso 50 | una sola vez en `main.py`, en la línea 4992 (los avisos previos). La de generar (5223) tiene ocho espacios y no coincide | sí: el caso corre y da `ROJO`; con 0 o 2 veces `reemplazar` corta |
| el medidor de anclas sobre `15d146a` | ninguna fila de `sabotaje_maria5.sh` | sí, y sobre `c0505cc` |
| la mutación a mano, los ocho archivos | `2 failed, 223 passed`: `[None]` y `[n/a]`, con `AssertionError: assert ('vendedor' in '')`. Ni 500 ni error de sintaxis | sí, antes que él (tabla «Tu idea, medida») |
| otro sabotaje igual en otro guion | ninguno saca los supuestos de los avisos previos. `sabotaje_maria3.sh:159` y `sabotaje_valor1c.sh:203` cambian un argumento de esa llamada; `sabotajes/cobro_corte1.sh:266` toca la de generar | sí, con `grep -rn _supuestos_maria scripts/testing/` |
| el `49` | queda sólo en el comentario del caso 49; el `echo` dice 50 | sí |
| el mensaje del commit | cierto «salvo un matiz»: que el caso 4 de maria1d no saca argumentos de `_supuestos_maria` | miré y no hay matiz: los cuatro renglones que saca están en `main.py:4895-4898`, dentro de `_supuestos_maria`. El mensaje queda |
| el comentario del caso 50 | impreciso: decía que lo que falta en la carátula «sólo se avisa al generar», y al generar el CUIT vacío no es un aviso, es un 400 | sí: `test_un_obligatorio_escrito_vacio_falta` afirma ese 400 y está en verde. Que el vendedor sí salga como supuesto al generar no lo corrí yo |
| lo que la prueba no distingue | un sabotaje que deje pasar algunos supuestos y no otros | es el riesgo 1 |

El comentario lo arreglé en `c0505cc`. Es todo lo que cambia desde `15d146a`
en el guion:

```diff
-# carátula sólo se avisa al generar
+# carátula no se avisa ahí
```

Ahora dice sólo lo que el caso obliga: con el sabotaje, los avisos previos no
nombran lo que falta en la carátula. Un comentario de bash no cambia lo que
corre; igual volví a correr el guion entero y las puertas sobre `c0505cc`.

## Comandos

```bash
VENV=/ruta/a/tu/venv
git diff 38a7ed2 c0505cc --stat -- scripts docs/pm/herramientas | tail -1    # 2 files changed, 10 insertions(+), 4 deletions(-)
git diff 15d146a c0505cc -- scripts | grep -c '^[+-]#'              # 2   (el renglón de comentario, sale y entra)
bash scripts/testing/sabotaje_maria5.sh c0505cc $VENV > /tmp/m5.log; echo $?    # 0   (unos 7 min)
grep -c '^ROJO ' /tmp/m5.log                        # 50
grep -c '^FALLA' /tmp/m5.log                        # 0
grep -E 'aviso_del_lector_perdido|guarda_sin_usar|previos_sin_supuestos' /tmp/m5.log
#   ROJO   aviso_del_lector_perdido: … 1 failed, 224 passed …
#   ROJO   guarda_sin_usar: … 14 failed, 211 passed …
#   ROJO   previos_sin_supuestos: … 2 failed, 223 passed …
$VENV/bin/python scripts/testing/anclas_perdidas.py c0505cc | sed -n 2,3p
#     perdida, una línea          2   guiones: 2
#     perdida, varias líneas      0   guiones: 0
grep -c sabotaje_maria5 docs/pm/herramientas/sabotajes-conocidos.txt     # 0
grep -c '^vencido' docs/pm/herramientas/sabotajes-conocidos.txt          # 4

# el rojo sin el arreglo: el guion de la base
git show 38a7ed2:scripts/testing/sabotaje_maria5.sh > /tmp/m5_viejo.sh
bash /tmp/m5_viejo.sh 38a7ed2 $VENV | tail -1; echo ${PIPESTATUS[0]}
#   PATRON NO ENCONTRADO (0 veces) en proyecto_maria/main.py: "        avisos = operacion_data.pop('avisos_peso', …
#   1
```

Corrí cada uno una vez, con la salida a un archivo; esas son sus líneas.

## Puertas

Sobre `c0505cc`, árbol limpio. Las mismas cuatro habían dado lo mismo sobre
`15d146a`.

| puerta | salida |
|---|---|
| `sabotaje_maria5.sh c0505cc` | `VERDE  sin sabotaje: 225 passed`; 50 `ROJO`, 0 `FALLA`; `OK: los 50 sabotajes dan rojo por la razón esperada`; `rc=0` |
| `tests/test_anclas_perdidas.py` | `27 passed` |
| `anclas_perdidas.py c0505cc` | `103 guiones, 2493 anclas medidas y 11 llamadas sin medir`; 2 y 0; ninguna fila de `sabotaje_maria5.sh`; `rc=0` |
| `chequeo-6.py 38a7ed2 c0505cc` | abajo, `avisos: 0` |

**No corrido:** la suite entera (cambió un guion, ningún producto ni prueba),
`compileall`, las pantallas, `e2e_maria.sh`, `smoke_friccion.sh`,
`ataque_aislamiento.sh`, Postgres, los demás guiones de sabotaje,
`/code-review`, `/security-review` (no toca plata, sesión, permisos ni
datos) y un revisor sobre el renglón de `c0505cc`.

## `chequeo-6`

```
chequeo-6 38a7ed2..c0505cc: avisos para mirar, no un veredicto
producto +0/−0
arnés +10/−3
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

1. **El caso 50 saca todos los supuestos del camino previo, no sólo la
   carátula.** Los dos caminos arman la carátula en la misma función,
   `_supuestos_maria`: no hay un renglón que la pase sólo a los avisos
   previos. La prueba que espera mira dos avisos de carátula («vendedor» y
   «cuit del importador»); si los avisos previos perdieran otro supuesto y
   conservaran esos dos, ni la prueba ni el caso lo verían. Eso lo mira
   `test_maria3_antes_de_generar.py::test_los_avisos_previos_son_los_mismos_que_al_generar`,
   fuera de este guion. Severidad baja.
2. **Los casos 32 y 33 esperan el mismo prefijo**,
   `test_un_peso_imposible_no_llega_al_txt[`. Si el 33 dejara de morder y
   otro cambio pusiera roja esa prueba, el guion diría `ROJO`: `caso` mira el
   nombre en `FAILED`, no la causa. El 34 sí distingue (`[peso2]`). Es previo
   y el commit no lo empeora; severidad baja.
3. **El comentario del 33 dice «el TXT no la usa» y el camino de los
   renglones (`maria_generator.py:1098`) la sigue usando.** El ancla vieja
   atacaba el mismo uso que la nueva; el comentario es previo y no lo toqué.
   Si querés que diga «un ítem suelto», es una línea.
4. **Las anclas del 26 y el 33 son cortas.** Si aparece otro texto igual en
   su archivo, el guion corta con `PATRON NO ENCONTRADO (2 veces)`: falla a
   la vista, no en silencio.

## Líneas para `COLA-LIMPIEZA.md`

- `sabotaje_maria5.sh`: el `50` del último `echo` está escrito a mano, como
  el `38` de maria8; y el venv por defecto es `/tmp/cdi-dev2/venv`, que ya no
  existe.

## Archivos de producto que toqué

Ninguno.

## Sigo con

El vencido `scripts/testing/sabotaje_valor1b.sh` (las anclas de 102 y 114
están dos veces en `finalize.js`). Primero miro si cada protección sigue
existiendo.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `2e936b5`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`, D247 (a) sobre `4a58c68`, D248 (c) sobre `3fcc9c4`, el vencido `sabotaje_maria1d.sh` sobre `6e4e658`. Entregada sin veredicto: **el vencido `sabotaje_maria5.sh` sobre `c0505cc`** (base `38a7ed2`; sólo `scripts/testing/sabotaje_maria5.sh` y mi línea fuera de `sabotajes-conocidos.txt`, arnés +10/−3; 50 `ROJO`, 0 `FALLA`; anclas 2 y 0; el caso 50 es una idea de la PM y va como supuesto reversible; un adversario Sonnet medio revisó `15d146a` y de ahí a `c0505cc` cambia un renglón de comentario). Si vuelve con devolución, va primero. **Pieza activa: el vencido `scripts/testing/sabotaje_valor1b.sh`** (las anclas de 102 y 114 están dos veces en `proyecto_maria/static/v2/screens/finalize.js`, que no se toca); después, uno por pieza: doc1.py, maria7 (97), guardar2 (74); al arreglar cada uno saco mi línea de `docs/pm/herramientas/sabotajes-conocidos.txt`. Después **D249 (a)**, decidida por la PM: sólo `tests/test_sufijos2.py` y `scripts/testing/sabotajes/sufijos2.sh`, criterio entero en `docs/pm/PARA-DEV-2.md`, sección D247 (la familia de fragmentos «…» de `limpiar_sufijo`, un sabotaje por cambio, `sufijos2.sh` entero en `ROJO` con la cuenta exacta, `sabotaje_sufijos1.sh` en 46, anclas que no empeoran: el criterio dice 5 y 1 y hoy son 2 y 0). D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D250. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga, y su porqué se comprueba con `git show`, no se supone; que «nadie cubría» algo se mide antes de escribirlo; `anclas_perdidas.py` mide un commit: el arreglo se commitea antes de medir; el SHA que se entrega pasa por subagente o `/code-review`, y si el gancho de parada ya subió el commit, lo que siga va en un commit nuevo; después de un commit nuevo o de corregir uno, las puertas corren otra vez sobre ese SHA; un ancla lleva sólo el texto que saca más lo mínimo que la ata a su lugar. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
