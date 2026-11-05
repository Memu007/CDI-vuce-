"""CATALOGO-LARGO-1 contra un Postgres de verdad: SQLite no controla el largo
de las columnas y el corte no se ve.

1. Crea una base descartable en el servidor de la URL y arranca ahí la
   versión anterior (un worktree, e099744 por defecto): registra un usuario,
   un cliente y guarda un producto de 300 caracteres en el catálogo de un
   proveedor, lo más largo que esa versión acepta.
2. Arranca la versión nueva sobre la misma base, dos veces.

Comprueba:
- que product_key y descripcion del catálogo pasan a text y la fila vieja
  queda igual, y que arrancar otra vez no cambia nada;
- que guardar-uso con una descripción de 301, 501 y 2000 caracteres responde
  200 con historial_guardado y queda entera en la memoria del cliente y en el
  catálogo, y que con 2001 responde 400 y no guarda nada;
- que el catálogo guarda, cambia y borra un producto de 2000 caracteres.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/catalogo_largo1_postgres.py postgresql://cdi@127.0.0.1:5432/postgres [SHA anterior]
"""
import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from urllib.parse import quote, urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
ANTERIOR = sys.argv[2] if len(sys.argv) > 2 else "e099744"
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: catalogo_largo1_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base> [SHA]  (sólo un Postgres local)")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = f"catalogo_largo1_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
TMP = tempfile.mkdtemp(prefix="catalogo_largo1_pg_")
WT = os.path.join(TMP, "wt")

import psycopg2  # noqa: E402

FALLAS = []
CLAVE = "SecureP@ss1"
USUARIO = f"cl1{uuid.uuid4().hex[:6]}"
VENDOR = "Proveedor sintetico"
VENDOR_ID = "proveedor_sintetico"
NCM = "73181500"
VIEJO = "tornillo " + "v" * 291


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
               " where table_name='vendor_catalog_products' and column_name in ('product_key','descripcion')"
               " order by column_name")


def catalogo():
    return sql("select product_key, descripcion from vendor_catalog_products where owner_username=%s"
               " order by length(descripcion)", USUARIO)


# Lo que hace la versión anterior: crea su esquema, el usuario, el cliente y
# guarda un producto en el catálogo.
VIEJA = r'''
import sys
from fastapi.testclient import TestClient
import proyecto_maria.main as m
from proyecto_maria.core.rate_limit import limiter
limiter.enabled = False
usuario, clave, vendor, vendor_id, desc = sys.argv[1:6]
with TestClient(m.app, raise_server_exceptions=False) as c:
    r = c.post("/auth/register", json={"username": usuario, "password": clave,
               "email": f"{usuario}@example.com", "name": usuario})
    assert r.status_code == 200, r.text
    r = c.post("/api/clientes", json={"nombre": "Cliente CATALOGO-LARGO-1 sintetico"})
    assert r.status_code == 200, r.text
    cid = r.json()["cliente"]["id"]
    r = c.post(f"/api/catalog/{vendor_id}/productos",
               json={"vendor_name": vendor, "productos": [{"descripcion": desc}]})
    assert r.status_code == 200, r.text
print("vieja ok " + cid)
'''

try:
    admin(f'create database "{BASE}"')

    # --- 1. la versión anterior
    subprocess.run(["git", "-C", REPO, "worktree", "add", "--detach", WT, ANTERIOR],
                   check=True, capture_output=True)
    r = subprocess.run([sys.executable, "-c", VIEJA, USUARIO, CLAVE, VENDOR, VENDOR_ID, VIEJO],
                       cwd=WT, env={**os.environ, **entorno(URL_BASE), "PYTHONPATH": WT},
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or "vieja ok" not in r.stdout:
        print(r.stdout[-2000:], r.stderr[-4000:])
        sys.exit("la versión anterior no arrancó o no guardó el producto")
    CID = r.stdout.split("vieja ok ")[1].split()[0]
    antes = catalogo()
    chequear(columnas() == [("descripcion", "character varying", 500), ("product_key", "character varying", 300)]
             and antes == [(VIEJO, VIEJO)],
             f"la base de {ANTERIOR} tiene las columnas cortas y el producto viejo: {columnas()} {len(antes)}")

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

    for vez in ("primer", "segundo"):
        with Arranque(main_mod.app, raise_server_exceptions=False):
            pass
        chequear(columnas() == [("descripcion", "text", None), ("product_key", "text", None)]
                 and catalogo() == antes,
                 f"{vez} arranque: las columnas son text y el producto viejo queda igual: {columnas()}")

    with Arranque(main_mod.app, raise_server_exceptions=False) as c:
        r = c.post("/auth/login", json={"username": USUARIO, "password": CLAVE})
        chequear(r.status_code == 200, f"login ({r.status_code})")
        for largo in (301, 501, 2000):
            desc = f"producto {largo} " + "x" * (largo - len(f"producto {largo} "))
            r = c.post("/api/ncm/guardar-uso", json={"descripcion": desc, "ncm": NCM, "client_id": CID,
                                                     "vendor_name": VENDOR})
            hist = sql("select descripcion from client_product_history where client_id=%s and descripcion=%s",
                       CID, desc)
            cat = sql("select descripcion from vendor_catalog_products where owner_username=%s"
                      " and descripcion=%s", USUARIO, desc)
            chequear(r.status_code == 200 and r.json() == {"success": True, "historial_guardado": True}
                     and len(hist) == 1 and len(cat) == 1,
                     f"guardar-uso con {largo} caracteres se guarda entero en las dos memorias: "
                     f"{r.status_code} {r.text[:120]} historial {len(hist)} catálogo {len(cat)}")

        antes = catalogo()
        r = c.post("/api/ncm/guardar-uso", json={"descripcion": "y" * 2001, "ncm": NCM, "client_id": CID,
                                                 "vendor_name": VENDOR})
        chequear(r.status_code == 400 and "2000" in r.text and catalogo() == antes
                 and not sql("select 1 from client_product_history where descripcion like 'yyy%%'"),
                 f"guardar-uso con 2001 da 400 y no guarda nada: {r.status_code} {r.text[:120]}")

        largo = "z" * 2000
        r = c.post(f"/api/catalog/{VENDOR_ID}/productos", json={"vendor_name": VENDOR,
                                                                "productos": [{"descripcion": largo}]})
        url = f"/api/catalog/{VENDOR_ID}/productos/{quote(largo)}"
        r_put = c.put(url, json={"ncm": NCM, "descripcion_original": "Z" * 2000})
        cambiado = sql("select ncm, descripcion from vendor_catalog_products where product_key=%s", largo)
        r_del = c.delete(url)
        chequear(r.status_code == 200 and r_put.status_code == 200 and cambiado == [(NCM, "Z" * 2000)]
                 and r_del.status_code == 200
                 and not sql("select 1 from vendor_catalog_products where product_key=%s", largo),
                 f"el catálogo guarda, cambia y borra un producto de 2000: {r.status_code} "
                 f"{r_put.status_code} {r_put.text[:120]} {r_del.status_code} {r_del.text[:120]}")
finally:
    subprocess.run(["git", "-C", REPO, "worktree", "remove", "--force", WT], capture_output=True)
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")
    shutil.rmtree(TMP, ignore_errors=True)

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
