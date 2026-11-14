# Vencido `sabotaje_valor1b.sh`: reproducción de la PM

Entrega `70eb5dc` (informe `a926930`, canal `PARA-PM-2.md`). Base `9153d23`. Sólo arnés:
`scripts/testing/sabotaje_valor1b.sh` +10/−6 y una línea menos en `sabotajes-conocidos.txt`.
El caso 8 ata su ancla a `op.campos_completados = …` de `calcularSeguro`, el caso 10 al
cierre de esa función, y el último `echo` pasa de 23 a 22. Un adversario revisó el SHA
final. Veredicto: **aceptado sobre `70eb5dc`**.

## Corrido por la PM (2026-11-14, entre 09:36 y 09:54 UTC)

Se superpuso con la reproducción de doc1 y con dos tandas de fondo (`run6` y `despacho1b`).
Al terminar no quedó ningún worktree en `70eb5dc` (`git worktree list`).

| Qué | Resultado |
|---|---|
| `chequeo-6.py 9153d23c 70eb5dcb` | producto +0/−0, arnés +10/−6, historia vacía, `avisos: 0` |
| unión `70eb5dcb..a926930a` fuera de `docs/pm`, y en `docs/pm/herramientas` | vacía |
| casos en el guion | 22 |
| copia del guion de `70eb5dcb` | 22 `ROJO`, 0 `FALLA`, `rc=0`; caso 8: `1 failed, 75 passed`; caso 10: `2 failed, 74 passed` |
| guion de `9153d23c` sobre `70eb5dcb` | `PATRON NO ENCONTRADO (2 veces)` en el ancla vieja del 8, `rc=1`, 8 `ROJO` antes de cortar |
| copia con el caso 8 sacando `cuentasViejas();` de `borrarSeguroCalculado` (mío) | `FALLA calculado_cuentas_viejas: quedó verde`, `rc=1`, 21 `ROJO` |
| `test_valor1.py` sin cambio | `76 passed` |
| `anclas_perdidas` sobre `70eb5dcb` | de una línea 2 (maria7, guardar2), de varias 0, otra cantidad 0 |
| `vencido` en `sabotajes-conocidos.txt` | 3: doc1.py, maria7, guardar2 |

El ancla vieja no faltaba: aparecía 2 veces. El guion viejo corta en el 8; que la del 10
también quedó en una sola vez lo dice `anclas_perdidas` («otra cantidad» pasa de 2 a 0).

Mi negativo muestra que el caso 8 responde por `calcularSeguro`: el mismo `cuentasViejas();`
sacado de la otra función deja verde la prueba que espera.

Casos 9 y 10 (riesgo 2 de la Dev): esperan la misma prueba,
`test_el_seguro_calculado_deja_de_avisarse_como_no_leido`, con mutaciones distintas (el 9 saca
`completados.add('seguro')` y da 1 failed; el 10 saca el refresco del semáforo y da 2). Son dos
causas con una sola prueba que las mira; queda como riesgo aceptado.

## Decisiones

- Supuesto (el `echo` de 23 a 22): aceptado. El guion tiene 22 casos y da 22 `ROJO`.
- Riesgos 1 a 3: aceptados. El 1 (no hay línea `VERDE` sin sabotaje) y el `22` escrito a mano
  van a `COLA-LIMPIEZA.md`.
- Sin D nueva: la próxima sigue siendo D250.

## No corrido

- Suite entera y `e2e_maria.sh`: sin cambio de producto.
- Subagentes adversariales de la PM: arnés sin dinero, sesión ni datos.
- Un negativo mío del caso 10; los otros 20 casos, más allá de la corrida entera del guion.
