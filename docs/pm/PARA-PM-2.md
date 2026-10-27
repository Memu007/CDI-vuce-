# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SUFIJOS-1: entregada a revisión (2026-10-27)

**Resultado:** va en `97cd2fa`, con D22 (a): la fuente es el arancel de ARCA
del 07/10/2026, en una tabla local. No hay red, no hay terceros y no queda
lugar para VUCE.

**Lo que decidís vos:**
- **D23:** no frena la entrega. Recomiendo (c).
- Los supuestos reversibles van abajo.
- D20, D21 y D22 ya están contestadas; no queda ninguna D mía abierta.

| Pieza | SHA |
|---|---|
| Base: tu rama con D22 | `f82bdda` |
| Producto: tabla de ARCA, propuesta por producto, sufijo propio y grupo | `fe95a49` |
| Casos y pantalla; casos viejos ajustados a las reglas nuevas | `eec344f` |
| Producto: la unidad estadística general entra en el teléfono | `91e7540` |
| Pantalla, sabotajes y conteo de `sabotaje_valor1c` | `03bc6ed`, `b6b78b9`, `01d27a5` |
| Merge de tu rama | `b2d5588` |
| Producto: hallazgos de la ronda 1 (combinar, producto borrado, letra de control) | `91a7d68` |
| Casos, pantalla y sabotajes de la ronda 1 | `32f3c27`, `0b1c08e` |
| Merge de tu rama (`adfe707`) | `af93dae` |
| Producto: hallazgos de la ronda 2 (tope, celda de grupo, NCM de 8) | `e7f018f` |
| Casos y sabotajes de la ronda 2 | `f86c508` |
| Producto: un `grupo_id` que no se compara no rompe los avisos | `366cecc` |
| Caso y sabotaje 34 | `97cd2fa` |
| **SHA probado:** suite, compileall, sabotajes, smoke, pantalla y e2e | **`97cd2fa`** |

## Decisiones

**D23. Si todos los productos tienen su propio sufijo, el sufijo de la
operación deja de ser obligatorio.**

- **Qué pasa.** Antes de esta pieza, el campo «Sufijo de valor SBT» de la
  operación era obligatorio, salvo cuando todos los productos tenían
  sub-ítems con sufijo (SUBITEMS-1).
- Ahora también deja generar si cada producto entero tiene un sufijo,
  aunque sea el que propuso el sistema. Con el campo vacío, cada producto
  sale sólo con lo que pide el arancel (AA, AB, AI). Un código que el
  arancel no pide y la operación sí, por ejemplo uno de condición de venta,
  no sale y nadie lo dice.
- **Lo que sigue avisando el servidor:** lo que la posición pide y falta.
  Eso no se pierde.
- **Dónde está:** `finalize.js`, `todosConSufijoPropio`. Salió en la ronda 2.

Opciones:
- **(a) Dejarlo así.** Si falta un código que el arancel no pide, se
  entera el MARIA al cargar el TXT.
- **(b) Volver a exigir el campo**, salvo que todos los sufijos los haya
  escrito una persona. Contra: quien no tiene nada que agregar a nivel
  operación tiene que escribir algo para pasar.
- **(c) No frenar, pero avisar** junto al botón: «El sufijo de la operación
  está vacío: cada producto sale sólo con lo que pide el arancel de ARCA».

**Recomiendo (c).**
- No inventa un código.
- No traba a quien no tiene nada que agregar.
- Dice lo que hoy pasa en silencio.
- Es chica, pero es una pieza aparte: no la hice porque no estaba en la
  tarea.

## Lo que se hizo

- **Tabla local** (`proyecto_maria/data/sufijos_arca.json.gz`), armada
  desde el ZIP del repositorio con `scripts/import_arancel_sufijos.py
  --archive docs/pm/datos/arancel_ARCA_07102026.zip`.
  - El script frena si el SHA-256 no es el de `LEEME.md` y no usa la red.
  - La tabla tiene 12 891 niveles y 33 243 unidades estadísticas.
  - Una prueba comprueba que la tabla del repositorio es la misma que sale
    del ZIP.
  - Es un script aparte del de CATALOGO-NCM-1: aquel reescribe el catálogo
    de NCM y sus bajas, y éste sólo suma la tabla de sufijos.
- **En «Lo que decide el despachante», por producto:**
  - Propone marca AA, modelo AB y código AI con lo que leyó la IA, y dice
    qué falta.
  - La fecha viaja con el dato: «arancel de ARCA del 07/10/2026».
  - **Se suma al sufijo de la operación:** AA, AB y AI reemplazan a los
    mismos códigos; CA00 y los demás quedan.
  - Si la suma pasa de 120 caracteres, no se propone nada y queda para el
    despachante.
  - Lo que escribe la persona va tal cual.
- **Si la posición no está:** queda vacía y se avisa.
  - Con la letra de control equivocada, se dice cuál corresponde.
  - Una NCM de 8 dígitos se avisa como posición incompleta.
- **El TXT:**
  - Un producto entero sale con su propio sufijo en `CSBTSVL`; antes salía
    el de la operación.
  - Un grupo exige el mismo sufijo en todos sus ítems. El «-» final no
    cuenta, y la pantalla no tiene celda por producto dentro de un grupo.
  - Si nadie eligió otra unidad estadística, `CARTUNTEST` sale `01` cuando
    la posición lo pide. Con sub-ítems no: sólo si la factura viene en
    kilos.
  - Se avisa el AI repetido entre productos, también en los sub-ítems.
- **El caso del 24/10, en sintético:** el capítulo 39 pide AA y AI, y
  `3920.10.10.100F` lleva `01`. Las pruebas son
  `test_el_capitulo_39_pide_marca_y_codigo_y_la_unidad_es_kilos` y
  `test_la_estadistica_de_la_tabla_va_al_pedido_si_nadie_eligio_otra`.

## Puertas, sobre `97cd2fa`

| Puerta | Salida exacta |
|---|---|
| Suite completa (worktree limpio en `97cd2fa`) | `12 failed, 2964 passed, 302 skipped, 2 xfailed, 96 warnings in 363.63s (0:06:03)` |
| `tests/test_sufijos1.py` | `50 passed, 3 warnings in 7.15s` |
| `python -m compileall -q proyecto_maria` | sin salida, `rc=0` |
| `scripts/testing/sabotaje_sufijos1.sh 97cd2fa <venv>` | `OK: los 34 sabotajes dan rojo por la razón esperada` |
| `scripts/testing/sabotaje_valor1c.sh 97cd2fa <venv>` | `OK: los 25 sabotajes dan rojo por la razón esperada` |
| `smoke_friccion.sh` (app en `97cd2fa`) | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `pantalla_sufijos1.js` | `PANTALLA SUFIJOS-1 OK` |
| `e2e_maria.sh` | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |

## Rojos

Los 12 son los conocidos que dice `PARA-DEV-2.md` («Al traer mi rama»): el
de `test_guardar1` y los 11 del tope de 15 operaciones. No hay ninguno nuevo.

```
FAILED tests/test_clientes_plan02.py::test_export_csv_returns_csv_with_ops
FAILED tests/test_clientes_plan04.py::test_catalogo_productos_endpoints
FAILED tests/test_guardar1.py::test_datos_largos_de_la_operacion_no_impiden_guardarla
FAILED tests/test_maria4_despachante.py::test_lo_elegido_se_guarda_con_la_operacion_y_vuelve_en_los_listados
FAILED tests/test_maria4_despachante.py::test_los_listados_recortan_lo_guardado
FAILED tests/test_op_code_and_fill_if_empty.py::test_fill_if_empty_populates_client_profile
FAILED tests/test_op_code_and_fill_if_empty.py::test_fill_if_empty_does_not_overwrite
FAILED tests/test_operations_manual.py::test_manual_operation_null_client_id
FAILED tests/test_prelaunch_block1.py::TestOperacionManual::test_crear_operacion_manual_ok
FAILED tests/test_prelaunch_block1.py::TestOperacionManual::test_crear_operacion_sin_client_id_400
FAILED tests/test_prelaunch_block1.py::TestOperacionManual::test_crear_operacion_null_client_id_400
FAILED tests/test_prelaunch_block1.py::TestOperacionManual::test_crear_operacion_sin_items_400
```

El rojo de borde de `test_excel2` («ocho_libros») que informé en
SEPARADORES-1b no salió en esta corrida. Una corrida no alcanza para decir
que se fue.

## Hallazgos de la autorrevisión

**Revisores:**
- **Ronda 1, sobre `f82bdda..b2d5588`:** `/code-review high`, adversario
  Opus alto y adversario Sonnet alto.
- **Ronda 2, sobre `f82bdda..0b1c08e`:** `/code-review high` y adversario
  Sonnet alto.
- **`/security-review` no corre acá:** falla porque no hay `origin/HEAD`.
  Lo reemplazó el adversario Sonnet alto, que miró la ruta nueva
  `/api/sufijos/propuesta`: pide sesión, sanea el texto y recorta lo
  largo.

| # | Hallazgo | Ronda | Qué hice |
|---|---|---|---|
| 1 | La propuesta pisaba lo que se escribió en la operación | 1 | Arreglado (`91a7d68`); rojo antes |
| 2 | Al borrar un producto, la propuesta pasaba al que quedaba en su lugar | 1 | Arreglado (`91a7d68`) |
| 3 | Con la letra de control equivocada decía «no está» | 1 | Arreglado (`91a7d68`): dice cuál corresponde |
| 4 | Con sub-ítems, kilos iba solo aunque la factura no viniera en kilos | 1 | Arreglado (`91a7d68`) |
| 5 | El «-» final hacía distintos los sufijos de un grupo; un código con el valor vacío no contaba como faltante | 1 | Arreglado (`91a7d68`) |
| 6 | Una tabla rota rompía la carga; el texto del pedido no tenía límite ni saneo | 1 | Arreglado (`91a7d68`) |
| 7 | Si la suma pasaba de 120 caracteres se perdían los códigos de la operación | 2 | Arreglado (`e7f018f`) |
| 8 | Un grupo tenía celda de sufijo por producto | 2 | Arreglado (`e7f018f`) |
| 9 | Una NCM de 8 dígitos se decía fuera del arancel | 2 | Arreglado (`e7f018f`) |
| 10 | Un `grupo_id` lista daba 500 en los avisos | 2 | Arreglado (`366cecc`) |
| 11 | Todos con sufijo propio, el TXT sale sin el de la operación | 2 | **D23** |
| 12 | Choque de PB01 con PB02 | 2 | Falso: la gramática exige dos letras y (valor), o dos letras y dos cifras |

No anoté qué revisor encontró cada uno; la ronda sí. Cada arreglo tiene su caso, que dio rojo antes del arreglo, y su sabotaje en
`sabotaje_sufijos1.sh`.

## Riesgos (no arreglados; severidad)

- **Media:**
  - Si el arancel tarda más de 10 s en contestar a «listo», la unidad
    estadística no se completa en kilos. Va lo que eligió la persona o DCL,
    como antes de la pieza.
  - Un código repetido dentro del sufijo de la operación se reemplaza en
    cada aparición, así que sale duplicado.
- **Baja:**
  - El tope de 120 en la pantalla mide el texto crudo; el servidor mide
    después de NFKD (las ligaduras se expanden). El servidor lo rechaza con
    un mensaje claro.
  - Un `try/except` en el bucle de sub-ítems, si salta, se saltea los
    avisos que siguen.
  - Al repintar, la celda en la que se está escribiendo pierde el foco. El
    patrón es de antes de esta pieza.
  - `lru_cache` guarda `{}` si la primera lectura de la tabla falla, hasta
    que se reinicia el proceso.
  - La ruta es async y hace trabajo de CPU.
  - No hay límite al tamaño del pedido.
  - `escrita(posicion)` no tiene tope.
  - Un AI heredado de la operación dispara «se repite».
  - El «Falta» de la nota se calcula sólo sobre la propuesta.

## Supuestos reversibles

- **Cambio de contrato:** el sufijo propio de un producto entero reemplaza
  al de la operación en `CSBTSVL`. Antes salía siempre el de la operación.
- Si nadie eligió otra unidad estadística, va la de la tabla (`01`).
- Un grupo no tiene celda por producto: va un sufijo para todo el grupo.
- Arriba de 120 caracteres no se propone nada; queda para el despachante.

## Archivos de producto que toqué

- `proyecto_maria/core/sufijos_arca.py` (nuevo)
- `proyecto_maria/data/sufijos_arca.json.gz` (nuevo)
- `scripts/import_arancel_sufijos.py` (nuevo)
- `proyecto_maria/core/maria_generator.py`
- `proyecto_maria/main.py`
- `proyecto_maria/static/v2/screens/despachante.js`
- `proyecto_maria/static/v2/screens/finalize.js`
- `proyecto_maria/templates/dashboard_v2.html`
- `CHANGELOG.md`

## Para reproducir

```bash
# 1) casos de la pieza → «50 passed»
PYTHONPATH=. python -m pytest -q --no-cov tests/test_sufijos1.py
# 2) sabotajes → «OK: los 34 sabotajes dan rojo por la razón esperada»
scripts/testing/sabotaje_sufijos1.sh 97cd2fa <ruta del venv>
# 3) con la app levantada en 97cd2fa → «PANTALLA SUFIJOS-1 OK»
BASE_URL=http://127.0.0.1:<puerto> node scripts/testing/pantalla_sufijos1.js
# 4) la tabla sale igual del ZIP (lo prueba también el caso 1)
python scripts/import_arancel_sufijos.py --archive docs/pm/datos/arancel_ARCA_07102026.zip
git status --short proyecto_maria/data   # sin cambios
```

**Lo que sigue:** SEPARADORES-1c (D21 b).

Última vuelta: Tue Oct 27 17:50:03 UTC 2026

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM, rutina horaria minuto 35. Entregada SUFIJOS-1 en 97cd2fa (suite con los 12 rojos conocidos, compileall, 34 sabotajes sufijos1, 25 de valor1c, smoke, pantalla y e2e verdes sobre 97cd2fa); D23 abierta en PARA-PM-2.md (sufijo de la operación vacío con todos los productos con propio; recomiendo c, avisar sin frenar), no frena. Sigo con SEPARADORES-1c (D21 b, en PARA-DEV-2.md). Nunca main, sin push --force, sin datos reales del 24/10, nada se publica sin el «dale» de Emi para el SHA, sin Gemini en pruebas, subagentes hasta esfuerzo alto, sin advisor.
