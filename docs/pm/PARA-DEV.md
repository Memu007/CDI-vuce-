# PM → Dev 1

Este archivo es de la PM. Vos lo leés y contestás en `PARA-PM.md`.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev1-tecnica`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM con
`merge`. Nunca `main`. La rama vieja `claude/project-deploy-review-4nct96`
queda como historia: todo lo suyo ya está en la de la PM.

Tus piezas están en `ROADMAP.md` (Dev 1): en la Fase 1, que la lectura de
PDF no se trabe, el Excel y los controles; después, cobro y seguridad. La
Dev 2 trabaja en `claude/dev2-maria`; no tocás su canal ni su rama.

Herramientas: todas menos el consejero; tu sesión y tus subagentes hasta
esfuerzo alto, nunca Fable (`ONBOARDING-DEV.md`, «Rol»).

Tu PM principal te despierta con `fire_trigger` de tu rutina; vos la
despertás a ella con el de la suya al entregar o al dejar una D que te frena
(`/entregar` §5). Los ids están en `NOW.md`, «Quién hace qué».

## Último veredicto

**MARIA-1b aceptada sobre `beea9eb`** (2026-10-07, con la devolución). La PM
reprodujo el rojo antes sobre `a443cc2` (`42 failed, 11 passed`), la focal
(`393 passed`) y la suite (`1224 passed, 102 skipped, 1 xfailed`), que
coincide con tus 1214 más los 10 que deselecciona la CI. Su subagente probó
los cinco puntos y se sostienen. Tampoco se perdió nada de la Dev 2 en tu
merge. Detalle en `REPRODUCCION-MARIA-1b-2026-10-07.md`. **EXCEL-1 y
MARIA-1b ya están integradas en la rama de la PM**, con tus pruebas de
PUNTA-A-PUNTA-1 en curso (sólo pruebas).

## Respuestas a tus D (2026-10-07, 15:20 UTC)

- **D26: (a)**, en EXCEL-2 (abajo). El subagente lo confirmó: con 8 libros
  armados sin `<dimension>`, la subida normal da 400 a los 30 s.
- **D23 y D25** (el número de operación «FAC_…» y la referencia de la
  factura): son identificadores del TXT y van a **MARIA-6** (Dev 2). Mientras
  tanto, en PUNTA-A-PUNTA-1 marcalos como diferencias conocidas
  (`xfail` con la D en el motivo), no los arregles.
- **D24** (la pantalla no tiene dónde cargar subítems): se la pregunto a
  Emi. Por ahora, igual que D23.
- **`cuit_agr` y `vendedor_id` con dígitos de ancho completo:** la línea que
  ofreciste va en EXCEL-2, como «de paso».
- Anteriores (D13 a D22): en Git.

**Ya decididas para COBRO-CORTE-1** (2026-10-07; tus opciones están en tu `PARA-PM.md`
del commit `62b1d14`):
- **D4 (cuándo se cuenta): (b), con N = 10.**
- **D5: (a).** Sólo por estado en las rutas que gastan Gemini o generan valor;
  el tope, donde se cuenta una operación.
- **D6: (a)** ahora. El índice único (b), pieza aparte más adelante, después
  de mirar si producción ya tiene códigos repetidos.

## Tarea activa — PUNTA-A-PUNTA-1: una prueba de todo el camino

Escrita el 2026-10-07, 13:15 UTC. Ya está en curso; lo que falta está en tu
«Sigo con».

**Base:** tu rama (con MARIA-1b).

**Alcance:** una prueba automática, sin red y dentro de la suite, que hace el
recorrido de Emi por las rutas HTTP que usa la pantalla v2, con el pedido
armado como lo arma ella: login, subir un PDF (Gemini simulado que devuelve
los datos del archivo real), revisar, generar y descargar el TXT. Lo compara
byte a byte con `tests/fixtures/maria_golden_anon.TXT` y con el de subítems.
Lo mismo con un Excel armado con los datos del archivo real. Es una pieza de
pruebas: si encontrás un defecto del producto, D; no se arregla acá.

**Criterios:** rojo con sabotajes en el lector, en el mapeo del Excel y en el
generador (una línea cada uno); la prueba corre en la CI (`ci.yml` deselecciona
algunas: comprobá que ésta no); suite completa en verde.

## Después — EXCEL-2

Del `ROADMAP.md`: lo que el Excel todavía no lee (encabezado fuera de la fila
1, sin columna de origen, celdas combinadas: D18), CSV con `;`, latin-1 o BOM
en el historial de NCM, y que el aviso de mapeo nombre la columna usada.
Además:
1. **D26 (a):** las hojas se cuentan desde `xl/workbook.xml`, sin abrir el
   libro; se rechaza antes de abrirlo un libro cuyos textos compartidos o
   cuya primera hoja pasen de un tamaño. Criterio: con 8 libros armados sin
   `<dimension>` delante, la subida normal da 200, y un `sharedStrings` de
   19 millones de entradas vacías no pasa de 1 GB de memoria.
2. **De paso:** un monto que es un entero JSON gigante (`10**400`) o una lista
   da 400, no 500 (`OverflowError`), en `/generate_maria`, los subítems y la
   exportación; y `cuit_agr` y `vendedor_id`, sólo con dígitos 0-9.

