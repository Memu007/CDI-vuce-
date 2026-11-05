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
