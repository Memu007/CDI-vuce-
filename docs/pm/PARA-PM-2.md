# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## ENTRADAS-3 (D109 a, D110 a): **entregada** en `cf5309a` (2026-11-08)

Base `0f09bd8` (producto igual a `fd545c1`). Ninguno de estos da 500 ni se guarda:

- un cuerpo más hondo que la pila en aprender productos, guardar despacho y
  editar producto (400 «Body JSON inválido»);
- un NUL en la consulta (400 «La consulta tiene un carácter nulo.»);
- un campo del cliente que no es texto, en el alta o en la edición (400
  «<campo> tiene que ser texto.»).

Un número de más de 1e15 en valor absoluto, en la operación manual o al
guardar al cliente, da 400 «… es demasiado grande.». Con eso, el listado y las
métricas del cliente ya no revientan en Postgres por datos nuevos.

El registro de pedidos (`api_logs`) ahora guarda un pedido con NUL en la ruta o
con una ruta de más de 200 caracteres: antes se perdía en Postgres.

`tiene_medio_par` y `_sin_nul` se recorren dentro del `try` en un solo lugar,
`_cuerpo_guardable`. El aviso de medio par se levanta afuera del `try`.

| SHA | qué |
|---|---|
| `02ad156` | fix: cuerpo hondo, NUL en la consulta, campo no texto, número enorme, `api_logs` + CHANGELOG |
| `c7fa1f8` | test: casos, sabotajes (`entradas3.sh`, ajuste de `entradas2.sh`) y chequeo en Postgres |
| `0fc85a0` | fix: un nombre null en el cliente da 400 (hallazgo del adversario, abajo) |
| `cf5309a` | test: nombre null, campo desconocido muy anidado, sabotaje del «None» reescrito |

`producto +48/−21`. Pasa de 20 netas porque son cinco reglas separadas más la
del nombre, cada una en un solo lugar. Las reglas son: NUL en la consulta,
`api_logs`, campo no texto, tope numérico y el recorrido dentro del `try`. No
encontré código para sacar: las tres rutas de catálogo pierden su propio
`tiene_medio_par`.

## Decisiones

- **D115: filas ya guardadas con un número enorme.** El tope frena lo nuevo,
  pero una fila que ya tenga `total_value` 1e308 sigue desbordando la suma en
  Postgres. El listado y las métricas de ese cliente dan 500. No sé si hay
  alguna en producción: no la miro.
  - (a) Dejarlo. Si aparece un 500 de ese cliente, se limpia esa fila a mano.
  - (b) Pieza chica: la lectura suma con tope (`LEAST`/`GREATEST` o en Python),
    así una fila vieja no tumba la pantalla.
  - (c) Migración que corrija las filas fuera de rango.

  **Recomiendo (a).** El dato sólo pudo entrar a mano por la API, no desde la
  pantalla, y (c) toca datos de producción. Si querés red de seguridad, (b),
  que no toca datos.
- **D117: un NUL en un campo de formulario multipart da 500 en Postgres.**
  En `/upload_excel_v2/`, el `cliente_id` (~9082/9101) da
  `CharacterNotInRepertoireError`. Lo encontró el adversario y lo reproduje.
  La sonda está en mi scratchpad. Es otra vía de entrada, fuera de D109/D110.
  - (a) Pieza chica: el mismo `_guardable_en_pg` en los campos `Form` que van a la base.
  - (b) Que `_RutaSinNul` mire también el cuerpo multipart: lo rechaza todo,
    pero lee el cuerpo en el middleware.
  - (c) Cola de limpieza.

  **Recomiendo (a)**: es el patrón que ya usamos y no lee cuerpos en un middleware.

## Lo que hay que saber

- El tope es **1e15**, el mismo de `validate_numeric`
  (`security/input_validation.py:206`). Es distinto de `_MAX_VALOR = 1e12`
  (`client_memory.py:39`), que es el tope del promedio del historial. No los
  unifiqué: son reglas distintas y unificar no está en la pieza.
- El tope va sobre cada número. En la operación manual también va sobre el
  total, que se calcula. Al guardar al cliente, el total es el
  `resumen.valor_total` que manda el cliente. Así, ítems de valor 1e15 por
  cantidad 1e15 se guardan con total 0. Eso no desborda nada: la suma que
  revienta es la de `total_value`. Lo dejo como estaba; lo encontró el
  adversario.
- Cambios visibles fuera de lo pedido, todos consecuencia de las reglas:
  - un `cuit` numérico (sin comillas) ahora da 400;
  - `/health?x=%00` da 400;
  - en aprender productos, si un cuerpo trae a la vez un medio par y un NUL,
    el mensaje puede cambiar de orden;
  - `divisa` ahora pasa por la limpieza de NUL.
- Un null en un texto del cliente (salvo el nombre) queda vacío, no «None».
  Un nombre null da 400. Un nombre `""` en la edición se acepta, igual que
  antes: no lo cambié.

## Riesgos

- `client_ip` es `String(45)`. Detrás de un proxy, si llega una lista de IPs,
  el registro de ese pedido puede perderse, como antes con la ruta. No lo vi
  pasar y no lo toqué.
- La guarda es por ruta, no en el parseo general: una ruta nueva que lea JSON
  a mano tiene que pasar por `_cuerpo_guardable` o `_json_guardable`.
- `_TEXTOS_DEL_CLIENTE` repite los nombres que el alta y la edición leen más
  abajo. Va a la cola de limpieza si querés.
- `DataStore.add_operation` (`core/datastore.py`) parece código muerto. No lo toqué.

## Hallazgos de la autorrevisión

| quién | modelo y esfuerzo | hallazgo | qué hice |
|---|---|---|---|
| adversario | Sonnet alto | NUL en un campo multipart da 500 en Postgres | D117 |
| adversario | Sonnet alto | nombre null en la edición dejaba al cliente sin nombre | `0fc85a0` + caso en `cf5309a` |
| adversario | Sonnet alto | al guardar al cliente, ítems enormes con `resumen.valor_total` 0 se guardan (sin desborde) | informativo, arriba |
| `/code-review` | high | sin hallazgos confirmados dentro de la pieza; riesgos ya listados | — |
| `/security-review` | — | sin hallazgos ≥8 | — |
| yo | — | el sabotaje del «None» no producía el defecto | reescrito en `cf5309a` |
| yo | — | se había perdido el caso del campo desconocido muy anidado | vuelto en `cf5309a` |

## Puertas

Todas sobre `cf5309a`, desde worktree limpio, una a la vez; logs en el scratchpad.

| puerta | salida exacta |
|---|---|
| suite (env de `/entregar`, SQLite) | `5212 passed, 335 skipped, 3 xfailed, 97 warnings in 1038.00s`; salida 0 |
| suite como la CI (`env -u DATABASE_URL ENVIRONMENT=testing …`) | `5212 passed, 335 skipped, 3 xfailed, 96 warnings in 1005.40s`; salida 0 |
| `compileall -q proyecto_maria` | salida 0 |
| `entradas3_postgres.py` en `cf5309a` | 16 `OK`, `fallas: 0`, salida 0; última: `OK | NUL en la consulta: 400 {"detail":"La consulta tiene un carácter nulo."}` |
| `entradas3_postgres.py` en `fd545c1` (producto de antes, arnés nuevo) | `fallas: 11`, salida 1 (abajo) |
| `entradas3.sh cf5309a` | BASE en verde, 11 `ROJO`, `sabotajes con falla: 0` |
| `entradas2.sh cf5309a` | BASE en verde, 24 `ROJO`, `sabotajes con falla: 0` |

Rojos de Postgres sin el arreglo, copiados del log:

```
FALLA | NUL en la ruta: 404; en api_logs: 0
FALLA | ruta de 300 caracteres: 404; en api_logs: 0
FALLA | 1e308: manual 200, guardar al cliente 200
FALLA | 1e308: manual 200, guardar al cliente 200
FALLA | después de 1e308: listado 500, métricas 500
FALLA | -1e308: manual 200, guardar al cliente 200
FALLA | -1e308: manual 200, guardar al cliente 200
FALLA | después de -1e308: listado 500, métricas 500
FALLA | 1e16: manual 200, guardar al cliente 200
FALLA | 1e16: manual 200, guardar al cliente 200
FALLA | NUL en la consulta: 500 {"detail":"No pudimos procesar tu solicitud. Probá de nuevo en unos segundos. Si
```

No corrí `smoke_friccion.sh` ni `ataque_aislamiento.sh`: la pieza no toca sesión ni permisos, y lo que cambia (400 en entradas) lo cubren la suite, el arnés de Postgres y los sabotajes. Queda para la PM si lo quiere antes de publicar.

chequeo-6, entero:

```
chequeo-6 0f09bd8..cf5309a: avisos para mirar, no un veredicto
producto +48/−21
  AVISO producto suma 27 líneas netas: el informe dice por qué (§6: más de 20)
arnés +389/−25
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12048 → 12075
avisos: 1
```

## Comandos

```bash
git fetch origin claude/dev-maria && git checkout cf5309a
PY=<venv>/bin/python scripts/testing/sabotajes/entradas3.sh cf5309a   # BASE en verde, 11 ROJO, «sabotajes con falla: 0»
PY=<venv>/bin/python scripts/testing/sabotajes/entradas2.sh cf5309a   # BASE en verde, 24 ROJO, «sabotajes con falla: 0»
<venv>/bin/python scripts/testing/entradas3_postgres.py postgresql://cdi@127.0.0.1:55432/postgres   # «fallas: 0»
PY=<venv>/bin/python -m pytest -q --no-cov tests/test_entradas3.py tests/test_entradas2.py   # verde
```

## Archivos de producto tocados

`proyecto_maria/main.py`, `CHANGELOG.md`.

Sigo con ENTORNO-4 (D112 c + D113 b).

/compact conservar: Dev MARIA (session_01C8gCBjvn36wnYC6qG2Sixi), rama claude/dev-maria, rutina trig_01WmrC3ALqBXkD9UBv6dFGbP; aviso a la PM session_01B7FVQspcEHF7PqNv797wNM con send_message next. ENTRADAS-3 (D109 a, D110 a) entregada en cf5309a (base 0f09bd8); D115 y D117 abiertas (mías; D116 es de la técnica: PERMISOS-1), D114 también de la técnica, próxima D libre D118. ENTORNO-3 aceptada; D111 a, D112 c + D113 b decididas. Sigue ENTORNO-4, después SUFIJOS-2+SEGURO-1, el resto y D102 (fijar bcrypt). Corte de rutinas 2026-11-08 15:50 UTC. Nada se publica sin el «dale» de Emi para el SHA; nunca main; sin secretos; TXT y proforma reales nunca en el repo.
