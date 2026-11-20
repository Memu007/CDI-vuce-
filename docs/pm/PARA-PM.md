# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1-PRODUCTO, con NOKEY adentro

| | SHA |
|---|---|
| base | `ac4993b7` |
| producto | `7f4e04d1` (soltar la conexión), `5fc724d7` (comentario), `b3b99395` (NO KEY en cancelar y reactivar), `5cc054b0` (tope antes del cuerpo) |
| pruebas | `eca24bb4`, `2f25488d`, `1235ac4f`, `709b3a3e`, `0b1f02b0`, `5460fb94` |
| docs | `4d33d2ca` (CHANGELOG) |
| **puertas sobre** | **`b4f7e5905e2aac755f871849a296d202a3e72840`** (merge de tu `44e3b0ba`) |
| entrego | el commit de este informe, encima de `1c5924dc` |

**Ojo con el rango.** Todas las puertas corrieron sobre `b4f7e590`. Después integré 9 commits tuyos
(hasta `7b32f0c2`), sólo de `docs/pm`: `git diff b4f7e590 1c5924dc -- proyecto_maria scripts tests`
da vacío. Los casos nuevos siguen fuera de git: van en `scripts/testing/conexiones1_tests.diff`
(`git apply --check` rc=0 sobre el SHA).

**Resultado.**
- Las rutas que cobran sueltan la conexión antes de esperar el cuerpo, la IA o el archivo
  (`_billing_vigente` → `_soltar_conexion`; analyze y sugerir, además, antes de Gemini). Con 60
  pedidos lentos de una cuenta, la otra espera ≤ 0,44 s en sugerir, PDF, analyze y manual, con 0 × 500
  en los cinco picos. En el pico de login espera 3,96 s: es bcrypt (D180), que en la base ya daba 3,68 s.
- D188: la carga manual ya no vence créditos sin candado. `conexiones1_creditos.py`: en la base
  «quedan 0 de 10 pagos (perdidos 10)» en usuario y org, rc=1; en el SHA «pierden: 0; no valen: 0;
  sin carrera: 0», rc=0.
- Cancelar y reactivar toman al usuario con `FOR NO KEY UPDATE OF users` (`b3b99395`): recarga +
  cancelar y recarga + reactivar con créditos vencidos daban deadlock y 500, también en la base.
- La carga manual mira el tope del plan en `require_cupo_del_plan`, antes de leer el cuerpo. Lo
  encontró el adversario Opus: una cuenta al tope recibía 404/400 en vez de 402.
- Suite completa `6251 passed, 110 skipped, 3 xfailed`; `e2e_maria.sh` OK; `cobro_corte1.sh` 87 ROJO, «sabotajes con falla: 0»;
  D205 sigue «cuenta mal»: renovación «cuentas mal: 4», natural «cuentas mal: 19», todas en
  renovación + guardado; «recargas perdidas: 0», «rondas con deadlock: 0».
- `producto +218/−54` en el rango de la base (+164 netas). Lo mío, medido contra `44e3b0ba`, es
  `producto +47/−42`, avisos 0. Los 164 y los dos AVISO son de ADMIN-USUARIOS y CATALOGO-PAIS-2, que
  vinieron con tus merges.

### Decisiones

Nada para decidir. D231 (a) ya la decidiste: quedan el pin de SQLAlchemy 2.0.25 y el `of=`.

Supuesto reversible: como `require_billing_vigente` suelta la conexión al salir, ahora también la
sueltan las rutas que ya la usaban (`/process_operation/`, `/upload_pdf/public`, `/generate_maria`,
`/generate_maria_export`, `/api/migrations/{batch_id}/confirm`, `/api/clientes/{client_id}/operaciones`).
No las pidió la tarea una por una, pero es el lugar por donde pasan todas (§6: un chequeo, una vez).

### El intermitente: por qué la conexión sobrevivió 14 s de dispose + gc

Con evidencia, en `raiz3.log`: un diagnóstico con `gc.get_referrers` desde la conexión asyncpg que
seguía abierta, excluyendo los frames del propio diagnóstico.

- La tarea de log (`log_request_background`, `main.py:1978-2001`) devolvía su conexión **después**
  del `engine.dispose()`. `dispose` cierra sólo lo que está en el pool en ese momento y lo cambia por
  uno nuevo; lo que vuelve después entra al pool viejo y queda idle.
- El gc no lo junta porque una referencia fuerte viva retiene el pool viejo. **Lo que dije antes,
  «sólo listas de gc», era falso.** Las 5 cadenas RAIZ dan lo mismo: la tarea del lifespan del
  TestClient (`testclient.py:589`) → middlewares → `Router.lifespan` → `lifespan()` de
  `main.py:1652`, suspendido en su `yield` → la local `result` del `select(User)` del bucle de
  `_admin_usernames()` (~1749) → `CursorResult` → `PGExecutionContext_asyncpg` → `_ConnectionFairy`
  → `AsyncAdaptedQueuePool` viejo. Mientras viva la app, vive el pool viejo, y su conexión también.
- `raiz.log` estaba autorreferido (el frame del diagnóstico) y lo descarté; `raiz2.log` y
  `raiz3.log` excluyen esos frames. `raiz3.log`: `soltar()` viejo con la carrera de 1 s en la tarea
  de log, rc=2 en 24 s, «conexiones adentro: 6», «tareas de la app sin terminar: []».
- El `soltar()` nuevo espera a `tareas_de_la_app` antes del dispose, así la conexión vuelve al pool
  que se cierra. En esta tanda, con el `soltar()` nuevo, no hubo ningún rc=2: `nokey` rc=0 con sus 4
  corridas y `producto` rc=0 con sus 11.
- **No sé por qué tu corrida con 1 s pasó dos veces con el `soltar()` viejo** y la mía no. Lo dejo
  dicho; no lo cierro con la suerte.
- El síntoma es sólo del arnés: en producción, `dispose` está sólo en `close_db()`. El `result`
  retenido sí es del producto (el arranque retiene el pool que usó); sacarlo es una línea
  (`del result`), fuera de alcance: va a riesgos.

### Comandos

Con `SHA=b4f7e5905e2aac755f871849a296d202a3e72840 BASE=ac4993b7`, `PY` el python del venv y
`export PATH=<venv>/bin:$PATH`:

```bash
$PY docs/pm/herramientas/chequeo-6.py $BASE $SHA        # producto +218/−54, historia vacía, avisos: 2 (de lo integrado)
$PY scripts/testing/anclas_perdidas.py $SHA             # perdida 0/0
scripts/testing/sabotajes/conexiones1_producto.sh $SHA  # 11 BIEN, rc=0
scripts/testing/sabotajes/conexiones1_nokey.sh $SHA     # 4 BIEN, rc=0
# en un worktree del SHA:
git apply --check -v scripts/testing/conexiones1_tests.diff                  # rc=0
scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_creditos.py     # «pierden: 0», rc=0 (en la base: «perdidos 10», rc=1)
PG=<url pg16> PUERTO=8883 scripts/testing/sabotajes/cobro_corte1.sh $SHA    # 87 ROJO, «sabotajes con falla: 0»
scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_medir.py --pico 60 --lento 30 --cuota-de-produccion
```

### Lo que ya corrí, sobre `b4f7e590`

| Puerta | rc | Salida |
|---|---|---|
| `chequeo-6` | 0 | abajo, entero |
| `anclas_perdidas` SHA | 0 | 112 guiones, 2706 anclas, perdida 0/0, no medido 5, sin ancla 6 |
| `anclas_perdidas` base | 0 | 110 guiones, 2664 anclas, 1 perdida de una línea y 4 de varias (son de la base) |
| `git apply --check` | 0 | «Checking patch tests/test_conexiones1.py...» |
| `conexiones1_producto.sh` | 0 | 11 BIEN (tabla abajo), 138 s |
| `conexiones1_nokey.sh` | 0 | 4 BIEN, 220 s |
| `conexiones1_creditos.py` | 0 | «suelta la conexión en _billing_vigente: True», «pierden: 0; no valen: 0; sin carrera: 0» |
| suite completa, base limpia + diff | 0 | `6251 passed, 110 skipped, 3 xfailed, 109 warnings in 1380.05s (0:23:00)` |
| `GEMINI_API_KEY= e2e_maria.sh` | 0 | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» (antes, 3 `curl: (7)` de la espera) |
| `cobro_corte1.sh` (PG16) | 0 | 87 ROJO, 0 ROTO, PATRÓN o MAL, «BASE \| en verde», «BASE \| la pantalla en verde», «BASE \| el lock en verde», «sabotajes con falla: 0», 4710 s |
| `limpieza1.sh` | 0 | `ROJO \| el job con continue-on-error: dice «la CI puede esconder el resultado de la suite: ['continue-on-error: true']»`, «sabotajes con falla: 0» |
| `cobro_mp1.sh` (sólo D, sobre `709b3a3e`) | 0 | «BASE \| la carrera de D en Postgres, en verde», dos FALLA esperadas |

`chequeo-6 ac4993b7..b4f7e590`, entero:

```
chequeo-6 ac4993b7..b4f7e5905e2aac755f871849a296d202a3e72840: avisos para mirar, no un veredicto
producto +218/−54
  AVISO producto suma 164 líneas netas: el informe dice por qué (§6: más de 20)
arnés +872/−95
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12289 → 12294
  proyecto_maria/routers/admin_router.py: 403 → 465
  proyecto_maria/services/billing_service.py: 418 → 420
  proyecto_maria/static/v2/paises_maria.js: 288 → 295
  AVISO creció una función de más de 150: proyecto_maria/static/v2/paises_maria.js:2 <anónima> 286 → 293, 2 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/catalogo.js: 404 → 405
  proyecto_maria/static/v2/screens/clientes.js: 2219 → 2224
avisos: 2
```

Los dos AVISO quedan: `admin_router.py`, `paises_maria.js`, `catalogo.js` y `clientes.js` no son
míos (ADMIN-USUARIOS-1, CATALOGO-PAIS-2). Contra `44e3b0ba..HEAD`: `producto +47/−42`, `arnés
+384/−70`, historia vacía, `main.py 12287 → 12294`, `billing_service.py 422 → 420`, `avisos: 0`.

`conexiones1_producto.sh`:

| Corrida | Resultado |
|---|---|
| sin sabotaje | 10 passed |
| manual lee el cuerpo antes del 402 | 1 failed (el de la cuenta que no puede cargar) |
| manual no mira el tope antes del cuerpo | 1 failed (el mismo) |
| `_billing_vigente` no suelta | 6 failed |
| sugerir no suelta antes de Gemini | 2 failed |
| analyze no suelta antes de leer el archivo | 3 failed |
| soltar sin try | 3 failed, con «conexión caída» |
| rollback en vez de close | 1 failed, con «MissingGreenlet» |
| créditos sin sabotaje | salida 0, «pierden: 0; no valen: 0; sin carrera: 0» |
| manual con el cupo sin candado (D188) | salida 1, «PIERDE \| usuario, carrera» |
| el tope de la dependencia vence créditos | salida 1, «PIERDE \| usuario, carrera» |

`conexiones1_nokey.sh`:

| Corrida | Resultado |
|---|---|
| sin sabotaje | salida 0, con las 4 líneas de candados (orden 1 y orden 2 de `_cuenta_con_suscripciones: FOR NO KEY UPDATE OF users \| FOR UPDATE` y de `_cuenta_bloqueada: FOR NO KEY UPDATE OF users \| FOR NO KEY UPDATE OF organizations`); «deadlocks: 0; rondas sin armar: 0; filas MAL: 0» |
| sin key_share ni of= | salida 1, «deadlocks: 3 … filas MAL: 2» |
| key_share sin of= | salida 1, «FOR NO KEY UPDATE \| FOR UPDATE \| MAL» (el segundo sólo puede venir de la cache) |
| suscripciones con FOR UPDATE | salida 1, deadlock en recarga + cancelar y en recarga + reactivar, «filas MAL: 2» |

El `FOR UPDATE` de la org en `_cuenta_con_suscripciones` queda a propósito: es la fila que se cambia.

### Mediciones, sobre `b4f7e590`

Medidor (`medir_sin_cuota` rc=0 505 s, `medir_cuota` rc=0 506 s): cuánto espera la otra cuenta en cada
pico de 60 pedidos lentos de una cuenta. En los cinco picos, 0 × 500 para la otra cuenta.

| pico | sin cuota | con cuota | códigos de la cuenta lenta, sin cuota | con cuota |
|---|---|---|---|---|
| bcrypt (login) | 3,82 s | 3,96 s | | |
| gemini (sugerir) | 0,38 s | 0,44 s | | |
| pdf | 0,04 s | 0,05 s | 422 × 16, 504 × 44 | 422 × 16, 429 × 25, 504 × 19 |
| excel (analyze) | 0,11 s | 0,11 s | 504 × 60 | 504 × 60 |
| cuerpo manual | 0,03 s | 0,04 s | 404 × 60 | 404 × 60 |

- Cuerpo manual: los 60 esperaban el cuerpo a la vez «con 0 conexiones tomadas»; llegaron en 0,88 s
  sin cuota y 0,93 s con cuota.
- `corte_cuerpo_a_medias` y `corte_manual_a_medias`: `{400: 15}`, sin y con cuota.
- En el log: Traceback, QueuePool limit, CancelledError y «Exception in ASGI application» en 0; close
  empezados = terminados = 3898; api_logs 826.
- `cuerpo` rc=0 5 s: 1 × 100 MB y 4 × 100 MB de G → 402 en ≤ 0,057 s, con 3–4 MB enviados al 402,
  «retenidas 0», RSS 158,7 → 159,9 MB; «medición válida».
- `natural` rc=1 68 s: «rondas con deadlock: 0, recargas perdidas: 0, cuentas mal: 19», las 19 en
  renovación + guardado (D205). `renovacion` rc=1 8 s: «cuentas mal: 4; rondas sin armar: 0».
  Los dos rc=1 son D205, esperado.

### Los criterios contra los casos

| Criterio | Dónde | Resultado |
|---|---|---|
| otra cuenta ≤ ~1 s y sin errores con 60 lentos, en sugerir, PDF, analyze y manual | medidor con la cuota; `test_la_espera_no_retiene_conexiones` (`RUTAS`) | ≤ 0,44 s, 0 × 500 (login 3,96 s, D180); el caso está verde y se pone rojo con «no suelta» |
| la impaga recibe «falta pagar» sin que se lea el pedido (4×100 de G) | `conexiones1_cuerpo.py`; `test_cuenta_que_no_puede_cargar_no_lee_el_cuerpo` | 4 × 402 en ≤ 0,057 s con ≤ 4 MB enviados, «retenidas 0», «lecturas de cuerpo en la ronda 0»; dos sabotajes rojos |
| recarga + alta con créditos vencidos: 0 perdidas (D188) | `conexiones1_creditos.py` | base perdidos 10, SHA 0; dos sabotajes rojos |
| corte a mitad del cuerpo: 400, sin ERROR ni 500 | fila `("body", …, _cortar_a_mitad, manual, 400)`; fase `corte_manual_a_medias` | `{400: 15}` sin y con cuota, Traceback 0, 500 0 |
| cada commit nuevo que suelta tiene su caso con la base caída (D202) | `test_la_base_caida_al_soltarla_no_corta_el_pedido` (`SUELTAN`: sugerir, analyze, manual) | verde; «soltar sin try» lo pone rojo |
| D205 sigue «cuenta mal» | `conexiones1_natural.py`, `conexiones1_renovacion.py` | renovación «cuentas mal: 4; rondas sin armar: 0», rc=1; natural 19 mal (10 prueba vencida, 9 active fuera de gracia), 0 perdidas, rc=1 |
| recarga + cancelar y recarga + reactivar | `conexiones1_pares.py` | 0 deadlocks; rojo con «suscripciones con FOR UPDATE» |
| SQL de cada candado con la cache caliente, en los dos órdenes | `conexiones1_pares.py` | las 4 líneas, exigidas por `nokey.sh` |
| `creditos.py` no fija `GEMINI_API_KEY` | `1235ac4f` | `grep -c GEMINI scripts/testing/conexiones1_creditos.py` da 0 |

### Líneas borradas en pruebas de plata, con su porqué

- `test_cobro_corte1.py:593`: la fila `require_active_billing` del 401 sin sesión pasa a
  `require_cupo_del_plan`, porque la dependencia vieja ya no existe. Rojo con la nueva devolviendo
  `None`: `{'require_cupo_del_plan': None} != {'require_cupo_del_plan': 401}`.
- `test_maria1b_controles.py:36-47`: se van el `SimpleNamespace`, el override de
  `require_active_billing` y su `pop`; el override de un nombre que ya no existe da AttributeError.
- `test_prelaunch_block2.py` y `block3.py`: sólo docstrings y comentarios que nombraban la
  dependencia vieja.
- `cobro_corte1.sh`: salen el `ACTIVA=…` y su `case`, y el bucle pasa a `vigente bloqueada maria`. El
  paso «activa» saboteaba `require_active_billing`, que se borró; lo que cuidaba lo cubre «vigente».
  Las 79 líneas de sabotaje de los otros pasos son iguales en `ca50916` y en el SHA.
- **Cuenta de ROJO:** la última aceptada, `ca50916`, dio 88; sobre `b4f7e590`, 87. Se
  esperaba 87: sale uno, el del paso «activa».

### Hallazgos

| Agente | Modelo, esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| adversario | Sonnet, alto | H3 (el multipart se lee antes de las dependencias); `key_share` no entra en la clave de la cache de SQL; 108 passed con PG16 | H3 a riesgos (previo); la cache es la razón del `of=`, y la cubre «key_share sin of=» |
| adversario | Opus, alto | #1 medio: una cuenta al tope recibe 404/400 en la carga manual en vez de 402 | arreglado en `5cc054b0`, casos en `0b1f02b0`; rojo con «manual no mira el tope» |
| | | #2 bajo, previo: MissingGreenlet en `_vencer_y_guardar` | riesgos |
| | | #3: H3 | riesgos |
| adversario | Sonnet, alto | sin defectos, 7200 casos, 0 diferencias; bajo: el 400 sale antes del 402 | riesgos |
| `/security-review` | Sonnet | nada por encima del 80 %; dos menores | riesgos (el error que se traga `_soltar_conexion`, la org con FOR UPDATE) |
| `/code-review high` | Opus | 7 nits | arreglados o contestados antes de `b4f7e590`; el 401 de `require_cupo_del_plan` salió de ahí (`5460fb94`) |

Los adversarios corrieron con Postgres 16 local. Que lo hicieran sin red y con `GEMINI_API_KEY`
vacía lo dicen su pedido y su informe; no lo verifiqué por fuera.

### Qué no se corrió

- La base caída al soltar en generar, exportar, confirmar y procesar: sólo en sugerir, analyze y
  manual, que son los commits nuevos (D202).
- `cobro_mp1.sh` entero: sólo el sabotaje D, sobre `709b3a3e`, no sobre `b4f7e590`.
- Los sabotajes de otras piezas de la tanda (son tuyos al publicar).
- La CI no corre `tests/test_conexiones1.py`: está fuera de git.

### Riesgos

- **El 500 por clave foránea** en alta contra borrar cliente: escrito, sin arreglar.
- **H2 y H3**, previos: el multipart se lee antes de las dependencias de cobro; el 400 de un cuerpo
  roto sale antes del 402 y sin `operacion_id`.
- `_soltar_conexion` se traga el error del commit: deja un `warning` y cierra. Hoy, antes de soltar
  no hay nada sin confirmar; si una ruta futura escribe antes, eso se pierde en silencio.
- `_vencer_y_guardar` sigue sin candado en las rutas que no son la carga manual, y con el
  MissingGreenlet previo.
- La org con FOR UPDATE en `_cuenta_con_suscripciones`, a propósito.
- `close_db` con una tarea de log viva devuelve una conexión al pool descartado: es el camino del
  intermitente, en el apagado.
- El `result` del lifespan (`main.py` ~1749) retiene el pool del arranque mientras vive la app.
- Login con 60 pedidos lentos: la otra cuenta espera 3,96 s (base 3,68 s). Es el pool que toma bcrypt
  (D180), fuera de esta pieza.
- Los casos están fuera de git y la CI no los corre.

Archivos de producto tocados: `proyecto_maria/main.py`, `proyecto_maria/services/billing_service.py`,
`CHANGELOG.md`.

Ahora sigo con lo que marques. **Próxima D: D232.**

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica. CONEXIONES-1-PRODUCTO (con NOKEY) entregada: puertas sobre b4f7e590, informe en el commit docs encima de 1c5924dc; espero veredicto y no hay pieza marcada «apenas entregues». Reglas de Emi: me pide sólo la PM principal (session_01B7FVQspcEHF7PqNv797wNM); nada se publica sin su «dale» para el SHA; nunca main; sin secretos; tests/test_conexiones1.py nunca va a git (su copia es scripts/testing/conexiones1_tests.diff). Próxima D: D232.
