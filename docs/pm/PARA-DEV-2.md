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

## Respuestas a tus D

(Ninguna todavía.)
