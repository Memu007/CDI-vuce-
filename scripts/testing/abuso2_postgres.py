"""Límites del login y de recuperar usuario contra un Postgres de verdad. En
Postgres `lower('İ')` es `i` y en Python no, así que el tope de recuperar
usuario contado sobre el texto pedido deja pasar variantes del mismo email que
la base resuelve a la misma cuenta. SQLite no lo muestra: su `lower` es ASCII.
Comprueba que:
1. cinco pedidos de recuperar usuario con variantes del mismo email, cada uno
   desde otra IP, mandan tres mails a la cuenta y los otros dos no mandan nada;
2. un login correcto perdona sólo los fallos de su propia cuenta (las mismas
   filas que tests/test_abuso2.py, en Postgres).

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/abuso2_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
"""
import os
import sys
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: abuso2_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

BASE = f"abuso2_{uuid.uuid4().hex[:8]}"
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
CLAVE = "Clave-sintetica-1!"


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


try:
    admin(f'create database "{BASE}"')
    from fastapi.testclient import TestClient  # noqa: E402
    import proyecto_maria.main as main_mod  # noqa: E402
    from proyecto_maria.core.rate_limit import limiter  # noqa: E402

    n_ip = iter(range(1, 10_000))

    def ip():
        return {"X-Forwarded-For": f"2001:db8::ab2:{next(n_ip):x}"}

    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        def registro(u):
            r = c.post("/auth/register", headers=ip(),
                       json={"username": u, "password": CLAVE, "email": f"{u}@ejemplo.test", "name": "Ab"})
            assert r.status_code == 200, r.text

        # 1. recuperar usuario: variantes con İ cuentan como la misma cuenta
        limiter.enabled = True
        u = "ab2_iii_" + uuid.uuid4().hex[:6]
        registro(u)
        enviados = []
        main_mod.send_email = lambda to, *a, **k: enviados.append(to) or True
        email = f"{u}@ejemplo.test"
        pos = [i for i, ch in enumerate(email) if ch == "i"]

        def con_i_turca(*cuales):
            return "".join("İ" if i in cuales else ch for i, ch in enumerate(email))

        variantes = [email, con_i_turca(pos[0]), con_i_turca(pos[1]), con_i_turca(pos[2]),
                     con_i_turca(pos[0], pos[1])]
        respuestas = [c.post("/auth/recover-username", json={"email": v}, headers=ip()) for v in variantes]
        codigos = [r.status_code for r in respuestas]
        chequear(codigos == [200] * 5, f"recuperar con variantes de İ contesta 200 a todas: {codigos}")
        chequear(enviados == [email] * 3,
                 f"cinco variantes del mismo email mandan tres mails a la cuenta: {len(enviados)} mandados")

        # 2. login correcto: perdona sólo lo propio
        limiter.enabled = False
        propia, otra = "ab2_p_" + uuid.uuid4().hex[:6], "ab2_o_" + uuid.uuid4().hex[:6]
        registro(propia)
        registro(otra)
        cuentas = {"propia": propia, "otra": otra, "nadie": "nadie_" + uuid.uuid4().hex[:6]}

        def login(quien, clave, h):
            return c.post("/auth/login", json={"username": cuentas[quien], "password": clave}, headers=h)

        for fallos, quedan in [(["otra"] * 4, 1), (["nadie"] * 4, 1),
                               (["otra", "otra", "propia", "propia"], 3), (["propia"] * 4, 5)]:
            h = ip()
            previos = [login(q, "mal", h).status_code for q in fallos]
            bien = login("propia", CLAVE, h).status_code
            despues = [login("otra", "mal", h).status_code for _ in range(6)]
            chequear(previos == [401] * len(fallos) and bien == 200
                     and despues == [401] * quedan + [429] * (6 - quedan),
                     f"fallos {fallos}, login bueno ({bien}), después {despues}: esperaba {quedan} 401")
finally:
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
