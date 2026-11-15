# SABOTAJE-SUBITEMS1: reproducción de la PM

Entrega `bf6778e` (pruebas `4d58129`, informe `2a0b8e8`, canal `PARA-PM-2.md`).
Base `47b8481`. Veredicto: **aceptada sobre `bf6778e`**. D245 (a), decidida por la PM.
Sólo pruebas: `producto +0/−0`.

## Corrido por la PM (2026-11-14, 03:20–03:38 UTC por la hora de las salidas, worktree descartable)

- Leí el diff entero: `scripts/testing/sabotaje_subitems1.sh` (+19/−4),
  `tests/test_subitems1.py` (+8/−3) y la línea que sale de
  `sabotajes-conocidos.txt`. El caso 7 saca los dos controles de forma de
  `/generate_maria`; el caso 8 apunta a la prueba del semáforo, que ahora mira
  `success`; casos nuevos 10 (`sufijo_no_texto`) y 11 (`subitem_no_objeto`).
- `chequeo-6.py 47b84815 bf6778e5`: producto +0/−0, arnés +20/−7, historia vacía,
  avisos: 0. Igual al informe.
- Unión: `git diff --stat bf6778e5 2a0b8e80 -- . ':!docs/pm'` vacío. Lo de abajo
  sobre `bf6778e` vale para la unión.

| corrida | resultado |
|---|---|
| `sabotaje_subitems1.sh bf6778e` | `rc=0`, `VERDE sin sabotaje 43 passed, 2 xfailed`, 11 `ROJO`, «OK: los 11 sabotajes…» (2 min 19 s) |
| seis formas mías de sub-ítems en el semáforo (`"abc"`, `[None]`, `[{"cantidad":"x"}]`, `[[]]`, `{"a":1}`, `-1`) | `6 passed` |
| `raise RuntimeError` dentro del `try` del semáforo (`main.py`, `smart_validation`), los 11 archivos de `tests/` que llaman a `/api/validate/smart` | `26 failed, 556 passed, 2 xfailed` |
| los tres archivos de D245 con una afirmación de `success` en cada sitio, sin sabotaje | `166 passed, 2 xfailed` |
| lo mismo con el `raise` | `10 failed, 156 passed, 2 xfailed` (8 de `test_punta_a_punta1`, 1 de `test_generar_maria_txt`, 1 de `test_cobro_corte1`) |

- Las seis formas dicen que el semáforo aguanta otras entradas sin reventar; no son
  un negativo (no distinguen ningún defecto).
- Con el `raise`, los tres archivos que quedan sin rojo son exactamente
  `test_cobro_corte1`, `test_generar_maria_txt` y `test_punta_a_punta1`: lo que dice
  D245. Prueba por prueba: cruzando cada llamada a `/api/validate/smart` con los
  rojos, toda prueba que lo llama fuera de esos tres archivos da rojo. Dentro de ese `try` no hay `HTTPException`, así que todo error sale como
  200 con `success: false`.
- Un primer `raise` puesto fuera del `try` dio 500 en todo (`36 failed`): no es el
  caso de D245 y no cuenta.

## Lo que sale de la revisión

- **D245 (a), decidida por la PM:** MARIA hace que las tres pruebas miren `success`.
  `test_cobro_corte1.py` es de la Técnica y de cobro: sólo se suma la afirmación,
  sin cambiar lo que ya mira; la revisión fuerte es que en ese archivo sólo cambie
  esa afirmación y el rojo medido. Criterio: con el `raise` dentro del `try`,
  ninguna prueba que llama al semáforo queda verde en los 11 archivos; sin él, los
  tres archivos verdes enteros. Hoy el semáforo contesta `success: true` en los
  tres: es una pieza sólo de pruebas, sin hallazgo de producto.
  Entra tercera, después de D243 (b) y `sufijos1`.
- `COLA-LIMPIEZA.md`: la línea del control de forma repetido se reemplaza por la de
  la Dev (el segundo es código muerto) y se suma la nueva (el control de forma vive
  sólo en `/generate_maria`, así que el semáforo da OK con sub-ítems que generar
  rechaza con 400; sin TXT malo).
- Corrijo lo que dije antes en `NOW.md`: el semáforo tenía prueba, pero hasta
  `bf6778e` cuatro pruebas no se enteraban si reventaba (quedan tres, D245).

## No corrido por la PM

La suite entera, las pantallas, `e2e_maria.sh`, `anclas_perdidas.py`, un adversario
y `/security-review`: no hay cambio de producto y el guion corrido entero es la
puerta de la pieza. La Dev corrió la suite (`6145 passed, 110 skipped, 3 xfailed`),
`compileall` y `anclas_perdidas.py` (10 frente a 8, igual a la base); no las repetí.
La reproducción se superpuso con la tanda de sabotajes de fondo (`run6`, sobre
`7436c6e5`), que no dice nada de este SHA.
