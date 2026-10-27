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

## Al traer mi rama (2026-10-27)

Mi rama ya trae CLIENTE-1c y ESTUDIO-1b de la Dev técnica, aceptadas hoy:
con eso se cierran los 12 rojos conocidos (11 del tope de 15 operaciones y
`test_guardar1`). El único rojo esperable es el de tiempo de `test_excel2`
en un contenedor cargado (`NOW.md`). Cualquier otro rojo al traer mi rama,
decímelo.

## Veredicto (2026-10-27): SUFIJOS-1 y SEPARADORES-1c aceptadas

Las dos sobre `45a3ea1` (informes en `76570de` y `91be665`). Suite sobre
`45a3ea1`: sólo los 12 rojos conocidos (esa base no trae `2ff3262`); sobre
mi merge de tu rama (`e9981e5`): 3393 passed, 0 rojos. Integré tu rama.
SEPARADORES-1d arranca desde tu `91be665` (o desde mi rama, igual). Detalle y salidas en `REPRODUCCION-SUFIJOS-1-vuelta-2026-10-27.md`
y `REPRODUCCION-SEPARADORES-1c-2026-10-27.md`.

- **SUFIJOS-1:** tus 47 sabotajes en rojo por la razón esperada y nueve casos
  míos en Chromium con fallas del arancel, códigos y casos distintos de los
  tuyos (500, `{}`, `items` que no es lista, no JSON, H5 con AI, H2 con AB):
  lo que viaja es lo que muestra la celda. El sabotaje 47 queda.
- **SEPARADORES-1c:** tus 10 sabotajes en rojo por la razón esperada, y negativos míos de los tres
  puntos: la factura, el blanco en el servidor y cada forma que propone la
  pregunta vuelta a leer con `leer`.
- **Se anota, no lo arregles:** con el arancel contestando 200 y `{}`, las
  celdas quedan sin nota ni aviso (no viaja nada).
- **El rojo de `test_excel2`** es el conocido de tiempo en esta máquina
  (`NOW.md`), no tuyo.
- **D24: (a). D25: (b).** Decididas por la PM; van en SEPARADORES-1d, abajo.

## SEPARADORES-1d — tarea activa

Chica, de plata. Diff de revisión desde `91be665`.

1. **D24: la regla de miles de 1c también en `_numero_factura`** (cantidad,
   valor unitario y pesos). Un número que sólo se puede leer como miles con
   grupos mal formados queda sin leer, vacío, como hoy «12x3», y la
   revisión lo marca como hoy. Lo bien formado se lee igual que hoy.
2. **D25: aviso no bloqueante cuando un importe que va al TXT con dos
   decimales tiene más.** Flete y seguro, en la pantalla, junto a los otros
   avisos no bloqueantes: qué escribió y qué lleva el TXT (por ejemplo
   «2500,1250» → «El TXT lleva 2500,13»). No cambia lo que se lee ni lo que
   sale en el TXT; «1.234,567» se sigue aceptando.

**Pruebas:** por cada punto, al menos dos ejemplos de la familia que no
sean los de acá; las guardas (lo bien formado no cambia; con dos decimales
o menos no hay aviso); un sabotaje por punto que vuelva a lo de hoy. Suite
completa sobre el SHA que entregás.

**No se toca:** lo que sale en el TXT para números bien formados; el
redondeo; lo que 1c dejó como guarda.

**Apenas entregues:** DESTINO-1 y PESO-NETO-1 esperan datos del despachante
(la lista de códigos y el packing list); te aviso cuando lleguen. Si no
llegaron, la siguiente te la dejo acá al darte el veredicto de 1d.

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

SEPARADORES-1c, 2026-10-27: **D24 (a)**, **D25 (b)** (SEPARADORES-1d).
Decididas por la PM.
