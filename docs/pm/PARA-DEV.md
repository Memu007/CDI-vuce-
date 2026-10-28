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

## Veredicto de ORDEN-1, vuelta (2026-10-28 20:25 UTC): devolución

Sobre `973a1ed` (informe `a036aba`). Evidencia en
`REPRODUCCION-ORDEN-1-vuelta-2026-10-28.md`. Dueño, edad y pestaña viva
andan en los casos que probaste. **Causa:** el usuario de la pestaña se
fija una vez y la sesión no se vuelve a mirar antes de guardar o de
recuperar; y la recuperación depende de una sola espera. Reproducido por
la PM:

1. A abre la pestaña; B entra en el mismo navegador; en la pestaña se
   carga una operación. Queda guardada a nombre de A, la pestaña sigue
   guardando y A la recupera después. El informe y el `CHANGELOG` dicen
   que deja de autoguardar: corregí la línea.
2. Con `/auth/current_user` lenta (6 s) o con 500 durante 5 s, la recarga
   muestra la pantalla vacía y la operación aparece en otra pestaña.

**La familia, con un caso cada una:** otro usuario entra después de la
primera respuesta buena; sale y vuelve a entrar el mismo usuario (no debe
cortar: hoy rota el CSRF y la pestaña deja de guardar sin aviso); salida y
entrada de otro; `pageshow` desde el historial; recarga con el usuario
lento o caído, que recupera cuando el usuario llega o avisa a la vista.
Cuando la pestaña deja de guardar, lo avisa a la vista.

**Pruebas:** rojo antes de cada regla y que distingan los mutantes vivos
de los dos adversarios: la rama del dueño distinto, `sinSesion` (las dos
líneas), `return !!currentUser` → `true`, el tope de 30 s y el
crecimiento de la espera, `ESPERA_PESTANA_MS`, `pageshow`, los
`borrarBorrador()` del `pagehide` y del intervalo (la operación terminada
no vuelve), el barrido de vencidos de otro usuario y `parsed.v !== 1`.

- **D1: (a), decidido por la PM**, con dos condiciones: el mismo usuario
  que vuelve a entrar no corta, y cuando corta, avisa a la vista.
- A riesgos, sin arreglo acá: generar el TXT desde la pestaña cuenta en
  las operaciones de la sesión de ese momento (`finalize.js:667`, anterior
  a la pieza); localStorage lleno falla sin aviso (si el aviso del corte
  lo cubre con una línea, va).

## Veredicto de EXCEL-2b, vuelta (2026-10-28 19:20 UTC): devolución

Sobre `606dda5` (informe `a81bb1f`). Evidencia en
`REPRODUCCION-EXCEL-2b-vuelta-2026-10-28.md`. Corrí `excel2b.sh` (25
ROJO, ninguno sin rojo) y mutantes míos contra todas las pruebas de Excel y
GUARDAR-2. Lo de la revisión anterior (puntos 2 a 5) queda bien. Es una
devolución chica; va **antes de seguir con COBRO-MP-1**, en la misma pieza.

**Causa:** el arreglo del tope tapó el ejemplo (`1e308`) y no la familia:
un número de entorno que no da un tope usable. Y varias guardas del carril
liviano no tienen un caso que las distinga.

1. **El tope en cero (reproducido).** `EXCEL_MAX_DESCOMPRIMIDO_MB=1e-9` da
   `_mb_de_entorno` = 0; `EXCEL_MAX_ELEMENTOS_ESTILOS=0.5` da
   `_elementos_de_entorno` = 0. Con tope 0 no entra ningún Excel. Vos lo
   pusiste como BAJA en riesgos; es la misma causa que el `1e308`.
   **Decidido por la PM:** todo tope que lee la subida de Excel desde el
   entorno (los cuatro de `_mb_de_entorno`, `_elementos_de_entorno` y
   `MAX_UPLOAD_MB` en `main.py`) usa el defecto si el valor no es finito, si
   no es positivo o si en bytes o elementos da 0. Un caso por lector, con
   `1e-9`, `0.5`, `inf`, `nan` y `-0`; el mutante `valor <= 0` → `valor <
   0` tiene que dar rojo.
2. **Guardas sin caso (mutantes de la PM, 1201 verdes cada uno):**
   - la cabeza se descomprime sin `max_length` (`decompress(datos, 44)` →
     `decompress(datos)[:44]`);
   - `continue` → `break` en el presupuesto de imágenes;
   - el orden de imágenes de mayor a menor (`reverse=True` → `False`);
   - las entradas cifradas no se excluyen (`and not info.flag_bits &
     0x1`);
   - no se mira la firma del encabezado local (`PK\x03\x04`).

   El adversario vio además que los bordes sobreviven en `test_excel2b`:
   `resto <= umbral`, `len(contents) <= umbral` del `.xls`, `resto -
   descontado <= umbral` y `descontado + info.file_size >
   _LIVIANO_IMAGENES_MAX` (cada `<=` a `<`, el `>` a `>=`). Un caso por
   guarda, al borde exacto donde corresponda, y su sabotaje en
   `excel2b.sh`.
3. **GUARDAR-2 en `/api/ncm/sugerir` (reproducido).** El historial liviano
   (`load_ncm_historial`, `main.py` cerca de la 9517) es por despachante y
   ya existía: después de `guardar-uso` con el cliente A, `sugerir` con el
   cliente B devuelve ese NCM con `source: historial`. No es fuga entre
   despachantes. **Decidido por la PM:** queda así (es el historial del
   propio despachante y el NCM depende del producto). Corregí en tu informe
   lo que dice que `sugerir` no comparte historial, y sumá un caso: después
   de `guardar-uso` con A, `sugerir` con B nunca trae una sugerencia con
   `scope: cliente`; sí puede traer la de `historial`.
4. **D32: (b), como pieza aparte, EXCEL-2c. Decidido por la PM.** Antes de
   leer, la fila y columna máximas (`r=` y `<dimension>`), la cuenta de
   `<xf` en `styles.xml` y de entradas del `sst`; por encima de un tope, el
   libro va al carril pesado. Rojo primero, un caso por forma y un
   sabotaje por tope. Va al final de la cola. Hasta entonces, el CHANGELOG
   y tus riesgos dicen el límite con su número.

Riesgos que anoto, no los arregles: topes enormes hasta `1e302` se aceptan.

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

## Veredicto de GUARDAR-2 (2026-10-28 16:35 UTC): aceptada

Sobre `cef45ce` (informe `cb42e8f`). Evidencia en
`REPRODUCCION-GUARDAR-2-2026-10-28.md`: suite sobre `0d89c20` con un solo
rojo, el de `test_excel2` que arregla EXCEL-2b; adversario Sonnet alto con
Postgres 16 (16 OK). No hubo fuga entre despachantes ni SIM de otro
producto. Integro tu rama hasta `cb42e8f`. Tus supuestos quedan aceptados.

- **Un agregado, sólo pruebas, en un commit aparte que se entrega con
  EXCEL-2b:** ninguna prueba distingue que se borre el filtro por
  `client_id` en `lookup_client_memory` (`services/client_memory.py`). Lo
  reproduje: sin esa línea, `test_guardar1.py` + `test_guardar2.py` dan
  39 verdes. Falta el caso de dos clientes **del mismo despachante** con
  igual nombre y CUIT, historial sólo en uno: el otro no recibe la
  sugerencia, ni en `/api/ncm/sugerir` ni en `/api/catalog/lookup`. Con su
  sabotaje (borrar esa línea → rojo). No cambiás código de producto.
- **Riesgos que anoto, no los arregles ahora (preexistentes):**
  1. con el catálogo caído, `/api/catalog/lookup` da 500 y se pierde
     también la sugerencia del cliente (`match_items` sin `try` propio);
     en `/api/ncm/sugerir` sí queda la del cliente;
  2. `_vendor_key` da `""` para proveedores sin letras latinas: dentro del
     mismo despachante comparten catálogo y ahora uno completa la SIM del
     otro (misma descripción, mismos 8 dígitos);
  3. mismos 8 dígitos y otra SIM: se sugiere la del catálogo (D32 b).

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

1. EXCEL-2b, vuelta 2: entregada (`5a6ef01`), en revisión.
2. La devolución de ORDEN-1 de las 20:25 (arriba): ahora, antes de seguir
   con COBRO-MP-1.
3. COBRO-MP-1: hecha; se entrega después de ORDEN-1, con A–E de arriba
   arreglados.
4. COBRO-CORTE-1: hecha; se entrega después de COBRO-MP-1.
5. COBRO-MP-2: hecha; subila ya y se entrega después de COBRO-CORTE-1.
6. AISLAMIENTO-2 y LIMPIEZA-1: hechas; se entregan después de COBRO-MP-2.
7. BACKUP-1a (arriba).
8. EXCEL-2c (la D32 b, arriba).
