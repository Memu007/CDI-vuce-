# Reproducción de SUBITEMS-1 — 2026-10-07

**Veredicto: se sostiene** sobre `88564ec` (base `db2bc04`, arriba de la
reentrega de MARIA-5, que está devuelta). Se integra junto con esa
reentrega. Cuatro arreglos chicos van en ella: puntos 7 a 10 de
`PARA-DEV-2.md`. D27 de la Dev 2: (a).

## Lo que corrió la PM

| Qué | Salida |
|---|---|
| Rojo antes: `test_subitems1.py` y `test_punta_a_punta1.py` con el producto de `db2bc04` | `14 failed, 9 passed, 2 xfailed` |
| Suite | `1475 passed, 102 skipped, 2 xfailed, 25 warnings in 208.03s` (coincide con el informe) |

## Subagente de la PM (Sonnet medio)

**Se sostiene:**
- **Pedidos al azar:** 3000 contra el generador y 600 por `/generate_maria`.
  - Los `MSBTFOB` suman el `MARTFOB`, y las cantidades de los subítems, la
    del producto.
  - Donde los dos árboles generan, el TXT es idéntico byte a byte.
- **Los 400 nuevos:** son sólo los que la pieza rechaza a propósito: cantidad
  con más de dos decimales (230), valor en 0 (255) y cantidad en 0 o
  negativa (33).
- **Líneas inyectadas:** con `=`, saltos, `\x00`, `\x85` o U+2028 en el
  sufijo, 400.
- **XSS:** no hay.
- **Recarga:** los subítems sobreviven a recargar la página.
- **Agrupar:** se bloquea si hay subítems.
- **Regresiones:** `test_punta_a_punta1`, `test_maria_subitems` y
  `test_subitems1` dan `31 passed, 2 xfailed` (D23 y D25).

| # | Hallazgo | ¿Antes? | Cómo quedó |
|---|---|---|---|
| 1 | `subitems` = `5`, `True` o `3.5`: 500 (`controles_maria.py:106`) | Sí, ya pasaba | Punto 7 |
| 2 | En el borde de 0,01 la pantalla (float) y el servidor (decimal) discrepan: 5 de 120 | Nuevo | Punto 8 |
| 3 | La suma del panel redondea las cantidades a enteros («Suman 3 de 3») | Nuevo | Punto 9 |
| 4 | Deshacer una acción masiva cierra los paneles (los datos quedan) | Nuevo | Se deja |
| 5 | El error de sufijo de un subítem sale bajo el campo general | Nuevo | Punto 10 |
| 6 | La prueba de punta a punta no corre `ncm.js` (la cubre `pantalla_subitems1.js`) | — | Se deja |

## No corrido

- `sabotaje_subitems1.sh`.
- Varios productos con subítems en la pantalla a la vez.
- `/api/validate/smart` con subítems válidos.
- Gemini real y el Kit.

Contexto de la Dev 2 al entregar: ~55 %, por su informe.
