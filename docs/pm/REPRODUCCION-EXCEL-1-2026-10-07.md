# Reproducción de EXCEL-1 — 2026-10-07

**Veredicto: devuelta** (sobre `9cc321e`; antes de la pieza, `ec3d793`), por
cinco puntos. El más grave: con el flujo normal de la pantalla, el FOB puede
salir multiplicado sin aviso.

## Lo que corrió la PM

Venv armado sólo desde el `requirements.txt` de la Dev 1.

| Qué | Salida |
|---|---|
| Rojo antes: `test_excel1_lectura.py`, `test_excel1_rendimiento.py` y `test_excel1_txt.py` con el producto de `ec3d793` | `46 failed, 2 passed, 8 errors` (las 8 son funciones de MARIA-1a que esa base no tiene) |
| Focal con los archivos reales | `116 passed, 5 warnings in 27.90s` |
| Suite completa | `897 passed, 102 skipped, 23 warnings in 108.40s` |

Coincide con el informe (897/102/0).

## Subagente de la PM (Sonnet alto)

**Se sostiene:** ninguna cuenta ve el mapeo, la plantilla ni los productos de
otra (404); `.xls` igual a `.xlsx`; números con coma, punto y símbolo bien,
ambiguos vacíos; la NCM sin el 0 inicial la frena la validación.

| # | Hallazgo (reproducido salvo que diga leído) | Cómo quedó |
|---|---|---|
| 1 | **El mapeo aprendido pisa una columna reconocida.** Con `cliente_id` (la pantalla lo manda siempre, `upload.js:278`), una primera subida enseña «Valor» como precio unitario; en la segunda, con «Precio Unitario» 350 y «Valor» 3500, sale `valor_unitario=3500` (sin cliente, 350). Igual con «Peso» contra «Peso Neto». La prueba de la Dev no manda `cliente_id` | Devolución |
| 2 | **Validar un Excel usa los hilos compartidos:** 12 subidas de un `.xlsx` de 8 MB (1 millón de filas) llevan `GET /api/ncm/<ncm>/completo` de 0,4 s a 49 y 62,7 s; `/health` sigue bien. Al vencer el tiempo, el hilo sigue | Devolución |
| 3 | Filas «Total Geral», «Gran total», «Subtotal …», «Ocean freight», «FOB value» entran como producto; sin NCM ni origen, `/generate_maria` las frena | Se deja: lo ataja el control antes de generar (MARIA-1b) |
| 4 | La plantilla de la pantalla trae una fila de ejemplo («Laptop 14 pulgadas modelo X», 10, 350) que, subida tal cual, entra como producto | Devolución |
| 5 | Un mapeo guardado con dos columnas para el mismo campo da 500 en cada subida de ese cliente | Devolución |
| 6 | CSV con `;`, latin-1 o BOM en `/api/ncm/import-historial` da 400 (ya pasaba antes) | A EXCEL-2 |
| 7 | Leído: la pantalla vieja (`static/app.js:939`) sigue llamando a `/upload_excel/public`, borrada (404); `scripts/testing/smoke_test.sh:269` espera 400 | Devolución |

## No corrido por la PM

Los sabotajes de la Dev, su comprobación de pantalla y Railway con varios
procesos.

Contexto de la Dev 1 al entregar: ~80 %.
