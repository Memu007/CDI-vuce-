# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-MP-1: entregado en `784e793` (informe en el commit de arriba)

**Resultado.** Están A a E de tu devolución del 2026-10-28 17:05 UTC, cada
uno con su rojo antes y sus sabotajes. También los arreglos de lo que
encontraron los adversarios, `/code-review high` y `/security-review`, que
corrí antes de entregar como pediste a las 23:33. Puertas en verde: suite
completa, pruebas de la pieza, smoke y ataque de aislamiento sobre
`551de83`; sabotajes, carrera en Postgres 16 y pantalla sobre `784e793`.
`784e793` sólo cambia la prueba de pantalla y el script de sabotajes (ver
«Puertas»), así que el producto entregado es el de `551de83`. Lo que queda afuera está en
«Riesgos».

ORDEN-1 (vuelta 2) sigue entregada en `86c9d84` + su informe; este informe
reemplaza aquel cuerpo.

### Decisiones

Numeradas desde D8: vos asignaste D6 a COBRO-MP-1 y D7 a COBRO-MP-2
(`192774f`). Mencionabas «D8» como lugar posible para BACKUP y AISLAMIENTO;
si lo querés para eso, renumerá estas.

- **D8 (antes D33). Las consultas a Mercado Pago frenan todo el servidor.**
  Son síncronas dentro del handler async; el SDK espera hasta 60 s por
  consulta, y con el aviso IPN sin firma (D28) cualquiera las provoca.
  (a) Tarea aparte, después de esta tanda: las tres consultas a un hilo con
  tope de 10 s. (b) Dentro de COBRO-MP-1 ahora. (c) Dejarlo.
  **Recomiendo (a):** toca el camino del cobro, ya revisado; mezclarlo agranda
  una pieza de plata.
- **D9 (antes D34). Un cobro de renovación que todavía no dice qué pago lo
  cobró responde 200.** Mercado Pago no reintenta y la renovación se pierde
  hasta que alguien mire el log. (a) Dejar 200 y el log. (b) 503, para que
  reintente. **Recomiendo (b):** perder una renovación cobrada le cuesta al
  cliente; un reintento de más es una lectura.
- **D10. Si el navegador no llega a Mercado Pago, el botón de checkout queda
  en «Abriendo…» hasta recargar.** Pasa si la persona aprieta «Quedarse» en
  un aviso de «salir de la página», o si la navegación se corta. (a) Riesgo
  aceptado: recargar lo arregla. (b) Un tope que rehabilita el botón; reabre
  el doble checkout que D cierra, porque otro clic cancela la suscripción
  adonde va el navegador. **Recomiendo (a).**

La vieja D35 (rechazo fijo) y la vieja D36 (pagos de antes del registro)
salen de las decisiones: D35 va a riesgos, como pediste, y A reemplaza D36.

### SHAs

La pieza no es un rango continuo: está intercalada con ORDEN-1, EXCEL-2b,
BACKUP, CORTE, MP-2 y tus merges. Base de la retoma: `957539d`.

| Qué | SHA |
|---|---|
| Retoma (pasos 1 a 4, arreglo de la renovación, CHANGELOG, sabotajes) | `b545847`, `730a608`, `cfaf2fc`, `f6ddd52`, `7d1ca39`, `be4a6c6`, `0cac99d`, `5a2fb30`, `f54d8a9` |
| Devolución anterior (id del pago, ruta, último pago, aviso sin token) | `d868adf`, `0ed51b5`, `6f9131c`, `836da59` |
| **A**: rojo / producto / sabotajes | `d7edcfe`, `292eca1` / `b44c25e` / `8ca00f7` |
| **B**: rojo / producto | `c3a05a7` / `85a32e6` |
| **C y E**: rojo / producto | `86687fa` / `4b3ebbd` |
| **D**: rojo en Postgres 16 / producto | `aaa20f0` / `d316db2` |
| Pantalla del perfil, C y D: rojo / producto | `3b38dc2` / `12ec020` |
| Sabotajes de B a E | `c73a286` |
| Cancelar espera al checkout en curso: rojo / producto / sabotaje | `472e389` / `87094a1` / `4115f32` |
| E con un pago rechazado: rojo / producto / negativo / sabotajes | `5c12041` / `f974303` / `f564015` / `3761589` |
| Cancelada que reabrió el checkout: rojos / producto / sabotajes | `1e67ba6`, `ca382ed` / `17f0b71` / `84d8062` |
| «Activar plan» no se rehabilita al ir a Mercado Pago: rojo / producto / sabotaje | `d60f526` / `14a4af7` / `ec6aa97` |
| Los tres botones y volver con «Atrás»: rojo / producto / sabotajes | `1df639b` / `32def35` / `04457fe` |
| Un solo `irAlCheckout(plan, boton)` (refactor) | `75b32ac` |
| Sabotajes de D contra `irAlCheckout`, tope de la pantalla | `db08e76` |
| Un checkout a la vez entre el aviso y el perfil: rojo / producto / sabotajes | `4b4ae3d` / `8ca38cc` / `551de83` |
| Un checkout fallido no traba el siguiente, sin recargar (prueba) | `784e793` |
| Informe | este commit |

Archivos de producto: `proyecto_maria/main.py`,
`proyecto_maria/database/connection.py`, `proyecto_maria/database/models.py`,
`proyecto_maria/services/billing_service.py`,
`proyecto_maria/templates/dev_dashboard.html`,
`proyecto_maria/static/v2/screens/profile.js`,
`proyecto_maria/static/v2/app_v2.js` y `CHANGELOG.md`.

### A–E: qué hace ahora

- **A. Un pago viejo no se reaplica.** Elegí cortar por fecha.
  - `init_db` siembra una sola vez `InicioRegistroPagosMP` (fila id=1, campo
    `desde`). Si ya había pagos en `mp_pagos_aplicados`, `desde` es el primero
    registrado; si no, ahora. Al rearrancar no se mueve. Si dos procesos
    arrancan a la vez, el `IntegrityError` del segundo se ignora.
  - El webhook rechaza, a la vista del admin en `/api/dev/pagos-mp-rechazados`,
    el pago con `date_approved` anterior a `desde` («aprobado antes de que
    empezara el registro de pagos (…)») y el que no trae una fecha legible
    con zona («sin fecha de aprobación legible»). Sin la fila, 503.
  - Por qué así: los pagos de antes del registro no están en ningún lado, y
    la fecha de aprobación la da Mercado Pago, no el aviso.
- **B. La exportación cuenta**, una vez por operación: `/generate_maria_export`
  pasa por `_contar_maria` con su archivo `MARIA_EXPORT_<id>.TXT` antes de
  escribirlo. Con el tope lleno, la nueva da 402 y la ya contada sale.
- **C. Cancelar desde past_due.** `/api/billing/cancel` lo admite: cancela en
  Mercado Pago, la cuenta queda `canceled` y `trial_ends_at` queda en ahora
  como máximo, así no gana acceso. Si Mercado Pago no cancela, queda como
  estaba. «Cancelar plan» se ve con el plan vencido y la confirmación no
  promete el período pagado. Agregado por un adversario: una cuenta
  `canceled` que reactivó y abrió un checkout nuevo también puede cancelar
  esa suscripción (`17f0b71`); `billing/me` dice `suscripcion_abierta`.
- **D. Dos checkouts a la vez dejan una sola suscripción.**
  - El checkout toma la fila con `with_for_update` hasta guardar la
    suscripción nueva; el segundo espera, ve la del primero, la cancela y
    guarda la suya. Cancelar también toma la fila (`87094a1`), así no deja
    viva la suscripción de un checkout en curso.
  - En la pantalla, los tres botones («Activar plan», «Reactivar plan» y
    «Activar plan ahora», el aviso de arriba) usan `CDI.irAlCheckout(plan,
    boton)`: se deshabilita mientras pide, no se rehabilita mientras el
    navegador va a Mercado Pago, y una guarda común impide que otro botón pida
    un segundo checkout. Si falla, avisa con el detalle del servidor o «No se
    pudo iniciar el cobro.», restaura el botón y suelta la guarda. Volver con
    «Atrás» desde la caché recarga la página.
- **E. Reactivar una prueba con recarga vuelve a `trial`.** `_pago_un_plan_mp`
  mira los pagos aplicados: una recarga sola no es un plan. Sin pagos
  aplicados (pagó antes del registro, o sólo tiene rechazos) decide
  `payment_provider == "mercadopago"`.

### Cómo se vio en rojo

Copiado de la salida (`rojos_pieza.log` reproduce cada rojo sobre su commit;
los de pantalla, del mensaje de cada commit, copiado de la salida de ese
momento):

| Commit | Salida |
|---|---|
| `d7edcfe` (A) | «9 failed, 61 passed» |
| `c3a05a7` (B) | «2 failed, 53 passed» |
| `86687fa` (C y E) | «7 failed, 2 passed» |
| `aaa20f0` (D, Postgres 16) | «FALLA \| sin suscripción anterior: queda una sola suscripción viva en Mercado Pago (['nueva-1', 'nueva-2'])», «fallas: 4» |
| `3b38dc2` (pantalla) | «FALLA: past_due: no se ve «Cancelar plan»»; con C arreglado, «FALLA: el botón «Activar plan» no se deshabilita mientras pide el checkout» |
| `472e389` (cancelar contra checkout) | «['nueva-1'], CDI guarda None» |
| `5c12041` (E, rechazado) | «1 failed, 9 passed»; «billing_status: trial, needs_checkout: False» |
| `1e67ba6` (cancelada con checkout) | «1 failed, 12 passed»; «No se puede cancelar desde el estado actual: canceled» |
| `d60f526` | «FALLA: el botón «Activar plan» se vuelve a habilitar mientras el navegador va a Mercado Pago» |
| `1df639b` | «FALLA: volver de Mercado Pago con «Atrás» no recarga la página», «FALLA: «Reactivar plan» se vuelve a habilitar…», «FALLA: «Activar plan ahora» se vuelve a habilitar…» |
| `4b4ae3d` | «FALLA: «Activar plan ahora» y después «Activar plan» pidieron 2 checkouts» |
| `784e793` | Con la guarda sin soltar (sabotaje): «FALLA: después de un checkout fallido, «Activar plan» no vuelve a pedirlo» |

### Puertas

Sobre `551de83` corrí la suite, las pruebas de la pieza, `compileall`, el
smoke y el ataque. En esa corrida los sabotajes dieron «sabotajes con falla: 1»:
«VERDE | D: un checkout fallido deja trabados los demás: la prueba no lo
vio». La causa estaba en la prueba: cada caso de la pantalla recarga el
perfil (`perfilCon` hace `page.goto`), y la recarga suelta la guarda común.
`784e793` agrega un caso sin recarga: después del error, otro clic tiene
que pedir el checkout. Ese commit no toca producto, así que las puertas de
producto de `551de83` siguen valiendo. Los sabotajes se corrieron otra vez
sobre `784e793`.

| Puerta | Salida |
|---|---|
| Suite completa, worktree limpio | «4283 passed, 121 skipped, 3 xfailed, 102 warnings in 586.29s (0:09:46)», rc=0 |
| Pruebas de la pieza (7 archivos, abajo) | «220 passed, 4 warnings in 90.82s (0:01:30)» |
| `cobro_mp1.sh 784e793` (incluye la carrera en Postgres 16 y la pantalla) | 68 ROJO; BASE, la carrera en Postgres y la pantalla, en verde; «VERDE \| sin mirar antes de insertar: sigue en verde, como tiene que ser»; «sabotajes con falla: 0», rc=0. Entre ellos, «ROJO  \| D: cancelar no espera al checkout en curso», «ROJO  \| D: otro botón pide un segundo checkout mientras hay uno en curso» y «ROJO  \| D: un checkout fallido deja trabados los demás: dice «FALLA: después de un checkout fallido, «Activar plan» no vuelve a pedirlo»» |
| `compileall -q proyecto_maria` | rc=0 |
| `smoke_friccion.sh` contra la API en `551de83` | «==> OK · telemetría + alias session/state + by-cuit protegido», rc=0 |
| `ataque_aislamiento.sh` en `551de83` | «Bloqueado: 47 · Fugas: 0 · Sin probar: 0», «PUERTA G3 PASADA», rc=0 |

No corrido: nada contra Mercado Pago real (G7).

### Revisiones

| Quién | Sobre | Hallazgo | Qué se hizo |
|---|---|---|---|
| Opus alto, 19:39 | `c73a286` | (Media) Un pago en vuelo al desplegar, aprobado antes de `desde`, queda rechazado y la cuenta en past_due | Riesgo de diseño de A (abajo) |
| Opus alto | | (Media-baja) Plan viejo más un rechazo o una recarga reactiva como prueba | Rechazo: `5c12041`/`f974303`. Recarga: riesgo |
| Opus alto | | (Baja-media) Cancelar contra un checkout deja `nueva-1` viva | `472e389`/`87094a1` |
| Opus alto | | (Media, de COBRO-MP-2) Dos miembros de una organización crean dos suscripciones | Riesgo, fuera de la pieza |
| Sonnet alto, 19:39 | `c73a286` | Cancelar contra checkout (Postgres); recarga y vuelta a prueba; pago en vuelo; el `finally` rehabilita el botón | `87094a1`; riesgo; riesgo; `14a4af7`/`32def35` |
| Sonnet alto, 20:19 | `87094a1`, `f974303` | (Media) Cancelada con suscripción viva no puede cancelar (409) | `1e67ba6`/`17f0b71` |
| Sonnet alto, 20:19 | | (Baja) Pool de conexiones agotado con muchos cancel (preexistente) | Riesgo |
| Sonnet alto, 20:19 | | (Baja) `_pago_un_plan_mp` no ve pagos `org:<id>` | Riesgo, por lectura |
| Sonnet alto, 23:58 | checkout | Cruce entre el aviso y el perfil: dos checkouts | `4b4ae3d`/`8ca38cc`/`551de83` |
| Sonnet alto, 23:58 | | Botón trabado tras «Quedarse»; `pageshow`; 401 y 402 cosméticos | D10; riesgo; sin cambio |
| `/code-review high` | rama | `err.message` crudo en el toast; dos copias de la lógica | `75b32ac` |
| `/code-review high` | | La pantalla se colgaba si no redirigía; un sabotaje medía un TypeError | `db08e76` |
| `/code-review high` | | «Quedarse»; `pageshow`; `_wired`; `openTopup` | D10; riesgos bajos |
| `/security-review` (17:02, 20:12 y 23:42) | rama | Ninguno con confianza 8 o más en la última | — |

### Supuestos (reversibles)

- A corta por fecha de aprobación y no por período: lo elegí porque la fecha
  la da Mercado Pago y no depende del estado de la cuenta.
- `17f0b71` (cancelar una `canceled` con suscripción abierta) y los arreglos
  de los botones no estaban en A–E: salieron de los adversarios y los dejé
  porque sin ellos D no se cumple del todo. Si no los querés acá, se separan.

### Riesgos

- **Pago en vuelo al desplegar** (A): un pago aprobado antes de `desde` cuyo
  aviso llega después queda rechazado; Emi lo ve en el panel, pero no hay
  forma de aplicarlo a mano.
- **Plan pagado antes del registro, más una recarga aplicada:** reactivar lo
  trata como prueba.
- **Un rechazo queda fijo** (vieja D35): si el aviso `payment` de una
  renovación llega antes que el `subscription_authorized_payment` y se compara
  con otro monto, el segundo no lo aplica.
- **Renovación sin suscripción, rechazada para siempre.**
- **Dos pagos distintos de una cuenta a la vez** suman uno solo.
- **F**, la renovación con monto de panel menor, el aviso sin
  `external_reference` que da 400 y `precio_esperado` sin vencimiento.
- **Dos miembros de una organización** pueden crear dos suscripciones
  (COBRO-MP-2).
- **Pool de conexiones** agotado con muchos cancel a la vez (preexistente:
  pico de 51, TimeoutError con 60).
- **`_pago_un_plan_mp` no ve pagos `org:<id>`** (por lectura, sin prueba).
- **Botón trabado** (D10) y `pageshow`, `_wired` y `openTopup`, bajos.
- **D28:** el aviso IPN sin firma se sigue aceptando.
- **Nada contra Mercado Pago real** (G7).
- El aviso «Task was destroyed but it is pending … async_generator_athrow» es
  preexistente.

### Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout 784e793
export GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
$PM_DIR/venv/bin/python -m pytest -q --no-cov tests/test_cobro_mp1.py tests/test_cobro_mp1_cde.py tests/test_cobro_corte1.py tests/test_cobro_mp2.py tests/test_g7_cobro.py tests/test_prelaunch_block2.py tests/test_webhook_ipn.py
#   «220 passed»
PY=$PM_DIR/venv/bin/python PUERTO=8854 bash scripts/testing/sabotajes/cobro_mp1.sh 784e793
#   68 «ROJO  |», «BASE  | la pantalla, en verde» y «sabotajes con falla: 0»
```

/compact conservar: Dev 1 (técnica), sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica, rutina trig_011UpBfwEu9TUzoNUrviqoP5 (la maneja la PM), aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM). Emi: sin fecha, calidad primero, una pieza a la vez, sin saltear /entregar. COBRO-MP-1 entregada en 784e793 + informe, con D8–D10. Sigue COBRO-CORTE-1; después COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1, BACKUP-1a, EXCEL-2c.
