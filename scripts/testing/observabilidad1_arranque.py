"""OBSERVABILIDAD-1 con la app arrancada de verdad (uvicorn), en SQLite y,
si se le pasa la URL, en Postgres.

Parte de una base cuya `api_logs` es de antes de la columna `owner_username`
y ya tiene filas, como la de producción. Comprueba:
- al arrancar, la columna existe (VARCHAR(50), nullable, sin default) con
  un índice, y las filas viejas quedan como estaban y sin dueño;
- un pedido cualquiera deja su métrica en la base, sin «Error logging
  metrics», y el panel de admin (/api/dev/stats) responde;
- un segundo arranque no cambia ni el esquema ni las filas, y en Postgres
  no pide el lock de la tabla (arranca con una lectura abierta sobre ella);
- si la migración falla, la app arranca igual, lo dice en el log y los
  pedidos responden. En SQLite falla porque `api_logs` es una vista; en
  Postgres, porque otra conexión tiene tomada la tabla: el arranque no
  espera ese lock más de unos segundos.

uso (Postgres local y descartable, nunca el de producción; el usuario tiene
que poder crear bases; sin URL corre sólo SQLite):
  python scripts/testing/observabilidad1_arranque.py [postgresql://cdi@127.0.0.1:55432/postgres]
Necesita uvicorn (y psycopg2 para Postgres) en el mismo Python.
"""
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from http.cookiejar import CookieJar
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
if URL:
    _u = urlparse(URL)
    if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
        sys.exit("uso: observabilidad1_arranque.py [postgresql://usuario@127.0.0.1:<puerto>/<base>]  (sólo un Postgres local)")
    import psycopg2

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TMP = tempfile.mkdtemp(prefix="obs1_")
FALLAS = []
ADMIN, CLAVE = f"adm_obs_{uuid.uuid4().hex[:6]}", "SecureP@ss1"

COLUMNAS_VIEJAS = """
    id VARCHAR PRIMARY KEY,
    endpoint VARCHAR(200) NOT NULL,
    method VARCHAR(10) NOT NULL,
    client_ip VARCHAR(45),
    user_agent TEXT,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    operation_id VARCHAR,
    external_api VARCHAR(50),"""
FILAS_VIEJAS = """
INSERT INTO api_logs (id, endpoint, method, status_code, response_time_ms, error_message, created_at)
VALUES ('vieja-1', '/robots.txt', 'GET', 200, 4, NULL, '2026-10-24 10:00:00'),
       ('vieja-2', '/api/clientes', 'POST', 500, 31, 'falló algo ñandú', '2026-10-24 10:01:00')"""


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class SQLite:
    nombre = "SQLite"

    def __init__(self):
        self.ruta = os.path.join(TMP, f"obs1_{uuid.uuid4().hex[:8]}.db")
        self.url = f"sqlite+aiosqlite:///{self.ruta}"

    def sql(self, *consultas):
        con = sqlite3.connect(self.ruta)
        try:
            salida = None
            for q in consultas:
                cur = con.execute(q)
                salida = cur.fetchall() if cur.description else None
            con.commit()
            return salida
        finally:
            con.close()

    def vieja(self):
        self.sql(f"CREATE TABLE api_logs ({COLUMNAS_VIEJAS} created_at DATETIME DEFAULT CURRENT_TIMESTAMP)",
                 FILAS_VIEJAS)

    def columna(self):
        f = [c for c in self.sql("PRAGMA table_info(api_logs)") if c[1] == "owner_username"]
        return (f[0][2], not f[0][3], f[0][4]) if f else None

    def indices(self):
        return sorted(n for (_, n, *_) in self.sql("PRAGMA index_list(api_logs)")
                      if [c[2] for c in self.sql(f'PRAGMA index_info("{n}")')][:1] == ["owner_username"])

    def esquema(self):
        return self.sql("SELECT type, name, sql FROM sqlite_master WHERE tbl_name = 'api_logs' ORDER BY 1, 2")

    def borrar(self):
        pass


class Postgres:
    nombre = "Postgres"

    def __init__(self):
        self.base = f"obs1_{uuid.uuid4().hex[:8]}"
        self.url = _u._replace(path=f"/{self.base}").geturl()
        self.admin(f'create database "{self.base}"')

    def admin(self, q):
        con = psycopg2.connect(URL)
        con.autocommit = True
        try:
            con.cursor().execute(q)
        finally:
            con.close()

    def sql(self, *consultas):
        with psycopg2.connect(self.url) as con, con.cursor() as cur:
            salida = None
            for q in consultas:
                cur.execute(q)
                salida = cur.fetchall() if cur.description else None
            return salida

    def vieja(self):
        self.sql(f"CREATE TABLE api_logs ({COLUMNAS_VIEJAS} created_at TIMESTAMPTZ DEFAULT now())", FILAS_VIEJAS)

    def columna(self):
        f = self.sql("select data_type || '(' || character_maximum_length || ')', is_nullable = 'YES', "
                     "column_default from information_schema.columns "
                     "where table_schema = 'public' and table_name = 'api_logs' and column_name = 'owner_username'")
        return (f[0][0].replace("character varying", "VARCHAR"), f[0][1], f[0][2]) if f else None

    def indices(self):
        return sorted(n for (n,) in self.sql(
            "select c.relname from pg_index i join pg_class c on c.oid = i.indexrelid "
            "join pg_attribute a on a.attrelid = i.indrelid and a.attnum = i.indkey[0] "
            "where i.indrelid = 'api_logs'::regclass and a.attname = 'owner_username'"))

    def esquema(self):
        cols = self.sql("select column_name, data_type, is_nullable, column_default from information_schema.columns "
                        "where table_schema = 'public' and table_name = 'api_logs' order by ordinal_position")
        idx = self.sql("select indexname, indexdef from pg_indexes where tablename = 'api_logs' order by 1")
        res = self.sql("select conname, pg_get_constraintdef(oid) from pg_constraint "
                       "where conrelid = 'api_logs'::regclass order by 1")
        return cols, idx, res

    def borrar(self):
        self.admin(f'drop database if exists "{self.base}" with (force)')


class App:
    """Un arranque de uvicorn sobre la base; cada uno con su log."""

    def __init__(self, base, etiqueta, admins=ADMIN):
        self.puerto = puerto_libre()
        self.log = os.path.join(TMP, f"{base.nombre}_{etiqueta}.log")
        env = {**os.environ, "DATABASE_URL": base.url, "ENVIRONMENT": "testing",
               "EMAIL_VERIFICATION_REQUIRED": "false",
               "JWT_SECRET_KEY": "clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
               "GEMINI_API_KEY": "test-key", "VUCE_MODE": "fake", "TARIFAR_MODE": "fake", "AFIP_MODE": "fake",
               "DOLARAPI_BASE": "http://127.0.0.1:9/v1/dolares", "ADMIN_USERNAMES": admins,
               "CDI_DATA_DIR": os.path.join(TMP, "data"), "PYTHONPATH": REPO}
        env.pop("PYTEST_CURRENT_TEST", None)  # con ella el middleware no graba métricas
        self.p = subprocess.Popen([sys.executable, "-m", "uvicorn", "proyecto_maria.main:app",
                                   "--port", str(self.puerto)], cwd=REPO, env=env,
                                  stdout=open(self.log, "w"), stderr=subprocess.STDOUT)
        self.web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
        hasta = time.monotonic() + 120
        while time.monotonic() < hasta and self.p.poll() is None:
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{self.puerto}/health", timeout=2)
                self.arranco = True
                return
            except (urllib.error.URLError, ConnectionError, OSError):
                time.sleep(0.1)
        self.arranco = False

    def pedir(self, ruta, cuerpo=None):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.puerto}{ruta}",
            data=json.dumps(cuerpo).encode() if cuerpo is not None else None,
            headers={"Content-Type": "application/json"} if cuerpo is not None else {})
        try:
            r = self.web.open(req, timeout=30)
            return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def texto(self):
        return open(self.log, encoding="utf-8", errors="replace").read()

    def parar(self):
        self.p.terminate()
        try:
            self.p.wait(30)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.wait()


def esperar(condicion, segundos=15):
    hasta = time.monotonic() + segundos
    while time.monotonic() < hasta:
        if condicion():
            return True
        time.sleep(0.1)
    return condicion()


def base_vieja(b):
    print(f"\n== {b.nombre}: base vieja con filas")
    b.vieja()
    antes = b.sql("select * from api_logs order by id")
    chequear(b.columna() is None, "la base de partida no tiene api_logs.owner_username")

    # Un nombre de ADMIN_USERNAMES no se registra: la cuenta se crea con la lista
    # vacía y el arranque que la tiene en la lista le da el rol.
    app = App(b, "1", admins="")
    try:
        if not app.arranco:
            chequear(False, f"la app arranca: {app.texto()[-1500:]}")
            return
        chequear(b.columna() == ("VARCHAR(50)", True, None),
                 f"al arrancar la columna existe, VARCHAR(50), nullable, sin default: {b.columna()}")
        chequear(b.indices() == ["ix_api_logs_owner_username"], f"con un índice: {b.indices()}")
        # Sin nombrar owner_username: si la columna falta, el resto se sigue midiendo.
        despues = b.sql("select id, endpoint, method, client_ip, user_agent, status_code, response_time_ms, "
                        "error_message, operation_id, external_api, created_at from api_logs "
                        "where id like 'vieja-%' order by id")
        chequear(despues == antes, "las filas viejas quedan como estaban")
        if b.columna() is not None:
            chequear(b.sql("select owner_username from api_logs where id like 'vieja-%'") == [(None,), (None,)],
                     "y sin dueño inventado")

        r = app.pedir("/robots.txt")
        chequear(r[0] == 200, f"un pedido cualquiera responde: {r[0]}")
        nuevas = lambda: b.sql("select endpoint from api_logs "  # noqa: E731
                               "where id not like 'vieja-%' and endpoint = '/robots.txt'")
        chequear(esperar(lambda: bool(nuevas())), f"y deja su métrica en la base: {nuevas()}")
        chequear("Error logging metrics" not in app.texto(), "sin «Error logging metrics» en el log")

        r = app.pedir("/auth/register", {"username": ADMIN, "password": CLAVE,
                                         "email": f"{ADMIN.replace('_', '-')}@example.com", "name": "adm"})
        chequear(r[0] == 200, f"registro del admin: {r[0]} {r[1][:120]!r}")
    finally:
        app.parar()

    esquema1, filas1 = b.esquema(), b.sql("select * from api_logs order by id")
    lectura = None
    if b.nombre == "Postgres":
        # Una lectura larga abierta: si el arranque pidiera el lock de la tabla
        # aunque la columna ya esté, esperaría y fallaría.
        lectura = psycopg2.connect(b.url)
        lectura.cursor().execute("select count(*) from api_logs")
    app = App(b, "2")
    try:
        chequear(app.arranco, "arranca otra vez")
    finally:
        app.parar()
        if lectura is not None:
            lectura.rollback()
            lectura.close()
    chequear(b.esquema() == esquema1, "el segundo arranque no cambia el esquema de api_logs")
    chequear(b.sql("select * from api_logs order by id") == filas1, "ni sus filas")
    chequear("api_logs.owner_username" not in app.texto(), "ni dice que agregó algo")
    chequear("[OBSERVABILIDAD-1]" not in app.texto(),
             "ni falla" + (" con una lectura abierta sobre la tabla" if lectura is not None else ""))

    app = App(b, "admin")
    try:
        r = app.pedir("/auth/login", {"username": ADMIN, "password": CLAVE})
        chequear(r[0] == 200, f"entra el admin: {r[0]} {r[1][:120]!r}")
        r = app.pedir("/api/dev/stats")
        chequear(r[0] == 200 and '"endpoint":"/robots.txt"' in r[1].decode(),
                 f"el panel de admin responde y muestra la métrica: {r[0]} {r[1][:160]!r}")
    finally:
        app.parar()


def base_con_falla(b):
    print(f"\n== {b.nombre}: la migración falla")
    traba = None
    if b.nombre == "SQLite":
        b.sql("CREATE TABLE logs_reales (id VARCHAR PRIMARY KEY, endpoint VARCHAR(200))",
              "CREATE VIEW api_logs AS SELECT id, endpoint FROM logs_reales")
    else:
        b.vieja()
        traba = psycopg2.connect(b.url)
        traba.cursor().execute("LOCK TABLE api_logs IN ACCESS EXCLUSIVE MODE")
    inicio = time.monotonic()
    app = App(b, "falla")
    try:
        chequear(app.arranco, f"la app arranca igual ({time.monotonic() - inicio:.1f} s)")
        if app.arranco:
            chequear(esperar(lambda: "[OBSERVABILIDAD-1] no se pudo agregar api_logs.owner_username" in app.texto(), 5),
                     "y lo dice en el log")
            r = app.pedir("/robots.txt")
            chequear(r[0] == 200, f"los pedidos responden aunque la métrica no se grabe: {r[0]}")
    finally:
        app.parar()
        if traba is not None:
            traba.rollback()
            traba.close()
    if traba is not None:
        chequear(b.columna() is None, "con la tabla tomada no agregó nada")
        app = App(b, "suelta")
        try:
            chequear(app.arranco and b.columna() == ("VARCHAR(50)", True, None),
                     "suelta la tabla, el próximo arranque la agrega")
        finally:
            app.parar()


bases = []
try:
    for clase in [SQLite] + ([Postgres] if URL else []):
        for escenario in (base_vieja, base_con_falla):
            b = clase()
            bases.append(b)
            try:
                escenario(b)
            except Exception as e:  # un escenario cortado es una falla, no un traceback
                chequear(False, f"{b.nombre}: {escenario.__name__} se cortó: {e!r}")
finally:
    for b in bases:
        b.borrar()
    if FALLAS:
        print(f"\nlogs en {TMP}")
    else:
        shutil.rmtree(TMP, ignore_errors=True)

print(f"\nfallas {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
