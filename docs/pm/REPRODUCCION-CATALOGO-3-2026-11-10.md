# Reproducción de CATALOGO-3 (Dev MARIA), 2026-11-10

Producto e informe en `f4ade80`, base `07504e0`, rama `claude/dev-maria`.
Veredicto: **devolución** (arriba de `PARA-DEV-2.md`), por tres causas.

## Puertas del informe, reproducidas sobre `f4ade80`

| qué | salida |
|---|---|
| `test_catalogo3` + `test_despacho1b` + `test_despacho1c` | pasan |
| golden | `115 passed, 2 xfailed in 14.49s` |
| `compileall` | rc=0 |
| `catalogo3.sh` (sabotajes) | 25 ROJO, `fallas: 0` |
| arnés Postgres 16, `f4ade80` | 7 OK, `todo OK` |
| arnés Postgres 16, base `07504e0` | `5 fallas` (dos workers, varchar(3), migración, TAIWAN, CJK en dos filas): coincide |
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
en curso a las 02:36 UTC (iba por el 75 %, sin rojos hasta ahí); el resultado se suma acá al terminar. La devolución no depende de la suite.
