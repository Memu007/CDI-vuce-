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

**MARIA-3 devuelta** (2026-10-07, sobre `088577f`). La PM reprodujo el rojo
antes (`54 failed`) y la focal (`183 passed`). Su subagente Sonnet alto: los
gastos FOB, los avisos antes de generar (672 combinaciones sin diferencias) y
el archivo de 2025 se sostienen; el de 2026 difiere sólo en `LDVDREFDOC`
(MARIA-6) y una línea en blanco. Detalle en
`REPRODUCCION-MARIA-3-2026-10-07.md`.

**Devolución, cinco puntos** (cada uno con su rojo antes y verde después):
1. **Procedencia:** se rechazan 129 de los 309 países que ofrece la pantalla
   (`pais_de_la_tabla` compara contra `PAISES_INDEC`, que no tiene 668 Hong
   Kong, 436 Turquía, 435 Chipre, 223 Puerto Rico, 150, 242, 254, 358…).
   La pantalla y la validación usan una sola tabla oficial; decí cuál y de
   dónde sale.
2. **Año del `IEXT` sin fecha:** con la fecha vacía o ilegible, el año sale de
   hoy o de texto suelto (`/26`, `/07`, `/99`, `/٢٥`). Sin una fecha de
   emisión válida no se genera: se pide la fecha, como con el estado.
3. **Fechas que salen equivocadas como válidas:** año de dos dígitos
   (`01/01/69` → 1969: tiene que ser 2069 o pedirse); fecha futura o de hace
   más de dos años → aviso antes de generar. El d/m contra m/d ambiguo queda
   anotado como riesgo.
4. **Procedencia rara** (`²`): 400 con un mensaje propio, nunca el texto de
   Python ni un 500 en `/generate_maria/avisos`. Una procedencia de ítem en
   blanco no pisa la de la operación.
5. **Gastos:** un importe no finito, negativo o absurdo (`1e308`, `nan`,
   `inf`, `-5`) no llega al TXT, tampoco por `gastos_fob`: 400 con mensaje.

Suite completa en verde. MARIA-1d sigue en curso: entregá primero la
devolución.

## Respuestas a tus D (2026-10-07, 10:15 UTC)

- **MARIA-3:** devuelta (arriba); va antes que MARIA-1d.
- **D12: (a), como MARIA-1d**, antes de MARIA-5.
- Anteriores (D5 a D11): en Git.

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
