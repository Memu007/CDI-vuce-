"""La columna users.cancelar_sin_confirmar contra un Postgres de verdad: el
arranque la agrega a una base que ya tiene datos, la marca se guarda con el 503
de cancelar y se borra al conciliar, un segundo arranque no cambia nada, y la
vuelta atrás la saca sin tocar el resto de la fila.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/cobro_mp4_postgres.py postgresql://cdi@127.0.0.1:55432/cdi_prueba
  (o con su propio Postgres: PY=python scripts/testing/con_pg16.sh \
     bash -c '"$0" scripts/testing/cobro_mp4_postgres.py "$BACKUP1A_PG_URL"' python)
La base tiene que estar vacía: el script crea las tablas.
"""
import os
import sys
from contextlib import closing
import types
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
if not URL.startswith("postgresql://") or (urlparse(URL).hostname or "") not in ("127.0.0.1", "localhost"):
    sys.exit("uso: cobro_mp4_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

os.environ.update(
    DATABASE_URL=URL, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
    MP_ACCESS_TOKEN="TEST-fake", MP_PREAPPROVAL_PLAN_ID_PREMIUM="plan-premium",
)
os.environ.pop("FRONTEND_URL", None)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import httpx  # noqa: E402
import psycopg2  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import proyecto_maria.main as main_mod  # noqa: E402
from proyecto_maria.core.rate_limit import limiter  # noqa: E402
from proyecto_maria.database.connection import engine  # noqa: E402
from tests.test_cobro_mp2 import FALLA, SUS, _RUTA_SUS, _SDK, _api_mp  # noqa: E402

limiter.enabled = False
main_mod.mercadopago.SDK = _SDK
main_mod.MP_ACCESS_TOKEN = "TEST-fake"
main_mod.IS_PRODUCTION = False
_simulado = types.SimpleNamespace(**{k: getattr(httpx, k) for k in dir(httpx) if not k.startswith("_")})
_simulado.Client = lambda **kw: httpx.Client(transport=httpx.MockTransport(_api_mp), **kw)
main_mod.httpx = _simulado

COLUMNA = "cancelar_sin_confirmar"
FALLAS = []


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def sql(consulta, *args):
    # El «with» de psycopg2 cierra la transacción, no la conexión.
    with closing(psycopg2.connect(URL)) as con, con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall() if cur.description else None


def columnas():
    return {nombre: (tipo, largo, nula) for nombre, tipo, largo, nula in sql(
        "select column_name, data_type, character_maximum_length, is_nullable from information_schema.columns "
        "where table_schema = current_schema() and table_name = 'users'")}


def filas():
    """Todo users salvo la columna nueva, para ver que ni el arranque ni la vuelta atrás tocan el resto."""
    nombres = sorted(c for c in columnas() if c != COLUMNA)
    return sql(f"select {', '.join(nombres)} from users order by username")


def arrancar():
    """Cada TestClient corre en su propio loop: el pool de asyncpg no puede pasar de uno a otro."""
    engine.sync_engine.dispose(close=False)
    return TestClient(main_mod.app)


def entrar(c, usuario):
    r = c.post("/auth/login", json={"username": usuario, "password": "SecureP@ss1"})
    assert r.status_code == 200, r.text
    c.cookies.clear()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# 1. La base de antes: tablas, un estudio con datos y la columna todavía sin agregar.
with arrancar() as c:
    nombres = {k: f"mp4_{k}_{uuid.uuid4().hex[:8]}" for k in ("duena", "abrio")}
    for u in nombres.values():
        r = c.post("/auth/register", json={"username": u, "password": "SecureP@ss1",
                                           "email": f"{u}@example.com", "name": u})
        assert r.status_code == 200, r.text
org_id, sid = str(uuid.uuid4()), f"sus-{nombres['abrio']}"
sql("insert into organizations (id, name, owner_username, plan, billing_status, trial_ends_at, payment_provider, "
    "ops_used_this_period, extra_ops_remaining) values (%s, 'Estudio', %s, 'premium', 'active', %s, "
    "'mercadopago', 0, 0)", org_id, nombres["duena"], datetime.now(timezone.utc) + timedelta(days=20))
sql("update users set organization_id = %s where username in (%s, %s)", org_id, *nombres.values())
sql("update users set mp_preapproval_id = %s where username = %s", sid, nombres["abrio"])
sql(f"alter table users drop column {COLUMNA}")
antes = filas()
chequear(COLUMNA not in columnas() and len(antes) >= 2, f"la base de antes no tiene la columna y tiene {len(antes)} cuentas")

# 2. El arranque la agrega; la marca va y viene con el 503 de cancelar.
with arrancar() as c:
    chequear(columnas().get(COLUMNA) == ("character varying", 100, "YES"), f"el arranque agrega {COLUMNA}")
    chequear(filas() == antes and sql(f"select count(*) from users where {COLUMNA} is not null")[0][0] == 0,
             "el arranque no toca las filas y la marca nace vacía")
    SUS[sid] = "authorized"

    def _cancela_sin_confirmar(request):
        s = _RUTA_SUS.fullmatch(str(request.url)).group(1)
        if request.method == "PUT":
            SUS[s] = "cancelled"
            FALLA["GET"] = _cancela_sin_confirmar
        if "GET" in FALLA or request.method == "PUT":
            return httpx.Response(500, json={})
        return httpx.Response(200, json={"id": s, "status": SUS[s]})
    FALLA["PUT"] = _cancela_sin_confirmar
    token = entrar(c, nombres["abrio"])
    r = c.post("/api/billing/cancel", headers=token)
    FALLA.clear()
    marca = sql(f"select {COLUMNA} from users where username = %s", nombres["abrio"])[0][0]
    chequear(r.status_code == 503 and marca == sid, f"el 503 guarda la marca: {r.status_code} {marca!r}")
    r = c.post("/api/billing/cancel", headers=token)
    guardado = sql(f"select {COLUMNA}, mp_preapproval_id from users where username = %s", nombres["abrio"])[0]
    estado = sql("select billing_status from organizations where id = %s", org_id)[0][0]
    chequear(r.status_code == 200 and guardado == (None, None) and estado == "canceled",
             f"el reintento concilia y borra la marca: {r.status_code} {guardado} {estado}")
    sql(f"update users set {COLUMNA} = 'sus-quedo' where username = %s", nombres["duena"])
    despues = filas()

# 3. Un segundo arranque no cambia nada: ni la columna ni lo guardado en ella.
with arrancar():
    chequear(columnas().get(COLUMNA) == ("character varying", 100, "YES") and filas() == despues
             and sql(f"select {COLUMNA} from users where username = %s", nombres["duena"])[0][0] == "sus-quedo",
             "el segundo arranque no cambia la columna ni lo guardado")

# 4. Vuelta atrás: la columna se va y el resto de la fila queda.
VUELTA_ATRAS = f"alter table users drop column if exists {COLUMNA}"
sql(VUELTA_ATRAS)
chequear(COLUMNA not in columnas() and filas() == despues, "la vuelta atrás saca la columna y deja el resto")
sql(VUELTA_ATRAS)
chequear(COLUMNA not in columnas(), "la vuelta atrás, dos veces, no falla")

print(f"vuelta atrás: {VUELTA_ATRAS}")
print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
