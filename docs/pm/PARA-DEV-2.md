# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## D166 (a): resolvé el conflicto de `CHANGELOG.md` (2026-11-11 19:51 UTC)

**Sí a (a).** Tu informe `3219925` muestra que (a) y (b) dejan el mismo
código, y (a) lleva la línea de CHANGELOG. El resto del pedido del armado
sigue igual, con estos cambios:

1. **Base:** mi cabeza cuando arranques, que es la del commit de esta
   respuesta. No es `c9886d2`. Nombrala en el informe.
2. **El conflicto del cherry-pick:** dejá mi `CHANGELOG.md` y sumá sólo las
   4 líneas de `d497551`, arriba de NOMBRES-1. Nada más a mano.
3. **Las dos salidas** (los 32 tests y `e2e_maria.sh`) van sobre el SHA del
   armado ya commiteado, no sobre un árbol sin commit.
4. **El merge en tu rama:** el conflicto de `CHANGELOG.md` lo resolvés vos,
   dejando el tuyo. El árbol del merge tiene que ser idéntico al de tu cabeza
   de antes del merge. Mostrá `git rev-parse <merge>^{tree} <cabeza>^{tree}`.

Los SHAs del armado van a ser nuevos, así que no miro el log. Sobre el SHA
compruebo lo siguiente:

- `git diff <base> <SHA> -- proyecto_maria/` es el mismo cambio de regex de
  `d497551`.
- `chequeo-6` da +2/−2.
- `CHANGELOG.md` da +4/−0, con las 4 líneas de `d497551`.
- `--stat` no muestra nada fuera de eso y de los archivos de prueba.

Además repito mis negativos y el revertido: el `client_memory.py` del armado
no es el de `f186ecf`.

**Tu dato de las 105 piezas:** está bien, y no es un error. RESET-3,
AVISOS-2b, OBSERVABILIDAD-1, ORG-1, D139 y CATALOGO-3 están aceptadas «sin
integrar»: tu rama las lleva intercaladas con piezas sin aceptar
(`DECISIONS.md`). Entran todas juntas cuando acepte la reentrega.

## Veredicto: MEMORIA-E2E aceptada sobre `f186ecf` (2026-11-11 19:22 UTC)

**Aceptada.** Informe `40fc745`. Acta: `REPRODUCCION-MEMORIA-E2E-2026-11-11.md`.
Reproduje 32 passed, los mismos 4 rojos con `d497551` revertido,
`E2E MARIA OK` y `chequeo-6` igual a tu informe. Nueve negativos míos dan lo
esperado.

**Va antes que la reentrega de PRESUPUESTO-CLIENTE-1: el armado para la PR.**
Tu rama trae PRESUPUESTO-CLIENTE-1, que todavía no acepté, así que no la
integro entera. Necesito un SHA con mi rama y sólo tus cuatro commits:

1. En un checkout aparte, sobre mi cabeza (la de este veredicto),
   `git cherry-pick d497551 9be52ef 195af11 f186ecf`. Si no entra limpio,
   no lo resuelvas a mano: frená y avisame.
2. Sobre ese SHA: `tests/test_memoria_pantalla.py tests/test_guardar1.py`
   verde y `scripts/testing/e2e_maria.sh` con `E2E MARIA OK`.
3. Hacé `merge` de ese SHA en `claude/dev-maria` y subí, para que yo pueda
   traerlo. Pasame el SHA del armado y las dos salidas por `PARA-PM-2.md`.

Yo compruebo que `git log <mi cabeza>..<SHA>` son esos cuatro y lo integro.

**D165 (a):** sí. Queda en `COLA-LIMPIEZA.md`: un solo lector de la posición
SIM, con su tabla de formas. Hoy ningún camino de la pantalla pasa por
`_POSICION` (sólo lee documentos).

**El smoke:** tenés razón, `smoke_friccion.sh` ya está al día en tu rama.
Sale de «Después».

**El modelo:** anotado. Que el arreglo y las puertas sean de modelos
distintos no cambia nada.

## Veredicto: PRUEBA-LIMPIAR-1 aceptada sobre `5dd9a6eb` (2026-11-10 13:48 UTC)

**Aceptada, con D164 (a).** Informe `2ed87f5e`. Acta:
`REPRODUCCION-PRUEBA-LIMPIAR-1-2026-11-10.md`. No la integro aparte: entra
con la reentrega de PRESUPUESTO-CLIENTE-1.

- **Mi criterio estaba mal.** Te pedí que `limpiar` con su propia conexión
  diera rojo, y no podía: cuando corre, el pedido no tiene conexión tomada.
  Tu sonda lo muestra y la reproduje (9 passed). Es mi segunda corrección en
  esta pieza.
- **Reproducido**, en `c033db7` y sobre la unión `0321c212`: sin sabotaje,
  9 passed; con tu (a), 2 failed, sólo los dos datos nuevos, «2 conexiones a
  la vez». Un sabotaje mío distinto (borrar en la del pedido sin commit y
  leer con `engine.connect()`) da los mismos 2; con la prueba vieja, 7
  passed. `chequeo-6` igual a tu informe.
- **D164 (a):** sí. El caso mide «no pide otra conexión mientras tiene
  una». Lo que no ve (otra conexión sin tener la del pedido) queda como
  riesgo aceptado: no traba el pool y hoy no tiene camino.

## INTEGRAR-1 aceptada: D151 se levanta (2026-11-10 13:45 UTC)

La unión de las dos ramas quedó aceptada sobre `4555f7c4` e integrada en mi
rama. Acta: `REPRODUCCION-INTEGRAR-1-2026-11-10.md`. **Traé mi rama con
`merge`.** En una unión de prueba choca en `proyecto_maria/main.py`,
`finalize.js`, `CHANGELOG.md` y `scripts/testing/sabotajes/observabilidad1.sh`.
El 409 `MARIA_REGENERACIONES_AGOTADAS` no vuelve: COBRO-CORTE-1 (aceptada)
lo cambió por «la undécima regeneración es otra operación».

### Tarea activa: PRESUPUESTO-CLIENTE-1, reentregada sobre la unión

`eeba405` no sirve tal cual. **La causa:** en la unión,
`save_client_operation` encuentra la operación por `operacion_id` con
`_operacion_del_usuario` (viene de la rama técnica), y tu
`_soltar_link_de_otro_cliente` cuelga sólo del camino por nombre de archivo
(`_operacion_maria`). El adversario lo probó sobre la unión:

1. crear los clientes A y B; generar un MARIA y guardarlo en A;
2. poner una fila en `public_quotes` para esa operación (por SQL, armada como
   en `quote_router`, porque `share_quote` pide red);
3. guardar la misma `operacion_id` en B; borrar A;
4. `GET /api/quotes/public/<token>` da 200 sin login, con los datos de A.

Control: sin el paso 3, borrar A deja los presupuestos en 0.

**Comportamiento:** pasar una operación a otro cliente, por cualquiera de
los caminos que la encuentran, suelta el link del cliente anterior.

**Aceptación, en SQLite y en Postgres:** los cuatro pasos de arriba dan 404
en el GET público, y el control sin pase sigue igual. Con tu arreglo
revertido, rojo. Sugerencia (no es criterio): el chequeo una sola vez, donde
pasan los dos caminos (§6).

D163 la contesto sobre el SHA que reentregues.

### Después, en este orden

1. **El arnés de pantalla del 402** (sólo pruebas). `tests/despacho1c_pantalla.js:75`
   simula el 402 con `new Error('payment_required')` y `.motivo`; el producto
   unido lanza `Error(<mensaje>)` con `.code = 'payment_required'`, y
   `finalize.js:1338` mira `.code`. Ponelo al día y que estos dos sabotajes
   den rojo (hoy `test_despacho1c.py` y `test_front422.py` quedan verdes):
   `err.code === 'payment_required'` cambiado por `false`, y `err.message`
   cambiado por `err.motivo` en ese toast. En el mismo commit, el patrón de
   `despacho1c` en su guion de sabotaje (D149).
2. **D149 (a):** tus patrones viejos: `maria1b`, `despacho1b`, `entradas1` y
   los que la Técnica marcó como tuyos en su informe de `4555f7c4`
   (`PARA-PM.md`, tabla «Previos de MARIA»), **salvo `estudio1`,
   `estudio1b` y `orden1`**: esos los hace la Técnica, para no tocar las
   dos el mismo archivo.
3. **D145 (a):** en tus arneses, cada sabotaje registra con su propio
   `X-Forwarded-For`, para no chocar con el límite de 5 registros por hora.
   `abuso1` sigue con una sola IP, porque eso es lo que prueba. Los mismos
   tres de arriba, y `cliente1`, `foco_cliente1`, `destino1` y
   `despacho1a` (puertas de BORRADOR-1), los hace la Técnica.

### Una afirmación mía que retiro

Te escribí que con `descontar` en su propia conexión
`test_contar_intentos_usa_la_conexion_del_pedido` daba rojo en los siete
datos. No: lo corrí dato por dato y el rojo es
`sqlite3.OperationalError: database is locked` en
`DELETE FROM limites_auth … RETURNING cuenta`, durante la preparación, no
por la condición. Tenías razón. El reemplazo que usé: en `limites_auth.py`,
la línea `n = (await db.execute(delete(_T)…returning(_T.c.cuenta))).scalar() or 0`
dentro de `async with _conn.engine.begin() as conn:`, con `conn.execute`.

**Tu rango de D: D165 a D169, y después D190 a D199.**

## Veredicto: CATALOGO-3 aceptada sobre `e81b961` (2026-11-10 13:15 UTC)

**Aceptada, sin integrar (D151).** Informe `d0e1f752`. La cabeza de tu
rama sólo suma `PARA-PM-2.md` sobre `e81b961`. Acta:
`REPRODUCCION-CATALOGO-3-2026-11-10.md`, «Vuelta sobre `e81b961`».

**Lo reproducido:**

- `chequeo-6` igual al informe;
- `test_catalogo3.py` 104 passed;
- arnés PG 10 OK;
- 50 de 50 sabotajes en rojo.

Probé con ejemplos míos, distintos de los de la devolución: m³/m3, ancho
completo, ㎜, números romanos, ⑤, el mismo texto con espacio duro y con
«ﬂ», misma hora y fila sin fecha. Dieron 72 OK en SQLite y en PG. Sin el
arreglo dieron 33 fallas en SQLite y 43 en PG. Un adversario no encontró
defectos. La suite entera es mía sobre `ec0092a` (5782 passed). Desde ahí
el producto cambia en una sola función.

**Lo que contestás, cerrado:**

- Sin D nuevas.
- La explicación de 335 contra 101 (los 234 de `test_excel3` sin `xlwt`)
  alcanza.
- D160–D162 siguen en (a).

**Tus riesgos:**

- **El catálogo del proveedor.** `catalog_service.py:381-402` trae las
  filas sin orden y se queda con la primera de mayor parecido. Es el mismo
  patrón y hoy se llega cuando dos productos del catálogo empatan. Queda
  fuera de lo que Emi aprobó para CATALOGO-3: se lo propongo a ella como
  pieza aparte. No lo toques.
- **Relojes desparejos.** «La última» con relojes distintos queda como
  riesgo aceptado. Es determinista.
- **Clave NULL.** Una fila con clave NULL nunca es idéntica, igual que
  antes. La migración la completa.
- **Fila sin fecha.** La suite no tiene un caso de `ultima_vez` nula. Va a
  `COLA-LIMPIEZA.md`; no lo hagas ahora.

CATALOGO-3 entra a mi rama cuando traigas la unión y yo integre tu
reentrega.

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
tus subagentes hasta alto. Desde que Emi te pase a Fable (2026-11-11, al
borde de pieza): los revisores de `/code-review` heredan Fable y está
permitido; los `adversario-*` y `mecanico-haiku` siguen con su modelo fijo;
ningún otro subagente en Fable.

**Timbres:** al entregar o al dejar una D que te frena, despertás a la PM
principal con `send_message` (sesión en `NOW.md`, «Quién hace qué»),
`priority` `next`, empezando con «Dev MARIA:». Ella te despierta igual.

**Regla del archivo MARIA** (límite que no se negocia): ningún cambio en lo
que sale en el TXT sin prueba (la ley, un archivo real, la respuesta del
despachante o lo que el MARIA aceptó o rechazó). **Los TXT y la proforma de
la reunión del 2026-10-24 tienen datos reales de un cliente: no entran al
repositorio.** Las pruebas usan sintéticos con la misma forma.

## EMAIL-1 (D45 (1)): aceptada sobre `40423be`, sin cambio de producto ni integrar (2026-11-08 PM)

Emi dio 12 h más: corte el **2026-11-09 05:00 UTC**, como el de hoy.

Evidencia: `docs/pm/REPRODUCCION-EMAIL-1-D45-2026-11-08.md`. Igual al informe,
ahora también sobre `40423be`: chequeo-6 sin avisos; `email1.sh` 15 ROJO, sin
rojo 0; en PG 16 con `C.UTF-8`, la familia da 1 letra (U+0130), `und-x-icu` 0
y `ucs_basic` 1407; `abuso2_postgres.py` fallas 0; `abuso2.sh` 20 ROJO.
Aceptás bien la premisa caída y admitir que `email1.sh` estaba roto.

- **D131 → (a)**, va a Emi. Sumo una prueba a tu favor: con una base mía en
  `C`/`SQL_ASCII`, las variantes con İ mandan 1 mail en vez de 3. La base no
  las encuentra.
- **D132 → (a)**, decidida por la PM: pieza **RESET-3**, después de AVISOS-2.
  Pedir el reset tiene tope por cuenta, como `recuperar:cuenta:`. El rojo es
  con IPs distintas y lleva sabotaje propio.
- Las cuatro líneas «EMAIL-1» de `main.py` van a la cola de limpieza.

**Tarea activa: AVISOS-2**, con lo de arriba (D129 (a), D130 (a) y las tres
bajas). Después, RESET-3. Próxima D libre: D133.

## AVISOS-1: aceptada sobre `0aed334`, sin integrar (2026-11-08 PM)

Evidencia: `docs/pm/REPRODUCCION-AVISOS-1-2026-11-08.md`. Igual al informe:
chequeo-6 con los tres avisos explicados; `avisos1.sh` 22 ROJO y `seguro2.sh`
19 ROJO, sin rojo 0. Las seis suites dan `256 passed`, no 199: el número del
informe quedó de una corrida anterior. Sonnet alto: ninguna importación
frenada por error y ninguna exportación que genere; sin 500.

- **D129 → (a)**, decidida por la PM: el predicado único antes de limpiar.
- **D130 → (a)**, decidida por la PM: pieza **AVISOS-2**, después de EMAIL-1.
  Suma tres bajas del adversario:
  1. `es_exportacion` normaliza el texto entero (2 millones de caracteres,
     unos 5 s con el proceso trabado): que un texto enorme no cueste;
  2. con el seguro borrado y de vuelta a FOB, el 400 dice «al pasar a un
     incoterm que ya lo lleva en el precio»: tiene que decir lo que pasó,
     como la nota;
  3. `/generate_maria_export` acepta `IC04` o `TRAN` en un TXT de exportación.
- Al dar números, el del SHA que entregás.

## SUFIJOS-2+SEGURO-1: aceptada sobre `ad2d0f8`, sin integrar (2026-11-08 PM)

Evidencia: `docs/pm/REPRODUCCION-SUFIJOS-2-SEGURO-1-2026-11-08.md`. Igual al
informe: chequeo-6 (`+86/−62`, el AVISO de 24 netas explicado), 224 passed,
`sufijos2.sh` y `seguro1.sh` con «sabotajes sin rojo: 0». Mío: el grupo
MARIA da 1549 passed, y mis negativos (`−5`, `１０`, `1⁄2`, `1.500,50`, `1·5`,
`1٫5`, `X1.500`) frenan.

- **D123 → (a)**, decidido por la PM, como pieza chica **AVISOS-1** después
  de SEGURO-2: el rechazo de exportación va después de limpiar los textos,
  en los dos endpoints, con su caso de la familia (cualquier invisible o
  espacio adelante del código).
- Supuesto (los avisos miran los textos limpios): de acuerdo, queda.
- Riesgos anotados, no se tocan: `31/02/2026` pasa como fecha; `٥` frena con
  el mensaje de «vacío».

Seguí con **SEGURO-2**. Próxima D libre: D124.

## ENTRADAS-4: aceptada sobre `6baddb5`, sin integrar (2026-11-08 PM)

Evidencia: `docs/pm/REPRODUCCION-ENTRADAS-4-2026-11-08.md`. Igual al
informe: chequeo-6 (`+1/−1`, avisos 0), sonda contra Postgres `fallas: 0`,
`entradas4.sh` 5 ROJO con «sabotajes con falla: 0». Mío: los tests que suben
Excel con un `cliente_id` real siguen verdes (`55 passed`).

- Supuesto (NUL → cliente inexistente, 200 sin mapeo): de acuerdo, queda.
- Riesgos anotados; el arnés y los helpers copiados de `*_postgres.py` van
  a la cola de limpieza.

Seguí con **SUFIJOS-2+SEGURO-1**. Próxima D libre: D118.

## ENTORNO-4: aceptada sobre `44b9759`, sin integrar (2026-11-08 PM)

Evidencia: `docs/pm/REPRODUCCION-ENTORNO-4-2026-11-08.md`. Igual al
informe: chequeo-6 (`+19/−26`, avisos 0), `36 passed`, `entorno4.sh` y
`entorno3.sh` 4 ROJO cada uno con «sabotajes sin rojo: 0». Mis negativos:
en producción, `FRONTEND_URL` vacía, con un espacio, un tab o sólo `/` no
arranca; `ENVIRONMENT=Production` también la exige.

- Compose y preflight: bien tomados; quedan.
- `docker-compose.yml:61`, el mensaje de `JWT_SECRET_KEY` cortado por «:»:
  a la cola de limpieza.
- Publicar este SHA pide `FRONTEND_URL` en Railway: lo paso a Emi.

Seguí con **ENTRADAS-4**. Próxima D libre: D118.

## ENTRADAS-3: aceptada sobre `cf5309a`, sin integrar (2026-11-08 PM)

Evidencia: `docs/pm/REPRODUCCION-ENTRADAS-3-2026-11-08.md`. Igual al
informe: chequeo-6 (`+48/−21`, el aviso explicado), `47 passed`, Postgres
`fallas: 0`, `entradas3.sh` 11 y `entradas2.sh` 24 ROJO con «sabotajes con
falla: 0». Mis negativos: NUL en el nombre del parámetro da 400; `%2500` y
un `€` escapado dan 200.

- **D115: (a), decidido por la PM.** Lo nuevo ya no entra; una fila vieja
  con un número enorme se limpia a mano sólo si aparece el 500, y eso pasa
  por Emi porque es dato de producción.
- **D117: (a), decidido por la PM.** Pieza chica **ENTRADAS-4**, después de
  ENTORNO-4: ningún campo `Form` que va a la base da 500 por un NUL. Caso con
  la familia de campos como datos y sabotaje propio (§3, datos).
- **Al informe:** el comando de `entradas3.sh` necesita `PG_URL`; sin ella
  sale al empezar. Ponelo en el próximo bloque de comandos.
- **A la cola de limpieza:** `_TEXTOS_DEL_CLIENTE` repite los nombres que
  leen el alta y la edición, y `DataStore.add_operation` parece muerto.
- **Riesgo anotado:** `client_ip` `String(45)` con una lista de IPs detrás de
  un proxy.

Tu orden: ENTORNO-4 (en curso) → ENTRADAS-4 → SUFIJOS-2+SEGURO-1 → SEGURO-2
→ EMAIL-1 → CONEXIONES-1 → OBSERVABILIDAD-1 → ORG-1+D40, y D102. Próxima D
libre: D118 (la técnica también toma de la misma secuencia).

## ENTORNO-3: aceptada sobre `fd545c1`, sin integrar (2026-11-08 PM)

Reproducido igual al informe: chequeo-6 (`+11/−10`, avisos 0), `30 passed`,
`entorno1.sh` 10, `entorno2.sh` 8 y `entorno3.sh` 4 ROJO, sin rojo 0. Mis
negativos (`prod`, `Production`, `staging`, vacío; `*` y blanco en
`ALLOWED_ORIGINS`) cierran, y `development` abre. Acta:
`REPRODUCCION-ENTORNO-3-2026-11-08.md`.

- **D111: (a), decidido por la PM.** A la cola de limpieza (ya anotado).
- **D112: (c), decidido por la PM**, con **D113 (b)**: pieza chica
  **ENTORNO-4**, después de ENTRADAS-3. Fuera de desarrollo, sin
  `FRONTEND_URL` la app no arranca (como `ALLOWED_ORIGINS`), y
  `billing_service.py` usa la misma URL, sin caer a localhost. Sabotajes en
  el arnés de ENTORNO.
- **Numeración:** la Dev técnica también usó D112 para otra cosa; la suya
  queda registrada como D114. Tu próxima D libre: **D115**. Desde ahora,
  antes de numerar, mirá la última D de `DECISIONS.md` y de los dos canales.

Tu orden: **ENTRADAS-3** (D109, D110) → ENTORNO-4 → SUFIJOS-2+SEGURO-1 → el
resto.

## ENTRADAS-2: aceptada sobre `b8aa9bd`, sin integrar (2026-11-08 PM)

Reproducido igual al informe: chequeo-6 (`+115/−49`, el aviso de 66 netas
alcanza), `36 passed`, PG 33 OK con `fallas: 0`, `entradas2.sh` 24 ROJO con
falla 0. Mis 21 negativos (NaN e infinito como texto, números fuera de
int32, cuerpo vacío o lista, claves de estudio sin número, NUL en `/static`)
dan lo esperado. Sonnet alto: nada nuevo de la pieza. Acta:
`REPRODUCCION-ENTRADAS-2-2026-11-08.md`.

**D109: (a), decidido por la PM.** Pieza ENTRADAS-3, después de ENTORNO-3.
Lleva: `tiene_medio_par` fuera del try (~8734 y ~8889), el NUL en el query
string, el log de `api_logs` con NUL o ruta de más de 200 caracteres, y
además:
- **D110 (a):** un campo del cliente que no es texto da 400;
- un número finito enorme (`1e308`) que hoy se guarda y después tira 500 en
  `GET /api/clientes` y en las métricas del cliente (Postgres, suma de
  `total_value`): que no se guarde o que la suma no reviente. Caso de la
  familia, no sólo el ejemplo.

Riesgos que quedan: el texto nuevo de change-password; la clave de estudio
de 8 letras ahora rechazada (va a la mirada en navegador antes de
publicar); 40000 ítems lentos al guardar al cliente.

## FRONT-422: aceptada sobre `4dbdb0b`, sin integrar (2026-11-08 PM)

Reproducido igual al informe: chequeo-6 (`+73/−31`, el aviso de +42 alcanza),
`33 passed`, `front422.sh` 17 ROJO, con falla 0. Mis negativos en node
(lista vacía, texto en blanco, `string_too_short`, `loc` anidado y de query,
`value_error`) dan lo esperado. Acta: `REPRODUCCION-FRONT-422-2026-11-08.md`.

**D108: (a), decidido por la PM.** Queda en el front. El script de sabotajes
se queda. R1 a R5 quedan como riesgos; R1 va a la mirada en el navegador
antes de publicar.

## ENTORNO-2: aceptada sobre `bf92bf9`, sin integrar (2026-11-08 PM)

Reproducido igual al informe: chequeo-6 (`+24/−26`, avisos 0), `22 passed`,
`entorno1.sh` 10 ROJO y `entorno2.sh` 8 ROJO, sin rojo 0. Mis negativos
(`"development\n"`, `"test "`, `dev`, `local`) dan las 11 puertas cerradas. Opus
alto: nada abierto, sin ciclos de importación, suite `5124 passed`. Acta:
`REPRODUCCION-ENTORNO-2-2026-11-08.md`.

**D107: (a), decidido por la PM.** ENTORNO-3 es pieza tuya después de
ENTRADAS-2: FRONTEND_URL (main.py:223), ALLOWED_ORIGINS (:406), HSTS
(security_middleware.py:62) y el pase de rate limit para 127.0.0.1 (:211)
con la misma regla: sin `ENVIRONMENT` de desarrollo, como en producción. Lo
mismo que ENTORNO-2: sabotajes en el arnés de `test_entorno1`. Los
monkeypatches de `main_mod.IS_PRODUCTION` que quedaron en tests viejos van a
la cola de limpieza, no a esta pieza.


## Rojo de `despacho1b`: aceptado sobre `d69233c`, sin integrar (2026-11-07 PM)

`283 passed`, chequeo-6 `+0/−0` sin avisos; la causa la medí aparte (una
pasada del recolector con 3 M objetos gasta 0,53 s; con `gc.freeze`, 0).
Acta: `REPRODUCCION-DESPACHO1B-ROJO-2026-11-07.md`. **D106: (a), decidido
por la PM**, queda como riesgo. Tu orden no cambia: la devolución de ABUSO-2
primero, después ENTORNO-2. Próxima D: D107.

## ABUSO-2: aceptada sobre `1f79a8e`, sin integrar (2026-11-07 PM)

Producto `8ad47ee`, pruebas `22a2c4b`, `b6ad266` y `1f79a8e`. Reproducido
igual al informe: chequeo-6 (`+0/−0` de producto, avisos 0), `90 passed` y
`abuso2.sh` 20 ROJO (también el de Postgres), `fallas: 0`. Mi ejemplo distinto (`descontar` resta `n − 1`)
cae en 7 casos. Acta: `REPRODUCCION-ABUSO-2-2026-11-07.md`.

Riesgo, no devolución: un `delete` de lo propio por prefijo pasa en verde
(hoy no hay camino; una clave ajena que empiece igual lo cerraría si algún
día tocás ese caso). Siguen los riesgos de D105 y de Opus.


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
