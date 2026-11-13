# Reproducción EXCEL-2c (Dev técnica), 2026-11-08

Sobre `c2b84f1` (informe `6c7e079`), base `a87b4f7`. Veredicto: **aceptada,
sin integrar**.

| Qué | Resultado |
|---|---|
| `chequeo-6.py a87b4f7 c2b84f1` | `producto +53/−29`, 1 AVISO (24 netas, con su porqué), historia vacío — igual al informe |
| `tests/test_excel2c.py` | `54 passed` |
| `test_excel*` + `test_maria5*` + `test_rendimiento*` | `1354 passed, 234 skipped` |
| `excel2c.sh c2b84f1` | 16 ROJO, `sabotajes con falla: 0` |
| Mío: libro normal de 500 y de 19000 filas | `(1, False)`: siguen en el carril liviano |
| Mío: 21000 filas | `(1, True)`: carril pesado |
| Mío: `<row r="1_000_000">` (Python lee `1_000_000` como número) | `(1, True)`: carril pesado, no se escapa |
| La falla de `excel2.sh` («ROTO … la función de 3e6e63e») | el patrón está en `522e082~1` y no en `522e082` ni en `a87b4f7`: viene de EXCEL-3b, no de esta pieza |

Diff de producto leído entero: `_medida_hoja` reemplaza a `_ultima_columna`;
`_contar_hojas_xlsx` devuelve `(hojas, caro)` y `validar_con_carril` hace
`liviano = liviano and not caro`. Los callers de las funciones que cambiaron
de tipo de retorno son sólo internos (`git grep`).

No corrí la suite completa (la Dev tampoco: corrió las de Excel y
rendimiento, `1429 passed`). Sin adversario propio: elige entre dos grupos
de hilos, no rechaza más de lo que rechazaba salvo contar celdas sin `r`;
la Dev pasó Opus alto, Sonnet alto de seguridad y `/code-review`.
