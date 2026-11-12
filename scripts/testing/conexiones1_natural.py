"""Caso 8: dos pedidos de una org a la vez, sin tomar la fila desde afuera.

Cada fila de FILAS es un par con la org puesta de una forma. Por ronda: deadlock y
quién perdió, si la recarga quedó entera y vigente (con un reintento firmado si perdió
el aviso) y si la renovación dejó la cuenta active con el período por delante.
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
from conexiones1_rondas import DEADLOCKS, PEDIDOS, correr, m, soltar  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from tests.mp_firma import aviso_firmado  # noqa: E402

N = int(os.environ.get("N", "10"))
ESTADO = ("select (select estado from mp_pagos_aplicados where payment_id = %s),"
          " extra_ops_remaining, extra_ops_expires_at > now() from organizations where id = %s")
AL_DIA = "extra_ops_expires_at = now() + interval '20 days'"
FUERA_DE_GRACIA = f"trial_ends_at = now() - interval '{m.BILLING_GRACE_DAYS_ACTIVE + 1} days'"
# (a, b, cómo queda la org además de los créditos extra vencidos, códigos que b puede dar sin deadlock)
FILAS = [(a, b, ajuste, {200}) for b in ("guardado", "maria", "alta") for a, ajuste in
         (("recarga", "créditos vencidos"), ("recarga", AL_DIA))] + [
    ("alta", "guardado", "créditos vencidos", {200}),
    ("alta", "cancelar", "créditos vencidos", {200}),
    ("alta", "reactivar", "billing_status = 'canceled'", {200}),
    ("renovación", "guardado", FUERA_DE_GRACIA, {200, 402}),
    ("renovación", "guardado", "billing_status = 'trial', trial_ends_at = now() - interval '1 day'", {200, 402}),
]


def recarga_quedo(pid, org, esperados):
    estado, creditos, vigentes = h.sql(ESTADO, pid, org)[0]
    bien = estado == "aplicado" and creditos == esperados and vigentes
    return bien, f"pago {estado or 'sin fila'}, créditos {creditos}/{esperados} {'vigentes' if vigentes else 'vencidos'}"


def ronda(c, a, b, ajuste, admite):
    sesion, cliente, ref, (_, _, org) = h.preparar(c, True)
    if "=" in ajuste:
        h.sql(f"update organizations set {ajuste} where id = %s", org)
    _, previos, vigentes = h.sql(ESTADO, None, org)[0]
    esperados = h.RECARGA + (previos if vigentes else 0)
    antes, barrera, pid = h.sql(DEADLOCKS)[0][0], threading.Barrier(2, timeout=h.PLAZO), []

    def pedir(nombre):
        barrera.wait()
        if nombre != "recarga":
            return PEDIDOS[nombre](c, ref, sesion, cliente)
        p, r = h.recargar(c, ref)
        pid.append(p)
        return r
    with ThreadPoolExecutor(2) as hilos:
        r_a, r_b = (f.result(h.PLAZO) for f in [hilos.submit(pedir, a), hilos.submit(pedir, b)])
    soltar(c)
    dl = h.sql(DEADLOCKS)[0][0] - antes
    pierde = [n for n, r in ((a, r_a), (b, r_b)) if r.status_code != 200]
    linea = f"{'DEADLOCK' if dl else 'ok      '} | {a} + {b} | {ajuste[:40]} | {a} {r_a.status_code}, {b} " \
            f"{r_b.status_code}{' | pierde ' + ' y '.join(pierde) if dl and pierde else ''}"
    bien = True
    if pid:
        bien, quedo = recarga_quedo(pid[0], org, esperados)
        linea += f" | {quedo}"
        if r_a.status_code != 200:
            r = c.post("/api/payments/webhook", **aviso_firmado("payment", pid[0], "secreto-de-prueba"))
            bien, quedo = recarga_quedo(pid[0], org, esperados)
            linea += f" | reintento {r.status_code}: {quedo}"
    if a == "renovación":
        estado, delante = h.sql("select billing_status, trial_ends_at > now() from organizations where id = %s", org)[0]
        bien = estado == "active" and delante
        linea += f" | termina {estado}, período {'por delante' if delante else 'vencido'}"
    print(linea + ("" if bien else " | RECARGA PERDIDA" if pid else " | CUENTA MAL"), flush=True)
    if not dl and (r_a.status_code != 200 or r_b.status_code not in admite):
        raise h.Invalida("ronda sin carrera: un pedido dio un código que la fila no admite, sin deadlock")
    return dl, int(not bien and bool(pid)), int(not bien and not pid)


def main():
    totales = [0, 0, 0]
    with TestClient(m.app, raise_server_exceptions=False) as c:
        for a, b, ajuste, admite in FILAS:
            rondas = [ronda(c, a, b, ajuste, admite) for _ in range(N)]
            totales = [t + sum(col) for t, col in zip(totales, zip(*rondas))]
            print(f"{a} + {b}, {ajuste[:40]}: {sum(bool(r[0]) for r in rondas)}/{N} rondas con deadlock,"
                  f" {sum(r[1] or r[2] for r in rondas)}/{N} mal")
    print("deadlocks: {}, recargas perdidas: {}, cuentas mal: {}".format(*totales))
    return 1 if any(totales) else 0


if __name__ == "__main__":
    sys.exit(correr(main))
