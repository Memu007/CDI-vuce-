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

(ninguno todavía)

## Tarea activa — MARIA-2: sin clave de Gemini no se inventan productos

Asignada el 2026-10-07. Roadmap aprobado por Emi (`ROADMAP.md`, cola MARIA,
pieza 1). Hallazgo M4 de `AUDITORIA-2026-10-06.md`.

**Base:** la cabeza de `claude/practical-shannon-szpwkn` al arrancar. Su
código es idéntico a `e8344d0`.

**Problema.** Si falta la clave de Gemini (o el lector con IA está apagado),
el lector de PDF devuelve dos productos de demostración
(`proyecto_maria/pdf_extractor.py:1933-1960`, «ITEM DEMOSTRACION»). Llegan a
la pantalla y al TXT sin ninguna marca: un despachante podría declarar
productos que no existen.

**Alcance.**
1. Sin clave o con el lector apagado: ningún producto inventado. Error claro
   en castellano («no se pudo leer la factura automáticamente; cargá los
   productos a mano»), con un código de estado que el frontend distinga
   (`main.py:3446`, `upload_pdf_public`).
2. La pantalla muestra ese mensaje y deja seguir con carga manual.
3. Revisá si hay otros caminos que devuelvan datos inventados cuando falla
   Gemini (por ejemplo, el «fallback» del mismo lector) y listalos. Los que
   inventen datos, mismo arreglo; los que sólo leen el texto del PDF, quedan.

**Fuera de alcance:** el país de origen, las cantidades y el peso (MARIA-1a);
que leer un PDF frene el sitio (RENDIMIENTO-1, de la Dev 1); cambiar el
modelo de Gemini.

**Criterios de aceptación** (con la salida pegada):
- Rojo antes: sin clave, subir un PDF devuelve los productos de
  demostración. Verde después: error claro y cero productos.
- Con clave inventada (`test-key`) las pruebas siguen como antes: ni Gemini
  real ni internet desde las pruebas.
- Los dos archivos reales siguen saliendo idénticos.
- Suite completa en verde sobre el SHA que entregás, desde base limpia.
- Una captura de la pantalla con el mensaje (navegador local).

**Leé:** `AUDITORIA-2026-10-06.md` (M4) y `ROADMAP.md` (cola MARIA).

**Cuándo frenar y consultar (D):** si quitar el modo demostración rompe una
pantalla de bienvenida o una demo comercial que dependa de él.

**Entrega:** con `/entregar`. Producto, pruebas e informe en commits
separados. Autorrevisión con un subagente Sonnet medio o alto.

## Después — MARIA-1a: la factura bien leída (apenas entregues MARIA-2)

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
