"""CONEXIONES-1 G: ¿cuánto le cuesta al worker que una cuenta impaga mande
cuerpos grandes a /api/operations/manual?

Uso, desde la raíz del árbol que se quiere medir y con Postgres 16 descartable:

    scripts/testing/con_pg16.sh python scripts/testing/conexiones1_cuerpo.py

Levanta gunicorn igual que `conexiones1_medir.py` (flags del CMD del
`Dockerfile`, un worker, la sonda). Siembra dos cuentas: la impaga
(`past_due`, que da 402) y la otra, al día. En cada ronda la impaga abre N
sockets y manda el cuerpo entero menos sus dos últimos bytes. Después espera,
sin plazo fijo, a que cada pedido esté en uno de dos estados: ya respondido, o
retenido con todo lo mandado leído por el worker (la cola de recepción del
puerto en cero y la sonda con N lecturas de cuerpo en vuelo). Con los cuerpos
retenidos mide la memoria del worker y lo que espera la otra cuenta. Después
manda los dos bytes que faltan y cronometra el 402.

La memoria sale de `/proc/<pid>/status` del worker: `VmHWM` se reinicia antes de
cada ronda escribiendo 5 en `clear_refs`, así que da el pico exacto de la ronda.

Sale con 0 si la medición vale y con 2 si no vale: la impaga recibió algo que no
es 402, se cortó sin respuesta, el worker se recicló o no llegó al estado
esperado. No tiene umbral de aprobado: mide.
"""

import argparse
import asyncio
import os
import secrets
import shlex
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

import asyncpg
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conexiones1_medir import (  # noqa: E402
    OTRA, RAIZ, Medicion, argv_del_dockerfile, arrancar, cerrar, con_base,
    entorno_de_la_app, ip_al_azar, puerto_libre, sembrar_y_entrar,
)

IMPAGA = "medicion_impaga"
MB = 1024 * 1024
TRAMO = b"a" * MB
RETENIDOS = 2  # los bytes del final que se mandan recién al soltar


def memoria(pid) -> dict:
    """VmRSS y VmHWM del proceso, en MB."""
    valores = {}
    for linea in Path(f"/proc/{pid}/status").read_text().splitlines():
        clave, _, resto = linea.partition(":")
        if clave in ("VmRSS", "VmHWM"):
            valores[clave] = round(int(resto.split()[0]) / 1024, 1)
    return valores


def reiniciar_pico(pid) -> None:
    Path(f"/proc/{pid}/clear_refs").write_text("5")


def cola_de_recepcion(puerto) -> int:
    """Bytes que llegaron al puerto de la app y el worker todavía no leyó."""
    total = 0
    for archivo in ("/proc/net/tcp", "/proc/net/tcp6"):
        if not Path(archivo).exists():
            continue
        for linea in Path(archivo).read_text().splitlines()[1:]:
            campos = linea.split()
            if int(campos[1].rsplit(":", 1)[1], 16) == puerto:
                total += int(campos[4].split(":")[1], 16)
    return total


class Subida:
    """Un POST de la impaga por un socket propio, con el cuerpo retenido al final."""

    def __init__(self, puerto, token, tamano):
        self.puerto, self.token, self.tamano = puerto, token, tamano
        self.enviados = 0
        self.parcial = False  # mandó todo menos lo retenido
        self.codigo = self.t_respuesta = self.enviados_al_responder = None
        self.cortada = None  # el servidor cerró sin responder
        self.soltar = asyncio.Event()

    async def correr(self):
        lector, escritor = await asyncio.open_connection("127.0.0.1", self.puerto)
        self.t0 = time.monotonic()
        tarea = asyncio.create_task(self._escribir(escritor))
        try:
            await self._leer(lector)
        finally:
            tarea.cancel()
            await asyncio.gather(tarea, return_exceptions=True)
            escritor.close()

    async def _escribir(self, escritor):
        cabecera = (f"POST /api/operations/manual HTTP/1.1\r\nHost: 127.0.0.1\r\n"
                    f"Authorization: Bearer {self.token}\r\nX-Forwarded-For: {ip_al_azar()}\r\n"
                    f"Content-Type: application/json\r\nContent-Length: {self.tamano}\r\n"
                    f"Connection: close\r\n\r\n").encode()
        cuerpo_sin_final = self.tamano - RETENIDOS
        try:
            escritor.write(cabecera + b'{"x":"')
            self.enviados = 6
            while self.enviados < cuerpo_sin_final:
                tramo = TRAMO[:cuerpo_sin_final - self.enviados]
                escritor.write(tramo)
                await escritor.drain()
                self.enviados += len(tramo)
            self.parcial = True
            await self.soltar.wait()
            self.t_suelta = time.monotonic()
            escritor.write(b'"}')
            await escritor.drain()
            self.enviados += RETENIDOS
        except (ConnectionError, OSError) as err:
            self.error_escritura = type(err).__name__

    async def _leer(self, lector):
        try:
            linea = await lector.readline()
        except (ConnectionError, OSError):
            linea = b""
        if not linea:
            self.cortada = True
            return
        self.t_respuesta = time.monotonic()
        self.enviados_al_responder = self.enviados
        self.codigo = int(linea.split()[1])
        largo = 0
        while (cab := await lector.readline()) not in (b"\r\n", b""):
            if cab.lower().startswith(b"content-length:"):
                largo = int(cab.split(b":")[1])
        await lector.readexactly(largo)

    def resultado(self) -> dict:
        retenida = hasattr(self, "t_suelta") and self.t_respuesta and self.t_respuesta >= self.t_suelta
        desde = self.t_suelta if retenida else self.t0
        return {
            "codigo": self.codigo, "cortada": bool(self.cortada), "retenida": bool(retenida),
            "s_al_402": round(self.t_respuesta - desde, 3) if self.t_respuesta else None,
            "mb_enviados_al_402": round(self.enviados_al_responder / MB, 1)
            if self.enviados_al_responder is not None else None,
        }


class OtraCuenta:
    """La cuenta al día pide sin pausa mientras dura la ronda, anotando en qué fase."""

    def __init__(self, puerto, token):
        self.c = httpx.AsyncClient(base_url=f"http://127.0.0.1:{puerto}", timeout=120,
                                   headers={"Authorization": f"Bearer {token}"})
        self.fase, self.serie = "", []

    async def pedir(self):
        ruta = ("/auth/current_user", "/api/billing/me")[len(self.serie) % 2]
        t0 = time.monotonic()
        try:
            r = await self.c.get(ruta, headers={"X-Forwarded-For": ip_al_azar()})
            codigo = r.status_code
        except httpx.TransportError as err:
            codigo = type(err).__name__
        self.serie.append((self.fase, codigo, time.monotonic() - t0))

    async def linea_de_base(self, n=20):
        self.fase, self.serie = "base", []
        for _ in range(n):
            await self.pedir()

    async def mientras(self, fin: asyncio.Event, subidas):
        """Pide una vez por cada 5 % de bytes subidos, cambio de fase o respuesta.

        Sin pausa llegaría a --max-requests del Dockerfile y reciclaría el worker.
        """
        paso = sum(s.tamano for s in subidas) / 20

        def estado():
            return (sum(s.enviados for s in subidas) // paso, self.fase,
                    sum(1 for s in subidas if s.codigo or s.cortada))

        while not fin.is_set():
            visto = estado()
            await self.pedir()
            while estado() == visto and not fin.is_set():
                await asyncio.sleep(0.05)

    def resumen(self) -> dict:
        por_fase = {}
        for fase, codigo, seg in self.serie:
            por_fase.setdefault(fase, []).append((codigo, seg))
        salida = {}
        for fase, filas in por_fase.items():
            ms = sorted(round(s * 1000, 1) for _, s in filas)
            salida[fase] = {"n": len(ms), "mediana_ms": ms[len(ms) // 2], "max_ms": ms[-1],
                            "no_200": sum(1 for c, _ in filas if c != 200)}
        return salida


async def _listo(med, puerto, subidas):
    """Cada subida respondió, o mandó todo menos lo retenido y el worker lo leyó."""
    pendientes = [s for s in subidas if s.codigo is None and not s.cortada]
    if any(not s.parcial for s in pendientes):
        return False, "subiendo"
    cola = cola_de_recepcion(puerto)
    en_vuelo = (await med.sonda()).get("cuerpo_en_vuelo", 0)
    return cola == 0 and en_vuelo == len(pendientes), {"cola": cola, "en_vuelo": en_vuelo}


async def ronda(med, puerto, token, otra, n, tamano_mb, plazo) -> dict:
    ok, _, dato = await med.esperar(med._quieta, plazo)
    if not ok:
        return {"invalida": f"la app no quedó quieta antes de la ronda: {dato}"}
    p0 = await med.sonda()
    pid = p0["pid"]
    await otra.linea_de_base()
    reiniciar_pico(pid)
    antes = memoria(pid)
    subidas = [Subida(puerto, token, tamano_mb * MB) for _ in range(n)]
    fin = asyncio.Event()
    otra.fase = "subiendo"
    muestreo = asyncio.create_task(otra.mientras(fin, subidas))
    tareas = [asyncio.create_task(s.correr()) for s in subidas]
    listo, s_listo, dato = await med.esperar(_listo, plazo, med, puerto, subidas)
    otra.fase = "retenido"
    retenidas = [s for s in subidas if s.codigo is None and not s.cortada]
    en_retencion = {**memoria(pid), "retenidas": len(retenidas),
                    "cuerpo_en_vuelo": (await med.sonda()).get("cuerpo_en_vuelo", 0)}
    await otra.pedir()
    vivas = sum(1 for s in retenidas if s.codigo is None and not s.cortada)
    otra.fase = "soltado"
    for s in subidas:
        s.soltar.set()
    try:
        await asyncio.wait_for(asyncio.gather(*tareas), plazo)
    except asyncio.TimeoutError:
        pass
    fin.set()
    await muestreo
    ok, _, _ = await med.esperar(med._quieta, plazo)
    p1 = await med.sonda()
    return {
        "n": n, "mb": tamano_mb, "listo": listo, "s_hasta_listo": s_listo, "dato_listo": dato,
        "antes": antes, "en_retencion": en_retencion, "vivas_al_soltar": vivas,
        "despues": memoria(pid), "quieta_al_final": ok, "pid_final": p1["pid"], "pid": pid,
        "lecturas_de_cuerpo": p1.get("cuerpo_en_vuelo_total", 0) - p0.get("cuerpo_en_vuelo_total", 0),
        "subidas": [s.resultado() for s in subidas], "otra": otra.resumen(),
    }


def problemas(r) -> list:
    """Lo que hace que la ronda no valga como medición."""
    if "invalida" in r:
        return [r["invalida"]]
    malos = []
    codigos = sorted({s["codigo"] for s in r["subidas"]}, key=str)
    if codigos != [402]:
        malos.append(f"la impaga recibió {codigos}, no sólo 402")
    if not r["listo"]:
        malos.append(f"no llegó a responder o retener todo: {r['dato_listo']}")
    if r["pid_final"] != r["pid"]:
        malos.append(f"el worker se recicló ({r['pid']} → {r['pid_final']})")
    if not r["quieta_al_final"]:
        malos.append("la app no quedó quieta al final")
    if r["vivas_al_soltar"] != r["en_retencion"]["retenidas"]:
        malos.append("el servidor cortó una subida retenida antes de soltarla")
    return malos


def imprimir(r) -> None:
    print(f"\n== {r.get('n')} × {r.get('mb')} MB")
    if "invalida" in r:
        return
    print(f"listo en {r['s_hasta_listo']} s · retenidas {r['en_retencion']['retenidas']}"
          f" · lecturas de cuerpo en la ronda {r['lecturas_de_cuerpo']}")
    print(f"memoria MB: antes RSS {r['antes']['VmRSS']} · retenido RSS {r['en_retencion']['VmRSS']}"
          f" · pico {r['despues']['VmHWM']} · después RSS {r['despues']['VmRSS']}")
    for s in r["subidas"]:
        print("  impaga:", s)
    for fase, datos in r["otra"].items():
        print(f"  otra cuenta, {fase}: {datos}")


def arbol() -> str:
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=RAIZ, capture_output=True,
                         text=True).stdout.strip()
    sucio = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", "proyecto_maria"],
                           cwd=RAIZ).returncode != 0
    lee = "Depends(_leer_cuerpo)" in (RAIZ / "proyecto_maria" / "main.py").read_text()
    return f"árbol {sha}{' con cambios en proyecto_maria' if sucio else ''}" \
           f" · main.py {'lee' if lee else 'no lee'} el cuerpo antes del cobro"


async def medir(a, med, proc, log, puerto) -> list:
    if not await arrancar(med.c, proc, log, med):
        return [{"invalida": "la app no arrancó"}]
    token = await sembrar_y_entrar(med, IMPAGA)
    token_otra = await sembrar_y_entrar(med, OTRA)
    if None in (token, token_otra):
        return [{"invalida": "no pude entrar con las cuentas sembradas"}]
    await med.pg.execute("update users set billing_status = 'past_due' where username = $1", IMPAGA)
    otra = OtraCuenta(puerto, token_otra)
    resultados = []
    try:
        for spec in a.rondas.split(","):
            n, mb = (int(x) for x in spec.split("x"))
            r = await ronda(med, puerto, token, otra, n, mb, a.plazo)
            imprimir(r)
            resultados.append(r)
            if problemas(r):
                break
    finally:
        await otra.c.aclose()
    return resultados


def parsear():
    ap = argparse.ArgumentParser()
    ap.add_argument("pg_admin", nargs="?", default=os.environ.get("BACKUP1A_PG_URL"),
                    help="URL de Postgres con permiso para crear bases")
    ap.add_argument("--rondas", default="1x1,1x10,1x100,1x500,8x100,8x100,8x100",
                    help="N×MB por ronda: N subidas a la vez de MB cada una")
    ap.add_argument("--plazo", type=float, default=300.0)
    a = ap.parse_args()
    if not a.pg_admin:
        sys.exit("falta la URL de Postgres (argumento o BACKUP1A_PG_URL)")
    return a


async def main() -> int:
    a = parsear()
    print(arbol())
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
                                    env=entorno_de_la_app(url_base, puerto, puerto_sonda, secreto,
                                                          tmp, False),
                                    start_new_session=True)
        med = Medicion(a, pg, base, puerto, puerto_sonda, secreto, log)
        resultados = await medir(a, med, proc, log, puerto)
    finally:
        await cerrar(admin, pg, proc, med, base)
    malos = [m for r in resultados for m in problemas(r)]
    print(f"\nlog de gunicorn: {log}")
    print("LA MEDICIÓN NO VALE: " + "; ".join(malos) if malos else "medición válida")
    return 2 if malos else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
