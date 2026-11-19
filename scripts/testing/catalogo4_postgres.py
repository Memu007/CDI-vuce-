"""CATALOGO-4 contra un Postgres de verdad: el escenario de tests/test_catalogo4.py con las filas
que devuelve Postgres, que cambian de lugar cuando se actualizan.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/catalogo4_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
"""
import os
import sys
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: catalogo4_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

BASE = f"catalogo4_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
os.environ.update(
    DATABASE_URL=URL_BASE, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares", NCM_GEMINI_FALLBACK="false",
)
os.environ.pop("PYTEST_CURRENT_TEST", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import psycopg2  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

CLAVE = "Clave-sintetica-1!"


def admin(consulta):
    con = psycopg2.connect(URL)
    con.autocommit = True
    try:
        with con.cursor() as cur:
            cur.execute(consulta)
    finally:
        con.close()


malos = ["no corrió"]
try:
    admin(f'create database "{BASE}"')
    from fastapi.testclient import TestClient  # noqa: E402
    import proyecto_maria.main as main_mod  # noqa: E402
    from proyecto_maria.core.rate_limit import limiter  # noqa: E402
    from tests.test_catalogo4 import errores, sin_ncm_mal, sugeridos  # noqa: E402
    limiter.enabled = False
    motor = create_engine(URL_BASE)

    def escribir(consulta, **params):
        with motor.begin() as con:
            con.execute(text(consulta), params)

    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        u = "c4_" + uuid.uuid4().hex[:10]
        r = c.post("/auth/register", json={"username": u, "password": CLAVE,
                                           "email": f"{u}@example.com", "name": "C"})
        if r.status_code != 200:
            sys.exit(f"FALLA | no se pudo registrar el usuario: {r.status_code} {r.text[:200]}")
        assert c.post("/auth/login", json={"username": u, "password": CLAVE}).status_code == 200
        malos = errores(sugeridos(c, escribir)) + sin_ncm_mal(c)
    motor.dispose()
finally:
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")

for m in malos:
    print(f"FALLA | {m}")
print(f"fallas: {len(malos)}")
sys.exit(1 if malos else 0)
