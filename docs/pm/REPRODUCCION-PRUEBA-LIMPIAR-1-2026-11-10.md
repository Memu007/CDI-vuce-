# Reproducción PRUEBA-LIMPIAR-1 (2026-11-10, PM principal)

**Veredicto: aceptada sobre `5dd9a6eb`, con D164 (a).** Sólo pruebas
(`tests/test_sesion1.py`). Sin integrar: entra con la reentrega de
PRESUPUESTO-CLIENTE-1 sobre la unión.

## Mi criterio estaba mal

Pedí que «`limpiar` con su propia conexión» diera rojo en los datos nuevos.
No se podía cumplir: cuando `limpiar` corre, el pedido no tiene ninguna
conexión tomada, así que abrir otra no deja dos a la vez (sonda de MARIA,
`NullPool`, máximo 1). Es mi segunda corrección en esta pieza; la primera
está en `REPRODUCCION-INTEGRAR-1-2026-11-10.md`. El caso mide «no pide otra
conexión mientras tiene una», no «nunca usa otra».

## Lo que corrí

`tests/test_sesion1.py -k contar_intentos`, SQLite, worktree limpio.
Guion: `pl1/run.sh` del scratchpad de la PM (no está en el repo).

| Corrida | Sobre `c033db7` (base de la pieza) | Sobre la unión `0321c212` + la prueba de `5dd9a6eb` |
|---|---|---|
| sin sabotaje | 9 passed | 9 passed |
| sabotaje de la tarea: `limpiar` en `engine.begin()` propio | 9 passed | 9 passed |
| (a) de MARIA: `select` en la sesión del pedido y el `DELETE` en otra | 2 failed: «perfil con la clave buena» y «cambiar la clave con la clave buena», «2 conexiones a la vez» | igual |
| mío: `DELETE` en la del pedido, sin commit, y `SELECT` con `engine.connect()` | los mismos 2 failed | igual |
| el mío con la prueba vieja (`c033db7`) | 7 passed | no corrido |

Los dos datos nuevos son los que distinguen; los siete de antes siguen igual.
`chequeo-6 c033db7 5dd9a6eb`: producto +0/−0, arnés +11/−3, historia
vacío, avisos 0.

## Riesgo aceptado

Una versión de `limpiar` que use otra conexión sin tener tomada la del
pedido no se ve. No traba el pool y hoy no tiene camino. No va a la cola.
