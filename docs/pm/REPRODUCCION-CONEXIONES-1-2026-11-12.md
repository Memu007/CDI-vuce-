# Reproducción de CONEXIONES-1 B (2026-11-12, PM principal)

Entrega `c57b645e` (informe), arnés `ff2e2aae`, `9c6f721f` y `37c11eb4`, Dev
técnica. Producto igual a `c8733be`: `git diff c8733be c57b645e -- proyecto_maria
Dockerfile requirements.txt` da 0 líneas.

**Estado: aceptada como medición sobre `c57b645e` e integrada.** D180 (a):
CONEXIONES-1 C, sólo arnés (medir a otra cuenta); el arreglo de producto es
propuesta a Emi. D181 (b).

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
  por cuenta (sin decorador; el `Limiter` de `core/rate_limit.py:67` no trae
  límite por defecto). Retiene la conexión hasta 30 s (`NCM_GEMINI_TIMEOUT_S`) mientras
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

Por eso, (a), decidido por la PM: hay camino de hoy para que una cuenta sola
tome todo el pool. Falta medir si eso hace esperar o fallar a **otra**
cuenta: es CONEXIONES-1 C, sólo arnés. El arreglo de producto va a Emi,
porque la fila del roadmap dice «arreglar sólo si las deja» y no quedan
(consejero). El login queda afuera: cero 500 y 3,1 a 3,7 s.

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

# Reproducción de CONEXIONES-1 C (2026-11-12, PM principal)

Entrega `9ecfd2ac` (informe), arnés `33c61162` y `76b50666`, Dev técnica.
Base `8d61bb09`. `chequeo-6 8d61bb09 76b50666`: producto +0/−0, arnés
+58/−27, historia vacía, 0 avisos.

**Estado: aceptada como medición sobre `9ecfd2ac` e integrada.** D182 (el
arreglo) va a Emi.

Corrido en `/tmp/cdi-pm/wt-con1c` (`76b50666`) y en `/tmp/cdi-pm/wt-con1c-fix`
(`76b50666` más el arreglo a mano), todo `--pico 60 --lento 30`, con
`con_pg16.sh`. Mi arreglo es el del informe línea por línea; el diff del
informe no entra con `git apply` porque el hunk de `main.py:10448` está
cortado, y lo apliqué a mano. Lo que corrí:

```diff
@@ require_billing_vigente
+    # Termina la transacción de lectura: si no, la conexión queda tomada
+    # mientras el endpoint espera a la IA o a la lectura del PDF.
+    await db.commit()
@@ sugerir_ncm, después de `limite = _segundos_de_entorno(...)`
+        await db.commit()
@@ tests/test_cobro_corte1.py, _commit_que_falla
-    if sys._getframe(1).f_code.co_filename != main.__file__:
+    quien = sys._getframe(1).f_code
+    if quien.co_filename != main.__file__ or quien.co_name == "require_billing_vigente":
```

## Lo corrido: la otra cuenta, espera máxima

| Corrida | bcrypt | sugerir (Gemini) | subida de PDF | 500 en total | rc |
|---|---|---|---|---|---|
| hoy, sin cuota | 3,01 s | **30,02 s** | **30,0 s** | 10 (de la cuenta que satura) | 4 |
| hoy, cuota de producción | 3,38 s | **30,04 s** | **5,26 s** | 0 | 4 |
| arreglo, sin cuota | 2,89 s | 0,32 s | 0,04 s | 0 | 0 |
| arreglo, cuota de producción | 2,81 s | 0,35 s | 0,06 s | 0 | 0 |

- Igual al informe en la forma y en el orden de magnitud. La subida con
  cuota me dio 5,26 s contra 6,51 s: es una carrera.
- Con el arreglo, en sugerir, máxT/máxPG baja de 50/50 a 27/28 y 25/28;
  `close_con_transaccion` baja de 280 a 105. Al final, `tomadas` 0 en las
  cuatro.
- **`sabotajes/conexiones1.sh 76b50666`:** cinco `BIEN` y rc=0 (sin sabotaje,
  los dos `close` cancelados y los dos sabotajes de producto).
- **Mi negativo, pico de 40 con el arreglo:** rc=0, «sin conexiones
  tomadas», log limpio, 0 × 500. La otra cuenta espera 2,29 s (bcrypt),
  0,25 s (sugerir) y 0,06 s (subida). La subida sigue en máxT/máxPG 40/40 con
  un pico de 40 (con 60, 50/50): cada pedido toma una conexión, pero la otra
  cuenta no espera. Pico momentáneo, no retención (inferido: no muestreé en el
  tiempo).
- **pytest con el arreglo** (`test_cobro_corte1.py` y `test_excel2b.py`): 201
  passed. El rc=1 es sólo el piso de cobertura, que no aplica a una parte de
  la suite.
- **Sin el ajuste del inyector** (`test_cobro_corte1.py`): 4 failed, los cuatro
  que nombra el informe. El ajuste es necesario.
- **Ocho rutas con `Depends(require_billing_vigente)`:** las conté en
  `main.py`; coinciden con la lista del informe.

## El adversario (opus alto) y lo que verifiqué

Verificado por mí:
- `/api/migrations/analyze` pasa por la dependencia y
  después lee el Excel (hasta 60 s). El arreglo suelta la conexión de la
  dependencia, pero no medí si el análisis toma otra: a medir.

Para medir, no verificados:
- `/api/operations/manual` retendría la conexión mientras espera el cuerpo.
- Cada pedido pide conexión dos veces (usuario y ruta).
- El `commit` de `sugerir_ncm` no tiene manejo de error propio.
- No copiar el `commit` a `require_active_billing` sin resolver
  `_expire_extra_ops` (`billing_service.py:109-118`): es condición de la pieza.
- Falta una prueba rápida que dé rojo sin los `commit`. El medidor ya
  distingue (rc=4 hoy, rc=0 con el arreglo); falta un sabotaje con ancla en
  código en `conexiones1.sh` y un pytest.

## No corrido

- `/security-review`, la suite completa y `e2e_maria.sh` con el arreglo: van en
  la pieza de producto, si Emi dice que sí.
- La subida muestreada en el tiempo y `/api/migrations/analyze` con otra
  cuenta: CONEXIONES-1 D.

# Reproducción de CONEXIONES-1 D (2026-11-12, PM principal)

Entrega `c1311852` (informe), arnés `ebd2c1fd` y `f9962e6e`, merge `75349ca8`,
Dev técnica. Base `18202930`. `chequeo-6 18202930 f9962e6e`: producto +0/−0,
arnés +140/−21, historia vacía, 0 avisos.

**Estado: aceptada como medición sobre `c1311852` e integrada.** D183 se suma
a D182 para Emi, con una condición nueva (abajo, hallazgo 1).

**Lo que cierra:** el pedido manual se frena sólo del lado del cliente (el
medidor manda medio cuerpo; el producto no tiene nada inyectado). Con eso,
**hoy una cuenta con sesión le hace dar 500 a otra cuenta**, sin IA ni PDF de
por medio. Era el «no corrido» de B.

Corrido en `/tmp/cdi-pm/wt-con1d` (`f9962e6e`) y en `/tmp/cdi-pm/wt-con1d-fix`
(`f9962e6e` más el diff del informe, que entra con `git apply --check` rc=0),
todo `--pico 60 --lento 30` con `con_pg16.sh`.

## Lo corrido: la otra cuenta, espera máxima

| Corrida | bcrypt | sugerir | subida PDF | analyze (Excel) | manual (cuerpo) | 500 de la otra cuenta | rc |
|---|---|---|---|---|---|---|---|
| hoy, sin cuota | 3,51 s | **30,03 s** | **29,98 s** | **30,25 s** | **30,08 s** | 24 (12 analyze, 12 manual) | 4 |
| arreglo, sin cuota | 3,3 s | 0,3 s | 0,04 s | 0,07 s | 0,03 s | 0 | 0 |
| arreglo, cuota de producción | 3,16 s | 0,34 s | 0,03 s | 0,07 s | 0,03 s | 0 | 0 |

- Igual al informe en forma y magnitud (el informe: hoy 12 × 500 hasta
  30,13 s en analyze y manual; con el diff, máximo 3,77 s).
- Hoy, contadores del log: `QueuePool limit` 280, `Exception in ASGI` 54,
  `Error logging metrics` 10, `Traceback` 324; los mismos del informe. Con el
  arreglo, todos 0.
- **manual:** hoy, «50 de 60 esperando el cuerpo con 50 conexiones tomadas»;
  con el arreglo, «60 de 60 llegaron en 0,64 s con 0 conexiones tomadas».
- **Subida de PDF muestreada en el tiempo (hoy):** T=50 hasta 30,98 s,
  después baja en escalones a los ~31, ~61, ~91 y ~121 s, y a 0 en 127,5 s,
  con 4 PDFs en el lector. Es lo que dice el informe. Parte de esas 50 la
  toman pedidos que esperan el candado de validación antes del lector. Con el
  arreglo, T=50 sólo en la muestra de llegada (~0,56 s) y después 0.
- **Filas perdidas en `api_logs` (hoy, `pico_excel`):** 72 pedidos, 62
  filas. Los 10 `Error logging metrics` los conté en todo el log, no por
  fase: que sean esas 10 es inferido.
- `close_con_transaccion`: 434 hoy, 165 con el arreglo.
- **`sabotajes/conexiones1.sh f9962e6e`:** cinco `BIEN`, rc=0.

## Lo probado por la PM

- `tests/test_conexiones1.py`: 4 failed sin el diff, 4 passed con el diff.
- **Mi negativo 1:** `_leer_cuerpo` movida después de `require_active_billing`
  → 1 failed. La prueba distingue el orden.
- **Mi negativo 2:** analyze con un cliente ya existente → 200, `existing` 1,
  0 conexiones tomadas durante la lectura.
- Las 1113 líneas «Task was destroyed» son anteriores al diff.


## El adversario (opus alto) sobre `_leer_cuerpo` y el `commit` de analyze

Corrió con SQLite y NullPool, no con Postgres. Suite tocada con el diff: 204
passed.

1. **Cliente que corta a mitad del cuerpo: 500 y ERROR con traza; hoy, 400
   sin ruido. Reproducido por mí** (ASGI a mano en `wt-con1d-fix`, sesión
   válida, dos trozos y `http.disconnect`): con `_leer_cuerpo`, `[500]
   ClientDisconnect`; anulándola, `[400] Body JSON inválido`. Cualquier
   cuenta con sesión lo provoca, también una impaga. No toca datos.
   **Condición de la pieza de producto:** un corte a mitad del cuerpo
   contesta como hoy, sin ERROR ni fila 500.
2. **El cuerpo entero se lee antes del 402 y del 429** (del adversario, no
   reproducido por mí): una cuenta impaga hace leer 32 MB antes del 402. El
   401 y el 403 de CSRF siguen antes. El mismo vector ya existe sin sesión
   en las rutas con cuerpo tipado (`/process_operation/`). **Riesgo**;
   sugerencia para la pieza: un tope de tamaño.
3. **analyze toma una conexión nueva al final** para guardar el respaldo;
   con el pool lleno, la falla llega después de leer el Excel, con
   rollback y 500. No pierde nada. Leído, no corrido. **Riesgo.**

Lo que no rompe, según el adversario: el `commit` de analyze no confirma
nada ajeno (`require_billing_vigente` y `_vencer_y_guardar` ya confirmaron);
los clientes siguen usables (`expire_on_commit=False`); no hay carrera
nueva (`confirm` relee con `FOR UPDATE`); la ruta no usa `SET LOCAL`.

## No corrido

- «Hoy, cuota de producción» en D (la de C sigue valiendo para sugerir y
  la subida).
- El adversario con Postgres; el hallazgo 3 corrido.
- `/security-review`, la suite completa y `e2e_maria.sh` con el arreglo: van
  en la pieza de producto, si Emi dice que sí.

## E (sólo arnés): aceptada sobre `19714ecf` (2026-11-12 06:55 UTC)

Base `89d3fa3c`. Arnés +31/−21, producto 0. `chequeo-6`: igual al informe,
historia vacía, 0 avisos.

Leído en el diff:

- El sabotaje nuevo se ancla en `session.add(log_entry)`, que es código.
  Ninguna espera fija nueva: `grep '^+' | grep -i sleep` da vacío.
- El contador de «Error logging metrics: QueuePool limit» va por fase. Cada
  fase anota dónde termina el log al empezar y lo lee recién cuando
  `_cerrada` dio vacío, es decir, cuando ya terminaron sus tareas de
  registro. La sonda cuenta `log_tareas_fin` en el callback de fin de la
  tarea (`conexiones1_sonda.py:98`), o sea después del print. La app corre
  con `PYTHONUNBUFFERED=1`. Por eso una corrida sin arreglo no puede pasar
  de rc=4 a rc=2 por el orden del log.
- Una fase con menos avisos que filas perdidas queda inválida
  (`enviados - filas > explicadas`). También queda inválida si hay filas de
  más.

Reproducido en un worktree:

| corrida | resultado |
|---|---|
| producto de D + `test_conexiones1.py` de E | `1 failed, 4 passed`; body-400: `assert 500 == 400` |
| diff revisado (`git apply --check` limpio) + `test_conexiones1` + `test_cobro_corte1` | `103 passed, 3 warnings in 61.50s` |
| medidor con el diff revisado (`--pico 60 --lento 30`) | rc=0, «sin conexiones tomadas»; detalle abajo |
| `sabotajes/conexiones1.sh 19714ecf` | rc=0, seis `BIEN`; el nuevo: «el producto pierde filas de api_logs sin avisar: salida 2, dice «no explican la diferencia»» |

Detalle del medidor:

- `corte_manual_a_medias`: {400: 15}, como máximo 1 conexión tomada.
- `pico_cuerpo_manual`: «60 de 60 esperando el cuerpo a la vez (llegaron en
  0.58 s, con 0 conexiones tomadas)». La otra cuenta recibió 0 × 500 y
  esperó hasta 0,03 s.
- En el log: «Exception in ASGI application», «Traceback», «QueuePool
  limit» y «Error logging metrics» aparecen 0 veces. Hay 826 filas de
  `api_logs` para 826 tareas de registro.

**Mis negativos** cortan de otras dos formas: sin mandar nada del cuerpo,
y en tres trozos antes de cortar. Con el `except ClientDisconnect` las dos
dan 400 «Body JSON inválido», sin ERROR. Sin él dan 500, y el log dice
«Excepcion no manejada en POST /api/operations/manual: ClientDisconnect».
La condición del corte se cumple, y no sólo para el ejemplo del caso.

**D185: (a), decidido por la PM.** Un tope de tamaño para el cuerpo leído
antes del 402 y del 429 no entra en esta fila. Es exposición que crea el
propio diff: una cuenta impaga o sin cuota hace leer el cuerpo entero.
Por eso va a Emi como una línea de riesgo dentro del punto 13, y a la cola
como pieza propia.

**Lo que cambia para la pieza de producto:**

- El diff tiene un trozo más, el import de `ClientDisconnect`.
- Un corte de una cuenta impaga contesta 400 en vez de 402.
- El cuerpo se lee antes del 402 y del 429.
- El texto «Body JSON inválido» queda en dos lugares (§6, declarado por la
  Dev).

### No corrido por mí

- El medidor sin el diff. La Dev informa rc=4. No hace falta que lo corra:
  el corte del segmento de log espera a las tareas de registro (ver arriba).
- Los adversarios, `/security-review`, la suite completa y `e2e_maria.sh`
  con el diff revisado. Van en la pieza de producto.
