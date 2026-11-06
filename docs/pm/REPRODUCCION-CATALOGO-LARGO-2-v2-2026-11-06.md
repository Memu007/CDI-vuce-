# CATALOGO-LARGO-2, vuelta 2: reproducción de la PM (2026-11-06)

Producto `d5bc7c1`, pruebas `b0bbd8c`, informe `62214fd` (rama
`claude/dev-maria` en `21e07cf`), base `5e69f63`. Veredicto: **aceptada, sin
integrar** (la rama de MARIA trae `e0b8626`, igual que `ca87d82`).

## Puertas (corridas por la PM, entorno de prueba, sin red)

| Puerta | Resultado PM |
|---|---|
| `tests/test_catalogo_largo2.py` en `b0bbd8c` | `40 passed` |
| `scripts/testing/catalogo_largo2_postgres.py` (PG 16) | 21 OK, `fallas: 0`, rc=0 |
| `chequeo-6.py 5e69f63 d5bc7c1` | `producto +153/−75`, `avisos: 1` (78 netas, explicadas en el informe), historia vacía |
| `sabotajes/catalogo_largo2.sh 04e0e70` | 37 `ROJO`, 0 `ROJO?`, 0 VERDE, 0 ROTO, `fallas: 0`, rc=0 |
| suite completa en `b0bbd8c` | `5 failed, 4984 passed, 335 skipped, 3 xfailed`, rc=1 |

Los 5 rojos de la suite son `test_despacho1b.py` (3) y `test_rendimiento1c.py`
(2): pypdf 6.21.4 responde «Maximum page tree page entry limit exceeded»
antes del tope propio. Son los mismos 5 de D73 (PYPDF-1), que ya dan igual en
la base (acta de RESET-1). La Dev informa `4989 passed`: la diferencia es la
de D73, que ya está en PYPDF-1. No son de esta pieza.

## Negativos de la PM (SQLite, `tests/test_zz_pm_cl2.py`, fuera del repo)

Ejemplos distintos de los de la devolución: seis lotes malos (medio par bajo
`\udc00` dentro de la descripción, medio par alto `\ud83d` solo, objeto y
decimal en origen, entero en NCM, entero en proveedor) y `guardar-uso` con
NCM entero.

| árbol | resultado |
|---|---|
| `d5bc7c1` | los 7 dan 400 con motivo y no guardan ninguna fila |
| `5e69f63` | 4 dan 500; los 2 medios pares dan 400 con el mensaje del codec |

## Adversarios con contexto nuevo (Opus alto y Sonnet alto, PG 16, sin red)

Ninguno encontró un 500 nuevo, una escritura a medias ni una fila perdida en
las tres vías (lote, `guardar-uso`, `PUT`). Aguantó: lote atómico, migración
de claves idempotente en tres arranques, `lock_timeout` de 5 s con la tabla
tomada (sigue sin mover nada ni decir «migrado»), 200 000 filas en 0,1 s por
arranque, 319 entradas malas sin 500 (Opus), `PUT` atómico.

Hallazgos y destino:

1. **Media (Opus): el informe de D84 dice que el usuario ve qué fila
   corregir, y no es así.** El 400 no nombra el ítem, `saveCatalogLearn` sólo
   mira `res.ok`, y la pantalla dice «Algunos productos no quedaron en la
   memoria» cuando no quedó ninguno. No empeora: en PG la base perdía el lote
   entero con 500. Va a CATALOGO-3 (el 400 nombra el ítem y la pantalla dice
   la verdad). D84 se decide igual (a).
2. **Baja-media (Opus y Sonnet), declarado por la Dev:** con choque, la
   migración mueve una fila y la otra queda con su clave latina para siempre
   (sin `ORDER BY`), y el log repite «quedan por un choque» en cada arranque.
   Cola de limpieza.
3. **Media-baja, de antes (Sonnet):** `_migrate_product_history_clave` crea el
   índice único sin `lock_timeout` (`main.py:1464`); un `guardar-uso` abierto
   traba el arranque. Cola de limpieza.
4. **Bajas, de antes:** lotes iguales o `PUT` a la vez dan 500 y pierden lotes
   buenos (búsqueda y después insert); `/api/catalog/lookup` da 500 con
   entradas raras y no limpia el NUL; precios raros (`True`→1.0, `-5`). Cola.
5. **Baja, nuevo:** proveedor `"\x00"` en el lote guarda bajo `vendor_id ""`
   (antes 500 en PG); es el destino de D85. CATALOGO-3.
6. **Cosmético:** NCM de más de 2000 dice «pasa de 2000» aunque el tope es
   20; `guardar-uso` dice «La NCM», el lote «El NCM». Cola.

Scripts: `/tmp/cdi-pm/adv-cl2v2-opus/advrun/` y
`/tmp/cdi-pm/adv-cl2v2-sonnet/advrun/` (fuera del repo).
