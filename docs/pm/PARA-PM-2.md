# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Vencido `sabotaje_maria1d.sh`: entregado en `6e4e658`. Vuelve a encontrar sus dos anclas; 8 `ROJO`, `rc=0`; anclas perdidas en 4 y 0

| qué | SHA |
|---|---|
| base (informe de D248 (c)) | `8f50af3` |
| pruebas: dos anclas reescritas y mi línea fuera de `sabotajes-conocidos.txt`. **Lo que se entrega** | `6e4e658` |
| tu rama, traída hasta `e3c7fe9` (D248 (c) aceptada) | `c5c6b00` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +4/−4`: `scripts/testing/sabotaje_maria1d.sh` y una
línea menos en `docs/pm/herramientas/sabotajes-conocidos.txt`.

Leí la aceptación de D248 (c) y tu línea: **`6e4e658`, el SHA que entrego,
pasó por un adversario** (abajo, «Revisión del SHA final»).

## Nada para decidir

Antes de reescribir comprobé que las dos protecciones siguen existiendo
(D195 (a)): no hay sabotaje para retirar ni D nueva. Un supuesto reversible:

1. **Achiqué las dos anclas en lugar de sólo arreglarlas.** El 4 son los
   cuatro renglones de la carátula, sin contexto después; el 8 es la clave
   `"avisos": ` con el término que saca. Lo pidió `/code-review` y lo comprobé:
   las dos se habían perdido justo por el contexto de más. Si preferís el
   ancla larga, es una línea por caso.

## Lo que cambió

```diff
-# 4. el endpoint no pasa la carátula a los avisos
+# 4. al generar, la carátula no llega a los supuestos. La misma función arma
+# los avisos previos, que este guion no mira
 reemplazar $M "        vendedor_nombre=request.vendedor_nombre,
         comprador_nombre=request.comprador_nombre,
         comprador_cuit=request.comprador_cuit,
         moneda=request.moneda,
-    )" "    )"
+" ""
 caso endpoint_sin_caratula "${T}test_ningun_none_en_el_txt_de_una_factura_vacia[pdf_directo]"
…
 # 8. los avisos previos no dicen la procedencia rara de un producto
-reemplazar $M '    return {"avisos": errores_de_procedencia(items) + kit_warnings + avisos_ncm + supuestos, "supuestos": supuestos}' \
-  '    return {"avisos": kit_warnings + avisos_ncm + supuestos, "supuestos": supuestos}'
+reemplazar $M '"avisos": errores_de_procedencia(items) + ' '"avisos": '
```

Por qué se habían perdido:

- **Caso 4.** El ancla cerraba con el `)` de la llamada. `67d5688` (MARIA-7)
  sumó tres argumentos después de `moneda=` y el `)` dejó de seguir.
- **Caso 8.** El ancla era el `return` entero. `d810c47` (VALOR-1) le sumó
  `avisos_valor` y lo partió en varios renglones.

Los nombres de los casos y los textos esperados no cambiaron. Los otros seis
casos no se tocaron.

## Resultado

| qué | antes, guion de `8f50af3` | ahora, `6e4e658` |
|---|---|---|
| el guion | `VERDE`, 3 `ROJO` y corta: `PATRON NO ENCONTRADO (0 veces) en proyecto_maria/main.py: '        vendedor_nombre=…moneda=request.moneda,\n    )'`; `rc=1` | `VERDE  sin sabotaje: 48 passed`; 8 `ROJO`, 0 `FALLA`; `OK: los 8 sabotajes dan rojo por la razón esperada`; `rc=0` |
| caso 4 | no llegaba a correr | `ROJO   endpoint_sin_caratula: 2 failed, 46 passed` |
| caso 8 | no llegaba a correr | `ROJO   procedencia_rara_sin_aviso: 8 failed, 40 passed` |
| anclas perdidas | 5 de una línea, 1 de varias | `perdida, una línea 4 guiones: 3`; `perdida, varias líneas 0 guiones: 0` |
| mi línea en `sabotajes-conocidos.txt` | estaba | no está; quedan 5 `vencido` |

Que la protección sigue, medido a mano sobre el producto de `8f50af3` (el
mismo de `6e4e658`) antes de tocar el guion:

| mutación | resultado | pruebas en rojo |
|---|---|---|
| ninguna | `48 passed` | |
| sin los cuatro renglones de la carátula | `2 failed, 46 passed` | `test_ningun_none_en_el_txt_de_una_factura_vacia[pymupdf]` y `[pdf_directo]` |
| sin `errores_de_procedencia(items)` en los avisos previos | `8 failed, 40 passed` | las ocho de `test_procedencia_rara_de_un_producto_avisa_igual_antes_y_al_generar[…]` |

## Revisión adversarial

Pieza chica de arnés. Cuatro pasadas, porque cada revisión movió el SHA:

| SHA | quién | resultado |
|---|---|---|
| `2f9cf03` (primera versión) | adversario Sonnet, esfuerzo medio | sin defectos; un hueco a comprobar (abajo) |
| `2f9cf03` | `/code-review high` | 3 observaciones, las tres aplicadas → `d103d80` |
| `d103d80` | `/code-review high` | 3 observaciones, las tres aplicadas → `6e4e658` |
| **`6e4e658` (lo que se entrega)** | adversario Sonnet, esfuerzo medio | sin defectos; dos huecos previos, uno ya medido y el otro en riesgos |

Los revisores de `/code-review` heredan mi modelo (Fable 5.2, esfuerzo alto).

### Primer adversario, sobre `2f9cf03`

| qué probó | resultado |
|---|---|
| el guion entero | `VERDE` y 8 `ROJO`, 0 `FALLA` |
| ¿cada sabotaje ataca lo mismo que el viejo? | sí: el 4 saca los mismos cuatro renglones; el 8 saca el mismo término |
| ¿el rojo es por la afirmación? | sí. Caso 4: `assert "vendedor" in avisos and "importador" in avisos`, con 200 de `/generate_maria`. Caso 8: `assert "Item 1: Procedencia no reconocida '…'" in […]` |
| ¿el texto esperado distingue? | el 8, sí (ningún otro caso pone roja esa prueba). El 4, no del todo: su prueba también cae con los casos 1 y 3. Es previo |
| anclas | código, una vez; ningún otro guion usa esos textos |
| sacar la línea de `sabotajes-conocidos.txt` | corresponde |

Marcó un hueco: si sólo los avisos previos dejan de recibir la carátula, este
archivo de pruebas queda verde. Lo medí sobre los 20 archivos que llaman a
`/generate_maria/avisos`: `4 failed, 1169 passed`. Lo ven
`test_maria3_antes_de_generar.py::test_los_avisos_previos_son_los_mismos_que_al_generar`
(2) y `test_maria5_caratula_vacia.py::test_los_avisos_antes_de_generar_tambien`
(2). **No es un hueco de la suite**, sólo de este guion, y el comentario
nuevo del caso 4 lo dice.

### `/code-review high 8f50af3..2f9cf03` y `8f50af3..d103d80`

Sin errores de corrección en ninguna de las dos.

| observación | qué hice |
|---|---|
| el ancla del 4 arrastraba un renglón ajeno (`vendedor_id=`) como contexto: el mismo patrón que la había perdido | aplicado: sólo los cuatro renglones |
| el ancla del 8 dependía de la sangría y de `kit_warnings` como segundo término | aplicado |
| el comentario del 4 decía «el endpoint», y el cambio cae en una función que usan dos | aplicado |
| (segunda pasada) el ancla del 8, sin la clave, podía caer en otro lugar de `main.py` y dar `ROJO` igual | aplicado: lleva `"avisos": ` |
| (segunda pasada) el comentario del 4 decía «ni al generar ni en los avisos previos», y el guion sólo mira generar | aplicado: dice qué mira y qué no |
| (segunda pasada) el mensaje del commit contaba mal por qué se perdió el ancla del 4 | era cierto: lo comprobé con `git show 67d5688`. Corregido en el mensaje (el commit no estaba subido) y acá |

### Revisión del SHA final, `6e4e658`

Adversario Sonnet, esfuerzo medio, en un worktree propio que retiró al
terminar. Después de su revisión no cambió nada: `6e4e658` es lo revisado y
lo entregado.

| qué probó | resultado |
|---|---|
| el guion entero sobre `6e4e658` | `VERDE` (48 passed) y 8 `ROJO`; `OK: los 8 sabotajes dan rojo por la razón esperada`; `rc=0` |
| `anclas_perdidas.py 6e4e658` | 4 de una línea, 0 de varias |
| caso 4 puesto a mano | `py_compile` bien; `2 failed, 46 passed`; el fallo es `AssertionError: assert ('vendedor' in '…')`, después del 200: no es sintaxis ni un 500 |
| caso 8 puesto a mano | `py_compile` bien; el fallo es `assert "Item 1: Procedencia no reconocida '…'. Debe indicar un país válido." in […]` |
| anclas | código, una sola vez en `main.py`; ningún otro guion de `scripts/` usa esos textos |
| dónde cae cada una | el 4 en `_supuestos_maria` (`main.py:4895-4898`), que llaman `main.py:4992` y `main.py:5223`; el 8 en `main.py:5008`, el `return` de los avisos previos |
| comentario del 4 y mensaje del commit | coinciden con `git show 67d5688` |
| sacar la línea de `sabotajes-conocidos.txt` | corresponde; las demás quedaron iguales |
| casos 1, 2, 3, 5, 6 y 7 | `ROJO` por el nombre esperado: 32, 7, 3, 4, 8 y 2 failed |

Dos huecos previos, ninguno del diff:

- El caso 4 sólo prueba el camino de generar. Es el mismo que marcó el
  primero y ya está medido arriba: lo ven otros dos archivos de pruebas.
- `caso` sólo mira que el nombre de la prueba aparezca en `FAILED`, no por
  qué falló. Va al riesgo 1.

No corrió el guion viejo sobre `8f50af3` (lo corrí yo: la columna «antes» de
«Resultado») ni la suite entera.

## Comandos

```bash
VENV=/ruta/a/tu/venv
git diff 8f50af3 6e4e658 --stat | tail -1           # 2 files changed, 4 insertions(+), 5 deletions(-)
bash scripts/testing/sabotaje_maria1d.sh 6e4e658 $VENV > /tmp/m1d.log; echo $?    # 0   (unos 40 s)
grep -c '^ROJO ' /tmp/m1d.log                       # 8
grep -c '^FALLA' /tmp/m1d.log                       # 0
grep -E 'endpoint_sin_caratula|procedencia_rara' /tmp/m1d.log
#   ROJO   endpoint_sin_caratula: … 2 failed, 46 passed …
#   ROJO   procedencia_rara_sin_aviso: … 8 failed, 40 passed …
$VENV/bin/python scripts/testing/anclas_perdidas.py 6e4e658 | sed -n 2,3p
#     perdida, una línea          4   guiones: 3
#     perdida, varias líneas      0   guiones: 0
grep -c sabotaje_maria1d docs/pm/herramientas/sabotajes-conocidos.txt    # 0
grep -c '^vencido' docs/pm/herramientas/sabotajes-conocidos.txt          # 5

# el rojo sin el arreglo: el guion de la base
git show 8f50af3:scripts/testing/sabotaje_maria1d.sh > /tmp/m1d_viejo.sh
bash /tmp/m1d_viejo.sh 8f50af3 $VENV | tail -1; echo ${PIPESTATUS[0]}
#   PATRON NO ENCONTRADO (0 veces) en proyecto_maria/main.py: '        vendedor_nombre=…
#   1
```

Corrí cada uno una vez, con la salida a un archivo; esas son sus líneas. El
guion viejo lo guardé en mi carpeta de trabajo, no en `/tmp`.

## Puertas

Sobre `6e4e658`, árbol limpio.

| puerta | salida |
|---|---|
| `sabotaje_maria1d.sh 6e4e658` | `VERDE  sin sabotaje: 48 passed`; 8 `ROJO`, 0 `FALLA`; `OK: los 8 sabotajes dan rojo por la razón esperada`; `rc=0` |
| `tests/test_anclas_perdidas.py tests/test_maria1d_campos_vacios.py` | `75 passed` |
| `anclas_perdidas.py 6e4e658` | `103 guiones, 2492 anclas medidas y 11 llamadas sin medir`; 4 y 0; `rc=0` |
| `chequeo-6.py 8f50af3 6e4e658` | abajo, `avisos: 0` |

**No corrido:** la suite entera (cambió un guion, ningún producto ni prueba;
la única corrida ancha fue la medición del hueco, con una mutación puesta),
`compileall`, las pantallas, `e2e_maria.sh`, `smoke_friccion.sh`,
`ataque_aislamiento.sh`, Postgres, los demás guiones de sabotaje y
`/security-review` (no toca plata, sesión, permisos ni datos).

## `chequeo-6`

```
chequeo-6 8f50af3..6e4e658: avisos para mirar, no un veredicto
producto +0/−0
arnés +4/−4
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

1. **El texto esperado del caso 4 no es exclusivo.** La prueba
   `test_ningun_none_en_el_txt_de_una_factura_vacia[pdf_directo]` también se
   pone roja con los casos 1 y 3. Si el caso 4 dejara de morder y otro cambio
   la pusiera roja, el guion diría `ROJO`: `caso` mira el nombre de la prueba
   en `FAILED`, no la causa. Los dos adversarios miraron la causa a mano. Es
   previo; severidad baja.
2. **El caso 4 se sigue llamando `endpoint_sin_caratula`.** El nombre quedó
   viejo (la mutación cae en `_supuestos_maria`). No lo cambié para no mover
   un nombre que ya está en actas tuyas; el comentario dice lo que hace.
3. **El ancla del 8 es corta.** Si aparece otro `"avisos": errores_de_procedencia(items) + `
   en `main.py`, el guion corta con `PATRON NO ENCONTRADO (2 veces)`: falla a
   la vista, no en silencio.

## Líneas para `COLA-LIMPIEZA.md`

- `sabotaje_maria1d.sh`: el `8` del último `echo` está escrito a mano, como el
  `38` de maria8; y el venv por defecto es `/tmp/cdi-dev2/venv`, que ya no
  existe.

## Archivos de producto que toqué

Ninguno.

## Sigo con

El vencido `scripts/testing/sabotaje_maria5.sh` (anclas perdidas en 193 y
227). Primero miro si cada protección sigue existiendo.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `e3c7fe9`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`, D247 (a) sobre `4a58c68`, D248 (c) sobre `3fcc9c4`. Entregada sin veredicto: **el vencido `sabotaje_maria1d.sh` sobre `6e4e658`** (base `8f50af3`; sólo `scripts/testing/sabotaje_maria1d.sh` y mi línea fuera de `sabotajes-conocidos.txt`, arnés +4/−4; 8 `ROJO`, 0 `FALLA`; anclas 4 y 0; el SHA final pasó por un adversario Sonnet medio). Si vuelve con devolución, va primero. **Pieza activa: el vencido `scripts/testing/sabotaje_maria5.sh`** (anclas perdidas en :193, `avisos = operacion_data.pop('avisos_peso', [])…` en `main.py`, y :227, `QARTKGRNET={peso_valido(peso_kg, idx):.3f}` en `maria_generator.py`); después, uno por pieza: valor1b (102, 114 están dos veces), doc1.py, maria7 (97), guardar2 (74); al arreglar cada uno saco mi línea de `docs/pm/herramientas/sabotajes-conocidos.txt`. Después **D249 (a)**, decidida por la PM: sólo `tests/test_sufijos2.py` y `scripts/testing/sabotajes/sufijos2.sh`, criterio entero en `docs/pm/PARA-DEV-2.md`, sección D247 (la familia de fragmentos «…» de `limpiar_sufijo`, un sabotaje por cambio, `sufijos2.sh` entero en `ROJO` con la cuenta exacta, `sabotaje_sufijos1.sh` en 46, anclas que no empeoran: el criterio dice 5 y 1 y hoy son 4 y 0). D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D250. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga, y su porqué se comprueba con `git show`, no se supone; `anclas_perdidas.py` mide un commit: el arreglo se commitea antes de medir; el SHA que se entrega pasa por subagente o `/code-review`, y si el gancho de parada ya subió el commit, lo que siga va en un commit nuevo; un ancla lleva sólo el texto que saca más lo mínimo que la ata a su lugar. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
