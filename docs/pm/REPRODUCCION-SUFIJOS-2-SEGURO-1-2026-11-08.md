# Reproducción SUFIJOS-2+SEGURO-1 sobre `ad2d0f8` (base `7c0ac55`), 2026-11-08

PM principal, worktree limpio en `ad2d0f8`, SQLite y sin red.

| Qué | Resultado | Informe |
|---|---|---|
| `chequeo-6.py 7c0ac55 ad2d0f8` | producto +86/−62, 1 AVISO (24 netas, explicado), historia vacío | igual |
| tests de sufijos2, sufijos1 y seguro1 | 224 passed | igual |
| `-k "maria or sufij or golden or seguro or txt"` | 1549 passed, 66 skipped | — |
| `sufijos2.sh` | 32 ROJO, «sabotajes sin rojo: 0» | igual |
| `seguro1.sh` | ROJO, «sabotajes sin rojo: 0» | igual |

## Negativos de la PM

- Frenan con «cambiaría»: `AJ(−5)`, `ZA(１０)`, `AJ(1⁄2)`, `AJ(1.500,50)`,
  `AJ(1#2)`, `AJ(1·5)`, `AJ(1٫5)`, `AJ(X1.500)`, `AJ(1 1/2 PULG)`.
- Pasan bien: `AJ(1,5)`; `AJ(1.5)` → `1,5`; `AJ(3.14159)` → `3,14159`;
  `AJ(ABC-1.5)` → `ABC 1,5`; `AJ(N°5)` → `N 5`; `AJ(ROJO/AZUL)`, `AJ(5x10)`,
  `AJ(1e3)`.

## Riesgos (no bloquean)

- `AJ(31/02/2026)` pasa como fecha (`31 02 2026`): no cambia ningún número.
- `AJ(٥)` frena, pero con el mensaje de «vacío» en vez del de «cambiaría».
- D123: un `tipo_destinacion` con un invisible adelante da 200 en avisos y 400
  en generar; viene de antes y la generación frena. Pieza aparte AVISOS-1.

Veredicto: aceptada sobre `ad2d0f8`, sin integrar.
