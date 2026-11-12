# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Dos cosas, entregadas en `204c638` (sólo arnés): la vuelta de D216/D217 y `catalogo_largo2.sh` re-anclado

| qué | SHA |
|---|---|
| base (tu cabeza `eeec625`, integrada) | `e115e50` |
| **Parte 1.** D216 (b): el sabotaje 31 espera el caso de `-500` | `170cdc0` |
| **Parte 1.** D217 (a): el sabotaje 32, el seguro en avisos | `0baa07b` |
| **Parte 2.** la prueba de Postgres usa el id que arma el producto | `81e81e0` |
| **Parte 2.** las siete anclas | `ac58fb0` |
| **Parte 2.** arreglos de la autorrevisión | `6af3b80`, `a538124`, `204c638` |
| **Parte 2.** el texto de su línea en `sabotajes-conocidos.txt` | `2cc6d18` |
| **el que se entrega** | `204c638` |
| tu cabeza `8f79bcc`, integrada después: no toca producto, estos guiones ni sus pruebas | `829f2d1` |
| informe | el commit siguiente |

**Resultado.**

- **Parte 1.** `sabotaje_maria3.sh` entero da 32 `ROJO` y sale 0. Nada para
  decidir.
- **Parte 2.** `catalogo_largo2.sh` tiene 38 sabotajes. Entero y con
  Postgres, 37 dan `ROJO`. El otro, «la clave junta ﬁ con fi», queda verde
  con su ancla presente: es D199. Lo salteé sólo en una copia local (no
  commiteada): 37 `ROJO`, `fallas: 0`, sale 0. Su línea sigue en
  `sabotajes-conocidos.txt` hasta que decidas.
- Producto: **+0/−0** en las dos.

## Decisiones (todas de la parte 2)

**D199. Retirar el sabotaje «la clave junta ﬁ con fi».** Cambia `NFD` por
`NFKD` en `_normalize` y espera que fallen
`test_lo_que_no_tiene_letras_latinas_se_guarda_sin_cruzarse[catalogo]` y
`[guardar-uso]`. Hoy la clave pasa antes por `_compatible`, que junta «ﬁ»
con «fi» a propósito: `tests/test_catalogo3.py:145` lo exige y
`catalogo3.sh:98` ya tiene el sabotaje de esa línea. Para la clave, el
cambio del sabotaje no cambia nada, y por eso queda verde.
- (a) Lo retiro y sale la línea del guion de `sabotajes-conocidos.txt`.
  **Recomiendo (a)**: lo que protegía ya no es lo que el producto hace, y lo
  que hace hoy tiene su sabotaje en otro guion.
- (b) Queda como está, vencido.

Mientras no decidas, el selector saltea el guion entero por este solo
sabotaje.

**D218. La tabla `operation_items` no tiene sabotaje en el arranque.** El
arranque pasa a texto tres tablas. `catalogo_largo2_postgres.py` no mira la
tercera. `catalogo3_postgres.py` sí: sacándole la tupla a mano da `FALLA |
operation_items.origen pasa a text y la fila vieja queda igual`. Pero ningún
guion de sabotaje corre esa prueba.
- (a) Pieza chica aparte: un sabotaje que saca la tupla y corre
  `catalogo3_postgres.py`. **Recomiendo (a)**: es una migración.
- (b) Queda como riesgo anotado.

**D219. Ninguna prueba fija el id de un proveedor de nombre largo.** Con más
de 60 caracteres, `_vendor_key` arma el id con un corte y un resumen. Cambié
el corte a mano (`[:38]` y `[:21]`) y corrí los 8 archivos de prueba del
catálogo: `256 passed`. Si ese esquema cambia sin querer, los proveedores
largos ya guardados dejan de encontrarse y nada avisa. No corrí la suite
entera con ese cambio.
- (a) Un dato más en `test_un_proveedor_latino_conserva_su_id`: un nombre
  largo con su id escrito. **Recomiendo (a)**: una línea.
- (b) Queda como riesgo anotado.

**D220. Fuera de la clave, «ﬁ» se pierde.** Salió al revisar D199.
`_normalize` sola no junta «ﬁ» con «fi»: la borra. La clave no lo sufre
(pasa por `_compatible`), pero dos lugares llaman a `_normalize` sin ese
paso. Medido llamando a las funciones, no por la pantalla:

| «Arandela ﬁna» | da |
|---|---|
| `clave_de_producto` | `arandela fina` |
| `_word_set` (el parecido entre descripciones) | `['arandela']` |
| `_norm_desc` (`descripcion_normalizada` del cliente) | `arandela na` |

La búsqueda exacta anda. El parecido pierde la palabra que trae la
ligadura. No medí si alguna factura real llega con ligaduras.
- (a) A la cola de limpieza: que esos dos lugares pasen por `_compatible`,
  con su caso. **Recomiendo (a)**, sin apuro.
- (b) No se hace nada.

---

## Parte 1. Vuelta de D216 y D217 (`sabotaje_maria3.sh`)

Hice lo que decidiste, sin supuestos:

- **31** (`170cdc0`): espera `[/generate_maria/avisos-flete--500]`.
- **32** (`0baa07b`): saca sólo `importe_valido(request.seguro, "Seguro")`
  del endpoint y espera `[/generate_maria/avisos-seguro-nan]`.

### Para reproducir

```bash
bash scripts/testing/sabotaje_maria3.sh 204c638 <venv>
# VERDE sin sabotaje: 136 passed; 32 líneas ROJO;
# «OK: los 32 sabotajes dan rojo por la razón esperada»; sale 0
python scripts/testing/anclas_perdidas.py 204c638 | grep -c sabotaje_maria3
# 0
```

### Puertas

| puerta | sobre | salida |
|---|---|---|
| guion entero | `0baa07b` | `VERDE  sin sabotaje: 136 passed`; 32 `ROJO`; `ROJO   avisos_flete_sin_validar: 2 failed, 134 passed`; `ROJO   avisos_seguro_sin_validar: 2 failed, 134 passed`; `OK: los 32 sabotajes dan rojo por la razón esperada`; `rc=0 segundos=216` |
| la mutación 32 a mano | antes de escribir el sabotaje | `2 failed, 134 passed`: `avisos-seguro-nan` y `avisos-seguro-1e+308` |
| la mutación 31 a mano | antes de cambiar el id | el caso de `-500` falla con `assert 200 == 400`; `2 failed, 134 passed` |
| `anclas_perdidas.py` | `0baa07b` | ninguna fila de `sabotaje_maria3.sh` |
| `chequeo-6.py e115e50 0baa07b` | | abajo, entera |

El guion entero corrió sobre `0baa07b`, no sobre `204c638`. Entre los dos no
cambió el guion, su prueba ni el producto:
`git diff --stat 0baa07b 204c638 -- scripts/testing/sabotaje_maria3.sh tests proyecto_maria`
da vacío.

```
chequeo-6 e115e50..0baa07b: avisos para mirar, no un veredicto
producto +0/−0
arnés +6/−2
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

No hubo rojos intermedios.

### Hallazgos de la autorrevisión (parte 1)

| quién | hallazgo | severidad | qué hice |
|---|---|---|---|
| adversario Sonnet, medio | El rojo del 32 sale por lo que dice su comentario; el id esperado no es prefijo de otro; el ancla está una vez (corrió las mutaciones 31 y 32 a mano) | — | nada |
| adversario Sonnet, medio | `gastos_fob` y `gastos_anteriores_fob` sin sabotaje: sacando sus dos líneas, `136 passed`; antes las valida `gastos_fob_para_el_txt` | baja | nada: es lo que mediste vos |
| adversario Sonnet, medio | `caso` acepta cualquier rojo que traiga el id esperado, aunque venga de otra causa. No encontró un caso concreto | baja | nada: viene de antes. Riesgo anotado |
| `/code-review high` (revisores Fable, alto) | El «32» del mensaje final se cambia a mano | baja | no lo toqué: viene de antes. Repito la propuesta para la cola: «`sabotaje_maria3.sh`: contar los casos en `caso` en vez de escribir el número» |

---

## Parte 2. `catalogo_largo2.sh` re-anclado

### Supuestos (reversibles)

1. **La prueba de Postgres estaba en rojo sin sabotaje** (`81e81e0`). Tenía
   escrito a mano el id de un proveedor de nombre largo, y el producto hoy
   lo arma distinto. Ahora lo pide a `_vendor_key`, como ya hacía
   `tests/test_catalogo_largo2.py`. De ahí sale D219.
2. **Los tres sabotajes «no mide el origen»** (catálogo, cambiar,
   guardar-uso) anclan en la línea que llama a `origen_para_guardar` en cada
   lugar.
3. **Un sabotaje nuevo, «el origen no se mide»** (`a538124`). Con el
   supuesto 2, nada tocaba la línea de adentro de `origen_para_guardar` que
   mide. Usa el mismo molde que «el catálogo no mide el proveedor». El
   `/code-review` objeta que espera los mismos tres casos que los del
   supuesto 2 y que saca más que la medida; lo dejé porque los casos
   esperados son los del tope. Suma unos 40 s al guion. Si no lo querés, lo
   saco.
4. **«La migración de claves no mueve nada»** ancla en `no_ascii = "GLOB`
   (antes `sin_latinas = "NOT GLOB`). En Postgres espera
   `FALLA | «螺丝钉» de una fila vieja es una sola fila y sigue editable`.
5. **Los tres sabotajes «el arranque no pasa … a text»** esperan
   `FALLA | primer arranque: las columnas son text` (`204c638`). Esperaban
   «arranque: las columnas son text», que la prueba también imprime en sus
   líneas `OK`: se cumplía con o sin sabotaje. Es el texto que ya usa
   `catalogolargo1.sh`.
6. **El sabotaje de la transacción** incluye la tercera tabla en su ancla y
   se llama «el arranque traba las tablas en una transacción» (`6af3b80`).
7. **El texto de la línea del guion en `sabotajes-conocidos.txt`**
   (`2cc6d18`) dice lo que le falta hoy: D199.

### Qué cambió en cada sabotaje

| sabotaje | ancla de hoy |
|---|---|
| guardar en el catálogo no mide el origen | `origen, aviso = origen_para_guardar(prod.get("origen"))` |
| cambiar el origen no lo mide | `origen, aviso = origen_para_guardar(updates["origen"])` |
| guardar-uso no mide el origen | `origin, aviso_origen = catalog_svc.origen_para_guardar(data.get("origen"))` |
| el origen no se mide (nuevo) | `origen = texto_para_guardar(valor, "El origen")` |
| la migración de claves no mueve nada (SQLite y Postgres) | `no_ascii = "GLOB` |
| el arranque no pasa el origen de la memoria del cliente a text | la línea de `client_product_history`, que ya no es la última de la lista |
| el arranque traba las tablas en una transacción | la lista de las tres tablas |

### Para reproducir

```bash
# Postgres local y descartable; unos 23 minutos
PY=<venv>/bin/python scripts/testing/con_pg16.sh bash -c \
  'PG_URL="$BACKUP1A_PG_URL" bash scripts/testing/sabotajes/catalogo_largo2.sh 204c638'
# 37 ROJO y «VERDE | la clave junta ﬁ con fi: la prueba no lo vio»;
# fallas: 1; sale 1. Ese verde es D199.
python scripts/testing/anclas_perdidas.py 204c638 | grep -c catalogo_largo2
# 0
```

Así, con el guion commiteado, no lo corrí yo: corrí una copia local que
saltea ese sabotaje, como pide tu regla. El verde de «ﬁ» lo vi en la corrida
del guion viejo sobre `8c4a434`; desde ahí no cambiaron ni el producto ni
esas líneas del guion. La copia difiere en esto:

```
31c31
< sabotaje() {
---
> _sabotaje_real() {
56a57
> sabotaje() { case "$2" in "la clave junta ﬁ con fi") echo "SALTEADO | $2";; *) _sabotaje_real "$@";; esac; }
```

### Puertas

| puerta | sobre | salida |
|---|---|---|
| guion entero con Postgres, «ﬁ» salteado en la copia | `204c638` | 37 `ROJO`, 1 `SALTEADO | la clave junta ﬁ con fi`, `fallas: 0`, `rc=0 segundos=1377`. Los tres «el arranque no pasa … a text» dicen `FALLA | primer arranque: las columnas son text` |
| lo mismo, antes del último arreglo | `a538124` | 37 `ROJO`, 1 `SALTEADO | la clave junta ﬁ con fi`, `fallas: 0`, `rc=0 segundos=1345` |
| `anclas_perdidas.py` | `204c638` | ninguna fila de `catalogo_largo2.sh` ni de `sabotaje_maria3.sh`. En el repo quedan: `perdida, una línea 10 (guiones: 6)`, `perdida, varias líneas 4 (guiones: 3)`, `otra cantidad 2 (guiones: 1)` |
| rojo antes: guion viejo | `8c4a434` | 23 `ROJO`; 4 `ROTO` (los tres del origen y la migración de claves); `VERDE | la clave junta ﬁ con fi: la prueba no lo vio`; `BASE  | la prueba en Postgres ya está en rojo sin sabotaje`; `fallas: 6`; `rc=1 segundos=1022` |
| la prueba de Postgres sin sabotaje | antes y después de `81e81e0` | 3 `FALLA` → 21 `OK`, `fallas: 0` |
| `chequeo-6.py`, por tramo | | abajo, enteras |

La pieza quedó partida por dos integraciones de tu rama, así que `chequeo-6`
va por tramo. Sobre el rango entero cuenta tus documentos como arnés y no
sirve.

```
chequeo-6 8c4a434..ac58fb0: avisos para mirar, no un veredicto
producto +0/−0
arnés +18/−34
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

```
chequeo-6 dd89d03..a538124: avisos para mirar, no un veredicto
producto +0/−0
arnés +6/−2
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

```
chequeo-6 0baa07b..204c638: avisos para mirar, no un veredicto
producto +0/−0
arnés +3/−3
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

### Rojos y errores intermedios

- Guion viejo sobre `8c4a434`: `fallas: 6`. Es el rojo de antes, arriba.
- Mi corrida a mano de `catalogo3_postgres.py` para D218 imprimió la `FALLA`
  de `operation_items` y después se cayó: la lancé sin las variables de
  prueba. Error de mi invocación; no la repetí.
- Una copia local temprana del guion tenía un error de sintaxis mío. Nunca
  estuvo en el repositorio.

### Hallazgos de la autorrevisión (parte 2)

| quién | hallazgo | severidad | qué hice |
|---|---|---|---|
| adversario Sonnet, medio | Los tres sabotajes del origen dan rojo con `assert (200, None) == (400, …)`; el de la migración, con `«螺丝钉» quedó en 2 filas`; las anclas están una vez; con 0 o 2 da `ROTO` | — | nada |
| corrida propia del guion viejo, y `/code-review high` (revisores Fable, alto), primera pasada | «ﬁ» queda verde con el ancla presente | media | D199 |
| adversario Sonnet, medio | El nombre del sabotaje de la transacción contaba las tablas | baja | arreglado en `6af3b80` |
| adversario Sonnet, medio (por lectura) y `/code-review high`, primera pasada | `operation_items` sin sabotaje. El revisor midió `fallas: 0` con la tupla sacada; eso no lo reproduje yo, sí la `FALLA` de `catalogo3_postgres.py` | media | D218 |
| adversario Sonnet, medio, y `/code-review high`, primera pasada | Ninguna prueba fija el id de un proveedor largo | media | D219, reproducido |
| `/code-review high`, primera pasada | Nada tocaba la línea que mide el origen. El adversario había medido que sacarla sola da `6 failed` | media | arreglado en `a538124` (supuesto 3) |
| `/code-review high`, primera pasada | El sabotaje de la migración en Postgres esperaba un texto que también sale en `OK` | media | arreglado en `a538124` |
| `/code-review high`, las dos pasadas | Los otros tres sabotajes del arranque tenían, en su primer texto, el mismo problema. La primera pasada lo nombró de costado y no lo arreglé; la segunda lo trajo como hallazgo | baja | arreglado en `204c638` (supuesto 5) |
| `/code-review high`, segunda pasada | El cambio del sabotaje «ﬁ» no es inocuo fuera de la clave | media | reproducido; D220, y corregí el porqué de D199 |
| `/code-review high`, segunda pasada | La línea de `sabotajes-conocidos.txt` deja afuera del selector al guion entero por un solo sabotaje, y su campo de salida dice «reescribirlo» | baja | no la toqué: tu regla dice que la línea queda hasta D199. Lo anoté en D199 |
| `/code-review high`, segunda pasada | El sabotaje nuevo del origen repite casos esperados y saca más que la medida | baja | supuesto 3 |

Propuestas para la cola de limpieza (la escribís vos), las dos de la primera
pasada de `/code-review`:

- El ancla del sabotaje de la transacción copia la lista entera de tablas.
- Tres pares ancla/reemplazo están repetidos entre la mitad de SQLite y la
  de Postgres.

`/security-review`: no corrido. Ninguna de las dos partes toca producto.

## Qué no corrí y riesgos

- La suite entera: no. Es arnés, producto +0/−0.
- El guion commiteado de `catalogo_largo2`, entero y sin el salto: no.
- D219: la mutación sólo contra 8 archivos de prueba.
- D220: medido en las funciones, no por la pantalla ni por un pedido.
- Riesgo: mientras D199 esté abierta, el selector no elige
  `catalogo_largo2.sh`.
- Riesgo: `caso`, en `sabotaje_maria3.sh`, no comprueba que el rojo venga
  sólo de la causa esperada.

Archivos de producto tocados: ninguno. Arnés:
`scripts/testing/sabotaje_maria3.sh`,
`scripts/testing/sabotajes/catalogo_largo2.sh`,
`scripts/testing/catalogo_largo2_postgres.py` y
`docs/pm/herramientas/sabotajes-conocidos.txt` (el texto de una línea).

No hay pieza marcada «apenas entregues»: sigo con `sabotaje_valor1.sh`, como
dice tu canal, salvo que llegue una devolución o la tarea de comparación.

/compact conservar: Dev 2 (MARIA), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (rama claude/practical-shannon-szpwkn, cabeza 8f79bcc, ya integrada en 829f2d1), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. Entregado en 204c638 (informe en el commit siguiente), esperando veredicto, dos cosas: la vuelta de D216 (b) y D217 (a) en sabotaje_maria3.sh (32 de 32 en rojo, sale 0) y el re-anclaje de sabotajes/catalogo_largo2.sh (todos en rojo menos «la clave junta ﬁ con fi», salteado sólo en una copia local: fallas 0, sale 0). Producto +0/−0. Abiertas, las decide la PM: D199 (retirar ese sabotaje; su línea queda en herramientas/sabotajes-conocidos.txt hasta entonces), D218 (operation_items sin sabotaje en el arranque), D219 (id de proveedor largo sin prueba), D220 (fuera de la clave, _normalize borra «ﬁ»). Sigue, una pieza por guion: valor1 (la que arranco ahora), maria8, maria1d, maria5, valor1b, doc1.py, maria7, guardar2; puerta de cada una: guion entero todo ROJO y sale 0, sin filas en anclas_perdidas.py, y sale su línea de sabotajes-conocidos.txt. Rango de D: D216 a D225; próxima libre D221. Una devolución de la PM o la tarea de comparación van primero. Los detalles están en PARA-PM-2.md: el resumen los cita, no los copia. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; las Devs no usan el consejero.
