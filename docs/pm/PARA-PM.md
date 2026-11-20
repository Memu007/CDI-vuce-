# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1-NOKEY, vuelta: anclas de `cobro_corte1.sh` y el intermitente de `conexiones1_rondas.py:104`

| | SHA |
|---|---|
| base (lo último entregado, informe NOKEY) | `331bae9f` |
| test: anclas 430, 434 y 438 de `cobro_corte1.sh` siguen el candado NO KEY | `090609bc` |
| test: `soltar()` espera a que terminen las tareas de la app antes del dispose; `nokey.sh` sin sabotaje espera 0 | `05e61efa` |
| merges de tu rama | `590846b8`, `147be3b1` |
| informe | el commit `docs:` que trae este archivo |

**Ojo con el rango.** Entre `331bae9f` y `05e61efa` también están `7f4e04d1`,
`eca24bb4`, `5fc724d7` y `2f25488d`, que son de CONEXIONES-1-PRODUCTO y **no
están entregados**: van en su propia entrega, con su revisión fuerte. Esta
vuelta son sólo `090609bc` y `05e61efa`, y ninguno de los dos toca
`proyecto_maria/`: `git log 590846b8..05e61efa -- proyecto_maria/` da sólo tu
merge `147be3b1` y los dos commits de CATALOGO-PAIS-2 que trajo (`5ec05bbf`,
`d5b9e626`).

**Resultado.**

- Anclas: `anclas_perdidas` pasa de 5 PERDIDA (sobre `331bae9f`) a 0 (sobre
  `05e61efa`).
- `cobro_corte1.sh` sobre `05e61efa`: rc=0 en 4770 s, 87 ROJO, ningún ROTO, PATRÓN ni MAL, «sabotajes con falla: 0». «BASE  | el lock en verde» y los tres sabotajes del lock en ROJO (abajo).
- El intermitente de `conexiones1_rondas.py:104` es **del arnés, no de la
  app**. Arreglado en `05e61efa`: 12/12 verdes con el arreglo, 11/12 sin él.

### El intermitente: causa

`MetricsMiddleware` (`main.py:1978-2001`) registra cada pedido en una tarea que
sigue viva después de responder (`log_request_background`: `session.add`, `await
session.commit()` en la 1998, `break`). `soltar()` llamaba a `engine.dispose()`,
que reemplaza el pool. Si la tarea de log devuelve su conexión **después** del
dispose, la conexión cae en el pool descartado, queda abierta en Postgres
(idle, último SQL `COMMIT;`) y el chequeo de `OTRAS` la cuenta.

Evidencia, sin el arreglo (12 réplicas de `conexiones1_pares.py` con un
diagnóstico que, cuando `soltar()` falla, vuelca tareas, pool y quién retiene
cada conexión abierta):

- 11 rc=0, 1 rc=2. La que falla dice:
  ```
  DIAG falla: la app no soltó sus conexiones: idle, espera Client:ClientRead, hace 14.3 s: COMMIT;
  DIAG pids idle: [17823]
  DIAG engine.pool: … Pool size: 20  Connections in pool: 0 Current Overflow: -20 Current Checked out connections: 0
  ```
  El pool vivo no tiene nada prestado. En ese momento ya no queda la tarea de
  log (sólo `run_portal` y dos `TaskHandle._run_coro`, del portal). A la
  conexión del pid 17823 no la referencia ningún objeto de la app: sólo listas
  de gc. Es decir, alguien la devolvió, pero a un pool que ya no existe.
- Contando en cada llamada a `soltar()` qué tareas de la app siguen vivas: en 2
  de 56 llamadas estaba viva
  `MetricsMiddleware.dispatch.<locals>.log_request_background [log_request_background:1998]`,
  parada justo en el `await session.commit()`.

**Por qué no es de la app.** En el producto, `engine.dispose()` sólo está en
`close_db()` (`database/connection.py:161`), que corre al apagar. Fuera de eso,
la conexión que devuelve la tarea de log vuelve al pool vivo. Una conexión que
la app no devuelve nunca la seguiría atrapando el aviso `non-checked-in` de gc
que `soltar()` ya tenía, y ese aviso no apareció.

**Arreglo (arnés, `05e61efa`).** Antes del dispose, `soltar()` espera con
`h.hasta` a que no quede ninguna tarea de la app sin terminar (las que tienen
el código en `proyecto_maria/`). Si una tarea no termina nunca, `h.hasta` se
vence y el mensaje la nombra («tareas de la app sin terminar: [...]»): no se
esconde nada, se espera una condición observable. Con el arreglo: 12/12 rc=0,
«fin en 506s».

### `conexiones1_nokey.sh`: «sin sabotaje» ahora espera 0

Antes salía 1 por 3 deadlocks de los pares del alta. El alta del arnés es
`/api/operations/manual`, y PRODUCTO (`7f4e04d1`) cambió su dependencia a
`require_billing_vigente`, que suelta la conexión: los deadlocks del alta
pasaron de 3 a 0. Por eso el control ahora exige 0.

**Esto depende de PRODUCTO.** Sobre un SHA sin `7f4e04d1`, «sin sabotaje» vuelve
a dar 1 y el guion da MAL. Si aceptás la vuelta y rechazás PRODUCTO, esta línea
vuelve a 1.

### Decisiones

- **D231 (pendiente de tu veredicto).** El pin de SQLAlchemy 2.0.25 y el `of=`.
  Sigo recomendando a): dejar el pin y el `of=`. Lo contestás con el veredicto.

Lo de `limpieza1` ya lo aceptaste («no lo nombra como PERDIDA»): no queda
abierto.

### Comandos

```bash
PY=$PWD/<venv>/bin/python
git log --oneline 590846b8..05e61efa -- proyecto_maria/
# sólo 147be3b1 (tu merge), 5ec05bbf y d5b9e626 (CATALOGO-PAIS-2): nada mío
git show --stat 090609bc 05e61efa | grep '|'
# sólo cobro_corte1.sh, conexiones1_rondas.py y conexiones1_nokey.sh
$PY scripts/testing/anclas_perdidas.py 05e61efa | grep -c PERDIDA
# 0 (sobre 331bae9f da 5)
PG=postgresql://<usuario>@127.0.0.1:<puerto> PY=$PY scripts/testing/sabotajes/cobro_corte1.sh 05e61efa
# «BASE  | el lock en verde», los tres sabotajes del lock en ROJO, ningún ROTO, «sabotajes con falla: 0»
PY=$PY scripts/testing/sabotajes/conexiones1_nokey.sh 05e61efa
# tres BIEN; «sin sabotaje: salida 0», «deadlocks: 0; rondas sin armar: 0; filas MAL: 0»
for i in $(seq 12); do PY=$PY scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_pares.py >/dev/null 2>&1; echo "réplica $i rc=$?"; done
# las 12 con rc=0
```

### Lo que ya corrí

| Puerta | SHA | Resultado |
|---|---|---|
| `anclas_perdidas.py` | `331bae9f` | «110 guiones, 2664 anclas medidas y 11 llamadas sin medir», 5 PERDIDA |
| `anclas_perdidas.py` | `05e61efa` | «110 guiones, 2663 anclas medidas y 11 llamadas sin medir», 0 PERDIDA; sólo las 6 SIN ANCLA de `limpieza1` (175–187) |
| `cobro_corte1.sh` con Postgres 16 | `05e61efa` | rc=0 en 4770 s; 87 ROJO, 3 BASE en verde, «sabotajes con falla: 0» |
| `conexiones1_pares.py`, 12 réplicas, sin el arreglo | `2f25488d` + diagnóstico | 11 rc=0, 1 rc=2 (la de arriba) |
| `conexiones1_pares.py`, 12 réplicas, con el arreglo | `05e61efa` | 12 rc=0, «fin en 506s» |
| `conexiones1_nokey.sh` | `05e61efa` | rc=0 en 136 s, tres BIEN (abajo) |

`conexiones1_nokey.sh` sobre `05e61efa`:

```
BIEN  | sin sabotaje: salida 0, dice «_cuenta_bloqueada después del aviso: FOR NO KEY UPDATE OF users | FOR NO KEY UPDATE OF organizations»
        deadlocks: 0; rondas sin armar: 0; filas MAL: 0
BIEN  | sin key_share ni of=: salida 1, dice «FOR UPDATE | FOR UPDATE | MAL DEADLOCK | recarga + guardado DEADLOCK | recarga + maria»
        DEADLOCK | recarga + alta | org | créditos vencidos | [200, 500] | deadlocks +1
        DEADLOCK | recarga + guardado | org | créditos vencidos | [200, 500] | deadlocks +1 | MAL
        DEADLOCK | recarga + maria | org | créditos vencidos | [200, 500] | deadlocks +1 | MAL
        deadlocks: 3; rondas sin armar: 0; filas MAL: 2
BIEN  | key_share sin of=: salida 1, dice «FOR NO KEY UPDATE | FOR UPDATE | MAL»
        deadlocks: 0; rondas sin armar: 0; filas MAL: 0
rc=0 en 136s
```

`cobro_corte1.sh` sobre `05e61efa`, desde la base del lock hasta el final (antes hay 81 ROJO, «BASE  | en verde», «BASE  | la pantalla en verde» y la línea «Preparing worktree»):

```
BASE  | el lock en verde
ROJO  | no se bloquea la fila del usuario: dice «FALLA | tope»
ROJO  | no se bloquea la fila de la organización: dice «FALLA | estudio»
ROJO  | se cuenta con el usuario leído antes del lock: dice «FALLA | tope»
ROJO  | borrar cliente no espera el candado de la cuenta: dice «FALLA | borrar cliente»
ROJO  | el guardado mira el cliente antes del candado: dice «FALLA | guardar en un cliente que se borró»
ROJO  | Postgres recibe el id que no puede comparar: dice «FALLA | id con NUL»
sabotajes con falla: 0
rc=0 en 4770s
```

`chequeo-6`, enteros:

```
chequeo-6 590846b8..2f25488d: avisos para mirar, no un veredicto
producto +0/−0
arnés +5/−7
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
---
chequeo-6 147be3b1..05e61efa: avisos para mirar, no un veredicto
producto +0/−0
arnés +18/−8
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
---
chequeo-6 331bae9f..05e61efa: avisos para mirar, no un veredicto
producto +30/−27
arnés +135/−62
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12289 → 12279
  proyecto_maria/static/v2/paises_maria.js: 288 → 295
  AVISO creció una función de más de 150: proyecto_maria/static/v2/paises_maria.js:2 <anónima> 286 → 293, 2 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/catalogo.js: 404 → 405
  proyecto_maria/static/v2/screens/clientes.js: 2219 → 2224
avisos: 1
```

El primero es `090609bc` (está entre `590846b8` y `2f25488d`, junto con el
`2f25488d` de PRODUCTO). El tercero incluye PRODUCTO y lo de MARIA de tus
merges: el AVISO de `paises_maria.js` viene de `5ec05bbf` (CATALOGO-PAIS-2), no mío.

### Hallazgos

| Revisor | Modelo y esfuerzo | Hallazgo | Qué pasó |
|---|---|---|---|
| — | — | Vuelta de arnés sin producto: no corrí adversarios ni `/code-review` | declarado abajo |

### Qué no se corrió

- **Suite completa sobre `05e61efa`.** No la corrí: esta vuelta no toca nada
  que corra pytest. La suite con PRODUCTO va en su entrega.
- **Adversarios y `/code-review`.** No los corrí sobre esta vuelta: son dos
  cambios de arnés, sin producto. PRODUCTO los lleva.
- **Un rojo más fuerte del arreglo.** Sin el arreglo el intermitente salió en
  1 de 12 (vos lo viste en 3/12 y 4/12). El rojo existe, pero es débil: 12/12
  con el arreglo no prueba que nunca falle, sólo que bajó.
- **La primera corrida de `cobro_corte1.sh`.** Se cortó a los 30 min por el
  límite de la herramienta, con 46 ROJO y sin ROTO; la relancé entera con 2 h.

### Riesgos

- **Apagado.** `close_db()` hace `engine.dispose()` mientras puede haber una
  tarea de log en vuelo. Esa conexión quedaría fuera del pool hasta que el
  proceso termine. Al apagar es inocuo (el proceso muere), pero no está
  medido.
- **`nokey.sh` depende de PRODUCTO** (arriba).
- El texto del `CHANGELOG` de NOKEY dice «el alta de un integrante»: el «alta»
  del arnés es la carga manual (`/api/operations/manual`). Lo corrijo en
  PRODUCTO, que es la que cambia ese comportamiento, salvo que digas otra cosa.

### Corrección de la «Observación, no es mía»

En el informe anterior dije que las 5 PERDIDA de `anclas_perdidas` no eran
mías. Las 3 de `cobro_corte1.sh` (430, 434, 438) **sí eran mías**: las rompió
`298e5fee`, que cambió `.with_for_update()` por `key_share=True, of=…` sin
mover las anclas. Las arregla `090609bc`. Las 2 de `catalogo_largo2.sh` (224,
263) no eran mías: las arregló `cbd7718c`, que vino con tu merge.

Ahora sigo con CONEXIONES-1-PRODUCTO (D182, D183, D188). **Próxima D: D232.**

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica. CONEXIONES-1-NOKEY vuelta entregada (090609bc anclas cobro_corte1, 05e61efa soltar() espera tareas de la app; informe en el docs siguiente); D231 pendiente del veredicto. Pieza activa: CONEXIONES-1-PRODUCTO (7f4e04d1, eca24bb4, 5fc724d7, 2f25488d ya en la rama, sin entregar). Revisión fuerte: /security-review, /code-review high, adversarios con Postgres 16 sin red y GEMINI_API_KEY vacía, suite completa sobre el SHA final, e2e_maria.sh, conexiones1_producto.sh en su commit test:, anclas_perdidas, git apply --check en worktree limpio; corregir CHANGELOG «alta de un integrante». Próxima D: D232. Sin advisor, nunca main, sin secretos, test_conexiones1.py no se sube.
