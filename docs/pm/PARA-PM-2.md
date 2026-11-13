# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## PAIS-NL: entregada en `a2c6dc6`. «NL» y «NLD» dan 423 (PAISES BAJOS) en el TXT, el catálogo y la pantalla; la tabla no repite claves; ninguna otra forma de escribir un país cambia de código. Dos decisiones: D239 y D240

| qué | SHA |
|---|---|
| base (informe de SUFIJO-BORRADOR) | `6fbfefd` |
| producto: una sola «NL» en `PAISES_INDEC`, en 423; «NL» y «NLD» en 423 en la pantalla (+ `CHANGELOG.md`) | `7908921` |
| pruebas | `fc26da0`, `5b4a238`, `a2c6dc6` |
| `CHANGELOG.md`: lo que cambia en los lectores y al agrupar | `f779bd1` |
| integración de tu rama (`431b2ec`) | `54eff7a` |
| integración de tu rama (`6887343`), después de las puertas: sólo `docs/pm/` | `a1000dd` |
| **Lo que se entrega** | `a2c6dc6` |
| informe | el commit siguiente |

`producto +2/−2` (más 6 líneas de `CHANGELOG.md`).

**Lo que tenés que saber antes de publicar** (medido, sin migración, detalle
abajo):

1. Lo guardado como «NL» o «NLD» pasa de 434 a 423 solo, al generar.
2. Lo que alguien **escribió** «NL» en el campo de origen de la pantalla antes
   de este cambio quedó guardado como «434» (la pantalla guarda el código, no
   la sigla) y sigue en 434. No se distingue de un «434 · HOLANDA» elegido a
   propósito. En una misma operación pueden quedar los dos: un producto que
   llegó como «NL» (ahora 423) y otro tipeado «NL» a mano (guardado «434»).
3. Un «NL» guardado pudo venir de una factura que decía «Holanda»: el lector
   de facturas convertía «Holanda» y «434» a «NL». Esos también pasan a 423.
4. El lector de facturas y el de despachos cambian qué guardan, porque arman
   su mapa código→sigla desde la misma tabla: ahora «NL» es la sigla de 423 y
   434 queda sin sigla. Tabla abajo. El único caso que pierde algo es el
   despacho que trae «434» solo, sin nombre: antes daba «NL», ahora queda sin
   origen con el aviso «No reconocí el origen» (D239).
5. En un grupo, «NL» ya no va junto con «Holanda», «434» ni «434 · HOLANDA»:
   da «Grupo …: todos los ítems deben tener el mismo origen» (antes generaba
   434). **Un grupo ya guardado así deja de generar** hasta que alguien
   corrija el origen. Al revés, «NL» con «Países Bajos» o «423» en un grupo
   antes daba ese error y ahora genera 423. Tabla abajo.
6. Una pestaña abierta desde antes de publicar sigue con la tabla vieja hasta
   que se recarga: «NL» tipeado ahí se sigue guardando «434». No lo medí; es
   lo que hace un navegador con un script ya cargado.

## Decisiones

**D239. El lector de despachos no guarda un código de la tabla escrito solo
cuando ese país no tiene sigla de dos letras, y la pantalla no deja
escribirlo.** `origen_iso2` (`despacho_lector.py:246`) con «434» da `None`: el
renglón queda sin origen y con el aviso «No reconocí el origen «434»». Les
pasa a 115 de los 309 códigos de la tabla, antes y ahora: con este cambio 434
entra a ese grupo (antes «434» daba «NL») y 423 sale (antes «423» solo no se
reconocía). Con el nombre al lado («434 HOLANDA», que es el formato de las
fixtures: «310 CHINA») se reconoce. Dos cosas más del mismo lector:
- El campo de origen de la pantalla de importar despachos acepta dos letras
  (`clientes.js:1692`, `maxlength="2"`): con «434» solo, ahí no se puede
  escribir ni «434» ni «HOLANDA». En la edición del catálogo el campo acepta
  tres (`clientes.js:1427`). Leído en el código, no corrido en el navegador.
- «434 NL» y «434 PAISES BAJOS» dan «NL» (423) aunque el documento imprime
  434: el control de contradicción entre código y nombre sólo actúa cuando el
  código tiene sigla. El agujero ya estaba («423 NL» daba «NL», que era 434);
  se mudó de 423 a 434.

No sé qué tan seguido un despacho real trae el código solo: los reales los
tenés vos.
- (a) pieza aparte, chica: con un código de la tabla sin sigla, el lector
  guarda el código, y con código y nombre de países distintos no elige el
  nombre. Pocas líneas de producto y su caso; la pantalla de importar tiene
  que poder mostrar y guardar tres cifras.
- (b) queda así: es visible (aviso y origen vacío), salvo «434 NL», que
  guarda 423 sin avisar.
- **Recomiendo (a)**, sin apuro, detrás de lo que ya está en fila: el lector
  existe para no volver a tipear, y 115 códigos de 309 caen ahí.
  (`docs/archive/` y los despachos reales no los miré para esto.)

**D240. Los nombres de país en inglés se reconocen a medias.** Medido en
`codigo_de_pais`: dan `None` «Netherlands», «The Netherlands», «Nederland»,
«Holland», «Belgium», «United States», «Switzerland», «Sweden», «Turkey»,
«Denmark», «Poland» e «Ireland»; se reconocen Germany, Italy, Spain, France,
Japan, Brazil, Austria, United Kingdom, South Korea, India, Mexico, Vietnam,
Thailand, Taiwan, Hong Kong y Canada. A la factura leída con IA se le pide la
sigla («Código ISO2 del país», `pdf_extractor.py:432`), así que ahí el nombre
en inglés casi no llega; donde sí llega es en una celda de Excel
(`main.py:5898`): «Netherlands» termina en «XX». No es un dato mal: frena
antes de generar. El mensaje de `fc26da0` dice «toda forma de escribir»: el
caso cubre las ocho formas que lista, no éstas.
- (a) pieza aparte: sumar los nombres en inglés de los países que faltan. Si
  va, Emi tiene que decir si «Holland» es 423 o 434.
- (b) queda así.
- **Recomiendo (b)** hasta que un despachante lo pida: no hay dato mal y la
  lista se abre sin fin.

## Resultado

**Rojo antes del arreglo, con cada mitad revertida y con dos sabotajes**
(`tests/test_catalogo3.py` de `5b4a238` en un worktree descartable; `a2c6dc6`
le cambia sólo un comentario; textos copiados de la salida):

| producto | resultado | lo que dice |
|---|---|---|
| todo el arreglo revertido (el de `6fbfefd`) | `2 failed, 106 passed` | `test_la_tabla_de_paises_no_tiene_claves_repetidas`: `AssertionError: assert {'NL'} == set()` · `test_paises_bajos_es_423_y_holanda_434`: `At index 0 diff: 434 != 423` |
| sin sacar la «NL» repetida de `PAISES_INDEC` | `3 failed, 105 passed` | los dos de arriba y `test_la_pantalla_y_el_servidor_reconocen_los_mismos_paises`: `Left contains 3 more items, first extra item: ('NL', '423', '434')` |
| sin «NL» en 423 en la pantalla | `1 failed, 107 passed` | `test_la_pantalla_y_el_servidor_reconocen_los_mismos_paises`: `first extra item: ('NL', '434', '423')` |
| sin «NLD» en 423 en la pantalla | `1 failed, 107 passed` | `test_paises_bajos_es_423_y_holanda_434`: `At index 2 diff: 434 != 423` |
| sabotaje: el mapa de los lectores vuelve a dar «NL» para 434 (`por_codigo[434] = 'NL'` en `_iso2_por_codigo_maria`) | `1 failed, 107 passed` | `test_paises_bajos_es_423_y_holanda_434`: `AssertionError: _origen_desde_factura` · `At index 8 diff: 423 != 434` |
| sabotaje: al exportar, «NL» y «NLD» dan 434 (`maria_generator_export.get_pais_codigo`) | `1 failed, 107 passed` | `test_paises_bajos_es_423_y_holanda_434`: `At index 0 diff: 434 != 423` |
| entero | `108 passed` | |

Con el arreglo entero revertido el caso de paridad queda verde: la pantalla y
el servidor coincidían, los dos en 434. «NLD» sale sólo de la tabla de la
pantalla (el servidor la lee de ahí), por eso sin esa mitad cae el caso del
servidor y no el de paridad. La primera fila la repetí con
el caso de `a2c6dc6` (comando abajo): los mismos dos rojos.

**«Ninguna otra entrada cambia de valor».** Volqué, antes y después, lo que
resuelven el servidor (`codigo_de_pais`, `get_pais_codigo`) y la pantalla de
verdad (`resolve`, `label`, con node) para 2.515 formas: todas las claves de
`PAISES_INDEC`, de `ALIASES`, las ISO3, los nombres, códigos y etiquetas de la
tabla, y sus minúsculas. Cambian cuatro: «NL», «NLD», «nl» y «nld», de
`434 · HOLANDA` a `423 · PAISES BAJOS`, igual en los cuatro valores.

**Lo que el caso no fija** (medido una vez, sin caso): «434» solo en el lector
de despachos queda sin origen (si va D239 (a), eso cambia: no lo quise clavar),
y el rechazo del grupo «NL» + «Holanda» (es el control de grupos de siempre
sobre dos códigos que el caso ya fija como distintos). El caso de claves
repetidas mira el literal de `PAISES_INDEC`; una clave repetida dentro de
`ALIASES` de `paises_maria.js` no la vería (hoy no hay: 728 claves, ninguna repetida, contadas del texto).

## Medido y no arreglado

### Qué queda guardado cuando se carga «NL»

Por la API, en la base y con el arreglo. El servidor guarda el texto como
llega; el código se resuelve al generar.

| se carga | `operation_items.origen` | memoria (`client_product_history.origen_frecuente`) | catálogo (`vendor_catalog_products.origen`, al confirmar el NCM) | TXT antes | TXT ahora |
|---|---|---|---|---|---|
| «NL» | «NL» | «NL» | «NL» | 434 | **423** |
| «nl» | «nl» | (no medido: mi dato chocaba con el de «NL») | «NL» | 434 | **423** |
| «NLD» | «NLD» | «NLD» | «NLD» | 434 | **423** |
| «434» | «434» | «434» | «434» | 434 | 434 |
| «HOLANDA» | «HOLANDA» | «HOLANDA» | «HOLANDA» | 434 | 434 |
| «434 · HOLANDA» | igual | igual | igual | 434 | 434 |
| «423», «PAISES BAJOS», «423 · PAISES BAJOS» | igual | igual | igual | 423 | 423 |

Guardar la operación no escribe el catálogo; lo escribe confirmar el NCM.

### Qué guarda la pantalla (navegador real)

| | llega guardado: lo que muestra el campo | escrito a mano en el campo de origen: lo que queda en el estado |
|---|---|---|
| «NL», «nl», «NLD», antes | «434 · HOLANDA» (el estado conserva la sigla) | **«434»** |
| «NL», «nl», «NLD», ahora | «423 · PAISES BAJOS» (el estado conserva la sigla) | «423» |
| «Holanda», antes y ahora | «434 · HOLANDA» | «434» |
| «Países Bajos», antes y ahora | «423 · PAISES BAJOS» | «423» |

De ahí sale el punto 2 de arriba: lo escrito a mano como «NL» antes del cambio
ya es un «434» en la base.

### Qué cambia en los lectores (por el mapa código→sigla)

`_iso2_por_codigo_maria` (`pdf_extractor.py:2057`) se arma con las claves de
dos letras de `PAISES_INDEC`: antes 434→«NL»; ahora 423→«NL» y 434 sin sigla.

| leído | lector de facturas, antes → ahora | lector de despachos, antes → ahora |
|---|---|---|
| «NL», «nl», «NLD» | «NL» (434) → «NL» (**423**) | «NL» (434) → «NL» (**423**) |
| «Holanda», «HOLANDA» | «NL» (434) → como está escrito (434) | «NL» (434) → como está escrito (434) |
| «Países Bajos», «PAISES BAJOS» | como está escrito (423) → «NL» (423) | como está escrito (423) → «NL» (423) |
| «434» | «NL» (434) → «434» (434) | «NL» (434) → **sin origen, con aviso** |
| «423» | «423» (423) → «NL» (423) | sin origen → «NL» (423) |
| «434 HOLANDA» | | «NL» (434) → «HOLANDA» (434) |
| «423 PAISES BAJOS» | | «PAISES BAJOS» (423) → «NL» (423) |
| «423 NL», «434 NL» | | «NL» (434) → «NL» (**423**) |
| «423 HOLANDA» | | «NL» (434) → sin origen (el código y el nombre dicen países distintos) |
| «434 PAISES BAJOS» | | sin origen → «NL» (423): la contradicción ya no se ve, porque 434 no tiene sigla |
| «434 · HOLANDA» | «NL» (434) → como está escrito (434) | «NL» (434) → sin origen |
| «423 · PAISES BAJOS» | como está escrito (423) → «NL» (423) | sin origen → «NL» (423) |

Entre paréntesis, el código que da en el TXT. Nada de esto lo toqué: sale de
sacar la clave repetida, que es lo pedido.

### Qué pasa al generar con dos productos (por el control de grupos)

Generador llamado directo, dos productos, el primero con origen «NL».

| el segundo | mismo grupo, antes → ahora | sin grupo, antes → ahora |
|---|---|---|
| «Holanda», «434», «434 · HOLANDA» | genera 434 → **error** «Grupo g: todos los ítems deben tener el mismo origen» | un origen (434) → dos (423 y 434) |
| «Países Bajos», «423» | **error** (el mismo) → genera 423 | dos (434 y 423) → uno (423) |
| «nld» | genera 434 → genera 423 | 434 → 423 |

«434» con «Holanda», sin «NL»: genera 434 antes y ahora.

## Revisión adversarial

| quién | sobre | hallazgo | qué hice |
|---|---|---|---|
| `adversario-sonnet-alto` (Sonnet, alto) | `6fbfefd..fc26da0` | media, del caso: con el mapa de los lectores dando otra vez «NL» para 434, todo seguía verde | el caso mira los dos lectores (`5b4a238`); rojo arriba |
| | | media, del caso: al exportar, «NL» no tenía prueba | el caso mira `maria_generator_export.get_pais_codigo` (`5b4a238`); rojo arriba |
| | | media: en un grupo, «NL» con «Holanda», «434» o «434 · HOLANDA» ahora da error | reproducido (tabla de arriba); `CHANGELOG.md` (`f779bd1`) y punto 5 |
| | | baja-media: el campo de origen de la pantalla de importar despachos acepta dos letras; con «434» solo no hay cómo corregirlo ahí (leído, no corrido) | D239 |
| | | baja: el `CHANGELOG.md` decía menos de lo que cambia | tercera viñeta (`f779bd1`) |

No encontró otra copia de la tabla, otra entrada que cambie de valor, ni un
desfase entre servidor y pantalla al cargar la página. Midió además las formas
en inglés que no se reconocen (D240).

## `/code-review high` sobre `6fbfefd..54eff7a`

Los revisores heredan Fable. Nueve hallazgos; ninguno pide tocar el producto
de la pieza:

| # | hallazgo | qué hice |
|---|---|---|
| 1 | un «NL» guardado genera 423 y un «434» que salió del mismo «NL» tipeado sigue en 434: una operación puede llevar los dos, y nada marca cuáles | punto 2 y riesgos; sin migración, como pediste |
| 2 | un grupo guardado con «NL» y «434» u «Holanda» deja de generar | punto 5 y riesgos |
| 3 | `origen_iso2('434 NL')` y `('434 PAISES BAJOS')` dan «NL» (423) aunque el documento imprime 434 | de antes, mudado de código: D239 |
| 4 | `origen_iso2('434')` y `('434 · HOLANDA')` dan `None` | D239 |
| 5 | el comentario del caso prometía más de lo que mira (con «434» el lector de despachos da `None`); dos frases del `CHANGELOG.md` no tienen caso | comentario corregido (`a2c6dc6`); lo que no fijo y por qué, arriba |
| 6 | el caso de claves repetidas sólo mira el literal de Python | hueco anotado arriba; hoy no hay repetidas en `ALIASES` |
| 7 | «NL» se mantiene a mano en más de un lugar (`PAISES_INDEC` y `ALIASES` de la pantalla) | línea para la cola, abajo |
| 8 | las formas en inglés no se reconocen | D240 |
| 9 | una pestaña abierta durante la publicación sigue guardando «434» para «NL» tipeado | punto 6 y riesgos |

Después de `/code-review` sólo cambió un comentario de la prueba (`a2c6dc6`):
no lo volví a correr.

## Comandos

```bash
S=<carpeta descartable>; PY=<python del entorno virtual>
export GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
# verde
env -u DATABASE_URL -u ENVIRONMENT $PY -m pytest -q --no-cov -p no:cacheprovider tests/test_catalogo3.py   # 108 passed
# rojo: los casos de hoy con el producto de la base
git worktree add -q --detach $S/wt a2c6dc6
(cd $S/wt && git checkout -q 6fbfefd -- proyecto_maria/core/maria_generator.py proyecto_maria/static/v2/paises_maria.js \
  && env -u DATABASE_URL -u ENVIRONMENT $PY -m pytest -q --no-cov -p no:cacheprovider tests/test_catalogo3.py)
#   2 failed, 106 passed:
#   test_la_tabla_de_paises_no_tiene_claves_repetidas   AssertionError: assert {'NL'} == set()
#   test_paises_bajos_es_423_y_holanda_434              At index 0 diff: 434 != 423
git worktree remove --force $S/wt
```

## Puertas

Todas sobre `a2c6dc6`, una por vez.

| puerta | salida |
|---|---|
| `pytest -q --no-cov --timeout=120` (entera) | `6131 passed, 110 skipped, 3 xfailed, 104 warnings in 1372.01s (0:22:52)` (antes, sobre `52f13ca`: `6130 passed, 110 skipped, 3 xfailed`; el que suma es `test_la_tabla_de_paises_no_tiene_claves_repetidas`) |
| `python -m compileall -q proyecto_maria` | sin salida, sale 0 |
| `correr_pantallas.sh a2c6dc6` (las 34) | `resumen: 34 verdes, 0 rojas` (z22 de `orden1` esta vez no dio la carrera de D237) |
| `e2e_maria.sh` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |
| `smoke_friccion.sh` (API local con base descartable) | `==> OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido`, sale 0 |
| `anclas_perdidas.py a2c6dc6` | `revisión a2c6dc6: 102 guiones, 2466 anclas medidas y 11 llamadas sin medir` (igual que la base `6fbfefd`, fila por fila) |
| grep de historia de §6 sobre `proyecto_maria/` | vacío |

No corrí: `ataque_aislamiento.sh` ni `/security-review` (la pieza cambia qué
código da una sigla: no toca qué se guarda, sesión, permisos ni una entrada
nueva de usuario; si la contás como pieza de datos de §3, falta eso y lo
corro), Postgres, Firefox ni WebKit, ni la pantalla de importar despachos en
el navegador (lo de `maxlength` de D239 está leído). Sin guion de sabotaje
propio: los rojos van arriba, una vez cada uno.

## `chequeo-6`

```
chequeo-6 6fbfefd..a2c6dc6: avisos para mirar, no un veredicto
producto +2/−2
arnés +25/−4
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/maria_generator.py: 2391 → 2391
  proyecto_maria/static/v2/paises_maria.js: 47 → 47
avisos: 0
```

## Riesgos

- **Sin migración.** Los puntos 1 a 3 de arriba. Para saber cuánto hay antes
  de publicar alcanza con contar, en producción y sin cambiar nada, los
  `origen` «NL», «NLD» y «434» de `operation_items`,
  `client_product_history.origen_frecuente` y `vendor_catalog_products`. Los
  «434» no dicen si fueron «NL» escrito a mano o «HOLANDA» elegido: eso sólo
  lo sabe quien lo cargó.
- **Grupos guardados** con «NL» junto a «Holanda» o «434» (punto 5): dejan de
  generar con un error que dice el grupo, no cuál producto ni qué país. No
  medí cuántos hay: se cuenta igual que arriba, mirando `grupo_id`.
- **Pestañas abiertas** al publicar (punto 6): hasta recargar siguen
  guardando «434» para «NL» tipeado.
- **«HOLANDA» sigue en 434**, como decidiste. Lo que eso da hoy: una factura
  o una celda que dice «Holanda» genera 434 y la pantalla muestra
  «434 · HOLANDA»; una que dice «NL» o «Países Bajos», 423.
- Un TXT ya generado con «NL» salió con 434: no se regenera solo.

Línea que propongo para `COLA-LIMPIEZA.md`: «`paises_maria.js` repite a mano
alias que el servidor tiene en `PAISES_INDEC` («NL» está en los dos; «NLD»
sólo en la pantalla): una sola fuente para las siglas.»

## Archivos de producto que toqué

`proyecto_maria/core/maria_generator.py` (una línea de `PAISES_INDEC`),
`proyecto_maria/static/v2/paises_maria.js` (dos alias), `CHANGELOG.md`.

## Sigo con

D237 (a): z22 de `scripts/testing/pantalla_orden1.js` espera los pedidos de
avisos antes de cerrar la sesión.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama `claude/dev-maria`, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `6887343`). PAIS-NL entregada sobre `a2c6dc6` (base `6fbfefd`), con D239 (el lector de despachos no guarda un código de la tabla sin sigla escrito solo, el campo de origen de esa pantalla acepta dos letras y «434 NL» guarda 423; recomiendo (a), pieza chica aparte) y D240 (nombres de país en inglés reconocidos a medias; recomiendo (b), queda así) sin contestar. Pieza activa: D237 (a) (z22 de `scripts/testing/pantalla_orden1.js` espera los pedidos de avisos antes de cerrar la sesión, sin espera fija). Después: D238 (a) (el aviso «Es obligatorio» del sufijo no queda a la vista de una operación a la otra; pieza chica aparte), CUIT-GENERAR (D235 a; apartada con las reversiones `3a6f656` y `2f04637`, se recupera revirtiéndolas; hallazgos del adversario en el scratch `cg_adversario.md`; revisión fuerte §3 con `/security-review`; sus D toman número nuevo), y los vencidos de `sabotajes-conocidos.txt`, uno por pieza. Próxima D: D241. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, sin secretos ni datos reales, VUCE y Gemini simulados, una corrida por vez, un rojo se diagnostica y no se repite hasta verde, las Devs no usan el consejero ni subagentes de esfuerzo muy alto.
