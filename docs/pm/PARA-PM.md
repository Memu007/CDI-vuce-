# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## NOMBRES-1, entregada en `ccded98` (informe en el commit de arriba)

Base: `4087b46` (merge de tu rama con NOMBRES-1 en la tarea activa).

| Commit | Qué |
|---|---|
| `5af134f` | fix: `_exigir_username_libre` compara contra las cuentas guardadas sin distinguir mayúsculas; CHANGELOG |
| `fa722eb` | test: `tests/test_nombres1.py` y el guion `scripts/testing/sabotajes/nombres1.sh` |
| `7820e15` | el comentario de la función dice qué pasa con una cuenta vieja que no es ASCII |
| `ccded98` | test: el caso apaga el limitador con `monkeypatch`, para que no quede apagado en los casos siguientes |

**producto +4/−2**, arnés +190/−0. Archivo de producto tocado: `proyecto_maria/main.py`.

### Resultado

1. **Registrarse y crear un estudio** con un nombre que ya existe escrito con otras mayúsculas da 400 «Usuario ya existe». Vale para cualquier cuenta, esté o no en `ADMIN_USERNAMES`. El chequeo vive en un solo lugar (`_exigir_username_libre`), por donde pasan las dos rutas.
2. **No hay ruta para cambiar el nombre de usuario.** Busqué todas las altas de `User(`: el registro, crear un estudio y las cuentas de demostración del arranque, que existen sólo fuera de producción. La landing arma el nombre a partir del email en minúsculas.
3. **Lo que ya existe queda como está.** El login y la promoción del arranque siguen comparando exacto. Dos cuentas viejas que difieren sólo en mayúsculas entran cada una con su clave, y el arranque promueve sólo la que coincide exacto. No hay migración, borrado ni índice nuevo.

Nada para decidir. No propongo índice único, así que D128 queda libre.

### Riesgos (quedan, sin arreglo)

| Riesgo | Severidad | Por qué queda |
|---|---|---|
| Dos altas simultáneas `Foo` y `foo` pueden entrar las dos | baja | Sólo lo cierra un índice único, y la tarea lo excluye. Ni el adversario ni yo lo reprodujimos |
| La búsqueda con `lower()` recorre toda la tabla `users` en cada alta | baja | Pasa sólo al registrarse o crear un estudio. Un índice sobre `lower(username)` es la misma D que el índice único |
| Postgres con una colación rara (por ejemplo turca) podría bajar distinto que Python | especulativa | El pedido ya llega en ASCII. En el peor caso bloquea un nombre de más; nunca deja pasar uno igual |
| Las demos del arranque no pasan por el chequeo | baja | Existen sólo fuera de producción, y ya era así |
| El sabotaje «arranque sin distinguir» depende de que SQLite ordene la mayúscula primero | arnés | El guion corre en SQLite. En Postgres el caso pasa en verde (38 passed), pero ese sabotaje no lo corrí ahí |
| `de_la_lista` y `exacto` no distinguen el arreglo | arnés | Son controles: los rechazan la lista o el nombre exacto también sin el arreglo. Los que distinguen son los otros cuatro, por las dos rutas |

### Hallazgos de la autorrevisión

| Revisor (modelo, esfuerzo) | Hallazgo | Qué hice |
|---|---|---|
| adversario-sonnet-alto (Sonnet, alto) | Nada grave ni medio | — |
| adversario-sonnet-alto | Baja: carrera de dos altas simultáneas | No la pudo reproducir. Riesgo arriba |
| adversario-sonnet-alto | Especulativa: colación turca en Postgres | Riesgo arriba |
| adversario-sonnet-alto | Observación: recorrido completo de la tabla; `de_la_lista` no cubre el cambio | Riesgo arriba |
| `/code-review high` | El comentario afirmaba de más sobre ASCII | Arreglado en `7820e15` |
| `/code-review high` | `limiter.enabled = False` quedaba apagado para los casos siguientes | Arreglado en `ccded98` |
| `/code-review high` | Carrera, login exacto, demos, recorrido completo, colación del sabotaje, ayudantes copiados de `test_permisos2.py`, el `TestClient` del arranque siembra las demos | Riesgos arriba o igual que en `test_permisos2.py`; sin cambio |
| `/security-review` (subagente general, mismo modelo que la sesión) | Sin hallazgos de confianza ≥8. Descartó inyección SQL (valor ligado y formato validado antes), escalada a admin (la promoción sigue exacta), confusión de identidad (login sin tocar) y enumeración por «Usuario ya existe» (ya existía) | — |

### Pruebas

| Puerta | Sobre | Resultado |
|---|---|---|
| rojo antes del arreglo, SQLite | `fa722eb` con el `main.py` de `4087b46` | «8 failed, 5 passed in 8.94s» |
| rojo antes del arreglo, Postgres 16 descartable | `fa722eb` con el `main.py` de `4087b46` | «8 failed, 30 passed in 12.80s» |
| verde, Postgres 16 descartable | `ccded98` | «38 passed in 9.58s» |
| `nombres1.sh` | `ccded98` | «BASE en verde» con «38 passed, 5 warnings in 9.82s», 5 `ROJO`, «sabotajes con falla: 0», salida 0 |
| `permisos2.sh` | `fa722eb` | 10 `ROJO`, «sabotajes con falla: 0», salida 0 |
| suite completa, worktree limpio | `ccded98` | «4731 passed, 110 skipped, 3 xfailed in 770.69s (0:12:50)», salida 0 |
| `compileall -q proyecto_maria` | `ccded98` | salida 0 |
| `smoke_friccion.sh`, app de prueba local | `ccded98` | «==> OK · telemetría + alias session/state + by-cuit protegido», salida 0 |
| `ataque_aislamiento.sh` | `ccded98` | «Bloqueado: 47 · Fugas: 0 · Sin probar: 0», «✅ PUERTA G3 PASADA. Ningún despachante ve datos de otro.», salida 0 |

En los dos rojos, los 8 que fallan son `mayusculas`, `capitalizada`, `existe_en_mayusculas` y `mezcla`, por las dos rutas.

Sabotajes de `nombres1.sh`, tal como los dio la corrida:

| Sabotaje | Primer FAILED |
|---|---|
| el chequeo vuelve a comparar exacto | `test_un_nombre_que_existe_con_otras_mayusculas_no_se_registra[mayusculas-/auth/register]` |
| el chequeo no baja la cuenta guardada | `…[existe_en_mayusculas-/api/organizations/create]` |
| el chequeo no baja el pedido | `…[capitalizada-/auth/register]` |
| el login busca sin distinguir mayúsculas | `test_dos_cuentas_viejas_que_difieren_en_mayusculas_siguen_entrando` |
| el arranque promueve sin distinguir mayúsculas | `test_dos_cuentas_viejas_que_difieren_en_mayusculas_siguen_entrando` |

`permisos2.sh` corrió sobre `fa722eb`. Lo que cambió después (`7820e15` y `ccded98`) son un comentario y el fixture de `test_nombres1.py`, que `permisos2.sh` no usa.

### chequeo-6

```
chequeo-6 4087b46..ccded98: avisos para mirar, no un veredicto
producto +4/−2
arnés +190/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 11373 → 11375
avisos: 0
```

### Lo que no se corrió

- **La CI de GitHub** no corrió: esta rama no tiene PR.

### Para reproducir

```bash
git fetch origin claude/dev-tecnica && git checkout --detach ccded98
export DATABASE_URL=sqlite+aiosqlite:///./test.db GEMINI_API_KEY=test-key ENVIRONMENT=test \
       VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares

# 38 passed
python -m pytest -q --no-cov tests/test_nombres1.py tests/test_permisos2.py

# El rojo: «8 failed, 5 passed»
git show 4087b46:proyecto_maria/main.py > proyecto_maria/main.py
python -m pytest -q --no-cov tests/test_nombres1.py; git checkout -- proyecto_maria/main.py

# «BASE  | en verde», 5 ROJO, «sabotajes con falla: 0», salida 0
PY=<venv>/bin/python bash scripts/testing/sabotajes/nombres1.sh ccded98; echo salida=$?

# Postgres 16 descartable: 38 passed
PY=<venv>/bin/python bash scripts/testing/con_pg16.sh bash -c \
  'DATABASE_URL="${BACKUP1A_PG_URL/postgresql:/postgresql+asyncpg:}" python -m pytest -q --no-cov tests/test_nombres1.py tests/test_permisos2.py'

# Los números de §6: la salida de arriba
python docs/pm/herramientas/chequeo-6.py 4087b46 ccded98
```

`<venv>` es el entorno virtual del proyecto.

/compact conservar: Dev 1, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica; aviso a la PM principal (session_01B7FVQspcEHF7PqNv797wNM) con send_message priority next. NOMBRES-1 entregada en ccded98, esperando veredicto; corte 2026-11-09 05:00 UTC. Sin pieza «apenas entregues». Próxima D libre: D128. Reglas de Emi: sólo la PM y Emi me piden, nada se publica sin su «dale» para el SHA, nunca main, sin secretos.
