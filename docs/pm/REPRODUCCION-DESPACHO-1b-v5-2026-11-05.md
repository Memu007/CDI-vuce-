# DESPACHO-1b vuelta 5: reproducción de la PM (2026-11-05)

Producto `b5fb03a`, base `03296d4`. Revisión con subagente adversarial (Opus,
alto) en Postgres 16.15 descartable y worktrees limpios; la PM confirmó el
`for/else` leyendo `services/client_memory.py:230-236`.

## Lo que se sostiene

- `despacho1b_postgres.py` (script de `b5fb03a`): producto de `03296d4`
  **«fallas: 8»** (las mismas 8 del informe); `b5fb03a` **«fallas: 0»**.
- Sabotaje a mano sin `.with_for_update()`: `fallas: 10`, entre ellas «una
  fila con 16 usos: ['200'] [(8,)]».
- `despacho1b.sh b5fb03a` con `PG_DSN`: 136 ROJO distintos, «sabotajes sin
  rojo: 0», «sin Postgres, no corridos: 0», sin VERDE, ANCHO ni ROTO.
  **No corrió en una sola pasada** (tope de 2 h de la tarea de fondo): el
  original hizo del 1 al 72 y una copia que saltea los primeros 70 hizo del
  71 al 136 (`SALIDA 0`); coinciden en el 71 y el 72.
- Suite con el comando de `ci.yml`, worktree limpio: `4512 passed, 102
  skipped, 10 deselected, 2 xfailed, 93 warnings in 693.97s`, sale con 0
  (4278 del informe + 234 de `xlwt`, instalado en este venv).
- `chequeo-6.py 4931eb2 b5fb03a`: `producto +19/−11`, `arnés +145/−4`,
  historia vacía, `avisos: 0`, igual al informe. Contra `03296d4` da 1 AVISO
  de líneas netas que viene de RENDIMIENTO-1c, no de esta pieza.
- Sin doble suma (un solo camino suma, después del bucle) y sin fila de otro
  cliente u otra cuenta (owner y client salen de la sesión y de
  `_get_owned_client`; el reintento no los cambia).
- Cliente entero borrado mientras la vía espera: DELETE 200; aprender 200
  con `aprendidos:0`, guardar 500, guardar-uso 200 con
  `historial_guardado:false`; la clave foránea rechaza el reintento, sin
  huérfanas, conexión sana.

## Lo que falta: el agotamiento de los 3 intentos no tiene prueba

Negativo de la PM: en Postgres, un trigger `BEFORE INSERT` crea la fila con
la misma clave y un `AFTER INSERT FOR EACH STATEMENT` la borra, así la fila
está en el `INSERT … DO NOTHING` y falta en el `SELECT … FOR UPDATE` en cada
intento; los intentos se cuentan con una secuencia (no se deshace con el
rollback). Sobre `b5fb03a`:

```
operacion    intentos=3 status=200 {"success":true,…,"historial_guardado":false}
aprender     intentos=3 status=200 {"success":true,…,"aprendidos":1}
guardar      intentos=3 status=500 {"detail":"No pudimos procesar tu solicitud…","code":"internal_error"}
guardar-uso  intentos=3 status=200 {"success":true,"historial_guardado":false}
despues, sin trigger: 200 {"success":true,"historial_guardado":true}
```

Sobre `03296d4` da `intentos=1`: el negativo distingue las dos versiones.

- La frase del informe «si las 3 fallan, sale un error (500), nunca un 200
  mudo» es cierta sólo para guardar. Las otras tres avisan con un dato
  (`historial_guardado`, `aprendidos`), que es lo mismo que hacían ante
  cualquier rechazo de la base. No es pérdida nueva y hace falta una carrera
  triple.
- **Ninguna prueba fija el 3 ni el error al agotar:** con `range(3)` →
  `range(2)`, `despacho1b_postgres.py` sigue en `fallas: 0`. Por código (no
  corrido): `else: raise RuntimeError` → `return None` haría que guardar
  conteste 200 sin guardar y ninguna prueba lo vería.

## D51 y D52

- D51 confirmado: `historial_guardado` aparece sólo en `main.py`; ningún
  `.js` ni `.html` lo lee.
- D52 confirmado, en los dos sentidos (SQLite descartable, Gemini anulado):
  guardar-uso con «日本語の製品» y `3926.90.90` da 200, y después «TORNILLO DE
  ACERO», «VALVULA ESFERICA DE BRONCE» y «xyz» reciben
  `('3926.90.90','historial','日本語の製品')`. Al revés, una consulta que
  normaliza a vacío («日本語の», «---...», «Ωμέγα») recibe las primeras 5
  entradas del historial como «historial». Sólo el paso 3 de `sugerir_ncm`.

## No corrido

`despacho1b.sh` de punta a punta en una sola pasada; operación con el cliente
borrado en el medio; dos procesos con PUT repetido; la carrera en SQLite
(sólo razonada); e2e.
