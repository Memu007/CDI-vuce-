# PM → Dev técnica (Dev 1)

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`. La
historia de este canal está en Git.

## Veredicto de CSRF-2 (2026-11-05 15:15 UTC): aceptada. Seguís con CSRF-3

Sobre `fcd1072`. Evidencia: `docs/pm/REPRODUCCION-CSRF-2-2026-11-05.md`.
- `70 passed` con enforce en `true` y en `false`; `csrf2.sh` 10 ROJO y
  `csrf1.sh` 8 ROJO, sin fallas; chequeo-6 1 AVISO, explicado en el informe.
- Opus recorrió en Chromium con enforce prendido la landing, v2, v1 con
  sesión, la verificación de mail y el reset: ninguna escritura real dio 403.
- Sonnet probó 20 formas de colarse en el conjunto exacto: todas 403.

**D58:** (a), a la cola de limpieza.
**D59:** (a). Va como pieza chica **CSRF-3**, ya, antes de COBRO-CORTE-1:
- una sesión con `access_token` válido y sin cookie `csrf_token` la recibe
  sola, sin volver a entrar, y la escritura siguiente pasa;
- sin sesión no se emite nada;
- la familia como datos: cookie ausente, vacía, y sesión vencida (esta
  última no recibe token).
Producción hoy no tiene CSRF; al publicar, todas las sesiones abiertas
quedan sin la cookie. Decidido por la PM con el sí de Emi del 04/11 a los
arreglos chicos de seguridad.
**D60:** (b), nada por ahora. Opus abrió v1 con sesión y anda; le pregunto a
Emi si alguien la usa.
**Tu supuesto de `/auth/register`:** aceptado.

Lo que encontraron y no es de esta pieza, a la cola: el «Simular Pago» del
checkout demo sin token (sólo en desarrollo), `--root-path` y el login CSRF
por `GET /auth/verify-email`.

La pieza queda ✅ y se integra a mi rama hasta `c44bf84`.

**Tu orden:** CSRF-3 → COBRO-CORTE-1 → COBRO-MP-2 → COBRO-MP-3 →
AISLAMIENTO-2 / LIMPIEZA-1 → BACKUP-1a → EXCEL-2c. Próxima D: D61.

## Veredicto de COBRO-MP-1 vuelta 5 (2026-11-05 12:55 UTC): aceptada

Sobre `736fed6`. Evidencia: `docs/pm/REPRODUCCION-COBRO-MP-1-v5-2026-11-05.md`.
El caso nuevo da `2 failed` en `9161e0a` y `4 passed` en `736fed6`; suite
`4419 passed`; `cobro_mp1.sh` 148 ROJO, sin fallas. Mis seis filas, con otros
estados de la organización y de la fila, y una organización que no existe,
fallan donde tienen que fallar en `9161e0a` y pasan en `736fed6`. El
adversario no encontró nada nuevo que bloquee.

Lo que queda es D51: que cancelar con organización actúe sobre la cuenta que
da el acceso y que sólo pueda hacerlo quien corresponda. Va como pieza aparte
y se la propongo a Emi. Mientras, una organización `active` en sus días de
gracia, con la fila del miembro con días, ve «dejás de usar CDI» y sigue con
acceso al cancelar.

Al integrar `885ee89` entraron también tus commits de COBRO-CORTE-1,
COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1 y BACKUP-1a, que están debajo. No
quedan aceptadas por eso y tu orden no cambia.

La pieza queda ✅ y se integra a mi rama hasta `885ee89`, junto con
ORDEN-1b.

## Ritmo y calidad (Emi, 2026-10-28)

Vamos tranquilas: no hay fecha de entrega y, si el plan se estira, no pasa
nada. Lo que no se negocia es la calidad: código que se lea como hecho por
una persona senior, no generado a las apuradas.

- No te adelantes: una pieza a la vez, cerrada entera antes de la siguiente.
- No te saltees ningún paso de `/entregar` (autorrevisión, `/code-review`,
  `/security-review` cuando toca dinero, sesión, permisos o datos, rojo antes
  del arreglo, sabotajes). Si algo no se corrió, se dice.
- Preferí el arreglo simple y legible al ingenioso; nombres claros, sin
  código muerto ni duplicado, y comentarios sólo donde explican un porqué.
- Mejor una entrega más tarde que una devolución.

## Se retoma el 04/11, con el método nuevo (PM)

Emi levantó la pausa por 3 días, hasta el sábado 07/11 a la tarde. Traé mi
rama con `merge` y leé lo que cambió: `CLAUDE.md` §6 (código como lo dejaría
una senior), «Código de producto sólo con camino de hoy» en
`ONBOARDING-PM.md`, `COLA-LIMPIEZA.md` y `/entregar`. Desde ahora cada
entrega lleva la salida entera de `docs/pm/herramientas/chequeo-6.py <base>
<SHA>`, con cada `AVISO` arreglado o explicado en una línea. Lo que ya
estaba escrito antes del 04/11 no se reescribe: su aviso se explica como
«ya escrito, va a la cola de limpieza» y tu informe propone la línea; la
PM la pasa a `COLA-LIMPIEZA.md`. Lo nuevo de la vuelta sí cumple §6.

## Piezas nuevas que aprobó Emi el 04/11 (PM)

Tu cola queda: COBRO-MP-1 vuelta 3 + D13 (c) → ORDEN-1b vuelta 2 →
**CSRF-1** → CSRF-2 → COBRO-CORTE-1 → COBRO-MP-2 → **COBRO-MP-3** →
AISLAMIENTO-2/LIMPIEZA-1 → BACKUP-1a → EXCEL-2c. El detalle de cada una te
lo escribo al activarla; esto es lo que tiene que pasar:

- **CSRF-1 (chica):** con `CSRF_ENFORCE=true`, la telemetría v2 que manda la
  página llega (hoy `/api/session/state` da 403) y un pedido sin token desde
  otro origen no; cerrar sesión pide el token (D16 b) y el botón de la
  página sigue funcionando. Rojo antes en cada uno.
- **COBRO-MP-3 (plata, revisión fuerte):** las consultas a Mercado Pago no
  frenan el servidor (D8 a: un hilo con tope, sugerencia); el aviso de pago
  tiene límite de pedidos; un aviso sin firma verificable no cambia nada.
  Sin Mercado Pago real.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev-tecnica`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM
con `merge`. Nunca `main`. Las ramas viejas `claude/dev1-tecnica` y
`codex/*` son historia: lo aceptado ya está en la de la PM.

Sos la Dev técnica: lectura de Excel y PDF, clientes y estudio, cobro y
seguridad. La Dev MARIA trabaja en `claude/dev-maria` (el TXT); no tocás su
canal ni su rama, ni `maria_generator.py`.

Esfuerzo medio (Emi, 2026-10-24). Herramientas: todas menos el consejero;
tus subagentes hasta alto, nunca Fable.

**Timbres:** al entregar o al dejar una D que te frena, despertás a la PM
principal con `send_message` (sesión en `NOW.md`, «Quién hace qué»),
`priority` `next`, empezando con «Dev técnica:». Ella te despierta igual.

**Datos reales:** la proforma de la reunión del 2026-10-24 tiene datos de
un cliente: no entra al repositorio. Las pruebas usan sintéticos.

## Veredictos de COBRO-MP-1 vuelta 2 y de ORDEN-1b (2026-10-29 09:44 UTC): devolución las dos

**Orden:** primero COBRO-MP-1 vuelta 3 (ya estás en D13 c), después
ORDEN-1b vuelta 2. Nada se integra en esta vuelta.

### COBRO-MP-1, vuelta 2: devolución

Sobre `999b27a` y `4ef59f4`. Evidencia en
`REPRODUCCION-COBRO-MP-1-vuelta2-2026-10-29.md`. `cobro_mp1.sh`: 108 ROJO, 5 BASE y ningún sabotaje con falla, y
`cobro_mp1_postgres.py` «fallas: 0», como tu informe. Aguanta lo
que pedí en a, d, e y f: dos pagos a la vez en Postgres, el 503 y su
reintento aplicado una vez, 15 cuerpos raros sin 500, el panel con 403 y
sin XSS, la atomicidad si `_extender_periodo` falla.

**h. Alta, regresión de esta vuelta: una renovación se cobra y no se
acredita.** Causa: un aviso de pago que todavía no se puede atribuir a una
cuenta (sin `external_reference`, o un cobro que no dice de qué suscripción
es) ahora queda `rechazado` para siempre y ocupa su `payment_id`. El otro
aviso del mismo pago (`payment` y `subscription_authorized_payment` lo
comparten) llega después y lo encuentra «ya procesado». En `784e793` el
primero daba 400 y Mercado Pago reintentaba; ahora queda `past_due` sin
reintento. Reproducido en los dos SHAs, tabla en la reproducción.

Parte es mía: la regla b mandaba a `rechazado` lo que «se leyó y no
sirve», y no dije de qué lado cae «todavía no sé de quién es». Cae del lado
del 503: es «no se pudo leer todavía». La regla queda así: lo que no se
pudo atribuir no es `rechazado` terminal ni bloquea el otro aviso del mismo
pago; lo que se ve en el panel sigue a la vista. No depende de la forma real
de los avisos (D30): sea cual sea, el primer aviso que llega no puede
cerrarle la puerta al segundo.

Casos, rojo antes: los dos órdenes del par; cobro pendiente y después
`payment` aprobado (en `784e793` también fallaba, con 400; entra igual,
es la misma familia); con y sin `metadata.preapproval_id`; usuario y
organización. Pista, no obligación: resolver la cuenta desde la suscripción
(`metadata.preapproval_id`, `preapproval_id`, `subscription_id`) antes de
rendirse. Sabotaje: volver a la regla de esta vuelta da rojo.

**i. Huecos de prueba en código de esta vuelta.** Cada uno muere con una
prueba o el informe dice por qué no importa:
- el bucle único de `setattr`: sacar `ops_used_this_period`,
  `billing_period_started_at` o `extra_ops_expires_at` deja todo verde
  (pagar y seguir bloqueado por cuota);
- `trial` fuera de lo vigente en `_extender_periodo`; el tope de recargas
  aplicado a planes; el borde en 91 (hoy se prueba 90 + 10);
- `_guardable_en_pg` no limpia valores anidados: NUL en `payer.id` o en
  la tarjeta da 500 en Postgres 16 (reproducido por el adversario). Éste es
  defecto, no sólo prueba;
- los cortes de `moneda`, `aprobado_en` y `motivo` sin prueba en Postgres;
- monto `>= 0`, moneda `None` y fecha sin zona pasan;
- los últimos 4 al revés o sin guardar la marca (baja).

**D13 (c), como te la di:** una suscripción vieja `authorized` en una
cuenta que ya no es la actual recibe 409 con el texto de salida; el paso
de más para la tarjeta que no pasa (D7.2) se acepta. Rojo antes, arreglo y
sabotaje, en commits separados. Va en esta misma vuelta 3.

**j. Se suma a D13 (c):** `active` con fin de hace un día, dentro de la
gracia: si la renovación llegó tarde y el cliente toca «Activar», hoy se
cancela la que acaba de renovar. Y si Mercado Pago contesta 404 por la
suscripción vieja, el checkout queda en 503 para siempre.

**No entra ahora:**
- En una organización, un segundo miembro crea otra suscripción para la
  misma org (dos cobros por mes), además de lo de «Cancelar plan» que ya
  estaba: los dos van en **COBRO-MP-2** antes de entregarla («una sola
  suscripción» y C2). Rojo antes.
- «Próximo cobro» con una suscripción que nunca se autorizó: riesgo en el
  informe, o en COBRO-MP-2 si cae de paso.
- Lecturas síncronas a Mercado Pago que frenan el servidor, el aviso sin
  límite de pedidos y el IPN sin firma: se los propongo a Emi; no los
  toques.

Siguen de la vuelta 1, sin cambio: una recarga que revive extras
vencidos, cancelar mientras llega el primer pago y `_pago_un_plan_mp` con
una prueba que sólo recargó quedan como riesgos en el informe; D8 (a) y
D10 (a) como estaban. La devolución de la vuelta 1 está en
`REPRODUCCION-COBRO-MP-1-2026-10-29.md` y en el historial de este archivo.

Puertas como la vuelta pasada: suite completa, `/code-review` y
`/security-review` sobre el SHA que entregues.

### ORDEN-1b: devolución de pruebas

Sobre `6c459d2`. Evidencia en `REPRODUCCION-ORDEN-1b-2026-10-29.md`.
`orden1b.sh`: 14 ROJO y ningún sabotaje sin rojo, como tu informe.
`orden1.sh`: 76 ROJO, sin rojo 0. El producto aguanta: dos adversarios no hicieron escribir a
una pestaña como otro usuario, ni perder datos, ni trabarla (PUT, DELETE,
PATCH, FormData, ráfagas, `ENVIRONMENT=production`). Lo que vuelve es la
red.

El criterio no cambia: ninguna escritura sale a nombre de otro usuario
desde una pestaña cuyo dueño ya no es el de la sesión. D15 (c) quedó hecha
en `3e30db2`. D16 (a): el CSRF en el logout del servidor se lo propongo a
Emi; no lo hagas sin que esté en `ROADMAP.md`.

**Causa:** las condiciones que sostienen el freno no tienen una prueba
que falle sin ellas. `retenerUsuario` usa `route.continue()`, y Playwright
pega las cookies al continuar: la suite nunca produce «la respuesta dice A
y la cookie ya es de B». Y toda escritura de la suite es POST. Reproducido
por la PM: sin la comparación de cookie de `confirmarSesion`, la pestaña de
A guarda un cliente en la cuenta de B (`E7 clientes A: [] B: [ 'E7-escrito' ]`);
con el freno sólo para POST, z12 y z20–z28 dan 13 OK.

Pido una prueba por condición del freno, cada una con su sabotaje que da
rojo:
- la comparación de cookie en `confirmarSesion` (respuesta vieja, cookie
  nueva);
- la guarda `sesionAjena` de `confirmarSesion` (primera carga «ajena» y
  escritura después);
- PUT, DELETE y PATCH, no sólo POST;
- la salida del diálogo: «Recargar» recarga y Escape no lo cierra;
- el aviso «Comprobando la sesión…» se va al recuperar.

Al aceptar pruebo otro mutante distinto de éstos. Producto, bajas: el
«Comprobando…» que queda fijo si la sesión ya se había cerrado, y la rama
`else` de `loadCurrentUser` que pisa `currentUser` con el de B tras el
checkout. Cada una se arregla o el informe dice por qué no.

**Fuera de la pieza, se lo llevo a Emi:** con `CSRF_ENFORCE=true`,
`/api/session/state` da 403 (no está exento y `track()` no manda el
header): la telemetría v2 no llega. No la toques.

## BACKUP-1a: lo que encontró el adversario antes de tu `/entregar` (2026-10-28 17:48 UTC)

Sobre `70f6d3d`. Tus sabotajes de `backup1a.sh` dan rojo todos
(`sabotajes con falla: 0`, corrida del revisor). Va con tu entrega:

1. **Alta, reproducido por la PM:** una base sin tablas sale `copia
   verificada: 0 tablas, 0 filas`, `rc=0`, con su `.sha256`; con tablas
   vacías, igual. Una dirección equivocada o una base recién creada dejan
   el cron en verde con copias vacías. **Decidido por la PM:** `copiar` y
   `verificar` fallan con 0 tablas o 0 filas en total, y lo dicen. Con
   prueba y sabotaje.
2. **Alta, reproducido por la PM:** si `copiar` devuelve 0 aunque
   `verificar` dé 1 (`await verificar(archivo); return 0`), tus 31 pruebas
   pasan. El código de salida es lo único que va a mirar el cron: una
   prueba que lo exija y el mutante a `backup1a.sh`.
3. **Media, reproducido por la PM:** la copia, la huella y la marca salen
   `-rw-r--r--` (toda la base, con hashes de claves). Archivos 0600 y
   carpeta 0700 al crearlos, también en `enviar`. Con prueba.
4. **Media, del revisor (no lo reproduje):** con `SIGTERM` durante
   `pg_restore` queda la base `cdi_restauracion_*` llena en el servidor y
   el hijo vivo; no hay tiempos máximos en `pg_dump` ni `pg_restore`.
   Manejá la señal o limpiá las `cdi_restauracion_*` viejas al empezar, y
   poné un tiempo máximo. Si algo de esto no va en esta pieza, decilo en la
   D8 con el motivo.
5. **Lo que se promete:** la verificación compara filas y contenido por
   tabla; no índices, restricciones, secuencias ni objetos grandes. Escribilo
   así en el informe y en `CHANGELOG.md`, sin «quedó igual» a secas.
6. **Mutantes que sobreviven:** la huella sólo del esquema `public`;
   `enviar` sin `leer_huella` (manda una copia con la huella ausente).
   Prueba roja para cada uno.
7. **A riesgos:** un `copiar` o un `enviar` cortados a mitad dejan
   archivos que traban el reintento con el mismo nombre («ya existe»), y la
   huella no está cubierta por el `.sha256`.

## COBRO: lo que encontró el adversario antes de tu `/entregar` (2026-10-28 17:05 UTC)

No es un veredicto: el informe de COBRO no llegó. El adversario Opus atacó
`b3ac325..dda9f5b` y la PM reprodujo A–D en SQLite (`/tmp/cdi-pm/wt-cobro-o`)
y A también sobre la base. Arreglalos **antes** de entregar las tres COBRO,
en commits aparte encima de `dda9f5b`, rojo antes y un sabotaje por regla.
Todo decidido por la PM.

- **A. Regresión de COBRO-MP-1 (alta).** Un pago aplicado antes de que
  existiera `mp_pagos_aplicados` se vuelve a aplicar con cada aviso IPN
  sin firma (`?topic=payment&id=<id>`): en `dda9f5b` la cuenta past_due
  queda `active` 30 días más y con el contador en 0; en la base respondía
  `skipped: payment_id ya procesado`. Ningún pago anterior al despliegue
  se puede volver a aplicar, sea el último o uno más viejo. Elegí cómo
  (cargar la tabla desde `last_payment_id` en la migración, no aplicar un
  pago aprobado antes del período vigente, o las dos) y decilo en el
  informe. Prueba: un pago aplicado por el código viejo, reenviado.
- **B. `/generate_maria_export` no cuenta (media).** Con el tope lleno, la
  importación da 402 y la exportación sale cinco veces con 200. La D4 b es
  «el MARIA de un operation_id»: la exportación también cuenta, con la
  misma regla de una vez por operación.
- **C. past_due no puede cancelar (media).** `/api/billing/cancel` da 409
  y la suscripción `authorized` sigue cobrando cuando la tarjeta vuelve.
  Desde past_due se puede cancelar: cancela en Mercado Pago, la cuenta
  queda `canceled` y no gana acceso.
- **D. Dos checkouts a la vez (media/alta).** Dos pedidos simultáneos
  crean dos suscripciones en Mercado Pago y CDI guarda una sola; cancelar
  deja la otra cobrando. El checkout bloquea la fila de la cuenta (como
  el conteo), el segundo no crea otra, y el botón de `profile.js`
  (`openCheckout`) se deshabilita como el de `app_v2.js`. Prueba de la
  carrera en Postgres 16.
- **E. Reactivar una prueba con recarga (baja).** Queda `canceled` con
  `needs_checkout` y el texto «período ya pagado», que es falso. Vuelve a
  `trial` con sus días, como una prueba sin recarga.
- **A riesgos, no ahora:** el webhook que no bloquea la fila mientras un
  pedido la vence (F, base); el aviso `payment` de renovación antes que
  `subscription_authorized_payment` con monto de panel menor; el aviso sin
  `external_reference` que da 400 antes de deduplicar; `precio_esperado`
  sin vencimiento (D29).

El adversario Sonnet de COBRO sigue: si suma algo, va abajo de esto.

## BACKUP-1a — después de LIMPIEZA-1 (2026-10-28 12:00 UTC)

Primero **subí LIMPIEZA-1 a tu rama ya** (commits aparte, encima de
`7d3a7f8`), para que no se pierda si se recicla el contenedor; se sigue
entregando después del informe de AISLAMIENTO-2.

Después, la mitad de BACKUP-1 que no espera a Emi (hallazgo D1 de
`AUDITORIA-2026-10-06.md`: no hay ninguna copia de la base de producción).
Es de MARIA en `ROADMAP.md`; te la paso yo porque ella no tiene pieza que
arranque y vos tenés menos entregas en cola. Decidido por la PM.

- **Qué:** un script que saca la copia de una base Postgres
  (`pg_dump -Fc`), la restaura en una base descartable y comprueba que
  quedó igual: por tabla, la cantidad de filas, y algo que distinga el
  contenido (por ejemplo, un resumen de las filas ordenadas). Si la
  restauración no da igual, sale con error y lo dice.
- **Lo que espera a Emi, no lo hacés:** adónde va la copia (fuera de
  Railway) y dónde se programa. Dejá el envío como un paso aparte con un
  destino de prueba local, y en el informe, la lista de lo que tiene que
  cargar Emi para activarlo.
- **Límites:** sólo Postgres 16 local; ninguna dirección ni clave de
  producción en el repositorio, en las pruebas ni en el informe. La
  dirección de la base entra por variable, nunca por argumento (queda en el
  historial del shell).
- **Pruebas:** copia y restauración de una base con datos sintéticos de
  todas las tablas; una fila cambiada, una tabla vacía y una copia cortada
  a la mitad tienen que dar error. Un sabotaje por regla.
- Commits aparte encima de LIMPIEZA-1, con su propio `/entregar` después
  del de LIMPIEZA-1. Toca datos: revisión fuerte. Si algo choca, preguntá
  en la **D8**.

## COBRO-CORTE-1 — hecha, sin entregar (encargada 2026-10-28 05:00 UTC)

En commits aparte encima de COBRO-MP-1 (`f54d8a9`), con su propio
`/entregar` después del de COBRO-MP-1. Arregla C1, C5 y C6
(`AUDITORIA-2026-10-06.md`). Tu análisis de entonces está en `62b1d14`;
las decisiones, en `efef997` (ahí se llamaron D4 a D6 y siguen valiendo):

- **Cuándo se cuenta (D4 b, N = 10):** la primera vez que se genera el
  MARIA de un `operation_id` del usuario se crea la operación y se cuenta.
  Las descargas siguientes del mismo id no cuentan, y `finalize.js` guarda
  con ese id (no uno nuevo). Un mismo id no pasa de 10 regeneraciones con
  contenido distinto.
- **El corte (D5 a):** en las rutas que gastan Gemini o generan valor, sólo
  por estado (vencido o impago → 402). El tope del plan, sólo donde se
  cuenta una operación.
- **Carreras (D6 a):** `SELECT … FOR UPDATE` de la fila de la cuenta
  (usuario u organización) mientras se mira el tope, se cuenta y se
  calcula el `op_code`, en una sola transacción, sin migración. El índice
  único `(owner_username, op_code)` es una pieza aparte, más adelante.
- **El aviso:** dice la razón real (impago, vencido o tope).

Premisa primero: la base se movió tres semanas desde `62b1d14` (ORG-1,
COBRO-MP-1). Comprobá que las rutas y líneas que nombraste siguen siendo
esas antes de tocar nada. Cada prueba se ve en rojo antes del arreglo.

Pruebas: una cuenta impaga y una vencida no generan ni suben a Gemini
(402 con su razón); una paga con el tope lleno puede validar y bajar lo ya
contado; regenerar el mismo id no cuenta y la 11.ª distinta se frena;
guardar después de generar no cuenta dos veces; pedidos al mismo tiempo
contra un Postgres local no pasan el tope ni repiten `op_code` (o
declarado «no corrido»). Un sabotaje por regla. Nada contra Mercado Pago
real. Tu próxima D es la **D6** de esta numeración.

Es plata: la reviso con Opus y Sonnet, alto.

## COBRO-MP-2: subila ya (2026-10-28 10:00 UTC)

Decís que está hecha en `dda9f5b`, pero tu rama remota sigue en `192774f`.
Como con COBRO-MP-1: subila ya a `claude/dev-tecnica`, sin force push,
aunque la entrega espere al cupo. Si el contenedor se recicla, se pierde.

## AISLAMIENTO-2 — empezala ya (2026-10-28 10:00 UTC)

Mientras esperás el cupo de las 18:00, la siguiente de la Fase 3. ABUSO-1
la hace la Dev MARIA (decidido por la PM: es vecina de SESION-1, que ya
hizo); vos te quedás con **AISLAMIENTO-2** y después **LIMPIEZA-1**. En
commits aparte encima de `dda9f5b`, con su propio `/entregar` después del
de COBRO-MP-2. No toca plata ni la cola MARIA.

- **La prueba de aislamiento cubre poco:** `scripts/testing/ataque_aislamiento.sh`
  ve sólo clientes y descargas (22 casos). Que cubra también operaciones,
  notas, presupuestos, estudios y admin: otro dueño no ve, no cambia y no
  borra lo ajeno, y lo de un estudio no se ve desde otro.
- **Dos puntos ciegos de la prueba de recorrido de admin**
  (`REPRODUCCION-ADMIN-2-2026-10-07.md`): un WebSocket bajo `/api/admin/`
  sin control, y una ruta cruda en `/api/admin` o `/dev` exactos, sin barra
  final. Hoy no existen: la prueba tiene que verlos si alguien los agrega.
- **Latente:** `roles` guardado como texto en vez de lista haría que
  «administrador» cuente como admin (también en `require_admin`).

Premisa primero, sobre `dda9f5b`: corré la prueba y decí qué cubre hoy. Si
aparece una fuga de verdad, frená y avisá con una D8 antes de arreglarla:
es lo más grave que puede salir. Pruebas: cada caso nuevo en rojo con un
sabotaje que abra la fuga; los dos puntos ciegos con un sabotaje cada uno.
Es aislamiento: revisión fuerte.

## COBRO-MP-2 — hecha, sin entregar (encargada 2026-10-28 08:00 UTC)

COBRO-CORTE-1 quedó hecha (`27e4594`). Sigue la última de la Fase 2. En
commits aparte encima de `27e4594`, con su propio `/entregar` después del
de COBRO-CORTE-1. Arregla C2, C4 y C8 de `AUDITORIA-2026-10-06.md` y lo que
de tu D9 del 07/10 quedó para acá (`7f1dd2c`):

- **Cancelar (C2):** cancelar en CDI también cancela la suscripción en
  Mercado Pago, y la cuenta sigue activa hasta el fin del período pagado,
  como ya dice la pantalla («activo hasta…»). Si Mercado Pago no contesta
  o da error, no se cancela en CDI a medias: se dice que no se pudo.
- **Una sola suscripción (C4):** el checkout mira si ya hay una vigente y
  no deja pagar dos veces. Un pago nunca hace perder los días que
  quedaban.
- **Reactivar pagando (C8 y D9):** cancelar y reactivar desde una prueba
  gratis no deja la cuenta activa sin pagar. Sin `MP_ACCESS_TOKEN` no se
  dice «Tu cuenta Premium ha sido activada» ni se cambia nada.

Premisa primero: comprobá cada una sobre `27e4594` (la base cambió con
COBRO-MP-1 y COBRO-CORTE-1) y cómo se cancela una suscripción en la API de
Mercado Pago según el código y la documentación que ya esté en el repo (la
red está cerrada: lo que no puedas ver, como supuesto). Si para «no perder
días» o «una sola suscripción» hay que elegir entre comportamientos que ve
el cliente, preguntá en la **D7** antes de hacerlo.

Pruebas, con Mercado Pago simulado (nada contra el real): cancelar llama
a Mercado Pago y deja la cuenta activa hasta el fin del período; Mercado
Pago con error no deja nada a medias; el segundo checkout con una vigente
se frena; un pago no acorta el período; cancelar y reactivar una prueba no
la activa; sin token no dice «activada» ni cambia el estado. Cada prueba en
rojo antes del arreglo; un sabotaje por regla. Línea en `CHANGELOG.md`.

Es plata: la reviso con Opus y Sonnet, alto.

### D7 (2026-10-28 08:20 UTC, sobre tu `192774f`): (a) en las cuatro

Decidido por la PM; Emi lo confirma de día y puede cambiarlo antes de
publicar. La premisa y «Lo que hago sin esperar» van como los escribiste.

- **D7.1 (a):** los días de prueba que quedan se suman al pago.
- **D7.2:** en modo suscripción, como lo planteaste, con un caso más: el
  409 vale sólo si la cuenta está vigente en CDI. Si está `past_due` o
  vencida y en Mercado Pago figura `authorized` (por ejemplo, la tarjeta
  falla), la vieja se cancela antes de crear la nueva, como con `pending`:
  si no, el que quiere pagar con otra tarjeta queda trabado. Si cancelar la
  vieja falla, 503 y no se crea nada. En modo preference, **(a)**: pagar
  por adelantado suma 30 días desde el fin.
- **D7.3 (a):** reactivar lleva al checkout de una suscripción nueva. Antes
  de pagar, la respuesta dice que cobra ahora y suma 30 días desde el fin
  del período ya pagado. Ningún texto dice «próximo cobro» si no lo hay.
- **D7.4 (a):** sin token, en producción, el checkout da 503 y no hay botón
  de simular. Para saber si es producción usá el criterio que ya tenga el
  código, cerrado por defecto: si falta la variable que lo dice, no hay
  demo. Si no hay criterio o cerrarlo rompe cómo arrancan las pruebas, D8
  antes de inventar uno.

**Riesgos aceptados:** el de estudios (quién cancela en un estudio es de
permisos, Fase 3) y el de las cuentas `active` sin pago de Mercado Pago, que
vuelven a `trial`. Los dos, al informe. Sumá a riesgos, para publicar, los
supuestos de Mercado Pago que no pudiste ver sin red: los estados, que una
`cancelled` no vuelve, el cobro inmediato y la ruta `PUT /preapproval/{id}`
(y por qué no el SDK).

## Orden

1. COBRO-MP-1, vuelta 3: la devolución de arriba, con D13 (c), ahora.
2. ORDEN-1b, vuelta 2: las pruebas de arriba, apenas entregues la 1.
3. COBRO-CORTE-1: hecha; se entrega después de COBRO-MP-1.
4. COBRO-MP-2: hecha; suma la cancelación de organizaciones y la segunda
   suscripción de una org (arriba), y se entrega después de COBRO-CORTE-1.
5. AISLAMIENTO-2 y LIMPIEZA-1: hechas; se entregan después de COBRO-MP-2.
6. BACKUP-1a (arriba).
7. EXCEL-2c (D32 b, decidido por la PM): antes de leer, la fila y columna
   máximas (`r=` y `<dimension>`), la cuenta de `<xf` en `styles.xml` y de
   entradas del `sst`; por encima de un tope, el libro va al carril pesado.
   Rojo primero, un caso por forma y un sabotaje por tope. Hasta entonces,
   el CHANGELOG y tus riesgos dicen el límite con su número.
