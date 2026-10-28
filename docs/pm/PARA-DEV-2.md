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

## DESPACHO-1b: devolución, sobre `09e16f3`, y D47 y D48 (2026-10-28 20:15 UTC)

Evidencia en `REPRODUCCION-DESPACHO-1b-vuelta-2026-10-28.md`. Bien: la
memoria del hijo con tope, el lector fuera del pool de las facturas, el
anterior vacío que no promedia y `despacho1b.sh` 30 de 30. **Causa de la
devolución:** tres de los siete puntos cambiaron el ejemplo y no la causa.
Cada punto, rojo antes del arreglo y con su sabotaje:

1. **Trabajo y turnos, no sólo bytes.** Reproducido por la PM: un PDF de
   49 KB (20 hojas que comparten un contenido de 500 KB con unas 14 000
   operaciones) ocupa el hijo 23,5 s con 76 MB. Dos de esos y un despacho
   normal de otro usuario: `A,B,C -> TimeoutError×3 10.0s`. **La familia:**
   el hijo corta por trabajo (operaciones, texto o CPU, lo que elijas,
   medido) y un usuario no puede ocupar todos los lugares del lector. La
   prueba: ese PDF se corta rápido y el despacho del otro usuario entra.
2. **La identidad del producto (punto 5 de la devolución anterior).**
   Reproducido: dos renglones del mismo NCM con los primeros 275
   caracteres iguales quedan en una fila (`veces_usado` 2, peso 25,5,
   mezcla de 1 y 50), porque `_norm_desc` corta en 200. Y el NCM con
   puntos no se une: «8471.49.00», «84714900» y «8471.4900» quedan en
   tres filas (regresión de `solo_mismo_ncm`). **La familia:** dos
   productos son el mismo sólo si el NCM normalizado y la descripción
   entera coinciden; nada se compara cortado o con formato distinto.
3. **El promedio (punto 4 anterior).** Reproducido: sin valor, después
   (2, 3), después (4, 6) da peso 2,67 y valor 4,0 en vez de 3 y 4,5:
   `_incr_avg` divide por `veces_usado`, que cuenta usos sin valor. **La
   familia:** cada promedio cuenta sólo los usos que trajeron ese valor.
   `client_service.py:371` hace la misma cuenta: mismo arreglo, con su
   prueba.
4. **Todo valor que entra al catálogo pasa el mismo tope.** Reproducido:
   `catalogo/productos/learn` guarda `inf` y desde ahí el GET del catálogo
   da 500 (`Out of range float values are not JSON compliant: inf`) para
   siempre. Es anterior a la pieza, pero es la misma causa que el punto 3
   de la devolución anterior. Y un `\ud800` suelto en el JSON de guardar
   da 500: lo del lector (tu 2b), en la otra entrada.
5. **Mutantes vivos del adversario**, un caso por cada uno que dé rojo con
   su sabotaje: el número de hijos a la vez, el `except MemoryError` al
   abrir, un tope de pypdf que no sea Flate, `columnas[max(k,0)]`,
   `_MAX_TEXTO` sin parchar la prueba, el borde de 500 renglones,
   `isinstance(resultado, dict)` y `BrokenPipe`.

- **D47: (b), decidido por la PM.** Si la divisa no es USD o no se
  encontró, no se guarda `valor_unitario` y ese renglón avisa; lo demás
  se guarda. La (a) queda para proponer como pieza propia.
- **D48: (a), decidido por la PM, como pieza RENDIMIENTO-1c, la próxima
  después de esta devolución.** La validación del PDF corre en el proceso
  aparte, con tope de memoria y de tiempo, para leer despachos y leer
  facturas. La prueba: tu PDF de 200 repeticiones no hace crecer la app,
  medido en el proceso de la app; y diez a la vez no frenan una subida
  normal. Está en producción: la publicación la decide Emi.
- Riesgos, sin arreglo acá: el hijo carga `.env` por
  `pdf_extractor.py:16-18` (declaralo; si se arregla con una línea, va).

## Orden después de las 18:00, y D45 y D46 (2026-10-28 17:58 UTC)

1. DESPACHO-1b (devolución de las 20:15, arriba). 1b. RENDIMIENTO-1c
(D48, arriba). 2. DISCO-1 (devolución). 3. SESION-1
(devolución, abajo). 4. ABUSO-1 (devolución, abajo). 5. SUFIJOS-2
(devolución, abajo) y lo que se suma de SEGURO-1. 6. EMAIL-1: la D45 y el
mutante. 7. CONEXIONES-1: la D46. 8. OBSERVABILIDAD-1 (devolución,
abajo). 9. ORG-1 + D40 (devolución, abajo). Cada una con su rojo, su sabotaje y
`/entregar`; me despertás al entregar cada una, sin esperar a juntar.

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

## SESION-1: devolución, sobre `895ee73` (2026-10-28 17:58 UTC)

Evidencia en `REPRODUCCION-SESION-1-2026-10-28.md`. Reproduje la carrera y
la cookie copiada de tu D43, y además que el link de verificación del
correo vuelve a abrir sesión después de un logout o un cambio de clave (y
se reusa), que `/auth/me` y `/ui_event` aceptan un token revocado, y que con
`active_jti` en NULL el token de verificación sirve como Bearer.

**La causa:** la revocación se mira sólo en `get_current_user`. Todo camino
que emite sesión o decodifica un token por su cuenta la saltea; y el login
escribe `active_jti` sin comprobar que la clave con la que entró siga
vigente. **D43: (1), decidido por la PM.** Pido:

1. Un solo lugar que decide si un token vale (firma, tipo, `jti` contra
   `active_jti`) y que usen todos: `get_current_user`, `/auth/me`, la
   telemetría, el logout. El token de verificación no sirve como sesión.
2. Verify-email: no abre sesión, o la abre sólo si el token no se usó y es
   posterior al último cambio de clave o logout. Un uso.
3. La carrera (D43 a): el login escribe `active_jti` sólo si el hash de la
   clave sigue siendo el que validó (escritura condicional o relectura en la
   misma transacción). Rojo en SQLite y en PG con el login en vuelo.
4. Cambio de clave (D43 b): rota el `jti` y le da cookie nueva a quien
   cambió; la copia queda afuera. Si no, el aviso y el CHANGELOG no dicen
   «cierra las otras».
5. D43 (c): clave actual mal en change-password no da 401 (no manda al
   login). D43 (d): el logout borra la cookie aunque falle la base.
6. Tope de intentos sobre `current_password` en `PUT` del perfil y en
   change-password.
7. Pruebas que maten estos mutantes, que hoy dan `31 passed`: sacar
   `user.active_jti is not None and` de `revocar_sesion_de_la_request`;
   decodificar sin verificar la firma; y los tres del revisor Sonnet (header
   que le gana a la cookie, sin validar el tipo de `current_password`,
   perfil que no pide la clave si el correo anterior estaba vacío).
8. El informe sin `request.state.token_jti`, que no existe.

Pedí un caso de la familia, no sólo los ejemplos: buscá cualquier otro
`decode` de JWT o emisión de cookie fuera del lugar único y que dé rojo.
`ADMIN_USERNAMES` (main.py:1457) no lo tocás: se lo llevo a Emi.

## ABUSO-1: devolución, sobre `43916a7` (2026-10-28 17:58 UTC)

Evidencia en `REPRODUCCION-ABUSO-1-2026-10-28.md`. **D44: (1), decidido
por la PM**: el login usa la conexión del pedido, no una segunda; rojo con
logins malos concurrentes en PG que hoy agota el pool, y `/health`
respondiendo. Además:

1. Las pruebas no distinguen la duración: bloqueo de 15 min a 60 s y la
   ventana del tope de recuperar de 3600 a 60 dan `63 passed`. Casos «a los
   14 min sigue bloqueado, a los 16 no» y lo mismo para la ventana.
2. Claves de 121 a 300 caracteres en PG (el revisor vio
   `StringDataRightTruncationError` con 200) y el mutante `len(clave) <=
   300` muerto.
3. El 500 de `/auth/recover-username` con un surrogate suelto en el correo.

Lo demás del revisor (XFF y `TRUSTED_PROXY_HOPS`, IPv6, deadlock con
ventanas cortas, filas sin tope, tiempos del login) va a riesgos en tu
informe, sin tocar producto.

## SEGURO-1: aceptada sobre `5dfaf47` (2026-10-28 18:15 UTC)

`test_seguro1.py` `48 passed` (corrida de la PM). Se integra con la cadena,
después de SUFIJOS-2. Evidencia: `REPRODUCCION-SEGURO-1-2026-10-28.md`.

Se suma, en commits aparte junto con la vuelta de SUFIJOS-2:
- **Una prueba que fije la lista de los cinco.** Hoy sumar `DAT` (o `DDU`,
  `DAF`, `DES`, `DEQ`) a `INCOTERMS_CON_SEGURO` deja `48 passed`.
- **`/generate_maria/avisos` normaliza el incoterm igual que
  `/generate_maria`**: con `"CIF\x00"` hoy los avisos ofrecen el 1 % y
  generar da 400. Una sola función para los dos.
- A riesgos: el 1 % mandado sin `seguro_calculado` entra al TXT (es lo
  encargado; lo cubre SEGURO-2, que espera a Emi); seguro mayor que el FOB
  sin aviso (preexistente); la revisión dice «no los sumes dos veces» y el
  400 dice «cargá el de la factura».

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

## EMAIL-1: aceptada sobre `2b93071` (2026-10-28 17:46 UTC)

Lo de la pieza está bien: ningún camino manda el correo de una cuenta a
otra y la respuesta no cambia exista o no. Se integra con la cadena.
Evidencia en `REPRODUCCION-EMAIL-1-2026-10-28.md`. Sumá, encima de la
cadena: una prueba que dé rojo si `if not email: return None` de
`_cuenta_por_email` pasa a `if False:` (hoy `24 passed`).

**A riesgos, sin tocar producto** (todo es de antes de la pieza): el nombre
va sin escapar en el HTML de los dos correos de recuperación (phishing
desde el remitente de CDI, reproducido); el envío síncrono delata la cuenta
por tiempo y traba el worker; un token de recuperación viejo sigue valiendo
tras usar uno nuevo; `dev_token_hint` fuera de producción; el 500 sin
`FRONTEND_URL`. El 1, el 2 y el token se los propongo a Emi como pieza
aparte: **no los arregles hasta que diga que sí**.

## DISCO-1: devolución, sobre `88b22c8` (2026-10-28 17:46 UTC)

La migración está bien (dos arranques, sin duplicar, dueños separados,
Postgres 16 y SQLite). Evidencia en `REPRODUCCION-DISCO-1-2026-10-28.md`.
Va encima de la cadena, después de D41.

1. **Causa (regresión, reproducida por la PM en Postgres 16):** en
   Postgres, una excepción de la base atrapada sin `rollback` deja la
   transacción abortada para todo lo que sigue en ese pedido. En
   `sugerir_ncm` los pasos 1 y 2 atrapan sin `rollback`; si fallan, el
   paso 3 (ahora en la base) falla también y se pierde el historial sin
   aviso. Rompiendo una columna de `client_product_history`: `c996ad4`
   `['historial']`, `88b22c8` `[]`. Revisá **todo** `except` que atrape un
   error de la base y siga usando la misma sesión en lo que toca tu diff,
   no sólo estos dos. Prueba roja en Postgres (en
   `disco1_postgres.py` vale) con su mutante en `disco1.sh`.
2. **Un NUL** en la descripción o el NCM de `guardar-uso` da 500 en
   Postgres (el archivo lo aceptaba). Que sea 400 claro, o que se limpie;
   lo mismo en la importación. Con prueba.
3. **Tope de tamaño, decidido por la PM:** la descripción y el NCM de
   `guardar-uso` y de cada fila importada con un largo máximo; si se pasa,
   400. Elegí el número mirando qué largo de descripción admite el resto
   del producto y decilo. 30 MB entraron con 200. El
   tope de filas por dueño va a riesgos.
4. **Orden fijo al importar:** ordená las filas por la clave antes de
   escribirlas, para que dos importaciones del mismo dueño no se bloqueen
   entre sí (el revisor sacó `DeadlockDetectedError` en 2 de 4 corridas con
   órdenes distintos; no lo reproduje). Si no hace falta, decí por qué.
5. **No pises un `.migrado` anterior** al pasar el archivo (elegí otro
   nombre libre). Menor.
6. **Pruebas que faltan** (mutantes que hoy sobreviven): sin `order_by` en
   la carga; `_HISTORIAL_FILAS_POR_SENTENCIA = 10**6` (con unas 7000 filas
   el real da ok y el mutante falla en asyncpg); sin `or count < 1`; sin
   `not desc.strip()`; `os.replace` por `os.remove` en la suite, no sólo en
   el script de Postgres. Cada una roja con su mutante y sumada a
   `disco1.sh`.

## DATOS-1: aceptada sobre `c996ad4` (2026-10-28 17:41 UTC)

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

## DESTINO-1: aceptada sobre `f887b4a` con `b9881fb` (2026-10-28 17:52 UTC)

`test_destino1.py` `32 passed` y `destino1.sh b9881fb` 19 de 19 en rojo
(corrida de la PM). Integrada `f887b4a` en la rama de la PM; `b9881fb`
entra con la cadena. Evidencia: `REPRODUCCION-DESTINO-1-2026-10-28.md`.

- **Punto 2(b), decidido por la PM: queda así.** Tenías razón: vacío es «el
  de la operación», y ese grupo no se genera. No heredes el del primero.
- Los tres riesgos y la premisa del golden quedan como los escribiste.

## ORG-1: aceptada sobre `4ce6d22`, con ORG-1b y DESPACHO-1a (2026-10-28 17:38 UTC)

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
