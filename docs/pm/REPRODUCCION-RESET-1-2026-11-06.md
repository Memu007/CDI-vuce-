# RESET-1: reproducción de la PM (2026-11-06)

Producto `02a21e7` (informe `5e69f63`, rama `claude/dev-maria`), base `5b0ca2b`.
Árbol previo al arreglo del pedido: `82130a8`. Veredicto: **aceptada, sin
integrar** (misma razón que `ca87d82`: la rama de MARIA trae `e0b8626`).

## Puertas (corridas por la PM, entorno de prueba, sin red)

| Puerta | entrega | base | `82130a8` |
|---|---|---|---|
| `tests/test_reset1.py` | `6 passed` | `4 failed, 2 passed` | `1 failed, 5 passed` (el vencimiento) |
| `scripts/testing/reset1_postgres.py` (PG 16) | `fallas: 0` | `fallas: 3` | `fallas: 1` (pedido a la vez que el cambio de email) |
| `chequeo-6.py 5b0ca2b 02a21e7` | `producto +23/−15`, `avisos: 0`, historia vacía | | |
| `sabotajes/reset1.sh 02a21e7` | 8 ROJO, `fallas: 0` | | |
| suite completa | `5 failed, 4951 passed, 355 skipped, 3 xfailed` | | |

Los 5 rojos de la suite son `test_despacho1b.py` (3) y `test_rendimiento1c.py`
(2): pypdf 6.21.4 responde «Maximum page tree page entry limit exceeded» antes
del tope propio. Dan los mismos 5 rojos sobre la base `5b0ca2b`
(`5 failed, 293 passed`): son PYPDF-1 (D73), no de esta pieza.

## Negativos de la PM (SQLite, `tests/test_pm_reset1.py`, fuera del repo)

| Caso | entrega | base |
|---|---|---|
| El email va a otro y vuelve al original: el link pedido antes no sirve | pasa | **falla** (`200 == 400`) |
| Otro usuario cambia email y clave y usa su link: mi link sigue sirviendo | pasa | pasa |

## Adversarios con contexto nuevo (Opus alto y Sonnet alto)

Ninguno encontró entrada de quien no es el dueño, dueño trabado, 500,
deadlock ni regresión. Postgres (scripts propios, esperas por condición en
`pg_stat_activity`): el mismo link 6 veces a la vez da `[200, 400×5]` (base
`200×6`); dos links distintos a la vez `[200, 400]` (base `[200, 200]`); el
pedido primero y el cambio de clave o de email detrás dejan el link muerto
(base: sirve); martillo de 40 rondas con 7 operaciones a la vez: 0 respuestas
5xx, 0 anomalías (base 50). Recorrido por la API: mayúsculas, espacios, emails
que difieren sólo en mayúsculas, miembros de estudio, sesiones por Bearer y
cookie: igual o mejor que la base.

Observaciones bajas, todas de antes de la pieza:

1. En SQLite el `FOR UPDATE` no hace nada: el pedido a la vez que un cambio
   de email puede dejar un link vivo. Producción es Postgres.
2. Fuera de producción y sin SMTP, `request_password_reset` devuelve
   `dev_token_hint` en la respuesta (`main.py:1720`). `IS_PRODUCTION` toma
   `ENVIRONMENT` con valor por defecto `development`: si un despliegue no la
   fija, quien sepa un email recibe el link. Va como RESET-2.
3. El rehash de demo (`main.py:3171`, sólo fuera de producción) y
   `_archived_test_email` (D83) escriben la clave o el email sin barrer links.
4. Dos casos del test (`el mismo link dos veces` y el del vencimiento sobre la
   base) no distinguen el defecto solos; el sabotaje que saca `expires_at >
   now` sí da rojo.

## No corrido

`/security-review` como comando (la Dev lo hizo en línea; la PM cubrió con dos
adversarios). SMTP real, producción y terceros.
