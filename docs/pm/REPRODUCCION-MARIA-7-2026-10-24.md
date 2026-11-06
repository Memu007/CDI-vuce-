# Reproducción de MARIA-7 — 2026-10-24

PM principal. Entrega de la Dev MARIA: informe `284b029` (rama
`claude/dev-maria`), probado en `f0b73f7`. Base: `3fd8826`. Diff propio:
`git diff 3fd8826 f0b73f7`.

**Veredicto: con devolución.** No se integra todavía. Lo pedido en los nueve
puntos está y sus pruebas distinguen (11 sabotajes del adversario en rojo),
pero quedan dos defectos reproducidos y la D2 se cierra con evidencia del
archivo aceptado.

## Lo corrido

Worktrees descartables en `f0b73f7` y `3fd8826`, sondas en local (fuera del
repositorio), sin Gemini ni servicios reales.

| Qué | Resultado |
|---|---|
| Revisión adversarial (Opus, alto, contexto nuevo) | 9 hallazgos; 11 sabotajes propios, todos en rojo en las pruebas de MARIA-7 |
| Sabotaje h (`ROUND_HALF_EVEN`) | **no corrido**: el patrón aparecía dos veces. Lo pide la devolución |
| Suite completa, e2e | **no corridas por la PM** en esta vuelta: la devolución cambia el producto |

## Reproducido por la PM

**1. Dos sufijos sin guion entre ellos se funden.** `limpiar_sufijo` toma el
valor con `\((.*?)\)(?=-|$)`: el valor termina recién en un `)` seguido de
guion o del final.

| Entrada `CSBTSVL` | `3fd8826` | `f0b73f7` |
|---|---|---|
| `AA(ROJO) AB(AZUL)-CA00-` | igual a la entrada | `AA(ROJO  AB AZUL)-CA00-` |
| `AA(ROJO)AB(AZUL)-CA00-` | igual a la entrada | `AA(ROJO AB AZUL)-CA00-` |

AB desaparece y AA queda con un valor falso; el aviso sale, pero el TXT se
genera. Ninguna prueba de la pieza lo cubre.

**2. El identificador corto choca con numeraciones comunes** (es la D1, ya
declarada por la Dev). Últimos 8 alfanuméricos:

| Factura A | Factura B | IDSO de las dos |
|---|---|---|
| `FAC_ABC-2026-0001` | `FAC_XYZ-2026-0001` | `20260001` |
| `FAC_PI20260001` | `FAC_CI20260001` | `20260001` |
| `FAC_INV2026-00123` | `FAC_SO2026-00123` | `02600123` |

**3. D2, con el archivo que el MARIA aceptó** (en local, no en el
repositorio). La versión rechazada justo antes de la aceptada tenía el kilo
neto con un milésimo distinto de cero y la cantidad estadística en kilos al
centésimo (no coincidían). La aceptada tiene el kilo neto **al centésimo,
escrito con tres decimales** (el tercero en 0) e igual a la cantidad
estadística. Eso decide la D2: (b).

**4. Palabras de cuenta dentro de otras palabras.** `_PALABRAS_DE_CUENTA`
busca `BIC\b`, `IBAN`, `BANK`… sin borde adelante: `ARABIC TRADING 123` y
`VAT ARABIC-1234567` se toman por cuenta y la identificación tributaria no
sale.

**5. La unidad del PDF.** El lector de PDF nunca trae `unidad`: un PDF sale
07 salvo que el usuario elija la unidad en el panel del despachante (y sale
el aviso de «Unidad de medida» que ya existía). El Excel sí la trae
(EXCEL-3). Queda como está (abajo).

## Del adversario, sin reproducir por la PM

- Kilos con sub-ítems: el mensaje sugiere una salida que el control después
  rechaza. Pasa a MARIA-8 (sub-ítems).
- El control de grupo compara `unidad_estadistica` cruda (`1`, `01`, `kg`):
  error falso entre valores iguales. Va en la devolución.
- `fecha_inicio_actividad` acepta 1800 y 2999. Riesgo anotado; no se pide.
- `saveOperationToHistory` no guarda la unidad elegida; sin pérdida efectiva
  encontrada. No se pide.
- D3 confirmada: «Ñ» y comillas pasan sin limpiar en textos libres. Sigue
  (a): el archivo aceptado trae «S.A.», comas y paréntesis.
