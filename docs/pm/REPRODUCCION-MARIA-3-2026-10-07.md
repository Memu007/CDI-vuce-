# Reproducción de MARIA-3 — 2026-10-07

**Veredicto: devuelta** (sobre `088577f`, base `2461939`), por cinco puntos.

## Lo que corrió la PM

| Qué | Salida |
|---|---|
| Rojo antes: `test_maria3_antes_de_generar.py` con el producto de `2461939` | `54 failed, 11 passed` |
| Focal con los archivos reales, sub-ítems, MARIA-4 y gastos FOB | `183 passed, 5 warnings in 7.29s` |
| Suite completa | `911 passed, 102 skipped, 24 warnings in 80.97s` |

Coincide con el informe (911/102/0).

## Subagente de la PM (Sonnet alto)

**Se sostiene:** gastos anteriores al FOB con EXW, FCA y FAS (150 a
`GTOS-ANT-FOB`); con C o D, `GTOS-POS-FOB` y el campo ignorado con aviso; 672
combinaciones sin diferencias entre los avisos previos y la generación; fecha
vacía con aviso en 31/02, 29/02/2025 e ISO inválido; 2025 idéntico con
procedencia `222`, `PE` o `Peru`; 2026 con diferencias sólo en `LDVDREFDOC`
(MARIA-6) y una línea en blanco final.

| # | Hallazgo (reproducido) | Cómo quedó |
|---|---|---|
| 1 | La procedencia rechaza 129 de los 309 países que ofrece la pantalla (668 Hong Kong, 436 Turquía, 435 Chipre, 223 Puerto Rico, 242, 254, 358…): `pais_de_la_tabla` compara contra `PAISES_INDEC` | Devolución |
| 2 | Sin fecha válida, el año del `IEXT` sale de hoy o de texto suelto (`/26`, `/07`, `/99`, `/٢٥`), sin aviso | Devolución: sin fecha válida no se genera |
| 3 | `01/01/69` → 1969; fechas de 2099 o 1950 sin aviso; d/m contra m/d ambiguo no se detecta | Devolución (año de dos dígitos, futura o vieja); lo ambiguo, riesgo |
| 4 | Procedencia `²`: 400 con el texto de Python en `/generate_maria` y 500 en `/avisos`; una procedencia de ítem en blanco pisa la de la operación | Devolución |
| 5 | `gastos_anteriores_fob=1e308` escribe más de 300 cifras; `gastos_fob` explícito deja `nan`, `inf` y `-5.00` en el TXT | Devolución |

Confirmó la D12 de la Dev («None» en campos vacíos, `pdf_extractor.py`
~2299): va en MARIA-1d.

## No corrido por la PM

Los sabotajes de la Dev (`sabotaje_maria3.sh`), su comprobación de pantalla y
el Kit real.

Contexto de la Dev 2 al entregar: ~40 % (después de compactar).

## Devolución — aceptada sobre `0d6cb3e` (2026-10-07)

PM: rojo antes sobre `088577f` (`75 failed`), focal `243 passed`, suite
`1021 passed, 102 skipped` (igual al informe). Ojo: trae pruebas de MARIA-1d
en curso; MARIA-3 se integra junto con MARIA-1d.

Subagente Sonnet medio: los 309 códigos de la pantalla dan 200 como
procedencia; sin fecha válida, 400 con mensaje; `01/01/69` → 2069 con aviso
de futura; fechas de 2099 o 1950 con aviso; `²` → 400 propio; procedencia de
ítem en blanco no pisa la de la operación; `1e308`, `nan`, `inf`, `-5`,
`1e15` → 400; 2025 idéntico, 2026 sólo `LDVDREFDOC` (MARIA-6). Nuevo, menor:
procedencia `²` en un ítem da 200 sin aviso en `/avisos` y 400 al generar →
MARIA-1d.
