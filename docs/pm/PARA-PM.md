# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL-3d: entregada

**Resultado:** los tres hallazgos de tu reproducción (`REPRODUCCION-EXCEL-3c-2026-10-25.md`)
están arreglados y cada uno tiene su prueba y su sabotaje en rojo. «Flete
int.» combinado da flete 1200 y FOB 3550. «Freight elevator» sale por la
misma regla, sin palabras nuevas en la lista. La cabecera y su hijo se
deciden igual, y todo renglón que entra sin precio se avisa con su fila, en
toda la familia. D17 está en su propio commit y `ataque_aislamiento.sh`
vuelve a probar G3. La autorrevisión encontró dos agujeros más dentro de la
pieza; los dos están arreglados, con su rojo antes. Quedan tres decisiones
(D20–D22): son cosas que ya pasaban en la base, o una regresión chica que
sigue una regla que ya teníamos. Falta la prueba con la proforma real del
24/10, que no entra al repositorio: la hace Emi.

| SHA | Qué |
|---|---|
| `d4982e9` | fix: lo que empieza como un cargo no cambia el FOB sin un aviso con su fila |
| `b6b06a7` | test: casos y sabotajes |
| `c0f69b5` | changelog |
| `25f2a4f` | **D17**: `ataque_aislamiento.sh` vuelve a generar el MARIA.TXT de Ana |
| `22b481a` | fix (code-review): la descripción copiada no saca del grupo al renglón con medidas; un solo aviso de flete dudoso con tope |
| `d5f1e58` | test: rojos de esa vuelta |
| `6c5fd02` | fix (adversario Opus): la copia de un cargo combinado con texto en Item no entra al FOB |
| `2cc46d3` | test: su rojo y sus sabotajes |
| `e24abfa` | changelog |
| `7de44b7` | test: los sabotajes de 3b y 3c siguen al código nuevo. **Las puertas corrieron sobre este SHA** |
| `eeae447` | changelog: dice sólo lo que fijan las pruebas |
| (este informe) | docs |

Después de `7de44b7` sólo cambian `CHANGELOG.md` y este archivo.

Archivo de producto tocado: **`proyecto_maria/main.py`** (`try_extract_with_mapping`
y los avisos del mapeo). La rama también lleva ESTUDIO-1 (`609ec52`…`c992715`),
que ya estaba en `31c9b5a`, sin entregar: su informe va aparte.

## Decisiones

Numero desde D20 porque D18 y D19 ya están usadas en otros informes.

- **D20. Cabecera de descuento sin precio con copias que sí tienen precio (R3 del adversario Sonnet).**
  Una cabecera «Discount tag labels», «Rebate valve DEMO» o «Freight elevator DEMO»
  sin precio, con la descripción combinada y copias que tienen texto en Item y precio.
  En `31c9b5a` daba FOB 170 y sin leer [3]. Ahora da FOB 100, sin leer [3, 4, 5],
  y ningún aviso propio. Con Item vacío la base ya daba eso. La causa: esa cabecera
  sale antes de registrarse, y su copia se decide «sin leer».
  - (a) Dejarlo. Sigue la regla de EXCEL-3b, «una nota de descuento sin precio
    no abre grupo», y las filas quedan nombradas en «sin leer». Nada entra al FOB
    en silencio.
  - (b) Que la cabecera sin precio, cuando sus copias sí tienen precio, abra el grupo.
  - **Recomiendo (a).** El FOB baja, pero de forma visible, y (b) reabre lo que
    decidimos en EXCEL-3b. El riesgo: las filas aparecen en «sin leer» sin un
    aviso que diga por qué.
- **D21. Plurales y rótulos que la lista no conoce, con o sin combinadas.**
  «Fletes», «Seguros» y «Bank fee», con el origen combinado o sin combinadas,
  entran como producto y suben el FOB sin aviso: 3500 → 4700. En `31c9b5a` da
  exactamente lo mismo; no es de esta pieza. La regla de EXCEL-3d se apoya en
  lo que la lista reconoce como cargo, y esas palabras no están. «Ocean freight»
  sigue igual porque me pediste no tocarlo.
  - (a) Dejarlo como riesgo.
  - (b) Una pieza chica aparte: plurales y «fee» en `_FILA_QUE_NO_ES_MERCADERIA_RE`,
    con un aviso de su fila como los de esta pieza.
  - **Recomiendo (b), aparte.** Cambia la lista base, que se usa también sin
    combinadas. Mezclarla acá agranda una pieza que ya está revisada.
- **D22. Una fila con origen propio que empieza como un cargo.** «Gastos administrativos»
  con «China» en el origen y precio entra como producto, sin aviso, con o sin
  combinadas, igual que en `31c9b5a`. Lo mismo pasa con la copia con medidas e
  «Insurance» en Item. La fila tiene su propio origen, así que no pasa por el
  filtro de lo que no es mercadería.
  - (a) Dejarlo. Un producto real puede tener ese rótulo y un origen.
  - (b) Avisarlo con su fila, sin sacarlo, como «Payment terminal POS».
  - **Recomiendo (b) en la misma pieza que D21.** Sólo agrega un aviso y no
    cambia el FOB.

## Punto por punto contra tu reproducción

| Hallazgo o pedido | Ahora | Prueba (`tests/test_excel3.py`) |
|---|---|---|
| 1. Cargo con una palabra que la lista no conoce entra al FOB sin aviso | Queda sin leer, es el flete con «de la fila N», o entra con «fila N («rótulo»)». Ninguna otra salida | `test_un_cargo_con_palabras_de_mas_no_cambia_el_fob_sin_un_aviso_con_su_fila`: cada cargo de `CARGOS_CON_PALABRAS_DE_MAS` en las 6 `FORMAS_DEL_CARGO` |
| «Flete int.» combinado (C2:C4) | flete 1200, FOB 3550, «Flete: se leyó 1.200,00 de la fila 4» | `test_el_flete_int_combinado_se_lee_como_en_la_base` |
| «Freight elevator», con la misma regla | Se lee como flete, con un aviso que nombra su fila: «1 renglón(es) se leyeron como flete y dicen algo más: fila 3 («…»); si alguno es un producto, cargalo en la revisión.» | `test_un_producto_que_empieza_como_el_flete_con_el_origen_combinado_se_lee_como_flete_avisado`, `test_con_la_descripcion_combinada_un_rotulo_de_flete_en_item_se_lee_como_flete_avisado` |
| Producto que empieza como un cargo | Entra con «fila N («rótulo»)» | `test_un_producto_que_empieza_como_un_cargo_entra_con_un_aviso_que_nombra_su_fila` («Payment terminal POS», «Handling cart», «Seguro de puerta», «Insurance card printer») |
| «Insurance as per policy» e «Insurance 40 GBP» en Item, con la descripción combinada | Ya no entran en silencio | dentro de la familia, forma `descripcion_rotulo_en_item` |
| 2. La cabecera y su hijo se deciden distinto | Se deciden igual: si la cabecera queda sin leer, el hijo también, y los dos aparecen nombrados | `test_la_cabecera_y_su_hijo_se_deciden_igual`: 4 formas de cabecera (vertical por herencia, vertical combinada, horizontal, código combinado) por 4 rótulos; `test_la_cabecera_insurance_sin_combinadas_deja_sin_leer_al_hijo` |
| 3. D12 (a) avisa sólo en el grupo con medidas | Todo renglón que entra sin precio se avisa con su fila: con la descripción combinada («filas 3, 4»), con el origen combinado y sin combinadas («fila 3») | `test_todo_renglon_que_entra_sin_precio_se_avisa_con_su_fila` |
| Copia de un cargo combinado con texto en Item («A2», «#3», «2b», «(3)», «-») | Queda sin leer o entra con aviso de su fila | `test_la_copia_de_un_cargo_combinado_con_texto_en_item_no_cambia_el_fob_sin_su_fila`: 4 rótulos × 5 formas de Item × 2 combinadas |
| Avisos largos | Nombran hasta cinco filas y cuentan el resto («… y 2 más») | `test_los_avisos_nombran_hasta_cinco_filas_y_cuentan_el_resto` |

Lo que decidí: el cargo «dudoso», el que empieza como cargo y dice algo más,
**entra con aviso**. No lo dejo afuera, porque los productos reales de la
familia («Payment terminal POS») también empiezan así. El cargo que dice sólo
el cargo queda sin leer, como en EXCEL-3c.

## Hallazgos de la autorrevisión

| Revisor | Modelo y esfuerzo | Hallazgo | Qué hice |
|---|---|---|---|
| `/code-review high` sobre `31c9b5a..d4982e9` | el de la sesión, alto | Con la especificación combinada, una nota «Freight included» en Item sacaba del grupo al renglón con medidas (regresión mía) | Arreglado en `22b481a`. Rojo en `d5f1e58`: falla con `d4982e9` y pasa con el arreglo |
| ídem | ídem | Un aviso por cada flete dudoso, sin tope; las listas de filas se armaban de dos maneras | Un solo aviso, con hasta cinco filas; las listas usan una sola función (`22b481a`) |
| ídem | ídem | La cabecera sin leer deja al hijo sin leer | Sin cambio: eso cumple «se deciden igual» |
| ídem | ídem | El rótulo dudoso se guardaba como texto en un lado y verdadero/falso en otro | No pude armar un caso que lo distinga: los dos árboles dan lo mismo. Lo unifiqué como texto. Va sin rojo propio |
| Sabotajes | — | «el flete dudoso no se avisa» daba VERDE | La prueba ahora pide el texto exacto del aviso (`d5f1e58`) |
| Adversario | Opus, alto, sobre `d4982e9` | La copia de un cargo combinado con texto en Item («A2», «#3») entraba al FOB sin aviso | Arreglado en `6c5fd02`. Rojo: 40 casos que fallan con el código anterior (`2cc46d3`) |
| Adversario | Sonnet, alto, sobre `6c5fd02`: 48 casos | R3: cabecera de descuento sin precio con copias con precio | D20 |
| ídem | ídem | Mejoras confirmadas: C1, C2, D4, D5, D9, D10, R6 y D13. C14 y D7 ahora nombran las dos filas | — |
| ídem | ídem | Ya pasaban en la base: cargo en «Part No.» tapado por el texto de Item (C8); copia con medidas e «Insurance» en Item (D3); fila con origen propio que empieza como cargo (D8, C13); Origin «Freight» da XX (C9); «1. Insurance» entra sin aviso (C10) | Riesgos. D3, D8 y C13 van en D22 |
| Sabotajes en `e24abfa` | — | 4 ROTO (el patrón ya no estaba) y 1 VERDE, de 3b y 3c | Al día en `7de44b7`: 79 ROJO, 0 sin rojo |
| CHANGELOG en `e24abfa` | — | Afirmaba más de lo que fija la prueba de la familia | Corregido en `eeae447` |

## Puertas, sobre 7de44b7

| Puerta | Salida |
|---|---|
| `compileall -q proyecto_maria` | rc=0 |
| Suite completa (worktree limpio) | `2469 passed, 102 skipped, 2 xfailed, 25 warnings in 288.41s (0:04:48)`, rc=0 |
| `test_excel3.py` | `264 passed, 3 warnings in 7.41s` |
| `excel3.sh 7de44b7` | 79 ROJO, «sabotajes sin rojo: 0», rc=0 |
| `smoke_friccion.sh` | «==> OK · telemetría + alias session/state + by-cuit protegido», rc=0 |
| `ataque_aislamiento.sh` (D17) | «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.», `Bloqueado: 22 · Fugas: 0`, rc=0 |

**No corrí:**
- el mapeo guardado del cliente (`celdas_rellenadas` al reaplicar un mapeo
  guardado, `main.py` ~8007);
- la proforma real del 24/10, que la hace Emi;
- la e2e completa y los sabotajes de piezas anteriores, salvo los de 3b y 3c que
  están en `excel3.sh`.

## Riesgos

- Los avisos se muestran en un toast de 4 s (`app_v2.js:213`). Si el usuario no
  lo lee, la fila sin leer igual queda en la lista de «sin leer», pero el aviso
  del producto dudoso no queda en ningún lado. Ya pasaba.
- Una regla por prefijo nunca es completa: D21 y D22 son los huecos que
  encontré. Puede haber otros que ninguna prueba cubre.

## Comandos

```bash
git checkout <SHA de este informe>
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
python -m pytest -q --no-cov tests/test_excel3.py              # 264 passed
PY=<venv>/bin/python bash scripts/testing/sabotajes/excel3.sh   # 79 ROJO, «sabotajes sin rojo: 0»
PUERTO=8847 ./scripts/testing/ataque_aislamiento.sh             # «PUERTA G3 PASADA», Bloqueado: 22 · Fugas: 0
```

## Sigo con

ESTUDIO-1: `/security-review`, las puertas sobre su SHA final y el informe.
Después, CLIENTE-1c y GUARDAR-2.

/compact conservar: Soy la Dev técnica (Dev 1) de CDI, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica (nunca main), rutina trig_011UpBfwEu9TUzoNUrviqoP5 min 15; aviso a la PM principal session_01B7FVQspcEHF7PqNv797wNM con send_message priority next empezando «Dev técnica:». EXCEL-3d entregada (puertas sobre 7de44b7; después sólo CHANGELOG eeae447 y este informe). Abiertas para la PM: D20 (R3 cabecera de descuento sin precio con copias con precio, recomiendo a), D21 (plurales Fletes/Seguros/Bank fee, recomiendo b aparte), D22 (fila con origen propio que empieza como cargo, recomiendo b con D21). Próxima D: D23. Sigo con ESTUDIO-1 (security-review, puertas, informe), después CLIENTE-1c (D15 b y D16 b con _fecha_inic_activ_de_api, error de --base sin la clave, dígito de ancho completo) y GUARDAR-2 (desde 2d930c5 en claude/dev1-tecnica). Reglas de Emi: sólo me piden la PM o Emi; nada se publica sin su «dale» para el SHA; nunca main; sin secretos ni datos reales (la proforma del 24/10 no entra); no tocar maria_generator.py, controles_maria.py, despachante.js ni el canal/rama de la Dev MARIA; subagentes hasta alto, sin Fable.
