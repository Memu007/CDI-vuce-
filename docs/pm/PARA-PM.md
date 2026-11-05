# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CSRF-3, entregada en `9fe55d4` (informe en el commit de arriba)

| SHA | qué |
|---|---|
| `0510d47` | producto: la sesión válida sin `csrf_token` lo recibe en la próxima lectura |
| `4931b82` | pruebas: familia de sesiones en pytest, pantalla v2 y `csrf3.sh` |
| `8463f7d` | producto: `GET /dashboard` trae el token y la pestaña v2 vuelve a ser estricta |
| `392423b` | pruebas: la familia corre también sobre `/dashboard`; escenario «otro entra antes» |
| `9fe55d4` | pruebas: `test_auth_invalid_plan.py` arma un `Request` de verdad (abajo) |

Base: `d21e16d` (tu merge de las 15:11).

**Resultado.**
- **Emisión.** `get_current_user` marca la sesión como válida después de
  verificar firma, vencimiento, usuario y jti. En la salida de lecturas y
  rutas exentas, si la sesión quedó marcada y no hay cookie `csrf_token` (o
  está vacía), `CSRFMiddleware` se la emite.
  - Sin sesión, vencida o revocada: no se emite nada.
  - Un token que ya está no se cambia: no hay forma de reemplazar el de otro.
- **La página v2 llega con su token.** `GET /dashboard` valida la sesión con
  `get_current_user` (sin cortar si no hay), así la emisión le pone el token
  a la página misma. Una pestaña abierta con `access_token` y sin
  `csrf_token` escribe sin volver a entrar y sin el aviso de otro usuario.
- **La pestaña v2 sigue estricta.** Cualquier cambio del token entre que
  abre y que sabe quién es se toma como otro login. El primer arreglo
  (`0510d47`) eximía a la pestaña sin token; la autorrevisión mostró que
  así escribía a nombre de otro usuario si éste entraba antes. `8463f7d` lo
  retira; el rojo antes está abajo.
- Producto `+14/−2`.

### Decisiones

Nada para decidir. Supuesto reversible: `pantalla_csrf3.js` entra con
`/auth/register` y no con `/auth/login`, porque el segundo escenario abre dos
sesiones y chocaba con el límite de intentos del login (429).

### Puertas

| puerta | resultado |
|---|---|
| suite completa sobre `392423b` | `1 failed, 4449 passed, 121 skipped, 3 xfailed`: el rojo es mío (abajo) |
| suite completa sobre `9fe55d4` | `4450 passed, 121 skipped, 3 xfailed`, 0 failed |
| `tests/test_csrf.py` sobre `392423b` | 38 passed |
| `compileall -q proyecto_maria` sobre `392423b` | salida 0 |
| sabotajes `csrf3.sh` sobre `392423b` | 8 ROJO, «sabotajes con falla: 0» |
| sabotajes `csrf1`, `csrf2`, `orden1b`, `orden1` sobre `392423b` | todos ROJO (8, 10, 29 y 76), cada script sale con 0 y ninguno sin rojo |
| `/code-review high` y adversario Sonnet alto | 1 confirmado y arreglado; el resto, en la tabla |
| `/security-review` (Sonnet alto) | ninguno con confianza ≥ 8 |
| chequeo-6 | 0 avisos (abajo) |

El rojo de la suite sobre `392423b`:

```
FAILED tests/test_auth_invalid_plan.py::test_get_current_user_with_invalid_plan_falls_back_to_premium
proyecto_maria/auth/dependencies.py:97: in get_current_user
    request.state.sesion_valida = True
E   AttributeError: 'MockRequest' object has no attribute 'state'
```

La prueba llamaba a `get_current_user` con un doble que no tenía `state`. Un
`Request` de Starlette siempre lo tiene, así que no toqué el producto:
`9fe55d4` cambia el doble por un `Request` real con el header Bearer (+2/−4).
Entre `392423b` y `9fe55d4` sólo cambia ese archivo de pruebas; por eso los
sabotajes y `compileall` valen para los dos. La suite se volvió a correr
entera sobre `9fe55d4`.

`smoke_friccion.sh` y `ataque_aislamiento.sh`: no corridos. La pieza no toca
datos ni permisos de clientes o descargas, que es lo que cubre el segundo; el
primero queda para tu corrida antes de publicar.

### Rojo antes

- **Pruebas nuevas sobre la base** (`test_csrf.py` de `392423b` con el
  producto de `d21e16d`): `4 failed, 34 passed`. Fallan exactamente
  `[ausente-…]` y `[vacia-…]`, en `/auth/current_user` y en `/dashboard`. Las
  filas `presente`, `vencida`, `revocada` y `sin_sesion` pasan en la base,
  porque piden que no se emita nada; las cubren los sabotajes.
- **Pantalla nueva sobre `4931b82`** (el primer arreglo, con la exención del
  front): 3 de 3 «FALLA: entró otro usuario y la pestaña no lo avisó».
- Sobre `392423b`, la pantalla da «OK: CSRF-3 en el navegador» 5 de 5.

### Sabotajes de `csrf3.sh`, uno por regla

```
ROJO  | la sesión se marca válida antes de mirar si está revocada: dice «FAILED tests/test_csrf.py::test_sesion_sin_token_csrf_lo_recibe_y_escribe[revocada-/auth/current_user]»
ROJO  | la sesión se marca válida antes de verificar la firma: dice «FAILED tests/test_csrf.py::test_sesion_sin_token_csrf_lo_recibe_y_escribe[vencida-/auth/current_user]»
ROJO  | el token se emite sin sesión: dice «FAILED tests/test_csrf.py::test_sesion_sin_token_csrf_lo_recibe_y_escribe[sin_sesion-/auth/current_user]»
ROJO  | el token se cambia aunque la sesión ya lo tenga: dice «FAILED tests/test_csrf.py::test_sesion_sin_token_csrf_lo_recibe_y_escribe[presente-/auth/current_user]»
ROJO  | una cookie csrf_token vacía cuenta como token: dice «FAILED tests/test_csrf.py::test_sesion_sin_token_csrf_lo_recibe_y_escribe[vacia-/auth/current_user]»
ROJO  | la sesión sin token no lo recibe: dice «FAILED tests/test_csrf.py::test_sesion_sin_token_csrf_lo_recibe_y_escribe[ausente-/auth/current_user]»
ROJO  | la página v2 abre sin el token: dice «FAILED tests/test_csrf.py::test_sesion_sin_token_csrf_lo_recibe_y_escribe[ausente-/dashboard]»
ROJO  | la pestaña no mira si el token cambió: dice «FALLA: entró otro usuario y la pestaña no lo avisó»
sabotajes con falla: 0
```

### Hallazgos de la autorrevisión

Las filas 1 a 5 salen de `/code-review high` (Opus, alto) y del adversario
(Sonnet, alto). No guardé de cuál de los dos salió cada una; las dos
revisiones corrieron sobre `4931b82`.

| # | hallazgo | qué se hizo |
|---|---|---|
| 1 | con la exención del front, una pestaña sin token escribía a nombre de otro usuario si éste entraba antes de que supiera quién era | confirmado con rojo antes; arreglado en `8463f7d` |
| 2 | tres hallazgos sobre la carrera al abrir la v2: el token llegaba con una respuesta cualquiera, después de que la pestaña ya había leído el suyo | resueltos por `/dashboard`. La sonda da un solo `Set-Cookie` csrf, en `GET /dashboard`, ningún 403, y `/auth/current_user` responde entre 237 y 350 ms, contra ~1350 ms antes |
| 3 | un cliente Bearer sin cookie de sesión recibe `Set-Cookie` csrf | informativo: no le da nada, su credencial no viaja en cookie |
| 4 | «Salir» sin token | ya cubierto por `csrf1.sh` |
| 5 | doble `Set-Cookie` si una ruta emite por su cuenta y además valida la sesión | especulativo: las que emiten solas son login y registro, sin sesión previa; el navegador se queda con el último |
| 6 | `/security-review` (Sonnet, alto), sobre `392423b`: nada ≥ 8; descartó fijación de token, emisión a sesión vencida o revocada, Bearer contra cookie y emisión en exentas | — |

Preexistentes, no tocados: login CSRF sobre `/auth/login` exento; la cookie de
verificación de correo se fija con un GET; el double-submit no está firmado
(un subdominio podría plantar la cookie; este cambio no lo empeora, porque
nunca reemplaza un token que ya está).

### Riesgos

- `GET /dashboard` ahora consulta la base. Si la base no responde, la página
  da 500 en vez de servirse; un error que no sea `HTTPException` se propaga.
- La transición de prueba vencida a `past_due` que hace `get_current_user`
  ahora también corre al abrir `/dashboard`. Es el mismo efecto que ya tenía
  cualquier lectura autenticada.
- Un cliente Bearer recibe la cookie `csrf_token` (fila 3).

### chequeo-6, salida entera

```
chequeo-6 d21e16d..9fe55d4: avisos para mirar, no un veredicto
producto +14/−2
arnés +163/−8
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/auth/dependencies.py: 146 → 148
  proyecto_maria/main.py: 11269 → 11279
avisos: 0
```

### Para reproducir

```bash
git checkout 9fe55d4
# 1. 38 passed
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test python -m pytest -q --no-cov tests/test_csrf.py
# 2. 8 ROJO, «sabotajes con falla: 0»
PY=$(which python) PUERTO=8879 scripts/testing/sabotajes/csrf3.sh 9fe55d4
# 3. 0 avisos
python docs/pm/herramientas/chequeo-6.py d21e16d 9fe55d4
```

### Archivos de producto tocados

`proyecto_maria/auth/dependencies.py` y `proyecto_maria/main.py`
(`CSRFMiddleware` y `GET /dashboard`), y `CHANGELOG.md`. `app_v2.js` cambia
en `0510d47` y vuelve a quedar igual que en la base en `8463f7d`.

---

/compact conservar: Dev 1, rama claude/dev-tecnica. CSRF-3 entregada en
9fe55d4 (informe en el commit de arriba), sin D. Sigue COBRO-CORTE-1, en tu
orden. Nada se publica sin el «dale» de Emi; nunca main.
