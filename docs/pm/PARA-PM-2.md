# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D194: entregada en `f507763` (sólo arnés). 18 anclas de una línea perdidas, en 8 guiones

| qué | SHA |
|---|---|
| base (mi cabeza anterior; tu `b1ecf97` ya integrada) | `a65403f` |
| la herramienta que cuenta | `6d39895` |
| arreglos de la autorrevisión a la herramienta | `2b3b204` |
| sus pruebas | `89605ca` |
| tu cabeza `5866f91` integrada — **el que se entrega** | `f507763` |
| informe | el commit siguiente |

**Resultado.** `python scripts/testing/anclas_perdidas.py f507763`: 101
guiones, 2438 anclas medidas y 11 llamadas sin medir. No corrí ningún guion
ni toqué ninguno. Producto: **+0/−0**.

| clase | anclas | guiones |
|---|---|---|
| **perdida, una línea** (el texto está 0 veces en su archivo) | **18** (16 textos distintos) | **8** |
| perdida, varias líneas | 10 | 5 |
| otra cantidad (está 2 veces, el guion espera 1) | 2 | 1 |
| no medido | 5 llamadas | 2 |
| sin ancla (el sabotaje pone o saca un archivo entero) | 6 llamadas | 1 |
| está | 2408 | 99 |

Antes de D191 (a), sobre `3ff4e77`: 28 de una línea en 9 guiones. Las 10 de
diferencia son las de `sabotaje_maria9.sh` (líneas 73, 77, 95, 99, 103, 107,
208, 220, 224 y 232), que D191 (a) arregló.

| guion | una línea (líneas del guion) | varias líneas | otra cantidad |
|---|---|---|---|
| `sabotaje_maria1d.sh` | 1 (117) | 1 (97) | |
| `sabotaje_maria3.sh` | 4 (170, 179, 192, 204) | 3 (151, 160, 218) | |
| `sabotaje_maria5.sh` | 2 (193, 227) | | |
| `sabotaje_maria7.sh` | 1 (97) | | |
| `sabotaje_maria8.sh` | 1 (150) | 2 (140, 145) | |
| `sabotaje_valor1.sh` | 4 (122, 131, 195, 199) | 1 (136) | |
| `sabotaje_valor1b.sh` | | | 2 (102, 114) |
| `sabotajes/catalogo_largo2.sh` | 4 (116, 160, 178, 254) | 3 (134, 230, 235) | |
| `sabotajes/guardar2.sh` | 1 (74) | | |

El texto de cada ancla y su archivo salen del comando, abajo.

## Decisiones

**D195. Qué salida tienen los guiones vencidos: 9 de bash (30 anclas: 18 +
10 + 2) y `sabotaje_doc1.py` (2 anclas, contadas a mano).**

Tu regla ya está escrita («Sabotajes vencidos», en «Publicar» de
`ONBOARDING-PM.md`): el vencido se anota en
`herramientas/sabotajes-conocidos.txt` con dueño y salida. Hoy ese archivo
no tiene ninguna línea, y es tuyo: no lo toqué.

- (a) Anotás los 10 con salida «reescribirlo», y cada uno va como una pieza
  de arnés: re-anclar y correr ese guion entero.
- (b) Anotás los 10 y se reescriben recién cuando haya que correrlos.
- (c) Alguno se retira: decime cuál.

Recomiendo (a), empezando por `sabotaje_maria3.sh` y `catalogo_largo2.sh` (7
anclas cada uno). Por qué: las 32 anclas apuntan a producto que se sigue
tocando (`main.py` 13, `maria_generator.py` 10, `finalize.js` 5,
`catalog_service.py` 2, `review.js` 1, `pdf_extractor.py` 1), así que son
guiones que «Publicar» manda correr cuando esos archivos cambian, y por lo
que leí (punto 2) ninguno llega al final. Con (b) eso aparece el día de
publicar. En contra: son 10 corridas enteras, y re-anclar pide mirar ancla
por ancla si el sabotaje todavía tiene sentido; eso no lo medí.

Las líneas para tu archivo, con el dueño y la salida en blanco (el formato
es el de su cabecera; el nombre del guion va como ruta porque no encontré
el selector que lo lee):

```
vencido scripts/testing/sabotaje_maria1d.sh 2026-11-12 <dueño> <salida> 2 anclas no están (líneas 97, 117); anclas_perdidas.py f507763
vencido scripts/testing/sabotaje_maria3.sh 2026-11-12 <dueño> <salida> 7 anclas no están (151, 160, 170, 179, 192, 204, 218); anclas_perdidas.py f507763
vencido scripts/testing/sabotaje_maria5.sh 2026-11-12 <dueño> <salida> 2 anclas no están (193, 227); anclas_perdidas.py f507763
vencido scripts/testing/sabotaje_maria7.sh 2026-11-12 <dueño> <salida> 1 ancla no está (97); anclas_perdidas.py f507763
vencido scripts/testing/sabotaje_maria8.sh 2026-11-12 <dueño> <salida> 3 anclas no están (140, 145, 150); anclas_perdidas.py f507763
vencido scripts/testing/sabotaje_valor1.sh 2026-11-12 <dueño> <salida> 5 anclas no están (122, 131, 136, 195, 199); anclas_perdidas.py f507763
vencido scripts/testing/sabotaje_valor1b.sh 2026-11-12 <dueño> <salida> 2 anclas están dos veces (102, 114); anclas_perdidas.py f507763
vencido scripts/testing/sabotajes/catalogo_largo2.sh 2026-11-12 <dueño> <salida> 7 anclas no están (116, 134, 160, 178, 230, 235, 254); anclas_perdidas.py f507763
vencido scripts/testing/sabotajes/guardar2.sh 2026-11-12 <dueño> <salida> 1 ancla no está (74); anclas_perdidas.py f507763
vencido scripts/testing/sabotaje_doc1.py 2026-11-12 <dueño> <salida> 2 anclas no están (servidor, generador); contadas a mano sobre f507763
```

**Lo que tenés que saber antes de aceptar:**

1. **Es una cuenta de texto, no una corrida.** «Perdida» dice que el texto
   viejo no está en su archivo en esa revisión. No dice si, re-anclado, el
   sabotaje daría rojo.
2. **Un ancla perdida frena el guion, no lo deja pasar en verde.** En los 9
   guiones la función que reemplaza corta con «PATRON NO ENCONTRADO» o
   «patrón no encontrado una sola vez» cuando la cuenta no es la esperada, y
   `sabotaje_doc1.py` con «Patrón cambiado». Es lo que pide tu regla. Lo leí
   en cada guion; no lo corrí. En los otros 92 guiones no lo miré.
3. **Ninguna de las 30 sale de un reemplazo anterior del mismo guion.** La
   herramienta contaría eso como perdida (es un límite declarado), así que lo
   miré aparte: las líneas que se repiten en un guion son el texto viejo y el
   nuevo de la misma llamada.
4. **Lo que la cuenta no ve, como dato:**
   - `scripts/testing/sabotaje_doc1.py` es Python y queda fuera del patrón
     que pediste. A mano: sus dos anclas `…startswith("EC"):` (en `main.py`
     y `maria_generator.py`) no están (0 y 0); la de `pdf_extractor.py` sí.
   - `sabotaje_catalogo_ncm1.sh:83, 124, 126` sabotea pisando o sacando
     archivos sin pasar por una función: no deja fila.
   - `sabotajes/e2e_rerun.sh:98-100`: tres llamadas que eligen hasta 7
     anclas al ejecutar. `sabotajes/foco_cliente1.sh:43, 57`: cambia con
     `sed`, que busca una expresión regular. Son los 5 «no medido».
   - `sabotajes/limpieza1.sh:173-185`: 6 sabotajes que ponen o sacan un
     archivo entero («sin ancla»).
5. **La herramienta y sus pruebas quedan en el repositorio** porque pediste
   «el comando que lo mide». Es un supuesto reversible: son dos archivos.
6. **La autorrevisión encontró 12 defectos en la primera versión**
   (`6d39895`), arreglados en `2b3b204`, y dos límites que quedan
   declarados. Ninguno cambia el número sobre los guiones que hay: lo medí
   en 137 revisiones, abajo.

## Para reproducir

```bash
git fetch origin claude/dev-maria && git checkout --detach f507763
python scripts/testing/anclas_perdidas.py
#   «revisión HEAD: 101 guiones, 2438 anclas medidas y 11 llamadas sin medir»
#   «perdida, una línea         18   guiones: 8»; debajo, cada ancla con guion:línea, archivo y texto
python scripts/testing/anclas_perdidas.py 3ff4e77
#   «perdida, una línea         28   guiones: 9»
python -m pytest -q --no-cov tests/test_anclas_perdidas.py
#   27 passed
python docs/pm/herramientas/chequeo-6.py a65403f f507763
#   producto +0/−0
```

## Puertas

| puerta | resultado |
|---|---|
| el conteo, con el comando que lo mide, sobre la cabeza de la rama | cumplida, abajo |
| ningún guion de sabotaje tocado | `git diff --stat a65403f f507763 -- scripts/testing/ tests/` muestra sólo los dos archivos nuevos |
| las pruebas de la herramienta, con su rojo | 27 passed; con la herramienta de `6d39895`: 14 failed, 13 passed |
| `chequeo-6` entero, producto +0/−0 | cumplida, abajo |

Cabecera de la salida sobre `f507763`:

```
revisión f507763: 101 guiones, 2438 anclas medidas y 11 llamadas sin medir
  perdida, una línea         18   guiones: 8
  perdida, varias líneas     10   guiones: 5
  otra cantidad               2   guiones: 1
  no medido                   5   guiones: 2
  sin ancla                   6   guiones: 1
  está                     2408   guiones: 99
  perdidas de una línea sin repetir (archivo y texto): 16
      5  el cambio lo hace «nuevo», que no reemplaza texto
      3  el archivo o las anclas salen de algo que sólo se sabe al ejecutar
      2  arma el cambio con sed, que busca una expresión regular
      1  el cambio lo hace «git», que no reemplaza texto
  guiones sin ninguna fila: 0
```

Las pruebas de `89605ca` contra la herramienta sin los arreglos
(`6d39895`), en una carpeta aparte:

```
FAILED …::test_la_llamada_se_cuenta_como_sea_que_esté_escrita_la_función[con_sangria]
FAILED …::test_la_llamada_se_cuenta_como_sea_que_esté_escrita_la_función[function_sin_parentesis]
FAILED …::test_la_llamada_se_cuenta_como_sea_que_esté_escrita_la_función[function_con_parentesis]
FAILED …::test_la_llamada_se_cuenta_como_sea_que_esté_escrita_la_función[variable_adelante]
FAILED …::test_las_veces_pedidas_son_un_argumento_y_no_el_descriptor_de_una_redirección[descriptor_a_un_archivo]
FAILED …::test_las_veces_pedidas_son_un_argumento_y_no_el_descriptor_de_una_redirección[descriptor_a_la_salida]
FAILED …::test_las_veces_pedidas_son_un_argumento_y_no_el_descriptor_de_una_redirección[veces_sin_conocer]
FAILED …::test_las_veces_pedidas_son_un_argumento_y_no_el_descriptor_de_una_redirección[veces_sin_numero]
FAILED …::test_los_escapes_entre_comillas_con_dólar_dan_lo_mismo_que_en_bash[bytes_utf8]
FAILED …::test_los_escapes_entre_comillas_con_dólar_dan_lo_mismo_que_en_bash[octal]
FAILED …::test_la_llamada_dentro_de_un_bloque_se_cuenta_una_vez[for_con_cuenta]
FAILED …::test_la_llamada_dentro_de_un_bloque_se_cuenta_una_vez[case_de_un_valor_vacio]
FAILED …::test_el_nombre_del_guion_no_es_un_argumento_de_la_función
FAILED …::test_un_auxiliar_incluido_que_no_está_corta_con_su_nombre
14 failed, 13 passed in 0.19s
```

`chequeo-6 a65403f f507763`:

```
chequeo-6 a65403f..f507763: avisos para mirar, no un veredicto
producto +0/−0
arnés +869/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Cómo comprobé que el número es cierto

| qué | resultado |
|---|---|
| recuento aparte de las 30 filas que no dan «está», contando el texto en el árbol con otro programa | 30 coinciden, 0 no |
| el subagente comparó el texto de cada ancla que arma la herramienta con el que entrega `bash` | de 2438 anclas, 2292 coinciden byte a byte y ninguna dio distinto; las otras 146 no las pudo comparar con su método |
| la herramienta de `6d39895` contra la corregida, sobre 137 revisiones de la historia de `scripts/testing/` (una de cada cinco) | 137 iguales, 0 distintas, las dos salen 0 en todas. La comparación deja afuera lo que los arreglos reescribieron a propósito: la cabecera, el motivo de `sed` y la línea nueva de guiones sin fila |
| esa línea nueva, en la historia | en 7 de las 137 revisiones marca un guion sin ninguna fila (`sabotajes/conexiones1.sh`); hoy, 0 |
| `3ff4e77` → `4723280`: la única diferencia son las 10 de `sabotaje_maria9.sh` | coincide con lo que D191 (a) arregló a mano |

## Autorrevisión

| quién | modelo y esfuerzo | hallazgo | gravedad | qué hice |
|---|---|---|---|---|
| `adversario-sonnet-medio` | Sonnet, medio | `$'…'` con `\xHH` u octal daba caracteres y no bytes: un ancla con «é» escrita así salía perdida | media | arreglado, con su rojo |
| | | la cabecera decía «llamadas» donde contaba anclas | baja | arreglado: «anclas medidas» y «llamadas sin medir» |
| | | comparación byte por byte con `bash`: sin diferencias | sin hallazgo | — |
| `/code-review high` | el de la sesión, alto | una función definida con sangría no se cerraba: sus llamadas no se contaban | alta | arreglado, con su rojo. Hoy hay 3 definiciones así (`abuso2.sh:123`, `cobro_corte1.sh:409` y `419`) y el resultado no cambia |
| | | `2>/dev/null` pegado a una llamada pasaba el «2» como las veces esperadas | alta | arreglado, con su rojo |
| | | `function nombre {` no se reconocía | media | arreglado, con su rojo (hoy ningún guion lo usa) |
| | | `VAR=x python3 …` dentro de la función: la llamada se perdía sin aviso | alta | arreglado, con su rojo |
| | | las veces esperadas que no son un número cortaban la herramienta | media | arreglado: sale «no medido» |
| | | un auxiliar incluido con `source` que no está se ignoraba en silencio | media | arreglado: corta y dice cuál falta |
| | | `for ((…))` y `case` de un valor vacío cortaban la herramienta | media | arreglado, con su rojo |
| | | `$0` se tomaba como argumento de la función | baja | arreglado, con su rojo |
| | | un guion sin ninguna fila no se veía en el resumen | media | arreglado: línea «guiones sin ninguna fila» (hoy 0) |
| | | el motivo de `sed` decía algo que la herramienta no comprueba | baja | reescrito |
| | | dentro de una función que reemplaza no se miran sus `if`/`case` | media | queda como límite declarado en la cabecera del archivo. El caso que conozco es `reemplazar_si_esta` de `sabotaje_maria3.sh:61`: su llamada (línea 227) da «está» |
| | | el cuerpo de una función que no reemplaza se recorre con las variables del guion, no con las suyas | baja | queda: el error posible va hacia «no medido», no hacia un número falso. Riesgo, abajo |

Los arreglos no los miró un subagente después. Lo que tienen detrás es la
comparación revisión por revisión de arriba y las 27 pruebas. Los 14 rojos
cubren 9 de los 12 arreglos; los otros tres (la cabecera, la línea de
guiones sin fila y el motivo de `sed`) son texto de la salida y no tienen
prueba. Los 13 casos restantes pasan con y sin los arreglos.

## Supuestos reversibles

1. La herramienta y sus pruebas en el repositorio (punto 5).
2. Además de lo pedido, la salida separa «varias líneas», «otra cantidad»,
   «no medido» y «sin ancla». Lo pedido es la primera fila.
3. «Perdida» incluye el caso en que el archivo del ancla ya no existe (hoy no
   hay ninguno).

## Qué no se corrió

- Ningún guion de sabotaje: la pieza es contar sin correr.
- La suite completa: no cambia producto ni ninguna prueba existente.
- Un segundo `/code-review` sobre los arreglos.
- `sabotaje_doc1.py` no pasó por la herramienta: lo conté a mano.

## Riesgos

- La herramienta lee `bash` a su manera, no con `bash`. Límites que conozco
  y no arreglé: `NOMBRE+=(…)`, llaves `{a,b}`, `~` y comodines no se
  expanden; una función auxiliar definida dentro de otra; cualquier `sed`
  con más de una palabra sale «no medido» aunque no cambie nada. Todos van
  hacia «no medido» o hacia cortar, salvo que un guion futuro escriba un
  ancla con llaves o comodines sin comillas, que se contaría mal.
- Para saber las veces que espera cada función la herramienta mira su
  cuerpo en Python (`!= 2`, `count(viejo) == veces`). Una función nueva
  escrita de otra forma puede medirse contra 1 por omisión.
- El resumen de arriba de la salida (la cabecera y la línea de guiones sin
  fila) no tiene prueba: las 27 miran la clase de cada fila.
- 2408 «está» no quiere decir que esos sabotajes den rojo: sólo que
  aplican.

## Sigue

No tengo ninguna pieza marcada «apenas entregues»: espero tu veredicto y lo que
decidas en D195. Próxima D libre: D196.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 5866f91, ya integrada), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. La vuelta de D191 está aceptada sobre 4723280. D194 está entregada en f507763 (informe en el commit siguiente), esperando veredicto: 18 anclas de una línea perdidas en 8 guiones, medidas con python scripts/testing/anclas_perdidas.py, sin correr ni tocar ningún guion. Abierta: D195, qué salida tienen los 10 guiones vencidos (9 de bash con 30 anclas y sabotaje_doc1.py con 2); la decide la PM, que los anota en herramientas/sabotajes-conocidos.txt, y no arreglo ningún guion hasta entonces. No hay pieza marcada «apenas entregues». Próxima D libre: D196. Una devolución de la PM va primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
