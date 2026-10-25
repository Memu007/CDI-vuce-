# Reproducción de EXCEL-3d (2026-10-25)

Entrega de la Dev técnica: `5468581` en `claude/dev-tecnica` (informe
`470fc48`, puertas sobre `7de44b7`, D20–D22). Veredicto en `PARA-DEV.md`:
**devolución, EXCEL-3e**.

Comparé con cuatro SHAs:
- `e08b4c4`: la base de mi veredicto de EXCEL-3c, antes de EXCEL-3c;
- `273c153`: EXCEL-3c;
- `31c9b5a`: la base de EXCEL-3d (EXCEL-3c más mi rama);
- `5468581`: EXCEL-3d.

Todo con planillas sintéticas, por la misma lectura que usa la pantalla
(`upload_excel_v2`). Encabezado de las planillas con medidas (`RENGLONES_PVC`):
`Item | Part No. | Specification | Width(m) | Length (m) | QTY (Rolls) |
SM.TOTAL (sqm) | Unit price (USD/sqm) | Total Amount(USD)`.

## Lo que la Dev corrió (informe)

- suite: 2469 passed, 102 skipped, 2 xfailed;
- `test_excel3.py`: 264 passed;
- `excel3.sh`: 79 sabotajes en rojo, 0 sin rojo;
- humo OK;
- `ataque_aislamiento.sh` (D17): G3 passed, 22 bloqueados, 0 fugas.

No corrió: un mapeo guardado de un cliente, la proforma real ni el e2e
completo.

## Lo que corrí yo

- `test_excel3.py` sobre `5468581`: **264 passed**.
- Sabotajes de EXCEL-3d: los 7 que se ven nuevos dan `ROJO`;
  «sabotajes sin rojo: 0».
- Suite completa: **no corrida** por mí.

## Los tres puntos que devolví: arreglados

| Caso | 3c (`273c153`) | 3d (`5468581`) |
|---|---|---|
| «Freight charges to BA», origen combinado | FOB +700, sin aviso | flete 700, aviso de fila dudosa |
| «Gastos de despacho», «Seguro internacional todo riesgo» | entran sin aviso | entran con aviso que nombra la fila 4 |
| «Insurance premium 0.3%», «Bank charges USD», «Handling fee», «Pago anticipado 30% saldo» | — | sin leer |
| Cabecera «Seguro todo riesgo» / «Gastos de origen» con hijo | fila 3 sin leer, hijo entra con 60 | filas 3 y 4 sin leer |
| «Freight surcharge», cabecera con hijo | — | cabecera leída como flete 120, hijo sin leer |
| D12: descripción combinada `B2:B4`, sin medidas, precio sólo arriba | avisos `[]` | «2 renglón(es) entraron sin precio (filas 3, 4)» |
| D12: lo mismo con `C2:C4`, o con el precio combinado `E2:E4` | avisos `[]` | mismo aviso |
| D12 con 7 filas | — | «filas 3, 4, 5, 6, 7 y 2 más» |

Productos reales sin combinadas: igual que antes. Con el origen combinado, el
aviso nombra las filas 3 y 4.

Siguen entrando sin aviso en las dos versiones, porque la primera palabra no
está en la lista: «Packing charges», «Inland freight», «Courier fee DHL»
(familia D21/H4).

## H1: regresión de plata sin aviso (lo que vuelve)

Fila 2 `1, DT-1, LONA DEMO, 2, 10, 1, 20, 1.5, 30`; fila 3 un cargo con
medidas que no son números. Especificación combinada `C2:C3`.

| Fila 3 | `e08b4c4` | `273c153` | `31c9b5a` | `5468581` |
|---|---|---|---|---|
| `Freight, -, -, "/", "/", -, 1, 1200, 1200` | FOB 30, flete 1200 | FOB 30, flete 1200, aviso fila 3 | igual | **FOB 1230**, producto «LONA DEMO, ancho / m x largo / m», avisos `[]` |
| lo mismo con medidas `-` | flete 1200 | flete 1200, aviso | igual | **FOB 1230**, sin aviso |
| lo mismo con medidas `0` | flete 1200 | flete 1200, aviso | igual | **FOB 1230**, sin aviso |
| `Discount, -, -, "/", "/", -, 1, -10, -10` | descuento 10 | descuento 10, aviso | igual | descuento perdido; producto fantasma y el aviso dice «sin precio (fila 3)» |

Causa, en `5468581`:
- `main.py:4973`: `con_medidas` mira si la celda tiene **texto**, no un
  número. «/», «-» y 0 cuentan como medidas.
- `main.py:4945`: con la especificación combinada, la fila tiene
  `descripcion_propia` vacía.
- Con las dos cosas, la fila no pasa por la lectura de flete o descuento
  (`main.py:4984`). Entra como hijo del grupo y hereda la decisión del
  producto de arriba (`main.py:5071`).

El adversario lo vio también en `.xls`, y con «Freight» que trae sólo el
importe (la base lo leía, 3d lo deja sin leer). Esos dos no los re-corrí yo.

## E1 (del adversario): no es un hallazgo

El adversario dijo que la docstring de `tests/test_excel3.py:1046-1047`
(«en la base, sin leer las dos») era falsa. Con su base, `31c9b5a`, quedaba
sin leer sólo la fila 3 y el FOB era 41.5.

Pero la base de mi veredicto de EXCEL-3c era `e08b4c4`, y ahí quedan las dos
sin leer:

| Sin combinadas, cabecera `H-1` + hijo sin descripción | `e08b4c4` | `273c153` | `31c9b5a` | `5468581` |
|---|---|---|---|---|
| «Insurance» | FOB 1.5, sin leer [3, 4] | FOB 41.5, sin leer [3] | igual que 3c | FOB 1.5, sin leer [3, 4] |
| «Handling trolley DEMO» (producto real) | FOB 1.5, sin leer [3, 4] | FOB 41.5, sin leer [3] | igual que 3c | FOB 1.5, sin leer [3, 4] |

Lo de que el hijo entre lo trajo EXCEL-3c, y EXCEL-3d vuelve a lo de antes,
que es lo que pedí en el punto 2.

Las filas sin leer se ven en la pantalla: el semáforo las muestra
(`operacion.filas_excel_sin_leer`, `static/v2/screens/semaforo.js:71`).
Sólo pido que la docstring diga a qué SHA llama «la base».

## Riesgos que ya estaban en la base (se anotan, no se arreglan ahora)

Mismo resultado en los cuatro SHAs:
- Una fila con «Freight» en la columna Item y «-» en las demás, sin
  combinadas: FOB 1230 y un producto «-» (familia H2).
- «Seguro de carga» con medidas «/» y la especificación combinada: FOB 930.

Del adversario, ya en la base:
- **H2**: un cargo en «Part No.» queda escondido cuando Item tiene texto.
  También cuando Part No. está a la derecha de la descripción.
- **H3**: un código o HS combinado con letras llega al seguro.
- **H4**: «Ocean freight», «Sea freight», «Air freight», «Courier DHL»,
  «Comisión bancaria», «Packing charges», «THC», «2. Insurance» y «Bank»
  entran sin aviso, con o sin combinadas.
- **H5**: el aviso de flete (`main.py:8115`) nombra 5 filas sin «y N más».
- **H6**: un hijo con origen propio bajo una cabecera «Insurance» entra,
  aunque la cabecera quede sin leer.

Nota sobre los avisos: una fila heredada muestra el rótulo de su cabecera.

Lo que el adversario encontró bien: la numeración de filas, que no haya texto
de Python en los avisos, los productos reales, los descuentos combinados, las
combinadas horizontales, NBSP y acentos.

## Integración

No integro todavía. ESTUDIO-1 (`609ec52`…`c992715`, toca `models.py`) es
ancestro de `5468581`: integrar EXCEL-3d metería ESTUDIO-1 sin revisar.
EXCEL-3e, CLIENTE-1b y ESTUDIO-1 entran juntas cuando ESTUDIO-1 quede aceptada.

## Cómo repetirlo

Los scripts quedan en el scratchpad de la PM: `p3d/sonda.py`,
`p3d/sonda3.py` y `p3d/sonda_h1.py`. Se corren con el entorno de prueba de
`docs/pm/herramientas/LEEME.md`, con `PYTHONPATH` en el árbol de cada SHA.
Para `e08b4c4` se usa la carpeta `tests/` de `5468581`, porque los ayudantes
`RENGLONES_PVC` y `SIN_ORIGEN` no existían todavía.
