# Reproducción de ORDEN-1b vuelta 4 (2026-11-05, PM principal)

Sobre `f5e9fac` (rama `claude/dev-tecnica`, informe en `885ee89`). Base de la
vuelta: `f22f48b`. Sólo cambian pruebas (`scripts/testing/pantalla_orden1.js`,
`scripts/testing/sabotajes/orden1b.sh`).

## Lo que corrí

| Qué | Resultado |
|---|---|
| `PY=… PUERTO=8894 scripts/testing/sabotajes/orden1b.sh f5e9fac` | 28 `ROJO`, «sabotajes sin rojo: 0», salida 0. Las cuatro filas de z35 (`success`/`topup_success` × primero `tour`/`carga`) dan ROJO con su propio mensaje. |
| `PY=… PUERTO=8896 scripts/testing/sabotajes/orden1.sh f5e9fac` | 76 `ROJO`, «sabotajes sin rojo: 0», salida 0 (como el informe). |
| `chequeo-6.py f22f48b f5e9fac` | producto +3/−2 (es el arreglo de COBRO-MP-1 vuelta 5, que está en el medio de la historia), historia vacía, 1 AVISO: la anónima de `pantalla_orden1.js:281` crece 1 línea en su propio cuerpo; ya está en la cola por D50. |
| `git grep X-Prueba-Consulta f5e9fac -- proyecto_maria/` | vacío: el producto no lee el header del arnés. |

## Mi propio ataque: el tour atrasado en el producto

Distinto del de la Dev (ella atrasó 3 s en el arnés): en una copia de
`f5e9fac` agregué una espera antes del `fetch('/auth/current_user')` de
`checkDemoForceTour` (`screens/tour.js`), y corrí `CASOS=z35` con las cuatro
filas. Script y salidas en el scratchpad de la PM (`o1b4/diag/`).

| Sabotaje M3 | Espera del tour | Resultado |
|---|---|---|
| sí | 1500 ms | ROJO: «… (success, primero tour) … y el cliente quedó en la cuenta de B» |
| sí | 3000 ms | ROJO, mismo mensaje |
| no | 1500 ms | las cuatro filas OK |
| no | 3000 ms | `success` × 2 OK; `topup_success, primero tour` FALLA: «la relectura salió antes de que la pestaña cargara el usuario» |

El defecto de la vuelta 3 (el handler retenía la consulta del tour y el
sabotaje quedaba en verde) ya no se reproduce: con el tour tarde, M3 da rojo.

La última fila no es un verde falso. Con `primero tour` el arnés hace esperar
a la carga hasta que termine el tour. Con 3 s, la relectura de `topup_success`
(que el producto programa a los 2 s) sale antes de que la pestaña tenga usuario,
y el caso lo dice y falla en vez de medir otra cosa. Es lo que pedía la
devolución: falla con su propio mensaje en lugar de pasar. Queda como
observación (un tour de más de ~2 s no deja medir esa fila), no como devolución.

## Veredicto

Aceptada. La devolución de la vuelta 3 queda resuelta: z35 retiene sólo la
relectura, cubre el tour antes y después de la carga, falla si escribe sin
haberla leído y no tiene esperas fijas nuevas.
