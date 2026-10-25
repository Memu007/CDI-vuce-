# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## VALOR-1b y MARIA-9: entregadas a revisión (2026-10-25)

**Resultado:** las dos van juntas en `efa2e08`.
- **VALOR-1b:** van los cuatro puntos de tu devolución.
  - «Calcular seguro» ya no usa cuentas de un pedido que cambió. Lo
    comprueba al apretarlo, sea cual sea el campo que lo cambió.
  - El seguro calculado deja de avisarse como no leído.
  - La base es el FOB de la factura (D13 b).
  - Un ajuste o un renglón que no es número va como `valor.error`, sin
    texto de Python y sin perder los avisos.
- **MARIA-9:** van sus cuatro puntos.
- **El TXT no cambia** con ninguna de las dos fuera de lo que pediste en
  MARIA-9.1: un sufijo general que nadie usa vuelve a dejar generar.
- Los sabotajes dan rojo por la razón esperada: 23 de VALOR-1b, 31 de VALOR-1
  y 30 de MARIA-9.
- Suite, smoke, e2e y la pantalla de MARIA-9 dan verde sobre `efa2e08`.

**Lo que decidís vos:** D15 (MARIA-9), nueva. No frena la entrega.

| Pieza | SHA |
|---|---|
| Base: informe de VALOR-1 | `23ba183` |
| MARIA-9. Producto: el sufijo general se valida sólo si alguien lo usa | `4ab6a9b` |
| Casos y sabotajes | `b90e11d`, `ecfd977` |
| Producto: cada error de sufijo sale donde se corrige | `e87ea74` |
| Pantalla y sabotajes | `7a83be6` |
| Producto: el error de kilos nombra sólo el renglón chico | `9c20f21` |
| Casos y sabotajes | `a6f7551` |
| Producto: lo que encontró la autorrevisión (kilos, procedencia) | `58f2f79` |
| Casos y sabotajes | `9f1e5b5` |
| Merge de tu rama (`13a0939`, la devolución de VALOR-1) | `52b56a4` |
| VALOR-1b. Producto: la firma del pedido, el aviso del seguro, D13 y los ajustes por API | `28819f0` |
| Casos y sabotajes | `9546fa7`, `7184e9e` |
| Producto: lo que encontró la autorrevisión (verdadero en un renglón, mensajes) | `6ed3619` |
| Casos y sabotajes | `efa2e08` |
| **SHA probado:** suite, sabotajes, smoke, e2e y pantalla | **`efa2e08`** |

## Decisiones

**D15. Un sufijo general que nadie usa pero no se puede leer frena el TXT.**
MARIA-9.1 dice «se valida sólo si algún sub-ítem o renglón lo toma». Ya lo
hace con «ROJO» y con todo lo que no se puede separar en códigos. Pero un
general con `=`, con caracteres de control o de más de 120 caracteres
sigue frenando aunque nadie lo use. Esos controles están antes, porque
rompen el formato `clave=valor` del TXT. El mensaje tampoco dice que es el
sufijo de la operación. Lo encontró mi adversario.
- (a) Dejarlo así y que el mensaje diga «Sufijo de valor de la
  operación: …». Es un cambio de una línea.
- (b) Saltear también esos controles cuando nadie lo usa.

**Recomiendo (a).** Un `=` o un salto de línea en ese campo es un error de
carga, no un texto libre, y nadie lo ve si no frena. No cambié nada: es
la letra de tu tarea.

**D13 y D14:** las tomé como decidiste (b y a).

## Lo que se hizo

### VALOR-1b

1. **Cuentas viejas.** Seguí tu «familia» hasta el final. No alcanzaba con
   llamar a `cuentasViejas()` desde cada lugar que escribe en `op`. Hay
   caminos que cambian el pedido sin pasar por la tarjeta:
   - la restauración;
   - la pantalla de revisión;
   - un campo del despachante;
   - un cambio de operación.

   Ahora:
   - cada respuesta de `/avisos` guarda la **firma del pedido con el que se
     pidió** (`firmaDelPedido`: todo `buildMariaRequest()` menos
     `operation_id`, que lleva la hora). La firma se toma al mandar, no al
     volver;
   - «Calcular seguro» compara esa firma con la del pedido de ahora. Si no
     coinciden, no calcula: pide las cuentas de nuevo;
   - `usarDescuento()` y el cálculo del seguro llaman además a
     `cuentasViejas()`, así el botón se esconde hasta que vuelvan las
     cuentas.

   Las pruebas miran las cuentas con las que se calcula, no el seguro, y dan
   rojo con las dos bases. Cubren:
   - el descuento, el flete, el seguro a mano, la restauración y otra
     operación;
   - un pedido que cambia mientras viajan las cuentas.
2. **El aviso del seguro sin leer.** Al calcularlo, `seguro` entra en
   `campos_completados` y se refresca el semáforo: el aviso «No pudimos leer
   el seguro…» se va. Si `seguro` está en `campos_sin_leer`, la nota del
   botón dice «La factura puede traer un seguro que no pudimos leer:
   revisala antes de calcularlo.».
3. **D13 (b).** Ahora `BASE_SEGURO_SUGERIDO = "fob_factura"`. El botón dice
   «1 % de FOB de la factura + flete». Los casos de la base siguen probando
   que la constante manda: el sabotaje la fija en el código y da rojo.
4. **Ajustes que no son número, por API.**
   - `ajustes_incluir` y `ajustes_deducir` van sin tipo en `MariaRequest`
     (`Any`). `/generate_maria` responde como antes de VALOR-1 y no los usa.
   - `/avisos` los muestra como `valor.error` sin perder los avisos.
   - Un texto, una lista, un objeto, verdadero o falso dan «Ajustes a
     deducir: no es un importe.» o el mensaje de `importe_valido` con el
     texto cortado a 20 caracteres.
   - Un renglón con una cantidad o un valor que no es número da «Renglón 2:
     el valor total «abc» no es un número; no se pueden hacer las cuentas.».
     Verdadero o falso en un renglón ya no cuentan como 1 o 0.
   - Un `TypeError` que se escape da un mensaje fijo, sin el texto de
     Python.

El CHANGELOG dice sólo lo probado: saqué «de antes de cambiar un ajuste ni»
de la línea de VALOR-1.

### MARIA-9

1. **El sufijo general que no se usa ya no frena.**
   `usa_el_sufijo_de_la_operacion` decide si algún sub-ítem o renglón lo
   toma; si nadie lo toma, no se analiza. Cuando alguno lo toma y no se
   puede separar, `/avisos` lo anticipa con el mismo texto del error.
   - Casos: sub-ítems a mano, renglones por API, mezcla, ítem entero con
     sufijo propio.
   - La autorrevisión encontró que el endpoint preguntaba con los renglones
     antes de ponerles la procedencia de la operación. Pedía el sufijo
     general cuando cada renglón traía el suyo. Arreglado en `58f2f79`.
2. **Cada error de sufijo sale donde se corrige** (`finalize.js`). El de
   la operación va bajo su campo, y el de un sub-ítem, bajo ese sub-ítem.
   Lo prueba `scripts/testing/pantalla_maria9.js` con el error forzado
   (`page.route`).
3. **Bordes.** Cada uno tiene su caso y su sabotaje:
   - 120 caracteres pasan y 121 no;
   - `CA100-`, `A(X)-` y `;` como separador;
   - las unidades `05` y `99` del aviso.
4. **El error de kilos nombra sólo el renglón chico.** Si ninguno da cero
   solo y el cero sale del ajuste del redondeo, sigue nombrando a todos,
   porque ahí el culpable es el conjunto.

## Comandos para reproducir

```bash
S=<tu scratchpad>   # con un venv del proyecto en $S/venv y node en el PATH
git fetch origin claude/dev-maria
git diff efa2e08 origin/claude/dev-maria -- proyecto_maria tests scripts   # vacío
git diff 23ba183 efa2e08 -- tests/fixtures/                                # vacío: los golden no cambian
$S/venv/bin/python -m pytest -q --no-cov tests/test_valor1.py tests/test_maria9_*.py tests/test_maria7_devolucion.py   # 213 passed
scripts/testing/sabotaje_valor1b.sh efa2e08 $S/venv   # «OK: los 23 sabotajes dan rojo por la razón esperada»
scripts/testing/sabotaje_valor1.sh  efa2e08 $S/venv   # «OK: los 31 sabotajes dan rojo por la razón esperada»
scripts/testing/sabotaje_maria9.sh  efa2e08 $S/venv   # «OK: los 30 sabotajes dan rojo por la razón esperada»
```

Para `e2e_maria.sh`, poné `$S/venv/bin` primero en el `PATH`: levanta su
propio servidor con el `python` que encuentra.

Cada sabotaje arma su propio worktree descartable. No los corras en
paralelo con la suite (ver «Rojos»).

## Puertas

Todas sobre `efa2e08`. La suite y compileall corrieron solas, en un
worktree limpio.

| Puerta | Salida |
|---|---|
| Suite completa | `2165 passed, 102 skipped, 2 xfailed, 25 warnings in 271.86s (0:04:31)`, rc=0 |
| `compileall -q proyecto_maria` | rc=0 |
| `sabotaje_valor1b.sh` | `OK: los 23 sabotajes dan rojo por la razón esperada`, rc=0 |
| `sabotaje_valor1.sh` | `OK: los 31 sabotajes dan rojo por la razón esperada`, rc=0 |
| `sabotaje_maria9.sh` | `OK: los 30 sabotajes dan rojo por la razón esperada`, rc=0 |
| Smoke (`levantar.sh efa2e08 8831`) | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `e2e_maria.sh` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |
| `pantalla_maria9.js` | `PANTALLA MARIA-9 OK` |
| Golden (`git diff 23ba183 efa2e08 -- tests/fixtures/`) | vacío |

No corrí `ataque_aislamiento.sh`: no toqué datos, sesión ni permisos.

## Autorrevisión

| Revisor | Modelo y esfuerzo | Sobre | Hallazgos | Qué pasó |
|---|---|---|---|---|
| `/code-review high` | — | `23ba183..9f1e5b5` (MARIA-9) | 6 | Arreglados: procedencia en el endpoint (`58f2f79`). Quedan como riesgo: el mensaje con «sbt» lleva al campo general un error de sufijo de renglón que llega por API (la pantalla nunca manda `item.sufijo`); `usa_el_sufijo_de_la_operacion` repite reglas del generador (deuda); los avisos de transformación del general salen aunque nadie lo use; un análisis repetido (eficiencia); un ítem entero descarta su sufijo propio sin avisar (de antes) |
| Adversario | Sonnet, alto | `23ba183..a6f7551` (MARIA-9) | 5 (4 reproducidos, 1 por lectura) | (1) D15. (2) kilos que culpaban al más grande: arreglado en `58f2f79`. (3) El prefijo «Item N» es el del primer renglón: ya pasaba. (4) Un aviso falso del general: riesgo. (5) Pantalla: informativo |
| `/code-review high` | — | `52b56a4..7184e9e` (VALOR-1b) | 10 | Arreglados en `6ed3619`: verdadero o falso en un renglón contaban como 1 o 0; comentario y CHANGELOG. Los demás, en «Riesgos» |
| Adversario | Sonnet, alto (uno solo: vuelta de una devolución de plata) | `52b56a4..7184e9e` (VALOR-1b) | 6 | Arreglados: ninguna prueba distinguía la firma tomada al mandar de la tomada al volver (caso y sabotaje 5b, `efa2e08`); listas y objetos con el texto de Python en el mensaje (`6ed3619`); verdadero en un renglón (el mismo de arriba). Quedan: `_exacto` y `grupo_id` (de antes, en «Riesgos»); el clic que sólo pide las cuentas (informativo) |
| Revisión de seguridad | Opus, el de la sesión (subagente general) | `52b56a4..efa2e08` | 0 vulnerabilidades | `/security-review` no corre en esta sesión (pide `origin/HEAD`, que no existe); la hizo un subagente con la misma consigna. Sin XSS (todo va por `textContent` o `CDI.escapeHtml`), el TXT no cambia, los campos `Any` no abren nada nuevo (corrió entradas hostiles: 1 MB, anidado 5000 niveles, `10**400`), sin filtración en los errores. Un detalle de antes: ver `_exacto` en «Riesgos» |

MARIA-9 no tuvo revisión de seguridad aparte: no toca plata, sesión ni
permisos (sufijos y kilos del TXT). La de arriba cubre sólo VALOR-1b.

El adversario de VALOR-1b probó sin hallazgo: 14 variantes y unos 190
renglones adulterados con el TXT idéntico byte a byte, y ningún 500 en
`/avisos`.

## Rojos

- **`test_excel2::test_ocho_libros…` bajo carga.** Con los sabotajes
  corriendo en paralelo, la suite sobre `7184e9e` dio `1 failed, 2160
  passed`: «la subida normal dio 400 a los 30.1 s … tardó demasiado». Es el
  rojo de entorno conocido, por la CPU cargada. Sola, sobre `efa2e08`, da
  verde.
- **`e2e_maria.sh` sin el venv.** La primera corrida dio `ModuleNotFoundError:
  No module named 'fastapi'`. El script levanta su propio servidor con el
  `python` del `PATH`, que era el del sistema. Con `$S/venv/bin` en el `PATH`
  da verde. Es del entorno, no del producto.
- Ningún rojo de producto.

## Riesgos y lo que no se cubrió

**De VALOR-1b:**
- **El clic que sólo pide las cuentas.** Si el pedido cambió desde las
  últimas cuentas, «Calcular seguro» no calcula: las pide de nuevo y la
  persona tiene que volver a apretarlo. Pasa en la ventana de 400 ms después
  de escribir o con un campo del despachante. No hay aviso de que el clic
  no hizo nada; el botón se esconde y vuelve.
- **La firma es todo el pedido**, no sólo lo que entra en las cuentas. Un
  cambio que no mueve el seguro (un dato del despachante, una descripción)
  también pide recalcular. Lo elegí así a propósito: un falso «cambió» sólo
  cuesta otro clic, y un falso «no cambió» calcula con cuentas viejas.
  Supuesto reversible.
- **`campos_completados`:** al calcular, `seguro` cuenta como completado y
  el aviso se va, como pediste en el punto 2. Si la factura sí traía un
  seguro que no leímos, el único aviso que queda es la nota del botón,
  antes de apretarlo.
- `ajustes_*` como `Any` en `MariaRequest`: el tipo lo valida
  `cuentas_del_valor`, no Pydantic. Hoy no lo usa nadie más.
- `seguroSinLeer` repite la regla de `camposSinLeer` de `review.js`: aquélla
  devuelve mensajes y no se puede reutilizar sin tocar revisión.
- Ajustes y renglones se validan en dos funciones parecidas (`_ajuste` y
  `_numeros_de_los_renglones`).
- **De antes de este diff:**
  - `_exacto` (`maria_generator.py` ~709) repite el valor entero en el
    mensaje. Un renglón con 1 MB de espacios y `inf` devuelve un
    `valor.error` de 1.000.053 caracteres. Es un eco al mismo usuario, en
    texto plano. Se arregla cortando a 20, como `importe_valido`.
  - Un `grupo_id` que es lista u objeto da 500 en `/generate_maria`, y en
    `/avisos` «Hay un dato que no es un número».
- Los que nombraste, sin tocar: `type=number` con «1.000,50», los
  cosméticos, el ajuste mal escrito restaurado sobre un campo vacío.

**De MARIA-9:**
- doble redondeo de kilos (`465.1249` sale `465.13`);
- `cantidad=2.675` sale `2.67` sola y `2.68` en un ítem unido;
- `#sbtSufijoValor` está fuera de `#despachanteWrap`;
- la unidad «99» pasa sin aviso;
- `pantalla_subitems1.js` da rojo **de antes**, no de MARIA-9: usa la ruta
  `chromium-1194` y no carga el CUIT del despachante. Parche:
  `await page.request.put(base + '/api/user/profile', { data: { cuit: '20123456786' } });`
  y la ruta `/opt/pw-browsers/chromium`.

**General:** la CI deselecciona tests de presupuestos y no reemplaza la
suite.

**No corrí** `ataque_aislamiento.sh`: no toqué datos, sesión ni permisos.

## Archivos de producto que toqué

- `proyecto_maria/core/maria_generator.py`
- `proyecto_maria/main.py` (`MariaRequest`, `_cuentas_del_valor`, `/generate_maria`)
- `proyecto_maria/static/v2/screens/finalize.js`

## Siguiente

Arranco SEPARADORES-1. Si el veredicto trae una devolución, esa va primero.

Última vuelta: 2026-10-25 02:27 UTC.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. Entregadas VALOR-1b y MARIA-9 en efa2e08 (suite, 23+31+30 sabotajes, smoke, e2e y pantalla sobre ese SHA); D15 (sufijo general con «=» que nadie usa) abierta en PARA-PM-2.md; D13 (b) y D14 (a) decididas. Sigue SEPARADORES-1. Nunca main, sin push --force, sin datos reales del 24/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
