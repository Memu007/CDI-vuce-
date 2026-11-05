# Reproducción de COBRO-MP-1 vuelta 4 (2026-11-05, PM principal)

Producto `9161e0a` sobre base `9048b6a` (informe `60d9626`). Revisión
adversaria con contexto nuevo (Opus, esfuerzo alto) y reproducción mía del
hallazgo.

## Resultado

Devolución corta por una causa. El dinero se sostiene: ningún camino de
cancelar da acceso gratis, corre `trial_ends_at` hacia adelante o deja una
suscripción cobrando sin salida. La devolución de la vuelta 3 queda
resuelta: cualquier `billing_status` con suscripción abierta sale.

## Puertas (adversaria)

| Qué | Salida |
|---|---|
| `test_cobro_mp1_cde.py` de la Dev sobre `9048b6a` | `16 failed, 15 passed` (caen en el campo nuevo de `/billing/me`) |
| Cancelar directo sobre `9048b6a`, familia none / None / expired / desconocido | `assert 409 == 200` ×4, `4 failed` |
| Lo mismo sobre `9161e0a` | `31 passed` |
| Negativos de la revisora (26 filas: fechas con y sin zona, MP caído, id desconocido, segundo cancel, reactivar) | `26 passed` |
| `cobro_mp1.sh 9161e0a` | 146 ROJO, 0 ROJO?, `sabotajes con falla: 0`, EXIT=0 |
| Sabotaje propio: sacar `db_user.trial_ends_at = ahora` | `15 failed, 42 passed` |
| Suite como CI | `4415 passed, 121 skipped, 3 xfailed in 617.18s`, EXIT=0 |
| `chequeo-6.py 9048b6a 9161e0a` | `producto +46/−44`, historia vacía, 2 AVISO: `app_v2.js:7` (D54) y `pantalla_orden1.js:280` (es de ORDEN-1b, ya en la cola por D50) |

## Hallazgo (confirmado, lo reproduje)

`/billing/me` muestra el estado de la organización (`billing_entity`), pero
`cancelar_corta_acceso(db_user)` (`main.py:3321`) mira la fila del usuario,
y `profile.js:419-424` arma la confirmación sólo con ese dato.

Caso a, organización `past_due` vencida, dueño con fila `trial` +10 y
suscripción abierta (mi corrida, `test_zz_org2.py`):

    base:  ME: past_due corta: None
    nuevo: ME: past_due corta: False
    los dos, al cancelar: CANCEL: 200 … | ORG: past_due acceso org: False

En la base la confirmación decía «pago pendiente… dejás de usar CDI»
(cierto); ahora dice «vas a poder seguir usando CDI hasta el fin del período
ya pagado», y la cuenta no tiene acceso.

Caso b (sólo la adversaria): organización `active` +20, fila del dueño
`past_due` −30. Ahora dice «dejás de usar CDI», y la organización conserva
20 días.

No movió dinero ni acceso: es lo que la pantalla promete. Es nuevo de esta
vuelta.

## Ds

- D51: la guarda ya miraba al usuario (cierto); el texto de la confirmación
  no, y empeoró en esta vuelta.
- D52: confirmado, ningún caso de la familia gana acceso.
- D53: ya era así en la base (devolvía una fecha pasada); ahora lo dice.
- D54: confirmado, los commits que tocan `app_v2.js` son de ORDEN-1b.

## No corrido

- La confirmación en el navegador: el texto se deriva de `profile.js`.
- `con_pg16.sh` fuera de `cobro_mp1.sh`: el script ya corre sus casos en Postgres.

Evidencia fuera del repo:
`/tmp/claude-0/-home-user/eb961cf0-672f-50aa-9215-aa9e8513acf1/scratchpad/cmp4/` (`sab.log`, `suite.log`, `mis_tests/`).
