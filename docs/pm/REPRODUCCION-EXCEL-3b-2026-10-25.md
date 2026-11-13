# Reproducción de EXCEL-3b — 2026-10-25

Sobre `7043cf2` (informe `e08b4c4`, base `53a441d`). Revisor adversarial
Sonnet, esfuerzo alto, con worktrees propios de la base y de la entrega.
La PM re-corrió P1 y SG1 sobre `7043cf2`. Todo local y con sintéticos.

**Veredicto: devolución (EXCEL-3c).** No se integra.

## Lo que se corrió

| Qué | Resultado |
|---|---|
| `tests/test_excel1*`, `test_excel2`, `test_excel3` | `245 passed in 73.41s` |
| `tests/test_excel3.py` solo | `59 passed` |
| `scripts/testing/sabotajes/excel3.sh 1a5053a` | 53 ROJO, `sabotajes sin rojo: 0` |
| ~60 sintéticos por `/upload_excel_v2/`, base contra entrega | abajo |
| fuzz de 200 proformas simples sin combinadas | 186 iguales; 14 distintas, todas R3 |
| `.xls` del repo (`proforma_china_sintetica.xls`, `combinada_con_codigo.xls`) | iguales a la base |

## Hallazgos

| # | Qué | Base | `7043cf2` | Gravedad |
|---|---|---|---|---|
| R1 | Origen combinado: producto real «Payment terminal POS» / «Handling cart» queda sin leer | 3 ítems, 430 | 1 ítem, 50, sin leer [3, 4] | media-baja (con aviso) |
| R2 | Cabecera de grupo sin código y con hijos que traen código propio deja de heredar | 3 ítems, 540 | 1 ítem, 86,4, sin leer [3, 4] | media-baja (con aviso) |
| R3 | Rótulo de flete o descuento a la derecha de la descripción ya no se lee (a propósito, punto 2) | descuento 10 | sin leer [3] | baja; queda |
| B1 | Descripción combinada hasta «Insurance» en la columna Item: el seguro entra como producto. El CHANGELOG de la pieza dice que eso ya no pasa | 3 ítems, 3590 | igual | media: infla sin aviso |
| D12 | Descripción combinada con el precio sólo arriba o combinado: los hijos entran con precio 0, sin aviso al subir | precio 0 | igual | el informe decía «sin leer con aviso» |

Lo que la PM vio sobre `7043cf2`:
- P1: `1 50.0 [3, 4]`, último ítem `['', 'Widget A', 10.0, 5.0, 'CN', '']`.
- SG1: `3 3590.0`, último ítem `['', 'LAPTOP DEMO', 1.0, 40.0, '', '']`.

Causa de R1 y B1: el filtro de lo que no es mercadería (`main.py:4912`)
decide con datos copiados de una combinada en vez de con las celdas propias
de la fila. Se suma `origen_propio` (`main.py:4787`). R2: `main.py:4856`.

## Recetas (openpyxl; `ws.append` por fila, `ws.merge_cells` al final)

- **P1:** cabecera `Item, Description, Origin, Qty, Unit Price, Amount`.
  Filas:
  - `[1,"Widget A","CN",10,5,50]`
  - `[2,"Payment terminal POS","CN",3,100,300]`
  - `[3,"Handling cart","CN",2,40,80]`

  Combinar `C2:C4`. **P2** es lo mismo sin combinar y da lo de la base.
- **SG1:** cabecera `Item, Description, Origin, Qty, Unit price, Amount`.
  Filas:
  - `[1,"LAPTOP DEMO","China",10,350,3500]`
  - `[None,None,"China",10,5,50]`
  - `["Insurance",None,None,1,40,40]`

  Combinar `B2:B4`. Variantes:
  - **SG2:** con origen `None` en la fila 2, combinar `B2:B4` y `C2:C4`.
  - **SG3:** la fila del seguro es `["Seguro",None,None,None,None,40]`.
  - **SG4:** la fila del seguro es `["Payment 30% TT",None,None,1,100,100]`.
- **G2:** cabecera `Item, Part No., Specification, Width(m), Length (m),
  QTY (Rolls), SM.TOTAL (sqm), Unit price (USD/sqm), Total Amount(USD)`.
  Filas:
  - `[1,None,"PVC BLUE",3.2,10,2,64,1.35,86.4]`
  - `[None,"DT-1A",None,3.2,15,3,144,1.35,194.4]`
  - `[None,"DT-1B",None,3.2,20,3,192,1.35,259.2]`

  **G3:** la cabecera trae `DT-1` y los hijos `DT-1-15` y `DT-1-20`.
- **D12:** grupo `DT-1 / PVC BLUE` con dos renglones sin precio ni importe
  y una fila «Total». Las cuatro combinaciones salen de combinar o no la
  especificación (`C2:C4`) y el precio (`I2:I4`).

## Lo que no se corrió

- La suite completa (el revisor no; la Dev sí: 1816 passed).
- Un `.xls` propio con combinadas hasta el flete o el seguro: no hay xlwt y
  no se instalan dependencias.
- Rendimiento o abuso del `.xls`.
- De punta a punta hasta `/generate_maria` con filas sin leer o con precio
  0: sólo se leyó `validate_items_for_maria` («Valor inválido»).
- La e2e y `/security-review`.
- La proforma real del 24/10: no está en el entorno del revisor.
