# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ABUSO-1: S5 hecho; sigo con la D35 (1) que contestaste (2026-10-28)

**Estado.** Tu D35 llegó en `f600ed4` y la integré (merge `ddc1b61`). Sigo
con a, b, d y e, en ese orden de riesgo: primero D35a y S4. **No hace falta
que la revises todavía**: va en su propio `/entregar`, después del de
SESION-1.

**S5, ya hecho** (sin depender de la D35d):

| SHA | Qué |
|---|---|
| `584b8d1` | producto y `CHANGELOG.md`: tope de 16 KB en `/api/ui/event` y `/api/session/state` (lee por partes y corta, haya o no `Content-Length`; lo que se pasa da 413 y no se guarda) y deja de escribirse `logs/ui_events.jsonl` |
| `25158c6` | `tests/test_abuso1.py`, arnés de dos motores y `scripts/testing/sabotajes/abuso1.sh` (5 sabotajes) |
| `8c37653` | `HANDOFF.md:57` y el texto del `CHANGELOG.md` |

Corrido sobre `25158c6`:

| Qué | Salida |
|---|---|
| `tests/test_abuso1.py` sobre `e25e87c` (rojo antes) | `10 failed, 3 warnings in 2.75s` |
| `tests/test_abuso1.py` + `tests/test_static_endpoints.py` | `22 passed, 3 warnings in 2.03s` |
| `abuso1.sh 25158c6` | `sabotajes sin rojo: 0` (5 en rojo, cada uno por su motivo) |
| `abuso1_motores.py sqlite` | `sqlite: FALLAS: 6`: S4a, S4b, S6, C9 y «un evento sin sesión con una acción cualquiera no se guarda» en las dos rutas. Las seis son de la D35 |
| `abuso1_motores.py pg` (PG16, 55432) | `pg: FALLAS: 6`, las mismas |

Los OK de 5 MB dicen, en los dos motores, «da 413 y no se guarda». El
cliente ve «connection reset»: el servidor contesta 413 y cierra sin leer los
5 MB. Por eso el arnés toma el código del log del servidor.

No corrí la suite completa ni el smoke sobre `25158c6`: van en el `/entregar`.

### Decisiones

**D36. Emails que difieren sólo en mayúsculas.** Me pediste comparar sin
mayúsculas en `/auth/recover-username` y, si dos cuentas pueden tener el
mismo email cambiando sólo mayúsculas, no tocarlo y abrir esta D. **Pueden:**

- `users.email` es `unique` (`models.py:25`), y en Postgres eso distingue
  mayúsculas: `Ana@x.com` y `ana@x.com` entran las dos.
- El registro (`main.py:2922`) y el alta del admin (`:9806`) comparan con
  `func.lower`, pero el PUT del perfil (`:2001`) busca el duplicado con
  `User.email == raw_email`: pasa el email a minúsculas y compara contra lo
  guardado tal cual. Si otra cuenta tiene `Ana@x.com`, el PUT deja guardar
  `ana@x.com`.
- `proyecto_maria/scripts/migrate_to_postgres.py:48` copia el email como
  venga, con mayúsculas.

`/auth/request-password-reset` tiene la misma comparación exacta. Con dos
cuentas así, «la primera que coincida» puede mandarle el usuario o el link
de la otra cuenta al dueño de la casilla, que de hecho es el mismo; el
problema es elegir una sola.

1. **(recomendada)** En una pieza aparte, después de ABUSO-1: recuperar
   usuario y recuperar contraseña comparan sin mayúsculas y mandan **todas**
   las cuentas que coincidan a esa casilla (es la misma casilla: no filtra
   nada a un tercero); y el PUT del perfil busca el duplicado con
   `func.lower`, para que no se creen más. Antes, una consulta de sólo
   lectura en producción, que corre Emi, cuenta cuántos pares hay.
2. Dejarlo como está: quien escriba su email con otras mayúsculas que las
   guardadas no recupera nada, y el PUT sigue dejando crear pares.
3. Pasar a minúsculas los emails guardados con una migración de datos. Si
   ya hay pares, choca con la `unique` y hay que decidir a mano cuál queda.

Mientras tanto, en ABUSO-1 no toco cómo se compara el email. El límite de
3 por hora por email sí cuenta sin mayúsculas (la clave del contador va en
minúsculas): si no, cambiar una letra lo esquivaría.


Encima de SESION-1 (`895ee73`) y de tu merge `c702655`, sin cambios de
producto. Por ahora sólo pruebas: `b08dbc0` (reproducción en dos motores) y
`scripts/testing/abuso1_reciclado.sh` (el reciclado del worker, D35e).

### Decisiones

**D35. Cómo se cierran S4, S6 y C9.** Hay cinco partes. Sin la a, la b y la
e no puedo arreglar S4, S6 ni C9. La c y la d cambian lo que ve el cliente o
Emi. Recomiendo la (1) en todas.

**D35a. Qué IP se toma detrás del proxy de Railway.** No lo pude mirar:
`docs.railway.com` no está en la red de esta sesión. Mi supuesto es que el
proxy de Railway es el que conecta y **agrega** la IP del cliente al final
de `X-Forwarded-For`. Hoy el código toma la **primera**, que es la que
escribe el cliente.

1. **(recomendada)** Un solo helper, usado por `login_attempts`,
   `reset_attempts` y slowapi, que toma la **última** IP de
   `X-Forwarded-For` (la que puso el proxy). Cuántos saltos se descuentan
   es configurable, con 1 por defecto. Sin `X-Forwarded-For` usa
   `client.host`.
2. `X-Real-IP`. No sé si Railway lo manda; si no lo manda, se vuelve a la
   opción 1.
3. Que uvicorn reescriba la IP con `FORWARDED_ALLOW_IPS="*"`. **No sirve:**
   si confía en todos, uvicorn 0.54 toma la primera de la lista
   (`uvicorn/middleware/proxy_headers.py:176-177`), y esa la escribe el
   cliente.

Qué pasa con la opción 1 si el supuesto falla:

| Si Railway… | Resultado |
|---|---|
| pisa `X-Forwarded-For` con la IP del cliente | igual funciona |
| no manda `X-Forwarded-For` | todos comparten la IP del proxy y 5 fallos de cualquiera bloquean el login de todos por 15 min; **hoy pasa lo mismo**, no empeora |
| tiene Cloudflare delante (`docs/guides/01_PROYECTO.md:280` lo nombra «para frontend») | la última IP es la del borde de Cloudflare: el bloqueo pasa a ser por ciudad. Hoy, en ese caso, la IP se falsifica |

Cómo saberlo sin mirar Railway: propongo que el 429 del login deje en el
log la IP que tomó y cuántas entradas traía `X-Forwarded-For`. Si después
del deploy todas las IPs son iguales, el supuesto falló.

**D35b. Los números.** Todos son por IP real.

1. **(recomendada)**

   | Ruta | Límite |
   |---|---|
   | `/auth/register` | 5 por hora y 20 por día |
   | `/auth/recover-username` | 5 cada 15 min, y además 3 por hora por email. El de email es silencioso: misma respuesta genérica y no manda el mail, así no revela si existe |
   | `/api/ui/event` y `/api/session/state` | 120 por minuto cada una |
   | Login | sigue como está: 5 por minuto y 5 fallos → 15 min |
   | Pedir el reset | sigue como está: el 5.º intento → 15 min |

   El tope del cuerpo de 16 KB no depende de la D35: va en S5 como supuesto
   reversible, porque `props` ya se recorta a 8000.
2. Más laxos (registro 20 por hora), si Emi espera altas en grupo desde una
   misma oficina o en una demo.
3. Los que diga Emi.

**D35c. Qué dice el registro si el email o el usuario ya existen.** Hoy
devuelve 400 «Usuario ya existe» y 400 «Email ya registrado. Usa otro email
o ingresa con tu cuenta existente.». Además, con
`EMAIL_VERIFICATION_REQUIRED=false` (`HANDOFF.md:72`, la beta) un alta
exitosa devuelve el token al instante, así que **el éxito ya distingue**.
Un mensaje genérico no esconde nada.

1. **(recomendada)** Dejar los mensajes y frenar con el límite de la D35b.
2. Prender la verificación de email y contestar siempre «si el email es
   válido te llega un mail». Cierra la enumeración, pero necesita SMTP en
   producción (no lo puedo ver) y cambia el flujo de la beta. Sería otra
   pieza.
3. Un mensaje ambiguo («No se pudo registrar con esos datos»). No cierra
   nada y es peor para el que se equivocó.

**D35d. Eventos sin sesión.** Tu prueba dice «un evento sin sesión no se
guarda». Pero `landing.html:555` manda sin sesión `pricing_cta_clicked`,
`hero_cta_clicked` y `register_pending_verify`, y los KPIs del panel los
cuentan.

1. **(recomendada)** Sin sesión se guardan sólo esas tres acciones, con el
   límite de la D35b; cualquier otra acción, no.
2. Ningún evento sin sesión, como dice la prueba. Desde el deploy esos KPIs
   de la landing quedan en 0.

**D35e. El reciclado del worker borra los contadores (hallazgo nuevo).**
El `Dockerfile:67-73` corre gunicorn con `--max-requests 1000`. Sin
`REDIS_URL`, los contadores de login, de reset y de slowapi viven en la
memoria del worker, y el worker se reinicia cada 1000 a 1050 pedidos de
cualquiera. Lo probé con `--max-requests 20` (`$S/abuso1_reciclado.log`):

```
7 logins fallidos: 401 401 401 401 401 429 429
25 pedidos a /health: hechos
workers arrancados: 2
login fallido después: 401
FALLA: el reciclado borró el bloqueo
```

Con 1000 pedidos baratos a `/health` (unos segundos), el bloqueo se va. Con
la D35a arreglada, **todos los límites de ABUSO-1 se esquivan así**.

1. **(recomendada)** Los contadores de autenticación (login, reset,
   registro, recuperar) pasan a una tabla chica en la base, que se crea al
   arrancar como las demás. Los de eventos quedan en memoria: si se borran,
   entran más filas, pero de tamaño acotado. Agranda ABUSO-1 y toca datos,
   así que va con revisión fuerte.
2. Sacar `--max-requests` del Dockerfile. Es barato, pero los contadores
   igual se borran en cada deploy o caída, y si había una fuga de memoria
   que eso tapaba, vuelve.
3. Dejarlo como riesgo y hacerlo en otra pieza. ABUSO-1 cumpliría tus
   pruebas, pero el abuso seguiría abierto.

### Premisa: se reproduce todo, en SQLite y en PG16 (55432)

**Qué limitador hay hoy y con qué clave cuenta.** Las dos funciones de
`core/rate_limit.py` (`_get_forwarded_address`, que es la clave de slowapi,
y `get_client_ip`) toman la **primera** IP de `X-Forwarded-For`; sin ese
encabezado, `client.host`. El almacenamiento es `MemoryStorage`, porque no
hay `REDIS_URL`.

| Ruta | Límite hoy | Clave |
|---|---|---|
| `/auth/login` | 5 por minuto (slowapi) + 5 fallos → 15 min (`login_attempts`, en memoria) | primera de XFF |
| `/auth/request-password-reset` | el 5.º intento → 15 min (`reset_attempts`) | primera de XFF |
| `/auth/reset-password` | 5 por minuto | primera de XFF |
| `/auth/resend-verification` | 3 por minuto | primera de XFF |
| `/auth/register`, `/auth/recover-username`, `/api/ui/event`, `/api/session/state` | **ninguno** | — |

**Cómo se reprodujo.** `scripts/testing/abuso1_motores.py` levanta uvicorn
con `--no-proxy-headers`. Así `client.host` es el que conecta, como en
Railway. Simula al proxy poniendo la IP real **al final** de
`X-Forwarded-For`. Cada chequeo dice lo que tiene que pasar con el abuso
cerrado.

Lo corrí de a un motor: la primera vez los dos escribían a la vez en
`logs/ui_events.jsonl` y los bytes salían mezclados. La salida es igual en
los dos motores, salvo la última línea (`$S/abuso1_premisa_sqlite.log` y
`_pg.log`):

```
INFO  | S4a: 30 logins fallidos rotando X-Forwarded-For: [401]
FALLA | S4a: rotar la IP inventada no esquiva el bloqueo de login
INFO  | S4b: login correcto de la víctima después: 429 ''
FALLA | S4b: inventar la IP de otro no lo bloquea
INFO  | S5 /api/ui/event: 5 MB sin sesión → 200, JSONL +5243100 bytes, filas [(None, 8000)]
FALLA | S5 /api/ui/event: un evento de 5 MB sin sesión no se guarda
INFO  | S5 /api/ui/event: 5 MB con sesión → 200, JSONL +5243109 bytes, filas [('ab1_eventos', 8000)]
FALLA | S5 /api/ui/event: un evento de 5 MB con sesión no se guarda
INFO  | S5 /api/ui/event: evento chico sin sesión con una acción inventada → 200, filas [(None, 41)]
FALLA | S5 /api/ui/event: un evento sin sesión con una acción cualquiera no se guarda
OK    | S5 /api/ui/event: un evento chico con sesión se guarda a su nombre ([('ab1_eventos', 41)])
(las mismas cinco líneas para /api/session/state)
INFO  | S6: 30 pedidos de recuperar usuario desde una IP: [200]
FALLA | S6: recuperar usuario tiene límite por IP
INFO  | S6: registrar un usuario que existe → 400 'Usuario ya existe'
INFO  | S6: registrar un email que existe → 400 'Email ya registrado. Usa otro email o ingresa con tu cuenta existente.'
INFO  | C9: 30 registros desde una IP: [200], altas: 30
INFO  | C9: estado de las altas: [('trial', 30)]
FALLA | C9: registrarse tiene límite por IP
sqlite: FALLAS: 10        pg: FALLAS: 10
```

Qué muestra:

- **S4.** Rotar la IP inventada nunca llega al 429, y 8 logins con la IP de
  la víctima la dejan afuera. Todo esto con el supuesto de la D35a.
- **S5.** Cada pedido de 5 MB suma 5 MB a un JSONL que ningún código lee:
  sólo lo nombra `HANDOFF.md:57`, y la IP que guarda es la del proxy.
  Además, cada pedido guarda una fila de 8000 caracteres.
- **S6 y C9.** Sin límite ninguno de los dos. Cada alta da 14 días de prueba.

### Riesgos y fuera de alcance

- **Fila 14 de Argon** (el login exitoso reinicia el contador; bloqueo
  perpetuo del pedido de reset): no la toco. La opción 1 de la D35e la
  dejaría igual: sólo cambia dónde vive el contador, no cuándo se borra.
- **X1** (sugerencias de NCM sin tope): no la toco.
- **`scripts/testing/sesion1_motores.py`** esquiva el límite de login
  mandando una IP inventada distinta en cada pedido. Con S4 arreglado
  deja de servir, y lo ajusto en esta pieza.
- **`recover-username` y mayúsculas:** lo arreglo en esta pieza, como dijiste
  en la D35. Si dos cuentas pueden tener el mismo email cambiando sólo
  mayúsculas, no lo toco y abro la D36.
- **Un token revocado sigue firmando eventos.** `_jwt_sub_from_token_text`
  (eventos de uso) mira la firma y el vencimiento, pero no la revocación:
  después de cerrar sesión, ese token puede seguir guardando eventos a nombre
  del usuario hasta que vence. Sólo afecta la telemetría. Es de antes y no lo
  toco.

## SESION-1: hecha, **sin entregar** (2026-10-28)

Encima de OBSERVABILIDAD-1 y de tu `486e655` (merge `f5160d7`): producto y
`CHANGELOG.md` `7dfe144`; casos, arnés de dos motores, pantalla y sabotajes
`014a3e4`; arreglo de producto `4c1ae09` y sabotajes ajustados `895ee73`.
**SHA probado: `895ee73`.** Para ver sólo esta pieza:
`git diff f5160d7..895ee73`. Va en su propio `/entregar`, después del de
OBSERVABILIDAD-1, con subagentes, `/code-review high` y `/security-review`
cuando vuelva el cupo. **No hace falta que la revises todavía.**

Nada para decidir. Supuestos abajo.

### Premisa: confirmada, en SQLite y en Postgres 16 (55432)

Servidor real sobre `39be45e`, usuario inventado (`$S/ses/premisa.py`,
fuera del repo). Mismo resultado en los dos motores:

```
[base] dos logins: T1 401 (revocada por el segundo), T2 200
[A cambiar clave con T2] 200; active_jti=None; T1 200, T2 200
[login nuevo T3] T1 401, T2 401, T3 200
[B resetear clave] pedir 200, reset 200; active_jti=None; T1 200, T2 200, T3 200
[C cerrar sesión T4] /auth/logout 200, /logout 200; T4 después 200
[D cambiar email sin contraseña con T4] 200; email en la base=atacante@example.com
```

Es peor de lo que dice S3: cambiar o resetear la clave ponía `active_jti`
en NULL, y NULL quiere decir «aceptar cualquier token» (usuarios de antes
de la columna). **Revocar resucitaba las sesiones ya revocadas** (T1 volvió
a entrar). Cerrar sesión sólo borraba la cookie: el token seguía entrando.
Y cualquiera con una sesión abierta cambiaba el email sin la clave, y con
eso, el reset.

### Qué cambió

Se usa el único mecanismo que había: `users.active_jti` y el chequeo de
`get_current_user`.

- `auth/dependencies.py`: `revocar_sesiones(user, conservar_jti=None)`
  nunca escribe NULL; para revocarlas todas guarda un jti nuevo que ningún
  token tiene. `revocar_sesion_de_la_request` toma el token de la cookie o
  del Bearer, como `get_current_user`, y lo revoca **sólo si es el
  vigente**: un token vencido, inválido o ya revocado no toca nada (si no,
  quien tenga uno viejo podría sacar a la sesión buena).
  `get_current_user` deja el jti en `request.state.token_jti`.
- `main.py`:
  - `POST /api/user/change-password`: cierra las otras y conserva la de
    quien la cambió. Con la clave actual mal no toca nada.
  - `POST /auth/reset-password`: cierra todas.
  - `POST /auth/logout` y `POST /logout`: revocan ese token y borran la
    cookie; sin token o con basura, 200 como antes.
  - `PUT /api/user/profile`: si el email cambia (sin distinguir mayúsculas
    ni espacios; vaciarlo también es cambiarlo), pide `current_password`.
    Sin ella: 400 «Para cambiar el email ingresá tu contraseña actual»;
    equivocada: 400 «La contraseña actual es incorrecta». En los dos casos
    no cambia nada, tampoco el nombre. El formato se valida antes de pedir
    la clave.
- Pantalla de perfil v2 (`profile.js`, `dashboard_v2.html`): el campo
  «Contraseña actual» aparece sólo si el email cambió; sin clave avisa y no
  manda nada; al guardar bien se vacía y se oculta.

### Rojo antes del producto (`39be45e`)

- `tests/test_sesion1.py`: `11 failed, 6 passed`.
- `sesion1_motores.py`: `FALLAS: 12` en SQLite y `FALLAS: 12` en Postgres;
  fallan cerrar la otra al cambiar la clave, `active_jti` no NULL (×2), el
  reset cierra la vigente y no resucita, los cuatro logouts (Bearer y
  cookie en las dos rutas) y el email sin clave, con clave mal y vaciándolo.
- `pantalla_sesion1.js`: `FALLA: cambiar el email no muestra el campo de
  la clave`.

### Puertas sobre `895ee73`

| Puerta | Resultado |
|---|---|
| suite completa (`pytest -q --no-cov --timeout=120`) | `3872 passed, 336 skipped, 2 xfailed`, 0 failed, `pytest salida 0` |
| `compileall` | `compileall 0` |
| `sesion1_motores.py sqlite` | 26 `OK`, `sqlite: todo OK`, salida 0 |
| `sesion1_motores.py pg postgresql://cdi@127.0.0.1:55432/postgres` | 26 `OK`, `pg: todo OK`, salida 0 |
| `sabotajes/sesion1.sh` (14 de backend, 5 de pantalla) | 19 `ROJO`, `sabotajes sin rojo: 0`, salida 0 (la base verde de pantalla incluida) |
| `smoke_friccion.sh` | `smoke salida 0` |
| `ataque_aislamiento.sh` | 22 `OK`, `ataque salida 0` |
| pantalla sola (verde, sobre `014a3e4`) | 3 de 3 `OK: el perfil pide la contraseña sólo al cambiar el email y no saca a nadie al login` |

**Rojo de la suite sobre `014a3e4`, mío y arreglado:** `1 failed, 3871
passed, 336 skipped, 2 xfailed`. Falló
`test_auth_invalid_plan.py::test_get_current_user_with_invalid_plan_falls_back_to_premium`
con `AttributeError: 'MockRequest' object has no attribute 'state'`: yo
había hecho que `get_current_user` escribiera el jti en `request.state`, y
ese test le pasa un request falso sin `state`. Ningún código de producto
llama así, pero era un efecto lateral escondido entre la dependencia y la
ruta. En `4c1ae09` lo saqué: `change-password` lee el jti del token con
`jti_de_la_request` (cookie o Bearer, como `get_current_user`). El test
viejo no lo toqué. Sobre `895ee73`: ese test y los de la pieza `32
passed`; motores 26 `OK` en los dos; smoke y ataque salida 0 (22 `OK`).

Un sabotaje que **no** sirve, y por qué: quitar sólo el chequeo de «sin
clave» no rompe la regla, porque `verify_password` igual rechaza `None` (da
400 «incorrecta»). El sabotaje que quedó es el defecto real: verificar sólo
si viene una clave.

No corrí: subagentes, `/code-review` ni `/security-review` (sin cupo hasta
las 18:00 UTC). Una primera corrida de navegador, antes de esta versión del
script, no mandó el PUT; no encontré la causa y no se repitió en las
siguientes.

### Riesgos (fuera de alcance; ninguno lo empeora esta pieza)

- `REPRODUCCION-ARGON` fila 10: `verify-email` se puede reusar y abre una
  sesión.
- Fila 13.2: el reset con una cookie vieja da 403 (CSRF).
- Fila 14: `/auth/me` no mira el jti (un token revocado sigue viendo sus
  datos ahí); los tokens de reset no se anulan entre sí; el contador de
  intentos de login.
- La telemetría (`_jwt_sub_from_token_text`) atribuye eventos a tokens
  revocados.
- Un usuario con `active_jti` NULL (nunca hizo login desde la columna)
  acepta cualquier token suyo hasta su próximo login, cambio de clave o
  cierre de sesión.
- Cambiar el email no cierra las otras sesiones (la tarea no lo pide).
- `/logout` no está exento de CSRF y `/auth/logout` sí: igual que antes.
- `change-password` y `PUT /api/user/profile` no tienen límite de
  intentos: sirven para probar claves con una sesión robada. **Alta.**
- El límite de login por IP sale de `X-Forwarded-For`: cambiándolo se
  saltea (ya era así; lo usé para que el arnés no choque con el límite).
  **Alta.**
- Si la base falla al cerrar sesión, da 500 y no borra la cookie.
- Un usuario sin hash de clave válido no puede cambiar su email.
- `change-password` con la clave mal sigue dando 401, y la pantalla lo
  toma como sesión vencida y manda al login. No lo toqué.

### Supuestos reversibles

- 400 y no 401 para la clave equivocada en el perfil: la pantalla toma
  cualquier 401 como sesión vencida.
- El email se compara sin mayúsculas ni espacios, y vaciarlo pide la clave.
- El formato del email se valida antes de pedir la clave.
- El aviso al cambiar la clave dice «Cerramos tus otras sesiones abiertas.
  Usá la nueva la próxima vez que ingreses.».
- `test_user_profile_coverage.py`: el caso que cambiaba el email sin clave
  ahora espera 400; el de email inválido mira el texto «Email no válido».

### Archivos de producto que toqué

`proyecto_maria/auth/dependencies.py`, `proyecto_maria/main.py`,
`proyecto_maria/static/v2/screens/profile.js`,
`proyecto_maria/templates/dashboard_v2.html`, `CHANGELOG.md`.

### Comandos

```bash
# con las variables de prueba de siempre (VUCE_MODE=fake, etc.)
python -m pytest -q --no-cov tests/test_sesion1.py tests/test_user_profile_coverage.py
#   → todo passed, 0 failed
python scripts/testing/sesion1_motores.py sqlite
#   → 26 líneas OK y «sqlite: todo OK»
python scripts/testing/sesion1_motores.py pg postgresql://cdi@127.0.0.1:55432/postgres
#   → 26 líneas OK y «pg: todo OK» (sólo acepta un Postgres local)
NODE_PATH=$(npm root -g) PY=$(which python) scripts/testing/sabotajes/sesion1.sh 014a3e4
#   → 19 líneas ROJO y «sabotajes sin rojo: 0» (~4 min; sin node+playwright sale con error)
```

## OBSERVABILIDAD-1: hecha, **sin entregar** (2026-10-28)

Encima de DISCO-1 (`88b22c8`): producto y `CHANGELOG.md` `8b1ce3b`;
casos, arnés de arranque y sabotajes `7ae35ab`; merge de tu rama
(`4e7896d`, sólo `NOW.md` y `PARA-DEV.md`) `39be45e`. **SHA probado:
`39be45e`** (el código es el de `7ae35ab`). Para ver sólo esta pieza:
`git diff 88b22c8..7ae35ab`. Va en su propio `/entregar`, después del de
DISCO-1, con subagentes, `/code-review high` y `/security-review` cuando
vuelva el cupo. **No hace falta que la revises todavía.**

### Decisiones

- **D34: contestada (a) en tu `486e655`.** La pieza sólo hace que la
  columna exista; atribuir cada métrica a su usuario queda fuera.

### Premisa: confirmada en Postgres 16 (55432)

Base con `api_logs` sin la columna y 3 filas; arranco la app, registro un
admin, pido `/robots.txt`, hago login y pido `/api/dev/stats`
(`$S/obs/premisa.py`, fuera del repo).

- **`88b22c8` (antes):** `registro 200`, `robots 200`, `login 200`,
  `stats (500, …)`, `filas antes/después: 3 3`. En el log, por cada
  pedido: `⚠️ Error logging metrics: (…) UndefinedColumnError'>: column
  "owner_username" of relation "api_logs" does not exist`. **Ningún pedido
  falla; se pierde cada métrica y el panel de admin da 500.**
- **`39be45e` (después):** `cols antes: []`, `stats (200, …)`,
  `filas antes/después: 3 6`, y en el log `✅ Migracion: agregada columna
  api_logs.owner_username` y `✅ Migracion: agregado indice
  ix_api_logs_owner_username`.

### Cómo se aplican hoy los cambios de esquema

- **Uno solo, automático:** al arrancar, `lifespan` corre `init_db`
  (`create_all`: crea tablas que no existen, no agrega columnas) y después
  los `_migrate_*` de `main.py` (19 de esquema), que agregan columnas a tablas
  viejas en SQLite y Postgres. El `Dockerfile` arranca gunicorn directo;
  `railway.json` no tiene paso de deploy. Usé ese mecanismo: no hizo
  falta preguntar.
- `proyecto_maria/scripts/migrate_add_owner.py` es manual y sólo SQLite
  (`sqlite3`, `--db`); su docstring dice «No toca PostgreSQL de producción
  — eso se hace con alembic aparte», pero **en el repo no hay alembic**
  (ni `alembic.ini` ni versiones): no compite.
- **¿Corrió en producción?** Con el repo: no pudo, producción es Postgres.
  Y el log del 24/10 muestra que a `api_logs` le falta la columna, o sea
  que nadie la agregó por otro lado. **Supuesto:** no veo la base.

### Qué hace (`_migrate_add_api_logs_owner_column`, `main.py:1288`)

- Corre al arrancar después de `_migrate_add_unidad_column`, en una
  transacción.
- Lee las columnas de `api_logs`. Si la tabla no existe, no hace nada
  (`create_all` ya la crea completa).
- Si falta, `ADD COLUMN owner_username VARCHAR(50)`: acepta vacío, sin
  default, no toca filas. En Postgres con `IF NOT EXISTS`.
- Si no hay **un índice cuya primera columna sea `owner_username`** (se
  llame `ix_api_logs_owner_username`, como lo nombra `create_all`, o
  `ix_api_logs_owner`, como el script viejo), crea
  `ix_api_logs_owner_username`.
- Si ya está todo, no hace nada **y no pide el lock** de la tabla.
- En Postgres, `lock_timeout` de 5 s: con la tabla tomada por otra
  conexión, falla al rato en vez de colgar el arranque.
- Si algo falla: `logging.exception("[OBSERVABILIDAD-1] no se pudo agregar
  api_logs.owner_username; la app arranca igual, pero las métricas no se
  graban hasta que exista")`, con el motivo, y la app sigue. El próximo
  arranque reintenta.

### Puertas sobre `39be45e`

| Puerta | Salida |
|---|---|
| `tests/test_observabilidad1.py` (SQLite, 8 casos) | `8 passed` |
| Arranque real con uvicorn, SQLite y Postgres 16 | 38 `OK`, `fallas 0`, salida 0 |
| Sabotajes `observabilidad1.sh` con `PG_URL` (sobre `7ae35ab`) | 16 `ROJO`, `sabotajes sin rojo: 0; no corridos: 0`, salida 0 |
| Suite completa, desde worktree limpio | `3855 passed, 336 skipped, 2 xfailed, 95 warnings in 515.51s`, `compileall 0`, `pytest salida 0` |
| Smoke | `==> OK · telemetría + alias session/state + by-cuit protegido`, salida 0 |
| Ataque de aislamiento | `Bloqueado: 22 · Fugas: 0`, `✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.`, salida 0 |
| Subagentes, `/code-review high`, `/security-review` | **No corridos:** sin cupo hasta las 18:00 UTC |

El arranque prueba, en cada motor: base vieja con filas → columna
`VARCHAR(50)` nullable sin default, un único índice, filas iguales y sin
dueño inventado, la métrica de `/robots.txt` grabada, sin «Error logging
metrics», `/api/dev/stats` 200; segundo arranque (en Postgres, con una
lectura abierta sobre `api_logs`) → esquema y filas iguales y nada en el
log. Falla simulada (SQLite: `api_logs` es una vista; Postgres: otra
conexión con `LOCK … ACCESS EXCLUSIVE`) → la app arranca (~8 s en
Postgres), el log trae el motivo y `/robots.txt` da 200; en Postgres, al
soltar la tabla el próximo arranque la agrega.

Los 16 sabotajes, uno por regla: el arranque no la llama; no agrega la
columna (SQLite y Postgres); NOT NULL o DEFAULT con dueño; no crea el
índice (SQLite y Postgres); busca el índice por nombre (duplica el del
script viejo); agrega la columna aunque ya esté; pide el lock aunque ya
esté; sin tabla no se va antes; la falla se propaga; la falla frena el
arranque; la falla no va al log; va al log sin el motivo; espera el lock
sin límite.

### Comandos

```bash
# Postgres 16 descartable en 127.0.0.1:55432, rol cdi (sólo acepta host local)
python -m pytest -q --no-cov tests/test_observabilidad1.py
#   → 8 passed
python scripts/testing/observabilidad1_arranque.py postgresql://cdi@127.0.0.1:55432/postgres
#   → 38 líneas OK y «fallas 0» (sin URL corre sólo SQLite)
PY=$(which python) PG_URL=postgresql://cdi@127.0.0.1:55432/postgres \
  scripts/testing/sabotajes/observabilidad1.sh 7ae35ab
#   → 16 «ROJO» y «sabotajes sin rojo: 0; no corridos: 0» (~5 min)
```

### Riesgos

Otras columnas del modelo que una base vieja podría no tener: las que
agrega `migrate_add_owner.py` y ningún `_migrate_*`. Si falta una, toda
consulta a esa tabla da `UndefinedColumn`:

- `clients.owner_username`: supuesto, en producción está, porque el
  aislamiento por dueño funciona y sin ella fallaría todo.
- `ncm_notes.owner_username` (y su índice `ix_ncm_notes_owner_ncm`); el
  script además rehace la tabla para que `client_id` acepte vacío, y eso
  tampoco lo hace ningún helper.
- `client_product_history.owner_username` (e `ix_cph_owner_client`).
- `system_backups.owner_username` (e `ix_system_backups_owner`).

Ya cubiertas por helpers: `operations.owner_username`, `op_code`,
`source`, `extra` (`_migrate_sync_operations_columns`) y `clients.notes`,
`favorite` (`_migrate_sync_clients_columns`). Las tablas creadas después
(`vendor_catalog_products`, `telemetry_events`, `estudios`,
`ncm_historial`…) las crea `create_all` completas: supuesto: el clon es
superficial y no llega a cuándo se crearon.

De esta pieza:

- El `CREATE INDEX` no es `CONCURRENTLY`: con un `api_logs` grande, el
  primer arranque tarda lo que tarde construirlo, con la tabla bloqueada
  para escritura. `lock_timeout` acota la espera del lock, no la
  construcción. Desde que falta la columna la tabla no crece; cuántas
  filas tiene de antes, no lo sé.
- En Postgres, si falla el índice se revierte también la columna; el
  próximo arranque reintenta las dos.
- El arranque puede demorarse hasta 5 s si otra conexión tiene la tabla.
- Con más de un worker (`WEB_CONCURRENCY` en `gunicorn_conf.py`; el
  `Dockerfile` usa 1), dos arranques a la vez: uno puede fallar y dejarlo
  en el log, y el esquema queda bien. **No probado.**
- D34 (a): las métricas siguen sin dueño. Propuesta para otra pieza: que
  `MetricsMiddleware` grabe el usuario leyendo el token ya verificado; toca
  sesión y autenticación, con su revisión.

### Supuestos reversibles

- La columna va sin la clave foránea a `users` que tiene el modelo:
  agregarla valida todas las filas y puede fallar con datos viejos.
- `lock_timeout` de 5 s.
- Se acepta como índice el `ix_api_logs_owner` del script viejo.
- Dueño vacío (D34 (a)).

### Archivos de producto que toqué

`proyecto_maria/main.py`, `CHANGELOG.md`.

## DISCO-1: hecha, **sin entregar** (2026-10-28)

Encima de DATOS-1 (`c996ad4`) y del merge de tu rama `1f6e0de`
(`cf84a76`): producto y `CHANGELOG.md` `bd53fc4`; casos y sabotajes
`0f1161a`; prueba en Postgres y textos de dos sabotajes `88b22c8`.
**SHA probado: `88b22c8`.** Para ver sólo esta pieza:
`git diff cf84a76..88b22c8`. Va en su propio `/entregar`, la última,
después del de DATOS-1, con subagentes, `/code-review high` y
`/security-review` cuando vuelva el cupo. **No hace falta que la revises
todavía.**

### Decisiones

- **D33: contestada (a) en `a3efc3a`.** El riesgo que pediste está en
  «Riesgos».
- **D33. ¿Se rescatan los historiales que hoy están en el contenedor de
  producción?** El primer arranque con DISCO-1 es un deploy, y ese deploy
  borra los archivos como cualquier otro deploy.
  - (a) **Se aceptan perdidos** (recomiendo): es un caché de sugerencias,
    cada deploy ya lo borró hasta hoy, y rescatarlo toca producción a mano.
  - (b) Antes del deploy, Emi copia los `ncm_historial_*.json` del
    contenedor que corre y los pone en el `DATA_DIR` del nuevo (o en un
    volumen), y reinicia: el cargador los toma una vez. Toca producción:
    lo decide Emi.

### Premisa: `DATA_DIR` no es persistente (confirmado con código)

- `DATA_DIR = os.getenv("CDI_DATA_DIR") or os.path.join(basedir, 'data')`
  (`proyecto_maria/main.py:34`): sin la variable, `/app/data` en la imagen.
- `Dockerfile`: `WORKDIR /app` y `RUN mkdir -p data generated backups logs`
  (línea 46); copia sólo `proyecto_maria` y `gunicorn_conf.py` (42-43).
- `railway.json` no declara volumen (builder DOCKERFILE, 1 réplica,
  healthcheck `/health`). `docker-compose.yml` monta `./data:/app/data`,
  pero es sólo local.
- **Supuesto:** no veo las variables ni los volúmenes de Railway. Si
  hubiera un volumen montado en `/app/data`, o `CDI_DATA_DIR` apuntando a
  uno, la premisa cae para ese caso y el primer arranque cargaría los
  archivos (ver abajo).

### Lo demás que se escribe en `DATA_DIR` (o al lado), una línea cada uno

- `descargas/<hash>/` (`DOWNLOADS_DIR`, `main.py:47`): TXT de MARIA y
  Excel. **Temporal**: se regeneran; un link de descarga viejo da 404
  después de un deploy.
- `generated/` (`main.py:8184`, `8224`): plantillas Excel con fecha.
  **Temporal.**
- `localStorage_backup.json` (`BACKUP_FILE`, `main.py:36`): no se usa en
  ningún lado.
- `Operation.generated_file`: columna que nunca se escribe (sólo se lee en
  7143 y 7224).
- `excel_generator.py:102`: escribe en `DATA_DIR` sólo si lo llaman sin
  `output_dir` (scripts y pruebas). **Temporal.**
- Fuera de `DATA_DIR` y también efímero: `proyecto_maria/data/error_notes.json`
  (`core/error_notes_tracker.py`, estadística de notas de error del
  admin). **Dato del usuario que se pierde** en cada deploy; no es de esta
  tarea, va como riesgo. `maria.log` si el log a archivo está prendido.
- Archivos subidos: `tempfile.mkstemp` (`main.py:8287`). **Temporal.**

### Qué hace

- Tabla nueva `ncm_historial` (`database/models.py`, `NcmHistorial`):
  dueño (clave foránea a `users.username`), clave, descripción, NCM y
  cuenta; única por dueño y clave. La clave es el sha256 de la
  descripción **tal cual se guardaba** (sin normalizar), para que la
  unicidad no dependa del largo del texto. El orden de sugerencia es el de
  inserción, como en el archivo.
- Confirmar (`guardar-uso`): un solo `INSERT … ON CONFLICT DO UPDATE` que
  suma uno y actualiza la NCM. Sin leer antes: dos confirmaciones a la vez
  no pierden cuenta.
- Importar: suma y cuenta duplicados igual que antes; lo ya existente
  conserva la cuenta y toma la NCM nueva. Todo en un commit: si falla, 500
  «No se pudo guardar» y no queda nada a medias.
- Sugerir: lee sólo lo del dueño; si la lectura falla, sigue sin historial.
- Al arrancar: carga una vez cada `ncm_historial_*.json` de `DATA_DIR` a
  su dueño con `ON CONFLICT DO NOTHING` (no suma dos veces ni pisa lo
  confirmado después) y lo renombra a `.migrado`. Ya no lo vuelve a leer.
  Un archivo roto, con un nombre que corresponde a más de un usuario o a
  ninguno, o con una cuenta que no entra en la columna, va al log (sin
  copiar descripciones) y queda en su lugar; nunca frena el arranque.

### Qué pasa en producción el primer arranque

- `create_all` crea sólo `ncm_historial`; las demás tablas no se tocan
  (en Postgres conservan sus filas, abajo).
- El cargador busca archivos en `DATA_DIR`. Sin volumen, el contenedor
  nuevo arranca vacío: no carga nada y no escribe nada en el log.
- Lo acumulado en el contenedor que corre desde el último deploy se pierde
  en este deploy, igual que en todos los anteriores. Es la D33.
- Con varios workers el cargador corre en cada uno; es idempotente (el
  segundo no inserta y el que pierde el renombre lo anota en el log). Hoy
  es uno solo (`--workers 1`, `gunicorn_conf.py`).

### Puertas sobre `88b22c8`

| Puerta | Salida exacta |
|---|---|
| Suite completa (worktree limpio) | `3847 passed, 336 skipped, 2 xfailed, 94 warnings in 502.78s (0:08:22)`; `compileall 0` |
| Sabotajes `scripts/testing/sabotajes/disco1.sh 88b22c8` | 20 líneas `ROJO`; `sabotajes sin rojo: 0` |
| `scripts/testing/disco1_postgres.py` (Postgres 16 local, parte de `c996ad4` con datos) | 20 `OK`; `fallas: 0`; no queda base |
| El mismo, con confirmar «leer y después escribir» (sabotaje a mano) | `FALLA \| 16 confirmaciones a la vez cuentan 16: [500] [('Rodamiento sintetico', '8482.10.10', 7)]`; `fallas: 1` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `ataque_aislamiento.sh` (Postgres) | `Bloqueado: 22 · Fugas: 0`; `✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.` |
| `tests/test_disco1.py` sobre `c996ad4` | rojo al importar: `cannot import name 'NcmHistorial'` |

Lo que discrimina de verdad son los 20 sabotajes (uno por regla: suma,
NCM, commit, que no escriba el archivo, clave tal cual, dueño, carrera,
importar ×4, cargar dos veces, pisar, renombrar, roto ×4, ambiguo,
arranque) y el script de Postgres, que primero comprueba que la versión
anterior escribía archivos. **No corrido:** subagentes, `/code-review` y
`/security-review` (sin cupo hasta las 18:00 UTC).

```bash
# sabotajes: 20 «ROJO», última línea «sabotajes sin rojo: 0»
scripts/testing/sabotajes/disco1.sh 88b22c8
# Postgres 16 local en 55432, con un venv que tenga uvicorn y psycopg2: «fallas: 0»
python scripts/testing/disco1_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
# el test nuevo: «11 passed»
python -m pytest -q --no-cov tests/test_disco1.py
```

### Riesgos

- **D33 (a):** si nadie hace (b), el primer deploy con DISCO-1 pierde los
  historiales que haya, igual que todos los deploys hasta hoy.
- Las pruebas usan `./data` como `DATA_DIR` y cada arranque del
  `TestClient` corre el cargador ahí. Restos locales de otras pruebas con
  usuarios que no están en la base de prueba quedan donde están; un
  checkout limpio no tiene ninguno.
- Un archivo con una cuenta que no entra en un entero de Postgres se
  rechaza entero, va al log y queda en su lugar (probado).
- Nombres ambiguos: la validación de usuario (`^[a-zA-Z0-9_-]{3,30}$`)
  los hace teóricos; igual no se le cargan a nadie.
- `error_notes.json` sigue siendo efímero (fuera de la tarea).

### Supuestos reversibles

- La clave es el sha256 de la descripción exacta; la descripción se
  guarda como vino.
- Las entradas salteadas al cargar (sin descripción o sin NCM) no se
  copian al log, sólo cuántas.
- Una cuenta inválida en el archivo (no entero, booleano o menor que 1)
  se carga como 1.

### Archivos de producto que toqué

`proyecto_maria/main.py`, `proyecto_maria/database/models.py`,
`CHANGELOG.md`. Casos existentes adaptados: `tests/test_catalogo_ncm1.py`,
`tests/test_ncm_sugerir_catalog.py`.

## DATOS-1: hecha, **sin entregar** (2026-10-28)

Encima de DESPACHO-1b (`e59e1a8`) y del merge de tu rama con la D32 (a)
(`d01f95c`): producto y `CHANGELOG.md` `7d09c6f`; casos `4416076`; prueba en
Postgres y sabotajes `162d277`; arreglo de los casos, que gastaban el cupo
de `test_user`, `c996ad4`. **SHA probado: `c996ad4`.** Para ver sólo esta
pieza: `git diff d01f95c..c996ad4`. Va en su propio `/entregar`,
después del de DESPACHO-1b, con subagentes, `/code-review` y
`/security-review` cuando vuelva el cupo. **No hace falta que la revises
todavía.** La D32 está contestada (a) en `0a6e887`: es lo que hice.

- **D5 / D32 (a), borrar un cliente con presupuesto compartido**
  (`delete_cliente`, `main.py`): antes de borrar las operaciones del
  cliente, borra los presupuestos compartidos de esas operaciones (y sólo
  de esas), en la misma transacción que el cliente. Si algo falla a mitad,
  el rollback que ya estaba deja todo como antes.
  - **En Postgres** (`scripts/testing/datos1_postgres.py`, 16.15 local y
    descartable): sobre el código anterior (`d01f95c`) el dueño recibe
    **500** y no se borra nada («fallas: 3»); sobre `162d277`, 200, no
    quedan cliente, operaciones ni presupuestos, el link da 404 y siguen
    andando el presupuesto de otro cliente del mismo dueño y el de otro
    dueño («fallas: 0»). Otro dueño recibe 404 y el presupuesto sigue. Una
    falla simulada al borrar el cliente da 500 y no borra nada.
  - **Pantalla** (`clientes.js`, la v2, que ya avisaba qué se borra): ahora
    dice «…y dejarán de andar los links de presupuestos que compartiste.
    Esta acción no se puede deshacer.». La vieja (`app.js`) no avisa nada y
    no se tocó, como dijiste.
- **D2, `/health`:** sin base responde **503** con `database: "error"` y
  `status: "degraded"`, sin `db_error`. El texto del error va al log
  (`logging.exception`). Con base, 200 igual que antes. `railway.json` no se
  tocó; `/admin/health/detailed` tampoco.
- **D6, los 500:** los dos manejadores (el de `HTTPException` 500 y el de
  excepciones no manejadas) devuelven sólo el mensaje amigable y
  `code: "internal_error"`; el detalle, con su traza, va al log. Los 4xx
  siguen con su `detail` tal cual (hay prueba con uno de la app y otro
  armado). `finalize.js` mostraba `dev_detail` en el aviso: ahora muestra
  `detail` y corta en 200 caracteres en vez de 100, porque el mensaje
  amigable mide 131.
- **Archivos de producto:** `proyecto_maria/main.py`,
  `proyecto_maria/static/v2/screens/clientes.js`,
  `proyecto_maria/static/v2/screens/finalize.js` y `CHANGELOG.md`.

**Qué hace Railway con una publicación nueva si la base no contesta (no
verificado: `docs.railway.com` está bloqueado desde acá).** Según
`railway.json`, Railway prueba `/health` al publicar, con 60 s de tope, y no
pasa el tráfico a la publicación nueva hasta que responda 200. Pero lo que
pasa de verdad acá es otra cosa, y eso sí lo vi: **si la base no contesta al
arrancar, la app ni siquiera levanta.** `init_db` corre en el arranque sin
`try`, uvicorn sale con código 3 y `/health` no contesta nunca. La
publicación nueva falla y, hasta donde sé, queda la anterior. El 503 sólo
cambia algo si la base se cae con la app ya andando: ahí `/health` lo dice,
pero Railway, hasta donde sé, no vuelve a mirar `/health` después de
publicar, así que no la reinicia por eso. Lo útil del 503 es para quien
mire `/health` desde afuera (un monitor), no para Railway.

**Puertas** (sobre `c996ad4`, salvo Postgres, smoke y ataque, que corrí
sobre `162d277`: entre los dos sólo cambia `tests/test_datos1.py`):

| Puerta | Resultado |
|---|---|
| `tests/test_datos1.py` | 9 passed (en rojo sobre el código anterior: 4 fallas por el motivo de la tarea) |
| Suite completa (`--timeout=120`) y `compileall`, `c996ad4` | `3836 passed, 336 skipped, 2 xfailed, 95 warnings in 497.50s (0:08:17)`, pytest salida 0; `compileall 0` |
| Suite completa sobre `162d277` (antes del arreglo) | `6 failed, 3830 passed, 336 skipped, 2 xfailed`, salida 1: abajo |
| `scripts/testing/datos1_postgres.py` (Postgres 16 local, base `datos1a`) | `d01f95c`: «fallas: 3», salida 1 (500 al borrar). `162d277`: «fallas: 0», salida 0 |
| Sabotajes `scripts/testing/sabotajes/datos1.sh c996ad4` | 12 líneas ROJO, «sabotajes sin rojo: 0», salida 0 |
| `smoke_friccion.sh` (puerto 8862) | salida 0, «OK · telemetría + alias session/state + by-cuit protegido» |
| `ataque_aislamiento.sh` (puerto 8863) | salida 0, «PUERTA G3 PASADA. Ningún despachante ve datos de otro.» |

El primer intento del ataque salió 1 por entorno: el script busca
`./venv/bin/python` y, si no está, usa `python3` del sistema, que no tiene
`fastapi` (`ModuleNotFoundError: No module named 'fastapi'`). Con el venv
en el `PATH`, salida 0.

**La suite sobre `162d277` salió en rojo por mis casos, no por el
producto.** Seis casos de otros archivos
(`test_op_code_and_fill_if_empty.py`, `test_operations_manual.py` y cuatro
de `test_prelaunch_block1.py::TestOperacionManual`) recibían **402**
«Alcanzaste el límite de 15 operaciones del plan Premium». Las pruebas de
borrado de `test_datos1.py` creaban operaciones como `test_user`, que
comparte toda la suite, y le gastaban 4 de su cupo: lo medí al final de una
corrida de ese archivo solo, 4 sobre `162d277` y 0 sobre `c996ad4`, sin
clientes, operaciones ni presupuestos sobrantes. El arreglo (`c996ad4`):
cada prueba usa dueños propios y borra al terminar lo que creó. Con eso,
suite en verde y los 12 sabotajes siguen en rojo.

**Sabotajes (12, uno por regla), todos en rojo:** `/health` sin base sigue
en 200; `/health` vuelve a mostrar el error de la base; `/health` no deja
el error en el log; cada 500 vuelve a mandar `dev_detail` (uno por
manejador); cada 500 no deja el detalle en el log (uno por manejador); los
4xx pierden su motivo; no se borran los presupuestos del cliente; se
borran también los ajenos; el borrado no es una sola transacción; otro
dueño puede borrar el cliente.

**Comandos:**

```bash
git diff d01f95c..c996ad4 --stat        # 7 archivos
python -m pytest -q --no-cov -p no:randomly tests/test_datos1.py
#   9 passed
PY=<venv>/bin/python scripts/testing/sabotajes/datos1.sh c996ad4
#   12 líneas ROJO y al final «sabotajes sin rojo: 0»
python scripts/testing/datos1_postgres.py postgresql://cdi@127.0.0.1:<puerto>/<base>
#   8 líneas OK y «fallas: 0» (sólo acepta un Postgres local)
```

**Riesgos y lo que no hice:**
- **Un link compartido deja de andar** cuando se borra su cliente (es la
  D32 (a)): quien lo abra ve 404. Está en `CHANGELOG.md` y la pantalla v2
  lo avisa; la vieja no.
- **Previo, fuera de la pieza:** si alguien de un equipo cargó operaciones
  sobre el cliente, el borrado sólo toca las del dueño. En Postgres, las de
  otro miembro seguirían bloqueando el borrado del cliente por la clave
  foránea (500 y nada borrado). No lo probé.
- Los 502 y 503 de la app siguen pasando su `detail` tal cual: D6 habla de
  los 500 y no los toqué.
- La falla a mitad está probada con una falla simulada al borrar el
  cliente, el último paso. No probé una caída de la base a mitad.
- El texto nuevo de la pantalla no lo vi en el navegador: está en el código
  (`clientes.js:1816`) y no tiene prueba automática.
- **Fuera de la pieza: la suite está cerca del límite de `test_user`.** El
  resto de los archivos ya le gasta por lo menos 11 de sus 15 operaciones
  (con mis 4, caían). Un caso nuevo que cree unas pocas operaciones como
  `test_user` va a romper casos ajenos, con un 402 que no apunta al
  culpable. No lo toqué.
- Sin correr todavía: subagentes, `/code-review` y `/security-review`.
  Vuelven a las 18:00 UTC.

## DESPACHO-1b: hecha, **sin entregar** (2026-10-28)

Commits encima de SEGURO-1 (`371cde2`), de mi informe (`de9cb24`) y del
merge de tu rama (`49f8e29`): producto y `CHANGELOG.md` `0591722`; casos,
pantalla y sabotajes `e59e1a8`. **SHA probado: `e59e1a8`.** Para ver sólo
esta pieza: `git diff 49f8e29..e59e1a8`. Va en su propio `/entregar`,
después del de SEGURO-1, con subagentes y `/code-review` cuando vuelva el
cupo. **No hace falta que la revises todavía.** La D31 está contestada
(a) en `3da0a8b`: es lo que hice, sin cambios.

**La premisa: confirmada, sin Gemini y sin librería nueva.** El repo ya saca
texto de PDF con `pypdf` (el lector de facturas, `pdf_extractor.py`) y lo
corre aparte con su tope de tiempo (`_leer_pdf_aparte`). Uso lo mismo, con
los mismos topes de página.

- **Qué lee** (`proyecto_maria/core/despacho_lector.py`, nuevo): por
  renglón, posición SIM, descripción, sufijos, origen, unidad, cantidad,
  valor unitario y kilo neto. **Por rótulo:** busca la línea del rótulo y
  toma el valor de abajo en la misma columna. Hay una prueba con los
  rótulos en otro orden y otra con un valor vacío en el medio: sin kilo, el
  origen sigue siendo el origen (leyendo por posición, caería en el kilo).
- **Números** `1.234,56`. Otra forma (`12.5`, `1,234.56`) no se adivina:
  queda faltante, con un aviso.
- **Subítems:** con unidad `SUBITEM`, un renglón por subítem con su valor,
  descripción y sufijos. La posición y el origen se toman del ítem, y el
  aviso lo dice. Lo que al subítem le falta no se toma del ítem.
- **Lo que falta** queda en `faltantes`, vacío y marcado en pantalla. Nada
  se rellena: sin kilo, el peso queda vacío, no cero ni una cuenta.
- **Escaneado:** sin texto, avisa «El PDF no tiene texto que se pueda leer:
  parece escaneado…» y no devuelve renglones. Un PDF que no es despacho o
  está roto, también avisa.
- **Tilde rota** («Las dem?s»): la descripción queda como vino, con un
  aviso para que la corrijan en la revisión.
- **Divisa:** la del FOB, no la del flete (hay prueba con las dos
  distintas).
- **Pantalla** (Catálogo del cliente, `clientes.js`): «Cargar desde
  despacho» abre el selector, muestra los renglones editables con lo
  faltante marcado y guarda sólo al tocar «Guardar en el catálogo». La
  prueba de pantalla falla si se pide guardar antes del clic. Probada en
  1280 y 390 px.
- **Guardar** es todo o nada: si un renglón no sirve, 422 con qué le falta
  a cada uno y no se guarda ninguno. Pide posición con sus 8 dígitos y
  descripción; el origen, si viene, tiene que ser un país de la tabla. Tope
  de renglones (400 si se pasa). Lista vacía, 400.
- **De quién:** leer y guardar usan `_get_owned_client`: un cliente ajeno o
  de otro dueño da 404 y no se toca nada.
- **Nunca** arma un TXT ni una operación: hay pruebas que cuentan las
  operaciones antes y después y que fallan si se llama al generador. El
  lector de facturas sigue rechazando un despacho (prueba con el sintético).
- **Datos:** el sintético lo arma la prueba con la forma de
  `DESPACHOS-FORMA.md` y valores inventados: dos ítems, uno con subítems,
  un `AI` con espacios, «Las dem?s», FOB y flete en divisas distintas y un
  renglón sin kilo neto. Ningún despacho real.
- **Archivos de producto:** `proyecto_maria/core/despacho_lector.py`
  (nuevo), `proyecto_maria/main.py`, `proyecto_maria/static/v2/screens/clientes.js`,
  `proyecto_maria/static/v2/app_v2.css`,
  `proyecto_maria/templates/dashboard_v2.html` y `CHANGELOG.md`.

**Supuestos reversibles:**
- Los rótulos del subítem («Nº Subitem» y sus valores) son supuestos: los
  despachos de muestra no los traían con su rótulo. Están escritos en la
  cabecera de `despacho_lector.py`.
- La unidad, la cantidad y el valor unitario salen de «VALOR MERCADERIA».
- El peso que guarda el catálogo es por unidad: kilo neto dividido
  cantidad, si están los dos.

**Puertas sobre `e59e1a8`:**

| Puerta | Resultado |
|---|---|
| `tests/test_despacho1b.py` | 50 passed |
| Suite completa (`--timeout=120`) y `compileall` | 3827 passed, 336 skipped, 2 xfailed, 0 failed; `compileall` 0 |
| Sabotajes `scripts/testing/sabotajes/despacho1b.sh e59e1a8` | 24 líneas ROJO, «sabotajes sin rojo: 0», salida 0 |
| Pantalla `scripts/testing/pantalla_despacho1b.js` | OK en 1280 px (panel 644 px) y 390 px (panel 308 px) |
| `smoke_friccion.sh` (puerto 8855) | salida 0, «OK · telemetría + alias session/state + by-cuit protegido» |
| `ataque_aislamiento.sh` (puerto 8857) | salida 0, «PUERTA G3 PASADA. Ningún despachante ve datos de otro.» (cubre clientes y descargas; lo de esta pieza lo cubren sus pruebas de 404) |

La suite suma los 50 casos nuevos a los 3777 de SEGURO-1. Los 32 avisos
«Task was destroyed but it is pending!» de su salida ya estaban en las
suites de `4ca6829` y `a08de1f`: no son de esta pieza. Los sabotajes
corrieron también en `9dcd5cc` (mismo árbol que `e59e1a8`), con los mismos 24
rojos.

**Sabotajes (24, uno por regla), todos en rojo:** el subítem toma lo que le
falta del ítem; lo que falta no se marca; se lee por posición; se aceptan
números con otra forma; un número que no se entiende se lee igual; los
subítems no se separan; la posición heredada no se avisa; la divisa es la
del flete; un sufijo con espacios no se lee; un escaneado no avisa; sin
kilo se inventa el peso; leer no mira el dueño; guardar no mira el dueño;
se guarda lo bueno y se descarta el resto; guardar acepta una lista vacía;
guardar no tiene tope; leer acepta lo que no es PDF; guardar arma un TXT;
guardar crea una operación; el lector de facturas acepta despachos; el
botón no está conectado; el faltante no se marca en pantalla; se guarda al
leer, sin revisar; el panel es más ancho que la pantalla.

**Comandos:**

```bash
git diff 49f8e29..e59e1a8 --stat        # 9 archivos, ninguno en tests/fixtures
python -m pytest -q --no-cov tests/test_despacho1b.py
#   50 passed
PY=<venv>/bin/python scripts/testing/sabotajes/despacho1b.sh e59e1a8
#   24 líneas ROJO y al final «sabotajes sin rojo: 0»
PY=<venv>/bin/python BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_despacho1b.js
#   OK en 1280 y 390
```

**Riesgos y lo que no hice:**
- **No se probó con un despacho real** (no entran). Si el sistema del
  despachante pega dos columnas con un solo espacio, el valor puede quedar
  faltante: falla hacia «falta», no hacia un dato cambiado.
- **Costos de la D31 (a), decidida por la PM:**
  1. **El valor unitario queda sin divisa** en el catálogo: si el despacho
     estaba en otra moneda, la pantalla de revisión la muestra, pero el
     catálogo la pierde y su promedio puede mezclar monedas.
  2. **Dos subítems que sólo difieren en sufijos** (el `AI`) **se funden
     en un producto**, porque el catálogo junta por NCM y descripción
     parecida.
  Los sufijos, la unidad y la posición completa tampoco se guardan; se ven
  en la revisión.
- Dos renglones con el mismo NCM y descripción parecida (Jaccard ≥ 0,80,
  la regla de siempre del catálogo) se funden en uno: `guardados` puede
  decir más de lo que aparece.
- Guardar en un producto que ya existe promedia sus valores, como el
  aprendizaje de hoy.
- `leer` tiene el límite de pedidos del resto; `guardar` no, igual que el
  aprendizaje de hoy.
- El rechazo del lector de facturas pasa por Gemini, simulado en la prueba.
- Previos, no de esta pieza: `--t-12` no está definido en el CSS; el
  tablero mide 523 px de ancho en 390.
- La pantalla muestra en notación exponencial un número absurdo
  (`1e21`); no cambia lo que se guarda.
- Sin correr todavía: subagentes, `/code-review` y `/security-review`.
  Vuelven a las 18:00 UTC.

## SEGURO-1: hecha, **sin entregar** (2026-10-28)

Commits encima de SUFIJOS-2 (`4ca6829`) y del merge de tu rama
(`1948207`): producto y `CHANGELOG.md` `4f75f3d`; casos y sabotajes
`a08de1f`; un sabotaje con su patrón arreglado `371cde2`. **SHA probado:
`371cde2`.** Sabotajes 10/10 en rojo en `371cde2`
(`scripts/testing/sabotajes/seguro1.sh`) y suite completa en `a08de1f`:
3777 passed, 336 skipped, 2 xfailed, 0 failed (`compileall` limpio). Entre `a08de1f` y `371cde2` sólo cambia el script de
sabotajes, que pytest no junta. Va en su propio `/entregar`, después del de SUFIJOS-2,
con `/security-review` porque es un campo de dinero. **No hace falta que la
revises todavía.** La D30 ya está contestada (a).

**La premisa: confirmada.** `cuentas_del_valor` no conocía el incoterm,
pero quien la llama (`_cuentas_del_valor` en `main.py`) tiene
`request.incoterm`. Se lo paso: la regla vive en el servidor sin salir del
alcance.

- **La regla, en el servidor:** `INCOTERMS_CON_SEGURO = ("CIF", "CIP",
  "DPU", "DAP", "DDP")` en `maria_generator.py`. Con esos, las cuentas
  traen `seguro_sugerido: None` y `seguro_en_el_precio: true`. Con los
  demás, el 1 % como antes. Mayúsculas, minúsculas y espacios dan lo mismo
  (`" cif "` es CIF); vacío o desconocido (`"XYZ"`, `"C I F"`), con 1 %.
- **La pantalla sigue al servidor**, no al incoterm de la operación: sin
  `seguro_en_el_precio` hay botón aunque la operación diga CIF (hay una
  prueba que lo fija). Con CIF no hay «Calcular seguro» ni «Dejar el
  seguro», y `calcularSeguro()` no pone nada. La nota dice «Con CIF el
  seguro ya está en el precio: el sistema no lo calcula.» y agrega que lo
  carguen en la revisión si no hay seguro.
- **El seguro se sigue declarando:** una operación CIF con seguro 14,88
  sale con `MDDTASS 14.88` y `CDDTINCOTE CIF`. Un seguro escrito de 93,13
  (el mismo número que daría el 1 %) con CIF también genera: es de la
  persona.
- **Cambio de incoterm con el seguro calculado:** cuando llegan las cuentas
  del pedido de ahora con `seguro_en_el_precio` y la operación tiene
  `seguro_calculado`, la pantalla borra el seguro, saca la marca, lo agrega
  a `campos_sin_leer` (el mismo mecanismo que un campo que el lector no
  leyó) y lo saca de `campos_completados`. El semáforo dice «No pudimos leer
  el seguro de la factura: completalo.». Con cuentas de otro pedido no
  borra nada. El leído o escrito no se toca. De CIF a CFR vuelve el botón y
  no pone nada solo.
- **El servidor también frena:** un pedido con `seguro_calculado` y uno de
  los cinco da 400 «Seguro: lo calculó el sistema, pero con CIF el seguro ya
  está en el precio y no se calcula. Cargá el de la factura en la
  revisión.», en `/generate_maria` y en los avisos, aunque las cuentas
  estén en error. Cubre una pestaña con el `finalize.js` viejo.
- **El golden no se tocó:** `git diff 1948207..a08de1f -- tests/fixtures`
  sale vacío.
- **Dos pruebas existentes cambiaron, sin cambiar lo que miden:** en
  `tests/test_valor1.py` la expectativa de las cuentas suma
  `"seguro_en_el_precio": False`, y la función nueva
  `borrarSeguroCalculado` se suma a las listas de los arneses de pantalla de
  `test_valor1.py` y `test_valor1c.py` (extraen funciones por nombre).
- **Archivos de producto:** `proyecto_maria/core/maria_generator.py`,
  `proyecto_maria/main.py`, `proyecto_maria/static/v2/screens/finalize.js` y
  `CHANGELOG.md`.

**Supuestos reversibles:**
- El borrado usa `campos_sin_leer`, que es la lista del lector. Por eso el
  semáforo dice «No pudimos leer el seguro de la factura», aunque lo que
  pasó es que el sistema lo borró. Si preferís otro texto, es un aviso
  propio en `semaforo.js`.
- La nota nombra el incoterm de la operación («Con CIF…»); si falta, dice
  «este incoterm».
- El 400 del servidor con un calculado y CIF no estaba pedido: es la regla
  «vive en el servidor» aplicada a `seguro_calculado`. Sin él, una pestaña
  vieja mandaría el 1 % con CIF.

**Sabotajes (uno por regla):** DPU fuera de la lista; el incoterm sin
normalizar; `main.py` no pasa el incoterm; la pantalla decide por
`op.incoterm`; el botón calcula con CIF; `pintarValor` no borra; el
servidor no frena el calculado con CIF; se borra también el escrito; se
borra sin mirar la firma del pedido; el borrado deja el seguro como
completado. En la primera corrida, el del incoterm en `main.py` no
encontraba su patrón (la línea aparece cuatro veces): lo arreglé en
`371cde2` con un patrón que aparece una sola vez.

**Comandos:**

```bash
git diff 1948207..371cde2 --stat                 # 8 archivos; tests/fixtures no aparece
git diff 1948207..371cde2 -- tests/fixtures | wc -l   # 0
PY=<venv>/bin/python scripts/testing/sabotajes/seguro1.sh 371cde2
#   10 líneas ROJO y al final «sabotajes sin rojo: 0»
python -m pytest -q --no-cov tests/test_seguro1.py tests/test_valor1.py tests/test_valor1c.py
#   151 passed
```

**Riesgos y lo que no hice:**
- **Seguro 0 en el TXT si nadie lo completa** (D30, contestada (a)): un seguro «para completar» avisa en pantalla y no frena el TXT. Frenarlo es SEGURO-2.
- `finalize.js` se carga con `?v={{ version }}`; una pestaña abierta antes
  del despliegue sigue con el JS viejo y muestra el botón con CIF. Si lo
  aprieta, el servidor da el 400 de arriba: no sale el 1 % en el TXT.
- Sin correr todavía: subagentes, `/code-review` y `/security-review`.
  Vuelven a las 18:00 UTC.

## SUFIJOS-2: hecha, **sin entregar** (2026-10-28)

Commits encima de `4905cd8`: casos en rojo `a12aae3`; producto y
`CHANGELOG.md` `79dc0c6`; sabotajes `b5c63c8`; un caso más en rojo
`34ff7f0`, su arreglo `0118f5f` y su sabotaje `f2e09d8`; el comentario en
líneas cortas `4ca6829`. **SHA probado: `4ca6829`.** Sabotajes 9/9 en rojo
(`scripts/testing/sabotajes/sufijos2.sh`) y suite completa en `4ca6829`:
3731 passed, 336 skipped, 2 xfailed, 0 failed. Va en su propio `/entregar`, después del de DESTINO-1, cuando
vuelva el cupo. **No hace falta que la revises todavía.** La D29 ya
está contestada (a).

- **Sufijo libre:** un número con decimales sale con coma. `AF(2.5)` sale
  `AF(2,5)`. Un punto o una coma cuentan como decimal sólo entre dígitos y
  una sola vez: `V1.2.3` sale `V1 2 3`, como antes, y `ROJO, AZUL` sale con
  espacio. Vale también para la propuesta que arma el arancel.
- **Sufijo que pide número** (los `Z`, D29 contestada (a)) con decimales: no se
  genera. El error dice dónde (operación, ítem, sub-ítem o renglón) y cuál
  sufijo, y llega como 400.
- **Ninguno vacío:** `AA()`, `AA(   )` o `AA(--)` (que queda vacío al
  limpiar) no se generan. Mismo tipo de error.
- **Lo que sigue igual:** los `Z` enteros con la forma del archivo aceptado
  (`ZA(016384)`…) y los sufijos que ya traían coma. El golden no cambió:
  `git diff 4905cd8..4ca6829 -- tests/fixtures` sale vacío.
- **Una prueba existente cambió:**
  `tests/test_sufijos1.py::test_un_codigo_con_el_valor_vacio_es_un_codigo_que_falta`
  esperaba que `AA( )` generara con el aviso de un código que falta. La
  regla nueva dice que no se genera: ahora es
  `test_un_codigo_con_el_valor_vacio_no_se_genera`.
- **Archivos de producto:** `proyecto_maria/core/maria_generator.py` y
  `proyecto_maria/core/sufijos_arca.py`.

**La premisa.** Que la coma no rompe el campo sí se sabe desde el repo: el
TXT es `CLAVE=valor` por línea, y el archivo real de 2026 ya trae una coma
en `LDDTNOMFOD`. El paréntesis se toma entero, en el generador y en
`despachante.js`, así que la coma de adentro no parte el sufijo. Cuáles
piden número **no** se sabe desde el repo: es la D29.

**Rojo encontrado en la autorrevisión.** `\d` en Python también toma
dígitos que no son ASCII. Con eso, `٣.٥` salía `٣,٥` en el TXT. Primero el
caso en rojo (`34ff7f0`), después el arreglo con `[0-9]` (`0118f5f`) y su
sabotaje.

**Riesgos y lo que no hice:**
- En un sufijo libre, `1.234` con punto de miles sale `1,234`, que se lee
  como 1 con decimales. No hay forma de distinguirlos.
- En un `Z`, `1.234` da error y no se lee como 1234. Es a propósito: no se
  adivina.
- Fuera de alcance, sin tocar: un `Z` con texto (`16 GB`, `2 5`) pasa; el
  generador no rellena con ceros a seis dígitos como el archivo aceptado.
  Si querés, lo propongo como pieza.
- Sin correr todavía: subagentes, `/code-review` y `/security-review`.
  Vuelven a las 18:00 UTC.

## DESTINO-1: hecha, **sin entregar** (2026-10-28)

Producto `7526be9`, pruebas y sabotajes hasta `f887b4a`, encima de
`4ce6d22`. Sabotajes 15/15 en rojo (`scripts/testing/sabotajes/destino1.sh`)
y suite completa en `f887b4a`: 3697 passed, 0 failed. Va en su propio
`/entregar`, después del de ORG-1, cuando vuelva el cupo. **No hace falta que
la revises todavía.** Ojo con D28: no eran seis pruebas las que comparan el
golden entero, son ocho (se sumaron `test_maria1b_controles` y
`test_maria3_antes_de_generar`); las dos con el mismo criterio de (a).

## ORG-1, ORG-1b y DESPACHO-1a: listas, **sin entregar** (2026-10-28)

**DESPACHO-1a está hecha** (producto `e438dad`, probado en `51890cd`), en
commits aparte sobre ORG-1b. Va en el mismo `/entregar` que ORG-1 y ORG-1b,
con su propio apartado y su diff: «DESPACHO-1a», abajo.

**ORG-1b (D27 b) está hecha**, en commits aparte, con su propio SHA de
producto (`f8616cf`). Va en el mismo `/entregar` que ORG-1. Detalle en
«ORG-1b», abajo.

**ORG-1. Estado:** los cinco puntos están hechos. Tienen casos en SQLite, un script
contra Postgres, sabotajes y suite completa. **No la entrego todavía.** Tu
canal dice «`/entregar` espera a que vuelva el cupo», y el cupo de
subagentes y `/code-review` vuelve el 28/10 a las 18:00 UTC. Ahí corro la
autorrevisión independiente y `/security-review`, reproduzco lo que
encuentren y entrego con el timbre. Subo ahora para que el trabajo no se
pierda si el contenedor muere. **No hace falta que la revises todavía.**

## Decisiones

**D32 — qué pasa con el presupuesto compartido al borrar su cliente (DATOS-1, D5).**
Hoy borrar un cliente ya borra sus operaciones (es lo que dice el código
desde antes). Un presupuesto compartido (`public_quotes`) apunta a una
operación y no puede quedar sin ella (`operation_id` es obligatorio), así
que para borrar el cliente hay que elegir. El presupuesto guarda una copia
con la descripción, cantidad y valor de cada producto del cliente, el
costo calculado y el nombre del usuario.

- **(a) Recomiendo esta.** Se borran también los presupuestos compartidos de
  las operaciones del cliente, en la misma transacción. El link deja de
  andar (404) antes de vencer. Es coherente con lo que ya hace el borrado
  (borra las operaciones) y es lo único que cumple un pedido de supresión:
  la copia tiene datos del cliente. Pierde: el link compartido.
- **(b)** Las operaciones con presupuesto compartido quedan sin cliente
  (`client_id` vacío) y el presupuesto sigue hasta que venza. Pierde menos
  hoy, pero no cumple la supresión: quedan la operación y la copia, y como
  los vencidos sólo se borran si alguien abre el link, quedan para siempre.
  Esas operaciones no aparecen en ningún cliente.
- **(c)** No borrar: responder 409 «tiene presupuestos compartidos» en vez
  del 500. No pierde nada, pero no hay forma de dar de baja un presupuesto,
  así que el cliente sigue sin poder borrarse: no resuelve D5.

**D31 — contestada (a) en `3da0a8b`.** El catálogo guarda lo que ya tiene
columna; los dos costos están en los riesgos de DESPACHO-1b.

**D30 — contestada (a) en `53e1e86`.** Un seguro «para completar» sigue siendo un aviso; SEGURO-2 no la empiezo hasta verla en tu canal.

**D29 — contestada (a) en `3d3ab47`.** `PIDE_NUMERO = ("Z",)` queda.

**D28 — contestada (a) en `be1cac2`.** DESTINO-1 rompe seis pruebas que
comparan el golden entero. No
frena la entrega de ORG-1, ORG-1b y DESPACHO-1a; frena DESTINO-1, que
arranco apenas entregue. Lo aviso ahora porque pediste que avise antes de
cambiar una prueba que compara el golden.

Estas pruebas generan con `iva_adicional="IVAAD1"` y comparan contra
`maria_golden_anon.TXT` todo el archivo, byte a byte. El golden trae
`COMERC` + `IVAAD1`:

- `tests/test_generar_maria_txt.py::test_golden_reproduce_estructura_real`
- `tests/test_maria1b_controles.py::test_el_archivo_real_sale_identico_por_la_ruta`
- en `tests/test_punta_a_punta1.py`, las cuatro que comparan con
  `_GOLDEN_PATH`: líneas 433, 438, 445 y 478.

Con DESTINO-1, `IVAAD1` se lee como bien de uso de una persona. Eso da
`USOPAR` + `IVAAD1`, que difiere del golden en una línea: el `MCPL` de
`GANANCIASOP3`. Ningún par permitido da `COMERC` + `IVAAD1`, así que no
hay entrada que reproduzca el golden entero. El golden de subítems trae
`COMERC` + `NO_VALIDA`, que es un par permitido, y no cambia.

- **(a) Recomiendo esta.** El golden no se toca. Las seis pruebas comparan
  el archivo entero salvo esa línea, y la prueba exige que esa línea diga
  exactamente `USOPAR`. Así cualquier otro cambio sigue apareciendo y la
  diferencia queda escrita, con referencia a la pregunta 7 al despachante.
- **(b)** Las pruebas siguen generando con comercialización. Ahí la línea
  que difiere pasa a ser la de `IVAADICIONAL1` (`NO_VALIDA` en vez de
  `IVAAD1`). El arreglo de las pruebas es el mismo de (a), pero muestra un
  caso que el MARIA nunca vio.
- **(c)** DESTINO-1 espera la respuesta a la pregunta 7.

D26 y D27 ya están contestadas: D26 (a) por ahora, D27 (b) como ORG-1b.

| Pieza | SHA |
|---|---|
| Casos en rojo antes del producto | `9d727e7` |
| Producto y `CHANGELOG.md` | `e43810b` |
| Sabotajes (9, uno por motivo) | `18f7f25` |
| Carrera de dos invitaciones a la vez, en Postgres | `ddfc798` |
| **SHA probado:** suite, compileall, smoke, aislamiento | **`18f7f25`** |
| ORG-1b: la prueba de pantalla, en rojo antes del producto | `9ad42e4` |
| **ORG-1b: producto y `CHANGELOG.md`** | **`f8616cf`** |
| ORG-1b: sabotajes (7, uno por motivo) | `b7a7927` |
| ORG-1b: arreglo de la prueba (dos sabotajes no daban su rojo) | `5d42909` |
| **ORG-1b, SHA probado:** pantalla y sabotajes | **`5d42909`** |

Entre `18f7f25` y `ddfc798` sólo cambia `scripts/testing/org1_postgres.py`,
que pytest no junta. Tu diff de revisión de ORG-1 parte de `ea64a9c`, la
punta de tu rama.

ORG-1b está encima de `ddfc798`, pero no pegada a él. En el medio quedan mi
informe (`de8d175`) y el merge de tu rama (`373ef55`). Ninguno de los dos
toca producto. Para ver sólo ORG-1b: `git diff 373ef55..5d42909`.

Toqué estos archivos de producto:
- `proyecto_maria/main.py` (ORG-1)
- `proyecto_maria/templates/landing.html` (ORG-1b)
- `CHANGELOG.md` (las tres)
- `proyecto_maria/main.py`, `proyecto_maria/templates/dashboard_v2.html` y
  `proyecto_maria/static/v2/screens/clientes.js` (DESPACHO-1a)

## 1. La premisa: confirmada

Corrí `org1_postgres.py` contra un Postgres 16 local con el código de
`ea64a9c`. El resultado fue `fallas: 15`. Cada 500 trae en el log
`TypeError: can't compare offset-naive and offset-aware datetimes` (15
veces). Es tu sospecha: asyncpg devuelve `expires_at` con zona, y se compara
con `datetime.utcnow()`, que no tiene zona. Validar, registrarse, una
vencida y una usada daban 500 en Postgres. Invitar no daba 500, porque no
compara fechas.

## 2. Qué cambió, por punto

Todo está en `proyecto_maria/main.py`.

1. **Sin 500 en las dos bases.** El registro y `validate_invitation`
   comparan `_utc(expires_at) < datetime.now(timezone.utc)`. `_utc` ya
   existía y toma una fecha sin zona como UTC. Así entran los registros
   viejos de SQLite y los de Postgres, que vienen con zona.
2. **Atada al email.** Al registrarse con `invite_token`, el email del
   registro, ya con `strip().lower()`, tiene que ser el de la invitación. Si
   no, responde 400 «Esta invitación es para otro email. Registrate con el
   email al que te invitaron.». La invitación sigue pendiente y no se crea el
   usuario. Una invitación sin email no deja entrar a nadie. El otro camino
   que pone `organization_id` es `/api/organizations/create`, que es el
   dueño creando su estudio. Sacar un miembro lo vuelve a `None`. No hay
   camino para que una cuenta existente se sume.
3. **Tope del plan.** El tope sale de
   `billing_service.get_plan(org.plan or "premium")["users"]`. Un helper
   nuevo, `_emails_de_miembros`, cuenta los usuarios del estudio, dueño
   incluido.
   - Al invitar: responde 400 «El estudio ya ocupa los {tope} usuarios de
     su plan, contando las invitaciones pendientes.» si miembros más
     pendientes sin vencer llegan al tope.
   - Al registrarse: responde 400 «El estudio ya tiene los {tope} usuarios
     de su plan.» si los miembros ya llegaron. Hace rollback y la invitación
     queda pendiente.
4. **Un solo uso.** Pasos del registro:
   - Gasta la invitación con
     `UPDATE invitations SET status='accepted' WHERE id=… AND status='pending'`.
   - Comprueba `rowcount == 1`; si no, hace rollback y responde 400 «Esta
     invitación ya fue usada».
   - Recién después cuenta el tope.
   - Hace un solo commit con el usuario.

   El estudio se lee con `FOR UPDATE` al invitar y al registrarse.

## 3. Qué deja una carrera

| Carrera | Antes (`ea64a9c`) | Ahora |
|---|---|---|
| Dos registros con la misma invitación, SQLite | `[(200, ''), (500, 'No pudimos procesar tu solicitud…')]` | `[200, 400 «ya fue usada»]`, un usuario, invitación `accepted` |
| Lo mismo, Postgres | dos 500 (el `TypeError`) | `[(200, ''), (400, 'Esta invitación ya fue usada')]` |
| Dos registros con invitaciones distintas por el último lugar, SQLite | `[(200, ''), (200, '')]`: entran los dos | `[200, 400 «los 2 usuarios»]`, miembros 2, `['accepted', 'pending']` |
| Lo mismo, Postgres | dos 500 | `[(200, ''), (400, 'El estudio ya tiene los 2 usuarios de su plan.')], miembros 2, ['accepted', 'pending']` |
| Dos invitaciones enviadas a la vez por el último lugar, Postgres | `[(200, ''), (200, '')], pendientes 2` | `[(200, ''), (400, 'El estudio ya ocupa los 2 usuarios de su plan, contando las invitaciones pendientes.')], pendientes 1` |
| Lo mismo, SQLite | — | **No está protegido** (riesgo abajo) |

Cómo se serializa cada base:
- **SQLite:** el primer `UPDATE` del registro toma el candado de escritura
  de la base. Por eso el tope se cuenta después de gastar la invitación: el
  otro registro espera y cuenta con el primero ya adentro.
- **Postgres:** el `FOR UPDATE` sobre el estudio serializa los registros y
  las invitaciones del mismo estudio.

Las carreras son reales, no secuenciales. En SQLite, dos hilos esperan
juntos en una barrera después del hash de la clave. En Postgres, cada
invitación espera en su commit, ya pasado el control del tope. Espera a que
la otra también llegue al commit o quede frenada en el candado, mirado en
`pg_stat_activity`. No hay esperas fijas: el plazo de 20 s sólo corre si no
pasa ninguna de las dos.

## Supuestos reversibles

- **Las pendientes cuentan por email distinto.** Una pendiente de alguien
  que ya es miembro no cuenta. Reinvitar a un email pendiente no ocupa otro
  lugar y responde 200, como hoy.
- **El `FOR UPDATE` sobre el estudio**, al invitar y al registrarse. Es una
  fila por estudio y por pedido, no un candado global.
- **Los tres textos de error nuevos** (arriba).
- **Una invitación «expired» con fecha futura** responde «ya fue usada»,
  porque no está pendiente. Hoy sólo `validate_invitation` marca «expired»,
  y lo hace con la fecha vencida, así que no debería existir.

## D26 y D27: contestadas

- **D26 (a) por ahora.** No hay forma de cancelar una invitación pendiente.
  Se lo proponés a Emi. No la empiezo sin tu aviso.
- **D27 (b): es ORG-1b**, abajo.

## ORG-1b: el registro con invitación trae el email invitado

En `landing.html`, cuando `/api/invitations/{token}` responde válida y trae
email:
- El email del registro se completa con ese email.
- Queda `readOnly`, no `disabled`, así viaja en el envío.
- Debajo aparece «Es el email al que te invitaron.».

Sin `invite`, con un token que no existe, con uno ya usado o con una
respuesta válida sin email, el campo queda como antes: vacío y editable. El
servidor no cambia, y su 400 sigue siendo la guarda.

**La prueba** es `scripts/testing/pantalla_org1b.js`. Usa Playwright, la API
local de verdad y datos inventados. Los casos van en este orden:

1. Sin `invite`, y con un token que no existe: el campo queda vacío y
   editable, y la línea no se ve. El registro se abre con el botón del
   inicio, como lo haría una persona.
2. Respuesta válida sin email: igual que el caso 1. Es el único caso con la
   respuesta simulada (`page.route`), porque la API no deja invitar sin
   email.
3. Invitación válida con el email cambiado a mano en el DOM (se le sacan
   `readOnly` y `disabled`): da 400, y el error dice «otro email».
4. Invitación válida:
   - el email viene completo, es de sólo lectura y no `disabled`;
   - la línea se ve;
   - escribir encima no lo cambia;
   - el registro da 200, manda el email y el token, y la invitada queda en
     el estudio.
5. El mismo token ya usado: igual que el caso 1.

**Rojo antes del producto** (contra `373ef55`): `FALLA: con invitación
válida el email no viene completo: {"value":"","readOnly":false,"disabled":false}`.

**Dos sabotajes no daban su rojo en la primera vuelta**, y los arreglé en la
prueba (`5d42909`):
- **«La línea se ve siempre»:** sin invitación válida, el registro está
  cerrado, así que «no se ve» era cierto para cualquier cosa. Ahora la
  prueba abre el registro antes de mirar.
- **«Además disabled»:** caía antes, en el caso del DOM, con un 422. Ahora
  ese caso saca también `disabled`, como haría quien edita el DOM.

| Sabotaje (`sabotajes/org1b.sh`) | Rojo |
|---|---|
| no se completa el email | «con invitación válida el email no viene completo» |
| el email completo queda editable | «con invitación válida el email no es de sólo lectura» |
| además `disabled` (no viaja en el envío) | «con invitación válida el email está disabled» |
| la línea del email invitado no aparece | «con invitación válida no se ve la línea del email invitado» |
| la línea se ve siempre | «sin invite: se ve la línea del email invitado» |
| se bloquea aunque la invitación no traiga email | «válida sin email: el email no queda vacío y editable» |
| el servidor deja de exigir el email invitado | «con el email cambiado en el DOM el registro dio 200, no 400» |

**Supuesto reversible:** el texto «Es el email al que te invitaron.».

La captura a 390 px se ve bien. El campo de sólo lectura se ve igual que uno
editable; lo explica la línea de abajo. No le cambié el estilo, porque no lo
pediste.

## DESPACHO-1a: el catálogo del cliente en Excel

En la pestaña Catálogo del cliente, arriba de «Productos aprendidos», hay un
botón «Descargar en Excel». Baja `GET /api/clientes/{id}/catalogo/productos.xlsx`:
- un renglón por producto de `ClientProductHistory` de ese cliente y ese
  dueño, en el orden de la pantalla (el último usado primero);
- columnas: Posición, Descripción, Origen, Valor unitario promedio,
  Cantidad promedio, Peso unitario promedio, Veces usado, Última vez;
- un cliente ajeno o que no existe da el mismo 404 que
  `/catalogo/productos` (`_get_owned_client`); sin sesión, 401;
- todo texto se escribe como texto. El que empieza con `=`, `+`, `-` o
  `@` además lleva el apóstrofo invisible (`quotePrefix`), así sigue
  siendo texto si alguien edita la celda;
- la posición va como texto y con formato de texto (`@`), tal como está
  guardada: `01012100`, `0402100Z`, `0101.21.00`.

Toqué `proyecto_maria/main.py` (el endpoint y `_catalogo_xlsx`),
`proyecto_maria/templates/dashboard_v2.html` (el botón),
`proyecto_maria/static/v2/screens/clientes.js` (la descarga) y
`CHANGELOG.md`.

| Pieza | SHA |
|---|---|
| Casos en rojo antes del producto | `ee82997` |
| **Producto y `CHANGELOG.md`** | **`e438dad`** |
| Prueba en el navegador y sabotajes (14, uno por motivo); ajuste del mensaje del caso de aislamiento | `51890cd` |
| **SHA probado** | **`51890cd`** |

Su diff propio parte del merge de tu rama que trajo la tarea:
`git diff fe1571c..51890cd`.

**Rojo antes del producto:**
- `tests/test_despacho1a.py` contra `fe1571c`: `13 failed, 5 warnings in 0.70s`;
  todos por la ruta que no existía (`{"detail":"Not Found"}`).
- `pantalla_despacho1a.js` contra `fe1571c`:
  `FALLA: 1280 px: no se ve «Descargar en Excel»`, salida 1.

**Los casos** (`tests/test_despacho1a.py`, 13 con los parametrizados):
- el archivo se abre con openpyxl y trae lo guardado, fila por fila y en
  orden;
- la posición como texto, con ceros y letra;
- el catálogo vacío trae sólo los encabezados;
- `=HYPERLINK(...)`, `+1+1`, `-2+3` y `@SUMA(A1)` en la descripción, y
  `=1` en el origen, quedan como texto con `quotePrefix`;
- caracteres de control en la descripción no rompen la descarga;
- el nombre del archivo es ASCII aunque el cliente se llame
  «Ñandú Café — … 🚢»;
- otro dueño recibe el mismo 404 que el catálogo de la pantalla, y en el
  cuerpo no aparece el producto;
- un cliente que no existe da 404;
- no se mezclan productos de otro cliente ni de otro dueño;
- sin sesión da 401.

**En el navegador** (`scripts/testing/pantalla_despacho1a.js`, API local y
datos inventados, 1280 y 390 px): carga dos productos, uno con `=1+1` en
la descripción, abre el catálogo, aprieta el botón, baja el archivo y lo
lee con openpyxl. Compara las descripciones con la pantalla y las
posiciones con la API, y exige que sean texto. Salida:
`OK 1280 px: «catalogo_cliente_inventado_d1a_1280.xlsx» trae ["=1+1 NOTEBOOK INVENTADA","CABALLO INVENTADO"], posiciones ["8471.30.12","0101.21.00"], todo como texto`,
y lo mismo a 390 px.

**Sabotajes** (`scripts/testing/sabotajes/despacho1a.sh 51890cd`): salida
0, `sabotajes sin rojo: 0`. Sin sabotaje, las pruebas y la pantalla dan
verde.

| Sabotaje | Rojo (copiado de la salida) |
|---|---|
| no se mira de quién es el cliente | `test_otro_dueno_recibe_el_mismo_404_que_en_el_catalogo`, «assert 200 == 404» |
| la consulta no filtra por dueño | `test_no_se_mezclan_…`, «trae productos de otro dueño» |
| la consulta no filtra por cliente | `test_no_se_mezclan_…`, «trae productos de otro cliente» |
| se puede bajar sin sesión | `test_sin_sesion_da_401`, «assert 404 == 401» |
| «=» queda como fórmula | `test_una_descripcion_con_formula_queda_como_texto[=HYPERLINK…]`, «assert 'f' == 's'» |
| sin el apóstrofo invisible | `…[+1+1]` y `…[@SUMA(A1)]`, «quotePrefix» |
| la posición sólo de dígitos sale como número | `test_la_posicion_sale_como_texto_con_ceros_y_letra`, «1012100» |
| la posición sin formato de texto | `test_la_posicion_…`, «number_format» |
| el orden no es el de la pantalla | `test_el_archivo_se_abre_y_trae_lo_guardado`, «TELEFONO INVENTADO» |
| cantidad y peso cruzados | `test_el_archivo_…`, «450.25» |
| el catálogo vacío sale sin encabezados | `test_un_catalogo_vacio_trae_solo_los_encabezados` |
| no se limpian los caracteres de control | `test_una_descripcion_con_caracteres_de_control_…`, «IllegalCharacterError» |
| el nombre del archivo va como viene | `test_el_nombre_del_archivo_es_ascii`, «UnicodeEncodeError» |
| el botón no está conectado | `FALLA: 1280 px: el botón no bajó nada` |

En la primera vuelta, el sabotaje «no filtra por cliente» dio rojo, pero
el mensaje de pytest cambiaba según las pruebas de antes en la misma base.
Le puse al caso un mensaje propio para cada fuga (`51890cd`). El rojo es
el mismo, ahora se lee.

**Puertas de DESPACHO-1a, sobre `51890cd`:**

| Puerta | Resultado |
|---|---|
| Las 12 de `tests/` que tocan clientes, catálogo o DESPACHO-1a | `249 passed, 3 warnings in 71.12s (0:01:11)` |
| `compileall -q proyecto_maria` | `compile-ok` (rc 0) |
| `node --check …/clientes.js` | `js-ok` |
| `pantalla_despacho1a.js` | `OK 1280 px …` y `OK 390 px …`, salida 0 |
| `sabotajes/despacho1a.sh 51890cd` | `sabotajes sin rojo: 0`, salida 0 |

**Sin correr todavía**, para el `/entregar` del 28/10 a las 18:00 UTC: la
suite completa sobre el SHA final, `smoke_friccion.sh`,
`ataque_aislamiento.sh` (no cubre esta ruta nueva: el aislamiento de esta
ruta lo cubren los casos y tres sabotajes), subagentes, `/code-review high`
y `/security-review`.

**Supuestos reversibles:**
- Se limpian los caracteres de control que Excel no acepta. Sin eso, la
  descarga da 500 con una descripción así.
- El nombre del archivo, en ASCII: `catalogo_<nombre>.xlsx`. El servidor
  y la pantalla lo arman cada uno, con el mismo criterio.
- El apóstrofo invisible (`quotePrefix`) en lo que empieza con
  `=`, `+`, `-` o `@`.
- La fecha como fecha de Excel, `dd/mm/yyyy`, y el día en UTC, igual que
  la pantalla (`slice(0, 10)`).
- El texto del botón, «Descargar en Excel», y el toast «Descarga iniciada.».

**Riesgos de DESPACHO-1a:**
- **Empates en «última vez».** En Postgres, los productos aprendidos en un
  mismo pedido llevan el mismo `now()`. El orden entre ellos no está fijado,
  ni en la pantalla ni en el Excel, y puede salir distinto entre una y
  otro. No lo arreglé: cambiaría también la consulta de la pantalla.
- **Un texto de más de 32767 caracteres** se escribe entero; Excel lo corta
  al abrirlo o se queja. No lo vi en el catálogo; no lo traté.
- **Un promedio NaN** se escribiría como NaN. El aprendizaje no debería
  dejarlo; no lo traté.
- **A 390 px el tablero ya se corre 133 px de costado**, con o sin el botón
  (lo medí también sacando el botón). El botón se ve entero. No es de esta
  pieza y no lo toqué.

## Puertas de ORG-1 y ORG-1b

| Puerta | Resultado |
|---|---|
| `tests/test_org1.py` sobre `ddfc798` | `46 passed, 3 warnings in 31.56s` |
| Los mismos casos contra `ea64a9c` | `36 failed, 10 passed, 39 warnings in 45.26s` |
| `org1_postgres.py`, Postgres 16 local, sobre `ddfc798` | `fallas: 0`, 3 de 3 corridas |
| Lo mismo contra `ea64a9c` | `fallas: 15` |
| `sabotaje_org1.sh 18f7f25` | `OK: los 9 sabotajes dan rojo por la razón esperada`, salida 0 |
| Suite completa, worktree limpio en `18f7f25` | `1 failed, 3323 passed, 302 skipped, 2 xfailed, 94 warnings in 505.43s (0:08:25)` |
| `compileall -q proyecto_maria` | rc 0 |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `ataque_aislamiento.sh` | `Bloqueado: 22 · Fugas: 0`, «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.» |
| ORG-1b: `sabotajes/org1b.sh 5d42909` | `sabotajes sin rojo: 0`, salida 0; los 7 dan su rojo, y sin sabotaje la prueba da verde |
| ORG-1b: `pantalla_org1b.js` contra `373ef55` | `FALLA: con invitación válida el email no viene completo`, salida 1 |
| ORG-1b: `test_pa1_textos`, `test_regression_phase0`, `test_static_endpoints` (las que leen la landing) y `test_org1`, sobre `5d42909` | `93 passed, 1 skipped, 3 warnings in 32.68s` |

Los casos corren cada uno dos veces, `sqlite_sin_zona` y
`postgres_con_zona`. El segundo inyecta un `expires_at` con zona al cargar
la fila, que es lo que hace asyncpg.

**El único rojo de la suite** es
`test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`.
Es el de tiempo ya informado en SUFIJOS-1, 1c y 1d: «la subida normal dio
400 a los 30.0 s: … tardó demasiado». ORG-1 no toca la lectura de Excel.

**Sabotajes** (`sabotaje_org1.sh`). Cada uno vuelve a lo de antes o rompe
una guarda:

| Sabotaje | Qué hace | Rojos |
|---|---|---|
| `fecha_sin_zona` | vuelve a comparar con `datetime.utcnow()` | 14 failed |
| `sin_email` | cualquiera con el enlace entra | 10 failed |
| `invitar_sin_tope` | invitar sin tope | 13 failed |
| `tope_fijo` | tope 3 escrito a mano | 10 failed |
| `vencida_ocupa` | guarda: una pendiente vencida ocupa lugar | 2 failed |
| `reinvitar_ocupa` | guarda: reinvitar ocupa otro lugar | 1 failed |
| `registro_sin_tope` | registrarse sin tope | 3 failed |
| `gasto_sin_condicion` | gasta sin mirar si seguía pendiente | 2 failed |
| `contar_antes` | cuenta el tope antes de gastar (la carrera de SQLite) | 1 failed |

Dos sabotajes más se aplicaron a mano en Postgres, porque el candado sólo se
ve ahí:
- Sin `FOR UPDATE` al invitar: `FALLA | dos invitaciones a la vez por el
  último lugar: sale una ([(200, ''), (200, '')], pendientes 2)`, 3 de 3.
- Sin `FOR UPDATE` al registrarse: `FALLA | dos invitaciones por el último
  lugar: entra una ([(200, ''), (200, '')], miembros 3, ['accepted',
  'accepted'])`, 3 de 3.

**Lo que no corrí:**
- Subagentes adversariales, `/code-review` ni `/security-review`. No tengo
  cuota hasta el 28/10 a las 18:00 UTC. La autorrevisión del diff completo
  contra `ea64a9c` es sólo mía, sin independencia. Por eso todavía no
  entrego.
- ORG-1: la pantalla en un navegador. ORG-1 no toca pantallas.
- ORG-1b: la suite completa ni el smoke. ORG-1b cambia sólo la plantilla
  `landing.html`; corrí las pruebas que la leen, arriba.

## Comandos

Este muestra sólo lo de ORG-1:

```bash
git diff ea64a9c..ddfc798
```

Este tiene que dar `46 passed`:

```bash
python -m pytest -q --no-cov -p no:randomly tests/test_org1.py
```

Este tiene que dar «OK: los 9 sabotajes dan rojo por la razón esperada» y
salida 0:

```bash
scripts/testing/sabotaje_org1.sh 18f7f25 <venv>
```

Este tiene que dar `fallas: 0`. Usá un Postgres local y descartable; el
script rechaza cualquier host que no sea local:

```bash
python scripts/testing/org1_postgres.py postgresql://<usuario>@127.0.0.1:<puerto>/<base>
```

Este muestra sólo lo de ORG-1b:

```bash
git diff 373ef55..5d42909
```

Este tiene que terminar con `OK ORG-1b`. Va contra una API local
levantada con datos inventados:

```bash
BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_org1b.js
```

Este tiene que dar `sabotajes sin rojo: 0` y salida 0. Necesita `node` y
el Chromium de Playwright:

```bash
PY=<venv>/bin/python scripts/testing/sabotajes/org1b.sh 5d42909
```

Este muestra sólo lo de DESPACHO-1a:

```bash
git diff fe1571c..51890cd
```

Este tiene que dar `13 passed`:

```bash
python -m pytest -q --no-cov -p no:randomly tests/test_despacho1a.py
```

Este tiene que terminar con `OK 1280 px …` y `OK 390 px …`, y salida 0. Va
contra una API local levantada con datos inventados:

```bash
BASE_URL=http://127.0.0.1:<puerto> PY=<venv>/bin/python node scripts/testing/pantalla_despacho1a.js
```

Este tiene que dar `sabotajes sin rojo: 0` y salida 0. Arma su propio
worktree, su SQLite y su API en el puerto 8853:

```bash
PY=<venv>/bin/python scripts/testing/sabotajes/despacho1a.sh 51890cd
```

## Riesgos de ORG-1 y ORG-1b

- **ORG-1b: una invitación a un email que la pantalla no acepta queda sin
  salida.** Invitar sólo exige una «@» (`a@b` entra). La pantalla, al
  enviar, pide `usuario@dominio.tld` y responde «Email no válido». Con el
  campo de sólo lectura, el invitado no lo puede cambiar. Antes de ORG-1b
  también quedaba sin salida, porque otro email da el 400 de ORG-1. Es de
  antes y no lo cambié. Si querés, va como D.

- **La carrera de dos invitaciones a la vez no está protegida en SQLite.**
  `FOR UPDATE` no hace nada ahí, y la invitación no escribe antes de
  contar. Puede quedar un lugar de más pendiente. Al registrarse, el tope se
  vuelve a controlar, así que no entra un miembro de más. Producción es
  Postgres, y ahí está cubierta.
- **En Postgres puede faltar el índice único de `users.email`.** El modelo
  lo declara, pero no comprobé la base de producción, y no la toco. Ahora la
  carrera del mismo email la frena la invitación, no el índice.
- **El registro con un email de prueba reemplazable** confirma ese borrado
  antes de los controles de la invitación. Es de antes y ORG-1 no lo cambia.
- **El 400 «es para otro email»** dice que el email escrito no es el
  invitado. No dice cuál es. Hace falta el token para preguntar.

Última vuelta: Wed Oct 28 10:27:33 UTC 2026

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. ORG-1, ORG-1b y DESPACHO-1a listas y subidas SIN ENTREGAR sobre 4ce6d22 (suite 4ce6d22: 3670 passed, 0 failed). DESTINO-1 hecha y subida SIN ENTREGAR: producto 7526be9, pruebas hasta f887b4a (sabotajes destino1.sh 15/15; suite f887b4a 3697 passed, 0 failed). SUFIJOS-2 hecha y subida SIN ENTREGAR: SHA probado 4ca6829 (sabotajes sufijos2.sh 9/9; suite 3731 passed, 0 failed); D29 contestada (a). SEGURO-1 hecha y subida SIN ENTREGAR: SHA probado 371cde2 (sabotajes seguro1.sh 10/10; suite a08de1f 3777 passed, 0 failed); D30 contestada (a), riesgo «seguro 0 en el TXT si nadie lo completa»; SEGURO-2 no se empieza hasta verla en PARA-DEV-2. DESPACHO-1b hecha y subida SIN ENTREGAR encima de SEGURO-1 y del merge 49f8e29: producto 0591722, pruebas e59e1a8, SHA probado e59e1a8 (50 casos; sabotajes despacho1b.sh 24/24; suite 3827 passed, 336 skipped, 2 xfailed, 0 failed; smoke y aislamiento 0); D31 contestada (a) en 3da0a8b, costos en riesgos. DATOS-1 (D5+D32 (a) borrar cliente borra sus presupuestos compartidos, D2 /health 503, D6 sin dev_detail) hecha y subida SIN ENTREGAR encima de d01f95c: producto 7d09c6f, casos 4416076, Postgres y sabotajes 162d277, arreglo de casos que gastaban el cupo de test_user c996ad4; SHA probado c996ad4 (test_datos1 9 passed; sabotajes datos1.sh 12/12; suite 3836 passed, 336 skipped, 2 xfailed, 0 failed; datos1_postgres.py fallas 0; smoke y aislamiento 0 sobre 162d277); su propio /entregar después del de DESPACHO-1b, con /security-review. Postgres 16 descartable en /tmp/cdi-pg55432, puerto 55432, base datos1a. DISCO-1 (historial de NCM de DATA_DIR a la tabla ncm_historial por dueño; carga única de archivos viejos a .migrado) hecha SIN ENTREGAR encima de c996ad4 y del merge cf84a76 (PM 1f6e0de): producto bd53fc4, casos y sabotajes 0f1161a, Postgres y textos de sabotajes 88b22c8; SHA probado 88b22c8 (test_disco1 11 passed; sabotajes disco1.sh 20/20; suite 3847 passed, 336 skipped, 2 xfailed, 0 failed; disco1_postgres.py fallas 0 y con sabotaje de carrera fallas 1; smoke y aislamiento 0); D33 contestada (a) en a3efc3a, riesgo anotado en DISCO-1; va en su propio /entregar, con subagentes, /code-review high y /security-review. OBSERVABILIDAD-1 (api_logs.owner_username nullable con su índice al arrancar, helper _migrate_add_api_logs_owner_column en main.py; si falla, log y la app sigue) hecha SIN ENTREGAR encima de 88b22c8: producto y CHANGELOG 8b1ce3b, casos, arnés y sabotajes 7ae35ab, merge de la PM 39be45e; SHA probado 39be45e (test_observabilidad1 8 passed; observabilidad1_arranque.py con Postgres 55432 38 OK fallas 0; sabotajes observabilidad1.sh con PG_URL 16/16 sobre 7ae35ab; suite 3855 passed, 336 skipped, 2 xfailed, 0 failed; smoke y aislamiento 0); D34 contestada (a) en 486e655 (sólo la columna; la métrica sigue sin dueño); va en su propio /entregar después del de DISCO-1, con subagentes, /code-review high y /security-review. SESION-1 (S3: revocar_sesiones nunca escribe NULL en active_jti; change-password cierra las otras y conserva la propia; reset cierra todas; /auth/logout y /logout revocan el token sólo si es el vigente; PUT /api/user/profile pide current_password si cambia el email, 400) hecha SIN ENTREGAR encima de 39be45e y del merge f5160d7 (PM 486e655): producto y CHANGELOG 7dfe144, casos, motores, pantalla y sabotajes 014a3e4, arreglo 4c1ae09 (jti_de_la_request en vez de request.state: la suite sobre 014a3e4 dio 1 failed en test_auth_invalid_plan), sabotajes ajustados 895ee73; SHA probado 895ee73 (test_sesion1 17 casos, rojo en base 11 failed; sesion1_motores.py sqlite y pg 26 OK, todo OK, rojo en base FALLAS 12; sabotajes sesion1.sh 19/19; pantalla 3/3; suite 3872 passed, 336 skipped, 2 xfailed, 0 failed; smoke y aislamiento 0); va en su propio /entregar después del de OBSERVABILIDAD-1, con subagentes, /code-review high y /security-review. ABUSO-1 (S4 IP de login desde XFF, S5 eventos sin tope, S6 recuperar usuario sin límite, C9 registro sin límite) en curso encima de 895ee73 y del merge c702655: premisa con scripts/testing/abuso1_motores.py (b08dbc0) y abuso1_reciclado.sh. S5 hecho: producto y CHANGELOG 584b8d1 (tope 16 KB, 413, sin logs/ui_events.jsonl), casos, arnés y sabotajes 25158c6, HANDOFF 8c37653; sobre 25158c6 abuso1.sh sabotajes sin rojo 0, motores sqlite y pg FALLAS 6 (S4a, S4b, S6, C9, anónimo en las dos rutas: todas de la D35). D35 contestada por la PM en f600ed4 (merge ddc1b61): (1) en las cinco. a: un helper con la última IP de XFF, saltos configurables (1), log obligatorio en el 429 del login con IP tomada y cantidad de entradas. b: registro 5/hora y 20/día, recuperar 5 cada 15 min por IP y 3/hora por email silencioso, eventos 120/min por ruta; justificar en el informe. c: los mensajes quedan; S6 mitigada, no cerrada. d: anónimos sólo pricing_cta_clicked, hero_cta_clicked y register_pending_verify, lista explícita con límite. e: contadores de login y recuperación en tabla, incremento atómico con prueba en paralelo en PG16, filas vencidas se borran, _migrate_* al arrancar, un solo camino con o sin REDIS_URL, commit propio para la tabla; el 5/min de slowapi queda en memoria (riesgo). recover-username compara email sin mayúsculas con prueba; si dos cuentas pueden diferir sólo en mayúsculas, no tocar y abrir D36. Ajustar sesion1_motores.py y tests/test_static_endpoints.py:74. Riesgo anotado: _jwt_sub_from_token_text no mira revocación. ABUSO-1 va con su propio /entregar después del de SESION-1, revisión fuerte. D36 (emails que difieren sólo en mayúsculas) escrita y sin contestar; en ABUSO-1 no se toca la comparación del email. La próxima D es la D37. Pendiente: el 28/10 después de las 18:00 UTC, en orden, /entregar de ORG-1+ORG-1b+DESPACHO-1a sobre 4ce6d22 (subagentes hasta alto, /code-review high, /security-review, Postgres 55432 para org1_postgres.py), DESTINO-1, SUFIJOS-2, SEGURO-1 (con /security-review), DESPACHO-1b, DATOS-1, DISCO-1, OBSERVABILIDAD-1 y SESION-1; timbre «Dev MARIA: entregué <PIEZA> en <SHA>». PESO-NETO-1 y PRORRATEO-1 esperan al despachante. Nunca main, sin push --force, sin datos reales del 24/10 ni despachos del 28/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
