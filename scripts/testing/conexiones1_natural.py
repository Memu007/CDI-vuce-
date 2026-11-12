"""Caso 8: dos pedidos de una org a la vez, sin tomar la fila desde afuera.

Cada fila de FILAS es un par con la org puesta de una forma. Por ronda: deadlock y
quién perdió, si la recarga quedó entera y vigente (con un reintento firmado si perdió
el aviso), si la renovación que dio 200 dejó la cuenta active con el período por delante
y, en los pares de alta, si lo que dio 200 quedó entero y lo que no, no dejó nada.
uso: [N=rondas, 10 si no] scripts/testing/con_pg16.sh python scripts/testing/conexiones1_natural.py
Sale 1 si algo de eso falló, 2 si falló el arnés o una ronda sin deadlock dio un código
que la fila no admite, y 0 si no.
"""
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conexiones1_creditos as h  # noqa: E402
from conexiones1_renovacion import VENCIDAS  # noqa: E402
from conexiones1_rondas import DEADLOCKS, PEDIDOS, correr, m, soltar  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from tests.mp_firma import aviso_firmado  # noqa: E402

N = int(os.environ.get("N", "10"))
ESTADO = ("select (select estado from mp_pagos_aplicados where payment_id = %s),"
          " extra_ops_remaining, extra_ops_expires_at > now() from organizations where id = %s")
OPERACIONES = ("select o.id, count(i.id) from operations o left join operation_items i on i.operation_id = o.id"
               " where o.owner_username = (select owner_username from organizations where id = %s) group by o.id")
CUENTA = "select ops_used_this_period, billing_status from organizations where id = %s"
CREDITOS = {"créditos vencidos": None, "créditos al día": "extra_ops_expires_at = now() + interval '20 days'"}
# (a, b, rótulo, cómo queda la org además de los créditos extra vencidos, códigos que b puede dar sin deadlock)
FILAS = [("recarga", b, *c, {200}) for b in ("guardado", "maria", "alta") for c in CREDITOS.items()] + [
    ("alta", b, "créditos vencidos", None, {200}) for b in ("guardado", "cancelar")] + [
    ("alta", "reactivar", "cancelada", "billing_status = 'canceled'", {200})] + [
    ("renovación", "guardado", *v, {200, 402}) for v in VENCIDAS.items()]


def recarga_quedo(pid, org, esperados):
    estado, creditos, vigentes = h.sql(ESTADO, pid, org)[0]
    bien = estado == "aplicado" and creditos == esperados and vigentes
    return bien, f"pago {estado or 'sin fila'}, créditos {creditos}/{esperados} {'vigentes' if vigentes else 'vencidos'}"


def alta_quedo(org, antes, r_a, b, r_b):
    """La operación del alta con su ítem, la del guardado, una cuenta por operación y el
    plan que dijo cancelar o reactivar: nada más que lo que dio 200."""
    ops, (usadas, plan) = dict(h.sql(OPERACIONES, org)), h.sql(CUENTA, org)[0]
    alta = r_a.json()["operation_id"] if r_a.status_code == 200 else None
    guardadas = len(ops) - (alta in ops)
    plan_esperado = r_b.json()["billing_status"] if b != "guardado" and r_b.status_code == 200 else antes[1]
    bien = (not alta or ops.get(alta) == 1) and guardadas == (b == "guardado" and r_b.status_code == 200) \
        and usadas - antes[0] == len(ops) and plan == plan_esperado
    return bien, f"{len(ops)} operaciones, {usadas - antes[0]} contadas, plan {plan}"


def ronda(c, a, b, rotulo, ajuste, admite):
    sesion, cliente, ref, (_, _, org) = h.preparar(c, True)
    if ajuste:
        h.sql(f"update organizations set {ajuste} where id = %s", org)
    if "recarga" in (a, b):
        _, previos, vigentes = h.sql(ESTADO, None, org)[0]
        esperados = h.RECARGA + (previos if vigentes else 0)
    cuenta_antes = h.sql(CUENTA, org)[0]
    antes, barrera, pid = h.sql(DEADLOCKS)[0][0], threading.Barrier(2, timeout=h.PLAZO), []

    def pedir(nombre):
        barrera.wait()
        if nombre != "recarga":
            return PEDIDOS[nombre](c, ref, sesion, cliente)
        pid.extend(h.recargar(c, ref))
        return pid[1]
    with ThreadPoolExecutor(2) as hilos:
        r_a, r_b = (f.result(h.PLAZO) for f in [hilos.submit(pedir, a), hilos.submit(pedir, b)])
    soltar(c)
    dl = h.sql(DEADLOCKS)[0][0] - antes
    pierde = [n for n, r, ok in ((a, r_a, {200}), (b, r_b, admite)) if r.status_code not in ok]
    linea = f"{'DEADLOCK' if dl else 'ok      '} | {a} + {b} | {rotulo} | {a} {r_a.status_code}, {b} " \
            f"{r_b.status_code}{' | pierde ' + ' y '.join(pierde) if dl and pierde else ''}"
    bien = True
    if pid:
        bien, quedo = recarga_quedo(pid[0], org, esperados)
        linea += f" | {quedo}"
        if pid[1].status_code != 200:
            r = c.post("/api/payments/webhook", **aviso_firmado("payment", pid[0], "secreto-de-prueba"))
            bien, quedo = recarga_quedo(pid[0], org, esperados)
            linea += f" | reintento {r.status_code}: {quedo}"
    if a == "alta":
        bien, quedo = alta_quedo(org, cuenta_antes, r_a, b, r_b)
        linea += f" | {quedo}"
    if a == "renovación":
        estado, delante = h.sql("select billing_status, trial_ends_at > now() from organizations where id = %s", org)[0]
        bien = r_a.status_code != 200 or (estado == "active" and delante)
        linea += f" | termina {estado}, período {'por delante' if delante else 'vencido'}"
    print(linea + ("" if bien else " | RECARGA PERDIDA" if pid else " | CUENTA MAL"), flush=True)
    if not dl and (r_a.status_code != 200 or r_b.status_code not in admite):
        raise h.Invalida("ronda sin carrera: un pedido dio un código que la fila no admite, sin deadlock")
    return bool(dl), int(not bien and bool(pid)), int(not bien and not pid)


def main():
    totales = [0, 0, 0]
    with TestClient(m.app, raise_server_exceptions=False) as c:
        for a, b, rotulo, *resto in FILAS:
            rondas = [ronda(c, a, b, rotulo, *resto) for _ in range(N)]
            totales = [t + sum(col) for t, col in zip(totales, zip(*rondas))]
            print(f"{a} + {b}, {rotulo}: {sum(r[0] for r in rondas)}/{N} rondas con deadlock,"
                  f" {sum(r[1] or r[2] for r in rondas)}/{N} mal")
    print("rondas con deadlock: {}, recargas perdidas: {}, cuentas mal: {}".format(*totales))
    return 1 if any(totales) else 0


if __name__ == "__main__":
    sys.exit(correr(main))
