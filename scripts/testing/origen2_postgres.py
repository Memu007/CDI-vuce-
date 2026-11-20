"""El origen habitual del cliente contra un Postgres de verdad: SQLite no
controla el largo de la columna y el corte a 3 no se ve.

1. Crea una base descartable en el servidor de la URL y arranca ahí la versión
   anterior (un worktree, 4fe296d4 por defecto): registra un usuario y guarda
   clientes con «CN», sin origen y con «CHINA» y «Holanda», que esa versión
   recorta a «CHI» y «HOL». Otro queda con el origen vacío, escrito en la base.
2. Arranca dos veces la versión nueva sobre la misma base.

Comprueba:
- que clients.default_origin pasa a text y cada fila vieja queda igual;
- que el alta y la edición guardan enteros «BRASIL» y un nombre de la tabla
  de 54 caracteres, que «Narnia» da 400 sin tocar la fila, y que editar otro
  dato deja «CHI» como estaba.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/origen2_postgres.py postgresql://cdi@127.0.0.1:5432/postgres [SHA anterior]
"""
import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
ANTERIOR = sys.argv[2] if len(sys.argv) > 2 else "4fe296d4"
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: origen2_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base> [SHA]  (sólo un Postgres local)")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = f"origen2_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
TMP = tempfile.mkdtemp(prefix="origen2_pg_")
WT = os.path.join(TMP, "wt")

import psycopg2  # noqa: E402

FALLAS = []
CLAVE = "SecureP@ss1"
USUARIO = f"or2{uuid.uuid4().hex[:6]}"
ANTILLAS = "659 · ANTILLAS HOLANDESAS (TERRITORIO DE PAISES BAJOS)"


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
        return cur.fetchall() if cur.description else None


def entorno(url):
    return dict(
        DATABASE_URL=url, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
        JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
        GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
        DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares", NCM_GEMINI_FALLBACK="false",
    )


def columna():
    return sql("select data_type, character_maximum_length from information_schema.columns"
               " where table_name='clients' and column_name='default_origin'")


def origenes():
    return dict(sql("select name, default_origin from clients where owner_username=%s", USUARIO))


# Lo que hace la versión anterior: crea su esquema, el usuario y los clientes.
VIEJA = r'''
import sys
from fastapi.testclient import TestClient
import proyecto_maria.main as m
from proyecto_maria.core.rate_limit import limiter
limiter.enabled = False
usuario, clave = sys.argv[1:3]
with TestClient(m.app, raise_server_exceptions=False) as c:
    r = c.post("/auth/register", json={"username": usuario, "password": clave,
               "email": f"{usuario}@example.com", "name": usuario})
    assert r.status_code == 200, r.text
    for nombre, origen in (("china", "CN"), ("sin origen", "CN"), ("vacio", "CN"), ("chi", "CHINA"),
                           ("hol", "Holanda")):
        r = c.post("/api/clientes", json={"nombre": nombre, "default_origin": origen})
        assert r.status_code == 200, r.text
        if nombre == "sin origen":
            r = c.put(f"/api/clientes/{r.json()['cliente']['id']}", json={"default_origin": ""})
            assert r.status_code == 200, r.text
print("vieja ok")
'''
VIEJOS = {"china": "CN", "sin origen": None, "vacio": "", "chi": "CHI", "hol": "HOL"}

try:
    admin(f'create database "{BASE}"')

    # --- 1. la versión anterior
    subprocess.run(["git", "-C", REPO, "worktree", "add", "--detach", WT, ANTERIOR],
                   check=True, capture_output=True)
    r = subprocess.run([sys.executable, "-c", VIEJA, USUARIO, CLAVE],
                       cwd=WT, env={**os.environ, **entorno(URL_BASE), "PYTHONPATH": WT},
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or "vieja ok" not in r.stdout:
        print(r.stdout[-2000:], r.stderr[-4000:])
        sys.exit("la versión anterior no arrancó o no guardó los clientes")
    sql("update clients set default_origin='' where owner_username=%s and name='vacio'", USUARIO)
    chequear(columna() == [("character varying", 3)] and origenes() == VIEJOS,
             f"la base de {ANTERIOR} tiene el origen en 3 y los clientes viejos: {columna()} {origenes()}")

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
        chequear(columna() == [("text", None)] and origenes() == VIEJOS,
                 f"{vez} arranque: el origen es text y los clientes viejos quedan igual: {columna()} {origenes()}")

    ids = dict(sql("select name, id from clients where owner_username=%s", USUARIO))
    with Arranque(main_mod.app, raise_server_exceptions=False) as c:
        r = c.post("/auth/login", json={"username": USUARIO, "password": CLAVE})
        chequear(r.status_code == 200, f"login ({r.status_code})")
        r = c.put(f"/api/clientes/{ids['china']}", json={"default_origin": "BRASIL"})
        chequear(r.status_code == 200 and origenes()["china"] == "BRASIL",
                 f"la edición guarda «BRASIL» entero: {r.status_code} {r.text[:120]} {origenes()['china']!r}")
        r = c.post("/api/clientes", json={"nombre": "antillas", "default_origin": ANTILLAS})
        chequear(r.status_code == 200 and origenes().get("antillas") == ANTILLAS,
                 f"el alta guarda entero un origen de {len(ANTILLAS)}: {r.status_code} {r.text[:120]}")
        r = c.put(f"/api/clientes/{ids['sin origen']}", json={"default_origin": "Narnia"})
        chequear(r.status_code == 400 and "Narnia" in r.text and origenes()["sin origen"] is None,
                 f"«Narnia» da 400 y no toca la fila: {r.status_code} {r.text[:120]}")
        r = c.put(f"/api/clientes/{ids['chi']}", json={"notas": "otro dato"})
        chequear(r.status_code == 200 and origenes()["chi"] == "CHI",
                 f"editar otro dato deja «CHI»: {r.status_code} {origenes()['chi']!r}")
finally:
    subprocess.run(["git", "-C", REPO, "worktree", "remove", "--force", WT], capture_output=True)
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")
    shutil.rmtree(TMP, ignore_errors=True)

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
