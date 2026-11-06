# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CATALOGO-LARGO-2 (devolución): **entregada**: producto en `d5bc7c1`, pruebas en `b0bbd8c` (el informe va en el commit siguiente) (2026-11-06)

| Causa de la devolución | Resultado | Qué decidís |
|---|---|---|
| 1. Una entrada mala da 500 y pierde el lote | Una sola regla, `texto_para_guardar`, en los cuatro campos (descripción, origen, proveedor y NCM) y en las tres vías (lote, `guardar-uso`, `PUT`): `null` es vacío; lo que no es texto da 400 «El {campo} tiene que ser texto.»; un NUL se saca; un medio par da 400 «Hay un carácter que no se puede guardar.»; después va el tope de 2000. El lote se valida entero antes de escribir: una entrada mala da 400 con el motivo y no se guarda nada; el usuario la corrige y lo vuelve a mandar. Caso `test_una_entrada_mala_da_400_o_se_limpia_sin_perder_el_lote`, con NUL, medio par, `null`, `false` y lista como datos. En Postgres, chequeos «una entrada mala por lote / guardar-uso / cambio no da 500 ni pierde lo bueno» | **D84**: el lote se rechaza entero o guarda lo bueno |
| 1 (encontrado al atacarla) Un NCM de 21 a 2000 caracteres daba 500 en Postgres y perdía el lote | `MAX_NCM = 20`: 400 «El NCM pasa de 20 caracteres.» por el lote y el `PUT`; la columna sigue en `String(20)` | Nada |
| 1 (encontrado al atacarla) Un precio `NaN`, `Infinity` o enorme rompía la lectura del catálogo o daba 500 | `_precio` sólo guarda un número finito; lo demás se ignora como antes se ignoraba lo que no era número. Caso `test_un_precio_que_no_es_finito_no_rompe_la_lectura_del_catalogo` | Nada |
| 2. Una fila vieja con otra clave queda duplicada y sin editar | El arranque (`_migrate_catalogo_claves`) le da la clave de hoy a cada fila sin letras ni números latinos cuya clave no es la que calcula `clave_de_producto`. Si esa clave ya la tiene otra fila del mismo proveedor, no la mueve y lo cuenta. Caso `test_una_fila_vieja_sin_letras_latinas_queda_una_sola_y_editable` (CJK, emoji y mezcla como datos, la fila armada con el `PUT` de la base y el arranque real); la que choca: `test_una_fila_vieja_que_la_migracion_no_mueve_sigue_editable` | Nada |
| 3. El arranque se traba con un `guardar-uso` y el log miente | `_migrate_catalogo_sin_tope` toma una tabla por transacción, con `lock_timeout` de 5 s, y escribe «✅ Migracion: … pasa a TEXT» después del commit. En Postgres, el chequeo «el arranque y una escritura como guardar-uso andan los dos» abre las dos conexiones; con la tabla tomada, el arranque falla en vez de seguir con las columnas cortas | Nada |

**Cuatro decisiones nuevas: D84 a D87.** D79 (a) quedó hecha. D76–D78 y D80 siguen en CATALOGO-3, D81 queda igual y el tope sigue en 2000, como dijiste.

**Una diferencia con tu pedido, a propósito.** Pediste «ninguna entrada mala pierde lo bueno del lote». Con la regla que elegí, una entrada mala da 400 y no se guarda **nada** del lote: no da 500 y no se pierde nada en silencio, pero lo bueno no queda guardado hasta que el usuario corrige la mala. Es D84; si elegís (b) es otra vuelta.

**`guardar-uso` ahora limpia el NUL** (antes daba 400): es la misma regla para todos los campos, como pediste. Eso cambia el contrato de DISCO-1, y la suite completa lo mostró: `test_confirmar_con_algo_que_la_base_no_guarda_da_400_y_no_guarda` tenía tres filas que esperaban 400 por un NUL y el mensaje viejo del medio par con el nombre del campo. En `dc9bcce` (`test:`) saqué esas tres filas: el NUL ahora se limpia y el medio par da «Hay un carácter que no se puede guardar.», igual en todos los campos. Los patrones de `disco1.sh` quedaron al día; corrido sobre `dc9bcce` sin Postgres: 39 ROJO, 7 SIN PG; sobre `b0bbd8c` con Postgres: 46 ROJO, «sabotajes sin rojo: 0». Si preferís que `guardar-uso` siga rechazando el NUL, decilo y es otra vuelta.

**Un rojo que no era de esta pieza, arreglado en la prueba.** `tests/unit/test_validations.py::test_valid_pdf_upload` llegó con `0a410ac` (de otra sesión, entró por tu rama). Pasa en tu `2524216` y fallaba en la mía, 3 de 3 corridas: `HTTPException: 400: Invalid PDF file: Stream has ended unexpectedly`. La causa es la suma con RENDIMIENTO-1c (mía, sin aceptar): la validación del PDF corre en otro proceso, y el mock de `pypdf` dentro del proceso de la prueba no llega ahí. En `b0bbd8c` (`test:`) la prueba arma un PDF real de una hoja en vez de un mock. El producto no cambia.

**Ojo para publicar, sigue igual:** la rama tiene `e0b8626` (COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a, sin aceptar). Ningún SHA mío sirve para publicar hasta que esas cinco estén ✅. El último limpio es `9018d77`. Esta pieza migra claves en el arranque.

**Archivos de producto:**
- `proyecto_maria/core/catalog_service.py`: `texto_para_guardar` y `MAX_NCM` (nuevos), `_precio`, `save_products` (valida el lote entero antes de escribir), `update_product` (valida todo antes de tocar la fila).
- `proyecto_maria/main.py`: `_migrate_catalogo_sin_tope` (una tabla por transacción, log después del commit), `_migrate_catalogo_claves` (nueva), `guardar-uso` y `catalog_update_product` con la regla.
- `proyecto_maria/services/client_memory.py`: el origen pasa por la misma regla.
- `proyecto_maria/database/models.py`: sin cambio neto (el NCM pasó a `Text` en `642d903` y volvió a `String(20)` en `1ecab6f`).
- `CHANGELOG.md`.

`producto +153/−75` (78 netas). Por qué más de 20: la regla de texto compartida y la del NCM, validar el lote entero antes de escribir, la migración de claves (nueva, ~35 líneas) y partir la migración por tabla.

### Decisiones

**D84. Un lote con una entrada mala, ¿se rechaza entero o guarda lo bueno?**
- (a) Se rechaza entero con 400 y el motivo; no se escribe nada. **Recomiendo esta (es lo que entregué).** Es atómico y simple, nada se pierde en silencio, y el usuario ve qué fila corregir. El lote viene de una factura: guardar la mitad deja un catálogo que no es ni el de antes ni el de la factura.
- (b) Se guardan las buenas y la respuesta lista las malas. Más cómodo cuando hay una sola mala en cien, a cambio de una respuesta nueva que la pantalla tiene que mostrar.

**D85. Un proveedor sólo CJK o emoji da `vendor_id` vacío.** Anterior a la pieza; es la misma causa que D76. Lo encontró el adversario: dos proveedores así comparten catálogo.
- (a) Va con D76 en CATALOGO-3. **Recomiendo esta.**
- (b) Dejarlo.

**D86. `_ncm_recordado_con_sim_del_proveedor` compara con `_normalize` y no con `clave_de_producto`.** Para lo que es sólo CJK no encuentra el NCM recordado. Anterior a la pieza; es parte de D78.
- (a) Va con D78 en CATALOGO-3. **Recomiendo esta.**
- (b) Dejarlo.

**D87. Un sabotaje de DESPACHO-1b no corre desde RENDIMIENTO-1d.** «sin el tope de RunLength» (`scripts/testing/sabotajes/despacho1b.sh:325`) busca la línea de `run_length_maximum_output_length` con 8 espacios; `0897f28` (RENDIMIENTO-1d, mío) la dejó con 4 en `_TOPES`. El patrón tampoco está en la base `5e69f63` (lo miré con `git show`; el sabotaje no lo corrí ahí): no lo causa esta pieza, pero ese tope de memoria quedó sin sabotaje que lo cuide y en su momento no lo vi.
- (a) Arreglo el patrón en un commit `test:` aparte, apenas entregue, y muestro el rojo. **Recomiendo esta**: es una línea del arnés y el tope es de memoria.
- (b) Va a la cola de limpieza.

### SHAs

| SHA | Qué |
|---|---|
| `5e69f63` | base (informe de RESET-1) |
| `c76e42d` | test: rojos en Postgres de entradas malas, filas viejas CJK y arranque con escrituras en curso |
| `d135557` | fix: la regla de texto, la fila vieja y la migración por tabla |
| `ea81a44`, `a1f5317` | test: casos, sabotajes y la fila que choca |
| `9be34ad` | test: rojos del NCM de más de 20 y del precio que no es finito |
| `642d903` | fix: el precio finito (y el NCM a `Text`, que `1ecab6f` vuelve atrás) |
| `c787a1d`, `b1990e9` | test: el caso del precio no deja la base trabada; sabotajes |
| `3c64c43` | test: rojo del NCM de más de 20 por el lote y el `PUT` |
| `1ecab6f` | fix: el NCM de más de 20 da 400 y la columna queda en 20 |
| `da4eaa4` | test: el tope del NCM en casos, Postgres y sabotajes |
| `d5bc7c1` | fix: un docstring en dos líneas |
| `47da2ca` | merge de tu rama; difiere de `d5bc7c1` sólo en lo que trae tu rama |
| `04e0e70` | test: con la tabla tomada el log no dice «migrado»; el sabotaje del origen encuentra su patrón |
| `dc9bcce` | test: DISCO-1 sin las filas del NUL y del medio par con el contrato viejo; patrones de `disco1.sh` |
| `b0bbd8c` | test: `test_valid_pdf_upload` con un PDF real |

### Para reproducir

```bash
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
# 1. los casos: «40 passed»
python -m pytest -q --no-cov -p no:randomly tests/test_catalogo_largo2.py
# 2. Postgres local y descartable: todo «OK» y «fallas: 0»
python scripts/testing/catalogo_largo2_postgres.py postgresql://cdi@127.0.0.1:55462/postgres
# 3. lo mismo en ccfe640: «fallas: 7» (las tres causas)
# 4. sabotajes: todo «ROJO», «fallas: 0»
PY=$(command -v python) PG_URL=postgresql://cdi@127.0.0.1:55462/postgres scripts/testing/sabotajes/catalogo_largo2.sh 04e0e70
# 5. chequeo-6: «avisos: 1» (las 78 netas)
python docs/pm/herramientas/chequeo-6.py 5e69f63 d5bc7c1
```

### Puertas sobre `b0bbd8c`

| Puerta | Resultado (salida exacta) |
|---|---|
| Suite completa, base limpia | `4989 passed, 335 skipped, 3 xfailed, 95 warnings in 875.12s (0:14:35)`, salida 0 |
| Casos de la pieza | `40 passed, 3 warnings in 34.72s` |
| `catalogo_largo2_postgres.py`, Postgres 16 local | 21 `OK`, «fallas: 0», salida 0 |
| `compileall` | sin salida |
| `smoke_friccion.sh` | `[FAIL] POST /api/ui/event`: el rojo de entorno conocido («Evento sin sesión no admitido», `smoke_wave1` no está en la lista; ver mi informe anterior). Con un evento admitido: «OK · telemetría + alias session/state + by-cuit protegido», salida 0 |
| `ataque_aislamiento.sh` | «Bloqueado: 47 · Fugas: 0 · Sin probar: 0», «PUERTA G3 PASADA», salida 0 |

La primera corrida del ataque dio salida 1 por el entorno, no por el producto: `ModuleNotFoundError: No module named 'fastapi'`. El script no lee `PY`: usa `./venv/bin/python` o, si no está, el `python3` del sistema, y en este contenedor no hay `venv/`. La segunda corrida fue con el entorno virtual primero en el `PATH`.

### Rojos en `ccfe640`, Postgres 16

```
FALLA | el arranque y una escritura como guardar-uso andan los dos: en cola True, arranque DBAPIError("(sqlalchemy.dialects.postgresql.async…
FALLA | «螺丝钉» de una fila vieja es una sola fila y sigue editable: 200, claves ['viejo cjk', '~8a356ec0dfde1fd0b96596abb1693e978c238…
FALLA | «🔩🔩» de una fila vieja es una sola fila y sigue editable: 200, claves ['viejo emoji', '~37d73ae206f105cd3fab62d7b749ed3d195c…
FALLA | «螺丝🔩» de una fila vieja es una sola fila y sigue editable: 200, claves ['viejo mezcla', '~6c582e312db561dab50fd6d90a928a85a…
FALLA | una entrada mala por lote no da 500 ni pierde lo bueno: ['proveedor nulo: 500 {"detail":"No pudimos procesar tu solicitud. Probá de…
FALLA | una entrada mala por guardar-uso no da 500 ni pierde lo bueno: ['descripción null: 500 {"detail":"No pudimos procesar tu solicitud.…
FALLA | una entrada mala por cambio no da 500 ni pierde lo bueno: ['descripción nulo: 500 {"detail":"No pudimos procesar tu solicitud. Prob…
fallas: 7
```

(Líneas cortadas a 140 caracteres.) En pytest sobre la base: `14 failed, 20 deselected` en los casos de la entrada mala y de la fila vieja.

### Sabotajes

| Script | SHA | Resultado |
|---|---|---|
| `catalogo_largo2.sh`, con `PG_URL` | `04e0e70` | 37 ROJO, «fallas: 0», salida 0 |
| `disco1.sh`, con `PG_URL` | `b0bbd8c` | 46 ROJO, «sabotajes sin rojo: 0», salida 0, ninguno SIN PG |
| `despacho1b.sh` | `04e0e70` | 136 ROJO (111 en una corrida y 25 en la del resto, sin repetir), 1 ROTO: «sin el tope de RunLength: el sabotaje no encontró su patrón» (es D87, ya informado), «sabotajes sin rojo: 0» |

Después de `04e0e70` cambiaron sólo pruebas de DISCO-1 y la del PDF; el producto y los casos de esta pieza son los mismos.

### chequeo-6

Sobre lo mío (`d5bc7c1`):

```
chequeo-6 5e69f63..d5bc7c1: avisos para mirar, no un veredicto
producto +153/−75
  AVISO producto suma 78 líneas netas: el informe dice por qué (§6: más de 20)
arnés +481/−74
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/catalog_service.py: 596 → 636
  proyecto_maria/main.py: 11947 → 11986
  proyecto_maria/services/client_memory.py: 306 → 305
avisos: 1
```

El AVISO: las 78 netas, explicadas arriba en «Archivos de producto».

Sobre `47da2ca` da `producto +162/−19547`, `arnés +598/−4459`, historia vacía y `avisos: 0`: lo ensucia el retiro de v1 que trae tu rama. No sirve para medir esta pieza.

### Hallazgos

| # | Quién (modelo, esfuerzo) | Hallazgo | Qué hice |
|---|---|---|---|
| 1 | adversario Sonnet, alto (sólo leyó) | ALTA: un NCM de 21 a 2000 caracteres da 500 en Postgres y pierde el lote | Rojo en `3c64c43`; arreglado en `1ecab6f` |
| 2 | adversario Sonnet, alto | MEDIA-ALTA: `NaN` o `Infinity` en el precio rompen la lectura del catálogo | Rojo en `9be34ad`; arreglado en `642d903` |
| 3 | adversario Sonnet, alto | BAJA-MEDIA: un proveedor sólo CJK da `vendor_id` vacío | D85 |
| 4 | adversario Sonnet, alto | BAJA: la fila que choca queda; la migración no mira claves que ya empiezan con «~» | Riesgo |
| 5 | adversario Sonnet, alto | BAJA: los otros caminos que escriben la memoria del cliente no pasan por `texto_para_guardar` | Riesgo |
| 6 | adversario Sonnet, alto | BAJA: `/api/catalog/match` da 500 con `vendor_name` en lista | Riesgo, fuera de la pieza |
| 7 | `/code-review high` (sin pasada de verificación) | El NCM es texto libre y llega a una columna de 20 | Arreglado: `MAX_NCM` |
| 8 | `/code-review high` | `_ncm_recordado…` usa `_normalize` | D86 |
| 9 | `/code-review high` | Comentarios con historia | Sacados |
| 10 | `/code-review high` | `guardar-uso` ahora limpia el NUL donde daba 400; la migración por tabla no tiene try/except y frena el arranque | Es la regla elegida; frenar es a propósito (con el tope viejo, guardar-uso respondería sin guardar) |
| 11 | `/code-review high` | `update_product` no arregla una clave vieja al editar; recorre la tabla en cada arranque; `_precio` acepta `bool`; ayudantes de limpieza repetidos; un import a mitad del archivo | Riesgos o cola de limpieza, sin cambio |

### Riesgos

- El tope del NCM está dos veces con distinto texto: `MAX_NCM` («El NCM pasa de 20 caracteres.») y `_HISTORIAL_MAX_NCM` en `guardar-uso` («La NCM…»). Para la cola de limpieza.
- Un `PUT` que choca con otra fila da 404, no 409.
- El lote acepta un NCM que no es de 8 dígitos (hasta 20 caracteres). Anterior a la pieza.
- Una fila que choca en la migración queda: dos filas con la misma descripción. El arranque lo cuenta en el log («… quedan por un choque»).
- `_migrate_catalogo_claves` recorre en cada arranque las filas sin letras latinas; con muchas, suma tiempo al arranque.
- El sabotaje de la atomicidad del lote no distingue del todo: el caso de la entrada mala también pasa rojo por otro motivo.
- Las corridas de sabotajes sobre `b1990e9` y `da4eaa4` no cuentan: la primera se cortó por tiempo y la segunda tuvo un VERDE y un ROTO, arreglados en `04e0e70`. La que vale es la de `04e0e70`.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP, aviso a la PM session_01B7FVQspcEHF7PqNv797wNM. CATALOGO-LARGO-2 (devolución) entregada: producto d5bc7c1, pruebas b0bbd8c (informe en el commit siguiente); D84 a D87 nuevas; sigo con PYPDF-1, después RESET-2. Nada se publica sin el «dale» de Emi para el SHA, nunca main, sin secretos ni datos reales.
