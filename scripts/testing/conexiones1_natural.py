"""Caso 8: dos pedidos de una org a la vez, sin tomar la fila desde afuera.

Recarga + guardado y recarga + MARIA con créditos extra vencidos, y de control
los mismos con créditos al día. Cada ronda larga los dos juntos (barrera) y
dice si hubo deadlock, quién perdió, cómo quedó la recarga (estado del pago,
créditos y si siguen vigentes) y, si perdió el aviso de Mercado Pago, cómo
quedó después de un reintento firmado.
uso: scripts/testing/con_pg16.sh python scripts/testing/conexiones1_natural.py
     (N rondas por combinación, 10 si no se dice)
Sale 1 si hubo algún deadlock, 2 si el arnés falló y 0 si no.
"""
import itertools
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
RECARGA = ("select (select estado from mp_pagos_aplicados where payment_id = %s),"
           " extra_ops_remaining, extra_ops_expires_at > now() from organizations where id = %s")


def recarga_quedo(pid, org):
    estado, creditos, vigentes = h.sql(RECARGA, pid, org)[0]
    return f"pago {estado or 'sin fila'}, créditos {creditos} {'vigentes' if vigentes else 'vencidos'}"


def ronda(c, otro, vencidos):
    sesion, cliente, ref, (_, _, org) = h.preparar(c, True)
    if not vencidos:
        h.sql("update organizations set extra_ops_expires_at = now() + interval '20 days' where id = %s", org)
    antes, barrera, pid = h.sql(DEADLOCKS)[0][0], threading.Barrier(2), {}

    def recarga():
        barrera.wait()
        pid["v"], r = h.recargar(c, ref)
        return r

    def pedido():
        barrera.wait()
        return PEDIDOS[otro](c, ref, sesion, cliente)

    with ThreadPoolExecutor(2) as hilos:
        futuros = [hilos.submit(recarga), hilos.submit(pedido)]
        aviso, r_otro = (f.result(h.PLAZO) for f in futuros)
    soltar(c)
    dl = h.sql(DEADLOCKS)[0][0] - antes
    linea = f"{'DEADLOCK' if dl else 'ok      '} | recarga + {otro} | créditos {'vencidos' if vencidos else 'al día'}" \
            f" | aviso {aviso.status_code}, {otro} {r_otro.status_code}"
    linea += f" | {recarga_quedo(pid['v'], org)}"
    if aviso.status_code != 200:
        r = c.post("/api/payments/webhook", **aviso_firmado("payment", pid["v"], "secreto-de-prueba"))
        linea += f" | reintento {r.status_code}: {recarga_quedo(pid['v'], org)}"
    print(linea, flush=True)
    return dl


def main():
    total = 0
    with TestClient(m.app, raise_server_exceptions=False) as c:
        for otro, vencidos in itertools.product(("guardado", "maria"), (True, False)):
            dls = [ronda(c, otro, vencidos) for _ in range(N)]
            total += sum(dls)
            print(f"recarga + {otro}, créditos {'vencidos' if vencidos else 'al día'}:"
                  f" {sum(map(bool, dls))}/{N} rondas con deadlock")
    print(f"deadlocks: {total}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(correr(main))
