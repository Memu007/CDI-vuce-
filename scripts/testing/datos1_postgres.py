"""DATOS-1 (D5, D32 (a)) contra un Postgres de verdad: ahí la clave foránea de
`public_quotes` hacía fallar con 500 el borrado de un cliente que tenía un
presupuesto compartido. SQLite no la hace cumplir, así que tests/ no lo ve.

Comprueba:
1. el dueño borra un cliente con presupuesto compartido: 200, el cliente, sus
   operaciones y sus presupuestos desaparecen y el link da 404;
2. los presupuestos de otro cliente del mismo dueño y de otro dueño siguen
   andando;
3. otro dueño no puede borrarlo (404) y el presupuesto sigue andando;
4. un cliente sin presupuesto se sigue borrando;
5. si el borrado falla a mitad, no se borra nada (ni cliente ni presupuesto);
6. una operación guardada en otro cliente pierde su link; si ese guardado
   falla (400), el link sigue; borrar después el cliente anterior no la toca.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/datos1_postgres.py postgresql://cdi@127.0.0.1:55432/<base>
"""
import os
import sys
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_host = urlparse(URL).hostname or ""
if not URL.startswith("postgresql://") or _host not in ("127.0.0.1", "localhost"):
    sys.exit("uso: datos1_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

os.environ.update(
    DATABASE_URL=URL, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import psycopg2  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

import proyecto_maria.main as main_mod  # noqa: E402
from proyecto_maria.core.rate_limit import limiter  # noqa: E402
from proyecto_maria.database.models import Client  # noqa: E402
from tests.test_maria7_rechazos_24_10 import _pedido  # noqa: E402

limiter.enabled = False
FALLAS = []
CLAVE = "SecureP@ss1"
ITEM = {"pieza": "8471.30.12", "descripcion": "TABLETA SINTETICA", "origen": "CHN",
        "cantidad": 1, "valor_unitario": 50, "peso_unitario": 0.5}


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def sql(consulta, *args):
    with psycopg2.connect(URL) as con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall() if cur.description else None


def contar(tabla, columna, valor):
    return sql(f"select count(*) from {tabla} where {columna}=%s", valor)[0][0]


def cliente_de(op):
    """El cliente de la operación; None también si la operación no está."""
    filas = sql("select client_id from operations where id=%s", op)
    return filas[0][0] if filas else None


with TestClient(main_mod.app, raise_server_exceptions=False) as c:

    class Usuario:
        def __init__(self):
            nombre = f"d1_{uuid.uuid4().hex[:8]}"
            c.cookies.clear()
            r = c.post("/auth/register", json={"username": nombre, "password": CLAVE,
                                               "email": f"{nombre}@example.com", "name": nombre})
            assert r.status_code == 200, r.text
            self.sesion = dict(c.cookies)

        def activo(self):
            c.cookies.clear()
            for k, v in self.sesion.items():
                c.cookies.set(k, v)
            return c

        def cliente_vacio(self):
            self.activo()
            r = c.post("/api/clientes", json={"nombre": f"Cliente DATOS1 {uuid.uuid4().hex[:6]}"})
            assert r.status_code == 200, r.text
            return r.json()["cliente"]["id"]

        def cliente(self, compartir=True):
            """Cliente sintético con una operación; devuelve (cliente, op, token o None)."""
            cid = self.cliente_vacio()
            r = c.post(f"/api/clientes/{cid}/operaciones", json={"items": [ITEM]})
            assert r.status_code == 200, r.text
            op = r.json()["operation_id"]
            token = None
            if compartir:
                r = c.post("/api/quotes/share", json={"operation_id": op})
                assert r.status_code == 200, r.text
                token = r.json()["token"]
            return cid, op, token

    def link(token):
        return c.get(f"/api/quotes/public/{token}").status_code

    a, b = Usuario(), Usuario()
    cid, op, token = a.cliente()
    _, _, token_otro_cliente = a.cliente()
    _, _, token_ajeno = b.cliente()

    # --- 3. otro dueño
    b.activo()
    r = c.delete(f"/api/clientes/{cid}")
    chequear(r.status_code == 404 and contar("clients", "id", cid) == 1 and link(token) == 200,
             f"otro dueño no lo borra: 404 y el presupuesto sigue ({r.status_code})")

    # --- 5. falla a mitad: el cliente se borra último
    borrar_real = AsyncSession.delete

    async def _falla_con_el_cliente(self, obj):
        if isinstance(obj, Client):
            raise RuntimeError("falla simulada al borrar el cliente")
        return await borrar_real(self, obj)

    a.activo()
    AsyncSession.delete = _falla_con_el_cliente
    try:
        r = c.delete(f"/api/clientes/{cid}")
    finally:
        AsyncSession.delete = borrar_real
    chequear(r.status_code == 500 and contar("clients", "id", cid) == 1
             and contar("operations", "id", op) == 1 and contar("public_quotes", "operation_id", op) == 1
             and link(token) == 200,
             f"si falla a mitad no se borra nada ({r.status_code})")

    # --- 1. el dueño lo borra
    a.activo()
    r = c.delete(f"/api/clientes/{cid}")
    chequear(r.status_code == 200, f"el dueño borra el cliente con presupuesto compartido ({r.status_code} {r.text[:160]})")
    chequear(contar("clients", "id", cid) == 0 and contar("operations", "client_id", cid) == 0
             and contar("public_quotes", "operation_id", op) == 0,
             "no quedan cliente, operaciones ni presupuestos")
    chequear(link(token) == 404, "el link borrado da 404")

    # --- 2. los demás siguen
    chequear(link(token_otro_cliente) == 200, "el presupuesto de otro cliente del mismo dueño sigue")
    chequear(link(token_ajeno) == 200, "el presupuesto de otro dueño sigue")

    # --- 4. sin presupuesto
    cid2, _, _ = a.cliente(compartir=False)
    a.activo()
    r = c.delete(f"/api/clientes/{cid2}")
    chequear(r.status_code == 200 and contar("clients", "id", cid2) == 0,
             f"un cliente sin presupuesto se sigue borrando ({r.status_code})")

    # --- 6. la operación pasa a otro cliente
    x, y = a.cliente_vacio(), a.cliente_vacio()

    def guardar(cid, valor=50, opid=None):
        cuerpo = {"items": [{**ITEM, "valor_unitario": valor}]}
        if opid:
            cuerpo["operacion_id"] = opid
        return c.post(f"/api/clientes/{cid}/operaciones", json=cuerpo)

    r = c.post("/generate_maria", json=_pedido())
    assert r.status_code == 200, r.text
    op6 = r.json()["operacion_id"]
    r = guardar(x, opid=op6)
    assert r.status_code == 200 and r.json()["operation_id"] == op6, r.text
    r = c.post("/api/quotes/share", json={"operation_id": op6})
    assert r.status_code == 200, r.text
    token6 = r.json()["token"]
    r = guardar(y, "NaN", op6)
    chequear(r.status_code == 400 and link(token6) == 200 and cliente_de(op6) == x,
             f"si el guardado en otro cliente falla, el link sigue ({r.status_code})")
    r = guardar(y, opid=op6)
    chequear(r.status_code == 200 and r.json()["operation_id"] == op6 and link(token6) == 404
             and contar("public_quotes", "operation_id", op6) == 0 and cliente_de(op6) == y,
             f"guardada en otro cliente, la operación pierde su link ({r.status_code})")
    r = c.delete(f"/api/clientes/{x}")
    chequear(r.status_code == 200 and link(token6) == 404 and cliente_de(op6) == y,
             f"borrar el cliente anterior no la toca ni devuelve el link ({r.status_code})")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
