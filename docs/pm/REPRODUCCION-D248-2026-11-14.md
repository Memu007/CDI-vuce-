# D248 (c): reproducción de la PM

Entrega `3fcc9c4` (informe `8f50af3`, canal `PARA-PM-2.md`). Base `ee3ccfd`. Sólo
arnés: `scripts/testing/sabotaje_maria8.sh` +17/−14. `caso` acepta varios textos
esperados y exige todos; el caso 20 (`pide_sufijo_operacion`) pasa a `sin_herencia`:
el renglón, el ítem entero y el sub-ítem sin sufijo propio dejan de heredar el de la
operación, con una prueba por lugar. Veredicto: **aceptada sobre `3fcc9c4`**.

## Corrido por la PM (2026-11-14, entre 07:45 y 07:57 UTC, worktrees descartables)

Con `GEMINI_API_KEY` vacía, SQLite, `ENVIRONMENT=test` y los modos falsos. La corrida
se superpuso con la tanda de fondo (`run6`).

| Qué | Resultado |
|---|---|
| `chequeo-6.py ee3ccfdc 3fcc9c46` | producto +0/−0, arnés +17/−14, historia vacía, `avisos: 0` |
| unión `3fcc9c46..8f50af39` fuera de `docs/pm` | vacía |
| `anclas_perdidas` sobre `3fcc9c46` | 103 guiones; de una línea 5, de varias 1 |
| copia del guion de `3fcc9c46` | `46 passed` sin sabotaje; 38 `ROJO`, 0 `FALLA`, `rc=0`; `sin_herencia`: `4 failed, 42 passed` |
| `test_maria9_bordes.py` sin cambio | `9 passed` |

El cambio de `caso`, con copias recortadas del guion (caso 0, el 20 y el cierre):

| Copia | Resultado |
|---|---|
| entera | `ROJO sin_herencia`, `rc=0` |
| sin el `reemplazar` del sub-ítem (el de la Dev) | `FALLA … sin «…test_un_grupo_a_mano_y_los_subitems_a_mano_no_se_mezclan»`, `rc=1` |
| los tres puestos, pero esperando una prueba que queda verde (mío) | `FALLA … sin «…test_con_todos_los_sufijos_propios_no_hace_falta_el_de_la_operacion»`, `rc=1` |

Cada lugar por separado, en `maria_generator.py` de `3fcc9c46`, contra
`test_maria8_subitems_por_posicion`, `test_maria9_sufijo_operacion`, `test_sufijos1` y
`test_sufijos2` (sin cambio, `244 passed`):

| Lugar | Sin herencia | Hereda otro valor (`or "AA(OTRO)-"`) |
|---|---|---|
| renglón (1701) | 5 failed; maria8: `sin_sufijo_propio…` y `el_pedido_de_la_pantalla…` | 5 failed; maria8: `sin_sufijo_propio…` y `sin_ningun_sufijo…` |
| ítem entero (1726) | 25 failed; sólo maria8: `1 failed` (`un_renglon_solo_sale_como_antes`) | 22 failed; sólo maria8: `46 passed` |
| sub-ítem (1799) | 5 failed; maria8: `un_grupo_a_mano…` | 4 failed, todas de maria9; maria8 verde |

Confirma el riesgo 2 de la Dev: en el ítem entero y el sub-ítem, maria8 prueba que se
hereda algo y no qué; el valor lo sostienen maria9 y sufijos2.

## Deslices de la PM

- La primera corrida usó el guion de mi rama y no la copia de `3fcc9c4` (apareció
  `pide_sufijo_operacion`). La corté (`rc=143`) y la descarté; la válida es la de la
  tabla. Es la regla «un guion de sabotaje se corre con la copia del SHA que se revisa».
- El chequeo de worktrees después de cortarla filtraba `/tmp/tmp.*`, que es justo donde
  ese guion arma el suyo. Sin filtro: no quedó ninguno en `3fcc9c4`.

## Decisiones

- Supuesto 1 (varios textos en `caso`): aceptado.
- Supuesto 2 (un caso, la cuenta queda en 38): aceptado; coincide con «un caso por
  causa». El riesgo 1 (que cada prueba responda sólo por su lugar está medido, no
  obligado) queda aceptado con la tabla de arriba.
- No hay D nueva: la próxima sigue siendo D250.

## Riesgos

1. El de arriba (riesgo 1 de la Dev): medido, aceptado.
2. Ítem entero y sub-ítem: maria8 no distingue qué se hereda (medido por la PM).
3. El ancla genérica de 1726 falla a la vista si cambia la línea.
4. `test_con_todos_los_sufijos_propios_no_hace_falta_el_de_la_operacion` sigue sin
   sabotaje (ya aceptado en SABOTAJE-MARIA8).
5. Es la tercera entrega seguida cuyo SHA final no pasó por subagente ni `/code-review`
   (el adversario y `/code-review` fueron sobre `22ac41c`). Riesgo y una línea a la
   Dev, no devolución.
6. El `38` del último `echo` del guion está escrito a mano: va a `COLA-LIMPIEZA.md`.

## No corrido

- e2e_maria.sh: la pieza no toca el recorrido MARIA, sólo un guion de sabotaje.
- Suite entera: sin cambio de producto.
- Subagentes adversariales de la PM: arnés sin dinero, sesión ni datos.
