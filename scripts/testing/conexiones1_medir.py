"""CONEXIONES-1: ¿quedan conexiones de Postgres tomadas después de muchos 401?

Uso, desde la raíz de un checkout:

    python scripts/testing/conexiones1_medir.py postgresql://cdi@127.0.0.1:55432/postgres

Crea una base descartable, levanta gunicorn con los flags del CMD del
`Dockerfile` (leídos del archivo; sólo cambia la IP del bind a 127.0.0.1 y se
agrega `-c conexiones1_sonda.py`, que expone los contadores del pool),
ENVIRONMENT=production. Siembra una cuenta y dispara fases de 401, normales,
una mezcla y cortes del cliente. Después de cada fase espera a que el pool y
`pg_stat_activity` queden quietos: nada tomado, nada en transacción y tantas
conexiones en Postgres como el pool cree tener. No hay esperas fijas: se
consulta la condición hasta que se cumple o vence el plazo.

Sale con 0 si no queda nada tomado, 1 si queda algo y 2 si la medición no
vale (respuestas inesperadas, el worker se recicló o la app no arrancó).
"""

import argparse
import asyncio
import collections
import json
import os
import random
import re
import secrets
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import asyncpg
import bcrypt
import httpx
import jwt

RAIZ = Path.cwd()
SONDA = Path(__file__).resolve().with_name("conexiones1_sonda.py")

# Lo que en el log de gunicorn delata una conexión perdida o una tarea
# cortada. Las dos primeras y la del pool lleno cuentan como fuga.
SEÑALES_DE_FUGA = (
    "non-checked-in connection",
    "Task was destroyed but it is pending",
    "QueuePool limit",
)
SEÑALES_A_LA_VISTA = (
    "CancelledError",
    "Event loop is closed",
    "Exception in ASGI application",
    "Error logging metrics",
    "Traceback",
)


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
    import socket

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def sonda(puerto: int) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/", timeout=5) as r:
        return json.loads(r.read())


async def estados_pg(pg, base: str) -> dict:
    filas = await pg.fetch(
        "select coalesce(state, '?') as s, count(*) as n from pg_stat_activity "
        "where datname = $1 and pid <> pg_backend_pid() group by 1",
        base,
    )
    return {f["s"]: f["n"] for f in filas}


async def esperar_quieto(pg, base, puerto_sonda, plazo=60.0):
    """Espera hasta que no quede nada tomado ni en transacción y Postgres
    tenga exactamente las conexiones que el pool cree tener."""
    t0 = time.monotonic()
    while True:
        p = sonda(puerto_sonda)
        e = await estados_pg(pg, base)
        en_pg = sum(e.values())
        quieto = (
            p["tomadas"] == 0
            and set(e) <= {"idle"}
            and en_pg == p["libres"]
        )
        if quieto or time.monotonic() - t0 > plazo:
            return quieto, round(time.monotonic() - t0, 2), p, e
        await asyncio.sleep(0.1)


def ip_al_azar() -> str:
    return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


async def cortar(puerto: int, ruta: str, token: str):
    """Manda el pedido y cierra el socket sin leer la respuesta."""
    r, w = await asyncio.open_connection("127.0.0.1", puerto)
    w.write(
        f"GET {ruta} HTTP/1.1\r\nHost: 127.0.0.1\r\n"
        f"Authorization: Bearer {token}\r\n\r\n".encode()
    )
    await w.drain()
    w.close()
    await w.wait_closed()


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pg_admin", help="URL de Postgres con permiso para crear bases")
    ap.add_argument("--n", type=int, default=120, help="pedidos por fase de 401")
    ap.add_argument("--normales", type=int, default=80)
    ap.add_argument("--cortes", type=int, default=60)
    ap.add_argument("--concurrencia", type=int, default=40)
    ap.add_argument("--plazo", type=float, default=60.0)
    a = ap.parse_args()

    base = f"conexiones1_{uuid.uuid4().hex[:8]}"
    admin = await asyncpg.connect(a.pg_admin)
    await admin.execute(f'create database "{base}"')
    url_base = a.pg_admin.rsplit("/", 1)[0] + "/" + base
    pg = await asyncpg.connect(url_base)

    puerto, puerto_sonda = puerto_libre(), puerto_libre()
    tmp = Path(tempfile.mkdtemp(prefix="conexiones1_"))
    log = tmp / "gunicorn.log"
    secreto = secrets.token_hex(32)
    entorno = {
        k: v for k, v in os.environ.items()
        if not k.startswith(("PYTEST", "REDIS", "DATABASE", "JWT", "SECRET"))
    }
    entorno.update(
        ENVIRONMENT="production",
        PORT=str(puerto),
        DATABASE_URL=url_base,
        JWT_SECRET_KEY=secreto,
        ALLOWED_ORIGINS="http://127.0.0.1",
        FRONTEND_URL="http://127.0.0.1",
        CDI_DATA_DIR=str(tmp / "data"),
        VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
        DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
        GEMINI_API_KEY="test-key",
        PYTHONPATH=str(RAIZ), PYTHONUNBUFFERED="1", PYTHONDONTWRITEBYTECODE="1",
        CONEXIONES1_SONDA_PUERTO=str(puerto_sonda),
    )
    argv = argv_del_dockerfile(puerto)
    print("gunicorn:", " ".join(shlex.quote(x) for x in argv[1:]))
    with open(log, "w") as salida:
        proc = subprocess.Popen(argv, cwd=RAIZ, env=entorno, stdout=salida,
                                stderr=subprocess.STDOUT, start_new_session=True)

    # Una fuga vista vale aunque la medición tenga otros problemas: con la
    # fuga, el pool se llena y los pedidos siguientes contestan 500.
    fuga = invalida = False
    try:
        base_url = f"http://127.0.0.1:{puerto}"
        async with httpx.AsyncClient(base_url=base_url, timeout=60) as c:
            t0 = time.monotonic()
            while True:
                if proc.poll() is not None:
                    print("gunicorn terminó al arrancar:\n" + log.read_text()[-3000:])
                    return 2
                try:
                    if (await c.get("/health")).status_code == 200:
                        sonda(puerto_sonda)
                        break
                except (httpx.TransportError, OSError):
                    pass
                if time.monotonic() - t0 > 120:
                    print("la app no respondió /health en 120 s:\n" + log.read_text()[-3000:])
                    return 2
                await asyncio.sleep(0.2)

            usuario, clave = "medicion", secrets.token_urlsafe(16)
            await pg.execute(
                "insert into users (username, email, password, name, plan, roles, "
                "is_verified, billing_status, trial_ends_at) values "
                "($1, $2, $3, 'Medicion', 'premium', '[]'::json, true, 'active', $4)",
                usuario, "medicion@ejemplo.test",
                bcrypt.hashpw(clave.encode(), bcrypt.gensalt()).decode(),
                datetime.now(timezone.utc) + timedelta(days=3650),
            )
            r = await c.post("/auth/login", json={"username": usuario, "password": clave},
                             headers={"X-Forwarded-For": ip_al_azar()})
            if r.status_code != 200:
                print("no pude entrar con la cuenta sembrada:", r.status_code, r.text[:300])
                return 2
            token = r.json()["access_token"]
            exp = datetime.now(timezone.utc) + timedelta(hours=1)
            t_inexistente = jwt.encode({"sub": "no-existe", "jti": "x", "exp": exp}, secreto, "HS256")
            t_revocado = jwt.encode({"sub": usuario, "jti": "otro", "exp": exp}, secreto, "HS256")
            t_mal = jwt.encode({"sub": usuario, "jti": "x", "exp": exp}, "otra-clave-" + secreto, "HS256")

            def pedido(tipo):
                if tipo == "sin_token":
                    return c.get("/auth/current_user")
                if tipo == "token_mal_firmado":
                    return c.get("/auth/current_user", headers={"Authorization": f"Bearer {t_mal}"})
                if tipo == "usuario_inexistente":
                    return c.get("/auth/current_user", headers={"Authorization": f"Bearer {t_inexistente}"})
                if tipo == "token_revocado":
                    return c.get("/auth/current_user", headers={"Authorization": f"Bearer {t_revocado}"})
                if tipo == "login_clave_mala":
                    return c.post("/auth/login", json={"username": usuario, "password": "mala"},
                                  headers={"X-Forwarded-For": ip_al_azar()})
                if tipo == "normal":
                    return c.get("/auth/current_user", headers={"Authorization": f"Bearer {token}"})
                raise ValueError(tipo)

            esperado = {"normal": 200}
            tipos_401 = ["sin_token", "token_mal_firmado", "usuario_inexistente",
                         "token_revocado", "login_clave_mala"]
            mezcla = [t for t in tipos_401 for _ in range(a.n // len(tipos_401))]
            mezcla += ["normal"] * (a.n // len(tipos_401))
            random.shuffle(mezcla)
            fases = [(t, [t] * a.n) for t in tipos_401]
            fases += [("normal", ["normal"] * a.normales), ("mezcla", mezcla)]

            sem = asyncio.Semaphore(a.concurrencia)
            pid0 = sonda(puerto_sonda)["pid"]
            filas = []

            async def uno(tipo, codigos):
                async with sem:
                    r = await pedido(tipo)
                    codigos[(tipo, r.status_code)] += 1

            async def muestrear(maximo, fin):
                while not fin.is_set():
                    maximo[0] = max(maximo[0], sonda(puerto_sonda)["tomadas"])
                    await asyncio.sleep(0.05)

            async def correr(nombre, tareas):
                maximo, fin = [0], asyncio.Event()
                m = asyncio.create_task(muestrear(maximo, fin))
                await asyncio.gather(*tareas)
                fin.set()
                await m
                quieto, seg, p, e = await esperar_quieto(pg, base, puerto_sonda, a.plazo)
                filas.append((nombre, maximo[0], quieto, seg, p, e))
                return quieto

            for nombre, tipos in fases:
                codigos = collections.Counter()
                ok = await correr(nombre, [uno(t, codigos) for t in tipos])
                malos = {k: v for k, v in codigos.items() if k[1] != esperado.get(k[0], 401)}
                print(f"{nombre}: {dict(sorted(codigos.items()))}")
                if malos:
                    print(f"  respuestas inesperadas: {malos}")
                    invalida = True
                if not ok:
                    print(f"  quedaron conexiones tomadas después de {nombre}: no sigo")
                    fuga = True
                    break

            async def corte(t):
                async with sem:
                    await cortar(puerto, "/auth/current_user", t)

            if not fuga:
                cortes = [corte(token if i % 2 else t_revocado) for i in range(a.cortes)]
                fuga = not await correr("cortes_del_cliente", cortes)
                print(f"cortes_del_cliente: {a.cortes} pedidos cortados sin leer")

            pid1 = sonda(puerto_sonda)["pid"]
            if pid1 != pid0:
                print(f"el worker se recicló ({pid0} → {pid1}): la medición no vale")
                invalida = True

        print()
        print(f"{'fase':<22}{'máx tomadas':>12}  {'quieto':<7}{'seg':>6}  pool al final / pg_stat_activity")
        for nombre, maximo, quieto, seg, p, e in filas:
            print(f"{nombre:<22}{maximo:>12}  {'sí' if quieto else 'NO':<7}{seg:>6}  "
                  f"tomadas={p['tomadas']} libres={p['libres']} desborde={p['desborde']} / {e}")
        p = sonda(puerto_sonda)
        print(f"cierres de sesión: {p['cierres']}, cancelados: {p['cierres_cancelados']}")
        print(f"filas en api_logs: {await pg.fetchval('select count(*) from api_logs')}")
    finally:
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
        await pg.close()
        await admin.execute(
            "select pg_terminate_backend(pid) from pg_stat_activity where datname = $1", base)
        await admin.execute(f'drop database "{base}"')
        await admin.close()

    texto = log.read_text()
    print()
    for s in SEÑALES_DE_FUGA + SEÑALES_A_LA_VISTA:
        n = texto.count(s)
        print(f"log: {s!r}: {n}")
        if n and s in SEÑALES_DE_FUGA:
            fuga = True
    acceso = re.findall(r'"(\S+) (\S+) HTTP/1.1" \d{3}', texto)
    print(f"respuestas en el log de acceso fuera de /health: "
          f"{sum(1 for _, ruta in acceso if ruta != '/health')}")
    print(f"log completo: {log}")
    codigo = 1 if fuga else 2 if invalida else 0
    print({0: "sin conexiones tomadas", 1: "QUEDAN CONEXIONES TOMADAS",
           2: "LA MEDICIÓN NO VALE"}[codigo])
    return codigo


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
