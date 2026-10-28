# Reproducción de SESION-1 (2026-10-28)

Entrega de la Dev MARIA en `895ee73`. Veredicto: **devolución**.

## Suite

No corrida por la PM sobre `895ee73`: la devolución cambia producto y la
suite se corre sobre la vuelta.

## Lo que reprodujo la PM

Con `probe.py` en SQLite (sólo el arnés toca `server.py`, para abrir la
puerta del login en vuelo; el producto, tal cual):

```
[1 copia] change-password 200; la copia del mismo token entra: 200; active_jti igual al del token: True
[2 reset] login con clave vieja (en vuelo) 200; reset 200; después del reset el token del atacante entra: 200; la víctima vieja: 401
[3 change] login viejo 200; change 200; atacante entra: 200; víctima (quien cambió) entra: 401
```

Es D43 (a) y (b) de la Dev: un login con la clave vieja que termina después
del cambio o del reset pisa `active_jti` y deja afuera a quien cambió la
clave; y cambiar la clave no corta una cookie copiada, aunque el aviso y el
CHANGELOG dicen que «cierra las otras».

También reproducido, con `test_adv.py` del revisor:

- el link de verificación del correo (válido 24 h) vuelve a abrir sesión
  después de un logout y de un cambio de clave, y se puede usar otra vez;
- `/auth/me` y `/ui_event` aceptan un token revocado;
- con `active_jti` en NULL, el token de verificación sirve como Bearer.

Mutantes que sobreviven, `test_sesion1.py` + `test_user_profile_coverage.py`:

| mutante | resultado |
|---|---|
| sacar `user.active_jti is not None and` de `revocar_sesion_de_la_request` | `31 passed` |
| decodificar con `options={"verify_signature": False}` | `31 passed` |

## Del revisor, no corrido por la PM

Sonnet alto, `mut.py` del revisor, mismo par de archivos de prueba. 3 de 10
mutantes sobreviven (`31 passed`):

- la cookie deja de ganarle al header (`M3`);
- se saca la validación de tipo de `current_password` en el perfil (`M8`);
- el perfil no pide la clave si el correo anterior estaba vacío (`M9`).

Opus alto: los 19 sabotajes de la Dev dan ROJO y `sesion1_motores` en PG da
26 OK. El informe cita `request.state.token_jti`, que no existe en
`895ee73`.

## Causa

La revocación se mira sólo en `get_current_user`. Todo camino que emite una
sesión o decodifica un token por su cuenta la saltea: verify-email,
`/auth/me`, la telemetría y el logout. Y el login escribe `active_jti` sin
comprobar que la clave con la que entró siga vigente.

## Riesgos que la Dev ya escribió (D43), sin tocar en esta pieza

- `ADMIN_USERNAMES` compara contra el correo (`main.py:1457`): alto y de
  antes. Va a Emi con la pieza de seguridad.
- El logout v1 no pide CSRF; el reset pendiente sobrevive a un cambio de
  clave.

## Veredicto

Devolución sobre `895ee73`. Lo que se pide está en `PARA-DEV-2.md`.
