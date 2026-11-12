# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## D169 de MARIA: foco_perfil.sh mide pantalla_sesion1 en #pfEmail (sólo arnés)

**Resultado.** El caso está en `CASOS` (117c1d16). La puerta se cumple sobre
832bf74, pero **no sobre HEAD de esta rama**: el arreglo del arnés
(bcd1f07d, «espera el foco antes de escribir») está sólo en
`claude/dev-maria`. Ni tu rama ni la mía lo tienen, así que en nuestras HEAD
`pantalla_sesion1.js` es el mismo que en 832bf74 (blob 2af1303d) y pierde.
El verde se ve en la punta de MARIA (54ba0013). Supongo que tu «HEAD» era la
de ella; si no, va a aparecer cuando integres MARIA.

**Nada para decidir.** Esta pieza no integra la rama de MARIA: eso lo hacés vos.

| SHA medido | caso `pantalla_sesion1.js·#pfEmail` | rc |
|---|---|---|
| 832bf742 | PIERDE | 1 |
| 69d3ddbd (HEAD de esta rama antes del caso) | PIERDE | 1 |
| 54ba0013 (punta de `claude/dev-maria`) | NO PIERDE | 0 |

Los dos casos de `pantalla_estudio1` dan NO PIERDE en los tres SHAs.
Las líneas del caso, copiadas del log (sin las de `pantalla_estudio1` y con los correos tapados):

```
== 832bf74 832bf742
PIERDE      | scripts/testing/pantalla_sesion1.js·#pfEmail: lo escrito cayó en «Mi CUIT» (robado=%23pfEmail&valor=<MAIL>) · focos: foco=campo&ms=64
FALLA: TimeoutError: page.waitForResponse: Timeout 30000ms exceeded while waiting for event "response"
rc=1
== HEAD 69d3ddbd
PIERDE      | scripts/testing/pantalla_sesion1.js·#pfEmail: lo escrito cayó en «Mi CUIT» (robado=%23pfEmail&valor=<MAIL>) · focos: foco=campo&ms=49
FALLA: TimeoutError: page.waitForResponse: Timeout 30000ms exceeded while waiting for event "response"
rc=1
== 54ba0013 54ba0013
NO PIERDE   | scripts/testing/pantalla_sesion1.js·#pfEmail · focos: foco=reloj&ms=3000 foco=reloj&ms=3000 foco=reloj&ms=3000
rc=0
```

`chequeo-6 69d3ddbd 117c1d16`: producto +0/−0, arnés +1/−0, historia vacía,
avisos: 0.

Sin revisión de subagentes ni `/code-review`: es una línea de datos de un
arnés.

```bash
PY=<venv>/bin/python scripts/testing/foco_perfil.sh 832bf74;  echo rc=$?   # sesion1 PIERDE, rc=1
PY=<venv>/bin/python scripts/testing/foco_perfil.sh 54ba0013; echo rc=$?   # sesion1 NO PIERDE, rc=0
```

## CONEXIONES-1 K: soltar() dice qué hacen las conexiones; los pares de alta miden el estado final (sólo arnés)

**Resultado.** Las dos puertas se cumplen.

1. Cuando `soltar()` falla, dice el estado, en qué espera, desde cuándo y el
   comienzo de la consulta de cada conexión que quedó.
2. Los pares de alta miden lo que quedó en la base: la operación del alta y
   su ítem, la del guardado, una cuenta por operación y el plan. En HEAD, con
   N=20, ningún par de alta queda mal (0/20 en cada fila), ni siquiera en las
   rondas con deadlock. El sabotaje (una cuenta de más sin operación) da
   «CUENTA MAL» en 15 de 15 rondas.

`chequeo-6`: producto +0/−0, 0 avisos.

**Nada para decidir.** D205, D206 y D208 siguen como estaban. Supuesto
reversible: las filas «recarga + alta» de D188 también miden el alta (te lo
explico abajo).

| SHA | qué |
|---|---|
| 2ddeb589 | `test:` soltar() dice qué hacen las conexiones; los pares de alta miden el estado final |
| 7dcfc5cc | `test:` los pares recarga + alta también miden la operación y la cuenta del alta; recarga perdida y cuenta mal por separado |
| (este) | `docs:` informe |

Base f93c58c0. Las mediciones son sobre 7dcfc5cc, salvo la puerta forzada.
Esa corrió sobre 2ddeb589, y `conexiones1_rondas.py` no cambió entre
2ddeb589 y 7dcfc5cc.

## Puerta 1: soltar() con una conexión de la app tomada a propósito (forzado)

Un script descartable, fuera del repo: abre una conexión con el `engine` de
la app, hace `select count(*) from organizations`, no la devuelve y llama a
`soltar()`. La línea que dio:

```
forzado | soltar(): la app no soltó sus conexiones: idle in transaction, espera Client:ClientRead, hace 15.1 s: select count(*) from organizations
```

Después vienen «greenlet is being finalized» y un SAWarning: el gc limpia una
conexión sin devolver. Es esperable, porque la conexión se dejó tomada a
propósito.

«espera Client:ClientRead» es el `wait_event` de Postgres: la conexión está
esperando que la app le mande algo. Si no hay espera, la línea dice
«espera nada».

## Puerta 2: estado final de los pares de alta

Qué cuenta como «mal», en `alta_quedo`, para toda fila donde uno de los dos
pedidos es el alta:

- si el alta dio 200, su operación existe con exactamente un ítem;
- hay una operación más sólo si el guardado dio 200;
- `ops_used_this_period` sube una vez por operación guardada;
- `billing_status` es el que devolvió cancelar o reactivar si dieron 200; si
  no, el de antes.

Las recargas perdidas y las cuentas mal se cuentan por separado: una ronda
puede marcar las dos.

**HEAD (7dcfc5cc), N=20, rc=1**:

```
recarga + guardado, créditos vencidos: 15/20 rondas con deadlock, 0/20 mal
recarga + guardado, créditos al día: 0/20 rondas con deadlock, 0/20 mal
recarga + maria, créditos vencidos: 19/20 rondas con deadlock, 0/20 mal
recarga + maria, créditos al día: 0/20 rondas con deadlock, 0/20 mal
recarga + alta, créditos vencidos: 0/20 rondas con deadlock, 20/20 mal
recarga + alta, créditos al día: 0/20 rondas con deadlock, 0/20 mal
alta + guardado, créditos vencidos: 8/20 rondas con deadlock, 0/20 mal
alta + cancelar, créditos vencidos: 7/20 rondas con deadlock, 0/20 mal
alta + reactivar, cancelada: 5/20 rondas con deadlock, 0/20 mal
renovación + guardado, prueba vencida: 0/20 rondas con deadlock, 16/20 mal
renovación + guardado, active fuera de gracia: 0/20 rondas con deadlock, 15/20 mal
rondas con deadlock: 54, recargas perdidas: 20, cuentas mal: 31
rc=1
```

El rc=1 no viene de K:

- las 20 «mal» de recarga + alta son las recargas perdidas de D188 (lo mismo
  que en J). El lado del alta da bien en las 20 rondas: «1 operaciones, 1
  contadas, plan active | RECARGA PERDIDA»;
- las 31 cuentas mal son las de renovación (D205, de J).

En los pares de alta con deadlock, el que pierde no deja nada a medias. Estas
son las rondas con deadlock del log, agrupadas con `sort | uniq -c` (campos: par, códigos, qué quedó):

```
5 DEADLOCK | alta + guardado  | alta 500, guardado 200  | 1 operaciones, 1 contadas, plan active
3 DEADLOCK | alta + guardado  | alta 200, guardado 500  | 1 operaciones, 1 contadas, plan active
5 DEADLOCK | alta + cancelar  | alta 200, cancelar 500  | 1 operaciones, 1 contadas, plan active
2 DEADLOCK | alta + cancelar  | alta 500, cancelar 200  | 0 operaciones, 0 contadas, plan canceled
4 DEADLOCK | alta + reactivar | alta 200, reactivar 500 | 1 operaciones, 1 contadas, plan canceled
1 DEADLOCK | alta + reactivar | alta 500, reactivar 200 | 0 operaciones, 0 contadas, plan trial
```

Los 253 tracebacks del log son los deadlocks de la app:

| error | veces |
|---|---|
| `DeadlockDetectedError` | 72 |
| 500 de MARIA | 19 |
| 500 del guardado | 14 |
| 500 «MP reintentará» | 4 |

En la corrida N=20 sobre 2ddeb589 eran 310 tracebacks y 64 deadlocks.

**Sabotaje** (copia fuera del repo; antes de medir, `alta_quedo` suma 1 a
`ops_used_this_period` sin crear operación), N=3, sólo las filas con alta,
rc=1:

```
recarga + alta, créditos vencidos: 0/3 rondas con deadlock, 3/3 mal
recarga + alta, créditos al día: 0/3 rondas con deadlock, 3/3 mal
alta + guardado, créditos vencidos: 1/3 rondas con deadlock, 3/3 mal
alta + cancelar, créditos vencidos: 0/3 rondas con deadlock, 3/3 mal
alta + reactivar, cancelada: 2/3 rondas con deadlock, 3/3 mal
rondas con deadlock: 3, recargas perdidas: 3, cuentas mal: 15
rc=1
```

Las 15 rondas dicen «CUENTA MAL». Por ejemplo:

```
ok       | recarga + alta | créditos vencidos | recarga 200, alta 200 | pago aplicado, créditos 0/10 vencidos | 1 operaciones, 2 contadas, plan active | RECARGA PERDIDA | CUENTA MAL
```

«recarga + alta, créditos al día» no tiene recarga perdida, así que ahí el
«mal» viene sólo de la cuenta.

## chequeo-6 f93c58c0..7dcfc5cc

```
chequeo-6 f93c58c0..HEAD: avisos para mirar, no un veredicto
producto +0/−0
arnés +36/−11
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

`pyflakes` sobre `conexiones1_natural.py` da limpio. Hay una línea de más de
120 caracteres (la 40, de `recarga_quedo`), pero ya estaba en la base.

## Revisión

| # | quién (modelo, esfuerzo) | hallazgo | qué hice |
|---|---|---|---|
| 1 | `/code-review high` y adversario Sonnet alto | «recarga + alta» no medía el alta: la condición era `a == "alta"` | arreglado en 7dcfc5cc: se mide cuando el alta es cualquiera de los dos |
| 2 | `/code-review high` | el resultado de la recarga y el del alta usaban la misma variable `bien`, así que uno pisaba al otro | arreglado en 7dcfc5cc: `recarga_bien` y `cuenta_bien` por separado |
| 3 | `/code-review high` | el arnés supone que la org arranca sin operaciones | no aplica: `preparar` crea usuario y org nuevos en cada ronda |
| 4 | `/code-review high` | cuenta sólo las operaciones del dueño | no aplica: todos los pedidos los hace el dueño |
| 5 | `/code-review high` | carrera en `soltar()`: la conexión puede cerrarse entre el sondeo y la consulta | queda: el mensaje dice «ya no queda ninguna» y la corrida igual sale rc=2 |
| 6 | `/code-review high` | una consulta de más por ronda | arreglado: la cuenta previa se lee sólo si hay alta |
| 7 | adversario Sonnet alto | `plan_esperado` toma el plan de la respuesta | queda: la puerta pide que la respuesta y la base coincidan; si el endpoint decide bien es otra pregunta |
| 8 | adversario Sonnet alto | con `state_change` NULL saldría «hace None s» | queda: es sólo el texto del mensaje del rc=2 |

El adversario no pudo correr el arnés porque no tiene las dependencias.
Probó `QUE_HACEN` y `OPERACIONES` contra un PG16 propio y salieron bien.

## Riesgos y lo no corrido

- No corrí `conexiones1_soltar.py`. El comportamiento nuevo de `soltar()` se
  probó una vez, con la puerta forzada.
- La puerta forzada corrió sobre 2ddeb589. `conexiones1_rondas.py` no cambió
  después.
- Tampoco corrí la suite completa ni `e2e_maria.sh`: no hay producto.
- Lo que se cuenta como deadlock en cada fila varía entre corridas (64 en
  2ddeb589, 54 en 7dcfc5cc). Las cuentas mal y las recargas perdidas son las
  mismas de J.

## Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout 7dcfc5cc
# HEAD: rc=1; los pares de alta 0/20 mal; recargas perdidas 20 (D188); cuentas mal sólo de renovación
N=20 PY=<venv>/bin/python scripts/testing/con_pg16.sh <venv>/bin/python scripts/testing/conexiones1_natural.py > k.log 2>&1; echo rc=$?
grep -E 'mal$|^rondas' k.log
python docs/pm/herramientas/chequeo-6.py f93c58c0 7dcfc5cc   # producto +0/−0, avisos: 0
```

/compact conservar: Dev 1 técnica, rama claude/dev-tecnica; entregué CONEXIONES-1 K (32b1161c) y D169 de MARIA (117c1d16 + informe); nada para decidir; espero veredicto, nada «apenas entregues».
