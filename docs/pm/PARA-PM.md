# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## EXCEL-2b (D4 a, D5 a): carril liviano

| Qué | SHA |
|---|---|
| Producto: `file_security.py`, `main.py`, `CHANGELOG.md` | `cf2012b` |
| Pruebas: `tests/test_excel2b.py`, D5 en `tests/test_excel2.py`, `tests/medir_excel2.py`, `sabotajes/excel2b.sh` y patrones nuevos en `excel1.sh` | `116d9f2` |
| Pruebas: dos sabotajes de `excel1.sh` que habían envejecido con EXCEL-3c | `b3ac325` |
| Merge de tu rama (`cab8fe7`, sólo `docs/pm/`) | `cecabf7` |
| Revisión: la prueba del índice largo espía la apertura del zip; caso y sabotaje del tope de 20 lecturas; la fixture de EXCEL-1 también reinicia el pool liviano | `27c67d8` |
| Revisión: la prueba de D5 afirma el tiempo antes que los carriles | `bdc902d` |
| Revisión, rojo: una cabeza de imagen descomprimía la entrada entera en el hilo del servidor | `cfbc489` |
| Revisión, producto: la cabeza se lee de los bytes subidos, con 16 KiB de lo comprimido como mucho | `6c227c9` |
| Revisión: tres sabotajes de la cabeza en `excel2b.sh` | `d2de9fb` |
| Informe | este commit |

El producto cambió dos veces: `cf2012b` y el arreglo de la revisión, `6c227c9`.

La pieza termina en `d2de9fb`. Este informe queda encima de tres commits de
COBRO-MP-1 (`d868adf`, `0ed51b5`, `6f9131c`) que entrego enseguida, con su
propio informe: las puertas de arriba son sobre `d2de9fb`, sin ellos.

Archivos de producto tocados: `proyecto_maria/main.py` y
`proyecto_maria/security/file_security.py`.

**Resultado.** La subida normal detrás de ocho pesadas tarda 0,1 a 0,6 s, contra
27,3 s en la base. **Pero la revisión encontró un hueco que no está cerrado:** un
libro de 1,5 KB con una celda suelta en la última fila entra al carril
liviano y tarda segundos en leerse. Dos de esos libros ya hacen esperar a la
normal 5,5 s, más que el tope de D5. La condición «un libro que dice ser chico
no se cuela» se cumple para el tamaño, pero no para la densidad. Lo que decidís
vos es la **D32**.

La revisión también encontró algo que sí cerré: leer las cabezas de 20 imágenes
falsas descomprimía 9,5 MiB en el hilo del servidor (0,207 s con el sitio
trabado). Ahora tarda 0,002 s.

## Decisiones

**D32. Libros chicos en bytes pero caros de leer, que hoy van al carril
liviano.**

Lo reproduje sobre `bdc902d`, con las sondas del adversario Opus
(`/tmp/rv-excel2b-o/`):
- Un `.xlsx` de 1578 bytes con una celda en la fila 1.048.576, columna C:
  `liviano True`, la lectura tarda 2,84 s.
- El mismo libro con la celda en la columna AZ: tarda 10,25 s y usa 1476 MB
  de memoria.
- Con trampas en la columna C, de punta a punta: con 2, la normal tarda
  «normal: 200 5.5 s»; con 4, «normal: 200 10.6 s». En las dos corridas sale
  «carriles: [('normal.xlsx', True), ('trampa.xlsx', True)]».

Los adversarios midieron otras formas de lo mismo, que no reproduje:
- un `styles.xml` con 395 000 `<xf/>`: 8 a 11,4 s;
- un `sst` grande: 4,5 s;
- un `.xls` de 5,5 KB con una celda en (65535, 255): 6,3 a 6,5 s.

Lo lento es de antes (en la base también tardaba). Lo nuevo es que ahora va al
carril de las subidas normales.

- **(a)** Se acepta como riesgo y se entrega así. El carril liviano protege
  contra libros grandes, no contra libros armados para ser lentos. Es ABUSO-1.
- **(b)** En el hilo liviano, antes de leer, se recorre el XML de la primera
  hoja (que entró al carril, así que pesa 2 MiB o menos) buscando la fila y la
  columna más altas en `r="…"` y en `<dimension>`. Además se cuentan los `<xf`
  de `styles.xml` y las entradas del `sst`. Si alguno pasa un tope, la lectura
  va al pesado. El `.xls` lee siempre en el pesado: para medirlo hay que
  abrirlo.
- **(c)** Sólo el `.xls` va siempre al pesado.

**Recomiendo (b).** Es la única de las tres que devuelve la garantía de D5
frente a los casos reproducidos, y cuesta milisegundos: es buscar con una
expresión regular en 2 MiB, como mucho. Su límite es que es una heurística:
cierra las tres formas conocidas, no las que falten descubrir. Si elegís (b),
va con rojo primero (las tres trampas como prueba de D5) y un sabotaje por
tope. Si elegís (a), corrijo el CHANGELOG para que no prometa más de lo que
cumple.

## Supuestos reversibles

- `EXCEL_LIVIANO_MB` en 0, negativo o no numérico vale 2 (el default). Es lo
  que hace `_mb_de_entorno` con las otras variables; no hay forma de apagar el
  carril desde el entorno. Si la querés, es una línea.
- Las imágenes se descuentan si empiezan con su firma (PNG, JPEG, GIF, BMP,
  TIFF, WMF, EMF), no por el nombre. Como mucho 10 MiB y 20 partes leídas:
  al leer, `_xlsx_solo_primera_hoja` vuelve a comprimir las imágenes, así que
  no son gratis.
- Los pools livianos usan las mismas variables de hilos que los pesados
  (`EXCEL_VALIDATE_WORKERS`, `EXCEL_READ_WORKERS`, 2 por defecto). Son 4 hilos
  más en el proceso y todos comparten el GIL. Quien haya bajado esas variables
  a 1 para ahorrar memoria tiene ahora 2 lecturas a la vez, no 1.
- Toda subida de Excel que pasa por `validate_file_upload` valida en el carril
  que le toca. La lectura liviana es sólo de `/upload_excel_v2/`. En
  `/api/ncm/import-historial` y `/api/migrations/analyze`, un libro chico valida
  en el liviano y lee en el pool de siempre (`_leer_tabla`, fuera de alcance).
- De paso arreglé dos sabotajes de `excel1.sh` cuyo patrón había envejecido con
  mi EXCEL-3c (`92badcf`, ya en la base). No los rompió EXCEL-2b.

## Cómo se decide el carril

Se mide una vez, en `validar_con_carril`, y la lectura usa ese mismo valor:
- `.xls`: por su tamaño, porque no está comprimido.
- `.xlsx`: la suma de los tamaños descomprimidos que declara el índice del zip,
  menos las imágenes reconocidas por su firma. Esto corre en el hilo del
  servidor, antes de abrir el zip:
  - el fin del índice se busca en los últimos 64 KiB, como hace `zipfile`;
  - si hay zip64, va al carril pesado;
  - si el índice pasa de 128 KiB, va al carril pesado sin leerlo;
  - la cabeza de cada imagen (44 bytes) se saca de los bytes subidos, mirando
    16 KiB de lo comprimido como mucho; si de ahí no salen, esa entrada no se
    descuenta y cuenta como XML;
  - ante cualquier excepción, va al carril pesado.

**El libro que dice ser chico y no lo es.** No se puede saber cuánto
descomprime de verdad sin descomprimirlo, y eso es justo lo que el carril quiere
evitar. Lo que sí vale es esto:
- Todos los lectores usan `zipfile`: `_abrir_excel`, `_xlsx_solo_primera_hoja` y
  openpyxl, y `_otras_hojas_con_datos`.
- `zipfile` no entrega más bytes que los declarados.

Un libro de 3 MiB de hoja que declara 50 000 bytes entra al carril liviano,
pero ahí sólo hay 50 000 bytes de trabajo: el XML queda cortado y da 400
enseguida. Lo probé de punta a punta con
`test_el_libro_que_dice_ser_chico_se_rechaza_rapido_en_el_carril_liviano`:
- da «Invalid Excel file: unclosed token: line 1, column 49999»;
- se valida en `validar-excel-liviano_0`;
- no se lee.

Lo que viene disfrazado de otra forma (nombre de imagen, zip64, índice largo,
imagen inflada, más de 20 imágenes) va al carril pesado, y cada caso tiene su
prueba y su sabotaje. Lo que esta medida no ve es la densidad: eso es la D32.

Quedan fuera de alcance, como pediste, el límite de frecuencia (ABUSO-1) y las
opciones (b) y (c) de D4. Alguien con sesión puede inundar el carril liviano
con libros chicos: eso es ABUSO-1.

## Mediciones

`infolist` en el hilo del servidor, por cantidad de entradas:

| Entradas | Tiempo |
|---|---|
| 30 | 0,0005 s |
| 1 000 | 0,0032 s |
| 10 000 | 0,036 s |
| 100 000 | 0,537 s |

Con el tope de 128 KiB de índice entran como mucho unas 2 800 entradas.

Una imagen falsa de 95 MiB llevaba `_leer_excel_ruta` a 0,722 s (0,023 s sin
ella): por eso el descuento tiene un tope de 10 MiB.

`.xls` armados con filas normales:

| Tamaño | Validar | Leer |
|---|---|---|
| 0,54 MiB | 0,039 s | 0,188 s |
| 1,53 MiB | 0,121 s | 0,294 s |
| 3,35 MiB | 0,348 s | 0,916 s |

Un `.xls` liviano de filas normales cuesta 0,5 s o menos. Uno armado con una
celda en (65535, 255) tarda 6,3 s con 5,5 KB (D32).

## Hallazgos de la revisión

| Quién (modelo, esfuerzo) | Sev. | Hallazgo | Qué hice |
|---|---|---|---|
| Adversario Opus, alto | ALTA | Un `.xlsx` ralo de 1,5 KB con una celda en la fila 1.048.576 va al carril liviano: columna C 7,26 s; columna AZ 14,38 s y 1473 MB. Con 2 trampas, la normal tarda 21,3 s; con 20, da 504 a los 61,4 s | Lo reproduje (ver D32): 2,84 s y 10,25 s con 1476 MB; con 2 trampas, la normal tarda 5,5 s. **D32** |
| Adversario Opus, alto | MEDIA | `styles.xml` con 395 000 `<xf/>`: 8 s en el liviano | No reproducido. D32 (b) lo cubre |
| Adversario Opus, alto | MEDIA | `.xls` con una celda en (65535, 255): 6,3 s | No reproducido. D32 (b) y (c) lo cubren. Corregí la frase del informe que decía que un `.xls` liviano cuesta menos de 0,5 s |
| Adversario Opus, alto | MEDIA/BAJA | La medida en el hilo del servidor lo traba hasta 0,11 s, y `/health` llegó a 4,49 s con lecturas en curso (GIL) | Lo primero, reproducido sobre `bdc902d`: 20 entradas DEFLATE de bloques vacíos declaradas como imagen tardan 0,207 s en el hilo del servidor y descomprimen 9 961 400 bytes («se descomprimieron 9961400 bytes en el hilo del servidor», rojo de `cfbc489`). Arreglado en `6c227c9`: 0,002 s. Lo del GIL es preexistente: riesgo |
| Adversario Opus, alto | BAJA | Con el carril liviano, hay el doble de lectores a la vez | Supuesto declarado |
| Adversario Opus, alto | — | El tope de 20 lecturas de cabezas de imagen no tenía caso ni sabotaje | Arreglado en `27c67d8`: caso con 40 imágenes y sabotaje |
| Adversario Sonnet, alto | ALTA | Lo mismo por densidad: `styles` 11,4 s, `sst` 4,5 s, `.xls` 6,5 s; con 4 libros densos, la normal espera 36,3 s | **D32** |
| `/code-review` alto, #1 | — | El carril se elige por bytes descomprimidos: un XML denso de 2 MiB es lento igual | **D32** |
| `/code-review` alto, #2 | — | La decisión se toma una vez y el carril liviano tiene el mismo tiempo máximo de 60 s: una lectura que vence ocupa un hilo liviano 60 s | D32 (b) lo achica; el tiempo máximo propio del carril liviano no lo agregué (no estaba pedido) |
| `/code-review` alto, #3 | — | La fixture de EXCEL-1 no reiniciaba el pool liviano | Arreglado en `27c67d8` |
| `/code-review` alto, #4 | — | `dt < 5` depende de la máquina | Lo decidiste en D5 (a). En esta máquina: 0,1 a 0,6 s |
| `/code-review` alto, #5 | — | La prueba del índice largo espiaba `infolist`, que no distingue «no se leyó» | Arreglado en `27c67d8`: espía `ZipFile._RealGetContents`. Su sabotaje nuevo da rojo |
| `/code-review` alto, #6 | — | Los pools livianos reutilizan las variables de hilos | Supuesto declarado |
| `/code-review` alto, #7 | — | Cuatro fábricas de pools casi iguales | No lo hago: es un refactor fuera de la tarea |
| `/code-review` alto, #8 | — | El índice del zip se lee tres veces, una en el hilo del servidor | Acotado por el tope de 128 KiB (unas 2 800 entradas, unos milisegundos) |
| `/code-review` alto, #9 | — | `import-historial` y `migrations/analyze` validan en el liviano y leen en el pool de siempre | Supuesto declarado |
| `/code-review` alto, #10 | — | La prueba de punta a punta afirma el texto de expat «column 49999» | Anotado: si cambia el lector de XML, esa línea se ajusta |
| `/security-review` | — | Sin hallazgos | — |

## Puertas (sobre `d2de9fb`)

| Puerta | Salida |
|---|---|
| Rojo de D5 en la base `bc1b16d` (prueba endurecida, producto de la base) | «AssertionError: la subida normal tardó 27.3 s: esperó detrás de las pesadas» |
| D5 con el producto, dos corridas en `d2de9fb` (la primera, con los sabotajes corriendo al lado) | «normal: 200 en 0.6 s», «normal: 200 en 0.1 s» |
| Rojo de la cabeza de imagen, prueba de `cfbc489` con el producto de `bdc902d` | «AssertionError: se descomprimieron 9961400 bytes en el hilo del servidor» |
| `pytest tests/test_excel2b.py` más D5 | «18 passed, 3 warnings in 35.70s» |
| `excel2b.sh d2de9fb` | «base en verde», 16 de 16 «ROJO» por su motivo, «sabotajes sin rojo: 0», salida 0 |
| `excel1.sh d2de9fb` | 36 de 36 «ROJO», «sabotajes con falla: 0», salida 0 |
| Suite completa, worktree limpio en `d2de9fb` | «4065 passed, 121 skipped, 3 xfailed in 562.51s (0:09:22)», salida 0 |
| `compileall -q proyecto_maria` | salida 0 |
| `smoke_friccion.sh` contra la API levantada en `d2de9fb` | «==> OK · telemetría + alias session/state + by-cuit protegido», salida 0 |

Sabotajes nuevos de la revisión, con su texto de rojo copiado de la salida:
- «la normal vuelve a la cola de las pesadas (D5)»: dice «esperó detrás de las
  pesadas». Antes de `bdc902d` daba rojo por los carriles, sin ese texto,
  porque la validación de la normal no terminaba y su carril no se anotaba.
- «el índice largo se lee antes del tope y sigue yendo al pesado»: dice «el
  índice largo se leyó en el hilo del servidor».
- «las cabezas de imagen se leen sin tope de lecturas»: dice «FAILED
  tests/test_excel2b.py::test_no_se_leen_mas_de_20_cabezas_de_imagen».
- «la cabeza vuelve a descomprimir la entrada entera»: dice «se descomprimieron».
- «la cabeza de una imagen sin comprimir no se lee»: dice «FAILED
  tests/test_excel2b.py::test_una_imagen_guardada_sin_comprimir_tampoco_cuenta».
- «la cabeza de una imagen comprimida no se lee»: dice «FAILED
  tests/test_excel2b.py::test_una_imagen_de_verdad_no_cuenta».

## Comandos

```bash
git fetch origin claude/dev-tecnica && git checkout d2de9fb
export GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares
PY=$PM_DIR/venv/bin/python scripts/testing/sabotajes/excel2b.sh   # 16 «ROJO», «sabotajes sin rojo: 0»; incluye el rojo de D5 por tiempo
PY=$PM_DIR/venv/bin/python scripts/testing/sabotajes/excel1.sh    # «sabotajes con falla: 0»
$PM_DIR/venv/bin/python -m pytest -q --no-cov tests/test_excel2b.py "tests/test_excel2.py::test_ocho_libros_con_la_primera_hoja_al_borde_del_tope_no_dejan_sin_lectura_a_una_subida_normal"   # 18 passed
```

Para ver la D32 (las sondas están en `/tmp` de mi contenedor, no en el
repositorio): un `.xlsx` con una sola hoja de dos filas normales y
`<row r="1048576"><c r="AZ1048576"><v>1</v></c></row>`, subido a
`/upload_excel_v2/`, va a `validar-excel-liviano` y tarda segundos en leerse.

## Riesgos y lo no corrido

- **D32**, arriba.
- Un libro denso de la D32 usa hasta 1,5 GB al leerse, en cualquier carril.
  Antes había 2 lecturas a la vez; ahora puede haber 4.
- `_sin_dtd` mira sólo las partes por nombre (preexistente, no lo toqué).
- Las sondas de punta a punta de la D32 no terminan solas: imprimen el
  resultado y quedan colgadas al cerrar, así que las corté con `timeout` (124).
  Es la sonda, no el producto: la suite no se cuelga.
- `ataque_aislamiento.sh`: no corrido; la pieza no toca datos, sesión ni
  permisos.
- Fuera del repositorio sigue `/orden1_app.py`, vacío, en la raíz del
  contenedor (de ORDEN-1).

El informe de ORDEN-1 sigue en `cdc9c57`; el de GUARDAR-2, en `cb42e8f`.

/compact conservar: Dev 1 (técnica), rama claude/dev-tecnica. Entregando en orden: EXCEL-2b (este, D32 abierta), COBRO-MP-1, COBRO-CORTE-1, COBRO-MP-2, AISLAMIENTO-2, LIMPIEZA-1, BACKUP-1a. Informes en el scratchpad (informe_*.md); push y aviso a la PM principal por cada uno.
