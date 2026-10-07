# Dev 2 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## SUBITEMS-1 (puntos 7 a 10) y la e2e — reentrega con MARIA-5: **`df4de22`** (producto en `4446571`)

**Resultado: los cuatro puntos de `5170016`, con rojo antes y verde después, y
`e2e_maria.sh` en «E2E MARIA OK». Para decidir: nada; dos cosas para que
mires (abajo).** Base: tu rama hasta `4c6f2d4` integrada (`a123b93`), arriba
de la segunda devolución de MARIA-5 y CATALOGO-NCM-1 (`a8a83f3`, ya informada
abajo). D27: tomada (a).

| # | Qué hace ahora | Rojo antes |
|---|---|---|
| 7 | `subitems` = `5`, `true`, `3.5` o un objeto: 400 «Item 1: los sub-ítems no tienen el formato esperado». `controles_antes_de_generar` ya no recorre lo que no es una lista | `3 failed` (500) en `tests/test_subitems1.py` |
| 8 | El panel compara el valor en decimal exacto (enteros grandes, los mismos dígitos que `Decimal(repr())` del servidor), con 0,01 de tolerancia | `pantalla_subitems1.js` en `a123b93`: «1 × 0,04 contra 1 × 0,03» daba «⚠» y el servidor generaba |
| 9 | «Suman 2,9 de 3 unidades…» y dice qué no cierra: «Las cantidades de los subítems no suman la del producto» / «Los valores… (se admite 0,01 de diferencia)» | en `a123b93`: «Suman 3 de 3 unidades» |
| 10 | El error de un subítem (`Item N, sub-ítem M: …`, el del sufijo incluido) vuelve al paso de NCM, abre el panel y sale bajo ese subítem; se va al corregir, agregar o borrar uno. Para que «Item N» sea el producto de la pantalla, el generador numera los errores de sub-ítems por su lugar en el pedido (antes, con un grupo antes, decía la línea del TXT y no coincidía con el de `main.py`) | en `a123b93`: «no sale bajo el subítem 2»; `3 failed` en Python por el número |

**La e2e** (`config/e2e_maria.js`), puesta al día:
- Completa la fecha de emisión (la línea de GUARDAR-1 de la Dev 1; sin ella
  no hay OK posible en mi SHA; si la Dev 1 suma la misma, el merge es trivial).
- Mi pieza cambió el recorrido: desde MARIA-5, un 0 en el peso de un grupo no
  se acepta (vuelve el valor). La e2e ahora prueba eso, desagrupa, pone 0 en
  un producto solo (Validación lo frena) y vuelve a agrupar.
- Espera la respuesta de la revalidación. Una corrida dio rojo ahí («Generar»
  seguía apagado con el resultado viejo en pantalla); no confirmé la causa,
  creo que leyó el resultado de la visita anterior. Después de esperar la
  respuesta: 5 de 5 OK.

| Puerta | Resultado |
|---|---|
| Integración: tu rama hasta `8a3e286` (GUARDAR-1) traída con `merge` en `df4de22`. Choques: la fecha de la e2e (quedó tu línea, `01/10/2026`) y `CHANGELOG.md` (quedan las dos entradas) | — |
| Suite completa, worktree limpio, en `df4de22` | `1526 passed, 102 skipped, 2 xfailed, 25 warnings in 150.27s`, 0 failed |
| Pantallas en `df4de22` (y en `4446571`) | `OK: pantalla MARIA-5`, `OK: pantalla CATALOGO-NCM-1`, `OK: pantalla SUBITEMS-1` |
| `e2e_maria.sh` en `df4de22` (y en `4446571` y `fe79a0e`) | `E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.` |
| Sabotajes | SUBITEMS-1: 9 de 9 (dos nuevos: el control que revienta con `5` y el número de línea); `sabotajes/maria1b.sh`: 0 fallas (un patrón al día). MARIA-5: 49 de 49 en `fe79a0e`; CATALOGO-NCM-1, MARIA-3 y 1d: corriendo al escribir esto (los agrego en cuanto terminen). |

**Autorrevisión** (adversario Sonnet alto, sobre `fe79a0e`): el TXT no
cambia (3000 pedidos al azar, los 949 que salen, idénticos byte a byte entre
`a123b93` y `fe79a0e`), sin XSS, sin 500, y el panel coincide con el servidor
en ~20.000 casos del borde. Encontró:
- **Media, corregido en `4446571`:** el error quedaba en la posición; al
  borrar o agregar un subítem caía sobre otra fila. Rojo antes en la pantalla.
- **Para que mires (no lo toqué):** con un grupo antes, el mismo producto
  dice «Item 3, sub-ítem 2» en sus subítems pero «Item 2» en el peso y el
  estado (esos siguen con la línea del TXT, como antes). Unificar todo a la
  posición de la pantalla toca mensajes de otras piezas; lo dejo a tu criterio.
- **Para que mires (no lo toqué):** los errores de subítems de los controles
  de MARIA-1b (`{errors: [...]}`, p. ej. cantidad NaN) siguen saliendo en la
  pantalla final, no bajo el subítem; el panel ya los marca antes.
- Muy baja, no tocado: con valores absurdos (1e-300 junto a 1e11) el
  `Decimal` de 28 dígitos del servidor redondea y el panel no; con 200.000
  subítems el panel desborda la pila. Ninguno se alcanza desde la pantalla.

Para reproducir:
```
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh df4de22 8890
for s in maria5 catalogo_ncm1 subitems1; do BASE_URL=http://127.0.0.1:8890 node scripts/testing/pantalla_$s.js; done   # tres «OK: pantalla …»
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh a123b93 8891
BASE_URL=http://127.0.0.1:8891 node scripts/testing/pantalla_subitems1.js   # FALLA: el error del sufijo no sale bajo el subítem 2
scripts/testing/sabotaje_subitems1.sh df4de22 <venv>                     # OK: los 9 sabotajes…
```

## MARIA-5 y CATALOGO-NCM-1 — segunda devolución: **`a8a83f3`** (producto en `135ff27`)

**Resultado: los seis puntos de `b2bb20c`, con rojo antes y verde después.
Para decidir: nada nuevo; la D27 de SUBITEMS-1 sigue abierta.** Base: tu rama
hasta `b2bb20c` integrada, con SUBITEMS-1 (`88564ec`) adentro. SUBITEMS-1 ya
estaba entregada en un corte limpio cuando llegó el veredicto.

| # | Qué hace ahora | Prueba (`tests/test_devolucion2_maria5_ncm.py`) |
|---|---|---|
| 1 | Una columna de peso que no dice de qué es («Peso por caja», «Peso por bulto») es «dudosa». Nunca le gana a una reconocida: «Peso por caja» = 40 y «Peso» = 2,5 da 2,5, en cualquier orden. Sola, se usa como de una unidad, con el aviso «no dice si es el peso de una unidad o el de toda la línea… Revisala». Orden: neto > total > de una unidad > dudosa > bruto | rojo antes: 400 kg |
| 2 | El bruto es bruto aunque diga «unitario» («Peso bruto unitario», «Gross weight per unit»): va último y con aviso | rojo antes: leído como neto |
| 3 | Dos pesos de la línea que no coinciden: «en 1 fila(s) «Peso total» no da lo mismo que «Peso neto» (por ejemplo, 27 kg y 25 kg)» | rojo antes: sólo los nombres |
| 4 | `pantalla_maria5.js` manda CUIT, vendedor y comprador (MARIA-1b) | las tres pantallas dan OK en `135ff27`, el producto de `61cf88f` |
| 5 | La NCM tiene **un solo aviso**: el de `_control_ncm`, con el texto del catálogo vigente («se dio de baja en el nomenclador vigente de ARCA (2026-10-07)… buscá la nueva»; ya no «el de 2018»). Sale en `/api/validate/smart` con cabecera o sin ella, en `/generate_maria` y **en `/generate_maria/avisos`**. Sigue siendo aviso, no freno. `run_smart_validations` ya no lo agrega por su cuenta. `test_maria1b_controles.py` espera el texto nuevo | rojo antes: dos avisos, y ninguno en los avisos de antes de generar |
| 6 | Sin el archivo del catálogo (la prueba apunta a uno que no existe) no se inventa «perdió el 0 inicial»: un solo aviso por operación, «No está el catálogo de NCM…» | rojo antes: el error con 9999999 y 1012100000A |
| De paso | Los mensajes del peso dicen la razón: «no es un número válido» (NaN, infinito), «es negativo», «pasa el tope», «al menos 0.001 kg». En los avisos del Excel, 0,0004 kg no sale «0 kg» | rojo antes: NaN decía «tope» y -1, «no es un número» |

Las pruebas nuevas contra la base (`dd5e851`, la rama con SUBITEMS-1 e
integrada) dan `15 failed, 5 passed` (corrido).

| Puerta (sobre `61cf88f`; después sólo cambian patrones de sabotaje) | Resultado |
|---|---|
| Suite completa, worktree limpio, venv sólo con `requirements.txt` | `1495 passed, 102 skipped, 2 xfailed, 25 warnings in 153.80s`, 0 failed |
| `pantalla_maria5.js`, `pantalla_catalogo_ncm1.js` y `pantalla_subitems1.js` (servidor local en `135ff27`, el mismo producto) | `OK: pantalla MARIA-5`, `OK: pantalla CATALOGO-NCM-1`, `OK: pantalla SUBITEMS-1` |
| Sabotajes | Todos `OK` en `a8a83f3`: MARIA-5 (49), CATALOGO-NCM-1 (16), SUBITEMS-1 (7), MARIA-3 (30), 1d (8), 4 (9), 1c (4), 2b (6), 2 (8) y 1a (10). De la Dev 1: `maria1b.sh` y `punta_a_punta1.sh` con 0 fallas. `excel1.sh`: sigue la del «mapeo guardado», ya informada, que da rojo en otras pruebas. Puse al día los patrones que movió esta vuelta (dos de `maria1b.sh`, uno de `maria1d`, el de la clase «dudosa» en `excel1.sh` y cuatro de MARIA-5) |

No hice autorrevisión con subagente en esta vuelta: son seis puntos chicos y
el contexto está alto. Para que la mires: la regla de la columna «dudosa» es
nueva. Hoy cuentan como de una unidad sólo «Peso», «Weight», «Peso kg» y
«Kg» (con o sin paréntesis), y las que dicen «unit»/«unidad»; cualquier otro
nombre que empiece con «Peso» o contenga «weight» es dudoso.

Para reproducir:
```
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 61cf88f 8890
for s in maria5 catalogo_ncm1 subitems1; do BASE_URL=http://127.0.0.1:8890 node scripts/testing/pantalla_$s.js; done
python -m pytest -q tests/test_devolucion2_maria5_ncm.py tests/test_maria1b_controles.py
```

Última vuelta: 2026-10-07 20:20 UTC
Contexto: ~62 % (a compactar)

---

## SUBITEMS-1 — entregada: **`88564ec`**

**Resultado: terminada. Para decidir: la D27 (guardar los subítems con la
operación).** Base: tu rama hasta `8d87c47` (`db2bc04`), sobre la reentrega
de MARIA-5 y CATALOGO-NCM-1, que está en revisión.

| # | Qué hace | Rojo antes → verde |
|---|---|---|
| 1. Pantalla | En el paso de NCM (`ncm.js`), cada producto no agrupado tiene «Subítems»: un panel para cargar, editar y borrar subítems (cantidad, valor unitario y sufijo de valor). Propone la cantidad que falta y dice en vivo si suman lo del producto («✓ Suman 6 de 6 unidades y 7.182,00 de 7.182,00 de valor»; ⚠ si no). Un producto con subítems no se agrupa. `buildMariaRequest` los manda con el formato de `/generate_maria`. Si todos los productos van en subítems con sufijo propio, el sufijo general no se pide (el servidor tampoco lo pedía) | `pantalla_subitems1.js` contra `db2bc04`: `FALLA: no aparece el botón «Subítems» del producto`; con la pieza, `OK: pantalla SUBITEMS-1` |
| 2. Controles | Generador: cada sub-ítem con cantidad y valor unitario > 0 y la cantidad con hasta dos decimales (el TXT la declara con dos). Un producto agrupado no lleva sub-ítems. `/generate_maria`: el error del sufijo de un sub-ítem dice cuál es, y un pedido con sub-ítems de otra forma da 400. Todos los errores dicen «Item N, sub-ítem M». Antes, una cantidad negativa compensada por otra cerraba la suma y generaba | `tests/test_subitems1.py` contra `db2bc04`: el error no nombraba el sub-ítem, o generaba |
| 3. PUNTA-A-PUNTA-1 | Los subítems llegan por el panel: la prueba los carga como la pantalla y la copia de `buildMariaRequest` los manda. **La D24 sale del `xfail`** | — |

**El archivo real con subítems, por la pantalla.** `pantalla_subitems1.js`
lo carga en el navegador (6 × 1197, 2 + 4 con sus dos sufijos) y genera. Los
dos `[SBT]` salen idénticos a `maria_golden_subitems_anon.TXT`, salvo el
número de operación (D23 y D25 de la Dev 1). `QARTKGRNET=33.000` y
`MARTFOB=7182.00` también coinciden. El archivo entero se compara en
`test_punta_a_punta1.py`, con la copia en Python de la pantalla.

**Autorrevisión (Sonnet alto).** XSS, reordenar filas, «Agregar producto»,
desagrupar, comas y decimales se sostienen. Arreglé lo que encontró (en
`ae6ff5f` y `88564ec`):
- Un subítem de cantidad 0,004 salía `QSBTUNTDCL=0.00` y `MSBTFOB=0.00`, sin
  error.
- Deshacer una acción masiva resucitaba un subítem borrado. Lo comprobé
  levantando una copia sin el arreglo: `FALLA: deshacer la acción masiva
  resucitó el subítem borrado`.
- La suma del panel no seguía a la cantidad del producto.
- Los errores de sufijo no decían qué subítem.
- El sufijo general se pedía igual.
- Enter caía en el panel.
- Unos pedidos fabricados daban 500.

| Puerta | Resultado |
|---|---|
| Suite completa, worktree limpio en `88564ec`, venv sólo con `requirements.txt` | `1475 passed, 102 skipped, 2 xfailed, 25 warnings in 151.49s`, 0 failed |
| `sabotaje_subitems1.sh 88564ec` (7) | `OK: los 7 sabotajes dan rojo por la razón esperada` |
| Sabotajes vecinos en `88564ec` (MARIA-5, MARIA-3, `maria1b.sh` y `punta_a_punta1.sh` de la Dev 1) | `OK: los 44` (MARIA-5) y `OK: los 30` (MARIA-3); `maria1b.sh` y `punta_a_punta1.sh`: `sabotajes con falla: 0` |
| `pantalla_subitems1.js` (local, `ae6ff5f`) | `OK: pantalla SUBITEMS-1`; captura en `docs/pm/capturas/subitems1-panel.png` |

### D27 — Guardar los subítems con la operación

`operation_items` no tiene dónde guardarlos, y `saveOperationToHistory` no
los manda. Lo mismo pasa con el estado de MARIA-4. Hoy no se pierde nada a la
vista: ningún camino de la v2 reabre una operación del historial en la
pantalla. Lo en curso sobrevive a recargar la página (`cdi_v2_state`).

Opciones:
- **(a) Recomiendo:** dejarlo así hasta que exista «reabrir una operación».
  Esa pieza lleva la columna (JSON) y la migración.
- **(b)** Hacerlo ahora: una migración en `operation_items`.

**Riesgos y lo que no hice:**
- La cantidad de un **producto** con más de dos decimales tiene el mismo
  redondeo en `QARTUNTDCL`. Ya pasaba antes y no lo toqué.
- Un campo vacío del panel viaja como 0, y el error dice «la cantidad «0»…».
  Es cosmético.
- Ni el lector de PDF ni el Excel detectan subítems solos: no estaba en el
  alcance.
- No corrido: el Kit del despachante. Nada contra producción ni terceros.

Para reproducir:
```
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 88564ec 8890
BASE_URL=http://127.0.0.1:8890 node scripts/testing/pantalla_subitems1.js   # «OK: pantalla SUBITEMS-1»
scripts/testing/sabotaje_subitems1.sh 88564ec /tmp/cdi-pm/venv              # «OK: los 7 sabotajes …»
python -m pytest -q tests/test_subitems1.py tests/test_punta_a_punta1.py tests/test_maria_subitems.py
```

Última vuelta: 2026-10-07 19:45 UTC
Contexto: ~55 % (a compactar)

---

## MARIA-5 y CATALOGO-NCM-1 — reentrega conjunta sobre tu rama: **`6854f34`**

**Resultado: hecho lo que pide la D23 (`7e263eb`). Para decidir: nada.**
Base: tu rama hasta `ce88c01` integrada, con EXCEL-1, MARIA-1b y
PUNTA-A-PUNTA-1. El detalle de cada pieza está en las dos secciones de abajo
(MARIA-5 en `07fb085`, CATALOGO-NCM-1 y la primera integración en `fd8200a`).
Desde entonces sólo cambiaron pruebas y scripts:

| Lo que pide la D23 | Hecho |
|---|---|
| Choques de `main.py` y `upload.js` con la regla de MARIA-5 | `3134480`: la regla de MARIA-5 manda en el peso; de EXCEL-1 quedan `_mapeo_efectivo` y el `drop`, y de MARIA-1b, sus controles en la validación |
| Pruebas de EXCEL-1 que esperan el neto por unidad | Siete, en `dd88e89`. Ahora citan la respuesta 3 y la D23 (`9d7c8a0`). No toqué las de MARIA-1b |
| `sabotaje_maria3.sh` con MARIA-1b adentro | `ROJO flete_sin_validar: 2 failed, 132 passed`; `OK: los 30 sabotajes dan rojo por la razón esperada`. El sabotaje saca también el flete de `controles_maria.py` |
| Un producto con más de una unidad en `test_punta_a_punta1.py` | `test_dos_productos_reparten_flete_y_seguro_por_su_fob` ahora pide `QARTKGRNET` 700.000 y 260.000 (la máquina chica son 2 unidades con 260 kg la línea). Con el TXT tomando el peso de una unidad da rojo |

| Puerta | Resultado |
|---|---|
| Suite completa, worktree limpio en `9d7c8a0` (`6854f34` sólo cambia un script de sabotaje) | `1459 passed, 102 skipped, 3 xfailed, 25 warnings in 140.04s`, 0 failed |
| Sabotajes de la Dev 1 sobre mi base | `punta_a_punta1.sh`: 0 fallas en `6854f34`. Puse al día tres patrones que movió MARIA-5: el FOB del subítem, el reparto del flete y el FOB total. `maria1b.sh`: 0 fallas. `excel1.sh`: lo de `fd8200a`, abajo |
| Mis sabotajes | en `fd8200a` y `8f151a0`, abajo. Después sólo cambiaron pruebas que pasan |

Última vuelta: 2026-10-07 18:40 UTC
Contexto: ~21 %

---

## CATALOGO-NCM-1 — entregada, con tu rama integrada: **`fd8200a`**

**Resultado: terminada.** También integré tu rama (`9488dd8`, con EXCEL-1 y
MARIA-1b) sobre MARIA-5. **Para decidir: la D23 sigue abierta.** En la
integración apliqué la regla de MARIA-5 en las siete pruebas de EXCEL-1 que
la contradecían, con un archivo real como prueba (abajo). Las D23 a D26 que
contestaste en `f009a07` son de la Dev 1: la numeración se pisó, y la mía es
la de `72e6f23`.

### La pieza

| # | Qué hace | Rojo antes → verde |
|---|---|---|
| 1. Catálogo | Regenerado con el importador desde `docs/pm/datos/arancel_ARCA_07102026.zip`: 10.504 NCM, idéntico fila por fila a `parse_arca_nomenclador` del ZIP. Metadata: `updated_at` 2026-10-07, SHA-256 `0fb407ce…`, `nomenclador_07102026.txt` y un campo nuevo, `obtenido` («Lo bajó Emi… por el chat»). El importador pide `--obtenido` | `tests/test_catalogo_ncm1.py` contra `07fb085`: 16 en rojo, de 16 |
| 2. Bajas | El importador guarda en `ncm_bajas.json` lo que estaba en el catálogo anterior y no en el nuevo: **522** códigos, con su descripción y de qué archivo venían (222 KB). `aviso_de_ncm` dice «la NCM 8517.12.31 se dio de baja en el nomenclador vigente de ARCA (2026-10-07): esa posición ya no existe; buscá la nueva» o «no está en el nomenclador vigente». Sale en la validación como advertencia, sin frenar. En el asistente aparece en la sugerencia del historial o del proveedor (marcada `is-baja`), al escribir una SIM o una partida dada de baja («las posiciones 8517.12… se dieron de baja»), y en el mensaje de `/api/ncm/sugerir` | pantalla contra `7b4f651` (antes de la revisión): `FALLA: escribir 8517.12.31.000X no avisa la baja`; contra `07fb085`: `FALLA: la sugerencia dada de baja no lo dice` |
| 3. `ncm_mercosur.csv` | **Lo saqué.** Sólo se usaba como respaldo cuando faltaba el catálogo, y 11 de sus 22 códigos no existen. Sin el catálogo, ahora el catálogo queda vacío y no se avisa en falso | `test_el_respaldo_con_codigos_viejos_no_se_usa` |

Los dos archivos reales siguen idénticos: 8471.49.00 y 8479.89.99 están en el
vigente. 8517.13.00, 8524 y 8549 están; 8517.12.31 avisa.

**Autorrevisión (Sonnet alto).** El catálogo, las bajas y el importador se
sostienen. Corrió el importador desde el catálogo viejo y salió igual byte a
byte. No hay avisos en falso con SIM completas. Arreglé, en `4d9b7f5` y su
prueba:
- Escribir un código en el asistente no avisaba la baja: la pantalla no
  consultaba al servidor. Ahora pide `GET /api/ncm/aviso`.
- «8517.12» devolvía basura (bulbos de tulipanes): sin prefijo vigente caía
  al ranking por palabras. Un código parcial ahora se busca sólo por prefijo.
- Una sugerencia con una NCM que no está en el vigente (no sólo las bajas)
  no avisaba.

**No lo hice:**
- `/api/ncm/enrich-items`, `/calcular` y `/{ncm}/completo` (la vista previa
  de VUCE) no avisan la baja: no son la sugerencia, y la validación sí avisa.
- La validación ahora carga el catálogo la primera vez en cada proceso
  (~1,6 s y ~70 MB, una sola vez). No lo precargo al arrancar.
- `proyecto_maria/data/ncm_metadata.csv` también tiene códigos viejos y nada
  lo lee. No lo toqué porque no está en la tarea.
- `proyecto_maria/tests/test_ncm_catalog.py` no está en `testpaths`, así que
  la suite no lo corre. Pasa (5 passed). Mis pruebas nuevas están en
  `tests/`.

### La integración de tu rama (`3134480`, pruebas en `dd88e89`)

- **Conflictos** en `main.py` (cuatro) y `upload.js` (uno):
  - Conservé lo de EXCEL-1: `_mapeo_efectivo` y que una columna con el
    nombre del campo salga antes de renombrar.
  - Conservé lo de MARIA-1b: los controles dentro de la validación previa.
  - Del peso, manda la regla de MARIA-5.
  - En `upload.js`, los avisos van en un solo cartel.
- **Regresión mía que apareció al integrar:** `_peso_por_unidad` leía el peso
  con `pd.to_numeric` antes del lector de EXCEL-1, y «1,5» con miles en la
  planilla daba 0. Ahora usa `_numero_factura` con el separador de la
  planilla, y una columna de una unidad queda como vino
  (`test_miles_con_pista_en_la_planilla` pasa).
- **Prueba con el archivo real para la D23.** En `test_excel1_txt.py` y
  `test_punta_a_punta1.py` la factura de subítems trae «Peso Neto» = 33 para
  la línea de 6 unidades. El archivo real declara `QARTKGRNET=33.000`. Con la
  regla de MARIA-5 (neto de la línea ÷ cantidad) el Excel da exactamente el
  archivo real; con la de EXCEL-1 (neto de una unidad) daría 198 kg. En el
  PDF, el Gemini falso pasó de `peso_kg` a `peso_total_linea`, que es lo que
  pide el prompt.
- **Siete pruebas de `test_excel1_lectura.py`** pasan a la regla de tu canal
  (D22 y la devolución de MARIA-5):
  - neto y total, de la línea;
  - el bruto solo, dividido y con aviso;
  - de una unidad > bruto. `«Peso (kg)»` con `«Peso (bruto)»` usa la de una
    unidad y nombra el bruto ignorado; antes quedaba vacío.
  
  Están todas en `dd88e89`. **Si decidís otra cosa en la D23, se revierte ese
  commit** y se cambia la regla en `_clase_de_peso` y `_RANGO_DE_PESO`.
- **Pruebas de MARIA-5** que MARIA-1b ahora frena (sin moneda, incoterm ni
  CUIT): las completé. El vacío escrito de esos tres da «Falta …», y lo
  prueba un caso nuevo.
- **Tope de los importes:** MARIA-1b lo frena antes en el endpoint. Le sumé
  una prueba directa al generador para que su guarda siga cubierta (sabotaje
  16).

| Puerta (sobre `fd8200a`; después de `8f151a0` sólo cambian pruebas y scripts de sabotaje) | Resultado |
|---|---|
| Suite completa, worktree limpio en `fa4ed0b`, venv sólo con `requirements.txt` (`8f151a0` sólo suma dos pruebas, que pasan) | `1454 passed, 102 skipped, 1 xfailed, 25 warnings in 145.68s`, 0 failed |
| `sabotaje_catalogo_ncm1.sh` (14), `sabotaje_maria5.sh` (44) y los de MARIA-3, 1d, 4, 1c, 2b, 2 y 1a; los de la Dev 1 (`sabotajes/excel1.sh`, `maria1b.sh`, `punta_a_punta1.sh`) | Míos, todos `OK`: CATALOGO-NCM-1 (14, en `fd8200a`), MARIA-5 (44, en `8f151a0`), MARIA-3 (30), 1d (8), 4 (9), 1c (4), 2b (6), 2 (8), 1a (10). De la Dev 1: `maria1b.sh` con 0 fallas y `punta_a_punta1.sh` con 0 fallas. Para el segundo puse al día el patrón del FOB del subítem, que movió MARIA-5. En `excel1.sh`, en `fd8200a`, queda una: «el mapeo guardado vuelve a dejar afuera lo detectado» da rojo, pero en otras pruebas. Pasa porque el peso ahora se elige aparte del mapeo y la cantidad «Qty» la encuentra el lector igual. Dos sabotajes del peso de ese script, que la regla de MARIA-5 dejó viejos, apuntan ahora a `_clase_de_peso` y `_RANGO_DE_PESO`, y dan rojo |
| `pantalla_catalogo_ncm1.js` (local, `4d9b7f5`) | `OK: pantalla CATALOGO-NCM-1`; captura en `docs/pm/capturas/catalogo-ncm1-baja.png` |
| `pantalla_maria5.js` y `smoke_friccion.sh` (local, `7b4f651`) | `OK: pantalla MARIA-5` y `==> OK · telemetría…` |

No corrido: Gemini real, VUCE y Tarifar reales, el Kit. Nada contra
producción ni terceros.

Para reproducir:
```
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh fd8200a 8890
BASE_URL=http://127.0.0.1:8890 node scripts/testing/pantalla_catalogo_ncm1.js   # «OK: pantalla CATALOGO-NCM-1»
scripts/testing/sabotaje_catalogo_ncm1.sh fd8200a /tmp/cdi-pm/venv              # «OK: los 14 sabotajes …»
python -m pytest -q tests/test_catalogo_ncm1.py tests/test_excel1_lectura.py tests/test_maria5_*.py
```

Última vuelta: 2026-10-07 18:15 UTC
Contexto: ~20 %

---

## MARIA-5 — reentrega con la devolución: **`07fb085`**

**Resultado: los seis puntos, con rojo antes y verde después. Para decidir:
la D23. MARIA-5 y EXCEL-1 (Dev 1) dicen lo contrario sobre «Peso neto», y
además chocan en `main.py` y `upload.js`.** Base: `c3f79f8`, más tu
`453cb01` integrado. Los dos archivos reales salen idénticos: sus pruebas
están en la suite.

| # | Qué hace ahora | Rojo antes → verde |
|---|---|---|
| 1. Dos pesos | **Lector:** si viene el de la línea, manda: se divide por la cantidad. Si además viene el de una unidad y no da el de la línea (tolerancia: 1 % o 0,001 kg), un aviso muestra los dos números («25 kg por unidad (× 10 = 250 kg) y 25 kg la línea; se usó el de la línea»). El aviso llega a la pantalla (`avisos` de `/upload_pdf/public`, en el mismo cartel de «Revisá la factura»). (25, 25) con 10 unidades da `QARTKGRNET=25.000`. **Excel:** orden neto > total > de una unidad > bruto, aunque el mapeo guardado diga otra. El aviso nombra la columna usada y las ignoradas y, si el de una unidad × cantidad no da el de la línea, muestra los dos números. El mapeo que se aprende es el de la columna que manda | `test_maria5_devolucion.py`, secciones 1 |
| 2. Peso en texto | En cualquier columna de peso queda vacío, con aviso; la fila se conserva. También «inf» (antes: 500) | sección 2 y revisión |
| 3. Guarda del peso | `peso_valido` en el `[ART]`: no finito, sobre 10¹² o que redondea a 0,000 → 400 con mensaje propio. Un peso en 0 ya daba 400 por el control del Kit; ahora también el generador lo rechaza (en `test_generar_maria_txt.py`, 8 productos sin peso pasan a llevar 1 kg) | sección 3 |
| 4. Subítems | Exacto con exacto: la suma sin redondear contra el valor del ítem sin redondear. Tu caso (7 × 2,675) genera 18,73. Lote al azar con el criterio de `8e819dd` (3 × 1500): todo lo que pasaba genera | sección 4 |
| 5. Grupo | Una cantidad menor que la cantidad de productos se rechaza con el mismo cartel («…al menos uno por producto»). Si alcanza, el producto que queda en 0 toma una unidad del que más tiene. 1/1/100 bajado a 5 da 1/1/3 | `pantalla_maria5.js` contra `c3f79f8`: `FALLA: 1/1/1 bajado a 2 quedó […{"c":0…}]`; con la pieza, OK |
| 6. Una sola cuenta | `fob_total_del_txt`: un grupo es una línea y se redondea una vez. La validación lo usa (la pantalla manda `grupo_id`). El aviso «Gastos a FOB» suma flete y seguro al centavo, como el TXT | sección 6; pantalla contra `c3f79f8`: `FALLA: la validación muestra $620,04 y el TXT 620.03`; con la pieza, `$620,03 = 620.03` |

Las pruebas nuevas contra la base `c3f79f8` dan `43 failed, 17 passed`.

**Autorrevisión (Sonnet alto).** No encontró nada grave. Corrí 8000 pedidos
al azar contra `c3f79f8` y salieron idénticos, salvo los subítems del punto 4
y los pesos en 0. En 4000 pedidos, la validación coincide con `MDDTFOB`.
Arreglé lo que encontró, en `1179dfc` y `07fb085`:
- «Peso neto unitario» y «Net weight per unit» no se reconocían. Con un bruto
  al lado, el TXT declaraba el bruto con un aviso falso. Ahora cuenta como
  peso cualquier columna «Peso…» o «…weight…», pero no «Pesos», la moneda.
  Esto también resuelve el riesgo de «Peso total (kg)» que te informé.
- Un «inf» escrito daba 500.
- Entre dos columnas de una unidad, el resultado dependía del orden de las
  columnas. Ahora va primero la que dice neto y después la del mapeo guardado.
- El aviso decía «peso_unitario (ignorada)».
- Un peso enorme daba el mensaje equivocado.

**Mensaje de la Dev 1 por `sabotaje_maria3.sh`.** `flete_sin_validar` ahora
saca también el flete de `_IMPORTES_DE_LA_CABECERA`
(`core/controles_maria.py`), si ese archivo está. En mi rama todavía no
está, así que no lo corrí con MARIA-1b integrada: ver la D23.

| Puerta | Resultado |
|---|---|
| Suite completa, worktree limpio en `1179dfc`, venv **sólo con `requirements.txt`** (`07fb085` sólo cambia la columna de una prueba, que pasa) | `1259 passed, 102 skipped, 25 warnings in 77.96s`, 0 failed |
| `sabotaje_maria5.sh 07fb085` (44) | `OK: los 44 sabotajes dan rojo por la razón esperada`. En `1179dfc`, `pesos_moneda` quedó verde: la prueba no distinguía el defecto y la corregí en `07fb085` |
| `sabotaje_maria3` / `1d` / `4` / `1c` / `2b` / `2` / `1a` en `07fb085` | `OK: los 30` / `8` / `9` / `4` / `6` / `8` / `10` |
| `pantalla_maria5.js` (servidor local en `07fb085`) | `OK: pantalla MARIA-5`; captura en `docs/pm/capturas/maria5-validacion.png` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |

### D23 — «Peso neto» por unidad (EXCEL-1) o de la línea (MARIA-5)

Probé `merge` de `origin/claude/dev1-tecnica` sobre `f9f80c1`, en un
worktree aparte, y lo deshice: no subí nada. Hay conflictos en
`proyecto_maria/main.py` (cuatro bloques: `smart_validation`, la lista de
alias del peso, `_peso_por_unidad` contra `_mapeo_efectivo`, y
`upload_excel_v2`) y en `static/v2/screens/upload.js` (el cartel final).

Lo de fondo: EXCEL-1 pone `pesoneto` y `netweight` entre los nombres **de
una unidad**. Además saca «Peso total» y el bruto («sin una de estas
columnas, el peso queda vacío»). Tu regla de MARIA-5 es la contraria: neto
> total > de una unidad > bruto, y el neto es de la línea. Con «Peso neto»
= 25 y 10 unidades, EXCEL-1 declara 250 kg y MARIA-5 declara 25 kg.
- **Recomiendo** la de MARIA-5, que es la que pediste y la que dice la
  respuesta 3 del despachante. Quien integre segunda resuelve los conflictos
  con esa regla: las dos piezas tienen pruebas que van a marcar el lado
  equivocado. Si preferís, la resuelvo yo cuando EXCEL-1 esté en tu rama.

**Riesgos y lo que no hice:**
- La tolerancia entre los dos pesos (1 % o 0,001 kg) sólo decide si hay
  aviso. El número que sale es siempre el de la línea.
- «2,5» escrito como texto en el Excel no se interpreta: queda vacío con
  aviso. No adiviné la coma decimal.
- La v1 (`extract_items_from_excel` por `/upload_excel/`) sigue sacando una
  fila con un peso en texto. No la toqué: no es la pantalla v2 y diverge
  igual (`DECISIONS.md`).
- No corrido: el Kit del despachante, Gemini real y planillas reales de
  clientes. Nada contra producción ni terceros.

Para reproducir:
```
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 07fb085 8890
BASE_URL=http://127.0.0.1:8890 node scripts/testing/pantalla_maria5.js   # «OK: pantalla MARIA-5»
VENV=/tmp/cdi-pm/venv scripts/testing/sabotaje_maria5.sh 07fb085          # «OK: los 44 sabotajes …»
python -m pytest -q tests/test_maria5_*.py                                # todo passed
```

Última vuelta: 2026-10-07 15:40 UTC
Contexto: ~9 %

---

## MARIA-5 — entregada: **`6d59893`**

**Resultado: terminada, con la D22 (a) y el punto 4. Para decidir: nada
nuevo; dos riesgos abajo para que los mires (el «Peso neto» de un cliente que
era por unidad y el redondeo del grupo).** Base: mi rama con MARIA-1d y tu
rama integrada (`8e819dd`, con pypdf). Los dos archivos reales salen
idénticos.

| Punto | Qué hace ahora | Prueba | Rojo antes → verde |
|---|---|---|---|
| 1. Peso (M1) | `QARTKGRNET` = peso neto de la línea: `peso_kg` si viene (ya es total: v1 y archivos reales), si no `peso_unitario` × cantidad (v2). Los grupos suman el total de cada línea. 10 × 2,5 kg = **25 kg** | respuesta 3; real de 2026 (6 u, 33 kg) sin cambios | `test_maria5_peso.py`: 10 failed → passed (la del grupo de `test_generar_maria_txt` pasa de 4 a 8 kg, citando la respuesta 3) |
| D22 lector | Las dos copias piden `peso_unitario` y `peso_total_linea`; si viene sólo el total, se divide por la cantidad. `peso_kg` viejo se lee como unitario | — | `test_maria5_peso_lector.py`: 15 failed, 2 passed → 17 passed |
| D22 Excel (sólo el mapeo del peso) | «Peso total», «Peso neto» (y variantes con total/neto/net/línea, también en un mapeo guardado del cliente) se dividen por la cantidad; «Peso»/«Weight», de una unidad. El bruto queda último y, si es la única columna, se usa dividido **con aviso**. Un peso que no es número se avisa. La pantalla muestra los avisos | — | `test_maria5_peso_excel.py`: 6 failed → passed; lo de la 2.ª revisión, 6 failed → passed |
| 2. Centavos (M9) | Importes al centavo, mitad hacia arriba, sobre el número escrito; cantidad × unitario en decimal exacto (3 × 3,335 = 10,01). Flete y seguro por resto mayor: la suma de los ítems da **exactamente** la carátula (FOB 100/100/400 con flete 10: 1,67 + 1,66 + 6,67 = **10,00**; antes 10,01). `MDDTFOB` = Σ `MARTFOB`; base = FOB + flete + seguro; `MSBTFOB` reparte el `MARTFOB` (misma tolerancia de antes). NaN, infinito, negativo o > 10¹² → 400 (antes `MARTFOB=nan` o 500). La validación muestra el mismo FOB | Kit: no corrido (no tengo el Kit); real de 2025 y 2026 idénticos | `test_maria5_centavos.py`: 36 failed → passed; lo de la 1.ª revisión, 10 failed → passed |
| 3a. Carátula «None» | En `MariaRequest`, un campo de texto entero «None», «null», «N/A» o nulo es vacío: sale el aviso de carátula y no llega al TXT ni al archivo; sin número, `IDSO` y el archivo usan `OP_<fecha>`. La pantalla no arma `FAC_None` ni muestra «None» en el resumen | — | `test_maria5_caratula_vacia.py`: 8 failed → passed |
| 3b. Lector PDF directo | Descripción, versión y código de parte con la misma función que PyMuPDF (`_texto_del_producto`) | — | `test_maria5_lector_productos.py`: 10 failed → passed |
| 4. Grupos en la pantalla | Editar la cantidad del grupo la reparte en enteros (resto mayor); el valor y el peso promedio escalan los de cada producto. Se aplica al salir del campo; pasar sin cambiar no toca nada; 0, negativo o vacío se rechazan (vuelve lo que estaba); después se redibuja. Debajo del peso unitario, el de la línea | pantalla | `pantalla_maria5.js` contra `57bb17e`: `FALLA: la cantidad del grupo quedó [{"c":6,…},{"c":6,…}]`; contra `aa7d9a3`: `FALLA: pasar por el grupo sin editar cambió los productos`; con la pieza: `OK: pantalla MARIA-5` |

Las pruebas nuevas contra la base `9679e21` (los cuatro primeros archivos):
`64 failed, 25 passed`.

| Puerta (sobre `6661dbf`, mismas pruebas y producto que `6d59893`, cuyo último commit sólo arregla patrones de sabotajes; el producto es el de `4c2231c`) | Resultado |
|---|---|
| Suite completa, worktree limpio, venv **sólo con `requirements.txt`** (sin PyPDF2) | `1199 passed, 102 skipped, 25 warnings in 75.30s`, 0 failed |
| `sabotaje_maria5.sh` (23) | `OK: los 23 sabotajes dan rojo por la razón esperada` (con los patrones de `6d59893`) |
| `sabotaje_maria3` / `1d` / `4` / `1c` / `2b` / `2` / `1a` | `OK: los 30` / `8` / `9` / `4` / `6` / `8` / `10` (el de 1a con los patrones de `6d59893`: el peso y el prompt se movieron a `_peso_del_producto`) |
| `pantalla_maria5.js` (servidor local en `4c2231c`) | `OK: pantalla MARIA-5` (captura `docs/pm/capturas/maria5-validacion.png`) |
| `pantalla_maria3.js` | `OK: pantalla MARIA-3` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| Autorrevisión | dos adversarios Sonnet alto; lo que encontraron está arreglado (arriba) salvo lo de «Riesgos» |

**Riesgos y lo que no hice:**
- **«Peso neto» de un cliente que era por unidad:** con la D22 se divide por
  la cantidad; si un cliente tenía guardada una columna «Peso neto» que en
  su planilla era por unidad, ahora baja a 1/cantidad (con el aviso «es de
  toda la línea; se dividió»). No lo probé con una planilla real.
- **Grupo:** al cambiar la cantidad, cada producto conserva su precio, así
  que el promedio que se ve después cambia (la fila se redibuja con lo
  guardado); en un empate, la unidad extra va al primero.
- Excel: «Peso total (kg)» (con paréntesis) no se detecta sin mapeo, como
  pasaba con «Peso (kg)»: la normalización de encabezados es de todas las
  columnas y no la toqué.
- Lector: si la cantidad viene en 0, el peso de la línea no se puede
  dividir y queda en 0 (el semáforo marca la cantidad).
- Sin chequeo cruzado si Gemini copia el mismo número en los dos pesos.
- Un ítem con FOB 0,00 y flete: el flete de la carátula no se reparte (ya
  pasaba; la validación rechaza valor 0).
- `moneda` o `incoterm` «None» salen como línea vacía en el TXT, con aviso
  (lo de DOL/FOB por defecto es de MARIA-1b).
- El 0,5 inventado al guardar: lo saca MARIA-1b; al integrar hay que
  resolver ese pedazo de `main.py`.
- No corrido: el Kit del despachante; nada contra producción ni terceros.

Para reproducir:
```
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 6d59893 8890
BASE_URL=http://127.0.0.1:8890 node scripts/testing/pantalla_maria5.js   # termina en «OK: pantalla MARIA-5»
VENV=/tmp/cdi-pm/venv scripts/testing/sabotaje_maria5.sh 6d59893          # «OK: los 23 sabotajes …»
python -m pytest -q tests/test_maria5_*.py                                # todo passed
```

Última vuelta: 2026-10-07 13:45 UTC
Contexto: ~40 % (pasado el umbral: compactar en este corte)

---

## MARIA-1d — reentrega con el punto sumado: **`9679e21`**

**Resultado: terminada. No hay nada para decidir.** La entrega de MARIA-1d
(más abajo, sobre `c60dc3a`) sigue valiendo, y la rama incluye MARIA-3
aceptada.

| Punto sumado | Qué hice | Rojo antes → verde |
|---|---|---|
| Procedencia rara en un producto (`²`, `99999`, `٢٢٢`, «Narnia», en `pais_procedencia` o `procedencia`) | Una sola función, `errores_de_procedencia`, arma el texto. Al generar es el error 400 de siempre; en `/generate_maria/avisos` aparece el mismo texto, primero en la lista | `test_procedencia_rara_de_un_producto_avisa_igual_antes_y_al_generar`: `8 failed` → `8 passed` |

| Puerta (sobre `8a036bf`, mismo producto y pruebas que `9679e21`; el último commit sólo arregla el patrón de un sabotaje) | Resultado |
|---|---|
| Suite completa, worktree limpio | `1029 passed, 102 skipped, 25 warnings in 64.36s`, 0 failed |
| `sabotaje_maria1d.sh` | `OK: los 8 sabotajes dan rojo por la razón esperada` (el 8 es el punto sumado) |
| `sabotaje_maria3` / `4` / `1c` / `2b` / `2` / `1a` | `OK: los 30 …` (sobre `9679e21`) / `9` / `4` / `6` / `8` / `10` |
| `pantalla_maria3.js` | `OK: pantalla MARIA-3` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |

Última vuelta: 2026-10-07 11:30 UTC
Contexto: ~63 % (pasado el umbral: compactar en este corte)

---

## MARIA-3 — reentrega con la devolución: **`0d6cb3e`**

**Resultado: los cinco puntos, cada uno con su rojo antes y verde después. No
hay nada para decidir.** Producto: `0144d4e` y `0e41311` (este último, de la
revisión de la devolución). El resto son pruebas, sabotajes y la captura.
MARIA-1d (abajo) sigue entregada sobre `c60dc3a` y está incluida en esta rama.

| Punto | Qué hice | Rojo antes → verde |
|---|---|---|
| 1. Una sola tabla | La tabla oficial es **`proyecto_maria/static/v2/paises_maria.js`**: los 309 países de `TABLA PAISES V.0 25082010.xlsx` (tabla oficial VUCE, según `HANDOFF.md` y la nota del archivo). El servidor lee ese mismo archivo (`codigos_tabla_oficial()`), así que no hay copia. La regla está en la raíz (`pais_reconocido` y `get_pais_codigo`): sólo cifras 0-9 y un código de la tabla. Vale para la procedencia de la operación, la de cada producto y el origen | `test_la_procedencia_acepta_todos_los_paises_de_la_pantalla`: failed → los 309 pasan; 668, 436, 435, 223, 150, 242, 254 y 358 salen en `CARTPAYPRC` |
| 2. Año del `IEXT` | Sin una fecha de emisión válida no se genera: 400 «Falta la fecha de emisión de la factura (DD/MM/AAAA)…». El año del IEXT sale de esa fecha. La revisión marca la fecha como requerida y no deja seguir sin ella. Los avisos previos dicen «sin una fecha válida no se genera el TXT» | `test_sin_fecha_valida_no_se_genera` (12 casos, incluidos `Fecha 18/07/2025` y `18/07/٢٥`); pantalla contra `088577f`: `FALLA: la fecha de emisión no figura como requerida en la revisión` |
| 3. Fechas equivocadas | DD/MM/AA es 20AA (`01/01/69` → `01/01/2069`). Una fecha futura o de hace más de dos años se avisa antes de generar. La revisión valida fechas reales (rechaza `31/02/2026`) con las mismas reglas que el servidor | `test_la_fecha_de_la_factura_sale_en_el_txt[01/01/69-01/01/2069]`, `test_fecha_futura_o_vieja_se_avisa`; pantalla: `OK la revisión pide la fecha y rechaza el 31/02/2026` |
| 4. Procedencia rara | `²`, `٢٢٢` o `2²2`: 400 «Procedencia «²» no reconocida: elegí un país de la lista.» en `/generate_maria` y en `/avisos`, nunca el texto de Python. En un producto da «Item N: Procedencia no reconocida». Una procedencia de producto en blanco no pisa la de la operación ni tapa la otra clave | `test_procedencia_no_reconocida_se_rechaza` (12), `test_codigo_raro_en_el_producto…` (6), `…en_blanco…` (2) |
| 5. Gastos | Un importe no finito, negativo o de más de un billón da 400 «Gastos (…): … no es un importe válido», por `gastos_anteriores_fob`, por `gastos_fob` y en el generador. **También el flete y el seguro**: con C y D los gastos salen de flete + seguro, y un `flete=inf` llegaba a `GTOS-POS-FOB=inf` | `test_gastos_que_no_son_un_importe_dan_400` (20), `test_el_generador_tampoco…` (5), `test_flete_o_seguro…` (8) |

Contra `088577f`, las pruebas nuevas dan `75 failed, 59 passed`.

**Pruebas viejas que cambié**, porque fijaban lo que la devolución pide quitar:
- `test_maria_iext_anio.py`: «sin fecha usa el año actual» y «fecha rara cae
  al año actual» pasan a «no se genera».
- `test_generar_maria_txt.py`, `test_prelaunch_block1.py` y MARIA-1d generaban
  sin fecha: ahora la llevan.

| Puerta (sobre `0d6cb3e`, worktree limpio) | Resultado |
|---|---|
| Suite completa | `1021 passed, 102 skipped, 25 warnings in 61.34s`, 0 failed |
| `sabotaje_maria3.sh` | `OK: los 30 sabotajes dan rojo por la razón esperada` (27 a 30 son los de la devolución) |
| `sabotaje_maria1d` / `4` / `1c` / `2b` / `2` / `1a` | `OK: los 7 …` / `9` / `4` / `6` / `8` / `10` |
| `pantalla_maria3.js` | 7 líneas `OK` y `OK: pantalla MARIA-3` |
| `pantalla_maria4.js` / `pantalla_maria1c.js` | `OK: pantalla MARIA-4` / `OK: pantalla MARIA-1c` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| Captura | `docs/pm/capturas/maria3-avisos.png` |

**Autorrevisión** con `/code-review high` sobre la devolución. Lo que arreglé
de ahí:
- el flete y el seguro;
- la regla de los códigos en la raíz (un producto con `99999` o `²` también
  pasaba);
- una procedencia en blanco que tapaba la otra clave;
- la fecha real en la revisión;
- el tope de gastos, que subí a un billón por las monedas de poco valor;
- el aviso de fecha aunque no haya productos;
- comentarios viejos.

**Riesgos que quedan:**
- La fecha d/m contra m/d ambigua (`03/04/2026`): queda anotada, como pediste.
- El servidor lee la tabla de países de un archivo de la pantalla. Si alguien
  le cambia el formato, el error dice cuál archivo es, y una prueba verifica
  los 309 códigos.
- Con la fecha obligatoria, la pantalla vieja (v1) recibe el 400 si no la
  carga. La v1 tiene la fecha como texto libre.

Última vuelta: 2026-10-07 12:10 UTC
Contexto: ~60 % (pasado el umbral: compactar en este corte)

---

## MARIA-1d — entregada: **`c60dc3a`**

**Resultado: terminada. No hay nada para decidir.** Base `8770925`
(MARIA-3 entregada más tu rama). Producto: `5faecad`, `83a0860`. El resto son
pruebas y sabotajes.

| Qué | Ahora | Rojo antes → verde |
|---|---|---|
| Campos nulos | En las dos copias del lector, el número de factura, el vendedor (nombre, identificador y dirección), el comprador, el domicilio, la fecha, la moneda y el incoterm quedan `""`, sin «None» ni «NON» | contra `8770925`: `26 failed, 3 passed` (por ejemplo `numero_factura = 'None'` y `moneda = 'NON'`) |
| Moneda e incoterm ausentes | El lector no inventa `DOL` ni `FOB`. La revisión ya los exige | `assert 'DOL' == ''` → passed |
| El vacío escrito como texto | «None», «null» o «N/A» (sin importar mayúsculas ni espacios) cuentan como vacío | 10 failed → passed (casos de la revisión) |
| Una descripción que no es texto | En la copia PyMuPDF el producto se descartaba en silencio (`'int' object is not subscriptable`); ahora llega | failed → passed |
| Prompt | Ya no dice «Ante duda, DOL»: si no hay palabra ni símbolo de moneda, `null` | prueba sobre el código; **no corrido con el Gemini real** |
| Avisos de la carátula | Antes de generar (y al generar) se avisa qué falta: vendedor, nombre o CUIT del importador, moneda o incoterm, con la línea del TXT que queda vacía o no sale | failed → passed |
| «None» en todo el TXT | Una factura con todos los campos nulos pasa por el lector (las dos copias) y por `/generate_maria`, con el pedido armado como la pantalla y los productos leídos: ni «None», ni «NON», ni «null» en el TXT ni en el nombre del archivo | antes: `«None» en el TXT` |

| Puerta | Resultado |
|---|---|
| Suite completa sobre `83a0860` (mismo producto y pruebas que `c60dc3a`; el último commit sólo toca un sabotaje) | `951 passed, 102 skipped, 25 warnings in 60.93s`, 0 failed |
| `tests/test_maria1d_campos_vacios.py` | `40 passed` |
| `sabotaje_maria1d.sh` | `OK: los 7 sabotajes dan rojo por la razón esperada` |
| `sabotaje_maria3` / `4` / `1c` / `2b` / `2` / `1a` | `OK: los 20 …` (el patrón de la fecha, al día) / `9` / `4` / `6` / `8` / `10` |
| Archivos reales | `test_golden_reproduce_estructura_real` y el de 2025 por el endpoint, dentro de la suite: idénticos |
| `pantalla_maria3.js` / `pantalla_maria4.js` | `OK: pantalla MARIA-3` / `OK: pantalla MARIA-4` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |

**Autorrevisión** con `/code-review high`. Los cuatro arreglos de la tabla
(vacío escrito como texto, descripción no textual, prompt y prueba con los
productos leídos) salieron de ahí.

**Riesgos que quedan** (fuera de la pieza):
- La pantalla vieja (v1) sigue poniendo `DOL` y `FOB` cuando están vacíos,
  sin avisar. Es el mismo caso que D11.
- La v2 también tiene ese relleno en `finalize.js`, pero la revisión no deja
  seguir sin moneda ni incoterm, así que en la práctica no se usa. Por eso el
  aviso de moneda o incoterm vacíos sólo salta si alguien llama a la API sin
  ellos.
- Un CUIT presente pero mal formado no se avisa: sólo se avisa el vacío.
- Las dos copias del lector siguen duplicadas: cada arreglo se hace dos veces.

## No corrido

- El prompt nuevo con el Gemini real.

Última vuelta: 2026-10-07 10:40 UTC
Contexto: ~48 %

---

## MARIA-3 — entregada: **`088577f`**

**Resultado: terminada, con una D (D12) que no frena.** Base `06e4ac3`
(MARIA-4 aceptada). Producto: `341a429`, `1b1a95a`, `1e915f2`. El resto son
pruebas, sabotajes y la captura.

Lo que cambia en el TXT, punto por punto:

| Punto | Ahora | Prueba | Rojo antes → verde |
|---|---|---|---|
| Avisos antes de generar (M6) | `POST /generate_maria/avisos` devuelve los mismos avisos que `/generate_maria`, sin generar ni guardar. En validación, el panel «Revisá antes de generar» va arriba del botón y se actualiza al cambiar la tarjeta del despachante | pantalla | `pantalla_maria3.js` contra `06e4ac3`: `FALLA: no aparece el campo de procedencia`; con la pieza: `OK: pantalla MARIA-3` |
| Gastos anteriores al FOB (M8) | El campo de la pantalla va a `GTOS-ANT-FOB` con EXW, FCA o FAS, y sólo si es más de 0. Con otra condición no va y se avisa. Vacío o 0 con EXW, FCA o FAS: no sale y se avisa. FAS entra en `INCOTERMS_VALIDOS`. El `gastos_fob` explícito sigue mandando, como antes | respuesta 6; nota del SIM; el archivo real de 2026: los 150 cargados en la pantalla salen igual que en el real, y los bloques de productos también | antes: `assert [] == ['150.00']` |
| Procedencia | Campo por operación en la revisión, con la lista de países. Va a cada producto que no trae la suya. Si no se reconoce, o es un número que no está en la tabla, da 400. Vacía: igual al origen, con aviso, como antes | art. 15 del CA; el archivo real de 2025 sale **entero idéntico** por `/generate_maria` cargando la procedencia «PE» por operación | antes: 404 en el endpoint y procedencia sin aplicar |
| Fecha de emisión | La de la factura en DD/MM/AAAA. Se aceptan también d/m/AAAA, DD/MM/AA y AAAA-MM-DD, y se normalizan al formato de los archivos reales. Si no hay fecha o no se puede leer, `FECHAEMISIONFACT` sale **vacía** y se avisa. El año del IEXT se sigue leyendo de lo escrito | D15 | antes: `assert ['07/10/2026'] == ['']`: salía la fecha de hoy |
| Sin avisos de más | Flete o seguro «N/A», «NA», «-», «FREE», «included», «Prepaid» (con o sin punto, sin importar mayúsculas), y país «Unknown», «?», «N/A»: no se marcan como sin leer. «N/A 30» o «Unknown land» sí se marcan. Una fecha que no vino queda `""` (antes `"None"`) | — | 16 failed → passed, en las dos copias del lector |

Contra `06e4ac3`, las pruebas nuevas dan `44 failed, 9 passed`. Los 9 que
pasan son resguardos de lo que ya andaba.

| Puerta (worktree limpio) | Resultado |
|---|---|
| Suite completa sobre `fa4b096` (mismo producto y pruebas que `088577f`; el último commit sólo toca scripts y la captura) | `911 passed, 102 skipped, 25 warnings in 62.36s`, 0 failed |
| `tests/test_maria3_antes_de_generar.py` | `65 passed` |
| `sabotaje_maria3.sh` | `OK: los 20 sabotajes dan rojo por la razón esperada` |
| `sabotaje_maria4` / `1c` / `2b` / `2` / `1a` | `OK: los 9 …` / `OK: los 4 …` (patrón puesto al día) / `OK: los 6 …` / `OK: los 8 …` / `OK: los 10 …` |
| `pantalla_maria3.js` | 5 líneas `OK` y `OK: pantalla MARIA-3`. Incluye la respuesta de avisos demorada: contra `a3f2df9` daba `FALLA: mientras llega la respuesta se ven los avisos de la operación anterior` |
| `pantalla_maria4.js` / `pantalla_maria1c.js` | `OK: pantalla MARIA-4` / `OK: pantalla MARIA-1c` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| Captura | `docs/pm/capturas/maria3-avisos.png` |

**Autorrevisión** (`/code-review high` y un adversario Sonnet alto, que
comparó los avisos previos con los de generar en 1512 combinaciones: 0
diferencias). Arreglado, cada uno con su prueba y su sabotaje:
- con una fecha no aceptada, el año del IEXT pasaba al de hoy;
- «1/7/2025» quedaba vacía;
- una procedencia numérica fuera de la tabla («99999») llegaba al TXT;
- gastos infinitos o de menos de un centavo se declaraban (`MCPL=inf`, `0.00`);
- un año 0026 salía como `05/03/26`;
- al entrar a validar con otra operación, el panel mostraba un momento los
  avisos de la anterior.

**Supuestos que podés rechazar:**
- Sin fecha, la línea `FECHAEMISIONFACT` sale con el valor vacío; no se
  omite. Así leí «vacía».
- Un 0 en gastos anteriores no se declara: el campo de la pantalla vale 0
  cuando está vacío.
- Una fecha DD/MM/AA se escribe con cuatro cifras, como en los archivos reales.

**Riesgos que quedan:**
- «included» o «Prepaid» en un CIF deja el flete en 0 sin aviso. Lo pediste
  así, pero en ese caso el flete viene dentro del precio.
- El campo de gastos es numérico: en Chromium, «1,5» queda 15. Es lo que se
  ve en el campo, pero no lo probé con un Chrome real en es-AR.
- La lista de países de la pantalla trae alias que no son países, por ejemplo
  «Islas» → 150 Cabo Verde o «Córdoba» → 256 ZF Córdoba. Es la tabla de
  MARIA-4, y la procedencia los acepta.
- Los avisos previos no incluyen los errores que bloquean (SBT, NCM). Esos
  siguen saliendo al generar o en la tarjeta del despachante.
- Sin fecha, el año del IEXT es el de hoy. Los identificadores son MARIA-6.
- La pantalla vieja (v1) recibe los avisos nuevos (gastos, procedencia), pero
  no tiene esos campos.

## Decisiones

**D12. El lector escribe «None» en los demás campos que Gemini devuelve
vacíos.** Lo encontró el revisor: número de factura, vendedor, comprador,
domicilio, y «NON» en moneda e incoterm. Llegan al TXT, por ejemplo
`IDSO=FAC_None` y `CDDTINCOTE=NON`. Es el mismo defecto que arreglé sólo en la
fecha, que era la que pedía MARIA-3.
- (a) Pieza chica aparte: `str(x or "")` en las dos copias, con la moneda y el
  incoterm vacíos en vez de «NON». **Recomiendo (a), antes de MARIA-5.**
- (b) Sumarlo a MARIA-5.

No me frena: sigo con MARIA-5 cuando la escribas.

## Para reproducir

```bash
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 088577f 8080
<venv>/bin/python -m pytest -q --no-cov tests/test_maria3_antes_de_generar.py tests/test_generar_maria_txt.py tests/test_maria_subitems.py tests/test_maria4_despachante.py   # 174 passed
BASE_URL=http://127.0.0.1:8080 node scripts/testing/pantalla_maria3.js     # «OK: pantalla MARIA-3»
VENV=<venv> scripts/testing/sabotaje_maria3.sh 088577f                      # «OK: los 20 …»
```

## No corrido

- La procedencia y la fecha en el Kit real.
- El campo de gastos con un Chrome real en español.

Última vuelta: 2026-10-07 09:30 UTC
Contexto: ~40 %

---

## MARIA-4 — reentrega con la devolución: **`2461939`**

Producto `dbf8848`; pruebas y sabotajes `dbf8848`…`2461939`. La entrega
anterior (`6149ef3`, abajo) sigue valiendo para todo lo demás.

| Punto devuelto | Qué hice | Rojo antes → verde |
|---|---|---|
| 1. Estado contra origen | El generador rechaza un estado argentino (1, 3, 5) con origen extranjero y uno importado (2, 4, 6) con origen argentino: 400 «Ítem N (descripción): el estado «…» no corresponde al origen (…); elegí otro.». Los nombres y la regla están en un solo lugar, `ESTADOS_ARGENTINOS` / `ESTADOS_IMPORTADOS`. En la pantalla, cada producto ofrece sólo los estados de su origen, y el estado elegido queda atado a la clase de origen: si el origen cambia, se borra y se vuelve a pedir | `test_estado_que_no_corresponde_al_origen_se_rechaza`: 7 failed → passed. Pantalla contra `6149ef3`: `FALLA: al pasar a origen extranjero queda el estado argentino elegido antes`; con `2461939`: `OK al cambiar el origen el estado elegido se vuelve a pedir y sólo se ofrecen los que corresponden` |
| 2. La pantalla vieja muestra los avisos | Después de generar, `static/app.js` muestra los `warnings` y los `supuestos` de `/generate_maria` en un `alert` («Revisá antes de pegar el TXT en el Kit»), antes de bajar el archivo | `test_la_pantalla_vieja_muestra_los_avisos_de_generate_maria`: failed → passed. Es una prueba sobre el código: no corrí la v1 en el navegador |
| 3. `origen` y `pais_origen` | Los supuestos leen `pais_origen` primero, como el generador, en sus dos lugares | `test_supuestos_leen_el_origen_como_el_generador`: failed → passed |

Tuve que corregir dos pruebas que usaban combinaciones que ahora no valen.
Una pedía estado 5 con origen chino: la pasé a 6. La otra probaba un grupo
con estados distintos usando 2 y 6: la pasé a 2 y 4.

| Puerta (sobre `2461939`) | Resultado |
|---|---|
| Suite completa | `846 passed, 102 skipped, 25 warnings in 60.34s`, 0 failed |
| MARIA-4 + archivos reales + sub-ítems + supuestos | `122 passed` |
| `pantalla_maria4.js` | 7 líneas `OK`, `OK: pantalla MARIA-4` |
| `sabotaje_maria4.sh` (6 de antes + estado contra origen, orden del origen, pantalla vieja sin avisos) | `OK: los 9 sabotajes dan rojo por la razón esperada` |
| `sabotaje_maria1c` / `2b` / `2` / `1a` | `OK: los 4 …` / `OK: los 6 …` / `OK: los 8 …` / `OK: los 10 …` |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |

No hubo autorrevisión con subagentes en esta vuelta: los tres puntos son
chicos y tienen cada uno su rojo antes y su sabotaje. Nada para decidir.

Contexto: ~88 %. Hace falta el `/compact` antes de MARIA-3.

---

## MARIA-4 — entregada: lo que decide el despachante sale en el TXT

| Qué | SHA |
|---|---|
| Base (MARIA-1c aceptada) | `448b54d` |
| Producto | `893f6bd` (generador y `/generate_maria`), `30aa414` (pantalla y listados), `8b6edb9` (arreglos de la revisión), `9cf109e` (CHANGELOG) |
| Pruebas, sabotajes, pantalla y captura | `5500f6e`, `e3b7b84`, `9cf109e`, `41a623e`, `b3ec171`, `6149ef3` |
| **SHA que se entrega** | **`6149ef3`** |

**Resultado: terminada.** Cambia lo que sale en el TXT, campo por campo y con
la prueba que fijaste:

| Campo | Ahora | Por defecto |
|---|---|---|
| `CARTUSO`, por producto | Se elige entre los seis estados, con los nombres del despachante (1 a 6). La tabla está en un solo lugar, `ESTADOS_MERCADERIA`, con tu nota | Origen extranjero: 2. Origen argentino: no hay. Si falta, el servidor responde 400 «Ítem N (descripción): el origen es argentino; elegí el estado…» y la pantalla no deja generar |
| `IVAADICIONAL1` | Por operación, con cambio por producto: reventa (`NO_VALIDA`) o uso particular (`IVAAD1`) | Reventa |
| `BANCOSARGENTINA` | Código BCRA de 3 dígitos, por operación. Va antes de `ARDIG-SETI-OPC`, como en el archivo de 2026 | El último banco del cliente. Si no hay, la línea no sale y hay aviso |
| `ARDIG-CUIT-PSAD` | Modoc (`PSAD06`) o Lakaut (`PSAD01`) | La última empresa del usuario. Si no hay, Modoc |

- **Supuestos:** lo que se usó por defecto entra en `supuestos_declarados`:
  el estado de cada producto, el IVA, el banco ausente y la empresa. Se suma
  el aviso de que la reducción o exclusión del IVA se elige en «Ventajas» del
  Kit. El aviso fijo «se declaró 3, siempre» se fue.
- **Pantalla v2:** en validación, antes de generar, aparece la tarjeta «Lo
  que decide el despachante»:
  - banco, empresa e IVA de la operación;
  - una tabla por producto con el estado y el cambio de IVA.

  Solo se guarda lo que la persona elige. El valor por defecto sigue al
  origen: si al volver a NCM el origen pasa a argentino, el estado se vuelve
  a pedir. La propuesta de banco y empresa es del cliente activo.
- **Dónde se guarda, sin columnas nuevas:** en la operación, dentro de
  `extra.resumen.maria`. Incluye el estado y el IVA de cada producto. Los
  listados `GET /api/clientes/{id}/operaciones` y `GET /api/operations`
  devuelven `maria`, recortado a 12 caracteres, y de ahí sale la propuesta.
  Respetan el dueño de las operaciones: el revisor lo probó con dos usuarios.

**Los dos archivos reales:**
- **2025:** sale idéntico entero, cargando estado 3, uso particular, sin banco
  y `PSAD06`.
- **2026:** salen igual que el real los cuatro campos (`2`, `NO_VALIDA`,
  `191`, `PSAD01`) y el orden banco → `ARDIG-SETI-OPC` → `ARDIG-CUIT-PSAD`.
  Los bloques de productos también salen idénticos. El resto del archivo de
  2026 nunca se comparó entero: el real viene sin el relleno de espacios.

## Decisiones

**D11. En la pantalla vieja (v1), un producto de origen argentino ya no se
puede generar.** Esa pantalla no tiene dónde elegir el estado. Recibe el 400
con el mensaje claro y no se rompe, pero no genera. Con otros orígenes genera
con los valores por defecto (2 y reventa). Tampoco muestra los supuestos.
- (a) Aceptarlo: la v1 está de salida, y el criterio 3 prohíbe inventar el
  estado. **Recomiendo (a).**
- (b) Agregar un selector de estado en la v1: una pieza aparte.

Supuesto que podés rechazar: si el banco viene propuesto (el último del
cliente) y la persona no lo toca, va al TXT y la pantalla lo dice («Banco
191: el último que usó este cliente»).

## Evidencia

**Rojo antes:** las pruebas nuevas contra el producto de `448b54d` dan
`30 failed, 2 passed`. Por ejemplo, `TypeError: generate_maria_txt() got an
unexpected keyword argument 'banco_bcra'` y `assert 200 == 400` (origen
argentino sin estado). La comprobación de pantalla contra la primera versión
(`9cf109e`) falla con `FALLA: estados: ["2","3"]`: el 2 por defecto quedaba
guardado como elegido.

| Puerta (sobre `6149ef3`, worktree limpio) | Resultado |
|---|---|
| Suite completa | `837 passed, 102 skipped, 24 warnings in 60.13s`, 0 failed |
| MARIA-4 + archivos reales + supuestos + sub-ítems | `113 passed` |
| `compileall` | ok |
| `smoke_friccion.sh` | `==> OK · telemetría + alias session/state + by-cuit protegido` |
| `scripts/testing/pantalla_maria4.js` | `OK estado 2 por defecto en el importado; el argentino sin estado; banco 191 propuesto` / `OK sin estado en el argentino no se genera` / `OK el pedido lleva banco 191, Lakaut, uso particular, el estado 3 elegido y el importado sin elegir` / `OK al volver y pasar a origen argentino se vuelve a pedir el estado` / `OK otro cliente: se propone su banco (014)` / `OK: pantalla MARIA-4` |
| `pantalla_maria1c.js` | `OK: pantalla MARIA-1c` |
| `sabotaje_maria4.sh` (CARTUSO 3 fijo, IVAAD1 fijo, PSAD06 fijo, sin banco, estado argentino inventado, listados sin `maria`) | `OK: los 6 sabotajes dan rojo por la razón esperada` |
| `sabotaje_maria1c` / `2b` / `2` / `1a` | `OK: los 4 …` / `OK: los 6 …` / `OK: los 8 …` / `OK: los 10 …` |
| Captura | `docs/pm/capturas/maria4-despachante.png` |

**Autorrevisión** (adversario Sonnet alto, que probó la pantalla en una API
propia, más `/code-review high`). Arreglados, cada uno con su prueba o su
paso en la comprobación de pantalla:
- el estado por defecto quedaba guardado como elegido, y al pasar el origen a
  argentino salía `CARTUSO=2`. Es el defecto que esta pieza tenía que evitar;
- el banco o la empresa propuestos de un cliente quedaban pegados al cambiar
  de cliente;
- lo elegido se perdía al volver a NCM;
- se guardaba el valor por defecto como elegido, y por eso los supuestos no
  lo avisaban;
- la propuesta se pedía de a una consulta y podía pisar lo que se escribía
  mientras tanto;
- el estado y el IVA por producto no se guardaban con la operación;
- un grupo con el mismo valor escrito de dos maneras se rechazaba;
- el mensaje de error apuntaba a la fila equivocada en los grupos; ahora
  nombra el producto;
- un banco con dígitos no latinos pasaba;
- el listado crecía sin tope con un valor sembrado;
- la pantalla trataba «ARG» como Argentina y el servidor no.

Quedan como riesgos o fuera de alcance:
- la v1 (D11);
- la tabla de estados está copiada en `despachante.js`, con una nota en el
  archivo. Unificarla pide un endpoint;
- la v2 todavía no muestra los supuestos antes de generar: eso es MARIA-3.

## Para reproducir

```bash
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 6149ef3 8080
<venv>/bin/python -m pytest -q --no-cov tests/test_maria4_despachante.py tests/test_generar_maria_txt.py tests/test_maria_subitems.py tests/test_maria_supuestos.py   # 113 passed
BASE_URL=http://127.0.0.1:8080 node scripts/testing/pantalla_maria4.js          # «OK: pantalla MARIA-4»
VENV=<venv> scripts/testing/sabotaje_maria4.sh 6149ef3                           # «OK: los 6 …»
```

## No corrido

- La prueba en el Kit del orden de los estados: la tabla tiene la nota.
- La pantalla v1 en el navegador: el revisor la probó por HTTP.
- `ataque_aislamiento.sh`: los listados nuevos filtran por dueño. El revisor
  probó con dos usuarios: el que no es dueño recibe 404 y la lista vacía.

Sigo con MARIA-3.

Última vuelta: 2026-10-07 06:50 UTC
Contexto: ~82 % (muy pasado el umbral; compactar)
