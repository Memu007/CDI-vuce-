# Reproducción de EXCEL-3e — 2026-10-25

Sobre `6f798d8` (informe `e1acb64`; base de comparación `1955cac`; piso de
la tarea `31c9b5a`). La PM corrió las pruebas, el sabotaje y once negativos
propios en worktrees limpios (`/tmp/rev-x3e`, `/tmp/rev-x3e-base`,
`/tmp/rev-x3e-piso`). Un revisor adversarial con contexto nuevo (Opus alto)
trabajó con árboles propios. Todo local, con sintéticos y sin Gemini.

**Veredicto:** EXCEL-3e, **aceptada**. Un cargo o un descuento con medidas
que no son números, bajo una descripción combinada, ya no entra como
producto sin aviso: se lee como en el piso o queda sin leer con su fila
nombrada. Ninguna regresión de plata sin aviso. Lo que queda abierto ya
estaba en la base y va a **EXCEL-3f** (H1, H3) o se anota.

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| Las cinco de Excel (`test_excel1_lectura`, `test_excel1_txt`, `test_excel2`, `test_excel3`, `test_maria5_peso_excel`) sobre `6f798d8` | `861 passed, 5 warnings in 75.91s`, rc=0 |
| `PY=… bash scripts/testing/sabotajes/excel3.sh 6f798d8` | 96 ROJO, «sabotajes sin rojo: 0», rc=0 (en dos partes, abajo) |
| Suite completa sobre `6f798d8` | ver «Suite» abajo |

El sabotaje corrió en dos partes. La primera llegó a 81 de 96, todos «ROJO
… dice «…»», y se cortó por el tope de tiempo de la tarea en segundo plano
de la PM, no por el script. La segunda corrió los 15 restantes (82 a 96)
sobre el mismo SHA con una copia del script que sólo agrega un contador
para saltear los primeros 81 (`SALTEAR=81`): 15 ROJO, «sabotajes sin rojo:
0», rc=0. En total, 96 con rojo por la razón esperada.

### Negativos propios

Distintos de los ejemplos de la devolución («Freight» con «/»): otro rótulo,
otras medidas. Cada caso en `.xlsx` y `.xls`, con el mismo resultado en los
dos. «FOB» es la suma de los productos que entran.

| Caso | `31c9b5a` (piso) | `1955cac` (base) | `6f798d8` | Lectura |
|---|---|---|---|---|
| D: «Flete internacional», medidas «--», especificación combinada | flete 500 de la fila 3, FOB 30 | producto, FOB 530 | flete 500 de la fila 3 con aviso, FOB 30 | arreglado, igual al piso |
| D3: «Insurance», medidas «x», combinada | no corrido | producto, FOB 70 | fila 3 sin leer, FOB 30 | arreglado |
| E: el caso de la D24 (sin combinar, código DT-1, «-») | hereda con aviso, FOB 38 | hereda con aviso, FOB 38 | fila 3 sin leer, FOB 30 | lo que dice la D24 |
| G: «Freight» en Item y «LONA DEMO» escrita a mano en la descripción (sin combinar), medidas «/» | producto, FOB 1230, sin aviso | igual | igual (sin « ancho / m…» en la descripción) | de antes; ver H1 |
| C, C2: subtotal sin rótulo con cantidad, bajo `C2:C4` | no corrido | FOB 75 / 150 | mismo FOB; el renglón ahora lleva el código DT-1 | sin cambio de plata |
| H: producto real con código nuevo DT-9 y «-», combinada | no corrido | entra, FOB 38 | entra, FOB 38, sin «-» en la descripción | bien |
| A, B, D2, I | no corrido | — | idénticos a la base | — |

La fila sin leer del caso E va a `operacion.filas_excel_sin_leer` (la misma
lista `descartes`), que la pantalla muestra en el semáforo, como en la D20.

## Lo que probó el revisor (Opus alto)

Comparó base `1955cac` y entrega con las mismas planillas en `.xlsx` y
`.xls`, en árboles propios (ya borrados). Lo de la tarea anda: «Freight»,
«Discount», «Insurance» y «Handling fee» con medidas «/», «-», 0 o vacías
bajo la combinada se leen como flete o descuento, o quedan afuera con su
fila nombrada (por ejemplo, FOB 1230 en la base, 30 en la entrega con el
flete de 1200 de la fila 3). Ninguna excepción.

- **Lo nuevo, siempre con aviso:**
  - el renglón con código y sin descripción no hereda (la D24; también con
    0/0, «/» o «XL»);
  - un cargo en el medio de una combinada `C2:C4` (fila 3 «Insurance»,
    «Payment 30% TT» o «Handling fee»; fila 4 sin medidas): la base dejaba
    entrar la fila 4 (FOB 45), la entrega deja sin leer la 3 y la 4 (FOB
    30). Causa: `del_grupo_copiado` (`main.py:5081`) le pasa a la fila 4 la
    decisión del cargo (`main.py:5131`). Con «-» o números en la fila 4 ya
    se perdía en la base;
  - «Discount tag labels» con «-» bajo la combinada: la base lo dejaba con
    precio 0 y «sin precio»; ahora queda sin leer.
- **Igual que en la base, sin aviso:** la descripción repetida a mano (H1
  de abajo); una medida con texto de contenedor («1x40HQ», «20'», «40'HC»:
  `_es_una_medida` cuenta cualquier texto con una cifra que no sea cero);
  el rótulo en una columna de notas a la derecha (por diseño desde
  EXCEL-3b); medidas con Unicode raro («⁻1», un espacio de ancho cero
  delante).
- **Sin plata:** «XL» y «Std» ya no salen en la descripción; con Item «A2»
  bajo la combinada, las filas pierden el código DT-1. El TXT de
  importación no usa `codigo_parte`; sí el Excel de salida y la
  exportación (`maria_generator_export.py:233`).
- `_es_una_medida` recorrida con todo Unicode (cada carácter solo y con «1»
  o «-» al lado): 0 excepciones. «−1» (U+2212), «－1», «(5)», «0,0», «０»
  dan False; «1.000», «1,5», «.5», «５» dan True.
- `test_excel3.py`, `test_excel1_lectura.py` y `test_excel2.py` en
  `6f798d8`: 843 passed.

## Hallazgos

| # | Qué | Gravedad | Qué se hace |
|---|---|---|---|
| H1 | **Cargo con la descripción repetida a mano.** «Freight» en Item, la descripción del producto escrita otra vez (no combinada) y medidas «/»: entra como producto, FOB 1230, sin aviso. Igual en el piso `31c9b5a` y en la base: no es una regresión. La tarea decía «combinada o copiada», y en el código «copiada» es lo que rellena una combinada (`celdas_rellenadas`): la Dev leyó lo único que el código distingue; **la tarea no lo pedía con claridad**. Es de la familia H4 (el rótulo de un cargo en Item con descripción propia). | plata, media | EXCEL-3f |
| H3 | **Texto de contenedor como medida.** «Freight» con «1x40HQ» o «20'» en una medida entra como producto sin aviso (+1200). Igual en la base; la Dev lo anotó como riesgo. | plata, media | EXCEL-3f |
| H4 | **Un cargo en el medio de una combinada** deja sin leer también la fila de abajo, aunque no tenga medidas. Con aviso, baja el FOB. | plata, con aviso | se anota; se mira en EXCEL-3f |
| H5 | El código de parte se pierde en filas bajo la combinada con Item «A2»; «XL» y «Std» salen de la descripción. No llega al TXT de importación. | sin plata | se anota |
| H6 | Rótulo de cargo en una columna de notas a la derecha y Unicode raro en las medidas: igual que en la base. | plata, baja | se anota |
| H2 | **CHANGELOG del merge.** Las entradas de VALOR-1c y SEPARADORES-1 quedaron dentro de la de CLIENTE-1b, sin línea en blanco. | cosmético | resuelto en el merge de la PM (choque con las entradas de MARIA, sumadas sin cambiar texto) |

## Suite

Desde base limpia sobre `6f798d8` (`rm -f test.db`, entorno de prueba con
los modos simulados), al mismo tiempo que el sabotaje y el revisor (4
núcleos compartidos):

```
FAILED tests/test_clientes_plan02.py::test_export_csv_returns_csv_with_ops - ...
FAILED tests/test_clientes_plan04.py::test_catalogo_productos_endpoints - Ass...
FAILED tests/test_guardar1.py::test_datos_largos_de_la_operacion_no_impiden_guardarla
FAILED tests/test_maria4_despachante.py::test_lo_elegido_se_guarda_con_la_operacion_y_vuelve_en_los_listados
FAILED tests/test_maria4_despachante.py::test_los_listados_recortan_lo_guardado
FAILED tests/test_op_code_and_fill_if_empty.py::test_fill_if_empty_populates_client_profile
FAILED tests/test_op_code_and_fill_if_empty.py::test_fill_if_empty_does_not_overwrite
FAILED tests/test_operations_manual.py::test_manual_operation_null_client_id
FAILED tests/test_prelaunch_block1.py::TestOperacionManual::test_crear_operacion_manual_ok
FAILED tests/test_prelaunch_block1.py::TestOperacionManual::test_crear_operacion_sin_client_id_400
FAILED tests/test_prelaunch_block1.py::TestOperacionManual::test_crear_operacion_null_client_id_400
FAILED tests/test_prelaunch_block1.py::TestOperacionManual::test_crear_operacion_sin_items_400
= 12 failed, 3009 passed, 102 skipped, 2 xfailed, 23 warnings in 301.97s (0:05:01) =
rc=1
```

Los mismos 12 que informó la Dev. Esta vez `test_ocho_libros…` pasó.

- **Los 11 de presupuesto:** corridos solos con base nueva, `11 passed, 3
  warnings in 0.52s`. Con la suite entera chocan con el tope de 15
  operaciones del plan. **Corrección (09:35 UTC):** el informe decía que la
  CI los deselecciona y lo copié sin mirar; no es así (`ci.yml` deselecciona
  otros 10). La CI de mi rama estuvo verde hasta `c5eab07` y dio estos
  mismos 12 rojos en `bcab8b5`, la primera con la rama técnica integrada:
  es una regresión de las pruebas que trae esa rama, no ruido conocido. Va
  a la puerta de CLIENTE-1c.
- **`test_guardar1::test_datos_largos…`:** corrido solo falla igual,
  `assert [('',)] == [('2020-01-15',)]`. Es la regresión del CLIENTE-1c a
  medio hacer (`d7aa875`…`8b65b6b`, ya en la base `1955cac`): una fecha
  «2020-01-15T00:00:00» de la operación ya no se copia a la ficha del
  cliente; queda vacía, no mal. La cierra CLIENTE-1c.

## Limpieza

Sin `uvicorn`, `pytest` ni `chromium` de la revisión andando al terminar
(`ps`). Worktrees `/tmp/rev-x3e`, `/tmp/rev-x3e-base`, `/tmp/rev-x3e-neg` y
`/tmp/rev-x3e-piso` borrados (`git worktree prune`); el sabotaje borra el
suyo. Los ayudantes de los negativos quedaron fuera del repositorio.

## Suite sobre el merge `5eb6ae4`

Desde base limpia (`rm -f test.db`, el mismo entorno), en `/tmp/rev-merge`:
los mismos 12 FAILED de arriba, ninguno más.

```
= 12 failed, 3114 passed, 102 skipped, 2 xfailed, 94 warnings in 329.95s (0:05:29) =
rc=1
```

Los 105 passed de más son las pruebas de la Dev MARIA que ya estaban en mi
rama. Las líneas `ERROR sqlalchemy.pool…` son registro del cierre de
conexiones, no pruebas en error. Worktree `/tmp/rev-merge` borrado.
