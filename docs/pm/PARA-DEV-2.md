# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

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

Tu cola queda: CATALOGO-LARGO-2 → RESET-1 → PYPDF-1 → ABUSO-1 → SUFIJOS-2+SEGURO-1 → **SEGURO-2** → EMAIL-1 →
CONEXIONES-1 → OBSERVABILIDAD-1 → ORG-1+D40. El detalle, al activarlas:

- **CATALOGO-LARGO-1 (datos):** con cliente y proveedor, una descripción de
  301 a 2000 caracteres no se pierde en silencio en la memoria del cliente
  ni en el catálogo (`product_key` de 300, `descripcion` de 500): se guarda
  o da un error a la vista, nunca 200 sin guardar. Migración, si hace
  falta, probada en Postgres descartable.
- **SEGURO-2 (TXT):** lo que SEGURO-1 sólo avisa frena la generación hasta
  que se corrija, también el 1 % mandado sin calcular (D30 b).

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

## Rojo de `despacho1b`: aceptado sobre `d69233c`, sin integrar (2026-11-07 PM)

`283 passed`, chequeo-6 `+0/−0` sin avisos; la causa la medí aparte (una
pasada del recolector con 3 M objetos gasta 0,53 s; con `gc.freeze`, 0).
Acta: `REPRODUCCION-DESPACHO1B-ROJO-2026-11-07.md`. **D106: (a), decidido
por la PM**, queda como riesgo. Tu orden no cambia: la devolución de ABUSO-2
primero, después ENTORNO-2. Próxima D: D107.

## ABUSO-2: devolución sólo de pruebas, sobre `8ad47ee` (2026-11-07 PM)

Reproducido igual al informe: chequeo-6 (`+35/−24`, avisos 0), `83 passed`,
`abuso2.sh` 9 en rojo con `fallas: 0`. **El producto queda como está.** Acta:
`REPRODUCCION-ABUSO-2-2026-11-07.md`.

**Causa:** las pruebas de `descontar` miran sólo que la cuenta que entra
recupere su lugar, no que el perdón sea exactamente lo propio, una vez y en
la misma ventana. Reproducido por mí, con `83 passed` cada uno:

1. Sacar el `where clave == clave` del `update`: el login correcto resta de
   todas las filas (otras IPs, `recuperar:*`, `registro:*`).
2. Leer la fila propia con `select` en vez de borrarla: cada login correcto
   repetido vuelve a restar.

La familia (Sonnet alto, también en verde): la cuenta que olvida a las 48 h,
lo vencido sin purgar antes de restar, la IP con otra ventana que la cuenta.
Pedido: un caso por causa donde la familia va como datos. Un login correcto
no cambia ninguna otra clave; dos logins correctos seguidos perdonan una sola
vez; lo propio vencido no se resta; la cuenta y la IP olvidan juntas. Commits
sólo de pruebas y sabotajes; el informe muestra cada mutación en rojo.

- **D105: (a), decidido por la PM.** Queda como riesgo: un mail menos por
  hora para quien pidió, y (b) reabre el salto por muchas IPs.
- Riesgos que quedan (Opus alto): con cuentas duplicadas por mayúsculas del
  email, recuperar manda 3 mails por cuenta; el tope de recuperar es de
  ventana fija (de antes).

Tu orden: **esta devolución** → ENTORNO-2 → D100 →
ENTRADAS-2 → el resto.

## ENTRADAS-1: aceptada sobre `c839197`, sin integrar (2026-11-07 PM)

Los cuatro puntos de la devolución dan rojo: `entradas1.sh` 32 `ROJO` sin
fallas. Mi ejemplo distinto (email con tope 101) cae en registro, estudio y
perfil. Acta: `REPRODUCCION-ENTRADAS-1-2026-11-07.md`. Lo que sigue de acá ya
está en tu orden: FRONT-422 (D100) y ENTRADAS-2 (D101, D104); D102 chore y
D103 en la cola.

## ENTORNO-1: aceptada sobre `83085e4`, sin integrar (2026-11-07 PM)

Reproducido: chequeo-6 igual al informe, `82 passed`, `entorno1.sh` 10 en
rojo, `cobro_mp2.sh` 23 en rojo, suite `5017 passed` igual a la tuya. Opus y
Sonnet alto con uvicorn real: con `ENVIRONMENT` ausente o desconocido no
abre ninguna puerta; nada serio introducido. Acta:
`REPRODUCCION-ENTORNO-1-2026-11-07.md`. **Supuestos S1 a S4: aceptados.**

- **D97: (a), decidido por la PM.** Que no arranque sin `production` y con
  clave débil es lo buscado; antes de publicar se confirma Railway con Emi.
- **D98: (a), pieza nueva ENTORNO-2**, después de ABUSO-2 (seguridad chica,
  Emi: «a cero»). Comportamiento pedido: con `ENVIRONMENT` ausente o
  desconocido, los controles de configuración se portan como en producción:
  CSRF bloquea, cookies `Secure`, `/docs` y `/openapi.json` cerrados, sin
  `DATABASE_URL` no cae a SQLite, VUCE simulado no permitido, y
  `ENABLE_SIMULATE_CHARGE` no abre el cobro simulado fuera de desarrollo.
  Un caso por causa con los valores como datos, como en `test_entorno1`.
  Sugerencia (no es criterio): que todos pregunten a `_es_desarrollo`.
- **D99: a Emi** (usuarios demo que ya estén en producción); no bloquea.
- A la cola de limpieza: los parches de `IS_PRODUCTION` en `test_email1` y
  la clase tautológica de `test_prelaunch_block3`.

El rojo de `despacho1b`: falló una vez en la suite entera y pasa solo;
diagnosticar la causa (el diff no toca el lector).

## PYPDF-1: aceptada sobre `974263e`, sin integrar (2026-11-06 PM)

Acta: `REPRODUCCION-PYPDF-1-2026-11-06.md`. Coincide con tu informe: las
cuatro suites de PDF dan `324 passed`, `rendimiento1c.sh` 18 en rojo sin
falla y el sabotaje de D87 da los 2 rojos que nombrás. Probé seis PDF
distintos de los tuyos: uno cortado, uno basura y uno con `/Pages` en ciclo
siguen dando «PDF inválido» sin colgarse; uno de 600 bytes con `xref 0 999999`
da «demasiado pesado». Es justo D90. Bien que no se fijara una versión vieja.

- **D89: (a)**, el tope de memoria del hijo queda como respaldo, sin bomba
  más grande. Decidido por la PM.
- **D90: (a)**, toda `LimitReachedError` es «demasiado pesado». Decidido por
  la PM.
- Los comentarios «más que lineal» y el trato distinto del tope en
  `_leer_hojas` los paso yo a `COLA-LIMPIEZA.md`.
- `despacho1b.sh` entero queda como puerta mía antes de publicar.

**Tu orden:** RESET-2 → ABUSO-1. Tus próximas D siguen en D91.

## RESET-1: aceptada sobre `02a21e7`, sin integrar (2026-11-06 PM)

Acta: `REPRODUCCION-RESET-1-2026-11-06.md`. Coincide con tu informe:
`test_reset1.py` 6 passed (4 rojos en la base, 1 en `82130a8`), Postgres
`fallas: 0` (base 3, `82130a8` 1), 8 sabotajes en rojo, chequeo-6 `+23/−15`
sin avisos. La suite da `5 failed, 4951 passed`: los 5 de D73, que dan igual
sobre la base. Probé un ejemplo distinto: el email va a otro y vuelve al
original, y el link de antes sigue muerto (en la base revive). Dos
adversarios con contexto nuevo no encontraron cómo entrar ni cómo trabar al
dueño. Bien también que avisaras el orden y por qué.

- **D82:** (a), queda así. Decidido por la PM.
- **D83:** (a), queda así: sólo corre con la variable prendida y con emails
  de la lista de prueba. Decidido por la PM.

RESET-2 (en `ROADMAP.md`): el link vuelve en la respuesta sólo en el entorno
de prueba, nunca por un `ENVIRONMENT` que falta.

## CATALOGO-LARGO-2: aceptada sobre `d5bc7c1` (pruebas `b0bbd8c`), sin integrar (2026-11-06 PM)

Acta: `REPRODUCCION-CATALOGO-LARGO-2-v2-2026-11-06.md`. Coincide con tu
informe: `test_catalogo_largo2.py` 40 passed, Postgres 21 OK y `fallas: 0`,
37 sabotajes en rojo sin falla, chequeo-6 `+153/−75` con el aviso de 78 netas que explicaste.
La suite da `5 failed, 4984 passed`: los 5 de D73. Probé ejemplos distintos de
los de la devolución (medio par bajo dentro del texto, objeto y decimal en
origen, entero en NCM y en proveedor, NCM entero por `guardar-uso`): los siete
dan 400 sin guardar nada; en la base, cuatro daban 500. Opus y Sonnet alto,
en PG 16, no encontraron 500 nuevos, escrituras a medias ni filas perdidas.
Sin integrar, por lo mismo que `ca87d82`.

Una corrección al informe: en D84 decís que el usuario ve qué fila corregir.
No es así: el 400 no nombra el ítem, `saveCatalogLearn` sólo mira `res.ok`, y
la pantalla dice «Algunos productos no quedaron» cuando no quedó ninguno
(`finalize.js:764-768`). No empeora la base, pero una premisa así tiene que
estar probada antes de ofrecerla para decidir.

- **D84: (a)**, el lote entero se rechaza. Que el 400 nombre el ítem y que la
  pantalla diga la verdad va a CATALOGO-3. Decidido por la PM.
- **D85: (a)**, a CATALOGO-3 con D76; suma el proveedor `"\x00"`, que hoy
  guarda bajo `vendor_id ""`.
- **D86: (a)**, a CATALOGO-3 con D78.
- **D87: (a)**, el patrón de `despacho1b.sh:325` en un commit de pruebas
  aparte, con su rojo, en tu próxima entrega (PYPDF-1).
- **A la cola de limpieza** (decidido por la PM): la fila que choca en
  `_migrate_catalogo_claves` (sin `ORDER BY`, log repetido en cada
  arranque); el índice de `_migrate_product_history_clave` sin
  `lock_timeout` (`main.py:1464`); lotes o `PUT` a la vez dan 500;
  `/api/catalog/lookup` con 500 y sin limpiar el NUL; precios raros; los
  mensajes del NCM («pasa de 2000» con tope 20, «La NCM» y «El NCM»).

CATALOGO-3 sigue esperando el sí de Emi.

## SESION-1: aceptada sobre `2e62761`, sin integrar (2026-11-06 PM)

Acta: `REPRODUCCION-SESION-1-v3-2026-11-06.md`. Coincide con tu informe:
`test_sesion1.py` 42 passed (13 rojos en la base), motores pg OK, 38 sabotajes
en rojo, chequeo-6 `+95/−89` sin avisos, suite `4933 passed` con sólo las 5 de
D73. Probé otro ejemplo del pool (40 `PUT` del perfil): ningún 500 y otro
usuario entra al instante; en la base, 39 respuestas 500 y 29,5 s. Las dos
causas quedan cerradas.

- Se integra junto con `ca87d82`, por lo mismo: debajo vienen piezas sin
  aceptar (ahora también CATALOGO-LARGO-2).
- **D73:** no se fija una versión vieja a ciegas. Primero hay que ver qué
  cambió en 6.21.4, que puede ser un arreglo de seguridad. Va como pieza chica
  **PYPDF-1**, después de RESET-1. Decidido por la PM.
- **D74: (a)**, se acepta así. Lo que queda (la conexión tomada durante
  bcrypt, Gemini en `/api/ncm/sugerir` y la subida pública de PDF) entra en
  CONEXIONES-1 con los números del acta. Decidido por la PM.
- **D75: (a)**, a `COLA-LIMPIEZA.md`. Decidido por la PM.
- **Pieza nueva RESET-1** (seguridad, chica; Emi: «arreglos chicos de
  seguridad a cero»). Va después de CATALOGO-LARGO-2, antes de ABUSO-1. El
  problema viene de antes: `reset_password` no invalida nada.
  - Un link de reset pedido antes de que el dueño cambie la clave o el email
    ya no sirve después de ese cambio.
  - Un link usado una vez no sirve una segunda vez, tampoco con dos usos a la
    vez (se consume atómico, probado en Postgres).
  - El caso lleva los cambios como datos: cambio de clave, cambio de email,
    otro reset y el mismo link dos veces.
- Las anclas de `csrf3.sh` las actualizo yo al integrar.
- **Sigue CATALOGO-LARGO-2**, como ya venías. Tus próximas D empiezan en D76.

## `ca87d82`: aceptadas RENDIMIENTO-1c, DESPACHO-1b, CATALOGO-LARGO-1 y DISCO-1, sin integrar (2026-11-05 20:45 UTC, PM)

Acta: `REPRODUCCION-MARIA-ca87d82-2026-11-05.md`. Todo coincide con tu informe:
despacho1b 138, disco1 46 y catalogolargo1 12 en rojo; suite con Postgres
`4537 passed`. No se integra todavía porque `ca87d82` trae debajo commits de
piezas con devolución abierta (SESION-1, ABUSO-1, OBSERVABILIDAD-1, SUFIJOS-2,
ORG-1). No tenés que hacer nada por esto: seguí con RENDIMIENTO-1d.

## RENDIMIENTO-1d: aceptada sobre `558c941`, sin integrar (2026-11-05 21:35 UTC, PM)

Las tres cosas quedan: la salida del hijo no pierde texto (también con un
locale que no es UTF-8, bien visto), el tope de 64 K y la fila por usuario
tienen caso y sabotaje. Probé otro ejemplo: `DBFF` con «€», `DFFF` con un
emoji en un par válido, y el hijo en `ascii` y `cp1252`. Verde en `558c941`,
rojo en la base. Acta: `REPRODUCCION-RENDIMIENTO-1d-v2-2026-11-05.md`.

- Se integra junto con `ca87d82`, por lo mismo: lo de abajo sin aceptar.
- D67 repetida: de acuerdo con «D67 (id a 60)». Tu próxima es D69.
- Hallazgo 2 de tu `/code-review` (par partido en dos glifos): queda así.
- **Sigue DESPACHO-1d**, que ya tenés hecho: cerralo con `/entregar`.

## DESPACHO-1d: aceptada sobre `528961b`, sin integrar (2026-11-05 22:45 UTC, PM)

Acta: `REPRODUCCION-DESPACHO-1d-2026-11-05.md`. Coincide con tu informe:
`test_despacho1c.py` 83 passed, `despacho1d.sh` 9 y `despacho1c.sh` 15
sabotajes con `fallas: 0`, chequeo-6 `+64/−45` con los dos AVISOs del
envoltorio del módulo (explicados). Mi ejemplo distinto: siete nombres de
proveedor (200 «é», 59 letras más «ñb», sólo emoji, sólo CJK, «İstanbul»
largo, «ǅ» repetido) dan siempre un id que cumple `is_valid_vendor_id`. Un
adversario con contexto nuevo no encontró nada que frene; lo que marcó ya
estaba antes (va al acta).

- **D69: (a)**, como lo entregaste. Decidido por la PM.
- Se integra junto con `ca87d82`, por lo mismo: lo de abajo sin aceptar.
- **CATALOGO-LARGO-2: Emi dijo que sí.** Va después de SESION-1. Tu próxima
  D es D71.
- SESION-1: ver arriba.

## Orden desde el 2026-10-29

1 y 2: reemplazados por el orden del 05/11, arriba.
3. SESION-1. 4. ABUSO-1. 5. SUFIJOS-2 y lo que se suma de SEGURO-1.
6. EMAIL-1: la D45 y el mutante. 7. CONEXIONES-1: la D46.
8. OBSERVABILIDAD-1. 9. ORG-1 + D40. Las devoluciones están abajo. Cada
una con su rojo, su sabotaje y `/entregar`; me despertás al entregar cada
una, sin esperar a juntar.

- **D48: (a), decidido por la PM, como pieza RENDIMIENTO-1c.** La
  validación del PDF corre en el proceso aparte, con tope de memoria y de
  tiempo, para leer despachos y leer facturas. La prueba: tu PDF de 200
  repeticiones no hace crecer la app, medido en el proceso de la app; y
  diez a la vez no frenan una subida normal. Está en producción: la
  publicación la decide Emi.
- **D45 (EMAIL-1): (1), decidido por la PM.** El tope por correo se
  normaliza igual en Python y en la base; rojo en Postgres 16 con «İ» y con
  otra letra de la misma familia (minúscula distinta en Python y en PG),
  sabotaje que lo rompa, y la prueba de `_cuenta_por_email` que ya te pedí.
- **D46 (CONEXIONES-1): (1), decidido por la PM, al final de la cola.**
  Esperás a que `api_logs` tenga todos los pedidos, un control que cancele
  el `close` y tenga que dar rojo, y cortes en vuelo de verdad. Hasta
  entonces la D37 sigue abierta.

## ORG-1 + D40: devolución, sobre `b358827` (2026-10-28 18:50 UTC)

Evidencia en `REPRODUCCION-ORG-1-D40-2026-10-28.md`. Lo que la D40 cierra
está bien: normalización, carrera en Postgres, tope en el registro y el
sacado que no vuelve. **Causa de la devolución:** las reglas de la D40
tienen filtros que ninguna prueba distingue, y el «Sumá» 4 de la
aceptación de ORG-1 no llegó. Cada punto, rojo antes del arreglo y con su
sabotaje:

1. **El «Sumá» 4 entero**, un caso por guarda (la lista está en la
   aceptación de ORG-1, abajo). Reproducido por la PM: con el control de
   dueño al invitar en `if False`, o sin el filtro por estudio al sacar,
   las pruebas de ORG-1 siguen en `81 passed`.
2. **Una invitación vencida queda vencida.** Sin `status == "pending"` en
   el `UPDATE` del registro, `92 passed` (corrida de la PM): falta el caso
   del mismo email con una vencida y una pendiente.
3. **El orden de los mensajes.** Con el estudio lleno, invitar un email que
   ya tiene cuenta da «Ese email ya tiene una cuenta…», no el del tope.
4. **El `UPDATE` va en la misma transacción que la cuenta,** con una prueba
   secuencial (hoy sólo la de carrera lo distingue).
5. **Lugar muerto, decidido por la PM.** Una invitación pendiente cuyo
   email ya tiene cuenta en CDI (en cualquier estudio o en ninguno) no
   ocupa lugar: no se puede usar nunca. Generaliza la regla de la D40.
   Reproducido por la PM: (A) el invitado se registra sin el link y su
   pendiente ocupa lugar hasta que el dueño la borra; (C) X tiene
   pendientes en A y en B, entra con la de A, y la de B queda ocupando
   lugar en B. Los dos, rojos, y la familia: cualquier camino por el que
   un email pendiente llegue a tener cuenta.
6. **A riesgos:** el modo `REGISTER_TEST_EMAIL_REPLACE`; invitar dice si un
   email tiene cuenta, sin límite de pedidos; cambiar el email del perfil
   no pide verificarlo (lo llevo a Emi como seguridad, no lo arreglás acá).

SQLite y Postgres 16, CHANGELOG, commits separados y `/entregar`.

## OBSERVABILIDAD-1: devolución, sobre `39be45e` (2026-10-28 18:40 UTC)

Evidencia en `REPRODUCCION-OBSERVABILIDAD-1-2026-10-28.md`. La migración
cumple lo pedido: sólo agrega, dos arranques no cambian nada y si falla la
app arranca. **Causa de la devolución:** la pieza vuelve a grabar la
métrica sin mirar qué graba, y eso no se puede publicar así.

1. **Lo que graba la métrica, decidido por la PM (dentro de esta pieza).**
   Reproducido por la PM: `MetricsMiddleware` guarda el camino crudo y
   `/api/dev/stats` lo muestra; ahí quedan el token de invitación entero,
   el hash de un presupuesto público, la preferencia de pago, el nombre de
   archivo y el CUIT. Que guarde el molde de la ruta
   (`/api/invitations/{token}`), y un pedido que no coincide con ninguna
   ruta guarde `<sin ruta>`. Rojo antes del arreglo: cada ruta de la app
   con parámetro en el camino guarda su molde, sacada de la lista de rutas
   de la app y no de una lista a mano, más un camino que no existe. Un
   sabotaje que vuelva al camino crudo y dé rojo.
2. **El lock exclusivo dura sólo el `ALTER`.** Hoy el `ALTER` y el índice
   van en la misma transacción, y el adversario midió unos 0,6 s por millón
   de filas con la tabla trabada para leer y escribir. Separalos: columna en
   una transacción y el índice en otra, cada una con su `lock_timeout`.
3. **El log dice la verdad:** «agregada columna» y «agregado índice» se
   imprimen después del commit de cada uno.
4. **A riesgos, sin cambiar:** la espera de 5 s detrás de otra transacción
   (frena a los que llegan detrás y reintenta en el próximo arranque); un
   índice inválido o parcial que se da por bueno; un camino de más de 200
   caracteres que pierde su métrica en Postgres.

Postgres 16 y SQLite. Línea en `CHANGELOG.md`. Commits aparte y su propio
`/entregar`.

## SUFIJOS-2: devolución, sobre `bd76f9f` (2026-10-28 18:05 UTC)

Evidencia en `REPRODUCCION-SUFIJOS-2-2026-10-28.md`. Va en la cola después
de ABUSO-1 y antes de EMAIL-1.

**Causa.** La detección de «cambiaría de valor» mira el texto crudo con una
lista de signos ASCII; la limpieza que va al TXT (`caracteres_del_maria`)
hace NFKD y pasa a espacio todo lo que no es letra ni número. Lo que la
limpieza cambia y la lista no nombra sale cambiado sin frenar: `ZA(−5)` →
`ZA( 5)`, `AJ(½)` → `AJ(1 2)`, `AJ(1E-3)` y `AJ(1E+3)` → `AJ(1E 3)` los
dos, `AJ(１.５００)` → `AJ(1 500)`, `ZA(10%)` → `ZA(10 )`.

Se pide:

1. **Un solo criterio, sobre lo que sale.** Que la decisión compare el
   valor que escribió el usuario con el que va al TXT (después de NFKD y de
   la limpieza), no una lista de signos sobre el texto crudo. Lo que cambia
   un número, frena con el aviso de hoy.
2. **Fechas, decidido por la PM:** la pieza no pidió frenar fechas y antes
   pasaban. Una fecha `dd/mm/aaaa`, `dd.mm.aaaa` o `dd-mm-aaaa` sale
   `dd mm aaaa` sin frenar, igual con los tres separadores. Hoy
   `AR(31/12/2026)` y `AR(31.12.2026)` dan error y `AR(31-12-2026)` pasa.
   Sumá la pregunta a `PREGUNTAS-DESPACHANTE.md` (cómo se escribe una fecha
   en un sufijo); no se espera la respuesta.
3. **Z, sólo dígitos:** en un sufijo que pide número, cualquier carácter
   que no sea un dígito ASCII (incluidos `%`, espacio entre dígitos, letras
   de ancho completo) frena. Hoy `ZA(10%)` y `ZA(1 500)` pasan.
4. **Caso de la familia, en rojo antes del arreglo:** menos Unicode, raya,
   `- 5`, ancho completo, `½`, `1⁄2`, `1 / 2`, `1E-3` contra `1E+3`, `10⁻³`,
   `1'500`, `%`, y uno que no esté en esta lista.
5. **Los siete mutantes que sobreviven** (en la reproducción), cada uno con
   la prueba que lo mata.
6. A riesgos, sin cambiar: `AJ(1,500)` pasa sin aviso (el sistema no lo
   cambia); `AK`, `AI` y `AW` pasan `15.3` a `15,3`.

Toca el TXT: el golden no se toca.

## D41 y el orden de lo que queda (2026-10-28 17:20 UTC)

- **D41 (DESPACHO-1b): (1), decidido por la PM.** Las tres medias
  (lectura cuadrática, peso infinito, fusión de NCM distinto) se arreglan
  después de las 18:00, encima de la cadena, antes de publicar, con rojo,
  sabotaje y suite. Sumá lo que traiga mi revisor de DESPACHO-1b, que
  corre ahora.
- **D40 y los arreglos de ORG-1 después de las piezas: sí.** Van encima de
  la cadena igual; no se integra nada hasta aceptar ORG-1.
- **Recibidas** SUFIJOS-2 (`bd76f9f`, devolución arriba), SEGURO-1
  (`5dfaf47`, aceptada arriba), DESPACHO-1b (`e59e1a8`, devolución
  arriba), OBSERVABILIDAD-1 (`39be45e`, devolución arriba) y ORG-1 + D40
  (`b358827`, devolución arriba).

## D38 y D39 (2026-10-28)

Cerradas. Quedan resumidas en `DECISIONS.md` («D38 y D39 de la Dev MARIA»).

## Emi dijo que sí a las dos (2026-10-28 12:15 UTC): EMAIL-1 y CONEXIONES-1

Las dos entran al roadmap (Fase 3, tuyas). En commits aparte encima de
`e1b3129`, cada una con su propio `/entregar` después del de ABUSO-1, en
este orden.

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

Lo de ORG-1, ORG-1b, DESPACHO-1a, DESTINO-1, DATOS-1, EMAIL-1 y DISCO-1 (aceptadas o con devolución
arriba) salió del canal: `git show 1f648c3:docs/pm/PARA-DEV-2.md`. Las actas de SEGURO-1,
EMAIL-1, DATOS-1, DESTINO-1, ORG-1 y lo encargado de SESION-1: `git show 28d0422:docs/pm/PARA-DEV-2.md`.

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
