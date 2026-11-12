# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1 D (sólo arnés): analyze y manual retienen conexiones con otra cuenta; el login no. Decide Emi: D183 y D184

| Qué | SHA |
|---|---|
| Arnés: fases `pico_excel` y `pico_cuerpo_manual`, y la serie de conexiones tomadas | `ebd2c1fd` |
| Merge de la PM | `75349ca8` |
| Arnés: una fila de api_logs perdida con el pool lleno es «pool lleno», no una medición inválida | `f9962e6e` |
| Este informe | el commit `docs:` que lo trae |

**Producto tocado: ninguno.** El arreglo va como diff sin commitear, más abajo.

**Resultado, en corto:**
- Hoy, sobre `f9962e6e`, el medidor da rc=4. `/api/migrations/analyze` y `/api/operations/manual` le dan a la otra cuenta **12 × 500, con esperas de hasta 30.13 s**.
- Con el diff, rc=0. La otra cuenta recibe 0 × 500 en todas las fases y espera como mucho 3.77 s, en el login.
- El login (bcrypt) no retiene: da 0 × 500 y 4.12 s hoy, menos de 5 s. Por la regla de la tarea, no propongo nada para él.
- La subida pública retiene, no es un pico al llegar. Hoy tiene 50 conexiones tomadas durante 31 s y después baja en escalones de ~30 s. Con el diff, tiene una sola muestra en 50, al llegar.

## Decisiones

- **D183.** Si D182 dice que el arreglo de C entra, ¿entran también los hunks de analyze y de manual?
  - (a) **Los cuatro hunks** (recomendada). Con analyze y manual afuera, la otra cuenta sigue recibiendo 12 × 500 por esas dos rutas.
  - (b) Sólo los dos de C (billing y sugerir).
  - (c) Nada.
- **D184.** Si entra el arreglo, ¿`tests/test_conexiones1.py` entra con el commit de pruebas?
  - (a) **Sí** (recomendada). Tarda ~4 s, no usa PG, da rojo hoy y verde con el diff, y cada hunk tiene su caso: la tabla de abajo lo muestra.
  - (b) No, alcanza con el medidor. Pero el medidor necesita PG16 y tarda minutos, y la CI no lo corre.
- D182 (del informe de C) sigue pendiente de Emi.

## Resultado, para la otra cuenta

Comando: `scripts/testing/con_pg16.sh python scripts/testing/conexiones1_medir.py --pico 60 --lento 30`. Pool de producción: 20 + 30, con `pool_timeout=30`. En cada fase, 60 pedidos de una cuenta frenados en su punto lento, más 12 de la otra cuenta.

### Hoy, `f9962e6e`: rc=4, «POOL LLENO: ninguna conexión quedó tomada, pero la otra cuenta o el log sufrieron»

| Fase | Enviados · disp · tlog · filas | máxT/PG | Quedan | Seg | Espera máx. de la otra |
|---|---|---|---|---|---|
| pico_bcrypt | 72 · 72 · 72 · 72 | 50/50 | 0 | 0.05 | 4.12 |
| pico_gemini | 72 · 72 · 72 · 72 | 50/50 | 0 | 29.96 | 30.08 |
| pico_pdf | 72 · 72 · 72 · 72 | 50/50 | 0 | 22.03 | 29.98 |
| pico_excel | 72 · 72 · 72 · 62 | 50/50 | 0 | 29.84 | 30.13 |
| pico_cuerpo_manual | 72 · 72 · 72 · 72 | 50/50 | 0 | 0.2 | 30.13 |

Líneas del log, tal cual:

```
pico_bcrypt: la otra cuenta recibió 0 × 500 y esperó hasta 4.12 s; en total, 0 × 500
pico_gemini: la otra cuenta recibió 0 × 500 y esperó hasta 30.08 s; en total, 0 × 500
pico_pdf: la otra cuenta recibió 0 × 500 y esperó hasta 29.98 s; en total, 10 × 500
  pico_excel: 72 pedidos y 62 filas nuevas en api_logs
pico_excel: la otra cuenta recibió 12 × 500 y esperó hasta 30.13 s; en total, 22 × 500
pico_cuerpo_manual: 50 de 60 esperando el cuerpo a la vez (no llegaron en 10.03 s, con 50 conexiones tomadas); la otra cuenta recibió 12 × 500 y esperó hasta 30.13 s; en total, 22 × 500
```

Los códigos por fase:

| Fase | Códigos |
|---|---|
| pico_bcrypt | otra 200 × 12 · pico 401 × 60 |
| pico_gemini | otra 200 × 12 · pico 200 × 60 |
| pico_pdf | otra 200 × 12 · pico 422 × 16 · 500 × 10 · 504 × 34 |
| pico_excel | otra **500 × 12** · pico 500 × 10 · 504 × 50 |
| pico_cuerpo_manual | otra **500 × 12** · manual_lento 404 × 50 · 500 × 10 |

En el log del servidor:

| Contador | Cantidad |
|---|---|
| QueuePool limit | 280 |
| Exception in ASGI application | 54 |
| Error logging metrics | 10 |
| Traceback | 324 |
| non-checked-in connection · Task was destroyed · CancelledError · UnboundLocalError | 0 |

En pico_excel se perdieron 10 filas de api_logs. Son las de «Error logging metrics», con el pool lleno. Ver `f9962e6e`, más abajo.

### Con el diff: rc=0, «sin conexiones tomadas»

| Fase | máxT/PG | Seg | Espera máx. de la otra | Códigos |
|---|---|---|---|---|
| pico_bcrypt | 50/50 | 0.0 | 3.77 | otra 200 × 12 |
| pico_gemini | 27/30 | 29.6 | 0.44 | otra 200 × 12 |
| pico_pdf | 50/50 | 20.58 | 0.05 | 422 × 16 · 504 × 44 · otra 200 × 12 |
| pico_excel | 50/50 | 29.91 | 0.13 | 504 × 60 · otra 200 × 12 |
| pico_cuerpo_manual | 50/50 | 0.29 | 0.05 | 404 × 60 · otra 200 × 12 |

- La otra cuenta recibió 0 × 500 en todas las fases.
- Hay 72 filas de api_logs en todas.
- En el log, todos los contadores de arriba dan 0.

Línea de manual, tal cual:

```
pico_cuerpo_manual: 60 de 60 esperando el cuerpo a la vez (llegaron en 0.94 s, con 0 conexiones tomadas); la otra cuenta recibió 0 × 500 y esperó hasta 0.05 s; en total, 0 × 500
```

### Punto 3: la subida pública, en el tiempo

`T=` son las conexiones tomadas en cada muestra (~0.5 s). `{...}` son los pedidos en vuelo en el punto lento.

**Subida (pdf).**
- **Hoy, retención:**
  - `0.04s T=0 · 0.59s T=50 · 1.1s T=50 {'pdf': 1} · 1.64s T=50 {'pdf': 4} …`;
  - en T=50 hasta 31.03 s;
  - después baja en escalones de ~30 s: 47/46 desde 31.56 s, 44/42 desde 61.46 s, 40/38 desde 91.44 s y 36/34 desde 121.39 s;
  - de 124.06 s a 129.42 s cae de 32 a 2, y queda en 0 desde 129.95 s;
  - son 284 muestras, 58 en T=50.
  - Las conexiones siguen tomadas mientras dura el lector lento de 30 s.
- **Con el diff:** `0.04s T=0 · 0.57s T=50 · 1.07s T=0 · 1.61s T=0 {'pdf': 4} …`. Una sola muestra en 50, al llegar, y después 0. Son 286 muestras.

**Excel (analyze).**
- Hoy, T=50 desde 0.58 s hasta 60.79 s, y 0 desde 61.3 s: 171 muestras, 114 en T=50.
- Con el diff, una sola muestra en 50, a los 0.59 s: 171 muestras.

**Cuerpo de manual.**
- Hoy, T=50 con `{'cuerpo': 50}` desde 0.5 s hasta 40.01 s: 76 muestras, 75 en T=50.
- Con el diff: `0.0s T=0 · 0.54s T=50 · 1.08s T=50 · 1.6s T=50 · 2.11s T=15`.
  - Acá T=50 aparece en 3 de 5 muestras, no en una sola.
  - Que no retiene lo muestran «60 de 60 … con 0 conexiones tomadas» y la otra cuenta en 0.05 s.

**Otras fases.**
- Gemini:
  - hoy, T=50 hasta 29.9 s, T=10 de 30.98 s a 59.81 s, y 0 desde 60.35 s;
  - con el diff, el máximo es 5.
- Bcrypt: T=50 dura unos 3 s, hoy y con el diff, y el diff no lo cambia. Hoy son 7 de 11 muestras en T=50; con el diff, 6 de 11.

No sé la causa exacta del pico de 50 que queda al llegar en pdf y excel con el diff. No retiene, pero no lo afirmo como explicado.

### El diff propuesto, sin commitear

Es el de C, más un hunk de manual, otro de analyze y un ajuste a `test_cobro_corte1.py`, más el test nuevo.
- `git apply --check` sobre `f9962e6e`: limpio.
- No toca `require_active_billing`.
- Producto: +13/−0.

```diff
diff --git a/proyecto_maria/main.py b/proyecto_maria/main.py
index 52fe473f..05eaf627 100644
--- a/proyecto_maria/main.py
+++ b/proyecto_maria/main.py
@@ -2303,6 +2303,9 @@ async def require_billing_vigente(
     await _vencer_y_guardar(db, entidad)
     if not billing_service.tiene_acceso(entidad):
         raise HTTPException(status_code=402, detail=_detalle_402(entidad))
+    # Termina la transacción de lectura: si no, la conexión queda tomada
+    # mientras el endpoint espera a la IA o a la lectura del PDF.
+    await db.commit()
     return db_user
 
 
@@ -3746,11 +3749,18 @@ async def simulate_charge(user=Depends(get_current_user), db: AsyncSession = Dep
     }
 
 
+async def _leer_cuerpo(request: Request):
+    # Con el cuerpo ya leído, un cliente lento no retiene la conexión de las
+    # dependencias que vienen después.
+    await request.body()
+
+
 @app.post("/api/operations/manual")
 @limiter.limit(get_dynamic_rate_limit)
 async def create_manual_operation(
     request: Request,
     user=Depends(get_current_user),
+    _cuerpo=Depends(_leer_cuerpo),
     db: AsyncSession = Depends(get_db),
     db_user: User = Depends(require_active_billing),
 ):
@@ -7172,6 +7182,8 @@ async def analyze_client_migration(
         )
     )
     existing_clients = existing_result.scalars().all()
+    # Suelta la conexión mientras se lee el archivo; los clientes quedan cargados.
+    await db.commit()
     mapper = GeminiMigrationHeaderMapper(username=user["username"])
     try:
         # Con tiempo máximo, como leer un PDF (EXCEL-1).
@@ -10448,6 +10460,7 @@ async def sugerir_ncm(
         # (RENDIMIENTO-1). Si no contesta a tiempo, se sigue sin sus sugerencias.
         import asyncio
         limite = _segundos_de_entorno("NCM_GEMINI_TIMEOUT_S", 30.0)
+        await db.commit()
         try:
             de_gemini = await asyncio.wait_for(
                 asyncio.to_thread(_suggest_ncm_with_gemini, descripcion, 5 - len(sugerencias)),
diff --git a/tests/test_cobro_corte1.py b/tests/test_cobro_corte1.py
index cfb81a79..9775df77 100644
--- a/tests/test_cobro_corte1.py
+++ b/tests/test_cobro_corte1.py
@@ -828,7 +828,8 @@ _confirmar = main.AsyncSession.commit
 
 async def _commit_que_falla(self):
     # La autenticación confirma antes de la ruta: falla sólo el de main.py.
-    if sys._getframe(1).f_code.co_filename != main.__file__:
+    quien = sys._getframe(1).f_code
+    if quien.co_filename != main.__file__ or quien.co_name == "require_billing_vigente":
         return await _confirmar(self)
     raise RuntimeError("la base se cayó al confirmar")
 
diff --git a/tests/test_conexiones1.py b/tests/test_conexiones1.py
new file mode 100644
index 00000000..a029d48d
--- /dev/null
+++ b/tests/test_conexiones1.py
@@ -0,0 +1,109 @@
+"""Ninguna ruta lenta retiene una conexión a la base mientras espera.
+
+Cada ruta se frena en su punto lento (la IA, el lector de PDF, la lectura del
+Excel, el cuerpo del pedido) y ahí se cuentan las conexiones que tiene tomadas
+el pedido. Con el pool de producción, cada una tomada ahí es un lugar menos
+para las otras cuentas mientras dura la espera.
+"""
+import asyncio
+import io
+import uuid
+
+import pytest
+from fastapi.testclient import TestClient
+from pypdf import PdfWriter
+from sqlalchemy import event
+from starlette.requests import Request
+
+from proyecto_maria import main
+from proyecto_maria.database import connection as _conn
+from proyecto_maria.services import migration_service
+
+CLAVE = "Clave-Segura-123"
+
+
+def _pdf():
+    escritor, salida = PdfWriter(), io.BytesIO()
+    escritor.add_blank_page(100, 100)
+    escritor.write(salida)
+    return salida.getvalue()
+
+
+@pytest.fixture
+def tomadas():
+    """Cuántas conexiones hay tomadas ahora, sin las del registro de métricas,
+    que corre en su propia tarea."""
+    duenas = {}
+
+    def al_tomar(_dbapi, registro, _proxy):
+        try:
+            duenas[id(registro)] = asyncio.current_task()
+        except RuntimeError:
+            duenas[id(registro)] = None
+
+    def al_devolver(_dbapi, registro):
+        duenas.pop(id(registro), None)
+
+    motor = _conn.engine.sync_engine
+    event.listen(motor, "checkout", al_tomar)
+    event.listen(motor, "checkin", al_devolver)
+    yield lambda: sum(1 for t in duenas.values()
+                      if t is None or "log_request_background" not in t.get_coro().__qualname__)
+    event.remove(motor, "checkout", al_tomar)
+    event.remove(motor, "checkin", al_devolver)
+
+
+def _sesion(monkeypatch):
+    from proyecto_maria.core.rate_limit import limiter
+    monkeypatch.setattr(limiter, "enabled", False)
+    c = TestClient(main.app)
+    nombre = f"conex1_{uuid.uuid4().hex[:10]}"
+    r = c.post("/auth/register", json={"username": nombre, "password": CLAVE, "name": nombre,
+                                       "email": f"{nombre}@cdi.test"})
+    assert r.status_code in (200, 201), r.text
+    r = c.post("/auth/login", json={"username": nombre, "password": CLAVE})
+    assert r.status_code == 200, r.text
+    return c
+
+
+def _lector_falso(*_a, **_k):
+    raise main.DocumentoNoAdmitido("lector falso")
+
+
+# (punto lento, dónde está, qué hace en lugar de esperar, pedido, código esperado)
+RUTAS = [
+    ("_suggest_ncm_with_gemini", main, lambda *_a, **_k: [],
+     ("/api/ncm/sugerir", {"json": {"descripcion": "notebook de 14 pulgadas"}}), 200),
+    ("process_pdf", main, _lector_falso,
+     ("/upload_pdf/public", {"files": {"file": ("a.pdf", _pdf(), "application/pdf")}}), 422),
+    ("_read_sheets", migration_service, None,
+     ("/api/migrations/analyze",
+      {"files": {"file": ("clientes.csv", b"cuit,nombre\n20123456786,Cliente Uno\n", "text/csv")}}), 200),
+    ("body", Request, None,
+     ("/api/operations/manual", {"json": {"client_id": "999999999", "items": [
+         {"descripcion": "notebook", "cantidad": 1, "valor_unitario": 10}]}}), 404),
+]
+
+
+@pytest.mark.parametrize("punto, modulo, reemplazo, pedido, codigo", RUTAS,
+                         ids=[r[0] for r in RUTAS])
+def test_la_espera_no_retiene_conexiones(monkeypatch, tomadas, punto, modulo, reemplazo, pedido, codigo):
+    c = _sesion(monkeypatch)
+    vistas = []
+    original = getattr(modulo, punto)
+    if modulo is Request:
+        async def frenar(self):
+            if not hasattr(self, "_body"):
+                vistas.append(tomadas())
+            return await original(self)
+    else:
+        def frenar(*a, **k):
+            vistas.append(tomadas())
+            return (reemplazo or original)(*a, **k)
+    monkeypatch.setattr(modulo, punto, frenar)
+    monkeypatch.setattr(main, "lectura_automatica_disponible", lambda: True)
+    ruta, datos = pedido
+    with c:
+        r = c.post(ruta, **datos)
+    assert r.status_code == codigo, r.text
+    assert vistas and max(vistas) == 0, f"conexiones tomadas en {punto}: {vistas}"
```

Qué hace cada hunk de producto:

| Hunk | Ruta | Por qué retenía | Qué cambia |
|---|---|---|---|
| 1 | `require_billing_vigente` (8 endpoints) | la transacción de lectura queda abierta hasta que termina la ruta | commit al final de la dependencia |
| 2 | `/api/operations/manual` | lee el cuerpo (`await request.json()`) después de tomar la conexión | una dependencia lee el cuerpo antes de `get_db` |
| 3 | `/api/migrations/analyze` | el SELECT de `existing_clients` deja la transacción abierta mientras se lee el Excel | commit después del SELECT |
| 4 | `/api/ncm/sugerir` | la transacción queda abierta mientras espera a Gemini | commit antes de esperar |

Más detalles:
- `expire_on_commit=False` (`database/connection.py:79`), así que lo ya cargado sigue usable después del commit.
- En analyze no hay `add` ni `flush` antes del commit nuevo.
- El ajuste de `test_cobro_corte1.py` es para que su commit que falla no se dispare en el commit nuevo de `require_billing_vigente`: ese caso prueba otro commit de `main.py`.

### Punto 5: la prueba rápida

`tests/test_conexiones1.py` no tiene pico de 60.
- En cada ruta se frena el punto lento y se cuentan las conexiones que tiene tomadas el pedido. Así, una conexión retenida es un número, no una carrera.
- Sin commitear, como pide la tarea: va dentro del diff de arriba.
- Corre con `pytest -q --no-cov --timeout=120 tests/test_conexiones1.py`.

Hoy (sólo el test, sobre `f9962e6e`):

```
E   AssertionError: conexiones tomadas en _suggest_ncm_with_gemini: [1]
E   AssertionError: conexiones tomadas en process_pdf: [1]
E   AssertionError: conexiones tomadas en _read_sheets: [1, 1]
E   AssertionError: conexiones tomadas en body: [1]
FAILED tests/test_conexiones1.py::test_la_espera_no_retiene_conexiones[_suggest_ncm_with_gemini]
FAILED tests/test_conexiones1.py::test_la_espera_no_retiene_conexiones[process_pdf]
FAILED tests/test_conexiones1.py::test_la_espera_no_retiene_conexiones[_read_sheets]
FAILED tests/test_conexiones1.py::test_la_espera_no_retiene_conexiones[body]
============================== 4 failed in 4.21s ===============================
```

Con el diff: `4 passed in 4.09s`.

Sin un hunk por vez, cada uno tiene su caso. El test distingue cada hunk, no sólo el conjunto:

| Hunk sacado | Resultado | Caso que falla |
|---|---|---|
| 1 (billing) | 1 failed, 3 passed in 4.04s | `process_pdf` |
| 2 (manual) | 1 failed, 3 passed in 4.13s | `body` |
| 3 (analyze) | 1 failed, 3 passed in 4.08s | `_read_sheets` |
| 4 (sugerir) | 1 failed, 3 passed in 4.02s | `_suggest_ncm_with_gemini` |

### Supuesto reversible: `f9962e6e`

- La primera medición de hoy dio rc=2, «LA MEDICIÓN NO VALE»: se perdieron 10 filas de api_logs, cada una con su «Error logging metrics».
- Con el pool lleno, el registro de métricas no consigue conexión. Eso es un síntoma de pool lleno, no una medición rota.
- `f9962e6e` hace que la medición sea inválida sólo si sobran filas, o si las perdidas no tienen su error con el pool lleno.
- Si la PM prefiere el criterio de antes, se revierte ese commit y hoy vuelve a dar rc=2 en lugar de rc=4.

## Comandos

```bash
# 1. Worktree sobre la base, con el diff sacado de este informe
git worktree add --detach /tmp/wt-d f9962e6e && cd /tmp/wt-d
awk '/^```diff$/{f=1;next} /^```$/{f=0} f' docs/pm/PARA-PM.md > /tmp/arreglo.diff   # desde el árbol de la rama, no desde /tmp/wt-d
git apply --check /tmp/arreglo.diff; echo rc=$?        # rc=0

# 2. Sólo el test: 4 failed, con «conexiones tomadas en …: [1]»
git apply --include=tests/test_conexiones1.py /tmp/arreglo.diff
python -m pytest -q --no-cov --timeout=120 tests/test_conexiones1.py

# 3. El resto del diff: 4 passed
git apply --exclude=tests/test_conexiones1.py /tmp/arreglo.diff
python -m pytest -q --no-cov --timeout=120 tests/test_conexiones1.py

# 4. Medidor con el diff: rc=0, «sin conexiones tomadas»; sin el diff (git checkout -- . y borrar el test), rc=4
scripts/testing/con_pg16.sh python scripts/testing/conexiones1_medir.py --pico 60 --lento 30; echo rc=$?

# 5. Control, sobre la base sin diff: cinco BIEN y rc=0
PY=python scripts/testing/sabotajes/conexiones1.sh f9962e6e; echo rc=$?
```

## Puertas

| Puerta | Salida |
|---|---|
| Medidor hoy (`f9962e6e`) | rc=4, «POOL LLENO: ninguna conexión quedó tomada, pero la otra cuenta o el log sufrieron» |
| Medidor con el diff | rc=0, «sin conexiones tomadas» |
| `git apply --check` del diff sobre `f9962e6e` | limpio |
| `test_conexiones1.py` hoy · con el diff | 4 failed in 4.21s · 4 passed in 4.09s |
| `sabotajes/conexiones1.sh f9962e6e` | cinco BIEN, rc=0 |
| Suite completa con el diff | 6081 passed, 110 skipped, 3 xfailed, 101 warnings in 1329.50s, rc=0, sin FAILED ni ERROR. Corrió sobre `18202930` más el diff; entre `18202930` y `f9962e6e` sólo cambian `docs/pm` y dos scripts de `scripts/testing`, fuera de `testpaths = tests` |
| Esperas fijas nuevas | ninguna |

```
BIEN  | sin sabotaje: salida 0, dice «sin conexiones tomadas»
BIEN  | close_cancelado: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | close_cancelado_suelto: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | el producto guarda la sesión sin cerrar: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | el producto suelta la sesión sin cerrar: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
rc=0
```

<details><summary>chequeo-6, salida entera</summary>

Sobre lo commiteado (`18202930..f9962e6e`):

```
chequeo-6 18202930..HEAD: avisos para mirar, no un veredicto
producto +0/−0
arnés +140/−21
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
```

Sobre lo commiteado más el diff, en un commit local descartable que no se subió:

```
chequeo-6 18202930..34dbf5aac20b05ee6f9e66bf56b089fbe65fda69: avisos para mirar, no un veredicto
producto +13/−0
arnés +251/−22
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12270 → 12283
avisos: 0
```

</details>

**Qué no corrí:**
- Subagentes, `/code-review` y `/security-review`, porque la entrega es arnés más una propuesta. Si el diff entra, pasa por los tres antes del commit de producto.
- El medidor con `--cuota-de-produccion`.
- La subida contra MARIA real: es su zona (D74).
- La suite completa sin el diff: su salida trae 1113 líneas «Task was destroyed but it is pending!» y no sé si ya estaban sin el diff.

**Riesgos:**
- **El login tiene poco margen:** la otra cuenta espera 4.12 s hoy y 3.77 s con el diff, contra el umbral de 5 s de la tarea. No propongo nada porque no retiene, pero un pico mayor podría pasarlo.
- **El arreglo es general.**
  - El hunk 1 cambia los 8 endpoints de `require_billing_vigente`: `/process_operation/`, `/upload_pdf/public`, `/generate_maria`, `/generate_maria_export`, `/api/migrations/analyze`, `/api/migrations/{batch_id}/confirm`, `/api/clientes/{client_id}/operaciones` y `/api/ncm/sugerir`.
  - Además están manual y analyze.
  - La suite completa es la red: ver Puertas.
- **La subida es zona de MARIA.** El hunk 1 la toca de rebote.
- **`_leer_cuerpo` adelanta la lectura del cuerpo en manual.**
  - Con el diff, el cuerpo se lee antes del 402 de `require_active_billing` y antes del 429 del limitador.
  - Hoy se lee después. Sin sesión, el 401 sale antes, igual que hoy.
  - Manual no tiene tope de tamaño del cuerpo, ni hoy ni con el diff. El único tope, `_leer_cuerpo_con_tope`, lo usa sólo `/api/ui/event`.
  - Una cuenta sin pago o limitada puede hacer que se lea un cuerpo grande, sin tomar conexión.
- **`require_active_billing` tiene el mismo patrón que `require_billing_vigente`** y el diff no lo toca, como pide la tarea. Manual ya no retiene por él, porque el cuerpo llega antes. Si otra ruta lenta lo usa, queda igual que hoy.
- **La suite con el diff imprime 1113 avisos «Task was destroyed but it is pending!»** (`coro=<<async_generator_athrow without __name__>()>>`). No falla ningún caso; no los comparé con la suite sin el diff, así que no sé si son nuevos.
- **Con el diff queda un pico de 50 en una muestra al llegar** en pdf y excel, y en 3 de 5 en manual. Sin causa explicada. La otra cuenta no lo sufre: espera 0.05 s y 0.13 s.

**Archivos de producto tocados:** ninguno commiteado. El diff propone `proyecto_maria/main.py`.
