# Reproducción de CATALOGO-3 (Dev MARIA), 2026-11-10

Producto e informe en `f4ade80`, base `07504e0`, rama `claude/dev-maria`.
Veredicto: **devolución** (arriba de `PARA-DEV-2.md`), por tres causas.
Vuelta en `ec0092a` (informe `b7c4c85`, base de la vuelta `1345ca7`):
**aceptada** (sección «Vuelta», al final).

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
| `chequeo-6.py 07504e0 ec0092a` | producto +152/−99, 1 AVISO explicado en el informe, historia vacía; igual al informe |
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

- **H1, preexistente.** La memoria del cliente
  (`client_memory.py:286-287`) elige la fila de mayor parecido sin un orden
  explícito. Ante un empate devuelve la primera, aunque tenga otro NCM u
  otro origen:
  - «Cable 2,5mm2» con BR devolvió 85444900 CN;
  - «Filtro ABC-10» devolvió JP en vez de DE.

  En la base pasa lo mismo con el texto idéntico y dos NCM. Por eso, al
  reclasificar un producto, la memoria sigue sugiriendo el NCM viejo.
  Clasificación: pieza propia para Emi (MEMORIA-ORDEN-1: orden explícito
  y, ante un empate, primero el texto exacto). No es devolución.
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

