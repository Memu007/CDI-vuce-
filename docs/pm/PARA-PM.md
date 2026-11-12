# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1 E (sólo arnés): el corte en manual da 400 con el diff revisado y el medidor queda en rc=0. Decide la PM: D185

| Qué | SHA |
|---|---|
| Arnés: una fila de api_logs perdida sin aviso del pool lleno invalida la medición | `aa35f9bd` |
| Arnés: el sabotaje de filas perdidas exige el motivo, no sólo el rc 2 | `8c067a32` |
| Arnés: el medidor corta a mitad del cuerpo también en `/api/operations/manual` | `299e0ee8` |
| Este informe | el commit `docs:` que lo trae |

Base: `89d3fa3c` (tu merge). Producto tocado: ninguno. El diff revisado va
abajo, completo y sin commitear.

## Resultado, en corto

1. **Filas perdidas sin aviso:** sabotaje nuevo en `sabotajes/conexiones1.sh`.
   El ancla es `session.add(log_entry)` del registro de métricas, y descarta
   tres filas de 401 sin imprimir nada. El medidor da rc=2 con «no explican la
   diferencia». **Elegí el contador por fase:** cada fase cuenta los
   «Error logging metrics: QueuePool limit» del tramo de log que escribió esa
   fase. Si no alcanzan para explicar las filas que faltan, la medición no
   vale. El contador global del final se fue.
2. **Diff revisado:** `_leer_cuerpo` atrapa `ClientDisconnect` y contesta
   400 «Body JSON inválido», igual que el `except` de la ruta. El corte en
   manual da `{400: 15}` en `api_logs`. El medidor no cuenta ningún 500 ni
   Traceback, y en el pico la espera del cuerpo llega con 0 conexiones
   tomadas.
   - `git apply --check` limpio sobre `299e0ee8`, en un árbol limpio.
   - En el repo principal falla, porque ahí `tests/test_conexiones1.py` ya
     existe sin seguimiento: es el mismo archivo que el diff crea.
3. **Caso:** una fila nueva en `RUTAS` de `test_conexiones1.py`: `body-400`,
   que corta a mitad del cuerpo en manual.
   - Con el diff de D: **rojo**, `assert 500 == 400`, «1 failed, 4 passed in
     5.46s».
   - Con el revisado: **verde**, «5 passed in 5.42s».
4. **Medidor con el diff revisado:** rc=0, «sin conexiones tomadas», todas
   las fases quietas y sin conexiones que queden. El control dio seis `BIEN`
   (los cinco de antes y el nuevo). Ninguna espera fija nueva: el corte nuevo
   reusa `fase_de_cortes` como `corte_cuerpo_a_medias`.

## Decisiones

- **D185.** ¿Tope de tamaño para el cuerpo que `_leer_cuerpo` lee antes del
  402 y del 429? Hoy, con el diff, una cuenta sin pago o pasada de cuota
  puede mandar un cuerpo grande a manual y el servidor lo lee entero antes de
  contestarle.
  - (a) **Nada en esta fila** (recomendada). Va a la cola, como pieza propia.
    - No lo pide ningún criterio de E.
    - Hace falta sesión: `get_current_user` va antes.
    - A una cuenta con pago, hoy `request.json()` ya le lee el cuerpo entero
      sin tope, y no hay tope global en `main.py`. Lo nuevo es que también
      se le lee a la cuenta que recibe 402 o 429: sin el diff, a esa no se le
      leía.
    - `_leer_cuerpo_con_tope` (`main.py:2926`, no 2929) consume `stream()`,
      y entonces la ruta tendría que tomar el cuerpo de la dependencia y no
      de `request.json()`. Cambia la firma de la ruta y suma un caso de 413
      con su sabotaje.
  - (b) Tope en `_leer_cuerpo` con `_leer_cuerpo_con_tope`, guardando el
    resultado en `request._body` para que `request.json()` lo encuentre.
    Usa un atributo privado de Starlette. Suma ~6 líneas de producto y un
    caso.
  - (c) Tope por `Content-Length` en el middleware. Es más amplio que esta
    fila: toca todas las rutas.
- Siguen en Emi: **D182** (si el arreglo entra), **D183** (los cuatro hunks)
  y **D184** (`test_conexiones1.py` con el commit de pruebas, ya decidida
  (a) por vos si Emi dice que sí). Con E, el diff tiene un hunk más (el
  import de `ClientDisconnect`) y el test, un caso más.

## Declarado

- **En `299e0ee8` sin ningún diff, `body-400` también falla,** pero por
  otro motivo: «conexiones tomadas en body: [1]». Hoy el corte da 400 (el
  `except Exception` de la ruta), pero con la conexión tomada mientras
  espera el cuerpo.
  - Ese rojo distingue la retención, no el 500.
  - El que distingue el 500 es el rojo con el diff de D, de arriba.
- **Con el diff, el cuerpo se lee antes del 402 y del 429.** Una cuenta sin
  pago que corta a mitad del cuerpo recibe 400 y no 402, y así queda en
  `api_logs`.
  - Con el cuerpo completo, la respuesta no cambia: la dependencia sólo
    lee, y el 402 y el 429 llegan después igual que hoy.
  - No lo cubre ningún caso nuevo.
- **§6, chequeo repetido:** el 400 «Body JSON inválido» del corte queda en
  dos lugares, la dependencia y el `except` de la ruta.
  - No se puede poner una vez: la dependencia ve el corte y la ruta ve el
    JSON mal formado.
  - Unificarlos sería que la dependencia parsee el JSON, y entonces la ruta
    cambia de firma.
- `corte_manual_a_medias` usa el client_id 999999999. Con el cuerpo
  completo, manual contesta 404 (`manual_lento`, como en el pico): no crea
  operaciones.

## Medidor: con el diff revisado y sin diff

Mismo `299e0ee8`, `--pico 60 --lento 30`, PG16 por `con_pg16.sh`.

| | Con el diff revisado | Sin diff |
|---|---|---|
| Veredicto | rc=0, «sin conexiones tomadas» | rc=4, «POOL LLENO: ninguna conexión quedó tomada, pero la otra cuenta o el log sufrieron» |
| `corte_manual_a_medias` | máxT 1, `{400: 15}` | máxT 2, `{400: 15}` |
| `pico_bcrypt` | otra: 0 × 500, hasta 4.17 s | otra: 0 × 500, hasta 2.88 s |
| `pico_gemini` | otra: 0 × 500, hasta 0.42 s | otra: 0 × 500, hasta 30.1 s |
| `pico_pdf` | otra: 0 × 500, hasta 0.05 s; en total 0 × 500 | otra: 0 × 500, hasta 29.99 s; en total 10 × 500 |
| `pico_excel` | otra: 0 × 500, hasta 0.1 s; en total 0 × 500 | otra: 12 × 500, hasta 30.14 s; en total 22 × 500; «72 pedidos y 62 filas nuevas en api_logs» |
| `pico_cuerpo_manual` | «60 de 60 esperando el cuerpo a la vez (llegaron en 1.02 s, con 0 conexiones tomadas)»; otra: 0 × 500 | «50 de 60 esperando el cuerpo a la vez (no llegaron en 10.05 s, con 50 conexiones tomadas)»; otra: 12 × 500, hasta 30.1 s |
| Log: Exception in ASGI application · Error logging metrics · Traceback | 0 · 0 · 0 | 54 · 10 · 324 |

Sin diff, las 10 filas que faltan en `pico_excel` las explican los 10
«Error logging metrics» de esa fase: por eso da rc=4 y no rc=2. Es el
contador por fase funcionando del lado bueno.

## Rojo y verde del caso

Con el diff de D (el de tu `c1311852`) más el `test_conexiones1.py` de E:

```
E   assert 500 == 400
FAILED tests/test_conexiones1.py::test_la_espera_no_retiene_conexiones[body-400]
========================= 1 failed, 4 passed in 5.46s ==========================
```

Con el diff revisado: `5 passed in 5.42s`.

## Control del medidor (`sabotajes/conexiones1.sh 299e0ee8`, rc=0)

```
BIEN  | sin sabotaje: salida 0, dice «sin conexiones tomadas»
BIEN  | close_cancelado: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | close_cancelado_suelto: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | el producto guarda la sesión sin cerrar: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | el producto suelta la sesión sin cerrar: salida 1, dice «QUEDAN CONEXIONES TOMADAS»
BIEN  | el producto pierde filas de api_logs sin avisar: salida 2, dice «no explican la diferencia»
```

## Diff revisado (completo, sin commitear)

Producto: `main.py` +17/−0. Pruebas: `test_cobro_corte1.py` y
`test_conexiones1.py` (nuevo, 124 líneas).

```diff
diff --git a/proyecto_maria/main.py b/proyecto_maria/main.py
index 52fe473f..6fcc0dff 100644
--- a/proyecto_maria/main.py
+++ b/proyecto_maria/main.py
@@ -386,6 +386,7 @@ app = FastAPI(
 # Configurar CORS (OWASP A5 - Broken Access Control)
 from starlette.middleware.cors import CORSMiddleware
 from starlette.exceptions import HTTPException as StarletteHTTPException
+from starlette.requests import ClientDisconnect
 
 # CORS + cookies: la especificacion prohibe combinar allow_origins=["*"]
 # con allow_credentials=True (los browsers rechazan la cookie). Como la
@@ -2303,6 +2304,9 @@ async def require_billing_vigente(
     await _vencer_y_guardar(db, entidad)
     if not billing_service.tiene_acceso(entidad):
         raise HTTPException(status_code=402, detail=_detalle_402(entidad))
+    # Termina la transacción de lectura: si no, la conexión queda tomada
+    # mientras el endpoint espera a la IA o a la lectura del PDF.
+    await db.commit()
     return db_user
 
 
@@ -3746,11 +3750,21 @@ async def simulate_charge(user=Depends(get_current_user), db: AsyncSession = Dep
     }
 
 
+async def _leer_cuerpo(request: Request):
+    # Con el cuerpo ya leído, un cliente lento no retiene la conexión de las
+    # dependencias que vienen después.
+    try:
+        await request.body()
+    except ClientDisconnect:
+        raise HTTPException(status_code=400, detail="Body JSON inválido")
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
@@ -7172,6 +7186,8 @@ async def analyze_client_migration(
         )
     )
     existing_clients = existing_result.scalars().all()
+    # Suelta la conexión mientras se lee el archivo; los clientes quedan cargados.
+    await db.commit()
     mapper = GeminiMigrationHeaderMapper(username=user["username"])
     try:
         # Con tiempo máximo, como leer un PDF (EXCEL-1).
@@ -10448,6 +10464,7 @@ async def sugerir_ncm(
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
index 00000000..e5d0187f
--- /dev/null
+++ b/tests/test_conexiones1.py
@@ -0,0 +1,124 @@
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
+    # Un 500 vuelve como respuesta y no como excepción del cliente de prueba.
+    c = TestClient(main.app, raise_server_exceptions=False)
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
+def _cortar_a_mitad(pedido):
+    """El cliente manda parte del cuerpo y se desconecta."""
+    mensajes = iter([{"type": "http.request", "body": b'{"client_id": "9', "more_body": True},
+                     {"type": "http.disconnect"}])
+
+    async def recibir():
+        return next(mensajes)
+    pedido._receive = recibir
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
+    ("body", Request, _cortar_a_mitad,
+     ("/api/operations/manual", {"json": {"client_id": "999999999", "items": []}}), 400),
+]
+
+
+@pytest.mark.parametrize("punto, modulo, reemplazo, pedido, codigo", RUTAS,
+                         ids=[f"{r[0]}-{r[4]}" for r in RUTAS])
+def test_la_espera_no_retiene_conexiones(monkeypatch, tomadas, punto, modulo, reemplazo, pedido, codigo):
+    c = _sesion(monkeypatch)
+    vistas = []
+    original = getattr(modulo, punto)
+    if modulo is Request:
+        async def frenar(self):
+            if not hasattr(self, "_body"):
+                vistas.append(tomadas())
+                if reemplazo:
+                    reemplazo(self)
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

## Comandos copiables

Desde un worktree limpio en `299e0ee8`, con el entorno de pytest de siempre.

```bash
git worktree add /tmp/e 299e0ee8 && cd /tmp/e
awk '/^```diff$/{f=1;next} /^```$/{f=0} f' docs/pm/PARA-PM.md > /tmp/e.diff   # este informe, ya mergeado
git apply --check /tmp/e.diff && echo limpio                                    # → limpio
git apply /tmp/e.diff
python -m pytest -q --no-cov tests/test_conexiones1.py                          # → 5 passed
python -m pytest -q --no-cov tests/test_conexiones1.py tests/test_cobro_corte1.py   # → 103 passed
scripts/testing/con_pg16.sh python scripts/testing/conexiones1_medir.py --pico 60 --lento 30   # → rc=0, «sin conexiones tomadas»
git checkout -- . && rm tests/test_conexiones1.py
PY=python scripts/testing/sabotajes/conexiones1.sh 299e0ee8                    # → seis BIEN, rc=0
```

Para el rojo: el mismo árbol con el diff de D (`git show
c1311852:docs/pm/PARA-PM.md`, su bloque ```diff) y el
`test_conexiones1.py` de este diff → `1 failed, 4 passed`, `assert 500 == 400`
en `body-400`.

## Puertas

| Puerta | Resultado |
|---|---|
| `pytest tests/test_conexiones1.py tests/test_cobro_corte1.py`, con el diff | 103 passed, 5 warnings in 79.11s, rc=0 |
| Medidor con el diff | rc=0 |
| Medidor sin diff | rc=4 |
| `sabotajes/conexiones1.sh` | seis BIEN, rc=0 |
| `git apply --check` en árbol limpio | rc=0 |
| chequeo-6 `89d3fa3c..299e0ee8` | producto +0/−0, avisos 0 |

**No corrido:** la suite completa (sólo esos dos archivos), los subagentes
adversariales y `/code-review`. E es sólo arnés y un diff sin commitear; si
D182 dice que entra, esos van con la pieza de producto.

<details><summary>chequeo-6 89d3fa3c..299e0ee8</summary>

```
chequeo-6 89d3fa3c..299e0ee8: avisos para mirar, no un veredicto
producto +0/−0
arnés +31/−21
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
avisos: 0
rc=0
```

</details>
