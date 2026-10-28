# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-MP-2: premisa comprobada y D7 (2026-10-28 08:15 UTC)

No es una entrega. Base: `643894f` (merge de tu `a3efc3a` sobre `27e4594`).
Todavía no toqué el producto. Mientras contestás sigo con lo que no depende de
la D7, que está abajo, en «Lo que hago sin esperar».

### Premisa, sobre la base

| Hallazgo | ¿Se reproduce? | Dónde |
|---|---|---|
| C2: cancelar no llama a Mercado Pago | Sí | `/api/billing/cancel` (`main.py:2107`) sólo pone `billing_status = "canceled"` |
| C2: cancelar corta el servicio en el acto | Sí | `require_billing_vigente`, `require_active_billing` y `can_create_operation` piden `trial` o `active`. Con `canceled` dan 402: «Cancelaste tu suscripción. Reactivala para seguir usando CDI.» Además `canceled` no vence nunca (`_vencer_si_corresponde`, `main.py:1769`, y el cron) |
| C4: se puede pagar dos veces | Sí | El checkout (`main.py:10619`) no mira nada. En modo suscripción crea otra preapproval y pisa `mp_preapproval_id`, así que la vieja queda cobrando y CDI ya no la conoce |
| C4: un pago pierde los días que quedaban | En parte | COBRO-MP-1 (`_extender_periodo`, `main.py:10280`) ya suma desde el fin si la cuenta está `active`. Quedan dos casos que suman desde hoy: `canceled` con días pagados y `trial` con días de prueba |
| C8: reactivar una prueba la deja activa sin pagar | Sí | `/reactivate` (`main.py:2139`) pasa a `active` cualquier `canceled` con fecha futura, y `active` vence con 7 días de gracia |
| D9: sin token dice «activada» | Sí | `/api/payments/success` (`main.py:10043`) siempre dice «Tu cuenta Premium ha sido activada.» y guarda `user_plan = premium` en el navegador. La base no cambia: `demo-confirm` sólo toca un diccionario en memoria |

**Cómo se cancela en Mercado Pago.** El repositorio no trae documentación de
Mercado Pago, y `7f1dd2c` (mi D9 del 07/10) no está en el clon ni con
`fetch`. Lo de esa D9 sale de la auditoría y del código, y queda como
supuesto. El SDK instalado (`mercadopago==2.2.0`) tiene
`preapproval().update(id, datos)`, pero arma la ruta como
`"/preapproval" + id`, sin la barra: con el SDK la cancelación iría a otra
dirección. Por eso voy a usar `PUT https://api.mercadopago.com/preapproval/{id}`
con `{"status": "cancelled"}`, por `httpx`, igual que `_leer_cobro_autorizado_mp`.

Supuestos, porque no tengo red para comprobarlos:
- los estados de una suscripción son `pending`, `authorized`, `paused` y `cancelled`;
- una `cancelled` no se puede reactivar;
- al autorizar una suscripción nueva, Mercado Pago cobra el primer mes en el acto.

## Decisiones

**D7. Cuatro comportamientos de COBRO-MP-2 que ve el cliente.**

**D7.1 Pagar durante la prueba gratis.** Hoy el pago empieza a contar desde hoy
y los días de prueba que quedaban se pierden.
- **(a) Recomendada: los días de prueba se suman.** Si a alguien le quedan 5
  días de prueba y paga, queda activo 35 días. Es lo que pide la letra («un
  pago nunca hace perder los días que quedaban»), y no castiga al que paga
  antes.
- **(b) El pago reemplaza la prueba:** 30 días desde hoy, como ahora.

**D7.2 Segundo pago con un plan vigente.** Esto sólo se puede elegir en el modo
de pago mensual sin suscripción (preference), que es el respaldo. En
producción el modo es suscripción (DECISIONS, 2026-10-07).

En modo suscripción no hay nada que elegir, y lo hago así:
- si la suscripción guardada está `authorized` o `paused` en Mercado Pago, el
  checkout responde 409 «Ya tenés una suscripción activa» y no crea otra;
- si está `pending` (abrió el checkout y no pagó), la cancelo antes de crear
  la nueva, para que no queden dos que se puedan pagar;
- si Mercado Pago no contesta, el checkout responde 503 y no crea nada.

En modo preference, con el plan `active` y días por delante:
- **(a) Recomendada: se deja pagar por adelantado,** y suma 30 días desde el
  fin. En ese modo nada renueva solo: bloquearlo obliga a esperar el
  vencimiento para pagar.
- **(b) Se bloquea con 409 hasta que venza.**

**D7.3 Reactivar después de cancelar, con días pagados.** Una suscripción
cancelada en Mercado Pago no vuelve (supuesto). Hoy reactivar dice «Plan
reactivado. Sigue activo hasta el próximo cobro.», y con el arreglo eso sería
falso: no hay próximo cobro.
- **(a) Recomendada: reactivar lleva al checkout de una suscripción nueva.**
  El cobro es inmediato y suma 30 días desde el fin del período ya pagado, así
  que no se pierde ningún día. Es la única opción con la que vuelve la
  renovación automática. Mientras no reactive, conserva el acceso hasta el fin
  igual, porque cancelar ya no corta.
- **(b) Reactivar sólo cambia el estado a «activo», sin cobro y sin
  renovación.** Al vencer, la cuenta pasa a `past_due` y tiene que pagar. Hay
  que cambiar el texto: la pantalla diría «Próximo cobro» y no lo hay.
- **(c) Cancelar pausa la suscripción en Mercado Pago (`paused`) y reactivar
  la autoriza.** Va contra la letra («cancela la suscripción»). Además no sé
  sin red qué fecha de cobro queda después de una pausa.

**D7.4 Sin token en producción.** Sin `MP_ACCESS_TOKEN`, el checkout lleva a
una página demo con el botón «Simular Pago Exitoso». En cualquier entorno la
voy a cambiar para que no diga «activada» ni toque el navegador, porque eso no
se elige.
- **(a) Recomendada: en producción, sin token, el checkout responde 503
  «El cobro no está disponible»,** y el demo queda sólo fuera de producción.
  Un cliente real nunca debería ver un botón de simular pago.
- **(b) Sólo cambiar el texto,** y el demo sigue apareciendo también en
  producción.

### Lo que hago sin esperar (no tiene elección)

- **Cancelar** llama a Mercado Pago si hay `mp_preapproval_id`:
  - si Mercado Pago da error o no contesta, responde 502 o 503 con «No se
    pudo cancelar en Mercado Pago; tu plan sigue igual», y el estado no
    cambia;
  - si la suscripción ya estaba cancelada allá, se toma como hecho;
  - si hay suscripción pero falta el token, tampoco se cancela a medias;
  - sin suscripción en Mercado Pago, se cancela sólo en CDI.
- **`canceled` con fecha futura** conserva el acceso hasta esa fecha. Al
  pasarla queda `past_due`, sin los 7 días de gracia, porque ya no hay
  renovación que esperar.
- **Un pago sobre `canceled` con días** suma desde el fin.
- **Reactivar una prueba** la devuelve a `trial` con su misma fecha, nunca a
  `active`. Distingo la prueba sin agregar columnas ni migración:
  `payment_provider != "mercadopago"` quiere decir que nunca hubo un pago
  real, el mismo criterio que usa `_detalle_402`.
- **`/api/payments/success`** en modo demo o sin token no dice «activada» ni
  guarda `user_plan`.

### Riesgos que dejo afuera, salvo que digas otra cosa

- **Estudios.** Cancelar y reactivar actúan sobre el usuario, no sobre el
  estudio, y el checkout guarda la suscripción en el usuario que pagó (también
  si es la del estudio: `REPRODUCCION-ARGON-2026-10-24.md`, 6.3). Con el arreglo, si cancela el
  miembro que pagó, se cancela en Mercado Pago la suscripción del estudio,
  pero el estado del estudio en CDI no cambia: sigue con su fecha y su gracia.
  Definir quién puede cancelar en un estudio es una cuestión de permisos y
  queda fuera de esta pieza.
- **Una cuenta `active` creada a mano o con `simulate-charge`, sin pago de
  Mercado Pago.** Si se cancela y se reactiva, vuelve como `trial`. En
  producción sólo existen así los usuarios demo.
