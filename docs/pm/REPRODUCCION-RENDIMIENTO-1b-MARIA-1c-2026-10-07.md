# Reproducción de RENDIMIENTO-1b y MARIA-1c — 2026-10-07

**RENDIMIENTO-1b (`b01149c`, base `8fd801d`): devuelta** con un punto (el
vendedor con dos columnas). **MARIA-1c (`448b54d`, base `c3bef51`):
aceptada.**

## Lo que corrió la PM

Worktrees limpios. RENDIMIENTO-1b con el venv armado sólo desde su
`requirements.txt`; MARIA-1c con el de siempre. Gemini falso, terceros
simulados.

| Qué | Salida |
|---|---|
| RENDIMIENTO-1b, rojo antes (`test_rendimiento1b.py` con el producto de `8fd801d`) | `16 failed` (tiempos en 0, negativos, `inf`, `nan`; contenido enorme; primeras páginas) |
| RENDIMIENTO-1b, focal (con RENDIMIENTO-1) | `30 passed, 4 warnings in 14.09s` |
| RENDIMIENTO-1b, suite | `746 passed, 102 skipped, 23 warnings in 89.75s` |
| MARIA-1c, rojo antes (`test_maria1c_avisos_lectura.py` con el producto de `c3bef51`) | `13 failed` |
| MARIA-1c, focal (con MARIA-1a y los archivos reales) | `142 passed, 5 warnings in 6.59s` |
| MARIA-1c, suite | `804 passed, 102 skipped, 24 warnings in 74.58s` |

Coinciden con los informes (746 y 804).

## Subagente de la PM (Sonnet medio)

**RENDIMIENTO-1b, lo central se sostiene:** ningún PDF armado colgó los hilos
(bomba de 1,5 GB, cadenas de filtros, `/Prev` en bucle, árbol de páginas
cíclico, XObject recursivo, 20 mil páginas, XRef roto: todos terminan en menos
de 4 s; uno de 10 MB con millones de objetos tarda ~10 s sin trabar a nadie).
El escenario de la revisión anterior da 200 en los 4 armados y en el bueno.

**MARIA-1c se sostiene:** ningún dato que estaba y no se leyó queda sin aviso;
el TXT con valores bien leídos no cambia; la pantalla vieja no inventa.

| # | Hallazgo | Cómo quedó |
|---|---|---|
| 1 | RENDIMIENTO-1b: con «SELLER:» y «BUYER:» en la misma fila y los nombres debajo (dos columnas), el vendedor pasa de `ACME TRADING LTD` a `BUYER`: `pypdf` junta las columnas en una línea. Si Gemini no trae vendedor, se carga un dato equivocado sin aviso | **Devolución:** el vendedor nunca es una etiqueta y el caso de dos columnas vuelve a dar el nombre (o vacío) |
| 2 | MARIA-1c: flete o seguro «N/A», «-», «FREE», «included», «Prepaid», y país «Unknown» o «?», se marcan como no leídos (aviso de más, del lado seguro) | A MARIA-3, que ordena los avisos |
| 3 | Leído: `test_factura.pdf` rinde 17 caracteres con `pypdf` y 20 con pdfminer (mismo vendedor: vacío) | Informativo |

## No corrido por la PM

- Los sabotajes de las Devs y la comprobación de pantalla de MARIA-1c
  (`pantalla_maria1c.js`; la captura de la Dev está en su rama).
- Gemini real y PyMuPDF real.

Contexto a las 06:10 UTC: Dev 1 ~55 % (553 mil tokens); Dev 2 ~58 % (576 mil); ninguna pudo compactar: Emi
pega los `/compact` a la mañana.
