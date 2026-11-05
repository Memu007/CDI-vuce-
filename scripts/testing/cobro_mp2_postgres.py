"""Una sola suscripción por organización, contra un Postgres de verdad: SQLite
serializa las escrituras y no muestra los cruces.

1. Dos miembros de la misma organización pagan a la vez: tiene que quedar una
   sola suscripción viva en Mercado Pago (simulado), y es la que CDI guarda.
   El primero que bloquea la organización espera a ver al otro esperando el
   lock; si no lo ve en 5 s, el caso no probó el cruce y falla.
2. Un miembro con una suscripción pendiente genera (bloquea su fila y después
   la de la organización, en el orden de la generación) mientras otro paga:
   el checkout espera y termina, sin que Postgres corte a nadie por deadlock.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/cobro_mp2_postgres.py postgresql://cdi@127.0.0.1:55432/cdi_prueba
La base tiene que estar vacía: el script crea las tablas.
"""
import asyncio
import os
import sys
import threading
import types
import uuid
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
if not URL.startswith("postgresql://") or (urlparse(URL).hostname or "") not in ("127.0.0.1", "localhost"):
    sys.exit("uso: cobro_mp2_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

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
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

import proyecto_maria.main as main_mod  # noqa: E402
from proyecto_maria.core.rate_limit import limiter  # noqa: E402
from tests.test_cobro_mp2 import SUS, _api_mp, _SDK  # noqa: E402

limiter.enabled = False
main_mod.mercadopago.SDK = _SDK
main_mod.MP_ACCESS_TOKEN = "TEST-fake"
main_mod.IS_PRODUCTION = False
# httpx de main con la API simulada: el TestClient sigue con el de verdad.
_simulado = types.SimpleNamespace(**{k: getattr(httpx, k) for k in dir(httpx) if not k.startswith("_")})
_simulado.Client = lambda **kw: httpx.Client(transport=httpx.MockTransport(_api_mp), **kw)
main_mod.httpx = _simulado

FALLAS = []


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def sql(consulta, *args):
    with psycopg2.connect(URL) as con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall() if cur.description else None


def esperando_un_lock():
    return sql("""select count(*) from pg_stat_activity
                  where datname = current_database() and wait_event_type = 'Lock'""")[0][0]


CRUCE = []      # vacío: sin gancho; con un elemento: el caso 1 está corriendo
EN_ORG = []
VISTO = []
_execute_original = AsyncSession.execute


def _en_checkout():
    marco = sys._getframe(2)
    while marco is not None and marco.f_code.co_name != "billing_checkout":
        marco = marco.f_back
    return marco is not None


async def _execute_con_cruce(self, statement, *args, **kwargs):
    resultado = await _execute_original(self, statement, *args, **kwargs)
    tabla = getattr(getattr(statement, "column_descriptions", [{}])[0].get("entity"), "__tablename__", None) \
        if getattr(statement, "is_select", False) else None
    if not CRUCE or tabla != "organizations" or not _en_checkout():
        return resultado
    EN_ORG.append(1)
    if len(EN_ORG) == 1:
        for _ in range(500):
            if await asyncio.to_thread(esperando_un_lock):
                VISTO.append("el otro espera el lock")
                break
            if len(EN_ORG) >= 2:
                VISTO.append("llegaron los dos")
                break
            await asyncio.sleep(0.01)
        else:
            VISTO.append("nada")
    return resultado


AsyncSession.execute = _execute_con_cruce


def registrar(c, prefijo):
    usuario = f"{prefijo}_{uuid.uuid4().hex[:8]}"
    r = c.post("/auth/register", json={"username": usuario, "password": "SecureP@ss1",
                                       "email": f"{usuario}@example.com", "name": usuario})
    assert r.status_code == 200, r.text
    return usuario


def organizacion(*miembros):
    """Vencida y sin suscripción, para que cualquiera de los miembros pueda pagar."""
    org_id = str(uuid.uuid4())
    sql("insert into organizations (id, name, owner_username, plan, billing_status, trial_ends_at, "
        "ops_used_this_period, extra_ops_remaining) "
        "values (%s, 'Estudio', %s, 'premium', 'past_due', now() - interval '2 days', 0, 0)", org_id, miembros[0])
    for usuario in miembros:
        sql("update users set organization_id = %s where username = %s", org_id, usuario)
    return org_id


def bearer(c, usuario):
    """Un solo TestClient (un loop para el pool de asyncpg) y cada miembro con su token."""
    r = c.post("/auth/login", json={"username": usuario, "password": "SecureP@ss1"})
    assert r.status_code == 200, r.text
    c.cookies.clear()
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def vivas_y_guardadas(org_id):
    vivas = sorted(s for s, e in SUS.items() if e != "cancelled")
    guardadas = sorted(s for (s,) in sql("select mp_preapproval_id from users where organization_id = %s "
                                         "and mp_preapproval_id is not null", org_id))
    return vivas, guardadas


with TestClient(main_mod.app) as c:
    que = "dos miembros pagan a la vez"
    SUS.clear()
    a, b = registrar(c, "mp2pg_a"), registrar(c, "mp2pg_b")
    org_id = organizacion(a, b)
    tokens = [bearer(c, a), bearer(c, b)]
    CRUCE.append(1)
    with ThreadPoolExecutor(2) as hilos:
        pedidos = [hilos.submit(c.post, "/api/billing/checkout", json={"plan": "premium"}, headers=t)
                   for t in tokens]
        respuestas = [p.result() for p in pedidos]
    CRUCE.clear()
    codigos = sorted(r.status_code for r in respuestas)
    chequear(VISTO[:1] in (["llegaron los dos"], ["el otro espera el lock"]), f"{que}: los dos pedidos se cruzaron ({VISTO})")
    chequear(codigos in ([200, 200], [200, 409]),
             f"{que}: uno crea y el otro crea o recibe 409 ({[(r.status_code, r.text[:90]) for r in respuestas]})")
    vivas, guardadas = vivas_y_guardadas(org_id)
    chequear(len(vivas) == 1, f"{que}: queda una sola suscripción viva en Mercado Pago ({vivas})")
    chequear(vivas == guardadas, f"{que}: la viva es la que CDI guarda ({vivas} / {guardadas})")

    que = "un miembro genera mientras otro paga"
    SUS.clear()
    paga, genera = registrar(c, "mp2pg_a"), registrar(c, "mp2pg_b")
    org_id = organizacion(paga, genera)
    vieja = f"vieja-{uuid.uuid4().hex[:8]}"
    SUS[vieja] = "pending"
    sql("update users set mp_preapproval_id = %s where username = %s", vieja, genera)
    token = bearer(c, paga)
    cortado = []
    con = psycopg2.connect(URL)
    try:
        cur = con.cursor()
        cur.execute("select 1 from users where username = %s for update", (genera,))
        with ThreadPoolExecutor(1) as hilo:
            checkout = hilo.submit(c.post, "/api/billing/checkout", json={"plan": "premium"}, headers=token)
            espera = threading.Event()
            for _ in range(500):
                if checkout.done() or esperando_un_lock():
                    break
                espera.wait(0.01)
            chequear(not checkout.done() and esperando_un_lock(), f"{que}: el checkout espera a quien genera")
            try:
                cur.execute("select 1 from organizations where id = %s for update", (org_id,))
                con.commit()
            except psycopg2.Error as e:
                cortado.append(type(e).__name__)
                con.rollback()
            try:
                r = checkout.result()
            except Exception as e:  # el TestClient relanza el error del servidor
                cortado.append(type(e).__name__)
                r = None
    finally:
        con.close()
    # Postgres corta a uno de los dos, el que detecte el ciclo: cualquiera es la misma falla.
    chequear(cortado == [] and r.status_code == 200,
             f"{que}: nadie queda cortado por deadlock ({cortado}; checkout: {r and r.status_code}, {r and r.text[:90]})")
    chequear(SUS[vieja] == "cancelled", f"{que}: la pendiente del otro miembro queda cancelada ({SUS[vieja]})")
    vivas, guardadas = vivas_y_guardadas(org_id)
    chequear(len(vivas) == 1 and vivas == guardadas, f"{que}: una sola viva y es la que CDI guarda ({vivas} / {guardadas})")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
