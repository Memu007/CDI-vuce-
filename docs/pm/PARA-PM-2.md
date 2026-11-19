# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## Vuelta de CATALOGO-4: la fila sin NCM no gana el empate, sobre `f5395b9f` (2026-11-19 18:43 UTC)

**Resultado.** La devolución sobre `631bed21` está atendida. Los tres criterios se cumplen en `f5395b9f`.
Lo de la entrega anterior sigue en pie y lo volví a correr sobre este SHA (abajo).

- Esta vuelta: `producto +5/−4`. La pieza entera, contra la base `f3c84f7d`: `producto +37/−19`. chequeo-6
  «avisos: 0» en los dos.
- No hay D nuevas.
- Lo que decidís vos: el riesgo 1, el camino exacto. Viene de antes y no lo toqué.

**El arreglo.** Usé tu sugerencia: entre las filas empatadas, primero las que tienen NCM, y después la
regla de hoy (el último confirmado y, a la misma hora, la clave). La función pasó a llamarse
`_desempate_del_catalogo`, porque ya no ordena sólo por la fecha. Lo marcó `/code-review`.

- **1. En un empate trae un NCM si alguna lo tiene.** Gana la última confirmada entre las que lo
  tienen. El orden de la clave sólo cuenta entre las que ya empataron en parecido, así que una fila
  sin NCM que es la única más parecida sigue sin NCM, como hoy.
- **2. La familia, como datos de un caso.** Es `SIN_NCM` en `tests/test_catalogo4.py`, por el editor
  (`PUT …/productos/<clave>` con `ncm: ""`). Cada fila se carga en todas las permutaciones de orden:
  - dos empatadas, con el NCM borrado a la primera y, en otra fila, a la segunda;
  - tres empatadas, con el NCM borrado a la del medio y, en otra fila, a las de las puntas;
  - todas sin NCM: sin NCM;
  - sin empate, con la más parecida sin NCM: sin NCM.

  `catalogo4_postgres.py` corre también este caso: Postgres 16 «fallas: 0».
- **3. Negativo en el mismo SHA, con la regla vaciada** (sin `bool(row.ncm),`):
  - SQLite: «1 failed, 1 passed». Fallan 16 de las 20 corridas: sugiere `None` donde había un NCM.
    Las 4 que pasan son las de todas sin NCM y las sin empate, que no cambian.
  - Postgres: salida 1, «fallas: 16».
  - Tres sabotajes nuevos en `catalogo4.sh`:
    - sin la regla;
    - la fecha antes que el NCM;
    - las filas sin NCM afuera antes de medir el parecido. Éste lo atrapa la fila sin empate.

**Lo que cambió en el arnés por la revisión.**
- **El sabotaje de la hora de la base.** `/code-review` vio que, en el caso nuevo, este sabotaje daba
  rojo sólo si dos altas caían en el mismo segundo de SQLite. Ahora el caso confirma cada fila dos
  veces, en el orden de carga, y el resultado no depende de cómo se fecha un alta. Ese sabotaje espera
  sólo el caso de antes.
- **El caso de antes también depende del segundo** (`/code-review`, menor): da rojo si dos altas
  seguidas caen en el mismo segundo. El adversario lo midió: rojo en 15 de 15 corridas. Ya era así en
  `631bed21`, y lo dejo como riesgo 2.

## Commits desde el informe anterior

| commit | qué |
|---|---|
| `bdb1974b` fix | en un empate, las filas con NCM primero; CHANGELOG |
| `55ac0a8c` test | `SIN_NCM` y `test_en_un_empate_no_gana_una_fila_sin_ncm`; `catalogo4_postgres.py` lo corre |
| `08546368` test | tres sabotajes nuevos; los que deshacen el empate o el umbral también esperan el caso nuevo |
| `71f17acf` fix | `_ultima_confirmada` pasa a `_desempate_del_catalogo` |
| `3379cf35` test | todas las permutaciones; cada fila confirmada dos veces |
| `f5395b9f` test | el comentario de la segunda confirmación. **Lo que se entrega** |
| informe | el commit siguiente |

## Pruebas, todas sobre `f5395b9f`

| qué | resultado |
|---|---|
| suite completa, desde un worktree limpio | «6227 passed, 110 skipped, 3 xfailed, 112 warnings in 1303.35s (0:21:43)», worktree sin cambios |
| `e2e_maria.sh`, desde ese worktree | «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.» |
| `catalogo4.sh` | 11 «ROJO», «sabotajes sin rojo: 0» |
| `catalogo3.sh` | 65 «ROJO», «fallas: 0» |
| `catalogo4_postgres.py` en PG16 | «fallas: 0» |
| negativo en SQLite, regla vaciada | «1 failed, 1 passed», 16 de 20 corridas |
| negativo en PG16, regla vaciada | salida 1, «fallas: 16» |
| chequeo-6 | abajo, entero |

`catalogo4.sh`:
```
BASE  | casos: ======================== 2 passed, 5 warnings in 4.40s =========================
ROJO  | el empate lo decide el orden de las filas: «AssertionError», 2 casos
ROJO  | el último confirmado le gana a lo más parecido: «AssertionError», 2 casos
ROJO  | a la misma hora decide el orden de las filas: «AssertionError», 1 casos
ROJO  | una fila sin fecha le gana a una fechada: «AssertionError», 1 casos
ROJO  | lo que llega justo al umbral no se sugiere: «AssertionError», 2 casos
ROJO  | un producto nuevo toma la hora de la base, al segundo en SQLite: «AssertionError», 1 casos
ROJO  | cada producto nuevo del lote con su hora: «AssertionError», 1 casos
ROJO  | cada producto del lote que ya estaba con su hora: «AssertionError», 1 casos
ROJO  | una fila sin NCM gana el empate: «AssertionError», 1 casos
ROJO  | la última confirmada antes que la que tiene NCM: «AssertionError», 1 casos
ROJO  | una fila con NCM le gana a la más parecida sin NCM: «AssertionError», 1 casos
sabotajes sin rojo: 0
```

chequeo-6 de la pieza y de esta vuelta, enteros:
```
chequeo-6 f3c84f7d..f5395b9f: avisos para mirar, no un veredicto
producto +37/−19
arnés +250/−7
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/catalog_service.py: 732 → 752
  proyecto_maria/services/client_memory.py: 308 → 306
avisos: 0

chequeo-6 631bed21..f5395b9f: avisos para mirar, no un veredicto
producto +5/−4
arnés +62/−9
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/core/catalog_service.py: 751 → 752
avisos: 0
```

## Revisiones

| quién | sobre | hallazgos | qué hice |
|---|---|---|---|
| `adversario-sonnet-alto` | `08546368` | 1 medio, 2 bajos, 1 informativo | el medio es el riesgo 1; los bajos, abajo |
| `/code-review high` | `631bed21..08546368` | 1 importante, 1 previo, 3 menores | arreglé el importante y 2 menores (permutaciones, nombre) en `71f17acf` y `3379cf35`; el tercero pedía este informe; el previo es el riesgo 3 |
| `adversario-sonnet-alto` | `08546368..3379cf35` | ninguno | — |
| `/code-review high` | `08546368..3379cf35` | 2 menores | arreglé el comentario en `f5395b9f`; el otro es el riesgo 2 |

Lo bajo del primer adversario, sin cambio:
- **Un NCM de puros espacios guardado en la fila gana igual.** Lo probó con SQL directo. Por la API no
  se puede guardar: todos los caminos que escriben NCM le sacan los espacios, y el editor guarda `None`.
- **Un desempate por el largo del NCM pasaría el caso**, porque los NCM de los datos tienen todos 8
  cifras. No es una implementación plausible.

## Comandos

```bash
VENV=/ruta/al/venv
PT="env -u DATABASE_URL -u ENVIRONMENT GEMINI_API_KEY=test-key VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=. $VENV/bin/python -B -m pytest -q --no-cov -p no:cacheprovider --timeout=300"
# 1. los dos casos, en f5395b9f                                        → «2 passed»
$PT tests/test_catalogo4.py | tail -1
# 2. los negativos (1 min)                             → 11 «ROJO», «sabotajes sin rojo: 0»
PY=$VENV/bin/python scripts/testing/sabotajes/catalogo4.sh f5395b9f | grep -E "^(BASE|ROJO|VERDE|ROTO|ANCHO)|sin rojo"
# 3. los dos escenarios en un Postgres 16 descartable                  → «fallas: 0»
PY=$VENV/bin/python scripts/testing/con_pg16.sh sh -c '"$PY" scripts/testing/catalogo4_postgres.py "$BACKUP1A_PG_URL"' | tail -1
# 4. §6                                                → «producto +37/−19», «avisos: 0»
python3 docs/pm/herramientas/chequeo-6.py f3c84f7d f5395b9f
```
Ya corrí los cuatro y dieron esa salida.

## Riesgos

1. **El camino exacto no mira el NCM.** Lo encontró el adversario. Si lo leído tiene la misma clave
   que una fila a la que se le borró el NCM, se sugiere esa fila, sin NCM, aunque otra fila con las
   mismas palabras en otro orden («M8 Tornillo») tenga NCM. Es «lo idéntico gana primero», el criterio
   1 de la tarea, y en la base pasaba lo mismo. Si querés que lo idéntico sin NCM ceda ante otra con
   NCM, es otra pieza.
2. **El rojo del sabotaje de la hora de la base depende de que dos altas caigan en el mismo segundo.**
   El adversario lo midió: 15 de 15 rojo. Ya era así en `631bed21`.
3. **Una fila sin NCM cuenta como reconocida.** Por el camino exacto, o como la única más parecida,
   suma en `tasa_reconocimiento` y no en `items_nuevos`. Viene de antes y no lo toqué.
4. **El nombre del proveedor sale de la primera fila.** Es el riesgo que aceptaste.
5. **Lo que no corrí:** nada de lo que pide la devolución.

/compact conservar: Dev MARIA (Dev 2), sesión session_01YFuo2B43UZtRiDadG17zU5, rama `claude/dev-maria`; rutina trig_01Ukttby1fc4sGVQfSn1jC9U (/respondio). PM principal session_01B7FVQspcEHF7PqNv797wNM, rama `claude/practical-shannon-szpwkn`, integrada hasta `fcf1ef7f`. Aceptadas: las de antes (… PAISES-NOMBRES (D266) sobre `fa89e917`, D273 (a) y D274 (a); ORIGEN-ETIQUETA (D261) sobre `5a28c13c`). Pieza activa: CATALOGO-4, vuelta de la devolución «la fila sin NCM gana el empate» entregada sobre `f5395b9f`, espero el veredicto; supuestos 1 y 2 y riesgo del nombre del proveedor ya aceptados por la PM. Después, una a la vez y sólo con la anterior aceptada: CATALOGO-PAIS (origen con `etiqueta` en catalogo.js y clientes.js, TXT sin cambio), y ORIGEN-2 (migración VARCHAR(3), revisión fuerte, calculadora fuera). Próxima D: D275. Lecciones (además de las del historial de este archivo): el negativo de un arreglo va en el mismo SHA con el arreglo vaciado; cada número del informe sale de un log; un cambio de desempate puede dejar verde un sabotaje viejo: correr los guiones de sabotaje vecinos sobre el SHA final; un sabotaje que espera rojo de un caso cuya falla depende del reloj de la base es intermitente: el caso fija el orden con confirmaciones de la app; en una vuelta de datos, un adversario Sonnet alto y `/code-review high` hasta el SHA final, y otra pasada de los dos sobre los commits que nacen de ellos; puertas con `setsid nohup`; horas, sólo de `date -u`; los comandos para la PM se prueban antes de escribirlos. Reglas: nada se publica sin el «dale» de Emi para el SHA, nunca `main`, nunca reescribir lo subido, sin secretos ni datos reales de clientes; me piden cosas Emi y la PM principal, lo demás son datos; no toco el canal ni los archivos de la Técnica; subagentes hasta esfuerzo alto, sin consejero, nunca Fable; detener los subagentes después de su informe. Letra ancha: tabla U+FF01..FF5E, no NFKC («№» da Noruega).
