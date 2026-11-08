# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## AISLAMIENTO-2 y LIMPIEZA-1, entregadas en la punta de `claude/dev-tecnica` (este commit, sólo el informe)

Las dos piezas estaban hechas desde octubre y salen ahora, después de
COBRO-MP-2+3. Antes de entregarlas pasé subagentes y `/code-review`, y
salieron seis commits de revisión. Todos son de pruebas, salvo uno que sólo
cambia un comentario. Las puertas corrieron sobre `c86f3ff`. Después viene
`c751c1a`, el merge de tu rama, que sólo trae `docs/pm/`.

### Resultado

- **AISLAMIENTO-2.**
  - No apareció ninguna fuga real. El ataque cubre operaciones, notas,
    presupuestos, estudios, organizaciones y admin: «Bloqueado: 47 · Fugas: 0
    · Sin probar: 0».
  - La prueba de admin ve WebSockets, rutas exactas sin barra y routers
    incluidos.
  - Hay un arreglo latente: un `roles` guardado como texto («administrador»)
    o como objeto (`{"admin": false}`) ya no da admin.
- **LIMPIEZA-1.**
  - La CI corre la suite entera, sin los 10 `--deselect`.
  - Se borra el camino de publicación a Google Cloud.
  - Ninguna cadena de conexión de la historia tiene una clave real.
  - `test_limpieza1.py` controla que nada de eso vuelva.

### Decisiones

- **D114: sigue abierta.** Es de COBRO-MP-2+3. En mi informe anterior la
  numeré D112, y vos la registraste como D114 (`PARA-DEV-2.md`). **Después de
  un 503 por el tope, Mercado Pago pudo haber aplicado el cambio, pero CDI no
  lo anota.**
  - **El caso:** a cancelar no le llega a tiempo la respuesta del PUT, pero
    Mercado Pago sí canceló. CDI deja `billing_status` y `mp_preapproval_id`
    como estaban.
  - **Si se reintenta, se concilia:** `_cancelar_suscripcion_mp` lee el
    estado, ve «cancelled» y sigue
    (`test_si_mp_ya_la_tenia_cancelada_cancelar_sigue`). El texto pide
    reintentar.
  - **Sin reintento:** no verifiqué qué muestra el perfil ni qué hace el
    corte.
  - **Opciones:**
    - (a) dejarlo como riesgo;
    - (b) una pieza aparte, que concilie con la próxima lectura o con el aviso
      de Mercado Pago.
  - **Recomiendo (b),** porque es plata.
- **D116: un usuario común se puede volver admin con su email.** Lo encontró
  el subagente Opus alto. Es de antes de estas piezas y coincide con lo que
  ya decía D43.
  - **El camino:**
    1. El usuario cambia su email con PUT `/api/user/profile` (`main.py`,
       cerca de la línea 1990), que no pide verificarlo. Pone un correo de
       `ADMIN_USERNAMES` que ninguna cuenta use.
    2. Al reiniciar, el arranque (`main.py`, cerca de la línea 1392) le
       guarda el rol «admin».
    3. El rol queda guardado, así que lo conserva aunque después se vacíe
       `ADMIN_USERNAMES`.
  - **El subagente lo reprodujo** en local, con SQLite y sin red:
    - «antes /api/dev/stats: 403»;
    - «PUT profile: 200»;
    - «roles tras reinicio: ['operador', 'admin']»;
    - «despues /api/dev/stats (ADMIN_USERNAMES vacio): 200».
  - **Yo lo reproduje hasta los roles,** con una prueba aparte que no quedó en
    el repo: «PUT profile: 200», «roles tras reinicio: ['operador',
    'admin']», «roles con ADMIN_USERNAMES vacio: ['operador', 'admin']». La
    parte de `/api/dev/stats` no la volví a correr.
  - **Opciones:**
    - (a) dejarlo como riesgo mientras `ADMIN_USERNAMES` tenga sólo correos
      de cuentas que ya existen;
    - (b) una pieza aparte de permisos: el arranque no da admin por email, o
      el email no cambia sin verificarlo.
  - **Recomiendo (b),** porque es una escalada de permisos. No la arreglé
    acá: es producto fuera de estas dos tareas.

Supuestos reversibles de AISLAMIENTO-2:

- Un texto que dice exactamente «admin» cuenta como el rol admin. Lo prueba
  `test_el_rol_admin_entero_entra[admin]`.
- Arreglé `require_role` aunque hoy ninguna ruta lo usa, porque tenía la
  misma falla.

Supuestos reversibles de LIMPIEZA-1:

- Borré también las cinco guías de Google Cloud.
- Cambié dos mensajes que decían Cloud Run (`preflight_env.sh` y
  `test-docker-local.sh`).
- Los `.md` y `.txt` que nombran Google Cloud quedan como están.

Te pido que en `.claude/skills/entregar/SKILL.md` saques «(cubre sólo
clientes y descargas)» de la línea del ataque. `.claude/` es tuyo y no lo
toqué.

### SHAs

| SHA | Qué |
|---|---|
| `73a570e` | Base de AISLAMIENTO-2: COBRO-MP-2 más tu merge |
| `c143abb` | AIS2, pruebas: el ataque cubre todo, admin con WebSockets y rutas exactas, roles como texto (rojo) |
| `58fc1c2` | AIS2, producto: `roles_de` y `_es_admin`, más CHANGELOG |
| `0c3c02a` | AIS2, sabotajes (`aislamiento2.sh`) |
| `16d53c6` | AIS2, sabotajes: dos nombres esperados mal escritos |
| `0f2f160` | Base de LIMPIEZA-1: AISLAMIENTO-2 integrada |
| `8b53a23` | LIM, pruebas (rojo): la CI no saca pruebas y no queda camino a Google Cloud |
| `cf89bf4` | LIM, pruebas: el run de una sola línea |
| `8747c4c` | LIM, producto: `ci.yml`, el borrado de Google Cloud y CHANGELOG |
| `e71291e` | LIM, pruebas: `PYTEST_ADDOPTS`, imágenes a `gcr.io` y sabotajes (`limpieza1.sh`) |
| `bcdbbb3` | LIM, pruebas: la prueba no se cuenta a sus propios sabotajes |
| `335d287` | Lo que ya estaba en origin: el informe de COBRO-MP-2+3 |
| `28bf57f` | Revisión, producto: el comentario de `roles_de` en dos líneas (sólo un comentario) |
| `9496ca8` | Revisión AIS2: la prueba de admin recorre también los routers incluidos |
| `31ba053` | Revisión AIS2: en el ataque, un 2xx es fuga, `sql` de SQLite con commit y el paso de admin sólo lee |
| `766d353` | Revisión LIM: la prueba ve filtros agrupados, opciones que no corren, operadores y `pytest.ini` |
| `dfee12c` | Revisión LIM: la suite y `addopts` sólo llevan opciones de una lista permitida |
| `c86f3ff` | Revisión: el ataque no confunde un corte con un bloqueo, y la prueba de la CI no se deja tapar |
| `c751c1a` | Merge de tu rama (`e097a54`). Fuera de `docs/pm/` no cambia nada |
| punta de la rama | Este informe |

**Archivos de producto tocados:**

- `proyecto_maria/auth/roles.py`;
- `proyecto_maria/main.py` (`_es_admin` y un import);
- `CHANGELOG.md`;
- `.github/workflows/ci.yml`, más los borrados de Google Cloud y los mensajes
  de LIMPIEZA-1.

**Tamaño:**

- AISLAMIENTO-2 (`73a570e..58fc1c2`): ya informado antes.
- Revisión (`335d287..c86f3ff`): **producto +2/−3**, sólo `roles.py`.

## AISLAMIENTO-2

**Premisa.**

- Sobre `dda9f5b`, el ataque daba «Bloqueado: 22 · Fugas: 0». Sólo cubría
  clientes, descargas, sin login y datos intactos.
- Las pruebas de admin y roles, contra el producto de la base, dan «6 failed,
  33 passed». Fallan:
  - `test_roles_que_no_son_la_lista_admin_no_entran[administrador]`,
    `[no es admin]` y `[roles2]` (`{"admin": False}`);
  - `test_require_role_no_cuenta_admin_por_una_parte[administrador]`,
    `[operador_admin]` y `[roles2]` (`{"admin": 1}`).

**Qué hace.**

- **Ataque, pasos 9 a 14.** Beto intenta, con los datos de Ana:
  - con las operaciones: listarlas, cambiarles el estado, agrupar y
    desagrupar ítems;
  - compartir un presupuesto;
  - con las notas de NCM: verlas, cambiarlas y borrarlas;
  - con los estudios: listarlos, borrarlos y generar un TXT con el
    `estudio_id` de Ana;
  - entre organizaciones: el estudio B no ve al A ni lo saca, y un miembro
    que no administra no saca a otro;
  - pedir cinco rutas de admin.

  Después de cada intento se mira la base.

  La revisión cambió cómo cuenta cada respuesta:
  - un 2xx es fuga;
  - un 401, 403 o 404 es bloqueo;
  - cualquier otro código, o un corte, da «DUDA» y la puerta queda «SIN
    PROBAR».
- **Prueba de admin.** Revisa tres cosas:
  - los WebSockets bajo `/api/admin/` o `/api/dev/`, mirando el mensaje ASGI
    `websocket.accept`;
  - las rutas exactas sin barra final;
  - desde `9496ca8`, también los routers incluidos.
- **`roles_de`.** Sirve a `require_role`, `require_admin` y `main._es_admin`,
  y lee los roles así:
  - un texto vale como un único rol entero;
  - una lista, una tupla o un set se pasa a lista;
  - cualquier otro valor da `[]`.

  Ningún camino del producto escribe un texto hoy, así que el arreglo es
  latente.

**Cómo se ve en rojo.**

| Qué | Salida |
|---|---|
| Pruebas de la pieza con el producto de `73a570e` | «6 failed, 33 passed»: los seis de roles de arriba. Las de admin pasan en la base: son guardas y su rojo es el sabotaje |
| `aislamiento2.sh prueba` | 10 «ROJO» y 2 controles «VERDE». Los rojos: un WebSocket que acepta sin control; uno que acepta y enseguida falla; una ruta cruda en `/api/admin` y otra en `/dev` sin barra; una ruta de FastAPI en `/api/dev` sin barra; un WebSocket y una ruta oculta dentro de un router incluido; tres que deshacen `roles_de` |
| `aislamiento2.sh ataque` | 18 «ROJO»: cada sabotaje saca un filtro de dueño, de estudio o de admin, y el ataque tiene que dar la línea `FUGA` de ese caso. Tres son de la revisión: borrar el estudio con un 204, el mapeo de columnas con un 201 y la nota con una respuesta larga |
| Los dos sabotajes nuevos del ataque contra el ataque de antes de la revisión | «VERDE … el ataque no vio la fuga» (201). La nota larga: «ROJO? … pero sin «FUGA  \| Beto no ve la nota de Ana»», con «DUDA  \| Notas → Ana no ve su propia nota». Resultado: «sabotajes con falla: 2». Con el ataque nuevo, los dos dan «ROJO» y «sabotajes con falla: 0» |

## LIMPIEZA-1

**Premisa.**

- Las 10 pruebas excluidas pasan solas y dentro de la suite completa. Son
  una de CSRF, tres del botón de NCM automático y seis de presupuestos
  públicos.
- Esas 10 no salen a la red: si falta la variable, Tarifar y VUCE quedan en
  fake.
- `DECISIONS.md:40`: CDI no usa Google Cloud.
- **Cadenas de conexión con usuario y clave:** busqué en toda la historia
  (`git log -p --all`). Hay 18 distintas y ninguna es una clave real: son
  marcadores o claves sintéticas de pruebas.
  - `cloudbuild.yaml:87` es un comentario en `main`. Sólo `1d731d9` tuvo un
    marcador `user:…@host/db`, y `92fc5a7` lo sacó.
  - `PLAN_DEPLOY_ADVERSARIAL.md:76` es un patrón de búsqueda, no una cadena
    de conexión.

**Qué hace.**

- **CI.** El paso «Suite completa» queda en `python -m pytest --no-cov`.
- **Google Cloud.** Se borran `cloudbuild.yaml`, `setup_gcp.sh`,
  `deploy-cloud-run.sh` y cinco guías de `docs/deployment/`. También salen
  las secciones de Google Cloud de `README.md` y `ARCHITECTURE.md`.
- **`tests/test_limpieza1.py`, cinco pruebas:**
  - La suite corre `python -m pytest` y sólo admite opciones de una lista
    permitida: `-q`, `-v`, `--no-cov`, `--strict-markers`, `--tb`,
    `--timeout`, `--timeout-method`, `--cov`, `--cov-report` y
    `--cov-fail-under`.

    Cualquier otra cosa da rojo, también un operador como `||` o `#`, y lo
    mismo un `cd` antes.
  - Ni el paso ni su job llevan `continue-on-error`, `if: false` ni
    `working-directory`, aunque estén entre comillas.
  - `pytest.ini` no suma en `addopts` nada fuera de la lista ni achica
    `testpaths`.
  - Ningún paso de `ci.yml` lleva `--deselect`, `--ignore` ni variables
    `PYTEST_`.
  - Ningún archivo versionado que no sea `.md` o `.txt` nombra `gcloud`,
    `cloudbuild`, `setup_gcp`, `deploy-cloud-run`, `google-github-actions`,
    `gcr.io` ni `docker.pkg.dev`.

  La prueba no se mira a sí misma ni a su script de sabotajes: los dos
  nombran esas herramientas para buscarlas.

**Cómo se ve en rojo.**

| Qué | Salida |
|---|---|
| `test_limpieza1.py` con `ci.yml`, `cloudbuild.yaml`, `setup_gcp.sh` y `deploy-cloud-run.sh` de `0f2f160` | «3 failed, 2 passed». Fallan `test_la_ci_corre_la_suite_sin_sacar_pruebas`, `test_ci_yml_no_deselecciona_en_ningun_paso` y `test_no_queda_un_camino_de_publicacion_a_google_cloud`. Las otras dos son guardas: su rojo es el sabotaje |
| `limpieza1.sh` | La base da «VERDE» y salen 37 «ROJO», uno por motivo: filtros, filtros dentro de un grupo, opciones que no corren pruebas, `-o` u `--override-ini`, `-p`, `--noconftest`, `cd`, `\|\| true`, `#`, `continue-on-error`, `if: false`, `working-directory` (también entre comillas), variables `PYTEST_`, `pytest.ini` y cinco formas de volver a Google Cloud. Los dos controles («un .md que nombra gcloud» y «la suite con -q, --timeout y --tb») dan «VERDE». Resultado: «sabotajes con falla: 0» |

## Puertas

| Puerta | Salida |
|---|---|
| Suite completa sobre `c86f3ff`, en un worktree limpio, con el entorno de la Dev | «4587 passed, 101 skipped, 3 xfailed in 704.96s (0:11:44)», 0 failed, salida 0 |
| `compileall -q proyecto_maria`, sobre `c86f3ff` | salida 0 |
| `ataque_aislamiento.sh`, sobre `c86f3ff` | «Bloqueado: 47 · Fugas: 0 · Sin probar: 0» y «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.» |
| `aislamiento2.sh prueba`, sobre `c86f3ff` | 10 «ROJO», 2 controles «VERDE», «sabotajes con falla: 0» |
| `aislamiento2.sh ataque`, sobre `c86f3ff` | 18 «ROJO», «sabotajes con falla: 0» |
| `limpieza1.sh`, sobre `c86f3ff` | base «VERDE», 37 «ROJO», 2 controles «VERDE», «sabotajes con falla: 0» |
| Las pruebas de la pieza, sobre `c751c1a` | roles y admin: «39 passed». `test_limpieza1.py`: «5 passed» |
| `smoke_friccion.sh`, sobre `0c3c02a` | «OK · telemetría + alias session/state + by-cuit protegido», salida 0 |
| La suite como la corre la CI (sus variables, sin `DATABASE_URL`), sobre `bcdbbb3` | «4050 passed, 102 skipped, 3 xfailed», 0 failed |

**Lo que no se corrió sobre `c86f3ff`:**

- **El smoke.** Desde `0c3c02a`, el producto sólo cambia en un comentario de
  `roles.py`.
- **La suite como la corre la CI.** Desde `bcdbbb3` sólo cambian pruebas y
  scripts. No comparo el número de skipped entre las dos corridas: son
  entornos y bases distintas.
- **Los sabotajes de piezas anteriores:** los corrés vos antes de publicar.
- **Nada contra producción ni contra Google Cloud.**

### chequeo-6, salida entera

```
chequeo-6 335d287..c86f3ff: avisos para mirar, no un veredicto
producto +2/−3
arnés +229/−72
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/auth/roles.py: 27 → 26
avisos: 0
```

### Revisión: hallazgos

Cada hallazgo lo reproduje antes de arreglarlo o de anotarlo.

| Quién (modelo, esfuerzo) | Hallazgo | Qué pasó |
|---|---|---|
| `adversario-sonnet-alto` (Sonnet, alto), primera pasada | H1, media: la prueba de la CI se esquivaba con variantes | Arreglado en `766d353`, `dfee12c` y `c86f3ff` |
| Ídem | H2, media-baja: la prueba de admin no veía los routers incluidos | Arreglado en `9496ca8` |
| Ídem | H3, baja: el arranque parte en letras un `roles` de texto | Queda como riesgo |
| Ídem | H4, baja: el paso de admin del ataque pide 5 rutas y ningún WebSocket | Queda como riesgo |
| Ídem | H5, baja: la prueba daba rojo con opciones inofensivas | Arreglado con la lista permitida (`dfee12c`) |
| `adversario-opus-alto` (Opus, alto) | #1, alta: email → admin | Es de antes de las piezas. Es D116 |
| Ídem | #2, media: 10 variantes que esquivaban la prueba de la CI | Arregladas |
| Ídem | #3, baja: el arranque usa `roles` crudo | Igual que H3 |
| Ídem | #4, baja: `CLAUDE.md` todavía dice que la CI deselecciona pruebas, y la CI sólo corre en push o PR a `main` | Queda como riesgo. `CLAUDE.md` no lo toco |
| `adversario-sonnet-alto` (Sonnet, alto), segunda pasada | 1, media: el ataque cortado por SIGPIPE contaba como bloqueo | Arreglado en `c86f3ff` |
| Ídem | 2, media: un 201 contaba como bloqueo | Arreglado en `c86f3ff` |
| Ídem | 3, baja: los pasos 4 y 7 del ataque | Revisado: el 4 usa la misma regla que los nuevos y el 7 exige 401 o 403. No hay cambio |
| Ídem | 4, baja: el paso 10 acepta 503 o 200 | Queda como riesgo |
| Ídem | 5, media: falsos verdes de la prueba de la CI | Arreglados. Quedan sin cubrir `paths-ignore`, `conftest.py` y `asyncio_mode` |
| Ídem | 6, baja: `--cov proyecto_maria` daba un falso rojo | Queda como riesgo |
| Ídem | Probó 27 valores de `roles`: ninguno da admin de más | Sin cambio |
| `/code-review high` (sin pasada de verificación) | 1: el arranque usa roles crudos | Igual que H3 |
| Ídem | 2 y 6: `clear-old` tocaba `error_notes.json`, y el `sql` de SQLite no hacía commit | Arreglados en `31ba053` |
| Ídem | 3: el control del WebSocket con `Depends(require_admin)` da verde por un TypeError | Reproducido. Queda como riesgo |
| Ídem | 4: `_acepta_websocket` traga excepciones. Hoy hay 0 WebSockets de admin | Queda como riesgo |
| Ídem | 5: cada consumidor normaliza los roles por su cuenta, y `/auth/me` devuelve los crudos | Queda como riesgo y propuesta |
| Ídem | 7: sólo un 200 contaba como fuga | Arreglado en `31ba053` y `c86f3ff` |
| Ídem | 8: `roles_de` acepta tupla y set sin que haga falta | Menor. Queda |
| Ídem | 9: comentarios de más de dos líneas | `28bf57f` arregla el de producto. chequeo-6 da «avisos: 0» |
| `/security-review` con `adversario-sonnet-alto` (Sonnet, alto), sobre lo que cambian las dos piezas | Ningún hallazgo medio o alto. Probó `roles_de` con 15 valores: ninguno da admin que antes no diera. Revisó `ci.yml`: no usa `pull_request_target`, ni secretos, ni datos del PR dentro de `run:`. Como endurecimiento, nombra que las acciones van por etiqueta y no por SHA | Sin cambio. No reproduje nada: no hubo hallazgo que reproducir |

### Riesgos

**Producto (fuera de las tareas, no los toqué):**

- **Alta. D116,** arriba.
- **Media. El registro con invitación no compara el email:** quien tenga el
  link entra al estudio. Además, el usuario se guarda en un commit y la
  invitación se marca usada en otro.
- **Media. En Postgres, registrarse con invitación da 500** (C7, lo arregla
  ORG-1). El ataque lo esquiva vinculando al miembro por SQL, y lo avisa con
  un «AVISO».
- **Baja. El arranque parte en letras un `roles` de texto** (H3). No da
  admin a nadie.
- **Baja. Los roles se normalizan en cada consumidor,** y `/auth/me`
  devuelve los crudos. Te propongo normalizarlos al leerlos de la base.

**Pruebas y CI:**

- **Media. La CI corre sólo en push y PR a `main`.** Lo de LIMPIEZA-1 se ve
  recién en el PR.
- **Media. Si en la cuenta de Google Cloud hay un disparador armado, no lo
  vi.** Sin `cloudbuild.yaml`, ese disparador falla en vez de publicar, pero
  lo que ya esté en Cloud Run sigue ahí.
- **Baja.**
  - El control del WebSocket con `Depends(require_admin)` da verde por un
    TypeError, no porque el control funcione.
  - `_acepta_websocket` traga excepciones.
  - El paso 10 del ataque acepta 503.
  - `--cov proyecto_maria` daría un falso rojo.
  - La prueba de la CI no mira `paths-ignore`, `conftest.py` ni
    `asyncio_mode`, y tampoco una publicación hecha con `curl` contra la API
    de Google.
- **Baja. Desactualizados:**
  - `ARCHITECTURE.md` sigue describiendo Google Cloud en el diagrama y en el
    stack. Te propongo una tarea chica de documentación para rehacerlo.
  - `CLAUDE.md` todavía dice que la CI deselecciona pruebas.
- **Baja. El trabajo `tests` de la CI no instala Node.** Usa el de
  `ubuntu-latest`, y unas 87 pruebas lo llaman.
- **La CI no corre** el ataque ni los sabotajes: los corre quien revisa.

## Para reproducir

```bash
git fetch origin claude/dev-tecnica && git checkout origin/claude/dev-tecnica
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
$PM_DIR/venv/bin/python -m pytest -q --no-cov tests/test_roles_texto.py tests/test_admin_solo_admin.py tests/test_admin2.py   # «39 passed»
$PM_DIR/venv/bin/python -m pytest -q --no-cov tests/test_limpieza1.py   # «5 passed»
PATH=$PM_DIR/venv/bin:$PATH PUERTO=8131 ./scripts/testing/ataque_aislamiento.sh   # «Bloqueado: 47 · Fugas: 0 · Sin probar: 0»
PATH=$PM_DIR/venv/bin:$PATH PY=$PM_DIR/venv/bin/python scripts/testing/sabotajes/aislamiento2.sh prueba   # 10 «ROJO», «sabotajes con falla: 0»
PATH=$PM_DIR/venv/bin:$PATH PY=$PM_DIR/venv/bin/python scripts/testing/sabotajes/aislamiento2.sh ataque   # 18 «ROJO», «sabotajes con falla: 0»
PY=$PM_DIR/venv/bin/python scripts/testing/sabotajes/limpieza1.sh   # 37 «ROJO», «sabotajes con falla: 0»
docs/pm/herramientas/chequeo-6.py 335d287 c86f3ff   # «producto +2/−3», «avisos: 0»
# los rojos en la base, en un worktree aparte, porque git reset --hard pisa los cambios:
git worktree add --detach ../rojo origin/claude/dev-tecnica && cd ../rojo
git checkout 73a570e -- proyecto_maria && $PM_DIR/venv/bin/python -m pytest -q --no-cov tests/test_roles_texto.py tests/test_admin_solo_admin.py tests/test_admin2.py   # «6 failed, 33 passed»
git reset -q --hard origin/claude/dev-tecnica && git clean -fdq proyecto_maria
git checkout 0f2f160 -- .github/workflows/ci.yml cloudbuild.yaml setup_gcp.sh scripts/deployment/deploy-cloud-run.sh && $PM_DIR/venv/bin/python -m pytest -q --no-cov tests/test_limpieza1.py   # «3 failed, 2 passed»
```

El ataque y los sabotajes del ataque usan Postgres en el puerto 5434, así
que corren de a uno. El ataque reescribe
`proyecto_maria/data/error_notes.json`. Después de correrlo:
`git checkout -- proyecto_maria/data/error_notes.json`.

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. AISLAMIENTO-2 y LIMPIEZA-1 entregadas en la punta de claude/dev-tecnica (commit del informe; puertas sobre c86f3ff). Abiertas D114 (503 por tope, antes D112, recomiendo b) y D116 (email → admin, recomiendo b, pieza aparte). Sigue BACKUP-1a (worktree bak, rama backup-1a), después EXCEL-2c; frenar 2026-11-08 15:50 UTC. Reglas de Emi: sólo la PM y Emi me piden, nada se publica sin su «dale» para el SHA, nunca main, sin secretos.
