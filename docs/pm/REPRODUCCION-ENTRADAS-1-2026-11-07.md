# Reproducción ENTRADAS-1 (Dev MARIA), 2026-11-07

Base `b1e2daf`, producto entregado `589fd0b`, informe `59ab7fb`. Worktree
`/tmp/cdi-pm/rev-ent1`, venv de PM, SQLite propia y Postgres 16 local (55462).

**Veredicto: devolución sólo de pruebas.** El producto aguanta todo lo que se
probó; las pruebas no distinguen cuatro daños reales del arreglo.

## Lo que corrió la PM

| Qué | Resultado |
|---|---|
| `chequeo-6.py b1e2daf 589fd0b` | igual al informe: `producto +60/−33`, un `AVISO` de +27 netas, explicado y aceptado |
| grep de historia de §6 | vacío |
| `test_entradas1.py` + `test_user_profile_coverage.py` | `68 passed` |
| `entradas1_postgres.py` (PG 55462, rol `cdi`) | `fallas: 0` |
| `sabotajes/entradas1.sh 589fd0b` | `BASE en verde`, 22 `ROJO`, `sabotajes con falla: 0` |
| Suite completa sobre `589fd0b` | en curso al escribir; se completa en el commit siguiente |
| Negativo de PM | login con clave de 73 bytes, surrogate, NUL o 200 bytes: 401; `current_password` así en cambio de clave: 400 «incorrecta»; nueva de 72 bytes con «ñ» pasa el validador de largo, de 73 da 422 |

## Adversarios

**Opus alto** (producto, Postgres): sin 500 nuevo ni regresión de acceso;
login y `current_password` siguen como `str` libre, así que ninguna cuenta
queda afuera. Topes iguales a las columnas (`User.name`/`email` 100,
`Organization.name` 200, `Invitation.email` 100). Hallazgos:

1. Nuevo, UX: el 422 de la clave larga se ve «[object Object]» en el reset y
   en el perfil, y el de un nombre largo sale en inglés. Es D100.
2. Nuevo, menor: el alta de estudio ahora valida el email con la regla del
   registro (la landing ya la aplicaba); agrupar y desagrupar con tipos
   malos dan 422. El frontend no llama esas rutas. Aceptado.
3. Previo: un NUL en el **path** da 500 en Postgres en
   `GET /api/invitations/{token}` (sin sesión), `agrupar` y `desagrupar`.
4. Previo: `agrupar` con más de 32767 `item_ids` da 500 en Postgres
   (límite de parámetros del driver).

**Sonnet alto** (pruebas, mutaciones en copia propia): el producto aguanta;
las pruebas son más flojas que él. Con cada mutación siguiente la suite de la
pieza da `54 passed`:

1. El 422 devuelve la clave en `input` o dentro de `msg`. Ninguna prueba
   exige que la clave no aparezca en la respuesta.
2. El tope pasa de `> 72` a `> 73`: no hay caso de 73 bytes justos (`LARGA`
   mide 74). Con bcrypt 5, 73 bytes es el 500 que la pieza cierra.
3. `\x00` fuera de `_NO_GUARDABLE_EN_PG`: sólo caen los 4 casos de clave;
   ningún texto (nombre, invitación, perfil, ítems) cae, porque en SQLite la
   aserción `< 500` no puede fallar con NUL. Los sabotajes de texto usan
   sólo el surrogate.
4. El handler 422 vuelve a `JSONResponse`, o `allow_nan=True`: verde.
5. Previo, bajo: un username con `\n` final pasa la regex del registro
   (`$` de `re.match`). Va a la cola de limpieza; no es 500.

## Clasificación

- Hallazgos de pruebas 1 a 4 de Sonnet: **devolución** (la prueba no
  distingue el defecto, `CLAUDE.md` §1).
- Opus 3 y 4: previos, de la familia de D104 → entran en la pieza nueva
  ENTRADAS-2.
- Opus 1: D100. Opus 2: aceptado como cambio de contrato menor.

## No corrido

`smoke_friccion.sh`, `ataque_aislamiento.sh` (la pieza no toca permisos),
gunicorn.
