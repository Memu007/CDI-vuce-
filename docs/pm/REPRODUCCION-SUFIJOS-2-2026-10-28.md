# Reproducción de SUFIJOS-2 (2026-10-28)

Entrega de MARIA en `bd76f9f`: pieza `4ca6829` (base `4905cd8`) más el
arreglo `91f0fb6` (producto), `15566a0`, `4821fff` y `bd76f9f` (pruebas y
sabotajes). Suite de la Dev sobre `4821fff`: 4005 passed, 0 failed. La PM
no corrió la suite: la devolución no depende de ella.

## Casos, corridos por la PM sobre `bd76f9f`

`limpiar_sufijo(<texto>, " X")` en una copia limpia, 23 casos. «ERR» es el
error que frena la generación; `True`/`False` es si hay aviso.

| Entrada | Sale | Qué muestra |
|---|---|---|
| `AR(31/12/2026)` | ERR | una fecha con barra ya no se genera |
| `AR(31.12.2026)` | ERR | ídem con punto |
| `AR(31-12-2026)` | `AR(31 12 2026)` | la misma fecha con guion pasa |
| `AJ(2.5-3.5)` | ERR | |
| `AJ(-5)` | ERR | el caso del informe, bien |
| `ZA(−5)` (menos Unicode) | `ZA( 5)` | cambia el valor sin frenar |
| `AJ(–5)` (raya) | `AJ( 5)` | ídem |
| `ZA(- 5)` | `ZA(  5)` | ídem |
| `AJ(－５)` (ancho completo) | `AJ( 5)` | ídem |
| `AJ(½)`, `ZA(½)` | `AJ(1 2)`, `ZA(1 2)` | ídem |
| `AJ(1⁄2)`, `AJ(1 / 2)` | `AJ(1 2)`, `AJ(1   2)` | ídem; `AJ(1/2)` sí da ERR |
| `AJ(1E-3)`, `AJ(1E+3)` | `AJ(1E 3)` los dos | dos valores distintos, el mismo texto |
| `AJ(10⁻³)` | `AJ(10 3)` | |
| `AJ(１.５００)` (ancho completo) | `AJ(1 500)` | `AJ(1.500)` sí da ERR |
| `AJ(1'500)` | `AJ(1 500)` | |
| `ZA(10%)` | `ZA(10 )` | un Z con algo que no es número, sin frenar |
| `AJ(1,500)` | `AJ(1,500)`, sin aviso | el sistema no lo cambia; ver riesgos |

## Mutantes, corridos por la PM sobre `bd76f9f`

`test_sufijos2.py` + `test_sufijos1.py`, un cambio por vez. Siete de catorce
sobreviven con «122 passed»:

- sin el dígito siguiente en el vecino de un dígito no ASCII
  (`maria_generator.py`);
- `len(decimales) == 3` → `>= 3` en `miles_o_decimales` (`sufijos_arca.py`);
- `entero.lstrip("0") != ""` → `entero != "0"`;
- `_SIGNO_DE_UN_NUMERO` sin `+`, y sin `,`;
- Z sin `upper()` (un `za(...)` en minúscula deja de pedir número);
- `_UN_NUMERO` sin `-`.

Los otros siete dan rojo.

## Del adversario (Sonnet alto, contexto nuevo), no corrido por la PM

- Los sufijos de identificación (`AK`, `AI`, `AW`) pasan `15.3` a `15,3`.
- `AJ(1/2 KG)` también da ERR (misma familia que la fecha).

## Causa

La detección de «cambiaría de valor» mira el texto crudo, con una lista de
signos ASCII (`-`, `+`, `.`, `,`, `/`). La limpieza que va al TXT
(`caracteres_del_maria`, `sufijos_arca.py:193`) hace otra cosa: NFKD y
cualquier carácter que no es letra ni número pasa a espacio. Todo lo que la
limpieza cambia y la lista no nombra (menos Unicode, raya, fracciones,
exponentes, ancho completo, apóstrofo, `%`, espacios alrededor del signo)
sale cambiado sin frenar. Y al revés: la barra entre dígitos frena aunque
sea una fecha, que antes pasaba.

## Veredicto

Devolución sobre `bd76f9f`. Lo que se pide, en `PARA-DEV-2.md`.
