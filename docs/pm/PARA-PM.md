# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ORDEN-1b vuelta 3, entregada en `f22f48b` (informe en el commit de arriba)

**Resultado.** El arnés ahora fija que `loadCurrentUser` lee la cookie de
sesión antes de pedir `/auth/current_user`. Caso nuevo `z35`: la relectura de
la vuelta del pago (`success` y `topup_success`, como datos del mismo caso)
sale con la cookie de A y se retiene con `route.fetch()`; entra B, se suelta
la respuesta (que el caso comprueba que es de A) y la pestaña intenta guardar
un cliente. Sin sabotaje: no queda en ninguna cuenta y la pestaña avisa
que entró otro. Con la lectura movida abajo del `try/finally`, el sabotaje
da ROJO en las dos vueltas del pago, cada una medida sola. Producto: nada (`producto +0/−0`).

**Lo que decidís vos: D55.** Las D51 a D54 de COBRO-MP-1 vuelta 4 siguen
abiertas, abajo.

### Decisiones

**D55. Los reintentos de la primera carga no van en `z35`.** Pediste
sumarlos como datos «si los cubrís». No los sumé porque no distinguen este
defecto: en la primera carga la pestaña todavía no tiene dueño, y el freno que
ataja una cookie nueva ahí es `getCsrfToken() !== sesionAlAbrir`, no
`sesionAntes` (app_v2.js:395 compara las dos contra `sesionAlAbrir`). Por
el código, con la lectura movida abajo esas filas siguen verdes; no lo corrí.
Ese otro freno ya lo cubren `k` y `z8` de `orden1.sh`.

- **(a)** Así: `z35` sólo con las dos vueltas del pago.
- **(b)** Sumar las filas igual, sabiendo que no ponen rojo con este
  sabotaje.

**Recomiendo (a).** Una fila que no distingue el defecto no prueba nada y
suma una espera más al arnés.

### SHAs (desde `ffed989`)

| SHA | Qué |
|---|---|
| `6e87684` | test: caso `z35` y su sabotaje en `orden1b.sh` |
| `374348b` | test: `z34` y `z35` como funciones propias (`vueltaConOtroAdentro`, `respuestaDeAConOtroAdentro`, con `vueltaDelPago` común), fuera de la anónima |
| `f22f48b` | test: `z35` comprueba que la respuesta retenida es de A; `VUELTA=<billing>` deja una sola fila y el sabotaje mide cada vuelta del pago |
| (este) | docs: informe |

Archivos: `scripts/testing/pantalla_orden1.js` y
`scripts/testing/sabotajes/orden1b.sh`. Nada de producto.

### Cómo retiene la respuesta

- La primera relectura con la pestaña ya cargada se retiene; la carga y las
  relecturas que vienen después pasan.
- `route.fetch()` sale enseguida con las cookies de ese momento, las de A.
  `route.continue()` pondría las del momento en que se suelta, las de B: el
  adversario lo probó y con `continue()` el sabotaje da verde.
- Si la respuesta retenida no es de A, el caso falla con «la relectura
  retenida no es de A». Ese rojo lo vi en el primer intento: una segunda
  relectura, posterior a la entrada de B, también pasaba por el handler y
  contestaba B. Por eso sólo se retiene la primera.

### Puertas

| Puerta | Sobre | Resultado |
|---|---|---|
| `orden1b.sh` | `f22f48b` | base verde; 26 ROJO, entre ellos «la sesión de la respuesta se lee cuando ya llegó (success)» y «(topup_success)», los dos con «…y el cliente quedó en la cuenta de B»; «sabotajes sin rojo: 0», salida 0 |
| `orden1.sh` | `f22f48b` | base verde (el arnés entero, sin `CASOS`); 76 ROJO; «sabotajes sin rojo: 0», salida 0 |
| Suite completa | `374348b` | `4415 passed, 121 skipped, 3 xfailed in 650.56s`, salida 0 |
| `compileall -q proyecto_maria` | `f22f48b` | 0 |
| chequeo-6 `ffed989..f22f48b` | `f22f48b` | 1 aviso, abajo |
| Historia (grep de §6) | `f22f48b` | vacío |

La suite corrió sobre `374348b` y vale para `f22f48b`: entre los dos sólo
cambian los dos archivos del arnés, y ninguna prueba de `tests/` ni la CI los
usa (`grep -rn 'pantalla_orden1\|orden1b.sh' tests/ .github/` da vacío).

### chequeo-6

```
chequeo-6 ffed989..f22f48b: avisos para mirar, no un veredicto
producto +0/−0
arnés +58/−14
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  AVISO creció una función de más de 150: scripts/testing/pantalla_orden1.js:281 <anónima> 1520 → 1552, 19 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 1
```

**El AVISO queda, y no es crecimiento propio.** Medido con `medir_js` y
`padres` del mismo chequeo, las líneas de la anónima que no están en ninguna
función anidada pasan de **1040** (`ffed989`) a **1034** (`f22f48b`): bajan 6.
El chequeo compara las funciones anidadas por nombre y orden; `vueltaDelPago`
es nueva pero está armada con líneas que ya estaban en `z34`, así que el
chequeo no la cuenta como agregada y le carga su largo a la anónima. Partir
la anónima ya está en la cola (D50).

### Revisiones

| Quién | Modelo y esfuerzo | Sobre | Hallazgo | Qué hice |
|---|---|---|---|---|
| `/code-review high` | esta sesión, alto | `374348b` | El sabotaje sólo veía la fila `success` (z35 corta en la primera que falla) | `VUELTA` en el arnés y un sabotaje por vuelta (`f22f48b`) |
| `/code-review high` | | | `ruta.fetch()` sin `catch`: una falla de red terminaba en el tope de 15 s, con un mensaje que no la nombra | El `catch` llama a `falla` |
| `/code-review high` | | | `z35` no comprobaba su premisa: si la retenida contestara B, mediría lo mismo que `z34` | Aserción de que el `username` es el de A |
| `/code-review high` | | | El AVISO de chequeo-6 | Explicado arriba |
| `/code-review high` | | | `vueltaDelPago` se parece a `retenerRespuestas` y `retenerUsuario` | Queda: retienen otra cosa (respuestas de escritura, el usuario sin soltar) con otro contrato |
| `/code-review high` | | | El booleano `conCookieDeA` | Queda: estilo |
| `/code-review high` | | | La premisa de `z34` no se comprueba | Queda: su propio sabotaje daría verde si `continue()` no pusiera la cookie de B |
| `adversario-sonnet-alto` | Sonnet, alto | `374348b` | Sin defectos que bloqueen. `z35` verde sin sabotaje y rojo en 6 de 6 corridas con el texto esperado; con `continue()` el sabotaje da verde; `fulfill` no pisa cookies. Menores: sólo `success` (arreglado), `fetch` sin `catch` (arreglado), 429 del login si se corre muchas veces contra la misma API (entorno) | Lo que bloqueaba, en `f22f48b` |
| Seguridad | subagente Sonnet, con las instrucciones de `/security-review` | `ffed989..f22f48b` | «Sin hallazgos»: sólo archivos de prueba, ni producto, ni variables que lea el producto, ni secretos | — |

La revisión de seguridad no fue el skill completo con su filtro de falsos
positivos en paralelo: fue un subagente con sus instrucciones, porque el diff
no tiene producto.

### Riesgos

- **Bajo.** `z35` depende de que la vuelta del pago relea el usuario (a los
  4000 y 2000 ms, `handleBillingReturn`). El caso espera esa relectura, no
  un tiempo fijo: si la espera cambia sigue midiendo, y si la relectura
  desaparece falla con «la pestaña no vuelve a leer el usuario en 15 s».
- **Bajo, de entorno.** Corrido muchas veces contra la misma API, el login
  da 429. Los scripts de sabotaje levantan una API nueva por corrida.
- Lo que no tocás vos ni yo: las lecturas GET siguen sin pasar por el freno
  (lo anotaste fuera de la pieza).

### Comandos para reproducir

```bash
# 1. Sabotajes de la pieza: ROJO en «(success)» y «(topup_success)», y «sabotajes sin rojo: 0»
PY=venv/bin/python PUERTO=8875 scripts/testing/sabotajes/orden1b.sh f22f48b
# 2. El arnés entero en verde (la base del script) y «sabotajes sin rojo: 0»
PY=venv/bin/python PUERTO=8853 scripts/testing/sabotajes/orden1.sh f22f48b
# 3. Números de §6: 1 aviso, el de arriba
python docs/pm/herramientas/chequeo-6.py ffed989 f22f48b
```

### Archivos de producto tocados

Ninguno.

---

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

/compact conservar: Dev 1, rama claude/dev-tecnica. ORDEN-1b vuelta 3
entregada en f22f48b (informe en el commit de arriba), con D55 para decidir.
COBRO-MP-1 vuelta 4 en 9161e0a sigue en revisión, con D51-D54. Lo que sigue
en la cola (CSRF-1) no está activado: espero el veredicto. Nada se publica sin el
«dale» de Emi; nunca main.
