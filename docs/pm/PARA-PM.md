# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## NOMBRES-1 vuelta 2, entregada en `1960a9a` (informe en el commit de arriba)

Base: `ccded98`, que ya entregué. Tu devolución está en `180fde1` y la traje con el merge `0a0ab41`.

| Commit | Qué |
|---|---|
| `5cda09d` | test: el caso de las cuentas viejas corre una vez con cada cuenta en `ADMIN_USERNAMES`. El sabotaje del arranque queda sin `order_by` |
| `a150d5e` | test: arreglos de `/code-review`. La cuenta de la lista sale de las sembradas, la comparación de roles es por cantidad, y el sabotaje exige que el rojo venga de la línea de la promoción |
| `1960a9a` | test: fila con una sola cuenta sembrada y la lista en otras mayúsculas, más dos sabotajes de búsqueda de respaldo (arranque y login) |

**producto +0/−0** contra `ccded98`; arnés +44/−14. Contra `4087b46`, la pieza entera sigue en producto +4/−2. Producto sin cambio, como pediste.

### Resultado

1. **El caso da rojo con `lower()` + `.first()` sin `order_by`, encuentre la base la fila que encuentre.**
   - Cada una de las dos cuentas es, en una fila distinta, la de `ADMIN_USERNAMES`. Están cargadas como datos del caso.
   - La fila que la base devuelva primero sale sin admin en alguna de las dos corridas.
   - Lo probé en SQLite (`nombres1.sh`) y en **Postgres 16 real**. En PG falló en `[mayusculas]` y en `[sola_y_la_lista_en_mayusculas]`, con `assert 1 == 0`.
2. **Fila nueva, `sola_y_la_lista_en_mayusculas`.** La encontró el adversario: con las dos cuentas siempre sembradas, un arranque o un login que prueban primero exacto y, si no hay resultado, buscan con `lower()` quedaban verdes. La fila siembra sólo la cuenta en minúsculas y pone la lista en mayúsculas. Nadie tiene que quedar admin, y el nombre en mayúsculas no entra. Los sabotajes 6 y 7 la rompen.
3. **La carrera se reproduce.** Tu corrida lo mostró: con uvicorn sobre PG 16 y 4 altas a la vez, alternando las dos rutas, entraron las 4 (`rc69a854`, `RC69A854`, `Rc69a854`, `rc69A854`).
   - Hace falta que las altas lleguen al mismo tiempo. Contra una cuenta que ya existe, el chequeo frena siempre.
   - Las cuentas duplicadas son de quien las pidió.
   - La reserva de `ADMIN_USERNAMES` se chequea en memoria y no tiene esta carrera.
   - Ya pasaba antes: dos altas con el mismo nombre exacto dan 500.
   - Queda como límite conocido, sin índice. No la cierro: la decidís vos.
4. **Corrijo mi informe anterior: el «Postgres 16» de pytest era SQLite.** `tests/conftest.py:19` pisa `DATABASE_URL` con un SQLite temporal antes de importar la app. Por eso, las filas «Postgres 16 descartable» de `ccded98` («8 failed, 30 passed» y «38 passed») corrieron en SQLite.
   - Tu fila «las mismas dos suites en PG 16 (`con_pg16.sh`): 38 passed», de `REPRODUCCION-NOMBRES-1`, también corrió en SQLite, si fue con el comando de pytest de mi informe.
   - Esta vuelta probé en PG real con `--noconftest` y un plugin que imprime `dialecto: postgresql`. El comando está abajo.
   - Lo que no pasa por conftest no está afectado: tu carrera con uvicorn, y `test_backup1a.py`, que lee `BACKUP1A_PG_URL` por su cuenta.
   - No revisé si hay otras puertas en PG que pasen por conftest.

Nada para decidir. No abro ninguna D. La carrera es tuya y la dejo como la escribiste.

### Riesgos (quedan, sin arreglo)

| Riesgo | Severidad | Por qué queda |
|---|---|---|
| Dos altas simultáneas que difieren en mayúsculas entran las dos | media-baja (tuya) | Se reproduce (punto 3). Sin índice, por decisión tuya; el índice sobre `lower(username)` es para después, con Emi |
| Un pytest con `DATABASE_URL` de Postgres que carga `tests/conftest.py` corre en SQLite sin avisar | arnés | `conftest.py` queda fuera de alcance. Para PG real hace falta `--noconftest` y el plugin de abajo |
| `test_permisos2.py` no lo corrí en PG real | arnés | Puede depender de fixtures de conftest. En PG real corrí sólo `test_nombres1.py` |
| Los sabotajes 6 y 7 no los corrí en PG | arnés | Rompen la fila de una sola cuenta, donde hay una sola fila que encontrar: no depende del orden de la base |
| El caso repite el login por cada fila | arnés | Menos de 1 s por fila |
| `include_router` se suma de nuevo en cada `lifespan` de los `TestClient` | arnés | Ya pasaba; no cambia resultados |
| La búsqueda con `lower()` recorre toda la tabla `users` en cada alta | baja | Sigue igual que en `ccded98`. Va con el mismo índice |
| Postgres con una colación rara podría bajar las mayúsculas distinto que Python | especulativa | Sigue igual que en `ccded98`. En el peor caso bloquea un nombre de más; nunca deja pasar uno igual |
| Las demos del arranque no pasan por el chequeo | baja | Existen sólo fuera de producción, y ya era así |

Sale el riesgo del informe anterior «el sabotaje del arranque depende de que SQLite ordene la mayúscula primero»: ya no hay `order_by`, y el rojo sale también en PG.

### Hallazgos de la autorrevisión

| Revisor (modelo, esfuerzo) | Hallazgo | Qué hice |
|---|---|---|
| `/code-review high` sobre `5cda09d` | La cuenta de la lista se armaba aparte de las sembradas, y podía no coincidir con ninguna | Arreglado en `a150d5e`: sale de `str.lower` y `str.upper` sobre el mismo nombre |
| `/code-review high` | `"admin" in roles` no distinguía un admin de dos | Arreglado en `a150d5e`: `roles.count("admin") == …` |
| `/code-review high` | El sabotaje del arranque aceptaba cualquier rojo del caso | Arreglado en `a150d5e`: exige la línea de la promoción |
| adversario-sonnet-alto (Sonnet, alto) | Medio: un arranque que prueba exacto y, si no hay, busca con `lower()` quedaba verde | Lo reproduje. Arreglado en `1960a9a`: fila `sola_y_la_lista_en_mayusculas` y sabotaje 6 |
| adversario-sonnet-alto | Medio: lo mismo en el login | Lo reproduje. Arreglado en `1960a9a`: la misma fila y sabotaje 7 |
| adversario-sonnet-alto | Observación: la carrera sigue | Es tuya (punto 3) |

### Pruebas

| Puerta | Sobre | Resultado |
|---|---|---|
| `nombres1.sh` (SQLite) | `1960a9a` | «BASE … en verde» con «40 passed, 5 warnings in 12.99s», 7 `ROJO`, «sabotajes con falla: 0», salida 0 |
| `test_nombres1.py`, SQLite | `1960a9a` | «15 passed in 10.08s» |
| `test_nombres1.py`, Postgres 16 real (`--noconftest`) | `1960a9a` | «dialecto: postgresql», «15 passed in 16.68s» |
| lo mismo, con el arranque en `func.lower(...)` + `.first()` y sin `order_by` | `1960a9a` | `FAILED …siguen_entrando[mayusculas]` y `FAILED …siguen_entrando[sola_y_la_lista_en_mayusculas]`, «2 failed, 13 passed, 3 warnings in 15.93s»; sin el filtro, el error es «assert 1 == 0» |
| suite completa, worktree limpio | `1960a9a` | «4733 passed, 110 skipped, 3 xfailed in 742.41s (0:12:22)», salida 0 |
| `compileall -q proyecto_maria` | `1960a9a` | salida 0 |

En PG, las líneas «Exception closing connection» que salen al cerrar son ruido del `NullPool` del plugin: el resultado no cambia.

No volví a correr `smoke_friccion.sh`, `ataque_aislamiento.sh` ni `permisos2.sh`. Esta vuelta no toca producto ni `test_permisos2.py`. Sus salidas sobre `ccded98` y `fa722eb` están en el informe anterior (`bcdaa68`).

Sabotajes de `nombres1.sh`, tal como los dio la corrida:

| Sabotaje | El rojo dice |
|---|---|
| el chequeo vuelve a comparar exacto | `FAILED …test_un_nombre_que_existe_con_otras_mayusculas_no_se_registra[mayusculas-/auth/register]` |
| el chequeo no baja la cuenta guardada | `FAILED …[existe_en_mayusculas-/api/organizations/create]` |
| el chequeo no baja el pedido | `FAILED …[capitalizada-/auth/register]` |
| el login busca sin distinguir mayúsculas | `FAILED tests/test_nombres1.py::test_dos_cuentas_viejas_que_difieren_en_mayusculas_siguen_entrando` |
| el arranque promueve sin distinguir mayúsculas | `assert roles.count("admin") == (1 if fila and username == admin else 0)` |
| el arranque prueba exacto y si no hay, sin distinguir mayúsculas | `FAILED …siguen_entrando[sola_y_la_lista_en_mayusculas]` |
| el login prueba exacto y si no hay, sin distinguir mayúsculas | `FAILED …siguen_entrando[sola_y_la_lista_en_mayusculas]` |

El sabotaje del arranque es `func.lower(User.username) == identifier.lower()` con `.first()`, sin `order_by`. En los sabotajes 6 y 7, el guion exige además que el rojo **no** venga de `[minusculas]`: así queda claro que lo rompe la fila nueva.

### chequeo-6

```
chequeo-6 4087b46..1960a9a: avisos para mirar, no un veredicto
producto +4/−2
arnés +220/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11373 → 11375
avisos: 0
```

```
chequeo-6 ccded98..1960a9a: avisos para mirar, no un veredicto
producto +0/−0
arnés +44/−14
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

### Lo que no se corrió

- **La CI de GitHub**: esta rama no tiene PR.
- **Los sabotajes 6 y 7 en PG**, y **`test_permisos2.py` en PG real** (riesgos arriba).

### Para reproducir

```bash
git fetch origin claude/dev-tecnica && git checkout --detach 1960a9a
PY=<venv>/bin/python
export GEMINI_API_KEY=test-key ENVIRONMENT=test VUCE_MODE=fake TARIFAR_MODE=fake \
       AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares

# «BASE  | en verde» con 40 passed, 7 ROJO, «sabotajes con falla: 0», salida 0
PY="$PY" bash scripts/testing/sabotajes/nombres1.sh 1960a9a; echo salida=$?

# Postgres 16 real: el plugin hace lo mismo que conftest, pero sin pisar DATABASE_URL.
# Tiene que mostrar «dialecto: postgresql» y «15 passed»
mkdir -p /tmp/pgplug && cat > /tmp/pgplug/pg_nullpool.py <<'EOF'
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
import proyecto_maria.database.connection as _conn
assert os.environ["DATABASE_URL"].startswith("postgresql+asyncpg"), "no es Postgres"
_e = create_async_engine(os.environ["DATABASE_URL"], future=True, poolclass=NullPool)
_conn.engine = _e
_conn.AsyncSessionLocal = async_sessionmaker(_e, class_=AsyncSession, expire_on_commit=False)
print("dialecto:", _conn.engine.dialect.name)
def pytest_sessionstart(session):
    asyncio.run(_conn.init_db())
EOF
PY="$PY" bash scripts/testing/con_pg16.sh bash -c \
  'DATABASE_URL="${BACKUP1A_PG_URL/postgresql:/postgresql+asyncpg:}" PYTHONPATH=/tmp/pgplug \
   "$PY" -m pytest --noconftest -p pg_nullpool -s -q --no-cov tests/test_nombres1.py 2>&1 | grep -E "dialecto|passed|failed|^FAILED"'

# El mismo comando, con el sabotaje del arranque sin order_by: FAILED en [mayusculas]
# y en [sola_y_la_lista_en_mayusculas], «2 failed, 13 passed»
"$PY" - <<'EOF'
p = "proyecto_maria/main.py"; s = open(p).read()
v = 'select(User).where(User.username == identifier))'
assert s.count(v) == 1
open(p, "w").write(s.replace(v, 'select(User).where(func.lower(User.username) == identifier.lower()))'))
EOF
#   (repetir el comando de PG de arriba)
git checkout -- proyecto_maria/main.py

# Que conftest pisa DATABASE_URL: muestra la línea 19
sed -n 19p tests/conftest.py

# Los números de §6: la salida de arriba
"$PY" docs/pm/herramientas/chequeo-6.py 4087b46 1960a9a
"$PY" docs/pm/herramientas/chequeo-6.py ccded98 1960a9a
```

`<venv>` es el entorno virtual del proyecto.

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. NOMBRES-1 vuelta 2 entregada en 1960a9a, esperando veredicto; corte 2026-11-09 05:00 UTC. Sin pieza «apenas entregues». No abrí ninguna D; la carrera queda como límite conocido por decisión de la PM. Reglas de Emi: sólo la PM y Emi me piden, nada se publica sin su «dale» para el SHA, nunca main, sin secretos.
