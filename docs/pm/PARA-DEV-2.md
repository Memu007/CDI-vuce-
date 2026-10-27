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

## Al traer mi rama (2026-10-25)

Mi rama ya trae lo aceptado de la Dev técnica (EXCEL-3d, CLIENTE-1b,
ESTUDIO-1 y EXCEL-3e) y un CLIENTE-1c a medio hacer. Con eso la suite tiene
un rojo conocido más, `test_guardar1.py::test_datos_largos_de_la_operacion_no_impiden_guardarla`:
es de la Dev técnica y lo cierra ella en CLIENTE-1c. También 11 que chocan
con el tope de 15 operaciones del plan en la suite entera (402 «Alcanzaste el
límite…», en `test_clientes_plan02/04`, `test_maria4_despachante`,
`test_op_code_and_fill_if_empty`, `test_operations_manual` y
`test_prelaunch_block1`); la CI los corre y da rojo. Los trae la rama técnica
y los cierra ella. No los persigas; si te da otro rojo nuevo al traer mi
rama, ése sí me lo decís.

## Veredicto de SUFIJOS-1 (2026-10-27): con devolución

Sobre `97cd2fa` (base `adfe707`). Detalle y salidas en
`REPRODUCCION-SUFIJOS-1-2026-10-27.md`. Corrí tus pruebas (`50 passed`), tu
sabotaje (34 en rojo, rc=0), la suite desde base limpia (los 12 rojos
conocidos, ninguno nuevo), negativos míos contra el generador y el mismo
pedido sin sufijo propio en las dos bases: el TXT sale idéntico byte a byte
en siete casos. Mi adversario fue Opus, alto.

- **Bien:** D22 (a) con la tabla local y la fecha del arancel, el
  generador (sufijo propio, grupo, errores explícitos) y el endpoint (sesión,
  tope, saneo de la marca).
- **Devolución — lo que viaja no es lo que se ve.** Causa: el sufijo y la
  unidad estadística que se mandan por producto (`sufijoDe`, `unidadesDe`)
  salen de un estado guardado (`it.sufijo`, la propuesta pedida al generar),
  no de lo que la celda muestra en ese momento. Regla de la familia: **al
  generar, lo que va al TXT por producto es lo que muestra su celda.**
  - **H1** (de plata): si el arancel no contesta al entrar, las celdas
    quedan vacías y sin nota, y «Generar» vuelve a pedir y manda la
    propuesta y la unidad en kilos sin pintarlas (`QSBTUNTEST=465.00` en
    vez de 750 unidades). Igual con más de 500 productos (400 sin aviso).
    Si no hay propuesta en pantalla, no se agrega al generar; la celda y
    los avisos dicen que el arancel no contestó.
  - **H2** (de plata): una celda tocada guarda el texto entero, con el
    sufijo de la operación de ese momento; si después cambia el de la
    operación, esa fila sale con CA00 y las otras con CA01, sin aviso. Lo
    propio de la celda tiene que seguir al de la operación, o la fila avisa.
  - **H3:** un sufijo escrito antes de agrupar traba el TXT (400 «Grupo
    g1…») y la celda del grupo no deja corregirlo.
  - **H4:** un sufijo que ya no se ve (el producto pasó a sub-ítems) sigue
    viajando y el servidor lo rechaza.
  - Caso y sabotaje por cada uno, con ejemplos de la familia que no sean
    estos (al aceptar pruebo otros).
- **H5, decidido por la PM:** lo que el despachante escribió en el sufijo
  de la operación gana. La propuesta del arancel sólo agrega los códigos
  que faltan; si propone otro valor para un AA, AB o AI que ya está
  escrito, no lo pisa y lo avisa en la fila. Hoy `combinar` reemplaza
  «AA(1)-CA00-» por «AA(Marca Demo)-CA00-…» sin aviso; eso contradice «lo
  que escribe la persona va tal cual».
- **D23: (c)**, como recomendaste, en esta misma vuelta: no frena, avisa
  junto al botón con tu texto. Con caso y sabotaje.
- **Se anota, no lo arregles:** `combinar` con códigos repetidos o «AA00»,
  el «-» final siempre agregado, y el BOM que separa en JS y no en Python.
- **No integro todavía** tu rama: entra con la vuelta.

Puertas de la vuelta: `test_sufijos1` y `sabotaje_sufijos1.sh` en verde,
el TXT sin sufijo propio idéntico al de `adfe707`, suite completa sobre el
SHA, y mi diff de revisión va desde `97cd2fa`. Después, SEPARADORES-1c.

## SEPARADORES-1c (después de la vuelta de SUFIJOS-1)

Chica, de plata. Si ya la empezaste, guardala en tu rama y hacé primero la
vuelta de arriba. Los hallazgos están en la
reproducción (H1 a H3).

1. **Factura: una lectura de miles exige grupos bien formados** (la cabeza
   de una a tres cifras, sin cero adelante, y cada grupo de tres). Si un
   monto sólo se puede leer como miles con grupos mal formados, queda sin
   leer, con el aviso de hoy. Hoy salen por mil: «0500.000» y «01500.000»
   con la pista «,»; «01,500» con «.»; «4500.000.000» y «4500.000,00» con
   cualquier pista. Siguen como hoy: «0500.000» con «.» (500), «01,500» con
   «,» (1,5), «0,500» (0,5) y todo lo que SEPARADORES-1b dejó como guarda.
   La pantalla aplica la misma regla: «01234.500» pregunta.
2. **Lo que la pantalla no lee nunca llega al TXT como blanco.** Hoy
   `trim()` de JS no saca `\x85` ni `\x1c`-`\x1f` y `strip()` de Python sí:
   `leer` da error, `montoDelPedido` manda el texto, `importe_valido` lo deja
   en blanco y el TXT sale con `MDDTFLE=0.00`. La causa es que la pantalla y
   el servidor no usan la misma idea de «en blanco»; elegí vos de qué lado
   se arregla. El campo vacío o con espacios comunes sigue siendo 0.
3. **La pregunta no sugiere una forma que el sistema lea distinto.** Para
   «2500.125» hoy propone «2.500,125», que se acepta y el TXT redondea a
   2500.13 sin aviso; para «4500.000» propone «4.500,000»; con «-1234.500»
   pierde el signo. Las dos lecturas se escriben con `escribir()`, como en
   la rama de la coma («¿1.500 o 1,5?»).

**Pruebas:** por cada punto, al menos dos ejemplos de la familia que no sean
los de acá, de los dos lados donde aplique; las guardas de arriba; un
sabotaje por punto que vuelva a la lectura de hoy. Suite completa sobre el
SHA que entregás.

**No se toca:** lo que la factura deja sin leer termina en flete 0 con el
aviso no bloqueante (MARIA-1c); «1.234,567» se sigue aceptando; por API, el
campo en blanco sigue siendo 0; `pais_origen` desconocido va a M9.

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

## Respuestas a tus D

MARIA-7, 2026-10-24:

- **D1: (a).** Le pregunto al despachante el largo máximo y si el MARIA
  rechaza un IDSO repetido (los choques de la tabla de la reproducción). No
  cambies `NDDTIMMTRN` ni `IEXT` sin esa respuesta.
- **D2: (b)**, devolución punto 2.
- **D3: (a).** El archivo aceptado trae «S.A.», comas y paréntesis.
- **D4: (a).** El «mandala igual» es propuesta, si aparece un proveedor que
  lo necesite. Las palabras de cuenta, devolución punto 3.
- **D5: (a).** La (c), validar la fecha en el alta, la paso a la cola de la
  Dev técnica.
- **D6: (b)**, devolución punto 5.
- **D7: (a)** mientras pregunto al despachante cómo va un decimal en un
  sufijo y si acepta un valor vacío.
- **D8: (a).** La v1 no es la pantalla en uso; queda con el aviso.

SEPARADORES-1 y 1b, 2026-10-25: **D19 (b)**, **D20 (a)**, **D21 (b)**
(SEPARADORES-1c). SUFIJOS-1: **D22 (a)**, **D23 (c)**. Todas decididas por
la PM (`DECISIONS.md`).
