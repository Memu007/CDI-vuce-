# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## La lista de usuarios en Postgres 16, sobre `3abb203d` (2026-11-21 06:50 UTC)

**Resultado.** Se cumple en `3abb203d`, contra tu rama integrada en `840cd8f5`. Sólo pruebas:
`producto +0/−0`. No hay diferencia de producto en Postgres, así que no hay D280. **Para decidir:
nada.**
- Los nueve casos de `tests/test_admin_usuarios1.py` corren contra un Postgres 16 descartable
  (`con_pg16.sh`) con `scripts/testing/admin_usuarios1_postgres.py`, y dan verde: la familia `COBROS`
  (lista = acceso), sólo admin, mirar no cambia la base. Los mismos nueve siguen en verde en SQLite.
- `COBROS` suma `de_estudio_borrado`: la integrante de un estudio que no existe. Se ve `past_due`,
  como decide el acceso, en las dos bases.
- La base se lee y se siembra por otra conexión, con el driver sincrónico de la misma base (en
  Postgres, `psycopg2`; en SQLite, `sqlite3`), fuera del pool de la app. Sale el `sqlite3` fijo.
- Rojo en Postgres con `admin_router.py` de `a17011d1`: falla sólo el caso de cobros, con cuatro
  cuentas (abajo).
- Sin esperas fijas nuevas: la única espera es la del lock de SQLite en la otra conexión (hasta 30 s,
  como la suite), que termina cuando el lock se libera.

| SHA | qué |
|---|---|
| `35efacb6` | test: los casos corren en Postgres 16; `de_estudio_borrado` en la familia; la otra conexión |
| `704febe4` | test: el caso de cobros dice qué cuentas ve distinto la lista que el acceso |
| `e27fe425` | test: la otra conexión espera el lock de SQLite 30 s; el guion se corta ante una marca que no sabe leer (sale de `/code-review`) |
| `098af21f` | test: el guion revisa todas las marcas antes de correr (sale de `/code-review`) |
| `81e5feeb` | test: el guion se corta ante tuplas de otro largo, un solo nombre y listas vacías (sale de `/code-review`) |
| `54220630` | test: el guion corre lo mismo que junta pytest, y un caso que devuelve algo sin correr es falla (sale de `/code-review`) |
| `3abb203d` | test: un `sys.exit` dentro de un caso es falla del guion, no un verde (sale del adversario) |

Archivos: `tests/test_admin_usuarios1.py` y `scripts/testing/admin_usuarios1_postgres.py` (nuevo). No
toqué `tests/conftest.py` ni ningún ayudante compartido.

## La premisa: en Postgres la integrante colgada no se puede sembrar

- En Postgres, `users.organization_id` tiene la clave foránea `users_organization_id_fkey` sin
  `ON DELETE`. Un `UPDATE` a un estudio que no existe falla, y borrar un estudio con integrantes
  también. No hay camino del producto que borre estudios.
- La colgada sólo existe en una base sin esa clave. El arranque la suma en
  `_migrate_add_user_organization_id` (`main.py:1174`) y traga el error (`main.py:1212`): si la base ya
  tenía una colgada, la clave no entra y la app arranca igual. Si producción tiene la clave, no lo puedo ver.
- Por eso el caso la siembra por la otra conexión con `SET session_replication_role = replica`, que
  apaga la clave en esa conexión. Pide superusuario; `cdi` de `con_pg16.sh` lo es.
- Con la clave prendida (sabotaje `con_la_clave`) la siembra falla:
  `ForeignKeyViolation … users_organization_id_fkey`, `Key (organization_id)=(borrado-adus7d53735e) is
  not present in table "organizations"`.

## Cómo corre en Postgres

`tests/conftest.py` fuerza SQLite por proceso, así que pytest no puede apuntar a Postgres sin tocarlo.
Seguí la costumbre de los 22 `scripts/testing/*_postgres.py`: un guion que crea una base descartable,
importa el módulo de casos y corre cada `test_`.
- Fuera de pytest no hay atajo de sesión: «sin sesión» pasa por el 401 real. El `LIKE` es el de
  Postgres.
- El motor de la app va sin pool, como en `conftest.py`: una conexión de asyncpg queda atada a su loop.
- El guion llama a `pytest --collect-only` del archivo y compara: si pytest junta un caso que el guion
  no corrió (una clase, un caso importado) o al revés, es falla. Un caso que devuelve algo
  (`async`, generador) es falla. Un `parametrize` que no sabe leer lo corta antes de correr.

## Lo que encontré de paso

- **`payment_method_brand` es `String(20)`.** SQLite no hace cumplir el largo; Postgres sí, y la
  siembra fallaba con `StringDataRightTruncationError`. La marca se corta a 20. Sigue siendo única por
  cuenta, y la respuesta se filtra por el prefijo de la corrida.
- **Ruido de asyncpg.** Cada corrida en Postgres que llega a los casos deja 10 a 16 «Task was destroyed but it is pending …
  `Connection._cancel()`». Sale del registro de pedidos en segundo plano de `MetricsMiddleware`
  (`main.py:2003`), que bajo pytest está apagado y fuera de él no: el `TestClient` cierra su loop con
  la escritura a medias. No cambia resultados. Es producto, no lo toqué.

## Puertas sobre `3abb203d`

| puerta | resultado |
|---|---|
| chequeo-6 `840cd8f5 3abb203d` | `producto +0/−0`, `arnés +192/−20`, `avisos: 0` (salida entera abajo) |
| grep de historia de §6 | vacío |
| `anclas_perdidas.py 3abb203d` | `112 guiones, 2710 anclas medidas y 11 llamadas sin medir`; perdidas `0`, `0` y `0`; `no medido 5` en 2 guiones; `sin ancla 6` en 1 |
| casos de admin en SQLite (`test_admin_usuarios1`, `test_admin_solo_admin`, `test_cobro_corte1`) | `134 passed, 19 warnings in 58.34s` |
| los nueve casos en Postgres 16 | 9 `OK`, «el guion corrió 9 casos y pytest junta 9», `fallas: 0`, rc=0 |
| `admin_usuarios1.sh 3abb203d` | 31 `ROJO`, «BASE \| en verde», `sabotajes sin rojo: 0` |
| `/code-review` alto | sobre `840cd8f5..704febe4`, `704febe4..e27fe425`, `e27fe425..098af21f`, `098af21f..81e5feeb`, `81e5feeb..54220630` y `54220630..3abb203d` (hallazgos abajo) |
| adversario Sonnet alto | sobre `704febe4`, y otra vuelta sobre `704febe4..54220630` |
| adversario Sonnet medio | sobre `54220630..3abb203d` |

Puertas de 06:41:46Z a 06:45:44Z. El `admin_usuarios1.sh` deja un `sh: 0: getcwd() failed` después
de su cuenta, al borrar su worktree: no cambia el resultado.

La corrección de anclas que pediste: los 5 «no medido» son `e2e_rerun.sh` (3, «el archivo o las anclas
salen de algo que sólo se sabe al ejecutar») y `foco_cliente1.sh` (2, «arma el cambio con sed»). Los 6
«sin ancla» son de `limpieza1.sh` (5 «nuevo», 1 «git»).

chequeo-6, salida entera:
```
chequeo-6 840cd8f5..3abb203d: avisos para mirar, no un veredicto
producto +0/−0
arnés +192/−20
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

## Rojos en Postgres sobre `3abb203d`

Cada uno en un worktree descartable con `con_pg16.sh`:

| cambio | qué falla |
|---|---|
| `admin_router.py` de `a17011d1` | sólo `test_la_lista_muestra_el_cobro_con_el_que_decide_el_acceso`, con `prueba_vencida ('trial', 'past_due')`, `fuera_de_la_gracia ('active', 'past_due')`, `de_estudio_vencido ('trial', 'past_due')` y `de_estudio_borrado ('trial', 'past_due')` (lista, acceso); `fallas: 1` |
| la lista toma el estudio de `User.organization_id` y no del estudio que existe | `test_cada_cuenta_se_ve_con_su_saldo` (la colgada con `saldo_del_estudio: True`) y el de cobros (`de_estudio_borrado (None, 'past_due')`); `fallas: 2` |
| la siembra sin apagar la clave | la siembra: `ForeignKeyViolation` (arriba) |

Del guion, en Postgres sobre `3abb203d` (`pg_neg_guion.log`):

| cambio al archivo de casos | qué dice el guion |
|---|---|
| ninguno | 9 `OK`, «pytest junta 9», `fallas: 0`, rc=0 |
| una `class TestOtra` con un caso | «el guion corrió 9 casos y pytest junta 10; sólo pytest: ['TestOtra::test_x']», rc=1 |
| un `async def test_async` | «test_async: no corrió, devolvió <coroutine …>», rc=1 |
| un caso con `sys.exit(0)` | «test_zz_sale: SystemExit: 0», rc=1 |
| `indirect` por posición en el `parametrize` | «pytest no pudo juntar», rc=1 |
| un nombre de más en el `parametrize` | «pytest no pudo juntar», rc=1 |

La lectura de marcas, aparte (`pg_negativos_casos.log`): tupla corta, tupla larga, un solo nombre,
nombres en lista, `ids` función, generador, lista vacía, `pytest.param` y `xfail` se cortan con «tiene
marcas que este guion no sabe correr». Un `parametrize` bien formado da sus 2 casos.

## Hallazgos

| de | sobre | qué | qué hice |
|---|---|---|---|
| `/code-review` alto | `840cd8f5..704febe4` | la otra conexión perdía el timeout de 30 s de SQLite | arreglado en `e27fe425` |
| `/code-review` alto | `840cd8f5..704febe4` | el superusuario no estaba dicho en el uso | arreglado en `e27fe425` |
| `/code-review` alto | `840cd8f5..704febe4` | el mensaje de cobros sólo miraba las claves de un lado | arreglado en `e27fe425` (la unión) |
| `/code-review` alto | `840cd8f5..704febe4` | la marca cortada a 20 pierde el prefijo | no lo cambio: sigue única por cuenta y la respuesta se filtra por el prefijo |
| `/code-review` alto | `704febe4..e27fe425` y `e27fe425..098af21f` | el guion leía a medias las marcas: `pytest.param`, `ids` de otro largo, marca del módulo, tuplas de otro largo, un nombre | arreglado en `098af21f` y `81e5feeb` |
| `/code-review` alto | `098af21f..81e5feeb` | seguía reescribiendo la recolección de pytest: clases importadas, `unittest`, generadores async, nombres de más | arreglado en `54220630`: compara con `pytest --collect-only`; sale el chequeo de clases de `81e5feeb` |
| `/code-review` alto | `704febe4..e27fe425` | la lectura por otra conexión en SQLite puede trabarse con una transacción diferida | ya estaba con el `sqlite3` de antes; no lo reproduje; no lo cambio |
| `/code-review` alto | `81e5feeb..54220630` | detalles que fallan cerrado: ids no ASCII o repetidos dan falso rojo; sin la salida de error ni tiempo máximo al juntar; un caso async deja un `RuntimeWarning` | riesgo 3; ninguno da un verde falso |
| Sonnet alto | `704febe4` | nada que frene; sus sabotajes (`outerjoin` por `join`, sin `require_admin`, «mirar guarda») dan rojo en Postgres | — |
| Sonnet alto | `704febe4..54220630` | verde falso: un `sys.exit(0)` dentro de un caso cortaba el guion con rc=0, sin `fallas:` ni comparar con pytest (`SystemExit` no es `Exception`). Lo reproduje sobre `54220630`: los OK hasta el último caso y `rc=0` (`pg_sale_sin_arreglo.log`) | arreglado en `3abb203d`: «test_zz_sale: SystemExit: 0», `fallas: 1`, rc=1 |
| `/code-review` alto | `54220630..3abb203d` | detalle: `pytest.skip` o `pytest.fail` dentro de un caso cortan el guion con traceback, sin decir cuál; `os._exit(0)` no se puede atrapar | riesgo 3; los dos primeros dan rc=1 |
| Sonnet medio | `54220630..3abb203d` | ningún camino a rc=0 con un caso en rojo o sin correr | — |

## Riesgos

1. **Superusuario.** El caso de la colgada en Postgres apaga la clave con
   `session_replication_role`. Con un usuario común ese `SET` da error y la siembra corta el guion
   con rc distinto de 0, antes de los casos: rojo, no verde falso. Leído, no corrido.
2. **Sólo `C.UTF-8`.** El `LIKE` y el orden se probaron con el locale de `con_pg16.sh`. Con otro
   locale podrían dar distinto.
3. **El guion falla cerrado en detalles**: un id con tilde o repetido da rojo con todo corrido; si
   pytest no puede juntar, el motivo puede quedar en la salida de error, que no muestra; la
   recolección no tiene tiempo máximo; `pytest.skip` o `pytest.fail` en un caso cortan con traceback
   y rc=1. Un `os._exit(0)` en un caso sí daría rc=0: no se puede atrapar, y nada en el producto lo
   llama.
4. **El guion es para este archivo.** Si se le suma a `test_admin_usuarios1.py` una fixture nueva o una
   marca que no sabe leer, se corta y hay que enseñarle.

## No corrido

- La suite completa: no toqué `tests/conftest.py` ni ayudantes compartidos.
- Postgres con un usuario que no sea superusuario, y otros locales.
- El Postgres de producción, ni ver si tiene la clave foránea: está fuera de lo permitido.

## Comandos para vos

Desde la raíz del repo, con el venv del proyecto en `PY`:
```bash
PY=/ruta/al/venv/bin/python
T="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. $PY -m pytest -q --no-cov -p no:cacheprovider"
G='"$PY" scripts/testing/admin_usuarios1_postgres.py "$BACKUP1A_PG_URL"'
# 1. chequeo-6: «producto +0/−0» y «avisos: 0»
python3 docs/pm/herramientas/chequeo-6.py 840cd8f5 3abb203d | grep -E "producto|avisos"
# 2. verde en Postgres: «el guion corrió 9 casos y pytest junta 9» y «fallas: 0»
git worktree add -q --detach /tmp/pg-verde 3abb203d && (cd /tmp/pg-verde && PY=$PY bash scripts/testing/con_pg16.sh sh -c "$G" 2>/dev/null | grep -E "^FALLA|junta|fallas:"); git worktree remove --force /tmp/pg-verde
# 3. rojo en Postgres con la lista de a17011d1: «fallas: 1», y difieren prueba_vencida, fuera_de_la_gracia, de_estudio_vencido y de_estudio_borrado
git worktree add -q --detach /tmp/pg-rojo 3abb203d && (cd /tmp/pg-rojo && git checkout a17011d1 -- proyecto_maria/routers/admin_router.py && PY=$PY bash scripts/testing/con_pg16.sh sh -c "$G" 2>/dev/null | grep -E "^FALLA|fallas:" | cut -c1-330); git worktree remove --force /tmp/pg-rojo
# 4. SQLite: «134 passed»
git worktree add -q --detach /tmp/pg-sqlite 3abb203d && (cd /tmp/pg-sqlite && $T tests/test_admin_usuarios1.py tests/test_admin_solo_admin.py tests/test_cobro_corte1.py | tail -1); git worktree remove --force /tmp/pg-sqlite
```
Ya corridos por mí, con esta salida: el 1, `producto +0/−0` · `avisos: 0`; el 2, «el guion corrió 9
casos y pytest junta 9» · `fallas: 0`; el 3, la línea `FALLA` con las cuatro cuentas · `fallas: 1`; el
4, `134 passed, 19 warnings in 57.82s`. Cada uno levanta su Postgres y lo borra; el 2 y el 3 tardan
alrededor de un minuto.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`; rutina trig_01Ukttby1fc4sGVQfSn1jC9U (/respondio), que se apaga con esta entrega: la PM me despierta por send_message. PM principal session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `840cd8f5`; timbre con send_message, priority next. Aceptadas: las de antes (… ADMIN-USUARIOS-1 sobre `b06b47fa`; D278 (b) sobre `05ca7f71`, integrada en `647ea7da`); D279 decidida (b). Desde ahora `admin_router.py` y `billing_service.py` son de la Técnica (ADMIN-CREDITOS-1, tramo 2). Entregada: la lista de usuarios en Postgres 16 sobre `3abb203d` (base `840cd8f5`, sólo pruebas, producto +0/−0), informe en este archivo, esperando veredicto; sin D. Lo pedido: en Postgres 16 la lista da lo mismo que en SQLite (familia COBROS con la integrante de estudio borrado, sólo admin, mirar no cambia la base leída por otra conexión de Postgres); casos con `con_pg16.sh`; rojo una vez en Postgres con `admin_router.py` de `a17011d1`; sin esperas fijas nuevas; una diferencia de producto en Postgres = frenar y D280; puertas chequeo-6, anclas_perdidas, casos de admin en SQLite y Postgres, /code-review; suite completa sólo si toco conftest o un ayudante compartido (no los toqué). Después de esta entrega no me queda pieza: lo mío espera a alguien de afuera (lista de empaque, TXT reales, texto de Emi). Próxima D: D280. Lecciones (además de las del historial de este archivo): un guion que reemplaza a pytest se compara con lo que junta `pytest --collect-only` en vez de reescribir su recolección; `SystemExit` no es `Exception`; `pytest.ini` trae `-v` en addopts: `-o addopts=` para leer ids; el negativo de un arreglo va en el mismo SHA con el arreglo vaciado; cada número del informe sale de un log, también las cuentas de líneas («25 ROJO» eran 24); `anclas_perdidas.py <SHA>` después de tocar líneas que anclan sabotajes, también de guiones ajenos, y antes de lanzar la suite (los tests leen los guiones); el `LIKE` de SQLite no distingue mayúsculas: `PRAGMA case_sensitive_like` en el caso; un adversario revisó un SHA: lo cambiado después se dice; un ancho en `ch` depende de la fuente: medir con Inter y con Liberation Sans (`fuente/arial.conf`); una regla de pantalla se mide en cada ancho de disposición; un sabotaje que falla en el primer elemento de una lista no prueba los de atrás; no editar `scripts/` mientras corre un guion de sabotaje: cortar las puertas y relanzarlas sobre el SHA nuevo; un valor puesto por código no dispara `input`; un campo de texto pierde los saltos de línea; puertas con `setsid nohup`; horas, sólo de `date -u`; los comandos para la PM se prueban antes de escribirlos; un borrador con huecos no se sube; el `TestClient` arranca la app y el arranque vence lo vencido: sembrar después de entrar; una fecha de prueba fijada al importar se gasta mientras corre la suite: contarla desde que se siembra; un commit que sale de un hallazgo pasa otra vez por adversario y `/code-review`. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe. Letra ancha: tabla U+FF01..FF5E, no NFKC («№» da Noruega).
