# Reproducción ORIGEN-2 — 2026-11-20

Pieza de la Dev MARIA. Producto `0d7401ed`, base `4fe296d4`, informe `76b98256` en `PARA-PM-2.md`.
**Aceptada sobre `0d7401ed`**, integrada con `merge` de `76b98256`, sin publicar. Antes de publicar:
copia de la base (es migración de `clients.default_origin` de `varchar(3)` a `text`).

## Lo que corrí

| qué | dónde | salida |
|---|---|---|
| `chequeo-6.py 4fe296d4 0d7401ed` | rama de PM | igual al informe: `producto +44/−42`, dos `AVISO` (la función anónima de `clientes.js` y `init` con una línea sin rama), explicados en el riesgo 7 del informe; alcanzan |
| `tests/test_origen2.py` | `0d7401ed` | `3 passed` |
| `origen2_postgres.py` con `con_pg16.sh` | `0d7401ed` | 8 `OK`, `fallas: 0`. Base sembrada con `character varying(3)` y «CN», NULL, «», «CHI», «HOL»; primer y segundo arranque: `text`, filas iguales; «BRASIL» y la etiqueta de 54 enteras; `«Narnia» da 400 y no toca la fila`; `editar otro dato deja «CHI»: 200 'CHI'` |
| `sabotajes/origen2.sh 0d7401ed`, Postgres 16 descartable | worktree aparte | `BASE` «3 passed», «OK: pantalla del origen habitual», «Postgres: fallas: 0»; **24** «ROJO», `sabotajes sin rojo: 0`, `rc=0`, de 01:52:49 a 02:14:59 UTC. Las 24 líneas son las mismas, una por una, que la salida entera pegada en el informe |
| pytest entero (entorno de la suite, `-p no:randomly`) | `0d7401ed` | `6231 passed, 110 skipped, 3 xfailed, 110 warnings in 1139.51s` |
| `e2e_maria.sh` | `0d7401ed` y `76b98256` | `E2E MARIA OK` en los dos. `b73d96ec` (mi rama) es ancestro de `76b98256`, así que la segunda es la unión |
| Capturas `origen-2-960.png` y `origen-2-1280.png` | informe | se ven «Origen 203 · BRASIL» en la etiqueta y en «Origen habitual», en un renglón |

**Una cuenta del informe no coincide con su propia salida:** la tabla dice «25 ROJO»; la salida pegada
y mi corrida dan 24, y el guion tiene 24 llamadas (`grep -cE '^(sabotaje|pg) '` da 24). Es un error de
cuenta en la tabla, no de la prueba.

## Negativos míos (otro borde)

`tests/test_pm_or2.py`, fuera del repo, sobre `0d7401ed`: `3 passed`.
- Alta y edición: `310`, `["BR"]`, `{"x":1}`, `True`, `3.5` → 400; «BR\x00», un surrogate, «BR<script>»,
  «Brasil; DROP TABLE clients», «B R» → 400; en todos la fila queda «BR». Sólo blancos → 200 y vacío.
- PUT sólo con el origen («Chile») → 200 y «Chile»; PUT de otro dato lo deja; `null` lo vacía.
- **Lo que producción tiene hoy.** El selector de `1cc0a500` (`templates/dashboard_v2.html`) ofrece sólo
  «BR CN DE ES IN IT JP KR PY TR US UY» y vacío. Los doce pasan `origen_para_catalogo` sin cambio y
  `CDI.paisesMaria.etiqueta` los muestra bien («203 · BRASIL», «310 · CHINA», «438 · ALEMANIA,REP.FED.»,
  «410 · ESPAÑA», «315 · INDIA», «417 · ITALIA», «320 · JAPON», «309 · COREA REPUBLICANA»,
  «221 · PARAGUAY», «336 · TURQUIA», «212 · ESTADOS UNIDOS», «225 · URUGUAY»). La importación de clientes
  (`main.py` ~7342) y `client_service.py` no escriben el campo.

## Adversario (Sonnet alto, sin red, `GEMINI_API_KEY` vacía)

Nada que bloquee. Comprobado: la migración en PG16 dos veces seguidas (filas iguales, `text`, la
segunda no hace nada); los 308 «código · nombre» del `datalist` pasan el validador; JS y servidor
resuelven igual en 3533 entradas (0 diferencias); cliente ajeno → 404; 2 MB → 400 en 0,39 s; abrir A,
cerrar y dar de alta no arrastra el origen de A.

**Riesgo bajo, reproducido:** un cliente con un origen viejo recortado («CHI», «HOL») que alguien lee
con GET y devuelve entero con PUT recibe 400 y el otro cambio no se guarda. La pantalla no lo sufre
(no manda el origen sin tocar) y producción sólo pudo guardar las doce siglas de arriba, que pasan.
Queda como riesgo escrito, sin código: no hay camino de hoy.

## Decidido por la PM

- **D276 (a):** el alta sin origen sigue guardando «CN», como la base.
- **D277 (a):** riesgo escrito. Con el selector de producción no se pudo guardar un recorte de tres
  letras. La consulta de sólo lectura del informe se le ofrece a Emi, opcional, junto con la copia.
- **Riesgo 2** (traba de `clients` en el arranque, `lock_timeout` 5 s): va en la nota de publicar con la
  copia de la base; publicar en un momento sin uso.
- **Riesgo 6** (moneda recortada a 3, «Dólar» → «DÓL»; la reconstrucción de SQLite que no copia
  `fecha_inic_activ` ni `column_mapping`) y el riesgo 1 (la calculadora recorta a 3): cambian
  comportamiento, así que van a Emi como propuesta, no a la cola de limpieza.

## Lo que no corrí

Navegadores reales de Windows y macOS; la pantalla del adversario la leyó, no la corrió; nada contra
producción ni su copia.
