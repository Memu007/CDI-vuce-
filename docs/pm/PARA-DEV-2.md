# PM → Dev 2

Este archivo es de la PM principal (en CDI no hay PM visual). Vos lo leés y
contestás en `PARA-PM-2.md`.

## Cómo trabajás

`AGENTS.md`, `CLAUDE.md`, `docs/pm/ONBOARDING-DEV.md` y los comandos
`/entregar` y `/respondio`. No se copian acá.

**Tu rama: `claude/dev2-maria`**, creada desde la de la PM
(`claude/practical-shannon-szpwkn`). Antes de cada tarea traés la de la PM con
`merge`. Nunca `main`.

Sos la Dev de la **cola MARIA**: el archivo MARIA.TXT, el lector de facturas
y sus pantallas. La Dev 1 trabaja en `claude/dev1-tecnica` (lectura de PDF, Excel y controles); no
tocás su canal ni su rama.

Herramientas: todas menos el consejero; tu sesión y tus subagentes hasta
esfuerzo alto, nunca Fable (`ONBOARDING-DEV.md`, «Rol»).

**Tu PM es la PM principal.** Ella te despierta con `fire_trigger` de tu
rutina; vos la despertás con el de la suya al entregar o al dejar una D que te
frena (donde `/entregar` dice «PM visual», en CDI es la PM principal). Los ids
están en `NOW.md`, «Quién hace qué».

**Regla del archivo MARIA** (límite que no se negocia): ningún cambio en lo
que sale en el TXT sin prueba (la ley, un archivo real o la respuesta del
despachante). Los dos archivos reales anonimizados
(`tests/fixtures/maria_golden_anon.TXT` y `maria_golden_subitems_anon.TXT`)
tienen que seguir saliendo idénticos, salvo que la tarea diga otra cosa.

## Último veredicto

**MARIA-4 aceptada sobre `2461939`** (2026-10-07, con la devolución). La PM
reprodujo el rojo antes de la devolución sobre `6149ef3` (`9 failed`: estado
contra origen en `CN-1/3/5`, `AR-2/4/6` y `200-2`; supuestos con el orden del
origen; avisos en la pantalla vieja), la focal con los archivos reales (`122
passed`) y la suite (`846 passed, 102 skipped`). La primera revisión ya había
atacado lo central (`REPRODUCCION-MARIA-4-2026-10-07.md`). No corrido por la
PM: tu comprobación de pantalla de la v2.

Aceptadas y sin integrar hasta después del ensayo: MARIA-1a, 2b, 1c y 4.

**Tu contexto está en ~88 %: no arranques MARIA-3 hasta que Emi pegue tu
`/compact`** (a la mañana). Todo lo que necesitás está abajo.

## Respuestas a tus D (2026-10-07, 05:30 UTC)

- **D5: (a), como MARIA-1c** (abajo), antes de MARIA-4.
- **D6: a la Dev 1, en MARIA-1b.**
- **D7: (a).** Se mide con facturas reales cuando Emi pruebe.
- **D8: (a), dejarlo.** Lo mismo decidió la Dev 1 con su lectura lenta (D11).

## Respuestas a tus D (2026-10-07, 06:10 UTC)

- **D9: (a), hecho por la PM** en `docs/pm/herramientas/levantar.sh`: las
  novedades de ARCA apuntan a un puerto local cerrado.
- **D10:** tenés razón. MARIA-4 queda escrita abajo.

## Respuestas a tus D (2026-10-07, 10:15 UTC)

- **MARIA-3:** en revisión de la PM. Mientras, arrancá MARIA-1d (abajo).
- **D12: (a), como MARIA-1d**, antes de MARIA-5.

## Tarea activa — MARIA-1d: un campo vacío no llega al TXT como «None»

Asignada el 2026-10-07. Sale de tu D12. Es chica.

**Base:** tu rama (con MARIA-3).

**Alcance:** en las dos copias del lector, un campo que Gemini devuelve
vacío queda vacío: nada de «None» ni «NON» (número de factura, vendedor,
comprador, domicilio, moneda, incoterm y cualquier otro que encuentres con el
mismo defecto). Lo que queda vacío y el TXT necesita, se avisa antes de
generar.

**Criterios:** rojo antes y verde después con cada campo (hoy
`IDSO=FAC_None`, `CDDTINCOTE=NON`); una prueba que busque «None» en todo el
TXT generado con una factura de campos vacíos; los dos archivos reales salen
idénticos; suite completa en verde.

**Después:** MARIA-5; MARIA-6 cuando lleguen los archivos reales del
despachante.

**Datos nuevos del despachante para MARIA-4** (2026-10-06, 22:12 y 22:15;
detalle en `PREGUNTAS-DESPACHANTE.md`):
- **Empresa de digitalización:** se elige en cada operación, como el banco
  (CDI propone la última usada). Modoc = `PSAD06`, Lakaut = `PSAD01`.
- **Reducción o exclusión del IVA adicional:** es una «ventaja» que el
  despachante elige en el Kit (`IVAADREDUCCION`). No va en el TXT (ningún
  archivo real trae ventajas): sólo un aviso de que se elige ahí.
