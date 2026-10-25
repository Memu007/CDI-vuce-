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

## Veredicto de SEPARADORES-1b (2026-10-25): aceptada

Sobre `db39de0` (informe `8974daf`). Integrada con `merge` a la rama de la
PM, sin publicar. Detalle en `REPRODUCCION-SEPARADORES-1b-2026-10-25.md`.
Yo corrí tus pruebas (`295 passed`), tu sabotaje sobre `db39de0` (los 12 en
rojo, `rc=0`), la suite completa y dos negativos propios: 71 pedidos raros
contra las dos rutas (ningún 500; « 12.50 » como texto da el mismo TXT que
12.5) y `leer` sobre la familia nueva. Un adversario Opus alto: con número
JSON el TXT es idéntico al de la base; las 72 diferencias de `leer` en 1157
entradas pasan de leerse a preguntarse, ninguna cambia de magnitud.

Tu sabotaje usa por defecto tu venv (`/tmp/cdi-dev2/venv`); en otra máquina
sale con `rc=127` si no se le pasa el venv como segundo argumento. Para la
próxima, que lo diga el encabezado del script.

**Me equivoqué en la tarea:** «01,500» con la pista «.» sí se puede leer como
miles (da 1500). Bien que lo marcaras en D21.

## D20 y D21

- **D20: (a)**, como recomendaste. Con el seguro calculado, un ajuste que no
  se lee frena el TXT hasta que se corrija o se elija «Dejar el seguro como
  está».
- **D21: (b)**, pieza aparte: SEPARADORES-1c, abajo.

Las dos decididas por la PM (`DECISIONS.md`).

## D22 (SUFIJOS-1, 2026-10-25): (a), ARCA en el producto

Verifiqué tu premisa: en el repositorio no hay ruta `/cice/sufijos` ni una
respuesta guardada; `vuce_connector.py` sólo trae datos de NCM. Escribir
el lector de VUCE hoy sería inventar la forma. Decidido por la PM (se lo
cuento a Emi; se puede revertir):

- **Fuente: el arancel de ARCA** (`docs/pm/datos/arancel_ARCA_07102026.zip`),
  una tabla local armada con un script desde el zip, que comprueba el
  SHA-256 del `LEEME.md` antes de leer. Sin red, sin terceros.
- **La fecha de la foto viaja con el dato:** donde el sistema completa un
  sufijo o la unidad estadística, la pantalla dice que sale del arancel de
  ARCA del 07/10/2026. Si la posición no está en la tabla, nada se completa:
  se marca para el despachante, con aviso (el «sin VUCE, a mano» del
  roadmap).
- **VUCE queda para una pieza aparte**, cuando haya una respuesta real
  guardada (se la pido a Emi). En esta pieza no dejes lugar ni simulado de
  VUCE: no hay nada que probar con él.
- **El TXT:** lo que cambie en `CSBTSVL` o `CARTUNTEST` lleva su prueba (el
  caso del 24/10, en sintético: capítulo 39 pide AA y AI; `3920.10.10.100F`
  lleva `01`). Lo demás de la pieza (completar con lo que lee la IA, `AI`
  distinto por renglón, marcar lo que falta) sigue como en el roadmap.
- Antes de escribir el script, mirá `scripts/import_arancel_nomenclador.py`
  (CATALOGO-NCM-1): si ya lee el zip, reusalo, siempre con el zip del
  repositorio (`--archive`), sin bajar nada.

Seguís con SUFIJOS-1; el veredicto de arriba no trae devolución.

## Después de SUFIJOS-1: SEPARADORES-1c

Chica, de plata. Va apenas entregues SUFIJOS-1. Los hallazgos están en la
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

SEPARADORES-1, 2026-10-25:

- **D19: (b)**, como recomendaste, en SEPARADORES-1b punto 1 (decidido por
  la PM; `DECISIONS.md`).

SEPARADORES-1b, 2026-10-25:

- **D20: (a).** **D21: (b)**, SEPARADORES-1c (decididas por la PM;
  `DECISIONS.md`).
