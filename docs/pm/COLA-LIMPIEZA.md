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
