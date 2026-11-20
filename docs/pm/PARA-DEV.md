# PM → Dev técnica (Dev 1)

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`. La
historia de este canal está en Git.

## CONEXIONES-1-NOKEY, vuelta leída: anclas bien, se acepta con PRODUCTO (2026-11-20 17:44 UTC)

Vuelta `090609bc` y `05e61efa`, informe `77556d06`. Acta `REPRODUCCION-CONEXIONES-1-NOKEY-2026-11-20.md`.
**No es aceptación todavía:** la vuelta está encima de `7f4e04d1` y otros de PRODUCTO, así que
NOKEY se acepta e integra junto con PRODUCTO, sobre su SHA final. No hace falta separar nada.
Seguí con PRODUCTO, con lo sumado abajo.

- **Anclas:** `anclas_perdidas.py 05e61efa` da 0 PERDIDA (lo corrí). `limpieza1.sh` ya ancla en el
  nombre del job (`ac4993b7`, coincide con `ci.yml`): el vencido queda cumplido y su línea de
  `sabotajes-conocidos.txt` sale al aceptar.
- **`conexiones1_nokey.sh` sobre `05e61efa`:** rc=0 y los tres BIEN, igual a tu informe. Como
  «sin sabotaje: salida 0» depende de `7f4e04d1`, pasa a ser puerta de PRODUCTO.
- **El intermitente.** «Del arnés, no de la app» queda: `dispose(` sólo está en `close_db()` y no
  apareció el aviso `non-checked-in`. Tu arreglo espera una condición observable y queda. Pero el
  mecanismo está incompleto: forcé la carrera con 1 s de espera en la tarea de log, antes y después
  del `commit`, y el `soltar()` viejo pasó las dos veces (el nuevo tardó 101 s contra 44 s: la tarea
  estaba viva en el dispose). El `soltar()` viejo ya repetía dispose + gc justo para ese camino.
  Falta explicar por qué en tu volcado esa conexión sobrevivió 14 s de dispose + gc repetidos.
  **Un párrafo con evidencia en el informe de PRODUCTO**; si no sale, va como riesgo abierto. Un
  rc=2 «la app no soltó» con el `soltar()` nuevo, tuyo o mío, lo reabre como segunda causa.
  11/12 contra 12/12 no separa el arreglo de la suerte: no lo uses como prueba.
- **D231: (a)**, decidido por la PM: queda el pin de SQLAlchemy 2.0.25 y el `of=`.
- La palabra del CHANGELOG se corrige en PRODUCTO: de acuerdo.
- **No corrido por la PM:** `cobro_corte1.sh`, la suite, `e2e_maria.sh`, adversarios y
  `/code-review` sobre `05e61efa`. Van sobre el SHA final de PRODUCTO.

## Tarea activa: CONEXIONES-1, el arreglo de producto, en dos piezas (2026-11-20 13:56 UTC)

**Sí de Emi (20/11, leído 13:53 UTC: «Dale a todo» al punto 20: D206 (a), y D182 con D183 y D188).**
No es un «dale» de publicar. D205 (la renovación que deja `past_due`) **no** entra: sigue con Emi.
Antes de tocar código: `merge` de mi rama y tu `/compact conservar` al día (estás cerca del umbral).
Todo lo medido está en `REPRODUCCION-CONEXIONES-1-2026-11-12.md` (C, D, G, plan, H a K) y en tu plan
`b60c30d4` (D200–D203 (a), decididas por la PM).

### Pieza 1: CONEXIONES-1-NOKEY (D206 a), sola y primero

- **Comportamiento:** con créditos extra vencidos, recarga + guardado y recarga + MARIA a la vez no
  dan error ni dejan la recarga sin acreditar.
- **Lo que tiene que dar, según H a K:** esos dos pares, 0 deadlocks y la recarga acreditada en la
  misma ronda. Siguen rojos, y es lo esperado: los tres de alta (alta + guardado, + cancelar,
  + reactivar), recarga + alta (D188) y las dos filas de renovación (D205). Si algo de esa lista
  pasa a verde, o uno de los dos pares no, decilo con la salida.
- **Prueba:** el caso 6 (el SQL que llega a Postgres después de que el aviso compiló el suyo) y la
  carrera sin forzar de H, con el rojo una vez con el arreglo vaciado en el mismo SHA.

### Pieza 2: CONEXIONES-1-PRODUCTO (D182, D183, D188), apenas entregues la 1

Sobre la pieza 1. Comportamiento y pruebas; el cómo es tu plan (sugerencia, no criterio):
- con 60 pedidos lentos de una cuenta, **otra** cuenta no espera más de ~1 s ni recibe errores, en
  sugerir, subida de PDF, analyze y la carga manual (medidor de C y D, con cuota de producción);
- una cuenta impaga recibe «falta pagar» sin que se lea su pedido entero (la memoria del 4×100 de G,
  como hoy);
- recarga + alta con créditos vencidos: 0 recargas perdidas (D188, con el detector de J);
- un cliente que corta a mitad del cuerpo contesta como hoy (400), sin ERROR ni fila 500;
- cada `commit` nuevo que suelta la conexión tiene su caso con la base caída (D202);
- las dos filas de D205 siguen como hoy («cuenta mal»): no las arregles;
- el diff propuesto del informe entra con `git apply --check`.

**Sumado a PRODUCTO (20/11, adversarios y revisión de NOKEY).** Todo esto es criterio:
- el par recarga + cancelar y recarga + reactivar en el arnés de pares;
- `conexiones1_creditos.py` «perdidos 10» como el rojo de D188 en la base y 0 en tu SHA;
- para cada candado nuevo, el SQL capturado con la cache caliente, en los dos órdenes;
- `conexiones1_creditos.py:38` todavía fija `GEMINI_API_KEY="test-key"`: que no la fije;
- `conexiones1_nokey.sh` con «sin sabotaje: salida 0» y `anclas_perdidas.py` sobre la base y sobre
  tu SHA, sin PERDIDA nueva, y el sabotaje «el job con continue-on-error» de `limpieza1.sh` en ROJO;
- tu rango borra líneas de pruebas de plata (`test_cobro_corte1.py`, `test_maria1b_controles.py`,
  `test_prelaunch_block2/3`) y el paso «activa» de `cobro_corte1.sh`: cada una con su porqué, y la
  cuenta de ROJO de `cobro_corte1.sh` (hoy 87) contra la última aceptada;
- el 500 por clave foránea en alta contra borrar cliente queda como riesgo escrito, sin arreglarlo.

### Revisión fuerte (las dos piezas; en la 1, en proporción a sus líneas)

`/security-review`, adversarios **con Postgres 16** (el de D corrió con SQLite), la suite completa
desde base limpia sobre el SHA que entregás, `e2e_maria.sh`, y un guion de sabotaje propio anclado en
código. Adversarios sin red y con `GEMINI_API_KEY` vacía.

**Próxima D: D232.**

## CI-TOPE: aceptada sobre `c721f7fc` (informe `a0299443`) e integrada (2026-11-17 00:50 UTC)

Acta `REPRODUCCION-CI-TOPE-2026-11-17.md`. **Traé mi rama con `merge`.**

- Igual a tu informe: el diff fuera de `docs/pm` es la sola línea y el YAML da `tests` 30, `e2e-maria` 10.
- Mi negativo: ningún paso de `ci.yml` trae otro tope (`grep` de `timeout`, `--max` y `pytest`).
- La CI queda como no corrida: se ve en la próxima PR de publicación.


## Aviso: MARIA toca `test_sufijos2.py` y `sabotajes/sufijos2.sh` (2026-11-14 PM)

D247 ya está integrada. Por D249 (a), en `PARA-DEV-2.md`, MARIA vuelve a tocar esos
dos archivos (más casos y sabotajes para los mensajes de `limpiar_sufijo`), después
de otras piezas. No es tarea tuya; al traer mi rama, esos dos archivos pueden cambiar.

## GUARDA-VERSION: aceptada sobre `9661f5d3` (informe `bb83ecc6`) e integrada (2026-11-13 17:31 UTC)

Acta `REPRODUCCION-GUARDA-VERSION-2026-11-13.md`, sección «Vuelta 2».
**Traé mi rama con `merge`.**

- Igual a tu informe: `chequeo-6` (arnés +85/−6, 0 avisos), `4 passed` el
  archivo solo y el pytest entero sobre `9661f5d3`: `6130 passed, 110 skipped, 3 xfailed`, 1134.62 s, rc=0, 0 «dejó».
- Mis negativos, todos distintos de los tuyos:
  - sin la foto, o `or reporte.failed` → `or True`: caen tus tres datos de fuga;
  - la foto vacía: cae «la culpa es de quien la deja»;
  - `trylast=True`: cae sólo «foto antes de los fixtures»;
  - sin el chequeo de arranque: cae sólo «chequeo de arranque»;
  - sin `tryfirst`: verde, y es correcto (el conftest ya va antes).
- **Decidido por la PM:** el rojo nombra el dato que cae, y con eso alcanza
  para decir cuál se rompió. Acepto tu supuesto: la línea del resumen sale.
  Acepto también el riesgo del tope: bajarlo sólo trae falsas alarmas.
- D230 sigue con Emi (ahora no; va a la cola con los otros `async for`).


## Plan de la pieza de producto de CONEXIONES-1: leído sobre `b60c30d4` e integrado (2026-11-12 10:47 UTC)

Acta, sección «Plan» (en Git, `6001684c`). D200–D203 (a) por la PM, y siguen
para la pieza: D201 con el dato de que los créditos extra vencidos no se
gastan en un alta manual; D202 con tu condición (si el caso 4 da 200 con
algo perdido, pasás a (b)); D203 con `cancel_billing`/`reactivate_billing` +
alta como datos del caso 6.

## CONEXIONES-1 C: aceptada como medición sobre `9ecfd2ac` e integrada (2026-11-12 03:29 UTC)

Evidencia: `docs/pm/REPRODUCCION-CONEXIONES-1-2026-11-12.md`, sección C.
Integré con `merge` exactamente `9ecfd2ac`.

- Igual a tu informe: hoy, la otra cuenta espera 30,02 s en sugerir y 30,0 s
  en la subida (5,26 s con cuota), rc=4 las dos; con el arreglo, 0,32 s y
  0,04 s (0,35 y 0,06 con cuota), rc=0. Control: cinco `BIEN`. `chequeo-6`
  igual. Las ocho rutas de la dependencia, contadas.
- Mi negativo, pico de 40 con el arreglo: rc=0, 0 × 500, la otra cuenta
  hasta 2,29 s. La subida da 40/40 con 40 y 50/50 con 60, y la otra cuenta
  no espera: leo pico, no retención, pero no está muestreado (abajo, D).
- pytest con el arreglo: 201 passed. Sin el ajuste del inyector, tus 4 rojos.
- **Hallazgo menor:** el diff de tu informe no entra con `git apply` (el hunk
  de `main.py:10448` está cortado). Lo apliqué a mano. En el próximo, el diff
  propuesto va completo y probado con `git apply --check`.
- D182: Emi dijo que sí el 20/11 (tarea activa, arriba).

## BORRADOR-1: aceptada sobre `c8733be` e integrada (2026-11-12 00:48 UTC)

Evidencia: `docs/pm/REPRODUCCION-BORRADOR-1-2026-11-10.md`. Integré con
`merge` exactamente `c8733be` (tu informe `52029147` incluido), no tu cabeza:
CONEXIONES-1 B (`c57b645e`) la reviso aparte. El producto que entra es el de
`22163cec`, línea por línea. Igual a tu informe: los cinco arneses de
navegación (ninguno con 429), `estudio1b`, `despacho1d`, `borrador1`,
`cobro_mp1`, el ataque sin Postgres y su control, `chequeo-6`, tu portón y tus
`--remerge-diff`. Además corrí la e2e de MARIA (`E2E MARIA OK`), la suite
completa (`6077 passed, 110 skipped, 3 xfailed`) y, sobre el merge, el arnés 402 de MARIA
(`118 passed`). Una diferencia, abajo.

- **D149 (a):** aceptada; `estudio1.sh` quedó cerrado en IDS-PYTEST.
- **D145 (a) y D173 (a):** aceptadas. Los dos commits de arnés en vez de uno,
  también: no hacía falta `push --force`.
- **Supuesto de `destino1`** (manda la `X-Forwarded-For` pero no mira el
  status del registro): a la cola de limpieza.
- **El AVISO de `chequeo-6`** en `pantalla_cliente1.js:27` (296 → 297):
  aceptado; partir esa función va a la cola de limpieza.
- **El ataque no mira la versión de Postgres:** riesgo bajo, aceptado sin
  pieza.
- **D170 (b), D171 y D172** quedan como el 10/11 (acta): D171 espera a Emi;
  no la empieces.
- **La e2e de MARIA** sigue siendo puerta para lo que toque el recorrido
  MARIA o `static/v2`. Hoy da `E2E MARIA OK`: cualquier rojo es tuyo.
- **La diferencia de `estudio1` (ids de pytest):** cerrada en IDS-PYTEST.

**Tu rango de D: D180 a D189.**

## CONEXIONES-1, la tarea original (2026-11-08 PM)

Pasa de la cola de MARIA a la tuya, decidido por la PM: es de base y de
servidor, y MARIA tiene cuatro piezas por delante. Está en el roadmap (sí de
Emi del 28/10). El origen es la D37 de MARIA:
`git show 1f648c3:docs/pm/PARA-DEV-2.md`, y la D46 en `PARA-DEV-2.md`.

- Medí si un `await session.close()` cancelado (el `finally` de
  `get_async_session`, `database/connection.py`) deja conexiones tomadas:
  gunicorn con la misma configuración del `Dockerfile` y Postgres 16
  descartable, muchas respuestas 401 y algunas normales, mirando
  `pg_stat_activity` y el pool.
- Condiciones de la D46: esperás a que `api_logs` tenga todos los pedidos
  (no tiempos fijos); un control que cancele el `close` a propósito y tenga
  que dar rojo; cortes en vuelo de verdad (cliente que corta a mitad).
- También entran la conexión tomada durante bcrypt, Gemini en
  `/api/ncm/sugerir` (con la clave vacía y sin red) y la subida pública de
  PDF (D74 de MARIA).
- Si quedan conexiones tomadas: arreglo con una prueba roja antes y verde
  después. Si no quedan: producto sin cambio, el informe trae los números y
  el aviso de las pruebas sigue en riesgos.
- Toca todas las rutas: revisión fuerte, adversario y `/security-review` si
  hay producto.
- Corte, como antes: el **2026-11-09 a las 05:00 UTC**. Si no llegás,
  commit, push y anotá dónde quedaste.

**D134: (c), decidido por la PM.** Medí A y B en las dos ramas. En MARIA,
sobre `40423be` (EMAIL-1, su última aceptada), no sobre su punta, que trae
AVISOS-2 sin revisar. Un arreglo de A (middlewares o `get_async_session`, que
son iguales) va en tu rama. Un arreglo de B (`dependencies.py` o rutas) espera
a que yo integre la rama de MARIA: hasta entonces, el informe trae los
números y el arreglo propuesto, sin commitearlo.

## PERMISOS-3: aceptada sobre `9428e00`, sin integrar (2026-11-08 PM)

Evidencia: `docs/pm/REPRODUCCION-PERMISOS-3-2026-11-08.md`. Igual al informe:
chequeo-6 `+8/−12` sin avisos; `permisos2.sh` 10 ROJO, falla 0; `60 passed`;
ataque `47 · 0 · 0`. Sonnet alto: ninguna variante se registra (Unicode,
`\n`, `\x00`, mayúsculas), sin 500 y sin cambio en el front ni en el login.
Tus supuestos quedan como están.

- **D127: (b), decidido por la PM.** Nombres únicos sin mayúsculas para todas
  las cuentas es una pieza aparte, y antes hay que mirar producción: se la
  propongo a Emi. Sin su sí no entra.

## AISLAMIENTO-2 y LIMPIEZA-1: aceptadas sobre `c86f3ff`, sin integrar (2026-11-08 PM)

Evidencia: `docs/pm/REPRODUCCION-AISLAMIENTO-2-LIMPIEZA-1-2026-11-08.md`.
Igual al informe: chequeo-6 (`+2/−3`, avisos 0), `50 passed`,
`limpieza1.sh` 37, `aislamiento2.sh` 10 + 18 ROJO, todos con «sabotajes con
falla: 0», y el ataque `Bloqueado: 47 · Fugas: 0 · Sin probar: 0`.

- **D114:** contestada en la devolución de arriba (el reintento concilia,
  dentro de COBRO-MP-2+3).
- **D116: (b), decidido por la PM** (Emi: arreglos chicos de seguridad, sí).
  Pieza **PERMISOS-1**, después de la devolución de COBRO: ningún usuario
  llega a admin por un email que él mismo puso. Caso: cambia su email a uno
  de `ADMIN_USERNAMES` sin cuenta, reinicio, sigue sin admin; la familia
  como datos (mayúsculas, espacios, el email de una cuenta que se borró).
  Revisión más fuerte (§3): sabotaje propio.
- **El registro con invitación sin comparar el email:** ya es parte de ORG-1
  (MARIA, «atadas al email»); no lo tocás.
- **`.claude/skills/entregar/SKILL.md`:** saco «(cubre sólo clientes y
  descargas)» (hecho en este commit).
- **A la cola de limpieza:** normalizar `roles` al leerlos de la base
  (`/auth/me` devuelve crudos); el arranque que parte un texto en letras; el
  comentario nuevo de `ci.yml` cuenta historia; `CLAUDE.md` §5 dirá que la
  CI ya no deselecciona cuando esto llegue a `main`.

Tu orden: **la devolución de COBRO-MP-2+3** → PERMISOS-1 → BACKUP-1a →
EXCEL-2c. Próxima D libre: D117.

## Veredicto de COBRO-CORTE-1, vuelta 4 (2026-11-06 PM): aceptada, sin integrar

Sobre `ca50916`. Evidencia: `docs/pm/REPRODUCCION-COBRO-CORTE-1-v4-2026-11-06.md`.
`test_cobro_corte1.py` da `98 passed`; tus sabotajes, 88 `ROJO` y
`sabotajes con falla: 0`; la suite completa, `4284 passed, 335 skipped,
3 xfailed`, rc=0. El chequeo-6 da los 3 avisos que explicaste. Opus y Sonnet
alto no encontraron doble cobro ni datos de una carga en otra; lo de la
devolución queda cerrado (la respuesta escribe en la carga que la pidió, B
genera cuando vuelve A, regenerar no depende de `os.link`). No la integro
todavía: tu rama lleva debajo piezas sin aceptar desde `e0b8626`.

**A la cola de limpieza** (decidido por la PM, no son de esta pieza):
Enter doble en «Reintentar» o «Generar» (dos generaciones, sin cobro extra),
`CDI.api` sin timeout (spinner colgado), la falla doble commit + restaurar
`.anterior`, y `PUERTO` de `con_pg16.sh` que pisa el de tus sabotajes
(renombrar a `PG_PUERTO`; si tocás `backup1a.sh` en BACKUP-1a, hacelo ahí).

**VALIDACION-1: aceptada** sobre `c24a266` (producto `0bd4b6c`, informe
`9bc75e9`; 2026-11-07 PM), sin integrar: tu rama lleva debajo COBRO-MP-2+3 en
devolución. Evidencia: `docs/pm/REPRODUCCION-VALIDACION-1-2026-11-07.md`.
`validacion1.sh` da 7 ROJO y `FALLAS=0`; chequeo-6 con tus 2 avisos
explicados; Sonnet alto no encontró camino con datos de otra carga. Quedan
como riesgos, no los pido: sacar `!force` o el vencimiento de 60 s no lo ve
ninguna prueba; «Calcular seguro» cambia la cabecera sin revalidar; tu riesgo
1 (historial 0 con el validador caído) va a la cola como pieza aparte.

**CSRF-3: aceptada** sobre `9fe55d4` (2026-11-05 19:20 UTC), integrada. Evidencia: `docs/pm/REPRODUCCION-CSRF-3-2026-11-05.md`. Suite 4450 passed, csrf3/2/1 en rojo (8, 10, 8), chequeo-6 sin avisos; Opus y Sonnet alto sin hallazgo que bloquee. El 500 de `/dashboard` sin base y la carrera del token van a la cola de limpieza.

**Tu orden:** la devolución de COBRO-MP-2+3 →
AISLAMIENTO-2 / LIMPIEZA-1 → BACKUP-1a → EXCEL-2c. Próxima D: D62; desde ahora usás
los pares y MARIA los impares, para que no choquen.

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

