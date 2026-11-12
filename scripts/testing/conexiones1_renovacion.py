"""Caso 7: la renovación de la suscripción llega mientras otro pedido vence la cuenta.

require_billing_vigente lee la cuenta sin candado y, si está vencida, la pasa a
past_due; el aviso de renovación la deja active con 30 días más. Con usuario y
org, con prueba vencida y con active fuera de gracia, en los dos órdenes. La
cuenta tiene que terminar active y con el período por delante.
uso: scripts/testing/con_pg16.sh python scripts/testing/conexiones1_renovacion.py
Sale 1 si alguna cuenta terminó mal, 4 si alguna ronda no se armó y 0 si no.
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conexiones1_creditos as h  # noqa: E402
from conexiones1_rondas import m, ronda  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

VENCIDAS = {
    "prueba vencida": "billing_status = 'trial', trial_ends_at = now() - interval '1 day'",
    "active fuera de gracia": "billing_status = 'active', trial_ends_at = now() - interval "
                              f"'{m.BILLING_GRACE_DAYS_ACTIVE + 1} days'",
}
ORDENES = [("guardado", "renovación"), ("renovación", "guardado")]


def main():
    mal, sin_armar = 0, 0
    with TestClient(m.app, raise_server_exceptions=False) as c:
        for (a, b), de_org, (vencida, ajuste) in itertools.product(ORDENES, (False, True), VENCIDAS.items()):
            codigos, _, consultas, (tabla, clave, valor) = ronda(c, a, b, de_org, ajuste)
            estado, por_delante = h.sql(f"select billing_status, trial_ends_at > now() from {tabla} "
                                        f"where {clave} = %s", valor)[0]
            bien = estado == "active" and por_delante
            mal, sin_armar = mal + (not bien), sin_armar + (consultas is None)
            print(f"{'ok      ' if bien else 'MAL     '} | {a} + {b} | {'org' if de_org else 'usuario'} | {vencida}"
                  f" | {codigos} | termina {estado}, período {'por delante' if por_delante else 'vencido'}"
                  + " | NO SE ARMÓ" * (consultas is None))
            print("".join(f"         esperaba: {q}\n" for q in consultas or []), end="")
    print(f"cuentas mal: {mal}; rondas sin armar: {sin_armar}")
    return 1 if mal else 4 if sin_armar else 0


if __name__ == "__main__":
    sys.exit(main())
