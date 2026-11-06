"""CATALOGO-LARGO-2 contra un Postgres de verdad: SQLite no controla el largo
de las columnas y el corte no se ve.

1. Crea una base descartable en el servidor de la URL y arranca ahí la
   versión anterior (un worktree, 93cbdef por defecto): registra un usuario,
   un cliente y guarda en el catálogo un producto con origen «CN».
2. Arranca la versión nueva sobre la misma base: una con la tabla tomada por
   otra conexión y dos sin.

Comprueba:
- que con la tabla tomada el arranque falla en vez de seguir con el corte;
- que origen y vendor_nombre del catálogo y el origen de la memoria del
  cliente pasan a text y la fila vieja queda igual, y que arrancar otra vez
  no cambia nada;
- que el origen «TAIWAN» y un proveedor de 220 caracteres se guardan enteros
  por el catálogo, por cambiar el origen y por guardar-uso con y sin cliente,
  y que guardar-uso con un cliente guarda también el origen entero en la
  memoria del cliente;
- que guardar-uso de «螺丝» con proveedor y sin cliente guarda la fila;
- que 2000 caracteres CJK distintos se guardan por el catálogo, por
  guardar-uso y por cambiar la descripción: la clave entra en el índice único.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/catalogo_largo2_postgres.py postgresql://cdi@127.0.0.1:5432/postgres [SHA anterior]
"""
import asyncio
import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
ANTERIOR = sys.argv[2] if len(sys.argv) > 2 else "93cbdef"
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: catalogo_largo2_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base> [SHA]  (sólo un Postgres local)")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = f"catalogo_largo2_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
TMP = tempfile.mkdtemp(prefix="catalogo_largo2_pg_")
WT = os.path.join(TMP, "wt")

import psycopg2  # noqa: E402

FALLAS = []
CLAVE = "SecureP@ss1"
USUARIO = f"cl2{uuid.uuid4().hex[:6]}"
VENDOR = "Proveedor sintetico"
VENDOR_ID = "proveedor_sintetico"
LARGO = "Proveedor largo " + "x" * 204
LARGO_ID = ("proveedor_largo_" + "x" * 204)[:60]
NCM = "73181500"
# Variados: repetidos, Postgres los comprime y entran en el índice igual.
CJK_LARGO = "".join(chr(0x4E00 + i * 7) for i in range(2000))


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def admin(consulta):
    con = psycopg2.connect(URL)
    con.autocommit = True
    try:
        with con.cursor() as cur:
            cur.execute(consulta)
    finally:
        con.close()


def sql(consulta, *args):
    # El with de psycopg2 cierra la transacción, no la conexión.
    with contextlib.closing(psycopg2.connect(URL_BASE)) as con, con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall()


def entorno(url):
    return dict(
        DATABASE_URL=url, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
        JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
        GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
        DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares", NCM_GEMINI_FALLBACK="false",
    )


def columnas():
    return sql("select column_name, data_type, character_maximum_length from information_schema.columns"
               " where (table_name='vendor_catalog_products' and column_name in ('origen','vendor_nombre'))"
               " or (table_name='client_product_history' and column_name='origen_frecuente')"
               " order by column_name")


def fila(vendor_id, descripcion):
    return sql("select vendor_nombre, ncm, origen from vendor_catalog_products where owner_username=%s"
               " and vendor_id=%s and descripcion=%s", USUARIO, vendor_id, descripcion)


VIEJA = r'''
import sys
from fastapi.testclient import TestClient
import proyecto_maria.main as m
from proyecto_maria.core.rate_limit import limiter
limiter.enabled = False
usuario, clave, vendor, vendor_id, ncm = sys.argv[1:6]
with TestClient(m.app, raise_server_exceptions=False) as c:
    r = c.post("/auth/register", json={"username": usuario, "password": clave,
               "email": f"{usuario}@example.com", "name": usuario})
    assert r.status_code == 200, r.text
    r = c.post("/api/clientes", json={"nombre": "Cliente CATALOGO-LARGO-2 sintetico"})
    assert r.status_code == 200, r.text
    cid = r.json()["cliente"]["id"]
    r = c.post(f"/api/catalog/{vendor_id}/productos", json={"vendor_name": vendor,
               "productos": [{"descripcion": "TORNILLO", "ncm": ncm, "origen": "CN"}]})
    assert r.status_code == 200, r.text
print("vieja ok " + cid)
'''

try:
    admin(f'create database "{BASE}"')

    # --- 1. la versión anterior
    subprocess.run(["git", "-C", REPO, "worktree", "add", "--detach", WT, ANTERIOR],
                   check=True, capture_output=True)
    r = subprocess.run([sys.executable, "-c", VIEJA, USUARIO, CLAVE, VENDOR, VENDOR_ID, NCM],
                       cwd=WT, env={**os.environ, **entorno(URL_BASE), "PYTHONPATH": WT},
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or "vieja ok" not in r.stdout:
        print(r.stdout[-2000:], r.stderr[-4000:])
        sys.exit("la versión anterior no arrancó o no guardó el producto")
    CID = r.stdout.split("vieja ok ")[1].split()[0]
    viejo = fila(VENDOR_ID, "TORNILLO")
    chequear(columnas() == [("origen", "character varying", 5), ("origen_frecuente", "character varying", 3),
                            ("vendor_nombre", "character varying", 200)]
             and viejo == [(VENDOR, NCM, "CN")],
             f"la base de {ANTERIOR} tiene las columnas cortas y el producto viejo: {columnas()} {viejo}")

    # --- 2. la versión nueva sobre la misma base
    os.environ.update(entorno(URL_BASE))
    sys.path.insert(0, REPO)
    from fastapi.testclient import TestClient  # noqa: E402
    import proyecto_maria.main as main_mod  # noqa: E402
    from proyecto_maria.core.rate_limit import limiter  # noqa: E402
    from proyecto_maria.database.connection import engine  # noqa: E402
    limiter.enabled = False

    class Arranque(TestClient):
        """Un arranque de la app; al salir cierra las conexiones, como un
        proceso que termina (cada arranque tiene su propio loop)."""
        def __exit__(self, *exc):
            self.portal.call(engine.dispose)
            return super().__exit__(*exc)

    tomada = psycopg2.connect(URL_BASE)
    try:
        tomada.cursor().execute("select 1 from vendor_catalog_products limit 1")
        try:
            with Arranque(main_mod.app, raise_server_exceptions=False):
                arranco = True
        except Exception:
            arranco = False
            asyncio.run(engine.dispose(close=False))
    finally:
        tomada.close()
    chequear(not arranco and {t for _, t, _ in columnas()} == {"character varying"},
             f"con la tabla tomada el arranque falla en vez de seguir con las columnas cortas: {columnas()}")

    for vez in ("primer", "segundo"):
        with Arranque(main_mod.app, raise_server_exceptions=False):
            pass
        chequear(columnas() == [("origen", "text", None), ("origen_frecuente", "text", None),
                                ("vendor_nombre", "text", None)]
                 and fila(VENDOR_ID, "TORNILLO") == viejo,
                 f"{vez} arranque: las columnas son text y el producto viejo queda igual: {columnas()}")

    with Arranque(main_mod.app, raise_server_exceptions=False) as c:
        r = c.post("/auth/login", json={"username": USUARIO, "password": CLAVE})
        chequear(r.status_code == 200, f"login ({r.status_code})")

        r = c.post(f"/api/catalog/{LARGO_ID}/productos", json={"vendor_name": LARGO, "productos": [
            {"descripcion": "TUERCA", "ncm": NCM, "origen": "TAIWAN"}]})
        chequear(r.status_code == 200 and fila(LARGO_ID, "TUERCA") == [(LARGO, NCM, "TAIWAN")],
                 f"el catálogo guarda enteros el origen y el proveedor: {r.status_code} {r.text[:120]}")

        r = c.put(f"/api/catalog/{VENDOR_ID}/productos/tornillo", json={"origen": "TAIWAN"})
        chequear(r.status_code == 200 and fila(VENDOR_ID, "TORNILLO") == [(VENDOR, NCM, "TAIWAN")],
                 f"cambiar el origen lo guarda entero: {r.status_code} {r.text[:120]}")

        for desc, cliente in (("ARANDELA", {}), ("BULON", {"client_id": CID})):
            r = c.post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": NCM, "vendor_name": LARGO,
                                                     "origen": "TAIWAN", **cliente})
            memoria = sql("select origen_frecuente from client_product_history where client_id=%s"
                          " and descripcion=%s", CID, desc)
            chequear(r.status_code == 200 and r.json() == {"success": True, "historial_guardado": True}
                     and fila(LARGO_ID, desc) == [(LARGO, NCM, "TAIWAN")]
                     and memoria == [("TAIWAN",)] * len(cliente),
                     f"guardar-uso {'con' if cliente else 'sin'} cliente guarda enteros el origen y el "
                     f"proveedor: {r.status_code} {r.text[:120]} memoria del cliente {memoria}")

        r = c.post("/api/ncm/guardar-uso", json={"descripcion": "螺丝", "ncm": NCM, "vendor_name": VENDOR})
        chequear(r.status_code == 200 and r.json() == {"success": True, "historial_guardado": True}
                 and fila(VENDOR_ID, "螺丝") == [(VENDOR, NCM, None)],
                 f"guardar-uso de «螺丝» sin cliente guarda la fila: {r.status_code} {r.text[:120]}")

        url = f"/api/catalog/{VENDOR_ID}/productos"
        for via, desc in (("catálogo", CJK_LARGO[:-1] + "一"), ("guardar-uso", CJK_LARGO[1:] + "一"),
                          ("cambiar la descripción", CJK_LARGO)):
            if via == "catálogo":
                r = c.post(url, json={"vendor_name": VENDOR, "productos": [{"descripcion": desc, "ncm": NCM}]})
            elif via == "guardar-uso":
                r = c.post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": NCM, "vendor_name": VENDOR})
            else:
                r = c.put(f"{url}/tornillo", json={"descripcion_original": desc})
            chequear(r.status_code == 200 and len(fila(VENDOR_ID, desc)) == 1,
                     f"2000 caracteres CJK por {via} se guardan: {r.status_code} {r.text[:120]}")
finally:
    subprocess.run(["git", "-C", REPO, "worktree", "remove", "--force", WT], capture_output=True)
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")
    shutil.rmtree(TMP, ignore_errors=True)

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
