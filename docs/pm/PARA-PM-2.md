# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Vencido `sabotaje_doc1.py`: entregado en `d4c6b73`. Sus tres sabotajes vuelven a dar rojo, `rc=0`; quedan 2 `vencido`

| qué | SHA |
|---|---|
| base (informe de valor1b) | `a926930` |
| pruebas: dos anclas reescritas y mi línea fuera de `sabotajes-conocidos.txt`. **Lo que se entrega** | `d4c6b73` |
| informe | el commit siguiente |

`producto +0/−0`. `arnés +5/−4`: `scripts/testing/sabotaje_doc1.py` y una
línea menos en `docs/pm/herramientas/sabotajes-conocidos.txt`.

El SHA que entrego pasó por un adversario (abajo, «Revisión adversarial»).

## Nada para decidir

Antes de reescribir comprobé que las dos protecciones siguen existiendo
(D195 (a)): no hay sabotaje para retirar ni D nueva. Sin supuestos: no
agregué nada que la tarea no pida.

## Lo que cambió

```diff
     ("servidor", "proyecto_maria/main.py",
-     "    if (request.tipo_destinacion or \"\").strip().upper().startswith(\"EC\"):",
-     "    if False:", "test_ec_directa_nunca_entra_a_importacion"),
+     "        return destinacion_del_txt(tipo_destinacion, exportacion)",
+     "        return str(tipo_destinacion or \"\")", "test_ec_directa_nunca_entra_a_importacion"),
     ("generador", "proyecto_maria/core/maria_generator.py",
-     "    if str(tipo_destinacion or \"\").strip().upper().startswith(\"EC\"):",
-     "    if False:", "test_generador_directo_rechaza_ec"),
+     "    tipo_destinacion = destinacion_del_txt(tipo_destinacion)",
+     "    tipo_destinacion = destinacion_del_txt(tipo_destinacion, es_exportacion(tipo_destinacion))",
+     "test_generador_directo_rechaza_ec"),
```

Por qué se habían perdido: el control «una destinación de exportación (EC\*)
no genera un TXT de importación» estaba escrito dos veces, una en el servidor
y otra en el generador, y el guion apagaba cada una con `if False:`.

- `7a2961f` (AVISOS-1) cambió la línea de `main.py` por una expresión
  regular.
- `d7345fa` (AVISOS-1) dejó un solo predicado, `es_exportacion`, y sacó la
  línea de `maria_generator.py`.
- `217c7cd` (AVISOS-2) lo metió en `destinacion_del_txt`, que el servidor
  llama a través de `_destinacion_o_400` (`main.py:4947`) desde generar
  (`:5065`) y desde los avisos (`:4978`), y el generador en
  `maria_generator.py:1231`.

Qué ataca cada una ahora:

- **«servidor»:** el ayudante por el que pasan las dos rutas devuelve la
  destinación sin mirarla. El generador sigue controlando.
- **«generador»:** el generador acepta el tipo que venga (le dice a
  `destinacion_del_txt` que es de exportación cuando lo es). El control de
  forma del código queda; el servidor sigue controlando.

La mutación «clasificacion» no cambió: su ancla está una vez
(`pdf_extractor.py:2028`). Los nombres y las pruebas que espera cada una
tampoco.

## Resultado

| qué | antes, guion de `a926930` | ahora, `d4c6b73` |
|---|---|---|
| el guion | 1 `OK` y corta: `AssertionError: Patrón cambiado: servidor`; `rc=1` | 3 `OK` (`clasificacion`, `servidor`, `generador`); `rc=0` |
| mi línea en `sabotajes-conocidos.txt` | estaba | no está; quedan 2 `vencido` |

El guion sólo dice `OK`. Que cada rojo es por el motivo que dice, medido a
mano sobre el producto de `a926930` (el mismo de `d4c6b73`), en un worktree
descartable, con `tests/test_doc1_documentos.py` entero:

| mutación | resultado | pruebas en rojo |
|---|---|---|
| ninguna | `74 passed` | |
| «servidor» | `38 failed, 36 passed` | sólo `test_ec_directa_nunca_entra_a_importacion`: los 19 datos de exportación en las dos rutas. Generar: `assert ('exportación' in 'No hay productos para generar: volvé a cargar la factura.') is True`. Avisos: `assert ('exportación' in 'None') is True`. Los dos datos `IC04` siguen verdes |
| «generador» | `5 failed, 69 passed` | sólo `test_generador_directo_rechaza_ec`, sus 5 datos: 3 con `Failed: DID NOT RAISE ValueError` y los 2 con un invisible adelante con `AssertionError: Regex pattern did not match` (el error que llega es el de forma, `Destinación: va un código de 4 letras o números, como EC01.`, no el de exportación) |

Cada mutación pone en rojo sólo su prueba, y la del otro lado sigue verde:
son dos causas, no una repetida.

## Revisión adversarial

Pieza chica de arnés: un adversario Sonnet, esfuerzo medio, sobre `d4c6b73`,
en un worktree propio que retiró al terminar. Corrió el guion (3 `OK`) y
aplicó cada mutación a mano.

**Defectos del diff: ninguno.**

| qué probó | resultado | lo reproduje |
|---|---|---|
| «servidor» a mano | `38 failed, 2 passed` con `-k` del caso; rojo por `assert ('exportación' in 'None') is True`, no por un choque | sí, antes que él, con el archivo entero (tabla de arriba) |
| «generador» a mano | `5 failed`: 3 `DID NOT RAISE` y 2 por el mensaje de forma | sí, ídem |
| las dos anclas | cada una, una vez en su archivo, en código y en el control real | sí: `count == 1` en `main.py` y en `maria_generator.py` |
| una mutación parecida o más chica que deje todo verde | no la encontró. Probó `exportacion or es_exportacion(...)` en el ayudante y `pass` en las dos llamadas (`:4978` y `:5065`): `38 failed` las dos | no las repetí: no cambian nada del guion. Una duda sobre la primera: `main.py` no importa `es_exportacion`, así que puesta ahí su rojo sería un `NameError` y no una aserción; su informe no dice en qué archivo la puso |
| un choque a propósito (`destinacion_del_txt_roto`) | `NameError`; el segundo `assert` del guion lo rechaza | sí: con esa mutación en un worktree, el guion corta en `assert "DID NOT RAISE" in salida or "AssertionError" in salida`, `rc=1` |
| lo que saqué de `sabotajes-conocidos.txt` | sólo la línea de `sabotaje_doc1.py` | sí, es el `diff` |

Sus tres observaciones:

- **El control del guion es flojo** (previo): le alcanza con un dato en rojo
  y con cualquier rojo por aserción. Va como riesgo 2.
- **«servidor» apaga el ayudante entero**, también el lado de la exportación
  (`main.py:5307`), que `test_doc1_documentos.py` no mira. Lo medí: con esa
  mutación, `tests/test_avisos2.py` da `26 failed, 55 passed` en tres
  pruebas. Va como riesgo 3.
- **El mensaje del commit:** dijo que no comprobó «cada una pone en rojo
  sólo su prueba». Yo sí, con el archivo entero (tabla de arriba). También
  dijo que el pie del commit debería nombrar otro modelo: no es así, el pie
  es el de esta sesión.

No corrí `/code-review`: el SHA que se entrega pasó por el adversario, que es
una de las dos que pediste.

## Comandos

El guion mide el `HEAD` del árbol donde corre: va en un worktree parado en el
SHA.

```bash
VENV=/ruta/a/tu/venv
git diff a926930 d4c6b73 --stat -- scripts docs/pm/herramientas | tail -1    # 2 files changed, 5 insertions(+), 5 deletions(-)
git worktree add -q --detach /tmp/doc1 d4c6b73 && cd /tmp/doc1
$VENV/bin/python scripts/testing/sabotaje_doc1.py; echo $?
#   DOC-1 negativo clasificacion: rojo por guarda desactivada (OK)
#   DOC-1 negativo servidor: rojo por guarda desactivada (OK)
#   DOC-1 negativo generador: rojo por guarda desactivada (OK)
#   0
grep -c sabotaje_doc1 docs/pm/herramientas/sabotajes-conocidos.txt    # 0
grep -c '^vencido' docs/pm/herramientas/sabotajes-conocidos.txt       # 2

# el rojo sin el arreglo: el guion de la base
git checkout -q a926930
$VENV/bin/python scripts/testing/sabotaje_doc1.py 2>&1 | tail -1; echo ${PIPESTATUS[0]}
#   AssertionError: Patrón cambiado: servidor
#   1
```

Corrí cada uno una vez, con la salida a un archivo; esas son sus líneas. El
guion lo corrí en mi árbol parado en cada SHA, no en `/tmp/doc1`.

## Puertas

Sobre `d4c6b73`, árbol limpio.

| puerta | salida |
|---|---|
| `sabotaje_doc1.py` | 3 `OK`; `rc=0` |
| `tests/test_doc1_documentos.py` y `tests/test_anclas_perdidas.py` | `101 passed` (74 y 27) |
| `anclas_perdidas.py d4c6b73` | `103 guiones, 2493 anclas medidas y 11 llamadas sin medir`; `perdida, una línea 2 guiones: 2`, `perdida, varias líneas 0`, `otra cantidad 0`; `rc=0`. No mide este guion: sólo lee los `.sh` (riesgo 1) |
| `chequeo-6.py a926930 d4c6b73` | abajo, `avisos: 0` |

**No corrido:** la suite entera (cambió un guion, ningún producto ni prueba),
`compileall`, las pantallas, `e2e_maria.sh`, `smoke_friccion.sh`,
`ataque_aislamiento.sh`, Postgres, los demás guiones de sabotaje,
`/code-review` y `/security-review` (el diff no toca producto; lo que el
guion ataca sí es un control de qué se genera, y por eso medí cada mutación
a mano).

## `chequeo-6`

```
chequeo-6 a926930..d4c6b73: avisos para mirar, no un veredicto
producto +0/−0
arnés +5/−4
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Riesgos

1. **`anclas_perdidas.py` no mide este guion.** Sólo lee los `.sh`, y este
   es el único guion de sabotaje en Python. Si sus anclas se vuelven a
   perder, lo avisa el propio guion al correr (`Patrón cambiado: <nombre>`,
   `rc=1`), no la medición. Es previo; severidad baja.
2. **El guion acepta un rojo sin mirar mucho la causa.** Le alcanza con que
   falle un dato del caso, y con que la salida diga `DID NOT RAISE` o
   `AssertionError`: un 500 que haga fallar el `assert` de la prueba pasaría.
   Un `NameError` no pasa (medido). Tampoco corre la prueba sin sabotaje. Lo
   cubrí a mano (`74 passed` en la base y las dos tablas de arriba). Es
   previo; severidad baja.
3. **«servidor» es más ancha que su prueba.** Apaga el ayudante entero: el
   control de exportación, el de forma y el del lado de la exportación. No
   debilita este guion (su prueba da rojo por lo suyo). La llamada de los
   avisos y la de la exportación las ataca más fino `sabotajes/avisos2.sh`.
   No la angosté porque `main.py` no importa `es_exportacion`: apagar ahí
   sólo el control de exportación sería un `NameError`.
4. **El guion mide el `HEAD` del árbol donde está**, no un SHA que se le
   pase. Es previo.

## Líneas para `COLA-LIMPIEZA.md`

- `scripts/testing/sabotaje_doc1.py`: es el único guion de sabotaje en
  Python y `anclas_perdidas.py` no lo lee; no recibe un SHA (mide `HEAD`); no
  corre la prueba sin sabotaje y acepta cualquier rojo por aserción.

## Archivos de producto que toqué

Ninguno.

## Sigo con

El vencido `scripts/testing/sabotaje_maria7.sh` (1 ancla que no está, la de
la línea 97). Primero miro si la protección sigue existiendo.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `607272c`). Aceptadas: CUIT-GENERAR sobre `29327d2`, SABOTAJE-SUBITEMS1 sobre `bf6778e`, D243 (b) sobre `0dff850`, SABOTAJE-SUFIJOS1 sobre `afeae84`, D245 (a) sobre `e17c11e`, D246 (b) sobre `0224f01`, SABOTAJE-MARIA8 sobre `50320ff`, D247 (a) sobre `4a58c68`, D248 (c) sobre `3fcc9c4`, el vencido `sabotaje_maria1d.sh` sobre `6e4e658`, el vencido `sabotaje_maria5.sh` sobre `c0505cc`. Entregadas sin veredicto: **el vencido `sabotaje_valor1b.sh` sobre `70eb5dc`** (22 `ROJO`; el `echo` final pasó de 23 a 22 como supuesto reversible) y **el vencido `sabotaje_doc1.py` sobre `d4c6b73`** (base `a926930`; sólo `scripts/testing/sabotaje_doc1.py` y mi línea fuera de `sabotajes-conocidos.txt`, arnés +5/−4; 3 `OK`, `rc=0`; «servidor» ataca `_destinacion_o_400` en `main.py` y «generador» la llamada a `destinacion_del_txt` en `maria_generator.py`; a mano, 38 y 5 fallas, cada una sólo en su prueba; un adversario Sonnet medio revisó `d4c6b73`, sin defectos; `anclas_perdidas.py` no mide este guion). Si alguna vuelve con devolución, va primero. **Pieza activa: el vencido `scripts/testing/sabotaje_maria7.sh`** (1 ancla que no está, línea 97: `sufijo_sbt = limpiar_sufijo((sbt_sufijo_valor or "").strip(), " de la operación")[0]`; hoy el generador tiene `return limpiar_sufijo(…)[0]` en `maria_generator.py:1523`: falta comprobar que la prueba `test_dentro_del_sufijo_solo_letras_numeros_y_espacios` sigue distinguiéndolo); después guardar2 (74); al arreglar cada uno saco mi línea de `docs/pm/herramientas/sabotajes-conocidos.txt`. Después **D249 (a)**, decidida por la PM: sólo `tests/test_sufijos2.py` y `scripts/testing/sabotajes/sufijos2.sh`, criterio entero en `docs/pm/PARA-DEV-2.md`, sección D247 (la familia de fragmentos «…» de `limpiar_sufijo`, un sabotaje por cambio, `sufijos2.sh` entero en `ROJO` con la cuenta exacta, `sabotaje_sufijos1.sh` en 46, anclas que no empeoran: el criterio dice 5 y 1 y hoy son 2 y 0). D244, D239 y «Holanda» esperan a Emi: no se tocan. Próxima D: D250. Lecciones: antes de lanzar algo en segundo plano se borra su marca de fin; un texto de error que manda a corregir se prueba por cada origen del dato; una prueba que sólo mira el 200 de un endpoint que se traga sus errores no prueba nada; un dato nuevo de un caso no reusa un valor que otro control del mismo caso espera; antes de escribir el informe se trae la rama de la PM; antes de sacar una prueba por duplicada se compara lo que afirma cada una, no sólo sus entradas; antes de reescribir un sabotaje con el ancla perdida se mira si la protección que atacaba sigue existiendo: si no, es una D (D195 (a)); al ajustar una afirmación, la nueva tiene que seguir afirmando todo lo que afirmaba la vieja (el orden también), y una mutación que «mueve» una frase la tiene que sacar de donde estaba; una medición corre sobre el conjunto más angosto de pruebas que contesta la pregunta; antes de cambiar un número que la PM fijó como criterio se lee por qué lo fijó; un comentario o un mensaje de commit no afirma lo que el guion no obliga, y su porqué se comprueba con `git show`, no se supone; que «nadie cubría» algo se mide antes de escribirlo; `anclas_perdidas.py` mide un commit: el arreglo se commitea antes de medir; el SHA que se entrega pasa por subagente o `/code-review`, y si el gancho de parada ya subió el commit, lo que siga va en un commit nuevo; después de un commit nuevo o de corregir uno, las puertas corren otra vez sobre ese SHA; un ancla lleva sólo el texto que saca más lo mínimo que la ata a su lugar; la cuenta escrita a mano en el último `echo` de un guion se compara con sus líneas `ROJO`; una mutación se mide a mano con el archivo de pruebas entero, para ver que pone en rojo sólo lo suyo y por aserción; `anclas_perdidas.py` sólo lee los `.sh`; regla de la PM: en un vencido de sólo arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice, cualquier otro cambio sí. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica salvo lo que una D autoriza; subagentes hasta esfuerzo alto y sin consejero.
