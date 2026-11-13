# Reproducción de CATALOGO-LARGO-2 (Dev MARIA), 2026-11-06

Producto `ccfe640`, informe `5b0ca2b`, base `93cbdef`, rama `claude/dev-maria`.
Veredicto: **devolución** (arriba de `PARA-DEV-2.md`).

## Lo que reproduje yo

API con `TestClient`, Postgres 16 descartable (`pm_cl2nul`, creada y borrada
por la PM), modos falsos, sin red ni Gemini. Usuario sintético `pmcl2nul`.
`POST /api/catalog/importadora_pm/productos` con un ítem latino y otro raro,
después `GET /api/catalog/importadora_pm`.

| árbol | lote con «🔩\ud800» | productos guardados |
|---|---|---|
| `ccfe640` | **500** (`asyncpg DataError … surrogates not allowed`, en el INSERT de `product_key '~0a7f…'`) | ninguno (404) |
| `93cbdef` | 200 | 2 (el latino de esta vuelta y el de la anterior) |

En la base, «ボルト\x00» también da 200 con el latino guardado.

## Adversarios con contexto nuevo

**Opus alto, PG 16 en `adv_cl2_opus`.**
- Bien:
  - la migración no reescribe la tabla con 200 000 filas;
  - dos arranques a la vez terminan bien;
  - con la tabla tomada, falla a los 5 s, limpio;
  - todas las escrituras pasan por `validar_largo`.
- Hallazgos que van a la devolución:
  - el NUL o medio par rompe el lote (500), lo de arriba;
  - una fila vieja con clave latina y descripción CJK queda duplicada al
    guardar otra vez esa descripción, y su `PUT` da 404
    (`catalog_service.py:495-505`);
  - deadlock entre la migración y `guardar-uso`: el orden de tablas es
    inverso, y el log «✅ Migracion» sale antes del commit
    (`main.py:1244-1256`);
  - `vendor_name` `null` o `false` da 500 (en la base, 200).

**Sonnet alto, SQLite y Chromium.**
- Sin XSS con HTML y 1930 caracteres en origen y proveedor (v2). v1 se revisó
  leyendo el código.
- Las vías del proveedor encuentran la clave `~`.
- El TXT mejora: TAIWAN da 313 y CHILE 208. En la base, «CHI» llevaba a 310
  o al rechazo.
- `historial_guardado: true` siempre tuvo algo guardado, aunque la fila CJK
  de la memoria del cliente no se recupera (D78).
- Medio par en la descripción: en la base, 200 sin guardar; en `ccfe640`, 400
  con el texto del codec de Python.
- Anteriores a la pieza, ya declarados (D76, D77): el proveedor sólo CJK da
  `vendor_id ''`, y «电线 2mm» con «钢管 2mm» se pisan.

## Puertas del informe

Corridas por la PM sobre `ccfe640`. No cambian el veredicto: la devolución
sale de lo reproducido arriba.

| Puerta | resultado |
|---|---|
| `tests/test_catalogo_largo2.py` | `20 passed`; en la base `15 failed, 5 passed` |
| `chequeo-6.py 93cbdef 68bef16` | `producto +29/−24`, `avisos: 0`, historia vacía |
| `chequeo-6.py 195b96c ccfe640` | `producto +41/−27`, `avisos: 0`, historia vacía |
| `scripts/testing/catalogo_largo2_postgres.py` (PG 16) | `fallas: 0` (13 OK) |

Sabotajes y suite de esta entrega no se corrieron: la vuelta de la
devolución los trae de nuevo.
