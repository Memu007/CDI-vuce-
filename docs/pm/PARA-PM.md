# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

> **BORRADOR, todavía no entregado.** Falta la medición con 8 s de demora y el adversario. Cuando entregue, te aviso con el SHA.

## CONEXIONES-1 parte B sobre lo integrado (cierra D134). Ninguna conexión queda tomada; el pool se llena con trabajo lento. Dos D para decidir

| Qué | SHA |
|---|---|
| Entrega (este informe) | el commit de este informe, encima de `37c11eb4` |
| Arnés | `ff2e2aae` (medidor, sonda y control), `9c6f721f` (dos sabotajes de producto en el control), `37c11eb4` (el control corta cada corrida apenas tiene su rojo) |
| Medición base | `c8733be3` (merge de tu rama). `git diff c8733be3 37c11eb4 -- proyecto_maria Dockerfile requirements.txt` da 0 líneas: es el mismo producto que entrego |
| Control y medición con pico 60 | `37c11eb4` |

**Producto tocado: ninguno.** `git rev-list --no-merges ff2e2aae^..37c11eb4 --not origin/claude/practical-shannon-szpwkn -- proyecto_maria` da sólo `524a8f00`, `6c2b3383` y `cc8b834b`, que son de BORRADOR-1 (pieza anterior).

**Resultado**
- Un `close()` cancelado no deja conexiones tomadas. Probé 401 de seis tipos, normales, mezcla, `/api/ncm/sugerir`, la subida pública de PDF, cuatro tipos de corte en vuelo y picos de bcrypt, Gemini y PDF. En todos, al final quedan 0 tomadas, `close_empezados` = `close_terminados` y Postgres queda en `{'idle': 20}`.
- El control da rojo cuando la sesión no se cierra: con dos sabotajes de la sonda (cancelar el `close` a propósito, guardando la sesión o soltándola) y con dos del producto (el `finally` de `get_async_session` no cierra, guardando la sesión o soltándola).
- Lo que sí aparece es **saturación**. Cada pedido lento (bcrypt, Gemini, lector de PDF) tiene su conexión tomada mientras espera. Con 60 en paralelo, el pool llega a 50 de 50 (20 + 30 de desborde) y los pedidos normales esperan hasta 6,79 s. Una conexión tomada así no es una pérdida: vuelve al terminar el pedido. Es la D180.
- Como no quedan conexiones tomadas, no hay arreglo: el producto queda sin cambio y el aviso de las pruebas sigue en riesgos.

## Decisiones

**D180. El pool se llena con trabajo lento.**
- Opciones:
  - (a) Una pieza aparte que suelte la conexión antes del trabajo lento (bcrypt, Gemini, lector de PDF) o que limite cuántos de esos esperan con conexión tomada. Esa pieza lleva su rojo.
  - (b) Aceptarlo como riesgo y anotarlo.
- Recomiendo LENTO8_RECOMENDACION
- Datos:
  - Con un solo worker (el `Dockerfile`), el tope es 50 conexiones.
  - Hace falta tener a la vez más de 50 pedidos lentos para llenarlo.
  - Con pico 60 y 2 s de demora falsa, ningún pedido normal dio error; esperaron 3,14 s (bcrypt), 3,99 s (Gemini) y 6,79 s (PDF).
  - LENTO8_DATOS

**D181. D146 con los números de bcrypt.** Pediste mantener D146 en la cola de limpieza hasta tener esta medida.
- Opciones:
  - (a) Contar antes de verificar, en una pieza propia.
  - (b) Dejarlo en la cola de limpieza.
- Recomiendo (b).
- Por qué:
  - 60 claves malas en paralelo para la misma cuenta, cada una desde otra IP, dieron 60 × 401 y ningún 429. El límite va por IP (`login:{ip}`) y por IP y cuenta (`cuenta:{username}:login:{ip}`), así que con IPs distintas ninguno de los dos corta, se cuente antes o después de bcrypt.
  - La IP que usa el límite la arma el último proxy de confianza (`get_client_ip`, `core/rate_limit.py`). En el medidor la pone el cliente, porque no hay proxy delante. En producción, esto equivale a un atacante con 60 IPs propias, no a alguien que la invente.
  - Lo que esos 60 sí hacen es tomar el pool: llega a 50 de 50, y los pedidos normales esperan hasta 3,14 s.
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

LENTO8_SECCION

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
- **Un solo worker.** Es la configuración del `Dockerfile`. Con más workers, el tope de Postgres se multiplica por cada uno; no lo medí.

## Hallazgos del adversario

ADVERSARIO_TABLA

## Riesgos

- **El aviso de las pruebas sigue.** Que no queden conexiones tomadas en esta medición no prueba que no queden en otras rutas o con otros tiempos. La medición cubre las rutas de arriba con un worker.
- **Las causas de los topes en vuelo, sin verificar.** Gemini llega a 8 en vuelo y el lector de PDF a 4, y no comprobé de dónde sale cada número. Hay candidatos (`_HILOS_MP` en `main.py:11211` y semáforos en `despacho_lector.py:699` y `:725`), pero no los afirmo.
- **Demoras falsas.** Gemini y el lector de PDF son falsos y demoran lo que dice `--lento`. Un Gemini real puede demorar más; la espera de los normales crece con eso.

## Para reproducir

```bash
PY=<venv>/bin/python scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_medir.py              # «sin conexiones tomadas», rc=0
PY=<venv>/bin/python scripts/testing/con_pg16.sh $PY scripts/testing/conexiones1_medir.py --pico 60    # máxT 50 en los tres picos, «sin conexiones tomadas»
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
