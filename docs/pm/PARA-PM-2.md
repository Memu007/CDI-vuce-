# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CATALOGO-LARGO-2: **entregada** en `ccfe640` (el informe va en el commit siguiente) (2026-11-06)

| Punto de la tarea | Resultado | Qué decidís |
|---|---|---|
| Un origen de más de 5 (`TAIWAN`) o un proveedor de más de 200 no dan 200 sin guardar ni 500 | `origen` y `vendor_nombre` del catálogo y `origen_frecuente` de la memoria del cliente pasan a `Text`; el arranque las pasa a `TEXT` en Postgres. Se guardan enteros por las cinco vías: catálogo, cambiar un producto, guardar-uso, aprender y cargar una operación. Casos `test_el_origen_y_el_proveedor_no_tienen_tope_en_la_base` y `test_la_memoria_del_cliente_guarda_el_origen_entero` (4 vías como datos) | Nada |
| …o un 400 con el motivo | Más de 2000 caracteres en el proveedor o el origen dan 400 «El proveedor pasa de 2000 caracteres.» / «El origen pasa de 2000 caracteres.», sin guardar nada (ni catálogo ni `ncm_historial`). Caso `test_un_proveedor_o_un_origen_de_mas_de_2000_dan_400_sin_guardar`, 5 vías como datos. Aprender y la operación no lo guardan en la memoria del cliente y la operación avisa `historial_guardado: false` (`test_la_memoria_del_cliente_no_guarda_un_origen_de_mas_de_2000`) | El número 2000, abajo en «Supuestos» |
| Lo que normaliza a vacío (sólo CJK o emoji) no contesta `historial_guardado: true` sin guardar, ni se cruza | `clave_de_producto`: si `_normalize` da vacío, la clave es `~` + 40 hex de sha256 del texto en NFC sin mayúsculas. «螺丝» y «螺母», «🔩» y «🔧» quedan en filas distintas, se encuentran y se cambian. Caso `test_lo_que_no_tiene_letras_latinas_se_guarda_sin_cruzarse` (catálogo y guardar-uso) y `test_cambiar_la_descripcion_a_una_sin_letras_latinas_mueve_la_clave` | Nada |
| El tope de 2000 se cuenta igual en los dos lugares | Un solo `validar_largo(texto, que)` en `catalog_service.py`, en NFC; lo usan el catálogo, cambiar un producto, guardar-uso (`_problema_historial`) y la memoria del cliente | Nada |
| Lo que diste por cierto | **No se cumple:** un proveedor sólo CJK o emoji sigue dando `vendor_id` vacío. Ver «Contradicción» | D76 |

**Seis decisiones nuevas: D76 a D81.** Las anteriores siguen como las dejaste.

**El TXT cambia y tiene prueba.** Antes la memoria del cliente guardaba «TAI», «JAP», «ALE»: `get_pais_codigo` da 310 (China) para casi cualquier recorte de tres letras, así que el lookup con cliente sugería China. Ahora guarda el origen entero. La prueba afirma `get_pais_codigo("TAIWAN") == 313 != get_pais_codigo("TAI")` y lo mismo para JAPON y ALEMANIA.

**Ojo para publicar, sigue igual:** la rama tiene `e0b8626` (COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a, sin aceptar). Ningún SHA mío sirve para publicar hasta que esas cinco estén ✅. Esta pieza además migra columnas en el arranque.

**Archivos de producto:**
- `proyecto_maria/core/catalog_service.py`: `MAX_DESCRIPCION`, `validar_largo` (ahora con `que`), `clave_de_producto` (nueva), `save_products`, `update_product`, `lookup`.
- `proyecto_maria/database/models.py`: `VendorCatalogProduct.origen` y `.vendor_nombre`, `ClientProductHistory.origen_frecuente` a `Text`; docstring.
- `proyecto_maria/services/client_memory.py`: el origen entero y medido.
- `proyecto_maria/main.py`: `_migrate_catalogo_sin_tope` (nueva), `_problema_historial`, guardar-uso.
- `CHANGELOG.md`.

### Contradicción con tu veredicto

Escribiste que siete nombres de proveedor, incluidos sólo emoji y sólo CJK, «dan siempre un id que cumple `is_valid_vendor_id`». En `fb677d9`:

```
'螺丝厂' '' False
'🔩🔩' '' False
'Ningbo 螺丝厂' 'ningbo' True
```

(`_vendor_key(v)` y `is_valid_vendor_id(_vendor_key(v))`.) El adversario Opus lo reprodujo por la API: guardar con ese proveedor da 200 y `GET /api/catalog/` con ese id da 404. Dos proveedores sólo CJK distintos caen en el mismo `vendor_id ''`. Es anterior a la pieza y la tarea no lo pide: va como D76.

### Decisiones

- **D76. Proveedor sólo CJK o emoji: `vendor_id` vacío.** Se mezclan sus catálogos y quedan filas que la API no puede leer ni editar.
  - (a) Darle la misma salida que a la descripción: `~` + hash cuando el slug queda vacío, y que `is_valid_vendor_id` lo acepte.
  - (b) 400 «El proveedor necesita letras latinas o números».
  - (c) Dejarlo.
  - **Recomiendo (a), en una pieza chica.** (b) deja afuera a un proveedor real; (a) usa algo que ya está probado. Toca la ruta y la migración de las filas con `''`, por eso no entra acá. Junto con esto, el prefijo de 60: dos proveedores largos que comparten los primeros 60 caracteres comparten catálogo.
- **D77. Descripción mezclada se cruza.** «螺丝 M8x20» y «螺母 M8x20» dan la misma clave `m8x20` y se pisan (`clave_de_producto` en `fb677d9`: `'m8x20' 'm8x20'`). Anterior a la pieza.
  - (a) Que la clave incluya el hash cuando `_normalize` sacó letras que no son latinas.
  - (b) Dejarlo.
  - **Recomiendo (a)**, con su migración que une filas. Cambia la clave de filas que hoy existen: pide su pieza.
- **D78. La memoria del cliente y el NCM recordado siguen con la clave vieja.** `main.py:9931` (`_ncm_recordado_con_sim_del_proveedor`) compara con `_normalize`, y la memoria del cliente busca por `_normalize`: para lo que es sólo CJK no encuentra lo guardado.
  - (a) Que las dos usen `clave_de_producto`.
  - (b) Dejarlo.
  - **Recomiendo (a), pieza chica.** No lo hice acá porque la memoria del cliente tiene su propio índice único y la tarea no lo nombra.
- **D79. NUL o medio par en el origen o el proveedor del catálogo.** En SQLite se guarda; en PG daría 500 (inferido, no corrido). guardar-uso ya lo limpia con `_sin_nul`.
  - (a) Limpiarlo o dar 400 en el catálogo como en guardar-uso.
  - (b) Dejarlo.
  - **Recomiendo (a)**, junto con D76.
- **D80. El origen no se valida como país.** Hoy entra cualquier texto hasta 2000; `pdf_extractor.py:574-575` todavía recorta el origen a 3 al leer la factura, y el PUT de `origen_para_catalogo` sólo acepta 2 letras.
  - (a) Una pieza que defina qué es un origen válido y lo use en los tres lugares.
  - (b) Dejarlo.
  - **Recomiendo (a).** El recorte del extractor puede dar el mismo 310 que arreglé en la memoria.
- **D81. `app.js:1945` pinta `value="${item.origen}"` sin escapar.** Antes el origen tenía 5 caracteres en PG; ahora llega a 2000. La descripción (`app.js:1940`) ya estaba igual. No confirmé que ese `item.origen` venga del catálogo en pantalla.
  - (a) Escapar los dos con la función que ya usa la pantalla.
  - (b) Dejarlo.
  - **Recomiendo (a), con revisión de seguridad.** Lo marcó la revisión de seguridad como riesgo, no como hallazgo confirmado.

### Supuestos (reversibles)

- **El tope es 2000, el mismo de la descripción.** La tarea dice «se guardan enteros o 400»; sin tope, `Text` dejaba que unos 7 MB de pedido ocuparan unos 100 MB en la base, porque el nombre del proveedor se copia en cada una de hasta 500 filas (lo midió el adversario Opus). Usé el número que ya existe para no inventar otro.
- **guardar-uso mide dos veces:** en la ruta, para dar el 400 a la vista antes de tocar nada, y en el upsert, que es el piso para las otras vías.
- **Una fila sin descripción se salta antes de medirla**, así su origen no frena al resto del lote.

### SHAs (base `93cbdef`)

| SHA | Qué |
|---|---|
| `24a7aea` | test: rojos del origen y proveedor largos, la descripción sin letras latinas y el tope en NFC |
| `1f69b33` | fix: el catálogo guarda entero el origen y el proveedor y da clave a lo que no tiene letras latinas |
| `045304a` | refactor: comentarios de la clave y de la migración en dos líneas |
| `b644dee` | test: sabotajes del origen y el proveedor sin tope, la clave sin letras latinas y la migración |
| `1c15753` | test: rojo de 2000 caracteres CJK distintos en Postgres |
| `fce1d50` | fix: la clave de lo que no tiene letras latinas es un resumen que entra en el índice |
| `68bef16` | test: sabotajes de la clave en resumen |
| (`fb75e41`…`195b96c`, `351653c`) | SESION-1 v2 y merges tuyos, en el medio |
| `e6bb333` | test: rojos del origen cortado en la memoria del cliente y del tope de proveedor y origen |
| `5ab13a1` | fix: el origen entero en la memoria del cliente y tope de proveedor y origen |
| `b929262` | test: sabotajes de la memoria, del tope y de la migración en PG; ß/ss y ﬁ/fi se miran en `_normalize` |
| `3678636` | merge tuyo (sólo `docs/pm`) |
| `7e0a2fc` | test: rojos del origen largo en la memoria del cliente y de la fila sin descripción que frena el lote |
| `311b2f3` | fix: el origen de más de 2000 no entra en la memoria del cliente y la fila sin descripción no frena el lote |
| `fb677d9` | test: sabotajes del tope del origen en la memoria y del orden del salto |
| `ccfe640` | test: los sabotajes de CATALOGO-LARGO-1 y DISCO-1 apuntan al tope en `validar_largo` (sólo scripts; el producto es el de `fb677d9`) |
| este commit | docs: este informe |

### Rojo sobre la base

`tests/test_catalogo_largo2.py` de `fb677d9` sobre el producto de `93cbdef` (`$S/cl2/rojo_base_fb677d9.log`):

```
FAILED tests/test_catalogo_largo2.py::test_el_origen_y_el_proveedor_no_tienen_tope_en_la_base
FAILED tests/test_catalogo_largo2.py::test_lo_que_no_tiene_letras_latinas_se_guarda_sin_cruzarse[catalogo]
FAILED tests/test_catalogo_largo2.py::test_lo_que_no_tiene_letras_latinas_se_guarda_sin_cruzarse[guardar-uso]
FAILED tests/test_catalogo_largo2.py::test_cambiar_la_descripcion_a_una_sin_letras_latinas_mueve_la_clave
FAILED tests/test_catalogo_largo2.py::test_la_memoria_del_cliente_guarda_el_origen_entero[guardar-uso]
FAILED tests/test_catalogo_largo2.py::test_la_memoria_del_cliente_guarda_el_origen_entero[aprender]
FAILED tests/test_catalogo_largo2.py::test_la_memoria_del_cliente_guarda_el_origen_entero[operacion]
FAILED tests/test_catalogo_largo2.py::test_la_memoria_del_cliente_guarda_el_origen_entero[cambiar]
FAILED tests/test_catalogo_largo2.py::test_un_proveedor_o_un_origen_de_mas_de_2000_dan_400_sin_guardar[catalogo-proveedor]
FAILED tests/test_catalogo_largo2.py::test_un_proveedor_o_un_origen_de_mas_de_2000_dan_400_sin_guardar[catalogo-origen]
FAILED tests/test_catalogo_largo2.py::test_un_proveedor_o_un_origen_de_mas_de_2000_dan_400_sin_guardar[cambiar-origen-origen]
FAILED tests/test_catalogo_largo2.py::test_un_proveedor_o_un_origen_de_mas_de_2000_dan_400_sin_guardar[guardar-uso-proveedor]
FAILED tests/test_catalogo_largo2.py::test_un_proveedor_o_un_origen_de_mas_de_2000_dan_400_sin_guardar[guardar-uso-origen]
FAILED tests/test_catalogo_largo2.py::test_la_memoria_del_cliente_no_guarda_un_origen_de_mas_de_2000[aprender]
FAILED tests/test_catalogo_largo2.py::test_la_memoria_del_cliente_no_guarda_un_origen_de_mas_de_2000[operacion]
=================== 15 failed, 5 passed, 5 warnings in 6.78s ===================
```

En SQLite no hay tope de largo, así que el defecto de la base sólo se ve completo en Postgres. `scripts/testing/catalogo_largo2_postgres.py` sobre la base (`$S/cl2pg_rojo.log` y `$S/pg_cl2_rojo.log`):

```
FALLA | primer arranque: las columnas son text y el producto viejo queda igual: [('origen', 'character varying', 5), ('vendor_nombre', 'character varying', 200)]
FALLA | el catálogo guarda enteros el origen y el proveedor: 500 {"detail":"No pudimos procesar tu solicitud. ...
FALLA | cambiar el origen lo guarda entero: 500 ...
FALLA | guardar-uso sin cliente guarda enteros el origen y el proveedor: 200 {"success":true,"historial_guardado":false} memoria del cliente 0
FALLA | guardar-uso de «螺丝» sin cliente guarda la fila: 200 {"success":true,"historial_guardado":true}
FALLA | 2000 caracteres CJK por catálogo se guardan: 500 ...
FALLA | 2000 caracteres CJK por cambiar la descripción se guardan: 500 ...
```

(recorté las filas repetidas y el texto del 500; están enteras en los logs).

### Puertas

El producto de `ccfe640` es el de `fb677d9` (`git diff fb677d9 ccfe640 -- proyecto_maria/ tests/` da vacío): las puertas de producto se corrieron sobre `fb677d9`, en un worktree limpio, una detrás de otra. Logs en `$S/cl2/puertas_fb677d9/`.

| Puerta | Salida exacta |
|---|---|
| suite completa | `4950 passed, 355 skipped, 3 xfailed, 93 warnings in 840.59s (0:14:00)`, `suite=0` |
| compileall | `compileall=0`; avisa `invalid escape sequence '\-'` en `pdf_extractor.py:927` y `:936`, líneas de `1adee11`, anteriores a la base |
| Postgres de la pieza (`catalogo_largo2_postgres.py`) | `fallas: 0`, `rc=0` |
| Postgres de CATALOGO-LARGO-1 | `fallas: 0`, `rc=0` |
| sabotajes de la pieza | 22 ROJO, `fallas: 0`, `rc=0` |
| smoke | `[FAIL] POST /api/ui/event`, `SMOKE_EXIT=1`: el rojo conocido (el evento del smoke no está en la lista permitida) |
| smoke con eventos permitidos | `OK · telemetría + alias session/state + by-cuit protegido`, `SMOKE_EXIT=0` |
| ataque de aislamiento | `Bloqueado: 47 · Fugas: 0 · Sin probar: 0`, `PUERTA G3 PASADA`, `ataque=0` |
| sabotajes de CATALOGO-LARGO-1 sobre `fb677d9` | 6 ROJO, 5 ROTO, `fallas: 5`: buscaban el tope en el código que ahora es `validar_largo` |
| sabotajes de DISCO-1 sobre `fb677d9` | 2 ROTO, `sabotajes sin rojo: 2`, por lo mismo |
| los dos, sobre `ccfe640` | CATALOGO-LARGO-1: 11 ROJO, `fallas: 0`, `rc=0`; DISCO-1: 46 ROJO, `sabotajes sin rojo: 0`, `rc=0` |

Los ROTO eran míos: unifiqué el tope y no moví sus patrones. `ccfe640` los apunta a `validar_largo`; en DISCO-1, «el tope no deja entrar el máximo» pasa a sabotear `catalog_service.py`, que es donde se cuenta ahora.

### Sabotajes (`scripts/testing/sabotajes/catalogo_largo2.sh`, 22)

`$S/cl2/puertas_fb677d9/sab_catalogo_largo2.log`: 22 ROJO, «fallas: 0», `rc=0`. Uno por motivo: tope de 5 y de 200 de vuelta; la memoria recorta a 3 al crear y al cambiar, y su columna vuelve a 3; el catálogo, cambiar, guardar-uso y la memoria sin medir proveedor u origen; la fila sin descripción medida antes de saltarla; la clave vacía, la que junta ß con ss y ﬁ con fi (casefold y NFKD en `_normalize`); guardar, buscar y cambiar con la clave vieja; el arranque sin pasar a text cada una de las tres columnas; y la clave CJK como texto entero, que no entra en el índice de PG.

**Un sabotaje corregido.** El primero de casefold metía el cambio en el hash y daba VERDE: ß/ss y ﬁ/fi tienen letras latinas, así que van por `_normalize` y nunca por el hash. No distinguía nada. Lo reemplacé por casefold y NFKD en `_normalize`, que sí dan rojo.

### Revisión

| Quién | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| Adversario | Opus alto | La memoria del cliente corta el origen a 3, da 200 con `historial_guardado: true` y el lookup sugiere 310 | Arreglado (`5ab13a1`), con su rojo en `e6bb333` |
| Adversario | Opus alto | `Text` sin tope: ~7 MB de pedido ocupan ~100 MB en la base | Arreglado con el tope de 2000 (`5ab13a1`) |
| Adversario | Opus alto | Proveedor CJK o emoji da `vendor_id ''` | Anterior. D76 y «Contradicción» |
| Adversario | Opus alto | Descripción mezclada se cruza | Anterior. D77 |
| Adversario | Opus alto | La memoria sólo CJK no se encuentra | Anterior. D78 |
| Adversario | Opus alto | NUL o medio par en origen o proveedor: 500 en PG | No reproducido. D79 |
| Adversario | Sonnet alto | El NCM recordado compara con la clave vieja (`main.py:9931`) | D78 |
| Adversario | Sonnet alto | «TAIWAN» queda «TAI» en la memoria | El mismo del Opus, arreglado |
| Adversario | Sonnet alto | El tope de 2000 estaba contado dos veces | Arreglado: `_problema_historial` usa `validar_largo` |
| Adversario | Sonnet alto | El tope cuenta distinto los espacios internos (la memoria los colapsa antes de medir) | Riesgo bajo, abajo |
| Adversario | Sonnet alto | Revertir la lista de la migración no rompe ningún pytest | Lo cubre `catalogo_largo2_postgres.py` y su sabotaje; la CI no lo corre. Riesgo, abajo |
| `/code-review` (1) | high | Hash con puntuación o ancho completo distinto de `_normalize` | Riesgo bajo: sólo pasa con texto sin ninguna letra latina |
| `/code-review` (1) | high | Docstring de `models.py` | Revisado: nombra `clave_de_producto` |
| `/code-review` (1) | high | Fuzzy contra claves `~` | Riesgo bajo: un hash no se parece a una descripción |
| `/code-review` (1) | high | Comentarios de 3 líneas | Corregidos (`045304a`) |
| `/code-review` (2) | high | La memoria sin tope del origen en aprender y la operación | Arreglado (`311b2f3`), rojo en `7e0a2fc` |
| `/code-review` (2) | high | Una fila sin descripción frena el lote por su origen | Arreglado (`311b2f3`), rojo en `7e0a2fc` |
| `/code-review` (2) | high | El PUT de `origen_para_catalogo` sólo acepta 2 letras | D80 |
| `/code-review` (2) | high | guardar-uso mide dos veces | Se queda: ver «Supuestos» |
| `/security-review` | (sobre la rama) | Nada de confianza alta: el ALTER sólo usa nombres de una lista fija | — |
| `/security-review` | (sobre la rama) | `app.js:1945` sin escapar, ahora con hasta 2000 | D81 |

Los dos `/code-review` repitieron lo de D76, D77 y D78; no los cuento dos veces.

### chequeo-6

Desde la base, el rango incluye SESION-1 v2 (ya entregada), por eso da 25 netas:

```
chequeo-6 93cbdef..ccfe640: avisos para mirar, no un veredicto
producto +157/−132
  AVISO producto suma 25 líneas netas: el informe dice por qué (§6: más de 20)
arnés +932/−118
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/auth/__init__.py: 6 → 5
  proyecto_maria/auth/dependencies.py: 185 → 194
  proyecto_maria/config.py: 48 → 45
  proyecto_maria/core/catalog_service.py: 584 → 596
  proyecto_maria/core/limites_auth.py: 99 → 103
  proyecto_maria/database/models.py: 614 → 614
  proyecto_maria/main.py: 11925 → 11939
  proyecto_maria/services/client_memory.py: 302 → 306
avisos: 1
```

Por tramos de esta pieza:

```
chequeo-6 93cbdef..68bef16: avisos para mirar, no un veredicto
producto +29/−24
arnés +497/−44
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/catalog_service.py: 584 → 593
  proyecto_maria/database/models.py: 614 → 614
  proyecto_maria/main.py: 11925 → 11921
avisos: 0

chequeo-6 195b96c..ccfe640: avisos para mirar, no un veredicto
producto +41/−27
arnés +181/−33
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/catalog_service.py: 593 → 596
  proyecto_maria/database/models.py: 614 → 614
  proyecto_maria/main.py: 11932 → 11939
  proyecto_maria/services/client_memory.py: 302 → 306
avisos: 0
```

**Por qué el AVISO queda:** la pieza suma +70/−51, 19 netas; las otras 6 son de SESION-1 v2 (+95/−89), que ya informé. El segundo tramo empieza en `195b96c`, así que incluye `351653c`, que no toca producto.

### Riesgos

- **La migración sólo la prueba Postgres:** `catalogo_largo2_postgres.py` y su sabotaje la cubren; la CI no los corre.
- **El `ALTER … TYPE TEXT` toma la tabla:** si otra conexión la tiene, el arranque sigue con las columnas cortas (lo prueba el caso «con la tabla tomada»); hasta el siguiente arranque, un origen largo vuelve a dar 500 en PG.
- **Espacios internos:** la memoria colapsa espacios antes de medir y el catálogo no. Un texto de 2000 con espacios dobles entra en la memoria y da 400 en el catálogo. Sólo diverge entre rutas distintas.
- **El hash de lo que no tiene letras latinas distingue puntuación y ancho completo**, que `_normalize` saca: «螺丝。» y «螺丝» son dos filas.

### Comandos

```bash
S=<scratchpad>; cd <repo>; git fetch origin claude/dev-maria; git checkout ccfe640
E="DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares"
# 1. el caso de la pieza: «20 passed»
env $E python -m pytest -q --no-cov -p no:cacheprovider tests/test_catalogo_largo2.py
# 2. Postgres: ninguna FALLA
python scripts/testing/catalogo_largo2_postgres.py postgresql://<u>@127.0.0.1:<puerto>/<base>
# 3. sabotajes: 22 ROJO y «fallas: 0»
PY=$(which python) PG_URL=postgresql://<u>@127.0.0.1:<puerto>/<base> bash scripts/testing/sabotajes/catalogo_largo2.sh ccfe640
# 4. la contradicción: '螺丝厂' '' False
env $E python -c "from proyecto_maria.core import catalog_service as c; v='螺丝厂'; print(repr(v), repr(c._vendor_key(v)), c.is_valid_vendor_id(c._vendor_key(v)))"
# 5. chequeo-6 por tramos: «avisos: 0» en los dos
python docs/pm/herramientas/chequeo-6.py 93cbdef 68bef16; python docs/pm/herramientas/chequeo-6.py 195b96c ccfe640
```

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP, aviso a la PM session_01B7FVQspcEHF7PqNv797wNM. CATALOGO-LARGO-2 entregada en ccfe640 (informe en el commit siguiente); D76 a D81 nuevas; sigo con RESET-1, cuyas D empiezan en D82. Nada se publica sin el «dale» de Emi para el SHA, nunca main, sin secretos ni datos reales.
