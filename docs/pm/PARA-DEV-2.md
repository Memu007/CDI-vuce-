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

## Veredicto de MARIA-7 y MARIA-8 (2026-10-25): aceptadas con nota

Sobre `30ceace` (informe `f71eaa9`; el producto es igual en `536c679` y en
`f71eaa9`). Integradas con `merge` a la rama de la PM (`1fa0b6e`); el
producto es idéntico al revisado. Detalle en
`REPRODUCCION-MARIA-7-8-2026-10-25.md`. Mi adversario (Sonnet, alto):
- suite `2046 passed, 102 skipped, 2 xfailed`, cero rojos;
- tus sabotajes, 13/13, 38/38 y 25/25 en rojo;
- smoke y e2e OK;
- un fuzz de 5000 ítems con renglones unidos, donde FOB, cantidades y
  kilos cierran exactos.

`test_excel2` no reprodujo: pasó en 23–24 s contra el tope de 30. Es de
entorno, como dijiste.

Lo que queda va a **MARIA-9** (abajo), antes de SEPARADORES-1 y antes de
que esto se publique.

## Respuestas a tus D9–D11 (MARIA-7/8)

- **D9: (a).** El texto libre no genera. Tu ejemplo de mi herramienta es
  mío: ya estaba rota antes (le falta el CUIT del despachante y pide EC02).
  La arreglo yo; vos no la tocás.
- **D10: (a).** Palabra entera. La regresión que trae (nombres pegados de
  menos de 16 dígitos, como `CITIBANK 123456789`) queda como riesgo
  anotado.
- **D11: (b)**, en MARIA-9. Mi adversario encontró más que la falta de
  aviso: hay una regresión.

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

## Ahora — VALOR-1 (seguí), después MARIA-9, después SEPARADORES-1

### MARIA-9: el sufijo de la operación y sus errores en pantalla

Es lo que dejó la revisión de MARIA-7/8. Cada punto con su sintético y su
sabotaje.

1. **Un sufijo general que no se usa frena el TXT (regresión).** Si todos
   los sub-ítems o renglones traen su sufijo propio válido y
   `sbt_sufijo_valor` es texto libre («ROJO»), en `284b029` se generaba con
   los propios; hoy `/generate_maria` da 400 («Sufijo de valor de la
   operación: «ROJO» no se puede separar…»). Además,
   `/generate_maria/avisos` responde 200 sin anticiparlo.
   - **Causa:** el general se analiza aunque no se use.
   - **Qué:** se valida sólo si algún sub-ítem o renglón lo toma; cuando
     lo toma y es inválido, `/avisos` lo anticipa.
   - **Familia:** sub-ítems a mano, renglones por API, mezcla de ítems con y
     sin propio.
2. **La pantalla v2 no lleva los errores de sufijo a su lugar.**
   - **Causa:** `static/v2/screens/finalize.js:401` sólo reconoce
     `^Item N, sub-ítem M: ` y `:410` sólo los que dicen «sbt». Los mensajes
     nuevos («Sufijo de valor de la operación: …», «Sufijo de valor del
     ítem N, sub-ítem M: …», «…del renglón N…») caen como texto genérico.
   - **Qué:** cada uno se muestra donde se corrige: bajo el campo del
     sufijo de la operación o en el sub-ítem.
   - **Prueba:** de pantalla, con el error forzado (`page.route`).
3. **Bordes sin prueba.** Mutaciones de mi adversario que siguen en verde,
   cada una con su caso y su sabotaje:
   - el tope de 120 (120 pasa, 121 no);
   - `CA100-`;
   - `A(X)-`;
   - `;` como separador;
   - las unidades numéricas del aviso (`05`, `99`).
4. **Mensaje engañoso:** con dos renglones de la misma posición en kilos y
   uno solo de 0,004 kg, el error dice «los renglones 1 y 2 son tan chicos…»
   (`maria_generator.py` ~1304). Tiene que nombrar sólo el chico.

**Riesgos que no arreglás (anotalos si los tocás):**
- doble redondeo de kilos (`.3f` y después el centésimo: `465.1249` sale
  `465.13`);
- `cantidad=2.675` sale `2.67` sola y `2.68` como renglón de un ítem unido.

Van a M9 cuando Emi ordene los hallazgos de Argon (9.2 es la misma
familia).

### VALOR-1 y SEPARADORES-1

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
