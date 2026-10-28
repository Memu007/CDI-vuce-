# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev-maria`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM
con `merge`. Nunca `main`. Las ramas viejas `claude/dev2-maria` y
`codex/*` son historia: lo aceptado ya está en la de la PM.

Sos la Dev de la **cola MARIA**: el MARIA.TXT, el lector de facturas y sus
pantallas. La Dev técnica trabaja en `claude/dev-tecnica`; no tocás su
canal ni su rama.

Esfuerzo alto (Emi, 2026-10-24). Herramientas: todas menos el consejero;
tus subagentes hasta alto, nunca Fable.

**Timbres:** al entregar o al dejar una D que te frena, despertás a la PM
principal con `send_message` (sesión en `NOW.md`, «Quién hace qué»),
`priority` `next`, empezando con «Dev MARIA:». Ella te despierta igual.

**Regla del archivo MARIA** (límite que no se negocia): ningún cambio en lo
que sale en el TXT sin prueba (la ley, un archivo real, la respuesta del
despachante o lo que el MARIA aceptó o rechazó). **Los TXT y la proforma de
la reunión del 2026-10-24 tienen datos reales de un cliente: no entran al
repositorio.** Las pruebas usan sintéticos con la misma forma.

## D41 y el orden de lo que queda (2026-10-28 17:20 UTC)

- **D41 (DESPACHO-1b): (1), decidido por la PM.** Las tres medias
  (lectura cuadrática, peso infinito, fusión de NCM distinto) se arreglan
  después de las 18:00, encima de la cadena, antes de publicar, con rojo,
  sabotaje y suite. Sumá lo que traiga mi revisor de DESPACHO-1b, que
  corre ahora.
- **D40 y los arreglos de ORG-1 después de las piezas: sí.** Van encima de
  la cadena igual; no se integra nada hasta aceptar ORG-1.
- **Recibidas** SUFIJOS-2 (`bd76f9f`), SEGURO-1 (`5dfaf47`) y DESPACHO-1b
  (`e59e1a8`): revisión de la PM en curso. El orden después de las 18:00:
  primero las devoluciones que lleguen (DESTINO-1 ya está arriba), después
  D41.

## DATOS-1: aceptada sobre `c996ad4` (2026-10-28 17:55 UTC)

El producto hace lo que pedía la D32 (a): sin fuga a otro dueño, una sola
transacción, `/health` sin texto del error. Se integra con la cadena, cuando
se acepte DESPACHO-1b (está debajo). Evidencia en
`REPRODUCCION-DATOS-1-2026-10-28.md`. Sumá, encima de la cadena:

1. **Un cliente con dos operaciones compartidas** (reproducido por la PM):
   con `in_(op_ids[:1])` en el borrado de presupuestos, `test_datos1.py`
   sigue en `9 passed`. Es el caso normal; la prueba tiene que tenerlo.
2. **El orden presupuestos → operaciones** sólo lo frena
   `datos1_postgres.py`, que no corre en la suite. Hacelo rojo en SQLite
   (`PRAGMA foreign_keys=ON` en esa prueba) o decí por qué no se puede.
3. **Verificá y proponé (D43):** una operación del cliente con
   `owner_username` NULL (dato viejo) no entra en `op_ids`: el borrado dice
   «eliminadas: 1», la operación queda y su presupuesto compartido sigue
   accesible (revisor, Postgres 16; no lo reproduje). ¿Puede existir hoy
   una fila así, según las migraciones? Si sí, proponé el arreglo.
4. **A riesgos:** más de 32 767 operaciones dan 500 (límite de parámetros
   del `in_`, ya existía); `api_logs.operation_id` frenaría el borrado si
   algo lo llenara (hoy nada); la copia de `system_backups`
   (`client_migration`) guarda datos del cliente borrado; los 502 con
   `{err}`. La copia de `system_backups` la paso yo a Emi.

## DESPACHO-1b: devolución, sobre `e59e1a8` (2026-10-28 17:40 UTC)

Permisos bien: el adversario (Sonnet alto) no cruzó clientes ni dueños, y
los campos metidos en el cuerpo se ignoran. Va con la D41, después de las
18:00, encima de la cadena. Además de las tres medias que ya declaraste:

1. **Un PDF chico llena la memoria (alta, no declarada).** Reproducido por
   la PM sobre `e59e1a8`, con `leer_despacho` sola: 10 hojas con un flujo
   flate distinto de 70 MB cada una (0,79 MB de PDF) dan un pico de
   806 MB; 2 hojas, 244 MB. Por la API, el adversario vio 2,2 GB con un
   PDF de 2,2 MB y 30 hojas, y la memoria no vuelve. **Causa:** los topes
   miden después de pagar. `contenido.get_data()` descomprime la hoja
   entera para ver si pasa de `_MAX_CONTENIDO_PAGINA`, y eso hasta 200
   hojas. **La familia:** cada tope (hojas, bytes descomprimidos en total,
   largo de línea, columnas, renglones) corta antes de gastar. La prueba:
   ese PDF sintético se rechaza o se lee con la memoria acotada, medida
   en un proceso aparte.
2. **La lectura cuadrática frena también a las facturas.** Corre en los
   4 hilos de `_pool_lectura_pdf()`, los mismos del lector de facturas, y
   el 504 no corta el hilo: cuatro despachos de 156 KB dejaron una factura
   chica de otro usuario en 504. Entra en el arreglo de la cuadrática; la
   prueba mide el tope, no un tiempo.
3. **El peso infinito es de la misma causa que el 1:** el tope mira cada
   número, no lo que se calcula con ellos. Reproducido por la PM:
   `renglon_para_catalogo` con `cantidad=1e-320` y `kilo_neto=5` da
   `peso_unitario: inf`, y `json.dumps` falla igual que el 500 del
   catálogo. Todo valor derivado pasa por el mismo tope.
4. **Guardar empeora un producto que ya estaba (no declarada).** En
   `client_memory.py`, `_incr_avg` cuenta el promedio anterior vacío como
   0 con el peso de todas las veces: un producto sin peso, guardado otra
   vez con 2 kg, queda en 1 kg (y el valor, a la mitad). Con despachos
   sin peso es el caso común. Lo arreglás vos, con su prueba: el anterior
   vacío no promedia. Que el origen sea el último y no el frecuente va a
   riesgos.
5. **La fusión de NCM distinto tiene un caso más.** Verificado por la PM:
   «… TIPO A» y «… TIPO B» dan similitud 1,0 (las palabras de una letra
   no cuentan) contra el umbral 0,8, así que el respaldo por descripción
   las junta aunque el NCM sea otro. Y `_norm_desc` corta en 200
   caracteres: dos productos con el mismo texto de arancel adelante se
   juntan. En un despacho la posición SIM manda; la prueba lleva los dos
   casos.
6. **Valor unitario en otra divisa (hipótesis, sin reproducir):** el
   catálogo no guarda la divisa del FOB del despacho y la promedia con
   las demás. Verificalo; si es así, proponé qué hacer como D42.
7. **Pruebas que no ven el defecto.** Reproducido por la PM: sin el tope
   numérico (`if valor < 0:`) o sin el chequeo de hoja pesada,
   `test_despacho1b.py` da `50 passed`. El adversario suma: el tope de
   200 hojas, el margen de columna `+2`, la captura de
   `LecturaPdfDemasiadoLarga`, el commit único (rollback ante error de
   base) y `_sin_nul`. Un caso por cada uno, rojo con su sabotaje.

Riesgos, sin arreglo en esta pieza: más de 500 renglones (la pantalla manda
todo junto y el servidor dice «cargalos en partes»); guardar no tiene
`@limiter.limit`; renglones de «Información Adicional» que caerían en la
descripción (sin despacho real para probarlo).

## DESTINO-1: devolución de pruebas, sobre `f887b4a` (2026-10-28 17:25 UTC)

Informe `eacf591`. El producto está bien: el adversario (Sonnet alto) no
sacó un par mezclado ni un destino distinto del elegido, y tus 15 sabotajes
de `destino1.sh` dan rojo los 15 (corrida de la PM, `rc=0`). Lo que falta
son pruebas. **Causa:** ninguna prueba mira el par que sale cuando un ítem
se arma con varias entradas; `test_destino1.py` sólo prueba el grupo que da
error. Reproducido por la PM sobre `f887b4a`: agregando
`item.pop('iva_adicional', None)` después de `item = dict(renglones[0])` y
`combined.pop('iva_adicional', None)` después de `combined = dict(primero)`
(`maria_generator.py`), `test_destino1.py` + las suites de MARIA dan
`182 passed`, y el TXT sale `COMERC`/`NO_VALIDA` donde debía salir
`BDEUSO`/`IVAAD2`.

- **Sumá, en un commit de pruebas encima de la cadena** (como `6b9762e`, sin
  tocar producto), con el destino explícito **distinto del de la
  operación** en cada uno:
  1. dos renglones de la misma posición que se juntan;
  2. un grupo válido (todos con el mismo destino explícito, y el primero
     explícito con el resto vacío);
  3. un grupo de reventa (que no salga `USOPAR`/`IVAAD1` por ningún lado);
  4. un ítem con subítems y destino a nivel ítem.
  Cada una, roja con su mutante (los dos de arriba; el grupo que fuerza
  `IVAAD1`; el ítem con subítems que toma el de la operación) y verde sin
  él. Sumá los cuatro mutantes a `destino1.sh`.
- **A riesgos, sin tocar producto** (los tres son de antes de esta pieza o
  piden un body armado a mano): un `iva_adicional` falso por ítem (`false`,
  `0`, `[]`) se toma como «igual que la operación»; el 400 por destino
  inválido devuelve el valor entero (100 000 caracteres vuelven en el
  mensaje; los otros recortan a 20); `/generate_maria/avisos` no valida el
  destino, así que el error recién aparece al generar. Y la premisa: el
  golden de 2025 trae `COMERC` con `IVAAD1`; si la pregunta 7 dice otra
  cosa, se reabre la tabla (D28).
- La suite completa sobre `f887b4a` está corriendo; si da algo distinto de
  los dos rojos de tiempos de `4ce6d22`, te lo escribo acá. Acepto con las
  pruebas; integro después de ORG-1. Nada se publica antes.

## ORG-1: aceptada sobre `4ce6d22`, con ORG-1b y DESPACHO-1a (2026-10-28 17:45 UTC)

Integrada en la rama de la PM (merge `cda3320`). Evidencia en
`REPRODUCCION-ORG-1-2026-10-28.md`. Los guardas del producto están bien;
faltan pruebas y un 500. Todo va **encima de la cadena**, en los commits de
la D40, después de las 18:00 y antes de publicar.

- **D40: (1)**, decidido por la PM. Al invitar, el email que ya tiene cuenta
  da 400 y no ocupa lugar (misma respuesta en este estudio o en otro). Al
  registrarse con una invitación, las otras pendientes del mismo email en
  ese estudio quedan usadas.
- **Sumá, con la D40** (reproducido por la PM sobre `4ce6d22`):
  1. *Reingreso del sacado* (Postgres 16): dos invitaciones al mismo email,
     X entra con la primera, el dueño lo saca, X cambia su email en el
     perfil y entra con la segunda (`200`). La regla 2 de la D40 lo cierra;
     la prueba es el recorrido entero. El email del perfil sin verificar va
     a riesgos.
  2. *Email que el registro rechaza*: invitar `josé@example.com` o
     `ana@estudio` da 200 y ocupa lugar. Al invitar, la misma regla que el
     registro: 400 y no ocupa lugar.
  3. *Email largo*: en Postgres 16, invitar un email de 101 caracteres da
     **500** (`Invitation.email` es `String(100)`); de 100, 200. Tiene que
     dar 400 con la regla del 2. **Causa:** el largo lo frena la base, no
     la ruta; revisá los otros campos de la invitación.
  4. *Pruebas de los guardas.* Con cada uno de estos cambios
     `test_org1.py` + `test_despacho1a.py` siguen en `59 passed`
     (reproducidos por la PM: el filtro por estudio de `/mine`, el 403 al
     que no es dueño y el borrar de otro estudio; los demás, del revisor):
     invitar sin estudio (400), invitar sin ser dueño (403), «ya es
     miembro» con y sin filtro por estudio, pendientes menos miembros (sin
     `- set(emails_miembros)`), la validación de «@», el vencimiento de 7
     días, validar con el estudio borrado (404), sacar a alguien de otro
     estudio, sacar sin estudio (400), sacar no borra al usuario, `/mine`
     filtra los miembros por estudio, `is_owner`, y el texto «última vez»
     de DESPACHO-1a. Un caso por guarda, rojo con su sabotaje, en SQLite;
     los de base, también en Postgres 16.
- Al aceptar la última pieza de la cadena entran `6b9762e`, `3aaa3c4` y
  estos arreglos. Nada se publica antes.

## D38 y D39 (2026-10-28 14:00 UTC): sobre `2b93071` y `30c0e97`

- **D38: (1)**, como lo hiciste: si el email coincide exacto con una cuenta,
  esa; si hay varias y ninguna exacta, ninguna, con la misma respuesta que
  cuando no existe. Decidido por la PM. La (2) no: un pedido no manda
  correos de varias cuentas. La (3) (unificar pares e índice único sobre
  `lower(email)`) espera el conteo de Emi en producción; si da cero, el
  índice entra como paso nuevo sin tocar datos, y si no, decide Emi. En
  riesgos: quien tiene un par y escribe otras mayúsculas no recupera hasta
  la (3).
- **D39: (1) por ahora**: los 50 de 50 con 40 logins malos a la vez van a
  riesgos de CONEXIONES-1, con tus números. Decidido por la PM. Tu (2), la
  medición chica con 60 a 100 a la vez, es pieza nueva: se la propongo a
  Emi, recomendada, y no la empezás sin su sí.

EMAIL-1 y CONEXIONES-1 quedan hechas, sin entregar; las entregás después de
las 18:00 UTC en tu orden. Tu próxima D es la **D41**.

## Emi dijo que sí a las dos (2026-10-28 12:15 UTC): EMAIL-1 y CONEXIONES-1

Las dos entran al roadmap (Fase 3, tuyas). En commits aparte encima de
`e1b3129`, cada una con su propio `/entregar` después del de ABUSO-1, en
este orden.

### EMAIL-1 — empezala ya (tu (1) de la D36)

- Recuperar usuario y recuperar contraseña encuentran la cuenta aunque el
  email venga con otras mayúsculas.
- La causa es comparar el email tal cual: revisá **todo** lugar que busque,
  cree o cambie un email (registro, perfil, invitaciones, recuperar), no
  sólo los dos que viste. Ninguno deja crear un email que ya existe con
  otras mayúsculas.
- La respuesta no cambia exista o no el email (no revelar quién está).
- Si hoy hay dos cuentas con el mismo email en distintas mayúsculas, no se
  tocan: sin migración de datos y sin índice único nuevo hasta que Emi
  cuente los pares en producción. Qué hacer cuando un pedido encuentra
  dos cuentas, proponelo en la D38 con opciones; mientras, ningún camino
  le da a una cuenta el acceso de la otra.
- Pruebas en SQLite y Postgres 16; un sabotaje por regla. Autenticación:
  revisión fuerte.

### CONEXIONES-1 — después de EMAIL-1 (tu (1) de la D37)

- Medí si `session.close()` cancelado deja conexiones tomadas: gunicorn con
  la misma configuración del `Dockerfile` y Postgres 16, muchas respuestas
  401 y algunas normales, mirando `pg_stat_activity` y el pool. Esperás
  condiciones que se ven, no tiempos fijos.
- Si quedan conexiones tomadas: arreglo (por ejemplo, middlewares en ASGI
  puro) con una prueba que dé rojo antes y verde después. Si no quedan: no
  se cambia el producto; el informe trae los números y el aviso de las
  pruebas sigue en riesgos.
- Toca todas las rutas: revisión fuerte.

## D35 a D37 (2026-10-28)

Cerradas. Quedan resumidas en `DECISIONS.md` («D35 a D37 de la Dev MARIA»).

## D28 a D34 (2026-10-28)

Cerradas. Quedan resumidas en `DECISIONS.md` («D28 a D34 de la Dev MARIA»).

## Lo encargado de las piezas entregadas, todavía en revisión

Lo de ORG-1, ORG-1b, DESPACHO-1a, DESTINO-1 y DATOS-1 (aceptadas o con devolución
arriba) salió del canal: `git show 1f648c3:docs/pm/PARA-DEV-2.md`.

### ABUSO-1 — hecha, sin entregar (encargada 2026-10-28 10:00 UTC)

SESION-1 quedó hecha (`895ee73`, informe `5105838`): recibido, la reviso
cuando la entregues. Te paso la pieza vecina de la Fase 3, que también era
de la técnica: **ABUSO-1**, los hallazgos S4, S5, S6 y C9 de
`AUDITORIA-2026-10-06.md`. Decidido por la PM; dentro del roadmap. En
commits aparte encima de `895ee73`, con su propio `/entregar` después del
de SESION-1.

- **S4:** el límite de intentos de login usa la IP que manda el cliente
  (`X-Forwarded-For`): se esquiva y se puede bloquear a otra persona.
- **S5:** `/api/ui/event` (y `/api/session/state`, si está igual) sin
  sesión ni tope de tamaño: llenan el disco y ensucian los números del
  admin.
- **S6:** el registro dice qué usuarios y emails existen; recuperar
  usuario no tiene límite (correo masivo).
- **C9:** pruebas gratis infinitas: cada email nuevo da 14 días más y el
  registro no tiene límite.

**Premisa primero:** reproducí cada uno sobre `895ee73` (PG16 en el 55432
y SQLite) y decí qué limitador hay hoy y con qué clave cuenta. Si alguno ya
no se reproduce, decilo con la prueba.

**Antes de hacer, D35** para lo que cambia lo que ve el cliente o depende
de algo que no se ve desde acá: qué IP se toma detrás del proxy de Railway
(no se puede mirar; decí qué suponés y qué pasa si el supuesto falla), los
números de los límites nuevos (registros, recuperar usuario, eventos) y qué
dice el registro cuando el email o el usuario ya existen. Con opciones y tu
recomendación. Mientras contestás, hacé lo que no dependa de la D35 (por
ejemplo S5).

**Fuera de alcance:** la fila 14 de Argon (el login exitoso reinicia el
contador, bloqueo perpetuo del pedido de reset) y X1 (sugerencias de NCM
sin tope). Si tu cambio arregla alguno de paso, decilo; si no, una línea en
«riesgos».

Pruebas: cada hallazgo en rojo antes del arreglo, en PG16 y SQLite; una IP
inventada en `X-Forwarded-For` no esquiva el límite ni bloquea a otro; un
evento sin sesión o demasiado grande no se guarda; un sabotaje por regla.
Línea en `CHANGELOG.md`. Es autenticación y registro: revisión fuerte.

### SESION-1 — hecha, sin entregar (encargada 2026-10-28 09:00 UTC)

OBSERVABILIDAD-1 quedó hecha (`39be45e`). Lo tuyo que queda espera a gente
de afuera, así que te paso otra pieza de la Fase 3 que era de la técnica:
**SESION-1**, el hallazgo S3 de `AUDITORIA-2026-10-06.md`. Decidido por la
PM; dentro del roadmap. En commits aparte encima de `39be45e`, con su
propio `/entregar` después del de OBSERVABILIDAD-1.

- **El problema (S3):** resetear o cambiar la contraseña revive las
  sesiones viejas, incluso las ya revocadas; cerrar sesión no revoca; con
  una sesión robada se cambia el email sin contraseña y se toma la cuenta.
- **Premisa primero:** reproducí cada parte sobre `39be45e` (PG16 en el
  55432 y SQLite) antes de tocar nada, y decí dónde vive hoy la revocación
  (jti, versión de token, lo que haya) y qué rutas cambian contraseña o
  email. Si alguna parte ya no se reproduce, decilo con la prueba.
- **Qué hacer:** cambiar o resetear la contraseña y cerrar sesión revocan
  de verdad las sesiones que corresponden (las otras, y en cerrar sesión la
  propia), y una revocada no vuelve; cambiar el email pide la contraseña
  actual. Usá el mecanismo de revocación que ya exista; si no hay uno o hay
  dos que compiten, preguntá en la **D35** antes de inventar otro.
- **Fuera de alcance:** los hallazgos vecinos de Argon
  (`REPRODUCCION-ARGON-2026-10-24.md`, filas 10, 13.2 y 14: link de
  verificación reutilizable, reset con cookie vieja, contador de intentos,
  tokens de reset paralelos, `/auth/me` y el jti). Si tu cambio arregla
  alguno de paso, decilo; si no, una línea por cada uno a «riesgos». No
  los arregles a propósito: eso lo prioriza Emi.

Pruebas: cada parte de S3 en PG16 y SQLite, con la sesión vieja que ya no
entra después de cada acción y la sesión nueva que sí; cambiar el email sin
contraseña o con una equivocada falla y no cambia nada; un sabotaje por
regla. Línea en `CHANGELOG.md`. Es autenticación: revisión fuerte.

### OBSERVABILIDAD-1 — hecha, sin entregar (encargada 2026-10-28 08:00 UTC)

DISCO-1 quedó hecha (`88b22c8`). Lo tuyo que queda espera a alguien de
afuera (BACKUP-1 a Emi: dónde se guarda la copia fuera de Railway). Te paso
una pieza de la Fase 3 que era de la técnica, que tiene la cola larga:
**OBSERVABILIDAD-1**. Decidido por la PM; dentro del roadmap. En commits
aparte encima de `88b22c8`, con su propio `/entregar` después del de
DISCO-1.

- **El problema:** el log de producción del 24/10
  (`CIERRE-RETOMA-2026-10-24.md`, «Observación operativa») muestra que
  registrar una métrica falla porque a `api_logs` le falta la columna
  `owner_username`. El modelo la tiene (`database/models.py`, cerca de la
  línea 342), pero la tabla de producción se creó antes, y crear las tablas
  al arrancar no agrega columnas a una tabla que ya existe. Hay un script
  viejo, `scripts/migrate_add_owner.py`, que la agrega a mano.
- **Premisa primero:** reproducilo en Postgres 16 descartable (el 55432):
  una base con `api_logs` sin la columna, arrancar la app de `88b22c8` y un
  pedido cualquiera; qué pasa (¿se pierde la métrica, falla el pedido?).
  Decí cómo se aplican hoy los cambios de esquema al publicar y si
  `migrate_add_owner.py` corrió alguna vez en producción (con lo que se ve
  en el repo; no ves la base de producción: supuesto).
- **Qué hacer:** que al arrancar la columna exista, con su índice, sin
  intervención a mano: sólo agregar (columna que acepta vacío), sin borrar
  ni reescribir nada, y que correrlo dos veces no haga nada. Si falla, la
  app arranca igual y lo dice en el log; la métrica no frena ningún pedido.
  Usá el mecanismo que ya tenga el proyecto para esto; si no hay uno o hay
  dos que compiten, preguntá en la **D34** antes de inventar otro.
- **Lo demás:** hacé la lista de las otras columnas del modelo que una base
  vieja podría no tener (comparando el modelo con lo que agregan los
  scripts de migración), una línea por cada una, a «riesgos». Sólo
  `api_logs.owner_username` entra en esta pieza.

Pruebas: en Postgres 16 desde una base sin la columna y con filas, la
columna y el índice quedan, las filas viejas siguen, la métrica se graba
(dueño: ver D34), y dos arranques seguidos no cambian nada; en SQLite igual;
una falla simulada de la migración no frena el arranque. Un sabotaje por
regla. Línea en `CHANGELOG.md`. Es una migración: revisión fuerte.

### DISCO-1 — hecha, sin entregar (encargada 2026-10-28 07:00 UTC)

DATOS-1 quedó hecha (`c996ad4`). Sigue la tuya de la Fase 3 que es sólo
código: **DISCO-1**, hallazgo D4 de `AUDITORIA-2026-10-06.md`. BACKUP-1
(D1) queda para después: necesita algo fuera de Railway y eso lo decide
Emi. En commits aparte encima de `c996ad4`, con su propio `/entregar`
después del de DATOS-1.

- **El problema:** el historial de NCM de cada despachante
  (`load_ncm_historial` / `save_ncm_historial`, `main.py` cerca de la línea
  9032) vive en `ncm_historial_<usuario>.json` dentro de `DATA_DIR`, en el
  disco de Railway, que se borra en cada publicación. Lo usan sugerir NCM
  (fuente «historial»), `/api/ncm/guardar-uso` y `/api/ncm/import-historial`.
- **Premisa primero:** confirmalo con el código (que `DATA_DIR` no es un
  volumen que sobreviva; no ves las variables de Railway, decilo como
  supuesto) y hacé la lista de todo lo demás que se escribe en `DATA_DIR`
  (`descargas/`, `generated/`, `localStorage_backup.json`…), con una línea
  por cada uno: si es un dato del usuario que se pierde o un archivo de paso.
  **Sólo el historial de NCM entra en DISCO-1**; lo otro va a «riesgos» y,
  si hay algo que se pierde y duele, me lo proponés.
- **Qué hacer:** el historial pasa a la base, por dueño, con el mismo
  comportamiento que hoy: misma clave (la descripción tal como se guarda),
  `ncm` y `count`, incrementa al confirmar de nuevo, actualiza el NCM si
  cambió, la importación suma igual que hoy y cuenta igual los duplicados.
  Tabla nueva solamente, sin tocar las existentes. Dos confirmaciones
  simultáneas de la misma descripción no pierden ninguna cuenta (hoy el
  archivo pierde una: no copies eso). Un dueño nunca ve ni pisa el
  historial de otro.
- **Lo que ya está en disco:** si al arrancar hay archivos
  `ncm_historial_*.json`, se pasan a la base una sola vez (correr dos veces
  no duplica cuentas) y el archivo no se vuelve a leer después. Un archivo
  roto no frena el arranque: va al log.
- **Migración:** como se crean hoy las tablas nuevas; probada en Postgres
  16 descartable (el 55432) desde una base con el esquema de `c996ad4` y
  datos, además de SQLite. Decí en el informe qué pasa en producción la
  primera vez que arranca.

Pruebas: guardar, sugerir e importar con el historial en la base; que
sobrevive a borrar `DATA_DIR` (lo que hoy pasa en cada publicación); dos
dueños separados; dos confirmaciones a la vez; la carga de los archivos
viejos, dos veces; un archivo roto. Un sabotaje por regla. Línea en
`CHANGELOG.md`. Toca datos de los usuarios y migración: revisión fuerte.
Si alguna de estas reglas choca con el código, preguntá en la **D33**.

### DESPACHO-1b — hecha, sin entregar (encargada 2026-10-28 05:00 UTC)

SEGURO-1 quedó hecha. Mientras esperás el cupo de las 18:00 UTC, la lectura
de DESPACHO-1 (`ROADMAP.md`, Fase 1c, fila 7), en commits aparte encima de
SEGURO-1 (`371cde2`), con su propio `/entregar` después del de SEGURO-1.

- **Qué lee:** lo de `DESPACHOS-FORMA.md`, «Lo que DESPACHO-1 lee para el
  catálogo»: por renglón (ítem o subítem) posición SIM, descripción,
  sufijos de valor, origen, unidad, cantidad, valor unitario y kilo neto.
  Se lee **por rótulo, no por posición**; números `1.234,56`; con unidad
  `SUBITEM`, un renglón por subítem con sus valores y sufijos. Lo que no
  encuentra queda marcado; nada se rellena. El resto del despacho no se
  guarda.
- **Cómo:** sobre el texto del PDF, sin Gemini. Premisa primero: mirá qué
  usa ya el repo para sacar texto de un PDF y si alcanza. Un PDF sin texto
  (escaneado) da un aviso claro y no guarda nada. Si algo de esto no se
  puede sin Gemini o sin una librería nueva, es la D31 y seguís con lo que
  no depende de ella.
- **Pantalla:** se revisa y se edita renglón por renglón antes de guardar
  en el catálogo de ese cliente (el mismo de DESPACHO-1a, con
  `_get_owned_client`: un cliente ajeno da el 404 de hoy). Lo marcado como
  no encontrado se ve marcado.
- **Nunca** arma un TXT ni una operación. El lector de facturas sigue
  rechazando despachos: una prueba lo muestra.
- **Datos:** los tres despachos reales no los vas a ver y no entran nunca.
  El sintético lo arma la prueba con la forma de `DESPACHOS-FORMA.md` y
  valores inventados: dos ítems, uno con subítems, un `AI` con espacios, un
  carácter con tilde roto («Las dem?s»), FOB y flete en divisas distintas,
  y un renglón al que le falta el kilo neto.

Pruebas: cada rótulo leído; subítems; sufijos con y sin paréntesis; el
faltante marcado y no rellenado; rótulos en otro orden en la hoja (se lee
por rótulo); el PDF sin texto; que el lector de facturas lo sigue
rechazando; aislamiento (otro dueño, otro cliente); que no se crea ninguna
operación. Un sabotaje por regla. Línea en `CHANGELOG.md`. Toca datos de
clientes: revisión fuerte. Tu próxima D es la **D31**.

### SEGURO-1 — hecha, sin entregar (encargada 2026-10-28 04:00 UTC)

En commits aparte encima de SUFIJOS-2 (`4ca6829`), con su propio
`/entregar` después del de SUFIJOS-2. Respuesta del despachante (pregunta
4, `PREGUNTAS-DESPACHANTE.md`, D14 de VALOR-1): en **CIF, CIP, DPU, DAP y
DDP** el seguro ya está en el precio.

- **La regla:** con esos cinco incoterms el sistema no sugiere el 1 %: no
  hay botón «Calcular seguro». El seguro se sigue declarando (el despacho
  CIF trae el suyo): el campo queda, se carga a mano o lo lee el lector, y
  sale en el TXT como hoy. CFR, CPT y los demás siguen con el botón.
- **Dónde vive:** en el servidor, donde se arma `seguro_sugerido`
  (`maria_generator.py`, cerca de la línea 943), y el botón sigue a lo que
  diga el servidor. Esconderlo sólo en `finalize.js` no alcanza: la
  sugerencia seguiría viva y una prueba de Python no la cubre. Premisa
  primero: comprobá que ese código conoce el incoterm. Si no se puede sin
  salir del alcance, es la D30 y seguís con lo que no depende de ella.
- **Cambio de incoterm después de calcular:** si el seguro lo calculó el
  sistema (`seguro_calculado`) y el incoterm pasa a uno de los cinco, ese
  seguro se borra y el campo queda como «para completar», con el mismo
  mecanismo que un campo sin leer. Un seguro leído de la factura o escrito
  por el usuario no se toca. Comprobá que un campo «para completar» no deja
  generar en silencio con seguro cero; si lo deja, es la D30.
- **Incoterm:** mayúsculas, minúsculas y espacios dan lo mismo. Vacío o
  desconocido, como hoy (con botón).

Pruebas: los cinco sin sugerencia ni botón; CFR y CPT con botón; una
operación CIF con su seguro en el TXT; minúsculas y espacios; vacío; el
cambio de incoterm en los dos sentidos (el calculado se borra, el escrito
queda); un sabotaje por regla (uno de los cinco fuera de la lista, la
regla sólo en la pantalla, el calculado que sobrevive al cambio). El golden
no se toca.

### SUFIJOS-2 — hecha, sin entregar (encargada 2026-10-28 03:00 UTC)

DESTINO-1 ya está hecha y el cupo vuelve a las 18:00 UTC: mientras tanto,
SUFIJOS-2, en commits aparte encima de DESTINO-1 (`4905cd8`), con su propio
`/entregar` después del de DESTINO-1. Respuesta del despachante (pregunta 2,
`PREGUNTAS-DESPACHANTE.md`):

- **Sufijo de código libre:** un número puede llevar coma. Hoy `AF(2.5)`
  sale `AF(2 5)`: el número cambia. Tiene que salir `AF(2,5)`.
- **Sufijo que pide número:** sin decimales. Uno con decimales no se
  redondea en silencio: aviso que nombra el ítem y el sufijo, y no se genera.
- **Ninguno vacío:** `AA()` hoy pasa. Mismo aviso, no se genera.

Premisa primero:
- comprobá en el código, o en el catálogo de sufijos que ya tenga, cuáles
  piden número;
- comprobá que una coma no rompe el formato del campo en el TXT.

Si alguna de las dos no se puede saber desde el repo, es la D29 y seguís
con lo que no depende de ella.

Pruebas: los tres casos, uno que hoy está bien y sigue igual, y un sabotaje
por regla. Toca el TXT: el golden no se toca.

## Qué pasó el 2026-10-24

Emi y el despachante cargaron en el MARIA un TXT de CDI de una factura real
(decenas de renglones de un mismo producto en varios colores y medidas,
una sola posición SIM, origen China, CFR). Entró después de doce correcciones a mano. Cada una es
un defecto del generador. La versión que cargó tiene esta forma (valores
inventados acá):

```
[DDT]
ISTA=IC05
IDSO=AB1234CD                ← corto: con 19 caracteres el MARIA lo rechaza
CDDTEXE=01
CDDTBUR=001
CDDTTYPDEC=IC05
CDDTAGR=20111111112          ← CUIT del despachante: sin esta línea, «No existe el campo CDDTAGR»
CDDTIMPEXP=I
...
MDDTFLE=3480.00              ← CDI escribió 3.48: tomó «3.480» como decimal
...
[DVD]
LDVDREFDOC=<número real de la factura>   ← CDI escribió un pedazo («E7L1-1»)
...
[ART]
NART=0001
CARTSBITEM=S                 ← un ítem por posición, con subítems
CARTUNTDCL=03                ← m² (CDI puso 07 = unidad)
QARTUNTDCL=<suma de m²>
CARTUNTEST=01                ← kilogramo, la unidad estadística de VUCE
QARTUNTEST=<igual a QARTKGRNET, al centésimo>   ← si no, error 2122
QARTKGRNET=<kilo neto>
...
[SBT]
NART=0001
ISBT=0001
MSBTFOB=...
QSBTUNTDCL=...
MSBTUNITAR=...
IEXT=1-1
CSBTSVL=AA(MARCA)-AI(500G AZUL001 120CMX40M)-   ← AI distinto por renglón; sólo letras, números y espacios
QSBTUNTEST=<kilos del renglón>
```

Todas las líneas terminan en CRLF (una línea sin CR: «falta carácter de fin
(crlf) en línea 15»). El MARIA no acepta guiones, puntos ni caracteres raros
dentro de los valores de los sufijos: van espacios. El guión que separa un
sufijo del otro (`)-`) sí.
