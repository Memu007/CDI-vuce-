"""GUARDAR-1 contra un Postgres de verdad: SQLite no controla el largo de las
columnas y el error no se ve.

Comprueba, con terceros simulados:
1. que guardar una operación con la posición SIM completa (`84714900100D`,
   12 caracteres) responde 200 y la operación queda con sus ítems;
2. que el historial del cliente guarda una forma que entra (el NCM de 8
   dígitos de la SIM) y que un NCM que ya entraba queda igual;
3. lo mismo al aprender productos (`/catalogo/productos/learn`), que usa el
   mismo historial.
La sugerencia no se pide acá (`/api/ncm/sugerir` puede llamar a Gemini): la
cubre tests/test_guardar1.py.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/guardar1_postgres.py postgresql://cdi@127.0.0.1:55432/<base vacía>
"""
import os
import sys
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_host = urlparse(URL).hostname or ""
if not URL.startswith("postgresql://") or _host not in ("127.0.0.1", "localhost"):
    sys.exit("uso: guardar1_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

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
FALLAS = []


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def sql(consulta, *args):
    with psycopg2.connect(URL) as con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall()


with TestClient(main_mod.app, raise_server_exceptions=False) as c:
    usuario = f"g1_{uuid.uuid4().hex[:8]}"
    r = c.post("/auth/register", json={"username": usuario, "password": "SecureP@ss1",
                                       "email": f"{usuario}@example.com", "name": usuario})
    chequear(r.status_code == 200, f"registro ({r.status_code})")
    r = c.post("/api/clientes", json={"nombre": "Cliente de prueba", "cuit": "30999999995"})
    chequear(r.status_code == 200, f"alta del cliente ({r.status_code} {r.text[:120]})")
    cid = r.json()["cliente"]["id"]

    sim = "84714900100D"
    r = c.post(f"/api/clientes/{cid}/operaciones", json={"items": [
        {"pieza": sim, "ncm": sim, "descripcion": "COMPUTADORA PORTATIL DE PRUEBA", "origen": "CHN",
         "cantidad": 2, "valor_unitario": 100, "peso_unitario": 1.5},
        {"pieza": "8471.30.12", "ncm": "8471.30.12", "descripcion": "TABLETA DE PRUEBA", "origen": "CHN",
         "cantidad": 1, "valor_unitario": 50, "peso_unitario": 0.5},
    ]})
    chequear(r.status_code == 200, f"guardar con la SIM completa responde 200 ({r.status_code} {r.text[:160]})")
    op_id = r.json().get("operation_id") if r.status_code == 200 else None
    piezas = sorted(p for (p,) in sql("select pieza from operation_items where operation_id=%s", op_id)) if op_id else []
    chequear(piezas == ["8471.30.12", sim], f"la operación quedó con sus dos ítems y la SIM completa ({piezas})")

    hist = dict(sql("select descripcion, ncm from client_product_history where client_id=%s", cid))
    chequear(hist.get("COMPUTADORA PORTATIL DE PRUEBA") == "84714900",
             f"el historial guarda el NCM de la SIM ({hist})")
    chequear(hist.get("TABLETA DE PRUEBA") == "8471.30.12", f"un NCM que entra queda igual ({hist})")

    r = c.post(f"/api/clientes/{cid}/catalogo/productos/learn", json={"items": [
        {"ncm": "85171300900X", "descripcion": "TELEFONO DE PRUEBA"}]})
    chequear(r.status_code == 200, f"aprender un producto con la SIM completa responde 200 ({r.status_code} {r.text[:160]})")
    hist = dict(sql("select descripcion, ncm from client_product_history where client_id=%s", cid))
    chequear(hist.get("TELEFONO DE PRUEBA") == "85171300", f"aprender guarda el NCM de la SIM ({hist})")

    # Otros datos del mismo guardado con columnas de largo fijo o que
    # Postgres no acepta: moneda, origen, fecha del cliente, grupo, NUL.
    r = c.post("/api/clientes", json={"nombre": "Cliente sin fecha", "cuit": "30999999995"})
    cid2 = r.json()["cliente"]["id"]
    r = c.post(f"/api/clientes/{cid2}/operaciones", json={
        "currency": "DOLARES", "source": "x" * 80, "comprador_fecha_inic_activ": "2020-01-15T00:00:00",
        "items": [{"pieza": "84714900100D", "descripcion": "COMPU\x00TADORA", "origen": "CHN", "grupo_id": "g1"}]})
    chequear(r.status_code == 200, f"datos largos de la operación no impiden guardarla ({r.status_code} {r.text[:160]})")

    # El historial no puede tirar abajo el guardado: aunque otro dato no
    # entre en su columna, la operación queda guardada.
    import proyecto_maria.services.client_memory as memoria
    forma_real = memoria.ncm_para_historial
    memoria.ncm_para_historial = lambda ncm: str(ncm or "").strip() or None
    try:
        r = c.post(f"/api/clientes/{cid}/operaciones", json={"items": [
            {"pieza": "84714900100D", "ncm": "84714900100D", "descripcion": "MONITOR DE PRUEBA",
             "cantidad": 1, "valor_unitario": 10, "peso_unitario": 1}]})
    finally:
        memoria.ncm_para_historial = forma_real
    op_id = r.json().get("operation_id") if r.status_code == 200 else None
    piezas = [p for (p,) in sql("select pieza from operation_items where operation_id=%s", op_id)] if op_id else []
    chequear(r.status_code == 200 and piezas == ["84714900100D"],
             f"si el historial falla, la operación igual se guarda ({r.status_code}, {piezas})")
    hist = dict(sql("select descripcion, ncm from client_product_history where client_id=%s", cid))
    chequear("MONITOR DE PRUEBA" not in hist, f"y el historial de esa operación no queda a medias ({hist})")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
