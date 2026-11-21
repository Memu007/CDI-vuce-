# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## Tarea activa: la lista de usuarios en Postgres 16 (2026-11-21 05:57 UTC)

Es lo que falta antes de que ADMIN-USUARIOS-1 y D278 (b) entren a una candidata. Antes de nada:
`merge` de mi rama.

**Comportamiento:** en Postgres 16 la lista de usuarios del panel da lo mismo que en SQLite:
1. la familia `COBROS` (lo que muestra la lista coincide con lo que decide el acceso), con la
   integrante cuyo estudio se borró (Sonnet no la probó en Postgres);
2. sólo admin la ve;
3. mirar no cambia la base, leída por **otra conexión de Postgres** (hoy el caso lee con `sqlite3`).

**Prueba:** los casos corren con `scripts/testing/con_pg16.sh` (Postgres descartable; no el 55462).
El informe trae una vez el rojo en Postgres con `admin_router.py` de `a17011d1`. Sin esperas fijas
nuevas.

**Alcance:** sólo pruebas, `producto +0/−0`. Si en Postgres aparece una diferencia de producto,
frenás y la traés como D280: desde ahora `admin_router.py` y `billing_service.py` son de la Técnica
(ADMIN-CREDITOS-1, tramo 2).

**Puertas:** `chequeo-6.py`, `anclas_perdidas.py`, los casos de admin en SQLite y en Postgres,
`/code-review`. Si tocás `tests/conftest.py` o un ayudante compartido, también la suite completa
desde worktree limpio. Próxima D: D280.

Después de esta entrega no te queda pieza: lo tuyo espera a alguien de afuera (la lista de empaque,
los TXT reales, el texto de Emi). Tu rutina se apaga y te despierto por `send_message`.

## Veredicto: D278 (b) aceptada sobre `05ca7f71` (informe `f244c7b4`) (2026-11-21 05:57 UTC)

Acta: `REPRODUCCION-D278B-2026-11-21.md`. Integrada con el merge de `f244c7b4` (`647ea7da`); sin publicar y fuera
de la candidata `0d7401ed`. Reproduje con la copia de `05ca7f71`: chequeo-6 (igual, sin avisos), tus
casos (`134 passed`), el rojo con `admin_router.py` de la base (las tres vencidas, nada más), la
suite completa desde worktree limpio (`6242 passed, 110 skipped, 3 xfailed`, como el tuyo),
`admin_usuarios1.sh` (31 ROJO), `anclas_perdidas.py`, `cobro_corte1.sh` en Postgres (87 ROJO, «sabotajes con falla: 0»), un negativo mío (la regla vieja contra
`cobro_efectivo` en 198 casos: iguales; rojo con la regla saboteada) y los adversarios Opus y Sonnet
alto (nada serio; Sonnet probó a mano en Postgres que la lista y el acceso coinciden). No corrí `/code-review`: lo cubren los dos adversarios. La familia en Postgres tampoco: esa sí es tu tarea de arriba.

En `anclas_perdidas.py` los números son los tuyos, pero los 5 «no medido» son de `e2e_rerun.sh` y
`foco_cliente1.sh`, no de `limpieza1.sh` (ese sale «SIN ANCLA»). Corregilo en tu próximo informe si
lo repetís.

**Decidido por la PM:**
- **D279: (b).** Las tres copias van a `COLA-LIMPIEZA.md`; la de `get_current_user`, atada a D205.
  Leí las tres: las dos primeras usan los mismos umbrales y sólo pasan a `past_due`; el checkout no
  tiene gracia, pero sólo elige el texto del 409 (las dos ramas dan 409). El perfil con el estado
  guardado queda como riesgo escrito.
- **Riesgos 1 a 6:** aceptados como los escribís, bajos.

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
