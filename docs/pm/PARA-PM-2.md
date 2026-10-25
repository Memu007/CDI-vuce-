# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## VALOR-1 — entregada a revisión (2026-10-25)

**Resultado:** la tarjeta «Ajustes y seguro» de la pantalla final está
hecha: ajustes a incluir y a deducir, FOB casillero, el descuento de la
planilla como sugerencia y el botón «Calcular seguro». **El TXT no cambia**
(D12): `MDDTFOB` sigue siendo el FOB de la factura, y con ajustes el aviso
dice que el casillero «va al TXT en una próxima versión». Lo que la autorrevisión
encontró dentro de la tarea va arreglado, cada uno con su rojo antes. Los 31
sabotajes dan rojo por la razón esperada. El smoke y la e2e dan verde.
La suite completa sobre `3352a01` da verde, sin rojos de entorno.

**Lo que decidís vos:** D13 y D14, nuevas. Ninguna frena la entrega, pero **D13
contradice en parte «VALOR-1 no toca el TXT»**: leela antes del veredicto.

| Pieza | SHA |
|---|---|
| Base: mi informe de MARIA-7 y MARIA-8 | `f71eaa9` |
| Producto: la tarjeta | `d810c47` |
| Casos | `ec4f2d6` |
| Merge de tu rama (respuesta a D12) | `e528578` |
| Producto: el aviso y la base del seguro (D12, D12b) | `037ccbe` |
| Casos | `0df3d22` |
| Merge de tu rama | `39ba53e` |
| Producto: lo que encontró la autorrevisión | `5b6364c` |
| Casos y sabotajes 19 a 30 | `1c02398` |
| Merge de tu rama (`30d5c1b`, sólo `PARA-DEV.md`) | `21b08f6` |
| Producto: el botón del seguro sin operación cargada | `ded0ad3` |
| Caso y sabotaje 31 | `3352a01` |
| **SHA probado:** suite, sabotajes, smoke y e2e | **`3352a01`** |

Después de `3352a01` sólo cambian este informe y el merge de tu rama
(`d234fe2`: documentos y tu herramienta; `git diff 3352a01 HEAD --
proyecto_maria tests scripts` da vacío).

## Decisiones

**D13. Con el botón, los ajustes llegan al TXT por el seguro.**
Hice D12b como pediste: la base del seguro sugerido está en un solo lugar
(`BASE_SEGURO_SUGERIDO`, `core/maria_generator.py`), arranca en FOB
casillero y el botón la nombra («Calcular seguro (1 % de FOB casillero +
flete): …»). Pero el seguro que pone el botón sale en `MDDTASS`, `MARTASS`
y en los gastos posteriores al FOB. Ejemplo sintético: FOB 1387,50 y flete
7925. Sin ajustes, el sugerido es 93,13. Con 1000 a deducir es 83,13,
mientras `MDDTFOB` sigue en 1387,50. O sea: el TXT lleva un FOB sin ajustes
y un seguro calculado con ajustes.
- (a) Dejarlo así. El botón dice sobre qué calcula y lo aprieta la persona;
  el aviso agrega «El seguro sugerido ya usa el FOB casillero».
- (b) Que la base arranque en FOB factura hasta PRORRATEO-1. Es cambiar una
  constante y dos casos; el botón diría «1 % de FOB factura + flete».

**Recomiendo (b).** Con (a), el TXT queda incoherente consigo mismo hasta
PRORRATEO-1, y eso es justo lo que D12 quiso evitar. (b) se revierte con
una línea cuando el casillero vaya al TXT. No lo cambié: contradice tu D12b
y es tuya.

**D14. El botón aparece aunque la condición sea CIF o CIP.**
En CIF o CIP el seguro ya viene en el precio, y el 1 % sugerido puede
sobrar. Hoy el botón se ofrece igual si la operación no trae seguro.
- (a) Dejarlo así: se ofrece y la persona decide.
- (b) Esconderlo en CIF, CIP, CFR… según lo que diga el despachante.

**Recomiendo preguntarle al despachante** y, mientras tanto, (a). No sé qué
condiciones llevan el seguro adentro para el MARIA, y adivinarlo cambia lo
que sale.

**D9, D10 y D11:** leí tus respuestas en `PARA-DEV-2.md` (a, a y b en
MARIA-9). Las doy por cerradas.

## Lo que se hizo

- **Las cuentas viven en el servidor.** `cuentas_del_valor`
  (`core/maria_generator.py`) devuelve FOB factura, ajustes, FOB casillero,
  flete, seguro y seguro sugerido, al centavo con `Decimal`.
  `/generate_maria/avisos` las devuelve en `valor`. Un importe inválido, un
  casillero negativo, un producto mal formado o un número fuera de rango
  van como `valor.error` a la tarjeta: los avisos de siempre no se pierden.
- **La tarjeta** (`templates/dashboard_v2.html`, `static/v2/screens/finalize.js`)
  muestra las cuentas y se rehace al escribir.
  - Un número que el campo no entiende queda marcado y a la vista.
  - Lo que se está escribiendo no se pisa.
  - Una respuesta vieja no pisa una nueva.
  - Si fallan los avisos, lo dice.
- **El descuento de la planilla** se ofrece con su fila («La planilla trae
  un descuento de 87,50 (fila 14).») y no se pone solo. Si «Ajustes a
  deducir» ya tiene otro importe, el botón no aparece y el texto pide
  sumarlo a mano.
- **«Calcular seguro»** pone el sugerido y marca `seguro_calculado`. No pisa
  un seguro que traiga la factura. No calcula con cuentas de antes de
  cambiar un ajuste, ni de otra operación, ni con error. Funciona aunque
  todavía no haya operación cargada (esto lo encontré al releer, en `ded0ad3`).
- `review.js`: dos líneas. Un seguro escrito a mano deja de contar como
  calculado, así el botón no lo pisa.

**Supuesto reversible:** el aviso con ajustes sale sólo si hay algún ajuste.
Sin ajustes, casillero y factura son iguales y no hay nada que avisar.

## Comandos para reproducir

```bash
S=<tu scratchpad>   # con un venv del proyecto en $S/venv y node en el PATH
git fetch origin claude/dev-maria
git diff 3352a01 origin/claude/dev-maria -- proyecto_maria tests scripts   # vacío
git diff f71eaa9 3352a01 -- tests/fixtures/                                # vacío: los golden no cambian
$S/venv/bin/python -m pytest -q --no-cov tests/test_valor1.py             # «49 passed»
scripts/testing/sabotaje_valor1.sh 3352a01 $S/venv                        # «OK: los 31 sabotajes dan rojo por la razón esperada»
```

El sabotaje arma su propio worktree descartable. No lo corras en paralelo
con la suite.

## Puertas

| Puerta | SHA | Salida exacta |
|---|---|---|
| Casos de VALOR-1 | `3352a01` | `49 passed, 3 warnings in 12.10s` |
| Sabotaje de VALOR-1 | `3352a01` | `OK: los 31 sabotajes dan rojo por la razón esperada` |
| Suite completa, worktree limpio | `3352a01` | `==== 2095 passed, 102 skipped, 2 xfailed, 23 warnings in 248.18s (0:04:08) =====` (rc=0) |
| `compileall -q proyecto_maria` | `3352a01` | rc=0 |
| Smoke (API levantada con `levantar.sh`) | `3352a01` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| e2e MARIA | `3352a01` | rc=0, `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |

Cada sabotaje da rojo en su caso y no en otro: `deducir_suma` 7 failed,
`incluir_sin_validar` 6, `seguro_sin_flete` 4, seis más con 2 cada uno y
el resto con 1 (log completo en el scratchpad, no en el repo).

**No corrí** `ataque_aislamiento.sh`: no toqué datos, sesión ni permisos.
`/security-review` no corre en esta sesión (pide `origin/HEAD`, que no
existe); la revisión de seguridad la hice a mano: los textos de la tarjeta
van con `textContent`, y la tabla de cuentas con `innerHTML` pasa cada
celda por `CDI.escapeHtml`.

## Autorrevisión

| Revisor | Modelo y esfuerzo | Sobre | Hallazgos | Qué pasó |
|---|---|---|---|---|
| `/code-review high` | — | `f71eaa9..39ba53e` | CR#1 a CR#10 | Arreglados en `5b6364c`: cuentas viejas en el botón, descuento que pisa otra deducción, error que vaciaba la tarjeta, producto mal formado. Quedan: base del seguro (D13), CIF/CIP (D14), formato de importes duplicado en JS y Python (baja) |
| Adversario | Opus, alto | `f71eaa9..39ba53e` | ADV#1 a ADV#5 y menores (el conteo exacto no lo conservé) | Arreglados en `5b6364c`: respuesta vieja, campo mal escrito que se borraba, número enorme que daba 500. Quedan: D13, y un `ajustes` que no es número (texto, `[]` o `{}`) da 422 sólo por API (baja) |
| Relectura propia | — | `1c02398` | 1 | El botón sin operación cargada no hacía nada. Arreglado en `ded0ad3`, con rojo antes |

El adversario probó sin hallazgo:
- el redondeo, con 3000 muestras;
- `NaN`, `Infinity`, `1e400`, `true` y `-1` por la ruta del navegador, con
  el TXT idéntico;
- que `fob_factura` sea igual a `MDDTFOB`;
- que no se pise el seguro de la factura;
- que el descuento no se aplique solo;
- que no haya XSS.

## Riesgos y lo que no se cubrió

- **D13:** si la persona aprieta el botón con ajustes, el seguro del TXT ya
  usa el casillero y el FOB no.
- Hasta PRORRATEO-1, el `MDDTFOB` de una factura con descuento no coincide
  con el que se aceptó el 2026-10-24. Es lo que dijiste en D12.
- `onEnterValidating` y `pintarValor(null)` no tienen prueba propia; los
  cubre la de «otra operación».
- La CI deselecciona tests de presupuestos: no reemplaza la suite.

## Archivos de producto que toqué

- `proyecto_maria/core/maria_generator.py`
- `proyecto_maria/main.py` (`/generate_maria/avisos`, `_cuentas_del_valor`)
- `proyecto_maria/templates/dashboard_v2.html`
- `proyecto_maria/static/v2/screens/finalize.js`
- `proyecto_maria/static/v2/screens/review.js`

## Siguiente

Arranco MARIA-9 y después SEPARADORES-1, como dice tu canal. Si el veredicto trae una devolución, esa va primero.

Última vuelta: 2026-10-25 00:45 UTC.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. Entregada VALOR-1 en 3352a01 (suite, 31 sabotajes, smoke y e2e sobre ese SHA); D13 (base del seguro) y D14 (CIF/CIP) abiertas en PARA-PM-2.md; D9–D11 respondidas. Sigue MARIA-9 y después SEPARADORES-1. Nunca main, sin push --force, sin datos reales del 24/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
