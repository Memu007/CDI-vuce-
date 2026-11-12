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

## E (sólo arnés): aceptada sobre `19714ecf` (2026-11-12 06:52 UTC)

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
Por eso va a Emi como una línea de riesgo dentro del punto 13.

**Lo que cambia para la pieza de producto:**

- El diff tiene un trozo más, el import de `ClientDisconnect`.
- Un corte de una cuenta impaga contesta 400 en vez de 402 (leído, no
  corrido; lo prueba F).
- El cuerpo se lee antes del 402 y del 429.
- El texto «Body JSON inválido» queda en dos lugares (§6, declarado por la
  Dev).

### No corrido por mí

- El medidor sin el diff. La Dev informa rc=4. No hace falta que lo corra:
  el corte del segmento de log espera a las tareas de registro (ver arriba).
- Los adversarios, `/security-review`, la suite completa y `e2e_maria.sh`
  con el diff revisado. Van en la pieza de producto.

## F (sólo arnés y diff revisado): aceptada sobre `21df2a39` (2026-11-12 09:19 UTC)

Informe de la Técnica en `PARA-PM.md` de `21df2a39`; sólo trae ese
archivo (`git diff 759241ff 21df2a39 --stat`). El diff revisado, la
alternativa D186 y `sabotajes_f.py` los saqué del informe con sus `awk`.
Árboles descartables `/tmp/cdi-pm/wt-con1f` (`35c19be7`) y
`wt-con1f-head` (`759241ff`). `ls /tmp/conftest.py /tmp/cdi-pm/conftest.py`:
«No such file or directory» los dos.

### Lo corrido por la PM

| Qué | Dónde | Salida |
|---|---|---|
| `git apply --check` del diff revisado, en árboles nuevos | `35c19be7` y `759241ff` | «check limpio» en los dos |
| Pruebas de F sin el diff (rojo) | `35c19be7` | 7 failed, 1 passed; `('impaga', 402, 402, 'sin leer') != ('impaga', 400, 402, 0)`; `('al leer', 200, '', 1, 200, 2) != ('al leer', 500, …, 0, 200, 1)` |
| Con el diff revisado | `35c19be7` | `test_conexiones1.py` + `test_cobro_corte1.py`: 106 passed |
| `sabotajes_f.py` | `35c19be7` + diff | los 9 ROJO, con el mismo texto de rojo que la tabla del informe; «sabotajes sin rojo: ninguno», rc=0 |
| Alternativa D186 + `test_conexiones1.py` | `35c19be7` | 1 failed, 7 passed: `('impaga', 402, 402, 'sin leer') != ('impaga', 400, 402, 0)` |
| Alternativa D186 + pruebas de cobro (`test_cobro_corte1`, `test_cobro_mp1*`, `mp2`, `mp3`, `test_billing_*`, `test_api_clientes_billing`, `test_g7_cobro`) | `35c19be7` | 482 passed |
| Exención de `test_cobro_corte1.py`: `_commit_que_falla` sin `raise` | `759241ff` + diff | 4 failed, 94 passed (`importacion_al_confirmar`, `al_confirmar`, `al_confirmar_y_deshacer`, `al_confirmar_sin_enlaces`): los casos eximidos siguen llegando a la falla |
| `chequeo-6 35c19be7` con el diff commiteado en un árbol descartable (`4d64fb8c`, no es un SHA entregado) | | igual al informe: producto +26/−1, 1 AVISO explicado (+25 netas), historia vacía |

**Mis negativos** (en `759241ff` + el diff revisado; código abajo):

1. **Pool lleno al leer, pero la otra cuenta suelta mientras analyze espera
   para guardar** (espera del pool 10 s, como producción con 30 s): 200 y 1
   respaldo; al pedir conexión el pool tenía 5 de 5 tomadas. Sabotaje: la
   otra cuenta no suelta (espera 0,5 s) → `(500, 0, 5, [5]) != (200, 1, 5,
   [5])`. O sea: el 500 de F aparece sólo si el pool queda lleno durante toda
   la espera, y nunca deja medio respaldo.
2. **Cuerpos raros en `/api/operations/manual`**, como datos de un caso:
   corte sin un byte (al día y impaga) → 400 «Body JSON inválido»; JSON roto
   completo, al día → 400 «Body JSON inválido»; JSON roto completo, impaga →
   **402**. Ese último dato contradice el punto 4 del informe: con
   `_leer_json` el JSON se parsearía antes del plan y esa cuenta pasaría a
   400. El contrato HTTP sí cambia en ese caso.

### Leído

- `_FRIENDLY_5XX` (`main.py:466`) explica por qué el 500 de analyze dice
  «No pudimos procesar tu solicitud» y no el texto de la ruta.
- `expire_on_commit=False` (`database/connection.py:79`): los clientes y
  el usuario siguen cargados después de los `commit` nuevos.
- `sabotajes_f.py` ancla `SUELTA` y `COBRO` en líneas de comentario
  (§6: el ancla es código). Hoy el script vive en el informe, no en el repo:
  queda como condición cuando entre al repo.
- Los `commit` nuevos de `require_billing_vigente` y de analyze no tienen
  `try`, el de NCM sí. Lo que pasa con la base caída en cada uno no tiene
  caso: condición de la pieza de producto.
- La alternativa D186 pone un `commit` en `require_active_billing`, que
  llama a `can_create_operation` → `_expire_extra_ops`
  (`billing_service.py:109`, `:164`). En C quedó «no tocar
  `require_active_billing` sin resolver `_expire_extra_ops`»: es la razón
  para no elegir (b) todavía, no la del punto 1 de F (que se escribió para
  el diseño de leer el cuerpo primero).

### Decisiones

- **D186: (a) por ahora, decidido por la PM.** (b) suelta igual la conexión
  y no trae los dos cambios del punto 13 ni el riesgo del tope, pero guarda
  en la dependencia el vencimiento de créditos extra. G lo mide en una
  tercera columna, con un caso de créditos extra vencidos y una recarga a la
  vez. Si sale bien, la PM le lleva (b) a Emi como la recomendada.
- **D187: (a), decidido por la PM.** `pool_timeout=0.05` no es una espera
  fija: el caso no duerme; el motor deja de esperar.

### No corrido por la PM

- La suite completa y `e2e_maria.sh` con el diff revisado: sólo la corrida
  de la Dev (6085 passed, E2E MARIA OK). La puerta va sobre el SHA de la pieza
  de producto.
- Adversarios y `/security-review`: en la pieza de producto.

<details><summary>Negativos de la PM (no van al repo)</summary>

```python
"""Negativos de la PM sobre CONEXIONES-1 F (no van al repo)."""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import AsyncAdaptedQueuePool
from starlette.requests import Request

from proyecto_maria import main
from proyecto_maria.database import connection as _conn
from proyecto_maria.services import migration_service
from tests.test_conexiones1 import _sesion, _respaldos, _impaga, MANUAL


def test_pm_pool_lleno_al_leer_pero_se_libera_mientras_espera(monkeypatch):
    """Con espera de pool larga (como producción), si la otra cuenta suelta
    mientras analyze espera conexión para guardar, contesta 200 y guarda 1."""
    c, nombre = _sesion(monkeypatch)
    leer, guardar = migration_service.analyze_migration_file_async, AsyncSession.commit
    archivo = {"file": ("clientes.csv", b"cuit,nombre\n20123456786,Cliente Uno\n", "text/csv")}
    motor = create_async_engine(_conn.DATABASE_URL, poolclass=AsyncAdaptedQueuePool,
                                pool_size=5, max_overflow=0, pool_timeout=10)
    otras, liberar, pidio = [], [], []
    pedir = motor.pool._do_get

    def pedir_marcando():
        if len(otras) == 5:
            pidio.append(motor.pool.checkedout())
        return pedir()
    motor.pool._do_get = pedir_marcando

    async def leer_y_llenar(*a, **k):
        while motor.pool.checkedout() < motor.pool.size():
            otras.append(await motor.connect())
        return await leer(*a, **k)

    async def guardar_soltando(self, *a, **k):
        if otras and not liberar:
            async def soltar():
                # Suelta recién cuando el commit ya está esperando en la cola del pool.
                while not pidio:
                    await asyncio.sleep(0)
                for o in otras:
                    await o.close()
            liberar.append(asyncio.ensure_future(soltar()))
        return await guardar(self, *a, **k)

    monkeypatch.setattr(migration_service, "analyze_migration_file_async", leer_y_llenar)
    monkeypatch.setattr(AsyncSession, "commit", guardar_soltando)
    antes = _respaldos(nombre)
    _conn.AsyncSessionLocal.configure(bind=motor)
    try:
        with c:
            r = c.post("/api/migrations/analyze", files=archivo)
            c.portal.call(motor.dispose)
    finally:
        _conn.AsyncSessionLocal.configure(bind=_conn.engine)
    assert (r.status_code, _respaldos(nombre) - antes, len(otras), pidio[:1]) == (200, 1, 5, [5]), r.text


def _cortar_sin_nada(pedido):
    mensajes = iter([{"type": "http.disconnect"}])

    async def recibir():
        return next(mensajes)
    pedido._receive = recibir


def test_pm_cuerpos_raros_en_manual(monkeypatch):
    """Familia de cuerpos: corte sin un byte (impaga y al día), JSON roto
    completo (impaga y al día). (cuenta, cuerpo, código)."""
    CASOS = [
        ("al dia", "corte vacio", 400),
        ("impaga", "corte vacio", 400),
        ("al dia", "json roto", 400),
        ("impaga", "json roto", 402),
    ]
    leer, vieron = Request.body, []
    for cuenta, cuerpo, _cod in CASOS:
        with monkeypatch.context() as mp:
            c, nombre = _sesion(mp)
            if cuenta == "impaga":
                _impaga(nombre)
            if cuerpo == "corte vacio":
                async def frenar(self):
                    if not hasattr(self, "_body"):
                        _cortar_sin_nada(self)
                    return await leer(self)
                mp.setattr(Request, "body", frenar)
            with c:
                if cuerpo == "json roto":
                    r = c.post("/api/operations/manual", content=b'{"client_id": ',
                               headers={"content-type": "application/json"})
                else:
                    r = c.post("/api/operations/manual", json=MANUAL)
        detalle = r.json().get("detail")
        vieron.append((cuenta, cuerpo, r.status_code,
                       detalle if isinstance(detalle, str) else type(detalle).__name__))
    print(vieron)
    assert [v[:3] for v in vieron] == [(a, b, c) for a, b, c in CASOS], vieron
```

</details>

## G (sólo arnés): aceptada sobre `6ce56cf9` (2026-11-12 10:13 UTC)

Informe de la Técnica en `PARA-PM.md` de `6ce56cf9`. Producto +0/−0:
`git diff 2c69edf4 6ce56cf9 --stat -- proyecto_maria/` vacío; `chequeo-6`
igual al informe (arnés +592, historia vacía, 0 avisos). Los diffs (a) y (b)
y el arreglo de prueba de una línea («verde») los saqué del informe. Árbol
descartable `/tmp/cdi-pm/wt-g` en `6ce56cf9`, Postgres 16 descartable de
`scripts/testing/con_pg16.sh`.

### Lo corrido por la PM

| Qué | hoy | (a) revisado | (b) alternativa | verde | (a)+verde | (b)+verde |
|---|---|---|---|---|---|---|
| `conexiones1_creditos.py` (usuario y org, control y carrera) | PIERDE las dos carreras, «quedan 0 de 10 pagos», rc=1 | rc=1, igual | rc=1, igual | 4 OK, rc=0 | 4 OK, rc=0 | 4 OK, rc=0 |
| `conexiones1_cuerpo.py --rondas 1x100,4x100`: pico RSS (MB) | 157.7 · 158.5 | **357.7 · 959.3** | 157.9 · 158.9 | — | — | — |
| ídem: 402 con lo mandado | 3–4 MB, 0 retenidas | 100 MB, todas retenidas | 3–4 MB, 0 retenidas | — | — | — |
| ídem: otra cuenta al soltar, 4×100 | sin muestra | 249.4 ms | sin muestra | — | — | — |

Coincide con el informe (su 1×100 del revisado: pico 358.5). Los 4×500 MB
(pico 4159.7 MB) son de la Dev; no los corrí.

### Mi negativo: el orden de los candados

El arreglo verde toma la fila de la **org** en `require_active_billing`
(`db.refresh(entidad, with_for_update=True)`) y después la ruta cuenta con
`_cuenta_bloqueada` (`main.py:2257`), que toma **usuario y después org**. Una
cuenta de org, el **mismo usuario** con dos pedidos a la vez: alta manual (M)
y guardar una operación en un cliente (P). El arnés toma la org, espera a ver
M y P esperando, y suelta. Mide códigos y deadlocks de `pg_stat_database`.

| Árbol | control | carrera (3 rondas) |
|---|---|---|
| hoy | 200/200 | 200/200, deadlocks +0, las tres |
| verde | 200/200 | alta 200, **guardado 500**, deadlocks +1, las tres |
| (a)+verde | 200/200 | alta 200, **guardado 500**, deadlocks +1, las tres |
| (b)+verde | 200/200 | 200/200, deadlocks +0, las tres (no observado en este estado; no es una prueba de que no pueda pasar) |

El 500 tiene el texto amable («No pudimos procesar tu solicitud…»); el log
dice `DeadlockDetectedError` en `save_client_operation`. No verifiqué qué
quedó guardado ni contado después del 500. El ciclo pide dos pedidos del
mismo usuario a la vez (`_cuenta_bloqueada` bloquea el usuario que pide).
Cuentas sin org: no corrido (por lectura, una sola fila no arma ciclo).
Conclusión: verde como está no entra; arma el ciclo cuando la dependencia
sigue con la org tomada mientras la ruta cuenta. El negativo no tenía
créditos vencidos (`extra_ops_remaining = 0`, sin vencimiento): el caso de la
pieza los lleva como datos. Lo que separa (a) de (b) es la memoria de arriba.

### Leído

- `record_operation_created` (`billing_service`) corre sólo bajo el candado
  de `_contar_en_la_cuenta`: no es otro camino de pérdida. Mi sospecha,
  descartada.
- `_vencer_y_guardar` escribe `billing_status=past_due` desde una lectura
  sin candado; un aviso de pago de suscripción a la vez podría pisarse igual
  que la recarga. No medido: va como caso de la familia en la pieza.

### No corrido por la PM

- Adversarios, `/security-review`, suite y `e2e_maria.sh`: la entrega no
  tiene producto. Van en la pieza de producto.
- 4×500 MB, 8×100 MB y keep-alive: sólo la corrida de la Dev.
- El negativo en cuentas sin org y con usuarios distintos de la misma org.

<details><summary>Negativo de la PM (no va al repo; correr desde la raíz del repo con con_pg16.sh)</summary>

```python
"""Negativo PM sobre G: el arreglo de prueba bloquea la org antes que el usuario;
_cuenta_bloqueada bloquea usuario y después org. Con el mismo usuario de una org:
alta manual (M) y guardado en un cliente (P) a la vez. El arnés toma la org,
espera a ver M y P esperando, y suelta. Mide códigos y deadlocks de Postgres."""
import os, sys
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "scripts/testing")
import conexiones1_creditos as h  # noqa: E402
import psycopg2  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def deadlocks():
    return h.sql("select deadlocks from pg_stat_database where datname = current_database()")[0][0]


def guardar(c, sesion, cliente):
    return c.post(f"/api/clientes/{cliente}/operaciones", headers=sesion, json={"items": []})


def ronda(c, carrera):
    sesion, cliente, ref, (tabla, clave, valor) = h.preparar(c, True)
    h.sql("update organizations set extra_ops_expires_at = null, extra_ops_remaining = 0 where id = %s", valor)
    antes = deadlocks()
    if not carrera:
        a, b = h.alta(c, sesion, cliente), guardar(c, sesion, cliente)
        return a.status_code, b.status_code, deadlocks() - antes, []
    with ThreadPoolExecutor(2) as hilos, closing(psycopg2.connect(h.URL)) as candado:
        try:
            with candado.cursor() as cur:
                cur.execute("select 1 from organizations where id = %s for update", (valor,))
                cur.execute("select pg_backend_pid()")
                mio = cur.fetchone()[0]
            m = hilos.submit(h.alta, c, sesion, cliente)
            ok1 = h.hasta(lambda: len(h.esperando(mio)) >= 1)
            p = hilos.submit(guardar, c, sesion, cliente)
            ok2 = h.hasta(lambda: len(h.esperando(mio)) >= 2)
            q = [" ".join(x.split())[:80] for x in h.esperando(mio)]
        finally:
            candado.rollback()
        rm, rp = m.result(h.PLAZO), p.result(h.PLAZO)
        return rm.status_code, rp.status_code, deadlocks() - antes, q + [f"armada: {ok1 and ok2}", rm.text[:100], rp.text[:100]]


def main():
    print(h.arbol())
    with TestClient(h.main_mod.app, raise_server_exceptions=False) as c:
        for carrera in (False, True):
            for _ in range(1 if not carrera else 3):
                am, gp, dl, extra = ronda(c, carrera)
                print(f"{'carrera' if carrera else 'control'}: alta {am}, guardado {gp}, deadlocks +{dl}")
                for x in extra:
                    print("    ", x)


main()
```

</details>

## Plan de la pieza de producto (sólo docs): leído sobre `b60c30d4` (2026-11-12 10:47 UTC)

Integrado con avance directo. Sin producto.

**Qué árbol es cada «(b)»:**
- en G, (b) era el `commit` en la dependencia; perdía la recarga (rc=1);
- en el plan, (b) es la manual con `require_billing_vigente` +
  `_contar_operacion_bloqueada`. Según la Dev, da deadlock en alta + recarga
  de la org (rc=2, 3/3). Lo arregla `_cuenta_bloqueada` con
  `FOR NO KEY UPDATE OF`.

Mi negativo de G (alta + guardado) no veía ese par.

**Lo reproducido por la PM:**
- El comando 1 da `2.0.25 True False`: sin `of=`, `key_share` comparte la
  clave de cache con `FOR UPDATE`.
- El comando 2 da 3755 `require_active_billing` y 3840, 4611, 5032, 5296,
  7147, 7245, 8132, 10335 `require_billing_vigente`.
- El mecanismo, mínimo y sin la app (PG16 local, `fk.py` abajo):
  - `FOR UPDATE`: el segundo `UPDATE` de la org espera (FK →
    `FOR KEY SHARE` de la dueña) → `['ok', 'DeadlockDetectedError']`;
  - `FOR NO KEY UPDATE`: el segundo `UPDATE` no espera, el aviso confirma y
    el alta sigue → `['ok', 'ok']`.

**Leído:** `_vencer_y_guardar` hace su propio `commit`/`rollback`; el
`commit` nuevo de vigente no carga esa escritura (D202).

**No reproducido:** los resultados 1 a 3 dentro de la app; los midió la Dev
sobre árboles sin commitear. Van copiables en H.

**Abierto:**
- ¿Pasa hoy? En HEAD, el guardado y generar MARIA ya toman a la dueña con
  `FOR UPDATE` y después la org. Se mide en H.
- D204 (`past_due` sobre una renovación), en H.

**Decisiones:**
- D200 (a), D201 (a) con un dato de créditos vencidos, D202 (a) con la
  condición del caso 4 y D203 (a) con el espejo como dato: las decidió la
  PM.
- D204: la medición la ordena la PM; el arreglo lo decide Emi.

<details><summary>fk.py (mínimo, PG local)</summary>

```python
import asyncio, asyncpg, sys
DSN = "postgresql://cdi@127.0.0.1:55462/pm_fk_repro"
async def prep():
    c = await asyncpg.connect("postgresql://cdi@127.0.0.1:55462/postgres")
    await c.execute("DROP DATABASE IF EXISTS pm_fk_repro"); await c.execute("CREATE DATABASE pm_fk_repro"); await c.close()
    c = await asyncpg.connect(DSN)
    await c.execute("CREATE TABLE users(username text primary key, n int default 0);"
                    "CREATE TABLE orgs(id int primary key, owner_username text references users(username), cred int default 0);"
                    "INSERT INTO users VALUES ('ana'); INSERT INTO orgs VALUES (1,'ana');")
    await c.close()
async def esperar_bloqueado(mon, pid):
    for _ in range(500):
        r = await mon.fetchval("select wait_event_type from pg_stat_activity where pid=$1", pid)
        if r == 'Lock': return
        await asyncio.sleep(0.01)
    raise RuntimeError("no se bloqueó")
async def corrida(modo):
    await prep()
    alta, hook, mon = [await asyncpg.connect(DSN) for _ in range(3)]
    hpid = await hook.fetchval("select pg_backend_pid()"); apid = await alta.fetchval("select pg_backend_pid()")
    ta = alta.transaction(); await ta.start(); th = hook.transaction(); await th.start()
    await alta.execute(f"SELECT * FROM users WHERE username='ana' {modo}")      # alta: usuario primero
    await hook.execute("UPDATE orgs SET cred=cred+10 WHERE id=1")             # webhook: primer UPDATE
    t2 = asyncio.create_task(hook.execute("UPDATE orgs SET cred=cred+0 WHERE id=1"))  # segundo UPDATE: dispara la FK
    try:
        await asyncio.wait_for(asyncio.shield(t2), 0.5); print(modo, "-> 2do UPDATE no espera")
    except asyncio.TimeoutError:
        print(modo, "-> 2do UPDATE espera (FOR KEY SHARE sobre la dueña)")
    t1 = asyncio.create_task(alta.execute(f"SELECT * FROM orgs WHERE id=1 {modo}"))
    r2 = await asyncio.gather(t2, return_exceptions=True)
    if not isinstance(r2[0], Exception):
        try: await asyncio.wait_for(asyncio.shield(t1), 0.5)
        except asyncio.TimeoutError: await th.commit(); print(modo, "-> el webhook confirma; el alta sigue")
    res = [await asyncio.gather(t1, return_exceptions=True)][0] + r2
    print(modo, "->", [type(r).__name__ if isinstance(r, Exception) else "ok" for r in res])
    for t, c in ((ta, alta), (th, hook)):
        try: await t.rollback()
        except Exception: pass
    for c in (alta, hook, mon): await c.close()
async def main():
    await corrida("FOR UPDATE"); await corrida("FOR NO KEY UPDATE")
asyncio.run(main())
```

</details>

## H (sólo arnés): aceptada como medición sobre `bd8665bf`, con devolución por la causa (2026-11-12 11:45 UTC)

Integrada por avance directo. `chequeo-6.py 6001684c bd8665bf`: producto
+0/−0, arnés +323/−0, 0 avisos, igual al informe.

### Lo corrido por la PM, sobre `bd8665bf`

| Caso | Árbol | rc | Resultado |
|---|---|---|---|
| 6 | HEAD | 1 | `deadlocks: 5; rondas sin armar: 0` (las 5 del informe) |
| 6 | (b) completo | 0 | `deadlocks: 0; rondas sin armar: 0` |
| 6 | sólo NO KEY, 1.ª corrida | **2** | `Invalida: la app no soltó sus conexiones` en la ronda «recarga + maria \| usuario \| créditos al día» (la anterior, «… créditos vencidos», salió ok) |
| 6 | sólo NO KEY, 2.ª corrida | 1 | `deadlocks: 3; rondas sin armar: 0` (igual al informe) |
| 7 | HEAD | 1 | `cuentas mal: 4; rondas sin armar: 0` |

Final de la 1.ª corrida con sólo NO KEY:

```
ok       | recarga + maria | usuario | créditos vencidos | [200, 200] | deadlocks +0
Usuario registrado: cr_398dfcf2be (plan: premium, verificado: True)
Traceback (most recent call last):
  File "/tmp/cdi-parche.QwcF8P/scripts/testing/conexiones1_rondas.py", line 85, in correr
  File "/tmp/cdi-parche.QwcF8P/scripts/testing/conexiones1_pares.py", line 31, in main
    codigos, dl, consultas, _ = ronda(c, a, b, de_org, ajuste + (
  File "/tmp/cdi-parche.QwcF8P/scripts/testing/conexiones1_rondas.py", line 77, in ronda
    raise h.Invalida("la app no soltó sus conexiones")
conexiones1_creditos.Invalida: la app no soltó sus conexiones
rc=2
```

**El rc=2 no tiene causa confirmada.** Lo que corrí para buscarlo **no es
la misma ronda**: 50 veces `ronda(c, "maria", "recarga", …)`, usuario,
créditos al día, sobre HEAD sin parche (el orden inverso y otro árbol): 0
fallas. La ronda que falló (recarga primero, con NO KEY) no la repetí
aislada. Hipótesis, sin probar: algo abre una conexión después de
`engine.dispose` (por ejemplo, la tarea en segundo plano del registro de
pedidos, `log_request_background`, que no espera a nadie) y la espera de
«cero conexiones» lo ve. Es arnés, no producto: va como devolución.

### Mis negativos: la carrera sin forzar, sobre HEAD

El caso 6 toma la fila desde afuera para que los dos pedidos coincidan. Lo
lancé sin eso: los dos pedidos a la vez con una barrera de dos hilos, 30
rondas por par, org con créditos extra vencidos y sin limpiar.

| Par | HEAD | sólo NO KEY |
|---|---|---|
| recarga + guardado | 28/30 deadlock | 0/30 |
| recarga + MARIA | 30/30 | 0/30 |
| guardado + recarga | 25/30 | 0/30 |
| control: recarga + guardado con créditos al día | 0/30 | — |

**Condiciones, para no exagerar:** es con los dos pedidos lanzados en el
mismo instante y sólo en la primera actividad de la org después de que
vencen sus créditos extra: cualquier alta contada o recarga los limpia
(`_expire_extra_ops`, `billing_service.py:109`) y ahí ya no pasa. No sé
cada cuánto coinciden en producción.

**Quién pierde** (recarga + guardado, 30 rondas, 24 deadlocks): el guardado
18 veces, el aviso de MP 6. Las 6 veces que pierde el aviso, la recarga no
quedó acreditada (sin fila en `mp_pagos_aplicados`, créditos `(0, None)`).
Reenviado como lo reintentaría MP, da 200 y acredita (`aplicado`, `(10,
True)`). O sea: la plata no se pierde **si MP reintenta**; eso lo simulé, no
lo verifiqué con MP.

**¿Con el arreglo chico queda acreditada la recarga?** (11:52 UTC) Antes de
recomendarlo, chequeé que no cambie un error que MP reintenta por un pago
perdido: misma carrera, 30 rondas por par, y en **cada** ronda leí
`mp_pagos_aplicados` y los créditos de la org (`pm_natural3.py`, abajo).

| Árbol | Par | Resultado por ronda | Rondas |
|---|---|---|---|
| sólo NO KEY | recarga + guardado | 200 / 200, `aplicado`, `(10, True)`, sin deadlock | 30 |
| sólo NO KEY | recarga + MARIA | 200 / 200, `aplicado`, `(10, True)`, sin deadlock | 30 |
| HEAD | recarga + guardado | 200 / 200, `aplicado` | 3 |
| HEAD | recarga + guardado | recarga 200, guardado 500, `aplicado` | 22 |
| HEAD | recarga + guardado | recarga 500, sin fila, `(0, None)` (espera el reintento) | 5 |
| HEAD | recarga + MARIA | recarga 200, MARIA 500, `aplicado` | 29 |
| HEAD | recarga + MARIA | recarga 500, sin fila, `(0, None)` | 1 |

«Recargas con 200 y no acreditadas»: 0 en los dos árboles. Con el arreglo
chico, las 60 recargas quedaron acreditadas en el momento, sin depender del
reintento de MP. La recomendación de D206 (a) se mantiene.

**D204 sigue:** renovación + guardado con prueba vencida, usuario y org,
`[200, 402]`; las dos cuentas quedan `past_due` con el período por delante y
`tiene_acceso` da `False`: pagó y queda bloqueada hasta la próxima
renovación.

### Decisiones

- **H aceptada como medición, con devolución por la causa:** lo que abre una
  conexión después de `dispose` rompe la espera a cero conexiones. Diagnosticar
  el rc=2 o hacer la espera robusta a esa familia, con un caso que lo muestre.
- **D205 y D206 van a Emi** (punto 13 de NOW). Recomiendo D206 (a), que
  arregla 2 de los 5 pares (los otros 3 esperan D182), y D205 (a). Los dos llevan revisión fuerte: candados de cobro y
  `get_current_user`.

### No corrido por la PM

- `e2e_maria.sh` y la suite: H no toca producto.
- El caso 7 con (b): confío en el informe (4 MAL, igual que HEAD).

<details><summary><code>pm_natural.py</code> (en <code>scripts/testing/</code> de un worktree de <code>bd8665bf</code>; <code>con_pg16.sh $PY</code>)</summary>

```python
"""Negativo de la PM: recarga + guardado (y recarga + maria) de org con créditos
vencidos, lanzados a la vez SIN tomar la fila desde afuera. ¿Pasa sin forzar?"""
import os, sys, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conexiones1_rondas import correr, m, PEDIDOS, DEADLOCKS, OTRAS
import conexiones1_creditos as h
from proyecto_maria.database.connection import engine
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor
N = int(os.environ.get("N", "30"))
def main():
    with TestClient(m.app, raise_server_exceptions=False) as c:
        for a, b in (("recarga", "guardado"), ("recarga", "maria"), ("guardado", "recarga")):
            dl_tot, quinientos = 0, 0
            for i in range(N):
                s, cl, ref, cuenta = h.preparar(c, True)
                antes = h.sql(DEADLOCKS)[0][0]
                bar = threading.Barrier(2)
                def lanzar(p):
                    bar.wait(); return PEDIDOS[p](c, ref, s, cl)
                with ThreadPoolExecutor(2) as ex:
                    fs = [ex.submit(lanzar, a), ex.submit(lanzar, b)]
                    cods = [f.result(h.PLAZO).status_code for f in fs]
                c.portal.call(engine.dispose)
                h.hasta(lambda: h.sql(OTRAS)[0][0] == 0)
                dl = h.sql(DEADLOCKS)[0][0] - antes
                dl_tot += dl; quinientos += 500 in cods
            print(f"natural | {a} + {b} | org vencidos | rondas {N} | deadlocks {dl_tot} | rondas con 500: {quinientos}", flush=True)
    return 0
if __name__ == "__main__":
    sys.exit(correr(main))
```

</details>

<details><summary><code>pm_natural2.py</code> (igual; quién pierde, control, D204 y el bucle del rc=2)</summary>

```python
"""Negativos de la PM sobre HEAD: quién pierde en el deadlock natural, control con
créditos al día, si D204 persiste, y el rc=2 en bucle."""
import os, sys, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conexiones1_rondas import correr, m, PEDIDOS, DEADLOCKS, OTRAS, ronda
import conexiones1_creditos as h
from tests.mp_firma import aviso_firmado
from proyecto_maria.database.connection import engine
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor
N = int(os.environ.get("N", "30"))
def natural(c, vencidos):
    res = {"dl": 0, "pierde_webhook": 0, "pierde_guardado": 0, "no_acreditada": 0, "reintento_acredita": 0}
    for i in range(N):
        s, cl, ref, cuenta = h.preparar(c, True)
        if not vencidos:
            h.sql("update organizations set extra_ops_expires_at = now() + interval '20 days' where id = %s", cuenta[2])
        antes = h.sql(DEADLOCKS)[0][0]
        bar, pidbox = threading.Barrier(2), {}
        def rec():
            bar.wait(); pid, r = h.recargar(c, ref); pidbox["pid"] = pid; return r
        def gua():
            bar.wait(); return PEDIDOS["guardado"](c, ref, s, cl)
        with ThreadPoolExecutor(2) as ex:
            fr, fg = ex.submit(rec), ex.submit(gua)
            rr, rg = fr.result(h.PLAZO), fg.result(h.PLAZO)
        c.portal.call(engine.dispose); h.hasta(lambda: h.sql(OTRAS)[0][0] == 0)
        res["dl"] += h.sql(DEADLOCKS)[0][0] - antes
        pid = pidbox["pid"]
        if rr.status_code != 200:
            res["pierde_webhook"] += 1
            est = h.sql("select estado from mp_pagos_aplicados where payment_id = %s", pid)
            ops = h.sql("select extra_ops_remaining, extra_ops_expires_at > now() from organizations where id = %s", cuenta[2])
            res["no_acreditada"] += est != [("aplicado",)]
            r2 = c.post("/api/payments/webhook", **aviso_firmado("payment", pid, "secreto-de-prueba"))
            est2 = h.sql("select estado from mp_pagos_aplicados where payment_id = %s", pid)
            ops2 = h.sql("select extra_ops_remaining, extra_ops_expires_at > now() from organizations where id = %s", cuenta[2])
            res["reintento_acredita"] += est2 == [("aplicado",)]
            print(f"  webhook {rr.status_code}: estado {est} ops {ops} -> reintento {r2.status_code} estado {est2} ops {ops2}", flush=True)
        if rg.status_code != 200:
            res["pierde_guardado"] += 1
    print(f"natural recarga+guardado org créditos {'vencidos' if vencidos else 'al día'}: rondas {N} {res}", flush=True)
def d204(c):
    for de_org in (False, True):
        ajuste = "billing_status = 'trial', trial_ends_at = now() - interval '1 day'"
        codigos, _, _, (tabla, clave, valor) = ronda(c, "renovación", "guardado", de_org, ajuste)
        st = h.sql(f"select billing_status, trial_ends_at > now() from {tabla} where {clave} = %s", valor)
        s = h.preparar  # sesión: reusar no se puede; leer acceso directo
        print(f"d204 {'org' if de_org else 'usuario'}: {codigos} queda {st}", flush=True)
        ent = h.sql(f"select billing_status, trial_ends_at from {tabla} where {clave} = %s", valor)[0]
        fake = type("E", (), {"billing_status": ent[0], "trial_ends_at": ent[1], "plan": "premium"})()
        try:
            print("   tiene_acceso:", m.billing_service.tiene_acceso(fake), flush=True)
        except Exception as e:
            print("   tiene_acceso error:", repr(e)[:150], flush=True)
def bucle(c):
    fallas = 0
    for i in range(int(os.environ.get("NB", "50"))):
        try:
            ronda(c, "maria", "recarga", False, "billing_status = 'active', extra_ops_expires_at = now() + interval '20 days'")
        except h.Invalida as e:
            fallas += 1; print("  bucle Invalida:", e, flush=True)
    print(f"bucle maria+recarga usuario al día: fallas {fallas}", flush=True)
def main():
    with TestClient(m.app, raise_server_exceptions=False) as c:
        natural(c, True); natural(c, False); d204(c); bucle(c)
    return 0
if __name__ == "__main__":
    sys.exit(correr(main))
```

</details>

<details><summary><code>pm_natural3.py</code> (igual; un worktree de HEAD y otro con <code>parche_nokey.diff</code>)</summary>

```python
"""Negativo de la PM: carrera natural recarga + guardado / recarga + maria de org con
créditos vencidos; en CADA ronda, el estado de la recarga y los créditos al final."""
import os, sys, threading, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conexiones1_rondas import correr, m, PEDIDOS, DEADLOCKS, OTRAS
import conexiones1_creditos as h
from proyecto_maria.database.connection import engine
from fastapi.testclient import TestClient
from concurrent.futures import ThreadPoolExecutor
N = int(os.environ.get("N", "30"))
def main():
    perdidas = 0
    with TestClient(m.app, raise_server_exceptions=False) as c:
        for otro in ("guardado", "maria"):
            tabla = collections.Counter()
            for i in range(N):
                s, cl, ref, cuenta = h.preparar(c, True)
                antes = h.sql(DEADLOCKS)[0][0]
                bar, box = threading.Barrier(2), {}
                def rec():
                    bar.wait(); pid, r = h.recargar(c, ref); box["pid"] = pid; return r
                def otra():
                    bar.wait(); return PEDIDOS[otro](c, ref, s, cl)
                with ThreadPoolExecutor(2) as ex:
                    fr, fo = ex.submit(rec), ex.submit(otra)
                    rr, ro = fr.result(h.PLAZO), fo.result(h.PLAZO)
                c.portal.call(engine.dispose); h.hasta(lambda: h.sql(OTRAS)[0][0] == 0)
                dl = h.sql(DEADLOCKS)[0][0] - antes
                est = h.sql("select estado from mp_pagos_aplicados where payment_id = %s", box["pid"])
                ops = h.sql("select extra_ops_remaining, extra_ops_expires_at > now() from organizations where id = %s", cuenta[2])[0]
                acreditada = est == [("aplicado",)] and ops[1] is True and (ops[0] or 0) >= 9
                if rr.status_code == 200 and not acreditada:
                    perdidas += 1
                tabla[(f"recarga {rr.status_code}", f"{otro} {ro.status_code}", f"dl {dl}", f"estado {est[0][0] if est else '-'}", f"ops {ops}")] += 1
            for k, v in sorted(tabla.items(), key=str):
                print(f"recarga + {otro} | {' | '.join(k)} | x{v}", flush=True)
    print(f"recargas con 200 y no acreditadas: {perdidas}", flush=True)
    return 1 if perdidas else 0
if __name__ == "__main__":
    sys.exit(correr(main))
```

</details>

## I (sólo arnés): aceptada sobre `e9323b67` (2026-11-12 12:35 UTC)

Informe `7a68faec` (sólo `docs/pm/PARA-PM.md` sobre `e9323b67`).
`chequeo-6.py 734b484c e9323b67`: producto +0/−0, arnés +166/−3, historia
vacío, 0 avisos; igual al informe.

**La causa del rc=2 queda probada.** `log_request_background` (tarea de
fondo de `MetricsMiddleware`, `main.py:2008`) devuelve su conexión a un
pool que `engine.dispose` ya descartó; sólo gc la cierra. No es un defecto
para el usuario: el pedido ya respondió.

| corrida (todas sobre `e9323b67`) | rc | salida |
|---|---|---|
| caso 9 | 0 | vuelta 2, `log_request_background`, «la base quedó sin conexiones de la app» |
| caso 9 con `gc.collect()` → `pass` | 1 | vuelta 4, la misma tarea, «la app no soltó sus conexiones» |
| caso 8 natural, HEAD | 1 | «deadlocks: 18, recargas perdidas: 0»; vencidos: recarga + guardado 8/10, recarga + MARIA 10/10; al día 0/10 los dos; el aviso perdió 2 veces y el reintento firmado acreditó 10/10 |
| caso 8 natural, NO KEY | 0 | «deadlocks: 0, recargas perdidas: 0» |
| caso 6 NO KEY ×3 | 1 cada una | «deadlocks: 3; rondas sin armar: 0», siempre los 3 pares de alta; ningún rc=2 en 168 rondas |
| detector de D188, HEAD y NO KEY | 1 los dos | «pierden: 2», idéntico: NO KEY no lo empeora ni lo arregla |
| caso 7, HEAD | 1 | «cuentas mal: 4», renovación + guardado → `past_due` (D205) |
| negativo de la PM `pm_fuga_i.py` | 0 | A (conexión tomada, sin referencia) → «dejó conexiones sin devolver»; B (con referencia viva) → «no soltó sus conexiones»; malos 0 |

- **Prueba:** el caso 9 verde contra rojo con el arreglo revertido, y mis
  dos negativos: `soltar()` no tapa una fuga en ninguna de las dos formas.
- **El caso 6 ×3:** consistente y sin regresión; no es prueba de la causa.
- **«recargas perdidas: 0»** coincide con `pm_natural3.py` (sección H),
  corrido aparte.
- Mis números del natural (18 deadlocks, 10/10) difieren poco de los suyos
  (17, 9/10): variación normal de una carrera.
- **D207:** (b), decidido por la PM; una línea en `COLA-LIMPIEZA.md`.
- **No corrido:** suite y `e2e_maria.sh`: I no toca producto.

<details><summary>Negativo de la PM: <code>pm_fuga_i.py</code></summary>

```python
"""Negativo de la PM (entrega I): soltar() no da verde con una conexión de la app tomada.
A: tomada y sin referencia (gc la cierra) -> debe decir «dejó conexiones sin devolver».
B: tomada y con referencia viva (gc no la toca) -> debe decir «no soltó sus conexiones».
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conexiones1_rondas import OTRAS, correr, engine, h, m, soltar  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

VIVAS = []

def main():
    malos = 0
    with TestClient(m.app, raise_server_exceptions=False) as c:
        h.preparar(c, False)
        soltar(c)
        print("base limpia:", h.sql(OTRAS)[0][0])
        for nombre, guardar in (("A sin referencia", False), ("B con referencia", True)):
            async def tomar():
                conn = await engine.connect()
                await conn.exec_driver_sql("select 1")
                if guardar:
                    VIVAS.append(conn)
            c.portal.call(tomar)
            print(nombre, "OTRAS antes:", h.sql(OTRAS)[0][0])
            try:
                soltar(c)
                print(nombre, "-> VERDE (mal)")
                malos += 1
            except h.Invalida as e:
                print(nombre, "-> Invalida:", str(e)[:120])
            if VIVAS:
                async def cerrar():
                    for v in VIVAS:
                        await v.close()
                    VIVAS.clear()
                c.portal.call(cerrar)
                soltar(c)
    print("malos:", malos)
    return 1 if malos else 0

if __name__ == "__main__":
    sys.exit(correr(main))
```

</details>
