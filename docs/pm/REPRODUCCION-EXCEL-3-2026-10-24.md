# Reproducción de EXCEL-3 — 2026-10-24

PM principal. Entrega de la Dev técnica: informe `8622aab` (rama
`claude/dev-tecnica`), producto `f3f9eb8` + `b76be2f`. Base: `1910632` (el
producto es igual a `main` = `dddcf6d`; sólo cambian documentos).

**Veredicto: aceptada.** Integrada a la rama de la PM por SHA (`a173af2`,
que es `8622aab` más la D2 en documentos); el producto integrado es idéntico
al revisado.

## Lo corrido

Worktree limpio en `8622aab`, `--no-cov`, entorno de prueba con servicios
falsos (`VUCE_MODE=fake`, `TARIFAR_MODE=fake`, `AFIP_MODE=fake`, dólar
apuntando a un puerto cerrado).

| Qué | Resultado |
|---|---|
| Focales `test_excel3`, `test_excel1_lectura`, `test_maria1b_controles` | 120 passed |
| `compileall proyecto_maria` | ok |
| Suite completa en `8622aab` | 1 failed, 1756 passed, 102 skipped, 2 xfailed, exit 1 (el rojo, abajo) |
| Sabotajes `scripts/testing/sabotajes/excel3.sh` | 27 ROJO, «sabotajes sin rojo: 0» |
| Datos del sintético (`.xls` y `proforma_china_sintetica.py`) | inventados: «DEMO TEXTILE», «COMPRADOR DEMO S.A.», CUIT 30-00000000-1, banco y cuenta de demo |
| Proforma real del 24/10, en local y fuera del repositorio | 200; 48 productos, unidad `m2`; la mercadería, el peso bruto, el descuento y el flete coinciden con las filas `Total`, `Discount` y `Freight` de la hoja, y mercadería − descuento + flete da el `Total` final de la proforma |

### El rojo de la suite: no es de EXCEL-3

`test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`:
«la subida normal dio 400 a los 30.0 s: No pudimos abrir el Excel: tardó
demasiado». Corrida sola, falla igual en `8622aab` (30.0 s) y en la base
`1910632` (30.1 s); el subagente la vio fallar también sola en la base
(50–53 s). Siempre, no a veces, en esta máquina (4 núcleos, carga ~1).

Causa: la validación abre los Excel con 2 hilos
(`EXCEL_VALIDATE_WORKERS`, `file_security.py:381-390`) y el tope de 30 s
(`PDF_VALIDATE_TIMEOUT_S`, `file_security.py:525-540`) cuenta también la
espera en la fila. Detrás de ocho libros de casi 10 MiB, la subida normal
espera cuatro tandas: si cada libro tarda más de ~7,5 s, se corta. Depende de
la velocidad de la máquina. La Dev lo había declarado como rojo de entorno;
su «exit 0» es de su entorno. Es de EXCEL-2, ya publicado: va como pieza
aparte y su prioridad la decide Emi.

## Subagente adversario (Sonnet alto)

Sin bloqueantes. Clasificación de la PM (vara: ¿mete un dato equivocado al
TXT con una entrada realista y sin señal en la revisión?):

| # | Hallazgo | ¿Regresión? | PM |
|---|---|---|---|
| 1 | «Descuento comercial», «Discount for early payment» con importe negativo entran como producto de valor 0 | no (igual en la base) | para después |
| 2 | Un subtotal de grupo sin rótulo, con largo, entra como producto de valor 0 y cantidad de más | sí (antes quedaba sin leer) | para después; se ve en la revisión (valor 0 y aviso de heredados) |
| 3 | Un grupo con código y sin especificación toma la descripción del grupo anterior | — | para después; con aviso de heredados |
| 4 | Después de un flete sin monto, el renglón de abajo hereda «Freight…» y queda sin leer | — | para después; avisado como fila sin leer |
| 5 | Un renglón sin descripción con «Freight included» en otra columna pasa a ser flete | sí (antes fila sin leer) | para después; avisado como flete leído |
| 6 | El flete leído ya no figura entre las filas sin leer | intencional | aceptado: va a la operación con aviso |
| 7 | «Qty (M)» con «USD/M» sale con unidad `m` (metros, `02` en el TXT) y sin aviso | sí (antes sin unidad) | para después: aviso cuando la unidad sale del encabezado del precio. En lonas, «M» es metro |
| 8 | El mapeo guardado del cliente con la cantidad en rollos queda reemplazado por los m² | — | **reproducido por la PM**: con el mapeo `QTY (Rolls) → cantidad`, sale 64 m² y avisa «La cantidad se tomó de «SM.TOTAL (sqm)»…». Correcto: con precio por m², rollos × precio no da el valor de la factura |
| 9 | «1,5m» en la columna de largo sale «largo 1,5m m»; `Discount`/`Total` sin monto entran como ítem de cantidad 0 (igual en la base); SM.TOTAL vacío deja cantidad y peso en 0 | — | cosmético / para después |

Lo que el subagente intentó y no se rompió: 300 planillas al azar
(errores de celda, texto, fechas, `1e999`, «(850)», vacíos) sin ningún 500;
productos con «Total», «Discount», «Freight» o «Subtotal» en la descripción
y con NCM, iguales a la base; dos columnas de cantidad en una factura común,
igual a la base; precio por kg con columnas de peso total, sin confundir;
descuento en porcentaje y flete negativo, sin leer.

## Consejero

Consultado antes del veredicto. Pidió reproducir el punto 8 (hecho, arriba),
clasificar el resto por la vara de la tabla, integrar por SHA y no escribir
en este archivo los montos de la proforma real.
