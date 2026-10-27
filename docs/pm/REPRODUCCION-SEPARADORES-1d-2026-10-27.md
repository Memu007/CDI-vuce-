# Reproducción de SEPARADORES-1d — 2026-10-27

Sobre `140c122` (informe en `PARA-PM-2.md` de `claude/dev-maria`; producto
`1adee11`, pruebas y sabotajes `36f54a3`, SHA probado `1240c08` = su merge de
mi `7145201`). Diff de revisión `91be665..140c122` sobre `pdf_extractor.py`,
`finalize.js` y `CHANGELOG.md`. Todo local, con sintéticos.

**Veredicto:** SEPARADORES-1d **aceptada**. D24 y D25 se cumplen con ejemplos
distintos de los del informe; lo bien formado se lee igual que en la base.
Integrada por avance rápido: mi rama queda en `140c122`, el mismo árbol de la
suite de abajo. Fuera de `docs/pm`, contra mi `7145201` sólo cambian
`pdf_extractor.py`, `finalize.js`, `CHANGELOG.md`, sus pruebas y el script de
sabotajes.

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| Suite completa sobre `140c122`, desde base limpia | `3478 passed, 102 skipped, 2 xfailed, 94 warnings in 394.51s`, rc=0, ningún FAILED (el de tiempo de `test_excel2` no apareció acá) |
| Pruebas de 1d, 1c, 1b, 1 y VALOR-1 | `452 passed, 3 warnings in 73.86s` |
| `scripts/testing/sabotaje_separadores1d.sh 36f54a3 <venv>` | 5 de 5 en rojo, «OK: los 5 sabotajes dan rojo por la razón esperada» |
| `scripts/testing/sabotaje_separadores1c.sh 36f54a3 <venv>` | 10 de 10 en rojo, OK, salida 0 (las guardas de 1c siguen vivas) |

## Negativos propios

### D24: `_numero_factura` contra la base `91be665`, 19 textos

Mismo script contra los dos árboles. La única diferencia:

| Texto | Pista | Base | 1d |
|---|---|---|---|
| `01.234` | `,` | 1234.0 | sin leer |

Iguales en las dos (lo bien formado no cambia): `0.500` → 0.5, `0.1234`,
`12.5000`, `1.234,5678`, `1'234.50`, `1 234 567,89`, `1,234,567.89`,
`1.000` (con `,` → 1000; con `.` → 1), `1,5`, `3.335`, `USD 1.234,56`,
`1.234.567` con `,` → 1234567. Sin leer en las dos: `1.234.56`, `12.34.567`,
`1,23,456`, `1.2345.678`.

### D25: el aviso contra el redondeo del TXT

- Comparación al azar de `alCentavoDelTxt` de `finalize.js` (Node) contra el
  redondeo del generador: `comparados 20012 distintos 0`. El texto del aviso
  dice lo mismo que lleva el TXT.
- El aviso no queda viejo: flete y seguro se editan en `review.js` y
  `finalize.js` vuelve a calcular los avisos al entrar.

## Se anota

- Con pista `,`, un `1234.567` queda sin leer (antes, ×1000). Es el lado
  seguro: la revisión lo marca y se completa a mano. También alcanza a las
  celdas de texto de la planilla.
- El aviso de D25 cubre flete y seguro; gastos y ajustes no. Se anota, no es
  tarea: no hay campo de ajustes en el TXT (PRORRATEO-1 espera al
  despachante).
