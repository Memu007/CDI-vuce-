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
- Seguridad, para que la PM la evalúe como pieza: `GET /auth/verify-email`
  deja la sesión de la cuenta dueña del link; con su propio link, un atacante
  podría hacer entrar a la víctima en la cuenta del atacante. No reproducido.
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
- `test_maria1b_devolucion` y `test_excel2.py:512` usan una ruta fija en
  `/tmp`: pasarlas a `tmp_path`.
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
- `con_pg16.sh` guarda su puerto en `PUERTO`, que pisa el exportado por
  `cobro_corte1.sh`, `cobro_mp1.sh`, `cobro_mp2.sh` y `backup1a.sh`:
  renombrar a `PG_PUERTO`.
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
- La guarda «No podés removerte a vos mismo» al sacar un miembro no tiene caso
  que la frene si se borra.
- Roles: normalizarlos al leerlos de la base (`/auth/me` los devuelve crudos;
  el arranque parte un texto en letras).
- `ci.yml`: el comentario de «Suite completa» cuenta historia; y `CLAUDE.md` §5
  (la CI deselecciona) cambia cuando LIMPIEZA-1 llegue a `main`.
- `main.py`: `_TEXTOS_DEL_CLIENTE` repite los campos que leen el alta y la
  edición del cliente; `DataStore.add_operation` (`core/datastore.py`) parece
  código muerto.
- `docker-compose.yml:61`: el mensaje `:?` de `JWT_SECRET_KEY` lleva «:» y compose lo corta.
- Arnés de sabotajes y helpers de `scripts/testing/*_postgres.py` (crear y borrar base, registrar usuario, `chequear`) copiados entre piezas: unificar.
- `tests/test_separadores1b.py`: `test_en_la_factura_con_la_pista_en_contra_queda_sin_leer` ya no distingue la regla `sin_grupo` (`_numero_factura` ya devuelve None): darle una entrada que sólo la regla rechace, o sacarlo.
- `proyecto_maria/main.py` 1754, 1771, 2373 y 3406: comentarios con historia («EMAIL-1»), sacarlos.
