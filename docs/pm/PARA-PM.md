# Dev 1 → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL-1 — entregada sobre `9cc321e`

**Resultado:** los tres puntos están hechos. Una planilla con los datos de
los dos archivos reales da el mismo TXT que la carga por PDF. Leer o validar
un Excel no frena el sitio. Las rutas sin llamador se borraron (D13). Dos
rondas de revisión adversarial encontraron 7 + 7 cosas: las arreglé con una
prueba cada una o quedan abajo como D o riesgo.

**Lo que decidís vos:** D17 (aviso de filas sin leer: hoy es un aviso de 4 s
y no queda en el semáforo), D18 (las otras hojas del libro, y un encabezado
que no está en la fila 1) y D19 (riesgos anotados). Ninguna frena la
entrega.

| | SHA |
|---|---|
| Base (RENDIMIENTO-1b aceptada) | `ec3606e` |
| Producto | `3393c2f`, `7e804e5`, `a5bf254`, `2db5080` (borrado, D13), `1a3b7b5`, `42acd4a`, `7500bc5` |
| Pruebas y sabotajes | `b5ddaf3`, `60ec3b1`, `1df55b0`, `028a3ad`, `d47014f`, `052de35`, `86e3aaa`, `d051ebb`, `80776e8`, `b268bb6`, `2759c84`, `fb16ef0`, `72daa42`, `8fb81c2`, `9cc321e` |
| D14: MARIA-1a traída con `merge` desde la rama de la Dev 2 | `448b54d` |
| Tu rama traída con `merge` (sólo `docs/pm/`) | `7f16807` |
| CHANGELOG y este informe | los dos commits `docs:` de arriba |

### Qué cambia para el usuario

**Parte 1: del Excel al TXT** (sólo queda `/upload_excel_v2/`):
- **Nada se inventa.** Si falta un dato o no se puede leer, queda vacío
  (nada de cantidad 1 ni origen «XX») y el semáforo lo marca. Es la regla de
  MARIA-1a, con las funciones de la Dev 2 (D14).
- **Números.** «1.234,56» y «1,5» se leen bien. «1.500» sin otra pista
  queda vacío. La NCM numérica ya no sale con «.0».
- **País.** Se reconoce por el nombre: «China» ya no se corta a «CHI».
  También se reconoce la columna «País de origen».
- **Columnas.** El precio unitario gana sobre «Valor» (el total). El peso
  neto gana sobre el bruto, y si sólo hay bruto el peso queda vacío. Se
  aceptan encabezados con la unidad entre paréntesis, pero si sin
  paréntesis dos se llaman igual («Peso (kg)» y «Peso (bruto)») no se elige
  ninguna por el orden. El mapeo guardado del cliente manda (se corrige a
  mano en el catálogo) y lo detectado completa lo que falta.
- **Filas.** No entran las de total: «TOTAL», «Subtotal 8471.30.00»,
  «TOTAL USD», «Total FOB», «TOTAL AMOUNT» en la columna de código,
  «Totale», «合计», «Summe». Un producto que empieza con «Total» («TOTAL
  QUARTZ 9000») sí entra. Flete, seguro, pago o gastos sin NCM ni origen no
  entran como producto (sumarían al FOB) y se avisan. Cualquier otra fila
  sin NCM ni origen entra, con lo que le falta vacío.
- **Aviso.** «N fila(s) del Excel no se pudieron leer (filas …)» va dentro
  del aviso final de la subida, así otro aviso no lo tapa.
- «.XLSX» en mayúsculas ya no da error.

**Parte 2: no frena el sitio.** Leer y validar el Excel (y el CSV del
historial NCM, y el análisis de migración) corre en otro hilo, con tiempo
máximo `EXCEL_READ_TIMEOUT_S` (60 s) y un 504
`lectura_excel_demasiado_larga`; la pantalla ofrece la carga a mano. Además:
- el Excel tiene su propio grupo de hilos (`EXCEL_READ_WORKERS`, 2),
  separado del PDF;
- un .xlsx que descomprimido pasa de `EXCEL_MAX_DESCOMPRIMIDO_MB` (100) se
  rechaza antes de abrirlo, y ese chequeo también corre en otro hilo;
- las filas vacías no se recorren: una celda suelta en la fila 1.048.576
  tardaba 28 s y ahora menos de 8;
- más de 5000 filas con datos dan 400 con un mensaje claro.

**Parte 3 (D13):** se borraron `/upload_excel/`, `/upload_excel/public` y
`/api/clientes/import`. La pantalla vieja (`?v=1`) ya no carga Excel.

### Prueba del TXT (la que pediste)

En `tests/test_excel1_txt.py`, por cada archivo real anonimizado
(`maria_golden_anon`, `maria_golden_subitems_anon`), la misma factura entra
dos veces: como planilla y como PDF (con el Gemini falso de MARIA-1a). Cada
lado se completa como en la pantalla y se arma el TXT. Los dos TXT son
iguales y traen el FOB de la factura (`MDDTFOB=5000.00` y `7182.00`). Antes
de `1a3b7b5` daba rojo, porque «País de origen» no se reconocía, y ahora da
verde. El sabotaje «“País de origen” deja de reconocerse» la vuelve a poner
en rojo.

### Revisores

Primera ronda (Sonnet alto y Opus alto, sobre `80776e8`). Lo que arreglé en
`42acd4a`, rojo en `80776e8`:

```
E   AssertionError: ['Laptop']                                   (TOTAL QUARTZ/Total Station se perdían)
E   assert ['Laptop', 'F... T/T 30 days'] == ['Laptop']           (FOB TOTAL, Freight entraban)
E   AssertionError: tardó 27.7 s                                  (celda en la fila 1.048.576)
E   ... has no attribute '_MAX_FILAS_EXCEL'                       (sin tope de filas)
E   ... has no attribute '_POOL_LECTURA_EXCEL'                    (Excel y PDF compartían hilos)
E   assert 'descomprimido' in 'No se pudieron extraer items...'   (.xlsx de 150 MB descomprimido se abría)
pantalla_excel1.js: FALLA: el aviso en pantalla no nombra las filas sin leer: «Catálogo aprendido 6/6…»
```

Segunda ronda (Opus alto, sobre `2759c84`). Encontró que dos de mis
arreglos de la primera ronda rompían otras cosas, y tenía razón:
- dar prioridad a lo detectado pisaba el mapeo que el usuario había
  corregido a mano (FOB ×10);
- descartar las filas sin NCM ni origen perdía productos legítimos: una
  factura china con la NCM vacía y «CHINA» en una celda combinada pasaba de
  4 productos a 1;
- la regla del total, más estricta, dejaba entrar «TOTAL USD» y «TOTAL
  AMOUNT».

Lo corregí en `7500bc5`: el mapeo guardado vuelve a mandar; el total se
reconoce por sus palabras (sin una expresión regular que un texto armado
pueda trabar); y la regla de descarte quedó sólo para flete, seguro, pago y
gastos. Rojo en `2759c84`:

```
FAILED test_mapeo_corregido_a_mano_gana_sobre_lo_detectado
FAILED test_productos_sin_ncm_ni_origen_entran_aunque_otra_fila_los_traiga
FAILED test_filas_de_total_con_moneda_o_idioma_no_entran[TOTAL USD|Total FOB|TOTAL (USD)|Totale|合计|Summe|Gesamt|TOTAL DE LA FACTURA]
FAILED test_total_en_la_columna_de_codigo_no_entra
FAILED test_peso_neto_y_bruto_entre_parentesis_no_se_confunden
FAILED test_total_flete_y_condiciones_no_son_productos
E   assert [True] == [False]        (el índice del .xlsx se miraba en el bucle del servidor)
```

Sus 10 sondas contra `9cc321e`: las 9 que eran defecto salen bien. La
décima («Freight to Buenos Aires» con origen CN entra como producto) ya
pasaba antes; va en D19.

Me equivoqué dos veces en pruebas, y lo detectaron los sabotajes o la
corrida contra la base, no la suite:
- la de la «Excel-bomba» pasaba antes del arreglo, porque el zip no parecía
  un .xlsx y lo frenaba el control de tipo. Ahora es un .xlsx de verdad con
  relleno;
- la del índice en otro hilo miraba el hilo principal, pero con TestClient
  el servidor no corre ahí. Ahora mira si corre dentro del bucle del
  servidor.

Y un sabotaje («Peso (neto)/(bruto) vuelven a confundirse») dio verde: con
«neto» el nombre entero ya resuelve la columna. Agregué el caso ambiguo
«Peso (kg)» + «Peso (bruto)», que sí lo distingue.

### Corrido, con su salida

```
suite completa, worktree limpio en 9cc321e, venv-limpio (sólo requirements.txt):
  897 passed, 102 skipped, 25 warnings in 99.53s · fin: 0
scripts/testing/sabotajes/excel1.sh 9cc321e     → 30 ROJO, sabotajes con falla: 0
scripts/testing/sabotajes/rendimiento1.sh HEAD  → 11 ROJO, sabotajes con falla: 0
  (dos patrones habían quedado viejos por EXCEL-1: arreglados en fb16ef0)
rendimiento1b.sh, admin1.sh, admin2.sh          → sabotajes con falla: 0
scripts/testing/sabotaje_maria2.sh HEAD         → OK: los 8 sabotajes dan rojo por la razón esperada
smoke_friccion.sh (levantar.sh 9cc321e)         → ==> OK · telemetría + alias session/state + by-cuit protegido
ataque_aislamiento.sh                           → Bloqueado: 22 · Fugas: 0 · PUERTA G3 PASADA
pantalla_excel1.js (9cc321e)                    → OK: pantalla EXCEL-1   (en 80776e8: FALLA, ver arriba)
```

### Comandos para vos

```bash
git fetch origin claude/dev1-tecnica && git checkout 9cc321e
# 1) Sabotajes de EXCEL-1: cada línea dice ROJO y al final «sabotajes con falla: 0» (tarda ~15 min)
PY=<venv>/bin/python scripts/testing/sabotajes/excel1.sh 9cc321e
# 2) Las pruebas de la pieza: 61 passed
<venv>/bin/python -m pytest -q --no-cov tests/test_excel1_lectura.py tests/test_excel1_rendimiento.py tests/test_excel1_txt.py tests/unit/test_main_upload.py
# 3) Aviso en pantalla: «OK: pantalla EXCEL-1» (en 80776e8, FALLA)
PM_DIR=/tmp/cdi-pm docs/pm/herramientas/levantar.sh 9cc321e 8080
BASE_URL=http://127.0.0.1:8080 node scripts/testing/pantalla_excel1.js <cualquier .xlsx>
```

## Decisiones

- **D17 — El aviso de las filas sin leer dura 4 s.** Está dentro del aviso
  final de la subida, así que ya nada lo tapa. Pero es un aviso pasajero: no
  queda en el semáforo ni en la revisión. Opciones: (a) que el semáforo
  también lo muestre hasta que el usuario lo descarte, como hace con los
  «campos sin leer» de MARIA-1c (toca `semaforo.js` y el estado de la
  operación); (b) dejarlo así.
  **Recomiendo (a)**, en esta pieza o en MARIA-1b: es la única señal de que
  falta un producto.
- **D18 — Lo que el Excel no lee y no avisa.** Sólo se lee la primera hoja.
  Si el encabezado no está en la fila 1 (logo o datos del vendedor arriba),
  el archivo entero da 400. Sin columna de origen, también 400. Y en una
  celda combinada, sólo la primera fila recibe el valor. Opciones: (a)
  arreglarlo ahora: buscar la fila del encabezado, avisar si hay otras hojas
  con datos y aceptar que falte la columna de origen; (b) pieza aparte,
  después de PUNTA-A-PUNTA-1.
  **Recomiendo (b)**, salvo el aviso de «otras hojas con datos», que es
  barato y evita perder productos en silencio.
- **D19 — Riesgos que dejo anotados.**
  - «Freight to Buenos Aires» con origen CN entra como producto. Ya pasaba
    antes. Descartarlo pide adivinar, y con origen puede ser mercadería.
  - El tope de 5000 filas se mira después de leer todo el archivo. Un .xlsx
    de 8 MB, que descomprimido ocupa 96 MB, tarda unos 24 s en leerse antes
    de dar el 400. Con 2 hilos, dos subidas así demoran el Excel de los
    demás hasta 60 s, pero el PDF y el resto del sitio siguen andando. Para
    hacerlo hace falta tener sesión.
  - Los tiempos máximos se suman por etapa: validar (30 s), leer (60 s) y
    extraer (60 s).
  - La validación da 400 sin código propio.
  - Un descuento negativo queda en 0.
  - La NCM de «01012100» escrita como número pierde el 0 inicial (Excel ya
    la guarda así).
  - Un mapeo guardado que el sistema aprendió con la lista de nombres
    vieja («Valor» o «Peso Bruto») sigue mandando para ese cliente hasta que
    se corrija en su catálogo. Decidí que mande porque no se puede
    distinguir de una corrección del usuario.

  **Recomiendo** que vayan a PUNTA-A-PUNTA-1 como cosas a mirar, no como
  piezas.

## Qué no corrí

- No probé la pantalla con un Excel real de punta a punta: la prueba de
  pantalla simula la respuesta del servidor. El camino del servidor sí está
  probado de punta a punta en pytest.
- No probé Railway con varios procesos, ni medí la memoria con muchas
  subidas a la vez.

## Archivos de producto que toqué

`proyecto_maria/main.py`, `proyecto_maria/security/file_security.py`,
`proyecto_maria/services/migration_service.py`,
`proyecto_maria/static/v2/screens/upload.js`, `CHANGELOG.md`. Del lado de
las pruebas: `tests/test_excel1_*.py`, `scripts/testing/pantalla_excel1.js`
y `scripts/testing/sabotajes/{excel1,rendimiento1}.sh`.

## Sigo con

MARIA-1b (con la D6 de la Dev 2) apenas esté en el canal. Si D17 sale (a),
la hago primero.

Última vuelta: 2026-10-07
Contexto: ~80 %

`/compact conservar: Dev 1 de CDI, rama claude/dev1-tecnica. EXCEL-1
entregada sobre 9cc321e (suite 897 passed; sabotajes excel1/rendimiento1/1b/
admin1/2/maria2 en 0; humo, aislamiento y pantalla_excel1.js OK). D17
(semáforo para filas sin leer), D18 (otras hojas, encabezado fuera de fila 1)
y D19 (riesgos) abiertas. Sigue: MARIA-1b con la D6 de la Dev 2, luego
PUNTA-A-PUNTA-1. Entorno: PM_DIR=/tmp/cdi-dev1, levantar.sh <SHA> <puerto>,
venv /tmp/cdi-dev1/venv y venv-limpio; rutina de la PM
trig_01TvMmGfSLDfbcJrf66ZZ7YK.`
