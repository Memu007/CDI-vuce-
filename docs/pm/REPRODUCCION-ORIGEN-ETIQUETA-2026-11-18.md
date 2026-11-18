# ORIGEN-ETIQUETA (D261): `5a28c13c` (informe `e13f0ccf`), 2026-11-18, PM

**Veredicto: aceptada, integrada** (merge `fdf27eff` de `e13f0ccf` en la rama de PM). Base `04cdc9c0`.
Revisión de datos (§3): adversario Sonnet alto, `e2e_maria.sh` en el SHA. `04cdc9c0` es antecesor del
SHA y era la cabeza de la rama de PM, así que la corrida en el SHA es también la de la unión.

## Diff

`chequeo-6.py 04cdc9c0 5a28c13c`: «producto +12/−5», «arnés +89/−30», historia vacía, un AVISO:
`paises_maria.js:2 <anónima> 287 → 292, 2 en su propio cuerpo`. Es el envoltorio del módulo, el
mismo que se aceptó en PAISES-NOMBRES; `etiqueta` es una función aparte de tres líneas, como `label` y
`mostrar`. Explicación suficiente.

`git diff --stat 04cdc9c0 5a28c13c -- proyecto_maria/ ':!proyecto_maria/static/v2'` da vacío: el
servidor, lo guardado y el armado del TXT no cambian.

## Lo que corrí (worktree en el scratchpad de la PM, 23:15 a 23:22 UTC)

| Qué | SHA | Resultado |
|---|---|---|
| `test_catalogo3.py`, `test_paises_nombres.py` | `5a28c13c` | «134 passed» (salida 1 por la cobertura mínima de una corrida parcial) |
| `sabotajes/holanda423.sh` | `5a28c13c` | base «112 passed» y «OK: pantalla Holanda→423»; 24 ROJO; «sabotajes sin rojo: 0», salida 0 |
| `e2e_maria.sh` | `5a28c13c` | «E2E MARIA OK», salida 0 |
| sonda mía, node: `etiqueta` con 22 entradas | `5a28c13c` | 434, «0434», « 434 », «nl», «Holanda», «Países Bajos» → «423 · PAISES BAJOS»; «CN», « China », «310» → «310 · CHINA»; «ATLANTIDA», «-» y el HTML quedan como vinieron; blancos, `null` y vacío → «» |
| sonda mía: las 309 etiquetas de la tabla, por el servidor | `5a28c13c` | `get_pais_codigo(etiqueta(c)) == c` y `pais_de_la_tabla` verdadero en 308; 434 da 423, que es lo que ya sale para 434. `etiqueta(etiqueta(x)) === etiqueta(x)` en las 309. La más larga tiene 72 caracteres; el campo no tiene `maxlength` |

Adversario Sonnet alto (sin red, `GEMINI_API_KEY` vacía, servidor local, Playwright):
- Ningún camino lleva la etiqueta a la operación sin que la persona toque el campo. Lo probó al poblar,
  al enfocar y salir, al ir a validar y volver, y al tipear «434». El borrador serializa el estado, no
  el formulario.
- `getOriginLabel` de ncm.js da lo mismo antes y después en 201 867 entradas.
- El HTML en `origen_frecuente` y en la procedencia se ve como texto, sin diálogos.
- La tarjeta no desborda con 300 caracteres.

## Riesgos escritos (decididos por la PM)

- **Tocar el campo guarda la etiqueta.** Si la persona edita la procedencia y la deja igual, queda
  «310 · CHINA» en la operación en vez de «310». El TXT sale igual (`CARTPAYPRC=310`, reproducido por
  el adversario): `finalize.js` resuelve antes de mandar, y el servidor da el mismo código para las 309
  etiquetas. Es lo que quedó escrito en el campo, no una reescritura. Sin devolución.
- **Supuesto 1, aceptado:** «la revisión» es la procedencia, el único campo de origen de la revisión
  (`vendedor_pais` es el país del vendedor). Los catálogos siguen con «423»: ponerles la etiqueta
  sería otra pieza, y va a Emi.
- **Supuesto 2, aceptado:** lo que no es un país se muestra recortado; un origen frecuente de sólo
  blancos se ve «—». Es sólo lo que se ve.
- **Riesgo 1, aceptado sin «…»:** con el 682, la tarjeta mide 176 px de alto en un celular. El número
  es de MARIA; no lo medí. Cortarlo escondería el nombre, y hoy nada lo pide.
- La página de clientes ya medía 523 px a 390 px de ancho, con cualquier origen: viene de antes.

## No corrí

- La suite entera: el «6225 passed» es de MARIA.
- Los 28 TXT antes y después y la medida a 390 px: salen de guiones de su scratchpad. El TXT igual lo
  sostienen el diff vacío fuera de `static/v2`, la vuelta de las 309 etiquetas por el servidor y los
  sabotajes.
- `/security-review`: no toca sesión, permisos ni dinero; el adversario miró el HTML.
