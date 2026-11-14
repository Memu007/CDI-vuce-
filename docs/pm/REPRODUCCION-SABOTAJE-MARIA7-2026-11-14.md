# Vencido `sabotaje_maria7.sh`: reproducción de la PM

Entrega `4477ae3` (informe `0260962`, canal `PARA-PM-2.md`). Base `f3a7d29`. Sólo
arnés: el ancla del caso 6 (`sufijo_sucio`) pasa al `return limpiar_sufijo(…)[0]` de
`sufijo_de_la_operacion()` (`maria_generator.py:1523`) y sale la línea `vencido` del
guion de `sabotajes-conocidos.txt`. El SHA final pasó por un adversario Sonnet medio.
Veredicto: **aceptado sobre `4477ae3`**. D250: **(a)**, decidida por la PM.

## Corrido por la PM (2026-11-14, entre 10:10 y 10:26 UTC)

Con SQLite, `ENVIRONMENT=test` y los modos falsos; `GEMINI_API_KEY` vacía en lo mío (el
guion exporta `test-key`, previo). Se superpuso con la tanda de fondo (`run6`). Al
terminar no quedó ningún worktree en `4477ae3`.

| Qué | Resultado |
|---|---|
| `chequeo-6.py f3a7d29 4477ae3e` | producto +0/−0, arnés +1/−1, historia vacía, `avisos: 0` |
| unión `4477ae3e..02609624` fuera de `docs/pm`, y en `docs/pm/herramientas` | vacía |
| copia del guion de `4477ae3e` | `123 passed` sin sabotaje; 25 `ROJO`, 0 `FALLA`, `rc=0`; caso 6: `1 failed, 122 passed` |
| guion de `f3a7d29` sobre `4477ae3e` | `PATRON NO ENCONTRADO (0 veces)` en el ancla vieja del 6, `rc=1`, 5 `ROJO` antes de cortar |
| copia con el caso 6 cambiando sólo el texto de `donde` (sigue limpiando, mío) | `FALLA sufijo_sucio: quedó verde`, `rc=1` |
| `anclas_perdidas` sobre `4477ae3e` | de una línea 1 (`guardar2.sh`), de varias 0, otra cantidad 0 |
| `vencido` en `sabotajes-conocidos.txt` | 1: `guardar2.sh` |

## D250, medida

Mutación de la Dev en `maria_generator.py:2235` de `4477ae3e` (el sufijo de la operación
sin limpiar en el aviso «los N sub-ítems llevan el mismo sufijo»):

| Pruebas | Sin mutación | Con mutación |
|---|---|---|
| los 27 archivos con `sbt_sufijo_valor` | `1126 passed, 2 xfailed` | `1126 passed, 2 xfailed` |
| `-k 'sufijo or maria'` sobre `tests/` | — | `1369 passed, 6 skipped, 4882 deselected` |

Que nadie lo atrapa no alcanza: miré si la mutación cambia algo que se ve, llamando a
`supuestos_declarados` con los tres primeros renglones de `_lonas()` sin sufijo propio.

| Entrada | Sin mutación | Con mutación |
|---|---|---|
| sufijo de la operación que se limpia (`AA(MARCA ñandú.)-AI(620G/BLUE)-`) | el aviso muestra el limpio | el aviso muestra el sucio |
| el mismo, y el renglón 1 con el limpio como sufijo propio | sale el aviso | **no sale** |
| sufijo de la operación que no se separa (`AA(MARCA`) | sólo el error de la operación | el error y **además** «llevan el mismo sufijo» |

Las tres cambian: no es una mutación equivalente. El TXT no cambia (el generador limpia
por su lado); es un aviso equivocado antes de generar.

## Decisiones

- Supuestos y riesgos 1 a 4 de la Dev: aceptados. Las tres anclas con un comentario
  adentro (casos 16, 24 y 25), el `25` a mano y el venv por defecto van a
  `COLA-LIMPIEZA.md` con la línea de la Dev.
- **D250 (a)**, decidida por la PM, después de `guardar2.sh` y D249: comportamiento y
  prueba en `PARA-DEV-2.md`.
- Próxima D: D251.

## No corrido

- Suite entera, con y sin la mutación de D250: sin cambio de producto; la medición ancha
  fue `-k 'sufijo or maria'`.
- `e2e_maria.sh` y las pantallas: la pieza es un guion de sabotaje.
- Subagentes adversariales de la PM: arnés sin dinero, sesión ni datos.
- Los otros 24 casos, uno por uno, más allá de la corrida entera del guion.
