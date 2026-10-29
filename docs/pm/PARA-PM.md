# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## COBRO-MP-1, vuelta 2: entregada en `999b27a` (informe en el commit de arriba)

**Resultado.** Están a, b, d, e, f y g de tu devolución del 2026-10-29
01:41 UTC, cada una con su rojo antes y sus sabotajes. La c no la
implementé: con lo que hoy consulta el código no se distinguen los casos de
tu regla, así que va como **D13**, como pediste («D11 antes de inventar»;
D11 y D12 ya eran de ORDEN-1).

**Una puerta en rojo:** los sabotajes terminan en «sabotajes con falla: 2».
Los dos son defectos de la prueba, no del producto: un texto esperado mal
elegido y una carrera que en 2 de 6 corridas (la del lote y 1 de 5 a mano)
no mide la clave de D31. No los arreglé (pediste el informe sin código
nuevo): van como **D14**.

Lo que decidís vos: **D13** y **D14**. D11 y D12 de ORDEN-1 ya las contestaste
(`PARA-DEV.md`, ORDEN-1b): las atiendo en ORDEN-1b, que va en commits
aparte, después de este informe.

| Qué | SHA |
|---|---|
| Base: merge de tu rama (veredicto `2e1a855`) | `8e6a993` |
| Pruebas: casos de a, b, d, e, f y g, en rojo | `9a16147` |
| Producto: a, b, f y g | `3919cf5` |
| Pruebas: sabotajes de la vuelta 2 y D31 en Postgres | `b3f5edb` |
| Pruebas: un dato que no entra en su columna de Postgres, nueve casos en rojo | `5289dc6` |
| Producto: lo leído se guarda aunque no entre en su columna; el tope en un solo lugar | `26c12ed` |
| Producto: sin caminos que ningún dato recorre | `3c7f1e1` |
| Pruebas: el cobro sin suscripción legible se rechaza por eso y no por el monto | `a4a67ec` |
| Producto: sale el control del id de pago booleano | `1ba3f7e` |
| Pruebas: sabotajes del tope y de Postgres | `dbac021` |
| Pruebas: id de suscripción que no es un id, en rojo | `e9fd805` |
| Producto: el id de suscripción se valida antes de pedirlo (`/code-review high`, hallazgo 5) | `ad46a16` |
| Pruebas: la renovación sin referencia, en rojo sobre `e9fd805` | `bec9a8c` |
| Pruebas: sabotajes de la validación de ids | `999b27a` |
| Informe | este commit |

## Decisiones

**D13. Volver de Mercado Pago antes del aviso y tocar otra vez «Activar
plan» (causa c).**

Tu regla pide distinguir, para una suscripción vieja `authorized`:

- tiene un cobro aprobado que CDI no aplicó, o todavía no tuvo su primer
  cobro → 409 «Tu pago se está confirmando; probá en unos minutos»;
- su último cobro falló → se cancela como ahora.

El checkout (`main.py:10945-10973`) lee de la suscripción vieja sólo su
`status` (`_leer_suscripcion_mp`). Con eso no se distinguen los tres
casos: los tres dicen `authorized`. Para distinguirlos hay que leer algo
que el código hoy no consulta y que nunca verificamos contra Mercado Pago
real:

- (a) El bloque `summarized` de la suscripción (`charged_quantity`,
  `last_charged_date`, `semaphore`). Está en la documentación, sin
  verificar, igual que lo de D30.
- (b) Buscar los cobros de la suscripción
  (`/authorized_payments/search?preapproval_id=…`) y mirar el último.
  También sin verificar.
- (c) Con lo ya verificado: si la vieja está `authorized` y la cuenta no
  está vigente, 409 siempre, con un texto que ofrezca la salida: «Tu
  suscripción en Mercado Pago sigue activa. Si acabás de pagar, esperá
  unos minutos; si querés cambiar la tarjeta, cancelá el plan primero.»
  «Cancelar plan» ya cancela la suscripción en Mercado Pago.
- (d) Dejarlo como está: el riesgo de la c sigue abierto.

Recomiendo **(c)**. Usa sólo lo que ya se lee. Si se equivoca, el cliente
queda trabado unos minutos con una salida a la vista, en vez de perder
callado una suscripción que ya cobró. Lo que cambia contra tu regla: el
caso de la tarjeta que no pasa (D7.2) ya no se resuelve solo; el cliente
cancela y vuelve a activar, un paso más. (a) y (b) dependen de campos sin
verificar: si Mercado Pago no los trae, la decisión cae en el lado
equivocado sin que nadie lo vea. Si elegís (a) o (b), antes hace falta
una lectura contra Mercado Pago real, que yo no puedo hacer.

**D14. Los dos sabotajes que no dan su rojo.**

1. «g: un id largo de la exportación no se reconoce»
   (`cobro_mp1.sh:406-409`). Da rojo por el motivo correcto: «E
   AssertionError: guardar la exportación de id largo cuenta otra vez»
   (`tests/test_cobro_corte1.py:580`). El script espera el texto del
   assert anterior (línea 577), que con este sabotaje pasa: volver a
   exportar no depende de reconocer el nombre. Arreglo: cambiar el texto
   esperado, una línea.
2. «D31: sin candado y la clave repetida se da por guardada»
   (`cobro_mp1.sh:492-497`). En el lote dio rojo sin «FALLA | el mismo
   pago dos veces a la vez: uno aplicado y otro salteado». Esa salida no
   quedó guardada: el script sólo copia líneas de pytest. A mano, con el
   mismo sabotaje sobre `999b27a`, 4 de 5 corridas dan el rojo esperado y
   1 da `OK … ([200, 200], ['payment_id ya procesado', None])`. La barrera
   de `scripts/testing/cobro_mp1_postgres.py:121-145` suelta al primero
   apenas leyó la cuenta, y a veces el primero guarda antes de que el
   segundo registre el pago: el segundo lo ve en la consulta previa y no
   llega a la clave. El producto queda bien en las dos ramas. Lo que pasa
   es que la prueba no siempre mide la clave. Arreglo: que la barrera
   cruce a los dos después de esa consulta y antes de
   `_registrar_pago_mp`, y que el script muestre las líneas «FALLA» de
   las pruebas de Postgres.

Opciones:

- (a) Los arreglo en un commit de pruebas aparte, encima de este informe
  y antes de ORDEN-1b, y vuelvo a correr el script de sabotajes completo.
- (b) Van en la próxima vuelta de COBRO-MP-1, junto con lo que digas de
  D13.

Recomiendo **(a)**. Mientras no esté, el comando 3 de abajo da rojo.
Además, D31 queda medido sólo a veces. Mientras decidís, sigo con
ORDEN-1b.

## Qué cambió, por causa

**a. Dos pagos distintos de la misma cuenta a la vez.** El aviso toma la
cuenta (`User` u `Organization`) con `with_for_update`. Rojo sobre
`8e6a993` en `cobro_mp1_postgres.py`, PG16: «fallas: 4», las cuatro de a
(dos recargas y dos planes a la vez, de usuario y de organización, suman
uno). Verde: «fallas: 0». Sabotaje: sin el candado, el script vuelve a
rojo. `cobro_mp1d_postgres.py` sigue en verde.

**b. Una regla para lo que se lee de Mercado Pago.**

- No se pudo leer (excepción del SDK, cualquier status distinto de 200,
  sin id de pago, la renovación que todavía no dice qué pago fue): 503 y
  una línea de log (`_consultar_mp`, `_MPIlegible`).
- Se leyó y no sirve (referencia desconocida, cuenta que no existe, cobro
  sin suscripción, id de suscripción que no es un id, campos en `null` o
  de otro tipo, monto, moneda, fecha): fila `rechazado` con su motivo y
  200.
- Un dato secundario en `null` (`payer`, `card`) no frena un pago bueno:
  se aplica.
- Lo leído que no entra en su columna de Postgres (largo, NUL, surrogate
  suelto) se recorta o se reemplaza (`_guardable_en_pg`): antes daba 500.
- Los ids de suscripción que trae el cobro, la metadata, el pago o la
  transacción se validan con la misma forma que los de cobro y pago
  (`_id_mp`) antes de armar la URL de Mercado Pago.
- El usuario `org` paga su plan.

Rojos:
- `9a16147` sobre `8e6a993`: «60 failed, 156 passed» en los 4 archivos
  (a, b, e, f y g juntos).
- `5289dc6`: «FALLA | un pago a una cuenta que no existe, con la
  referencia larga queda rechazado (500, [])» y, arreglado ese, ocho más
  del tipo «FALLA | un pago con la marca larga queda aplicado (500, [])»
  («fallas: 8»).
- `a4a67ec`: el caso del cobro sin suscripción legible lo frenaba el
  monto; con el control sacado, «assert 'active' == 'past_due'».
- `e9fd805`: «assert 503 == 200» en los seis casos del id de suscripción.
- `bec9a8c` sobre `e9fd805`: «assert 503 == 200» en `[con_ruta]`.

**c.** D13, sin cambio.

**d. D31 en Postgres.** `cobro_mp1_postgres.py` pone `date_approved` y
vuelve a probar el mismo pago dos veces a la vez. Entra a
`cobro_mp1.sh`: sin el candado y con la clave repetida dada por guardada,
queda rojo.

**e. Los mutantes vivos.** Cada uno tiene su caso
(`tests/test_cobro_mp1_vuelta2.py`) y su sabotaje:
- sin la fila `InicioRegistroPagosMP`, no se aplica nada (503);
- el corte del registro no tiene margen;
- pagar de más se aplica;
- `past_due` con fin por delante suma desde hoy;
- el registro de un pago de organización lleva `org:`;
- el panel muestra los últimos 200 rechazados, del más nuevo al más viejo;
- el panel nombra todos los motivos.

**f. La recarga con el tope de 100.** El tope está en un solo lugar
(`billing_service.recarga_entra`). Con el tope lleno, `/api/billing/topup`
contesta 409 con la razón y la pantalla la muestra. Un pago de recarga que
no entra queda `rechazado` y no suma: lo ve Emi en el panel. Con los
extras vencidos se puede recargar.

**g. Ids de exportación y panel.**
- La exportación se llama `MARIA-EXPORT_<id>.TXT`: no choca con una
  importación de `EXPORT_<id>` y un id de 44 a 50 caracteres cuenta una
  vez.
- La pantalla v1 genera primero y guarda el historial con el archivo
  devuelto: cuenta una sola operación. Rojo en
  `pantalla_cobro_mp1_v2.js`: «guardar GROUPED_… → generar».
- El texto del panel de rechazados nombra la fecha.

## Riesgos

Ninguno lo arreglé: o está fuera de la tarea o el arreglo cuesta más que lo
que evita. Severidad entre paréntesis.

- **Exportaciones viejas (baja, transitoria).** Una operación guardada
  como `MARIA_EXPORT_<x>.TXT` antes del cambio de nombre no se reconoce:
  regenerar esa exportación cuenta una operación más, una vez.
- **Lo permanente reintenta (media).** Un pago aprobado sin id, un cobro
  sin pago y un 404 de Mercado Pago dan 503: es tu regla b («no se pudo
  leer»), pero Mercado Pago reintenta hasta rendirse y Emi no ve fila en
  el panel, sólo el log. Incluye un `preapproval_id` de la metadata que
  Mercado Pago no encuentra.
- **`metadata.preapproval_id` no se usa si el cobro no trae el suyo
  (media, D30).** Una renovación cuyo cobro no dice de qué suscripción es
  queda rechazada, aunque el pago traiga el id en la metadata. Depende de
  la forma real del cobro, que no verificamos.
- **Links de recarga de más (baja a media).** El tope se mira al armar
  el link, no se reserva. El adversario armó 12 links desde 0 extras y
  los pagó: 10 `aplicado`, 2 `rechazado`, la cuenta en 100. El tope no se
  pasa, pero el cliente pagó dos y Emi devuelve a mano.
- **La suscripción se pide dos veces (baja).** En una renovación sin
  referencia, el aviso lee la suscripción para la referencia y otra vez
  en el control del monto, con llamadas que bloquean.
- **`recarga_entra` vence extras (baja).** Llama a `_expire_extra_ops`,
  que modifica la cuenta. En el webhook el vencimiento se guarda aunque la
  recarga se rechace; en `billing_topup` depende de otro commit.
- **Una organización huérfana en `billing_topup` (baja).** Si la cuenta
  dice `organization_id` y la organización no existe, la recarga va al
  usuario, como el resto de `_get_billing_entity`.
- **La pantalla v1 sigue con `GROUPED_` (baja).** El guardado del Excel
  agrupado de v1 no cambió de nombre: no choca con `MARIA-EXPORT_`.
- **La cuenta inexistente ahora da 200 (cambio de contrato).** Antes
  daba 400; ahora queda `rechazado` con 200, según la regla b.
- **Un id mal formado que se leyó reintenta (media).** Lo encontró el
  segundo adversario: un `payment.id` del cobro o un `id` del pago que no
  es un id da 503 sin fila, y Mercado Pago reintenta. Sin id no hay clave
  para la fila; se podría registrar el rechazo con el id del cobro. Con ids
  reales casi no pasa. Si lo querés distinto, decímelo y va con su rojo.
- **`_id_mp` acepta `0`, `-` y negativos (baja).** Se piden a Mercado
  Pago y dan 503 si no existen.
- **El webhook con un cuerpo que no es un objeto da 500 (baja, previo).**
  `_verify_mp_webhook_signature` hace `body.get("data", {}).get(...)`.
- **El botón de recarga sigue visible con el tope lleno (baja).** El 409
  aparece al tocarlo, con la razón.
- **El aviso devuelve sin commit con el candado tomado (baja, previo).**
  La sesión lo suelta al cerrarse; no lo medí.
- **Los que pediste:** una recarga revive extras vencidos; cancelar
  mientras llega el primer pago deja la cuenta con su mes y sin
  suscripción; `_pago_un_plan_mp` con una prueba que sólo recargó. Sin
  cambio.

## Hallazgos de la revisión

| Fuente | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| Adversario sobre `b3f5edb` | Sonnet, alto | 1. Un dato largo, con NUL o surrogate da 500 en Postgres | Arreglado: rojo `5289dc6`, arreglo `26c12ed` |
| | | 2. `transaction_amount = 10**5000` da 500 | Descartado: el JSON de Mercado Pago no puede traer un entero así; `json.loads` lo rechaza («Exceeds the limit (4300 digits)») |
| | | 3. Links de recarga de más | Riesgo |
| | | 4. Exportaciones viejas | Riesgo |
| | | 5. Un 404 da 503 | Riesgo (regla b) |
| | | 6. `return` con el candado tomado | Riesgo, previo |
| `/security-review` sobre `8e6a993..dbac021` | Sonnet | Sin hallazgos con confianza ≥ 7 | — |
| `/code-review high` sobre `8e6a993..dbac021` | Opus, alto | 1. Exportaciones viejas | Riesgo |
| | | 2. Lo permanente reintenta | Riesgo |
| | | 3. `metadata.preapproval_id` (D30) | Riesgo |
| | | 4. El guardado del historial antes de los avisos | Descartado: `saveOperationToHistory` atrapa el error del `fetch`, y los ítems son los mismos que el servidor acaba de aceptar para generar |
| | | 5. Id de suscripción sin validar en la URL | Arreglado: rojo `e9fd805` y `bec9a8c`, arreglo `ad46a16` |
| | | 6. La suscripción se pide dos veces | Riesgo |
| | | 7. Links de recarga de más | Riesgo |
| | | 8. `recarga_entra` vence extras | Riesgo |
| | | 9. Sale el `min(…, 100)` al aplicar | Descartado: el único que suma extras es la recarga, y `recarga_entra` la rechaza antes; el borde de 100 tiene sabotaje |
| Adversario sobre `5289dc6..999b27a` | Sonnet, alto | 1. Un id de pago mal formado en el cobro (`"../x"`, `"12 34"`, `1.5`, una lista, 65 caracteres) da 503 siempre, sin fila; igual un `pay_resp.id` que no sirve | Riesgo, dentro de «Lo permanente reintenta»: es el mismo 503 que ya fija `test_un_pago_aprobado_sin_id_reconocible_reintenta`, sin código nuevo por tu decisión |
| | | 2. `_id_mp(0)` da `"0"`, y `"-"` o un negativo pasan: se piden a Mercado Pago y dan 503 si no los conoce | Riesgo (baja): la ruta no sale de su segmento; los ids reales pasan y los mal formados se rechazan |
| | | 3. `POST /api/payments/webhook` con firma y cuerpo `[]` o `{"data": 5}` da 500 en vez de 401 | Riesgo (baja), previo a la vuelta: no cobra nada |
| | | 4. Sin sabotaje propio para un `billing_topup` que lea los extras sin `recarga_entra` | Descartado: el endpoint llama al helper (dos sabotajes en el endpoint, uno en el helper); es un mutante de otra implementación |
| | | Lo que no rompió: ningún id llegó al SDK sin pasar por `_id_mp` (espía sobre `_Pagos.get` y `_Suscripciones.get`); ninguna suscripción de otra cuenta se aplicó; 17 sabotajes de ids, `recarga_entra` y renovación en rojo | — |

## Archivos de producto tocados

`proyecto_maria/main.py`, `proyecto_maria/services/billing_service.py`,
`proyecto_maria/static/app.js`, `proyecto_maria/static/v2/screens/profile.js`,
`proyecto_maria/templates/dev_dashboard.html` y `CHANGELOG.md`.

## Puertas, sobre `999b27a`

| Puerta | Salida |
|---|---|
| Suite completa (SQLite, worktree limpio) | `==== 4345 passed, 121 skipped, 3 xfailed, 101 warnings in 607.31s (0:10:07) ====` |
| Pruebas de cobro (13 archivos) | `================= 359 passed, 4 warnings in 123.89s (0:02:03) ==================`, salida 0 |
| `cobro_mp1_postgres.py` en PG16 | 29 líneas `OK`, `fallas: 0`, salida 0 |
| `cobro_mp1d_postgres.py` en PG16 | 14 líneas `OK`, `fallas: 0`, salida 0 |
| `scripts/testing/sabotajes/cobro_mp1.sh` | **rojo:** `sabotajes con falla: 2`, salida 1. 106 `ROJO`, 2 `ROJO?` (D14) y el `VERDE` de control esperado («sin mirar antes de insertar: sigue en verde, como tiene que ser») |
| `/code-review high` | 9 hallazgos, tabla de arriba, sobre `dbac021`; el 5 arreglado |
| `/security-review` | sin hallazgos ≥ 7, sobre `dbac021` |

**No corrí:** smoke y ataque de aislamiento (no toca sesión ni
permisos); `/code-review high` y `/security-review` de nuevo sobre
`ad46a16..999b27a`, que es el arreglo del hallazgo 5 y sus pruebas; ese
tramo lo revisó el segundo adversario.

**Incidente de entorno:** la primera corrida de los sabotajes se cortó
porque el adversario borró su worktree temporal (`/tmp/tmp.…/wt`), al
tomarlo por suyo; lo confirmó él. No es un rojo del producto. La relancé
con `TMPDIR` en mi carpeta de trabajo y otro puerto, sobre el mismo
`999b27a`; la de la tabla es esa. Las pruebas de cobro que había corrido
antes (351 passed) eran anteriores a `ad46a16` y no cuentan: las de la
tabla son sobre `999b27a`.

## Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout --detach origin/claude/dev-tecnica
E="GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares"
# 1. Los casos de la vuelta: tiene que dar «N passed», 0 failed
env $E python -m pytest -q --no-cov tests/test_cobro_mp1_vuelta2.py tests/test_cobro_mp1.py tests/test_cobro_corte1.py tests/test_prelaunch_block2.py | grep -E 'passed|failed'
# 2. Postgres: tiene que terminar en «fallas: 0»
PY=python scripts/testing/con_pg16.sh bash -c 'python scripts/testing/cobro_mp1_postgres.py "$BACKUP1A_PG_URL"'
# 3. Sabotajes: hoy da las dos líneas ROJO? de D14 y «sabotajes con falla: 2» (la de D31, a veces no); ninguna ROTO, ROJO! ni «la prueba no lo vio»
PY=python PUERTO=8854 bash scripts/testing/sabotajes/cobro_mp1.sh 999b27a | grep -E '^(ROTO|ROJO[?!])|no lo vio|sabotajes con falla'
```

/compact conservar: Dev 1, rama claude/dev-tecnica. COBRO-MP-1 vuelta 2
entregada en 999b27a (informe en el commit de arriba): espera veredicto con
D13 (c del checkout, recomiendo c) y D14 (los dos sabotajes en rojo
dudoso, recomiendo a). En curso ORDEN-1b (PARA-DEV.md, D11 y
D12), en commits aparte. Después CORTE-1, MP-2 (suma la cancelación de
organizaciones), AIS2, LIM, BACKUP-1a y EXCEL-2c. Nada se publica sin el
«dale» de Emi; nunca main.
