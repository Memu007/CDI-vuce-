# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-MP-2, entregada en `4f1822f` (informe en el commit de arriba)

### Decisiones

**D62. Una suscripción pausada de otro miembro, en el checkout de un miembro.** Hoy el checkout la cancela antes de crear la nueva, igual que una pendiente.

- (a) Frenar con 409, como con una autorizada.
- (b) Dejarlo como está.

Recomiendo **(b)**: una pausada no cobra, y la nueva la reemplaza. Con (a), un estudio con una pausada abandonada queda sin poder pagar hasta que quien la abrió la cancele. Si elegís (b), propongo además unificar en una sola lista los estados que el checkout y cancelar tratan como «paga» (hoy están escritos en dos lugares); va a la cola de limpieza, no a esta pieza.

### Resultado

Lo que pediste está cerrado: C2, C4, C8/D9 y D7.1 a D7.4, también en un estudio (cancelar, reactivar y la segunda suscripción).

- **Cancelar** cancela primero en Mercado Pago (`PUT /preapproval/{id}` con `{"status":"cancelled"}`) y después en CDI. La cuenta sigue hasta el fin del período. Si Mercado Pago no cancela, o no hay token, no se toca nada en CDI y se contesta 503.
- **Una sola suscripción.** El 409 vale sólo con la cuenta vigente. Si la cuenta está vencida o en `past_due` y hay una vieja, se cancela antes de crear la nueva; si no se puede, 503 y no se crea nada. En un estudio se miran las de todos los miembros antes de cancelar ninguna, y una autorizada de otro frena con 409 y dice de quién es.
- **Un pago no hace perder días:** suma 30 días desde el fin del período (o de la prueba) si todavía no venció, y desde hoy si venció. Vale también en modo preference.
- **Reactivar** lo pagado lleva al checkout, y la pantalla dice que cobra ahora y que suma 30 días desde el fin. Reactivar una prueba no la activa. Sin token, nunca dice «activada» ni cambia la cuenta.
- **Sin token, fuera de desarrollo o pruebas:** 503 y sin demo. El criterio es `_demo_permitida()`.
- **«Próximo cobro»** sale sólo si hay una suscripción de Mercado Pago que se renueva.

### SHAs

| SHA | qué |
|---|---|
| `7200b82`, `b35d66a`, `b68979a` | pruebas, antes del producto: C2, C4, C8/D9, D7.1 y D7.3 |
| `a5d4aa7` | producto: cancelar en Mercado Pago, una sola suscripción, sumar desde el fin, demo sólo en desarrollo; CHANGELOG |
| `a4ad212`, `512a028`, `dda9f5b` | sabotajes de `a5d4aa7` y D7.1 en `test_g7_cobro` |
| `836da59`, `2fd9b7b` | cinco sabotajes de `cobro_mp1.sh` siguen al código nuevo |
| `3d0c8e7` | producto: un miembro del estudio no abre una segunda suscripción; CHANGELOG |
| `3ee1521`, `9213536` | pruebas de `3d0c8e7`, en pytest y en Postgres (el deadlock) |
| `d528a67` | producto: los comentarios dejan de nombrar la pieza (historia de §6) |
| `767e139` | producto: cancelar y reactivar en un estudio; CHANGELOG |
| `f6865b7` | pruebas de `767e139`: cancelar, reactivar y sacar miembros |
| `7ffb1a6`, `7c065ab` | si una de varias no se cancela, las canceladas dejan de figurar (producto, pruebas) |
| `381d0eb`, `8cbfbd6`, `f023b4f` | el checkout lee todas antes de cancelar ninguna (prueba del cruce, producto y CHANGELOG, pruebas) |
| `efb7253`, `b183c34` | no se cancela ni se saca a quien no corresponde (producto y CHANGELOG, pruebas) |
| `e2e8963`, `e12e535` | al cancelar, la que cobra va última (producto, pruebas) |
| `11708b0`, `2a878cd` | se relee cada una justo antes de cancelarla (producto, pruebas) |
| `5a3c766`, `4f1822f` | el 403 nombra la que paga; un estado no textual de Mercado Pago da 503 (producto, pruebas) |

Tus commits intercalados son `a3efc3a`, `192774f`, `4e7896d`, `6a07e7d` y `1bdb7a0`.

**Producto de la pieza: `+415/−195`, 220 netas** (suma de los diez commits de producto). Por qué suma más de 20: la pieza agrega tres cosas que no existían, cancelar en Mercado Pago con su manejo de error (`_pedir_suscripcion_mp`, `_cancelar_suscripcion_mp`), el control de una sola suscripción por cuenta que paga, contando a los miembros del estudio (`_estado_suscripcion_vieja` y el bloque del checkout), y la regla de sumar desde el fin (`_extender_periodo`). Lo que se sacó fue la demo sin condición y los dos caminos de reactivar.

Última vuelta (`8a1dcdd..4f1822f`): producto `+29/−11`.

### Cómo se cumple cada punto

Casos en `tests/test_cobro_mp2.py` salvo que diga otro archivo; sabotajes en `scripts/testing/sabotajes/cobro_mp2.sh`.

| punto | qué hace el producto | caso | sabotaje |
|---|---|---|---|
| C2: cancela en MP y sigue hasta el fin | `cancel_billing` llama a `_cancelar_suscripcion_mp` antes de escribir; `billing_service` deja generar hasta `period_end` | `test_cancelar_cancela_la_suscripcion_en_mp_y_sigue_hasta_el_fin`; `test_cobro_corte1.py::test_la_cancelada_genera_hasta_el_fin_del_periodo` | «cancelar no llama a Mercado Pago», «la cancelada no sigue hasta el fin del período» |
| C2: si MP falla, nada a medias | 503 sin escribir; si el PUT falla se pregunta el estado, y una ya cancelada en MP sigue | `test_si_mp_no_cancela_no_se_cancela_a_medias` (con `[contesta_sin_cancelar]`), `test_si_mp_ya_la_tenia_cancelada_cancelar_sigue`, `test_sin_token_no_cancela_una_suscripcion_a_medias`, `test_cancelar_sin_suscripcion_no_llama_a_mp` | «si Mercado Pago falla, se cancela igual en CDI», «sin token, se cancela igual en CDI», «si el PUT falla no se pregunta el estado», «si el PUT contesta sin cancelar, se da por cancelada», «cancelar sin suscripción llama a Mercado Pago» |
| C8/D9 y D7.3: reactivar | lo pagado va al checkout; una prueba no se activa; el texto dice que cobra ahora y suma 30 días desde el fin | `test_cancelar_y_reactivar_una_prueba_no_la_activa`, `test_reactivar_lo_pagado_lleva_al_checkout_y_dice_que_cobra_ahora` | «reactivar una prueba la deja activa», «reactivar lo pagado no pasa por el checkout» |
| C4 y D7.2: el 409 sólo vigente | `billing_checkout` frena si la cuenta está vigente y hay una abierta, también en modo preference | `test_el_segundo_checkout_con_una_vigente_se_frena`, `test_modo_preference_con_suscripcion_vigente_tambien_se_frena` | «sin el 409 con una suscripción vigente» |
| D7.2: sin vigencia, la vieja se cancela antes | `_estado_suscripcion_vieja` lee el estado; pendiente o pausada se cancela; ya cancelada no se vuelve a cancelar; si falla o no se sabe, 503 sin crear | `test_sin_cuenta_vigente_la_vieja_se_cancela_antes_de_crear` (`[pending]`, `[ya_cancelada]`), `test_si_no_se_puede_cancelar_la_vieja_no_se_crea_nada`, `test_si_no_se_sabe_como_esta_la_suscripcion_no_se_crea_otra` (`[estado_desconocido]`, `[estado_lista]`) | «la vieja no se cancela antes de crear la nueva», «la vieja ya cancelada se vuelve a cancelar», «si no se puede cancelar la vieja, se crea igual», «si no se sabe cómo está la vieja, se crea igual», «un estado desconocido de Mercado Pago se acepta», «un estado que no es texto rompe con un 500» |
| D7.1: el pago suma desde el fin | `_extender_periodo` suma 30 días desde `period_end` si no venció | `test_un_pago_suma_desde_el_fin_del_periodo` | «el pago suma desde el fin sólo si está activa» |
| D7.4: sin token no hay demo | `_demo_permitida()` en checkout, en la página de la demo y al confirmarla | `test_sin_token_fuera_de_desarrollo_no_hay_demo` (`[sin_variable]`), `test_la_demo_no_dice_activada_ni_cambia_la_cuenta`, `test_la_pagina_de_exito_sin_token_no_dice_activada` | «el checkout sin token da demo fuera de pruebas», «sin la variable de entorno hay demo», «la página de la demo abre fuera de pruebas», «confirmar la demo funciona fuera de pruebas», «la vuelta del pago dice «activada»», «la vuelta de la demo dice «activada»» |
| «Próximo cobro» | `renueva` en `billing_me` | `test_billing_me_dice_si_hay_proximo_cobro` | «renueva sin suscripción», «renueva con un checkout sin pagar» |
| Estudio: segunda suscripción | el checkout lee las de todos los miembros antes de cancelar ninguna; una autorizada de otro da 409 con su nombre; una que se autoriza mientras se cancelan las otras no se cancela | `test_otro_miembro_no_abre_una_segunda_suscripcion_de_la_org` (4), `test_con_una_autorizada_de_otro_no_se_cancela_ninguna`, `test_la_que_se_autoriza_mientras_se_cancelan_las_otras_no_se_cancela` (`[PUT]`, `[GET]`), `test_si_una_no_se_cancela_la_ya_cancelada_en_mp_no_queda_anotada` | «el checkout no mira las suscripciones de los otros miembros», «se cancela una pendiente antes de ver la autorizada de otro», «en el checkout, si una no se cancela, las canceladas siguen anotadas», «en el checkout, la ya cancelada en Mercado Pago sigue anotada si otra falla», «no se vuelve a mirar la siguiente después de cancelar una», «la primera se cancela sin volver a mirarla después de leer las otras», «el 409 de la autorizada de otro miembro no dice de quién es», «la suscripción de un miembro no le cobra a la org»; en Postgres, «dos miembros pagan a la vez sin bloquear la organización» y «el checkout bloquea la organización antes que a los miembros» |
| Estudio: cancelar | cambia la org, no al usuario; sólo la dueña o quien abrió la que paga (autorizada o pausada); la que cobra se cancela última; si una falla, las canceladas dejan de figurar | `test_en_una_org_cancelar_cancela_la_suscripcion_y_sigue_hasta_el_fin` (con `[abrio-paused]`), `test_en_una_org_un_miembro_que_no_la_abrio_no_la_cancela`, `test_un_miembro_cuya_suscripcion_no_paga_no_cancela_el_plan_del_estudio` (`[pending-403]`, `[cancelled-403]`, y la lectura que falla da 503), `test_al_cancelar_la_que_paga_se_cancela_ultima` (3), `test_si_una_de_varias_no_se_cancela_la_cancelada_no_queda_anotada` | «en una org, cancelar cambia al usuario y no a la org», «en una org, cualquier miembro cancela el plan», «en una org, un miembro con una pendiente propia cancela el plan», «en una org, quien abrió una suscripción pausada no la cancela», «al cancelar, la que paga no va última», «en una org, si no se lee la del miembro, cancela igual», «si una de varias no se cancela, las canceladas siguen anotadas» |
| Estudio: reactivar y miembros | reactivar mira la org; los pagos se buscan por la org; no se saca del estudio a quien abrió una suscripción | `test_en_una_org_reactivar_lo_pagado_lleva_al_checkout` (con `[topup-trial]`), `test_no_se_saca_del_estudio_a_quien_abrio_la_suscripcion` | «en una org, reactivar mira al usuario y no a la org», «en una org, los pagos se buscan con el nombre del usuario», «se saca del estudio a quien abrió la suscripción» |

### Puertas

| Puerta | SHA | Salida |
|---|---|---|
| suite completa, desde un worktree limpio | `4f1822f` | `4528 passed, 101 skipped, 3 xfailed, 102 warnings in 608.15s (0:10:08)`, salida 0 |
| `compileall -q proyecto_maria` | `4f1822f` | salida 0 |
| sabotajes `cobro_mp2.sh`, con Postgres | `4f1822f` | 45 ROJO, 0 `ROJO?`, 0 VERDE, 0 ROTO; las dos bases en verde (pytest y los cruces en Postgres); `sabotajes con falla: 0`, `salida 0` |
| pruebas de cobro (`test_cobro_mp1*.py`, `test_cobro_mp2.py`, `test_cobro_corte1.py`) | `4f1822f` | `374 passed, 3 warnings in 165.66s (0:02:45)` |
| `/code-review high` | `7200b82^..b183c34` | abajo |
| `/security-review` | `8a1dcdd..4f1822f` | sin hallazgos de confianza 8 o más |
| chequeo-6 | `6f79edf..4f1822f` y por commit | abajo |

`smoke_friccion.sh` y `ataque_aislamiento.sh`: no corridos. La pieza no cambia quién ve qué datos: los permisos que toca (quién cancela el plan de un estudio) tienen sus propios casos y sabotajes arriba, y `ataque_aislamiento.sh` cubre clientes y descargas, que la pieza no toca.

### Rojo antes

Cada rojo sale de correr las pruebas del tramo contra el producto de antes. Sólo en el primer tramo las pruebas están commiteadas antes del producto. En la segunda suscripción (`3ee1521` después de `3d0c8e7`), en el estudio (`f6865b7` después de `767e139`) y en los tramos siguientes, el commit de pruebas va después del de producto. Los rojos, copiados de la salida:

| tramo | producto de antes | rojo |
|---|---|---|
| primer tramo (`tests/test_cobro_mp2.py` en `b68979a`) | `b68979a` | `32 failed, 2 passed, 5 warnings in 11.06s`: todos menos `test_cancelar_sin_suscripcion_no_llama_a_mp` y `[ya_cancelada]`; los motivos son `assert 200 == 503`, `assert 200 == 409`, el checkout que crea «nueva-1», `'activada'` en la página y la suma de `timedelta(days=30)` |
| segunda suscripción de otro miembro | `main.py` de `3d0c8e7^`, con las pruebas de `3ee1521` | `4 failed, 31 passed, 5 warnings in 12.71s`: `test_otro_miembro_no_abre_una_segunda_suscripcion_de_la_org` en `[autorizada_vigente]`, `[autorizada_vencida]`, `[pending]` y `[pausada]` |
| cancelar y reactivar en un estudio | `d528a67` | `5 failed, 36 passed in 19.01s`: cancelar en `[duena]` y `[abrio]`, el 403 de un miembro que no la abrió, reactivar y no sacar a quien abrió |
| la autorización durante la cancelación, la cancelada en MP, el miembro con una pendiente | `8a1dcdd` | `3 failed, 45 passed, 3 warnings in 24.35s`: `assert 200 == 409` (se creó «nueva-1»), `assert 'sus-mp2_miembro_…' is None`, `assert 200 == 403` con `{"success":true,"billing_status":"canceled",...}` |
| la que paga va última | antes de `e2e8963` | `3 failed, 1 passed, 49 deselected`, en `[duena-pendiente]`, `[abrio-pendiente]` y `[duena-autorizada]` |
| releer antes de cancelar | antes de `11708b0` | `[GET]`: `assert 200 == 409`; `1 failed, 3 passed, 50 deselected, 3 warnings in 5.03s` |
| el 403 nombra la que paga | antes de `5a3c766` | `AssertionError: {"detail":"Sólo quien administra el estudio o quien abrió la suscripción puede cancelar el plan."}`; `2 failed, 2 passed, 50 deselected, 3 warnings in 4.14s` |
| estado no textual | antes de `5a3c766` | `E   TypeError: unhashable type: 'list'` en `[estado_lista]`; `1 failed, 3 passed, 51 deselected, 3 warnings in 2.45s` |

### Hallazgos de la autorrevisión

Reproduje cada uno antes de anotarlo.

**Adversario Opus, esfuerzo alto, sobre `b183c34`** (corrió también los cruces en Postgres: `fallas: 0`)

| # | hallazgo | qué hice |
|---|---|---|
| 1 | cancelar un estudio con varias suscripciones podía cortar primero la que cobra | arreglado en `e2e8963`, con su rojo arriba |
| 2 | `reactivate_billing` no pide permiso de dueña | riesgo, abajo |
| 3 | entre leer las suscripciones y cancelarlas, una se puede autorizar | arreglado en `11708b0` (se relee cada una justo antes); queda la ventana mínima, abajo |
| 4 | un 404 de Mercado Pago se toma como cancelada | riesgo, abajo |
| 5 | los textos | riesgo y D62 |

**Adversario Sonnet, esfuerzo alto, sobre `b183c34`**

| # | hallazgo | qué hice |
|---|---|---|
| 1 | el mismo que el 1 de Opus | arreglado en `e2e8963` |
| 2 | la pausada de otro miembro se cancela en el checkout | D62 |
| 3 | una pendiente abandonada impide sacar del estudio a quien la abrió | riesgo, abajo |
| 4 | `reactivate_billing` sin permiso ni lock | riesgo, abajo |
| 5 | la guarda del 409 de `cancel_billing` no tiene prueba | declarado, abajo |

**`/code-review high` sobre `7200b82^..b183c34`**

| # | hallazgo | qué hice |
|---|---|---|
| 1 | la pausada de otro miembro | D62 |
| 2 | releer antes de cancelar | arreglado en `11708b0` |
| 3 | un GET que falla bloquea cancelar | riesgo, abajo |
| 4 | una cancelada conserva su id | bajo: no cobra, y el checkout siguiente la ve cancelada y no la toca |
| 5 | una pendiente que se autoriza antes del PUT | bajo: el PUT la cancela antes de que cobre el primer mes |
| 6 | el 403 decía «quien abrió la suscripción» a un miembro que abrió una | arreglado en `5a3c766` |
| 7 | se mantienen los locks mientras se espera a Mercado Pago | riesgo, abajo |
| 8 | los estados que «pagan», escritos en dos lugares | D62 |
| 9 | pruebas duplicadas | arreglado en parte (`_dos_pendientes`) |

**Adversario Sonnet, esfuerzo alto, sobre el arreglo (`8a1dcdd..2a878cd`)**: puso 12 sabotajes propios y los 12 dieron rojo.

| # | hallazgo | qué hice |
|---|---|---|
| 1 | queda una ventana entre la relectura y el PUT | riesgo, abajo |
| 2 | si falla el GET, cancelar da 503 | deliberado: sin saber cómo está, no se cancela a medias |
| 3 | un estado de Mercado Pago que no es texto da 500 | arreglado en `5a3c766` |
| 4 | dos miembros que pagan a la vez | riesgo, abajo |
| 5 | la misma carrera, en cancelar | riesgo, abajo |
| 6 | la pausada de otro | D62 |

**`/security-review`, Sonnet alto, sobre `8a1dcdd..4f1822f`:** sin hallazgos de confianza 8 o más.

### Riesgos

**Aceptados por vos:**

- El de estudios: el plan de un estudio lo cancela la dueña o quien abrió la suscripción que paga.
- Las cuentas `active` sin pago vuelven a `trial`.
- Los supuestos sobre Mercado Pago: los estados son `pending`, `authorized`, `paused` y `cancelled`; una cancelada no vuelve; el cobro es inmediato; se cancela con `PUT /preapproval/{id}` y `{"status":"cancelled"}` por httpx. No se usa el SDK porque en `mercadopago==2.2.0` `PreApproval.update` arma la ruta sin la barra antes del id.
- «Próximo cobro» sale con una suscripción que nunca se autorizó: `renueva` mira `billing_status == "active"`, `mp_preapproval_id` y `payment_provider == "mercadopago"` (`main.py:3267-3270`).

**Nuevos, para que los veas:**

- **La guarda del 409 de `cancel_billing`** (cancelar una cuenta ya cancelada) no tiene caso ni sabotaje.
- **Un 404 de Mercado Pago se toma como cancelada.** Si el id es de otra cuenta de MP o se borró, CDI la da por cancelada sin que lo esté.
- **Los locks se mantienen mientras se espera a Mercado Pago**, hasta unos 20 s en el peor caso (dos llamadas con su timeout). Otra acción de cobro de la misma cuenta espera ese tiempo.
- **`reactivate_billing` no pide ser dueña ni toma lock.** Hoy no hace daño: lo pagado va al checkout, que sí controla. Sólo cambia el texto que se muestra.
- **Una pendiente abandonada impide sacar del estudio a quien la abrió**, hasta que alguien la cancele.
- **Dos miembros que pagan a la vez**, o la misma carrera en cancelar: el lock de la org lo cubre en Postgres (los dos sabotajes de arriba); en SQLite, que no tiene `FOR UPDATE`, no.
- **La ventana entre la relectura y el PUT** sigue abierta, de milisegundos. Cerrarla del todo pide que Mercado Pago acepte un «cancelar si sigue pendiente», y su API no lo tiene.
- **Si falla el GET de una suscripción, cancelar da 503**, aunque las demás se pudieran cancelar. Es a propósito.

### Lo que no salió limpio

- La suite pasó con salida 0, pero el log trae 451 líneas `Task was destroyed but it is pending!`, de tareas de aiosqlite que quedan abiertas al cerrar el event loop. No las comparé con la cantidad en la base, así que no sé si esta pieza agrega alguna.

### chequeo-6

Uso como base `6f79edf`, tu última vuelta, que es lo que vas a medir. Ese rango trae también COBRO-CORTE-1 vuelta 3 (`ca50916`), que todavía no está en tu rama; `a5d4aa7`, en cambio, ya lo está, así que no cuenta acá. Los avisos de `finalize.js` y de `casosTardios` son de COBRO-CORTE-1, con su porqué en el informe de esa entrega. El de las 108 netas suma las dos piezas: 69 son de esta (los nueve commits de producto desde `3d0c8e7`, sumados con `git show --numstat`) y 39 de COBRO-CORTE-1. El porqué de las de esta pieza está en «Producto de la pieza».

```
chequeo-6 6f79edf..4f1822f: avisos para mirar, no un veredicto
producto +372/−264
  AVISO producto suma 108 líneas netas: el informe dice por qué (§6: más de 20)
arnés +1672/−302
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11237 → 11311
  proyecto_maria/services/billing_service.py: 412 → 414
  proyecto_maria/static/v2/app_v2.js: 1190 → 1192
  proyecto_maria/static/v2/screens/clientes.js: 1984 → 1984
  proyecto_maria/static/v2/screens/finalize.js: 1357 → 1387
  AVISO creció una función de más de 150: proyecto_maria/static/v2/screens/finalize.js:9 <anónima> 1349 → 1379, 6 en su propio cuerpo (§6: lo nuevo va aparte)
  proyecto_maria/static/v2/screens/profile.js: 587 → 587
  proyecto_maria/static/v2/screens/upload.js: 718 → 718
  AVISO función nueva de 67 líneas: scripts/testing/pantalla_cobro_corte1.js:33 casosTardios (§6: ~60)
avisos: 3
```

**La última vuelta, entera:**

```
chequeo-6 8a1dcdd..4f1822f: avisos para mirar, no un veredicto
producto +29/−11
arnés +161/−34
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11293 → 11311
avisos: 0
```

**Por commit de producto.** Medir toda la pieza desde `7200b82^` arrastra CORTE-1, CSRF, ORDEN, MP-1 y la limpieza, y da 66 avisos que no son de esta pieza. Medido commit por commit, sólo dos tienen avisos:

- **`a5d4aa7`, 15 avisos.**
  - Suma 151 netas: el porqué está arriba, en «Producto de la pieza».
  - 11 de historia (los comentarios nombraban «COBRO-MP-2» y las D): los sacó `d528a67`. Hoy `grep -rn 'COBRO-MP-2\|D7\.' proyecto_maria/ --include=*.py --include=*.js` da vacío.
  - 3 comentarios de 3 o 4 líneas. El del checkout quedó en dos (`main.py:10983`). Quedan dos docstrings de 3 líneas:
    - `_pedir_suscripcion_mp` (`main.py:10424`): la tercera línea dice por qué se usa httpx y no el SDK, que el código no muestra.
    - `_extender_periodo` (`main.py:10585`): dice desde cuándo suma en cada caso, que es la regla D7.1.
- **`3d0c8e7`, 1 aviso:** suma 29 netas, porque el checkout pasa de mirar al usuario a mirar a todos los miembros del estudio, con su lectura y su lock.
- Los otros ocho commits de producto dan `avisos: 0`.

### Para reproducir

```bash
git checkout 4f1822f
# 1. todo «passed»
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test python -m pytest -q --no-cov tests/test_cobro_mp2.py tests/test_cobro_corte1.py
# 2. todo ROJO y «sabotajes con falla: 0»; sin Postgres 16, la parte de Postgres da BASE en rojo y cuenta una falla
PY=$(which python) scripts/testing/sabotajes/cobro_mp2.sh 4f1822f
# 3. «avisos: 0»
python docs/pm/herramientas/chequeo-6.py 8a1dcdd 4f1822f
```

### Archivos de producto tocados

- `proyecto_maria/main.py` (`cancel_billing`, `reactivate_billing`, `billing_me`, `billing_checkout`, `_pedir_suscripcion_mp`, `_cancelar_suscripcion_mp`, `_estado_suscripcion_vieja`, `_extender_periodo`, `_demo_permitida` y las rutas de la demo)
- `proyecto_maria/services/billing_service.py`
- `proyecto_maria/static/v2/screens/profile.js`
- `CHANGELOG.md`

---

/compact conservar: Dev 1, rama claude/dev-tecnica. COBRO-MP-2 entregada en 4f1822f (informe en el commit de arriba), con D62. Sigue COBRO-MP-3. Nada se publica sin el «dale» de Emi; nunca main.

Corte (2026-11-06): la devolución de COBRO-MP-2 y COBRO-MP-3 está en 6ecfe06 (producto y casos commiteados y subidos), sin informe de la vuelta. En 6ecfe06 corrieron la suite («374 passed, 3 warnings in 165.66s») y 19 sabotajes de cobro_mp2.sh, todos en rojo; los demás sabotajes de MP-2 y los de MP-1, Postgres, compileall, `/code-review`, `/security-review` y chequeo-6 no se corrieron. VALIDACION-1 tiene el arreglo y el caso escritos, sin commitear.

VALIDACION-1 queda a medias en e59ae3c y no es entrega. El arreglo de `finalize.js` y el caso `pantalla_validacion1.js` dan rojo en la base y verde con el arreglo en panel, botón (dos casos) e historial. Faltan: el validador simulado en los casos «la anterior contesta después» y «falla el validador», el sabotaje `validacion1.sh`, traer la rama de la PM, la suite, las puertas, CHANGELOG y el informe. En los arneses de pantalla, destino1 y maria9 dan rojo con el arreglo y el mismo rojo con el `finalize.js` de la base (no pueden llenar el campo del sufijo), así que ese rojo no lo causa este cambio. maria3, maria4 y maria5 traen escrita una ruta de chromium que en este contenedor no existe. Con la ruta corregida en una copia los tres dan rojo (maria4: el mismo campo del sufijo; maria5: «no se ve el peso de la línea (25 kg) debajo del unitario»). Estos tres no los corrí con la base: no está comprobado que no los cause el cambio.
