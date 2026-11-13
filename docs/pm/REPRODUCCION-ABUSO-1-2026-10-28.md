# Reproducción de ABUSO-1 (2026-10-28)

Entrega de la Dev MARIA en `43916a7`. Veredicto: **devolución**.

## Suite

No corrida por la PM sobre `43916a7`: la devolución cambia producto.

## Lo que reprodujo la PM

Mutantes que sobreviven, `test_abuso1.py` + `test_auth_login.py`:

| mutante | resultado |
|---|---|
| bloqueo de 15 min pasa a `bloqueo: float = 60` | `63 passed` |
| ventana del tope por correo en recuperar, 3600 → 60 | `63 passed` |

Las pruebas no distinguen cuánto dura el bloqueo.

## De la Dev (D44), no corrido por la PM

El login toma dos conexiones a la base (`main.py:2770`, `2778`, `2827`).
Con 120 logins malos a la vez sobre PG: 401:96 / 500:24, `/health` en
33,9 s y el pool agotado.

## Del revisor (Sonnet alto), no corrido por la PM

- `len(clave) <= 300` sobrevive como mutante, y en PG una clave de 200
  caracteres da `StringDataRightTruncationError`.
- Un correo con un surrogate suelto da 500 en `/auth/recover-username`
  (de antes).
- La IP sale de XFF según `TRUSTED_PROXY_HOPS`: entrando directo se
  esquiva el tope; con una CDN delante, los usuarios compartirían clave.
  Hipótesis: se valida con el log de 429 después de publicar.
- IPv6 y puerto sin normalizar; una falla vuelve a bloquear tras un bloqueo
  viejo (heredado); deadlock en PG entre DELETE y upsert (38 de 400 con
  ventanas cortas); filas sin tope; un token revocado sigue escribiendo
  telemetría (familia de SESION-1); el login tarda 0,673 s con usuario que
  existe y 0,010 s sin él.

## Veredicto

Devolución sobre `43916a7`. Lo que se pide está en `PARA-DEV-2.md`; lo
demás va a riesgos.
