# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## OBSERVABILIDAD-1, vuelta de la devolución: **entregada** en `694f183` (2026-11-08), base `0231eee`

| SHA | qué |
|---|---|
| `df59756` | fix: la métrica guarda el molde de la ruta, y la migración confirma la columna y el índice por separado |
| `7fe33c5` | test: caso del molde para cada ruta con parámetro, fallas al confirmar en Postgres y sus sabotajes |
| `42dd9a6` | fix: el log nombra el paso de la migración que falló |
| `d7a57ac` | test: los moldes salen del openapi y la falla del índice se distingue |
| `2c52c83` | test: arreglos de la revisión de código en pruebas y sabotajes |
| `694f183` | test: dos sabotajes de Postgres vuelven a aplicar y a esperar el texto vigente |
| `328458d` | docs: borrador del informe, sin entregar |
| este commit | docs: el informe |

**Producto +35/−15** (sólo `proyecto_maria/main.py`). **Arnés +215/−25.** Suma
20 líneas netas: casi todas son el segundo `try` del índice, con su log, que
la devolución pide aparte.

Los cuatro puntos de la devolución:

1. `MetricsMiddleware` guarda `request.scope["route"].path_format`, por
   ejemplo `/api/invitations/{token}`. Si el pedido no coincide con ninguna
   ruta, guarda `<sin ruta>`.
2. La columna y el índice van en transacciones separadas, y cada una pone su
   `SET LOCAL lock_timeout = '5s'`. En SQLite no se pone.
3. «agregada columna» y «agregado indice» se imprimen después de salir del
   `engine.begin()` de cada uno, o sea después del commit. Si falla el
   índice, la columna queda y el log dice que falló el índice, no la columna.
4. Los tres riesgos van abajo, sin cambiar.

## Decisiones

- **D139. El panel de dev muestra `<sin ruta>` vacío, y antes ya pintaba caminos sin escapar.**
  `dev_dashboard.html:260` arma la tabla con `innerHTML` y el endpoint sin
  escapar. Con esta pieza el texto `<sin ruta>` se lee como una etiqueta y la
  celda queda vacía. Antes de la pieza era peor: un camino pedido por
  cualquiera, como `/<img src=x onerror=…>`, llegaba crudo al panel del
  admin. Esta pieza ya lo achica, porque ahora sólo llegan moldes de la app
  o `<sin ruta>`.
  - (a) Escapar el texto en el panel, en una pieza aparte. **Recomiendo (a):**
    es el arreglo de raíz y no le cambia el alcance a esta pieza.
  - (b) Cambiar la constante por algo sin `<>`, como `(sin ruta)`.
  - (c) Dejarlo como está.
- **D140. Las filas viejas de `api_logs` tienen el camino crudo**, con
  tokens, hashes y CUIT, de antes de esta pieza.
  - (a) Reescribirlas al molde. **Recomiendo (a) sólo si Emi quiere conservar
    la historia.** Es una migración de datos con revisión fuerte.
  - (b) Purgarlas.
  - (c) Dejarlas hasta que las rote la retención, si hay.

  No toqué ninguna: la devolución no lo pide.

Siguen abiertas:
- **D131**, de EMAIL-1, va a Emi.
- **D136**: no traigo tu rama hasta que INTEGRAR-1 esté aceptada.

D138 ya la decidiste. La próxima D libre es la D141.

Supuestos reversibles:

1. **`<sin ruta>` cubre también pedidos que nunca llegan a una ruta**: el
   preflight de CORS, el 400 de `_RutaSinNul`, el 307 de la barra final y el
   429 del límite. Ninguno deja el camino crudo.
2. **Los moldes del caso salen de `app.openapi()["paths"]`.** Con FastAPI
   0.162, las rutas de los routers incluidos (admin y quotes) no quedan
   sueltas en `app.routes`. El caso comprueba dos cosas: que todas las rutas
   sueltas con parámetro estén en el openapi, y que estén
   `/api/quotes/public/{hash}` y `/api/admin/errors/top/{limit}`. Una ruta
   con `include_in_schema=False` queda afuera; hoy no hay ninguna con
   parámetro.

## Comandos

```bash
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
# casos: «10 passed»
python -m pytest -q --no-cov tests/test_observabilidad1.py
# arranque con uvicorn en SQLite: termina en «fallas 0»
python scripts/testing/observabilidad1_arranque.py
# arranque en Postgres 16 descartable (crea y borra su base): «fallas 0», 7 secciones
python scripts/testing/observabilidad1_arranque.py postgresql://cdi@127.0.0.1:55432/postgres
# sabotajes (necesita Postgres): 24 «ROJO», al final «sabotajes sin rojo: 0; no corridos: 0», salida 0
./scripts/testing/sabotajes/observabilidad1.sh
# rojo del molde en la base: «la métrica guardó otra cosa que el molde: ['/api/admin/errors/top/7', …]»
git show 0231eee:proyecto_maria/main.py > /tmp/main-base.py   # y ponerlo en lugar de main.py para correr el caso
```

## Puertas

| corrida | SHA | salida exacta |
|---|---|---|
| suite completa | `694f183` | `5434 passed, 335 skipped, 3 xfailed, 111 warnings in 1038.99s (0:17:18)`, salida 0 |
| `compileall -q proyecto_maria` | `694f183` | sin salida, salida 0 |
| smoke_friccion | `694f183` | `==> OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido`, salida 0 |
| arranque SQLite | `694f183` | 19 `OK`, `fallas 0`, salida 0 |
| arranque Postgres 16 | `2c52c83` (desde ahí cambió sólo el script de sabotajes) | 60 `OK`, `fallas 0` |
| sabotajes | `694f183` | 24 `ROJO`, `sabotajes sin rojo: 0; no corridos: 0`, salida 0 |
| sabotajes | `2c52c83` | 23 `ROJO`, 1 `ROJO?` y 1 `ROTO`: `sabotajes sin rojo: 2; no corridos: 0` (ver abajo) |
| rojo del molde: caso nuevo contra el producto de la base | `0231eee` | `1 failed, 9 deselected`. `AssertionError: la métrica guardó otra cosa que el molde: ['/api/admin/errors/top/7', '/api/admin/logs/recent/7', '/api/catalog/zq9', '/api/catalog/zq9/productos', …]` |
| rojo de las transacciones: arranque PG nuevo contra el producto de una sola transacción | antes de `df59756` | `fallas 4`: en «falla al confirmar ALTER TABLE», `FALLA \| y el log no dice que la agregó` y `FALLA \| y el log no lo anuncia`; en «falla al confirmar CREATE INDEX», `FALLA \| la columna queda: None` y `FALLA \| y el log no lo anuncia` |
| rojo del log del índice: caso nuevo contra `7fe33c5` | `7fe33c5` | `1 failed, 9 passed`. `AssertionError: el log no dice que falló el índice: 'ERROR root:main.py:1625 [OBSERVABILIDAD-1] no se pudo agregar api_logs.owner_username; …` |

La corrida de sabotajes en `2c52c83` tuvo dos sin rojo, y las dos eran del
script, no del producto:

- `ROJO?` en «en Postgres no agrega la columna»: dio rojo, pero sin la línea
  que esperaba. En `2c52c83` cambié el texto del chequeo del arranque y no el
  del sabotaje.
- `ROTO` en «en Postgres espera el lock sin límite»: el patrón dejó de ser
  único cuando el índice sumó su propio `lock_timeout`.

Las dos se arreglaron en `694f183`, y la corrida de ese SHA da 0 sin rojo.

**Corrido y no corrido:**
- `/security-review` lo hice a mano sobre el diff: no encontré
  vulnerabilidades nuevas. La pieza achica la exposición, porque deja de
  guardar tokens, hashes y CUIT. Lo de `<sin ruta>` en el panel va en D139.
- `ataque_aislamiento.sh` no lo corrí: la pieza no toca sesión, permisos ni
  datos de clientes.

## Hallazgos de la autorrevisión

| quién | hallazgo | qué hice |
|---|---|---|
| `/code-review high` | SyntaxError en el sabotaje del lock | Arreglado en `2c52c83` |
| `/code-review high` | CORS, el 400 de `_RutaSinNul`, el 307 y el 429 quedan como `<sin ruta>` | Supuesto 1 |
| `/code-review high` | Dos workers que arrancan a la vez pueden competir en `CREATE INDEX IF NOT EXISTS` | Riesgo 5 |
| `/code-review high` | El chequeo `indice_con_tabla_tomada` miraba mal | Arreglado en `2c52c83` |
| `/code-review high` | El docstring del caso no decía lo que prueba | Arreglado en `2c52c83` |
| `/code-review high` | Dos moldes podían dar el mismo camino de ejemplo y tapar uno | Assert agregado en `2c52c83` |
| `/code-review high` | Filas viejas con caminos crudos | D140 |
| `adversario-sonnet-alto` (Sonnet, alto) | Media: `<sin ruta>` y los caminos sin escapar en el panel | D139 |
| `adversario-sonnet-alto` (Sonnet, alto) | Filas viejas con caminos crudos | D140 |
| `adversario-sonnet-alto` (Sonnet, alto) | La falla del índice decía que faltaba la columna | Arreglado en `42dd9a6`, con su rojo antes |
| `adversario-sonnet-alto` (Sonnet, alto) | `lock_timeout` no limita lo que tarda en construirse el índice | Riesgo 4 |
| `adversario-sonnet-alto` (Sonnet, alto) | `include_router(prefix=…)` dejaría el molde sin el prefijo | Desmentido: el `path_format` del scope ya trae el prefijo, y el caso lo cubre con `/api/admin/...` |
| `adversario-sonnet-alto` (Sonnet, alto) | La lista de rutas no salía de la app | Arreglado en `d7a57ac`: sale del openapi |
| yo | En `df59756` el log de producto llevaba la etiqueta `[OBSERVABILIDAD-1]`, que §6 no permite | Sacada en `42dd9a6`; el grep de historia da vacío |

## Riesgos

Los tres de la devolución, sin cambiar:

1. **La espera de 5 s detrás de otra transacción.** Si otra transacción tiene
   tomada `api_logs`, el arranque espera hasta 5 s por cada paso (columna e
   índice) y sigue sin el paso.
2. **Un índice inválido o parcial se da por bueno.** Basta un índice cuya
   primera columna sea `owner_username`; no se mira `indisvalid` ni el
   predicado.
3. **Un camino de más de 200 caracteres pierde su métrica en Postgres.** Con
   esta pieza sólo pasa si un molde de la app pasa los 200; hoy ninguno se
   acerca.

Además:

4. **Media, del adversario.** `lock_timeout` limita la espera del lock, no la
   construcción del índice. Con una `api_logs` muy grande, `CREATE INDEX`
   (sin `CONCURRENTLY`) bloquea las escrituras de métricas mientras dura.
5. **Baja, de `/code-review`.** Con varios workers o réplicas que arrancan a
   la vez, dos `CREATE INDEX IF NOT EXISTS` pueden chocar, y uno loguea la
   falla del índice. Hoy hay 1 worker sin `REDIS_URL` y `numReplicas` 1. Si
   cambia, se mitiga con `pg_advisory_xact_lock`.
6. **El caso SQLite de la falla del índice no distingue el defecto de
   juntar las transacciones.** En SQLite, el DDL de una transacción que falla
   no siempre se deshace igual que en Postgres. La separación la distinguen
   las dos secciones «falla al confirmar» del arranque en Postgres, que dan
   rojo con una sola transacción (tabla de puertas).

## chequeo-6

```
chequeo-6 0231eee..694f183: avisos para mirar, no un veredicto
producto +35/−15
arnés +215/−25
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12086 → 12106
avisos: 0
```

## Archivos de producto

`proyecto_maria/main.py`: `_migrate_add_api_logs_owner_column` y `MetricsMiddleware`.

## Lo que sigue

ORG-1+D40.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797wNM (send_message next, «Dev MARIA: …»), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. OBSERVABILIDAD-1 entregada en 694f183 (informe en este archivo, base 0231eee). SMOKE-1 entregada en 00df4de; RESET-3 en 8fda3d2; AVISOS-2b aceptada sobre aa115f4 sin integrar. Abiertas: D131 (de EMAIL-1, va a Emi), D136 (decidida: no traigo tu rama hasta que INTEGRAR-1 esté aceptada), D139 (panel sin escapar, recomiendo a), D140 (filas viejas con camino crudo). La próxima D libre es la D141. Sigue ORG-1+D40, después D102. Nunca main, nada se publica sin el «dale» de Emi para el SHA, sin secretos, sólo datos inventados.
