"""Caso 8: dos pedidos de una org a la vez, sin tomar la fila desde afuera.

Recarga + guardado y recarga + MARIA, con créditos extra vencidos y, de control,
al día. Por ronda: deadlock, quién perdió y cómo quedó la recarga (si perdió el
aviso de MP, también después de un reintento firmado).
uso: [N=rondas, 10 si no] scripts/testing/con_pg16.sh python scripts/testing/conexiones1_natural.py
Sale 1 si hubo deadlock o una recarga no quedó entera y vigente, 2 si el arnés
falló o una ronda sin deadlock no dio 200/200, y 0 si no.
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
ESTADO = ("select (select estado from mp_pagos_aplicados where payment_id = %s),"
          " extra_ops_remaining, extra_ops_expires_at > now() from organizations where id = %s")


def recarga_quedo(pid, org, esperados):
    estado, creditos, vigentes = h.sql(ESTADO, pid, org)[0]
    bien = estado == "aplicado" and creditos == esperados and vigentes
    return bien, f"pago {estado or 'sin fila'}, créditos {creditos}/{esperados} {'vigentes' if vigentes else 'vencidos'}"


def ronda(c, otro, vencidos):
    sesion, cliente, ref, (_, _, org) = h.preparar(c, True)
    if not vencidos:
        h.sql("update organizations set extra_ops_expires_at = now() + interval '20 days' where id = %s", org)
    _, previos, vigentes = h.sql(ESTADO, None, org)[0]
    esperados = h.RECARGA + (previos if vigentes else 0)
    antes, barrera = h.sql(DEADLOCKS)[0][0], threading.Barrier(2, timeout=h.PLAZO)

    def juntos(pedido):
        barrera.wait()
        return pedido()

    with ThreadPoolExecutor(2) as hilos:
        futuros = [hilos.submit(juntos, lambda: h.recargar(c, ref)),
                   hilos.submit(juntos, lambda: PEDIDOS[otro](c, ref, sesion, cliente))]
        (pid, aviso), r_otro = (f.result(h.PLAZO) for f in futuros)
    soltar(c)
    dl = h.sql(DEADLOCKS)[0][0] - antes
    linea = f"{'DEADLOCK' if dl else 'ok      '} | recarga + {otro} | créditos {'vencidos' if vencidos else 'al día'}" \
            f" | aviso {aviso.status_code}, {otro} {r_otro.status_code}"
    bien, quedo = recarga_quedo(pid, org, esperados)
    linea += f" | {quedo}"
    if aviso.status_code != 200:
        r = c.post("/api/payments/webhook", **aviso_firmado("payment", pid, "secreto-de-prueba"))
        bien, quedo = recarga_quedo(pid, org, esperados)
        linea += f" | reintento {r.status_code}: {quedo}"
    print(linea + ("" if bien else " | RECARGA PERDIDA"), flush=True)
    if not dl and (aviso.status_code, r_otro.status_code) != (200, 200):
        raise h.Invalida("ronda sin carrera: un pedido falló sin deadlock")
    return dl, not bien


def main():
    total = perdidas = 0
    with TestClient(m.app, raise_server_exceptions=False) as c:
        for otro, vencidos in itertools.product(("guardado", "maria"), (True, False)):
            dls, malas = zip(*[ronda(c, otro, vencidos) for _ in range(N)])
            total, perdidas = total + sum(dls), perdidas + sum(malas)
            print(f"recarga + {otro}, créditos {'vencidos' if vencidos else 'al día'}:"
                  f" {sum(map(bool, dls))}/{N} rondas con deadlock")
    print(f"deadlocks: {total}, recargas perdidas: {perdidas}")
    return 1 if total or perdidas else 0


if __name__ == "__main__":
    sys.exit(correr(main))
