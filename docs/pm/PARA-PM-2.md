# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SESION-1 (devolución sobre `c429307`): **entregada** en `2e62761` (el informe va en el commit siguiente) (2026-11-06)

| Punto | Resultado | Qué decidís |
|---|---|---|
| Causa 1. Lo validado con la clave actual pierde contra un reset o un cambio de clave en el medio | `guardar_si_la_clave_sigue` guarda con `UPDATE … WHERE username = … AND password = <hash validado>`; si no tocó una fila, deshace todo. Lo usan las dos rutas: change-password (vía `abrir_sesion`) y el cambio de email del perfil. Las dos dan **409** «La contraseña cambió mientras se guardaba…», sin guardar nada y sin token ni cookie. Caso `test_lo_que_cambia_la_clave_mientras_otro_valida_le_gana`, con las rutas y lo del medio como datos (4 filas) | Nada |
| «Dos cambios a la vez no dan 200 con un token muerto» | La fila «otro cambio de clave − cambiar la clave» del mismo caso: el del medio da 200 y su token entra; el otro da 409, sin token | Nada |
| Causa 2. Contar intentos no agota el pool | `limites_auth` recibe la sesión del pedido y no abre otra. Además `get_current_user` hace commit antes de la ruta: con eso, revisar la sesión devuelve su conexión y la ruta no tiene dos tomadas a la vez. Caso `test_contar_intentos_usa_la_conexion_del_pedido`, 7 rutas como datos (ver el perfil, perfil, cambiar la clave, login sin usuario, login con clave mala, login, pedir el reset): ninguna toma más de una conexión a la vez | Nada |
| Caso en PG (lo pediste) | `sesion1_motores.py pg`, fila 7: 80 pedidos a la vez por ruta, ningún 500 y otro usuario entra en menos de 2 s. Verde abajo, en Puertas | Nada |
| Firma y verificación, un solo lugar | `firmar_token` y `datos_del_token`, los dos en `auth/dependencies.py`, leen `settings.jwt_secret` y `settings.jwt_algorithm` | Nada |
| Un token sin `exp` no es sesión | `datos_del_token` decodifica con `require: ["exp"]`. Caso `test_un_token_sin_vencimiento_no_es_una_sesion` | Nada |
| Sale `create_access_token` | Borrado `auth/jwt_utils.py`; las pruebas firman con `firmar_token` o abren sesión | Nada |
| Un secreto | Salen `SECRET_KEY` y `ALGORITHM` de `main.py`; queda `settings.jwt_secret`. Caso `test_se_firma_y_se_verifica_con_la_misma_clave` | Nada |

**Tres decisiones nuevas: D73, D74 y D75.** D69 (a) y D71 (b) ya las decidiste; D71 queda para su pieza chica.

**Ojo para publicar, sigue igual:** la rama tiene `e0b8626` (COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a, sin aceptar). Ningún SHA mío sirve para publicar hasta que esas cinco estén ✅.

**Para vos, en Railway:** si `JWT_SECRET` falta o está vacío en producción, la app no arranca (falla cerrado; `config.py` lo exige fuera de desarrollo). Antes de publicar conviene mirar que esté puesto. No lo toqué ni lo puedo ver.

**Archivos de producto:**
- `proyecto_maria/auth/dependencies.py`: `firmar_token` (nueva), `datos_del_token`, `get_current_user`.
- `proyecto_maria/auth/jwt_utils.py`: borrado. `proyecto_maria/auth/__init__.py`: sale `create_access_token`.
- `proyecto_maria/config.py`: sale `jwt_exp_minutes`.
- `proyecto_maria/core/limites_auth.py`: todas las funciones reciben la sesión del pedido.
- `proyecto_maria/main.py`: `guardar_si_la_clave_sigue` (nueva), `abrir_sesion`, `change_password`, `update_user_profile`, `verificar_clave_actual`, `build_email_verification_token`, `login`, `register`, `request_password_reset`, `reset_password`, `recover_username`, imports.
- `CHANGELOG.md`.

### Decisiones

- **D73. Las 5 fallas de pypdf 6.21.4** en `tests/test_despacho1b.py` y `tests/test_rendimiento1c.py`, que también dan rojo en `fb75e41`.
  - Dato nuevo: mi entorno tiene pypdf 6.21.2 y la suite sobre `2e62761` da 0 failed; las 5 aparecen sólo con 6.21.4. `requirements` dice `pypdf>=6.21.2`, así que una instalación nueva (Railway incluida) baja 6.21.4: lo que corre no es lo que pasó las pruebas.
  - (a) Fijar `pypdf==6.21.2` en `requirements` ahora, y mirar 6.21.4 en una pieza aparte.
  - (b) Adaptar las pruebas a lo que hace 6.21.4.
  - **Recomiendo (a) y después (b).** Las fallas tocan los topes de PDFs armados; hasta saber si 6.21.4 cambió algo que el producto usa, conviene que se instale la versión probada. Ninguna de las dos entra en SESION-1.
- **D74. Con una cuenta real y la clave mala, otro usuario espera por CPU de bcrypt.** Sobre `2e62761`, PG 16 local, una fila más en una copia de `sesion1_motores.py` (`$S/d74_bcrypt.log`): «80 POST /auth/login a la vez: ningún 500 ({401: 80})» y «otro usuario entra en menos de 2 s (200, 4.7 s)». Con un usuario que no existe, 0,7 s. El adversario lo midió aparte, con 100 pedidos: «HEAD poolA (cuenta real): (200, 6.84 s) {401: 100}» y «HEAD nadie_existe: (200, 0.45 s)»; en `fb75e41`, «(200, 31.37 s) {500: 51, 401: 49}». El pool ya no se traba; lo que queda es CPU.
  - (a) Aceptarlo: ningún 500, el otro entra, y el tope por IP de 5/minuto del login ya frena a un solo atacante.
  - (b) Contar el intento antes de bcrypt y cortar con 429 sin probar la clave cuando se pasó el tope por usuario.
  - **Recomiendo (a) por ahora.** (b) cambia el orden del login y pide su propia pieza con sabotajes; hoy el caso que pediste (ningún 500 y el otro entra) está verde.
- **D75. Hay dos `get_db` iguales**, en `main.py:165` y `auth/dependencies.py:21`.
  - (a) Unificarlos.
  - (b) Dejarlos.
  - **Recomiendo (a), a la cola de limpieza.** No lo hice acá: `main.py:2418` y `main.py:11562` usan `populate_existing`, y cambiar de dónde sale la sesión de esas rutas pide su propia prueba.

### SHAs (base `fb75e41`)

| SHA | Qué |
|---|---|
| `5f7ba77` | test: rojos del cambio que pierde contra un reset, el token sin exp y la clave de firma |
| `0b2bf9a` | test: rojo de contar intentos con más pedidos que conexiones |
| `ce7cd9d` | fix: lo validado con la clave se guarda sólo si la clave sigue; contar intentos usa la conexión del pedido |
| `539b55b` | test: carrera, conexión del pedido, firma y exp; sabotajes al día |
| `8cbf15b` | test: la sesión de `get_current_user` no se queda con una conexión (rojo) |
| `fd1f65b` | fix: revisar la sesión devuelve su conexión antes de la ruta |
| `34e736a` | test: sabotaje de esa conexión y filas que ve cada sabotaje del pool |
| `f448d57` | refactor: sin `jwt_exp_minutes` ni `import jwt` sin uso; comentario de la conexión |
| `25a2718` | test: firma y exp parchean el settings que lee `dependencies` |
| `2e62761` | test: el sabotaje de la firma lee la clave de dos lugares |
| este commit | docs: este informe |

### Rojo sobre la base

`tests/test_sesion1.py` de `5f7ba77` sobre el producto de `fb75e41`:

```
FAILED tests/test_sesion1.py::test_lo_que_cambia_la_clave_mientras_otro_valida_le_gana[reset-cambiar la clave]
FAILED tests/test_sesion1.py::test_lo_que_cambia_la_clave_mientras_otro_valida_le_gana[reset-cambiar el email]
FAILED tests/test_sesion1.py::test_lo_que_cambia_la_clave_mientras_otro_valida_le_gana[otro cambio de clave-cambiar la clave]
FAILED tests/test_sesion1.py::test_lo_que_cambia_la_clave_mientras_otro_valida_le_gana[otro cambio de clave-cambiar el email]
FAILED tests/test_sesion1.py::test_un_token_sin_vencimiento_no_es_una_sesion
FAILED tests/test_sesion1.py::test_se_firma_y_se_verifica_con_la_misma_clave
================== 6 failed, 28 passed, 3 warnings in 30.67s ===================
```

El caso del pool, de `0b2bf9a`, sobre `fb75e41`:

```
FAILED tests/test_sesion1.py::test_contar_intentos_usa_la_conexion_del_pedido[perfil]
FAILED tests/test_sesion1.py::test_contar_intentos_usa_la_conexion_del_pedido[cambiar la clave]
FAILED tests/test_sesion1.py::test_contar_intentos_usa_la_conexion_del_pedido[login sin usuario]
FAILED tests/test_sesion1.py::test_contar_intentos_usa_la_conexion_del_pedido[login con clave mala]
FAILED tests/test_sesion1.py::test_contar_intentos_usa_la_conexion_del_pedido[login]
============ 5 failed, 1 passed, 34 deselected, 5 warnings in 4.96s ============
```

La fila que pasa es «pedir el reset»: no cuenta con otra conexión. «Ver el perfil» se sumó en `8cbf15b`.

**Rojo en PG del segundo arreglo.** Con `ce7cd9d` solo (contar ya usaba la sesión del pedido), `sesion1_motores.py pg` en `8cbf15b` seguía trabado, porque `get_current_user` se quedaba con su conexión mientras la ruta abría la suya:

```
FALLA | 7. 80 GET /api/user/profile a la vez: ningún 500 ({200: 3, 500: 77})
FALLA | 7. con GET /api/user/profile a la vez otro usuario entra en menos de 2 s (500, 30.6 s)
FALLA | 7. 80 PUT /api/user/profile a la vez: ningún 500 ({500: 80})
FALLA | 7. con PUT /api/user/profile a la vez otro usuario entra en menos de 2 s (500, 30.4 s)
FALLA | 7. 80 POST /api/user/change-password a la vez: ningún 500 ({500: 80})
FALLA | 7. con POST /api/user/change-password a la vez otro usuario entra en menos de 2 s (500, 30.4 s)
OK    | 7. 80 POST /auth/login a la vez: ningún 500 ({401: 80})
OK    | 7. 80 POST /auth/request-password-reset a la vez: ningún 500 ({200: 80})
pg: FALLAS: 6
```

`fd1f65b` lo arregla (verde en Puertas).

### Puertas sobre `2e62761`

| Puerta | Salida | Log |
|---|---|---|
| compileall | `compileall=0` (las SyntaxWarnings de `pdf_extractor.py:927/936` son de antes) | `compileall.log` |
| suite | «4938 passed, 355 skipped, 3 xfailed, 96 warnings in 874.38s (0:14:34)» | `suite.log` |
| smoke | `[FAIL] POST /api/ui/event`: el rojo conocido desde ABUSO-1 | `smoke.log` |
| smoke con telemetría permitida | «==> OK · telemetría + alias session/state + by-cuit protegido», `SMOKE_EXIT=0` | `smoke_permitida.log` |
| ataque de aislamiento | «Bloqueado: 47   ·   Fugas: 0   ·   Sin probar: 0», «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.» | `ataque_v2.log` |
| motores PG 16 | «pg: todo OK» | `motores_pg.log` |
| motores SQLite | «sqlite: todo OK» | `motores_sqlite.log` |
| sabotajes `abuso1.sh` | 26 ROJO, «sabotajes sin rojo: 0» | `abuso1.log` |
| sabotajes `sesion1.sh` | 38 ROJO, «sabotajes sin rojo: 0» | `sesion1.log` |

Logs en `$S/puertas_2e62761/`. Notas:

- **El ataque falló la primera vez por el arnés, no por el producto** (`ataque.log`: `ModuleNotFoundError: No module named 'fastapi'`). Mi arnés lo corre en un worktree sin `./venv`, y `ataque_aislamiento.sh:106` cae a `python3` del sistema. Lo volví a correr solo, en un worktree con el venv enlazado: `ataque_v2.log`, salida 0.
- La suite no ve las 5 fallas de D73 porque mi venv tiene pypdf 6.21.2.
- Fila 7 de motores PG:

```
OK    | 7. 80 GET /api/user/profile a la vez: ningún 500 ({200: 80})
OK    | 7. con GET /api/user/profile a la vez otro usuario entra en menos de 2 s (200, 0.8 s)
OK    | 7. 80 PUT /api/user/profile a la vez: ningún 500 ({400: 5, 429: 75})
OK    | 7. con PUT /api/user/profile a la vez otro usuario entra en menos de 2 s (200, 1.1 s)
OK    | 7. 80 POST /api/user/change-password a la vez: ningún 500 ({400: 5, 429: 75})
OK    | 7. con POST /api/user/change-password a la vez otro usuario entra en menos de 2 s (200, 1.0 s)
OK    | 7. 80 POST /auth/login a la vez: ningún 500 ({401: 80})
OK    | 7. con POST /auth/login a la vez otro usuario entra en menos de 2 s (200, 0.8 s)
OK    | 7. 80 POST /auth/request-password-reset a la vez: ningún 500 ({200: 80})
OK    | 7. con POST /auth/request-password-reset a la vez otro usuario entra en menos de 2 s (200, 0.9 s)
```

### Sabotajes (`scripts/testing/sabotajes/sesion1.sh`, 38)

`$S/s1_sab_34e736a_v2.log` (sobre `34e736a`): 38 ROJO, «sabotajes sin rojo: 0», salida 0. Sobre `2e62761` (`$S/puertas_2e62761/sesion1.log`): 38 ROJO, «sabotajes sin rojo: 0», salida 0; `abuso1.sh`: 26 ROJO, «sabotajes sin rojo: 0».

Los nuevos de esta vuelta: guardar sin mirar la clave validada (en change-password y en el perfil), contar intentos con una sesión propia (uno por función de `limites_auth`), `get_current_user` sin devolver su conexión, un token sin `exp` aceptado, y la firma que lee la clave de otro lugar que la verificación.

**El sabotaje de la firma, demostrado.** El primero que escribí (cambiar la clave en un lugar) no distinguía el defecto: lo que pasaba en la realidad era que `firmar_token` leyera la clave del entorno y `datos_del_token` de `settings`. Con ese sabotaje (`$S/h1_demo.log`): la prueba vieja más `test_prelaunch_block3`, «2 passed» (no lo ve); la nueva más esa, «1 failed, 1 passed»; la nueva sola, «1 failed».

### Revisión

| Quién | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| `/code-review` | high | La prueba de la firma no distinguía el defecto | Arreglada (`25a2718`, `2e62761`) y demostrada arriba |
| `/code-review` | high | `get_current_user` hace commit en la sesión del pedido | Riesgo bajo: lo único pendiente que puede llevar es el rehash de una clave en texto plano, que sólo pasa en desarrollo |
| `/code-review` | high | Un comentario decía otra cosa que el código | Corregido (`f448d57`) |
| `/code-review` | high | `JWT_SECRET` vacío | Falla cerrado: la app no arranca. Para vos, arriba (Railway) |
| `/code-review` | high | Dos `get_db` iguales | D75 |
| `/code-review` | high | Un commit de más en el período de prueba | Inofensivo: no hay nada pendiente en ese punto |
| `/code-review` | high | `A_LA_VEZ` fijo en el motores | Riesgo del arnés, abajo |
| `/code-review` | high | `_token_firmado` en las pruebas firma aparte | Se queda: arma tokens que el producto no emite (sin `exp`, con otra clave) |
| `/code-review` | high | Código sin uso | Sacado (`f448d57`) |
| `/code-review` | high | `hash_validado` se lee antes de validar | No es un defecto: es el hash contra el que se valida, y el UPDATE lo exige igual |
| Adversario | Sonnet alto | Con una cuenta real, el otro usuario espera por bcrypt | D74 |
| Adversario | Sonnet alto | El 429 del reset en su corrida | Del arnés: el tope de 5/minuto del login (`main.py:3114`) |
| `/security-review` | Sonnet alto (adversario, sólo lectura) | Nada con confianza mayor a 80 % | Informativo y de antes, en Riesgos |

### chequeo-6

```
chequeo-6 fb75e41..2e62761: avisos para mirar, no un veredicto
producto +95/−89
arnés +282/−69
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/auth/__init__.py: 6 → 5
  proyecto_maria/auth/dependencies.py: 185 → 194
  proyecto_maria/config.py: 48 → 45
  proyecto_maria/core/limites_auth.py: 99 → 103
  proyecto_maria/main.py: 11921 → 11932
avisos: 0
```

Producto +95/−89: 6 líneas netas, menos de 20.

### Riesgos

- **D74, CPU de bcrypt:** con una cuenta real y la clave mala a la vez, otro usuario entra en 4,7 s (80 pedidos) o 6,84 s (100). Ningún 500.
- **El rollback expira los objetos:** cuando `guardar_si_la_clave_sigue` deshace, el `User` del pedido queda expirado. Las dos rutas cortan con 409 justo después y no lo leen; una ruta nueva que lo use después del False haría otra consulta.
- **Dos usuarios que cambian al mismo email a la vez:** los dos pasan el chequeo de duplicado y el segundo choca con el índice único y da 500, no el 400. Era igual en `fb75e41` (el commit del final daba el mismo error).
- **El rehash de una clave en texto plano** se guarda con el commit de `get_current_user`. Sólo en desarrollo.
- **`A_LA_VEZ` fijo en 80** en `sesion1_motores.py`: el rojo depende de que 80 sea más que el pool (hoy 5 + 10). Si el pool crece, la fila puede dar verde sin probar nada.
- **De antes, del `/security-review`:** `reset_password` no consume el token de forma atómica (dos resets a la vez con el mismo token pueden pasar); un login exitoso limpia el contador por IP; un usuario con `active_jti` NULL acepta cualquier token suyo sin `type`.

### Propuestas (fuera de la pieza)

- Las tres que ya mandaste a la cola (borrar `pwd:` al resetear, que cambiar el email apague `is_verified`, `smoke_friccion.sh`) siguen igual.
- Consumir el token de reset con un `UPDATE … WHERE used = false` condicionado, como el de la clave.
- Leer `A_LA_VEZ` del tamaño del pool en el motores.

### Comandos

```bash
S=<scratchpad>; cd <repo>; git fetch origin claude/dev-maria; git checkout 2e62761
E="DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares"
# 1. el caso de la pieza: «42 passed»
env $E python -m pytest -q --no-cov -p no:cacheprovider tests/test_sesion1.py
# 2. motores en PG: «pg: todo OK» (fila 7: ningún 500 y otro usuario en menos de 2 s)
python scripts/testing/sesion1_motores.py pg postgresql://<u>@127.0.0.1:<puerto>/<base>
# 3. sabotajes: «sabotajes sin rojo: 0»
PY=$(which python) PG_DSN=postgresql://<u>@127.0.0.1:<puerto>/<base> scripts/testing/sabotajes/sesion1.sh
# 4. chequeo-6: «avisos: 0»
python docs/pm/herramientas/chequeo-6.py fb75e41 2e62761
```

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP, aviso a la PM session_01B7FVQspcEHF7PqNv797WNM. SESION-1 v2 entregada en 2e62761 (informe en el commit siguiente); D73, D74 y D75 nuevas; D69 (a) y D71 (b) ya decididas; sigo con CATALOGO-LARGO-2, cuyas D empiezan en D76. Nada se publica sin el «dale» de Emi para el SHA, nunca main, sin secretos ni datos reales.
