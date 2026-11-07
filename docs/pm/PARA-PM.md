# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-MP-2 (vuelta) y COBRO-MP-3, entregadas en `cb740f3` (informe en el commit de arriba)

Las dos piezas van en el mismo SHA. Tienen secciones separadas, y las puertas son comunes.

El producto de las dos piezas es el mismo que en `6ecfe06`. Después de ese SHA cambiaron sólo dos guiones de sabotaje (`b7ce3b1` y `5903441`), dos líneas del `CHANGELOG.md` (`b07acd5`) y un caso de `tests/test_cobro_mp2.py` (`cb740f3`). Además entraron tus dos merges y los commits de VALIDACION-1 (`e59ae3c`, `e4c79a1`, `60023d6`, `0b9d476` y `db31e0e`), que tocan `finalize.js` y su arnés: esa pieza va en su propio informe, después de este, y este no la cubre.

### Decisiones

**D64. Avisos de Mercado Pago sin firma.** Desde esta entrega, el aviso de pago sólo atiende Webhooks con firma válida contra `MP_WEBHOOK_SECRET`. Contesta 401 en tres casos, en cualquier entorno:

- un IPN, que no trae firma;
- un aviso sin clave configurada en CDI;
- un aviso con firma inválida.

Antes, sin clave fuera de producción, el aviso pasaba sin verificar (`return not IS_PRODUCTION`). Además, la rama IPN leía `topic` e `id` de la URL sin firma. Si en la cuenta de Mercado Pago de producción no están configurados los Webhooks con la clave, los avisos de pago se pierden: el pago se cobra y la cuenta no se activa.

- (a) Antes de publicar, Emi configura en Mercado Pago los Webhooks con la clave y carga `MP_WEBHOOK_SECRET` en Railway. Después prueba en sandbox que un pago active la cuenta.
- (b) Publicar sin configurarlo.

Recomiendo **(a)**. Con (b), los pagos reales no se aplican hasta que alguien lo note. Esto no se puede probar desde acá: no hay Mercado Pago real.

**D66. A qué IP cuenta el límite del aviso.** El límite usa `get_client_ip` (`core/rate_limit.py:43`), que toma el primer valor de `X-Forwarded-For`, y ese valor lo puede poner cualquiera. El límite cuenta sólo avisos firmados, así que quien no tiene la clave no le gasta el cupo a Mercado Pago. Pero quien tiene un aviso firmado de verdad puede reenviarlo cambiando ese encabezado, y cada valor nuevo arranca con su propio cupo.

- (a) Dejarlo así. Un aviso firmado repetido ya es idempotente: un pago se aplica una vez (`mp_pagos_aplicados`).
- (b) Contar con la IP que ve Railway y no con la del encabezado. Es un cambio en `core/rate_limit.py`, que usan todos los límites del servidor. Pieza aparte.

Recomiendo **(a)** para esta entrega y **(b)** como pieza aparte, si la querés. El límite de hoy frena el caso de la tarea, que es un aviso sin firma. Cambiar `get_client_ip` mueve todos los límites del servidor, y eso no entra en esta pieza.

### Resultado

**COBRO-MP-2, la vuelta.** Están cerradas las tres causas y D62 (a).

- **Una sola regla de quién toca el plan** (`_quien_toca_el_plan`, `main.py:10930`). La usan cancelar, reactivar, checkout y sacar a un miembro.
  - Sacar a un miembro sólo se frena si su suscripción es la que paga el estudio, autorizada o pausada (409).
  - Si el miembro tiene una suscripción pendiente, se cancela en Mercado Pago al sacarlo. Si Mercado Pago no contesta, 503 y el miembro sigue en el estudio.
  - Reactivar toma el mismo candado que cancelar.
- **El perfil** (`billing_me`) muestra a todos los miembros la suscripción que paga el estudio.
- **Con Mercado Pago sin contestar**, cancelar, reactivar, checkout y sacar a un miembro dan 503 a los 15 s.
  - Los 15 s cuentan desde que se toma el candado, así que la espera de otro pedido del mismo estudio no cuenta.
  - El corte del SDK (`requests.RequestException`) también da 503 en el checkout y en la recarga.
- **D62 (a):** la pausada de otro miembro frena el checkout con 409. Los estados que pagan se escriben una vez (`_ESTADOS_QUE_PAGAN`, `main.py:10451`).
- **No toqué** `expired` en 503, «Próximo cobro» con una cancelada desde Mercado Pago ni los textos viejos.

**COBRO-MP-3.**

- **Las consultas a Mercado Pago corren en hilos propios** (`_en_hilo_mp`, `main.py:10306`): hasta 8 a la vez (`_HILOS_MP`). Las usan el aviso de pago, el checkout, la recarga, cancelar, reactivar y sacar a un miembro.
  - Una consulta trabada contesta 503 a su pedido a los 15 s y deja de ocupar un lugar de los 8.
  - Su hilo sigue vivo hasta que corta el SDK: `connection_timeout=10.0` y `max_retries=1`, unos 20 s.
  - Con más consultas trabadas que hilos tiene el servidor, entrar a la cuenta sigue contestando.
- **El aviso de pago tiene límite:** 60 avisos firmados por minuto por IP, y después 429 (`_LIMITE_AVISOS_MP`, `main.py:10680`). Se cuenta después de la firma, así que los avisos sin firma no gastan el cupo de los firmados.
- **Un aviso sin firma verificable da 401 sin cambiar nada y sin consultar a Mercado Pago.** Vale para los IPN, la falta de clave, otra clave, un cuerpo o un `data` que no es un objeto y una firma con letras no ASCII, en desarrollo y en producción. La rama IPN se sacó. Ver D64.

### SHAs

| SHA | qué |
|---|---|
| `6b18c47` | informe anterior |
| `1f50328` | producto MP-3: hilos propios, límite del aviso, sólo avisos firmados |
| `24e23ce` | pruebas MP-3 |
| `52ab1c0` | producto MP-3: el límite cuenta sólo los firmados; 20 s por hilo; firma no ASCII da 401 |
| `4ef51eb` | pruebas de `52ab1c0` |
| `8e3274c` | merge de tu rama |
| `6c481d7` | producto MP-2: la regla única, el perfil del estudio, 503 con tope, D62 (a) |
| `1b909bf` | pruebas de `6c481d7` |
| `49f7850` | los sabotajes de MP-1 siguen al código de `6c481d7` |
| `26d06ba` | producto: el corte del SDK da 503 en el checkout |
| `ffc386b` | prueba de `26d06ba` |
| `2c86d9b` | producto: el tope cuenta desde el candado; la recarga da 503; `_aviso_mp_firmado`; `anyio` en requirements |
| `171313c` | pruebas: Postgres con el candado retenido, la recarga cortada, sabotajes del tope antes del candado |
| `0fbfaff` | los sabotajes de MP-3 siguen las líneas actuales |
| `6ecfe06` | los sabotajes de MP-1 y MP-2 cortan un caso trabado a los 120 s |
| `18f2928`, `e8a28b2`, `f283e64` | informes al corte (sólo `PARA-PM.md`) |
| `e59ae3c` | VALIDACION-1 a medias: no es entrega |
| `f9fe432` | merge de tu rama: limpieza aceptada (tandas 1 a 3) y `NOW.md` |
| `b7ce3b1` | los sabotajes ven un caso trabado por el texto de pytest-timeout; dos sabotajes nuevos del plazo de reactivar y checkout |
| `5903441` | el sabotaje de MP-1 «D: cancelar no espera al checkout en curso» sigue la línea del plazo |
| `7101e2f` | merge de tu rama (`NOW.md`, `DECISIONS.md`) |
| `b07acd5` | `CHANGELOG.md`: el 503 llega a los 15 s y el hilo vive hasta el corte del SDK; la recarga da 503 con ese corte |
| `e4c79a1`, `60023d6`, `0b9d476`, `db31e0e` | VALIDACION-1: no los cubre este informe |
| `cb740f3` | prueba: al sacar a un miembro con la suscripción ya cancelada, se cuentan los PUT a Mercado Pago |

Tus commits intercalados son `2524216`, `03b676d` y los merges `8e3274c`, `f9fe432` y `7101e2f`.

**Producto de las dos piezas (`4f1822f..6ecfe06`): `+157/−101`, 56 netas.**

| commit | `main.py` | `billing_service.py` | `requirements.txt` |
|---|---|---|---|
| `1f50328` | +45/−57 | +12/−4 | |
| `52ab1c0` | +10/−3 | +3/−2 | |
| `6c481d7` | +86/−43 | | |
| `26d06ba` | +4/−2 | | |
| `2c86d9b` | +21/−14 | | +1 |

MP-3 da −5 en `main.py` y +9 en `billing_service.py`; MP-2 da +52 en `main.py`. Por qué suma más de 20:

- La regla única `_quien_toca_el_plan` reemplaza los controles sueltos de cancelar y checkout, y suma reactivar y sacar a un miembro.
- Sacar a un miembro ahora lee su suscripción y la cancela, con su 409 y su 503.
- Se suman `_en_hilo_mp` con su tope, `_aviso_mp_firmado` y los tres textos del 409.
- Lo que se sacó es la rama IPN del aviso.

### Cómo se cumple cada punto: COBRO-MP-2

Casos en `tests/test_cobro_mp2.py`, sabotajes en `scripts/testing/sabotajes/cobro_mp2.sh`.

| punto | qué hace el producto | caso | sabotaje |
|---|---|---|---|
| Causa 1: quién toca el plan (dueña, quien abrió, otro miembro, como datos de un caso) | `_quien_toca_el_plan` para cancelar, reactivar, checkout y sacar; reactivar toma el candado de cancelar | `test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan` (ver la tabla de abajo) | «reactivar no mira quién toca el plan», «al sacar a un miembro no se mira su suscripción», «se saca del estudio a quien abrió la que paga», «se saca del estudio a quien tiene la pausada» |
| Causa 1: la pendiente de un miembro se cancela al sacarlo | lee su suscripción; la pendiente se cancela en MP; la cancelada no se vuelve a cancelar; si MP no contesta, 503 y sigue | mismo caso, filas `sacar_con_pendiente`, `sacar_con_cancelada`, `sacar_sin_mp`; las dos primeras cuentan los PUT a Mercado Pago sobre la suscripción del miembro (1 y 0) | «al sacar, la ya cancelada se vuelve a cancelar», «al sacar, si Mercado Pago no contesta se saca igual», «al sacar, la suscripción cancelada sigue anotada» |
| Causa 2: el perfil del estudio | `billing_me` muestra la suscripción que paga el estudio a todos | `test_billing_me_muestra_la_suscripcion_del_estudio_a_todos` | «el perfil de un miembro no ve la suscripción del estudio» |
| Causa 3: 503 dentro del tope | `_en_hilo_mp` con `hasta=plazo`; el plazo se calcula con el candado tomado; el corte del SDK da 503 | `test_con_mp_sin_contestar_se_contesta_503_dentro_del_tope` (8 filas); en Postgres, el escenario 3 de `cobro_mp2_postgres.py` | «sin tope al esperar a Mercado Pago (fila)», uno por fila; «el checkout sin respuesta de Mercado Pago da 500»; el del corte del SDK; los dos del plazo antes del candado (cancelar y sacar) |
| D62 (a) | la pausada de otro miembro da 409; los estados que pagan, una vez | `test_otro_miembro_no_abre_una_segunda_suscripcion_de_la_org` (`[pausada]`) y la fila `checkout_con_pausada` | «la pausada de otro miembro no frena el checkout» |

Los códigos de `test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan`, en el orden dueña, quien abrió y otro miembro:

| escenario | códigos |
|---|---|
| cancelar | 200, 200, 403 |
| checkout_con_pausada | 409, 200, 409 |
| sacar_con_pendiente | 200, 403, 403 |
| sacar_con_cancelada | 200, 403, 403 |
| sacar_sin_mp | 503, 403, 403 |
| sacar_a_la_que_paga | 409, 403, 403 |
| sacar_a_la_pausada | 409, 403, 403 |
| reactivar | según quién la canceló |

Sacar a un miembro lo hace sólo la dueña: por eso quien abrió y otro miembro dan 403 en las filas de sacar.

Dos casos quedaron absorbidos por el de la familia: `test_en_una_org_un_miembro_que_no_la_abrio_no_la_cancela` y `test_no_se_saca_del_estudio_a_quien_abrio_la_suscripcion`.

### Cómo se cumple cada punto: COBRO-MP-3

Casos en `tests/test_cobro_mp3.py`, sabotajes en `scripts/testing/sabotajes/cobro_mp3.sh`.

| punto | qué hace el producto | caso | sabotaje |
|---|---|---|---|
| Mercado Pago no frena el servidor | `_en_hilo_mp` corre cada consulta en un hilo, con un límite propio de 8 | `test_un_mercado_pago_trabado_no_frena_el_servidor`: 43 avisos firmados, un checkout y una recarga trabados; entrar a la cuenta contesta en menos de 15 s; ninguna consulta corre en el hilo del servidor; nunca hay más de 8 adentro | «Mercado Pago se consulta en el hilo del servidor», «las consultas a Mercado Pago usan los hilos de todo el servidor», «el pago de un aviso se consulta fuera del hilo», «la recarga crea el cobro fuera del hilo», «el checkout crea la suscripción fuera del hilo» |
| la recarga cortada | el corte del SDK da 503 | `test_la_recarga_con_mercado_pago_cortado_da_503` | «la recarga con Mercado Pago cortado da 500» |
| límite de pedidos | 60 firmados por minuto por IP, después 429; los sin firma no cuentan | `test_el_aviso_de_pago_tiene_limite_de_pedidos`: 60 sin firma dan 401, y después 60 firmados dan 200 y el 61 da 429 | «el aviso de pago sin límite de pedidos», «el límite cuenta también los avisos sin firma» |
| un aviso sin firma no cambia nada | 401 antes de leer el cuerpo o consultar a MP | `test_un_aviso_sin_firma_verificable_no_cambia_nada`: 7 tipos de aviso × desarrollo y producción × con y sin clave; 401, ninguna consulta a MP y la cuenta igual | «sin clave, en desarrollo, el aviso pasa sin verificar», «se atiende un IPN por la URL, sin firma», «un cuerpo que no es un objeto rompe la verificación», «un data que no es un objeto rompe la verificación», «la firma se compara como texto» |

Los avisos firmados de las pruebas salen de `tests/mp_firma.py`. En `test_cobro_mp1.py` se sacó la parte de IPN, y `test_signature_no_secret_in_dev_allows` pasó a `_rejects`.

### Puertas

| Puerta | SHA | Salida |
|---|---|---|
| suite completa, desde un worktree limpio | `cb740f3` | `4570 passed, 101 skipped, 3 xfailed in 706.31s (0:11:46)`, salida 0 |
| `compileall -q proyecto_maria` | `cb740f3` | salida 0, sin otra salida |
| sabotajes `cobro_mp3.sh` | `0fbfaff` | BASE en verde, 13 ROJO, `sabotajes con falla: 0` |
| sabotajes `cobro_mp2.sh`, con Postgres | `cb740f3` | 66 ROJO, BASE en verde en las dos partes (`en verde` y `los cruces en Postgres, en verde`), `sabotajes con falla: 0`, salida 0 |
| sabotajes `cobro_mp2.sh`, con Postgres | `b7ce3b1` | 65 ROJO, BASE en verde en las dos partes y 1 VERDE: `VERDE | al sacar, la ya cancelada se vuelve a cancelar: la prueba no lo vio`; `sabotajes con falla: 1`. Ver «Lo que no salió limpio» |
| sabotajes `cobro_mp1.sh`, entero | `6ecfe06` | 144 ROJO, el VERDE esperado («sin mirar antes de insertar: sigue en verde, como tiene que ser») y 1 ROTO («D: cancelar no espera al checkout en curso: el sabotaje no encontró su patrón»); `sabotajes con falla: 1` |
| sabotajes `cobro_mp1.sh`, sólo el bloque D en Postgres, con el patrón arreglado | `5903441` | `BASE  | la carrera de D en Postgres, en verde`, los dos ROJO (el segundo dice «FALLA | cancelar durante un checkout: no queda ninguna suscripción viva en Mercado Pago»), `sabotajes con falla: 0` |
| `cobro_mp2_postgres.py` (tres escenarios) | `6ecfe06` | 16 OK, `fallas: 0` |
| `tests/test_cobro_mp3.py tests/test_cobro_mp2.py` | `cb740f3` | `98 passed in 82.93s (0:01:22)` |
| pruebas de cobro | `171313c` | `222 passed in 112.92s` |
| `/code-review high` | `4f1822f..` la vuelta | abajo |
| `/security-review` | `4f1822f..0fbfaff` | sin hallazgos de confianza 8 o más (14 candidatos descartados) |
| chequeo-6 | `4f1822f..6ecfe06` y `db31e0e..cb740f3` | abajo, `avisos: 1` y `avisos: 0` |

`git diff 6ecfe06 cb740f3 -- proyecto_maria/main.py proyecto_maria/services/billing_service.py requirements.txt` da vacío: el producto de cobro no cambió desde `6ecfe06`. Los sabotajes de MP-3 y el escenario de Postgres se corrieron sobre `0fbfaff` y `6ecfe06`, y desde ahí esos guiones tampoco cambiaron. Lo que sí entró después es tu limpieza y VALIDACION-1, y los cubre la suite sobre `cb740f3`.

`smoke_friccion.sh` y `ataque_aislamiento.sh`: no corridos. La pieza no cambia quién ve qué datos. Los permisos que toca (quién toca el plan de un estudio) tienen sus casos y sabotajes arriba. `ataque_aislamiento.sh` cubre clientes y descargas, que la pieza no toca.

### Rojo antes

Los rojos están copiados de la salida.

| tramo | producto de antes | rojo |
|---|---|---|
| MP-2, las tres causas y D62 (pruebas de `1b909bf`) | `4f1822f` | `19 failed, 71 passed in 115.51s (0:01:55)`: el caso de la familia en `[reactivar-abrio]`, `[reactivar-miembro]`, `[checkout_con_pausada-duena]`, `[checkout_con_pausada-miembro]`, `[sacar_con_pendiente-duena]`, `[sacar_con_cancelada-duena]` y `[sacar_sin_mp-duena]`; el perfil en `[duena-con_suscripcion]` y `[miembro-con_suscripcion]`; la segunda suscripción en `[autorizada_vigente]`, `[autorizada_vencida]` y `[pausada]`; el tope en `[cancelar_lee]`, `[cancelar_cancela]`, `[checkout_lee]`, `[checkout_cancela]`, `[checkout_crea]`, `[sacar_lee]` y `[sacar_cancela]` |
| MP-2, el corte del SDK en el checkout | `6c481d7` | `FAILED tests/test_cobro_mp2.py::test_con_mp_sin_contestar_se_contesta_503_dentro_del_tope[checkout_crea_sdk_corta]`, `E   assert 500 == 503`; `1 failed, 7 passed in 15.01s` |
| MP-2, el tope antes del candado (Postgres) | `171313c` con el plazo movido antes del candado | `FALLA | con el candado tomado más que el tope, Mercado Pago sano contesta (sacar): 503 …`, `fallas: 1`; con el arreglo, `fallas: 0` |
| MP-3, los tres puntos | `6b18c47` | `6 failed in 2.61s`: el servidor trabado (`Left contains 45 more items, first extra item: 'payment.get'`: las consultas corrían en el hilo del servidor), el límite (`200 == 429`) y el aviso sin firma en `[con-secreto-dev]`, `[con-secreto-produccion]`, `[sin-secreto-dev]` y `[sin-secreto-produccion]` (el IPN sin firma daba 200) |
| MP-3, la recarga cortada | sabotaje sobre `0fbfaff` | `ROJO  | la recarga con Mercado Pago cortado da 500: dice «FAILED tests/test_cobro_mp3.py::test_la_recarga_con_mercado_pago_cortado_da_503»`. No tiene log propio de rojo antes: el sabotaje devuelve el producto de antes en esa línea. |

### Hallazgos de la autorrevisión

Reproduje cada uno antes de anotarlo.

**Adversario Sonnet, esfuerzo alto, sobre la vuelta de MP-2** (el único de la ronda)

| # | hallazgo | qué hice |
|---|---|---|
| 1, 2 | ver el registro de la ronda | arreglados |
| 3 | un hilo abandonado sigue hasta que corta el SDK; pico de hilos | riesgo, abajo |
| 4 | reactivar depende de leer Mercado Pago | riesgo, abajo |
| 5 | el corte del SDK daba 500 en el checkout | arreglado en `26d06ba`, con su rojo arriba |

**Adversario Opus, esfuerzo alto, sobre MP-3**

| # | severidad | hallazgo | qué hice |
|---|---|---|---|
| 1 | Alta | los IPN se rechazan: sin Webhooks configurados se pierden los pagos | D64 |
| 2 | Alta | el límite cuenta por `X-Forwarded-For` | D66; `52ab1c0` cuenta después de la firma |
| 3 | Media | los 8 hilos se comparten entre el aviso y el checkout | riesgo, abajo |
| 4 | Media | `max_retries` del SDK alargaba la espera | arreglado en `52ab1c0` (`max_retries=1`) |
| 5 | Media | mutantes sin sabotaje | sumé los que faltaban a `cobro_mp3.sh` (13) |
| 6 | Baja | — | ya estaba antes de la pieza |

**`/code-review high`, sobre `4f1822f..ffc386b`**

| # | qué hice |
|---|---|
| 3, 8, 9, 10 | arreglados |
| 1, 2, 4, 6, 7 | riesgos, abajo |
| 5 | supuesto reversible |
| extra: la espera del candado no tiene tope | riesgo, abajo |

**`/code-review high`, sobre `ffc386b..6ecfe06`**

| # | hallazgo | qué hice |
|---|---|---|
| 1 | un caso trabado no se veía: pytest-timeout en modo hilo imprime una línea `+++ Timeout +++` y el guion buscaba «Failed: Timeout» | arreglado en `b7ce3b1`: TRABA mira esa línea o la salida 124 |
| 2 | en la parte de Postgres, el corte de `timeout` (salida 124) no contaba como trabado | arreglado en `b7ce3b1` |
| 3 | la espera del candado no tiene tope | riesgo, abajo |
| 4 | la recarga da 503 a los ~20 s, no a los 15 | riesgo, abajo; `CHANGELOG.md` corregido en `b07acd5` |
| 5 | preapproval huérfana si el checkout pasa el tope | riesgo, abajo |
| 6 | un hilo abandonado suelta su lugar entre los 8: puede haber más de 8 hilos vivos | riesgo, abajo; la línea del `CHANGELOG.md` que decía «hasta 8 hilos» corregida en `b07acd5` |
| 7 | unificar `_aviso_mp_firmado` | descartado: ya es una sola función |
| 8 | espera fija en el escenario 3 de Postgres | queda: retener el candado más que el tope es el escenario |
| 9 | faltaban sabotajes del plazo de reactivar y checkout | sumados en `b7ce3b1` |
| 10 | `--timeout` repetido | sacado en `b7ce3b1` |

**`/security-review`, Sonnet alto, sobre `4f1822f..0fbfaff`:** sin hallazgos de confianza 8 o más; descartó 14 candidatos.

### Riesgos

**Ya aceptados por vos:** los de la entrega anterior siguen igual.

**Nuevos, para que los veas:**

- **Hilos abandonados.** Una consulta que pasa los 15 s contesta 503 y libera su lugar entre los 8, pero el hilo sigue vivo hasta que corta el SDK, unos 20 s. En el peor caso conviven 8 consultas nuevas y las abandonadas que todavía no cortaron, así que con Mercado Pago trabado puede haber más de 8 hilos vivos. No lo medí con carga.
- **La recarga no tiene tope propio.** Su 503 llega cuando corta el SDK, unos 20 s, no a los 15.
- **Los 8 lugares se comparten** entre el aviso de pago, el checkout, la recarga, cancelar, reactivar y sacar. Si Mercado Pago está trabado, un pico de avisos hace esperar al checkout, y al revés.
- **Una preapproval huérfana.** Si el checkout pasa los 15 s mientras Mercado Pago crea la suscripción, CDI contesta 503 pero Mercado Pago puede crearla igual. Esa suscripción no queda anotada en CDI.
- **Un PUT abandonado.** Lo mismo al cancelar: CDI contesta 503 y no cambia nada, pero Mercado Pago puede cancelar igual. Al reintentar, CDI la lee cancelada y sigue.
- **La ventana entre el GET y el PUT** sigue como en la entrega anterior.
- **Reactivar depende de leer Mercado Pago:** si no contesta, 503.
- **La espera del candado no tiene tope.** El tope de 15 s corre desde que se tiene el candado. Si otro pedido del mismo estudio lo retiene, se espera a ese pedido, que a su vez tiene su tope.
- **`fail_after(0)`.** Si el plazo ya venció antes de una consulta, se corta enseguida con 503.
- **La IP del límite** sale de `X-Forwarded-For`. Ver D66.

### Lo que no salió limpio

- **Un sabotaje de MP-2 dio VERDE sobre `b7ce3b1`:** `VERDE | al sacar, la ya cancelada se vuelve a cancelar: la prueba no lo vio`.
  - Causa: el Mercado Pago simulado de `tests/test_cobro_mp2.py` acepta cancelar una suscripción ya cancelada y la deja igual, así que la fila `sacar_con_cancelada` no distinguía si se le pedía cancelar de nuevo.
  - Arreglo, en `cb740f3` (sólo la prueba): la fila cuenta los PUT a la suscripción del miembro; `sacar_con_pendiente` espera 1 y `sacar_con_cancelada`, 0. El producto ya no la cancelaba de nuevo (`main.py:10093`).
  - Sobre `cb740f3`, ese sabotaje da `ROJO  | al sacar, la ya cancelada se vuelve a cancelar: dice «FAILED tests/test_cobro_mp2.py::test_solo_la_duena_o_quien_abrio_la_que_paga_la_tocan[sacar_con_cancelada-duena]»`.
- **Sabotajes de MP-2 y MP-1 sobre `171313c` cortados por el `timeout` general (salida 124).** `correr()` no tenía tope por caso.
  - En MP-2, un caso se colgó en el sabotaje «se saca del estudio a quien tiene la pausada», con la máquina cargada por corridas en paralelo. Corrido solo, ese sabotaje dio `1 failed, 91 passed in 75.12s`, es decir ROJO como corresponde. No identifiqué qué caso se colgó.
  - En MP-1, las corridas sólo iban lentas.
  - `6ecfe06` pone 120 s por caso y cuenta un caso trabado como falla, no como rojo. El código-review encontró que esa cuenta no veía el corte de pytest-timeout; `b7ce3b1` lo arregla. No probé un sabotaje que se trabe de verdad: sólo comprobé que el texto que se busca es el que imprime pytest-timeout.
- **La primera corrida de MP-2 sobre `6ecfe06` se rompió (salida 2)** en `cobro_mp2.sh: line 97: syntax error near unexpected token`. La causa fui yo: edité el guion mientras corría. Después corrí sobre `b7ce3b1` (el VERDE de arriba) y la que vale es la de `cb740f3`.
- **El ROTO de MP-1** («D: cancelar no espera al checkout en curso») lo causó `2c86d9b`, que sumó la línea del plazo donde el sabotaje buscaba su patrón. `5903441` lo arregla. Después del arreglo volví a correr sólo el bloque D, no MP-1 entero (lleva unos 80 min); los otros 144 ROJO son de `6ecfe06`, y desde ahí el producto no cambió. `cb740f3` no toca lo que cubre MP-1.
- **Sabotajes de MP-3 sobre `171313c` con salida 1:** tres patrones ya no encontraban sus líneas. Los corrigió `0fbfaff`, y ahí dieron 13 ROJO.
- **El log `Task was destroyed but it is pending!`** sigue apareciendo en la suite, como en la entrega anterior.

### chequeo-6

```
chequeo-6 4f1822f..6ecfe06: avisos para mirar, no un veredicto
producto +157/−101
  AVISO producto suma 56 líneas netas: el informe dice por qué (§6: más de 20)
arnés +801/−259
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11311 → 11358
  proyecto_maria/services/billing_service.py: 414 → 423
avisos: 1
```

```
chequeo-6 db31e0e..cb740f3: avisos para mirar, no un veredicto
producto +0/−0
arnés +12/−6
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

El porqué del aviso está en «Producto de las dos piezas». El rango entero `4f1822f..cb740f3` mezcla tu limpieza y VALIDACION-1, por eso lo mido en dos tramos.

### Para reproducir

```bash
git checkout cb740f3
# 1. «98 passed»
DATABASE_URL=sqlite+aiosqlite:///./t.db GEMINI_API_KEY=test-key ENVIRONMENT=test python -m pytest -q --no-cov tests/test_cobro_mp2.py tests/test_cobro_mp3.py
# 2. BASE en verde, todo ROJO, «sabotajes con falla: 0»
PY=$(which python) scripts/testing/sabotajes/cobro_mp3.sh cb740f3
# 3. lo mismo; sin Postgres 16, la parte de Postgres da BASE en rojo y cuenta una falla
PY=$(which python) scripts/testing/sabotajes/cobro_mp2.sh cb740f3
# 4. «avisos: 1», el de las 56 netas
python docs/pm/herramientas/chequeo-6.py 4f1822f 6ecfe06
# 5. «avisos: 0», sólo arnés
python docs/pm/herramientas/chequeo-6.py db31e0e cb740f3
```

### Archivos de producto tocados

- `proyecto_maria/main.py`: `cancel_billing`, `reactivate_billing`, `billing_me`, `remove_member`, `billing_checkout`, `billing_topup`, `mercadopago_webhook`, `_verify_mp_webhook_signature`, y las nuevas `_en_hilo_mp`, `_quien_toca_el_plan` y `_aviso_mp_firmado`
- `proyecto_maria/services/billing_service.py`
- `requirements.txt` (`anyio>=4.1.0`)
- `CHANGELOG.md`

---

/compact conservar: Dev 1, rama claude/dev-tecnica. COBRO-MP-2 vuelta y COBRO-MP-3 entregadas en cb740f3 (producto igual a 6ecfe06; informe en el commit de arriba), con D64 y D66. Sigue VALIDACION-1 (producto e4c79a1 y db31e0e, arnés 60023d6 y 0b9d476; falta: suite, compileall, /code-review high, /security-review, chequeo-6, informe); después COBRO-MP-3 si vuelve, AISLAMIENTO-2 / LIMPIEZA-1 → BACKUP-1a → EXCEL-2c. Nada se publica sin el «dale» de Emi; nunca main.
