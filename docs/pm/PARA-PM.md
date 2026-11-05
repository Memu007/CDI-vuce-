# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-MP-1 vuelta 3, entregada en `9048b6a` (informe en el commit de arriba)

**Resultado.** h, i, j y D13 (c) quedan hechos. Cada caso tuvo su rojo
antes del arreglo y tiene su sabotaje.

- **h:** un aviso que todavía no dice de qué cuenta es responde 503 y no
  se registra, así que el otro aviso del mismo pago lo acredita una sola
  vez, en los dos órdenes.
  - Antes de rendirse, la cuenta se busca en la suscripción
    (`metadata.preapproval_id`, `preapproval_id` o el id del cobro).
  - Un cobro con el pago `pending`, `in_process` o `authorized` también
    da 503.
- **j:** dentro de la gracia, la suscripción que acaba de renovar no se
  cancela. Si Mercado Pago contesta 404 por la vieja, «Activar plan» y
  «Cancelar plan» siguen adelante.
- **D13 (c):** una `authorized` vieja en una cuenta que no está vigente
  recibe 409 con el texto de salida y no se cancela.
- **i:** cada hueco tiene su prueba. El NUL anidado no era un defecto
  (abajo, con la evidencia).

Nada se integra en esta vuelta. Lo decidís vos: **D18**. **D17** es un
supuesto reversible.

## Decisiones

**D18. Un pago que dice su cuenta pero no su suscripción puede tapar la
renovación.** Lo encontró el adversario Sonnet alto y lo reproduje.

Cuando el aviso de pago trae `external_reference` pero no
`preapproval_id`, su monto se compara con el precio de hoy en PLANS:

- Si el precio cambió y el aviso de pago llega antes que el de cobro,
  queda `rechazado` (45000 contra 30000), ocupa el `payment_id` y el
  cobro lo encuentra «ya procesado». La cuenta queda `past_due`.
- Si el cobro llega primero, compara contra la suscripción y queda
  `aplicado` con 30000.

Pasa sólo si el aviso de pago real llega sin la suscripción, y eso
depende de la forma real de los avisos (D30). No lo arreglé: elegir entre
estas opciones cambia la regla del monto.

- **(a)** Dejarlo como riesgo hasta conocer D30.
- **(b)** Un pago sin suscripción cuyo monto no coincide con PLANS da 503
  en vez de `rechazado`, y el cobro decide. Contra: un pago ajeno de monto
  equivocado reintenta sin fin.
- **(c)** Que el cobro vuelva a evaluar un registro `rechazado` por monto
  cuando ese registro no tenía suscripción y la del cobro coincide.
  Requiere cambiar el registro de rechazado a aplicado, con su prueba en
  Postgres.

**Recomiendo (c).** Mantiene el rechazo de lo que de verdad no sirve y
deja que el aviso que sabe más corrija al que sabía menos. Es más código
que (b), así que lo haría en una vuelta propia y con su sabotaje.

**D17 (supuesto reversible).** Un cobro cuya suscripción no se puede leer
(`preapproval_id` ausente o ilegible) se procesa como su pago, con la
misma regla de cuenta y de monto. La prueba es
`vuelta2::test_un_cobro_sin_suscripcion_legible_se_acredita_como_su_pago`.
Si preferís que reintente, es un cambio de una línea y su prueba.

## SHAs

| Qué | SHA |
|---|---|
| Base: vuelta 2 y D14 | `4ef59f4` |
| Pruebas D13 (c), en rojo | `c5298cd` |
| Producto D13 (c): 409 sin cancelar | `f0b83d9` |
| Sabotajes D13 | `e2ec9fc`, `b5ab435`, `2fd9b7b` |
| Merge de tu rama | `53d968f` |
| Pruebas h y j, en rojo | `24dc074` |
| Producto h y j | `8eba7ca` |
| Sabotajes h y j | `9f12789` |
| Pruebas i | `054c8fa` |
| Sabotajes i | `f56f830` |
| Pausa en este canal | `88de6ce` |
| Merge de tu rama (§6) | `fa2732c` |
| Producto: comentarios de §6 y `_con_referencia_mp` | `94baa2e` |
| Anclas de los sabotajes al bloque movido | `c0235d0` |
| Producto: tres comentarios | `c11c1e6` |
| Pruebas: referencia vacía que no es texto, en rojo | `76a3a80` |
| Producto: `not external_ref` en lugar de `in (None, "")` | `0cc2dde` |
| Sabotajes de la referencia vacía y de los cortes en Postgres | `2d1b236` |
| Producto: docstring de `_con_referencia_mp` | `20ee063` |
| Pruebas: valores falsos por los dos avisos y su sabotaje | `e0d49f5` |
| Pruebas: el pago autorizado y su sabotaje | `f7c82ad` |
| Sabotajes: tres anclas viejas | `9048b6a` |

`0cc2dde` arregla una regresión mía de `8eba7ca`: con `0`, `False`, `[]` o
`{}` en `external_reference`, el pago no tomaba la referencia de la
suscripción.

## El NUL anidado no era un defecto

En i pediste arreglar `_guardable_en_pg` porque no limpiaba valores
anidados y un NUL en `payer.id` o en la tarjeta daba 500 en Postgres 16. La
función ya recorre los diccionarios y no cambió en esta vuelta
(`git log -S_guardable_en_pg 4ef59f4..HEAD -- proyecto_maria/main.py` sale
vacío). Lo que faltaba era la prueba, y la agregué a
`cobro_mp1_postgres.py`.

- Con el producto, `fallas: 0`:
  ```
  OK    | un pago con el pagador con NUL queda aplicado (200, [('aplicado',)])
  OK    | un pago con los últimos 4 con NUL queda aplicado (200, [('aplicado',)])
  OK    | un pago con la marca con NUL queda aplicado (200, [('aplicado',)])
  ```
- Con un mutante que limpia sólo el primer nivel, `fallas: 3`:
  ```
  FALLA | un pago con el pagador con NUL queda aplicado (500, [])
  FALLA | un pago con los últimos 4 con NUL queda aplicado (500, [])
  FALLA | un pago con la marca con NUL queda aplicado (500, [])
  ```

No sé con qué entrada lo reprodujo el adversario de la vuelta 2. Si fue
un NUL dentro de una lista, eso sí no se limpia, pero hoy ningún campo que
se guarda sale de una lista.

## Pruebas nuevas

**h** (`tests/test_cobro_mp1_h.py`)

| Prueba | Qué cubre |
|---|---|
| `test_los_dos_avisos_de_una_renovacion_la_acreditan_una_vez` | Los dos órdenes del par, con y sin `metadata.preapproval_id`, usuario y organización |
| `test_si_ningun_aviso_dice_de_quien_es_no_queda_rechazado` | 503 sin registro y `past_due` |
| `test_un_cobro_con_el_pago_pendiente_no_se_pierde` | Cobro con el pago `pending`, `in_process` o `authorized`, y después el pago aprobado |
| `test_un_pago_sin_cuenta_que_otro_aviso_ya_aplico_no_reintenta_mas` | 200 «payment_id ya procesado» |
| `test_sin_referencia_ni_en_el_pago_ni_en_la_suscripcion_reintenta` | `None`, `""`, `0` y `[]`, por los dos avisos |
| `test_una_referencia_vacia_de_otro_tipo_toma_la_de_la_suscripcion` | `0`, `False`, `[]` y `{}`, por los dos avisos |

**i** (`tests/test_cobro_mp1_i.py`)

| Hueco | Prueba |
|---|---|
| El bucle de `setattr`: operaciones e inicio del período | `test_pagar_el_plan_reinicia_la_cuota_del_periodo` |
| El bucle de `setattr`: `extra_ops_expires_at` | `test_una_recarga_vence_a_los_30_dias` |
| `trial` fuera de lo vigente | `test_pagar_durante_la_prueba_extiende_desde_el_fin` |
| El tope de recargas aplicado a planes | `test_el_tope_de_recargas_no_frena_un_plan` |
| El borde en 91 | `vuelta2::test_una_recarga_que_no_entra_queda_rechazada_y_no_suma[91-*]` |
| Monto `>= 0` | `test_una_suscripcion_de_monto_cero_no_se_aplica` y `test_un_link_con_precio_cero_se_compara_con_el_precio_de_hoy` |
| Moneda `None` | `test_un_pago_sin_moneda_no_se_aplica` |
| Fecha sin zona | `T1::test_un_pago_sin_fecha_de_aprobacion_legible_no_se_aplica[sin_zona]` |
| Los últimos 4 al revés y la marca | `test_se_guardan_los_ultimos_4_y_la_marca` |
| NUL anidado, y los cortes de moneda, fecha y motivo | `cobro_mp1_postgres.py` |

**j y D13** (`test_cobro_mp1_cde.py` y `test_cobro_mp1_vuelta2.py`)

- `test_sin_cuenta_vigente_una_autorizada_frena_el_checkout_y_sale_cancelando`
- `test_si_mp_no_conoce_la_suscripcion_vieja_el_checkout_crea_la_nueva`
- `test_si_mp_no_conoce_la_suscripcion_cancelar_sigue`
- `test_una_renovacion_de_una_suscripcion_con_referencia_que_no_sirve_queda_rechazada`
- `test_un_cobro_sin_suscripcion_legible_se_acredita_como_su_pago` (D17)
- `test_una_renovacion_sin_referencia_y_con_un_id_de_suscripcion_que_no_sirve_reintenta`

## Sabotajes nuevos en `cobro_mp1.sh`

- **h:**
  - sin cuenta queda rechazado (la regla de la vuelta 2), y un cobro sin
    suscripción queda rechazado;
  - una referencia vacía queda rechazada; una que no es texto no toma la
    de la suscripción, o queda rechazada;
  - la suscripción no se lee del pago;
  - un cobro con su pago pendiente, en proceso o autorizado no reintenta;
  - un pago sin cuenta que el otro aviso ya aplicó reintenta igual.
- **i:**
  - pagar no reinicia las operaciones ni el inicio del período;
  - la recarga no guarda su vencimiento;
  - la prueba vigente no cuenta como tiempo pagado;
  - el tope de recargas frena un plan;
  - una recarga que pasa a 101 entra;
  - un monto de cero cuenta como monto;
  - un pago sin moneda pasa;
  - se guardan los primeros 4 y no los últimos;
  - la marca no se guarda;
  - una fecha de aprobación sin zona pasa;
  - la moneda, la fecha y el motivo largos no entran en la fila (éstos
    tres sólo se ven en Postgres: dan 500 en vez de `rechazado`).
- **j y D13:**
  - un 404 de Mercado Pago deja el checkout en 503;
  - el checkout cancela la autorizada vieja;
  - sin cuenta vigente, el 409 dice que se renueva sola;
  - la cancelada no puede cancelar la autorizada que la frena.

Rojo de la última prueba con el arreglo revertido (la línea `sin_cuenta`
cambiada a `in (None, "")`): `4 failed, 20 passed`, con `[pago-cero]`,
`[pago-lista]`, `[cobro-cero]` y `[cobro-lista]`.

El estado `authorized` no tenía prueba; lo encontré releyendo el diff. Con
`"authorized"` sacado de la tupla de `main.py`: `4 failed, 8 passed`, con
`[authorized-pago_sin_nada-usuario]`, `[authorized-pago_sin_nada-organizacion]`,
`[authorized-pago_con_metadata-usuario]` y
`[authorized-pago_con_metadata-organizacion]`.

## Hallazgos de la autorrevisión

| Quién | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| Adversario sobre `c0235d0` | Sonnet, alto | 1. Media: un pago con cuenta y sin suscripción se compara con PLANS y puede tapar el cobro | Reproducido. **D18** |
| Adversario | Sonnet, alto | 2. Baja: con `0`, `False`, `[]` o `{}` en la referencia el pago no toma la de la suscripción | Regresión mía. Arreglado: rojo `76a3a80`, arreglo `0cc2dde` |
| Adversario | Sonnet, alto | 3. Baja: un 404 por demora de replicación en el doble clic crearía una tercera suscripción | No lo reproduje. Riesgo |
| `/code-review high` sobre `94baa2e..2d1b236` | Opus, alto | 1. `sin_cuenta = not external_ref` sin prueba que distinga valores falsos que no son texto | Arreglado en `e0d49f5`, con el sabotaje nuevo |
| `/code-review high` | Opus, alto | 2. El docstring de `_con_referencia_mp` decía de más | Corregido en `20ee063` |
| `/code-review high` | Opus, alto | 3. Un `metadata.preapproval_id` malformado rechaza aunque el cobro traiga uno válido | Riesgo: la precedencia de la metadata |
| `/code-review high` | Opus, alto | 4. Un pago sin suscripción con referencia `0`, `[]` o `{}` pasa de rechazado a 503 sin fin | Es la regla h, igual que con `None`. Va en el riesgo de pagos ajenos |
| `/code-review high` | Opus, alto | 5. Una referencia verdadera que no es texto (`123`, `['x']`) no toma la de la suscripción | Riesgo. Mercado Pago manda texto o null |
| `/code-review high` | Opus, alto | 6. La suscripción se lee dos veces | Riesgo conocido |
| `/code-review high` | Opus, alto | 7. La prueba nueva pasaba sólo por el aviso de pago | Sumé el aviso de cobro. Organización no: el camino de la referencia no depende del tipo de cuenta |
| `/security-review` sobre `f56f830..e0d49f5` | Sonnet, por defecto | «No findings». La revisión anterior, sobre `4ef59f4..f56f830`, también | — |
| Yo, releyendo el diff | — | `authorized` da 503 en el producto y no tenía prueba | Prueba y sabotaje en `f7c82ad` |
| Yo, corriendo `cobro_mp1.sh` sobre `f7c82ad` | — | Dos ROTO: las anclas de `_suscripcion_del_pago_mp` y de `sin_cuenta` quedaron viejas con `94baa2e` y `0cc2dde`. Un ROJO?: la suscripción ilegible ya no la distingue `test_si_no_se_puede_leer_la_suscripcion_de_una_renovacion_reintenta`, porque sin referencia también da 503 | Reanclados en `9048b6a`; el tercero espera `test_si_no_se_puede_leer_la_suscripcion_reintenta[excepcion-renovacion]` (la excepción da 500). Los tres, comprobados a mano |

El adversario no encontró nada en el refactor `94baa2e`, en h, en j, en
D13 (c), en la doble aplicación ni en las columnas. Ni él ni las revisiones
corrieron nada: leyeron el código, salvo el adversario, que reprodujo D18.

## Puertas, sobre `9048b6a`

| Puerta | Salida |
|---|---|
| Suite completa, en un worktree limpio | `4407 passed, 121 skipped, 3 xfailed in 548.98s (0:09:08)`, salida 0 |
| Pruebas de cobro (`test_cobro_mp1*.py`, `test_cobro_mp2`, `test_cobro_corte1`, `test_webhook_ipn`, `test_g7_cobro`) | `307 passed, 5 warnings in 135.91s (0:02:15)`, salida 0 |
| `cobro_mp1_postgres.py` en Postgres 16 | `fallas: 0`, salida 0, sobre `e0d49f5`: el producto y este guion no cambian en `f7c82ad` ni en `9048b6a` |
| `cobro_mp1.sh` | 135 ROJO y 1 «sin_rojo» en verde; `sabotajes con falla: 0`, salida 0 |
| `cobro_mp2.sh` | 23 ROJO; `sabotajes con falla: 0`, salida 0 |
| `/code-review high` | Sobre `94baa2e` y sobre `94baa2e..2d1b236`. `e0d49f5` responde a sus hallazgos 1 y 7. No lo volví a correr sobre `e0d49f5..9048b6a`: sólo pruebas y sabotajes |
| `/security-review` | «No findings» sobre `f56f830..e0d49f5`. `f7c82ad` y `9048b6a` no tocan producto |

No corrí `smoke_friccion.sh` ni `ataque_aislamiento.sh`: el cambio es sólo
el webhook y el checkout de Mercado Pago, que tienen sus pruebas en las
filas de arriba.

## chequeo-6

```
== base 53d968f
chequeo-6 53d968f..9048b6a: avisos para mirar, no un veredicto
producto +49/−24
  AVISO producto suma 25 líneas netas: el informe dice por qué (§6: más de 20)
arnés +473/−38
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11286 → 11311
avisos: 1
== base 4ef59f4
chequeo-6 4ef59f4..9048b6a: avisos para mirar, no un veredicto
producto +181/−73
  AVISO producto suma 108 líneas netas: el informe dice por qué (§6: más de 20)
arnés +1030/−80
historia (grep de §6, sin líneas movidas):
  AVISO historia en proyecto_maria/static/v2/app_v2.js:35: // el servidor exija CSRF (ORDEN-1b).
archivos de producto:
  proyecto_maria/main.py: 11281 → 11311
  proyecto_maria/static/v2/app_v2.js: 1140 → 1204
  AVISO creció una función de más de 150: proyecto_maria/static/v2/app_v2.js:7 <anónima> 1134 → 1198, 14 en su propio cuerpo (§6: lo nuevo va aparte)
  AVISO comentario nuevo de 4 líneas: proyecto_maria/static/v2/app_v2.js:32 (§6: una o dos)
  AVISO comentario nuevo de 3 líneas: proyecto_maria/static/v2/app_v2.js:843 (§6: una o dos)
  AVISO creció una función de más de 150: scripts/testing/pantalla_orden1.js:275 <anónima> 1044 → 1343, 174 en su propio cuerpo (§6: lo nuevo va aparte)
avisos: 6
```

Qué hago con cada AVISO:

- **Base `53d968f`, el producto suma 25 líneas netas.** Las necesitan:
  - h: `_suscripcion_del_pago_mp`, `_sin_cuenta_todavia_mp` y el 503 del
    cobro pendiente;
  - j: el 404;
  - D13 (c): el 409.

  `mercadopago_webhook` no crece: el bloque de la referencia se fue a
  `_con_referencia_mp`.
- **Base `4ef59f4`, el producto suma 108 líneas netas.** Además de lo de
  arriba, cuenta ORDEN-1b, que ya está en esta rama. Lo de COBRO-MP-1 en
  `main.py` es `+54/−24`.
- **Base `4ef59f4`, los avisos de `app_v2.js` y `pantalla_orden1.js`**
  (historia en la línea 35, la función de la línea 7, los comentarios de 4
  y 3 líneas, la función de `pantalla_orden1.js:275`): son de ORDEN-1b,
  escritos antes del 04/11, y van a la cola de limpieza. La historia de
  `app_v2.js:35` la saco en ORDEN-1b vuelta 2, que toca ese archivo.

Líneas que propongo para `COLA-LIMPIEZA.md`:

- `app_v2.js:7`: la función anónima del archivo (1198 líneas) se parte. Lo
  nuevo de ORDEN-1b, el freno y el diálogo, va a un módulo propio.
- `app_v2.js:32` y `:843`: los comentarios de ORDEN-1b se dejan en una o
  dos líneas.
- `pantalla_orden1.js:275`: el cuerpo de 1343 líneas se parte en un caso
  por archivo o por función.
- `main.py:10363` y `:10595`: los docstrings de `_guardable_en_pg` y del rechazo nombran «COBRO-MP-1,
  b». Son de antes del 04/11 y no los toqué.

## Riesgos

Ninguno de éstos lo arreglé en esta vuelta.

**De esta vuelta**

- **Pagos ajenos con 503.** Un pago sin cuenta y sin suscripción, de otro
  sistema con la misma cuenta de Mercado Pago, reintenta hasta que Mercado
  Pago deja de mandarlo. No se acredita nada.
- **Un cobro que queda pendiente** más allá de los reintentos de Mercado
  Pago no se acredita solo.
- **Un 404 con el token de otra cuenta** se toma como suscripción cancelada.
- **El 404 por demora** de replicación en un doble clic crearía una
  tercera suscripción (adversario, no reproducido).
- **D18**, que depende de D30.
- **Referencias que no son texto o que vienen vacías como texto:** `" "`,
  `"null"` o un valor verdadero que no es texto no toman la referencia de
  la suscripción.
- **Un `metadata.preapproval_id` inválido o malformado** gana sobre el
  id válido del cobro y lo deja rechazado o reintentando.
- **`last_payment_id` viejo** en la suscripción: el cobro puede mirar el
  pago anterior.
- **La metadata manda sobre la suscripción del cobro** al comparar el
  monto.
- **La suscripción se lee dos veces** en un mismo aviso.
- **Las llamadas a Mercado Pago son síncronas** y frenan el servidor. No las
  toqué, como pediste.
- **«Próximo cobro»** con una suscripción que nunca se autorizó.

**De la vuelta 1**

- Una recarga que revive extras vencidos.
- Cancelar mientras llega el primer pago.
- `_pago_un_plan_mp` con una prueba que sólo recargó.

D8 (a) y D10 (a) quedan como estaban.

## Archivos de producto

- `proyecto_maria/main.py`
- `CHANGELOG.md`

## Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout --detach origin/claude/dev-tecnica
# 1. Pruebas de cobro: «307 passed»
GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares \
  python -m pytest -q --no-cov -p no:cacheprovider tests/test_cobro_mp1*.py tests/test_cobro_mp2.py \
  tests/test_cobro_corte1.py tests/test_webhook_ipn.py tests/test_g7_cobro.py 2>&1 | grep -E "passed|failed"
# 2. Postgres 16: termina en «fallas: 0»
PY=python scripts/testing/con_pg16.sh bash -c '"$PY" scripts/testing/cobro_mp1_postgres.py "$BACKUP1A_PG_URL"' | tail -1
# 3. Sabotajes: sin ROTO, sin «ROJO?» y «sabotajes con falla: 0»
PY=python bash scripts/testing/sabotajes/cobro_mp1.sh 9048b6a | grep -E '^(ROTO|ROJO\?|VERDE)|con falla'
PY=python bash scripts/testing/sabotajes/cobro_mp2.sh 9048b6a | grep -E '^(ROTO|ROJO\?|VERDE)|con falla'
# 4. Los números de §6: los mismos AVISOS de la sección chequeo-6
python docs/pm/herramientas/chequeo-6.py 53d968f 9048b6a
```

/compact conservar: Dev 1, rama claude/dev-tecnica. COBRO-MP-1 vuelta 3
(h, i, j y D13 c) entregada en 9048b6a, en revisión de la PM, con D18 para
decidir y D17 como supuesto. Apenas entregué: ORDEN-1b vuelta 2 (una prueba
y su sabotaje por condición del freno, y la historia de app_v2.js:35).
Después CORTE-1, MP-2 (suma el segundo miembro y la cancelación de
organizaciones), AIS2, LIM, BACKUP-1a y EXCEL-2c. Nada se publica sin el
«dale» de Emi; nunca main.
