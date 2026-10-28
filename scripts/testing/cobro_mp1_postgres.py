"""COBRO-MP-1 contra un Postgres de verdad (D31): SQLite no lo cubre.

Comprueba, con Mercado Pago simulado:
1. que `create_all` crea `mp_pagos_aplicados` con su clave primaria;
2. que un pago se aplica una vez y su reenvío no;
3. que dos avisos del mismo pago a la vez se aplican una sola vez: los dos
   pasan el «¿ya está?» y la clave primaria frena al segundo al guardar;
4. que un pago que no alcanza queda «rechazado» y no toca la cuenta.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/cobro_mp1_postgres.py postgresql://cdi@127.0.0.1:55432/cdi_prueba

La base tiene que estar vacía: el script crea las tablas.
"""
import os
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
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


def pago(pid, ref, monto):
    PAGOS[pid] = {"id": pid, "status": "approved", "external_reference": ref,
                  "transaction_amount": monto, "currency_id": "ARS", "payer": {"id": "p"}}
    return pid


def extra(usuario):
    return sql("select coalesce(extra_ops_remaining, 0) from users where username=%s", usuario)[0][0]


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

    ipn = "/api/payments/webhook?topic=payment&id={}".format
    a = pago(f"pa-{usuario}", f"{usuario}:topup", 10000.0)
    antes = extra(usuario)
    r1, r2 = c.post(ipn(a)), c.post(ipn(a))
    chequear(r1.json().get("skipped") is None and r2.json().get("skipped") == "payment_id ya procesado"
             and extra(usuario) == antes + 10, f"un pago se aplica una vez ({r1.text[:80]} / {r2.text[:80]})")

    # Dos a la vez: los dos pasan el «¿ya está?» antes de que alguno guarde.
    original = main_mod._registrar_pago_mp
    pasaron = []

    async def _los_dos_pasan(*args, **kwargs):
        import asyncio
        estado = await original(*args, **kwargs)
        pasaron.append(estado)
        for _ in range(500):
            if len(pasaron) >= 2:
                break
            await asyncio.sleep(0.01)
        return estado

    main_mod._registrar_pago_mp = _los_dos_pasan
    b = pago(f"pb-{usuario}", f"{usuario}:topup", 10000.0)
    antes = extra(usuario)
    with ThreadPoolExecutor(2) as hilos:
        respuestas = list(hilos.map(lambda _: c.post(ipn(b)), range(2)))
    main_mod._registrar_pago_mp = original
    salteados = [r.json().get("skipped") for r in respuestas]
    chequear(pasaron == ["aplicado", "aplicado"], f"los dos avisos pasaron el «¿ya está?» ({pasaron})")
    chequear([r.status_code for r in respuestas] == [200, 200]
             and salteados.count("payment_id ya procesado") == 1 and salteados.count(None) == 1,
             f"dos a la vez: uno aplicado y otro salteado ({[r.status_code for r in respuestas]}, {salteados})")
    chequear(extra(usuario) == antes + 10, f"dos a la vez suman una sola recarga ({antes} → {extra(usuario)})")
    filas = sql("select count(*) from mp_pagos_aplicados where payment_id=%s", b)[0][0]
    chequear(filas == 1, f"dos a la vez dejan una fila ({filas})")

    m = pago(f"pm-{usuario}", f"{usuario}:topup", 5000.0)
    antes = extra(usuario)
    r = c.post(ipn(m))
    fila = sql("select estado, monto_esperado, motivo from mp_pagos_aplicados where payment_id=%s", m)
    chequear(r.status_code == 200 and extra(usuario) == antes and fila and fila[0][0] == "rechazado",
             f"un pago que no alcanza queda rechazado y no suma ({r.status_code}, {fila})")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
