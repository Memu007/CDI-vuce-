# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SESION-1 (devolución sobre `895ee73`): **entregada** en `c429307` (el informe va en el commit siguiente) (2026-11-05)

| Punto | Resultado | Qué decidís |
|---|---|---|
| 1. Un solo lugar decide si un token vale | `datos_del_token` es el único `jwt.decode` (firma y vencimiento); `sesion_de_la_request` rechaza un token con `type` o sin `sub` y compara `jti` contra `active_jti`. Lo usan `get_current_user`, `/auth/me`, la telemetría (`_ui_event`) y los dos logout. El token de verificación no es sesión | Nada |
| 2. Verify-email no abre sesión | Marca `is_verified` y redirige; no emite cookie ni toca `active_jti`. Reusar el link sólo vuelve a marcar verificado | **D71** |
| 3. La carrera del login (D43 a) | `abrir_sesion` escribe `active_jti` con `UPDATE … WHERE username = … AND password = <hash validado>`; si no tocó una fila, no hay cookie ni token. Rojo en SQLite (pytest) y en PG 16 (`sesion1_motores.py`) | Nada |
| 4. Cambio de clave (D43 b) | Revoca en el mismo commit que la clave y le da cookie y token nuevos a quien la cambió; la copia del token viejo da 401 | Nada |
| 5. D43 c y d | Clave actual equivocada: 400 «La contraseña actual es incorrecta» (no 401). Logout: borra la cookie aunque la base falle | Nada |
| 6. Tope sobre `current_password` | `verificar_clave_actual`, compartido por el PUT del perfil y change-password: cuenta antes de probar, más de 5 da 429. Vale también para 20 pedidos a la vez | Nada |
| 7. Mutantes | Los cinco pedidos mueren, más 24 sabotajes de las otras reglas: 29 ROJO, 0 sin rojo (abajo) | Nada |
| 8. Sin `request.state.token_jti` | Este informe no lo usa | Nada |
| Familia | `test_un_solo_lugar_lee_el_token_y_emite_la_cookie` recorre el AST de `proyecto_maria/`: un `jwt.decode` fuera de `datos_del_token` o un `set_cookie("access_token")` fuera de `abrir_sesion` da rojo | Nada |
| 9. NOW.md: logout y cambio/reset de clave no reactivan tokens | `revocar_sesiones` escribe un uuid nuevo, nunca NULL; reset llama a `revocar_sesiones(user)`. Casos `test_una_sesion_revocada_no_vuelve` y `test_resetear_clave_revoca_todas_las_sesiones` | Nada |
| 10. Vecinos de Argon | Una línea por fila en Riesgos | Nada |

**Una decisión nueva: D71.** Sigue abierta **D69** de DESPACHO-1d (`528961b`, en revisión), copiada abajo.

**Ojo para publicar, sigue igual:** la rama tiene `e0b8626` (COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a, sin aceptar). Ningún SHA mío sirve para publicar hasta que esas cinco estén ✅.

**Para vos, de tu sabotaje `csrf3.sh`:** los dos primeros (`REVOCADO` y `if token.startswith("Bearer ")` en `auth/dependencies.py`) ya no encuentran su texto: ese código se fue a `sesion_de_la_request`. La regla sigue: `request.state.sesion_valida = True` está después de `sesion = await sesion_de_la_request(request, db)` y de `if sesion is None: raise`. El ancla equivalente para los dos es mover la marca arriba de `sesion = await sesion_de_la_request(request, db)`. No lo toqué: es tuyo.

**Archivos de producto:**
- `proyecto_maria/auth/dependencies.py`: `_token_de_la_request`, `revocar_sesiones`, `datos_del_token`, `sesion_de_la_request`, `revocar_sesion_de_la_request`, `get_current_user`.
- `proyecto_maria/auth/jwt_utils.py` y `auth/__init__.py`: sale `decode_token`.
- `proyecto_maria/main.py`: `abrir_sesion`, `verificar_clave_actual`, `ChangePasswordRequest`, `change_password`, `update_user_profile`, `login`, `logout`, `logout_root`, `register`, `verify_email`, `get_auth_me`, `_ui_event` (sale `_jwt_sub_from_token_text`), `import_ncm_historial`, `create_organization`, `TokenResponse`, imports.
- `CHANGELOG.md`.

### Decisiones

- **D71. A dónde lleva el link de verificación, ahora que no abre sesión.** Hoy redirige a `/dashboard?verified=true`. Quien abre el link desde el correo, sin sesión en ese navegador, choca con `app_v2.js:45` (`if (res.status === 401) irAlLogin();`), cae en la portada y se pierde `verified=true`, que `tour.js:37` lee para el tour de bienvenida.
  - (a) Dejarlo como está.
  - (b) Redirigir al login con un mensaje («Tu correo quedó verificado, entrá con tu clave»).
  - **Recomiendo (b).** Con (a) el usuario no ve que verificó y no arranca el tour. (b) es una pieza chica de pantalla, con su caso; no la hice porque la pieza no la pedía.
- **D69 (de DESPACHO-1d, sigue abierta).** Reintentar crear después de cambiar el formulario reusa el cliente ya creado sin aplicarle el cambio. (a) reusar siempre, como está entregado; (b) reusar sólo si el formulario no cambió. **Recomiendo (a).** Detalle en `git show f9e99e8:docs/pm/PARA-PM-2.md`.

### SHAs (base `f9e99e8`)

| SHA | Qué |
|---|---|
| `b9216d9` | test: rojos (lugar único, verify-email, carrera, cambio de clave). Sobre la base: abajo |
| `b4afd7f` | fix: un solo lugar decide si un token es la sesión vigente |
| `05136ad` | test: verify-email se mide por la cookie; el caso del secreto usa `datos_del_token` |
| `98b39d8` | refactor: `revocar_sesiones` sin el jti a conservar |
| `a6bbbbe` | test: cambiar la clave revoca en el mismo commit; motores al contrato nuevo; sabotajes |
| `fbae2b6` | merge de tu rama |
| `6a7674f` | test: el tope de la clave actual con veinte pedidos a la vez (rojo) |
| `99dc3bc` | fix: la clave actual se cuenta antes de probarla |
| `85ff348` | test: sabotajes del tope por orden y del usuario sin jti |
| `409f6c5` | merge de tu rama (sólo docs) |
| `c429307` | test: dos pruebas viejas al contrato nuevo (ver Puertas) |
| este commit | docs: este informe |

### Rojo sobre la base

`tests/test_sesion1.py` de `c429307` corrido en un worktree de `f9e99e8`:

```
FAILED tests/test_sesion1.py::test_cambiar_clave_rota_la_sesion_de_quien_la_cambia
FAILED tests/test_sesion1.py::test_cambiar_clave_con_cookie_conserva_el_navegador
FAILED tests/test_sesion1.py::test_cambiar_clave_mal_no_revoca_nada - Asserti...
FAILED tests/test_sesion1.py::test_cambiar_clave_revoca_en_el_mismo_commit_que_la_clave
FAILED tests/test_sesion1.py::test_el_login_no_pisa_una_clave_que_cambio_mientras_validaba
FAILED tests/test_sesion1.py::test_una_sesion_revocada_no_vuelve - KeyError: ...
FAILED tests/test_sesion1.py::test_la_clave_actual_tiene_tope_de_intentos - a...
FAILED tests/test_sesion1.py::test_el_tope_de_la_clave_actual_vale_para_pedidos_a_la_vez
FAILED tests/test_sesion1.py::test_ningun_lugar_acepta_un_token_que_no_es_la_sesion_vigente
FAILED tests/test_sesion1.py::test_verificar_el_email_no_abre_sesion - Assert...
FAILED tests/test_sesion1.py::test_cerrar_sesion_borra_la_cookie_aunque_falle_la_base
FAILED tests/test_sesion1.py::test_un_solo_lugar_lee_el_token_y_emite_la_cookie
================== 12 failed, 17 passed, 3 warnings in 24.72s ==================
```

### Puertas sobre `c429307`

| Puerta | Salida |
|---|---|
| Suite completa | `4915 passed, 355 skipped, 3 xfailed, 101 warnings in 717.80s (0:11:57)`, exit 0 |
| `compileall -q proyecto_maria` | exit 0 |
| `smoke_friccion.sh` | `[FAIL] POST /api/ui/event`, exit 1, **igual en `f9e99e8`** (ver abajo). Con la acción cambiada a `hero_cta_clicked` en una copia: `OK · telemetría + alias session/state + by-cuit protegido`, exit 0 |
| `ataque_aislamiento.sh` | `Bloqueado: 47 · Fugas: 0 · Sin probar: 0`, `PUERTA G3 PASADA`, exit 0 |
| `sesion1_motores.py` sqlite | `sqlite: todo OK` (la carrera, «NO CORRIDO»: en SQLite la cubre pytest), exit 0 |
| `sesion1_motores.py` pg (PG 16 local descartable) | `pg: todo OK`, exit 0 |
| `sabotajes/sesion1.sh` (sobre `85ff348`) | 29 ROJO, `sabotajes sin rojo: 0` |

- **Smoke rojo, de antes de esta pieza:** `smoke_friccion.sh` manda `smoke_wave1` sin sesión, y desde ABUSO-1 (`a3abd92`) sin sesión sólo se guardan las acciones de `_UI_EVENT_SIN_SESION`: contesta `{"ok":false,"detail":"Evento sin sesión no admitido"}`. Corrido en `f9e99e8`: el mismo `[FAIL]`. Los otros tres chequeos no corrían porque el script corta en el primero; con la copia cambiada pasan los cuatro. El script no lo toqué (propuesta abajo).
- **Rojos de la suite en `409f6c5`, antes de `c429307`:** 8 F en `tests/test_abuso1.py` y 1 F en `tests/test_billing_autoservicio.py`. Las dos pruebas eran viejas, no el producto: abuso1 mandaba eventos con el token del registro, que el login siguiente revoca (el contrato de esta pieza); billing esperaba 401 con la clave actual equivocada, y D43 c pide 400. `c429307` las pone al contrato nuevo sin tocar producto.
- **Sabotajes sobre `85ff348` valen para `c429307`:** `git diff --stat 85ff348 c429307` toca sólo `docs/pm/`, `tests/test_abuso1.py` y `tests/test_billing_autoservicio.py`; `sesion1.sh` no corre ninguna de las dos pruebas ni sabotea código que cambió.
- Las 447 líneas «Task was destroyed but it is pending!» son de antes de esta pieza.

### Sabotajes (`scripts/testing/sabotajes/sesion1.sh`, 29)

Los cinco que pediste: «un usuario sin jti (de antes de la columna) no entra» (sacar `user.active_jti is not None and`), «abrir el token sin verificar la firma», «el header le gana a la cookie», «la clave actual no se mira si es texto», «un email vacío antes no pide la clave». Los otros 24: verificación como sesión, verify-email abre sesión, login pisa la clave (SQLite y PG), cambiar la clave sin revocar o sin token nuevo, reset y revocar que escriben NULL, logout que sólo borra la cookie, logout sin base, logout con token revocado, clave actual que acepta cualquier cosa, 401, tope (no suma, cuenta tarde), email sin clave, vaciar el email, mismo email en mayúsculas, email mal escrito, y cinco de pantalla. Cada línea del log con su rojo: `$S/ses1_sabotajes2.log` (copiable con el comando de abajo).

### Revisión

| Quién | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| Adversario | Sonnet alto | Ráfaga en paralelo pasa el tope | Arreglado (`6a7674f` rojo, `99dc3bc`) |
| Adversario | Sonnet alto | Patrones de `csrf3.sh` perdidos | Arriba, para vos |
| Adversario | Sonnet alto | La cookie se pone siempre en el login | Es lo pedido |
| Adversario | Sonnet alto | Logout con la base caída da 200 y el token sigue valiendo | Riesgo |
| Adversario | Sonnet alto | Una sesión robada bloquea 15 min al dueño probando claves | Riesgo |
| Adversario | Sonnet alto | El UPDATE de revocar no es condicional al jti | Riesgo |
| Adversario | Sonnet alto | `create_access_token` sólo lo usan las pruebas | Propuesta |
| Adversario | Sonnet alto | Una cookie basura le gana a un Bearer válido | Riesgo (es la regla pedida: la cookie gana) |
| Adversario | Sonnet alto | Cambiar el email no vuelve `is_verified` a falso | Fuera de la pieza; propuesta |
| `/code-review` | high | change-password con `abrir_sesion` en None devuelve `access_token: null` | Riesgo (sólo si cambia la clave a la vez otra vez) |
| `/code-review` | high | El redirect de verify-email cae en la portada | D71 |
| `/code-review` | high | `SECRET_KEY` y `settings.jwt_secret` son dos nombres | De antes; propuesta |
| `/code-review` | high | `register` y `create_organization` no miran el None | Riesgo bajo |
| `/code-review` | high | Telemetría: un SELECT por evento | Riesgo bajo |
| `/code-review` | high | El contador `pwd:` no se limpia con el reset | Propuesta |
| `/code-review` | high | El login limpia `login:{ip}` antes de `abrir_sesion` | Riesgo bajo |
| `/security-review` | — | Nada con confianza alta | — |

### chequeo-6

```
chequeo-6 f9e99e8..c429307: avisos para mirar, no un veredicto
producto +108/−257
arnés +431/−96
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/auth/__init__.py: 6 → 6
  proyecto_maria/auth/dependencies.py: 202 → 185
  proyecto_maria/auth/jwt_utils.py: 57 → 14
  proyecto_maria/main.py: 12014 → 11925
avisos: 0
```

### Riesgos

- **Logout con la base caída:** borra la cookie y da 200, pero el token sigue valiendo hasta vencer. Lo pedido (D43 d) es la cookie.
- **Sesión robada y tope:** quien tiene una sesión puede gastar los 5 intentos de `pwd:{usuario}` y el dueño espera 15 min para cambiar la clave o el email. El reset no limpia ese contador (propuesta).
- **Revocar no condicional:** `revocar_sesion_de_la_request` lee la sesión y después escribe un jti nuevo; un login en el medio queda revocado. Arreglo propuesto: `UPDATE … WHERE active_jti = <jti del token>`.
- **Cookie basura y Bearer:** con una cookie `access_token` inválida, un Bearer válido no entra.
- **Usuarios con `active_jti` NULL:** cualquier token suyo sin `type` vale hasta su primer login, logout o cambio de clave.
- **Argon fila 10 (link de verificación):** cubierta en parte: ya no abre sesión ni saca al dueño; sigue reusable 24 h, pero sólo marca verificado.
- **Argon fila 13.2 (reset con cookie vieja da 403):** ya resuelto por CSRF-1 (`/auth/reset-password` en `_CSRF_EXEMPT_PATHS`), no por esta pieza.
- **Argon fila 14, login exitoso borra el contador:** no tocado; el login limpia `login:{ip}`.
- **Argon fila 14, bloqueo perpetuo del pedido de reset:** no tocado.
- **Argon fila 14, tokens de reset en paralelo:** sigue abierto: `reset_password` marca usado sólo ese token.
- **Argon fila 14, `/auth/me` ignora el jti:** arreglado (punto 1).

### Propuestas (fuera de la pieza)

- Sacar `create_access_token` de `jwt_utils.py`: el producto no lo usa; las pruebas pueden usar `abrir_sesion`.
- Unificar `SECRET_KEY` y `settings.jwt_secret` en un nombre (hoy `TestJWTSecretUnificado` comprueba que son iguales).
- Limpiar `pwd:{usuario}` al resetear la clave.
- Cambiar el email vuelve `is_verified` a falso.
- `smoke_friccion.sh`: mandar una acción de `_UI_EVENT_SIN_SESION` (o la de prueba con sesión). Hoy da rojo en cualquier SHA desde ABUSO-1.

### Comandos

```bash
S=<scratchpad>; cd <repo>; git fetch origin claude/dev-maria; git checkout c429307
# 1. el caso de la pieza: «29 passed»
DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake \
  TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares \
  python -m pytest -q --no-cov -p no:cacheprovider tests/test_sesion1.py
# 2. sabotajes: «sabotajes sin rojo: 0» (con PG_DSN suma el de PG)
PY=$(which python) PG_DSN=postgresql://<u>@127.0.0.1:<puerto>/<base> scripts/testing/sabotajes/sesion1.sh
# 3. motores: «pg: todo OK»
python scripts/testing/sesion1_motores.py pg postgresql://<u>@127.0.0.1:<puerto>/<base>
# 4. chequeo-6: «avisos: 0»
python docs/pm/herramientas/chequeo-6.py f9e99e8 c429307
```

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP, aviso a la PM session_01B7FVQspcEHF7PqNv797wNM. SESION-1 entregada en c429307 (informe en el commit siguiente), D71 nueva y D69 abiertas; sigo con CATALOGO-LARGO-2. Nada se publica sin el «dale» de Emi para el SHA, nunca main, sin secretos ni datos reales.
