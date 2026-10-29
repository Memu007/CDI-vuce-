"""COBRO-MP-1 contra un Postgres de verdad (D31): SQLite no lo cubre.

Comprueba, con Mercado Pago simulado:
1. que `create_all` crea `mp_pagos_aplicados` con su clave primaria;
2. que un pago se aplica una vez y su reenvío no;
3. que dos avisos del mismo pago a la vez se aplican una sola vez;
4. que dos pagos distintos de la misma cuenta a la vez se acreditan los dos
   (vuelta 2, a): recarga y plan, de un usuario y de una organización. Sin
   candado sobre la cuenta, el segundo guardado pisa al primero;
5. que un pago que no alcanza queda «rechazado» y no toca la cuenta;
6. que un dato que se leyó de Mercado Pago y no entra en su columna (largo,
   de otro tipo, con NUL o con un surrogate suelto) no da 500: el pago queda
   aplicado o rechazado (vuelta 2, b).

Para que la carrera pase de verdad, el primer aviso que busca su pago en
mp_pagos_aplicados espera a ver al otro: o el otro también lo buscó (no hubo
candado sobre la cuenta) o Postgres lo muestra esperando un lock
(pg_stat_activity). Esperar ahí, y no al leer la cuenta, deja a los dos con
la búsqueda hecha y ninguno guardado: sin candado, la única que puede frenar
el mismo pago dos veces es la clave primaria (D14). Si no ve ninguna de las
dos en 5 s, el caso no probó la carrera y falla.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/cobro_mp1_postgres.py postgresql://cdi@127.0.0.1:55432/cdi_prueba

La base tiene que estar vacía: el script crea las tablas.
"""
import asyncio
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_host = urlparse(URL).hostname or ""
if not URL.startswith("postgresql://") or _host not in ("127.0.0.1", "localhost"):
    sys.exit("uso: cobro_mp1_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

os.environ.update(
    DATABASE_URL=URL, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import psycopg2  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

import proyecto_maria.main as main_mod  # noqa: E402
from proyecto_maria.core.rate_limit import limiter  # noqa: E402

PAGOS = {}


class _Pagos:
    def get(self, pid):
        return {"status": 200, "response": PAGOS[str(pid)]}


class _SDK:
    def __init__(self, token):
        pass

    def payment(self):
        return _Pagos()


main_mod.mercadopago.SDK = _SDK
main_mod.MP_WEBHOOK_SECRET = "secreto-de-prueba"
main_mod.MP_ACCESS_TOKEN = "TEST-fake"
main_mod.IS_PRODUCTION = False
limiter.enabled = False

FALLAS = []


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def sql(consulta, *args):
    with psycopg2.connect(URL) as con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall()


def esperando_un_lock():
    return sql("""select count(*) from pg_stat_activity
                  where datname = current_database() and wait_event_type = 'Lock'""")[0][0]


def pago(pid, ref, monto):
    PAGOS[pid] = {"id": pid, "status": "approved", "external_reference": ref,
                  "transaction_amount": monto, "currency_id": "ARS", "payer": {"id": "p"},
                  "date_approved": datetime.now(timezone.utc).isoformat()}
    return pid


def extra(usuario):
    return sql("select coalesce(extra_ops_remaining, 0) from users where username=%s", usuario)[0][0]


# Dentro del aviso, el primero que busca su pago ya anotado espera a ver al otro.
LLEGADAS = []
VISTO = []
_get_original = AsyncSession.get


def _en_el_aviso():
    marco = sys._getframe(2)
    while marco is not None:
        if marco.f_code.co_name == "mercadopago_webhook":
            return True
        marco = marco.f_back
    return False


async def _esperar_al_otro():
    for _ in range(500):
        if len(LLEGADAS) >= 2:
            VISTO.append("llegaron los dos")
            return
        if await asyncio.to_thread(esperando_un_lock):
            VISTO.append("el otro espera el lock")
            return
        await asyncio.sleep(0.01)
    VISTO.append("nada")


async def _get_con_carrera(self, entidad, *args, **kwargs):
    resultado = await _get_original(self, entidad, *args, **kwargs)
    if getattr(entidad, "__tablename__", None) == "mp_pagos_aplicados" and _en_el_aviso():
        LLEGADAS.append(1)
        if len(LLEGADAS) == 1:
            await _esperar_al_otro()
    return resultado


AsyncSession.get = _get_con_carrera


def ipn(pid):
    return f"/api/payments/webhook?topic=payment&id={pid}"


def a_la_vez(c, *pids):
    LLEGADAS.clear()
    VISTO.clear()
    with ThreadPoolExecutor(len(pids)) as hilos:
        return list(hilos.map(lambda pid: c.post(ipn(pid)), pids))


def se_cruzaron(que):
    chequear(VISTO[:1] in (["llegaron los dos"], ["el otro espera el lock"]),
             f"{que}: los dos avisos se cruzaron ({VISTO})")


with TestClient(main_mod.app) as c:
    pk = sql("""select a.attname from pg_index i join pg_attribute a
                on a.attrelid = i.indrelid and a.attnum = any(i.indkey)
                where i.indrelid = 'mp_pagos_aplicados'::regclass and i.indisprimary""")
    chequear(pk == [("payment_id",)], f"create_all creó mp_pagos_aplicados con clave primaria payment_id ({pk})")

    usuario = f"pg_{uuid.uuid4().hex[:8]}"
    r = c.post("/auth/register", json={"username": usuario, "password": "SecureP@ss1",
                                       "email": f"{usuario}@example.com", "name": usuario})
    chequear(r.status_code == 200, f"registro ({r.status_code})")
    c.cookies.clear()
    precio = float(main_mod.billing_service.PLANS["premium"]["price"])
    recarga = float(main_mod.billing_service.TOPUP_PRICE_ARS)

    a = pago(f"pa-{usuario}", f"{usuario}:topup", recarga)
    antes = extra(usuario)
    r1, r2 = c.post(ipn(a)), c.post(ipn(a))
    chequear(r1.json().get("skipped") is None and r2.json().get("skipped") == "payment_id ya procesado"
             and extra(usuario) == antes + 10, f"un pago se aplica una vez ({r1.text[:80]} / {r2.text[:80]})")

    que = "el mismo pago dos veces a la vez"
    b = pago(f"pb-{usuario}", f"{usuario}:topup", recarga)
    antes = extra(usuario)
    respuestas = a_la_vez(c, b, b)
    salteados = [r.json().get("skipped") for r in respuestas]
    se_cruzaron(que)
    chequear([r.status_code for r in respuestas] == [200, 200]
             and salteados.count("payment_id ya procesado") == 1 and salteados.count(None) == 1,
             f"{que}: uno aplicado y otro salteado ({[r.status_code for r in respuestas]}, {salteados})")
    chequear(extra(usuario) == antes + 10, f"{que}: suma una sola recarga ({antes} → {extra(usuario)})")
    filas = sql("select count(*) from mp_pagos_aplicados where payment_id=%s", b)[0][0]
    chequear(filas == 1, f"{que}: deja una fila ({filas})")

    # Dos pagos distintos de la misma cuenta a la vez: se acreditan los dos.
    org_id = str(uuid.uuid4())
    sql("""insert into organizations (id, name, owner_username, plan, billing_status, trial_ends_at,
                                      ops_used_this_period, extra_ops_remaining)
           values (%s, 'Estudio Inventado', %s, 'premium', 'active', now() + interval '10 days', 0, 0)
           returning id""", org_id, usuario)
    cuentas = {"del usuario": (usuario, "users", "username"),
               "de la organización": (f"org:{org_id}", "organizations", "id")}
    for nombre, (ref, tabla, clave) in cuentas.items():
        valor = usuario if tabla == "users" else org_id

        def leer(columna):
            return sql(f"select {columna} from {tabla} where {clave} = %s", valor)[0][0]

        que = f"dos recargas {nombre} a la vez"
        antes = leer("coalesce(extra_ops_remaining, 0)")
        pids = [pago(f"r{n}-{uuid.uuid4().hex[:8]}", f"{ref}:topup", recarga) for n in (1, 2)]
        respuestas = a_la_vez(c, *pids)
        se_cruzaron(que)
        chequear([(r.status_code, r.json().get("skipped")) for r in respuestas] == [(200, None), (200, None)],
                 f"{que}: los dos se aplican ({[r.text[:80] for r in respuestas]})")
        despues = leer("coalesce(extra_ops_remaining, 0)")
        chequear(despues == antes + 20, f"{que}: suman 20 ({antes} → {despues})")

        que = f"dos pagos de plan {nombre} a la vez"
        antes = leer("trial_ends_at")
        pids = [pago(f"p{n}-{uuid.uuid4().hex[:8]}", f"{ref}:premium", precio) for n in (1, 2)]
        respuestas = a_la_vez(c, *pids)
        se_cruzaron(que)
        chequear([(r.status_code, r.json().get("skipped")) for r in respuestas] == [(200, None), (200, None)],
                 f"{que}: los dos se aplican ({[r.text[:80] for r in respuestas]})")
        dias = (leer("trial_ends_at") - antes).days
        chequear(dias == 60, f"{que}: suman 60 días ({dias})")

    m = pago(f"pm-{usuario}", f"{usuario}:topup", recarga / 2)
    antes = extra(usuario)
    r = c.post(ipn(m))
    fila = sql("select estado, monto_esperado, motivo from mp_pagos_aplicados where payment_id=%s", m)
    chequear(r.status_code == 200 and extra(usuario) == antes and fila and fila[0][0] == "rechazado",
             f"un pago que no alcanza queda rechazado y no suma ({r.status_code}, {fila})")

    # Un caso por columna: cada dato raro, solo, en un pago que si no, se aplicaría.
    raros = {
        "la cuenta inexistente larga": ("rechazado", {"external_reference": f"{'x' * 250}:topup"}),
        "la cuenta inexistente con NUL": ("rechazado", {"external_reference": f"{usuario}\x00:topup"}),
        "la cuenta inexistente con un surrogate": ("rechazado", {"external_reference": f"{usuario}\ud800:topup"}),
        "la moneda con NUL": ("rechazado", {"currency_id": "AR\x00S"}),
        "la fecha con NUL": ("rechazado", {"date_approved": datetime.now(timezone.utc).isoformat() + "\x00"}),
        "los últimos 4 largos": ("aplicado", {"card": {"last_four_digits": "123456789"}}),
        "la marca larga": ("aplicado", {"card": {"network": "v" * 30}}),
        "la marca en una lista": ("aplicado", {"card": {"network": ["visa"]}}),
        "el pagador largo": ("aplicado", {"payer": {"id": "9" * 300}}),
    }
    for nombre, (estado, cambio) in raros.items():
        pid = pago(f"px{len(PAGOS)}-{uuid.uuid4().hex[:8]}", f"{usuario}:topup", recarga)
        PAGOS[pid].update(cambio)
        r = c.post(ipn(pid))
        fila = sql("select estado from mp_pagos_aplicados where payment_id=%s", pid)
        chequear(r.status_code == 200 and fila == [(estado,)],
                 f"un pago con {nombre} queda {estado} ({r.status_code}, {fila})")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
