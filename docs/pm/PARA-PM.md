# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-MP-1 vuelta 4, entregada en `9161e0a` (informe en el commit de arriba)

**Resultado.** Toda cuenta con una suscripción de Mercado Pago abierta
puede cancelarla, sea cual sea su estado (`none`, `None`, `expired`, uno
desconocido), y el perfil le muestra «Cancelar plan». Cancelar no da acceso
a quien no lo tenía. En la vuelta apareció un segundo defecto, del mismo
origen: la confirmación prometía «el período ya pagado» siguiendo el nombre
del estado, y a la cuenta en gracia o con la prueba vencida le prometía
días que cancelar no da. Quedó arreglado: el perfil y `/billing/cancel`
deciden con la misma función, `cancelar_corta_acceso`.

Lo que decidís vos: **D51, D52, D53 y D54**. D17 y D18 quedan como las
decidiste: D17 aceptado; D18 en (a) hasta conocer D30.

## Decisiones

**D51. Organización contra usuario.** `/billing/cancel` cambia la fila del
usuario, pero el acceso de un miembro de organización lo da la organización
(`billing_entity`). `cancelar_corta_acceso(db_user)` mira al usuario. Para
un miembro, el aviso «corta / no corta» puede no coincidir con su acceso
real. Esto ya era así antes de la vuelta: la guarda y la respuesta de
cancel siempre miraron al usuario.

- **(a)** Pieza aparte: decidir qué cancela un miembro (la suscripción de
  la organización, la suya o ninguna) y probarlo con una organización.
- **(b)** Resolverlo en esta vuelta.

**Recomiendo (a).** Es una decisión de producto (quién puede cancelar lo
de la organización), no un arreglo, y no la abrió esta vuelta.

**D52. Cancelar desde `none`, `None`, `expired` o un estado desconocido deja
`canceled`.** Con la suscripción abierta, cancelar la cierra en Mercado
Pago y pasa la cuenta a `canceled` con `trial_ends_at` recortado a ahora,
así que no gana acceso.

- **(a)** Mantenerlo: un solo estado final para «canceló».
- **(b)** Cerrar la suscripción y dejar el estado que tenía.

**Recomiendo (a).** El acceso es el mismo (ninguno), y (b) suma una rama
por estado que nadie mira.

**D53. Una cuenta `active` en gracia (ya pasó `trial_ends_at`, todavía
con acceso) lo pierde al cancelar.** Ya era así antes de la vuelta:
`canceled` da acceso sólo hasta `trial_ends_at`. Lo nuevo es que la
confirmación ahora lo dice, en vez de prometer «el período ya pagado».

- **(a)** Mantenerlo: cancelar en gracia corta, y el aviso lo dice.
- **(b)** Darle la gracia también a la cancelada.

**Recomiendo (a).** La gracia existe para esperar un cobro; quien cancela
ya no va a pagar.

**D54. `app_v2.js:7` da AVISO de chequeo-6 desde `9048b6a`.** Es el IIFE,
el archivo entero (1198 → 1193). El cambio es de ORDEN-1b vuelta 2, no de
esta pieza; contra `54dabb7` no aparece.

- **(a)** A la cola de limpieza, junto con D50.
- **(b)** Partirlo ahora.

**Recomiendo (a).** El archivo baja 5 líneas, y partir el IIFE toca todas
las pantallas v2.

## SHAs (desde `54dabb7`)

| SHA | Qué |
|---|---|
| `f3ec5ec` | fix: toda cuenta con una suscripción abierta puede cancelarla |
| `448b8f0` | test: la salida de la suscripción abierta, en cada estado |
| `853f0d0` | refactor(test): la pantalla recorre los estados sin período pagado en una función aparte |
| `74bf816` | fix: la confirmación de cancelar dice lo que el servidor decide |
| `276f862` | test: la confirmación sigue a `cancelar_corta_acceso` |
| `2f9c98f` | refactor(test): los casos de la cancelada van en su propia función de la pantalla |
| `0bdeef6` | fix: `cancelar_corta_acceso` mira el acceso que queda después de cancelar |
| `ba21290` | test: la bandera se compara con el acceso que queda |
| `30eeca5` | refactor: cancelar compara el acceso de hoy con una sola hora |
| `ccf8310` | test: el caso trae como dato si cancelar corta el acceso |
| `faaf37f` | fix: cancelar decide con `cancelar_corta_acceso` y no promete servicio a quien corta |
| `80f03a0` | test: cancelar no devuelve `service_until` a la cuenta que queda sin acceso |
| `10f74c4` | test: el caso de D13 no repite su chequeo de acceso |
| `9e23484` | test: los sabotajes de la confirmación esperan el primer estado que la pantalla mira |
| `9161e0a` | merge de la rama de la PM (sólo `docs/pm/`) |

**producto +40/−33** contra `54dabb7` (+46/−44 contra `9048b6a`, que
incluye ORDEN-1b vuelta 2), en `main.py`, `billing_service.py` y
`profile.js`, más 6 líneas en `CHANGELOG.md`. El arnés suma +129/−42.

## Qué cambió

- La guarda de `/billing/cancel` da 409 sólo si el estado no es `trial`,
  `active` ni `past_due` **y** no hay suscripción abierta.
- `/billing/me` trae dos campos nuevos, booleanos:
  - `suscripcion_abierta`: hay `mp_preapproval_id`, en cualquier estado;
  - `cancelar_corta_acceso`: lo mismo que decide cancel.
- `billing_service.cancelar_corta_acceso(cuenta, ahora)`: cancelar corta a
  quien hoy no tiene acceso y a quien ya pasó `trial_ends_at`. Una sola
  `ahora` para las dos preguntas.
- Cancel, si corta, recorta `trial_ends_at` a ahora (si seguía vigente),
  devuelve `service_until: null` y el log dice «sin acceso».
- El perfil muestra «Cancelar plan» con `suscripcion_abierta` en cualquier
  estado. La confirmación sigue a `cancelar_corta_acceso`; «pago pendiente»
  queda para `past_due`.

## Rojo antes del arreglo

**En `9048b6a`, con el caso de `448b8f0`** (`rojo_v4b`): 4 failed, 4
passed, los cuatro de la causa.

```
FAILED tests/test_cobro_mp1_cde.py::test_sin_cuenta_vigente_una_autorizada_frena_el_checkout_y_sale_cancelando[sin_plan]
FAILED tests/test_cobro_mp1_cde.py::test_sin_cuenta_vigente_una_autorizada_frena_el_checkout_y_sale_cancelando[sin_estado]
FAILED tests/test_cobro_mp1_cde.py::test_sin_cuenta_vigente_una_autorizada_frena_el_checkout_y_sale_cancelando[expired]
FAILED tests/test_cobro_mp1_cde.py::test_sin_cuenta_vigente_una_autorizada_frena_el_checkout_y_sale_cancelando[desconocido]
E   assert 409 == 200
```

**En `9048b6a`, con el caso final de `10f74c4`**: 16 failed, 15 passed.
Fallan los 8 parámetros de `test_billing_me_dice_si_hay_una_suscripcion_abierta`
(«assert None is False», «assert False is True», «assert None is True») y
8 de `test_sin_cuenta_vigente_…`, con «el perfil promete otra cosa». Con
el campo nuevo, el caso falla en `/billing/me` antes de llegar al 409: por
eso el rojo propio de la causa es el de `448b8f0`.

**El helper revertido a `not tiene_acceso`** (`rojo_v4i`): 2 failed,
`renovacion_tardia` y `vencida_en_gracia`. Es el rojo del segundo defecto.

## Caso y sabotaje

Un caso por causa, con la familia como datos:

- `test_sin_cuenta_vigente_una_autorizada_frena_el_checkout_y_sale_cancelando`:
  parámetros `billing_status`, `dias`, `corta`. Cada fila: el checkout da
  409, cancel da 200, `service_until` coincide con `corta` y la cuenta no
  gana acceso.
- `test_billing_me_dice_si_hay_una_suscripcion_abierta`: parámetros
  `estado`, `con_suscripcion`, `abierta`, `corta`.
- `pantalla_cobro_mp1.js` recorre en el perfil los estados sin período
  pagado y la cancelada: el botón y el texto de la confirmación.

Sabotajes nuevos o reanclados en `cobro_mp1.sh`:

| Sabotaje | Dónde |
|---|---|
| C: sólo past_due pierde los días al cancelar | `main.py` |
| C: cancelar promete servicio hasta una fecha sin acceso | `main.py` |
| C: sólo la cancelada con suscripción puede cancelarla | `main.py` |
| C: /billing/me dice abierta sólo a la cancelada | `main.py` |
| C: /billing/me nunca dice que cancelar corta el acceso | `main.py` |
| C: /billing/me dice que corta sólo con past_due | `main.py` |
| C: cancelar_corta_acceso no ve la cuenta que ya pasó su fecha | `billing_service.py` |
| C: sólo una cancelada con suscripción abierta ve «Cancelar plan» | `profile.js` |
| C: la promesa vuelve a seguir el nombre del estado | `profile.js` |
| C: sólo past_due no promete el período ya pagado | `profile.js` |
| C: el pago pendiente se le dice a quien no está en past_due | `profile.js` |

**Corrida de `cobro_mp1.sh` sobre `9e23484`**: 5 BASE en verde (la base, la
carrera de D en Postgres, los pagos a la vez en Postgres, la pantalla del
perfil y la pantalla v1), 146 ROJO y 1 VERDE esperado («sin mirar antes de
insertar: sigue en verde, como tiene que ser»). Última línea: «sabotajes con
falla: 0», salida 0. Los tres de la confirmación:

```
ROJO  | C: la promesa vuelve a seguir el nombre del estado: dice «FALLA: canceled vencida con suscripción abierta: la confirmación promete el período ya pagado»
ROJO  | C: sólo past_due no promete el período ya pagado: dice «FALLA: canceled vencida con suscripción abierta: la confirmación promete el período ya pagado»
ROJO  | C: el pago pendiente se le dice a quien no está en past_due: dice «FALLA: canceled vencida con suscripción abierta: la confirmación habla de un pago pendiente»
```

Sobre `10f74c4` la misma corrida dio «sabotajes con falla: 2» (144 ROJO, 2
ROJO?): esos dos esperaban la falla de `none`, pero la pantalla mira antes
la cancelada vencida y corta ahí. Daban rojo por la causa correcta con otro
texto. `9e23484` corrige el texto esperado. Queda que dos sabotajes distintos
esperan la misma línea: la primera aserción que los dos rompen.

## Puertas

| Puerta | Sobre | Resultado |
|---|---|---|
| Suite completa | `9161e0a` | «4415 passed, 121 skipped, 3 xfailed in 641.82s (0:10:41)», salida 0 |
| Suite completa | `10f74c4` | «4415 passed, 121 skipped, 3 xfailed in 634.26s (0:10:34)», salida 0 |
| `cobro_mp1.sh` | `9e23484` | 146 ROJO, «sabotajes con falla: 0», salida 0 |
| `cobro_mp2.sh` | `10f74c4` | 23 ROJO, «sabotajes con falla: 0», salida 0. De `10f74c4` a `9161e0a` sólo cambian `cobro_mp1.sh` y `docs/pm/`: no lo volví a correr. |
| `compileall -q proyecto_maria` | `9161e0a` | salida 0 |
| `smoke_friccion.sh` | `9161e0a` | «OK · telemetría + alias session/state + by-cuit protegido», salida 0 |
| `ataque_aislamiento.sh` | | No corrido: la pieza no toca clientes ni descargas, que es lo que cubre. |
| chequeo-6 | `9e23484` | Abajo, entero; `9161e0a` sólo suma `docs/pm/`. |

`9161e0a` es el merge de la rama de la PM (`ae546a7`): trae sólo `docs/pm/`.

## Revisiones

| Quién | Modelo y esfuerzo | Sobre | Resultado |
|---|---|---|---|
| `adversario-sonnet-alto` | Sonnet, alto | `54dabb7..853f0d0` | Corrió a las 04:17 (18 herramientas, 243 s). Su texto llegó por handback y no lo recuperé entero; lo que señaló coincide con lo arreglado después (la confirmación siguiendo el nombre del estado). |
| `/code-review high` 1 | | `54dabb7..853f0d0` | 3 hallazgos: `profile.js:419` trataba toda cancelada como período pagado (arreglado en `74bf816`…`ba21290`); `main.py:2133` none/expired pasan a canceled (D52); `main.py:2150` organización contra usuario (D51). |
| `/code-review high` 2 | | hasta `ba21290` | Hallazgos arreglados en la vuelta; no conservo el detalle. |
| `/code-review high` 3 | | hasta `ba21290` | Regla duplicada entre `/billing/me` y cancel, docstring viejo, dos relojes: arreglado en `30eeca5`, `faaf37f`, `80f03a0`. |
| `/code-review high` 4 | | hasta `80f03a0` | Sin bugs de producto. El ancla del sabotaje de past_due esperaba un texto al que el caso ya no llega, y una aserción muerta: arreglados en `10f74c4`. El resto, abajo en riesgos. |
| `/security-review` | Sonnet, alto | `54dabb7..10f74c4` | «No high-confidence vulnerabilities». Miró: ganar acceso al cancelar (lo impide el recorte), fechas nulas o sin zona, carreras (`with_for_update`), IDOR, XSS (textos constantes, sin `innerHTML`) y exposición (booleanos, sin el id de la suscripción). |

`80f03a0..9e23484` es sólo de pruebas: no corrí un quinto code-review, y el `/security-review` no se volvió a correr después de `10f74c4`.

## chequeo-6

Contra `54dabb7`:

```
chequeo-6 54dabb7..9e23484: avisos para mirar, no un veredicto
producto +40/−33
arnés +129/−42
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11311 → 11306
  proyecto_maria/services/billing_service.py: 402 → 412
  proyecto_maria/static/v2/screens/profile.js: 585 → 587
avisos: 0
salida 0
```

Contra `9048b6a`:

```
chequeo-6 9048b6a..9e23484: avisos para mirar, no un veredicto
producto +46/−44
arnés +362/−52
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11311 → 11306
  proyecto_maria/services/billing_service.py: 402 → 412
  proyecto_maria/static/v2/app_v2.js: 1204 → 1199
  AVISO creció una función de más de 150: proyecto_maria/static/v2/app_v2.js:7 <anónima> 1198 → 1193, 1 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/profile.js: 585 → 587
  AVISO creció una función de más de 150: scripts/testing/pantalla_orden1.js:280 <anónima> 1343 → 1520, 103 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 2
salida 0
```

- `app_v2.js:7`: D54.
- `pantalla_orden1.js:280`: D50, ya decidido en (a).

Los dos vienen de ORDEN-1b vuelta 2; esta pieza no toca esos archivos.

## Riesgos

- **Organización**: D51.
- **Pago tardío**: esta vuelta no toca qué pasa si Mercado Pago avisa un
  cobro después de cancelar; no lo volví a probar.
- **503**: si Mercado Pago no cancela, no cambia nada en CDI, como antes.
- **`dataset` viejo**: la confirmación lee `dataset.corta` de la última
  carga de `/billing/me`. Si la fecha pasa con el perfil abierto, el texto
  puede prometer días; el servidor igual corta bien.
- **Filas redundantes**: `renovacion_tardia` (active, −1) y
  `vencida_en_gracia` (active, −3) cubren la misma causa. Quedan como datos.
- **Sin fila de `trial`** en la familia de D13: la prueba vigente la cubren
  los casos de cancelar desde trial de `test_billing_autoservicio.py`.
- **Commits intermedios**: entre `faaf37f` y `80f03a0` un sabotaje queda con
  el ancla vieja, y hasta `10f74c4` otros dos esperan el texto de `none`.
  En `9e23484` están bien.
- **`service_until` sin zona**: se devuelve como está en la base. Viene de
  antes.
- **`ahora=None`** se normaliza sólo dentro del helper; `vigente` llamado
  aparte usa su propio reloj. En cancel se le pasa la misma `ahora`.
- `corta and vigente(...)` calcula `vigente` aunque ya se sepa; lo dejé
  por claridad.

## Comandos para reproducir

```bash
git fetch origin claude/dev-tecnica && git checkout 9161e0a
# 1. El caso: 31 passed
python -m pytest -q --no-cov tests/test_cobro_mp1_cde.py | tail -1
# 2. Sabotajes de la pieza: «sabotajes con falla: 0»
PY=python bash scripts/testing/sabotajes/cobro_mp1.sh 9e23484 | tail -1
# 3. Números de §6: 0 avisos contra 54dabb7
python docs/pm/herramientas/chequeo-6.py 54dabb7 9e23484
# 4. Historia: vacío
git diff 54dabb7 9e23484 -- proyecto_maria/ | grep '^+' | grep -E '[A-Z]{4,}(-[A-Z]{2,})*-[0-9]|caso [0-9]'
```

## Archivos de producto tocados

`proyecto_maria/main.py`, `proyecto_maria/services/billing_service.py`,
`proyecto_maria/static/v2/screens/profile.js` y `CHANGELOG.md`.

/compact conservar: Dev 1, rama claude/dev-tecnica. COBRO-MP-1 vuelta 4
entregada en 9161e0a y en revisión de la PM, con D51-D54 para decidir.
Apenas entregué: ORDEN-1b vuelta 3 (caso y sabotaje: la cookie leída
después de la respuesta en loadCurrentUser, reteniendo con route.fetch()).
Nada se publica sin el «dale» de Emi; nunca main.
