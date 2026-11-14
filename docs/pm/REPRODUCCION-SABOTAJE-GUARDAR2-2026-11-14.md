# Vencido `sabotajes/guardar2.sh`: reproducción de la PM

Entrega `aeb994f` (informe `279a685`, canal `PARA-PM-2.md`). Base `0260962`. Sólo arnés:
`scripts/testing/sabotajes/guardar2.sh` +1/−1 y una línea menos en
`sabotajes-conocidos.txt`. El ancla del sabotaje «gana la SIM de otro producto parecido del
proveedor» pasa de `catalog_svc._normalize(…)` a `catalog_svc.clave_de_producto(…)`, que es
lo que hoy está en `main.py:10177`; lo que se saca y lo que se espera no cambian. Veredicto:
**aceptado sobre `aeb994f`**.

## Corrido por la PM (2026-11-14, entre 10:37 y 10:43 UTC)

Las corridas se superpusieron con `run6` (cobro_mp2) de fondo. Al terminar no quedó ningún
worktree en `aeb994f`.

| Qué | Resultado |
|---|---|
| `chequeo-6.py 0260962 aeb994fb` | producto +0/−0, arnés +1/−1, historia vacía, `avisos: 0` |
| unión `aeb994fb..279a685e` fuera de `docs/pm` | vacía |
| copia del guion de `aeb994fb` | 11 `ROJO`, `sabotajes con falla: 0`, `rc=0`; el reescrito: `ROJO  \| … dice «FAILED tests/test_guardar2.py::test_la_sim_de_otro_producto_parecido_no_gana»` |
| guion de `0260962` sobre `aeb994fb` | `patrón no encontrado una sola vez (0)` en el ancla vieja, `ROTO`, `sabotajes con falla: 1`, `rc=1`; los otros 10 en `ROJO` |
| copia con el reemplazo cambiado por una línea equivalente (mío) | `VERDE \| … la prueba no lo vio`, `sabotajes con falla: 1`, `rc=1` |
| `anclas_perdidas.py aeb994fb` | 103 guiones, 2493 anclas, 11 sin medir; 0, 0 y 0 |
| `^vencido` en `sabotajes-conocidos.txt` | 0 |
| a mano, worktree de `aeb994fb`, `tests/test_guardar2.py` | sin cambio `22 passed`; con la condición sacada, `1 failed, 21 passed`, sólo `test_la_sim_de_otro_producto_parecido_no_gana` |

La base del guion es su propio chequeo silencioso (sólo imprime si ya está en rojo); el
`22 passed` es mi corrida a mano. El texto de la aserción (`'73181500900Z' == '73181500'`)
lo da la Dev y lo confirmó su adversario; yo no lo miré.

El negativo muestra que el guion marca `VERDE` y falla cuando el sabotaje no saca nada; que
el ancla sea la correcta lo sostienen las anclas en 0 y el `ROTO` del guion viejo.

## Riesgos de la Dev

1. `not del_proveedor.get("producto_key")` (`main.py:10176`, previo): ninguna prueba lo
   distingue (sacarlo deja `758 passed`). El `.get` va antes del `["producto_key"]` y evita
   un `KeyError`. A la cola como «pedir prueba o evidencia antes de sacarlo», no como «sobra».
2. El guion no fija cuántos sabotajes tiene. A la cola.

El otro sentido de la línea (volver a `_normalize`) lo ataca `catalogo3.sh`; según el
adversario de la Dev, da rojo en `test_catalogo3.py`. No lo corrí.

## Decisiones

- Riesgos 1 y 2: aceptados, a `COLA-LIMPIEZA.md`. Decidido por la PM.
- Sin revisor en el último SHA: no hizo falta, el SHA entregado pasó por el adversario.
- Sin D nueva: la próxima sigue siendo D251.

## No corrido

- El riesgo 1 medido por la PM: es de la Dev y su adversario.
- Suite entera y `e2e_maria.sh`: sin cambio de producto.
- Subagentes adversariales de la PM: arnés sin dinero, sesión ni datos.
- `catalogo3.sh`.
