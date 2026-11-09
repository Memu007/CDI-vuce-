# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## INTEGRAR-1: el merge está subido; D140, D141 y D143 las decidís vos

Base común `30533fe`. Padres: mi rama en `0d829b8` (trae la tuya) y `claude/dev-maria` en `4db641b`.

| Qué | SHA |
|---|---|
| Merge, resolución de los cinco choques | `b9db0ad` |
| Pruebas y patrones de sabotaje al día con el merge (11 archivos, +51/−25, sin producto) | `68e77ed` (mismo árbol que `80c1afb`, donde corrí los arneses) |
| Mis pruebas de NOMBRES-1 con IP propia (1 archivo de pruebas) | `39a9f80` (mismo árbol que `a4c97b4`, donde corrí la suite) |
| El sabotaje del login de NOMBRES-1 ancla en la búsqueda del merge | `0e51313` |
| `cobro_corte1`: dos anclas del guardado y el surrogate de Postgres al día con el merge (2 archivos de pruebas) | `6d13b43` |
| Este informe | el commit de arriba |

En D140 el merge quedó con (a), lo que ya estaba aceptado en COBRO-MP-3; por eso el único rojo de la suite es el caso de MARIA que espera (b).

El merge es contra `4db641b`, como dice la tarea. `claude/dev-maria` siguió después (`0231eee`, con RESET-3, AVISOS-2b y SMOKE-1: 12 archivos, +394/−136). Eso no está en el merge; lo traigo cuando lo aceptes y me lo pidas.

## Decisiones

**D140. Webhook de MP sin `MP_WEBHOOK_SECRET` en desarrollo.** Choque de fondo entre dos piezas aceptadas.
- (a) Rechaza en cualquier entorno. Es COBRO-MP-3 (mía, `1f50328`): «sin firma no se atiende». Es lo que dejé en el merge (`main.py:11481`, `if not MP_WEBHOOK_SECRET: return False`).
- (b) Acepta en desarrollo explícito y rechaza fuera. Es ENTORNO-1 (MARIA, `118447a`): `return _es_desarrollo()`.

Recomiendo (a). El webhook cambia el plan de una cuenta: una puerta de desarrollo ahí es la única de ENTORNO-1 que mueve plata si `ENVIRONMENT` queda mal puesto en un despliegue. Las pruebas firman con un secreto de prueba (`tests/mp_firma.py`), así que en desarrollo no hace falta la puerta.
Con (a) hay que cambiar dos cosas de MARIA, que hoy dan rojo sobre el merge: `tests/test_entorno1.py:96` (`webhook_sin_secreto` espera «abierta» en desarrollo) y los dos sabotajes de `scripts/testing/sabotajes/entorno1.sh` que la nombran (líneas 23-26 y 44-46). Con (b) se vuelve a abrir lo que cerró COBRO-MP-3 y hay que cambiar sus casos.
El cambio de esos casos de MARIA no está subido: lo hago cuando decidas.

**D141. Una operación movida a otro cliente conserva su presupuesto compartido con los datos del cliente viejo.** No es del merge: está en las dos ramas (las dos le cambian `client_id` a una operación existente, `0d829b8:main.py:7600` y `4db641b:main.py:8095`, `client_id=client_id` dentro de `campos`), y la revisión adversarial lo encontró.
- Borrar un cliente quedó sumado: sus operaciones quedan «Sin cliente» (mía, COBRO-CORTE-1, para que regenerar no vuelva a contar) y sus presupuestos compartidos se borran (MARIA, DATOS-1, D32 (a), porque la copia tiene datos del cliente).
- Pero guardar una operación existente desde otro cliente le cambia `client_id` (`main.py:8115-8129`). Su `PublicQuote` queda con la copia del cliente viejo, y al borrar ese cliente no se borra, porque el borrado busca por el `client_id` actual. El aviso de `clientes.js:1821` («dejan de andar los links de presupuestos que compartiste») queda falso para ese presupuesto.
- (a) Al guardar una operación con otro cliente, borrar su presupuesto compartido (el link deja de andar, como al borrar).
- (b) Dejarlo y corregir el aviso.
- (c) Dejarlo como está y anotarlo como límite conocido.

Recomiendo (a): es la misma regla de DATOS-1 (la copia del cliente se va con el cliente) aplicada al único otro camino por el que la operación deja de ser suya. Es una pieza nueva de datos, con su caso y su sabotaje: no la meto en el merge. La decisión es si va a la cola y con qué opción.

**D143. Al abrir la app, la recuperación del borrador te saca de la pantalla a la que fuiste.** No es del merge: es mía, de ORDEN-1 (`36aba87`), y está igual en `0d829b8`, en `4db641b` y en el merge. La encontró el arnés `cliente1`, que da rojo sin sabotaje en los tres (`locator.click: Timeout 30000ms exceeded`).
- El arranque de `app_v2.js` espera al usuario hasta 4 s (`Promise.race([usuarioListo, espera(4000)])`), recupera el borrador y hace `goTo('review')` o `goTo('upload')`. Si en ese rato la usuaria ya fue a Clientes, la devuelve a la carga.
- Con el arnés esperando a que haya una pantalla activa antes de navegar, `cliente1` da verde sobre `80c1afb`. Buscando el primer commit malo da `36aba87`.
- (a) Pieza de producto: el arranque sólo va a la carga o a la revisión si la usuaria todavía no fue a ninguna pantalla, con su caso y su sabotaje.
- (b) Cambiar el arnés para que espere la primera pantalla. Esconde lo que le pasa a la usuaria.
- (c) Las dos.

Recomiendo (a): el rojo describe algo que le pasa a quien abre la app y va rápido a Clientes. No lo arreglo dentro de INTEGRAR-1.

## Lo que se sumó sin decisión

| Choque | Cómo quedó |
|---|---|
| Borrar un cliente | Las dos: operaciones «Sin cliente» y sin detalle, y se borran sus presupuestos compartidos. Responde `operaciones_sin_cliente`. El texto de `clientes.js:1821` dice las dos cosas |
| Registro | Las dos: tope por IP (más de 5 por hora o 20 por día, `main.py:3387`) y `_exigir_username_libre` (`main.py:3392`, y en crear estudio `main.py:10659`) |
| `finalize.js`, guardado al historial | Sin pérdida. Lo que `4db641b` tiene de más en `generateMaria` (la rama `detail.message` y `err.motivo`) es código mío viejo (`704df60`) que saqué en `efaef2b` junto con el 409, que ya no existe. El toast del historial sigue en `finalize.js:1340` |
| `file_security.py` | Las dos: `import logging` y `import math`, y `PDF_DEMASIADO_PESADO` |
| `CHANGELOG.md` | Las entradas de las dos ramas, por fecha |
| `tests/conftest.py` | Cambia sólo por la resolución: `cuenta_de_prueba` con try/finally, `auth_override` la usa, y el limitador apagado de MARIA |

## Los 429 de la suite eran de mis pruebas de NOMBRES-1

Sobre `80c1afb` la suite dio 10 rojos, los mismos en dos corridas: D140 y nueve con `assert 429 == 200` (los 8 de `test_punta_a_punta1.py` y `test_prelaunch_block3.py::TestJWTSecretUnificado::test_token_generado_por_login_es_verificable_por_datos_del_token`). El log dice `429 login bloqueado: ip=testclient`.

Causa, medida leyendo `limites_auth` después de cada prueba: `test_nombres1.py::test_dos_cuentas_viejas_que_difieren_en_mayusculas_siguen_entrando` (mía, sólo de mi rama) deja tres logins fallidos en la IP `testclient`, que comparten todas las pruebas; los dos 401 de `test_prelaunch_block1.py` suman el cuarto y el quinto, y la IP queda bloqueada 15 minutos para las que vienen después. Es un choque que sólo existe en el merge: el bloqueo guardado en `limites_auth` es de la rama de MARIA (`1f0bfb0`, ABUSO-2) y no está en `0d829b8`; esa prueba es de mi rama y no está en `4db641b`.

Arreglo (`a4c97b4`, sólo pruebas): esa prueba entra desde una IP propia del rango de documentación (`2001:db8::…`, por `X-Forwarded-For`) y borra sus intentos al terminar. No cambia ningún assert.

| Orden mínimo (`test_nombres1`, `test_prelaunch_block1`, `test_prelaunch_block3`, `test_punta_a_punta1`, `-p no:randomly`) | Resultado |
|---|---|
| `80c1afb`, sin el arreglo | `9 failed, 123 passed, 2 xfailed in 22.20s` |
| `a4c97b4`, con el arreglo | `132 passed, 2 xfailed in 27.57s` |

`test_excel2d.py` (`[9995 combinadas en 19 990 filas]`) dio una vez `assert 0.5157383030000346 < 0.5`, con los arneses corriendo en paralelo; pasó en las otras dos suites y solo pasó (`7 passed in 3.12s`). Lo informo como carga del contenedor, no lo repetí para buscar verde.

Suite completa sobre `a4c97b4`: `1 failed, 5906 passed, 110 skipped, 3 xfailed in 1227.54s (0:20:27)`. El único rojo es el de D140: `test_entorno1.py::test_puerta_abierta_en_desarrollo[webhook_sin_secreto]`, con `AssertionError: webhook_sin_secreto no queda abierta: {'development': 'cerrada', 'test': 'cerrada', 'testing': 'cerrada'}`.

## Arneses de las dos ramas

Corrí todos los sabotajes (`scripts/testing/sabotajes/*.sh` y `scripts/testing/sabotaje_*.sh`) uno por uno sobre `80c1afb`, que tiene el mismo árbol que `68e77ed`. `nombres1.sh` lo corrí aparte sobre `0e51313`.

El único rojo que causa el merge es el de `cobro_corte1`, y es de pruebas. Para los demás corrí el mismo script, o busqué su patrón, en los dos padres.

| Arnés | Resultado en el merge | En los padres | Qué es |
|---|---|---|---|
| `sabotaje_maria1d`, `maria3`, `maria5`, `maria7`, `maria8`, `maria9`, `sabotaje_valor1` | `PATRON NO ENCONTRADO (0 veces)` | 0 veces en `4db641b` y en `0d829b8`; los scripts no cambian entre `4db641b` y `80c1afb` | Patrones que quedaron viejos en la rama de MARIA (por ejemplo `maria1d`: el endpoint cambió en `67d5688`) |
| `sabotaje_valor1b` | `PATRON NO ENCONTRADO (2 veces)` | 2 veces en `4db641b`; 1 en `0d829b8` | Previo de la rama de MARIA |
| `abuso1`, `catalogolargo1` | `ROTO`: `el sabotaje no encontró su patrón`. En `abuso1` es uno solo, «vencido el bloqueo, la cuenta sigue»: busca `nueva = case((vencido, tope), …)` y el producto dice `nueva = _T.c.cuenta + 1 if exacta else case(...)` desde ABUSO-2; los otros dan ROJO | 0 veces en `4db641b`; los dos son sólo de MARIA | Patrones viejos de la rama de MARIA |
| `sabotaje_sufijos1` | `FALLA  codigo_vacio_cargado: quedó verde` | Igual en `4db641b` | Previo de la rama de MARIA |
| `sabotaje_subitems1` | `FALLA  forma_500: quedó verde` y `FALLA  controles_500: quedó verde` | Igual en `4db641b`: `41 passed, 2 xfailed`, `SABOTAJES CON FALLA: 2` | Previo de la rama de MARIA |
| `cobro_corte1` | rc=1. Dos `ROTO`: «v2: generar guarda con la carga de la pantalla» y «v2: el guardado toma los valores de la pantalla al responder», `el sabotaje no encontró su patrón`. Y la base del lock: «el lock ya está en rojo sin sabotaje: no se puede medir nada», por «id con surrogate al guardar: una operación nueva y contada (400, 0, 0 operaciones)». Los otros dan ROJO | Los dos ROTO anclan en `saveOperationToHistory(items, data, carga, foto).catch(`, que está en `0d829b8`; en el merge sigue `.then(`. El 400 es la validación de MARIA, que ya espera `tests/test_cobro_corte1.py` | Del merge, sólo en pruebas. Arreglado en `6d13b43`. Sobre ese SHA, la base del lock sola (`cobro_corte1_postgres.py` en un PG16 propio) da `fallas: 0` con 18 OK, entre ellos «id con surrogate al guardar: rechazado sin contar (400, 0, 0 operaciones)». La corrida entera del arnés no entró antes del corte: va en «No corrido» |
| `cliente1` | «la prueba ya está en rojo sin sabotaje» | Igual en `0d829b8` y en `4db641b` | D143, mía |
| `aislamiento2` | rc=2: el runner lo llamó sin argumento (pide `prueba`, `ataque` o `todo`) | | Falta correrlo con Postgres; va en «No corrido» |
| `nombres1` (sobre `0e51313`) | base en verde (`40 passed`), siete ROJO, `sabotajes con falla: 0` | | Verde |

Verdes (rc=0): `sabotaje_catalogo_ncm1`, `maria1a`, `maria1c`, `maria2`, `maria2b`, `maria4`, `maria5d`, `maria7_devolucion`, `sabotaje_org1`, `sabotaje_separadores1`, `separadores1b`, `separadores1c`, `separadores1d`, `valor1c`, `abuso2`, `admin1`, `admin2`, `avisos1`, `avisos2`, `backup1a`, `catalogo_largo2`, `cliente1b`, `cliente1c`.

Los patrones viejos de MARIA no los toqué: son scripts de su rama y no los cambia el merge. Los anoto para que la PM decida si vuelven a ella.

`test_rendimiento1c.py` dio una vez 2 rojos (`no such table: users`) en el worktree del merge antes de `68e77ed`. `68e77ed` envuelve el subproceso con `cuenta_de_prueba("a")` y `cuenta_de_prueba("b")`. Con eso, solo: `15 passed in 49.65s`; en la suite sobre `a4c97b4` pasa.

## Revisión adversarial

Un revisor, `adversario-opus-alto` (Opus, esfuerzo alto), sobre `5068254`. Corrió la suite ahí: `87 failed, 3559 passed, 34 skipped in 991.75s`. Los que arreglé los reproduje antes (rojo en `5068254`, verde en `80c1afb`); el 11 lo verifiqué leyendo el código de los dos padres y del merge, sin correrlo.

| # | Hallazgo | Cómo quedó |
|---|---|---|
| 1 | Un presupuesto compartido sigue andando después de borrar el cliente, si la operación se había movido a otro | D141 |
| 2 | `test_cobro_corte1`: 4 casos «al confirmar» fallan porque el `db.commit` de `auth/dependencies.py:159` (MARIA) también cae en el commit que la prueba hace fallar | Arreglado en `80c1afb` (sólo prueba) |
| 3 | `surrogate` al guardar: la rama de MARIA ya rechaza con 400 «Hay un carácter que no se puede guardar.» y mi caso esperaba 200 | Me quedo con el 400 (más estricto, no cobra). Supuesto reversible: el caso lo espera así |
| 4 | `test_despacho1c`: 55 rojos porque el arnés ponía el cliente por un camino que el merge ya no usa | Arreglado: el arnés usa `CDI.state.clienteActivo` |
| 5 | `buildMariaRequest` y `fotoDeLaPantalla` quedan fuera del `try` de `generateMaria` | Previo (está igual en las dos ramas). Va abajo |
| 6 | `test_avisos1_seguro` arma `generateMaria` con stubs y le faltaban `fotoDeLaPantalla`, `pedidaMientrasOtra` y `lastValidation`, que `generateMaria` usa en el merge | Arreglado en `80c1afb`: el arnés los agrega |
| 7 | `test_datos1` y `test_avisos2` daban 401 en el merge | Arreglado: usan `cuenta_de_prueba` y `auth_override` |
| 8 | `test_admin_bootstrap`: en el merge cambiar el email pide la contraseña actual | Arreglado: la cuenta tiene un hash real y la prueba manda `current_password` |
| 9 | `test_nombres1` apagaba `login_attempts`, que en el merge ya no es el limitador | Arreglado: se sacó ese `monkeypatch` |
| 10 | Webhook sin secreto en desarrollo | D140 |
| 11 | `finalize.js`: un 402 de una carga ajena, `lastValidation`, y `total_items` después del borrado | Ninguno es del merge. El 402: `CDI.api` lo tira con la razón en `err.message` (mía, `efaef2b`; MARIA usa `err.motivo` de mi `704df60` viejo), y el `catch` de `generateMaria` la muestra aunque la carga ya no esté en pantalla; es la cuenta la que no paga, así que el texto es cierto. Igual en `0d829b8`. `lastValidation`: lo saqué de `onLeave` en VALIDACION-1 (`db31e0e`), atado a `lastValidationPedido`. `total_items`: una operación que quedó «Sin cliente» conserva su `total_items` sin detalle; las métricas filtran por `client_id`, así que no la cuentan. Igual en `0d829b8` (COBRO-CORTE-1) |
| 12 | `logger` sin definir en `main.py:8160` | Previo: pyflakes lo marca en `0d829b8:7639` y en `4db641b:8137` |

Lo que el revisor confirmó como bien: el webhook sin firma da 401 (`main.py:11481` y `11530`); el registro tiene las dos conductas (`3392`, `10659-10660`); no se perdió código en silencio al resolver; la única advertencia nueva de pyflakes es `uuid` importado dos veces.

## Arreglos de pruebas sobre el merge (`80c1afb`, subido como `68e77ed`, sin producto)

| Archivo | Qué cambió |
|---|---|
| `tests/test_cobro_corte1.py` | El caso de `surrogate` al guardar espera 400 y 0 operaciones. El commit que falla sólo falla si lo llama `main.py`: los commits de otros módulos pasan |
| `tests/test_rendimiento1c.py`, `tests/test_rendimiento1d.py` | El `subprocess` corre con `cuenta_de_prueba("a")` y `cuenta_de_prueba("b")`, porque en el merge la ruta pide sesión |
| `tests/test_datos1.py`, `tests/test_avisos2.py`, `tests/test_avisos1_seguro.py`, `tests/test_admin_bootstrap.py`, `tests/test_nombres1.py` | Como dicen las filas 6 a 9 de arriba |
| `scripts/testing/sabotaje_org1.sh`, `scripts/testing/sabotaje_separadores1.sh` | El patrón sigue a `billing_service.plan_de_la_cuenta(org)["users"]` |
| `tests/despacho1c_pantalla.js` | `getClienteActivo` y `setClienteActivo` usan `CDI.state.clienteActivo`; la falla sintética va en el getter de `banco_bcra` |

Sobre `a4c97b4`, `nombres1.sh` dio ROTO en «el login prueba exacto y si no hay, sin distinguir mayúsculas»: `patrón no encontrado una sola vez (0)`. El login del merge viene de ABUSO-2 (MARIA), que sacó el comentario que usaba de ancla. En `0e51313` (sólo `scripts/testing/sabotajes/nombres1.sh`, +2/−4) el ancla es la línea siguiente del merge, `if not user and "@" in (username or ""):`. El sabotaje es el mismo. Da `sabotajes con falla: 0`, con los siete ROJO.

El de `test_cobro_corte1` mira quién llama al commit (`sys._getframe(1)`): es frágil si el commit se mueve de archivo, pero es sólo de pruebas y falla en rojo, no en verde.

## Previos (están igual en una de las ramas, no los trae el merge)

Los arneses previos están en «Arneses de las dos ramas».

| Qué | Dónde |
|---|---|
| `logger` sin definir | `main.py:8160` |
| `uuid` importado dos veces | pyflakes, del merge de imports; no cambia conducta |
| `buildMariaRequest` y `fotoDeLaPantalla` fuera del `try` | `finalize.js:716-717` |
| `/api/organizations/create` sin tope por IP | el tope del registro no lo cubre |
| Chequeo sin mayúsculas y unicidad de la base pueden correr a la vez | carrera conocida de NOMBRES-1 |
| `tests/conftest.py` pone `ENVIRONMENT=testing` | no lo toco |
| El repo es shallow | `git log` corta antes de la base en algunos archivos |

## chequeo-6

El merge no suma avisos propios. Contra `4db641b` (lo que mi lado agrega encima de MARIA) da los mismos 7 avisos que mi rama sola contra la base (`30533fe..0d829b8`), y el neto de producto baja de 292 a 288. Esas líneas son las de mi rama (que trae la tuya), ya aceptadas pieza por pieza; el merge no agrega producto nuevo fuera de la resolución de los cinco choques. Los avisos de función y de comentario son los de esas piezas, ya informados en su entrega.

Contra `0d829b8` da 109 avisos y +3825/−1077: es la rama de MARIA entera, no lo que hice yo, y no la copio acá.

<details><summary>chequeo-6 4db641b..0e51313, el SHA subido (entero)</summary>

```
chequeo-6 4db641b..0e51313: avisos para mirar, no un veredicto
producto +727/−439
  AVISO producto suma 288 líneas netas: el informe dice por qué (§6: más de 20)
arnés +5761/−1018
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/auth/roles.py: 27 → 26
  proyecto_maria/database/models.py: 614 → 617
  proyecto_maria/main.py: 12078 → 12213
  AVISO creció una función de más de 150: proyecto_maria/main.py:5590 try_extract_with_mapping 309 → 312, 3 en su propio cuerpo (§6: lo nuevo va aparte)
  AVISO comentario nuevo de 4 líneas: proyecto_maria/main.py:2143 (§6: una o dos)
  proyecto_maria/security/file_security.py: 693 → 798
  AVISO comentario nuevo de 4 líneas: proyecto_maria/security/file_security.py:363 (§6: una o dos)
  proyecto_maria/services/billing_service.py: 407 → 418
  proyecto_maria/static/v2/app_v2.js: 1199 → 1201
  proyecto_maria/static/v2/screens/clientes.js: 2211 → 2211
  proyecto_maria/static/v2/screens/finalize.js: 1444 → 1477
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/finalize.js:9 <anónima> 1436 → 1469, 6 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/profile.js: 613 → 613
  proyecto_maria/static/v2/screens/upload.js: 718 → 718
  AVISO función nueva de 96 líneas: scripts/testing/conexiones1_sonda.py:59 _instalar (§6: ~60)
  AVISO función nueva de 67 líneas: scripts/testing/pantalla_cobro_corte1.js:33 casosTardios (§6: ~60)
avisos: 7
```

</details>

<details><summary>chequeo-6 30533fe..0d829b8, mi rama sola, para comparar (entero)</summary>

```
chequeo-6 30533fe..0d829b8: avisos para mirar, no un veredicto
producto +723/−431
  AVISO producto suma 292 líneas netas: el informe dice por qué (§6: más de 20)
arnés +5860/−669
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/auth/roles.py: 27 → 26
  proyecto_maria/database/models.py: 570 → 573
  proyecto_maria/main.py: 11237 → 11375
  AVISO creció una función de más de 150: proyecto_maria/main.py:5161 try_extract_with_mapping 309 → 312, 3 en su propio cuerpo (§6: lo nuevo va aparte)
  AVISO comentario nuevo de 4 líneas: proyecto_maria/main.py:1749 (§6: una o dos)
  proyecto_maria/security/file_security.py: 691 → 796
  AVISO comentario nuevo de 4 líneas: proyecto_maria/security/file_security.py:369 (§6: una o dos)
  proyecto_maria/services/billing_service.py: 412 → 423
  proyecto_maria/static/v2/app_v2.js: 1190 → 1192
  proyecto_maria/static/v2/screens/clientes.js: 1984 → 1984
  proyecto_maria/static/v2/screens/finalize.js: 1357 → 1391
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/finalize.js:9 <anónima> 1349 → 1383, 7 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/profile.js: 587 → 587
  proyecto_maria/static/v2/screens/upload.js: 718 → 718
  AVISO función nueva de 96 líneas: scripts/testing/conexiones1_sonda.py:59 _instalar (§6: ~60)
  AVISO función nueva de 67 líneas: scripts/testing/pantalla_cobro_corte1.js:33 casosTardios (§6: ~60)
avisos: 7
```

</details>

## Comandos para comprobarlo

Sobre lo subido (`0e51313`; el informe no cambia código):

```bash
git fetch origin claude/dev-tecnica && git checkout 0e51313
# D140: el merge quedó con (a); cada padre hace una cosa distinta
for s in 0e51313 0d829b8 4db641b; do git show $s:proyecto_maria/main.py | grep -A1 'if not MP_WEBHOOK_SECRET:' | tail -1; done
#   return False / return False / return _es_desarrollo()
# D141: las dos ramas le cambian client_id a una operación existente
git show 0d829b8:proyecto_maria/main.py | sed -n 7600p; git show 4db641b:proyecto_maria/main.py | sed -n 8095p
#   las dos:             client_id=client_id,
python -m pytest -q --no-cov --timeout=120 -p no:cacheprovider -W ignore
#   1 failed: test_entorno1.py::test_puerta_abierta_en_desarrollo[webhook_sin_secreto] (D140)
python -m pytest -q --no-cov -p no:randomly tests/test_nombres1.py tests/test_prelaunch_block1.py tests/test_prelaunch_block3.py tests/test_punta_a_punta1.py
#   132 passed, 2 xfailed
python docs/pm/herramientas/chequeo-6.py 4db641b 0e51313
#   avisos: 7, historia vacía, producto +727/−439
```

## No corrido

- Sabotajes que el corredor no alcanzó: lo cortó el límite de 30 minutos de las tareas en segundo plano, y no entraban antes del corte. `cobro_mp1` quedó a medias: hasta donde llegó, la base dio verde, 107 ROJO y ningún ROTO ni FALLA. Los otros 56 no se corrieron: `cobro_mp2`, `cobro_mp3`, `cobro_mp4`, `conexiones1`, `csrf1`, `csrf2`, `csrf3`, `datos1`, `despacho1a`, `despacho1b`, `despacho1c`, `despacho1d`, `destino1`, `disco1`, `email1`, `entorno1`, `entorno2`, `entorno3`, `entorno4`, `entradas1`, `entradas2`, `entradas3`, `entradas4`, `estudio1`, `estudio1b`, `excel1`, `excel2`, `excel2b`, `excel2c`, `excel2d`, `excel3`, `foco_cliente1`, `front422`, `guardar1`, `guardar2`, `limpieza1`, `maria1b`, `observabilidad1`, `orden1`, `orden1b`, `org1`, `org1b`, `pa1`, `permisos1`, `permisos2`, `punta_a_punta1`, `rendimiento1`, `rendimiento1b`, `rendimiento1c`, `rendimiento1d`, `reset1`, `seguro1`, `seguro2`, `sesion1`, `sufijos2`, `validacion1`. Entre ellos están los de las piezas que el merge tocó en los dos lados (`entorno1`, `datos1`, `csrf1`, `csrf2`, `csrf3`, `permisos2`, `validacion1`). D140 ya dice que `entorno1` va a dar rojo en sus dos sabotajes del webhook.
- `cobro_corte1.sh` entero sobre `6d13b43`: lo corté a los 30 minutos (la base y los sabotajes de pytest ya habían dado verde y ROJO). No llegó a los dos sabotajes de pantalla que estaban ROTO ni a los sabotajes del lock. Su patrón ahora aparece una vez en `finalize.js`.
- `aislamiento2.sh ataque` y `ataque_aislamiento.sh`: usan el Postgres compartido, que tenían ocupado los arneses de cobro. No los corrí.
- `smoke_friccion.sh`: no levanté el servidor para esta entrega.
- `/code-review` y `/security-review` sobre el merge: no los corrí en esta vuelta. La revisión adversarial es la de arriba.
- `claude/dev-maria` después de `4db641b` (`0231eee`): fuera del merge, como dice la tarea.

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. Dónde quedé al corte: INTEGRAR-1 entregada en 19036a2, sin aceptar (la PM la revisa después del corte). D140 (a): en la próxima vuelta cambio tests/test_entorno1.py y sabotajes/entorno1.sh, en commits separados. D141 y D143 son piezas para Emi: no las hago. No integro 0231eee hasta que la PM lo pida. Pendiente de INTEGRAR-1: los 56 arneses de «No corrido», cobro_mp1 entero y cobro_corte1.sh entero. Después, CONEXIONES-1 parte B, sin empezar. Corte 2026-11-09 05:00 UTC. Mis D van de la D140 a la D149, sin la D142; la próxima es la D144. Reglas de Emi: sólo la PM y Emi me piden, nada se publica sin su «dale» para el SHA, nunca main, sin secretos.
