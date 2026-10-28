# PM → Dev técnica (Dev 1)

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`. La
historia de este canal está en Git.

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

## Veredicto de EXCEL-3f (con H1-bis) (2026-10-28): aceptada

Sobre `8c63c37` (informe `0557f03`). El detalle está en
`REPRODUCCION-EXCEL-3f-2026-10-28.md`. Corrí la suite desde base limpia,
`cliente1c.sh` entero (44 ROJO), los 39 sabotajes de 3f y los que
reapuntaste de `excel3.sh` (todos en rojo) y trece negativos míos en
`.xlsx` y `.xls`, en la base y en la entrega. Mi adversario no corrió
(presupuesto). Integro tu rama hasta `8e744a0`, sin GUARDAR-2, que sigue en
revisión. **Con esto EXCEL-3 queda cerrada.**

- **Bien:** H1-bis tapa la clave en todas las formas que probé; D21 (b),
  D22 (b), H5, la descripción repetida a mano y el texto de contenedor, con
  sus sabotajes. Lo único que cambia el FOB es el plural, y se comporta como
  su singular en la base. Tus supuestos y tus riesgos quedan aceptados.
- **Riesgos que anoto, no los arregles:** «Seguros para puerta» sin origen
  sale del FOB con su fila nombrada (ya pasaba con el singular); «Transporte
  interno» con origen y «DHL» solo no llevan aviso (no cambian el FOB).
- **Un rojo que no es tuyo, para después de ORDEN-1:**
  `test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal`.
  En mi contenedor (4 núcleos) da rojo siempre: en la suite y 6 de 6 corrido
  solo, 3 en la base `89a0fde` y 3 en `8c63c37`. La subida normal tarda
  30,7 a 32,7 s y da 400 («tardó demasiado»). Vos lo viste 1 de 5. Lo que
  importa es que en producción una subida normal puede esperar ~30 s detrás
  de ocho pesadas. Pedido: diagnosticá dónde se van los 30 s (cola,
  hilos, CPU) y proponé el arreglo con una D. Sin subir el corte de 30 s ni
  aflojar la prueba.

## Tu diagnóstico de `test_excel2` y D4-D5 (2026-10-28): EXCEL-2b, ahora

Recibido en `b5a50d1` (medición `ff03efe`). Diagnóstico aceptado: los 30 s
son cola detrás de las pesadas, no trabajo de la subida normal. Es el
criterio de EXCEL-2 ya aceptado (D26 a: ocho libros armados y la normal da
200), así que arreglarlo está dentro del roadmap y no va a ABUSO-1.

- **D4: (a), carril liviano.** Pieza **EXCEL-2b**, ahora. Condiciones:
  - el umbral se mide una vez, sobre las partes XML descomprimidas (no las
    imágenes), con valor por defecto en el código y variable de entorno;
  - el tope de 10 MiB y el resto de los cortes de EXCEL-2 no se tocan;
  - sin límite de frecuencia: eso es ABUSO-1;
  - un caso que muestre que un libro que dice ser chico y no lo es no
    entra al carril liviano (el umbral no se puede burlar desde el libro);
  - sabotajes que manden la normal al carril pesado y que salteen la
    medida del umbral;
  - (b) y (c) no entran ahora.
  Toca `file_security.py` y `main.py`: revisión fuerte con adversario
  (cupo, hoy después de las 18:00 UTC).
- **D5: (a).** La prueba afirma también `dt` < 5 s, en la misma pieza.

Decidido por la PM.

## ORDEN-1 (en revisión) y tus D (2026-10-28)

Recibida en `cdc9c57` (código `0d89c20`). Es de pantalla y del borrador
del navegador: la reproduzco ahora y sumo un adversario sobre los
borradores (computadora compartida, pérdida de productos) cuando haya
presupuesto, hoy después de las 18:00 UTC. Mientras, no la integro.

- **D1: (a).** El orden vive en el borrador de cada pestaña. Una columna
  que nadie lee es una migración sin uso; si algún día una pantalla
  reabre operaciones del servidor, la posición entra en esa pieza.
- **D2: (a). Tenías razón:** «el Excel» lo puse yo sin comprobar que v2
  lo tuviera. Se cumple con la tabla y el TXT. Un Excel de la operación
  en v2 no entra al roadmap salvo que Emi lo pida.
- **D3: (a).** El centavo puede cambiar de ítem, el total no. Queda el
  xfail con su motivo.

Decidido por la PM.

## GUARDAR-2 (en revisión)

Recibida en `cef45ce` (informe `cb42e8f`). Toca lectura por dueño: la
reviso con adversario cuando haya presupuesto (hoy, después de las 18:00
UTC). Si vuelve con devolución, va antes que lo que estés haciendo.

## COBRO-MP-1 — hecha, sin entregar (encargada 2026-10-28 04:00 UTC)

EXCEL-2b quedó hecha y espera el cupo de las 18:00 UTC. Mientras, retomá
COBRO-MP-1 en commits aparte encima de EXCEL-2b, con su propio `/entregar`
después del de EXCEL-2b. EXCEL-2b se entrega sobre su propio SHA.

**Es una retoma.** Los pasos 1 a 4 están hechos y en pausa desde el 07/10
en `origin/claude/dev1-tecnica`, de `3d3f712` a `f5f06ee`: producto,
pruebas, el caso contra Postgres y el paso 4 (renovaciones). Las
respuestas D28 a D31 de ese día (`074a50b`, `git show 074a50b`) siguen
valiendo. `MP_PREAPPROVAL_PLAN_ID_*` está en Railway
(`DECISIONS.md`), así que el paso 4 corre en producción.

- **La base se movió tres semanas** (ORG-1 tocó planes y organizaciones;
  el cobro puede haber cambiado). Traelos commit por commit. Cada prueba
  que entonces estuvo en rojo antes del arreglo se vuelve a ver en rojo
  sobre la base nueva: un verde viejo no prueba nada acá.
- **Lo que no se negocia (D31):** que no se aplique dos veces lo frena el
  índice único de la base, no mirar antes de insertar; si el insert choca
  (`IntegrityError`), se responde `skipped` sin tocar la cuenta; una prueba
  manda dos avisos del mismo `payment_id` a la vez (`asyncio.gather`) y se
  aplica uno solo; el `create_all` de la tabla, contra un Postgres local, o
  declarado «no corrido».
- Un pago rechazado por monto lo ve Emi (D29 de entonces, condición 3).
- Nada contra Mercado Pago real.
- Tu próxima D es la **D6** (no reuses los números de octubre).

Es plata: la reviso con Opus y Sonnet, alto.

## COBRO-MP-1: subila ya (2026-10-28 05:00 UTC)

Está hecha en `f54d8a9`, pero sólo en tu contenedor (rama local
`cobro-mp-1`). Si el contenedor se recicla, se pierde. Subila ya a
`claude/dev-tecnica`, sin force push, aunque la entrega espere al cupo.
EXCEL-2b se sigue entregando sobre su propio SHA (`b3ac325`). Los dos
riesgos que proponés como piezas aparte (dos pagos a la vez de una cuenta
dan una sola extensión; un aviso de renovación sin suscripción puede
quedar rechazado para siempre) se los llevo a Emi de día: anotalos en el
informe, en «riesgos».

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

## COBRO-MP-2 — empezala ya (2026-10-28 08:00 UTC)

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

## Orden

1. EXCEL-2b (D4 a y D5 a): hecha, se entrega con el cupo de las 18:00 UTC.
2. Si GUARDAR-2 u ORDEN-1 vuelven con devolución, esa va primero.
3. COBRO-MP-1: hecha; subila ya y se entrega después de EXCEL-2b.
4. COBRO-CORTE-1: hecha; se entrega después de COBRO-MP-1.
5. COBRO-MP-2 (arriba), ahora.
