# Cola de limpieza

Deuda para después del lanzamiento: no abre tarea ni ocupa `NOW.md`. Se
trabaja en las semanas sin funciones nuevas que siguen a la entrega, con la
suite como red. Lo ya escrito que no cumple `CLAUDE.md` §6 viene acá, no a
un arreglo. Una línea por deuda: dónde está y qué falta.

- `proyecto_maria/`: comentarios y docstrings que nombran piezas, casos o
  fechas («(MARIA-7)», «DESPACHO-1b: …», «antes daba …»); los lista
  `chequeo-6.py origin/main <SHA>`, en «historia». Pasan al mensaje del
  commit o se borran.
- `proyecto_maria/main.py` `_migrate_product_history_clave` (87 líneas):
  partir en leer, unir y escribir claves.
- `proyecto_maria/core/despacho_lector.py:65`, `:678`, `:747` y
  `main.py:1401`: comentarios de 3 a 5 líneas, a una o dos con el porqué.
- La migración del historial deja el NCM y la descripción como estaban
  escritos (`'3926 90 90'`) en la fila que queda: dejarlos canónicos.
- `scripts/testing/pantalla_orden1.js:280`: la función anónima del arnés
  (1520 líneas) se parte por grupo de casos; los sabotajes de `orden1.sh` y
  `orden1b.sh` se reanclan en la misma pieza.
- `proyecto_maria/static/v2/app_v2.js:7`: el IIFE de la pantalla (~1190
  líneas) se parte por sección; lo nuevo ya va en funciones aparte.
- `proyecto_maria/main.py:8048`: `logger.warning("[fill-if-empty] …")` usa
  un `logger` que no existe a nivel de módulo (pyflakes: «undefined name»);
  si esa rama corre da `NameError` en vez del aviso. Lo vio la Dev MARIA.
- `proyecto_maria/static/csrf.js` y el envoltorio de `fetch` de
  `static/v2/app_v2.js` hacen lo mismo: dejar uno (D58 a de CSRF-2).
- `proyecto_maria/main.py:10221`: el «Simular Pago» del checkout demo hace
  POST sin token y da 403 con enforce prendido en desarrollo; en producción
  esa página no existe.
- Control CSRF: con `--root-path` el conjunto de exentas no coincide nunca
  (falla cerrada). Hoy no se usa.
- Orden de locks del conteo (sospechado, sin reproducir): la ruta manual con
  extras vencidas escribe la organización antes de bloquear el usuario
  (`_expire_extra_ops`), y aceptar invitación toma la organización y después
  el usuario; `_cuenta_bloqueada` va usuario → organización.
- `GET /dashboard` valida la sesión contra la base: si la base no responde,
  da 500 en vez de servir la página (riesgo declarado en CSRF-3).
- Carrera al abrir la v2 con dos respuestas que emiten `csrf_token`: queda el
  último `Set-Cookie`. No reproducida como fuga.
- `static/v2/screens/finalize.js` es un solo IIFE de ~1400 líneas: partirlo
  por pantalla (aviso de chequeo-6 en DESPACHO-1c).
- Avisos de guardado de la v2: duran 4 s sin marca fija; «Volvé a Listo y
  reintentá» confunde porque entrar a Listo regenera; `ERROR_AJENA` y
  `ERROR_SIN_SESION` se muestran como «Error de red».
- `CLAUDE.md` §5 dice que la CI deselecciona tests de presupuestos, pero
  `ci.yml:45` corre `python -m pytest --no-cov` sin `--deselect`. Lo corrige
  quien pueda tocar `CLAUDE.md` (decide Emi).
- `_migrate_add_user_cuit_column` (`main.py:470`) no tiene `lock_timeout`: el
  arranque espera detrás de un `sugerir` que tiene abierta la transacción
  mientras habla con Gemini (medido: 28,5 s).
- `api_logs.endpoint` es `String(200)`: un PUT o DELETE con clave larga pierde
  su métrica («value too long»).
- `proyecto_maria/pdf_extractor.py:927` y `:936`: `'\-'` sin `r''` da
  `SyntaxWarning` en `compileall` (Python 3.12).
- Dos `get_db` iguales, en `proyecto_maria/main.py:165` y
  `proyecto_maria/auth/dependencies.py:21`: dejar uno (D75 de MARIA).
- `_escribir_y_confirmar` (`main.py`): un commit que llega a la base y tira
  error en Python cobra sin entregar, y el reintento cobra otra vez (raro).
- `delete_cliente` bloquea usuario y después organización; sacar a un miembro
  del estudio, al revés: deadlock posible (500, sin pérdida de datos).
- `proyecto_maria/static/app.js:1945`: `value="${item.origen}"` sin escapar.
  Hoy no llega texto del catálogo ahí, pero escaparlo igual que la
  descripción (D81 de MARIA).
- `finalize.js`: Enter doble en «Reintentar» (`:1361-1366`) o en «Generar»
  manda dos generaciones; no cobra otra vez (reusa `operacion_id`).
- `CDI.api` sin timeout (`finalize.js:654`): una generación colgada deja la
  carga siguiente en el spinner.
- `_escribir_y_confirmar` (`main.py:5933-5941`): si falla el commit y también
  restaurar `.anterior`, se pierde el archivo ya entregado (falla doble).
- `_migrate_catalogo_claves`: con choque, la fila que se mueve sale sin
  `ORDER BY` y la otra queda con su clave latina; el log «quedan por un
  choque» se repite en cada arranque.
- `_migrate_product_history_clave` (`main.py:1464`): el índice único se crea
  sin `lock_timeout`; un `guardar-uso` abierto traba el arranque.
- `save_products` y `update_product` buscan y después insertan: lotes o `PUT`
  iguales a la vez dan 500 y pierden el lote.
- `/api/catalog/lookup`: 500 con medio par o campos que no son texto, y no
  limpia el NUL como el guardado.
- `_precio` acepta `True`, negativos y `"1_0"`.
- Mensajes del NCM: con más de 2000 dice «pasa de 2000» aunque el tope es 20;
  `guardar-uso` dice «La NCM» y el lote «El NCM».
- Comentarios que dicen «más que lineal» para la extracción de texto
  (`despacho_lector.py:43`, `test_rendimiento1b.py:151`,
  `test_rendimiento1d.py:6`): con pypdf 6.21.4 es lineal.
- `_leer_hojas` toma el tope propio de pypdf como «No pude abrir el PDF» y
  `validar_pdf` como «demasiado pesado»: unificar el trato.
- `test_email1.py:158` y `:216` parchean `IS_PRODUCTION`, que ya no decide el
  correo; `test_prelaunch_block3.py:205-235` (TestProduccionDemoUsers) no
  ejecuta código del producto.
- Registro: ramas que ya no pueden pasar después de `_email_valido` y un
  comentario con historia (D103).
- `register` y `create_organization`: `re.match(r'^[a-zA-Z0-9_-]{3,30}$')`
  acepta un `\n` final en el usuario; `fullmatch` lo cierra.
- Tests viejos (email1, prelaunch_block2/3, cobro_mp1/2 y los scripts
  `cobro_mp1*_postgres.py`) parchean `main_mod.IS_PRODUCTION`, que ya no
  controla lo que dicen probar: parchear `ENVIRONMENT` (ENTORNO-2).
- `RateLimitByEndpointMiddleware` (`security_middleware.py`) no está montado
  en la app: hoy no limita nada; borrarlo o montarlo es decisión aparte (D111).
- `main.py` todavía define `IS_PRODUCTION`; cuando ningún test lo parchee,
  sacarlo.
- Roles: normalizarlos al leerlos de la base (`/auth/me` los devuelve crudos;
  el arranque parte un texto en letras).
- `ci.yml`: el comentario de «Suite completa» cuenta historia; y `CLAUDE.md` §5
  (la CI deselecciona) cambia cuando LIMPIEZA-1 llegue a `main`.
- `main.py`: `_TEXTOS_DEL_CLIENTE` repite los campos que leen el alta y la
  edición del cliente; `DataStore.add_operation` (`core/datastore.py`) parece
  código muerto.
- `docker-compose.yml:61`: el mensaje `:?` de `JWT_SECRET_KEY` lleva «:» y compose lo corta.
- Arnés de sabotajes y helpers de `scripts/testing/*_postgres.py` (crear y borrar base, registrar usuario, `chequear`) copiados entre piezas: unificar.
- `proyecto_maria/main.py` 1754, 1771, 2373 y 3406: comentarios con historia («EMAIL-1»), sacarlos.
- `tests/conftest.py:19`: pisa `DATABASE_URL` con SQLite sin avisar, así que
  un `pytest` con la URL de Postgres corre en SQLite. Hoy se esquiva con
  `--noconftest -p pg_nullpool`; que avise o que respete una URL de PG pedida.
- `core/maria_generator_export.py:114`: el generador de exportación no pasa
  la destinación por `destinacion_del_txt` (sólo lo hace el endpoint), y el
  de importación chequea en el endpoint y en el generador. El chequeo, una
  vez, en los dos generadores.
- `tests/test_excel2d.py:199`: el tope de 0,5 s entre pasos del hilo testigo
  falló en la CI de `d9a6962` (sólo docs) con 0,506 s, y pasó en `2d08e94`
  con el mismo producto. Medir el freno sin depender de la carga del runner.
- `proyecto_maria/main.py` `_guardable_en_pg(endpoint)` en el registro de pedidos
  (D150): el molde no trae NUL ni caracteres sueltos; sacar la llamada, con su rojo.
- `proyecto_maria/main.py` `register` (219 líneas): partirla en validar la
  invitación, crear la cuenta y usar las otras pendientes, sin partir la transacción.
- `proyecto_maria/main.py:166` `pwd_context` de passlib: el producto no lo usa
  (el hash va directo con `bcrypt`), pero `tests/test_password_recovery_manual.py:5`
  lo importa. Sacarlo con ese import, y `passlib[bcrypt]` de `requirements.txt` (D153).
- `tests/test_catalogo3.py`: ningún caso de la memoria del cliente con
  `ultima_vez` nula («sin fecha pierde» sólo lo prueba el acta de la PM):
  un caso con la fila sin fecha en los dos órdenes, con su rojo.
- `proyecto_maria/main.py` login: el límite cuenta después de `verify_password`;
  cada clave mala paga bcrypt antes del freno (D146 b, D181 b). CONEXIONES-1 B:
  60 claves malas desde 60 IPs no las corta nada; el caso que falta probar es
  muchas a la vez desde la misma IP (`abuso1` sólo lo prueba en serie).
- `proyecto_maria/main.py` `delete_cliente`: la operación queda sin cliente con su
  `generated_file`, y el TXT se sigue bajando (fila 4 del code-review de INTEGRAR-1).
- `proyecto_maria/main.py` tope de registro: el `or` corta antes y el intento
  frenado por hora no suma al diario (fila 7 del code-review de INTEGRAR-1).
- `finalize.js`: el `{code, message}` del 409 de regeneraciones quedó sin uso
  desde COBRO-CORTE-1; sacarlo.
- `app_v2.js` recuperar el borrador: `b && adoptarTarde(b)` dos veces y un
  ternario en el arranque; unificar en un `recuperar(b)` (D172).
- `app_v2.js` aviso «pendiente»: no se borra, puede pisar el de «lleno» y, si la
  pestaña de antes murió sin `pagehide`, otra pestaña no lo encuentra por 3 min
  (D170 b; acta de BORRADOR-1, hallazgo 4).
- `tests/test_excel2d.py::test_la_subida_cara_no_frena_a_nadie`: compara tiempo
  contra 0,5 s y dio 0,66 s en la CI sin cambio de producto; medir algo que no
  dependa del runner.
- Tres lectores de la posición SIM que no aceptan lo mismo: `_NCM` en
  `client_memory.py`, `_POSICION` en `despacho_lector.py` y `_partes` en
  `sufijos_arca.py`. Uno solo, con su tabla de formas (D165 a, MEMORIA-E2E).
- `proyecto_maria/main.py` `save_client_operation` pasa las 150 líneas (153
  con la llamada de PRESUPUESTO-CLIENTE-1): partirla.
- `scripts/testing/pantalla_destino1.js`: manda la `X-Forwarded-For` pero no
  mira el status del registro; si falla, sigue sin decir por qué (supuesto de
  la Técnica en BORRADOR-1). Son 15 guiones con el mismo hueco; asignado a la Técnica.
- `scripts/testing/pantalla_cliente1.js:27`: la función anónima tiene 297
  líneas; partirla (AVISO de `chequeo-6` aceptado en BORRADOR-1).
- `proyecto_maria/static/v2/screens/profile.js` `open()`: mueve el foco a «Mi CUIT»
  150 ms después de cargar, aunque la persona ya esté escribiendo en otro
  campo; con carga lenta, lo escrito cae ahí (reproducido con
  `scripts/testing/foco_perfil.sh`, acta de BORRADOR-1, FOCO-PERFIL). El
  arreglo lleva en el mismo commit el cambio de `abrirMisEstudios` de
  `pantalla_estudio1.js` y de `abrirPerfil` de `pantalla_sesion1.js` (hoy
  esperan ese foco) y actualiza o saca
  `foco_perfil.sh`, que reemplaza ese `setTimeout` exacto.
- `proyecto_maria/main.py:2008` (`MetricsMiddleware`): `asyncio.create_task`
  sin guardar la referencia; Python podría recolectar la tarea y perder el
  registro en `api_logs`. No vista en ninguna corrida con gc forzado (D207).
- Sabotajes cuya ancla incluye un comentario (familia de las dos Devs,
  D168 de MARIA): `grep -nE "^ +[\$'\"].*( #|//) +[[:alnum:]ÁÉÍÓÚáéíóú]"
  scripts/testing/sabotajes/*.sh scripts/testing/sabotaje_*.sh` (aproximado:
  no ve patrones partidos en varias líneas). Cada Dev reancla en código lo
  suyo cuando vuelve a tocar el guion, y corre ese guion entero.
- `proyecto_maria/main.py` guardar-uso: el largo del texto se mide dos veces
  (`texto_para_guardar` y `_problema_historial`); dejar un solo chequeo.
- pytest muestra `PytestUnhandledThreadExceptionWarning` («Event loop is
  closed», de aiosqlite) en `test_despacho1b.py`: no rompe hoy, pero ensucia
  la salida que leen los guiones.
- `scripts/testing/sabotaje_maria3.sh`: contar los casos en `caso` en vez de a
  mano; el ancla de transacción copia toda la lista de tablas; tres pares
  ancla/reemplazo repetidos entre SQLite y Postgres (propuestas de MARIA, D216–D220).
- Guiones de `scripts/testing/sabotajes/` que tiran la salida del chequeo de
  base (`>/dev/null 2>&1`): una base roja dice sólo `BASE  | …` (113 líneas en
  58 guiones). `catalogo_largo2.sh` ya muestra la cola con `base_en_verde`:
  pasarla a `_entorno_comun.sh` (MARIA, D218).
- `catalogo3_postgres.py`: `entorno()` devuelve el entorno entero; en los
  arneses vecinos devuelve sólo lo que pisa. Unificar el contrato (MARIA, D218).

- `scripts/testing/pantalla_subitems1.js:23`: la función principal (181
  líneas) se parte (MARIA, PANTALLAS-MARIA).
- `scripts/testing/pantalla_maria4.js`: chequear las altas del armado y usar
  CUIT válidos, el mismo en el cliente y en la operación (MARIA).
- `static/v2/app_v2.js:921-932`: con un borrador guardado, si ella toca
  «Nueva operación» y sube antes de que llegue el usuario, el arranque adopta
  el borrador y hace `goTo` igual; una subida en vuelo se descarta. Leído, no
  corrido (Técnica, D211).

## Riesgos que esperan a Emi (no son tareas: no se toman de esta cola)

- `client_memory._norm_desc` pierde las ligaduras («Arandela ﬁna» queda
  `arandela na`). Arreglarlo cambia `descripcion_normalizada` ya guardada:
  es producto con migración de datos, y nadie lo midió en facturas reales (D220).
