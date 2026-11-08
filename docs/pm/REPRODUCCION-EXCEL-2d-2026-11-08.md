# Reproducción de EXCEL-2d (Dev técnica), 2026-11-08

Entrega `84fd9f2`, base `dca338a`, informe `4256a111` en `PARA-PM.md`.
Corrido por la PM principal en un worktree limpio de `84fd9f2`, venv
`/tmp/cdi-pm/venv` (Python 3.12), con `cobro_mp2.sh` de otra entrega
corriendo al mismo tiempo (4 núcleos).

## Resultado: aceptada, sin integrar

| Qué | Informe | PM |
|---|---|---|
| `chequeo-6.py dca338a 84fd9f2` | +97/−6, 2 AVISOS explicados | igual: +97/−6, 2 AVISOS (91 netas por topes nuevos; `try_extract_with_mapping` 309 → 312, partirla a la cola) |
| Excel y rendimiento (12 archivos) | 1455 | `1210 passed, 245 skipped` = 1455 |
| `excel2d.sh 84fd9f2` | 20 ROJO, falla 0 | sin `xlwt`: 13 ROJO, **falla 7**; con `xlwt` 1.3.0: **20 ROJO, falla 0** |
| `excel2.sh 84fd9f2` | 42 ROJO, falla 0 | 42 ROJO, falla 0 |

## Lo que dio distinto y su causa

- Los 245 `skipped` son todos `could not import 'xlwt'`: 11 de
  `tests/test_excel2d.py:80` y 234 de `tests/test_excel3.py:1150`.
- `xlwt` no está en `requirements.txt`, y la CI instala sólo
  `requirements.txt` (`.github/workflows/ci.yml:31` y `:79`). En la CI y en
  cualquier máquina sin `xlwt`, los casos `.xls` de EXCEL-2d (y los 234 de
  EXCEL-3) se saltean sin rojo. Por eso 6 de los sabotajes `.xls` dieron
  VERDE.
- El séptimo («las celdas rellenadas vuelven a copiarse en cada fila»)
  depende de un tiempo (2499 combinadas en 4998 filas). Dio VERDE una vez,
  con la máquina cargada y sin `xlwt`, y ROJO en la corrida con `xlwt`. No
  lo atribuyo a `xlwt`: queda como riesgo de un sabotaje que mide tiempo.
- Primera corrida: la hice con los guiones de mi rama (viejos), no con los
  de la entrega. Ese error es mío y no cuenta.

## Riesgos

- Casos `.xls` sin red en la CI: D124 (abajo).
- El sabotaje de tiempo puede quedar verde en una máquina muy cargada.

## D124, decidido por la PM

(a) La técnica, en un commit aparte dentro de su próxima entrega
(COBRO-MP-4): la CI instala `xlwt` para las pruebas (sin sumarlo a lo que
instala producción), y el informe muestra los casos `.xls` corriendo en la
CI, no salteados.
