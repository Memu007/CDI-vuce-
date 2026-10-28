# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## DESPACHO-1b: hecha, **sin entregar** (2026-10-28)

Commits encima de SEGURO-1 (`371cde2`), de mi informe (`de9cb24`) y del
merge de tu rama (`49f8e29`): producto y `CHANGELOG.md` `0591722`; casos,
pantalla y sabotajes `e59e1a8`. **SHA probado: `e59e1a8`.** Para ver sólo
esta pieza: `git diff 49f8e29..e59e1a8`. Va en su propio `/entregar`,
después del de SEGURO-1, con subagentes y `/code-review` cuando vuelva el
cupo. **No hace falta que la revises todavía.** Tiene una decisión: D31,
arriba en «Decisiones».

**La premisa: confirmada, sin Gemini y sin librería nueva.** El repo ya saca
texto de PDF con `pypdf` (el lector de facturas, `pdf_extractor.py`) y lo
corre aparte con su tope de tiempo (`_leer_pdf_aparte`). Uso lo mismo, con
los mismos topes de página.

- **Qué lee** (`proyecto_maria/core/despacho_lector.py`, nuevo): por
  renglón, posición SIM, descripción, sufijos, origen, unidad, cantidad,
  valor unitario y kilo neto. **Por rótulo:** busca la línea del rótulo y
  toma el valor de abajo en la misma columna. Hay una prueba con los
  rótulos en otro orden y otra con un valor vacío en el medio: sin kilo, el
  origen sigue siendo el origen (leyendo por posición, caería en el kilo).
- **Números** `1.234,56`. Otra forma (`12.5`, `1,234.56`) no se adivina:
  queda faltante, con un aviso.
- **Subítems:** con unidad `SUBITEM`, un renglón por subítem con su valor,
  descripción y sufijos. La posición y el origen se toman del ítem, y el
  aviso lo dice. Lo que al subítem le falta no se toma del ítem.
- **Lo que falta** queda en `faltantes`, vacío y marcado en pantalla. Nada
  se rellena: sin kilo, el peso queda vacío, no cero ni una cuenta.
- **Escaneado:** sin texto, avisa «El PDF no tiene texto que se pueda leer:
  parece escaneado…» y no devuelve renglones. Un PDF que no es despacho o
  está roto, también avisa.
- **Tilde rota** («Las dem?s»): la descripción queda como vino, con un
  aviso para que la corrijan en la revisión.
- **Divisa:** la del FOB, no la del flete (hay prueba con las dos
  distintas).
- **Pantalla** (Catálogo del cliente, `clientes.js`): «Cargar desde
  despacho» abre el selector, muestra los renglones editables con lo
  faltante marcado y guarda sólo al tocar «Guardar en el catálogo». La
  prueba de pantalla falla si se pide guardar antes del clic. Probada en
  1280 y 390 px.
- **Guardar** es todo o nada: si un renglón no sirve, 422 con qué le falta
  a cada uno y no se guarda ninguno. Pide posición con sus 8 dígitos y
  descripción; el origen, si viene, tiene que ser un país de la tabla. Tope
  de renglones (400 si se pasa). Lista vacía, 400.
- **De quién:** leer y guardar usan `_get_owned_client`: un cliente ajeno o
  de otro dueño da 404 y no se toca nada.
- **Nunca** arma un TXT ni una operación: hay pruebas que cuentan las
  operaciones antes y después y que fallan si se llama al generador. El
  lector de facturas sigue rechazando un despacho (prueba con el sintético).
- **Datos:** el sintético lo arma la prueba con la forma de
  `DESPACHOS-FORMA.md` y valores inventados: dos ítems, uno con subítems,
  un `AI` con espacios, «Las dem?s», FOB y flete en divisas distintas y un
  renglón sin kilo neto. Ningún despacho real.
- **Archivos de producto:** `proyecto_maria/core/despacho_lector.py`
  (nuevo), `proyecto_maria/main.py`, `proyecto_maria/static/v2/screens/clientes.js`,
  `proyecto_maria/static/v2/app_v2.css`,
  `proyecto_maria/templates/dashboard_v2.html` y `CHANGELOG.md`.

**Supuestos reversibles:**
- Los rótulos del subítem («Nº Subitem» y sus valores) son supuestos: los
  despachos de muestra no los traían con su rótulo. Están escritos en la
  cabecera de `despacho_lector.py`.
- La unidad, la cantidad y el valor unitario salen de «VALOR MERCADERIA».
- El peso que guarda el catálogo es por unidad: kilo neto dividido
  cantidad, si están los dos.

**Puertas sobre `e59e1a8`:**

| Puerta | Resultado |
|---|---|
| `tests/test_despacho1b.py` | 50 passed |
| Suite completa (`--timeout=120`) y `compileall` | 3827 passed, 336 skipped, 2 xfailed, 0 failed; `compileall` 0 |
| Sabotajes `scripts/testing/sabotajes/despacho1b.sh e59e1a8` | 24 líneas ROJO, «sabotajes sin rojo: 0», salida 0 |
| Pantalla `scripts/testing/pantalla_despacho1b.js` | OK en 1280 px (panel 644 px) y 390 px (panel 308 px) |
| `smoke_friccion.sh` (puerto 8855) | salida 0, «OK · telemetría + alias session/state + by-cuit protegido» |
| `ataque_aislamiento.sh` (puerto 8857) | salida 0, «PUERTA G3 PASADA. Ningún despachante ve datos de otro.» (cubre clientes y descargas; lo de esta pieza lo cubren sus pruebas de 404) |

La suite suma los 50 casos nuevos a los 3777 de SEGURO-1. Los 32 avisos
«Task was destroyed but it is pending!» de su salida ya estaban en las
suites de `4ca6829` y `a08de1f`: no son de esta pieza. Los sabotajes
corrieron también en `9dcd5cc` (mismo árbol que `e59e1a8`), con los mismos 24
rojos.

**Sabotajes (24, uno por regla), todos en rojo:** el subítem toma lo que le
falta del ítem; lo que falta no se marca; se lee por posición; se aceptan
números con otra forma; un número que no se entiende se lee igual; los
subítems no se separan; la posición heredada no se avisa; la divisa es la
del flete; un sufijo con espacios no se lee; un escaneado no avisa; sin
kilo se inventa el peso; leer no mira el dueño; guardar no mira el dueño;
se guarda lo bueno y se descarta el resto; guardar acepta una lista vacía;
guardar no tiene tope; leer acepta lo que no es PDF; guardar arma un TXT;
guardar crea una operación; el lector de facturas acepta despachos; el
botón no está conectado; el faltante no se marca en pantalla; se guarda al
leer, sin revisar; el panel es más ancho que la pantalla.

**Comandos:**

```bash
git diff 49f8e29..e59e1a8 --stat        # 9 archivos, ninguno en tests/fixtures
python -m pytest -q --no-cov tests/test_despacho1b.py
#   50 passed
PY=<venv>/bin/python scripts/testing/sabotajes/despacho1b.sh e59e1a8
#   24 líneas ROJO y al final «sabotajes sin rojo: 0»
PY=<venv>/bin/python BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_despacho1b.js
#   OK en 1280 y 390
```

**Riesgos y lo que no hice:**
- **No se probó con un despacho real** (no entran). Si el sistema del
  despachante pega dos columnas con un solo espacio, el valor puede quedar
  faltante: falla hacia «falta», no hacia un dato cambiado.
- **D31:** hoy el catálogo guarda NCM de 8 dígitos, descripción, origen,
  valor unitario, cantidad y peso. Los sufijos, la unidad, la posición
  completa y la divisa se ven en la revisión pero no se guardan. El valor
  unitario queda sin divisa.
- Dos renglones con el mismo NCM y descripción parecida (Jaccard ≥ 0,80,
  la regla de siempre del catálogo) se funden en uno: `guardados` puede
  decir más de lo que aparece. Dos subítems que sólo difieren en el `AI`
  quedan en uno.
- Guardar en un producto que ya existe promedia sus valores, como el
  aprendizaje de hoy.
- `leer` tiene el límite de pedidos del resto; `guardar` no, igual que el
  aprendizaje de hoy.
- El rechazo del lector de facturas pasa por Gemini, simulado en la prueba.
- Previos, no de esta pieza: `--t-12` no está definido en el CSS; el
  tablero mide 523 px de ancho en 390.
- La pantalla muestra en notación exponencial un número absurdo
  (`1e21`); no cambia lo que se guarda.
- Sin correr todavía: subagentes, `/code-review` y `/security-review`.
  Vuelven a las 18:00 UTC.

## SEGURO-1: hecha, **sin entregar** (2026-10-28)

Commits encima de SUFIJOS-2 (`4ca6829`) y del merge de tu rama
(`1948207`): producto y `CHANGELOG.md` `4f75f3d`; casos y sabotajes
`a08de1f`; un sabotaje con su patrón arreglado `371cde2`. **SHA probado:
`371cde2`.** Sabotajes 10/10 en rojo en `371cde2`
(`scripts/testing/sabotajes/seguro1.sh`) y suite completa en `a08de1f`:
3777 passed, 336 skipped, 2 xfailed, 0 failed (`compileall` limpio). Entre `a08de1f` y `371cde2` sólo cambia el script de
sabotajes, que pytest no junta. Va en su propio `/entregar`, después del de SUFIJOS-2,
con `/security-review` porque es un campo de dinero. **No hace falta que la
revises todavía.** La D30 ya está contestada (a).

**La premisa: confirmada.** `cuentas_del_valor` no conocía el incoterm,
pero quien la llama (`_cuentas_del_valor` en `main.py`) tiene
`request.incoterm`. Se lo paso: la regla vive en el servidor sin salir del
alcance.

- **La regla, en el servidor:** `INCOTERMS_CON_SEGURO = ("CIF", "CIP",
  "DPU", "DAP", "DDP")` en `maria_generator.py`. Con esos, las cuentas
  traen `seguro_sugerido: None` y `seguro_en_el_precio: true`. Con los
  demás, el 1 % como antes. Mayúsculas, minúsculas y espacios dan lo mismo
  (`" cif "` es CIF); vacío o desconocido (`"XYZ"`, `"C I F"`), con 1 %.
- **La pantalla sigue al servidor**, no al incoterm de la operación: sin
  `seguro_en_el_precio` hay botón aunque la operación diga CIF (hay una
  prueba que lo fija). Con CIF no hay «Calcular seguro» ni «Dejar el
  seguro», y `calcularSeguro()` no pone nada. La nota dice «Con CIF el
  seguro ya está en el precio: el sistema no lo calcula.» y agrega que lo
  carguen en la revisión si no hay seguro.
- **El seguro se sigue declarando:** una operación CIF con seguro 14,88
  sale con `MDDTASS 14.88` y `CDDTINCOTE CIF`. Un seguro escrito de 93,13
  (el mismo número que daría el 1 %) con CIF también genera: es de la
  persona.
- **Cambio de incoterm con el seguro calculado:** cuando llegan las cuentas
  del pedido de ahora con `seguro_en_el_precio` y la operación tiene
  `seguro_calculado`, la pantalla borra el seguro, saca la marca, lo agrega
  a `campos_sin_leer` (el mismo mecanismo que un campo que el lector no
  leyó) y lo saca de `campos_completados`. El semáforo dice «No pudimos leer
  el seguro de la factura: completalo.». Con cuentas de otro pedido no
  borra nada. El leído o escrito no se toca. De CIF a CFR vuelve el botón y
  no pone nada solo.
- **El servidor también frena:** un pedido con `seguro_calculado` y uno de
  los cinco da 400 «Seguro: lo calculó el sistema, pero con CIF el seguro ya
  está en el precio y no se calcula. Cargá el de la factura en la
  revisión.», en `/generate_maria` y en los avisos, aunque las cuentas
  estén en error. Cubre una pestaña con el `finalize.js` viejo.
- **El golden no se tocó:** `git diff 1948207..a08de1f -- tests/fixtures`
  sale vacío.
- **Dos pruebas existentes cambiaron, sin cambiar lo que miden:** en
  `tests/test_valor1.py` la expectativa de las cuentas suma
  `"seguro_en_el_precio": False`, y la función nueva
  `borrarSeguroCalculado` se suma a las listas de los arneses de pantalla de
  `test_valor1.py` y `test_valor1c.py` (extraen funciones por nombre).
- **Archivos de producto:** `proyecto_maria/core/maria_generator.py`,
  `proyecto_maria/main.py`, `proyecto_maria/static/v2/screens/finalize.js` y
  `CHANGELOG.md`.

**Supuestos reversibles:**
- El borrado usa `campos_sin_leer`, que es la lista del lector. Por eso el
  semáforo dice «No pudimos leer el seguro de la factura», aunque lo que
  pasó es que el sistema lo borró. Si preferís otro texto, es un aviso
  propio en `semaforo.js`.
- La nota nombra el incoterm de la operación («Con CIF…»); si falta, dice
  «este incoterm».
- El 400 del servidor con un calculado y CIF no estaba pedido: es la regla
  «vive en el servidor» aplicada a `seguro_calculado`. Sin él, una pestaña
  vieja mandaría el 1 % con CIF.

**Sabotajes (uno por regla):** DPU fuera de la lista; el incoterm sin
normalizar; `main.py` no pasa el incoterm; la pantalla decide por
`op.incoterm`; el botón calcula con CIF; `pintarValor` no borra; el
servidor no frena el calculado con CIF; se borra también el escrito; se
borra sin mirar la firma del pedido; el borrado deja el seguro como
completado. En la primera corrida, el del incoterm en `main.py` no
encontraba su patrón (la línea aparece cuatro veces): lo arreglé en
`371cde2` con un patrón que aparece una sola vez.

**Comandos:**

```bash
git diff 1948207..371cde2 --stat                 # 8 archivos; tests/fixtures no aparece
git diff 1948207..371cde2 -- tests/fixtures | wc -l   # 0
PY=<venv>/bin/python scripts/testing/sabotajes/seguro1.sh 371cde2
#   10 líneas ROJO y al final «sabotajes sin rojo: 0»
python -m pytest -q --no-cov tests/test_seguro1.py tests/test_valor1.py tests/test_valor1c.py
#   151 passed
```

**Riesgos y lo que no hice:**
- **Seguro 0 en el TXT si nadie lo completa** (D30, contestada (a)): un seguro «para completar» avisa en pantalla y no frena el TXT. Frenarlo es SEGURO-2.
- `finalize.js` se carga con `?v={{ version }}`; una pestaña abierta antes
  del despliegue sigue con el JS viejo y muestra el botón con CIF. Si lo
  aprieta, el servidor da el 400 de arriba: no sale el 1 % en el TXT.
- Sin correr todavía: subagentes, `/code-review` y `/security-review`.
  Vuelven a las 18:00 UTC.

## SUFIJOS-2: hecha, **sin entregar** (2026-10-28)

Commits encima de `4905cd8`: casos en rojo `a12aae3`; producto y
`CHANGELOG.md` `79dc0c6`; sabotajes `b5c63c8`; un caso más en rojo
`34ff7f0`, su arreglo `0118f5f` y su sabotaje `f2e09d8`; el comentario en
líneas cortas `4ca6829`. **SHA probado: `4ca6829`.** Sabotajes 9/9 en rojo
(`scripts/testing/sabotajes/sufijos2.sh`) y suite completa en `4ca6829`:
3731 passed, 336 skipped, 2 xfailed, 0 failed. Va en su propio `/entregar`, después del de DESTINO-1, cuando
vuelva el cupo. **No hace falta que la revises todavía.** La D29 ya
está contestada (a).

- **Sufijo libre:** un número con decimales sale con coma. `AF(2.5)` sale
  `AF(2,5)`. Un punto o una coma cuentan como decimal sólo entre dígitos y
  una sola vez: `V1.2.3` sale `V1 2 3`, como antes, y `ROJO, AZUL` sale con
  espacio. Vale también para la propuesta que arma el arancel.
- **Sufijo que pide número** (los `Z`, D29 contestada (a)) con decimales: no se
  genera. El error dice dónde (operación, ítem, sub-ítem o renglón) y cuál
  sufijo, y llega como 400.
- **Ninguno vacío:** `AA()`, `AA(   )` o `AA(--)` (que queda vacío al
  limpiar) no se generan. Mismo tipo de error.
- **Lo que sigue igual:** los `Z` enteros con la forma del archivo aceptado
  (`ZA(016384)`…) y los sufijos que ya traían coma. El golden no cambió:
  `git diff 4905cd8..4ca6829 -- tests/fixtures` sale vacío.
- **Una prueba existente cambió:**
  `tests/test_sufijos1.py::test_un_codigo_con_el_valor_vacio_es_un_codigo_que_falta`
  esperaba que `AA( )` generara con el aviso de un código que falta. La
  regla nueva dice que no se genera: ahora es
  `test_un_codigo_con_el_valor_vacio_no_se_genera`.
- **Archivos de producto:** `proyecto_maria/core/maria_generator.py` y
  `proyecto_maria/core/sufijos_arca.py`.

**La premisa.** Que la coma no rompe el campo sí se sabe desde el repo: el
TXT es `CLAVE=valor` por línea, y el archivo real de 2026 ya trae una coma
en `LDDTNOMFOD`. El paréntesis se toma entero, en el generador y en
`despachante.js`, así que la coma de adentro no parte el sufijo. Cuáles
piden número **no** se sabe desde el repo: es la D29.

**Rojo encontrado en la autorrevisión.** `\d` en Python también toma
dígitos que no son ASCII. Con eso, `٣.٥` salía `٣,٥` en el TXT. Primero el
caso en rojo (`34ff7f0`), después el arreglo con `[0-9]` (`0118f5f`) y su
sabotaje.

**Riesgos y lo que no hice:**
- En un sufijo libre, `1.234` con punto de miles sale `1,234`, que se lee
  como 1 con decimales. No hay forma de distinguirlos.
- En un `Z`, `1.234` da error y no se lee como 1234. Es a propósito: no se
  adivina.
- Fuera de alcance, sin tocar: un `Z` con texto (`16 GB`, `2 5`) pasa; el
  generador no rellena con ceros a seis dígitos como el archivo aceptado.
  Si querés, lo propongo como pieza.
- Sin correr todavía: subagentes, `/code-review` y `/security-review`.
  Vuelven a las 18:00 UTC.

## DESTINO-1: hecha, **sin entregar** (2026-10-28)

Producto `7526be9`, pruebas y sabotajes hasta `f887b4a`, encima de
`4ce6d22`. Sabotajes 15/15 en rojo (`scripts/testing/sabotajes/destino1.sh`)
y suite completa en `f887b4a`: 3697 passed, 0 failed. Va en su propio
`/entregar`, después del de ORG-1, cuando vuelva el cupo. **No hace falta que
la revises todavía.** Ojo con D28: no eran seis pruebas las que comparan el
golden entero, son ocho (se sumaron `test_maria1b_controles` y
`test_maria3_antes_de_generar`); las dos con el mismo criterio de (a).

## ORG-1, ORG-1b y DESPACHO-1a: listas, **sin entregar** (2026-10-28)

**DESPACHO-1a está hecha** (producto `e438dad`, probado en `51890cd`), en
commits aparte sobre ORG-1b. Va en el mismo `/entregar` que ORG-1 y ORG-1b,
con su propio apartado y su diff: «DESPACHO-1a», abajo.

**ORG-1b (D27 b) está hecha**, en commits aparte, con su propio SHA de
producto (`f8616cf`). Va en el mismo `/entregar` que ORG-1. Detalle en
«ORG-1b», abajo.

**ORG-1. Estado:** los cinco puntos están hechos. Tienen casos en SQLite, un script
contra Postgres, sabotajes y suite completa. **No la entrego todavía.** Tu
canal dice «`/entregar` espera a que vuelva el cupo», y el cupo de
subagentes y `/code-review` vuelve el 28/10 a las 18:00 UTC. Ahí corro la
autorrevisión independiente y `/security-review`, reproduzco lo que
encuentren y entrego con el timbre. Subo ahora para que el trabajo no se
pierda si el contenedor muere. **No hace falta que la revises todavía.**

## Decisiones

**D31 — qué guarda el catálogo de lo que lee un despacho (DESPACHO-1b).**
La lectura saca posición SIM completa, descripción, sufijos, origen,
unidad, cantidad, valor unitario y kilo neto. El catálogo de hoy
(`client_product_history`, el de DESPACHO-1a) tiene lugar para NCM de 8
dígitos, descripción, origen, valor unitario, cantidad y peso por unidad.
Los sufijos, la unidad, la posición completa (con su letra) y la divisa no
tienen columna.

- **(a) Recomiendo esta, y es lo que hice.** Se guarda lo que entra hoy; lo
  demás se ve en la revisión y no se guarda. Sin migración y sin tocar el
  catálogo de DESPACHO-1a. El costo: el valor unitario queda sin divisa, y
  dos subítems que sólo difieren en los sufijos (el `AI`) se funden en un
  producto, porque el catálogo junta por NCM y descripción parecida.
- **(b)** Una tabla o columnas nuevas para sufijos, unidad, posición y
  divisa. Es una migración sobre datos de clientes: pieza aparte, con su
  revisión fuerte, y antes conviene saber para qué se van a usar esos datos
  (sugerir sufijos al armar una operación sería otra pieza).

**D30 — contestada (a) en `53e1e86`.** Un seguro «para completar» sigue siendo un aviso; SEGURO-2 no la empiezo hasta verla en tu canal.

**D29 — contestada (a) en `3d3ab47`.** `PIDE_NUMERO = ("Z",)` queda.

**D28 — contestada (a) en `be1cac2`.** DESTINO-1 rompe seis pruebas que
comparan el golden entero. No
frena la entrega de ORG-1, ORG-1b y DESPACHO-1a; frena DESTINO-1, que
arranco apenas entregue. Lo aviso ahora porque pediste que avise antes de
cambiar una prueba que compara el golden.

Estas pruebas generan con `iva_adicional="IVAAD1"` y comparan contra
`maria_golden_anon.TXT` todo el archivo, byte a byte. El golden trae
`COMERC` + `IVAAD1`:

- `tests/test_generar_maria_txt.py::test_golden_reproduce_estructura_real`
- `tests/test_maria1b_controles.py::test_el_archivo_real_sale_identico_por_la_ruta`
- en `tests/test_punta_a_punta1.py`, las cuatro que comparan con
  `_GOLDEN_PATH`: líneas 433, 438, 445 y 478.

Con DESTINO-1, `IVAAD1` se lee como bien de uso de una persona. Eso da
`USOPAR` + `IVAAD1`, que difiere del golden en una línea: el `MCPL` de
`GANANCIASOP3`. Ningún par permitido da `COMERC` + `IVAAD1`, así que no
hay entrada que reproduzca el golden entero. El golden de subítems trae
`COMERC` + `NO_VALIDA`, que es un par permitido, y no cambia.

- **(a) Recomiendo esta.** El golden no se toca. Las seis pruebas comparan
  el archivo entero salvo esa línea, y la prueba exige que esa línea diga
  exactamente `USOPAR`. Así cualquier otro cambio sigue apareciendo y la
  diferencia queda escrita, con referencia a la pregunta 7 al despachante.
- **(b)** Las pruebas siguen generando con comercialización. Ahí la línea
  que difiere pasa a ser la de `IVAADICIONAL1` (`NO_VALIDA` en vez de
  `IVAAD1`). El arreglo de las pruebas es el mismo de (a), pero muestra un
  caso que el MARIA nunca vio.
- **(c)** DESTINO-1 espera la respuesta a la pregunta 7.

D26 y D27 ya están contestadas: D26 (a) por ahora, D27 (b) como ORG-1b.

| Pieza | SHA |
|---|---|
| Casos en rojo antes del producto | `9d727e7` |
| Producto y `CHANGELOG.md` | `e43810b` |
| Sabotajes (9, uno por motivo) | `18f7f25` |
| Carrera de dos invitaciones a la vez, en Postgres | `ddfc798` |
| **SHA probado:** suite, compileall, smoke, aislamiento | **`18f7f25`** |
| ORG-1b: la prueba de pantalla, en rojo antes del producto | `9ad42e4` |
| **ORG-1b: producto y `CHANGELOG.md`** | **`f8616cf`** |
| ORG-1b: sabotajes (7, uno por motivo) | `b7a7927` |
| ORG-1b: arreglo de la prueba (dos sabotajes no daban su rojo) | `5d42909` |
| **ORG-1b, SHA probado:** pantalla y sabotajes | **`5d42909`** |

Entre `18f7f25` y `ddfc798` sólo cambia `scripts/testing/org1_postgres.py`,
que pytest no junta. Tu diff de revisión de ORG-1 parte de `ea64a9c`, la
punta de tu rama.

ORG-1b está encima de `ddfc798`, pero no pegada a él. En el medio quedan mi
informe (`de8d175`) y el merge de tu rama (`373ef55`). Ninguno de los dos
toca producto. Para ver sólo ORG-1b: `git diff 373ef55..5d42909`.

Toqué estos archivos de producto:
- `proyecto_maria/main.py` (ORG-1)
- `proyecto_maria/templates/landing.html` (ORG-1b)
- `CHANGELOG.md` (las tres)
- `proyecto_maria/main.py`, `proyecto_maria/templates/dashboard_v2.html` y
  `proyecto_maria/static/v2/screens/clientes.js` (DESPACHO-1a)

## 1. La premisa: confirmada

Corrí `org1_postgres.py` contra un Postgres 16 local con el código de
`ea64a9c`. El resultado fue `fallas: 15`. Cada 500 trae en el log
`TypeError: can't compare offset-naive and offset-aware datetimes` (15
veces). Es tu sospecha: asyncpg devuelve `expires_at` con zona, y se compara
con `datetime.utcnow()`, que no tiene zona. Validar, registrarse, una
vencida y una usada daban 500 en Postgres. Invitar no daba 500, porque no
compara fechas.

## 2. Qué cambió, por punto

Todo está en `proyecto_maria/main.py`.

1. **Sin 500 en las dos bases.** El registro y `validate_invitation`
   comparan `_utc(expires_at) < datetime.now(timezone.utc)`. `_utc` ya
   existía y toma una fecha sin zona como UTC. Así entran los registros
   viejos de SQLite y los de Postgres, que vienen con zona.
2. **Atada al email.** Al registrarse con `invite_token`, el email del
   registro, ya con `strip().lower()`, tiene que ser el de la invitación. Si
   no, responde 400 «Esta invitación es para otro email. Registrate con el
   email al que te invitaron.». La invitación sigue pendiente y no se crea el
   usuario. Una invitación sin email no deja entrar a nadie. El otro camino
   que pone `organization_id` es `/api/organizations/create`, que es el
   dueño creando su estudio. Sacar un miembro lo vuelve a `None`. No hay
   camino para que una cuenta existente se sume.
3. **Tope del plan.** El tope sale de
   `billing_service.get_plan(org.plan or "premium")["users"]`. Un helper
   nuevo, `_emails_de_miembros`, cuenta los usuarios del estudio, dueño
   incluido.
   - Al invitar: responde 400 «El estudio ya ocupa los {tope} usuarios de
     su plan, contando las invitaciones pendientes.» si miembros más
     pendientes sin vencer llegan al tope.
   - Al registrarse: responde 400 «El estudio ya tiene los {tope} usuarios
     de su plan.» si los miembros ya llegaron. Hace rollback y la invitación
     queda pendiente.
4. **Un solo uso.** Pasos del registro:
   - Gasta la invitación con
     `UPDATE invitations SET status='accepted' WHERE id=… AND status='pending'`.
   - Comprueba `rowcount == 1`; si no, hace rollback y responde 400 «Esta
     invitación ya fue usada».
   - Recién después cuenta el tope.
   - Hace un solo commit con el usuario.

   El estudio se lee con `FOR UPDATE` al invitar y al registrarse.

## 3. Qué deja una carrera

| Carrera | Antes (`ea64a9c`) | Ahora |
|---|---|---|
| Dos registros con la misma invitación, SQLite | `[(200, ''), (500, 'No pudimos procesar tu solicitud…')]` | `[200, 400 «ya fue usada»]`, un usuario, invitación `accepted` |
| Lo mismo, Postgres | dos 500 (el `TypeError`) | `[(200, ''), (400, 'Esta invitación ya fue usada')]` |
| Dos registros con invitaciones distintas por el último lugar, SQLite | `[(200, ''), (200, '')]`: entran los dos | `[200, 400 «los 2 usuarios»]`, miembros 2, `['accepted', 'pending']` |
| Lo mismo, Postgres | dos 500 | `[(200, ''), (400, 'El estudio ya tiene los 2 usuarios de su plan.')], miembros 2, ['accepted', 'pending']` |
| Dos invitaciones enviadas a la vez por el último lugar, Postgres | `[(200, ''), (200, '')], pendientes 2` | `[(200, ''), (400, 'El estudio ya ocupa los 2 usuarios de su plan, contando las invitaciones pendientes.')], pendientes 1` |
| Lo mismo, SQLite | — | **No está protegido** (riesgo abajo) |

Cómo se serializa cada base:
- **SQLite:** el primer `UPDATE` del registro toma el candado de escritura
  de la base. Por eso el tope se cuenta después de gastar la invitación: el
  otro registro espera y cuenta con el primero ya adentro.
- **Postgres:** el `FOR UPDATE` sobre el estudio serializa los registros y
  las invitaciones del mismo estudio.

Las carreras son reales, no secuenciales. En SQLite, dos hilos esperan
juntos en una barrera después del hash de la clave. En Postgres, cada
invitación espera en su commit, ya pasado el control del tope. Espera a que
la otra también llegue al commit o quede frenada en el candado, mirado en
`pg_stat_activity`. No hay esperas fijas: el plazo de 20 s sólo corre si no
pasa ninguna de las dos.

## Supuestos reversibles

- **Las pendientes cuentan por email distinto.** Una pendiente de alguien
  que ya es miembro no cuenta. Reinvitar a un email pendiente no ocupa otro
  lugar y responde 200, como hoy.
- **El `FOR UPDATE` sobre el estudio**, al invitar y al registrarse. Es una
  fila por estudio y por pedido, no un candado global.
- **Los tres textos de error nuevos** (arriba).
- **Una invitación «expired» con fecha futura** responde «ya fue usada»,
  porque no está pendiente. Hoy sólo `validate_invitation` marca «expired»,
  y lo hace con la fecha vencida, así que no debería existir.

## D26 y D27: contestadas

- **D26 (a) por ahora.** No hay forma de cancelar una invitación pendiente.
  Se lo proponés a Emi. No la empiezo sin tu aviso.
- **D27 (b): es ORG-1b**, abajo.

## ORG-1b: el registro con invitación trae el email invitado

En `landing.html`, cuando `/api/invitations/{token}` responde válida y trae
email:
- El email del registro se completa con ese email.
- Queda `readOnly`, no `disabled`, así viaja en el envío.
- Debajo aparece «Es el email al que te invitaron.».

Sin `invite`, con un token que no existe, con uno ya usado o con una
respuesta válida sin email, el campo queda como antes: vacío y editable. El
servidor no cambia, y su 400 sigue siendo la guarda.

**La prueba** es `scripts/testing/pantalla_org1b.js`. Usa Playwright, la API
local de verdad y datos inventados. Los casos van en este orden:

1. Sin `invite`, y con un token que no existe: el campo queda vacío y
   editable, y la línea no se ve. El registro se abre con el botón del
   inicio, como lo haría una persona.
2. Respuesta válida sin email: igual que el caso 1. Es el único caso con la
   respuesta simulada (`page.route`), porque la API no deja invitar sin
   email.
3. Invitación válida con el email cambiado a mano en el DOM (se le sacan
   `readOnly` y `disabled`): da 400, y el error dice «otro email».
4. Invitación válida:
   - el email viene completo, es de sólo lectura y no `disabled`;
   - la línea se ve;
   - escribir encima no lo cambia;
   - el registro da 200, manda el email y el token, y la invitada queda en
     el estudio.
5. El mismo token ya usado: igual que el caso 1.

**Rojo antes del producto** (contra `373ef55`): `FALLA: con invitación
válida el email no viene completo: {"value":"","readOnly":false,"disabled":false}`.

**Dos sabotajes no daban su rojo en la primera vuelta**, y los arreglé en la
prueba (`5d42909`):
- **«La línea se ve siempre»:** sin invitación válida, el registro está
  cerrado, así que «no se ve» era cierto para cualquier cosa. Ahora la
  prueba abre el registro antes de mirar.
- **«Además disabled»:** caía antes, en el caso del DOM, con un 422. Ahora
  ese caso saca también `disabled`, como haría quien edita el DOM.

| Sabotaje (`sabotajes/org1b.sh`) | Rojo |
|---|---|
| no se completa el email | «con invitación válida el email no viene completo» |
| el email completo queda editable | «con invitación válida el email no es de sólo lectura» |
| además `disabled` (no viaja en el envío) | «con invitación válida el email está disabled» |
| la línea del email invitado no aparece | «con invitación válida no se ve la línea del email invitado» |
| la línea se ve siempre | «sin invite: se ve la línea del email invitado» |
| se bloquea aunque la invitación no traiga email | «válida sin email: el email no queda vacío y editable» |
| el servidor deja de exigir el email invitado | «con el email cambiado en el DOM el registro dio 200, no 400» |

**Supuesto reversible:** el texto «Es el email al que te invitaron.».

La captura a 390 px se ve bien. El campo de sólo lectura se ve igual que uno
editable; lo explica la línea de abajo. No le cambié el estilo, porque no lo
pediste.

## DESPACHO-1a: el catálogo del cliente en Excel

En la pestaña Catálogo del cliente, arriba de «Productos aprendidos», hay un
botón «Descargar en Excel». Baja `GET /api/clientes/{id}/catalogo/productos.xlsx`:
- un renglón por producto de `ClientProductHistory` de ese cliente y ese
  dueño, en el orden de la pantalla (el último usado primero);
- columnas: Posición, Descripción, Origen, Valor unitario promedio,
  Cantidad promedio, Peso unitario promedio, Veces usado, Última vez;
- un cliente ajeno o que no existe da el mismo 404 que
  `/catalogo/productos` (`_get_owned_client`); sin sesión, 401;
- todo texto se escribe como texto. El que empieza con `=`, `+`, `-` o
  `@` además lleva el apóstrofo invisible (`quotePrefix`), así sigue
  siendo texto si alguien edita la celda;
- la posición va como texto y con formato de texto (`@`), tal como está
  guardada: `01012100`, `0402100Z`, `0101.21.00`.

Toqué `proyecto_maria/main.py` (el endpoint y `_catalogo_xlsx`),
`proyecto_maria/templates/dashboard_v2.html` (el botón),
`proyecto_maria/static/v2/screens/clientes.js` (la descarga) y
`CHANGELOG.md`.

| Pieza | SHA |
|---|---|
| Casos en rojo antes del producto | `ee82997` |
| **Producto y `CHANGELOG.md`** | **`e438dad`** |
| Prueba en el navegador y sabotajes (14, uno por motivo); ajuste del mensaje del caso de aislamiento | `51890cd` |
| **SHA probado** | **`51890cd`** |

Su diff propio parte del merge de tu rama que trajo la tarea:
`git diff fe1571c..51890cd`.

**Rojo antes del producto:**
- `tests/test_despacho1a.py` contra `fe1571c`: `13 failed, 5 warnings in 0.70s`;
  todos por la ruta que no existía (`{"detail":"Not Found"}`).
- `pantalla_despacho1a.js` contra `fe1571c`:
  `FALLA: 1280 px: no se ve «Descargar en Excel»`, salida 1.

**Los casos** (`tests/test_despacho1a.py`, 13 con los parametrizados):
- el archivo se abre con openpyxl y trae lo guardado, fila por fila y en
  orden;
- la posición como texto, con ceros y letra;
- el catálogo vacío trae sólo los encabezados;
- `=HYPERLINK(...)`, `+1+1`, `-2+3` y `@SUMA(A1)` en la descripción, y
  `=1` en el origen, quedan como texto con `quotePrefix`;
- caracteres de control en la descripción no rompen la descarga;
- el nombre del archivo es ASCII aunque el cliente se llame
  «Ñandú Café — … 🚢»;
- otro dueño recibe el mismo 404 que el catálogo de la pantalla, y en el
  cuerpo no aparece el producto;
- un cliente que no existe da 404;
- no se mezclan productos de otro cliente ni de otro dueño;
- sin sesión da 401.

**En el navegador** (`scripts/testing/pantalla_despacho1a.js`, API local y
datos inventados, 1280 y 390 px): carga dos productos, uno con `=1+1` en
la descripción, abre el catálogo, aprieta el botón, baja el archivo y lo
lee con openpyxl. Compara las descripciones con la pantalla y las
posiciones con la API, y exige que sean texto. Salida:
`OK 1280 px: «catalogo_cliente_inventado_d1a_1280.xlsx» trae ["=1+1 NOTEBOOK INVENTADA","CABALLO INVENTADO"], posiciones ["8471.30.12","0101.21.00"], todo como texto`,
y lo mismo a 390 px.

**Sabotajes** (`scripts/testing/sabotajes/despacho1a.sh 51890cd`): salida
0, `sabotajes sin rojo: 0`. Sin sabotaje, las pruebas y la pantalla dan
verde.

| Sabotaje | Rojo (copiado de la salida) |
|---|---|
| no se mira de quién es el cliente | `test_otro_dueno_recibe_el_mismo_404_que_en_el_catalogo`, «assert 200 == 404» |
| la consulta no filtra por dueño | `test_no_se_mezclan_…`, «trae productos de otro dueño» |
| la consulta no filtra por cliente | `test_no_se_mezclan_…`, «trae productos de otro cliente» |
| se puede bajar sin sesión | `test_sin_sesion_da_401`, «assert 404 == 401» |
| «=» queda como fórmula | `test_una_descripcion_con_formula_queda_como_texto[=HYPERLINK…]`, «assert 'f' == 's'» |
| sin el apóstrofo invisible | `…[+1+1]` y `…[@SUMA(A1)]`, «quotePrefix» |
| la posición sólo de dígitos sale como número | `test_la_posicion_sale_como_texto_con_ceros_y_letra`, «1012100» |
| la posición sin formato de texto | `test_la_posicion_…`, «number_format» |
| el orden no es el de la pantalla | `test_el_archivo_se_abre_y_trae_lo_guardado`, «TELEFONO INVENTADO» |
| cantidad y peso cruzados | `test_el_archivo_…`, «450.25» |
| el catálogo vacío sale sin encabezados | `test_un_catalogo_vacio_trae_solo_los_encabezados` |
| no se limpian los caracteres de control | `test_una_descripcion_con_caracteres_de_control_…`, «IllegalCharacterError» |
| el nombre del archivo va como viene | `test_el_nombre_del_archivo_es_ascii`, «UnicodeEncodeError» |
| el botón no está conectado | `FALLA: 1280 px: el botón no bajó nada` |

En la primera vuelta, el sabotaje «no filtra por cliente» dio rojo, pero
el mensaje de pytest cambiaba según las pruebas de antes en la misma base.
Le puse al caso un mensaje propio para cada fuga (`51890cd`). El rojo es
el mismo, ahora se lee.

**Puertas de DESPACHO-1a, sobre `51890cd`:**

| Puerta | Resultado |
|---|---|
| Las 12 de `tests/` que tocan clientes, catálogo o DESPACHO-1a | `249 passed, 3 warnings in 71.12s (0:01:11)` |
| `compileall -q proyecto_maria` | `compile-ok` (rc 0) |
| `node --check …/clientes.js` | `js-ok` |
| `pantalla_despacho1a.js` | `OK 1280 px …` y `OK 390 px …`, salida 0 |
| `sabotajes/despacho1a.sh 51890cd` | `sabotajes sin rojo: 0`, salida 0 |

**Sin correr todavía**, para el `/entregar` del 28/10 a las 18:00 UTC: la
suite completa sobre el SHA final, `smoke_friccion.sh`,
`ataque_aislamiento.sh` (no cubre esta ruta nueva: el aislamiento de esta
ruta lo cubren los casos y tres sabotajes), subagentes, `/code-review high`
y `/security-review`.

**Supuestos reversibles:**
- Se limpian los caracteres de control que Excel no acepta. Sin eso, la
  descarga da 500 con una descripción así.
- El nombre del archivo, en ASCII: `catalogo_<nombre>.xlsx`. El servidor
  y la pantalla lo arman cada uno, con el mismo criterio.
- El apóstrofo invisible (`quotePrefix`) en lo que empieza con
  `=`, `+`, `-` o `@`.
- La fecha como fecha de Excel, `dd/mm/yyyy`, y el día en UTC, igual que
  la pantalla (`slice(0, 10)`).
- El texto del botón, «Descargar en Excel», y el toast «Descarga iniciada.».

**Riesgos de DESPACHO-1a:**
- **Empates en «última vez».** En Postgres, los productos aprendidos en un
  mismo pedido llevan el mismo `now()`. El orden entre ellos no está fijado,
  ni en la pantalla ni en el Excel, y puede salir distinto entre una y
  otro. No lo arreglé: cambiaría también la consulta de la pantalla.
- **Un texto de más de 32767 caracteres** se escribe entero; Excel lo corta
  al abrirlo o se queja. No lo vi en el catálogo; no lo traté.
- **Un promedio NaN** se escribiría como NaN. El aprendizaje no debería
  dejarlo; no lo traté.
- **A 390 px el tablero ya se corre 133 px de costado**, con o sin el botón
  (lo medí también sacando el botón). El botón se ve entero. No es de esta
  pieza y no lo toqué.

## Puertas de ORG-1 y ORG-1b

| Puerta | Resultado |
|---|---|
| `tests/test_org1.py` sobre `ddfc798` | `46 passed, 3 warnings in 31.56s` |
| Los mismos casos contra `ea64a9c` | `36 failed, 10 passed, 39 warnings in 45.26s` |
| `org1_postgres.py`, Postgres 16 local, sobre `ddfc798` | `fallas: 0`, 3 de 3 corridas |
| Lo mismo contra `ea64a9c` | `fallas: 15` |
| `sabotaje_org1.sh 18f7f25` | `OK: los 9 sabotajes dan rojo por la razón esperada`, salida 0 |
| Suite completa, worktree limpio en `18f7f25` | `1 failed, 3323 passed, 302 skipped, 2 xfailed, 94 warnings in 505.43s (0:08:25)` |
| `compileall -q proyecto_maria` | rc 0 |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `ataque_aislamiento.sh` | `Bloqueado: 22 · Fugas: 0`, «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.» |
| ORG-1b: `sabotajes/org1b.sh 5d42909` | `sabotajes sin rojo: 0`, salida 0; los 7 dan su rojo, y sin sabotaje la prueba da verde |
| ORG-1b: `pantalla_org1b.js` contra `373ef55` | `FALLA: con invitación válida el email no viene completo`, salida 1 |
| ORG-1b: `test_pa1_textos`, `test_regression_phase0`, `test_static_endpoints` (las que leen la landing) y `test_org1`, sobre `5d42909` | `93 passed, 1 skipped, 3 warnings in 32.68s` |

Los casos corren cada uno dos veces, `sqlite_sin_zona` y
`postgres_con_zona`. El segundo inyecta un `expires_at` con zona al cargar
la fila, que es lo que hace asyncpg.

**El único rojo de la suite** es
`test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`.
Es el de tiempo ya informado en SUFIJOS-1, 1c y 1d: «la subida normal dio
400 a los 30.0 s: … tardó demasiado». ORG-1 no toca la lectura de Excel.

**Sabotajes** (`sabotaje_org1.sh`). Cada uno vuelve a lo de antes o rompe
una guarda:

| Sabotaje | Qué hace | Rojos |
|---|---|---|
| `fecha_sin_zona` | vuelve a comparar con `datetime.utcnow()` | 14 failed |
| `sin_email` | cualquiera con el enlace entra | 10 failed |
| `invitar_sin_tope` | invitar sin tope | 13 failed |
| `tope_fijo` | tope 3 escrito a mano | 10 failed |
| `vencida_ocupa` | guarda: una pendiente vencida ocupa lugar | 2 failed |
| `reinvitar_ocupa` | guarda: reinvitar ocupa otro lugar | 1 failed |
| `registro_sin_tope` | registrarse sin tope | 3 failed |
| `gasto_sin_condicion` | gasta sin mirar si seguía pendiente | 2 failed |
| `contar_antes` | cuenta el tope antes de gastar (la carrera de SQLite) | 1 failed |

Dos sabotajes más se aplicaron a mano en Postgres, porque el candado sólo se
ve ahí:
- Sin `FOR UPDATE` al invitar: `FALLA | dos invitaciones a la vez por el
  último lugar: sale una ([(200, ''), (200, '')], pendientes 2)`, 3 de 3.
- Sin `FOR UPDATE` al registrarse: `FALLA | dos invitaciones por el último
  lugar: entra una ([(200, ''), (200, '')], miembros 3, ['accepted',
  'accepted'])`, 3 de 3.

**Lo que no corrí:**
- Subagentes adversariales, `/code-review` ni `/security-review`. No tengo
  cuota hasta el 28/10 a las 18:00 UTC. La autorrevisión del diff completo
  contra `ea64a9c` es sólo mía, sin independencia. Por eso todavía no
  entrego.
- ORG-1: la pantalla en un navegador. ORG-1 no toca pantallas.
- ORG-1b: la suite completa ni el smoke. ORG-1b cambia sólo la plantilla
  `landing.html`; corrí las pruebas que la leen, arriba.

## Comandos

Este muestra sólo lo de ORG-1:

```bash
git diff ea64a9c..ddfc798
```

Este tiene que dar `46 passed`:

```bash
python -m pytest -q --no-cov -p no:randomly tests/test_org1.py
```

Este tiene que dar «OK: los 9 sabotajes dan rojo por la razón esperada» y
salida 0:

```bash
scripts/testing/sabotaje_org1.sh 18f7f25 <venv>
```

Este tiene que dar `fallas: 0`. Usá un Postgres local y descartable; el
script rechaza cualquier host que no sea local:

```bash
python scripts/testing/org1_postgres.py postgresql://<usuario>@127.0.0.1:<puerto>/<base>
```

Este muestra sólo lo de ORG-1b:

```bash
git diff 373ef55..5d42909
```

Este tiene que terminar con `OK ORG-1b`. Va contra una API local
levantada con datos inventados:

```bash
BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_org1b.js
```

Este tiene que dar `sabotajes sin rojo: 0` y salida 0. Necesita `node` y
el Chromium de Playwright:

```bash
PY=<venv>/bin/python scripts/testing/sabotajes/org1b.sh 5d42909
```

Este muestra sólo lo de DESPACHO-1a:

```bash
git diff fe1571c..51890cd
```

Este tiene que dar `13 passed`:

```bash
python -m pytest -q --no-cov -p no:randomly tests/test_despacho1a.py
```

Este tiene que terminar con `OK 1280 px …` y `OK 390 px …`, y salida 0. Va
contra una API local levantada con datos inventados:

```bash
BASE_URL=http://127.0.0.1:<puerto> PY=<venv>/bin/python node scripts/testing/pantalla_despacho1a.js
```

Este tiene que dar `sabotajes sin rojo: 0` y salida 0. Arma su propio
worktree, su SQLite y su API en el puerto 8853:

```bash
PY=<venv>/bin/python scripts/testing/sabotajes/despacho1a.sh 51890cd
```

## Riesgos de ORG-1 y ORG-1b

- **ORG-1b: una invitación a un email que la pantalla no acepta queda sin
  salida.** Invitar sólo exige una «@» (`a@b` entra). La pantalla, al
  enviar, pide `usuario@dominio.tld` y responde «Email no válido». Con el
  campo de sólo lectura, el invitado no lo puede cambiar. Antes de ORG-1b
  también quedaba sin salida, porque otro email da el 400 de ORG-1. Es de
  antes y no lo cambié. Si querés, va como D.

- **La carrera de dos invitaciones a la vez no está protegida en SQLite.**
  `FOR UPDATE` no hace nada ahí, y la invitación no escribe antes de
  contar. Puede quedar un lugar de más pendiente. Al registrarse, el tope se
  vuelve a controlar, así que no entra un miembro de más. Producción es
  Postgres, y ahí está cubierta.
- **En Postgres puede faltar el índice único de `users.email`.** El modelo
  lo declara, pero no comprobé la base de producción, y no la toco. Ahora la
  carrera del mismo email la frena la invitación, no el índice.
- **El registro con un email de prueba reemplazable** confirma ese borrado
  antes de los controles de la invitación. Es de antes y ORG-1 no lo cambia.
- **El 400 «es para otro email»** dice que el email escrito no es el
  invitado. No dice cuál es. Hace falta el token para preguntar.

Última vuelta: Wed Oct 28 05:46:09 UTC 2026

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. ORG-1, ORG-1b y DESPACHO-1a listas y subidas SIN ENTREGAR sobre 4ce6d22 (suite 4ce6d22: 3670 passed, 0 failed). DESTINO-1 hecha y subida SIN ENTREGAR: producto 7526be9, pruebas hasta f887b4a (sabotajes destino1.sh 15/15; suite f887b4a 3697 passed, 0 failed). SUFIJOS-2 hecha y subida SIN ENTREGAR: SHA probado 4ca6829 (sabotajes sufijos2.sh 9/9; suite 3731 passed, 0 failed); D29 contestada (a). SEGURO-1 hecha y subida SIN ENTREGAR: SHA probado 371cde2 (sabotajes seguro1.sh 10/10; suite a08de1f 3777 passed, 0 failed); D30 contestada (a), riesgo «seguro 0 en el TXT si nadie lo completa»; SEGURO-2 no se empieza hasta verla en PARA-DEV-2. DESPACHO-1b hecha y subida SIN ENTREGAR encima de SEGURO-1 y del merge 49f8e29: producto 0591722, pruebas e59e1a8, SHA probado e59e1a8 (50 casos; sabotajes despacho1b.sh 24/24; suite 3827 passed, 336 skipped, 2 xfailed, 0 failed; smoke y aislamiento 0); D31 abierta (qué guarda el catálogo de un despacho; recomiendo a). Pendiente: el 28/10 después de las 18:00 UTC, en orden, /entregar de ORG-1+ORG-1b+DESPACHO-1a sobre 4ce6d22 (subagentes hasta alto, /code-review high, /security-review, Postgres 55432 para org1_postgres.py), DESTINO-1, SUFIJOS-2, SEGURO-1 (con /security-review) y DESPACHO-1b; timbre «Dev MARIA: entregué <PIEZA> en <SHA>». PESO-NETO-1 y PRORRATEO-1 esperan al despachante. La próxima D es la D32. Nunca main, sin push --force, sin datos reales del 24/10 ni despachos del 28/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
