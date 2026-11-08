# Reproducción NOMBRES-1, 2026-11-08 (PM principal)

Producto `5af134f`..`ccded98` (rama `claude/dev-tecnica`), base `4087b46`. Worktree limpio, GEMINI_API_KEY vacía.

| qué | resultado |
|---|---|
| `pytest tests/test_nombres1.py tests/test_permisos2.py` en SQLite | 38 passed |
| con el `main.py` de `4087b46` | 8 failed, 5 passed |
| `nombres1.sh ccded98` | BASE en verde (38 passed), 5 ROJO, «sabotajes con falla: 0», rc=0 |
| las mismas dos suites en PG 16 (`con_pg16.sh`) | 38 passed |
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
