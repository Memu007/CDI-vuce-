"""Caso 6: dos pedidos de la misma cuenta a la vez, códigos y deadlocks de Postgres.

Cada par va en los dos órdenes, con usuario y con org, con créditos extra
vencidos y al día. Antes mira qué candados le llegan a Postgres de _cuenta_con_suscripciones
y de _cuenta_bloqueada en los dos órdenes: la cache de SQL va cargada por la anterior.
Una recarga junto a un guardado, a MARIA, a cancelar o a reactivar tiene que armarse,
dar 200 a los dos y dejar los créditos vigentes; si no, la fila dice «MAL».
uso: scripts/testing/con_pg16.sh python scripts/testing/conexiones1_pares.py
Sale 1 si hubo algún deadlock, una fila MAL o un candado no es el de ESPERADOS,
4 si alguna ronda no se armó, 2 si el arnés falló y 0 si no.
"""
import itertools
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conexiones1_creditos import AL_DIA, RECARGA, preparar, sql  # noqa: E402
from conexiones1_rondas import correr, m, ronda  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from proyecto_maria.database.connection import AsyncSessionLocal, engine  # noqa: E402
from sqlalchemy import event  # noqa: E402

PARES = [("alta", "guardado"), ("alta", "recarga"), ("guardado", "recarga"), ("maria", "recarga"),
         ("alta", "renovación"), ("cancelar", "alta"), ("reactivar", "alta"),
         ("cancelar", "recarga"), ("reactivar", "recarga")]
OBJETIVO = [{"guardado", "recarga"}, {"maria", "recarga"}, {"cancelar", "recarga"}, {"reactivar", "recarga"}]
# El usuario NO KEY: la recarga que ya venció los créditos vuelve a chequear owner_username con KEY SHARE.
ESPERADOS = {"_cuenta_con_suscripciones": ["FOR NO KEY UPDATE OF users", "FOR UPDATE"],
             "_cuenta_bloqueada": ["FOR NO KEY UPDATE OF users", "FOR NO KEY UPDATE OF organizations"]}


def candados(c):
    """Los FOR ... que manda cada función, por orden de llamada."""
    _, _, _, (_, _, org) = preparar(c, True)
    usuario = sql("select owner_username from organizations where id = %s", org)[0][0]
    vistos = []

    def anotar(_conn, _cur, sentencia, *_):
        vistos.extend(re.findall(r"FOR (?:NO KEY )?UPDATE(?: OF \w+)?(?: NOWAIT| SKIP LOCKED)?", sentencia))

    async def pedir():
        filas = []
        for orden, nombres in enumerate((list(ESPERADOS), list(ESPERADOS)[::-1]), 1):
            for nombre in nombres:
                async with AsyncSessionLocal() as db:
                    vistos.clear()
                    await getattr(m, nombre)(db, usuario)
                    await db.rollback()
                filas.append((orden, nombre, list(vistos)))
        return filas
    event.listen(engine.sync_engine, "before_cursor_execute", anotar)
    try:
        return c.portal.call(pedir)
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", anotar)


def main():
    total, sin_armar, malas = 0, 0, 0
    with TestClient(m.app, raise_server_exceptions=False) as c:
        bien = True
        for orden, nombre, vistos in candados(c):
            bien &= vistos == ESPERADOS[nombre]
            print(f"orden {orden}, {nombre}:", " | ".join(vistos), "" if vistos == ESPERADOS[nombre] else "| MAL")
        for (x, y), orden, de_org, vencidos in itertools.product(PARES, (1, -1), (False, True), (True, False)):
            a, b = (x, y)[::orden]
            ajuste = f"billing_status = '{'canceled' if 'reactivar' in (a, b) else 'active'}'"
            codigos, dl, consultas, (tabla, clave, valor) = ronda(c, a, b, de_org, ajuste + (
                "" if vencidos else ", " + AL_DIA))
            mal = {a, b} in OBJETIVO and (dl or consultas is None or codigos != [200, 200] or not sql(
                f"select extra_ops_remaining >= %s and extra_ops_expires_at > now() from {tabla} "
                f"where {clave} = %s", RECARGA, valor)[0][0])
            total, sin_armar, malas = total + dl, sin_armar + (consultas is None), malas + bool(mal)
            print(f"{'DEADLOCK' if dl else 'ok      '} | {a} + {b} | {'org' if de_org else 'usuario'} | "
                  f"créditos {'vencidos' if vencidos else 'al día'} | {codigos} | deadlocks +{dl}"
                  + " | NO SE ARMÓ" * (consultas is None) + " | MAL" * bool(mal))
            print("".join(f"         esperaba: {q}\n" for q in consultas or []), end="")
    print(f"deadlocks: {total}; rondas sin armar: {sin_armar}; filas MAL: {malas}")
    return 1 if total or malas or not bien else 4 if sin_armar else 0


if __name__ == "__main__":
    sys.exit(correr(main))
