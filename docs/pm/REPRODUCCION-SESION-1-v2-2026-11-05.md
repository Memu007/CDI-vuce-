# SESION-1 (vuelta 2): reproducción de la PM, 2026-11-05

Producto `c429307`, informe `16d849d`, base `f9e99e8`. Rama `claude/dev-maria`.
Entorno: venv Python 3.12 (como la CI), Postgres 16 local, SQLite para pytest.

**Veredicto: devolución.** Lo que la pieza promete aguanta (ningún token que no
sea la sesión vigente entra), pero dos adversarios encontraron dos causas que
reproduje: un reset del dueño que no gana, y un tope que congela la app.

## Lo que coincide con el informe

| Puerta | Resultado PM |
|---|---|
| `tests/test_sesion1.py` en `c429307` | `29 passed` |
| la misma prueba en la base | `12 failed, 17 passed` (distingue) |
| `sesion1_motores.py pg` | `pg: todo OK`, rc=0 |
| `sabotajes/sesion1.sh c429307` | 29 `ROJO`, `sabotajes sin rojo: 0`, salida 0 |
| `chequeo-6.py f9e99e8 c429307` | `producto +108/−257`, historia vacía, `avisos: 0` |
| suite completa en `c429307` | `5 failed, 4910 passed, 355 skipped, 3 xfailed` en 675 s (ver abajo) |

## Negativo propio (distinto del de la Dev)

`test_pm_ses1_neg.py` (en el scratchpad de la PM, no en el repo): once tokens
contra `/api/user/profile`, todos 401, y el vigente 200. Sub de A con jti de
B, sub de B con jti de A, sin jti, vencido, otra clave, `type` de verificación,
`type` vacío, el token de verificación real, `alg none`, sub vacío, sub
inexistente. Más: cookie basura con Bearer válido de otro usuario da 401.

- En `c429307`: `2 passed`.
- En la base: `1 failed`. Entran (200) los dos tokens con `type` y jti vigente.
  La prueba distingue.

## Hallazgos de los adversarios, reproducidos y clasificados

**A. Un reset del dueño no gana contra un cambio de clave ya validado
(Opus alto). Reproducido por la PM. De antes, agravado por la pieza.**
`change_password` (`main.py:2373-2379`) valida la clave contra el hash leído al
entrar y guarda la nueva con un UPDATE por id, sin condición. Si el dueño
resetea en el medio, el reset se pierde y `abrir_sesion(…, db_user.password)`
le da al atacante un token vigente.

```
RESET_DEL_DUENO 200 {'message': 'Contraseña actualizada exitosamente'}
CAMBIO_DEL_ATACANTE 200 {'success': True, ... 'access_token': 'eyJhbGciOiJI…'}
TOKEN_NUEVO_DEL_ATACANTE_ENTRA 200
CLAVE_GUARDADA_ES_LA_DEL_RESET False ES_LA_DEL_ATACANTE True
LOGIN_DUENO_CON_CLAVE_DEL_RESET 401
```

Misma causa en el cambio de email (`main.py:2258`, `2289-2304`): el email del
atacante se guarda después del reset (`EMAIL_CAMBIADO 200 email_guardado
atacante@example.net`; reproducción del adversario, no repetida por la PM). Y
dos cambios de clave a la vez dan 200 con un token ya muerto (Sonnet, 4 de 12).

**B. El tope de la clave actual congela el pool con ~35 pedidos a la vez
(Sonnet alto). Reproducido por la PM. Nuevo de la pieza.**
`verificar_clave_actual` llama a `limites_auth`, que abre otra conexión
(`engine.connect()`/`begin()`) mientras el pedido ya tiene la suya de
`get_db`. Pool de 20+30. PM, 40 `PUT /api/user/profile` con email nuevo y clave
mala, un token, uvicorn real con 1 worker en Postgres:

```
c429307  PUT 40 {400: 3, 500: 37} max seg 30.7 otro usuario: (200, 29.4)
f9e99e8  PUT 40 {400: 40}         max seg 2.6  otro usuario: (200, 0.6)
```

Mismo patrón (contar o mirar el bloqueo con la sesión del pedido abierta) en
`/auth/login` (`main.py:3109-3179`) y `/auth/request-password-reset`
(`main.py:1678`), que vienen de ABUSO-1.

**Menores**
- Dos secretos: se firma con `SECRET_KEY` (`main.py`) y se verifica con
  `settings.jwt_secret`. Sólo difieren con una variable vacía (`JWT_SECRET_KEY=""`):
  login 200 y todas las rutas 401. De antes; la pieza le suma verify-email.
- `datos_del_token` no exige `exp`: un token firmado sin `exp` no vence. Ningún
  camino del producto lo emite. De antes.
- El logout de v1 (`static/app.js:4085`) no manda `X-CSRF-Token`: con CSRF
  activo da 403 y no cierra. De antes; depende de D60.
- Dos usuarios que pasan a un mismo email libre a la vez: un 500 en vez de 400,
  sin duplicado. De antes.

## Rojo de la suite: no es de la pieza

Los 5 son `test_despacho1b.py` (3) y `test_rendimiento1c.py` (2). Dan
`5 failed, 293 passed` igual en la base `f9e99e8`. Causa: `pypdf>=6.19.0` sin
tope instaló `6.21.4`, que corta antes con `Invalid PDF file: Maximum page tree
page entry limit exceeded!` en vez del mensaje propio. El PDF igual se rechaza
(400); cambia el texto y el camino. La suite de la Dev era con un pypdf
anterior.

## No corrido

- Los hallazgos de email y de dos cambios a la vez en la base.
- Postgres para el hallazgo A (el UPDATE por id no mira la clave en ningún motor).
