"""Caso 6: dos pedidos de la misma cuenta a la vez, códigos y deadlocks de Postgres.

Cada par va en los dos órdenes, con usuario y con org, con créditos extra
vencidos y al día. Antes mira qué candados le llegan a Postgres de _cuenta_bloqueada
después de que el aviso compiló los suyos, que son FOR UPDATE de las mismas tablas.
uso: scripts/testing/con_pg16.sh python scripts/testing/conexiones1_pares.py
Sale 1 si hubo algún deadlock o un candado no es FOR NO KEY UPDATE, 4 si alguna
ronda no se armó, 2 si el arnés falló y 0 si no.
"""
import itertools
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conexiones1_creditos import AL_DIA, preparar, sql  # noqa: E402
from conexiones1_rondas import correr, m, ronda  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from proyecto_maria.database.connection import AsyncSessionLocal, engine  # noqa: E402
from sqlalchemy import event  # noqa: E402

PARES = [("alta", "guardado"), ("alta", "recarga"), ("guardado", "recarga"), ("maria", "recarga"),
         ("alta", "renovación"), ("cancelar", "alta"), ("reactivar", "alta")]


def candados(c):
    """Los FOR ... que manda _cuenta_bloqueada, con la cache ya cargada por el aviso."""
    _, _, _, (_, _, org) = preparar(c, True)
    usuario = sql("select owner_username from organizations where id = %s", org)[0][0]
    vistos = []

    def anotar(_conn, _cur, sentencia, *_):
        vistos.extend(re.findall(r"FOR (?:NO KEY )?UPDATE(?: OF \w+)?", sentencia))

    async def pedir():
        for funcion in (m._cuenta_con_suscripciones, m._cuenta_bloqueada):
            async with AsyncSessionLocal() as db:
                vistos.clear()
                await funcion(db, usuario)
                await db.rollback()
        return list(vistos)
    event.listen(engine.sync_engine, "before_cursor_execute", anotar)
    try:
        return c.portal.call(pedir)
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", anotar)


def main():
    total, sin_armar = 0, 0
    with TestClient(m.app, raise_server_exceptions=False) as c:
        vistos = candados(c)
        bien = vistos == ["FOR NO KEY UPDATE OF users", "FOR NO KEY UPDATE OF organizations"]
        print("_cuenta_bloqueada después del aviso:", " | ".join(vistos), "" if bien else "| MAL")
        for (x, y), orden, de_org, vencidos in itertools.product(PARES, (1, -1), (False, True), (True, False)):
            a, b = (x, y)[::orden]
            ajuste = f"billing_status = '{'canceled' if 'reactivar' in (a, b) else 'active'}'"
            codigos, dl, consultas, _ = ronda(c, a, b, de_org, ajuste + (
                "" if vencidos else ", " + AL_DIA))
            total, sin_armar = total + dl, sin_armar + (consultas is None)
            print(f"{'DEADLOCK' if dl else 'ok      '} | {a} + {b} | {'org' if de_org else 'usuario'} | "
                  f"créditos {'vencidos' if vencidos else 'al día'} | {codigos} | deadlocks +{dl}"
                  + " | NO SE ARMÓ" * (consultas is None))
            print("".join(f"         esperaba: {q}\n" for q in consultas or []), end="")
    print(f"deadlocks: {total}; rondas sin armar: {sin_armar}")
    return 1 if total or not bien else 4 if sin_armar else 0


if __name__ == "__main__":
    sys.exit(correr(main))
