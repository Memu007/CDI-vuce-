# Reproducción de COBRO-MP-1, vuelta 2 (2026-10-29)

Entrega de la Dev técnica: producto `999b27a`; pruebas `4ef59f4`; rama en
`36cbd1d`. Base de la vuelta: `784e793` (la devolución anterior está en
`REPRODUCCION-COBRO-MP-1-2026-10-29.md`).

## Lo que corrió la PM

- `cobro_mp1.sh 4ef59f4`: 108 «ROJO  |», 5 «BASE» (la carrera de D y los pagos a la vez en Postgres, el perfil y la v1 en verde), el «VERDE» de control y «sabotajes con falla: 0», rc=0, como el informe. Los sabotajes no cubren la regresión de abajo: ninguno vuelve atrás la regla que la causa.
- `cobro_mp1_postgres.py` en PG16 (`con_pg16.sh`): 29 «OK», «fallas: 0», rc=0. Los NUL que prueba están en el primer nivel; el NUL anidado (`payer.id`, la tarjeta) no está entre ellos.
- **La regresión del adversario Opus, reproducida en los dos SHAs**, con sus
  pruebas de sondeo (`-k "A_ or A2 or B_ or H_"`; cada una afirma que el
  pago se acredita):

  | caso | `784e793` | `4ef59f4` |
  |---|---|---|
  | A: aviso `payment` sin referencia, después el de cobro | 400, Mercado Pago reintenta; el cobro acredita: `active` | `200 … "pago rechazado: external_reference desconocida: ''"`; el cobro: `200 … "payment_id ya procesado"`; `past_due` |
  | A2: igual, con `metadata.preapproval_id` | acredita | igual que A |
  | B: primero el cobro sin decir de qué suscripción, después el `payment` | `200 skipped "cobro autorizado con forma inesperada"`; el `payment` acredita | `200 … "pago rechazado: el cobro no dice de qué suscripción es"`; el `payment`: `"payment_id ya procesado"`; `past_due` |
  | H: cobro pendiente, después `payment` aprobado | 400 reintentable, `past_due` (ya fallaba) | rechazado para siempre con `cuenta ''`, `past_due` |
  | C: 503 y reintento | — | `[503, 200, 200, 200]`, se aplica una vez |

  Resultado: en `4ef59f4`, `4 failed, 1 passed`; en `784e793`,
  `4 passed, 1 failed` (H).

**La causa.** La regla nueva «rechazado» convierte en estado permanente lo
que antes era un 400 reintentable: un aviso cuyo pago no se puede atribuir
todavía a una cuenta. Como el par (`payment`, `subscription_authorized_payment`)
comparte `payment_id`, el primero que llega marca el pago y el segundo lo
encuentra «ya procesado», en los dos órdenes. Resultado: renovación cobrada
y no acreditada, sin reintento. Depende de la forma real de los avisos de
Mercado Pago (D30, no verificada), por eso pesa igual: la pieza promete que
cada pago se aplica una vez y entero.

## Adversario Opus alto (contexto nuevo, sobre `4ef59f4`)

1. **Alta, regresión:** la de arriba (main.py ~10768-10800;
   `_registrar_pago_mp` ~10534). La prueba de la Dev
   (`tests/test_cobro_mp1.py:534-538`) cubre sólo el orden benigno.
2. **Media, preexistente y agravada:** lecturas síncronas a Mercado Pago
   dentro del manejador async bloquean el servidor (un plan tardó 2,71 s
   mientras esperaba el aviso); `/api/payments/webhook` sin límite de
   pedidos y con IPN sin firma aceptado.
3. **Media, preexistente:** un segundo miembro de la organización crea otra
   suscripción para una org activa: dos cobros por mes (main.py
   ~10948-10981).
4. **Media, preexistente:** si Mercado Pago contesta 404 por la suscripción
   vieja, el checkout queda en 503 para siempre (main.py ~10952-10955).
5. **Baja, mutantes vivos:** monto `>= 0`, moneda `None`, fecha sin zona, y
   `_guardable_en_pg` que no limpia valores anidados (NUL en `payer.id` o
   en la tarjeta da 500 en PG16, reproducido con su script).

Aguanta: tres recargas a la vez en PG, el mismo plan tres veces, liberar el
candado, 503 y reintento aplicado una vez, 15 cuerpos raros con 200 y
ninguno con 500.

## Adversario Sonnet alto (contexto nuevo, sobre `999b27a`)

Base: las tres suites `187 passed`; `cobro_mp1_postgres.py` en PG16
`fallas: 0`.

1. **Alta/media, preexistente: una organización puede quedar con dos
   suscripciones cobrando, y «Cancelar plan» no corta el cobro.**
   `billing_checkout` no exige ser el dueño y guarda la suscripción en el
   `User` que la pidió; `cancel_billing` y `/api/billing/me` leen ese
   `User`, no la organización.
   `CREADAS [('preapproval','org:…:premium'), ('preapproval','org:…:premium')]`;
   el miembro cancela: `SUS {'nueva-1': 'authorized', 'nueva-2': 'cancelled'}`
   y la pantalla dice «Plan cancelado». Es el mismo que el 3 de Opus.
2. **Media: la suscripción `authorized` de una cuenta no vigente se cancela
   sin avisar** (D13 c). Caso nuevo: `active -1`, dentro de la gracia; si la
   renovación llegó tarde y el cliente toca «Activar», se cancela la que
   acaba de renovar.
3. **Media, hueco de prueba:** ninguna prueba mide que un pago de plan
   reinicie el uso. Sacar `ops_used_this_period` del bucle unificado deja
   las 187 en verde (igual `billing_period_started_at` y
   `extra_ops_expires_at` de la recarga).
4. **Media/baja, huecos de prueba:** `trial` fuera de `vigente` en
   `_extender_periodo` (pagar en la prueba perdería días); el tope de
   recargas aplicado a planes; tope en 101 (el borde nunca prueba 91);
   últimos 4 al revés.
5. **Baja, sólo Postgres:** sacar los cortes de `moneda`, `aprobado_en` o
   `motivo` deja `cobro_mp1_postgres.py` en `fallas: 0`.
6. **Baja, por lectura:** «Próximo cobro» con una suscripción que nunca se
   autorizó (el id se guarda al abrir el checkout).

Mutantes: 37; 16 muertos (dos sólo en Postgres: sin `with_for_update` y sin
limpiar NUL); vivos que importan: los de los puntos 3 a 5. Aguanta:
atomicidad (si `_extender_periodo` revienta, 500 y sin fila), panel de
admin con 403, sin XSS, fechas de Mercado Pago en 3.12.

## No corrido por la PM

La suite completa, `/code-review` y `/security-review` sobre `999b27a`; la
pantalla con un navegador fuera del script; nada contra Mercado Pago real.

## Veredicto

Devolución sobre `4ef59f4`. Aguanta lo pedido en a, d, e y f, pero la
vuelta trae una regresión de plata: un aviso que todavía no se puede
atribuir a una cuenta queda `rechazado` para siempre y le cierra el paso
al otro aviso del mismo pago; la renovación se cobra y no se acredita.
Parte viene de la regla b de la PM, que no decía de qué lado cae «todavía
no sé de quién es». El detalle, por causa, está en `PARA-DEV.md`.
