# Reproducción de MARIA-1b — 2026-10-07

**Veredicto: aceptada sobre `beea9eb`** con la devolución (abajo). Primero, **devuelta** sobre `21a7a7e` (base `c0bae0e`; `7b119b6` es EXCEL-1,
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

## La devolución — aceptada sobre `beea9eb`

Base `a443cc2` (la pieza devuelta con la rama de la PM integrada). Venv armado
sólo con el `requirements.txt` de la rama.

| Qué | Salida |
|---|---|
| Rojo antes: `test_maria1b_devolucion.py` con el producto de `a443cc2` | `42 failed, 11 passed` (las 11 ya estaban cubiertas) |
| Focal (devolución, controles, archivos reales, subítems, EXCEL-1, MARIA-3 y 1d) | `393 passed, 5 warnings in 38.82s` |
| Suite | `1224 passed, 102 skipped, 1 xfailed, 23 warnings in 133.91s` (la Dev: 1214 con los 10 que deselecciona la CI) |

**Subagente de la PM (Sonnet medio): los cinco puntos se sostienen.**
- **NaN e infinito:** `nan`, `-nan`, `1e999`, `Infinity` e `inf`, como
  texto o como número, dan 400 en ítems, subítems, flete, seguro, gastos y
  desbordes al multiplicar. `/api/validate/smart` con la cabecera ya no da
  500.
- **CUIT:** con dígitos de ancho completo o arábigos, 400.
- **Monedas:** «dol», « DOL » y «DOL\n» se normalizan; las otras monedas
  avisan.
- **Exportación:** con 9 tipos de salto y control en cada campo, ninguno
  parte una línea.
- **Presupuesto de las otras hojas:** corta en ~3 s y el semáforo lo dice.
  Con dos libros armados delante, la subida normal da 200 en 3,6 s.
- **Merge:** los dos archivos reales siguen idénticos y no se perdió nada de
  la Dev 2 (guardar sin inventar, procedencia rara en `/avisos`).

| # | Hallazgo | Cómo quedó |
|---|---|---|
| 1 | Con libros armados **sin** `<dimension>`, lo lento es abrir el libro (validar y leer la primera hoja con openpyxl), que no se corta: con 8 delante, la normal da 400 a los 30 s. Es la D26 de la Dev | D26 (a), a EXCEL-2 |
| 2 | Un entero JSON gigante (`10**400`) o una lista en un monto da 500 (`OverflowError` no se atrapa). Ya pasaba | A EXCEL-2, como «de paso» |
| 3 | `/api/validate/smart` **sin** la cabecera da verde con `NaN`. La pantalla manda la cabecera y `/generate_maria` lo frena | Se deja |
| 4 | Un `.rels` con la hoja en `%32` (armado a mano) se toma por vacía y no avisa | Se deja |
| 5–7 | `1_0` y `１２` como número; 5000 ítems de 9e11 sin tope total; la pantalla manda «XX» como origen (el mensaje dice «no reconocido») | Se dejan; ya pasaban |

Al integrar entraron también las pruebas de PUNTA-A-PUNTA-1 en curso
(`9610f6d`, `a443cc2`): son sólo pruebas y se revisan cuando se entreguen.
