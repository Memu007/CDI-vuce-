# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Entrega CATALOGO-4, desempate del catálogo del proveedor, sobre `631bed21` (2026-11-19 16:38 UTC)

**Resultado.** Base `f3c84f7d`. Los cuatro criterios se cumplen en `631bed21`. `producto +36/−19`
(`catalog_service.py` y `client_memory.py`). No hay D nuevas: lo que decidís vos son los supuestos 1 y
2 y si aceptás el riesgo 1. Los números salen de los logs de abajo.

- **1. Lo idéntico gana primero.** El camino exacto no cambió: se busca por clave antes de mirar el
  parecido. Lo prueba la quinta fila del caso, en los dos órdenes de carga.
- **2. El empate.** Ante dos productos igual de parecidos gana el último confirmado. A la misma hora, o
  sin fecha, gana la clave del producto, que es única en el catálogo del proveedor. Una fila sin fecha
  pierde contra una fechada. El caso, `tests/test_catalogo4.py`, lleva la familia como datos de una
  sola prueba: tres empates (latín, «²» y letra ancha) y dos que no empatan. Cada fila se carga en los
  dos órdenes y se mira el NCM sugerido en diez momentos:
  - después de cada una de las cuatro confirmaciones;
  - con las dos filas a la misma hora;
  - con sólo una fechada, una vez cada una;
  - sin fecha;
  - en un lote nuevo, y el mismo lote otra vez.

  `scripts/testing/catalogo4_postgres.py` corre ese mismo escenario contra un Postgres 16 descartable:
  «fallas: 0».
- **3. Lo que no empata no cambia.** Las dos filas sin empate pasan igual en la base y ahora. La
  medición al azar, con semilla fija, compara la base y `1f3ec92c`, que tiene el mismo producto que `631bed21`:
  ```
  2000 consultas; sin empate: 1999, distinto ganador: 0; con empate: 1, distinto ganador: 1
  por tipo: {'exact': 896, 'fuzzy': 645, 'none': 459}
  ```
- **4. Negativo en el mismo SHA.** Vacié el arreglo en `631bed21`: `catalog_service.py` y
  `client_memory.py` como en la base.
  - SQLite: «1 failed». Fallan 6 filas, los 3 empates en los 2 órdenes: gana siempre el primero
    cargado, aunque se haya confirmado el otro después.
  - Postgres: salida 1, «fallas: 6».

  Además, 8 sabotajes, cada uno deshace una parte de la regla y da rojo (abajo).

**Cómo.**
- Usé tu sugerencia: un solo lugar para los dos. `el_mas_parecido` busca la fila más parecida y
  desempata sólo entre las empatadas y sólo por encima del umbral. Lo usan el catálogo del proveedor y la
  memoria del cliente.
- `confirmada` es la regla «sin fecha antes que con fecha, y después la más nueva», también para los
  dos. La memoria del cliente da lo mismo que antes: lo prueban `test_catalogo3.py` y `catalogo3.sh`.
- `save_products` sella todo el lote con la hora de la app. Antes, un producto nuevo tomaba la hora de
  la base, que en SQLite va al segundo: dos confirmaciones seguidas empataban y volvía a decidir el
  orden.

## Supuestos

1. **«Confirmar» es cualquier guardado del producto.** Cuenta `guardar-uso`, el lote, y el editor del
   catálogo. El editor siempre manda el NCM que se ve (`catalogo.js:308`), así que guardar una fila es
   confirmar su NCM. El adversario mostró que un `PUT` directo a la API con sólo el precio también mueve
   la fecha y hace ganar ese producto en un empate. Desde la pantalla no hay forma de mandar sólo el
   precio. Si querés que sólo cuente el NCM, son dos líneas en `update_product`, pero entonces la fecha
   que muestra el catálogo deja de moverse con las otras ediciones.
2. **A la misma hora gana la clave mayor** en orden alfabético. Es arbitrario pero fijo: no depende del
   orden de carga ni de la base. Los productos de un mismo lote quedan todos a la misma hora, y decide
   la clave.

## Commits

| commit | qué |
|---|---|
| `76206b35` fix | `el_mas_parecido`; el empate del catálogo por el último confirmado; la hora del lote |
| `d73cc737` test | `test_catalogo4.py` y `catalogo4_postgres.py` |
| `568ac241` test | `catalogo4.sh`; los sabotajes de `catalogo3.sh` siguen a `el_mas_parecido` |
| `b342c101` fix | lo que marcó `/code-review`: el desempate sólo por encima del umbral, `confirmada` en un solo lugar, la entrada del CHANGELOG |
| `1f3ec92c` test | los sabotajes siguen a `confirmada` y al umbral; uno nuevo del umbral |
| `631bed21` test | `test_catalogo3.py` mira las dos direcciones en el caso sin letras latinas (abajo). **Lo que se entrega** |
| informe | el commit siguiente |

## Pruebas

| qué | SHA | resultado |
|---|---|---|
| `test_catalogo4`, `test_catalogo3`, `test_catalogo_largo1/2`, `test_guardar1/2`, desde un worktree limpio | `631bed21` | «216 passed, 5 warnings in 83.13s (0:01:23)» |
| suite completa, desde un worktree limpio | `631bed21` | «6226 passed, 110 skipped, 3 xfailed, 111 warnings in 1318.14s (0:21:58)», worktree sin cambios |
| `e2e_maria.sh`, desde ese worktree | `631bed21` | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» |
| `catalogo4.sh` | `631bed21` | 8 «ROJO», «sabotajes sin rojo: 0» |
| `catalogo3.sh` | `631bed21` | 65 «ROJO», «fallas: 0»; en `1f3ec92c` daba «fallas: 1» (abajo) |
| `catalogo4_postgres.py` en PG16 | `631bed21` | «fallas: 0» |
| negativo en SQLite y en PG16, arreglo vaciado | `631bed21` | SQLite «1 failed», 6 filas; PG salida 1, «fallas: 6» |
| medición de ganadores | `f3c84f7d` y `1f3ec92c` | arriba |
| costo sin parecido | `f3c84f7d`, `568ac241` y árbol de `b342c101` | abajo |
| chequeo-6 | `f3c84f7d..631bed21` | abajo, entero |

`catalogo4.sh`:
```
BASE  | casos: ======================== 1 passed, 5 warnings in 2.50s =========================
ROJO  | el empate lo decide el orden de las filas: «AssertionError», 1 casos
ROJO  | el último confirmado le gana a lo más parecido: «AssertionError», 1 casos
ROJO  | a la misma hora decide el orden de las filas: «AssertionError», 1 casos
ROJO  | una fila sin fecha le gana a una fechada: «AssertionError», 1 casos
ROJO  | lo que llega justo al umbral no se sugiere: «AssertionError», 1 casos
ROJO  | un producto nuevo toma la hora de la base, al segundo en SQLite: «AssertionError», 1 casos
ROJO  | cada producto nuevo del lote con su hora: «AssertionError», 1 casos
ROJO  | cada producto del lote que ya estaba con su hora: «AssertionError», 1 casos
sabotajes sin rojo: 0
```

**Un caso de `catalogo3.sh` dejó de distinguir su defecto.** En `1f3ec92c`, el sabotaje «el parecido
vuelve a ignorar las letras no latinas» quedó verde contra
`test_productos_sin_letras_latinas_con_la_misma_medida_no_se_pisan`. Con ese defecto los dos productos
empatan. El caso miraba una sola dirección («b 新» no toma el NCM de «a») y daba rojo sólo porque el
empate lo ganaba la primera fila cargada. Con el último confirmado gana «b», y el caso pasaba con el
defecto puesto. Otro caso lo seguía atrapando (`test_la_memoria_del_cliente_usa_la_misma_clave`).
En `631bed21` el caso mira las dos direcciones: con el producto, «2 passed»; con el sabotaje aplicado a
mano, «2 failed» con «assert '84714900' != '84714900'». En `catalogo3.sh` ese sabotaje vuelve a dar rojo. El producto no cambió.

Costo, medido con 100 consultas sin ninguna palabra en común contra 2000 filas de la memoria del
cliente:
- `568ac241`: 4,18–4,27 s, contra 3,28–3,38 s en la base. En ese SHA se desempataba entre todas las
  filas aunque ninguna llegara al umbral.
- Árbol de `b342c101`, intercalado con la base: 3,20–3,43 s, contra 3,45–3,48 s en la base.

El bench de `/api/catalog/lookup` (`bench_catalogo3_lookup.py 65`) no se movió: 1,11–1,15 s en los dos.

chequeo-6, entero:
```
chequeo-6 f3c84f7d..631bed21: avisos para mirar, no un veredicto
producto +36/−19
arnés +197/−7
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/catalog_service.py: 732 → 751
  proyecto_maria/services/client_memory.py: 308 → 306
avisos: 0
```

## Revisiones

| quién | sobre | hallazgos | qué hice |
|---|---|---|---|
| `adversario-opus-alto` | `568ac241` | 1 medio | supuesto 1 |
| `/code-review high` | `f3c84f7d..568ac241` | 4 | arreglé 3 en `b342c101`; el otro es el riesgo 1 |
| `/code-review medium` | `568ac241..1f3ec92c` | 2 menores | sin cambio; abajo |

El adversario:
- Reprodujo el negativo en SQLite y en un Postgres 16 propio: base «fallas: 6», `568ac241` «fallas: 0».
- Aplicó los sabotajes a mano: rojo los 7 de `catalogo4.sh` y los 2 de `catalogo3.sh` que cambiaban.
  Como control, dos cambios que no alteran el comportamiento quedaron verdes.
- Comprobó las fechas: SQLite las devuelve todas sin zona y Postgres todas con zona, así que la
  comparación no mezcla las dos clases. Una fila sin fecha nunca se compara con una fecha.
- El hallazgo, editar sólo el precio, es el supuesto 1.

El `/code-review high`:
1. **El desempate corría también por debajo del umbral.** Arreglado; las medidas están arriba.
2. **La regla de la fecha estaba escrita en dos lugares** (§6). Arreglado: ahora es `confirmada`.
3. **Faltaba la entrada del CHANGELOG.** Tenía razón: se me cayó del commit de producto. Está en
   `b342c101`.
4. **`vendor_nombre` sale de la primera fila.** Es el riesgo 1.

El `/code-review medium`, los dos sin cambio:
1. `el_mas_parecido` falla con una lista vacía si el umbral es 0 o menos. Hoy los dos llamados pasan
   0,80, y corregirlo obligaba a correr otra vez todas las puertas.
2. El encabezado de `catalogo4.sh` no nombra el sabotaje del umbral. Es un comentario.

## Comandos

```bash
VENV=/ruta/al/venv
PT="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider --timeout=300"
# 1. el caso, en 631bed21                                             → «1 passed»
$PT tests/test_catalogo4.py | tail -1
# 2. los negativos (1 min)                              → 8 «ROJO», «sabotajes sin rojo: 0»
PY=$VENV/bin/python scripts/testing/sabotajes/catalogo4.sh 631bed21 | grep -E "^(BASE|ROJO|VERDE|ROTO)|sin rojo"
# 3. el mismo escenario en un Postgres 16 descartable                  → «fallas: 0»
PY=$VENV/bin/python scripts/testing/con_pg16.sh sh -c '"$PY" scripts/testing/catalogo4_postgres.py "$BACKUP1A_PG_URL"' | tail -1
# 4. §6                                                → «producto +36/−19», «avisos: 0»
python3 docs/pm/herramientas/chequeo-6.py f3c84f7d 631bed21
```
Ya corrí los cuatro y dieron esa salida. La medición de ganadores y la de costo salen de guiones de mi
scratchpad: no te los pido, los resultados están arriba.

## Riesgos

1. **El nombre del proveedor sigue dependiendo del orden de las filas.** `match_items`,
   `get_vendor` y `get_vendor_by_id` toman `vendor_nombre` de la primera fila. Si un mismo proveedor
   se confirmó como «ACME S.A.» y después como «Acme SA», la pantalla puede mostrar uno u otro según la
   consulta. Viene de antes y no lo toqué. Si lo querés fijo, es otra pieza: alcanza con tomar el de
   la última confirmada.
2. **La medición al azar tiene un solo empate** en 2000 consultas, porque los empates son raros. Los
   empates los prueba la familia del caso, no la medición.
3. **Lo que no corrí:** nada de lo que pide la tarea.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`; rutina trig_01Ukttby1fc4sGVQfSn1jC9U (/respondio). PM principal session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `db37f430`. Aceptadas: las de antes (… PAISES-NOMBRES (D266) sobre `fa89e917`, D273 (a) y D274 (a); ORIGEN-ETIQUETA (D261) sobre `5a28c13c`). Pieza activa: CATALOGO-4 entregada sobre `631bed21`, espero el veredicto; supuestos 1 y 2 y riesgo 1 para la PM. Después, una a la vez y sólo con la anterior aceptada: CATALOGO-PAIS (origen con `etiqueta` en catalogo.js y clientes.js, TXT sin cambio), y ORIGEN-2 (migración VARCHAR(3), revisión fuerte, calculadora fuera). Próxima D: D275. Lecciones (además de las del historial de este archivo): el negativo de un arreglo va en el mismo SHA con el arreglo vaciado; cada número del informe sale de un log; un cambio de desempate puede dejar verde un sabotaje viejo que daba rojo sólo por el orden de las filas: correr todos los guiones de sabotaje vecinos sobre el SHA final; puertas con `setsid nohup` y un vigía de timeout largo; horas, sólo de `date -u` en el momento de escribirlas; los comandos para la PM se prueban antes de escribirlos. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe. Letra ancha: tabla U+FF01..FF5E, no NFKC («№» da Noruega).
