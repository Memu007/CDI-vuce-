"""ENTRADAS-1 contra un Postgres de verdad. En SQLite el NUL se guarda sin
quejarse, así que tests/test_entradas1.py (que conftest ata a SQLite) no lo
mide. Comprueba que:
1. una clave nueva con NUL da 422 en reset, cambio, registro y alta de
   estudio, y no cambia nada: el link sigue sirviendo, la clave vieja sigue
   y no se crea la cuenta;
2. un NUL en cada texto del registro y del alta de estudio no da 500.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/entradas1_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
"""
import os
import sys
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: entradas1_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

BASE = f"entradas1_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
os.environ.update(
    DATABASE_URL=URL_BASE, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import psycopg2  # noqa: E402

FALLAS = []
CLAVE, CLAVE2, NUL = "Clave-sintetica-1!", "Clave-sintetica-2!", "\x00"


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


def hay_usuario(u):
    with psycopg2.connect(URL_BASE) as con, con.cursor() as cur:
        cur.execute("select count(*) from users where username=%s", (u,))
        return cur.fetchone()[0] > 0


try:
    admin(f'create database "{BASE}"')
    from fastapi.testclient import TestClient  # noqa: E402
    import proyecto_maria.main as main_mod  # noqa: E402
    from proyecto_maria.core.rate_limit import limiter  # noqa: E402
    limiter.enabled = False

    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        def nuevo():
            return "e1_" + uuid.uuid4().hex[:10]

        def registro(**cambios):
            u = nuevo()
            cuerpo = {"username": u, "password": CLAVE, "email": f"{u}@example.com", "name": "E", **cambios}
            return u, c.post("/auth/register", json=cuerpo)

        def estudio(**cambios):
            u = nuevo()
            cuerpo = {"name": "Estudio", "username": u, "password": CLAVE, "email": f"{u}@example.com", **cambios}
            return u, c.post("/api/organizations/create", json=cuerpo)

        def login(u, clave):
            return c.post("/auth/login", json={"username": u, "password": clave})

        def por_reset(clave):
            u, r = registro()
            assert r.status_code == 200, r.text
            token = c.post("/auth/request-password-reset", json={"email": f"{u}@example.com"}).json()["dev_token_hint"]
            r = c.post("/auth/reset-password", json={"token": token, "new_password": clave})
            sigue = c.post("/auth/reset-password", json={"token": token, "new_password": CLAVE2}).status_code == 200
            return r, f"el link sigue sirviendo: {sigue}", sigue

        def por_cambio(clave):
            u, r = registro()
            sesion = {"Authorization": f"Bearer {r.json()['access_token']}"}
            r = c.post("/api/user/change-password", headers=sesion,
                       json={"current_password": CLAVE, "new_password": clave})
            sigue = login(u, CLAVE).status_code == 200
            return r, f"la clave vieja sigue: {sigue}", sigue

        def por_registro(clave):
            u, r = registro(password=clave)
            return r, f"sin cuenta nueva: {not hay_usuario(u)}", not hay_usuario(u)

        def por_estudio(clave):
            u, r = estudio(password=clave)
            return r, f"sin cuenta nueva: {not hay_usuario(u)}", not hay_usuario(u)

        # 1. clave nueva con NUL en las cuatro vías
        for via, hacer in [("reset", por_reset), ("cambio", por_cambio),
                           ("registro", por_registro), ("estudio", por_estudio)]:
            r, nada, ok = hacer(f"Clave-1!{NUL}x")
            chequear(r.status_code == 422 and ok,
                     f"clave con NUL por {via}: {r.status_code} {r.text[:100]}, {nada}")

        # 2. NUL en cada texto del alta
        for alta, campo in [(registro, "name"), (registro, "invite_token"), (registro, "username"),
                            (registro, "email"), (registro, "plan"),
                            (estudio, "name"), (estudio, "username"), (estudio, "email")]:
            _, r = alta(**{campo: f"E{NUL}x"})
            chequear(r.status_code < 500, f"NUL en {alta.__name__}.{campo}: {r.status_code} {r.text[:100]}")
finally:
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
