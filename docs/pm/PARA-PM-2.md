# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega Holanda→423 sobre `a910c5f` (2026-11-16 22:25 UTC)

**Resultado.** Tus criterios 1, 2, 3, 4 y 6 se cumplen en `a910c5f`. El 5 se cumple para el
selector, lo tipeado y la etiqueta de la pantalla, pero no para dos lugares que muestran lo
guardado tal cual (D261). Base: `8d2cacc` (tu rama hasta ahí). Producto: `producto +23/−18`, en
`maria_generator.py`, `despacho_lector.py` y `paises_maria.js`.

- **Cómo queda.** `paises_maria.js` sigue siendo la única tabla. Pierde `{"code":"434","name":"HOLANDA"}`
  (309 → 308 países), `"HOLANDA"` pasa a `"423"`, y entra `const REEMPLAZOS = {"434":"423"}`. La
  pantalla (`resolve`) y el servidor (`_reemplazos` → `codigo_de_pais`) leen esa misma constante; el
  código reemplazado tiene que estar en la tabla, como antes. El lector de despachos pasa por
  `codigo_de_pais`. Lo guardado no se migra.
- **Criterio 1.** Un caso, `test_holanda_y_paises_bajos_son_423`, con la familia como datos:
  `PAISES_BAJOS` (16 formas: «NL», «NLD», «423», «HOLANDA», «Holanda», «434», «0434», «434 · HOLANDA»,
  «434 - Holanda», «423 · HOLANDA», «434 · PAISES BAJOS»…) más el número 434 y el despacho
  «434 HOLANDA». Mira el catálogo, la exportación, los dos lectores (factura y despacho, este con tu
  agregado de `9491b80`), el TXT (`CARTPAYORI` y `CARTPAYPRC` = 423 para cada forma), la etiqueta de
  la pantalla para cada forma («423 · PAISES BAJOS») y que el selector no tenga ninguna opción con 434
  ni HOLANDA. Pantalla y servidor se comparan forma por forma en
  `test_la_pantalla_y_el_servidor_reconocen_los_mismos_paises`, que suma la familia. Reemplaza a
  `test_paises_bajos_es_423_y_holanda_434`.
  - Lo que **no** es Holanda tampoco da 423: `NO_SON_HOLANDA` = «434.», «４３４», «423 · 434»,
    «434 · 434», «4340», «00434», «434 · BELGICA», «434 - Vietnam» dan ningún país en el servidor y
    en la pantalla.
- **Criterio 2.** Volcado de 6742 formas (todos los códigos 000–999 con y sin 0 adelante, con «· X»
  y con « HOLANDA», cada «código · nombre» y «código - nombre» de la tabla, los alias, los nombres
  INDEC, los ISO3) por servidor, pantalla, importación, exportación y lector de despachos, más las
  opciones del selector, en `8d2cacc` y en `7924f36` (el producto de `a910c5f` es el mismo). Pantalla y
  servidor coinciden en las 6742, antes y después. El diff entero (columnas: servidor, pantalla,
  importa, exporta, despacho):

  ```
  formas sólo antes: [] sólo después: []
  '0434' ['434', '434', '434', '434', '0434'] -> ['423', '423', '423', '423', 'NL']
  '423 - HOLANDA' ['', '', '310', '212', ''] -> ['423', '423', '423', '423', 'NL']
  '423 HOLANDA' ['', '', '310', '212', ''] -> ['', '', '310', '212', 'NL']
  '423 · HOLANDA' ['', '', '310', '212', 'NL'] -> ['423', '423', '423', '423', 'NL']
  '434 - HOLANDA' ['434', '434', '434', '434', 'HOLANDA'] -> ['423', '423', '423', '423', 'NL']
  '434 · HOLANDA' ['434', '434', '434', '434', ''] -> ['423', '423', '423', '423', 'NL']
  '434 · PAISES BAJOS' ['', '', '310', '212', ''] -> ['423', '423', '423', '423', 'NL']
  '434 · X' ['', '', '310', '212', ''] -> ['', '', '310', '212', 'NL']
  '434' ['434', '434', '434', '434', ''] -> ['423', '423', '423', '423', 'NL']
  'HOLANDA' ['434', '434', '434', '434', 'HOLANDA'] -> ['423', '423', '423', '423', 'NL']
  'Holanda' ['434', '434', '434', '434', 'Holanda'] -> ['423', '423', '423', '423', 'NL']
  'holanda' ['434', '434', '434', '434', 'holanda'] -> ['423', '423', '423', '423', 'NL']
  lector de despachos, «NNN HOLANDA» o «NNN - HOLANDA» que guardaba el nombre y ahora «NL»: 1511
  selector: sale ['434 · HOLANDA'] entra [] (309 -> 308 opciones)
  ```

  Todas las filas tienen 434 o HOLANDA. Las 1511 son códigos que no están en la tabla seguidos de
  «HOLANDA» («500 HOLANDA»): el lector caía al nombre y guardaba «HOLANDA»; ahora el nombre es 423 y
  guarda «NL». «310 HOLANDA» sigue sin origen (código y nombre se contradicen). «434 · X» y
  «423 HOLANDA» en el despacho: ver supuesto 2.
- **Criterio 3.** Lo guardado que puede tener un código de país, y su dato con 434:

  | campo | ¿vuelve a generar? | dato con 434 que genera 423 |
  |---|---|---|
  | `client_product_history.origen_frecuente` (memoria del cliente) | sí: `/api/catalog/lookup` → `upload.js` → `it.origen` | `test_holanda_guardada_genera_423`: «434», «0434», «HOLANDA», «Holanda», «434 · HOLANDA» escritos por SQL; el lookup los devuelve tal cual y, como origen y procedencia, dan 423/423 |
  | `vendor_catalog_products.origen` (catálogo del proveedor) | sí: `match_items` → mismo lookup | el mismo caso, por la vía del proveedor |
  | borrador de la pantalla (`localStorage cdi_v2_state:<pestaña>`: `items[].origen`, `operacion.procedencia`) | sí: el origen va al servidor tal cual; la procedencia pasa por `resolve` (`finalize.js:921-924`) | las formas de `PAISES_BAJOS` (entre ellas «434 · HOLANDA» del selector viejo) en la pantalla y en el TXT del criterio 1 |
  | `operation_items.origen` (ítems de una operación guardada) | no vuelve a la generación: ninguna pantalla recarga los ítems; lo usan `agrupar`, las métricas del cliente, `export.csv` y la cotización | `agrupar` compara con `clave_de_origen`: los `GRUPOS` del criterio 4; las métricas, D261 |
  | `clients.default_origin` | no vuelve a la generación | — |

  No guardan país: `Operation.extra`, `VendorCatalogProduct.extra`, la procedencia por ítem. No se
  regeneran: el TXT en disco, `PublicQuote.snapshot_data`, `SystemBackup`.
  `data/product_catalog.json` y `client_service.py` son código muerto. **En producción no se midió:**
  no hay base para medir cuántas filas tienen 434.
- **Criterio 4.** «NL» + «HOLANDA», «NL» + «434», «Países Bajos» + «434 HOLANDA» (como lo guarda el
  lector de despachos) y «HOLANDA» + el número 434 en un mismo grupo generan un solo `CARTPAYORI=423`.
  «434» + «BELGICA» sigue dando «mismo origen», además del dato que ya existía
  (`test_generar_maria_txt.py:692`, CN y US).
  - **La premisa no se cumple:** ninguna prueba ni sabotaje de PAIS-NL fijaba el error para esos
    pares. En `8d2cacc` el único que dice «mismo origen» es el de CN y US, y el caso viejo de Holanda
    no arma grupos. Lo midió sólo el acta `REPRODUCCION-PAIS-NL-2026-11-13.md`. No hubo nada que
    re-apuntar ni que sacar.
- **Criterio 5.** El selector ya no ofrece «434 · HOLANDA», «HOLANDA» tipeado da 423 y la etiqueta
  (`label`, la que usa NCM para mostrar el origen) da «423 · PAISES BAJOS» para toda la familia;
  las tres cosas están fijadas en el caso. No hay generador del JS: el xlsx no está en el repo; la
  línea 1 del JS sigue nombrando la fuente. Lo que no se cumple, en D261.
- **Criterio 6.** Rojo con el producto de `8d2cacc` y las pruebas de `a910c5f`: `4 failed, 243 passed`
  (salida abajo).

**Lo que decidís vos:**

1. **D261. Dos lugares de la pantalla muestran lo guardado tal cual, y con un 434 viejo muestran
   «434».** Los encontró el adversario Opus; los verifiqué leyendo el código.
   - Métricas del cliente, «Origen frecuente» (`main.py:8466-8475`, `clientes.js:1139`): suma los
     orígenes por país con `clave_de_origen`, pero muestra la forma guardada más usada. En la base la
     pantalla guardaba «434» en los ítems para Holanda; con `["434"]*3 + ["NL"] + ["US"]*3` muestra
     «434». Hoy también muestra «CHINA» o «310» tal cual.
   - Procedencia en la revisión (`review.js:252-271`, `normalizeValueForField`): un borrador guardado
     con «434 · HOLANDA» lo muestra así. El TXT sale 423, porque `finalize.js` resuelve antes de
     mandar. Hoy pasa con cualquier país escrito a mano.

   Opciones:
   - (a) Mostrar los dos con `label` (métricas en el servidor o en `clientes.js`; procedencia al
     cargar el borrador). Cambia lo que se ve para todos los países («CN» → «310 · CHINA»).
   - (b) Dejarlo: lo guardado se muestra como se guardó.

   Recomiendo **(a), como pieza aparte**: es una línea en cada lugar más su prueba, pero cambia la
   pantalla para todos los países, y eso no lo pediste. No lo hice.
2. **D262. `_reemplazos` es la tercera copia de «leer una constante de `paises_maria.js`»** (con
   `_tabla_oficial` y `_nombres_de_pais`). Lo marcó `/code-review`.
   - (a) Una línea para `COLA-LIMPIEZA.md`: una sola `_constante_de_la_pantalla(nombre)`.
   - (b) Nada.

   Recomiendo **(a)**. No unifiqué: dos son de la base y sus líneas son anclas de sabotajes.

**Supuestos (reversibles):**

1. **«434 HOLANDA», separado sólo por un espacio, da 423 en el lector de despachos y no en el TXT ni
   en la pantalla.** Ninguna de las dos reconoce «código nombre» con sólo un espacio, para ningún
   país («310 CHINA» tampoco). Tu agregado de `9491b80` ata «434 HOLANDA» al lector de despachos, que
   es el único que lo lee; de ahí llega al grupo y al TXT como «NL».
2. **El lector de despachos toma las tres primeras cifras y no mira lo que sigue si no es un nombre**
   («423.», «434.», «434 · 434», «434 · X» dan NL). Es la base: «310 · X» ya daba CN. Lo nuevo es sólo
   que el 434 ahora tiene país. «４３４» sí lo fijé (da ningún país), y «３１０ CHINA» da CN por el
   nombre en la base y ahora (medí los 1000 códigos en cifras de ancho completo: idénticos).
3. **El docstring de `_tabla_oficial` dice «308 países: 434 sale como 423».** La base ya tenía la
   cuenta («309»); la actualicé en vez de sacarla.

| qué | SHA |
|---|---|
| base (tu rama hasta ahí) | `8d2cacc` |
| producto y CHANGELOG: Holanda y 434 son 423 | `b89ba7d` |
| pruebas: el caso con la familia, lo guardado, los sabotajes | `4d3cc16` |
| producto: `REEMPLAZOS` en vez de alias (de `/code-review`) | `9d6595e` |
| pruebas: `NO_SON_HOLANDA`, sabotajes a `REEMPLAZOS` | `4f63d23` |
| pruebas: ancla de `sabotaje_maria1a.sh` que quedó repetida | `7924f36` |
| tu `9491b80`, integrado | `734598f` |
| pruebas: texto esperado de tres sabotajes de pantalla | `0e9f886` |
| pruebas: etiqueta, selector, 434 con otro país. **Lo que se entrega** | `a910c5f` |
| informe | el commit siguiente |

## Comandos

```bash
VENV=/ruta/al/venv   # el tuyo
# 1. el rojo con el arreglo revertido: el producto de la base con las pruebas de a910c5f
git worktree add -f /tmp/rojo423 a910c5f && (cd /tmp/rojo423 && git checkout 8d2cacc -- proyecto_maria \
  && env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake \
     PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider \
     tests/test_catalogo3.py tests/test_country_catalog_frontend.py tests/test_maria3_antes_de_generar.py | tail -1); \
  git worktree remove -f /tmp/rojo423
#    «4 failed, 243 passed»

# 2. los guiones de sabotaje que anclan lo que toqué (catalogo3 tardó 37 minutos acá)
PY=$VENV/bin/python bash scripts/testing/sabotajes/catalogo3.sh a910c5f | tail -2
#    «fallas: 0»
bash scripts/testing/sabotaje_maria3.sh a910c5f $VENV | tail -1
#    «OK: los 32 sabotajes dan rojo por la razón esperada»
bash scripts/testing/sabotaje_maria1a.sh a910c5f $VENV | tail -1
#    «OK: los 10 sabotajes dan rojo por la razón esperada»

# 3. anclas y §6
python3.12 scripts/testing/anclas_perdidas.py a910c5f | grep -E '^revisión|perdida'
#    «2553 anclas medidas», perdidas 0, 0 y 0
python3.12 docs/pm/herramientas/chequeo-6.py 8d2cacc a910c5f
#    «producto +23/−18», «arnés +117/−26», «avisos: 0»
```

El 1, como lo medí (mismo worktree, mismas pruebas):

```
FAILED tests/test_catalogo3.py::test_holanda_y_paises_bajos_son_423 - assert ...
FAILED tests/test_catalogo3.py::test_holanda_guardada_genera_423 - AssertionE...
FAILED tests/test_country_catalog_frontend.py::test_country_catalog_uses_maria_codes_and_legacy_aliases
FAILED tests/test_maria3_antes_de_generar.py::test_la_procedencia_acepta_todos_los_paises_de_la_pantalla
================== 4 failed, 243 passed, 5 warnings in 33.10s ==================
```

Los motivos: «At index 8 diff: 434 != 423» (la familia), «['434', '434'] == ['423', '423']» (lo
guardado), «309 == 308» (las dos de la tabla).

El 3:

```
revisión a910c5f8: 103 guiones, 2553 anclas medidas y 11 llamadas sin medir
  perdida, una línea          0   guiones: 0
  perdida, varias líneas      0   guiones: 0
  perdidas de una línea sin repetir (archivo y texto): 0
chequeo-6 8d2cacc6..a910c5f8: avisos para mirar, no un veredicto
producto +23/−18
arnés +117/−26
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/despacho_lector.py: 900 → 899
  proyecto_maria/core/maria_generator.py: 2391 → 2394
  proyecto_maria/static/v2/paises_maria.js: 47 → 50
avisos: 0
```

El grep de historia de §6 sobre `proyecto_maria/` da vacío. Producto +5 netas: no pasa de 20.

## Sabotajes (§3)

`catalogo3.sh` suma 12, con `H=test_holanda_y_paises_bajos_son_423`:
- en el servidor: «Holanda vuelve a ser 434», «no lee el código 434», «da 423 para 434 con el nombre
  de otro país»;
- en la pantalla: «vuelve a dar 434 para Holanda», «el selector vuelve a ofrecer 434 · HOLANDA» (en la
  tabla), «el selector ofrece 434 · HOLANDA aparte de la tabla» (en `optionMarkup`), «no lee el código
  434», «compara el nombre con el código escrito», «muestra Holanda como 434 · HOLANDA» (en `label`),
  «da 423 para 434 con el nombre de otro país»;
- «el despacho con 434 vuelve a quedar sin origen» y «un grupo con dos países vuelve a generar».

Se re-apuntó uno: «la pantalla vuelve a aceptar un nombre que contradice el código» ataca la línea
nueva del `return` de `resolve`. `sabotaje_maria3.sh` queda igual a la base: su ancla 18 es otra vez
una línea del producto. `sabotaje_maria1a.sh`: el ancla de la tabla ISO3 suma `, **_PAISES_NORM`,
porque `_reemplazos` repetía el texto viejo (lo encontró `anclas_perdidas.py`).

Los textos esperados de pantalla son «item: (…)» y no «one more item: (…)»: pytest escribe «one more
item» sólo con una diferencia, y estos sabotajes dejan de 2 a 6 («N more items, first extra item»).
Cada uno de los cuatro de pantalla con texto propio lo medí a mano con el archivo de pruebas entero:
pone en rojo sólo `test_la_pantalla_y_el_servidor_reconocen_los_mismos_paises` o `$H`.

`catalogo3.sh` sobre `a910c5f` (22:02:50 → 22:39:24 UTC): 65 sabotajes (53 de la base y 12 nuevos),
los 65 `ROJO` por la razón esperada, ningún `ROJO?`, `VERDE` ni `ROTO`; termina con «fallas: 0»,
salida 0.

## Revisión

- **`/code-review high`** sobre `8d2cacc..4d3cc16`: el 434 como alias aceptaba «434.», «４３４»,
  «423 · 434» y «434 · 434», y el lector de despachos daba NL con «４３４». De ahí `REEMPLAZOS`
  (`9d6595e`). Sobre `8d2cacc..a910c5f`: 7 hallazgos, ninguno cambia código.
  - «434 HOLANDA» no se reconoce en el TXT ni en la pantalla: supuesto 1.
  - «0434 HOLANDA» de un despacho queda sin origen: la expresión del lector es `^(\d{3})\b`; en la
    base pasa igual con «0310 CHINA». Va a riesgos.
  - Se sacó `_codigo_de_la_tabla`, que limitaba a cifras 0-9: `codigo_de_pais` hace el mismo control;
    medido, supuesto 2.
  - `GRUPOS` llama a `origen_iso2` al importar el módulo: si un día lanza, se cae la colección entera,
    no un caso. El guion lo diría «ROJO?», no verde. No lo cambié.
  - `_reemplazos` es la tercera copia: D262.
  - «308 países» en el docstring: supuesto 3.
  - Los «item: (…)» dependen del orden de los datos: si cambia, el guion dice «ROJO?», no verde.
- **Adversario Opus alto** (sobre `4f63d23`): no encontró ninguna forma de Holanda que siga dando 434
  o nada, ni otro país que cambie (probó 0–9999, alias, INDEC, separadores, cifras de otros
  alfabetos). Encontró los tres sabotajes de pantalla que el guion no reconocía (`0e9f886`) y D261.
- **Adversario Sonnet alto** (sobre `4f63d23`): cuatro mutaciones quedaban verdes: `label` mostrando
  «434 · HOLANDA», una opción «434 · HOLANDA» en `optionMarkup`, y «434 · <otro país>» dando 423 en el
  servidor y en la pantalla. Ahora las cuatro dan rojo (medido a mano) y son sabotajes (`a910c5f`).
  También: `test_holanda_guardada_genera_423` generaba con lo guardado y no con lo que devolvía el
  lookup; ahora usa lo devuelto. Previos, no de esta pieza: los alias que sólo viven en `ALIASES` no
  tienen prueba de su código («PUERTO RICO» 223 → 224 queda verde), y la contradicción código/nombre
  de `origen_iso2` tampoco.
- **`/security-review`** sobre `8d2cacc..a910c5f`: sin hallazgos con confianza ≥ 8. `REEMPLAZOS` se
  busca con tres cifras ASCII (no hay `__proto__`), `_reemplazos` lee un archivo fijo del repo.

## Puertas

| puerta | SHA | resultado |
|---|---|---|
| suite completa, worktree limpio, `test.db` borrada | `a910c5f` | `6197 passed, 110 skipped, 3 xfailed` en 20:43 (22:02:50 → 22:23:38 UTC), salida 0 |
| `e2e_maria.sh` | `a910c5f` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» |
| `sabotajes/catalogo3.sh` | `a910c5f` | «fallas: 0», 65 de 65 `ROJO`, salida 0 |
| `sabotaje_maria3.sh` | `4f63d23` | «OK: los 32 sabotajes dan rojo por la razón esperada»; el producto, `test_maria3_antes_de_generar.py` y el guion no cambian de `4f63d23` a `a910c5f` (`git diff --stat` vacío) |
| `sabotaje_maria1a.sh` | `7924f36` | «OK: los 10 sabotajes dan rojo por la razón esperada»; ídem hasta `a910c5f` |
| pruebas vecinas (catalogo3, catalogo_largo2, generar_maria_txt, maria1a, ncm_batch_frontend, punta_a_punta1, despacho1a, despacho1c, excel1_lectura, maria1c_avisos_lectura, country_catalog_frontend, maria3) | `9d6595e` | `593 passed, 2 xfailed` |

No corrí `test_despacho1b`: lo medís vos. Los 110 `skipped` no los comparé con `-rs` contra otra
corrida.

## Riesgos

- **Lo guardado en producción no se midió.** Si hay filas con «434», generan 423; las métricas del
  cliente y un borrador viejo las muestran como están (D261).
- **El despachante puede seguir usando 434.** Tu DECISIONS de las 19:39 dice que va en una línea con
  el pedido del próximo «dale»; no lo verifiqué.
- **«0434 HOLANDA» en un despacho queda sin origen** (y cualquier «0NNN NOMBRE»): igual que en la base.
- **El lector de despachos no ve la contradicción con «·»** («434 · CHINA» da NL, «310 · BELGICA» da
  CN): igual que en la base.
- La CI deselecciona tests de presupuestos y Railway no la espera: no es red.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`, rutina trig_01Ukttby1fc4sGVQfSn1jC9U; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `9491b80`). Aceptadas: las de antes (CUIT-GENERAR `29327d2` … D257 (b) `3c7eb14`); D244 (a) entregada sobre `6112322`. En revisión: Holanda→423, entregada sobre `a910c5f` (base `8d2cacc`), informe en el commit siguiente; puertas verdes sobre `a910c5f` (suite 6197 passed, e2e OK, catalogo3, maria3 y maria1a). Abiertas mías: D259, D260 (si no las contestaste con D244), D261 (lo guardado se muestra tal cual en métricas y procedencia; recomiendo (a) como pieza aparte) y D262 (tres lecturas del JS; recomiendo (a), cola). Después viene D239 (a): la escribe la PM al aceptar Holanda→423; no la toco antes. `test_despacho1b`: lo mide la PM. Próxima D: D263. Sin pieza marcada «apenas entregues»: si al despertar no hay nada nuevo, termino la vuelta. Lecciones (además de las de antes, que siguen en el historial de este archivo): pytest escribe «one more item» sólo con una diferencia: un texto esperado de sabotaje se mide a mano antes de escribirlo; `O=… && (…) & (…) &` deja `$O` vacío en la segunda subshell: cada comando lleva su ruta; un adversario puede borrar el worktree de un guion mío: los adversarios trabajan sólo en sus propios worktrees, y un «fatal: Unable to read current working directory» en un guion es eso; una función nueva que copia una comprensión de otra repite su ancla: `anclas_perdidas.py` antes de commitear; horas, sólo de `date -u`. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe.
