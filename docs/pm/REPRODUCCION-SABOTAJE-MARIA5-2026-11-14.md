# Vencido `sabotaje_maria5.sh`: reproducción de la PM

Entrega `c0505cc` (informe `9153d23`, canal `PARA-PM-2.md`). Base `38a7ed2`. Sólo
arnés: `scripts/testing/sabotaje_maria5.sh` +10/−3 y una línea menos en
`sabotajes-conocidos.txt`. Las anclas de los casos 26 y 33 se acortan, sin cambiar qué se
sabotea ni qué se espera; el caso 50 (nuevo) deja vacíos los supuestos de los avisos
previos. El último commit cambia sólo un comentario. Veredicto: **aceptado sobre
`c0505cc`**.

## Corrido por la PM (2026-11-14, entre 09:09 y 09:30 UTC)

El guion exporta `GEMINI_API_KEY=test-key` y pisa lo que se le pase; es previo. Las corridas
se superpusieron con dos tandas de fondo (`run6` y `despacho1b`). Al terminar no quedó
ningún worktree en `c0505cc`.

| Qué | Resultado |
|---|---|
| `chequeo-6.py 38a7ed2b c0505ccb` | producto +0/−0, arnés +10/−3, historia vacía, `avisos: 0` |
| unión `c0505ccb..9153d23c` fuera de `docs/pm`, y en `docs/pm/herramientas` | vacía |
| copia del guion de `c0505ccb` | `225 passed` sin sabotaje; 50 `ROJO`, 0 `FALLA`, `rc=0`; caso 26: `1 failed`, caso 33: `14 failed`, caso 50: `2 failed` |
| guion de `38a7ed2b` sobre `c0505ccb` | `PATRON NO ENCONTRADO (0 veces)` en el ancla vieja del 26, `rc=1`, 25 `ROJO` antes de cortar |
| copia con el caso 50 en la llamada de generar (8 espacios, mío) | `FALLA previos_sin_supuestos: rojo, pero sin «…test_los_avisos_antes_de_generar_tambien[»`, `rc=1` |
| `anclas_perdidas` sobre `c0505ccb` | de una línea 2 (maria7:97, guardar2), de varias 0, otra cantidad 2 (valor1b:102 y 114) |
| `vencido` en `sabotajes-conocidos.txt` | 4: valor1b, doc1.py, maria7, guardar2 |

El guion viejo corta en el 26, así que sólo prueba que esa ancla vieja ya no está. Que la
del 33 tampoco está lo dice `anclas_perdidas`: `sabotaje_maria5.sh` ya no aparece.

El negativo de los 8 espacios muestra que el caso 50 responde sólo por los avisos previos:
saboteando la llamada de generar, la prueba que espera queda verde.

Riesgo 1 de la Dev, medido (`c0505ccb` con el sabotaje del caso 50,
`GEMINI_API_KEY` vacía): `test_maria3_antes_de_generar.py` y
`test_maria5_caratula_vacia.py` pasan de `156 passed` a `7 failed`. Entre los 7 está
`test_los_avisos_previos_son_los_mismos_que_al_generar` en sus dos variantes, `[None-]` y
`[150-PE]`: lo que el caso 50 no mira, maria3 lo ve.

Riesgo 3 de la Dev: `maria_generator.py:1098` (ítems que juntan renglones) llama a
`peso_valido`. El comentario del 33 («el TXT no la usa») es impreciso. Va a la cola de
limpieza.

## Decisiones

- Supuesto 1 (caso 50): aceptado.
- Supuesto 2 (anclas cortas): aceptado. Si aparece una copia, fallan a la vista (riesgo 4).
- Riesgos 1 a 4: aceptados. El 1 queda medido arriba; el 3 va a `COLA-LIMPIEZA.md`.
- SHA final sin revisor ni `/code-review`: es la cuarta vez seguida. Desde ahora, en un
  vencido de sólo arnés, un último commit que cambia únicamente comentarios no necesita
  revisor si el informe lo dice; cualquier otro cambio sí. Decidido por la PM.
- Sin D nueva: la próxima sigue siendo D250.

## No corrido

- Suite entera y `e2e_maria.sh`: sin cambio de producto.
- Subagentes adversariales de la PM: arnés sin dinero, sesión ni datos.
- Los otros 47 casos, uno por uno, más allá de la corrida entera del guion.
