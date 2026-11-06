# Reproducción de EMAIL-1 (2026-10-28)

Entrega de la Dev MARIA en `2b93071`. Diff de producto `e22a5cf..2b93071`:
sólo `proyecto_maria/main.py` (+53 −22): `_cuenta_por_email` y sus usos en
recuperar usuario, recuperar contraseña, login, perfil y registro. El envío
de correos, los tokens y las plantillas son anteriores a la pieza.

## Adversario (Sonnet alto, contexto nuevo)

`tests/test_email1.py` + `tests/test_abuso1.py`: `82 passed`. Ningún camino
mandó el correo de una cuenta a otra; la respuesta no cambia exista o no la
cuenta; el enlace usa `FRONTEND_URL` aunque venga otro `Host`. Hallazgos,
reproducidos por la PM con sus pruebas (`p1.py`, `p2.py`, contra una copia
de `2b93071`, sin correo real):

1. **Anterior a la pieza.** El nombre de la cuenta va sin escapar en el HTML
   de los dos correos (`<p>Hola {user.name or user.username},</p>`; ya está
   en `e22a5cf`, líneas 1554 y 1601). Registrando una cuenta con el email de
   otra persona y un nombre con HTML, recuperar usuario y recuperar
   contraseña le mandan a esa persona el HTML del atacante desde el
   remitente de CDI. Salida: «cuerpo tiene html atacante: True» en los dos.
   El registro no verifica el email por defecto.
2. **Anterior a la pieza.** El correo se manda síncrono dentro de la ruta:
   con un SMTP local que tarda 2 s, email que existe `2.26 s, 200`, que no
   existe `0.06 s, 200` (el tiempo delata la cuenta), y `/health` tardó
   `1.68 s` mientras tanto (se traba el worker).
3. **Anterior a la pieza.** Fuera de `ENVIRONMENT=production`, con el envío
   fallido, la respuesta trae `dev_token_hint` sólo si la cuenta existe
   (`existe: ['dev_token_hint', 'message'] | no existe: ['message']`).
   Depende de cómo está `ENVIRONMENT` en Railway; ya registrado en
   `REPRODUCCION-ENSAYO-2026-10-07.md`.
4. **Anterior a la pieza.** Producción sin `FRONTEND_URL`: `existe 500 | no
   existe 200`. Sólo con la configuración mal puesta.
5. **Anterior a la pieza.** Un token de recuperación pedido antes sigue
   valiendo después de usar uno nuevo: `t1 (anterior, no usado) tras reset
   con t2: 200`. Expira en 1 hora; un token usado da 400.
6. **De la pieza, menor.** Si `if not email: return None` de
   `_cuenta_por_email` pasa a `if False:`, `test_email1.py` da `24 passed`.
   Haría falta una cuenta con email vacío.

## Veredicto

Aceptada sobre `2b93071`. Lo de la pieza está bien; el 6 es una prueba que
se suma. Del 1 al 5 son de antes: van a riesgos y la PM le propone a Emi
una pieza de seguridad para el 1, el 2 y el 5.
