# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1 H: casos 6 y 7 sobre HEAD, como scripts (sólo arnés)

**Hallazgo de producción: sí, hoy dan deadlock.** En HEAD, una org con
créditos extra vencidos que guarda una operación a la vez que recarga, o que
genera MARIA a la vez que recarga, recibe un 500 y Postgres cuenta un
deadlock. El usuario ve «No se pudo guardar la operación al cliente: …
DeadlockDetectedError» o «Error generando archivo MARIA: … deadlock
detected». Lo mismo pasa con alta + guardado, alta + cancelar y alta +
reactivar de esa org. Con un usuario suelto, o con créditos al día, no pasa.

**D204 reproduce.** Si la renovación llega antes que el pedido que vence la
cuenta, la cuenta queda `past_due` con el período por delante: pagó y queda
bloqueada. Pasa con usuario y org, con prueba vencida y con `active` fuera de
gracia: 4 de 8. El parche (b) no lo arregla. El arreglo lo decide Emi (D205).

| SHA | Qué |
|---|---|
| `06695c86` | `test:` casos 6 y 7, `parche_b.diff`, `con_parche.sh` |
| `cfc5f2af` | `test:` `PARCHE=` elige el parche; `parche_nokey.diff` |
| `218069dc` | `test:` el contador no depende del 500; arnés roto sale 2 |
| `7e55e35d` | `test:` docstring del caso 7 a 80 columnas |
| este commit | `docs:` este informe |

Producto +0/−0. Emi no dijo que sí a D182: sigo en H.

## Decisiones

- **D205 (para Emi): el arreglo de D204.** Hoy quien vence lee la cuenta
  sin candado y escribe `billing_status = 'past_due'` encima de la
  renovación. Son dos lugares: `_vencer_y_guardar` (`main.py:2282`, desde
  `require_billing_vigente`) y `get_current_user`
  (`auth/dependencies.py:146`), que es el que escribe en las filas de
  prueba vencida de un usuario.
  - (a) **Recomendada.** Vencer con un `UPDATE … WHERE billing_status = <el
    leído> AND trial_ends_at = <el leído>`. Si la renovación ya escribió, no
    toca nada. Sin candado nuevo, así no suma otro orden de toma al de
    D206. Son los dos lugares, una sola función.
  - (b) Vencer bajo `FOR UPDATE` releyendo la fila. También arregla, pero
    toma otro candado en cada pedido de una cuenta vencida.
  - (c) No tocar: pasa sólo si los dos llegan en la misma ventana, y la
    próxima renovación lo corrige, pero mientras tanto pagó y no puede
    trabajar.
- **D206 (para Emi): los deadlocks de hoy.**
  - (a) **Recomendada.** Una pieza chica ya: las 2 líneas de
    `parche_nokey.diff` (`FOR NO KEY UPDATE` con `of=`). Medido: arregla
    recarga + guardado y recarga + MARIA, que son los que pidió saber. No
    arregla alta + guardado, alta + cancelar ni alta + reactivar: esos
    necesitan (b) entero, que espera D182.
  - (b) Esperar D182 y entrar todo con la pieza de (b).

## Resultados

Caso 6: 7 pares × 2 órdenes × usuario/org × créditos vencidos/al día = 56
rondas. Caso 7: 2 órdenes × usuario/org × prueba vencida/`active` fuera de
gracia = 8 rondas. Una vez cada uno, sobre `7e55e35d`, salvo el caso 6 en
HEAD: corrió con el árbol que después fue `218069dc`; `7e55e35d` sólo
cambia el docstring del caso 7.

| Caso | Árbol | rc | Resultado |
|---|---|---|---|
| 6 | HEAD | 1 | `deadlocks: 5; rondas sin armar: 0` |
| 6 | (b) completo | 0 | `deadlocks: 0; rondas sin armar: 0` |
| 6 | sólo `FOR NO KEY UPDATE` | 1 | `deadlocks: 3; rondas sin armar: 0` |
| 7 | HEAD | 1 | `cuentas mal: 4; rondas sin armar: 0` |
| 7 | (b) completo | 1 | `cuentas mal: 4; rondas sin armar: 0` |

Caso 6 en HEAD, las 5 rondas con deadlock, todas de org con créditos
vencidos, `[200, 500]`:

```
DEADLOCK | alta + guardado | org | créditos vencidos | [200, 500] | deadlocks +1
DEADLOCK | recarga + guardado | org | créditos vencidos | [200, 500] | deadlocks +1
DEADLOCK | recarga + maria | org | créditos vencidos | [200, 500] | deadlocks +1
DEADLOCK | alta + cancelar | org | créditos vencidos | [200, 500] | deadlocks +1
DEADLOCK | alta + reactivar | org | créditos vencidos | [200, 500] | deadlocks +1
```

Con sólo `FOR NO KEY UPDATE` quedan alta + guardado, alta + cancelar y alta +
reactivar. Por D203, el rojo de alta + cancelar/reactivar con (a) es el que
mete (b): con (b) completo dan 0.

Línea que el caso 6 imprime del código de `_cuenta_bloqueada`:
- HEAD: `_cuenta_bloqueada: with_for_update() | with_for_update()`
- (b) y sólo NO KEY, igual: `_cuenta_bloqueada: with_for_update(key_share=True, of=User) | with_for_update(key_share=True, of=Organization)`. Lo demás de (b) está fuera de esa función.

Caso 7 en HEAD. Con (b), las 4 MAL son iguales; en las ok cambia el código del
guardado en dos filas (usuario con prueba vencida y org `active` fuera de
gracia): `[200, 200]` en vez de `[402, 200]`. La cuenta termina igual,
`active` con el período por delante; leo que con (b) ese guardado ya vio la
renovación, pero no lo medí aparte.

```
ok       | guardado + renovación | usuario | prueba vencida | [402, 200] | termina active, período por delante
ok       | guardado + renovación | usuario | active fuera de gracia | [402, 200] | termina active, período por delante
ok       | guardado + renovación | org | prueba vencida | [402, 200] | termina active, período por delante
ok       | guardado + renovación | org | active fuera de gracia | [402, 200] | termina active, período por delante
MAL      | renovación + guardado | usuario | prueba vencida | [200, 402] | termina past_due, período por delante
MAL      | renovación + guardado | usuario | active fuera de gracia | [200, 402] | termina past_due, período por delante
MAL      | renovación + guardado | org | prueba vencida | [200, 402] | termina past_due, período por delante
MAL      | renovación + guardado | org | active fuera de gracia | [200, 402] | termina past_due, período por delante
```

## Comandos

Desde la raíz, con el venv del proyecto en `PY`. Cada uno tarda unos minutos.

```bash
PY=$PWD/venv/bin/python   # o el tuyo
# caso 6 en HEAD → 5 líneas DEADLOCK, «deadlocks: 5; rondas sin armar: 0», rc=1
scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_pares.py; echo rc=$?
# caso 6 con (b) → ninguna DEADLOCK, «deadlocks: 0; rondas sin armar: 0», rc=0
PY=$PY scripts/testing/conexiones1_con_parche.sh scripts/testing/conexiones1_pares.py; echo rc=$?
# caso 6 con sólo NO KEY → 3 DEADLOCK (alta + guardado/cancelar/reactivar), rc=1
PARCHE=conexiones1_parche_nokey.diff PY=$PY scripts/testing/conexiones1_con_parche.sh scripts/testing/conexiones1_pares.py; echo rc=$?
# caso 7 en HEAD y con (b) → 4 MAL, «cuentas mal: 4; rondas sin armar: 0», rc=1
scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_renovacion.py; echo rc=$?
PY=$PY scripts/testing/conexiones1_con_parche.sh scripts/testing/conexiones1_renovacion.py; echo rc=$?
# parche que no aplica → rc=2
PARCHE=no_existe.diff PY=$PY scripts/testing/conexiones1_con_parche.sh scripts/testing/conexiones1_pares.py; echo rc=$?
git worktree list | grep -c cdi-parche   # → 0
```

Códigos de salida: 1 = deadlock o cuenta mal; 4 = alguna ronda no se armó;
2 = el arnés falló o el parche no aplica; 0 = limpio. Un error de import o
de `git worktree add` sale 1 igual, pero sin la última línea «deadlocks: N»
o «cuentas mal: N»: así se distingue.

## Puertas

| Puerta | Salida |
|---|---|
| `chequeo-6 6001684..7e55e35d` | `producto +0/−0`, `arnés +323/−0`, historia vacía, `avisos: 0` |
| caso 6 y 7, con y sin parche | la tabla de Resultados |
| parche inexistente | rc=2 |
| worktrees `cdi-parche` sueltos | 0 |
| suite completa | **no corrida**: no hay producto |

Salida entera de `chequeo-6`:

```
chequeo-6 6001684ccc1249bc5bfbf33e10e6d327d80c51b2..7e55e35dc2dffa98c36502431bcc3929c1723b72: avisos para mirar, no un veredicto
producto +0/−0
arnés +323/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Cómo cuenta el arnés

- El deadlock lo cuenta `pg_stat_database.deadlocks` antes y después de la
  ronda. Postgres lo actualiza sin plazo fijo, pero sí al cerrar la conexión:
  la ronda cierra el pool de la app y espera a que no le quede ninguna
  conexión. Así cuenta también un deadlock que la app atrape y no dé 500
  (`_vencer_y_guardar` hace `rollback` de cualquier excepción).
- La ronda se arma cuando el segundo pedido está esperando el candado del
  primero; si no se arma, la ronda sale «NO SE ARMÓ» y el caso da 4.

## Revisión

| Quién | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| adversario | Sonnet, alto | Excepción del arnés salía 1, igual que un deadlock | Arreglado: sale 2 |
| adversario | Sonnet, alto | Parche que no aplica salía 1 | Arreglado: sale 2 |
| `/code-review` | high | El contador sólo esperaba si había un 500 | Arreglado: cierra el pool y espera siempre |
| `/code-review` | high | El docstring del caso 7 no nombraba `get_current_user` | Arreglado |
| `/code-review` | high | `.sh`: raíz relativa, trap, stderr tapado | Arreglado |
| adversario | Sonnet, alto | El 0 es de (b) completo, no de NO KEY solo | Declarado: la tabla trae las 3 variantes |
| adversario | Sonnet, alto | El caso 6 imprime el código fuente, no el SQL emitido, y corta «esperaba» a 110 caracteres: no se ve el modo del candado | Queda. La línea de `_cuenta_bloqueada` sí muestra el modo |
| `/code-review` | high | `ronda` duplica `fase_carrera` de `conexiones1_creditos.py`; el loop de reporte se repite en los dos casos | Queda: `creditos.py` no lo toco en H. Va a la cola si la pieza de producto no lo absorbe |
| adversario | Sonnet, alto | `parche_b.diff` contiene a `parche_nokey.diff` | Queda: son variantes completas, no se aplican juntas |
| adversario | Sonnet, alto | Con NO KEY, la ronda puede armarse por una espera de FK y no por el candado | Queda: el arnés no distingue qué pedido espera |
| adversario | Sonnet, alto | El argumento del `.sh` tiene que ser relativo a la raíz; el caso 7 no imprime el árbol | Queda: el uso lo dice |

El adversario reprodujo por su cuenta los mismos números de HEAD, (b) y NO
KEY antes del arreglo del contador.

## Riesgos y lo no corrido

- Cada caso corrió una vez por árbol. Es una carrera armada (el segundo
  pedido espera el candado del primero), no un sorteo, pero no midió
  frecuencia en producción.
- Suite completa, e2e y arneses de otras piezas: no corridos; no hay
  producto.
- `tests/test_conexiones1.py` sigue sin seguimiento a propósito.
