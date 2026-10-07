# Reproducción de MARIA-1b — 2026-10-07

**Veredicto: devuelta** sobre `21a7a7e` (base `c0bae0e`; `7b119b6` es EXCEL-1,
ya aceptada) por cuatro puntos, más la D22. EXCEL-1 sigue esperando: entra
con MARIA-1b.

## Lo que corrió la PM

Worktree limpio en `21a7a7e`, venv armado sólo con el `requirements.txt` de
la Dev 1, Gemini falso, terceros simulados.

| Qué | Salida |
|---|---|
| Rojo antes: `test_maria1b_controles.py` con el producto de `c0bae0e` | `27 failed, 10 passed` |
| Focal (MARIA-1b, archivos reales, subítems, EXCEL-1) | `158 passed, 5 warnings in 20.28s` |
| Suite | `941 passed, 102 skipped, 23 warnings in 108.66s` |

Coincide con el informe (941).

## Subagente de la PM (Sonnet alto)

**Se sostiene:**
- **El CUIT:** 12 CUIT reales de organismos y empresas pasan, y 3 inválidos
  frenan. Es el mismo cálculo que `validateCuitAR` de la pantalla.
- **Incoterms:** los del generador y FAS, DAT, DAF, DES, DEQ y DDU pasan.
- **El TXT:** en 25 casos, el archivo real sale idéntico. Sólo cambia lo que
  la pieza declara (`=` → `-`, saltos → espacio, moneda, incoterm y CUIT
  normalizados).
- **Guardar sin inventar:** no rompe listar, exportar, métricas ni las
  operaciones viejas.
- **Inyección:** no hay vía por campos que no van al TXT.

| # | Hallazgo | Cómo quedó |
|---|---|---|
| 1 | **`NaN` e `inf` pasan los controles.** En cantidad, valor, peso, flete, seguro y gastos FOB da 200 y el TXT sale con `QARTUNTDCL=nan`, `MDDTFLE=inf`, `MCPL=nan`; sólo `-inf` frena (`nan < 0` y `nan <= 0` son falsos). `/api/validate/smart` con la cabecera da 500 con `NaN` en un ítem. Desde la pantalla y el Excel no llega (queda null o 0): sólo por la API. Ya pasaba en `c0bae0e` | **Devolución 1** |
| 2 | **Mirar las otras hojas traba la lectura de Excel unos 3 minutos.** El tope de 10 s corta la espera, no el hilo, y el grupo tiene 2 hilos. Libro armado: 6 MB comprimido, 90 MB descomprimido, 50 hojas con celdas de 32 000 espacios; el escaneo solo tarda 188 s. Dos subidas así y una normal de una fila después da 504 a los 60 s. Lo introdujo la pieza | **Devolución 2** |
| 3 | Si el escaneo vence o falla, el semáforo no dice nada: sólo queda un `logging.warning` | **Devolución 2** (que lo diga) |
| 4 | Dígitos Unicode (ancho completo, arábigos) pasan como CUIT válido y el TXT los escribe tal cual (`NDDTIMMIOE=３０９９…`) | **Devolución 3** |
| 5 | Sólo DOL está confirmada con un archivo real; `EUR` y las otras 7 «habituales» salen sin aviso. Es el riesgo que declaró la Dev | **Devolución 4**: toda moneda que no sea DOL avisa hasta que el despachante confirme los códigos |
| 6 | Leído: el lector de PDF de `c0bae0e` pone DOL y FOB si no vienen | Ya lo saca MARIA-1d (integrada en la rama de la PM) |
| 7 | Leído: quedan «XX» en `/api/operations/manual` (`main.py:3208`) y en la pantalla al generar (el servidor lo rechaza), y `currency="USD"` al guardar | Se deja: no llega al TXT (lo frena el control); a EXCEL-2 si molesta |
| 8 | 500 con un sufijo de subítem que no es texto (`123`); probablemente ya pasaba | Se deja: sólo por la API |
| 9 | Leído: `review.js` bloquea una moneda fuera de las 9 habituales, aunque el servidor sólo avisa. No lo cambió la pieza | Se deja |

## No corrido por la PM

- Los sabotajes de la Dev (`maria1b.sh` y los demás) y las pantallas
  (`pantalla_maria1b.js`).
- `.xls` con `xlrd`, Gemini real.

Contexto de la Dev 1 al entregar: ~44 % (441 mil tokens); Emi la compactó
después.
