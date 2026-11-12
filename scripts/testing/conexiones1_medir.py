"""CONEXIONES-1: ¿quedan conexiones de Postgres tomadas después de 401, cortes
del cliente, bcrypt, Gemini o la lectura de un PDF?

Uso, desde la raíz de un checkout y con Postgres 16 descartable:

    scripts/testing/con_pg16.sh python scripts/testing/conexiones1_medir.py

La URL de admin sale de `BACKUP1A_PG_URL` (la exporta `con_pg16.sh`) o del
primer argumento. Crea una base descartable y levanta gunicorn con los flags del
CMD del `Dockerfile`, leídos del archivo. Sólo cambia la IP del bind a 127.0.0.1
y suma `-c conexiones1_sonda.py`, que expone los contadores. Corre con
ENVIRONMENT=production, la clave de Gemini vacía y DOLARAPI apuntando a un
puerto cerrado.

Después de cada fase no espera un tiempo fijo, sino condiciones:

- terminó cada `MetricsMiddleware.dispatch` y cada tarea que guarda la fila de
  `api_logs`;
- no hay ningún `close()` de sesión en curso, ni ningún bcrypt, Gemini o lector
  de PDF en vuelo;
- después, el pool vuelve a las tomadas que tenía al empezar la fase y
  `pg_stat_activity` no tiene conexiones fuera de reposo ni más de las que el
  pool cree tener.

En cada pico, los pedidos rápidos son de otra cuenta: miden lo que espera un
usuario que no carga nada mientras otro satura.

Sale con 0 si no queda nada tomado y la otra cuenta no sufrió; con 1 si queda
algo tomado o el log muestra una conexión perdida; con 2 si la medición no vale
(respuestas inesperadas, el worker se recicló o la app no arrancó), y con 4 si
nada quedó tomado pero el pool se llenó: algún 500, el aviso de QueuePool en el
log o la otra cuenta esperando más de `--espera-otra`. El 3 no se usa: es el
de `con_pg16.sh` cuando Postgres no levanta.
"""

import argparse
import asyncio
import collections
import io
import os
import functools
import random
import re
import secrets
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import asyncpg
import bcrypt
import httpx
import jwt

RAIZ = Path.cwd()
SONDA = Path(__file__).resolve().with_name("conexiones1_sonda.py")
USUARIO, OTRA = "medicion", "medicion_otra"
DESCRIPCION = "taladro inalambrico de prueba"

SEÑALES_DE_FUGA = (
    "non-checked-in connection",
    "Task was destroyed but it is pending",
)
SEÑALES_DE_POOL_LLENO = ("QueuePool limit",)
SEÑALES_A_LA_VISTA = (
    "CancelledError",
    "UnboundLocalError",
    "Exception in ASGI application",
    "Error logging metrics",
    "Traceback",
)

# El `detail` que acepta cada 401: el de esta rama o el de la rama de MARIA.
DETALLES_401 = {
    "sin_token": {"No autenticado"},
    "mal_firmado": {"Token inválido o expirado", "Sesión inválida o vencida"},
    "sin_sub": {"Token inválido", "Sesión inválida o vencida"},
    "inexistente": {"Usuario no encontrado", "Sesión inválida o vencida"},
    "revocado": {"Token revocado", "Sesión inválida o vencida"},
    "login_clave_mala": {"Credenciales inválidas"},
}
ESPERADO = {"normal": 200, "otra": 200, "sugerir": 200, "pdf_sin_lector": 503,
            "pico_gemini": 200, "pico_pdf": 422, "pico_bcrypt": 401, "pico_excel": 200,
            "manual_lento": 404}
EN_VUELO = ("bcrypt_en_vuelo", "gemini_en_vuelo", "pdf_en_vuelo", "excel_en_vuelo",
            "cuerpo_en_vuelo")
# Una planilla chica cuyos encabezados se reconocen sin la IA.
CSV_CHICO = b"cuit,nombre\n20123456786,Cliente Uno\n"
# Lo que el pico puede devolverle a la cuenta que lo carga sin que sea un rojo.
LIMPIOS_DEL_PICO = {429, 503, 504}


def argv_del_dockerfile(puerto: int) -> list:
    texto = (RAIZ / "Dockerfile").read_text()
    m = re.search(r"^CMD exec (gunicorn(?:[^\n]*\\\n)*[^\n]*)", texto, re.M)
    if not m:
        sys.exit("no encontré el CMD de gunicorn en el Dockerfile")
    partes = shlex.split(m.group(1).replace("\\\n", " "))
    assert partes[:2] == ["gunicorn", "proyecto_maria.main:app"], partes[:2]
    i = partes.index("--bind")
    assert partes[i + 1] == "0.0.0.0:${PORT}", partes[i + 1]
    partes[i + 1] = f"127.0.0.1:{puerto}"
    partes[0] = str(Path(sys.executable).with_name("gunicorn"))
    return partes + ["-c", str(SONDA)]


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def ip_al_azar() -> str:
    # El límite por IP de login y de subida sólo mira el primer valor de XFF.
    return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


def con_base(url: str, base: str) -> str:
    partes = urlsplit(url)
    return urlunsplit(partes._replace(path="/" + base))


def pdf_en_blanco() -> bytes:
    from pypdf import PdfWriter

    escritor, salida = PdfWriter(), io.BytesIO()
    escritor.add_blank_page(100, 100)
    escritor.write(salida)
    return salida.getvalue()


async def estados_pg(pg, base: str) -> dict:
    filas = await pg.fetch(
        "select coalesce(state, '?') as s, count(*) as n from pg_stat_activity "
        "where datname = $1 and pid <> pg_backend_pid() "
        "and backend_type = 'client backend' group by 1",
        base,
    )
    return {f["s"]: f["n"] for f in filas}


def en_curso(p: dict) -> dict:
    """Lo que la sonda ve sin terminar; vacío cuando la fase cerró."""
    errores = sum(v for k, v in p.items() if k.startswith("dispatch_error_"))
    pendiente = {
        "dispatch": p.get("dispatch_entradas", 0) - p.get("dispatch_ok", 0)
        - p.get("dispatch_cancelados", 0) - errores,
        "close": p.get("close_empezados", 0) - p.get("close_terminados", 0)
        - p.get("close_cancelados", 0) - p.get("close_con_error", 0)
        - p.get("close_saboteados", 0),
        "log": p.get("log_tareas", 0) - p.get("log_tareas_fin", 0)
        - p.get("log_tareas_canceladas", 0),
    }
    for k in EN_VUELO:
        pendiente[k] = p.get(k, 0)
    return {k: v for k, v in pendiente.items() if v}


class Medicion:
    def __init__(self, a, pg, base, puerto, puerto_sonda, secreto):
        self.a, self.pg, self.base = a, pg, base
        self.puerto, self.secreto = puerto, secreto
        self.sonda_cli = httpx.AsyncClient(base_url=f"http://127.0.0.1:{puerto_sonda}", timeout=10)
        self.c = httpx.AsyncClient(base_url=f"http://127.0.0.1:{puerto}", timeout=90)
        self.filas, self.invalida, self.fuga, self.lleno = [], False, False, False
        self.quinientos = 0
        self.pdf = pdf_en_blanco()

    async def sonda(self, ruta="/", **params) -> dict:
        return (await self.sonda_cli.get(ruta, params=params)).json()

    async def esperar(self, condicion, plazo, *args):
        """Consulta `condicion` hasta que dé verdadero o venza el plazo."""
        t0 = time.monotonic()
        while True:
            ok, dato = await condicion(*args)
            if ok or time.monotonic() - t0 > plazo:
                return ok, round(time.monotonic() - t0, 2), dato
            await asyncio.sleep(0.05)

    async def _cerrada(self):
        p = await self.sonda()
        pendiente = en_curso(p)
        return not pendiente, pendiente

    async def _quieta(self):
        # Entre fases no hay ningún pedido: quieto es nada tomado, nada fuera
        # de reposo en Postgres y ninguna conexión que el pool no conozca.
        p = await self.sonda()
        e = await estados_pg(self.pg, self.base)
        ajenas = sum(n for s, n in e.items() if s != "idle")
        quieta = p["tomadas"] == 0 and ajenas == 0 and sum(e.values()) == p["libres"]
        return quieta, (p, e)

    async def _subio(self, clave, antes):
        p = await self.sonda()
        return p.get(clave, 0) > antes, p.get(clave, 0)

    # --- pedidos -----------------------------------------------------------

    def tokens(self, token, otra):
        exp = datetime.now(timezone.utc) + timedelta(hours=1)
        firmar = lambda datos, clave=self.secreto: jwt.encode(datos, clave, "HS256")
        self.t = {
            "normal": token,
            "otra": otra,
            "mal_firmado": firmar({"sub": USUARIO, "jti": "x", "exp": exp}, "otra-" + self.secreto),
            "sin_sub": firmar({"jti": "x", "exp": exp}),
            "inexistente": firmar({"sub": "no-existe", "jti": "x", "exp": exp}),
            "revocado": firmar({"sub": USUARIO, "jti": "otro", "exp": exp}),
        }

    def armar(self, tipo) -> httpx.Request:
        """El pedido de cada tipo, para mandarlo con httpx o por un socket crudo."""
        url = f"http://127.0.0.1:{self.puerto}"
        auth = {"Authorization": f"Bearer {self.t['normal']}"}
        if tipo in ("login_clave_mala", "pico_bcrypt", "corte_bcrypt"):
            return httpx.Request("POST", url + "/auth/login",
                                 json={"username": USUARIO, "password": "mala-" + secrets.token_hex(4)},
                                 headers={"X-Forwarded-For": ip_al_azar()})
        if tipo in ("sugerir", "pico_gemini", "corte_gemini"):
            return httpx.Request("POST", url + "/api/ncm/sugerir", json={"descripcion": DESCRIPCION},
                                 headers=auth)
        if tipo in ("pdf_sin_lector", "pico_pdf", "corte_pdf"):
            return httpx.Request("POST", url + "/upload_pdf/public",
                                 files={"file": ("medicion.pdf", self.pdf, "application/pdf")},
                                 headers={**auth, "X-Forwarded-For": ip_al_azar()})
        if tipo == "pico_excel":
            return httpx.Request("POST", url + "/api/migrations/analyze",
                                 files={"file": ("clientes.csv", CSV_CHICO, "text/csv")}, headers=auth)
        if tipo == "manual_lento":
            # Un cliente que no existe: la ruta lee el cuerpo entero y responde 404.
            return httpx.Request("POST", url + "/api/operations/manual", headers=auth, json={
                "client_id": 999999999, "items": [{"ncm": "8471.30.12", "descripcion": DESCRIPCION,
                                                   "cantidad": 1, "valor_unitario": 10}]})
        cabeceras = {}
        if tipo in self.t:
            cabeceras["Authorization"] = f"Bearer {self.t[tipo]}"
        return httpx.Request("GET", url + "/auth/current_user", headers=cabeceras)

    async def mandar(self, tipo, codigos, latencias=None):
        t0 = time.monotonic()
        r = await self.c.send(self.armar(tipo))
        if latencias is not None:
            latencias.append(time.monotonic() - t0)
        detalle = ""
        if r.status_code == 401 and tipo in DETALLES_401:
            detalle = r.json().get("detail", "")
            if detalle in DETALLES_401[tipo]:
                detalle = ""
        codigos[(tipo, r.status_code, detalle)] += 1

    def crudo(self, tipo, sobra=0):
        """Cabecera y cuerpo del pedido para un socket crudo; `sobra` agranda el
        content-length para que la app espere bytes que no llegan."""
        pedido = self.armar(tipo)
        cuerpo = pedido.read()
        cabeceras = dict(pedido.headers)
        cabeceras["content-length"] = str(len(cuerpo) + sobra)
        linea = f"{pedido.method} {pedido.url.raw_path.decode()} HTTP/1.1\r\n"
        return (linea + "".join(f"{k}: {v}\r\n" for k, v in cabeceras.items()) + "\r\n").encode(), cuerpo

    async def cortar(self, tipo, clave, cuerpo_a_medias=False):
        """Manda el pedido por un socket crudo y lo cierra cuando la sonda ve
        que `clave` subió: el corte cae con el pedido en vuelo."""
        crudo, cuerpo = self.crudo(tipo, 64 if cuerpo_a_medias else 0)
        antes = (await self.sonda()).get(clave, 0)
        r, w = await asyncio.open_connection("127.0.0.1", self.puerto)
        w.write(crudo + cuerpo)
        await w.drain()
        ok, _, _ = await self.esperar(self._subio, 30, clave, antes)
        w.close()
        await w.wait_closed()
        return ok

    # --- fases -------------------------------------------------------------

    async def muestrear(self, maximo, fin, serie):
        t0 = time.monotonic()
        while not fin.is_set():
            p = await self.sonda()
            e = await estados_pg(self.pg, self.base)
            maximo["tomadas"] = max(maximo["tomadas"], p["tomadas"])
            maximo["pg"] = max(maximo["pg"], sum(e.values()))
            serie.append((round(time.monotonic() - t0, 2), p["tomadas"],
                          {k[:-9]: p[k] for k in EN_VUELO if p.get(k)}))
            await asyncio.sleep(0.05)

    async def fase(self, nombre, tareas, enviados_registrables=None):
        antes = await self.sonda()
        t0 = await self.pg.fetchval("select clock_timestamp()")
        maximo, fin, serie = {"tomadas": 0, "pg": 0}, asyncio.Event(), []
        muestreo = asyncio.create_task(self.muestrear(maximo, fin, serie))
        resultados = await asyncio.gather(*tareas)
        cerrada, seg_c, pendiente = await self.esperar(self._cerrada, self.a.plazo)
        fin.set()
        await muestreo
        quieta, seg_q, (p, e) = await self.esperar(self._quieta, self.a.plazo)
        filas_por_codigo = {f["status_code"]: f["n"] for f in await self.pg.fetch(
            "select status_code, count(*) as n from api_logs where created_at >= $1 group by 1", t0)}
        filas = sum(filas_por_codigo.values())
        delta = lambda k: p.get(k, 0) - antes.get(k, 0)
        fila = dict(nombre=nombre, enviados=len(tareas), max_tomadas=maximo["tomadas"],
                    max_pg=maximo["pg"], cerrada=cerrada, pendiente=pendiente,
                    quieta=quieta, seg=round(seg_c + seg_q, 2),
                    quedaron=p["tomadas"], pg_final=e,
                    dispatch=delta("dispatch_entradas"), tareas_log=delta("log_tareas"),
                    filas=filas, codigos_en_api_logs=filas_por_codigo, cancelados=delta("dispatch_cancelados"),
                    errores={k[15:]: delta(k) for k in p if k.startswith("dispatch_error_") and delta(k)},
                    serie=serie)
        self.filas.append(fila)
        if not quieta:
            self.fuga = True
        if not cerrada:
            print(f"  {nombre}: la fase no cerró en {self.a.plazo} s: {pendiente}")
            self.invalida = True
        if enviados_registrables is not None and filas != enviados_registrables:
            print(f"  {nombre}: {enviados_registrables} pedidos y {filas} filas nuevas en api_logs")
            self.invalida = True
        return resultados

    async def fase_de_pedidos(self, nombre, tipos):
        codigos = collections.Counter()
        await self.fase(nombre, [self.mandar(t, codigos) for t in tipos], len(tipos))
        self.revisar_codigos(nombre, codigos)

    def revisar_codigos(self, nombre, codigos, aceptados=None):
        print(f"{nombre}: {dict(sorted(codigos.items()))}")
        aceptados = aceptados or {}
        malos = {k: v for k, v in codigos.items()
                 if k[1] != ESPERADO.get(k[0], 401) and k[1] not in aceptados.get(k[0], ()) or k[2]}
        if malos:
            print(f"  respuestas inesperadas: {malos}")
            self.invalida = True

    async def fase_de_cortes(self, nombre, tipo, clave, n, modo=None, a_medias=False):
        if modo:
            await self.sonda("/modo", **modo)
        hechos = []

        async def en_serie():
            # Uno por vez: cada corte espera su propia condición en la sonda.
            for _ in range(n):
                hechos.append(await self.cortar(tipo, clave, a_medias))

        await self.fase(nombre, [en_serie()])
        self.filas[-1]["enviados"] = n
        hechos = sum(hechos)
        if modo:
            await self.sonda("/modo", **{k: 0 for k in modo})
        print(f"{nombre}: {hechos} de {n} cortados con el pedido en vuelo")
        if hechos != n:
            self.invalida = True

    async def fase_de_pico(self, nombre, tipo, clave, n, normales, modo):
        await self.sonda("/modo", **modo)
        codigos, latencias = collections.Counter(), []
        antes = (await self.sonda()).get(clave, 0)

        async def lentos():
            await asyncio.gather(*(self.mandar(tipo, codigos) for _ in range(n)))

        async def rapidos():
            await self.esperar(self._subio, 30, clave, antes)
            await asyncio.gather(*(self.mandar("otra", codigos, latencias) for _ in range(normales)))

        await self.fase(nombre, [lentos(), rapidos()], n + normales)
        await self.sonda("/modo", **{k: 0 for k in modo})
        espera = round(max(latencias, default=0), 2)
        self.filas[-1]["enviados"] = n + normales
        self.filas[-1]["latencia_otra_max"] = espera
        quinientos = sum(v for (_, codigo, _), v in codigos.items() if codigo == 500)
        self.quinientos += quinientos
        print(f"{nombre}: la otra cuenta recibió {codigos[('otra', 500, '')]} × 500 "
              f"y esperó hasta {espera} s; en total, {quinientos} × 500")
        if quinientos or espera > self.a.espera_otra:
            self.lleno = True
        # El 500 es el rojo del pool lleno, no una medición que no vale.
        self.revisar_codigos(nombre, codigos, {tipo: LIMPIOS_DEL_PICO | {500}, "otra": {500}})

    async def _llegaron(self, n):
        p = await self.sonda()
        return p.get("cuerpo_en_vuelo", 0) >= n, (p.get("cuerpo_en_vuelo", 0), p["tomadas"])

    async def fase_de_cuerpo_lento(self, nombre, tipo, n, normales):
        """n pedidos mandan la cabecera y medio cuerpo; con los n esperando el
        resto, la otra cuenta pide, y después se termina cada cuerpo."""
        crudo, cuerpo = self.crudo(tipo)
        mitad = len(cuerpo) // 2
        codigos, latencias, llegados = collections.Counter(), [], []

        async def lento(conexion):
            r, w = conexion
            await conexion_lista.wait()
            w.write(cuerpo[mitad:])
            await w.drain()
            estado = await r.readline()
            w.close()
            await w.wait_closed()
            codigos[(tipo, int(estado.split()[1]) if estado else 0, "")] += 1

        async def todos():
            conexiones = [await asyncio.open_connection("127.0.0.1", self.puerto) for _ in range(n)]
            for _, w in conexiones:
                w.write(crudo + cuerpo[:mitad])
                await w.drain()
            ok, seg, cuantos = await self.esperar(self._llegaron, 10, n)
            llegados.append((ok, seg, cuantos))
            await asyncio.gather(*(self.mandar("otra", codigos, latencias) for _ in range(normales)))
            conexion_lista.set()
            await asyncio.gather(*(lento(c) for c in conexiones))

        conexion_lista = asyncio.Event()
        await self.fase(nombre, [todos()], n + normales)
        ok, seg, (cuantos, tomadas) = llegados[0]
        espera = round(max(latencias, default=0), 2)
        self.filas[-1].update(enviados=n + normales, latencia_otra_max=espera,
                              esperando_cuerpo=cuantos, tomadas_esperando_cuerpo=tomadas)
        quinientos = sum(v for (_, codigo, _), v in codigos.items() if codigo == 500)
        self.quinientos += quinientos
        print(f"{nombre}: {cuantos} de {n} esperando el cuerpo a la vez "
              f"({'llegaron' if ok else 'no llegaron'} en {seg} s, con {tomadas} conexiones tomadas); la otra cuenta recibió "
              f"{codigos[('otra', 500, '')]} × 500 y esperó hasta {espera} s; en total, {quinientos} × 500")
        if quinientos or espera > self.a.espera_otra:
            self.lleno = True
        self.revisar_codigos(nombre, codigos, {tipo: {500}, "otra": {500}})

    async def todas(self):
        a, f = self.a, functools.partial
        mezcla = [t for t in list(DETALLES_401) + ["normal"] for _ in range(a.mezcla // 7)]
        random.shuffle(mezcla)
        pasos = [f(self.fase_de_pedidos, tipo, [tipo] * a.n) for tipo in DETALLES_401] + [
            f(self.fase_de_pedidos, "normal", ["normal"] * a.normales),
            f(self.fase_de_pedidos, "mezcla", mezcla),
            f(self.fase_de_pedidos, "sugerir", ["sugerir"] * a.cortes),
            f(self.fase_de_pedidos, "pdf_sin_lector", ["pdf_sin_lector"] * 10),
            f(self.fase_de_cortes, "corte_cuerpo_a_medias", "login_clave_mala",
              "dispatch_entradas", a.cortes, a_medias=True),
            f(self.fase_de_cortes, "corte_bcrypt", "corte_bcrypt", "bcrypt_en_vuelo_total", a.cortes),
            f(self.fase_de_cortes, "corte_gemini", "corte_gemini", "gemini_en_vuelo_total",
              a.cortes, modo={"gemini": a.lento}),
            f(self.fase_de_cortes, "corte_pdf", "corte_pdf", "pdf_en_vuelo_total",
              a.cortes, modo={"pdf": a.lento}),
        ] + [f(self.fase_de_pico, nombre, tipo, clave, a.pico, a.pico_normales, modo)
             for nombre, tipo, clave, modo in (
                 ("pico_bcrypt", "pico_bcrypt", "bcrypt_en_vuelo_total", {}),
                 ("pico_gemini", "pico_gemini", "gemini_en_vuelo_total", {"gemini": a.lento}),
                 ("pico_pdf", "pico_pdf", "pdf_en_vuelo_total", {"pdf": a.lento}),
                 ("pico_excel", "pico_excel", "excel_en_vuelo_total", {"excel": a.lento}),
             )] + [f(self.fase_de_cuerpo_lento, "pico_cuerpo_manual", "manual_lento", a.pico, a.pico_normales)]
        for paso in pasos:
            await paso()
            # Con una conexión tomada el veredicto ya es 1, y con el pool lleno
            # cada fase siguiente sólo suma plazos vencidos.
            if self.fuga:
                print(f"  {self.filas[-1]['nombre']} dejó conexiones tomadas: no sigo")
                return

    def tabla(self):
        print()
        print(f"{'fase':<23}{'env':>4}{'disp':>5}{'tlog':>5}{'filas':>6}{'máxT':>5}{'máxPG':>6}"
              f"{'quedan':>7}  {'quieto':<7}{'seg':>6}  extra")
        for f in self.filas:
            extra = {k: f[k] for k in ("codigos_en_api_logs", "cancelados", "errores", "latencia_otra_max", "pendiente")
                     if f.get(k)}
            print(f"{f['nombre']:<23}{f['enviados']:>4}{f['dispatch']:>5}{f['tareas_log']:>5}"
                  f"{f['filas']:>6}{f['max_tomadas']:>5}{f['max_pg']:>6}{f['quedaron']:>7}  "
                  f"{'sí' if f['quieta'] else 'NO':<7}{f['seg']:>6}  {extra} pg={f['pg_final']}")
        for f in self.filas:
            if f["nombre"].startswith("pico_"):
                print(f"serie {f['nombre']}: " + resumir(f["serie"]))


def resumir(serie, paso=0.5) -> str:
    """Una muestra cada `paso` segundos: alcanza para ver si las tomadas caen
    mientras el punto lento sigue en meseta. Un pico de menos de 0,05 s se pierde."""
    salida, proximo = [], 0.0
    for t, tomadas, en_vuelo in serie:
        if t >= proximo:
            salida.append(f"{t}s T={tomadas} {en_vuelo or ''}".rstrip())
            proximo = t + paso
    return " · ".join(salida)


def entorno_de_la_app(url_base, puerto, puerto_sonda, secreto, tmp, cuota_de_produccion) -> dict:
    entorno = {
        k: v for k, v in os.environ.items()
        if not k.startswith(("PYTEST", "REDIS", "DATABASE", "JWT", "SECRET", "GEMINI", "BACKUP1A"))
    }
    entorno.update(
        ENVIRONMENT="production", PORT=str(puerto), DATABASE_URL=url_base,
        JWT_SECRET_KEY=secreto, ALLOWED_ORIGINS="http://127.0.0.1",
        FRONTEND_URL="http://127.0.0.1", CDI_DATA_DIR=str(tmp / "data"),
        VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
        DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares", GEMINI_API_KEY="",
        PYTHONPATH=str(RAIZ), PYTHONUNBUFFERED="1", PYTHONDONTWRITEBYTECODE="1",
        CONEXIONES1_SONDA_PUERTO=str(puerto_sonda),
    )
    entorno.pop("AI_DAILY_PDF_LIMIT", None)
    if not cuota_de_produccion:
        entorno["AI_DAILY_PDF_LIMIT"] = "100000"
    return entorno


async def arrancar(c, proc, log, med) -> bool:
    t0 = time.monotonic()
    while True:
        if proc.poll() is not None:
            print("gunicorn terminó al arrancar:\n" + log.read_text()[-3000:])
            return False
        try:
            if (await c.get("/health")).status_code == 200:
                await med.sonda()
                return True
        except (httpx.TransportError, OSError, ValueError):
            pass
        if time.monotonic() - t0 > 120:
            print("la app no respondió /health en 120 s:\n" + log.read_text()[-3000:])
            return False
        await asyncio.sleep(0.2)


async def sembrar_y_entrar(med, usuario) -> str | None:
    clave = secrets.token_urlsafe(16)
    await med.pg.execute(
        "insert into users (username, email, password, name, plan, roles, "
        "is_verified, billing_status, trial_ends_at) values "
        "($1, $2, $3, 'Medicion', 'premium', '[]'::json, true, 'active', $4)",
        usuario, f"{usuario}@ejemplo.test",
        bcrypt.hashpw(clave.encode(), bcrypt.gensalt()).decode(),
        datetime.now(timezone.utc) + timedelta(days=3650),
    )
    r = await med.c.post("/auth/login", json={"username": usuario, "password": clave},
                         headers={"X-Forwarded-For": ip_al_azar()})
    if r.status_code != 200:
        print("no pude entrar con la cuenta sembrada:", r.status_code, r.text[:300])
        return None
    med.c.cookies.clear()  # Bearer sin cookie: el CSRF sólo mira la cookie.
    return r.json()["access_token"]


async def medir(med, proc, log) -> None:
    if not await arrancar(med.c, proc, log, med):
        med.invalida = True
        return
    tokens = [await sembrar_y_entrar(med, u) for u in (USUARIO, OTRA)]
    if None in tokens:
        med.invalida = True
        return
    med.tokens(*tokens)
    if os.environ.get("CONEXIONES1_SABOTAJE"):
        await med.sonda("/armar")
    pid0 = (await med.sonda())["pid"]
    await med.todas()
    pid1 = (await med.sonda())["pid"]
    if pid1 != pid0:
        print(f"el worker se recicló ({pid0} → {pid1}): la medición no vale")
        med.invalida = True
    med.tabla()
    p = await med.sonda()
    print(f"\nsonda al final: { {k: v for k, v in sorted(p.items()) if k != 'modo'} }")
    print(f"filas en api_logs: {await med.pg.fetchval('select count(*) from api_logs')}")


def leer_log(log, med) -> None:
    texto = log.read_text()
    print()
    for s in SEÑALES_DE_FUGA + SEÑALES_DE_POOL_LLENO + SEÑALES_A_LA_VISTA:
        n = texto.count(s)
        print(f"log: {s!r}: {n}")
        if n and s in SEÑALES_DE_FUGA:
            med.fuga = True
        if n and s in SEÑALES_DE_POOL_LLENO:
            med.lleno = True
        elif s in SEÑALES_DE_POOL_LLENO and med.quinientos:
            print(f"  {med.quinientos} × 500 en los picos sin {s!r} en el log: no sé de qué son")
            med.invalida = True
    print(f"log completo: {log}")


def parsear():
    ap = argparse.ArgumentParser()
    ap.add_argument("pg_admin", nargs="?", default=os.environ.get("BACKUP1A_PG_URL"),
                    help="URL de Postgres con permiso para crear bases")
    ap.add_argument("--n", type=int, default=40, help="pedidos por cada tipo de 401")
    ap.add_argument("--normales", type=int, default=40)
    ap.add_argument("--mezcla", type=int, default=84)
    ap.add_argument("--cortes", type=int, default=15, help="cortes por fase, y pedidos de sugerir")
    ap.add_argument("--pico", type=int, default=30, help="pedidos lentos por pico")
    ap.add_argument("--pico-normales", type=int, default=12)
    ap.add_argument("--lento", type=float, default=2.0, help="segundos de Gemini y del lector falsos")
    ap.add_argument("--plazo", type=float, default=90.0)
    ap.add_argument("--espera-otra", type=float, default=5.0,
                    help="segundos que la otra cuenta puede esperar en un pico")
    ap.add_argument("--cuota-de-produccion", action="store_true",
                    help="sin AI_DAILY_PDF_LIMIT: la cuota diaria de PDF de producción")
    a = ap.parse_args()
    if not a.pg_admin:
        sys.exit("falta la URL de Postgres (argumento o BACKUP1A_PG_URL)")
    return a


async def main() -> int:
    a = parsear()
    base = f"conexiones1_{uuid.uuid4().hex[:8]}"
    admin = await asyncpg.connect(a.pg_admin)
    proc = pg = med = None
    try:
        await admin.execute(f'create database "{base}"')
        url_base = con_base(a.pg_admin, base)
        pg = await asyncpg.connect(url_base)
        puerto, puerto_sonda, secreto = puerto_libre(), puerto_libre(), secrets.token_hex(32)
        tmp = Path(tempfile.mkdtemp(prefix="conexiones1_"))
        log = tmp / "gunicorn.log"
        argv = argv_del_dockerfile(puerto)
        print("gunicorn:", " ".join(shlex.quote(x) for x in argv[1:]))
        with open(log, "w") as salida:
            proc = subprocess.Popen(argv, cwd=RAIZ, stdout=salida, stderr=subprocess.STDOUT,
                                    env=entorno_de_la_app(url_base, puerto, puerto_sonda, secreto, tmp,
                                                          a.cuota_de_produccion),
                                    start_new_session=True)
        med = Medicion(a, pg, base, puerto, puerto_sonda, secreto)
        await medir(med, proc, log)
    finally:
        await cerrar(admin, pg, proc, med, base)
    leer_log(log, med)
    codigo = 1 if med.fuga else 2 if med.invalida else 4 if med.lleno else 0
    print({0: "sin conexiones tomadas", 1: "QUEDAN CONEXIONES TOMADAS",
           2: "LA MEDICIÓN NO VALE",
           4: "POOL LLENO: ninguna conexión quedó tomada, pero la otra cuenta o el log sufrieron"}[codigo])
    return codigo


async def cerrar(admin, pg, proc, med, base):
    if med is not None:
        await med.c.aclose()
        await med.sonda_cli.aclose()
    if proc is not None:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
    if pg is not None:
        await pg.close()
    await admin.execute(
        "select pg_terminate_backend(pid) from pg_stat_activity where datname = $1", base)
    await admin.execute(f'drop database if exists "{base}"')
    await admin.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
