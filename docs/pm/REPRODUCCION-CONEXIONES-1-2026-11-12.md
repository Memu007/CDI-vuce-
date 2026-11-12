# Reproducción de CONEXIONES-1 B (2026-11-12, PM principal)

Entrega `c57b645e` (informe), arnés `ff2e2aae`, `9c6f721f` y `37c11eb4`, Dev
técnica. Producto igual a `c8733be`: `git diff c8733be c57b645e -- proyecto_maria
Dockerfile requirements.txt` da 0 líneas.

**Estado: aceptada como medición sobre `c57b645e` e integrada.** D180 (a):
el arreglo va en una pieza aparte, CONEXIONES-1 C. D181 (b).

Corrido en `/tmp/cdi-pm/wt-con1` (`c57b645e`), con el venv de la PM:
gunicorn 26.2.0 y uvicorn 0.54.0. Medidor con `ENVIRONMENT=production`,
`GEMINI_API_KEY` vacía y `AI_DAILY_PDF_LIMIT=100000` (lo pone el medidor).

## Lo corrido

| Corrida | Resultado |
|---|---|
| Base (valores por defecto, pico de 30) | rc=0, «sin conexiones tomadas»; `pico_pdf` 422 × 30; normales hasta 2,23 s; `bcrypt_en_vuelo_max` 27 |
| `--pico 60 --lento 30 --plazo 600` | rc=1. `pico_pdf`: 422 × 16 · 500 × 10 · 504 × 34 (los 500 son `TimeoutError` × 10), normales 30,01 s. `pico_gemini`: 200 × 60, normales 30,07 s. `pico_bcrypt`: 401 × 60, normales 3,68 s. Al final: `tomadas` 0, `libres` 20, `close` empezados = terminados = 2968. `QueuePool limit` 50 en el log |
| `--pico 60 --lento 15 --plazo 400` (negativo de la PM) | rc=1. `pico_pdf`: 422 × 32 · 500 × 6 · 504 × 22 (`TimeoutError` × 6), normales 29,98 s. `pico_gemini`: 200 × 60, normales 30,0 s. `pico_bcrypt`: normales 3,13 s. Al final, `tomadas` 0, `libres` 20, `close` 2976 = 2976. `QueuePool limit` 30 |
| `sabotajes/conexiones1.sh` | cinco líneas `BIEN`: sin sabotaje rc=0; los dos `close` cancelados y los dos sabotajes de producto, rc=1 |
| `chequeo-6` en los tres rangos | igual al informe: `740ba3af..ff2e2aae` arnés +785/−0 con el AVISO de `_instalar` (96 líneas, explicado en el informe); `c8733be3..9c6f721f` arnés +28/−1; `5db9c1ec..37c11eb4` arnés +27/−20; producto +0/−0 e historia vacía en los tres |

La corrida de 30 s da exactamente los números del informe. La de 15 s la
corrí una vez, porque es una carrera; queda así: se rompe con 15 s, como
calcula el informe (más de unos 10 s).

**Diferencia menor:** `bcrypt_en_vuelo_max` me dio 36 con 30 s y 40 con 15 s;
el informe dice 40. Es cuántos llegan a la vez al grupo de hilos (tope 40):
varía de corrida en corrida y no cambia ninguna conclusión.

## Lo que mide el medidor y lo que no

- **El rc=1 de las corridas lentas no es una fuga.** El veredicto
  «QUEDAN CONEXIONES TOMADAS» sale si el log tiene `QueuePool limit`
  (`SEÑALES_DE_FUGA`), aunque al final queden 0 tomadas. La tabla sí
  distingue (columna `quedan` en 0, `tomadas` 0). El texto junta pool lleno y
  fuga: CONEXIONES-1 C tiene que separarlos.
- **Los «normales» son la misma cuenta que carga el pico.** Todos usan el
  token `normal`. Lo que pasa con otro usuario no está medido.
- **La IP al azar no cambia nada en la subida:** su límite por IP es
  `3000/minute` (`get_dynamic_rate_limit`, `config.py:44`). Leído, no corrido.
- **No miré cuál señal dispara cada rojo del control** (`tomadas`,
  `non-checked-in connection` o `Task was destroyed`). El control da el rojo
  esperado en los cuatro sabotajes.

## D180: el camino de hoy, con una sola cuenta

Leído en el código, con la configuración de producción (un worker, una
réplica: `Dockerfile`, `railway.json`; pool 20 + 30):

- **`/api/ncm/sugerir`** (`main.py:10331`) no tiene límite por minuto ni cuota
  por cuenta. Retiene la conexión hasta 30 s (`NCM_GEMINI_TIMEOUT_S`) mientras
  espera a Gemini. `pico_gemini` usa un solo token: **una cuenta sola llega a
  50 de 50 conexiones** y los normales esperan 30 s. Medido, sin 500.
- **`/upload_pdf/public`**: la cuota de producción es 50 PDFs por día y por
  cuenta (`AI_DAILY_PDF_LIMIT`, en memoria del proceso), justo el total del
  pool. Se mira después de validar. Antes, la conexión ya está tomada mientras
  el pedido espera el candado de validación de su usuario (hasta 30 s,
  `PDF_VALIDATE_TIMEOUT_S`): **una cuenta sin cuota igual toma conexiones
  antes del 429.** Leído, no medido.
- Que una cuenta le haga dar 500 a **otro** usuario con la configuración de
  producción: **no corrido**. Lo medido es que lo hace esperar unos 30 s, en el
  borde de `pool_timeout`.

Por eso, (a), decidido por la PM: hay camino de hoy para «una cuenta deja a
todos esperando unos 30 s», y con un poco más, 500.

## D181: (b)

60 claves malas desde 60 IPs no las corta nada, y eso pide 60 IPs. El caso que
importa es la misma IP: `@limiter.limit("5/minute")` (`main.py:3231`) corta
antes de entrar al login, con almacenamiento en memoria en un solo worker.
`abuso1` lo prueba en serie (`test_s4_el_limite_por_minuto_del_login_cuenta_la_ip_real`);
**en simultáneo no está corrido**. El pool que toma bcrypt es la D180.

## No corrido

- Adversarios y `/security-review`: esta entrega no tiene producto. Van en
  CONEXIONES-1 C.
- El caso de otro usuario, la cuota de 50 en producción y la misma IP en
  simultáneo (arriba).
