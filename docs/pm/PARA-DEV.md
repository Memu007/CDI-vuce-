# PM → Dev técnica (Dev 1)

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`. La
historia de este canal está en Git.

## Plan de la pieza de producto de CONEXIONES-1: leído sobre `b60c30d4` e integrado (2026-11-12 10:47 UTC)

Integré `b60c30d4` (avance directo, sólo `PARA-PM.md`). El plan queda como
base de la pieza; la pieza sigue esperando el sí de Emi a D182.

- **Lo reproduje:**
  - el comando 1 da `2.0.25 True False`;
  - el comando 2 da 3755 con `require_active_billing` y las 8 con
    `require_billing_vigente`;
  - el mecanismo de la FK, mínimo, en mi PG16 y sin la app:
    - con la dueña en `FOR UPDATE`, el segundo `UPDATE` de la org espera y
      sale `DeadlockDetectedError`;
    - con `FOR NO KEY UPDATE`, el segundo `UPDATE` no espera, el aviso
      confirma y el alta sigue (ok/ok).
- **No lo reproduje:** los resultados 1 a 3 dentro de la app. Los mediste
  sobre árboles sin commitear y no hay copiable.
- **Mi negativo de G no veía el par alta + recarga de la org: bien visto.**
  En el acta, cada «(b)» va a decir sobre qué árbol se midió. En G, (b) era
  el `commit` en la dependencia y perdía la recarga. En tu plan, (b) es
  vigente + el conteo bloqueado, y da deadlock.
- **Pregunta que el plan no contesta: ¿esto pasa hoy?** En HEAD, el guardado
  (8158/8181) y generar MARIA (`_contar_maria`) ya toman a la dueña con
  `FOR UPDATE` y después la org. Con una recarga de la org a la vez, el
  mecanismo es el mismo. Hasta que se mida, no escribo que (b) lo introduce.

**Tus D:**

- **D200: (a), por la PM.** `of=` en las dos consultas, más el caso 6
  mirando el SQL. La subida de SQLAlchemy va a la cola de limpieza.
- **D201: (a), por la PM**, con un dato más en el caso 5 u 8: después de
  borrar `require_active_billing`, los créditos extra vencidos no se pueden
  gastar en un alta manual. Lo hace hoy `_expire_extra_ops` dentro de
  `can_create_operation`, bajo el candado.
- **D202: (a), por la PM.** Lo leí: `_vencer_y_guardar` hace su propio
  `commit` (con `rollback` si falla), así que el `commit` nuevo de vigente
  no lleva esa escritura. Vale tu condición: si el caso 4 da 200 con algo
  perdido, pasás a (b) y lo decís.
- **D203: (a), por la PM**, y el espejo entra como dato del caso 6, no como
  riesgo: `cancel_billing` o `reactivate_billing` + alta de la misma org.
  Si un par da rojo con (a), entra (b) con ese rojo.
- **D204: la medición la ordeno yo; el arreglo lo decide Emi.** Si
  reproduce sobre HEAD, es plata en producción hoy, como D188: no la
  arreglás dentro de la pieza sin su sí. Va en la tarea de abajo.

**Condiciones de la pieza:** siguen las de F y G (base caída en los tres
`commit` como datos, `try/finally`, anclas en código, impaga con JSON roto
en 402, créditos + caso 6, `billing_status`, los demás caminos, revisión
fuerte). Tu plan las cubre todas.

## Tarea activa: CONEXIONES-1 H, sólo arnés: los casos 6 y 7 sobre HEAD (2026-11-12 10:47 UTC)

Tu cola del roadmap no tiene otra pieza que no espere a Emi. Sin producto:

1. **El caso 6 como script en el repo** (≤80 líneas, sin esperas fijas),
   corrido sobre HEAD. Pares: alta + guardado · alta + recarga ·
   guardado + recarga · generar MARIA + recarga · alta + aviso de suscripción
   · `cancel_billing` o `reactivate_billing` + alta. Cuentas: usuario y org.
   Créditos vencidos y no vencidos. Por par: códigos, deadlocks de
   `pg_stat_database` y el SQL de `_cuenta_bloqueada`.
   - Lo que más importa: **si guardado + recarga o generar MARIA + recarga
     de una org dan deadlock hoy.** Si da, es un hallazgo de producción y me
     lo decís arriba del informe.
2. **El caso 7 (D204) como script, sobre HEAD:** un aviso de renovación a la
   vez que una cuenta vencida pasa por vigente, con usuario y org, y con
   trial vencido y `active` fuera de gracia. Si no reproduce, lo decís así.
3. **Los resultados 1 a 3 del plan, copiables:** el parche de (b) +
   `FOR NO KEY UPDATE` como archivo de arnés que los scripts aplican en un
   worktree. Así los reproduzco con un comando.
4. Rojos: los casos corridos con el parche aplicado y sin él, una vez cada
   uno.

`chequeo-6` con producto +0/−0. Tus D siguen en D205–D209.

**Si Emi dice que sí a D182 mientras tanto,** dejás H donde esté, lo decís
en el informe y arrancás la pieza: los scripts de H son sus casos 6 y 7.

## CONEXIONES-1 G: aceptada sobre `6ce56cf9` e integrada (2026-11-12 10:13 UTC)

Evidencia y detalle: acta `REPRODUCCION-CONEXIONES-1-2026-11-12.md`,
sección G (en Git, `a7240cdb`). D188, D186 (b) y D182/D183 están con Emi;
D189 (b) y D184 (a) los decidió la PM.

## FOCO-PERFIL: aceptada sobre `dc4cf077` e integrada (2026-11-12 03:37 UTC)

Evidencia: `docs/pm/REPRODUCCION-BORRADOR-1-2026-11-10.md`, «FOCO-PERFIL».
Integré con `merge` exactamente `365ee834`. Sin D.

- Igual a tu informe: `foco_perfil.sh` sobre `5f78311a`, dos veces, rc=1 y
  PIERDE en los dos casos con los mismos valores robados; sobre `dc4cf077`,
  rc=0 y NO PIERDE con el reloj a 3000 ms tres veces. `chequeo-6` igual.
- Mi negativo: sólo el paso con `p2` vuelto a lo viejo da rc=1 y PIERDE en
  los dos casos, en la tercera apertura. La reproducción distingue cada una.
- `sabotajes/estudio1.sh` sobre `dc4cf077`: 37 ROJO, «sabotajes sin rojo:
  0», rc=0. Tu corrida sobre `78d4188e` vale: lo que cambia después es sólo
  `foco_perfil.sh`.
- Alcance mirado: `cobro_mp1` no escribe en el perfil (bien sacado);
  `sesion1` es de MARIA y ya está avisada.
- `foco_perfil.sh` queda en el repo (tu supuesto, aceptado). El arreglo de
  producto del foco, cuando salga de la cola, cambia `abrirMisEstudios` y
  actualiza o saca `foco_perfil.sh` en el mismo commit.

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
- **D182: a Emi, de día**, con mi recomendación de (a). Si dice que sí, la
  pieza es tuya entera (la dependencia es una sola), con lo que traiga D.

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

