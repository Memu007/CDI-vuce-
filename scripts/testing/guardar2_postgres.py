"""GUARDAR-2 (D32 b) contra un Postgres de verdad.

En Postgres el historial del cliente guarda el NCM de 8 dígitos de la SIM
(GUARDAR-1). Comprueba, con terceros simulados (Gemini apagado), que con la
SIM completa en el catálogo del proveedor:
1. el autorrelleno (`/api/catalog/lookup`) trae la SIM del proveedor;
2. `/api/ncm/sugerir` la trae primero;
3. con otra NCM en el proveedor, queda la del cliente;
4. si la consulta al catálogo del proveedor falla en la base, la del cliente
   no se pierde;
5. el catálogo del proveedor de otro despachante no cambia la SIM, y un
   client_id ajeno no trae su historial.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/guardar2_postgres.py postgresql://cdi@127.0.0.1:55432/<base vacía>
"""
import os
import sys
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_host = urlparse(URL).hostname or ""
if not URL.startswith("postgresql://") or _host not in ("127.0.0.1", "localhost"):
    sys.exit("uso: guardar2_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

os.environ.update(
    DATABASE_URL=URL, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import psycopg2  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import proyecto_maria.main as main_mod  # noqa: E402
from proyecto_maria.core.rate_limit import limiter  # noqa: E402

limiter.enabled = False
main_mod._suggest_ncm_with_gemini = lambda *a, **k: []
FALLAS = []
SIM = "84714900100D"


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def sql(consulta, *args):
    with psycopg2.connect(URL) as con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall()


with TestClient(main_mod.app, raise_server_exceptions=False) as c:
    usuario = f"g2_{uuid.uuid4().hex[:8]}"
    r = c.post("/auth/register", json={"username": usuario, "password": "SecureP@ss1",
                                       "email": f"{usuario}@example.com", "name": usuario})
    chequear(r.status_code == 200, f"registro ({r.status_code})")

    def caso(ncm_proveedor):
        proveedor = f"Proveedor {uuid.uuid4().hex[:6]}"
        r = c.post("/api/clientes", json={"nombre": "Cliente de prueba", "cuit": "30999999995"})
        cid = r.json()["cliente"]["id"]
        r = c.post(f"/api/clientes/{cid}/operaciones", json={"items": [
            {"pieza": SIM, "ncm": SIM, "descripcion": "COMPUTADORA PORTATIL", "origen": "CHN"}]})
        chequear(r.status_code == 200, f"guardar la operación ({r.status_code})")
        hist = dict(sql("select descripcion, ncm from client_product_history where client_id=%s", cid))
        chequear(hist == {"COMPUTADORA PORTATIL": "84714900"}, f"el historial tiene los 8 dígitos ({hist})")
        clave = proveedor.lower().replace(" ", "_")
        r = c.post(f"/api/catalog/{clave}/productos", json={
            "vendor_name": proveedor, "productos": [{"descripcion": "COMPUTADORA PORTATIL", "ncm": ncm_proveedor}]})
        chequear(r.status_code == 200, f"catálogo del proveedor con {ncm_proveedor} ({r.status_code} {r.text[:120]})")
        r = c.post("/api/catalog/lookup", json={"items": [{"descripcion": "COMPUTADORA PORTATIL"}],
                                                "vendor_name": proveedor, "client_id": cid})
        item = r.json()["items"][0] if r.status_code == 200 else {}
        r = c.post("/api/ncm/sugerir", json={"descripcion": "COMPUTADORA PORTATIL",
                                             "client_id": cid, "vendor_name": proveedor})
        sug = [(s["source"], s["ncm"]) for s in r.json().get("sugerencias", [])] if r.status_code == 200 else []
        return (item.get("source"), item.get("ncm")), sug

    autorrelleno, sug = caso(SIM)
    chequear(autorrelleno == ("cliente", SIM), f"el autorrelleno trae la SIM del proveedor ({autorrelleno})")
    chequear(sug[:1] == [("historial", SIM)], f"la sugerencia trae la SIM del proveedor primero ({sug})")

    autorrelleno, sug = caso("84713012100K")
    chequear(autorrelleno == ("cliente", "84714900"), f"con otra NCM en el proveedor queda la del cliente ({autorrelleno})")
    chequear([n for _, n in sug][:2] == ["84714900", "84713012100K"], f"y la sugerencia trae las dos ({sug})")

    # Por dueño: otro despachante, con su sesión, tiene la SIM en su catálogo
    # de un proveedor que el primero no cargó. Mismo cliente HTTP (un solo
    # bucle para el pool de la base): se cambia la cookie de sesión.
    sesion1 = dict(c.cookies)

    def como(sesion):
        c.cookies.clear()
        c.cookies.update(sesion)
        return c

    c.cookies.clear()
    usuario2 = f"g2o_{uuid.uuid4().hex[:8]}"
    r = c.post("/auth/register", json={"username": usuario2, "password": "SecureP@ss1",
                                       "email": f"{usuario2}@example.com", "name": usuario2})
    chequear(r.status_code == 200, f"registro del otro despachante ({r.status_code})")
    sesion2 = dict(c.cookies)
    proveedor = f"Proveedor {uuid.uuid4().hex[:6]}"
    r = como(sesion2).post(f"/api/catalog/{proveedor.lower().replace(' ', '_')}/productos", json={
        "vendor_name": proveedor, "productos": [{"descripcion": "COMPUTADORA PORTATIL", "ncm": SIM}]})
    chequear(r.status_code == 200, f"catálogo del otro despachante ({r.status_code})")
    r = como(sesion1).post("/api/clientes", json={"nombre": "Cliente de prueba", "cuit": "30999999995"})
    cid = r.json()["cliente"]["id"]
    c.post(f"/api/clientes/{cid}/operaciones", json={"items": [{"pieza": SIM, "descripcion": "COMPUTADORA PORTATIL"}]})

    def pedir(quien):
        r = quien.post("/api/catalog/lookup", json={"items": [{"descripcion": "COMPUTADORA PORTATIL"}],
                                                    "vendor_name": proveedor, "client_id": cid})
        item = r.json()["items"][0] if r.status_code == 200 else {}
        r = quien.post("/api/ncm/sugerir", json={"descripcion": "COMPUTADORA PORTATIL",
                                                 "client_id": cid, "vendor_name": proveedor})
        sug = [(s["source"], s["ncm"]) for s in r.json().get("sugerencias", [])] if r.status_code == 200 else []
        return (item.get("source"), item.get("ncm")), sug

    autorrelleno, sug = pedir(como(sesion1))
    chequear(autorrelleno == ("cliente", "84714900") and sug == [("historial", "84714900")],
             f"el catálogo de otro despachante no cambia la SIM ({autorrelleno} {sug})")
    autorrelleno, sug = pedir(como(sesion2))
    chequear(autorrelleno == ("proveedor", SIM) and sug == [("proveedor", SIM)],
             f"el historial de un cliente ajeno no se usa ({autorrelleno} {sug})")
    como(sesion1)

    # Si la consulta al catálogo del proveedor falla en la base, la sugerencia
    # del cliente no se pierde (en Postgres la transacción queda abortada).
    from sqlalchemy import text as sa_text
    from proyecto_maria.core import catalog_service as catalog_svc
    match_real = catalog_svc.match_items

    async def _match_que_falla(db, *a, **k):
        await db.execute(sa_text("select * from tabla_que_no_existe"))

    r = c.post("/api/clientes", json={"nombre": "Cliente de prueba", "cuit": "30999999995"})
    cid = r.json()["cliente"]["id"]
    c.post(f"/api/clientes/{cid}/operaciones", json={"items": [{"pieza": SIM, "descripcion": "COMPUTADORA PORTATIL"}]})
    catalog_svc.match_items = _match_que_falla
    try:
        r = c.post("/api/ncm/sugerir", json={"descripcion": "COMPUTADORA PORTATIL",
                                             "client_id": cid, "vendor_name": "Proveedor roto"})
    finally:
        catalog_svc.match_items = match_real
    sug = [(s["source"], s["ncm"]) for s in r.json().get("sugerencias", [])] if r.status_code == 200 else []
    chequear(sug == [("historial", "84714900")], f"si falla el catálogo del proveedor, queda la del cliente ({r.status_code} {sug})")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
