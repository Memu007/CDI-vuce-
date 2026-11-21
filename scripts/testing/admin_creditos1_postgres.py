"""Casos 8 a 11 de la carga de créditos desde el panel de admin, en Postgres 16.

8: el mismo pedido dos veces a la vez, para la misma cuenta y para dos cuentas.
9: la recarga pagada y la carga a la vez, en los dos órdenes.
10: el guardado de la integrante y la carga a la vez.
Los dos, con usuario solo y con integrante de un estudio, con créditos vencidos y al día.
11: sin la tabla de cargas, el arranque la crea; el segundo no falla y las demás tablas no cambian.
uso: scripts/testing/con_pg16.sh python scripts/testing/admin_creditos1_postgres.py
Sale 1 si una fila dice MAL, 4 si una ronda no se armó, 2 si el arnés falló y 0 si no.
"""
import asyncio
import itertools
import os
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conexiones1_creditos as h  # noqa: E402
from conexiones1_rondas import PEDIDOS, correr, m, ronda, soltar  # noqa: E402
import asyncpg  # noqa: E402
import psycopg2  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from proyecto_maria.database.connection import init_db  # noqa: E402
from scripts.datos.copia_base import diferencias, huella  # noqa: E402

N = 7
ADMIN = {}


def duena(ref):
    if not ref.startswith("org:"):
        return ref
    return h.sql("select owner_username from organizations where id = %s", ref[4:])[0][0]


def cargar(c, ref, pedido=None, cantidad=N):
    return c.post(f"/api/admin/usuarios/{duena(ref)}/creditos", headers=ADMIN,
                  json={"cantidad": cantidad, "pedido": pedido or str(uuid.uuid4())})


PEDIDOS["carga"] = lambda c, ref, *_: cargar(c, ref)


def creditos(cuenta):
    tabla, clave, valor = cuenta
    return h.sql(f"select extra_ops_remaining from {tabla} where {clave} = %s", valor)[0][0]


def cargas(pedido):
    return h.sql("select count(*) from creditos_admin where pedido = %s", pedido)[0][0]


def fila(texto, mal, codigos, dl, consultas):
    print(f"{'MAL' if mal else 'ok '} | {texto} | {codigos} | deadlocks +{dl}" + " | NO SE ARMÓ" * (consultas is None))
    return bool(mal), consultas is None


def mismo_pedido_misma_cuenta(c, de_org):
    pedido = str(uuid.uuid4())
    PEDIDOS["fija"] = lambda c, ref, *_: cargar(c, ref, pedido)
    codigos, dl, consultas, cuenta = ronda(c, "fija", "fija", de_org, h.AL_DIA)
    mal = dl or codigos != [200, 200] or creditos(cuenta) != 5 + N or cargas(pedido) != 1
    return fila(f"el mismo pedido dos veces, {'org' if de_org else 'usuario'}", mal, codigos, dl, consultas)


def mismo_pedido_dos_cuentas(c):
    """Las dos cuentas bloqueadas, cada una pide con la misma clave, y se sueltan juntas."""
    pedido, cuentas = str(uuid.uuid4()), []
    for _ in range(2):
        _, _, ref, cuenta = h.preparar(c, False)
        h.sql(f"update users set {h.AL_DIA} where username = %s", ref)
        cuentas.append((ref, cuenta))
    antes, consultas = h.sql("select deadlocks from pg_stat_database where datname = current_database()")[0][0], None
    with ThreadPoolExecutor(2) as hilos, closing(psycopg2.connect(h.URL)) as candado:
        try:
            with candado.cursor() as cur:
                cur.execute("select pg_backend_pid() from users where username in (%s, %s) for update",
                            tuple(r for r, _ in cuentas))
                mio = cur.fetchone()[0]
            futuros = [hilos.submit(cargar, c, ref, pedido) for ref, _ in cuentas]
            if h.hasta(lambda: len(h.esperando(mio)) >= 2):
                consultas = h.esperando(mio)
        finally:
            candado.rollback()
        codigos = sorted(f.result(h.PLAZO).status_code for f in futuros)
    soltar(c)
    dl = h.sql("select deadlocks from pg_stat_database where datname = current_database()")[0][0] - antes
    sumadas = sorted(creditos(cuenta) for _, cuenta in cuentas)
    mal = dl or codigos != [200, 409] or sumadas != [5, 5 + N] or cargas(pedido) != 1
    return fila(f"el mismo pedido para dos cuentas | créditos {sumadas}", mal, codigos, dl, consultas)


def a_la_vez(c, otro, orden, de_org, vencidos):
    a, b = ("carga", otro)[::orden]
    codigos, dl, consultas, cuenta = ronda(c, a, b, de_org, "billing_status = 'active'" + (
        "" if vencidos else ", " + h.AL_DIA))
    esperado = (0 if vencidos else 5) + N + (h.RECARGA if otro == "recarga" else 0)
    quedan = creditos(cuenta)
    mal = dl or codigos != [200, 200] or quedan != esperado
    return fila(f"{a} + {b} | {'org' if de_org else 'usuario'} | créditos "
                f"{'vencidos' if vencidos else 'al día'} | quedan {quedan}, esperaba {esperado}",
                mal, codigos, dl, consultas)


async def tablas_sin_cargas():
    con = await asyncpg.connect(h.URL)
    try:
        return {t: v for t, v in (await huella(con)).items() if t != "public.creditos_admin"}
    finally:
        await con.close()


def migracion(c):
    """Una base que ya tiene datos y no tiene la tabla de cargas."""
    antes = asyncio.run(tablas_sin_cargas())
    h.sql("drop table creditos_admin")
    for vuelta in ("primer", "segundo"):
        try:
            c.portal.call(init_db)
        except Exception as e:  # noqa: BLE001
            print(f"MAL | el {vuelta} arranque falla: {type(e).__name__}: {str(e)[:120]}")
            return True
    filas = h.sql("select count(*) from creditos_admin")[0][0]
    cambios = diferencias(antes, asyncio.run(tablas_sin_cargas()))
    mal = filas != 0 or cambios
    print(f"{'MAL' if mal else 'ok '} | migración: creditos_admin con {filas} filas; "
          f"{len(antes)} tablas más, cambios: {cambios or 'ninguno'}")
    return bool(mal)


def main():
    malas, sin_armar = 0, 0
    with TestClient(m.app, raise_server_exceptions=False) as c:
        ADMIN.update(h.preparar(c, False)[0])
        h.sql("update users set roles = %s where username = %s", '["admin"]',
              c.get("/auth/me", headers=ADMIN).json()["username"])
        rondas = [lambda: mismo_pedido_misma_cuenta(c, False), lambda: mismo_pedido_misma_cuenta(c, True),
                  lambda: mismo_pedido_dos_cuentas(c)]
        rondas += [lambda x=x: a_la_vez(c, *x) for x in itertools.product(
            ("recarga", "guardado"), (1, -1), (False, True), (True, False))]
        for r in rondas:
            mal, no = r()
            malas, sin_armar = malas + mal, sin_armar + no
        malas += migracion(c)
    print(f"filas MAL: {malas}; rondas sin armar: {sin_armar}")
    return 1 if malas else 4 if sin_armar else 0


if __name__ == "__main__":
    sys.exit(correr(main))
