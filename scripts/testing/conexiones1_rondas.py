"""Lo común de los casos de dos pedidos a la vez sobre la misma cuenta.

ronda() toma la fila de la cuenta, larga los dos pedidos, espera verlos
esperando y suelta. Mercado Pago es simulado.
"""
import gc
import os
import sys
import traceback
import uuid
import warnings
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conexiones1_creditos as h  # noqa: E402
import psycopg2  # noqa: E402
from proyecto_maria.database.connection import engine  # noqa: E402
from tests.mp_firma import aviso_firmado  # noqa: E402
from tests.test_maria7_rechazos_24_10 import _pedido  # noqa: E402

m, SUSCRIPCIONES, COBROS = h.main_mod, {}, {}
m._leer_cobro_autorizado_mp = COBROS.__getitem__
h._SDK.preapproval = lambda self: type("P", (), {
    "get": lambda _, sid: {"status": 200, "response": SUSCRIPCIONES[sid]}})()


def renovar(c, ref, *_):
    pid, sid, plan = f"rn-{uuid.uuid4().hex[:10]}", f"sus-{uuid.uuid4().hex[:8]}", f"{ref}:premium"
    precio = float(m.billing_service.PLANS["premium"]["price"])
    SUSCRIPCIONES[sid] = {"external_reference": plan, "auto_recurring": {"transaction_amount": precio}}
    COBROS[pid] = {"payment": {"id": pid}, "preapproval_id": sid}
    h.PAGOS[pid] = {"id": pid, "status": "approved", "external_reference": plan, "preapproval_id": sid,
                    "transaction_amount": precio, "currency_id": "ARS", "payer": {"id": "p"},
                    "date_approved": datetime.now(timezone.utc).isoformat()}
    return c.post("/api/payments/webhook", **aviso_firmado("subscription_authorized_payment", pid, "secreto-de-prueba"))


PEDIDOS = {
    "alta": lambda c, ref, s, cl: h.alta(c, s, cl),
    "guardado": lambda c, ref, s, cl: c.post(f"/api/clientes/{cl}/operaciones", headers=s, json={"items": []}),
    "recarga": lambda c, ref, *_: h.recargar(c, ref)[1],
    "maria": lambda c, ref, s, cl: c.post("/generate_maria", headers=s, json={
        **_pedido(), "operation_id": f"F{uuid.uuid4().hex[:8]}", "operacion_id": ""}),
    "renovación": renovar,
    "cancelar": lambda c, ref, s, cl: c.post("/api/billing/cancel", headers=s),
    "reactivar": lambda c, ref, s, cl: c.post("/api/billing/reactivate", headers=s),
}
DEADLOCKS = "select deadlocks from pg_stat_database where datname = current_database()"
DE_LA_APP = (" from pg_stat_activity where datname = current_database()"
             " and backend_type = 'client backend' and pid <> pg_backend_pid()")
OTRAS = "select count(*)" + DE_LA_APP
QUE_HACEN = ("select state, coalesce(wait_event_type || ':' || wait_event, 'nada'),"
             " round(extract(epoch from now() - state_change)::numeric, 1),"
             " left(regexp_replace(query, '\\s+', ' ', 'g'), 80)" + DE_LA_APP)


def ronda(c, a, b, de_org, ajuste):
    """Pone la cuenta según ajuste (un SET de SQL) y corre a y b con la fila tomada.
    Da (códigos, deadlocks, consultas que esperaban o None si no se armó, (tabla, clave, valor))."""
    sesion, cliente, ref, cuenta = h.preparar(c, de_org)
    h.sql(f"update {cuenta[0]} set {ajuste} where {cuenta[1]} = %s", cuenta[2])
    antes, consultas = h.sql(DEADLOCKS)[0][0], None
    with ThreadPoolExecutor(2) as hilos, closing(psycopg2.connect(h.URL)) as candado:
        try:
            with candado.cursor() as cur:
                cur.execute(f"select pg_backend_pid() from {cuenta[0]} where {cuenta[1]} = %s for update",
                            (cuenta[2],))
                mio = cur.fetchone()[0]
            futuros = [hilos.submit(PEDIDOS[a], c, ref, sesion, cliente)]
            if h.hasta(lambda: len(h.esperando(mio)) >= 1):
                futuros.append(hilos.submit(PEDIDOS[b], c, ref, sesion, cliente))
                if h.hasta(lambda: len(h.esperando(mio)) >= 2):
                    consultas = [" ".join(q.split())[:110] for q in h.esperando(mio)]
        finally:
            candado.rollback()
        codigos = [f.result(h.PLAZO).status_code for f in futuros]
    # Un deadlock que la app atrapa no da 500. Postgres lo suma a pg_stat_database
    # sin plazo fijo, pero sí al cerrar la conexión: se cierran todas y se espera.
    soltar(c)
    return codigos, h.sql(DEADLOCKS)[0][0] - antes, consultas, cuenta


def soltar(c):
    """Cierra las conexiones de la app y espera a que Postgres no vea ninguna.
    Falla si gc tuvo que cerrar una conexión que la app nunca devolvió al pool."""
    # La app registra cada pedido en una tarea que sigue después de responder: si
    # devuelve su conexión tras el dispose, cae en el pool descartado y sólo la cierra gc,
    # que corre en el loop para que asyncpg cierre el socket desde su propio hilo.
    async def cerrar():
        await engine.dispose()
        with warnings.catch_warnings(record=True) as avisos:
            warnings.simplefilter("always")
            gc.collect()
        return [str(a.message) for a in avisos if "non-checked-in" in str(a.message)]

    def libres():
        if fugas := c.portal.call(cerrar):
            raise h.Invalida(f"la app dejó conexiones sin devolver al pool: {fugas[0][:90]}")
        return h.sql(OTRAS)[0][0] == 0
    if not h.hasta(libres):
        quedan = "; ".join(f"{e}, espera {w}, hace {t} s: {q}" for e, w, t, q in h.sql(QUE_HACEN))
        raise h.Invalida(f"la app no soltó sus conexiones: {quedan or 'ya no queda ninguna'}")


def correr(caso):
    """Da lo que da el caso, o 2 si el arnés falló y la medición no vale."""
    try:
        return caso()
    except Exception:
        traceback.print_exc()
        return 2
