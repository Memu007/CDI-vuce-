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
y sus pantallas. La Dev 1 hace la cola técnica en `claude/dev1-tecnica`; no
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

**MARIA-2 aceptada sobre `65ea6f3`** (2026-10-07). La PM reprodujo el rojo
antes (vuelve `ITEM DEMOSTRACION` con el producto de la base), las focales
(`91 passed`) y la suite (`689 passed, 102 skipped`). Su subagente no encontró
otro camino que invente productos. Tu supuesto 1 (validar antes de la cuota)
queda aceptado. Detalle en `REPRODUCCION-MARIA-2-2026-10-07.md`. Integrada en
la rama de la PM.

## Respuestas a tus D (2026-10-07, 01:10 UTC)

- **D1 (sin clave, leer igual los PDF con texto): (a).** Nada de lector viejo
  sin probar.
- **D2 (Gemini caído o clave inválida): (b), pieza chica aparte, MARIA-2b.**
  Va **después** de MARIA-1a (abajo).
- **D3 (códigos de tres letras): (a).** La tabla «tres letras → dos letras»
  se genera una vez desde ISO 3166-1, con la prueba de que cada destino existe
  en la tabla oficial. `pycountry` sólo para generarla, no como dependencia.
  Prueba para el cambio en el TXT: la norma ISO y la tabla oficial VUCE.
- **D4 (producto sin origen): (a), vacío y con el aviso del semáforo.**
- **Tu plan de MARIA-1a, aprobado:** una sola función de origen para las dos
  copias del lector, una sola función para los números (con la regla de la
  coma que propusiste), nada de 0,5 ni 1 inventados, y el arreglo del precio
  `2.45` → `245` en la copia de PyMuPDF.

## Tarea activa — MARIA-1a: la factura bien leída

Hallazgo M5. El lector corta el país de origen a dos letras: `CHN` → `CH`,
que es **Suiza**; `MEX` → Montenegro. El corte está en **dos copias** del
lector (`pdf_extractor.py:2136` y `:2194`, y `:2339` y `:2361`): si se
arregla una sola, queda el error. Además, las cantidades con coma se
descartan en silencio y un peso faltante se completa con 0,5 kg
(`:2153-2162`, `:2197`, `:2356-2364`).

**Alcance:** el país sale bien con los códigos de dos y de tres letras y con
el nombre, contra la tabla oficial de países que ya está en el código
(`core/maria_generator.py:16`, tabla VUCE); cantidades con coma bien leídas;
un dato que falta queda vacío y con aviso, nunca inventado.

**Prueba para el cambio en el TXT:** la tabla oficial de países (ya está en el
código). Los dos archivos reales siguen saliendo idénticos.

**Fuera de alcance:** el peso total por producto (MARIA-5, espera al
despachante) y las validaciones antes de generar (MARIA-1b).

**Criterios:** rojo antes y verde después con `CHN`, `MEX`, `China` y
`P.R. China`, y con cantidades `1,5` (coma decimal) y `1,500` (separador de
miles en una factura en inglés). Si no se puede saber cuál es, aviso y nada
adivinado. Suite completa en verde.

## Después — MARIA-2b (apenas entregues MARIA-1a)

Tu D2: con clave, pero Gemini caído o con clave inválida, el mismo 503 con su
`code` y el botón de carga manual, en vez del 400 «No se encontró tabla de
items…». Con un Gemini falso que falla; ni Gemini real ni internet.
