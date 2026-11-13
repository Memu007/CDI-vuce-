# D238 (a): reproducción de la PM

Entrega `80cd954` (informe `3dc9908`, canal `PARA-PM-2.md`). Base `73f8db7`.
Veredicto: **aceptada sobre `80cd954`**. D242 (a), decidida por la PM.

## Corrido por la PM (2026-11-13, 23:38–23:47 UTC, worktrees descartables)

- `git diff 73f8db7 80cd954 --stat`: `finalize.js` (+7/−1), `CHANGELOG.md` (+5),
  `pantalla_sufijo_otra1.js`, `tests/test_avisos1_seguro.py`. Leí el diff entero:
  el oyente de `input` en `init()`, `pintarSufijo` esconde el aviso sin condición, y el
  rechazo del servidor vuelve a «Validación» antes de poner el aviso.
- `chequeo-6.py 73f8db7 80cd954`: igual al informe (producto +7/−1, arnés +10/−3,
  historia vacía, avisos: 0).
- Unión: `git diff --stat 80cd954 origin/claude/dev-maria -- . ':!docs/pm'` vacío.
  Lo de abajo sobre `80cd954` vale para la unión.

| corrida | resultado |
|---|---|
| `SOLO=sufijo_otra1`, `80cd954` | `rc=0`, `PANTALLA SUFIJO-OTRA OK` |
| lo mismo con `finalize.js` de `73f8db7` | `rc=1`, `FALLA: otra operación entra con el aviso de la anterior a la vista: «Ingresá el sufijo de valor SBT. Es obligatorio.»` |
| `SOLO="sufijo_borrador1 maria9"`, `80cd954` | `rc=0`, 2 verdes |
| 13 archivos de pytest que leen `finalize.js` (`test_avisos1_seguro`, `test_valor1`, `test_valor1c`, `test_maria7_rechazos_24_10`, `test_separadores1`, `1b`, `1c`, `1d`, `test_punta_a_punta1`, `test_estudio1b`, `test_maria1d_campos_vacios`, `test_excel1_txt`, `test_seguro2`), `80cd954` | `690 passed, 2 xfailed` |
| los mismos con `finalize.js` de `73f8db7` | `1 failed, 689 passed`: `test_cada_400_que_cambia_de_pantalla_deja_el_motivo_a_la_vista[sufijo]` |
| `e2e_maria.sh`, `80cd954` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |

## Negativos de la PM, cada uno un commit descartable sobre `80cd954`

| sabotaje | corrida | resultado |
|---|---|---|
| el rechazo pone el aviso y después vuelve (orden viejo) | `SOLO="sufijo_borrador1 maria9"` | `rc=1`, 2 rojas: `FALLA: el de la operación: no sale bajo el campo del sufijo de la operación` · `FALLA: generado y devuelto a la validación: … Timeout 15000ms exceeded.` |
| el oyente escucha `change` en vez de `input` | `SOLO=sufijo_otra1` | `rc=1`, `FALLA: con el sufijo ya escrito, el aviso sigue a la vista` |
| `pintarSufijo` esconde el aviso sólo si el campo entra vacío | `SOLO=sufijo_otra1` | **`rc=0`, verde: no distingue** |

El tercero es un hueco del caso, no del producto: `pintarSufijo` esconde sin
condición (`finalize.js:203`), así que una operación con su sufijo guardado entra sin
el aviso; eso lo afirmo por lectura, no por una corrida. El caso sólo prueba la
siguiente operación sin sufijo. Va como dato dentro de `sufijo_otra1` con la pieza de
`sabotaje_sufijos1.sh` (canal de MARIA).

D242 (a): no hay cambio de servidor, el servidor vuelve a rechazar en el próximo
«Generar» si el sufijo sigue mal, y es reversible.

`CHANGELOG.md`: título y dos líneas; dice lo que hace.

## No corrido por la PM

La suite completa, las 31 pantallas restantes, `anclas_perdidas.py`, `compileall`,
y los guiones de sabotaje de piezas anteriores que anclan en `finalize.js`. La tanda
de sabotajes que corre de fondo es sobre `7436c6e5` y no dice nada de este SHA. La
reproducción se superpuso con esa tanda (un guion de cobro empezado a las 23:33).
