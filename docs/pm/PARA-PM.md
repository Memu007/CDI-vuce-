# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1 parte B sobre lo integrado (cierra D134). Rojo: con lectores de PDF de 30 s el pool se agota y hay 500. Ninguna corrida termina con conexiones tomadas. Dos D para decidir

| Qué | SHA |
|---|---|
| Entrega (este informe) | el commit de este informe, encima de `37c11eb4` |
| Arnés | `ff2e2aae` (medidor, sonda y control), `9c6f721f` (dos sabotajes de producto en el control), `37c11eb4` (el control corta cada corrida apenas tiene su rojo) |
| Medición base | `c8733be3` (merge de tu rama). `git diff c8733be3 37c11eb4 -- proyecto_maria Dockerfile requirements.txt` da 0 líneas: es el mismo producto que entrego |
| Control y mediciones con pico 60 (demora falsa de 2 s, 8 s y 30 s) | `37c11eb4` |

**Producto tocado: ninguno.** `git rev-list --no-merges ff2e2aae^..37c11eb4 --not origin/claude/practical-shannon-szpwkn -- proyecto_maria` da sólo `524a8f00`, `6c2b3383` y `cc8b834b`, que son de BORRADOR-1 (pieza anterior).

**Resultado**
- **La medición con 30 s de demora termina en rc=1, «QUEDAN CONEXIONES TOMADAS».** En `pico_pdf` (60 subidas públicas de PDF a la vez, lector falso de 30 s) dio 422 × 16 · 500 × 10 · 504 × 34. Las 10 respuestas 500 son «Excepcion no manejada en POST /upload_pdf/public: TimeoutError: QueuePool limit of size 20 overflow 30 reached, connection timed out, timeout 30.00».
- **Ese rojo es pool agotado, no conexiones perdidas.** El medidor cuenta 'QueuePool limit' en el log como señal de fuga, y por eso sale 1. Pero en todas las fases `quedan` da 0, al final hay 0 tomadas y 20 libres, `close_empezados` = `close_terminados` (2968) y Postgres queda en `{'idle': 20}`. No cambié el medidor.
- **De dónde sale.** `get_current_user` llama a `sesion_de_la_request`, que consulta el usuario (`auth/dependencies.py:94`) y con eso toma la conexión. La subida la tiene tomada durante toda la lectura del PDF, que tiene 4 hilos (`PDF_READ_WORKERS`). Con 60 subidas, 50 toman las 50 conexiones (20 + 30 de desborde). Las otras 10 esperan su primera conexión más de `pool_timeout` (30 s) y dan 500.
- **Los números cierran con las constantes.** 10 = 60 − 50. 16 = 4 hilos × 4 tandas de 30 s dentro de `PDF_READ_TIMEOUT_S` (120 s, cuenta también la cola). 34 = 50 − 16, que dan 504 por ese plazo.
- **Con 8 s de demora, rc=0.** Sin 500, `quedan` 0 en todo, y los normales esperaron hasta 16,2 s.
- **Ninguna corrida termina con conexiones tomadas, y todo `close()` que empezó terminó.** Probé 401 de seis tipos, normales, mezcla, `/api/ncm/sugerir`, la subida pública de PDF, cuatro tipos de corte en vuelo y picos de bcrypt, Gemini y PDF.
- **Un `close()` cancelado no lo pude provocar en el producto.** uvicorn no cancela el pedido cuando el cliente corta (hallazgo 6). Forzado a propósito, sí deja la conexión tomada (hallazgo 4), y el medidor lo ve: es el control.
- **El control da rojo cuando la sesión no se cierra.** Lo probé con dos sabotajes de la sonda (cancelar el `close` a propósito, guardando la sesión o soltándola) y dos del producto (el `finally` de `get_async_session` no cierra, guardando la sesión o soltándola).
- **No arreglé nada en esta pieza.** La tarea dice «si quedan conexiones tomadas: arreglo». Lo que quedó es el pool lleno de pedidos vivos, no conexiones tomadas después de cerrar. Si eso entra en «quedan» lo decidís en la D180. El producto sigue igual, y el aviso de las pruebas sigue en riesgos.

## Decisiones

**D180. Con trabajo lento, el pool se agota y hay 500.**
- Opciones:
  - (a) Contarlo como «quedan conexiones tomadas» y hacer una pieza aparte, con su rojo antes. Esa pieza suelta la conexión antes del trabajo lento (lector de PDF, Gemini, bcrypt) o limita cuántos de esos esperan con una conexión tomada. El rojo sale de esta misma medición: `--pico 60 --lento 30`, que hoy da 500 × 10 en `pico_pdf`.
  - (b) No contarlo así: queda como riesgo anotado y CONEXIONES-1 cierra sin arreglo.
- Recomiendo (a).
  - Con 60 subidas a la vez y un lector de 30 s, hay 500 de verdad, para usuarios con sesión válida.
  - En `pico_pdf`, los pedidos normales esperan 29,97 s. Eso es casi `pool_timeout` (30 s), sobre 12 pedidos normales: están al borde, no a salvo.
  - La subida pública de PDF es zona de MARIA (D74). Si va (a), vos decidís quién la toma.
- Datos, todos con pico 60 sobre `37c11eb4`:

| Demora falsa | rc | `pico_pdf` | Espera máxima de un normal en `pico_pdf` |
|---|---|---|---|
| 2 s | 0 | 422 × 60 · 200 × 12 | 6,79 s |
| 8 s | 0 | 422 × 60 · 200 × 12 | 16,2 s |
| 30 s | 1 | 422 × 16 · 500 × 10 · 504 × 34 · 200 × 12 | 29,97 s |

  - **Dónde se rompe, calculado y sin correr.** Las 10 que esperan necesitan 10 conexiones libres en menos de 30 s. Con 4 hilos son 3 tandas (ceil(10/4)), así que se rompe con lecturas de más de unos 10 s cuando hay 60 subidas. Con 8 s pasó, porque 3 × 8 = 24 s. No corrí `--lento 15`.
  - Con un solo worker (el `Dockerfile`), el tope es 50 conexiones. Hacen falta más de 50 pedidos lentos a la vez.
  - **El pico de Gemini a 30 s no da 500, pero no está a salvo.** Dio 200 × 72 y los normales esperaron 30,12 s. Ahí compiten tres plazos de 30 s: la demora falsa, `NCM_GEMINI_TIMEOUT_S` y `pool_timeout`. El log de toda la corrida tiene 75 «Gemini no contestó a tiempo»: la mayoría de esos 200 son la respuesta vacía del plazo, no una sugerencia. No afirmo que Gemini esté bien.

**D181. D146 con los números de bcrypt.** Pediste mantener D146 en la cola de limpieza hasta tener esta medida.
- Opciones:
  - (a) Contar antes de verificar, en una pieza propia.
  - (b) Dejarlo en la cola de limpieza.
- Recomiendo (b).
- Por qué:
  - 60 claves malas en paralelo para la misma cuenta, cada una desde otra IP, dieron 60 × 401 y ningún 429. El límite va por IP (`login:{ip}`) y por IP y cuenta (`cuenta:{username}:login:{ip}`), así que con IPs distintas ninguno de los dos corta, se cuente antes o después de bcrypt.
  - La IP que usa el límite la arma el último proxy de confianza (`get_client_ip`, `core/rate_limit.py`). En el medidor la pone el cliente, porque no hay proxy delante. En producción, esto equivale a un atacante con 60 IPs propias, no a alguien que la invente.
  - Lo que esos 60 sí hacen es tomar el pool: llega a 50 de 50. Los pedidos normales esperaron hasta 3,14 s con la demora de 2 s, 4,05 s con 8 s y 3,65 s con 30 s; bcrypt es el real en las tres, así que la demora falsa no lo toca. Ningún 500.
  - bcrypt corre en el grupo de hilos de anyio (`run_in_threadpool`). Ese grupo tiene un tope de 40, y lo medí: `bcrypt_en_vuelo_max` dio 40. Los que esperan hilo igual tienen su conexión tomada.
  - Eso es la D180, no D146. Contar antes no lo cambia.

## Cómo se midió

Usé gunicorn con las mismas opciones del `Dockerfile` y Postgres 16 descartable (`con_pg16.sh`). La sonda (`conexiones1_sonda.py`) se carga con `-c` y expone por HTTP los contadores del pool y de `close()`.

Las condiciones de la D46:
- **Sin tiempos fijos.** Cada fase espera hasta que `api_logs` tiene una fila por pedido. La columna `filas` es igual a `env` en todas.
- **Cortes en vuelo de verdad.** El cliente corta el socket a mitad del pedido, mientras el servidor está en bcrypt, en Gemini o en el lector de PDF, o con el cuerpo a medias. Cada corte da «15 de 15 cortados con el pedido en vuelo».
- **Gemini sin clave real y sin red.** Hay un Gemini falso que demora `--lento` segundos. El lector de PDF falso demora lo mismo.
- **bcrypt es el real.**

Columnas: `máxT` es el máximo de `pool.checkedout()` y `máxPG` el máximo de conexiones en `pg_stat_activity`.

### Medición base (`c8733be3`, pico 30): «sin conexiones tomadas», rc=0

Las seis fases de 401, `normal`, `mezcla`, `sugerir` y `pdf_sin_lector` dan 0 en `quedan`. Sus códigos en `api_logs` son los esperados: 401 × 40 en cada tipo de 401, 200 × 40, «{401: 72, 200: 12}», 200 × 15 y 503 × 10.

| Fase | Códigos en `api_logs` | máxT | máxPG | quedan | seg | Espera máxima de un normal |
|---|---|---|---|---|---|---|
| `login_clave_mala` | 401 × 40 | 40 | 40 | 0 | 0.0 | — |
| `corte_cuerpo_a_medias` | 400 × 15 | 1 | 20 | 0 | 0.06 | — |
| `corte_bcrypt` | 401 × 15 | 11 | 20 | 0 | 0.5 | — |
| `corte_gemini` | 200 × 15 | 9 | 20 | 0 | 2.02 | — |
| `corte_pdf` | 422 × 15 | 5 | 20 | 0 | 1.99 | — |
| `pico_bcrypt` | 401 × 30 · 200 × 12 | 42 | 42 | 0 | 0.0 | 2.31 |
| `pico_gemini` | 200 × 42 | 42 | 42 | 0 | 0.06 | 0.62 |
| `pico_pdf` | 422 × 30 · 200 × 12 | 42 | 42 | 0 | 0.06 | 0.34 |

Sonda al final:
- `apilog_creados` 576 y «filas en api_logs: 576».
- `close_empezados` 2508 y `close_terminados` 2508.
- `close_con_transaccion` 220.
- `tomadas` 0, `libres` 20, `desborde` 0.
- `bcrypt_en_vuelo_max` 20, `gemini_en_vuelo_max` 8, `pdf_en_vuelo_max` 4.

Estas cadenas aparecen 0 veces en el log de gunicorn: 'non-checked-in connection', 'Task was destroyed but it is pending', 'QueuePool limit', 'CancelledError', 'UnboundLocalError', 'Exception in ASGI application', 'Error logging metrics' y 'Traceback'.

### Pico 60 (`37c11eb4`, `--pico 60`): «sin conexiones tomadas», rc=0

Las fases anteriores a los picos dan lo mismo que la base, salvo diferencias de uno en `máxT` (por ejemplo, `corte_bcrypt` 10 y `corte_cuerpo_a_medias` 0).

| Fase | Códigos en `api_logs` | máxT | máxPG | quedan | Espera máxima de un normal |
|---|---|---|---|---|---|
| `pico_bcrypt` | 401 × 60 · 200 × 12 | 50 | 50 | 0 | 3.14 |
| `pico_gemini` | 200 × 72 | 50 | 50 | 0 | 3.99 |
| `pico_pdf` | 422 × 60 · 200 × 12 | 50 | 50 | 0 | 6.79 |

Sonda al final:
- `apilog_creados` 666 y «filas en api_logs: 666».
- `close_empezados` 2988 y `close_terminados` 2988.
- `tomadas` 0, `libres` 20, `desborde` 0.
- `bcrypt_en_vuelo_max` 40, `gemini_en_vuelo_max` 8, `pdf_en_vuelo_max` 4.

Las ocho cadenas del log dan 0, también 'QueuePool limit'. Ningún 500.

### Pico 60 con 8 s de demora (`37c11eb4`, `--pico 60 --lento 8 --plazo 240`): «sin conexiones tomadas», rc=0

Corrida de 00:20:21 a 00:24:21 UTC. Las fases anteriores a los picos dan 0 en `quedan` y `{'idle': 20}`. `corte_gemini` tarda 7.99 s y `corte_pdf` 8.03 s, y cada corte da «15 de 15 cortados con el pedido en vuelo».

| Fase | Códigos en `api_logs` | máxT | máxPG | quedan | Espera máxima de un normal |
|---|---|---|---|---|---|
| `pico_bcrypt` | 401 × 60 · 200 × 12 | 50 | 50 | 0 | 4.05 |
| `pico_gemini` | 200 × 72 | 50 | 50 | 0 | 16.03 |
| `pico_pdf` | 422 × 60 · 200 × 12 | 50 | 50 | 0 | 16.2 |

Sonda al final:
- `apilog_creados` 666 y «filas en api_logs: 666».
- `close_empezados` 2988 y `close_terminados` 2988.
- `tomadas` 0, `libres` 20, `desborde` 0.
- `bcrypt_en_vuelo_max` 40, `gemini_en_vuelo_max` 8, `pdf_en_vuelo_max` 4.

Las ocho cadenas del log dan 0. Ningún 500.

### Pico 60 con 30 s de demora (`37c11eb4`, `--pico 60 --lento 30 --plazo 600`): «QUEDAN CONEXIONES TOMADAS», rc=1

Corrida de 00:24:37 a 00:32:01 UTC. Las fases anteriores a los picos dan 0 en `quedan` y `{'idle': 20}`. `corte_gemini` tarda 30.04 s y `corte_pdf` 30.02 s, y cada corte da «15 de 15 cortados con el pedido en vuelo».

| Fase | Códigos en `api_logs` | máxT | máxPG | quedan | seg | Espera máxima de un normal |
|---|---|---|---|---|---|---|
| `pico_bcrypt` | 200 × 12 · 401 × 60 | 50 | 50 | 0 | 0.0 | 3.65 |
| `pico_gemini` | 200 × 72 | 50 | 50 | 0 | 29.97 | 30.12 |
| `pico_pdf` | 200 × 12 · 422 × 16 · 500 × 10 · 504 × 34 | 50 | 50 | 0 | 22.18 | 29.97 |

En `pico_pdf` el medidor anota `'errores': {'TimeoutError': 10}` y «respuestas inesperadas: {('pico_pdf', 500, ''): 10, ('pico_pdf', 504, ''): 34}».

Sonda al final:
- `apilog_creados` 666 y «filas en api_logs: 666».
- `close_empezados` 2968 y `close_terminados` 2968.
- `close_con_transaccion` 280.
- `dispatch_entradas` 666: `dispatch_ok` 656 y `dispatch_error_TimeoutError` 10.
- `tomadas` 0, `libres` 20, `desborde` 0.
- `bcrypt_en_vuelo_max` 40, `gemini_en_vuelo_max` 8, `pdf_en_vuelo_max` 4.

En el log de gunicorn:

| Cadena | Veces |
|---|---|
| 'non-checked-in connection' | 0 |
| 'Task was destroyed but it is pending' | 0 |
| 'QueuePool limit' | 50 líneas, de 10 pedidos |
| 'CancelledError' | 0 |
| 'UnboundLocalError' | 0 |
| 'Exception in ASGI application' | 10 |
| 'Error logging metrics' | 0 |
| 'Traceback' | 60 |
| 'Gemini no contestó a tiempo' | 75 |

Los 10 tracebacks de 500 terminan en la consulta del usuario de `sesion_de_la_request` (`auth/dependencies.py:94`), que llama `get_current_user`, esperando su primera conexión.

### Control: el medidor da rojo cuando una sesión no se cierra

Corrida sobre `37c11eb4` (00:06:55 → 00:14:16 UTC), rc=0:

```
BIEN  | sin sabotaje: salida 0, dice «sin conexiones tomadas»
BIEN  | close_cancelado: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | close_cancelado_suelto: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | el producto guarda la sesión sin cerrar: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | el producto suelta la sesión sin cerrar: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
```

La corrida anterior sobre `c8733be3`, con el control de `9c6f721f`, dio las cuatro primeras líneas BIEN y terminó con `rc=124`: se le acabó el `timeout` en la quinta. No se colgó. El medidor seguía todas las fases aunque el rojo ya estuviera, y con la sesión soltada sin cerrar cada fase esperaba su plazo. `37c11eb4` corta la corrida apenas aparece el rojo. Por eso hay tres commits de arnés y no uno.

## Lo que no cubre

- Hay sesiones que no se abren con `get_async_session`, y la medición no pasa por ellas:
  - `main.py:10129`
  - 11 en `client_service.py`
  - `core/ncm_service.py:46` y `:85`
- **Una cancelación de verdad.** uvicorn no cancela al cortar el cliente (hallazgo 6), así que ninguna fase cancela un `close()` en el producto. Lo que prueba que el medidor la vería es el control.
- **Un solo worker.** Es la configuración del `Dockerfile`. Con más workers, el tope de Postgres se multiplica por cada uno; no lo medí.

## Hallazgos del adversario

Un adversario Opus, esfuerzo alto, sólo lectura. Lo que tomé de cada hallazgo:

| # | Hallazgo | Severidad que le dio | Qué hice |
|---|---|---|---|
| 1 | `/api/ncm/sugerir` tiene la conexión tomada mientras espera a Gemini, hasta 30 s (`NCM_GEMINI_TIMEOUT_S`, `main.py:10450`), y no tiene límite por minuto | media-alta | Reproducido a medias. Con 30 s, `pico_gemini` llega a 50 de 50 y los normales esperan 30,12 s, sin 500. En toda la corrida hay 75 «Gemini no contestó a tiempo», así que la mayoría de esas respuestas son el vacío del plazo. Va a la D180 |
| 2 | La subida pública de PDF tiene la conexión tomada mientras espera el candado por usuario y valida; la cuota de 50 por día se mira después, así que una cuenta sin cuota igual toma una conexión antes del 429 | media-alta | Reproducido: con 30 s, `pico_pdf` da 500 × 10 por «QueuePool limit» y 504 × 34. La parte de la cuota no la medí, porque el lector falso no pasa por ella. Va a la D180 |
| 3 | Con un worker y `--max-requests 1000`, al reiniciarse el worker los pedidos nuevos esperan a que termine el pedido lento en vuelo | media, condicional | No lo reproduje. Va a riesgos |
| 4 | Un `close()` cancelado sí deja la conexión tomada hasta que pasa el recolector de basura; lo reprodujo con aiosqlite | baja hoy | Es lo que el control prueba que el medidor ve (las dos líneas `close_cancelado`). Lo que lo hace inalcanzable hoy es el punto 6 |
| 5 | El rollback del `except` de `get_async_session` no corre en los pedidos: el envoltorio `get_db` manda el cierre a una tarea aparte | baja, no es fuga | No lo toqué: es producto y no deja conexiones tomadas. A la cola de limpieza si querés |
| 6 | uvicorn no cancela el pedido cuando el cliente corta: marca `disconnected` y sigue | baja | Confirmado en `uvicorn/protocols/http/httptools_impl.py`, `connection_lost` (líneas 116-128 del venv). Los cortes en vuelo son de verdad, pero el producto no se entera: termina el pedido y cierra normal. `corte_cuerpo_a_medias` corta antes de tocar la base |
| 7 | `enrich-items` abre una sesión por NCM, sin tope, en un `gather` | baja-media | Fuera de `get_async_session`; está en «Lo que no cubre» |
| 8 | Login: bcrypt con la conexión tomada | baja | Es la D181 |
| 9 | `resend_verification` tiene la conexión tomada mientras manda el mail | baja | No lo medí. Va a riesgos |

También anotó que las versiones de gunicorn y uvicorn no están fijas (el `Dockerfile` instala `gunicorn uvicorn[standard]` sin versión) y que el comentario de `conexiones1_medir.py:109` dice «primer valor de XFF» cuando `get_client_ip` usa el último que agregó el proxy; con un solo valor da lo mismo.

## Riesgos

- **El aviso de las pruebas sigue.** Que no queden conexiones tomadas en esta medición no prueba que no queden en otras rutas o con otros tiempos. La medición cubre las rutas de arriba con un worker.
- **Topes en vuelo.** Gemini llega a 8 en vuelo porque `asyncio.to_thread` usa el grupo de hilos por omisión, `min(32, cpu + 4)`, que con 4 CPU da 8. Si producción tiene otra cantidad de CPU, el tope cambia. El lector de PDF llega a 4 por `PDF_READ_WORKERS`. bcrypt llega a 40, el tope de hilos de anyio.
- **Dónde se rompe con el PDF.** Lo calculé, no lo corrí: con 60 subidas, lecturas de más de unos 10 s.
- **Reinicio del worker** por `--max-requests` con un pedido lento en vuelo (hallazgo 3): sin reproducir.
- **Versiones sin fijar** de gunicorn y uvicorn en el `Dockerfile`: si una versión nueva de uvicorn cancela al cortar el cliente, el hallazgo 4 pasa a ser alcanzable.
- **Demoras falsas.** Gemini y el lector de PDF son falsos y demoran lo que dice `--lento`. Un Gemini real puede demorar más; la espera de los normales crece con eso.

## Para reproducir

```bash
PY=<venv>/bin/python scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_medir.py              # «sin conexiones tomadas», rc=0
PY=<venv>/bin/python scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_medir.py --pico 60    # máxT 50 en los tres picos, «sin conexiones tomadas»
PY=<venv>/bin/python scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_medir.py --pico 60 --lento 8 --plazo 240    # «sin conexiones tomadas», rc=0 (unos 4 minutos)
PY=<venv>/bin/python scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_medir.py --pico 60 --lento 30 --plazo 600   # «QUEDAN CONEXIONES TOMADAS», rc=1; pico_pdf 422 × 16 · 500 × 10 · 504 × 34 (unos 7,5 minutos)
PY=<venv>/bin/python scripts/testing/sabotajes/conexiones1.sh 37c11eb4                                # cinco líneas BIEN, rc=0 (unos 8 minutos)
git diff c8733be3 37c11eb4 -- proyecto_maria Dockerfile requirements.txt | wc -l                       # 0
```

No corrí la suite completa ni `/security-review`, porque no hay producto ni `tests/` tocados.

## chequeo-6

Un AVISO, en el arnés: `_instalar` de `conexiones1_sonda.py:59` tiene 96 líneas, contra ~60. Queda así porque es la función que el gunicorn de la medición carga con `-c`. Envuelve `close()`, el dispatch, `api_logs`, Gemini, el lector y bcrypt, y expone los contadores, todo dentro del proceso del worker. Partirla va a la cola de limpieza si la querés; no toca producto.

<details><summary>Salida de <code>docs/pm/herramientas/chequeo-6.py</code> en los tres commits de arnés</summary>

```
chequeo-6 740ba3afe04a1248db6047d69b95d5fcd3fb45a0..ff2e2aae919a1402f1660fd9648bdcbaf1a6539b: avisos para mirar, no un veredicto
producto +0/−0
arnés +785/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  AVISO función nueva de 96 líneas: scripts/testing/conexiones1_sonda.py:59 _instalar (§6: ~60)
avisos: 1
```

```
chequeo-6 c8733be35eb4247d4c78d7b0f1f5e7bb7713c0f3..9c6f721f59465d07b9701add4c557051e0cd207b: avisos para mirar, no un veredicto
producto +0/−0
arnés +28/−1
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

```
chequeo-6 5db9c1ec19b42d974f7e604a186fda0cc9c78ad7..37c11eb40806e9ee9560397f73101a97ecd972ce: avisos para mirar, no un veredicto
producto +0/−0
arnés +27/−20
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

</details>
