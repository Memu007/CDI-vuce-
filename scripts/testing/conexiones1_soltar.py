"""Caso 9: una conexión devuelta después del dispose no deja la base ocupada.

La app registra cada pedido en una tarea que sigue después de responder. Si esa
tarea devuelve su conexión después del dispose, la conexión cae en el pool
descartado. Se repiten pedidos y dispose hasta que lo que hacía el arnés antes
(un dispose y esperar) deja una conexión abierta. Ahí se dice quién la devolvió
y se prueba soltar().
uso: scripts/testing/con_pg16.sh python scripts/testing/conexiones1_soltar.py [vueltas]
Sale 0 si soltar() deja la base sin conexiones de la app, 1 si no, 4 si en las
vueltas no quedó ninguna abierta (el caso no se armó) y 2 si el arnés falló.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conexiones1_rondas import OTRAS, correr, engine, h, m, soltar  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import Pool  # noqa: E402

VUELTAS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
TARDIAS = []
_devolver = Pool._return_conn


def _return_conn(self, registro):
    if self is not engine.pool:
        try:
            tarea = asyncio.current_task()
        except RuntimeError:
            tarea = None
        TARDIAS.append(tarea.get_coro().__qualname__ if tarea else "fuera de una tarea")
    return _devolver(self, registro)


Pool._return_conn = _return_conn


def main():
    with TestClient(m.app, raise_server_exceptions=False) as c:
        for vuelta in range(1, VUELTAS + 1):
            TARDIAS.clear()
            h.preparar(c, False)
            c.portal.call(engine.dispose)
            if h.hasta(lambda: h.sql(OTRAS)[0][0] == 0):
                continue
            print(f"vuelta {vuelta}: arnés anterior (dispose y esperar {h.PLAZO} s): "
                  f"{h.sql(OTRAS)[0][0]} conexión(es) de la app abiertas")
            print(f"devueltas al pool descartado por: {TARDIAS}")
            try:
                soltar(c)
            except h.Invalida as e:
                print(f"soltar(): {e}")
                return 1
            print("soltar(): la base quedó sin conexiones de la app")
            return 0
        print(f"en {VUELTAS} vueltas el dispose solo siempre dejó la base libre: el caso no se armó")
        return 4


if __name__ == "__main__":
    sys.exit(correr(main))
