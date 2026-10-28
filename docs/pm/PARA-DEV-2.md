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

## Emi dijo que sí a las dos (2026-10-28 12:15 UTC): EMAIL-1 y CONEXIONES-1

Las dos entran al roadmap (Fase 3, tuyas). En commits aparte encima de
`e1b3129`, cada una con su propio `/entregar` después del de ABUSO-1, en
este orden. Tu próxima D es la **D38**.

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

## D37 (2026-10-28): (2) por ahora, sobre `76def65`

ABUSO-1 no cambia por esto. El aviso «Event loop is closed» queda a la
vista: sin `filterwarnings` y sin repetir la suite hasta que salga verde.
Tampoco tocás los middlewares: tu hipótesis no está confirmada y el corte
ya pasa en la base `895ee73`. En riesgos va: que `session.close()` de
`get_async_session` se cancela después de la respuesta, en cuántas corridas
lo viste, que ya pasaba antes de ABUSO-1 y que no medimos si en producción
deja conexiones colgadas. Tu (1), medir con uvicorn y Postgres 16 muchas
respuestas 401 mirando `pg_stat_activity` y el pool, y pasar los
middlewares a ASGI puro sólo si quedan conexiones colgadas, es una pieza
nueva: Emi dijo que sí (CONEXIONES-1, arriba).

## D36 (2026-10-28): (2) por ahora, sobre `abdc0db`

Bien visto. En ABUSO-1 no se toca cómo se compara el email, como hiciste;
el contador por email en minúsculas queda. Tu (1) es una pieza nueva
(cambia recuperar usuario y contraseña, y el PUT del perfil) y necesita
una consulta en producción que corre Emi: se la propongo de día,
recomendada, y si dice que sí entra al roadmap después de ABUSO-1. Anotá
en riesgos los dos lugares que comparan exacto y el PUT que deja crear
pares. Decidido por la PM. Tu próxima D es la **D37**.

## D35 (2026-10-28): (1) en las cinco, sobre `e25e87c`

Decidido por la PM; Emi confirma de día los números (b) y el supuesto del
proxy (a). Seguí con S4, S6 y C9 sin esperarla.

- **a (1):** un solo helper para `login_attempts`, `reset_attempts` y
  slowapi; toma la **última** IP de X-Forwarded-For, saltos configurables
  (default 1); sin el header, `client.host`. La línea de log en el 429 del
  login (IP tomada y cantidad de entradas del XFF) es **obligatoria**: es lo
  único que valida el supuesto después de publicar.
- **b (1):** tus números. Escribí en el informe por qué alcanzan (por
  ejemplo, tres invitados de ORG-1 de la misma oficina en una hora quedan
  bajo 5/hora). El tope de 16 KB va en S5, como dijiste.
- **c (1):** los mensajes quedan. En el informe, la enumeración de S6 figura
  como **mitigada por el límite, no cerrada** (se cierra con la verificación
  de email, que es otra pieza).
- **d (1):** sin sesión se guardan sólo `pricing_cta_clicked`,
  `hero_cta_clicked` y `register_pending_verify`, en una lista explícita y
  con límite; cualquier otra acción sin sesión no se guarda.
- **e (1):** los contadores de login y de recuperación pasan a una tabla.
  Con memoria, las pruebas de ABUSO-1 dan verde y el abuso sigue abierto al
  reciclar el worker. `--max-requests` del Dockerfile no se toca.
  Condiciones, antes de construirla:
  - incremento atómico (C6 ya mostró carreras con pedidos en paralelo):
    una prueba con pedidos simultáneos en PG16;
  - tamaño acotado: las filas vencidas se borran al escribir o al arrancar;
  - se crea al arranque con el mismo patrón `_migrate_*` de DISCO-1 y
    OBSERVABILIDAD-1, en PG16 y SQLite;
  - un solo camino, haya o no `REDIS_URL`;
  - **commit propio** para la tabla, así la migración se revisa sola.
  El 5/min de slowapi en el login queda en memoria (slowapi no guarda en
  SQL): lo que importa es el bloqueo de 15 minutos en la tabla. Anotalo en
  riesgos.
- **recover-username y mayúsculas:** entra, porque ya tocás esa ruta:
  comparar el email sin distinguir mayúsculas, con su prueba. Si dos cuentas
  pueden tener el mismo email cambiando sólo mayúsculas, no lo toques y
  abrí la **D36**.

Revisión fuerte (autenticación y migración).

## D34 (2026-10-28): (a), sobre `39be45e`

(a), como ya aplicaste: OBSERVABILIDAD-1 sólo hace que la columna y su
índice existan. Que `MetricsMiddleware` grabe el dueño leyendo el token
toca sesión y autenticación: es otra pieza, no entra acá. Anotala en
«riesgos» como propuesta (una línea: qué haría y qué toca). Donde la tarea
decía «la métrica se graba con su dueño», vale «la métrica se graba y no
falla». Decidido por la PM. Tu próxima D es la **D35**.

## D33 (2026-10-28): (a), sobre `88b22c8`

Para el código, (a): no se cambia nada. El cargador de los
`ncm_historial_*.json` queda como está, así que (b) sigue siendo posible
sin tocar código. Si se rescatan o no los de producción lo decide Emi el
día que se publique DISCO-1: se lo cuento de día, con tu recomendación.
Decidido por la PM. Anotá en «riesgos» que, si nadie hace (b), el primer
deploy con DISCO-1 pierde los historiales que haya, igual que todos los
deploys hasta hoy. Tu próxima D es la **D34**.

## D32 (2026-10-28): (a), sobre `2efdffc`

Borrar un cliente borra también los presupuestos compartidos de sus
operaciones, en la misma transacción. Ya borra sus operaciones, y la copia
del presupuesto tiene datos del cliente: es lo único que cumple un pedido
de borrado. Pruebas además de las de la tarea: los presupuestos de otro
cliente y de otro dueño siguen andando; si algo falla a mitad, no se borra
nada (ni cliente ni presupuesto); el link borrado da 404. Si la pantalla ya
avisa qué se borra con el cliente, que nombre también los links
compartidos; si no avisa nada, no se agrega. El link que deja de andar va
en «riesgos» y en `CHANGELOG.md`. Decidido por la PM.

## D31 (2026-10-28): (a), sobre `e59e1a8`

El catálogo guarda lo que ya tiene columna; sufijos, unidad, posición
completa y divisa se ven en la revisión y no se guardan. Sin migración y
sin tocar el catálogo de DESPACHO-1a. Anotá en el informe de DESPACHO-1b,
en «riesgos», los dos costos que nombraste: el valor unitario sin divisa y
dos subítems que sólo difieren en sufijos fundidos en un producto. Guardar
lo demás (tu (b)) es una migración sobre datos de clientes y no está en el
roadmap: si hace falta, se la propongo a Emi cuando haya un uso (por
ejemplo, sugerir sufijos al armar una operación). Decidido por la PM.

## D30 (2026-10-28): (a) por ahora, sobre `371cde2`

SEGURO-1 se entrega como está: un seguro «para completar» avisa en pantalla
y no frena el TXT. Frenar en el servidor (tu (b), un cero real escrito a
mano) es una pieza nueva y no está en el roadmap: se la propongo a Emi de
día como **SEGURO-2**, con mi recomendación de (b). No la empieces hasta que
la veas acá. Anotá el riesgo (seguro 0 en el TXT si nadie lo completa) en
el informe de SEGURO-1, en «riesgos».

## D29 (2026-10-28): opción (a), sobre `4ca6829`

Los `Z` piden número y los `A` son libres: `PIDE_NUMERO = ("Z",)` queda
como está. Lo sostienen la tabla de ARCA (los `Z` son magnitudes, y en
algunos ARCA elige la unidad para no usar decimales) y el archivo aceptado
(`ZA(016384)`). Se revierte en esa línea. El costo que nombraste (unas 90
descripciones `Z` con decimales naturales: %, ppm, quilates) va en la
pregunta 10 al despachante (`PREGUNTAS-DESPACHANTE.md`), que Emi manda de
día. Si contesta otra lista, la lista cambia con sus pruebas, en otra
pieza. Lo de rellenar los `Z` con ceros a seis dígitos no entra ahora.
Decidido por la PM.

## D28 (2026-10-28): opción (a)

Tenés razón: la regla «`IVAAD1` se lee como bien de uso de una persona» la
puse yo, y deja al golden de 2025 sin entrada que lo reproduzca. Va la
**(a)**: el golden no se toca; las seis pruebas comparan el archivo entero
salvo el `MCPL` de `GANANCIASOP3`, y esa línea tiene que decir exactamente
`USOPAR`. La diferencia queda escrita en la prueba con referencia a la
pregunta 7. No se espera la respuesta: la tabla del despachante es
explícita, y lo de 2025 era el defecto que DESTINO-1 corrige. Si la
pregunta 7 dice otra cosa, se reabre. Decidido por la PM.

## ORG-1 — tarea activa

Invitaciones al estudio (`ROADMAP.md`, Fase 2; C7 de
`AUDITORIA-2026-10-06.md`). **Toca permisos: revisión fuerte.** Diff de
revisión desde la punta de mi rama. Trae mi rama antes de arrancar.

**Alcance:** las invitaciones funcionan sin 500, quedan atadas al email
invitado y respetan el tope de usuarios del plan. **No entra** lo demás de
la fila 7 de `REPRODUCCION-ARGON-2026-10-24.md` (miembros que no ven los
clientes del estudio, cancelar sobre el usuario, cobros del miembro raso,
el trial al sacar un miembro, vaciar el email): espera la decisión de Emi.
Si para que ORG-1 funcione hace falta algo de eso, es una D.

El código: `invite_to_organization` y `validate_invitation` en
`proyecto_maria/main.py` (~9480 y ~9540), el registro con `invite_token`
(~2898-2921), `Invitation` en `database/models.py` y el plan en
`services/billing_service.py`.

1. **Premisa primero.** Reproducí el 500 en Postgres antes de arreglar.
   Mi sospecha, sin correr: `expires_at` es `DateTime(timezone=True)` y se
   compara con `datetime.utcnow()`, sin zona; en Postgres vuelve con zona y
   la comparación revienta, en SQLite no. Hay Postgres 16 instalado en el
   contenedor (`/usr/lib/postgresql/16`). Si es otra cosa, decímelo con la
   salida.
2. **Sin 500 en las dos bases.** Validar, registrarse con invitación y una
   invitación vencida dan la respuesta de hoy en SQLite y en Postgres. Los
   registros viejos de SQLite vienen sin zona: también. Una prueba que sólo
   corre en SQLite no distingue este defecto: corré contra un Postgres
   local, o inyectá un `expires_at` con zona.
3. **Atada al email.** Al registrarse con `invite_token`, el email del
   registro (con `strip().lower()`, como lo guarda la invitación) tiene que
   ser el invitado. Si no coincide o falta: 400 y la invitación **no** se
   gasta. Una cuenta que ya existe y se suma por invitación no entra: hoy
   sólo existe el camino del registro.
4. **Tope del plan.** Sale de `billing_service.get_plan(org.plan or
   "premium")["users"]`, nunca un 3 escrito a mano. Cuentan los usuarios con
   el `organization_id` del estudio (el dueño también). Al invitar: 400 si
   miembros más invitaciones pendientes sin vencer llegan al tope. Al
   registrarse: 400 si los miembros ya llegaron, sin gastar la invitación.
   Sacar un miembro libera el lugar (ya lo hace).
5. **Un solo uso, de verdad.** Hoy el usuario y el «accepted» se guardan en
   dos commits: dos registros a la vez con el mismo token pasan los dos. La
   invitación se gasta en la misma transacción que el alta, con una
   actualización condicionada a `status = 'pending'`, y se comprueba que
   tocó una fila. Contame qué deja una carrera de dos registros a la vez; si
   en SQLite no se puede provocar, decilo.

**Pruebas:** por punto, casos de la familia y no un solo ejemplo; las
guardas (una invitación válida del email correcto con lugar entra igual que
hoy); un sabotaje por punto que vuelva a lo de hoy; corré
`scripts/testing/ataque_aislamiento.sh`. Suite completa sobre el SHA que
entregás.

**No se toca:** el alta sin invitación, el cobro y los planes, lo que ve
cada miembro.

**Tu cupo:** hasta el 28/10 a las 18:00 UTC no tenés subagentes ni
`/code-review`. Programá, armá casos y sabotajes ya; `/entregar` espera a
que vuelva el cupo. Yo sumo un adversario de permisos en mi revisión.

**Puede pausarse:** le pregunto a Emi si tres errores del TXT de la
auditoría (8.1, 9.2 y 8.2) van antes. Si dice que sí, te aviso acá y ORG-1
queda donde esté.

**DESTINO-1: empezala ya** (2026-10-28 02:00 UTC), mientras esperás el
cupo; antes decía «apenas entregues». En commits aparte, **encima** de lo
que hoy es ORG-1, ORG-1b y DESPACHO-1a: esa entrega nombra su propio SHA
(el último de esas tres piezas, antes de cualquier commit de DESTINO-1),
con su suite sobre ese SHA, y DESTINO-1 se entrega aparte, con su
`/entregar`, cuando esté. Si al volver el cupo DESTINO-1 está a medias,
primero entregás ORG-1 y después seguís. Datos que llegaron el 28/10
(`PREGUNTAS-DESPACHANTE.md`, «Respuestas del 2026-10-28»):

- `GANANCIASOP3` deja de ser `COMERC` fijo. Por operación, con cambio por
  ítem como hoy `IVAADICIONAL1`, se elige el destino y salen **los dos
  códigos juntos**, sólo en estos pares: comercialización o reventa
  `COMERC` + `NO_VALIDA`; bien de uso de la empresa `BDEUSO` + `IVAAD2`;
  bien de uso de una persona `USOPAR` + `IVAAD1`. Por defecto,
  comercialización.
- Hoy «uso particular» sale `COMERC` + `IVAAD1`, un par fuera de la lista:
  eso se corrige. Un dato guardado con el valor viejo (`iva_adicional`
  `IVAAD1`) se lee como bien de uso de una persona.
- `maria_golden_anon.TXT` (2025, aceptado por el MARIA) trae `COMERC` +
  `IVAAD1`: el golden no se toca; si una prueba lo compara campo a campo,
  avisá antes de cambiarla. Le pregunto al despachante (pregunta 7).
- Pruebas: los tres pares en el TXT, el defecto, el cambio por ítem, un
  valor que no es ninguno de los tres (error, no se genera), y un sabotaje
  por par. Es un campo de impuestos: revisión fuerte.

Después: **SUFIJOS-2**, **SEGURO-1**, **DESPACHO-1b**, **DATOS-1** y
**DISCO-1**, **OBSERVABILIDAD-1** y **SESION-1** (hechas, sin entregar)
y **ABUSO-1** (abajo, empezala ya). PESO-NETO-1 y PRORRATEO-1 siguen esperando al
despachante.

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

### DATOS-1 — hecha, sin entregar (encargada 2026-10-28 06:00 UTC)

DESPACHO-1b quedó hecha. Lo que te queda en las Fases 1c y 2 espera a
alguien de afuera (PESO-NETO-1, MARIA-6 y PRORRATEO-1 al despachante,
LEGAL-1 al texto de Emi), así que seguís con la primera tuya de la Fase 3
(`ROADMAP.md`): **DATOS-1**, hallazgos D5, D2 y D6 de
`AUDITORIA-2026-10-06.md`. En commits aparte encima de DESPACHO-1b
(`e59e1a8`), con su propio `/entregar` después del de DESPACHO-1b.

- **D5, borrar un cliente con presupuesto compartido:** hoy da error en
  Postgres, así que no se puede cumplir un pedido de borrado de datos.
  Premisa primero: reproducilo en Postgres 16 descartable (el 55432 de
  ORG-1) y mirá qué tablas apuntan al cliente. Borrar el cliente tiene que
  funcionar, sólo para su dueño (`_get_owned_client`, otro dueño 404). Si
  para eso hay que elegir entre borrar el presupuesto o dejarlo sin
  cliente, es la **D32** (contestada arriba: (a)).
- **D2, `/health` honesto:** con la base caída responde 503, no 200, y no
  muestra el texto del error al público (va al log). Railway usa `/health`
  para dar por buena una publicación (`railway.json`, 60 s): comprobá con
  el código qué pasa al arrancar (el comentario de `main.py` cerca de la
  línea 664 quiere que la app arranque «rota» para diagnosticar) y decí en
  el informe qué hace Railway con una publicación nueva si la base no
  contesta. `railway.json` no se toca. `/admin/health/detailed` queda fuera.
- **D6, sin detalles de error al público:** los dos manejadores de 500 de
  `main.py` (cerca de las líneas 412 y 440) dejan de devolver `dev_detail`,
  siempre: el detalle ya va al log, y no depende de detectar producción.
  Los 4xx siguen con su `detail` como hoy. Premisa primero: qué JS lee
  `dev_detail`, y que siga funcionando sin él.

Pruebas: el borrado en Postgres con presupuesto compartido (y que otro
dueño no puede); `/health` 200 con base y 503 sin ella, sin texto del
error; un `HTTPException` 500 y una excepción no manejada sin `dev_detail`,
con el detalle en el log; un 4xx igual que hoy. Un sabotaje por regla. Línea en `CHANGELOG.md`. Toca datos y
lo que se muestra al público: revisión fuerte y `/security-review`. Tu
próxima D es la **D33**.

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

### DESPACHO-1a — pieza nueva del roadmap; hacela mientras esperás el cupo

Emi sumó **DESPACHO-1** el 28/10 (`ROADMAP.md`, Fase 1c, fila 5): subir un
despacho ya oficializado (OM-1993-A) para armar el catálogo del cliente. Los
ejemplos llegaron el 28/10 pero son reales y sin tapar: no los vas a ver.
Su forma, sin datos, está en `DESPACHOS-FORMA.md`; la lectura se hace
después de DESTINO-1, SUFIJOS-2 y SEGURO-1, con un sintético armado desde
ahí.

Lo que no depende del ejemplo, ahora, como **DESPACHO-1a**:

- **Bajar el catálogo de un cliente en Excel** desde la pantalla de
  catálogo: un renglón por producto del historial del cliente
  (`ClientProductHistoryModel`) con posición, descripción, origen, valor
  unitario, cantidad y peso promedio, veces usado y última vez.
- Sólo los productos de ese cliente y de ese dueño (`_get_owned_client`);
  un cliente ajeno da el mismo 404 que hoy.
- Celdas que empiezan con `=`, `+`, `-` o `@` se escriben como texto (sin
  fórmulas): las descripciones vienen de facturas de terceros.
- La posición sale como texto, con ceros y letra como está guardada.
- Pruebas: aislamiento (otro dueño, otro cliente), la celda con `=`, un
  catálogo vacío, y que el archivo se abre con openpyxl y trae lo guardado.
  Un sabotaje por cada una. Línea en `CHANGELOG.md`.
- Commits separados sobre ORG-1b; se entrega en el mismo `/entregar` que
  ORG-1 y ORG-1b, pero en su propio apartado del informe con su diff
  propio, como hiciste con ORG-1b.

Si al mirar encontrás que la descarga ya existe o que el catálogo del
cliente no es ese modelo, avisá antes de construir.

### Tu aviso del 27/10 (`de8d175`, sin entregar)

Leído. Está bien esperar el cupo: no la reviso hasta tu `/entregar`. Los
supuestos reversibles los miro en la revisión.

- **D26: (a) por ahora.** Cancelar una pendiente es un endpoint nuevo y no
  está en el roadmap; se lo propongo a Emi con tu recomendación (b). No lo
  empieces sin mi aviso.
- **D27: (b), como ORG-1b.** Entra en la línea de ORG-1 del roadmap
  («invitaciones que funcionan»): sin esto, el punto 3 deja al invitado con
  un 400 evitable. Decidido por la PM.

### ORG-1b — hacela ahora, mientras esperás el cupo

En `landing.html`, cuando `/api/invitations/{token}` responde válida:

1. El email del registro se completa con `data.email` y queda de sólo
   lectura (`readOnly`, no `disabled`, para que viaje en el envío). Una
   línea cerca dice que es el email al que te invitaron.
2. Si `data.email` viene vacío, o no hay `invite`, o el token no es válido,
   el campo queda como hoy: vacío y editable.
3. El servidor no cambia: el 400 del punto 3 sigue siendo la guarda.

**Pruebas:** en un navegador (Playwright), con datos sintéticos: invitación
válida (email completo y de sólo lectura, el registro entra), sin `invite` y
con token inválido (campo editable y vacío), y una invitación válida con el
email cambiado a mano en el DOM (sigue el 400). Un sabotaje que saque el
completado y dé rojo. Una línea en `CHANGELOG.md`.

**Entrega:** commits aparte encima de `ddfc798`, en el mismo `/entregar` que
ORG-1, con su propio SHA de producto en la tabla, para que pueda revisarla
separada.

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

## Respuestas a tus D

MARIA-7, 2026-10-24:

- **D1: (a).** Le pregunto al despachante el largo máximo y si el MARIA
  rechaza un IDSO repetido (los choques de la tabla de la reproducción). No
  cambies `NDDTIMMTRN` ni `IEXT` sin esa respuesta.
- **D2: (b)**, devolución punto 2.
- **D3: (a).** El archivo aceptado trae «S.A.», comas y paréntesis.
- **D4: (a).** El «mandala igual» es propuesta, si aparece un proveedor que
  lo necesite. Las palabras de cuenta, devolución punto 3.
- **D5: (a).** La (c), validar la fecha en el alta, la paso a la cola de la
  Dev técnica.
- **D6: (b)**, devolución punto 5.
- **D7: (a)** mientras pregunto al despachante cómo va un decimal en un
  sufijo y si acepta un valor vacío.
- **D8: (a).** La v1 no es la pantalla en uso; queda con el aviso.

SEPARADORES-1 y 1b, 2026-10-25: **D19 (b)**, **D20 (a)**, **D21 (b)**
(SEPARADORES-1c). SUFIJOS-1: **D22 (a)**, **D23 (c)**. Todas decididas por
la PM (`DECISIONS.md`).

SEPARADORES-1c, 2026-10-27: **D24 (a)**, **D25 (b)** (SEPARADORES-1d).
Decididas por la PM. Aceptada en `140c122`.

ORG-1, 2026-10-27: **D26 (a)** por ahora (se lo propongo a Emi), **D27 (b)**
(ORG-1b, decidida por la PM). La próxima D es la D28.
