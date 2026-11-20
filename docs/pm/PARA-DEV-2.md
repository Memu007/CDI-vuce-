# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## Tarea activa: ADMIN-USUARIOS-1 (2026-11-20 18:47 UTC)

**Sí de Emi (20/11): «Quiero ver usuarios y darles créditos desde el panel».** Esta pieza es la
primera parte: **ver**. Dar créditos es ADMIN-CREDITOS-1 y no entra acá (espera la pieza de la
Técnica que cambia el candado de la cuenta, y respuestas de Emi). Ningún botón ni ruta que escriba.
Antes de tocar código: `merge` de mi rama y tu `/compact conservar` al día.

**Hoy:** `/dev/dashboard` (`dev_dashboard.html`) y `routers/admin_router.py` están detrás de
`require_admin`; no hay nada de usuarios ni de créditos. Revisión fuerte (permisos y datos, §3).

**Comportamiento:** en el panel de admin, una sección «Usuarios» lista cada cuenta con: usuario,
email, plan, estado de cobro, operaciones usadas en el período, créditos extra vigentes y hasta
cuándo vencen, fecha de la última recarga, estudio (si es integrante) y si es admin.
- **Sólo admin:** sin sesión, 401; con sesión de no admin, 403; en los dos casos sin datos.
- **Nada secreto:** nunca sale la contraseña ni su hash, `active_jti`, tokens de recuperación o de
  invitación, ids de pago de Mercado Pago (`last_payment_id`, `payment_customer_id`) ni datos de la
  tarjeta.
- **Integrante de estudio:** muestra el saldo y el plan del estudio, que es el que gasta, y dice que
  es del estudio.
- **Mirar no cambia nada:** créditos vencidos se muestran como 0 vigentes sin escribir la base
  (`_expire_extra_ops` pone el saldo en 0 sobre el objeto; si la ruta lo usa y hace `commit`, cambia
  datos). Las filas quedan iguales antes y después de mirar.
- Con muchas cuentas no se traba ni manda todo de una vez (límite por página o búsqueda: a tu
  criterio, decilo en el informe).

**La familia** (un caso por causa, entradas como datos): cuenta sola con créditos vigentes, con
créditos vencidos, sin créditos, integrante de estudio, admin por rol guardado, y los tres que piden
la página (sin sesión, no admin, admin).

**Prueba:**
- que **todas** las rutas de admin, nuevas y viejas, den 403 a un no admin, sacadas de las rutas de
  la app y no de una lista a mano;
- que la respuesta no traiga ninguna clave prohibida, mirando la respuesta entera;
- que la base quede igual después de listar una cuenta con créditos vencidos;
- el informe muestra una vez el rojo con cada arreglo revertido en el mismo SHA, y trae tu guion de
  sabotaje (sacar el `require_admin`, devolver un campo prohibido, hacer `commit` del vencido).

*Sugerencia (no es criterio):* las rutas en `admin_router.py`, que ya monta con `require_admin`, y no
tocar `main.py`, que la Técnica está cambiando.

**Puertas:** `chequeo-6`, tu caso y tu guion de sabotaje, adversarios Sonnet y Opus alto, y la suite
completa desde base limpia sobre el SHA (tocás el servidor). `e2e_maria.sh` sólo si tocás `static/v2`.
Sin datos reales: cuentas de prueba.

**Próxima D: D278.**

## Veredicto: CATALOGO-PAIS-2 aceptada sobre `9459a0d4` (informe `43f3aa29`) (2026-11-20 15:38 UTC)

Acta: `REPRODUCCION-CATALOGO-PAIS-2-2026-11-20.md`. La integro con `merge` de `43f3aa29`; sin
publicar. Reproduje con las copias de `9459a0d4`: chequeo-6 (+16/−3, el AVISO del envoltorio
explicado), `holanda423.sh` (34 ROJO, 0 ROTO), dos negativos míos (`'input'`→`'keyup'` y el `title`
con lo que vino del servidor: los dos rojos), `catalogo_largo2.sh` en PG16 (39 ROJO, «fallas: 0»),
`anclas_perdidas.py` (ya no te nombra) y `e2e_maria.sh` sobre el SHA y la unión: todo verde. Leí que
el `input` que manda el guardado sólo lo escucha `mostrar`, y que el cambio de `clientes.js` queda en
las filas del catálogo, no en la ficha.

**Decidido por la PM:**
- Supuestos 1 a 3 (`title` siempre presente, `aria-label="Origen"`, la sugerencia del navegador
  simulada con `insertReplacementText`): aceptados.
- Riesgos 1 a 3 (táctil y teclado no ven el `title`, el lector de pantalla puede repetir el valor,
  el tooltip nativo no se vio sin ventana): riesgo escrito, bajo.
- Vencido `catalogo_largo2.sh`: cerrado con `cbd7718c`; su línea sale de `sabotajes-conocidos.txt`.

**Ahora no tenés pieza.** Lo tuyo que queda en el roadmap espera a alguien de afuera (la lista de
empaque y los TXT reales del despachante, la pregunta 6, el texto de Emi). Al leer esto: `merge` de
mi rama, tu `/compact conservar` al día, y no arranques nada. Apago tu rutina; la prendo cuando te
asigne. **Próxima D: D278.**

## Veredicto: ORIGEN-2 aceptada sobre `0d7401ed` (informe `76b98256`) (2026-11-20 02:20 UTC)

Acta: `REPRODUCCION-ORIGEN-2-2026-11-20.md`. La integro con `merge` de `76b98256`; sin publicar, y antes
de publicar va la copia de la base. Reproduje chequeo-6, `test_origen2.py`, `origen2_postgres.py` en
PG16 (`fallas: 0`), `origen2.sh` (24 ROJO, «sabotajes sin rojo: 0»), el pytest entero (6231 passed) y
`e2e_maria.sh` sobre el SHA y la unión. Probé tipos que no son texto, NUL, surrogate, letra ancha, PUT
con sólo el origen y las doce siglas del selector de producción: todo bien.

**Una cuenta mal:** la tabla del informe dice «25 ROJO»; tu salida pegada, la mía y el guion dan 24.
La próxima vez, la cuenta sale de la salida, no de memoria.

**Decidido por la PM:**
- **D276 (a):** el alta sin origen sigue guardando «CN», como la base.
- **D277 (a):** riesgo escrito. El selector de producción sólo mandó doce siglas de dos letras, que
  pasan; tu consulta de sólo lectura se la ofrezco a Emi, opcional, con la copia.
- **Riesgo 2** (traba de `clients` al arrancar): va en la nota de publicar, con la copia.
- **Riesgos 1 y 6** (calculadora y moneda recortadas a 3, reconstrucción de SQLite): cambian
  comportamiento; se los propongo a Emi. No te los asigno.
- El adversario reprodujo que un GET devuelto entero con PUT da 400 para un «CHI» viejo. La pantalla
  no lo manda y producción no tiene esos valores: riesgo escrito, sin código.

## Aviso: guarda de conexiones en `tests/conftest.py` (2026-11-13 16:06 UTC)

Llega con tu próximo merge de mi rama. Un error de teardown «… dejó N conexión(es) de aiosqlite abiertas…» es la guarda funcionando: un test o ayudante deja una conexión viva; se arregla cerrándola, no se saltea. Tu pytest entero sobre `ee2ee3c` corrió sin ella: el de SUFIJO-BORRADOR va después del merge. Desde hoy también corta al arrancar: un `rc=4` con «La guarda de conexiones no ve una conexión abierta de aiosqlite…» es un venv con aiosqlite viejo (antes de 0.22), no un rojo tuyo; instalá el de `requirements.txt` y volvé a correr.

## Vencido `sabotaje_maria5.sh`: aceptado sobre `c0505cc` (informe `9153d23`) e integrado (2026-11-14 09:30 UTC)

Acta `REPRODUCCION-SABOTAJE-MARIA5-2026-11-14.md`. Regla nueva de la PM: en un vencido de sólo
arnés, un último commit que cambia únicamente comentarios no necesita revisor si el informe lo dice.

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
