"""Caso 6: dos pedidos de la misma cuenta a la vez, códigos y deadlocks de Postgres.

Cada par va en los dos órdenes, con usuario y con org, con créditos extra
vencidos y al día.
uso: scripts/testing/con_pg16.sh python scripts/testing/conexiones1_pares.py
Sale 1 si hubo algún deadlock, 4 si alguna ronda no se armó, 2 si el arnés
falló y 0 si no.
"""
import inspect
import itertools
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conexiones1_rondas import correr, m, ronda  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

PARES = [("alta", "guardado"), ("alta", "recarga"), ("guardado", "recarga"), ("maria", "recarga"),
         ("alta", "renovación"), ("cancelar", "alta"), ("reactivar", "alta")]


def main():
    candados = re.findall(r"with_for_update\([^)]*\)", inspect.getsource(m._cuenta_bloqueada))
    print("_cuenta_bloqueada:", " | ".join(candados))
    total, sin_armar = 0, 0
    with TestClient(m.app, raise_server_exceptions=False) as c:
        for (x, y), orden, de_org, vencidos in itertools.product(PARES, (1, -1), (False, True), (True, False)):
            a, b = (x, y)[::orden]
            ajuste = f"billing_status = '{'canceled' if 'reactivar' in (a, b) else 'active'}'"
            codigos, dl, consultas, _ = ronda(c, a, b, de_org, ajuste + (
                "" if vencidos else ", extra_ops_expires_at = now() + interval '20 days'"))
            total, sin_armar = total + dl, sin_armar + (consultas is None)
            print(f"{'DEADLOCK' if dl else 'ok      '} | {a} + {b} | {'org' if de_org else 'usuario'} | "
                  f"créditos {'vencidos' if vencidos else 'al día'} | {codigos} | deadlocks +{dl}"
                  + " | NO SE ARMÓ" * (consultas is None))
            print("".join(f"         esperaba: {q}\n" for q in consultas or []), end="")
    print(f"deadlocks: {total}; rondas sin armar: {sin_armar}")
    return 1 if total else 4 if sin_armar else 0


if __name__ == "__main__":
    sys.exit(correr(main))
