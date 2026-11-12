"""Sonda del pool para CONEXIONES-1. Archivo de configuración de gunicorn.

Lo carga `conexiones1_medir.py` con `-c`; la app y sus flags quedan como en el
Dockerfile. `post_worker_init` corre en el worker antes del primer pedido y:

- cuenta las entradas a `MetricsMiddleware.dispatch` que deberían dejar una
  fila en `api_logs`, cuántas terminaron y cómo;
- cuenta los `APILog` creados, las tareas que los guardan y los
  `AsyncSession.close()` empezados, terminados y cancelados;
- cuenta cuántos bcrypt, Gemini, lecturas de PDF y de Excel, y cuerpos de
  pedido sin terminar de llegar están en vuelo, para que el medidor actúe justo
  ahí sin esperas fijas;
- levanta un servidor HTTP aparte (`CONEXIONES1_SONDA_PUERTO`) que devuelve
  todo eso y los contadores del pool. `GET /modo?gemini=S&pdf=S&excel=S` pone
  Gemini y el lector de PDF falsos, y la lectura del Excel, que tardan S
  segundos (0 los saca); `GET /armar`
  arma el sabotaje.

`CONEXIONES1_SABOTAJE` es el control que tiene que dar rojo:
`close_cancelado` hace que algunos `close` levanten CancelledError sin cerrar
y guarda la sesión (quedan tomadas); `close_cancelado_suelto` hace lo mismo
pero la suelta (el recolector avisa en el log).
"""

import asyncio
import json
import os
import threading
import time
import weakref
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

SABOTAJE_CADA = 7
SABOTAJE_TOPE = 4


def _no_registrable(ruta):
    return ruta in ("/health", "/metrics") or ruta.startswith("/static")


_candado = threading.Lock()


def _contar_en_vuelo(c, clave, funcion):
    # Corre en hilos del pool: sin candado, dos += a la vez pierden una cuenta.
    def envuelta(*args, **kwargs):
        with _candado:
            c[clave] += 1
            c[clave + "_total"] += 1
            c[clave + "_max"] = max(c[clave + "_max"], c[clave])
        try:
            return funcion(*args, **kwargs)
        finally:
            with _candado:
                c[clave] -= 1
    return envuelta


def _instalar(c, modo, sabotaje):
    from sqlalchemy import event
    from sqlalchemy.ext.asyncio import AsyncSession

    import proyecto_maria.main as m
    from proyecto_maria.database.models import APILog

    event.listen(APILog, "init", lambda *a, **k: c.update(["apilog_creados"]))

    despachar = m.MetricsMiddleware.dispatch

    async def dispatch(self, request, call_next):
        if _no_registrable(request.url.path):
            return await despachar(self, request, call_next)
        c["dispatch_entradas"] += 1
        try:
            respuesta = await despachar(self, request, call_next)
        except asyncio.CancelledError:
            c["dispatch_cancelados"] += 1
            raise
        except BaseException as e:
            c["dispatch_error_" + type(e).__name__] += 1
            raise
        c["dispatch_ok"] += 1
        return respuesta

    m.MetricsMiddleware.dispatch = dispatch

    # La tarea que guarda la fila de api_logs es local a dispatch: se la ve al
    # crearla, para esperar a que termine en vez de esperar un tiempo.
    crear_tarea = asyncio.create_task

    def create_task(coro, *args, **kwargs):
        tarea = crear_tarea(coro, *args, **kwargs)
        if getattr(coro, "__qualname__", "").endswith("log_request_background"):
            c["log_tareas"] += 1
            tarea.add_done_callback(lambda t: c.update(
                ["log_tareas_canceladas" if t.cancelled() else "log_tareas_fin"]))
        return tarea

    asyncio.create_task = create_task

    cerrar = AsyncSession.close
    marcadas = weakref.WeakSet()
    retenidas = []

    async def close(self):
        c["close_empezados"] += 1
        # Después de un commit la sesión ya devolvió su conexión: el sabotaje
        # sólo elige sesiones con una transacción abierta, que todavía la tienen.
        abierta = self.in_transaction()
        c["close_con_transaccion"] += abierta
        if sabotaje and modo["armado"] and (
            self in marcadas
            or (abierta and c["close_con_transaccion"] % SABOTAJE_CADA == 0
                and c["saboteadas"] < SABOTAJE_TOPE)
        ):
            if self not in marcadas:
                c["saboteadas"] += 1
                marcadas.add(self)
                if sabotaje == "close_cancelado":
                    retenidas.append(self)
            c["close_saboteados"] += 1
            raise asyncio.CancelledError()
        try:
            await cerrar(self)
        except asyncio.CancelledError:
            c["close_cancelados"] += 1
            raise
        except BaseException:
            c["close_con_error"] += 1
            raise
        c["close_terminados"] += 1

    AsyncSession.close = close

    m.verify_password = _contar_en_vuelo(c, "bcrypt_en_vuelo", m.verify_password)

    sugerir = m._suggest_ncm_with_gemini

    def gemini(descripcion, limit=5):
        if not modo["gemini"]:
            return sugerir(descripcion, limit)
        time.sleep(modo["gemini"])
        return []

    m._suggest_ncm_with_gemini = _contar_en_vuelo(c, "gemini_en_vuelo", gemini)

    disponible = m.lectura_automatica_disponible
    m.lectura_automatica_disponible = lambda: bool(modo["pdf"]) or disponible()

    def leer_pdf(*args, **kwargs):
        time.sleep(modo["pdf"])
        raise m.DocumentoNoAdmitido("lector falso de la medición")

    m.process_pdf = _contar_en_vuelo(c, "pdf_en_vuelo", leer_pdf)

    from proyecto_maria.services import migration_service
    leer_hojas = migration_service._read_sheets

    def hojas(*args, **kwargs):
        time.sleep(modo["excel"])
        return leer_hojas(*args, **kwargs)

    migration_service._read_sheets = _contar_en_vuelo(c, "excel_en_vuelo", hojas)

    from starlette.requests import Request
    leer_cuerpo = Request.body

    async def body(self):
        # Sólo cuenta la primera lectura, la que espera al cliente.
        if hasattr(self, "_body"):
            return await leer_cuerpo(self)
        c["cuerpo_en_vuelo"] += 1
        c["cuerpo_en_vuelo_total"] += 1
        c["cuerpo_en_vuelo_max"] = max(c["cuerpo_en_vuelo_max"], c["cuerpo_en_vuelo"])
        try:
            return await leer_cuerpo(self)
        finally:
            c["cuerpo_en_vuelo"] -= 1

    Request.body = body


def post_worker_init(worker):
    from proyecto_maria.database.connection import engine

    pool = engine.pool
    c = Counter()
    modo = {"armado": False, "gemini": 0.0, "pdf": 0.0, "excel": 0.0}
    sabotaje = os.environ.get("CONEXIONES1_SABOTAJE", "")
    _instalar(c, modo, sabotaje)

    class _Sonda(BaseHTTPRequestHandler):
        def do_GET(self):
            pedido = urlparse(self.path)
            if pedido.path == "/armar":
                modo["armado"] = True
            elif pedido.path == "/modo":
                for clave, valor in parse_qs(pedido.query).items():
                    modo[clave] = float(valor[0])
            # El loop del worker suma claves mientras este hilo copia.
            while True:
                try:
                    contadores = dict(c)
                    break
                except RuntimeError:
                    pass
            cuerpo = json.dumps({
                "pid": os.getpid(),
                "tomadas": pool.checkedout(),
                "libres": pool.checkedin(),
                "desborde": pool.overflow(),
                "tamano": pool.size(),
                "modo": modo,
                "sabotaje": sabotaje,
                **contadores,
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
