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

## Veredicto de MARIA-7 (2026-10-24): con devolución

Sobre `f0b73f7` (informe `284b029`). Detalle en
`REPRODUCCION-MARIA-7-2026-10-24.md`. Los nueve puntos están y tus pruebas
distinguen (11 sabotajes de mi adversario, todos en rojo). No la integro
todavía: va primero esta devolución, después MARIA-8. Cada punto, con rojo
antes en un sintético y un sabotaje que lo vuelva a romper.

1. **Dos sufijos sin guion entre ellos se funden.** Causa: `limpiar_sufijo`
   toma el valor con `\((.*?)\)(?=-|$)`, que termina recién en un `)`
   seguido de guion o del final. `AA(ROJO) AB(AZUL)-CA00-` sale
   `AA(ROJO  AB AZUL)-CA00-`: AB se pierde y AA queda con un valor falso.
   **Qué:** cada sufijo conserva su código y su propio valor; entre sufijo
   y sufijo va el `-` (como en el archivo aceptado, arriba). Si un sufijo no
   se puede delimitar (paréntesis sin cerrar, un `(` dentro del valor), no
   se genera: error que diga qué producto y qué sufijo. **Por la familia:**
   espacio entre sufijos, nada entre sufijos, coma, dos guiones, paréntesis
   dentro del valor, paréntesis sin cerrar; en `[SBT]` y en el sufijo del
   ítem.
2. **D2: (b), por evidencia.** En el archivo que el MARIA aceptó el kilo
   neto está al centésimo con tres decimales (el tercero en 0) e igual a la
   cantidad estadística; la versión rechazada justo antes los tenía
   distintos en el milésimo. Con la estadística en kilos, `QARTKGRNET` sale
   al centésimo (`465.130`) y `QARTUNTEST` igual (`465.13`). Prueba con un
   kilo neto de milésimo 5 (el caso de medio centavo) y corré el sabotaje
   del redondeo (`ROUND_HALF_EVEN`) con un patrón que aparezca una sola vez.
3. **Palabras de cuenta dentro de otras palabras.** Causa:
   `_PALABRAS_DE_CUENTA` busca `BIC\b`, `IBAN`, `BANK`… sin borde adelante:
   «ARABIC TRADING 123» se toma por cuenta y la tributaria no sale. **Qué:**
   palabras enteras. **Familia:** una palabra que contenga cada una de las
   de la lista, y las mismas solas, que siguen siendo cuenta.
4. **El control de grupo compara la unidad estadística cruda** (`1`, `01`,
   `kg` son la misma y dan error). Comparar por código, con
   `get_unidad_codigo` o el equivalente de estadística.
5. **D6 entra acá (decidido por la PM):** una unidad que no se reconoce no
   sale 07 en silencio: aviso con la unidad leída, como el de «Unidad de
   medida». Es la misma familia del punto 5 (m² salía 07). No cambies el
   código que sale: sólo el aviso.

**Queda como está (decidido por la PM):** el PDF no trae la unidad; el
usuario la elige en el panel del despachante y ya sale el aviso. Leerla del
PDF va al roadmap cuando haya un PDF real que la necesite. El mensaje de
kilos con sub-ítems lo resolvés en MARIA-8.

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

## Tarea 1 — MARIA-7: lo que el MARIA rechazó el 24/10

En `proyecto_maria/core/maria_generator.py` y lo que lo alimenta:

1. **CRLF en todas las líneas**, también las que se reescriben después de
   armar el texto. Prueba: ninguna línea del TXT termina sin `\r`.
2. **Identificador corto.** `IDSO`, `IDDT` y la raíz de `IARTESPAPU` no se
   arman con el número de factura completo. Averiguá en el código y en
   `docs/` el largo máximo; si no está, usá 8 caracteres (lo que el MARIA
   aceptó) y anotalo como D para el despachante. El número completo sigue en
   `NRO.REF.INTERNA`.
3. **`CDDTAGR` obligatorio:** sin CUIT del despachante no se genera; error
   claro que diga dónde cargarlo. Hoy se omite la línea en silencio.
4. **`LDVDREFDOC` es el número real de la factura**, con el ancho fijo de
   hoy.
5. **Unidades:** la declarada es la de la factura (m² → `03`, no `07`); con
   unidad estadística en kilos (`01`), `QARTUNTEST` = `QARTKGRNET` redondeado
   igual (error 2122 del MARIA). La unidad estadística por posición la
   resuelve SUFIJOS-1 más adelante; acá, que el usuario la pueda elegir y
   que kilos dé cantidad = kilo neto.
6. **Caracteres:** en sufijos y textos libres, sólo letras, números y
   espacios; lo demás se cambia por espacio y se avisa.
7. **`IDTRIB-PROVEEDOR`:** un número de cuenta bancaria no es identificación
   tributaria; si lo que hay parece cuenta (o no hay), no se inventa: aviso.
8. **Fechas año/mes/día** (Emi, 2026-10-24): una fecha escrita `2026/08/07`
   en la factura es el 7 de agosto de 2026 y en el TXT sale `07/08/2026`; el
   24/10 salió `08/07/2026`. Con el año adelante, el orden es siempre
   año/mes/día. Si el orden no se puede saber (año al final y día y mes
   ambos de 12 o menos), se le pregunta al usuario; no se adivina. Prueba:
   sintéticos con `2026/08/07`, `2026-08-07`, `07/08/2026` y uno ambiguo.
9. **Fecha de inicio de actividad** (sumado por la PM el 2026-10-24, al
   revisar CLIENTE-1). El alta del cliente la guarda `AAAA-MM-DD` (campo de
   fecha del navegador) y el generador la copia tal cual al `MCPL` de
   `FECHA INIC.ACTIV` (`maria_generator.py`, bloque 6). Los dos golden
   tienen `DD/MM/AAAA`. Sale `DD/MM/AAAA`; si ya viene así, igual; si no se
   puede leer como fecha, error claro que diga dónde corregirla (no se
   adivina). Prueba: `2015-03-01`, `01/03/2015` y un texto que no es fecha.

**No se toca:** el valor de la fecha de emisión (Emi: «no se corrige»): el
punto 8 la lee bien, no la cambia.

**Puertas:** rojo antes con un sintético que reproduzca cada punto; los dos
golden siguen idénticos salvo lo que esta tarea cambia a propósito (decí
qué y por qué); suite completa; e2e de la CI (`ONBOARDING-DEV.md`).

## Tarea 2 (apenas entregues) — MARIA-8: subítems por posición

Cada renglón de la factura es un subítem con su FOB, cantidad, precio,
kilos y sufijos propios. Los renglones con la misma posición SIM, origen,
procedencia y estado van en un solo ítem (`CARTSBITEM=S`). Las sumas del
ítem (FOB, cantidad, kilos, cantidad estadística) cierran exactas al
centavo; el redondeo sobrante va al subítem más grande. Prueba: un sintético
de un ítem con al menos 12 subítems de dos anchos y tres colores, y otro con
dos posiciones distintas (dos ítems).

## Tarea 3 — VALOR-1, y 4 — SEPARADORES-1

Están en `ROADMAP.md`, Fase 1b. Antes de arrancarlas, leé la decisión del
2026-10-24 en `DECISIONS.md`: el reparto ítem por ítem de los ajustes queda
para PRORRATEO-1.

**Qué te deja EXCEL-3 para VALOR-1** (aceptada el 2026-10-24, en la rama de
la PM): la lectura del Excel devuelve `operacion.flete` (el de siempre),
`operacion.descuento` (nuevo, **positivo**: lo que la factura dice que se
deduce) y `operacion.filas_excel_flete` / `filas_excel_descuento` (filas de
la planilla). Hoy el descuento sólo se informa: no resta del FOB. VALOR-1
lo ofrece como ajuste a deducir y el usuario decide. Si necesitás otro
nombre o signo, pedilo por tu canal.

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
