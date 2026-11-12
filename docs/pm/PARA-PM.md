# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1 I: causa del rc=2 y caso natural (sólo arnés)

**El rc=2 era del arnés, no del producto.** Después de cada pedido, la app
registra el pedido en una tarea de fondo (`log_request_background`, lanzada
con `asyncio.create_task` en `MetricsMiddleware`, `main.py:1977-2015`). Esa
tarea sigue después de que llega la respuesta. Si abre su sesión antes del
`engine.dispose()` del arnés y la devuelve después, la conexión vuelve al
pool viejo, el descartado. Ese pool ya no se cierra con otro dispose: en
Postgres queda una conexión `idle` cuya última consulta es `COMMIT;`, y el
arnés anterior esperaba 15 s, la veía y salía 2. La cierra `gc.collect()`.

**Arreglo:** `soltar()` en `conexiones1_rondas.py`, que usan los casos 6, 7 y
8. Hace dispose + `gc.collect()` dentro del loop de la app y repite hasta
que Postgres no ve conexiones de la app, sin espera fija. Si gc tuvo que
cerrar una conexión que la app nunca devolvió al pool (una fuga real),
`soltar()` falla en vez de taparla.

**Caso natural** (`conexiones1_natural.py`, 78 líneas), sin tomar la fila
desde afuera. En HEAD, con créditos vencidos: deadlock en 8/10 rondas de
recarga + guardado y en 9/10 de recarga + MARIA. Con créditos al día, 0/10
en los dos pares. Una vez perdió el aviso de MP: la recarga no quedó
acreditada, y el reintento firmado la acreditó. Ninguna recarga quedó
perdida. Con `parche_nokey.diff`: 0 deadlocks en las 40 rondas y todas las
recargas quedaron enteras.

| SHA | Qué |
|---|---|
| `4268eb2c` | `test:` primera versión de `soltar`, casos 9 y 8 |
| `315c77f9` | merge de tu rama |
| `e9323b67` | `test:` `soltar()` detecta fugas, el caso 9 exige el pool descartado, el natural verifica la recarga |
| este commit | `docs:` este informe |

Producto +0/−0. Emi no dijo que sí a D182 ni a D206 (a): sigo en I.

## Decisiones

**Nada nuevo para decidir.** D205 y D206 siguen con Emi.

- **D207 (opcional, sólo para anotar).** `asyncio.create_task(...)` en
  `main.py:2008` no guarda la referencia de la tarea. Python puede
  recolectar una tarea sin referencia antes de que termine, y entonces se
  pierde el registro del pedido en `api_logs`. Al usuario no le pasa nada.
  - (a) Anotarla en la cola de limpieza: un `set` de tareas vivas.
  - (b) **Recomendada.** No hacer nada ahora. No la vi pasar en ninguna
    corrida, y lo que acá molestaba (la conexión tardía) no lo arregla.

## Causa, con evidencia

Medí con un script de diagnóstico que no se commitea: pedidos, dispose y,
si quedaba una conexión, qué mostraba Postgres y qué hacía gc.

| corrida | vueltas | quedó una conexión | en Postgres | después de `gc.collect()` |
|---|---|---|---|---|
| 1 | 30 | 1 vez (vuelta 10) | `idle`, `COMMIT;` | libre |
| 2 | 30 | 6 veces (vueltas 2, 10, 11, 13, 17, 20) | `idle`, `COMMIT;` las 6 | libre las 6 |

En las dos corridas, sin generadores suspendidos. Lo que quedaba eran dos
pools: el actual vacío y el descartado con 1 conexión. Quién la devuelve lo
muestra el caso 9: parchea `Pool._return_conn` y anota qué tarea devuelve
una conexión a un pool que no es el actual. En las tres corridas fue
`MetricsMiddleware.dispatch.<locals>.log_request_background`.

**Descartado:**
- La sesión de la dependencia del pedido: su cierre corre antes de que salga
  la respuesta.
- Un freno en el commit para forzarlo: 8/8 corridas dieron rc=4, porque el
  freno corría antes del dispose y el caso no se armaba.
- Antes (H): el caso 6 con NO KEY dio rc=2 en 1 de 6 corridas; 40 rondas
  aisladas dieron 0; vos corriste 50 y dieron 0. Por eso el caso 9 no espera
  al azar: repite pedido + dispose hasta que el dispose solo deja la
  conexión abierta (en las corridas, entre la vuelta 2 y la 20).

**Es del producto?** No como defecto para el usuario: el pedido ya respondió
y el registro se guarda. Es el arnés el que cerraba el pool en medio de una
tarea viva.

## El caso que antes daba rc=2: caso 9 (`conexiones1_soltar.py`)

Repite pedido + dispose hasta que el arnés anterior (dispose y esperar 15
s) deja una conexión abierta, y ahí prueba `soltar()`. Sale 4 si en 30
vueltas no se armó, y 2 si la conexión abierta no vino del pool descartado.

| corrida | rc | salida |
|---|---|---|
| HEAD | 0 | «vuelta 6: arnés anterior (dispose y esperar 15 s): 1 conexión(es) de la app abiertas» · «devueltas al pool descartado por: ['MetricsMiddleware.dispatch.<locals>.log_request_background']» · «soltar(): la base quedó sin conexiones de la app» |
| `gc.collect()` reemplazado por `pass` (el arreglo revertido) | 1 | «vuelta 5: arnés anterior (dispose y esperar 15 s): 1 conexión(es) de la app abiertas» · el mismo `log_request_background` · «soltar(): la app no soltó sus conexiones» |

**Que gc no tape una fuga.** Probé con un script que no se commitea: saca
una conexión del pool y no la devuelve. El `soltar()` de `4268eb2c` dio
verde: «soltar(): verde, OTRAS = 0», más un `SAWarning` que nadie miraba.
Con `e9323b67`: «OTRAS antes: 1» y «soltar(): la app dejó conexiones sin
devolver al pool: The garbage collector is trying to clean up
non-checked-in connection <AdaptedConnection <».

**El resto de la familia con el `soltar()` nuevo**, una vez cada uno:

| caso | corrida | rc | salida | rc=2 |
|---|---|---|---|---|
| 6 (`conexiones1_pares.py`) | con `parche_nokey.diff` | 1 | «deadlocks: 3; rondas sin armar: 0». Los 3 son pares con alta, de org con créditos vencidos: alta + guardado, alta + cancelar y alta + reactivar, con `[200, 500]`. Los otros 53 dieron `ok` | no |
| 7 (`conexiones1_renovacion.py`) | HEAD | 1 | «cuentas mal: 4; rondas sin armar: 0»: las 4 de renovación + guardado terminan `past_due`, como en H (D204) | no |

En ninguno de los dos hubo `Invalida` de `soltar()`. Los deadlocks con alta
ya estaban en H: NO KEY no cubre el alta.

## Caso natural (`conexiones1_natural.py`)

Los dos pedidos salen juntos con una barrera de hilos; nadie toma la fila
desde afuera. 10 rondas por combinación. Después de cada ronda:
`soltar()`, deadlocks de `pg_stat_database` y el estado de la recarga
(`mp_pagos_aplicados` y créditos de la org). Si perdió el aviso de MP,
manda el aviso firmado otra vez y mira de nuevo.

**HEAD** (`e9323b67`), rc=1, «deadlocks: 17, recargas perdidas: 0»:

| par | créditos | deadlock | quién pierde | recarga |
|---|---|---|---|---|
| recarga + guardado | vencidos | 8/10 | guardado 500 en 7, aviso 500 en 1 | aplicada, 10/10 vigentes en 9; la del aviso 500, abajo |
| recarga + guardado | al día | 0/10 | nadie | aplicada, 15/15 vigentes en las 10 |
| recarga + MARIA | vencidos | 9/10 | MARIA 500 en las 9 | aplicada, 10/10 vigentes en las 10 |
| recarga + MARIA | al día | 0/10 | nadie | aplicada, 15/15 vigentes en las 10 |

La ronda en que perdió el aviso, copiada del log:
`DEADLOCK | recarga + guardado | créditos vencidos | aviso 500, guardado 200 | pago sin fila, créditos 0/10 vencidos | reintento 200: pago aplicado, créditos 10/10 vigentes`

**Con `parche_nokey.diff`**, rc=0, «deadlocks: 0, recargas perdidas: 0»:
las 40 rondas `ok` con aviso 200 y el otro pedido 200. La recarga quedó
aplicada, 10/10 vigentes con créditos vencidos y 15/15 con créditos al día.

«10/10» quiere decir 10 créditos de la recarga y nada de los 5 vencidos;
«15/15», los 10 más los 5 que seguían vigentes.

Sale 2 si una ronda sin deadlock no dio 200/200: así no cuenta como «sin
deadlock» una ronda en la que un pedido falló por otra cosa. No pasó en
ninguna de las 80.

## Comandos

Desde la raíz, con `PY` apuntando al python del venv.

```bash
# caso 9: rc 0, con la vuelta, log_request_background y «la base quedó sin conexiones de la app»
scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_soltar.py
# rojo: en conexiones1_rondas.py, cambiar «gc.collect()» por «pass»: rc 1, «la app no soltó sus conexiones»

# natural en HEAD: rc 1, «deadlocks: N, recargas perdidas: 0» con N > 0
scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_natural.py
# natural con NO KEY: rc 0, «deadlocks: 0, recargas perdidas: 0»
PARCHE=conexiones1_parche_nokey.diff PY=$PY scripts/testing/conexiones1_con_parche.sh scripts/testing/conexiones1_natural.py

docs/pm/herramientas/chequeo-6.py 734b484c e9323b67
```

## Puertas

`chequeo-6`, salida entera:

```
chequeo-6 734b484c..e9323b67c9d3dcfe1ac06d05a7670757b7f7c2f9: avisos para mirar, no un veredicto
producto +0/−0
arnés +166/−3
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

Archivos de producto tocados: ninguno.

## Revisión

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| `/code-review` | Opus, alto | gc corría en el hilo principal, no en el loop de la app | Movido al loop (`c.portal.call`) |
| `/code-review` | Opus, alto | el natural no verificaba que los dos pedidos hubieran corrido | Sale 2 si no hubo deadlock y no dio 200/200 |
| `/code-review` | Opus, alto | el caso 9 salía 0 aunque nadie hubiera devuelto al pool descartado | Sale 2 |
| `/code-review` | Opus, alto | la barrera no tenía plazo | Tiene el plazo del arnés; el cuelgue al cerrar los hilos queda como riesgo |
| `/code-review` | Opus, alto | esperar la tarea de registro en vez de repetir dispose + gc | Queda así: dependería de un nombre interno del producto |
| `/code-review` | Opus, alto | `_return_conn` es privado de SQLAlchemy | Se usa sólo para diagnosticar en el caso 9 |
| `/code-review` | Opus, alto | el costo de gc en cada sondeo, el docstring de N y un nombre repetido | Bajo / corregido / renombrado a `ESTADO` |
| adversario | Sonnet, alto | MEDIA: gc tapaba una fuga real | Corregido con los avisos de gc; probado arriba |
| adversario | Sonnet, alto | MEDIA: el caso 9 con nadie anotado salía 0 | Corregido (igual que arriba) |
| adversario | Sonnet, alto | MEDIA: el natural no verificaba la recarga | Corregido: créditos esperados y «RECARGA PERDIDA» |
| adversario | Sonnet, alto | BAJA-MEDIA: no prueba que los pedidos se solapen | Límite del pedido: sin tomar la fila desde afuera, sólo lo muestra el deadlock |
| adversario | Sonnet, alto | BAJA: quién pierde se deduce del código HTTP | Límite: es lo que ve el usuario |
| adversario | Sonnet, alto | BAJA: una conexión ajena a la app en la base da falso rojo | Riesgo, abajo |

## Riesgos y lo no corrido

- `soltar()` cuenta todas las conexiones a la base del arnés, salvo la
  suya. Si otra cosa se conecta a esa base (no pasa con `con_pg16.sh`, que
  levanta una propia), espera de más y sale 2: falso rojo, nunca falso
  verde.
- Si un pedido se cuelga, `ThreadPoolExecutor` espera al cerrar. Lo corta el
  `timeout` de afuera (rc 124), no el caso.
- El natural en HEAD varía de corrida a corrida (antes dio 10/10 y 9/10;
  ahora 8/10 y 9/10). Los ceros con créditos al día y con NO KEY no
  cambiaron.
- **No corrido:** suite, e2e y arneses de otras piezas. No hay producto en
  la pieza.
