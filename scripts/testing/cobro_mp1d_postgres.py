"""COBRO-MP-1 D contra un Postgres de verdad: SQLite serializa las escrituras y
no muestra la carrera.

Dos /api/billing/checkout a la vez de la misma cuenta, con Mercado Pago
simulado. Al final tiene que quedar una sola suscripción viva en Mercado Pago
(no cancelada) y tiene que ser la que CDI guarda; si no, cancelar en CDI deja
la otra cobrando.
1. sin suscripción anterior;
2. con una suscripción anterior pendiente (los dos la ven);
3. un /api/billing/cancel mientras corre un checkout (hallazgo de los
   adversarios): si cancelar no espera al checkout, CDI queda cancelada y
   sin id, y la suscripción nueva sigue viva en Mercado Pago.

Para que la carrera pase de verdad, el primero que lee la cuenta en el
checkout espera a ver al otro: o el otro también la leyó (no hubo lock) o
Postgres lo muestra esperando un lock (pg_stat_activity). Si no ve ninguna de
las dos en 5 s, el caso no probó la carrera y falla.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/cobro_mp1d_postgres.py postgresql://cdi@127.0.0.1:55432/cdi_prueba

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
_host = urlparse(URL).hostname or ""
if not URL.startswith("postgresql://") or _host not in ("127.0.0.1", "localhost"):
    sys.exit("uso: cobro_mp1d_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

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
from tests.test_cobro_mp2 import CREADAS, SUS, _api_mp, _SDK  # noqa: E402

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


# El primero que lee la cuenta dentro del checkout espera a ver al otro.
# En el caso 3, el checkout espera a que cancelar haya leído la cuenta o
# esté esperando el lock.
LLEGADAS = []
VISTO = []
CON_CANCEL = []
CANCEL_LEYO = []
CHECKOUT_LEYO = threading.Event()
_execute_original = AsyncSession.execute


def _en(funcion):
    marco = sys._getframe(2)
    while marco is not None:
        if marco.f_code.co_name == funcion:
            return True
        marco = marco.f_back
    return False


async def _esperar_al_otro(llego):
    for _ in range(500):
        if llego():
            VISTO.append("llegaron los dos")
            return
        if await asyncio.to_thread(esperando_un_lock):
            VISTO.append("el otro espera el lock")
            return
        await asyncio.sleep(0.01)
    VISTO.append("nada")


async def _execute_con_carrera(self, statement, *args, **kwargs):
    resultado = await _execute_original(self, statement, *args, **kwargs)
    tabla = getattr(getattr(statement, "column_descriptions", [{}])[0].get("entity"), "__tablename__", None) \
        if getattr(statement, "is_select", False) else None
    if tabla != "users":
        return resultado
    if CON_CANCEL:
        if _en("cancel_billing"):
            CANCEL_LEYO.append(1)
        elif _en("billing_checkout"):
            CHECKOUT_LEYO.set()
            await _esperar_al_otro(lambda: CANCEL_LEYO)
        return resultado
    if not _en("billing_checkout"):
        return resultado
    LLEGADAS.append(1)
    if len(LLEGADAS) == 1:
        await _esperar_al_otro(lambda: len(LLEGADAS) >= 2)
    return resultado


AsyncSession.execute = _execute_con_carrera


def guardada(usuario):
    return sql("select mp_preapproval_id from users where username = %s", usuario)[0][0]


with TestClient(main_mod.app) as c:

    def a_la_vez(usuario):
        LLEGADAS.clear()
        VISTO.clear()
        c.cookies.clear()
        r = c.post("/auth/login", json={"username": usuario, "password": "SecureP@ss1"})
        assert r.status_code == 200, r.text
        with ThreadPoolExecutor(2) as hilos:
            return list(hilos.map(lambda _: c.post("/api/billing/checkout", json={"plan": "premium"}), range(2)))

    def caso(que, anterior=None):
        usuario = f"mp1d_{uuid.uuid4().hex[:8]}"
        r = c.post("/auth/register", json={"username": usuario, "password": "SecureP@ss1",
                                           "email": f"{usuario}@example.com", "name": usuario})
        assert r.status_code == 200, r.text
        SUS.clear()
        CREADAS.clear()
        if anterior:
            SUS[anterior] = "pending"
            sql("update users set mp_preapproval_id = %s where username = %s", anterior, usuario)
        respuestas = a_la_vez(usuario)
        chequear(VISTO[:1] in (["llegaron los dos"], ["el otro espera el lock"]),
                 f"{que}: los dos pedidos se cruzaron ({VISTO})")
        chequear([r.status_code for r in respuestas] == [200, 200],
                 f"{que}: los dos checkouts contestan 200 ({[(r.status_code, r.text[:80]) for r in respuestas]})")
        vivas = sorted(s for s, e in SUS.items() if e != "cancelled")
        chequear(len(vivas) == 1, f"{que}: queda una sola suscripción viva en Mercado Pago ({vivas})")
        chequear(vivas == [guardada(usuario)],
                 f"{que}: la viva es la que CDI guarda ({vivas} / {guardada(usuario)})")
        if anterior:
            chequear(SUS[anterior] == "cancelled", f"{que}: la anterior quedó cancelada ({SUS[anterior]})")

    caso("sin suscripción anterior")
    caso("con una pendiente anterior", anterior=f"vieja-{uuid.uuid4().hex[:8]}")

    # 3. Cancelar mientras corre el checkout de una cuenta vencida.
    que = "cancelar durante un checkout"
    usuario = f"mp1d_{uuid.uuid4().hex[:8]}"
    r = c.post("/auth/register", json={"username": usuario, "password": "SecureP@ss1",
                                       "email": f"{usuario}@example.com", "name": usuario})
    assert r.status_code == 200, r.text
    SUS.clear()
    CREADAS.clear()
    vieja = f"vieja-{uuid.uuid4().hex[:8]}"
    SUS[vieja] = "pending"
    sql("update users set billing_status = 'past_due', payment_provider = 'mercadopago', "
        "mp_preapproval_id = %s, trial_ends_at = now() - interval '2 days' where username = %s",
        vieja, usuario)
    LLEGADAS.clear()
    VISTO.clear()
    CANCEL_LEYO.clear()
    CHECKOUT_LEYO.clear()
    CON_CANCEL.append(1)
    c.cookies.clear()
    assert c.post("/auth/login", json={"username": usuario, "password": "SecureP@ss1"}).status_code == 200
    with ThreadPoolExecutor(2) as hilos:
        checkout = hilos.submit(c.post, "/api/billing/checkout", json={"plan": "premium"})
        chequear(CHECKOUT_LEYO.wait(10), f"{que}: el checkout leyó la cuenta")
        cancel = hilos.submit(c.post, "/api/billing/cancel")
        respuestas = [checkout.result(), cancel.result()]
    CON_CANCEL.clear()
    chequear(VISTO[:1] in (["llegaron los dos"], ["el otro espera el lock"]),
             f"{que}: los dos pedidos se cruzaron ({VISTO})")
    chequear([r.status_code for r in respuestas] == [200, 200],
             f"{que}: los dos contestan 200 ({[(r.status_code, r.text[:80]) for r in respuestas]})")
    estado, guardada_ = sql("select billing_status, mp_preapproval_id from users where username = %s",
                            usuario)[0]
    vivas = sorted(s for s, e in SUS.items() if e != "cancelled")
    chequear(estado == "canceled", f"{que}: la cuenta queda cancelada ({estado})")
    chequear(vivas == [], f"{que}: no queda ninguna suscripción viva en Mercado Pago ({vivas}, CDI guarda {guardada_})")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
