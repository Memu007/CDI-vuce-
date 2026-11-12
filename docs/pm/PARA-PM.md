# Dev → PM

Este archivo es mío y vos no lo tocás. Acá te informo.

## CONEXIONES-1 F (sólo arnés y diff revisado): las dos cuentas dan 400 al cortar y 402/429 completas; analyze con el pool lleno da 500 sin dejar nada. Decide la PM: D186, D187

| Qué | SHA |
|---|---|
| Este informe | el commit `docs:` que lo trae |

Base: `35c19be7` (tu merge, HEAD de `PARA-DEV.md`). Producto commiteado:
ninguno. El diff revisado va abajo, completo y sin commitear; `git apply
--check` limpio sobre `35c19be7` en un árbol limpio. Después traje tu `759241ff`
(sólo `NOW.md`); el `apply --check` sobre `759241ff` también da limpio.

## Resultado, en corto

1. **Cuenta impaga y cuenta sin cuota** (punto 1): un caso,
   `test_cuenta_que_no_puede_cargar_y_corta_el_cuerpo`, con `CUENTAS` como
   datos. Con el diff revisado da lo pedido:
   `[('impaga', 400, 402, 0), ('sin cuota', 400, 429, 0)]` (cuenta, cortado,
   completo, conexiones tomadas mientras se espera el cuerpo).
   En `35c19be7` sin diff: `[('impaga', 402, 402, 'sin leer'), ('sin cuota', 429, 429, 1)]`: la impaga contesta 402 sin leer el cuerpo y la sin cuota tiene una conexión tomada mientras espera el cuerpo.
2. **Hallazgo 3, analyze con el pool lleno al guardar** (punto 2): caso
   `test_analyze_con_el_pool_lleno_no_deja_nada_a_medias`. Otra cuenta toma
   las 5 conexiones de un motor propio del caso en dos momentos, como datos
   del mismo caso. analyze sólo escribe un `SystemBackup` (un `add` y un
   `commit`, con `rollback` si falla), así que cuento esos registros.
   - **Al leer el archivo:** contesta **500 «No pudimos procesar tu
     solicitud…»** y quedan **0** respaldos. Liberado el pool, el mismo
     pedido da 200 y deja 1.
   - **Recién después de guardar:** contesta **200** con 1 respaldo; el
     siguiente, 200 y 2. Nunca un 500 con el respaldo ya guardado.
   - Resultado del caso: `[('al leer', 500, 'No pudimos procesar tu
     solicitud', 0, 200, 1), ('al guardar', 200, '', 1, 200, 2)]`.
   - Sin espera fija: el caso llena el pool desde la lectura o desde el
     commit, y el motor corta con `pool_timeout=0.05` (D187).
3. **Suite completa y `e2e_maria.sh` con el diff revisado sin commitear**
   (punto 3): suite «6085 passed, 110 skipped, 3 xfailed, 103 warnings in 1343.27s (0:22:23)», salida 0, ninguna línea FAILED ni ERROR (las 1113 «Task was destroyed» son las de siempre). `e2e_maria.sh`: «E2E MARIA OK: carga, revisión, SIM/DC, agrupación, validación, SBT, descarga y memoria verificadas.», rc=0, con el mismo `main.py` (el e2e no lee `tests/`). **Esto no reemplaza la puerta
   sobre el SHA que entregue en la pieza de producto.**
4. **«Body JSON inválido» en un solo lugar** (punto 4, propuesta para la
   pieza de producto, no corrida):
   - Una dependencia `_leer_json(request)` hace `return await
     request.json()` y, con `except Exception` (cubre `ClientDisconnect` y el
     JSON mal formado), levanta el 400 «Body JSON inválido».
   - La ruta recibe `data=Depends(_leer_json)` y pierde su `try`/`except`:
     unas −3 líneas, y `_leer_cuerpo` se va.
   - **Cambia la firma Python de la ruta** (un parámetro `data` en vez de
     `_cuerpo`); el contrato HTTP no cambia.
   - Costo: el parseo del JSON también queda antes del 402 y del 429. Eso
     entra en lo que mide G.
   - `main.py` tiene el mismo texto en otras tres rutas (8003, 8091, 8104):
     podrían usar la dependencia, pero quedan fuera de esta pieza.

## Decisiones

- **D186. ¿Commit en `require_active_billing` en vez de `_leer_cuerpo`?**
  Es la alternativa que el revisor pidió llevar aparte. Con ella el
  plan se lee, se confirma y se suelta la conexión antes de leer el cuerpo,
  sin dependencia nueva: `main.py` +19/−1 en vez de +26/−1.
  - (a) **Quedarse con el diff revisado** (recomendada). Con la
    alternativa pasan 7 de los 8 casos de `test_conexiones1.py`; el del corte
    da `[('impaga', 402, 402, 'sin leer'), ('sin cuota', 429, 429, 0)]`. Suelta
    la conexión igual (0 tomadas), pero el corte contesta 402/429 y no el 400
    que pide el punto 1, y la impaga contesta sin leer el cuerpo, como hoy.
  - (b) Cambiar a la alternativa en la pieza de producto. Parche aparte,
    abajo, en un bloque `patch` (no `diff`, para que el awk de los comandos
    no lo junte con el revisado).
- **D187. `pool_timeout=0.05` en el caso del pool lleno.** Es cuánto espera
  el motor del caso por una conexión libre antes de rendirse. Con 0 no
  sirve: `asyncio.wait_for(…, 0)` corta aunque haya una conexión libre, y
  el reintento con el pool libre también fallaría. No es una espera fija:
  el caso no duerme, el motor deja de esperar.
  - (a) **Así** (recomendada).
  - (b) Otro valor que digas.
- **D185** decidida (a): el tope de cuerpo va a Emi como riesgo (abajo,
  «Riesgos»).
- Siguen en Emi: **D182** (si el arreglo entra), **D183** (los hunks) y
  **D184** (`test_conexiones1.py` con el commit de pruebas).

## Declarado

- **El 500 de analyze con el pool lleno es nuevo:** sin el commit que suelta
  la conexión al leer el archivo, analyze tiene la suya tomada y guarda
  igual (lo muestra el sabotaje «analyze sin soltar al leer»: `('al leer', 200,
  '', 1, 200, 2)`). Con el diff, en ese momento compite por una conexión como
  cualquier pedido. La cuenta tiene que volver a subir el archivo.
- El 500 deja un ERROR con traza en el log (`logging.exception
  "analyze_client_migration staging failed"`), como cualquier commit que
  falla en esa ruta.
- Con el diff revisado el `refresh` de analyze se va: con
  `expire_on_commit=False` y `batch.id` generado en Python no hace falta, y
  con él la ruta pedía una segunda conexión después del commit. El sabotaje
  «analyze con refresh» lo distingue: `At index 1 diff: ('al guardar', 500,
  'No pudimos procesar tu solicitud', 1, 200, 2) != ('al guardar', 200, '',
  1, 200, 2)` (respaldo guardado y 500).
- **Corrección propia:** la primera versión del caso llenaba el pool sólo al
  leer. Ahí el commit falla antes del `refresh`, así que **no distinguía**
  el sabotaje del refresh, aunque mi borrador decía que sí. Lo vi al correr
  los sabotajes; sumé el momento «al guardar» y ahora se pone rojo.
- `sugerir_ncm` suelta la conexión antes de la IA con `_soltar_conexion`:
  si la base se cayó en ese momento, se registra un `warning` y se sigue con
  lo ya leído. Caso `test_ncm_con_la_base_caida_al_soltarla_sigue_sugiriendo`.
- `test_cobro_corte1.py` exime por identidad de código
  (`quien is main.require_billing_vigente.__code__`) el commit nuevo de
  `require_billing_vigente`: el caso de la base caída al confirmar sigue
  probando el commit de la ruta y no el de la dependencia.
- **Corridas contaminadas, no citadas:** un `conftest.py` viejo, sin la
  fixture `_limitador_apagado`, quedó en un directorio padre de mis
  worktrees descartables y pytest lo cargó como `../conftest.py` en varias
  corridas de esta pieza. Las repetí en un árbol sin ese archivo y cito
  sólo esas. No medí si afectó entregas anteriores.

## Hallazgos de la autorrevisión

| # | Quién (modelo · esfuerzo) | Hallazgo | Qué pasó |
|---|---|---|---|
| 1 | Sonnet · alto | El cuerpo se lee antes del 402/429 y el corte no gasta el límite | D185 (a) y G |
| 2 | Sonnet · alto | El commit de NCM antes de la IA estaba fuera de un `try`: base caída = 500 | arreglado: `_soltar_conexion` y su caso; rojo `assert (500, []) == (200, ['8471.30.12'])` |
| 3 | Sonnet · alto | `upload_excel_v2` con `cliente_id` retiene la conexión mientras lee (`main.py` 9195→9210), fuera del diff | riesgo |
| 4 | Sonnet · alto | Ningún caso distinguía sacar el `refresh` de analyze | lo distingue el momento «al guardar» del caso del pool lleno (sabotaje «analyze con refresh»); la primera versión del caso no lo distinguía |
| 5 | Sonnet · alto | `RUTAS` armada a mano: sin el commit de cobro sólo cae `process_pdf` | riesgo |
| 6 | `/code-review high` | `main.py` 10466: commit de NCM sin `try` | el mismo que 2, arreglado |
| 7 | `/code-review high` | `test_conexiones1.py` 54: `tomadas()` recorre `duenas` desde otro hilo | refutado: bajo pytest no hay tareas de registro (`main.py` 1968-1975); la foto con `list()` va con la pieza de producto |
| 8 | `/code-review high` | `main.py` 3753: un corte del cuerpo en `_json_guardable` (`save_client_operation`) da 500 | riesgo, fuera de la pieza; propuesta: un lector compartido (punto 4) |
| 9 | `/code-review high` | `main.py` 3767: cuerpo leído antes del 402 y del 429 | el mismo que 1: D185 (a) y G |
| 10 | `/code-review high` | `main.py` 2309: commit incondicional en `require_billing_vigente` para 8 rutas, una ida y vuelta más a la base | riesgo; D186 lo baja a una ruta |
| 11 | `/code-review high` | `main.py` 3759: «Body JSON inválido» repetido | punto 4 |
| 12 | `/code-review high` | `test_cobro_corte1.py` 832: la exención del commit nuevo iba por nombre de archivo | aplicada antes de la suite: identidad de código. Con la exención vieja: «4 failed, 5 passed, 89 deselected»; su premisa «pasa vacío» era falsa |
| 13 | `/code-review high` | `test_conexiones1.py` 229: `otras` y `motor` sin cerrar si algo falla dentro del `with` | riesgo bajo; `try/finally` en la pieza de producto |
| 14 | `/code-review high` | `test_conexiones1.py` 224: `pool_timeout=0.05` como espera fija, con carrera | carrera refutada; el valor es D187 |
| 15 | `/code-review high` | `test_conexiones1.py` 169: `cortes.pop(0)` falla vacío si cambia el orden de pedidos | riesgo bajo |

## Sabotajes (uno por motivo, sobre el diff revisado)

Un script, `sabotajes_f.py` (abajo, en «Comandos copiables»): revierte una
parte del diff por vez en `main.py`, corre el caso con `-k` y deja `main.py`
como estaba. Corrida: los 9 en rojo, «sabotajes sin rojo: ninguno», salida 0.

| Sabotaje | Caso (`-k`) | Rojo, copiado de la salida |
|---|---|---|
| sin `except` del corte | `corta_el_cuerpo` | `At index 0 diff: ('impaga', 500, 402, 0) != ('impaga', 400, 402, 0)` |
| cuerpo leído después del plan | `corta_el_cuerpo` | `At index 0 diff: ('impaga', 402, 402, 'sin leer') != ('impaga', 400, 402, 0)` |
| manual sin límite | `corta_el_cuerpo` | `At index 1 diff: ('sin cuota', 400, 404, 0) != ('sin cuota', 400, 429, 0)` |
| manual sin leer el cuerpo antes | `espera and 404` | `assert ([1] and 1 == 0)` |
| analyze sin soltar al leer | `pool_lleno` | `At index 0 diff: ('al leer', 200, '', 1, 200, 2) != ('al leer', 500, 'No pudimos procesar tu solicitud', 0, 200, 1)` |
| analyze con `refresh` | `pool_lleno` | `At index 1 diff: ('al guardar', 500, 'No pudimos procesar tu solicitud', 1, 200, 2) != ('al guardar', 200, '', 1, 200, 2)` |
| ncm sin `try` al soltar | `base_caida` | `assert (500, []) == (200, ['8471.30.12'])` |
| ncm sin soltar | `espera and ncm` | `assert ([1] and 1 == 0)` |
| cobro sin commit | `espera` | `assert ([1] and 1 == 0)` · «1 failed, 4 passed, 3 deselected» |

`[1]` es la lista de conexiones tomadas mientras la ruta espera: con el
sabotaje queda una.

## Riesgos

- **Tope de cuerpo (D185 (a), para Emi):** con el diff, a una cuenta sin
  pago o pasada de cuota se le lee el cuerpo entero antes del 402/429. Lo
  mide G.
- `upload_excel_v2` con `cliente_id` sigue reteniendo la conexión mientras
  lee el archivo. Fuera del diff.
- `_soltar_conexion` registra la excepción entera en el `warning`.
- Si `_vencer_y_guardar` hace rollback, el commit nuevo de
  `require_billing_vigente` corre sobre una sesión ya cerrada; no lo medí.
- Un corte del cuerpo en `save_client_operation` (`_json_guardable`) da 500
  (hallazgo 8). Fuera de la pieza.
- Una ida y vuelta más a la base por pedido en las rutas con commit nuevo.
- `RUTAS` está armada a mano: una ruta lenta nueva no entra sola.
- El filtro de `tomadas` que descarta la conexión de la propia prueba no
  tiene caso que lo distinga.

## Diff revisado (completo, sin commitear)

Producto: `main.py` +26/−1. Pruebas: `test_cobro_corte1.py` +2/−1 y
`test_conexiones1.py` (nuevo, 260 líneas).

Por qué +25 netas (§6, más de 20): son cuatro lugares que retienen la
conexión, cada uno con su caso y su sabotaje: el commit de
`require_billing_vigente`, la lectura del cuerpo antes del plan
(`_leer_cuerpo`, 400 al cortar), el commit de analyze antes de leer el
archivo (sin el `refresh`) y `_soltar_conexion` antes de la IA de NCM. Más
de la mitad son comentarios y el `try`/`except` de los dos helpers. D186
(b) lo baja a +19/−1.

```diff
diff --git a/proyecto_maria/main.py b/proyecto_maria/main.py
index 52fe473f..f5967be0 100644
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
@@ -7211,7 +7227,6 @@ async def analyze_client_migration(
     db.add(batch)
     try:
         await db.commit()
-        await db.refresh(batch)
     except Exception as exc:
         await db.rollback()
         logging.exception("analyze_client_migration staging failed")
@@ -10328,6 +10343,15 @@ async def propuesta_de_sufijos(data: dict, user=Depends(get_current_user)):
     return {"fuente": sufijos_arca.fuente(tabla), "sin_tabla": not tabla, "items": salida}
 
 
+async def _soltar_conexion(db: AsyncSession) -> None:
+    # Suelta la conexión antes de esperar a un servicio lento. Si la base se
+    # cayó, lo ya leído alcanza: la ruta sigue sin cortar.
+    try:
+        await db.commit()
+    except Exception as err:
+        logging.warning("db release before slow call failed: %s", err)
+
+
 @app.post("/api/ncm/sugerir")
 async def sugerir_ncm(
     data: dict,
@@ -10448,6 +10472,7 @@ async def sugerir_ncm(
         # (RENDIMIENTO-1). Si no contesta a tiempo, se sigue sin sus sugerencias.
         import asyncio
         limite = _segundos_de_entorno("NCM_GEMINI_TIMEOUT_S", 30.0)
+        await _soltar_conexion(db)
         try:
             de_gemini = await asyncio.wait_for(
                 asyncio.to_thread(_suggest_ncm_with_gemini, descripcion, 5 - len(sugerencias)),
diff --git a/tests/test_cobro_corte1.py b/tests/test_cobro_corte1.py
index cfb81a79..8f35b604 100644
--- a/tests/test_cobro_corte1.py
+++ b/tests/test_cobro_corte1.py
@@ -828,7 +828,8 @@ _confirmar = main.AsyncSession.commit
 
 async def _commit_que_falla(self):
     # La autenticación confirma antes de la ruta: falla sólo el de main.py.
-    if sys._getframe(1).f_code.co_filename != main.__file__:
+    quien = sys._getframe(1).f_code
+    if quien.co_filename != main.__file__ or quien is main.require_billing_vigente.__code__:
         return await _confirmar(self)
     raise RuntimeError("la base se cayó al confirmar")
 
diff --git a/tests/test_conexiones1.py b/tests/test_conexiones1.py
new file mode 100644
index 00000000..99caa2d3
--- /dev/null
+++ b/tests/test_conexiones1.py
@@ -0,0 +1,260 @@
+"""Las rutas lentas de RUTAS no retienen una conexión a la base mientras esperan.
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
+import aiosqlite
+import pytest
+from fastapi.testclient import TestClient
+from pypdf import PdfWriter
+from sqlalchemy import event, func, select, update
+from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
+from sqlalchemy.pool import AsyncAdaptedQueuePool
+from starlette.requests import Request
+
+from proyecto_maria import main
+from proyecto_maria.core import rate_limit
+from proyecto_maria.database import connection as _conn
+from proyecto_maria.database.models import SystemBackup, User
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
+    monkeypatch.setattr(rate_limit.limiter, "enabled", False)
+    # Un 500 vuelve como respuesta y no como excepción del cliente de prueba.
+    c = TestClient(main.app, raise_server_exceptions=False)
+    nombre = f"conex1_{uuid.uuid4().hex[:10]}"
+    r = c.post("/auth/register", json={"username": nombre, "password": CLAVE, "name": nombre,
+                                       "email": f"{nombre}@cdi.test"})
+    assert r.status_code in (200, 201), r.text
+    r = c.post("/auth/login", json={"username": nombre, "password": CLAVE})
+    assert r.status_code == 200, r.text
+    return c, nombre
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
+    c, _ = _sesion(monkeypatch)
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
+
+
+def _impaga(nombre):
+    async def guardar():
+        async with _conn.AsyncSessionLocal() as db:
+            await db.execute(update(User).where(User.username == nombre).values(billing_status="past_due"))
+            await db.commit()
+    asyncio.run(guardar())
+
+
+def _sin_cuota(monkeypatch):
+    def gastar(c):
+        assert c.post("/api/operations/manual", json=MANUAL).status_code == 404
+    monkeypatch.setattr(rate_limit.settings, "rate_limit_basic", "1/minute")
+    monkeypatch.setattr(rate_limit.limiter, "enabled", True)
+    return gastar
+
+
+MANUAL = {"client_id": "999999999", "items": [{"descripcion": "notebook", "cantidad": 1, "valor_unitario": 10}]}
+# (cuenta, cómo queda sin poder cargar, código con el cuerpo completo)
+CUENTAS = [
+    ("impaga", lambda nombre, _mp: _impaga(nombre), 402),
+    ("sin cuota", lambda _nombre, mp: _sin_cuota(mp), 429),
+]
+
+
+def test_cuenta_que_no_puede_cargar_y_corta_el_cuerpo(monkeypatch, tomadas):
+    """El corte se contesta antes que el plan o la cuota, sin tomar conexión."""
+    leer, vieron = Request.body, []
+    for cuenta, preparar, codigo in CUENTAS:
+        with monkeypatch.context() as mp:
+            c, nombre = _sesion(mp)
+            gastar = preparar(nombre, mp)
+            vistas = []
+            # Un corte por pedido, en orden: gastar la cuota, el cortado, el completo.
+            cortes = ([False] if gastar else []) + [True, False]
+
+            async def frenar(self):
+                if not hasattr(self, "_body"):
+                    vistas.append(tomadas())
+                    if cortes.pop(0):
+                        _cortar_a_mitad(self)
+                return await leer(self)
+            mp.setattr(Request, "body", frenar)
+            try:
+                with c:
+                    if gastar:
+                        gastar(c)
+                    cortado = c.post("/api/operations/manual", json=MANUAL)
+                    completo = c.post("/api/operations/manual", json=MANUAL)
+            finally:
+                rate_limit.limiter.reset()
+        vieron.append((cuenta, cortado.status_code, completo.status_code, max(vistas, default="sin leer")))
+    assert vieron == [(cuenta, 400, codigo, 0) for cuenta, _p, codigo in CUENTAS]
+
+
+def _respaldos(nombre):
+    async def contar():
+        async with AsyncSession(_conn.engine) as db:
+            return await db.scalar(select(func.count()).select_from(SystemBackup)
+                                   .where(SystemBackup.owner_username == nombre))
+    return asyncio.run(contar())
+
+
+def test_analyze_con_el_pool_lleno_no_deja_nada_a_medias(monkeypatch):
+    """Si otra cuenta toma todas las conexiones mientras se lee el Excel, el
+    respaldo no se guarda y contesta 500; si las toma recién después de
+    guardarlo, contesta 200. Nunca un 500 con el respaldo guardado."""
+    c, nombre = _sesion(monkeypatch)
+    leer, guardar = migration_service.analyze_migration_file_async, AsyncSession.commit
+    archivo = {"file": ("clientes.csv", b"cuit,nombre\n20123456786,Cliente Uno\n", "text/csv")}
+    estado = {}
+
+    async def llenar(momento):
+        if estado["momento"] == momento and not estado["otras"]:
+            motor = estado["motor"]
+            while motor.pool.checkedout() < motor.pool.size():
+                estado["otras"].append(await motor.connect())
+
+    async def leer_y_llenar(*a, **k):
+        estado["leido"] = True
+        await llenar("al leer")
+        return await leer(*a, **k)
+
+    async def guardar_y_llenar(self, *a, **k):
+        await guardar(self, *a, **k)
+        if estado["leido"]:
+            await llenar("al guardar")
+
+    monkeypatch.setattr(migration_service, "analyze_migration_file_async", leer_y_llenar)
+    monkeypatch.setattr(AsyncSession, "commit", guardar_y_llenar)
+    vieron = []
+    for momento in ("al leer", "al guardar"):
+        # pool_timeout=0 no sirve: wait_for(…, 0) corta aunque haya una conexión libre.
+        motor = create_async_engine(_conn.DATABASE_URL, poolclass=AsyncAdaptedQueuePool,
+                                    pool_size=5, max_overflow=0, pool_timeout=0.05)
+        estado.update(momento=momento, motor=motor, otras=[], leido=False)
+        antes = _respaldos(nombre)
+        _conn.AsyncSessionLocal.configure(bind=motor)
+        try:
+            with c:
+                lleno = c.post("/api/migrations/analyze", files=archivo)
+                quedaron = _respaldos(nombre) - antes
+                for otra in estado["otras"]:
+                    c.portal.call(otra.close)
+                libre = c.post("/api/migrations/analyze", files=archivo)
+                c.portal.call(motor.dispose)
+        finally:
+            _conn.AsyncSessionLocal.configure(bind=_conn.engine)
+        vieron.append((momento, lleno.status_code, lleno.json().get("detail", "").split(".")[0],
+                       quedaron, libre.status_code, _respaldos(nombre) - antes))
+    assert vieron == [("al leer", 500, "No pudimos procesar tu solicitud", 0, 200, 1),
+                      ("al guardar", 200, "", 1, 200, 2)]
+
+
+def test_ncm_con_la_base_caida_al_soltarla_sigue_sugiriendo(monkeypatch):
+    """Si la conexión se cae después de la última lectura, soltarla antes de
+    la IA no corta el pedido: se sugiere con lo que ya se leyó."""
+    c, _ = _sesion(monkeypatch)
+    mirar = main._looks_like_ncm_code_query
+
+    def caer_y_mirar(descripcion):
+        async def caida(*a, **k):
+            raise RuntimeError("conexión caída")
+        monkeypatch.setattr(aiosqlite.Connection, "commit", caida)
+        monkeypatch.setattr(aiosqlite.Connection, "rollback", caida)
+        return mirar(descripcion)
+    monkeypatch.setattr(main, "_looks_like_ncm_code_query", caer_y_mirar)
+    monkeypatch.setattr(main, "_suggest_ncm_with_gemini",
+                        lambda *a, **k: [{"ncm": "8471.30.12", "desc": "notebook", "source": "ia"}])
+    r = c.post("/api/ncm/sugerir", json={"descripcion": "notebook de 14 pulgadas"})
+    assert (r.status_code, [s["ncm"] for s in r.json().get("sugerencias", [])]) == (200, ["8471.30.12"])
```

## Alternativa D186 (parche aparte, contra `35c19be7`)

```patch
diff --git a/proyecto_maria/main.py b/proyecto_maria/main.py
index 52fe473f..50b4bb6e 100644
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
 
 
@@ -2325,6 +2328,9 @@ async def require_active_billing(
     ok, reason = billing_service.can_create_operation(entidad)
     if not ok:
         raise HTTPException(status_code=402, detail=_detalle_402(entidad, reason))
+    # Termina la transacción de lectura: si no, la conexión queda tomada
+    # mientras la ruta lee el cuerpo.
+    await db.commit()
     return db_user
 
 
@@ -7172,6 +7178,8 @@ async def analyze_client_migration(
         )
     )
     existing_clients = existing_result.scalars().all()
+    # Suelta la conexión mientras se lee el archivo; los clientes quedan cargados.
+    await db.commit()
     mapper = GeminiMigrationHeaderMapper(username=user["username"])
     try:
         # Con tiempo máximo, como leer un PDF (EXCEL-1).
@@ -7211,7 +7219,6 @@ async def analyze_client_migration(
     db.add(batch)
     try:
         await db.commit()
-        await db.refresh(batch)
     except Exception as exc:
         await db.rollback()
         logging.exception("analyze_client_migration staging failed")
@@ -10328,6 +10335,15 @@ async def propuesta_de_sufijos(data: dict, user=Depends(get_current_user)):
     return {"fuente": sufijos_arca.fuente(tabla), "sin_tabla": not tabla, "items": salida}
 
 
+async def _soltar_conexion(db: AsyncSession) -> None:
+    # Suelta la conexión antes de esperar a un servicio lento. Si la base se
+    # cayó, lo ya leído alcanza: la ruta sigue sin cortar.
+    try:
+        await db.commit()
+    except Exception as err:
+        logging.warning("db release before slow call failed: %s", err)
+
+
 @app.post("/api/ncm/sugerir")
 async def sugerir_ncm(
     data: dict,
@@ -10448,6 +10464,7 @@ async def sugerir_ncm(
         # (RENDIMIENTO-1). Si no contesta a tiempo, se sigue sin sus sugerencias.
         import asyncio
         limite = _segundos_de_entorno("NCM_GEMINI_TIMEOUT_S", 30.0)
+        await _soltar_conexion(db)
         try:
             de_gemini = await asyncio.wait_for(
                 asyncio.to_thread(_suggest_ncm_with_gemini, descripcion, 5 - len(sugerencias)),
diff --git a/tests/test_cobro_corte1.py b/tests/test_cobro_corte1.py
index cfb81a79..8f35b604 100644
--- a/tests/test_cobro_corte1.py
+++ b/tests/test_cobro_corte1.py
@@ -828,7 +828,8 @@ _confirmar = main.AsyncSession.commit
 
 async def _commit_que_falla(self):
     # La autenticación confirma antes de la ruta: falla sólo el de main.py.
-    if sys._getframe(1).f_code.co_filename != main.__file__:
+    quien = sys._getframe(1).f_code
+    if quien.co_filename != main.__file__ or quien is main.require_billing_vigente.__code__:
         return await _confirmar(self)
     raise RuntimeError("la base se cayó al confirmar")
 
```

## Comandos copiables

Desde la raíz del repo, con el entorno virtual de pytest; el `export` es el entorno con el que los probé. Los tres
archivos salen del informe en la rama: el diff revisado (bloque `diff`), la
alternativa (bloque `patch`) y el script de sabotajes (bloque `python`).

```bash
git fetch origin claude/dev-tecnica
P="git show origin/claude/dev-tecnica:docs/pm/PARA-PM.md"
$P | awk '/^```diff$/{f=1;next} /^```$/{f=0} f' > /tmp/f.diff
$P | awk '/^```patch$/{f=1;next} /^```$/{f=0} f' > /tmp/falt.diff
$P | awk '/^```python$/{f=1;next} /^```$/{f=0} f' > /tmp/sabotajes_f.py
git worktree add --detach /tmp/f 35c19be7 && cd /tmp/f
export ENVIRONMENT=testing GEMINI_API_KEY= DOLARAPI_BASE=http://127.0.0.1:9/v1/dolares DATABASE_URL=sqlite+aiosqlite:///./test.db VUCE_MODE=fake TARIFAR_MODE=fake AFIP_MODE=fake EMAIL_VERIFICATION_REQUIRED=false
# rojo: la base con las pruebas de F
git apply --include='tests/*' /tmp/f.diff
python -m pytest -q --no-cov tests/test_conexiones1.py -k corta_el_cuerpo   # → 1 failed: ('impaga', 402, 402, 'sin leer') != ('impaga', 400, 402, 0)
git checkout -- . && rm tests/test_conexiones1.py
# verde: el diff revisado
git apply --check /tmp/f.diff && echo limpio && git apply /tmp/f.diff   # → limpio
python -m pytest -q --no-cov tests/test_conexiones1.py tests/test_cobro_corte1.py   # → 106 passed
python /tmp/sabotajes_f.py   # → nueve «ROJO», «sabotajes sin rojo: ninguno», rc=0
# alternativa D186
git checkout -- . && rm tests/test_conexiones1.py
git apply /tmp/falt.diff && git apply --include=tests/test_conexiones1.py /tmp/f.diff
python -m pytest -q --no-cov tests/test_conexiones1.py   # → 1 failed, 7 passed: test_cuenta_que_no_puede_cargar_y_corta_el_cuerpo
git checkout -- . && rm tests/test_conexiones1.py
```

`sabotajes_f.py` (se corre desde la raíz del árbol con el diff aplicado):

```python
"""Sabotajes de CONEXIONES-1 F. Se corre desde la raíz de un árbol
descartable con el diff revisado aplicado: cada sabotaje revierte una parte
de main.py, corre el caso que tiene que ponerse rojo y al final deja main.py
como estaba."""
import os, subprocess, sys

WT = os.getcwd()
MAIN = os.path.join(WT, "proyecto_maria", "main.py")
ORIGINAL = open(MAIN, encoding="utf-8").read()

LEER = ('    try:\n        await request.body()\n    except ClientDisconnect:\n'
        '        raise HTTPException(status_code=400, detail="Body JSON inválido")\n')
SUELTA = ("    # Suelta la conexión mientras se lee el archivo; los clientes quedan cargados.\n"
          "    await db.commit()\n")
COBRO = ("        raise HTTPException(status_code=402, detail=_detalle_402(entidad))\n"
         "    # Termina la transacción de lectura: si no, la conexión queda tomada\n"
         "    # mientras el endpoint espera a la IA o a la lectura del PDF.\n"
         "    await db.commit()\n")
SOLTAR = ('    try:\n        await db.commit()\n    except Exception as err:\n'
          '        logging.warning("db release before slow call failed: %s", err)\n')
CUERPO = "    _cuerpo=Depends(_leer_cuerpo),\n"
BILLING = "    db_user: User = Depends(require_active_billing),\n):"

# (nombre, [(viejo, nuevo)], selección -k, texto que tiene que aparecer en el rojo)
SABOTAJES = [
    ("sin except del corte", [(LEER, "    await request.body()\n")],
     "corta_el_cuerpo", "500"),
    ("cuerpo leído después del plan", [(CUERPO, ""), (BILLING, BILLING.replace("\n):", "\n" + CUERPO + "):"))],
     "corta_el_cuerpo", "'sin leer'"),
    ("manual sin límite", [('@app.post("/api/operations/manual")\n@limiter.limit(get_dynamic_rate_limit)\n',
                            '@app.post("/api/operations/manual")\n')],
     "corta_el_cuerpo", "404"),
    ("manual sin leer el cuerpo antes", [(CUERPO, "")], "espera and 404", "assert"),
    ("analyze sin soltar al leer", [(SUELTA, "")], "pool_lleno", "('al leer', 200, '', 1, 200, 2)"),
    ("analyze con refresh", [("    db.add(batch)\n    try:\n        await db.commit()\n    except Exception as exc:\n",
                              "    db.add(batch)\n    try:\n        await db.commit()\n        await db.refresh(batch)\n"
                              "    except Exception as exc:\n")],
     "pool_lleno", "('al guardar', 500, 'No pudimos procesar tu solicitud', 1"),
    ("ncm sin try al soltar", [(SOLTAR, "    await db.commit()\n")], "base_caida", "(500, [])"),
    ("ncm sin soltar", [("        await _soltar_conexion(db)\n", "")], "espera and ncm", "assert"),
    ("cobro sin commit", [(COBRO, COBRO.split("    # Termina")[0])], "espera", "assert"),
]


def correr(nombre, cambios, sel, esperado):
    texto = ORIGINAL
    for viejo, nuevo in cambios:
        n = texto.count(viejo)
        assert n == 1, (nombre, n, viejo[:60])
        texto = texto.replace(viejo, nuevo)
    open(MAIN, "w", encoding="utf-8").write(texto)
    db = os.path.join(WT, "test.db")
    if os.path.exists(db):
        os.remove(db)
    env = dict(os.environ, ENVIRONMENT="testing", GEMINI_API_KEY="", DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
               DATABASE_URL="sqlite+aiosqlite:///./test.db", VUCE_MODE="fake", TARIFAR_MODE="fake",
               AFIP_MODE="fake", EMAIL_VERIFICATION_REQUIRED="false")
    r = subprocess.run(["timeout", "600", sys.executable, "-m", "pytest", "-q", "--no-cov", "--timeout=120",
                        "-p", "no:cacheprovider", "tests/test_conexiones1.py", "-k", sel],
                       cwd=WT, env=env, capture_output=True, text=True)
    salida = r.stdout + r.stderr
    rojo = r.returncode == 1 and esperado in salida
    print(f"== {nombre} · -k '{sel}' · rc={r.returncode} · {'ROJO' if rojo else 'NO DISTINGUE'}")
    for linea in salida.splitlines():
        if linea.startswith("E   ") and ("assert" in linea or "At index" in linea) or " passed" in linea or " failed" in linea:
            print("   ", linea[:220])
    return rojo


if __name__ == "__main__":
    elegidos = [s for s in SABOTAJES if len(sys.argv) < 2 or s[0] in sys.argv[1:]]
    try:
        malos = [s[0] for s in elegidos if not correr(*s)]
    finally:
        open(MAIN, "w", encoding="utf-8").write(ORIGINAL)
    print("sabotajes sin rojo:", malos or "ninguno")
    sys.exit(2 if malos else 0)
```

## Puertas

Todas con el diff revisado aplicado y sin commitear sobre `35c19be7`.

| Puerta | Resultado |
|---|---|
| Suite completa (`DOLARAPI_BASE` local, `ENVIRONMENT=testing`, `GEMINI_API_KEY` vacía) | 6085 passed, 110 skipped, 3 xfailed, 103 warnings in 1343.27s (0:22:23) · salida 0 |
| `e2e_maria.sh` | E2E MARIA OK · rc=0 |
| `test_conexiones1.py` + `test_cobro_corte1.py` | 106 passed |
| Sabotajes (`sabotajes_f.py`) | 9 ROJO · «sabotajes sin rojo: ninguno» · rc=0 |
| `git apply --check` sobre `35c19be7` y sobre `759241ff` | limpio |
| Comandos copiables, probados tal como están en un árbol limpio | dieron lo que dice cada `→` |
| chequeo-6 | 1 AVISO (25 líneas netas de producto, explicado arriba) |

**No corrido:** la puerta sobre un SHA de producto (no hay commit de
producto en F); smoke, ataques y arneses de Postgres. **La suite y el e2e de
acá no reemplazan la puerta sobre el SHA que entregue en la pieza de
producto.**

<details><summary>chequeo-6 35c19be7 con el diff revisado commiteado en un árbol descartable</summary>

```
chequeo-6 35c19be7..cdc64f4f5bc29d8a63014afeac4eed6accb4f1c1: avisos para mirar, no un veredicto
producto +26/−1
  AVISO producto suma 25 líneas netas: el informe dice por qué (§6: más de 20)
arnés +262/−1
historia (grep de §6, sin líneas movidas): vacío
archivos de producto:
  proyecto_maria/main.py: 12270 → 12295
avisos: 1
```

</details>
