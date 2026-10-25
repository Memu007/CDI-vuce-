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

Arrancá ya. El veredicto de SEPARADORES-1b viene en un rato, arriba de
esto; si trae devolución, va primero.

## Veredicto de SEPARADORES-1 y VALOR-1c (2026-10-25): aceptadas

Sobre `a099655` (informe `4548644`; tu merge `d4a3f08` es sólo de
`docs/pm`). Integradas con `merge` a la rama de la PM. Detalle en
`REPRODUCCION-SEPARADORES-1-VALOR-1c-2026-10-25.md`. Yo corrí tus pruebas
(`301 passed`), tus dos sabotajes sobre `a099655` (26 y 17 en rojo, `rc=0`),
la suite completa y un negativo propio sobre `montos_ar.js` (200.000 montos,
ninguno mal). Un adversario Opus alto: TXT idéntico byte a byte en 56
pedidos salvo lo pedido, ningún 500 nuevo en 333, la marca del seguro y D19
probadas en el navegador.

Bien que avisaras los dos rojos de `d0bfebc` y los arreglaras en un commit
aparte: eran pruebas viejas que afirmaban lo que la tarea cambia.

## Tu tarea: SEPARADORES-1b

Chica. Las dos cosas son de plata.

1. **D19 (b).** `montoDelPedido` en `finalize.js` no manda 0 cuando no
   puede leer el monto: manda el texto tal cual y el servidor lo rechaza
   con un mensaje claro (no un 500, no un 422 crudo). Hoy la pantalla no
   llega a generar con un monto ilegible; esto es la segunda red, por si
   alguien llega por otro camino.
2. **La causa del H1 y el H2: un separador seguido de exactamente tres
   dígitos al final, cuando lo de adelante no es un grupo de miles bien
   formado, se lee sin preguntar.** En la factura, `_monto_factura` con la
   pista decimal en contra da «3480.000» → 3480000 y «3480,000» → 3480000.
   En la pantalla, `montos_ar.js` toma «1234.567» y «1234,567» como
   1234,567. Esa familia pasa a ser ambigua: en la factura queda sin leer
   (con el aviso de hoy) y en la pantalla se pregunta, como «1,500».
   **No toques `_numero_factura`** (precios y cantidades: ahí tres decimales
   son normales).

Lo que no cambia: «3.480», «3.480,00», «1.234.567», «1,234.56», «3,48»,
«0,500», «01,500» (con el cero adelante no puede ser miles) y
«1.234,567» (no es ambiguo) siguen como hoy.

**Pruebas:** un caso por cada punto y por cada lado (factura y pantalla),
con al menos dos ejemplos de la familia que no sean los de acá; los que no
cambian, como guarda; un sabotaje por punto que vuelva a la lectura de hoy.
Suite completa sobre el SHA que entregás.

**Riesgos que quedan anotados, no se tocan:** lo que la factura deja sin
leer sigue terminando en flete 0 con el aviso no bloqueante (diseño de
MARIA-1c; SEPARADORES-1 manda más casos ahí); `pais_origen` desconocido
sale `CARTPAYORI=310` sin aviso (va a M9).

**Apenas entregues:** SUFIJOS-1 (`ROADMAP.md`, Fase 1c, orden 1). En las
pruebas, VUCE siempre simulado (`VUCE_MODE=fake`): ninguna llamada real a
VUCE ni a terceros. Si para leer la forma de la respuesta te hace falta la
consulta real, es una D: no la hagas vos.

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
