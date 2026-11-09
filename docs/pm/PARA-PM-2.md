# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## OBSERVABILIDAD-1, devolución sobre `694f183`: **entregada** en `279ef26` (2026-11-09), base `0231eee`

La devolución tenía razón. La pieza cambió qué se guarda en `api_logs.endpoint`,
y el arnés de Postgres de ENTRADAS-3 seguía contando por el camino pedido. Lo
arreglé en el arnés. **El producto no cambió desde `694f183`.** Nada para
decidir dentro de la pieza; D150 es para después.

| SHA | qué |
|---|---|
| `df59756`, `42dd9a6` | fix (vuelta anterior, sin cambios) |
| `7fe33c5`, `d7a57ac`, `2c52c83`, `694f183` | test (vuelta anterior, sin cambios) |
| `328458d`, `e2dd1e2` | docs (vuelta anterior) |
| `d3a64f9` | test: el arnés de Postgres de ENTRADAS-3 lee el molde |
| `7fd0f5f` | test: cada pedido sin ruta cuenta su propia fila |
| `279ef26` | test: los sabotajes de ENTRADAS-3 leen la salida de Postgres como texto |
| este commit | docs: el informe |

**Producto +35/−15**, igual que en `694f183`. Las 20 netas ya las expliqué en
la vuelta anterior: son el segundo `try` del índice. **Arnés +252/−39.**

Los tres puntos de la devolución:

1. **Revisé todo lo que lee `api_logs.endpoint`.** El `grep` y lo que hice con
   cada resultado están en la tabla de abajo. Sólo el arnés de ENTRADAS-3 y
   sus sabotajes leían el camino. Los demás ya esperaban el molde o no miran
   la columna.
2. **`entradas3_postgres.py` sigue probando lo mismo.** Hay dos pedidos: el que
   lleva NUL (`/api/nul-a%00b`) y el de 300 caracteres que no existe. Cada uno
   suma una fila nueva con `endpoint = '<sin ruta>' and status_code = 404`, y
   ninguno da 500. `sabotajes/entradas3.sh` con Postgres da base verde y 12
   ROJO (tabla de puertas). El arnés de `694f183` sobre el mismo producto
   reproduce tu rojo: `FALLA | NUL en la ruta: 404; en api_logs: 0` y
   `FALLA | ruta de 300 caracteres: 404; en api_logs: 0`.
3. **`_guardable_en_pg`** tiene casos para dos de sus usos:
   - la guarda sobre `error_message`: `RuntimeError("e3\x00falla")` queda como
     `e3�falla`;
   - el `[:200]`: un molde de prueba de 313 caracteres queda recortado a 200.

   La llamada sobre `endpoint` no puede tener caso: es D150.

### Grep de lo que lee `api_logs.endpoint`

```bash
grep -rn --include='*.py' --include='*.sh' --include='*.sql' --include='*.html' --include='*.js' \
  -E "api_logs|\.endpoint\b|ApiLog" proyecto_maria scripts tests docs/pm/herramientas
```

| dónde | qué hace con `endpoint` | qué hice |
|---|---|---|
| `scripts/testing/entradas3_postgres.py` | contaba filas por el camino pedido | arreglado en `d3a64f9` y `7fd0f5f`: cuenta `<sin ruta>` y el molde |
| `scripts/testing/sabotajes/entradas3.sh:94-101` | sabotajes del registro en Postgres | adaptados en `d3a64f9`; en `279ef26` saqué el NUL de la salida |
| `scripts/testing/sabotajes/observabilidad1.sh` | sabotajes de la pieza | ya esperaban el molde: 24 ROJO |
| `scripts/testing/observabilidad1_arranque.py:256-265` | lee las filas nuevas de `/robots.txt` | queda: `/robots.txt` es su propio molde |
| `tests/test_observabilidad1.py:138` y `:258` | casos de la pieza | ya esperan el molde |
| `proyecto_maria/main.py:2697-2714` → `templates/dev_dashboard.html:260` | panel de dev, con `innerHTML` sin escapar | D139 (a): va en una pieza aparte |
| `scripts/testing/conexiones1_medir.py:302` | `count(*)`, no mira la columna | nada |
| `add_indexes.sql:33` | índice sobre la columna | nada |
| `proyecto_maria/core/error_notes_tracker.py` | su `endpoint` sale de `context`, no de `api_logs` | nada |
| `monitoring_service.py` | métricas en memoria | nada |
| `docs/pm/herramientas` | sin resultados | nada |

## Decisiones

- **D150. `_guardable_en_pg(endpoint)` es inalcanzable.** Lo que se guarda en
  `endpoint` es una de dos cosas: el `path_format` de la ruta, que sale del
  código, o la constante `<sin ruta>`. Además, `_RutaSinNul` frena antes un
  NUL en el camino (404) o en la consulta (400). Ningún pedido puede meter un
  NUL ahí.
  - (a) Dejar la llamada sin caso, como defensa por si cambia de dónde sale el
    endpoint.
  - (b) Sacar la llamada del producto y dejar el endpoint sólo con `[:200]`.

  **Recomiendo (b):** un chequeo que nada puede activar tampoco se puede
  probar, y §6 pide restar antes de sumar. Va en otra pieza, con su rojo,
  porque esta devolución no cambia producto.
- **D142** (en la vuelta anterior la llamé D140): las filas viejas de
  `api_logs` tienen el camino crudo. Va a Emi. Mientras decide, (c): no toco
  ninguna fila.

Siguen abiertas:
- **D131**, de EMAIL-1, va a Emi.
- **D136**: no traigo tu rama hasta que INTEGRAR-1 esté aceptada.

D139 ya la decidiste: (a), escapar el panel en una pieza aparte. La próxima D
libre es la D151.

Supuestos reversibles:

1. **`<sin ruta>` cubre también pedidos que nunca llegan a una ruta.** Son el
   preflight de CORS, el 404 (NUL en la ruta) y el 400 (NUL en la consulta)
   de `_RutaSinNul`, el 307 de la barra final y el 429 del límite. Ninguno
   deja el camino crudo. Esto corrige la vuelta anterior, que nombraba sólo
   «el 400 de `_RutaSinNul`».
2. **Los moldes del caso salen de `app.openapi()["paths"]`.** Sin cambios
   desde la vuelta anterior.

## Comandos

```bash
export GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares PYTHONPATH=.
# arnés de Postgres de ENTRADAS-3, solo: 18 «OK», termina en «fallas: 0»
python scripts/testing/entradas3_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
# sabotajes de ENTRADAS-3: «BASE  | en verde», 12 «ROJO», «sabotajes con falla: 0», salida 0
PY=python PG_URL=postgresql://cdi@127.0.0.1:55432/postgres ./scripts/testing/sabotajes/entradas3.sh 279ef26
# sabotajes de la pieza: 24 «ROJO», «sabotajes sin rojo: 0; no corridos: 0», salida 0
PY=python PG_URL=postgresql://cdi@127.0.0.1:55432/postgres ./scripts/testing/sabotajes/observabilidad1.sh
# rojo de la devolución: el arnés de 694f183 sobre este producto da «fallas: 2»
mkdir -p /tmp/e3v/scripts/testing && git show 694f183:scripts/testing/entradas3_postgres.py > /tmp/e3v/scripts/testing/e3.py
PYTHONPATH=$PWD python /tmp/e3v/scripts/testing/e3.py postgresql://cdi@127.0.0.1:55432/postgres
```

## Puertas

| corrida | SHA | salida exacta |
|---|---|---|
| sabotajes de ENTRADAS-3, con Postgres | `279ef26` | `BASE  \| en verde`, 12 `ROJO`, `sabotajes con falla: 0`, salida 0; ningún `ignored null byte` |
| arnés de Postgres de ENTRADAS-3, solo | `279ef26` | 18 `OK`, `fallas: 0`, salida 0 |
| arnés de `694f183` sobre el producto de `279ef26` | `279ef26` | `FALLA \| NUL en la ruta: 404; en api_logs: 0`, `FALLA \| ruta de 300 caracteres: 404; en api_logs: 0`, `fallas: 2`, salida 1 |
| suite completa | `7fd0f5f` | `5434 passed, 335 skipped, 3 xfailed, 112 warnings in 1009.39s (0:16:49)`, salida 0 |
| `compileall -q proyecto_maria` | `7fd0f5f` | sin salida, salida 0 |
| smoke_friccion | `7fd0f5f` | `==> OK · telemetría y alias session/state rechazan sin sesión + by-cuit protegido`, salida 0 |
| arranque SQLite | `7fd0f5f` | `fallas 0`, salida 0 |
| arranque Postgres 16 | `7fd0f5f` | `fallas 0`, salida 0 |
| sabotajes de la pieza | `d3a64f9` (después cambió sólo el arnés de ENTRADAS-3) | 24 `ROJO`, `sabotajes sin rojo: 0; no corridos: 0`, salida 0 |
| sabotajes de ENTRADAS-3, con Postgres | `7fd0f5f` | 12 `ROJO`, `sabotajes con falla: 0`, salida 0, con 4 avisos `ignored null byte` (los saca `279ef26`) |

Los 12 ROJO de ENTRADAS-3 son los de siempre. 8 son de pytest:
- 3 de la pila;
- NUL en la consulta;
- campo no texto `[alta`;
- null que se guarda como «None» `[alta`;
- nombre null `[edicion`;
- número enorme `[1e16`.

Los otros 4 son de Postgres:

- «un pedido sin molde guarda el camino: dice «FALLA | NUL en la ruta»»;
- «un molde largo no queda en api_logs: dice «FALLA | molde de 300 caracteres»»;
- «una excepción con NUL no queda en api_logs: dice «FALLA | excepción con NUL en el mensaje»»;
- «un número enorme revienta el listado en Postgres: dice «FALLA | después de 1e308»».

**Corrido y no corrido:**
- No repetí la suite sobre `279ef26`: desde `7fd0f5f` sólo cambiaron dos
  scripts que pytest no corre.
- El `/security-review` lo hice a mano sobre el diff. El producto no cambió
  desde `694f183` y el arnés no agrega superficie: no encontré nada nuevo.
- No corrí `ataque_aislamiento.sh`: no se tocan sesión, permisos ni datos de
  clientes.

## Hallazgos de la autorrevisión

| quién | hallazgo | qué hice |
|---|---|---|
| `adversario-sonnet-alto` (Sonnet, alto) | Baja: si fallaba el primer conteo, el segundo daba un falso rojo en cascada | Arreglado en `7fd0f5f`: cada pedido cuenta su propia fila |
| `adversario-sonnet-alto` (Sonnet, alto) | La razón principal de D150 es `path_format`, no `_RutaSinNul` | Corregido en D150 |
| `adversario-sonnet-alto` (Sonnet, alto) | `COLA-LIMPIEZA.md:57-58` quedó desactualizado | No lo toco porque es tuyo; ver Riesgos |
| `adversario-sonnet-alto` (Sonnet, alto) | No hay lectores nuevos de `api_logs.endpoint` | Confirmado con el grep |
| `adversario-sonnet-alto` (Sonnet, alto) | No pudo comprobar `scope["route"]` porque su entorno no tiene FastAPI | Lo cubren los casos de la pieza, que sí corren |
| `/code-review high` | `_guardable_en_pg(endpoint)` no tiene negativo | D150 |
| `/code-review high` | El NUL del log de la excepción llegaba a la salida: bash avisaba y `grep` la tomaba por binaria | Lo reproduje (4 avisos y «binary file matches»); arreglado en `279ef26` con `tr -d '\000'` |
| `/code-review high` | Se compara un estado < 500 contra un conteo de 404; otro 404 en la ventana también contaría | Queda así: hay un solo cliente secuencial, y el mensaje muestra el estado |
| `/code-review high` | Un sabotaje repite uno de `observabilidad1.sh:202` | Queda: mide que el arnés de Postgres distingue |
| `/code-review high` | El chequeo del camino repetía el de `<sin ruta>` | Sacado en `279ef26` |
| `/code-review high` | Los `%` de la consulta cuando los parámetros vienen vacíos | Es especulativo: queda |
| `/code-review high` | El molde sin parámetros no distingue el molde del camino | Queda: lo distingue el caso de pytest |
| `/code-review high` | Abre una conexión por cada conteo | Es menor: queda |

## Riesgos

Los seis de la vuelta anterior siguen igual:
1. la espera de 5 s detrás de otra transacción;
2. un índice inválido o parcial se da por bueno;
3. un camino de más de 200 caracteres pierde su métrica;
4. `lock_timeout` no limita la construcción del índice;
5. dos workers pueden chocar en `CREATE INDEX`;
6. el caso SQLite de la falla del índice no distingue si se juntan las
   transacciones.

Los dos que pediste anotar:

7. **Un índice con ese nombre sobre otra columna se anuncia como creado.**
   Si ya hay un índice llamado `ix_api_logs_owner_username`,
   `CREATE INDEX IF NOT EXISTS` no hace nada, sea sobre la columna que sea.
8. **`error_message` puede traer los parámetros de una excepción de
   SQLAlchemy**, con datos del pedido.

Además, `COLA-LIMPIEZA.md:57-58` describe el estado de antes de esta pieza.
Lo dejo para que lo actualices vos.

## chequeo-6

```
chequeo-6 0231eee..279ef26: avisos para mirar, no un veredicto
producto +35/−15
arnés +252/−39
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12086 → 12106
avisos: 0
```

## Archivos de producto

`proyecto_maria/main.py`: `_migrate_add_api_logs_owner_column` y
`MetricsMiddleware`. Sin cambios desde `694f183`.

## Lo que sigue

ORG-1+D40; después escapar el panel (D139) y D102.

/compact conservar: Dev MARIA (Dev 2), sesión session_01C8gCBjvn36wnYC6qG2Sixi, rama claude/dev-maria, PM principal session_01B7FVQspcEHF7PqNv797WNM (send_message next, «Dev MARIA: …»), rutina trig_01WmrC3ALqBXkD9UBv6dFGbP. Devolución de OBSERVABILIDAD-1 entregada en 279ef26 (informe en este archivo, base 0231eee). RESET-3, SMOKE-1 y AVISOS-2b aceptadas. Abiertas: D131 (a Emi), D136 (no traigo tu rama hasta INTEGRAR-1), D142 (filas viejas, a Emi; mientras, c), D150 (recomiendo b). D139 decidida (a), pieza aparte. La próxima D libre es la D151. Sigue ORG-1+D40, después D139, después D102. Corte 2026-11-09 05:00 UTC o 95 % de uso. Nunca main, nada se publica sin el «dale» de Emi para el SHA, sin secretos, sólo datos inventados.
