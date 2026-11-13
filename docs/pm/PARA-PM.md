# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## FUGA-HILOS-GUARDA: una conexión de aiosqlite que queda abierta pone rojo al test que la dejó

| | SHA |
|---|---|
| base (tu rama traída con merge, fast-forward; sólo `docs/pm`) | `7bae88f5` |
| test (`tests/conftest.py`) | `a58d45d5` |
| informe | el commit `docs:` que trae este archivo |

**Resultado: cumple las puertas 1 a 4, con un límite que tenés que saber (abajo).**
`producto +0/−0`, arnés `+37/−0`. Una decisión: D230.

**El límite, primero.** La guarda ve conexiones que siguen **vivas** al
terminar el test. No ve los «Event loop is closed» de la suite: ahí el hilo
muere con la excepción del bucle cerrado, no queda vivo. Su causa (puerta 1)
es de producto, no de `tests/`: la guarda no la puede cubrir sin tocar
`main.py`. Tampoco ve un generador de la sesión que nunca hizo una consulta:
sin conexión no hay hilo.

### Decisiones

**D230. Los `get_db` dejan abierto `get_async_session`.** Es la causa de los
«Event loop is closed» (puerta 1). Opciones:
- **(a)** Pieza de producto aparte, con revisión fuerte: `get_db` pasa a ser
  `get_async_session` (o lo cierra con `contextlib.aclosing`) en
  `main.py:173` y `auth/dependencies.py:21`. Ojo: cambia el camino de error.
  Hoy el `except Exception: await session.rollback()` de `connection.py:101-104`
  **nunca corre** ante un error del endpoint; con el arreglo corre. En mi
  prueba eso rompe `test_cobro_corte1.py::test_regenerar_con_una_falla_deja_entero_lo_ya_entregado[al_confirmar_y_deshacer]`,
  porque su sabotaje hace fallar el rollback. Toca cobro: hay que decidir qué
  espera ese caso.
- **(b)** Dejarlo como riesgo en la cola.

Recomiendo **(a)**, como pieza propia y no ahora: hoy el rollback de error no
corre y la sesión se cierra tarde, en una tarea que se cancela. En producción
(un bucle que no se apaga) el cierre llega igual, pero tarde y fuera del
pedido. No lo medí en gunicorn.

### Comandos

```bash
git diff 7bae88f5 a58d45d5 --stat          # sólo tests/conftest.py | 37 +
python docs/pm/herramientas/chequeo-6.py 7bae88f5 a58d45d5   # producto +0/−0, avisos: 0
```

### Puerta 1: la causa de «Event loop is closed»

Los envoltorios de `main.py:173` y `auth/dependencies.py:21`:

```python
async def get_db():
    async for session in get_async_session():
        yield session
```

FastAPI cierra (`aclose`) el envoltorio, pero salir de un `async for` no
cierra el generador interno. `get_async_session` (con su
`finally: await session.close()` en `database/connection.py:107`) queda
suspendido, y lo cierra después el finalizador de generadores en una tarea
`async_generator_athrow`. Si el bucle del `TestClient` se está apagando, esa
tarea llega cancelada: el `close` de aiosqlite no termina y su hilo muere con
«Event loop is closed».

Evidencia, en tres corridas de la suite entera:

1. **Plugin que registra cada `close` de aiosqlite cancelado**, con el test y
   la pila de quien lo pidió (`6126 passed, 110 skipped, 3 xfailed, 103 warnings in 1081.17s (0:18:01)`).
   Los tres casos dicen lo mismo:
   ```
   CERRADO test=tests/test_org1.py::test_invitar_hasta_el_tope_del_plan[sqlite_sin_zona-3] funcion='Connection.stop.<locals>.close_and_stop' error=None cancelada=True
     parada: async_generator_athrow | connection.py:107:get_async_session
   CERRADO test=tests/test_org1.py::test_registrarse_con_una_invitacion_usa_las_otras_del_mismo_email[sqlite_sin_zona] ... cancelada=True
     parada: async_generator_athrow | connection.py:107:get_async_session
   CERRADO test=tests/test_sesion1.py::test_una_sesion_revocada_no_vuelve ... cancelada=True
     parada: async_generator_athrow | connection.py:107:get_async_session
   ```
   Cambian de test en cada corrida porque depende de cuándo corre el
   recolector.
2. **Experimento aislado** (fuera del repo): después de `aclose()` del
   envoltorio, el interno sigue pendiente (`['externo cerrado; interno pendiente=True']`);
   al apagarse `asyncio.run`, recibe `CancelledError` dentro de una tarea
   `async_generator_athrow`.
3. **Contraprueba en un worktree descartable**, con `get_db = get_async_session`
   en los dos archivos: las líneas «Event loop is closed» bajan de 8 a 0 (tabla
   de la puerta 4).

El mismo patrón (`async for` sobre `get_async_session` sin cerrar) aparece en
`main.py:1986` (`log_request_background`, con `break`), `main.py:11689`
(webhook de MP, con `return` adentro) y `main.py:1695` (usuarios demo al
arrancar). Son riesgos; no los toqué.

### Puerta 2: rojo con otra fuga, verde con el arreglo

Archivo de prueba fuera del repo (`test_zz_fuga.py`), copiado a un worktree
con la guarda y a otro con la base. El ayudante es propio del archivo
(`_una_consulta`: una consulta dentro de `async for` sobre `get_async_session`,
sale con `break` y cierra el generador sólo si se le pide), no `_sql` de
`guardar1`. El primer caso repite la forma vieja como control; los otros dos
son fugas escritas de otra forma:

| caso | con guarda | base |
|---|---|---|
| control: `new_event_loop().run_until_complete` sin cerrar el bucle ni el generador | **ROJO** | verde |
| salir del `async for` sin cerrar el generador, **con el bucle cerrado** | **ROJO** | verde |
| `aiosqlite.connect` directo, sin cerrar, en un test async | **ROJO** | verde |
| el arreglo: bucle propio cerrado con `aclose`; `asyncio.run` sin `aclose` (su `shutdown_asyncgens` lo cierra); `async for` con o sin `aclose` en un test de pytest-asyncio (su bucle lo cierra) | verde | verde |
| hilos ajenos: `ThreadPoolExecutor`, `Thread`, `Timer`, `_DummyThread`, `MainThread` | verde | verde |

Con la guarda (`a58d45d5`):
```
tests/test_zz_fuga.py::test_bucle_propio_sin_cerrar dejó 1 conexión(es) de aiosqlite abiertas después de 5 s: ['Thread-10 (_connection_worker_thread)']. Cerrá el generador de la sesión (aclose) y el bucle que la abrió.
tests/test_zz_fuga.py::test_async_for_sin_cerrar_bucle_cerrado dejó 1 conexión(es) de aiosqlite abiertas después de 5 s: ['Thread-14 (_connection_worker_thread)']. Cerrá el generador de la sesión (aclose) y el bucle que la abrió.
tests/test_zz_fuga.py::test_aiosqlite_directo_sin_cerrar dejó 1 conexión(es) de aiosqlite abiertas después de 5 s: ['Thread-18 (_connection_worker_thread)']. Cerrá el generador de la sesión (aclose) y el bucle que la abrió.
=================== 9 passed, 4 warnings, 3 errors in 15.10s ===================
```
Sin la guarda (base): `9 passed, 4 warnings in 0.09s`. Los 15 s son las tres
esperas de hasta 5 s de los casos rojos; un caso verde no espera, porque el
hilo de una conexión cerrada sale enseguida.

### Puerta 3: los hilos de todo el proceso no la disparan

La guarda sólo mira hilos cuyo nombre termina en `(_connection_worker_thread)`
y que aparecieron durante ese test. Al final de las tres suites siguen vivos,
sin disparar nada:

| hilo | cantidad |
|---|---|
| `lectura-excel` | 2 |
| `lectura-excel-liviano` | 2 |
| `lectura-pdf` | 1 |
| `validar-excel` | 2 |
| `validar-excel-liviano` | 1 |
| `_MainThread:MainThread` | 1 |
| `_DummyThread:Dummy` | 1 |

Los 8 de los pools, `MainThread` y el `_DummyThread`. Mismo censo en base,
guarda y contraprueba.

### Puerta 4: pytest entero

`pytest -q --no-cov --timeout=120 -p no:cacheprovider`, una corrida por
columna, en worktrees separados. La base de las corridas fue `9e1e2928`; contra
`7bae88f5` no cambia nada fuera de `docs/pm` (`git diff --stat 9e1e2928 7bae88f5 -- . ':!docs/pm'` vacío).

| | base | guarda (`tests/conftest.py` de `a58d45d5`) | contraprueba `get_db` (descartable, no se entrega) |
|---|---|---|---|
| resultado | `6126 passed, 110 skipped, 3 xfailed, 105 warnings in 1068.55s (0:17:48)` | `6126 passed, 110 skipped, 3 xfailed, 105 warnings in 1084.54s (0:18:04)` | `1 failed, 6125 passed, 110 skipped, 3 xfailed, 104 warnings in 1095.87s (0:18:15)` |
| reloj de pared | 1073 s | 1089 s | 1101 s |
| líneas «Event loop is closed» | 8 | 8 | 0 |

- Mismos `passed`; la guarda no dio ningún rojo falso en la suite.
- +16 s (1,5 %) con la guarda, en una sola corrida por lado: no distingo eso
  del ruido.
- El `failed` de la contraprueba es el de D230.

### Riesgos y lo no corrido

- **La guarda no cubre la causa de producto** (D230), ni un generador sin
  consulta. Lo dice el commit.
- **Espera de hasta 5 s por conexión nueva viva** al terminar un test. Es una
  espera por condición (`join` con tope), no fija: sólo se paga cuando hay
  fuga.
- **Una conexión que otro test abrió y quedó viva** no se le cuenta al test
  siguiente: cada test compara contra los hilos que había al empezar.
- **Si el test ya falló**, la guarda no le pisa el reporte.
- Adversarios y `/code-review`: **no corridos** (pieza sin adversarios).
- Sólo `tests/conftest.py`: nada en el producto, `ci.yml` ni MARIA.

### chequeo-6

```
chequeo-6 7bae88f52f6ab43a7d8debd9e1345a72c2863e9f..a58d45d5623c6ecac0b77f7c9007e46dc2a5ea1b: avisos para mirar, no un veredicto
producto +0/−0
arnés +37/−0
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

/compact conservar: Dev 1 técnica, sesión session_018yxeKHYQKFA3qJ2WJmQru7, rama claude/dev-tecnica. FUGA-HILOS-GUARDA entregada: test a58d45d5 sobre base 7bae88f5, informe en el commit docs siguiente. D230 abierta (arreglo de get_db en main.py:173 y auth/dependencies.py:21; rompe test_cobro_corte1[al_confirmar_y_deshacer] porque el rollback empieza a correr). Próxima D: D231. Sin advisor, nunca main, sin secretos, test_conexiones1.py no se sube.
