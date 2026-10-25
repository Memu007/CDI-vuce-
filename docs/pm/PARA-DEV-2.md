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

## Veredicto de VALOR-1b y MARIA-9 (2026-10-25): aceptadas con nota

Sobre `efa2e08` (informe `8f529d5`; el producto es igual en los dos).
Integradas con `merge` a la rama de la PM (`9f787f6`). Detalle en
`REPRODUCCION-VALOR-1b-MARIA-9-2026-10-25.md`. Yo corrí tus pruebas
(`213 passed`) y tus tres sabotajes (23, 31 y 30 en rojo, `rc=0`). Dos
adversarios (Opus alto y Sonnet alto):
- el TXT es idéntico byte a byte en 86 casos y en 27, salvo el que pedía
  MARIA-9.1;
- el botón nunca pone un seguro calculado con cuentas viejas (cuatro caminos
  en pantalla, distintos de mi ejemplo del descuento);
- `/avisos` anticipa el error del sufijo en 6432 de 6432;
- ningún 500 nuevo.

La familia de las cuentas viejas la seguiste hasta el final, y la firma del
pedido la cierra mejor que lo que yo pedía.

### Tus D (decidido por la PM)

- **D18: (b).** El general se escribe sólo en `CSBTSVL` y siempre pasa por
  `limpiar_sufijo`: si nadie lo usa, no se escribe y saltear sus controles
  no rompe el formato. Dos condiciones:
  - cuando alguien lo usa, los controles de `=`, caracteres de control y
    largo siguen igual en los dos endpoints;
  - cuando nadie lo usa, `/avisos` no dice nada de él. Hoy, con `AA(X=Y)`
    sin usar, avisa «sale «AA(X Y)»» y `/generate_maria` da 400.
- **D13: (b)** y **D14: (a)**, como estaban.

### VALOR-1c: lo que queda (va primero, antes de SEPARADORES-1)

Pieza chica de la fila 3 del roadmap. Cada punto con su caso y su sabotaje
en rojo.

1. **Causa: un valor que puso el sistema con cuentas que ya no son llega al
   TXT.** Generar no mira si el seguro calculado sigue valiendo
   (`finalize.js:543`). Con el seguro calculado sobre flete 100 y el flete
   cambiado a 7925 en revisión, el TXT sale con `MDDTFLE=7925.00` y
   `MDDTASS=14.88`; sólo la nota lo dice.
   - **Lo que tiene que quedar:** nadie genera con un seguro calculado sobre
     otras cuentas sin enterarse y elegir (recalcularlo o dejarlo). Cómo, lo
     decidís vos; en silencio, no.
   - **Familia:** cualquier camino que cambie el pedido después de calcular
     (revisión, restauración, otra operación, un campo de la tarjeta) y
     cualquier valor que ponga el sistema con esas cuentas, no sólo el
     seguro.
2. **D18 (b)**, con sus dos condiciones de arriba.
3. **El mensaje de kilos nombra a todos los que dan cero.** Con kilos 0,005,
   0,005, 0,005 y 0,004 en la misma posición nombra sólo el 4, y por el
   ajuste del redondeo dan cero del 1 al 4 (14 de 601 casos del fuzz de mi
   adversario).
4. **Sin ítems, un error claro en los dos endpoints.** Con `items=[]` y el
   general vacío, hoy sale 200 con un TXT sin `[ART]` (antes, 400).
5. **Pruebas que no distinguen.** Mutaciones que siguen en verde:
   - el flete sin redondear en el seguro (`maria_generator.py:934`; FOB 1000
     con flete 0,495 lo separa);
   - la firma del pedido sin los ítems (`finalize.js:251`);
   - sacar `pintarValor(null)` (`finalize.js:84`);
   - `None` en vez de `request.iva_adicional` (`main.py:4341`: un caso con
     IVAAD1 da 200 o 400);
   - en `/avisos`, `request.items` en vez de los ítems con la procedencia
     (`_supuestos_maria(request, items, gastos)`, `main.py:4212`); el de
     `/generate_maria` ya lo cubre tu sabotaje 30;
   - el número de renglón del error de kilos como índice dentro del ítem.

Corregí el CHANGELOG para que diga sólo lo que queda probado.

**Riesgos que anoto, no los arregles (anotalos si los tocás):**
- mientras la firma está vieja, lo que se ve tarda en ponerse al día
  (`finalize.js:312-317`); nunca aplica el valor viejo;
- `"1_000"` pasa; `""` sale con comillas vacías; `nan`, `inf` y `1e400` en
  un renglón no dicen qué renglón;
- de antes: flete o seguro `true` por API cuentan como 1,00; `"abc"` como
  valor unitario en `/generate_maria` da 400 con texto de Python;
  `grupo_id` como lista da 500;
- los de tu informe: el clic que sólo pide las cuentas, la firma de todo el
  pedido, `_exacto`;
- de VALOR-1: `type=number` con «3.480» (va en SEPARADORES-1), los
  cosméticos y el ajuste mal escrito restaurado sobre un campo vacío;
- de MARIA-7/8 (D10): nombres pegados a un número, como `CITIBANK 123456789`;
- doble redondeo de kilos (`.3f` y después el centésimo: `465.1249` sale
  `465.13`) y `cantidad=2.675` (`2.67` sola, `2.68` como renglón de un ítem
  unido). Van a M9 cuando Emi ordene los hallazgos de Argon.

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

## Después de VALOR-1c: SEPARADORES-1

Está en `ROADMAP.md`, Fase 1b. El reparto ítem por ítem de los ajustes
queda para PRORRATEO-1 (`DECISIONS.md`, 2026-10-24).

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
