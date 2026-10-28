"""Sonda del pool para CONEXIONES-1. Archivo de configuración de gunicorn.

Lo carga `conexiones1_medir.py` con `-c`. No cambia la app ni sus flags: sólo
define `post_worker_init`, que levanta un hilo con un servidor HTTP aparte (en
`CONEXIONES1_SONDA_PUERTO`) que devuelve en JSON los contadores del pool del
worker. Leer esos contadores desde otro hilo no hace I/O ni toca el loop.

También cuenta cuántas veces `AsyncSession.close()` terminó cancelado: es la
premisa de la D37 (en el TestClient se cancela) medida en el servidor real.
"""

import asyncio
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def post_worker_init(worker):
    from sqlalchemy.ext.asyncio import AsyncSession

    from proyecto_maria.database.connection import engine

    pool = engine.pool
    cierres = {"total": 0, "cancelados": 0}
    cerrar = AsyncSession.close

    async def close_contado(self):
        cierres["total"] += 1
        try:
            await cerrar(self)
        except asyncio.CancelledError:
            cierres["cancelados"] += 1
            raise

    AsyncSession.close = close_contado

    class _Sonda(BaseHTTPRequestHandler):
        def do_GET(self):
            cuerpo = json.dumps({
                "pid": os.getpid(),
                "tomadas": pool.checkedout(),
                "libres": pool.checkedin(),
                "desborde": pool.overflow(),
                "tamano": pool.size(),
                "estado": pool.status(),
                "cierres": cierres["total"],
                "cierres_cancelados": cierres["cancelados"],
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, *args):
            pass

    ThreadingHTTPServer.allow_reuse_address = True
    servidor = ThreadingHTTPServer(
        ("127.0.0.1", int(os.environ["CONEXIONES1_SONDA_PUERTO"])), _Sonda
    )
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
