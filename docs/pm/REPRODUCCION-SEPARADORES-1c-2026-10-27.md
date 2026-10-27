# Reproducción de SEPARADORES-1c — 2026-10-27

Sobre `45a3ea1` (mismo código de 1c que `9663ac6`; informe en
`PARA-PM-2.md` de `claude/dev-maria`, `91be665`). Diff de revisión
`adfe707..9663ac6` sobre `pdf_extractor.py`, `maria_generator.py`,
`controles_maria.py` y `montos_ar.js`. Todo local, con sintéticos.

**Veredicto:** SEPARADORES-1c **sin hallazgos que frenen**; se acepta si la suite no trae rojos nuevos. Los tres puntos se cumplen con
ejemplos distintos de los del informe. D24 **(a)** y D25 **(b)**, decididas
por la PM: van juntas en SEPARADORES-1d.

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| `scripts/testing/sabotaje_separadores1c.sh 9663ac6 <venv>` | 10 de 10 en rojo por la razón esperada (rc=0) |
| Suite completa sobre `45a3ea1`, desde base limpia | corriendo al subir esto; el resultado va acá en la próxima vuelta |

## Negativos propios

### Punto 1, factura (`_monto_factura`)

| Texto | Pista decimal | Lee |
|---|---|---|
| `0.750,00` | `,` o ninguna | sin leer |
| `1234.567,00` | `,` | sin leer |
| `01 500,00` | `,` | sin leer |
| `250.000.0000` | `,` | sin leer |
| `1.23.456` | ninguna | sin leer |
| `USD 0.500.000` | ninguna | sin leer |
| `12.345.678,90` | `,` | 12345678.9 |
| `12,345,678.90` | `.` | 12345678.9 |
| `1 234 567,89` | `,` | 1234567.89 |
| `1'234'567.50` | `.` | 1234567.5 |
| `2.500.000` y `2,500,000` | ninguna | 2500000 |
| `1.500` | ninguna o `,` | 1500 |
| `1.500` | `.` | sin leer |
| `0,750` | `,` | 0.75 |
| `00750` | ninguna | 750 |

### Punto 2, blanco (`importe_valido`)

| Texto | Resultado |
|---|---|
| `\xa0`, `　`, `   ` | en blanco (0) |
| `​`, `﻿`, `​12`, `᠎` | 400 «no es un importe.» |
| `12\xa0` | 12.0 |

### Punto 3 y regla de la pantalla (`CDI.montos.leer`, node)

Cada forma que propone la pregunta se volvió a leer con `leer` y da lo que
la pregunta dice:

| Texto | Pregunta | Las dos formas, leídas |
|---|---|---|
| `-2500.125` | ¿-2500125 o -2500,1250? | -2500125 / -2500.125 |
| `4500.000` | ¿4500000 o 4500? | 4500000 / 4500 |
| `-1234.500` | ¿-1234500 o -1234,5? | -1234500 / -1234.5 |
| `-1,500` | ¿-1.500 o -1,5? | -1500 / -1.5 |
| `0012.500` | ¿12500 o 12,5? | 12500 / 12.5 |
| `01234,500` | ¿1234500 o 1234,5? | 1234500 / 1234.5 |
| `3500,250` | ¿3500250 o 3500,25? | 3500250 / 3500.25 |

Sin pregunta, como pide la tarea («siguen como hoy»): `0.500`, `0,500`,
`00.500` → 0.5; `01.500` → 1.5; `012.500` y `012,500` → 12.5; `1.500` →
1500; `1.234,567` → 1234.567. `123456789012345.500` y `+1234.500` → «Debe
ser un numero.».

## Observaciones

- `012.500` se lee 12,5 sin preguntar y `12.500` se lee 12500: el cero
  adelante cambia la lectura. Es lo que pide la regla (los miles no llevan
  cero adelante, «0500.000» con «.» es 500) y coincide con la factura. Se
  anota.
- D24 está reproducida tal como la cuenta la Dev: `_numero_factura` sigue
  leyendo por mil lo mal formado y eso entra al FOB.
- D25: la forma `2500,1250` se lee 2500,125 y el TXT lleva 2500.13 sin
  aviso.

## Limpieza

Sin `uvicorn` ni `chromium` de la revisión andando al terminar.
