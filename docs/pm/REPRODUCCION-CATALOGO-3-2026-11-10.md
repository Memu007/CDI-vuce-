# Reproducción de CATALOGO-3 (Dev MARIA), 2026-11-10

Producto e informe en `f4ade80`, base `07504e0`, rama `claude/dev-maria`.
Veredicto: **devolución** (arriba de `PARA-DEV-2.md`), por tres causas.
Vuelta en `ec0092a` (informe `b7c4c85`, base de la vuelta `1345ca7`):
**devolución**. La aceptó la PM a las 10:40 UTC y la retiró a las 10:45 UTC,
antes de integrarla: H1 no era preexistente («Retiro de la aceptación», al
final).

## Puertas del informe, reproducidas sobre `f4ade80`

| qué | salida |
|---|---|
| `test_catalogo3` + `test_despacho1b` + `test_despacho1c` | pasan |
| golden | `115 passed, 2 xfailed in 14.49s` |
| `compileall` | rc=0 |
| `catalogo3.sh` (sabotajes) | 25 ROJO, `fallas: 0` |
| arnés Postgres 16, `f4ade80` | 7 OK, `todo OK` |
| arnés Postgres 16, base `07504e0` | `5 fallas` (dos workers, varchar(3), migración, TAIWAN, CJK en dos filas): coincide |
| `chequeo-6.py 07504e0 f4ade80` | `producto +166/−66`, 1 `AVISO` (100 netas), explicado en el informe; historia vacía: coincide |
| suite completa | ver «Suite», abajo |

## Lo que reproduje yo

**Causa 1: guardar-uso pierde la confirmación entera.** `TestClient`, SQLite,
modos falsos, `POST /api/ncm/guardar-uso` con proveedor «Acme PM» y NCM
73181500; cuento filas de `ncm_historial`.

| origen | `07504e0` | `f4ade80` |
|---|---|---|
| CHN, ITA, Hong Kong, Viet Nam, U.S.A., PRC, Turkey, MACAO | 200, historial=1 | **400** «No reconozco el origen…», historial=0 |
| 123, CN | 200, historial=1 | 200, historial=1 |

«123» es LIBIA en `PAISES_INDEC` (D158). `get_pais_codigo("TAI")` da 310 en
la base y en la entrega: preexistente.

**Causa 2: textos iguales dan claves distintas.** `clave_de_producto`:

| a | b | `07504e0` | `f4ade80` |
|---|---|---|---|
| Capacitor 10µF 50V (U+00B5) | Capacitor 10μF 50V (U+03BC) | iguales | distintas |
| Bolt ｶﾞｽ M8 (medio ancho) | Bolt ガス M8 | iguales | distintas |
| Screw M8 螺丝 | Screw M8 | iguales | distintas |

**Causa 3: costo de la clave.** `clave_de_producto` 0,066 ms contra 0,006 ms
de `_normalize` con 65 caracteres; 0,464 ms contra 0,028 ms con 430.
Estimado, no medido de punta a punta: 20 ítems × 2000 filas de 65 caracteres,
~2,6 s contra ~0,25 s.

## Adversarios con contexto nuevo (sin red, GEMINI_API_KEY vacía)

**Sonnet alto, HTTP y aislamiento.**
- Lookup: 20 ítems × 2000 filas de ~430 caracteres, 19,44 s contra 1,87 s en
  la base (lo medí sólo en la función, arriba).
- Guardar-uso con origen fuera de la tabla: 400 y se pierde todo (reproducido
  arriba). El PUT del catálogo con «CHN» da 400.
- Clave de más de 2000 caracteres: PUT y DELETE dan «product_key inválido».
- Limpio y reproducido por él: aislamiento entre usuarios en GET, PUT y
  DELETE con ids `~`, CJK y de más de 60; path traversal; XSS (toast con
  textContent); sin 500 nuevos; migración SQLite con dos dueños, idempotente.

**Opus alto, migración y datos (Postgres 16 propio, bases borradas por él).**
- µ/μ, medio ancho, simplificado/tradicional y Ø/φ pasan de exact a none, en
  el catálogo y en la memoria del cliente (lo de la tabla de arriba lo
  reproduje yo; lo de Postgres, sólo él).
- La migración parte un proveedor cuyas filas se guardaron con nombre con y
  sin letras no latinas (`shenzhen_co`): cada nombre ve un solo producto. Lo
  leí en `main.py:1351-1358` y coincide; la corrida es sólo de él.
- `_migrate_catalogo_sin_tope` detiene el primer arranque si otra sesión
  tiene una transacción abierta sobre `operation_items` (LockNotAvailable a
  los ~6,5 s). Sólo de él.
- Un «TAI» viejo del catálogo vuelve por el match y traba la edición del NCM
  (`catalogo.js:309-318` manda el origen). Sólo de él. Además corrige el
  informe: `/generate_maria` frena «TAI» con «Origen no reconocido»; no sale
  como 310.
- 158 nombres que `paises_maria.js` resuelve y el servidor no («HONG KONG»,
  «MACAO», «PUERTO RICO»…); el servidor acepta «0313» y la pantalla no.
  Ningún país con código distinto en cada lado.
- Limpio: migración con dos dueños, vacío, NULL, largos, CJK y un choque
  («9 filas al día, 1 quedan por un choque»); el segundo arranque no hace
  UPDATE; sin `[:3]` no hay 500 con NUL ni medios pares.

## Clasificación

- A la devolución: causa 1 (regresión con camino de hoy: Excel con texto
  libre y `saveNcmUsage`), causa 2 (µ/μ y medio ancho por NFKC; «Screw M8»
  contra «Screw M8 螺丝», que D77 no pide) y causa 3.
- Riesgos, no se piden: clave de más de 2000 (sin camino de hoy); lock del
  primer arranque (va a la lista de publicar con D156); proveedor partido por
  la migración (costo de D157); simplificado/tradicional y Ø/φ.
- D159: lo de clientes (`clientes.js` maxlength, `clients.default_origin`
  VARCHAR(3), `[:3]` de main.py:7479/7557/9721) va como pieza aparte.

## Suite

Primera corrida perdida: la salida pasó por `| tail -30` y el resumen quedó
fuera; ese «rc=0» era de `tail`, no de pytest. La repetí con el registro
entero, sin `-x`, en `/tmp/cdi-pm/wt-cat3-suite` (`f4ade80`, SQLite):
`5724 passed, 101 skipped, 3 xfailed in 927.54s (0:15:27)`, `fin rc=0`, sin FAILED ni ERROR. Después del resumen quedan 713 avisos «Task was destroyed but it is pending!» del cierre de asyncio; no cambian el rc. La devolución no depende de la suite.

## Vuelta sobre `ec0092a` (2026-11-10 10:40 UTC)

Rango de la vuelta: `1345ca7..ec0092a`. Debajo de `1345ca7` hay commits de
PRESUPUESTO-CLIENTE-1 sin entregar: no entran en este veredicto. El
producto llega hasta `9dcee73`; `ec0092a` sólo suma
`scripts/testing/bench_catalogo3_lookup.py`.

| qué | salida |
|---|---|
| `chequeo-6.py 1345ca7 ec0092a` | producto +152/−99, 1 AVISO (53 netas) explicado en el informe, historia vacía, arnés +414/−44; igual al informe |
| `catalogo3.sh` sobre `ec0092a` | 45 ROJO, «fallas: 0», `fin rc=0` |
| arnés PG | 7 OK |
| golden | 115 passed, 2 xfailed |
| pantalla contra servidor (arnés JS) | 0 diferencias |
| mis 41 negativos, con ejemplos distintos de los de la devolución | verdes |
| suite entera, SQLite | `5782 passed, 101 skipped, 3 xfailed in 964.03s`, 0 FAILED, `fin rc=0` |

Bench (20 ítems, 2000 filas), total en segundos, base `07504e0` → vuelta:
65 caracteres 1,42 → 0,91; con acentos 1,51 → 0,95; con kana 1,01 → 0,58;
430 caracteres 3,94 → 2,69; con acentos 3,86 → 2,83; con kana 2,93 →
1,42. La vuelta es más rápida que la base en las seis.

La suite del informe (5548 passed, 335 skipped, sobre `9dcee73`) suma el
mismo total que la mía. No determiné por qué en su entorno se saltean más.
En el mío, las 90 pruebas de `tests/test_catalogo3.py` corren todas, la de
node incluida; entre mis salteadas está `test_backup1a` («sin Postgres 16
local»).

Las tres causas quedan cerradas. Un origen no reconocido conserva el NCM,
el historial, la memoria y el catálogo, y hay aviso. NFKC da la misma clave
para µ/μ, medio ancho, ㎜ y ℃. El lookup no es más lento que la base.

### Adversarios (sin red, GEMINI_API_KEY vacía)

- **H1 (reclasificado abajo: es la causa de la devolución).** La memoria del cliente
  (`client_memory.py:286-287`) elige la fila de mayor parecido sin un orden
  explícito. Ante un empate devuelve la primera, aunque tenga otro NCM u
  otro origen:
  - «Cable 2,5mm2» con BR devolvió 85444900 CN;
  - «Filtro ABC-10» devolvió JP en vez de DE.

  En la base pasa lo mismo con el texto idéntico y dos NCM. Por eso, al
  reclasificar un producto, la memoria sigue sugiriendo el NCM viejo.
  Clasificación de las 10:40, retirada: «pieza propia, no devolución».
- **H2, condición de publicación.** Si la migración encuentra un choque,
  deja las dos filas. El informe lo declaró sólo como «fila huérfana», pero
  pasa más que eso: el texto exacto lee la otra fila, y al confirmarlo pisa
  su NCM, su origen y su descripción, y la vieja queda huérfana. Al
  publicar, si el primer arranque dice que quedan N filas por un choque con
  N > 0, se frena antes de que alguien confirme.
- **H3, riesgo menor.** Si dos versiones escriben las claves a la vez (por
  el salteo del lock o porque queda una instancia vieja), la confirmación
  queda varada. No verifiqué si Railway deja la instancia vieja sirviendo.
- **H4, riesgo con seguimiento.** «Codo 1½ PVC» da `codo 11 2 pvc`, la misma
  clave que «11/2». Contra «1 1/2» el parecido baja de 1,0 a 0,67, con un
  umbral de 0,8; «2½"» contra «2 1/2"» da 0,5. La base acertaba de
  casualidad, porque convertía «1½» en «1». Se pierde una sugerencia, pero
  no entra un dato malo.
- **El extractor acepta orígenes hechos de cifras.**
  `_origen_desde_factura` ya no rechaza los orígenes hechos sólo de cifras.
  «212» da US, «310» y «0310» dan CN, y «100», «12» y «2024» dan vacío. Es
  lo que pide D158, y lo cubre un caso con su sabotaje. La columna del
  Excel se elige por su encabezado (`main.py:5571`). Es un riesgo.
- **Preexistente.** `main.py:8244` y `8844` guardan el origen crudo en
  `origen_frecuente`. Va con D159 (ORIGEN-2).
- **Menores, que son riesgo:**
  - el recorte de espacios en JS es cuadrático;
  - los avisos no tienen tope (119 KB en el peor caso);
  - `get_pais_codigo` y `pais_origen` de `/generate_maria` ya estaban en
    la base y no tienen pantalla.
- **Verificado que está bien:**
  - un origen no reconocido conserva el que ya estaba;
  - `operation_items.origen` pasa a text en PG;
  - una migración cortada no deja nada a medias;
  - C.UTF-8 e ICU eligen las mismas filas;
  - la migración se puede correr dos veces.

**Corrección del informe:** SUR→SR es Surinam (232), no Sudáfrica (ZAF→159).
Que SUR sea ambiguo sigue siendo un supuesto reversible.

## Retiro de la aceptación (2026-11-10 10:45 UTC)

La PM clasificó H1 como preexistente sin correr en la base los casos que
el NFKC iguala. Al correrlos, la base acertaba. Es un escape de la PM:
aceptó sin reproducir en la base lo que llamó «ya pasaba antes».

**Causa.** `lookup_client_memory` (`client_memory.py:276-289`) trae las
filas del cliente sin orden y se queda con la primera de mayor parecido.
La clave única incluye el NCM, así que el mismo texto con otro NCM es
otra fila, y confirmar suma a su propia fila sin cambiar cuál gana. Ante
un empate gana la que la base devuelva primero. El NFKC que pidió la PM en la causa 2 sumó a los empates ² contra
2 y el ancho completo, que la base distinguía. **Camino de hoy:** la misma
factura leída del PDF («2,5mm²») y tipeada a mano («2,5mm2»), con dos NCM.

**Por qué cambia entre corridas.** La consulta no tiene orden, y en SQLite
hay dos índices que la sirven (`ix_cph_owner_client` y
`ux_cph_owner_client_clave`). Con `EXPLAIN QUERY PLAN`, en tres corridas
SQLite usó uno, el otro y el primero. Con el primero las filas salen en el
orden de guardado; con el segundo, en el orden de la clave (un hash). No
determiné qué decide el índice: no es `PYTHONHASHSEED`, porque con la misma
semilla salió cada uno. En PG la consulta no corrió: **H1B y H1C, en PG no
corridos.** En el producto, el resultado depende de un orden que nadie
fijó.

**Por qué no lo vieron mis 41 negativos.** Cubrían orígenes nuevos en
guardar, PUT y lote (7 × 3), claves que NFKC iguala (8) y que no (4), y
lookup con una sola fila guardada (8). Ninguno guardaba dos filas que
empatan.

Pruebas en el scratchpad de la PM (`test_pm_h1b.py`, `test_pm_h1c.py`,
`test_pm_largo.py`), con `client` de `tests/test_prelaunch_block2.py`.
H1B guarda primero la otra fila y después la buscada; H1C, al revés. Las
dos buscan con el texto exacto de la buscada y la confirman tres veces.
Salida entera, dos corridas en cada árbol:

```
== corrida 1 wt-cat3v-base 07504e09
H1B Cable 2,5mm2 85444200 BR -> 85444200 BR | tras confirmar 3 veces -> 85444200 BR
H1B Filtro ABC-10 84213900 DE -> 84213900 DE | tras confirmar 3 veces -> 84213900 DE
H1B Capacitor 10μF 50V 85322500 JP -> 85322400 CN | tras confirmar 3 veces -> 85322400 CN
H1B Tuerca M6 73181500 TW -> 73181500 TW | tras confirmar 3 veces -> 73181500 TW
H1C Cable 2,5mm2 85444200 BR -> 85444200 BR | tras confirmar 3 veces -> 85444200 BR
H1C Filtro ABC-10 84213900 DE -> 84213900 DE | tras confirmar 3 veces -> 84213900 DE
H1C Capacitor 10μF 50V 85322500 JP -> 85322400 CN | tras confirmar 3 veces -> 85322400 CN
H1C Tuerca M6 73181500 TW -> 73181500 TW | tras confirmar 3 veces -> 73181500 TW
LG e acero con chaveta norma IEC modelo 80A -> 85015220 1.0
LG  acero con chaveta norma IEC modelo 280S -> 85015220 1.0
LG  acero con chaveta norma IEC modelo 132S -> 85015220 1.0
3 passed, 3 warnings in 2.13s =========================
== corrida 1 wt-cat3v ec0092a7
H1B Cable 2,5mm2 85444200 BR -> 85444900 CN | tras confirmar 3 veces -> 85444900 CN
H1B Filtro ABC-10 84213900 DE -> 84212300 JP | tras confirmar 3 veces -> 84212300 JP
H1B Capacitor 10μF 50V 85322500 JP -> 85322400 CN | tras confirmar 3 veces -> 85322400 CN
H1B Tuerca M6 73181500 TW -> 73181500 TW | tras confirmar 3 veces -> 73181500 TW
H1C Cable 2,5mm2 85444200 BR -> 85444900 CN | tras confirmar 3 veces -> 85444900 CN
H1C Filtro ABC-10 84213900 DE -> 84212300 JP | tras confirmar 3 veces -> 84212300 JP
H1C Capacitor 10μF 50V 85322500 JP -> 85322400 CN | tras confirmar 3 veces -> 85322400 CN
H1C Tuerca M6 73181500 TW -> 73181500 TW | tras confirmar 3 veces -> 73181500 TW
LG e acero con chaveta norma IEC modelo 80A -> 85015220 0.919
LG  acero con chaveta norma IEC modelo 280S -> 85015220 0.919
LG  acero con chaveta norma IEC modelo 132S -> 85015220 1.0
3 passed, 3 warnings in 2.50s =========================
== corrida 2 wt-cat3v-base 07504e09
H1B Cable 2,5mm2 85444200 BR -> 85444200 BR | tras confirmar 3 veces -> 85444200 BR
H1B Filtro ABC-10 84213900 DE -> 84213900 DE | tras confirmar 3 veces -> 84213900 DE
H1B Capacitor 10μF 50V 85322500 JP -> 85322400 CN | tras confirmar 3 veces -> 85322400 CN
H1B Tuerca M6 73181500 TW -> 73181600 CN | tras confirmar 3 veces -> 73181600 CN
H1C Cable 2,5mm2 85444200 BR -> 85444200 BR | tras confirmar 3 veces -> 85444200 BR
H1C Filtro ABC-10 84213900 DE -> 84213900 DE | tras confirmar 3 veces -> 84213900 DE
H1C Capacitor 10μF 50V 85322500 JP -> 85322500 JP | tras confirmar 3 veces -> 85322500 JP
H1C Tuerca M6 73181500 TW -> 73181500 TW | tras confirmar 3 veces -> 73181500 TW
LG e acero con chaveta norma IEC modelo 80A -> 85015220 1.0
LG  acero con chaveta norma IEC modelo 280S -> 85015220 1.0
LG  acero con chaveta norma IEC modelo 132S -> 85015220 1.0
3 passed, 3 warnings in 2.28s =========================
== corrida 2 wt-cat3v ec0092a7
H1B Cable 2,5mm2 85444200 BR -> 85444900 CN | tras confirmar 3 veces -> 85444900 CN
H1B Filtro ABC-10 84213900 DE -> 84212300 JP | tras confirmar 3 veces -> 84212300 JP
H1B Capacitor 10μF 50V 85322500 JP -> 85322400 CN | tras confirmar 3 veces -> 85322400 CN
H1B Tuerca M6 73181500 TW -> 73181600 CN | tras confirmar 3 veces -> 73181600 CN
H1C Cable 2,5mm2 85444200 BR -> 85444200 BR | tras confirmar 3 veces -> 85444200 BR
H1C Filtro ABC-10 84213900 DE -> 84213900 DE | tras confirmar 3 veces -> 84213900 DE
H1C Capacitor 10μF 50V 85322500 JP -> 85322500 JP | tras confirmar 3 veces -> 85322500 JP
H1C Tuerca M6 73181500 TW -> 73181500 TW | tras confirmar 3 veces -> 73181500 TW
LG e acero con chaveta norma IEC modelo 80A -> 85015220 0.919
LG  acero con chaveta norma IEC modelo 280S -> 85015220 0.919
LG  acero con chaveta norma IEC modelo 132S -> 85015220 1.0
3 passed, 3 warnings in 2.28s =========================
```

La otra fila de cada caso es «Cable 2,5mm²» 85444900 CN, «Filtro ＡＢＣ-10»
84212300 JP, «Capacitor 10µF 50V» (micro) 85322400 CN y «Tuerca M6»
73181600 CN.

- En la base, ²/2 y ancho completo aciertan siempre (8 de 8). En la vuelta
  fallan en 6 de 8: es la regresión.
- µ/μ y el texto idéntico con otro NCM fallan también en la base, y el
  resultado cambia entre corridas. Confirmar no lo arregla nunca.
- **Tuerca M6 (texto idéntico): lo esperado antes de confirmar es lo
  último guardado.** En H1B es TW; en H1C es CN. El TW de H1C antes de
  confirmar no es un acierto: salió la primera fila guardada.
- **Prueba larga (LG).** Se guardó un motor de 5,5 kW, modelo 132S, con
  NCM 85015220. Al pedir uno de 0,75 kW (80A) o de 75 kW (280S), las dos
  versiones sugieren el mismo NCM: la base con 1.0 y la vuelta con 0.919.
  Ya pasaba antes y la vuelta no lo empeora, así que es un riesgo.
- **Bench.** En 430 caracteres, matches_cli pasa de 13 a 20. Es
  vocabulario compartido del bench, todo con el mismo NCM: no hay segunda
  causa.

Lo demás de la vuelta queda como está arriba: las tres causas de
`f4ade80`, H2 como condición de publicación, H3 y H4, los menores y la
corrección de SUR.

## Vuelta sobre `e81b961` (devolución `973c489`), 2026-11-10 13:05 UTC

Producto de la vuelta: sólo `lookup_client_memory`
(`client_memory.py`, +12/−9). Base para el rojo: `b7c4c85`.

**Lo del informe, reproducido**

| Qué | Salida |
|---|---|
| `chequeo-6 b7c4c854 e81b961b` | `producto +12/−9`, `arnés +166/−4`, historia vacío, `avisos: 0`: igual al informe |
| `tests/test_catalogo3.py` (SQLite) | `104 passed, 3 warnings in 26.94s` |
| arnés PG 16 (`catalogo3_postgres.py`), mi PG en 127.0.0.1:55432 | 10 OK, `todo OK`, salida=0 |
| `sabotajes/catalogo3.sh e81b961b` | 50 líneas ROJO, `fallas: 0`, salida=0 |

Mi primera corrida del arnés PG cayó en el arranque: le faltó
`ENVIRONMENT=test` en mi entorno («DATABASE_URL no está definida y
ENVIRONMENT no es de desarrollo»). Es mío, no del arnés: con las variables
del informe dio lo de arriba.

**Mi prueba, con ejemplos propios** (no los de la devolución). El script
llama a `upsert_client_product_history` y `lookup_client_memory`, cada
guardado y cada búsqueda en su propia sesión y commit, contra SQLite o PG
(base propia `pm_e81` / `pm_b7c`, sin FK). Pares que empatan en parecido
1.000 y tienen otra clave guardada:

- «Tubo 20m³» / «Tubo 20m3», buscando además «Tubo 20m₃»;
- «Válvula ＸＹ-5» / «Válvula XY-5», y «Válvula XY－5»;
- «Sensor 5㎜ inductivo» / «Sensor 5mm inductivo», y «Sensor ５mm inductivo»;
- «Motor Ⅳ trifásico» / «Motor IV trifásico», y «Motor ⅠV trifásico»;
- «Arandela ⑤mm plana» / «Arandela 5mm plana», y «Arandela ５mm plana».

Por cada par: regla 1 en los dos órdenes de guardado, y sigue ganando el
idéntico después de confirmar dos veces la otra; regla 2 con A/B/A/B y el
tercer texto; regla 3 con las dos filas a la misma hora, cuatro corridas
en los dos órdenes; una fila sin fecha pierde contra una fecha de hace 400
días, en los dos órdenes. Además, dos pares que para la regla son el mismo
texto (espacio duro, «Perno M8 zincado», y ligadura, «Junta ﬂexible»):
A/B/A, gana la última confirmada buscando cualquiera de los dos.

| Producto | SQLite | PG 16 |
|---|---|---|
| `e81b961` | 72 OK, `fallas: 0` | 72 OK, `fallas: 0` |
| `b7c4c85` (sin el arreglo) | 39 OK, 33 FALLA (15 idéntico, 14 tercer texto, 4 mismo texto) | 29 OK, 43 FALLA (19, 18, 6) |

Ejemplo del rojo, SQLite en `b7c4c85`: «FALLA identico B, guardado
'Tubo 20m³' primero -> ('73063000', 'CN') (esperaba ('73064000', 'IT'))»;
«FALLA C con A sin fecha, guardado 'Tubo 20m³' primero -> ('73063000',
'CN') (esperaba ('73064000', 'IT'))».

Un error mío en la primera versión del script: esperaba que «Perno M8»
y «Junta ﬂexible» ganaran como idénticos contra «Perno M8» y «Junta
flexible». Para la regla acordada (NFC, sin mayúsculas y con los espacios
normalizados) son el mismo texto, y la vuelta da la última confirmada, que
es lo pedido. Los pasé a su propio grupo; no es un defecto de la Dev.

**Adversario** (Sonnet alto, contexto nuevo, sin red, sin clave de
Gemini): ningún defecto reproducible. Probó 300 conjuntos al azar en 4
órdenes de inserción (`nondet= 0 exc= 0`), un oráculo propio (`checked 196
mismatch 0`), `ultima_vez` nula en una o las dos filas y contra fecha con
zona horaria, en SQLite y en tres casos de PG 16 (sin excepción, la fila sin
fecha pierde), búsquedas de 5000 caracteres, vacías, con medio par UTF-16,
NUL y emoji, y 3000 filas empatadas (0,141 s por consulta). No corrió el
barajado al azar en PG ni la suite completa. La regla 1 no hace ganar a una fila con menos parecido: el
desempate corre sólo entre las del puntaje máximo. Observación baja: una
fila sin `clave` nunca es idéntica (ya era así; la migración la completa
salvo en filas que no son producto). Hueco: la suite no tiene caso de
`ultima_vez` nula; lo cubre mi prueba, en los dos motores.

**No corrido por mí:** la suite completa (la Dev: «5562 passed, 335
skipped, 3 xfailed» sobre `e81b961`; el cambio es una función), `golden`,
`smoke_friccion.sh` y `ataque_aislamiento.sh` (el cambio no toca rutas,
sesión ni permisos).

<details><summary>Script de la PM (`pm_empates.py`)</summary>

```python
"""PM: empates de lookup_client_memory con ejemplos propios, en SQLite o PG.
uso: PYTHONPATH=<worktree> python -I pm_empates.py <url async>
"""
import asyncio, sys, uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import text, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from proyecto_maria.database.models import Base, ClientProductHistory
from proyecto_maria.services.client_memory import (
    upsert_client_product_history as up, lookup_client_memory as look, clave_de_producto, parecido)

# (A, B, C): A y B son dos filas; C empata con las dos y no es idéntico a ninguna
CASOS = [
    (("Tubo 20m³", "73063000", "CN"), ("Tubo 20m3", "73064000", "IT"), "Tubo 20m₃"),
    (("Válvula ＸＹ-5", "84818099", "JP"), ("Válvula XY-5", "84813000", "DE"), "Válvula XY－5"),
    (("Sensor 5㎜ inductivo", "85365090", "CN"), ("Sensor 5mm inductivo", "90318099", "DE"), "Sensor ５mm inductivo"),
    (("Motor Ⅳ trifásico", "85015200", "BR"), ("Motor IV trifásico", "85015300", "CN"), "Motor ⅠV trifásico"),
    (("Arandela ⑤mm plana", "73182200", "CN"), ("Arandela 5mm plana", "73182100", "KR"), "Arandela ５mm plana"),
]
# el mismo texto para la regla acordada (NFC, sin mayúsculas ni espacios de más): decide la última confirmada
MISMOS = [(("Perno\u00a0M8 zincado", "73181400", "CN"), ("Perno M8 zincado", "73181300", "TW")),
          (("Junta ﬂexible", "40169300", "CN"), ("Junta flexible", "40169990", "KR"))]
FALLAS = []


def chk(nombre, got, want):
    ok = got == want
    print(("OK   " if ok else "FALLA"), nombre, "->", got, "" if ok else f"(esperaba {want})")
    if not ok:
        FALLAS.append(nombre)


async def main(url):
    eng = create_async_engine(url)
    async with eng.begin() as c:
        await c.run_sync(Base.metadata.drop_all)
        await c.run_sync(Base.metadata.create_all)
    S = async_sessionmaker(eng, expire_on_commit=False)
    pg = eng.dialect.name == "postgresql"

    async def nueva():
        db = S()
        if pg:
            await db.execute(text("SET session_replication_role = replica"))  # sin FK: usuario/cliente ficticios
        return db

    async def guardar(cid, fila):
        async with await nueva() as db:
            r = await up(db, "u_pm", cid, fila[1], fila[0], origen=fila[2])
            await db.commit()
            assert r is not None, fila

    async def buscar(cid, t):
        async with await nueva() as db:
            r = await look(db, "u_pm", cid, t)
            return r and (r["ncm"], r["origen"])

    for A, B, C in CASOS:
        ka, kb, kc = (clave_de_producto(x) for x in (A[0], B[0], C))
        print(f"\n== {A[0]!r} / {B[0]!r} / C={C!r}  parecido A-B={parecido(ka, kb):.3f} C-A={parecido(kc, ka):.3f} C-B={parecido(kc, kb):.3f}")
        # regla 1 en los dos órdenes, y sigue ganando aunque la otra sea más nueva
        for orden in ((A, B), (B, A)):
            cid = "c" + uuid.uuid4().hex[:8]
            for f in orden:
                await guardar(cid, f)
            chk(f"identico A, guardado {orden[0][0]!r} primero", await buscar(cid, A[0]), (A[1], A[2]))
            chk(f"identico B, guardado {orden[0][0]!r} primero", await buscar(cid, B[0]), (B[1], B[2]))
            await guardar(cid, orden[0])
            await guardar(cid, orden[0])
            otro = B if orden[0] is A else A
            chk(f"identico {otro[0]!r} tras confirmar dos veces la otra", await buscar(cid, otro[0]), (otro[1], otro[2]))
        # regla 2: A/B/A con un texto que no es idéntico a ninguna
        cid = "c" + uuid.uuid4().hex[:8]
        for i, f in enumerate((A, B, A, B)):
            await guardar(cid, f)
            if i:
                chk(f"C tras confirmar {f[0]!r} ({i+1}.ª)", await buscar(cid, C), (f[1], f[2]))
        # regla 3: a la misma hora, el mismo resultado en los dos órdenes
        hora = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        res = []
        for orden in ((A, B), (B, A), (A, B), (B, A)):
            cid = "c" + uuid.uuid4().hex[:8]
            for f in orden:
                await guardar(cid, f)
            async with await nueva() as db:
                await db.execute(update(ClientProductHistory).where(ClientProductHistory.client_id == cid).values(ultima_vez=hora))
                await db.commit()
            res.append(await buscar(cid, C))
        chk("C a la misma hora, cuatro corridas", len(set(res)), 1)
        # sin fecha pierde contra con fecha, en los dos órdenes
        for orden in ((A, B), (B, A)):
            cid = "c" + uuid.uuid4().hex[:8]
            for f in orden:
                await guardar(cid, f)
            async with await nueva() as db:
                q = update(ClientProductHistory).where(ClientProductHistory.client_id == cid)
                await db.execute(q.where(ClientProductHistory.ncm == A[1]).values(ultima_vez=None))
                await db.execute(q.where(ClientProductHistory.ncm == B[1]).values(ultima_vez=hora - timedelta(days=400)))
                await db.commit()
            chk(f"C con A sin fecha, guardado {orden[0][0]!r} primero", await buscar(cid, C), (B[1], B[2]))
    for A, B in MISMOS:
        cid = "c" + uuid.uuid4().hex[:8]
        for f in (A, B, A):
            await guardar(cid, f)
            for t in (A[0], B[0]):
                chk(f"mismo texto {t!r} tras confirmar {f[0]!r}", await buscar(cid, t), (f[1], f[2]))
    await eng.dispose()
    print(f"\nfallas: {len(FALLAS)}")
    sys.exit(1 if FALLAS else 0)


asyncio.run(main(sys.argv[1]))
```

</details>
