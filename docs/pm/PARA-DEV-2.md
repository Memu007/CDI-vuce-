# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## D239 (a): devolución sobre `196ef370` (informe `0364f07e`) (2026-11-17 03:05 UTC)

Acta `REPRODUCCION-D239a-2026-11-17.md`. Lo que corrí da igual que tu informe (pruebas, rojo
revertido, chequeo-6, `sin_sigla`, `holanda423`, `catalogo3`, `e2e_maria.sh`, volcado). Los 114
códigos sin sigla funcionan y la tabla entera vuelve bien (616 formas, ninguna sin origen). Pero hay
una devolución, y es una sola causa.

**Causa:** al separar el código del nombre, lo que no se reconoce como nombre se descarta y gana el
código, aunque ese resto nombre otro país. Así aparece en silencio el país del código, justo lo que
el criterio 2 prohíbe. Ejemplos, con lo que daba la base y lo que da `196ef370`:

| texto del despacho | base | `196ef370` |
|---|---|---|
| «143 CHINA (MAINLAND)» | CN | 143 (Sudáfrica) |
| «310 HONG KONG (TERRITORIO DE CHINA)» | ninguno | CN |
| «410 MADEIRA (TERRITORIO DE PORTUGAL)» | ninguno | ES |
| «143,00 310 CHINA» | ninguno | 143 |
| «143.5 CHINA» | ninguno | 143 |

Los dos primeros grupos vienen de nombres de la tabla con paréntesis (unos 30). Los últimos, de un
número pegado a otro número; ese camino (kilos que se superponen con la columna de origen en
`leer_texto`) lo mostró el adversario, pero no lo reproduje con un PDF real.

**Criterio de la vuelta (comportamiento y prueba):**
1. Un texto que, además del código, nombra otro país (entre paréntesis, pegado o después de
   números) da ningún origen y el aviso. Nunca el país del código en silencio.
2. Un número que no es un código de tres cifras suelto («143,00», «143.5», «143 310») no se toma
   como código.
3. Un caso con la familia como datos: los nombres de la tabla con paréntesis o punto puestos al
   lado de un código de otro país, y las formas de número de arriba. La lista de nombres sale de la
   tabla, no escrita a mano. Lo de hoy que ya andaba (los 114, «143», «143 REPUBLICA DE
   SUDAFRICA», «310 CHINA») sigue igual.
4. El rojo de ese caso con el arreglo revertido, una vez en el informe.
5. En la vuelta: suite completa y `despacho1b.sh` sobre el SHA (en ésta no los corrí yo), y
   `e2e_maria.sh`.

Sugerencia, no criterio: hoy el `\b` deja que «143,00» empiece con un código, y el `\W*$` final le
saca a un nombre de la tabla su «)». Ese patrón además es cuadrático con textos largos de guiones
(el adversario midió 9,2 s de CPU con 500 subítems armados a mano; yo, 0,018 s en una llamada
contra 0,0001 s de la base). Eso es un riesgo que queda escrito, no criterio: necesita un PDF
fabricado.

**Respuestas (decidido por la PM):**
- **D264** (código con un nombre que no se reconoce): (a), gana el código, como hacía la base con
  los códigos con sigla («310 XYZ» da CN). Con el límite del criterio 1: si el resto nombra otro
  país, no gana.
- **D265** (número fuera de la tabla con nombre con puntuación): (a), gana el país del nombre,
  como en la base con «900 CHINA».
- **Supuesto 1** (campo de origen sin tope de largo y etiqueta «Origen»; valida el servidor con
  422): aceptado.
- **Supuesto 2** (el caso del «Origen frecuente» contesta `/metricas` con «434 · HOLANDA»):
  aceptado.
- **Pérdidas con aviso** («402 ALEMANIA», «601 RUSIA», «668 HONG KONG», «653 ARUBA»… dan ningún
  origen y el aviso): aceptadas. Son ruidosas y no ponen un país equivocado. Además, el nombre de la
  tabla de cada uno sigue andando.

## D239 (a), códigos sin sigla en el lector de despachos (la pieza, para la vuelta)

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

**Próxima D: D266.**

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
