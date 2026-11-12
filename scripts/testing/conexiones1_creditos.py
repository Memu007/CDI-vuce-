"""Créditos extra vencidos: una operación nueva y una recarga a la vez no pierden la recarga.

La cuenta tiene créditos extra vencidos. Al crear una operación, la app los
vence en memoria; si ese vencimiento se escribe después de que la recarga
sumó, la recarga se pierde. Corre, para el usuario y para la organización:

- control: la recarga termina antes de pedir el alta;
- carrera: la fila de la cuenta queda tomada por el arnés; se pide la recarga
  y se espera a verla esperando el candado en pg_stat_activity; se pide el
  alta y se espera a ver un segundo pedido esperando; recién ahí se suelta.

Después de cada fase tiene que quedar la recarga entera (TOPUP_OPS) y su
vencimiento. Mercado Pago es simulado.

uso: scripts/testing/con_pg16.sh python scripts/testing/conexiones1_creditos.py
Sale 0 si no se pierde nada, 1 si se pierde una recarga, 2 si la medición no
vale (un pedido no dio lo esperado) y 3 si la carrera no se armó.
"""
import inspect
import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from urllib.parse import urlparse

URL = os.environ.get("BACKUP1A_PG_URL", "")
if urlparse(URL).hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: scripts/testing/con_pg16.sh python scripts/testing/conexiones1_creditos.py")

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
from tests.mp_firma import aviso_firmado  # noqa: E402

PAGOS = {}


class _SDK:
    def __init__(self, token):
        pass

    def payment(self):
        return self

    def get(self, pid):
        return {"status": 200, "response": PAGOS[str(pid)]}


main_mod.mercadopago.SDK = _SDK
main_mod.MP_WEBHOOK_SECRET = "secreto-de-prueba"
main_mod.MP_ACCESS_TOKEN = "TEST-fake"
main_mod.IS_PRODUCTION = False
limiter.enabled = False  # del arnés: el limitador no es lo que se mide
RECARGA = main_mod.billing_service.TOPUP_OPS
PLAZO = 15


class Invalida(Exception):
    pass


def sql(consulta, *args):
    with psycopg2.connect(URL) as con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall() if cur.description else None


def esperando():
    return [q for (q,) in sql("""select query from pg_stat_activity
                                  where datname = current_database() and wait_event_type = 'Lock'""")]


def hasta(condicion):
    fin = time.monotonic() + PLAZO
    while time.monotonic() < fin:
        if condicion():
            return True
        time.sleep(0.02)
    return False


def exigir(ok, que):
    if not ok:
        raise Invalida(que)


def preparar(c, de_org):
    usuario = f"cr_{uuid.uuid4().hex[:10]}"
    r = c.post("/auth/register", json={"username": usuario, "password": "SecureP@ss1",
                                       "email": f"{usuario}@example.com", "name": usuario})
    exigir(r.status_code == 200, f"registro {r.status_code}")
    sesion = {"Authorization": f"Bearer {r.json()['access_token']}"}
    c.cookies.clear()
    r = c.post("/api/clientes", headers=sesion, json={"nombre": "C"})
    exigir(r.status_code == 200, f"cliente {r.status_code}")
    cliente = r.json()["cliente"]["id"]
    vencidos = "extra_ops_remaining = 5, extra_ops_expires_at = now() - interval '1 day'"
    al_dia = "plan = 'premium', billing_status = 'active', trial_ends_at = now() + interval '10 days'"
    if de_org:
        org = str(uuid.uuid4())
        sql("""insert into organizations (id, name, owner_username, ops_used_this_period, plan,
                billing_status, trial_ends_at, extra_ops_remaining, extra_ops_expires_at)
                values (%s, 'Estudio Inventado', %s, 0, 'premium', 'active', now() + interval '10 days',
                        5, now() - interval '1 day')""", org, usuario)
        sql("update users set organization_id = %s where username = %s", org, usuario)
        return sesion, cliente, f"org:{org}", ("organizations", "id", org)
    sql(f"update users set {vencidos}, {al_dia} where username = %s", usuario)
    return sesion, cliente, usuario, ("users", "username", usuario)


def recargar(c, ref):
    pid = f"cr-{uuid.uuid4().hex[:10]}"
    PAGOS[pid] = {"id": pid, "status": "approved", "external_reference": f"{ref}:topup",
                  "transaction_amount": float(main_mod.billing_service.TOPUP_PRICE_ARS),
                  "currency_id": "ARS", "payer": {"id": "p"},
                  "date_approved": datetime.now(timezone.utc).isoformat()}
    return pid, c.post("/api/payments/webhook", **aviso_firmado("payment", pid, "secreto-de-prueba"))


def alta(c, sesion, cliente):
    return c.post("/api/operations/manual", headers=sesion,
                  json={"client_id": cliente, "items": [{"descripcion": "D", "cantidad": 1}]})


def validar(pid, r_aviso, r_alta):
    exigir(r_aviso.status_code == 200 and r_aviso.json().get("skipped") is None,
           f"recarga {r_aviso.status_code} {r_aviso.text[:120]}")
    fila = sql("select estado from mp_pagos_aplicados where payment_id = %s", pid)
    exigir(fila == [("aplicado",)], f"recarga no aplicada: {fila}")
    exigir(r_alta.status_code == 200, f"alta {r_alta.status_code} {r_alta.text[:120]}")
    op = sql("select count(*) from operations where id = %s", r_alta.json().get("operation_id"))
    exigir(op == [(1,)], f"alta sin operación guardada: {op}")


def fase_control(c, de_org):
    sesion, cliente, ref, cuenta = preparar(c, de_org)
    pid, r_aviso = recargar(c, ref)
    return pid, r_aviso, alta(c, sesion, cliente), [], cuenta


def fase_carrera(c, de_org):
    sesion, cliente, ref, cuenta = preparar(c, de_org)
    tabla, clave, valor = cuenta
    candado = psycopg2.connect(URL)
    try:
        with candado.cursor() as cur:
            cur.execute(f"select 1 from {tabla} where {clave} = %s for update", (valor,))
        with ThreadPoolExecutor(2) as hilos:
            aviso = hilos.submit(recargar, c, ref)
            if not hasta(lambda: len(esperando()) >= 1):
                raise Invalida("carrera: la recarga no llegó a esperar el candado")
            pedido = hilos.submit(alta, c, sesion, cliente)
            if not hasta(lambda: len(esperando()) >= 2):
                raise Invalida(f"carrera: el alta no llegó a esperar (terminó: {pedido.done()})")
            consultas = [" ".join(q.split())[:90] for q in esperando()]
            candado.rollback()
            pid, r_aviso = aviso.result(PLAZO)
            return pid, r_aviso, pedido.result(PLAZO), consultas, cuenta
    finally:
        candado.rollback()
        candado.close()


def arbol():
    fuente = inspect.getsource(main_mod.require_active_billing)
    return (f"{main_mod.__file__}; require_active_billing con commit: {'db.commit()' in fuente}; "
            f"_leer_cuerpo: {hasattr(main_mod, '_leer_cuerpo')}")


def main():
    print(arbol())
    perdidas, invalidas, sin_carrera = 0, 0, 0
    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        for de_org in (False, True):
            for nombre, fase in (("control", fase_control), ("carrera", fase_carrera)):
                que = f"{'organización' if de_org else 'usuario'}, {nombre}"
                try:
                    pid, r_aviso, r_alta, consultas, (tabla, clave, valor) = fase(c, de_org)
                    validar(pid, r_aviso, r_alta)
                except Invalida as e:
                    carrera = str(e).startswith("carrera:")
                    sin_carrera += carrera
                    invalidas += not carrera
                    print(f"NO VALE | {que}: {e}")
                    continue
                quedan, vence = sql(f"select coalesce(extra_ops_remaining, 0), extra_ops_expires_at "
                                    f"from {tabla} where {clave} = %s", valor)[0]
                perdio = max(RECARGA - quedan, 0)
                ok = quedan == RECARGA and vence is not None
                perdidas += not ok
                print(f"{'OK   ' if ok else 'PIERDE'} | {que}: quedan {quedan} de {RECARGA} pagos "
                      f"(perdidos {perdio}), vencimiento {'sí' if vence else 'no'}")
                for q in consultas:
                    print(f"        esperaba: {q}")
    print(f"pierden: {perdidas}; no valen: {invalidas}; sin carrera: {sin_carrera}")
    return 1 if perdidas else 2 if invalidas else 3 if sin_carrera else 0


if __name__ == "__main__":
    sys.exit(main())
