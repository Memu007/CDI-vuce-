# Reproducción D102 (a), versión fija de bcrypt — 2026-11-09

Entrega de la Dev MARIA: producto y pruebas `af924ea` (base `d39c1f6`),
informe `7755221` en `PARA-PM-2.md`. Revisó la PM principal.

## Diff

`git diff d39c1f6 af924ea --stat`: `requirements.txt` +1 (`bcrypt==5.0.0`),
`tests/test_entradas1.py` +16, `CHANGELOG.md` +4. Producto +0/−0 en
`proyecto_maria/`.

El `Dockerfile` (lo usa Railway por `railway.json`) y la CI instalan el
`requirements.txt` de la raíz: el pin queda donde se construye.
`proyecto_maria/requirements.txt` no lo lee nadie.

## Corrido por la PM

- Venv de la PM: `bcrypt 5.0.0`.
- `pytest -q --no-cov tests/test_entradas1.py -k 72` sobre `af924ea`:
  `5 passed, 75 deselected`.
- Mismo comando con `bcrypt==4.3.0` instalado aparte (`--target` en el
  scratchpad, `PYTHONPATH` delante): `1 failed, 4 passed`, con
  `E   assert 200 == 401` en el login. La prueba distingue el defecto.
- `verify_password` (`main.py:3208`) atrapa la excepción de `checkpw` y da
  `False`: con bcrypt 5 una clave de más de 72 bytes da 401, no 500.
- `pwd_context` de passlib (`main.py:166`) se crea al importar y las pruebas
  importan la app: passlib 1.7.4 con bcrypt 5 no rompe el arranque (Python
  3.12, el del `Dockerfile`).

No corrido por la PM: la suite completa (el informe trae 5453 passed) y
`ataque_aislamiento.sh` (tampoco lo corrió la Dev; la pieza no toca datos).

## Riesgo

El tope de 72 bytes del alta (`_clave_hasheable`) entró el 07/11 y no está
en `main`. Si la imagen de producción tiene bcrypt 4.x y alguien se registró
con una clave de más de 72 bytes, después de publicar esa clave deja de
entrar (con bcrypt 5 `checkpw` falla y da 401). Es raro, y se arregla con un
reseteo de clave. Va con la publicación.

## Decisiones

- **D153** (sacar `pwd_context` y passlib): **(a)**, a `COLA-LIMPIEZA.md`.
- **D154** (tope propio de 72 bytes en `verify_password`): **(a)**, no se
  agrega: el `except` ya da 401 y el alta ya rechaza.

Veredicto: **aceptada sobre `af924ea`**, sin integrar.
