# PM → Dev técnica (Dev 1)

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`. La
historia de este canal está en Git.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev-tecnica`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM
con `merge`. Nunca `main`. Las ramas viejas `claude/dev1-tecnica` y
`codex/*` son historia: lo aceptado ya está en la de la PM.

Sos la Dev técnica: lectura de Excel y PDF, clientes y estudio, cobro y
seguridad. La Dev MARIA trabaja en `claude/dev-maria` (el TXT); no tocás su
canal ni su rama, ni `maria_generator.py`.

Esfuerzo medio (Emi, 2026-10-24). Herramientas: todas menos el consejero;
tus subagentes hasta alto, nunca Fable.

**Timbres:** al entregar o al dejar una D que te frena, despertás a la PM
principal con `send_message` (sesión en `NOW.md`, «Quién hace qué»),
`priority` `next`, empezando con «Dev técnica:». Ella te despierta igual.

**Datos reales:** la proforma de la reunión del 2026-10-24 tiene datos de
un cliente: no entra al repositorio. Las pruebas usan sintéticos.

## Tarea 1 — EXCEL-3: la proforma china tal como viene

El 24/10 Emi subió una proforma `.xls` de un proveedor chino y CDI respondió
«No se pudieron extraer items». Forma (sintetizala igual, con datos
inventados):

- Filas 1 a 9: nombre del proveedor, «Proforma Invoice», comprador, CUIT,
  fecha, número de P/I, «Freight term: CNF Buenos Aires».
- Fila 11, encabezado: `Item | Part No. | Specification | Width(m) |
  Length (m) | SQ.MT. (sqm) | QTY (Rolls) | SM.TOTAL (sqm) |
  Unit price (USD/sqm) | Total Amount(USD) | Gross Weight(kgs) | Volume(CBM)`.
- 48 renglones; `Part No.` y `Specification` sólo en el primero de cada
  grupo (vale para los de abajo hasta el siguiente); cada grupo es un color
  y un ancho, cada renglón un largo distinto.
- Al final: `Total`, `Discount` (negativo), `Freight cost …` (con cantidad
  1) y otro `Total`; después texto (pago, banco, cuenta).

Qué tiene que pasar:
1. Encuentra el encabezado aunque no esté en la fila 1 (EXCEL-2 ya buscaba
   algo de esto: partí de ahí).
2. La descripción del grupo se arrastra a sus renglones; cada renglón sale
   como producto propio, con ancho y largo en la descripción.
3. La cantidad es la de la unidad del precio: el precio es por m², así que
   la cantidad es `SM.TOTAL (sqm)`, no los rollos; la unidad (m²) viaja con
   el producto.
4. `Gross Weight(kgs)` es bruto de toda la línea (regla de pesos vigente).
5. `Total`, `Discount` y `Freight` no son productos: el flete y el
   descuento se ofrecen en la operación (el descuento, como ajuste; lo
   resuelve VALOR-1 de la Dev MARIA: vos sólo los devolvés leídos).
6. Una columna `Item` con texto («1st container») no es un código.

**Puertas:** rojo antes con el sintético; suite completa; e2e de la CI.

## Tarea 2 (apenas entregues) — CLIENTE-1, después ESTUDIO-1 y PA-1

Están en `ROADMAP.md`, Fase 1b. ESTUDIO-1 toca qué va al `CDDTAGR`:
coordiná por la PM con la Dev MARIA (MARIA-7 punto 3), no por su canal.

## Respuestas a tus D

(Ninguna todavía.)
