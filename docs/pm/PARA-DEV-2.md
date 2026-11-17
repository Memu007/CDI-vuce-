# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## Holanda→423: aceptada sobre `b3a3bf69` (informe `97a066a8`) e integrada (2026-11-17 01:05 UTC)

Acta `REPRODUCCION-HOLANDA-423-2026-11-16.md`, sección «Vuelta». Reproduje tu rojo, `holanda423.sh`,
`seguro2.sh`, `e2e_maria.sh`, chequeo-6 y la suite entera (`6197 passed`): todo igual al informe.
El adversario no rompió nada. Probé ejemplos que no di: «CN» → «BR» → «CN» guardando sin recargar
(queda «CN»), lo mismo con un guardado fallido, y otros países en la procedencia («310 · CHINA»,
«434 · BELGICA»…), que se ven como vinieron.

- **Supuesto 4** (se ve «423», no la etiqueta): aceptado, decidido por la PM. Las etiquetas son D261.
- **Supuesto 5** (la fila manda el origen sólo si cambió): aceptado, decidido por la PM.
- **«Origen frecuente»** (`clientes.js:1139`), preexistente, decidido por la PM: el adversario lo
  reprodujo por la API. Va como criterio 6 de D239 (a), abajo.
- **Riesgo que queda escrito:** `mostrar` sin guarda de `CDI.paisesMaria`; sin camino hoy.

No se publica: espera el próximo «dale» de Emi.

## Tu próxima pieza: D239 (a), códigos sin sigla en el lector de despachos (activa ya)

Emi dijo sí a D239 (`DECISIONS.md`, 2026-11-16 18:42 UTC); va después de Holanda→423. Es tu D239
de `22e84e5d`, medida otra vez sobre `a910c5f`: 114 códigos de la tabla no tienen sigla de dos
letras (`_iso2_por_codigo_maria`). Un despacho que trae uno solo («143») sale sin origen y con
«No reconocí el origen…», y uno con código y nombre de países distintos elige el nombre
(«143 CHINA» da CN). Lo guardado no se migra.

**Criterio (comportamiento y prueba):**
1. Un código de la tabla sin sigla, escrito solo o con su propio nombre, entra por el lector de
   despachos, se guarda y genera ese código en el TXT (`CARTPAYORI`). La familia (los 114, con y
   sin su nombre) como datos de un solo caso; la lista sale de la tabla, no escrita a mano.
2. Código y nombre de países distintos dan ningún origen y el aviso, también cuando el código no
   tiene sigla («143 CHINA», y uno con sigla como «310 BRASIL», que ya lo hace). Un código con
   sigla, solo o con su nombre, sigue dando la sigla.
3. La pantalla de importar un despacho muestra y deja guardar el origen de tres cifras (hoy el
   campo corta en dos, `clientes.js:1692`), y lo que guarda llega igual al TXT.
4. Un volcado antes y después del lector de despachos sobre las mismas formas que usaste en
   Holanda (criterio 2): las únicas diferencias son los códigos sin sigla y los pares que se
   contradicen. El diff va al informe.
5. El rojo con el arreglo revertido, una vez en el informe.
6. El «Origen frecuente» de las métricas del cliente (`clientes.js:1139`) con un 434 guardado se ve
   como lo que sale en el TXT (423); los demás países, como hoy. Es una línea de la misma causa que
   Holanda→423, en un archivo que ya tocás.

**Revisión:** §3 fuerte (cambia un valor que sale en el TXT): `/security-review`, adversarios,
suite completa, `e2e_maria.sh` sobre el SHA y los guiones que anclen lo que toques.

**Lo que sigue en tu cola:** D263 (validación mira `origen`, el generador usa `pais_origen`), después
de ésta; D262 (a) ya está en la cola de limpieza.

**Próxima D: D264.**

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
