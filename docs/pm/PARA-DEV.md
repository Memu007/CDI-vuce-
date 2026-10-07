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

**MARIA-1b devuelta sobre `21a7a7e`** (2026-10-07) por cuatro puntos, más la
D22. La PM reprodujo el rojo antes sobre `c0bae0e` (`27 failed, 10 passed`),
la focal (`158 passed`) y la suite (`941 passed, 102 skipped`): coincide con
tu informe. Lo central se sostiene: tu CUIT acepta 12 reales y frena 3
inválidos, el archivo real sale idéntico en 25 casos y guardar sin inventar
no rompe nada. Lo que encontró el subagente, con su reproducción, está en
`REPRODUCCION-MARIA-1b-2026-10-07.md`. EXCEL-1 sigue aceptada y entra con
MARIA-1b.

**La devolución va antes que PUNTA-A-PUNTA-1.**

1. **`NaN` e `inf` no dejan generar.** Hoy, en cantidad, valor, peso, flete,
   seguro y gastos FOB, dan 200 y el TXT sale con `nan` o `inf`
   (`QARTUNTDCL=nan`, `MDDTFLE=inf`, `MCPL=nan`), porque `nan <= 0` es falso.
   Que frenen con el mismo error que un monto inválido, y que
   `/api/validate/smart` con la cabecera no dé 500 (hoy da 500 con un `NaN`
   en un ítem).
2. **Mirar las otras hojas no puede trabar la lectura.** El tope de 10 s
   corta la espera, pero no el hilo: con 2 hilos, dos libros armados (50
   hojas con celdas de 32 000 espacios, 90 MB descomprimido) dejan cualquier
   subida en 504 durante ~3 minutos. El escaneo necesita un presupuesto que
   corte de verdad, por ejemplo saltar las hojas cuyo XML dentro del ZIP pasa
   de un tamaño, o cortar por bytes o celdas leídas. Y si no se pudo mirar
   todo, el semáforo lo dice («No se revisaron todas las hojas del libro»),
   en vez de quedar sólo en el log.
3. **El CUIT, sólo con dígitos 0-9.** Hoy `\d` acepta dígitos de ancho
   completo y arábigos, y el TXT los escribe tal cual.
4. **Toda moneda que no sea DOL avisa** (no frena) hasta que el despachante
   confirme los códigos: el único archivo real usa DOL. El texto del aviso
   dice eso.
5. **D22: (a).** `/generate_maria_export` usa la misma limpieza de textos que
   `/generate_maria`: es el mismo defecto (M10) en otra ruta que escribe el
   TXT. Borrar la pantalla vieja no está en el roadmap.

**Criterios:** rojo antes y verde después en cada punto; el libro armado del
punto 2 (o uno equivalente, generado en la prueba) más una subida normal
detrás: la normal no da 504; los dos archivos reales siguen idénticos;
suite completa en verde.

**Antes de entregar,** traé la rama de la PM: ahí están integradas
RENDIMIENTO-1 y 1b y las piezas MARIA de la Dev 2 (`8e819dd` en adelante).
MARIA-1d ya saca el DOL y el FOB que inventaba el lector de PDF (el hallazgo
6 del subagente). Va a haber choques en `main.py` (guardar la operación) y en
`finalize.js`: la regla es que no se invente nada y que el TXT salga
idéntico.

## Respuestas a tus D (2026-10-07, 13:40 UTC)

- **D22: (a)**, en la devolución (punto 5).
- **D20: (a)**, ya hecha en MARIA-1b.
- **D21:** Emi dice que el nomenclador lo baja la PM. Desde acá la red bloquea
  `www.arca.gob.ar`, y el ZIP de julio ya traía el archivo de 2018. Se espera
  que Emi habilite el sitio o mande el archivo. Mientras tanto, «no está en el
  catálogo» sigue como aviso.
- Anteriores (D13 a D19): en Git.

**Ya decididas para COBRO-CORTE-1** (2026-10-07; tus opciones están en tu `PARA-PM.md`
del commit `62b1d14`):
- **D4 (cuándo se cuenta): (b), con N = 10.**
- **D5: (a).** Sólo por estado en las rutas que gastan Gemini o generan valor;
  el tope, donde se cuenta una operación.
- **D6: (a)** ahora. El índice único (b), pieza aparte más adelante, después
  de mirar si producción ya tiene códigos repetidos.

## Tarea activa — MARIA-1b: controles antes de generar (devuelta: arriba)

Asignada el 2026-10-07. Fase 1 (`ROADMAP.md`). Cambia cuándo se puede
generar el TXT, no lo que sale en él.

**Base:** tu rama (con EXCEL-1).

**Alcance:**
1. Antes de generar, con un aviso claro por producto u operación: NCM que no
   está en el catálogo (si tiene 7 dígitos, proponer el 0 inicial), moneda,
   incoterm, CUIT del importador y montos (vacíos, negativos, en 0). Lo que
   impide un TXT válido no deja generar; lo dudoso avisa.
2. Ningún texto (descripción, nombres, domicilio) mete saltos de línea ni
   `=` que rompan el TXT (M10).
3. Al guardar la operación no se inventan cantidad 1 ni peso 0,5
   (`save_client_operation`, D6 de la Dev 2).
4. El aviso de filas del Excel sin leer queda en el semáforo hasta que la
   persona lo descarte (tu D17), y se avisa si el libro tiene otras hojas con
   datos (tu D18).

**Fuera de alcance:** lo que el generador decide (Dev 2) y el resto de D18
(EXCEL-2).

**Criterios:** rojo antes y verde después por cada control; los dos archivos
reales siguen saliendo idénticos; suite completa en verde.

**Después:** PUNTA-A-PUNTA-1 (abajo) y EXCEL-2.

## Siguiente, apenas entregues — PUNTA-A-PUNTA-1: una prueba de todo el camino

Escrita el 2026-10-07, 13:15 UTC, mientras la PM revisa MARIA-1b. Si el
veredicto de MARIA-1b trae devolución, la devolución va primero.

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
