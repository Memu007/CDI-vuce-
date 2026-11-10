# Reproducción NOMBRES-1, 2026-11-08 (PM principal)

Producto `5af134f`..`ccded98` (rama `claude/dev-tecnica`), base `4087b46`. Worktree limpio, GEMINI_API_KEY vacía.

| qué | resultado |
|---|---|
| `pytest tests/test_nombres1.py tests/test_permisos2.py` en SQLite | 38 passed |
| con el `main.py` de `4087b46` | 8 failed, 5 passed |
| `nombres1.sh ccded98` | BASE en verde (38 passed), 5 ROJO, «sabotajes con falla: 0», rc=0 |
| las mismas dos suites «en PG 16» (`con_pg16.sh`) | 38 passed, **pero en SQLite**: `tests/conftest.py:19` pisa `DATABASE_URL`. Escape mío, lo vio la Dev técnica; corrida real en PG abajo |
| `chequeo-6.py 4087b46 ccded98` | producto +4/−2, arnés +190/−0, historia vacío, avisos 0 |

Adversario Opus alto, con contexto nuevo:

- **Creación y renombre de cuentas:** sólo `/auth/register` y
  `/api/organizations/create` crean un `User`, y las dos pasan por el chequeo.
  No hay ruta que cambie el nombre.
- **Regex y normalización:** el regex frena unicode, espacios y saltos de
  línea, y el nombre no pasa por ninguna normalización.
- **Búsquedas exactas:** el login, `get_current_user` y la promoción siguen
  comparando exacto.
- **Media-baja, la carrera:** se reproduce con uvicorn sobre PG 16 y 4 altas a
  la vez, que alternan las dos rutas: entran las 4 variantes. Contra una
  cuenta que ya existe, el chequeo frena siempre. Queda como límite conocido:
  un índice va con Emi.
- **Baja, hueco de la prueba:** si la promoción del arranque pasa a
  `lower()` + `.first()`, el caso sigue verde (13 passed), porque la cuenta de
  la lista es la sembrada primero. Va de devolución.

No corrí la suite completa: el informe trae 4731 passed sobre `ccded98`, y la
devolución es sólo de pruebas.

## Vuelta 2: pruebas sobre `1960a9a` (producto `ccded98` sin cambio)

`chequeo-6.py 4087b46 1960a9a`: producto +4/−2, avisos 0. En PG real con
`--noconftest -p pg_nullpool` (el plugin imprime el dialecto antes de correr).

| qué | resultado |
|---|---|
| `nombres1.sh 1960a9a` | BASE 40 passed, 7 ROJO, «sabotajes con falla: 0», salida 0 |
| `test_nombres1.py` en PG 16 real | «dialecto: postgresql», 15 passed |
| PG real, su sabotaje `func.lower` + `.first()` en el arranque | 2 failed (`[mayusculas]`, `[sola_y_la_lista_en_mayusculas]`), 13 passed |
| PG real, sabotaje mío distinto: `User.username.ilike(identifier)` + `.first()` | 2 failed, las mismas filas, 13 passed |
| SQLite, mi sabotaje `ilike` | 2 failed, las mismas filas, 13 passed |

El caso ahora da rojo encuentre la base la fila que encuentre: cada cuenta es
la de la lista, como datos. `main.py` quedó restaurado. No corrí la suite
completa: la vuelta es sólo de pruebas y su informe trae 4733 passed.
