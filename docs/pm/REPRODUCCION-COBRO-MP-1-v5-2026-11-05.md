# Reproducción de COBRO-MP-1 vuelta 5 (2026-11-05, PM principal)

Sobre `736fed6` (rama `claude/dev-tecnica`, informe en `885ee89`). Base de la
vuelta: `9161e0a`. Producto: una línea en `main.py` (`/api/billing/me`):
`cancelar_corta_acceso` pasa de mirar `db_user` a mirar `billing_entity`, la
misma cuenta que muestra la respuesta.

## Lo que corrí

| Qué | Resultado |
|---|---|
| `test_cancelar_avisa_por_la_cuenta_que_da_el_acceso` en `9161e0a` | `2 failed, 2 passed`: fallan `org_impaga_fila_en_prueba` y `org_activa_fila_impaga`, como dice el informe |
| el mismo caso en `736fed6` | `4 passed` |
| suite en `736fed6` (`pytest -q --no-cov tests/`) | `4419 passed, 121 skipped, 3 xfailed` en 604 s |
| `cobro_mp1.sh 736fed6` | 148 ROJO con su texto, «sabotajes con falla: 0», `EXIT=0`; el único VERDE es el esperado («sin mirar antes de insertar: sigue en verde, como tiene que ser») |
| `chequeo-6.py 9161e0a 736fed6` | producto +3/−2, historia vacía, 1 AVISO: la anónima de `pantalla_orden1.js:281`, que es de ORDEN-1b (en la cola por D50) |

## Mis negativos, con ejemplos distintos de los de la devolución

Seis filas más, agregadas a una copia del módulo y corridas en las dos SHAs:

| Organización | Fila del usuario | Espera `corta` | `9161e0a` | `736fed6` |
|---|---|---|---|---|
| `trial` +10 | `past_due` −30 | False | FALLA | pasa |
| `canceled` +5 | `active` +20 | False | pasa | pasa |
| `trial` −1 (vencida) | `active` +20 | True | FALLA | pasa |
| `canceled` −2 | `trial` +10 | True | FALLA | pasa |
| `organization_id` que no existe | `past_due` −30 | True | pasa | pasa |
| `organization_id` que no existe | `active` +20 | False | pasa | pasa |

Con una organización que no existe, `_get_billing_entity` vuelve a la fila
del usuario, y el aviso también: coherente.

## Adversario (Sonnet, alto, contexto nuevo)

Matriz de 72 casos: 6 estados de organización × 6 de la fila, con y sin
suscripción, con un miembro que no es el dueño. No encontró nada nuevo que
bloquee.

- Lo único que da peor que la base: una organización `active` en sus días de
  gracia, con la fila del miembro con días. Ahora el aviso dice «dejás de
  usar CDI» y, al cancelar, la organización sigue con acceso. Es el riesgo
  que la Dev ya había declarado (D51): con organización, cancelar sólo cambia
  la fila del usuario, así que ningún texto describe bien el efecto. El aviso
  ahora describe el acceso de la cuenta que muestra la pantalla, que es lo
  que pedía la devolución.
- Ya era así en la base, y el cambio no lo mueve:
  - un miembro que no es el dueño ve «Cancelar»;
  - `suscripcion_abierta` mira la fila del usuario;
  - con la fila `canceled`, sin suscripción, da un 409.
  Todo eso va a la pieza de D51.
- El front sólo lee `cancelar_corta_acceso` en `profile.js`; no hay otro
  llamador.

## Veredicto

Aceptada. Lo que falta, que cancelar con organización actúe sobre la cuenta
que da el acceso y que sólo pueda hacerlo quien corresponda, es D51, una
pieza aparte que todavía no está en el roadmap: se la propongo a Emi.
