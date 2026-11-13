# Reproducción de ORDEN1-INTERMITENTE (2026-11-13)

Entrega de la Técnica: arnés `8e775b2b`, informe `185f9e3b`, base `74e3cc74`.
Sólo arnés (producto +0/−0). Revisado por la PM principal en worktrees en el
SHA entregado y en la base, con el `correr_pantallas.sh` y el
`forzar_orden1.js` de la entrega. Veredicto: **devolución**, no se integra.

## Lo medido

| qué | salida |
|---|---|
| `chequeo-6.py 74e3cc74 8e775b2b` | producto +0/−0, arnés +55/−5, historia vacía, 1 AVISO (función anónima de `pantalla_orden1.js:284`, 1584 → 1585 líneas): igual que el informe |
| carrera forzada sobre `8e775b2b` | rc=0, `forzar_orden1: la consulta del hueco seguía retenida a los 10 s`, `OK A salió, volvió a entrar y generó enseguida: genera sin falsos bloqueos` |
| carrera forzada sobre la base `74e3cc74` | rc=1, `forzar_orden1: la consulta del hueco volvió antes de entrar: 401`, `FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')`: la misma `FALLA` de la premisa |
| `api.log` de esa corrida de la base | `POST /api/session/state` y `POST /auth/logout` 200; un único 401 en `GET /auth/current_user`; después `GET /?next=%2Fdashboard`: la pestaña fue al login |
| sabotaje de la PM: `ESPERA_SESION_MS` 10000 → 2000 en `app_v2.js`, `CASOS=z22`, servidor y base nuevos, `CSRF_ENFORCE=true`, dos veces por SHA | base: `rc=1 FALLA: A salió, volvió a entrar y generó enseguida y no generó: error: No se pudo comprobar la sesión. Recargá la página.` las dos; `8e775b2b`: `rc=0 OK=2` las dos |
| `orden1b.sh 8e775b2b` (sabotajes de la pantalla) | 29 `ROJO`, `sabotajes sin rojo: 0` |
| corredor entero sobre `8e775b2b` (terminó 04:51 UTC) | `resumen: 30 verdes, 0 rojas`, rc=0 |

## Lectura

La puerta forzada es determinista y se reproduce como dice el informe. Pero
el z22 nuevo suelta la consulta de usuario **antes** de apretar Generar, así
que ya no ejerce la escritura con un chequeo de sesión lento por debajo del
tope del producto. El sabotaje lo muestra: con el tope en 2 s y la respuesta
demorada 3 s, la base da el falso bloqueo y la entrega sale verde. La entrega
cambió un rojo intermitente por un defecto que deja de verse.

Hay que separar dos cosas. Un reloj que decide si la consulta vuelve antes o
después del login no vale: es la carrera. Una respuesta demorada a propósito,
por debajo del tope del producto, sí vale: es la entrada del caso.

## D213, leída en el código y en el `api.log`

La Técnica dice que el 401 tardío manda al login a una sesión válida. Lo que
forcé es otra cosa: el 401 llega con la sesión ya cerrada, y lo pide el
autoguardado del hueco por `api()` (`app_v2.js:24`) → `sesionEsDelDueno()`
(`:1030-1035`, `if (status === 401) irAlLogin();`) → `irAlLogin` (`:97`).
`revisarSesion` (`:1039`) hace lo contrario ante el mismo 401: se queda y
avisa «Se cerró la sesión…». Camino de hoy: salir en otra pestaña con una
operación cargada. No corrí si se pierde lo cargado. El «401 tardío con
sesión válida» no está reproducido. **(b) por ahora, decidido por la PM**; va
a `COLA-LIMPIEZA.md` como riesgo.

## No corrido

Adversarios (la tarea no los pide), pytest (sólo arnés), la familia z20a,
z21, z23 y z24 con la entrada forzada lenta (se pide en la devolución).

## Vuelta 2: arnés `6d1f1365`, informe `693a9bfa`

Veredicto: **aceptada e integrada**. Producto +0/−0.

| qué | salida |
|---|---|
| `chequeo-6.py 74e3cc74 6d1f1365` | producto +0/−0, arnés +94/−5, historia vacía, 0 AVISO: igual que el informe. La función anónima de `pantalla_orden1.js` queda en `:306`, 1584 líneas (la base tenía 1584) |
| carrera forzada sobre `6d1f1365`, cuatro veces | rc=0 las cuatro, `OK A salió, volvió a entrar y generó enseguida: genera sin falsos bloqueos`; el mensaje de `forzar_orden1` dio tres veces `seguía retenida a los 10 s` y una `se cortó sin respuesta antes de entrar` |
| carrera forzada sobre la base `74e3cc74` | rc=1, `volvió antes de entrar: 401`, `FALLA: page.evaluate: TypeError: Cannot read properties of null (reading 'click')` |
| familia forzada (`CASOS=z20,z21,z23,z24`) en base y en `6d1f1365` | `1 verdes, 0 rojas` las dos; seis `consultas de la pestaña mientras tanto: 0` en cada log: la familia no tiene la carrera, como dice el informe |
| `orden1b.sh 6d1f1365` | 30 `ROJO`, `sabotajes sin rojo: 0`; incluye `la comprobación de la sesión corta antes de lo que tarda`: es la puerta de la devolución (`ESPERA_SESION_MS` 2000 con `CASOS=z22` solo, `orden1b.sh:118-124`), y `ROJO` exige la `FALLA` exacta de z22 (`… y no generó: error: No se pudo comprobar la sesión`) |
| negativo de la PM: Generar sin comprobar la sesión, `CASOS=z22`, dos veces | `rc=1 FALLA: A salió, volvió a entrar y generó enseguida y Generar no comprobó la sesión` las dos |
| `CASOS=z22` sobre `693a9bfa` sin forzar, tres veces | `rc=0 OK=2` las tres |
| `ESPERA_SESION_MS` 2000 sobre `6d1f1365`, un caso por corrida (la Dev lo corrió sobre su commit provisorio) | z20, z21, z23 y z24 rojos, cada uno con `No se pudo comprobar la sesión. Recargá la página.` o `la pestaña no se tapa` |
| corredor entero sobre `6d1f1365` (terminó 05:35 UTC) | `resumen: 30 verdes, 0 rojas`, rc=0; `orden1` con 71 `OK`, entre ellos `OK A salió, volvió a entrar y generó enseguida: genera sin falsos bloqueos` |

**El mensaje de los dos relojes.** `forzar_orden1` retiene el login
`TOPE_MS` (10 s) desde que llega; el producto corta la consulta a los
`ESPERA_SESION_MS` (10 s) desde que la pide, un poco antes. Los dos relojes
casi empatan, así que el mensaje cambia entre corridas (3 a 1 en las mías);
el resultado no. El comando 1 del informe promete un texto fijo que no lo es:
va a la cola.

**El negativo distinto del ejemplo.** La devolución dio el tope en 2 s; el
negativo de la PM saca la comprobación de Generar, y el caso lo ve por el
encabezado que marca la consulta pedida desde `generateMaria`. Si esa función
se renombra, z22 da rojo (dicho en el informe).

No corrido: pytest y adversarios (sólo arnés), `/code-review` de la Dev.
