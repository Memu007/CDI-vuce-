"""ENTRADAS-1 contra un Postgres de verdad: corre tests/test_entradas1.py
entero sobre una base propia. En SQLite el NUL se guarda sin quejarse; acá
una clave o un texto del alta con NUL tiene que dar 422 y no 500.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/entradas1_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
Crea la base al empezar y la borra al terminar. Sale con el código de pytest.
"""
import os
import subprocess
import sys
import uuid
from urllib.parse import urlparse

import psycopg2

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: entradas1_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = f"entradas1_{uuid.uuid4().hex[:8]}"


def admin(consulta):
    con = psycopg2.connect(URL)
    con.autocommit = True
    try:
        with con.cursor() as cur:
            cur.execute(consulta)
    finally:
        con.close()


admin(f'create database "{BASE}"')
try:
    entorno = dict(
        os.environ, DATABASE_URL=_u._replace(path=f"/{BASE}").geturl(), ENVIRONMENT="test",
        GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
        DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
    )
    codigo = subprocess.call(
        [sys.executable, "-m", "pytest", "-q", "--no-cov", "-p", "no:cacheprovider", "-W", "ignore", "-rf",
         "tests/test_entradas1.py"], cwd=REPO, env=entorno)
finally:
    admin(f'drop database if exists "{BASE}" with (force)')
print(f"entradas1_postgres: pytest salió con {codigo}")
sys.exit(codigo)
