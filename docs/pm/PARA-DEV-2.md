# PM → Dev MARIA (Dev 2)

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`. La historia de este canal está en Git.

## D263: aceptada sobre `9e5960d2` (informe `b039eabb`), integrada; D269 activa (2026-11-17 11:50 UTC)

Acta `REPRODUCCION-D263-2026-11-17.md`. Lo que corrí da igual que tu informe: chequeo-6 (+19/−13,
`avisos: 0`), el rojo con el arreglo revertido, suite completa (6200 passed), `e2e_maria.sh` OK,
`origen_txt.sh` 4/4, maria3 32, maria4 8, maria8 70, `catalogo3.sh` «fallas: 0», y anclas como la base. Revertí cada uno de los
seis lugares de `origen_de` de a uno: validación y generador dan rojo con tu caso; clave de posición,
defensa del grupo y los dos supuestos quedan verdes, y cada uno cambia con una entrada mía (acta, y
abajo en D269). Mis negativos por el endpoint con renglones
juntos y con `grupo_id` dan, en cada 200, el valor validado, y muestran que la entrega arregla dos cosas de la base
(«4340» salía en el TXT al juntarse, y un `pais_origen` en blanco rechazaba un grupo bueno).

De D239 (a): mi `despacho1b.sh` con Postgres terminó: 136 `ROJO`, 0 sin rojo, `rc=0`. Se sostiene.

**Respuestas (decidido por la PM):**
- **D268** (el generador sin validar escribe 310): riesgo escrito, no pieza. El único llamador valida
  antes; no hay camino de hoy. Si aparece otro llamador, su pieza lleva la validación.
- **Unidad** (`unidad="  "` con `unidad_medida="KG"` sale 07): riesgo escrito. Sale con el aviso «la
  unidad no se reconoce», y la pantalla manda sólo `unidad`. No va a la cola de limpieza.
- **Cambios por API y sub-ítems:** aceptados como están; riesgos escritos en el acta.
- **Sin caso propio:** no alcanza. `test_supuestos_leen_el_origen_como_el_generador` no cubre la clave
  de posición (lee el aviso de estado con «CN»; la clave revertida quedó verde). Los cuatro lugares
  sin caso van como criterio 5 de D269.

## D269: los avisos no toman un origen que falta como China, y un caso por lugar de `origen_de` (pieza activa)

Hallazgo del adversario de D263, ya estaba en la base. `/generate_maria/avisos` lee el origen con
`get_pais_codigo(origen_de(item))`, que con un origen vacío o no reconocido da 310. La pantalla manda
«XX» cuando el origen está en blanco (`finalize.js`). Con un ítem «CN» y otro igual con «XX», los avisos
dicen «los renglones 1 y 2 van en un solo ítem (misma posición SIM, origen…)» y «Estado… 2 (nuevo sin
uso importado) por defecto»; después generar frena con «Origen no reconocido 'XX'». El aviso engaña
antes de generar. Pieza de la PM (`DECISIONS.md`, 2026-11-17).

**Criterio (comportamiento y prueba):**
1. Con un ítem sin origen o con uno no reconocido, ningún aviso lo trata como China: no lo junta con
   otro renglón ni le aplica el estado de importado. Un aviso nombra el ítem y dice lo mismo con que
   generar va a frenar.
2. La familia, como datos en un caso: vacío, en blanco, «XX», un nombre que no es país, y lo mismo
   por `pais_origen`.
3. Con orígenes válidos, los avisos y el TXT quedan como hoy.
4. El rojo con el arreglo revertido, una vez en el informe.
5. Los cuatro lugares de `origen_de` que hoy no tienen caso, como filas de datos en un caso
   (`pais_origen` en blanco viene por la API, no por la pantalla):
   - clave de posición: tres de la misma posición, uno CN, uno con `pais_origen` en blanco y `origen`
     BR, y uno BR → 2 ART (los dos BR juntos);
   - defensa del grupo: ese par BR con el mismo `grupo_id` → 200;
   - «sin estado»: `pais_origen` en blanco, `origen` AR, procedencia AR → sin aviso de estado;
   - «sin procedencia»: `pais_origen` en blanco sin `origen` → sin aviso de procedencia.
   Al aceptar, en cada uno de los seis lugares cambio `origen_de(item)` por la lectura sin `strip`
   (`pais_origen or origen`), de a uno, y falla la fila de ese lugar.
6. Si tocás lo que comparte el TXT (`clave_de_posicion`, el agrupado), revisión §3 fuerte: suite
   completa, `e2e_maria.sh` sobre el SHA y los guiones que anclen lo que toques. Si no, el caso, la
   suite y `e2e_maria.sh`.

**Próxima D: D270.**

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
