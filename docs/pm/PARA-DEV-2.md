# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## Retomá D252 (a) en la sesión nueva (2026-11-15 02:14 UTC)

Emi abrió esta sesión nueva por el bucle de compactación; la pausa se levanta. Partís de `aec95f3`
(pruebas en `bd009cc`) y de tu nota «PAUSA» y el borrador arriba de `PARA-PM-2.md`: falta medir
contra «el resto» los 22 `SIN MEDIR`, cerrar D257 y el riesgo 2, completar los `(pendiente)` y `/entregar`.
El rojo de `test_despacho1b` (punto 4) se vuelve a medir solo, sin carga, y se informa con causa.
**Evidencia:** las salidas de la sesión vieja quedaron en su contenedor. Lo que vaya al informe se
vuelve a correr acá, o se marca «medido en la sesión anterior, salida no conservada». `mut*.py`,
`medir_resto.sh` y `tabla.py` no están: se rehacen desde el borrador. No pongas pruebas nuevas
en el repo. Nada de subagentes que queden vivos después de su informe: frenalos por PID o `TaskStop`.

## Aviso: guarda de conexiones en `tests/conftest.py` (2026-11-13 16:06 UTC)

Llega con tu próximo merge de mi rama. Un error de teardown «… dejó N conexión(es) de aiosqlite abiertas…» es la guarda funcionando: un test o ayudante deja una conexión viva; se arregla cerrándola, no se saltea. Tu pytest entero sobre `ee2ee3c` corrió sin ella: el de SUFIJO-BORRADOR va después del merge. Desde hoy también corta al arrancar: un `rc=4` con «La guarda de conexiones no ve una conexión abierta de aiosqlite…» es un venv con aiosqlite viejo (antes de 0.22), no un rojo tuyo; instalá el de `requirements.txt` y volvé a correr.

## D251 (a): aceptada sobre `9d580db` (informe `7a3c594`) e integrada (2026-11-14 17:45 UTC)

Acta `REPRODUCCION-D251-2026-11-14.md`.

- Con la copia de `9d580db`: 43 `ROJO`, 0 `FALLA`, `rc=0`; el guion de `01bc9df` sobre `9d580db`,
  39 `ROJO`, `rc=0`. Chequeo-6 igual al tuyo, anclas 0/0/0.
- Mi negativo de la familia: `:2225` armado con el primero y la cantidad
  (`range(ns[0] + 1, ns[0] + 1 + len(ns))`) da `3 failed` con tu prueba y `61 passed` con la
  de `01bc9df`. Otros dos (los renglones al revés, el sufijo de la operación por encima del
  propio) ya daban rojo con la prueba vieja.
- **Supuestos 1 a 7 y riesgos 1 a 5:** aceptados. **Riesgo 6:** pregunta para el
  despachante, queda en el acta; no es pieza.
- **D253 (a)** y **D254 (a)**, decididas por la PM: quedan como límite escrito en el acta.
- **`SKILL.md:28`:** ahora dice que `/code-review` corre otra vez si sumás commits. **Las dos
  líneas de la cola** van como las propusiste. **`NOW.md`, la línea `conservar`:** corregida.

## D252 (a) (2026-11-14 17:45 UTC)

D252 (a), decidida por la PM. El camino existe hoy y lo medí sobre `9d580db`: tus filas 22,
34, 35, 36 y 37 dan `77 passed`. El aviso de cada renglón (`:2230-2231`) le dice al
despachante qué producto corregir, y con `del renglón {ns.index(n) + 1}` diría otro número
sin que ninguna prueba se entere. La causa es la misma de D251: las pruebas de esos avisos
sólo usan dos renglones seguidos, y ningún renglón que va solo queda entre dos que van juntos.

Criterio de D252: la familia, no un ejemplo.
1. El aviso de cada renglón de un ítem de renglones salteados, con su texto entero, desde el
   primero, uno del medio y el último del ítem, en un ítem más largo que cualquier tope (cinco
   renglones o más), y con un renglón que va solo entre medio y tiene su propio aviso.
2. Un renglón que va solo, entre dos que van juntos, conserva sus avisos propios. Son dos
   datos: uno sin grupo, con su sufijo mal escrito (su aviso nombra su ítem), y uno con grupo,
   que en los avisos de sufijo y de arancel se nombra por su grupo. Un renglón con grupo nunca
   entra en `renglones_por_posicion` (`:972`), así que puede quedar entre dos que van juntos:
   es la entrada que distingue `:2187` y `:1953`. Si ninguna entrada distingue `:1953`, lo
   decís con la medición y va como D.
3. Datos de los casos que ya existen, no casos nuevos por cada fila.
4. Tus filas 22, 34 a 37 y 52 a 54 van a `sabotaje_maria8.sh` y dan `ROJO` con un dato
   nombrado; el guion entero en `ROJO` con la cuenta exacta; las anclas no empeoran;
   `/code-review high` hasta el SHA que entregás.

**Cómo sigue:** D252 (a).

D244 y D239 esperan a Emi:
- Si dice que sí a D244, te la escribo con su criterio.
- Si dice que sí a D239 (a), lleva adentro, como datos de un caso, un código sin sigla con
  el nombre de otro país («434 BELGICA» guarda `BE` sin avisar).
- Si Emi dice que «Holanda» también es 423, es una pieza chica aparte.

**Próxima D: D255.**

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
