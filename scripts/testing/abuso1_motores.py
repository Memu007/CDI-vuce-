"""ABUSO-1 (S4, S5, S6 y C9 de AUDITORIA-2026-10-06) contra un servidor real
(uvicorn), en Postgres y en SQLite, con datos inventados.

Cada chequeo dice lo que tiene que pasar cuando el abuso está cerrado: sobre
el código de antes del arreglo da FALLA, y esa FALLA es la reproducción.
1. S4: rotar una IP inventada en X-Forwarded-For no esquiva el bloqueo de
   login, y mandar la IP de otro no lo bloquea a él;
2. S5: un evento demasiado grande o sin sesión no se guarda (ni en la tabla
   ni en logs/ui_events.jsonl);
3. S6: recuperar usuario tiene límite;
4. C9: registrarse tiene límite (cada alta da 14 días de prueba).

El servidor corre con --no-proxy-headers: así request.client.host es la
dirección del que conecta, como en Railway, donde el que conecta es su proxy
y no el cliente. Sin eso, uvicorn confía en 127.0.0.1 y reescribe la IP él
mismo, y la prueba no se parecería a producción.

Las IPs del cliente se simulan como las agregaría el proxy: al final de
X-Forwarded-For. Lo de la izquierda es lo que inventa el cliente.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/abuso1_motores.py sqlite
  python scripts/testing/abuso1_motores.py pg postgresql://cdi@127.0.0.1:55432/postgres
En pg crea una base propia con esa conexión y la borra al terminar. De a uno:
los dos motores escriben el mismo logs/ui_events.jsonl.
"""
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from urllib.parse import urlparse

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MOTOR = sys.argv[1] if len(sys.argv) > 1 else ""
ADMIN = sys.argv[2] if len(sys.argv) > 2 else ""
if MOTOR not in ("pg", "sqlite") or (MOTOR == "pg" and (
        not ADMIN.startswith("postgresql://") or urlparse(ADMIN).hostname not in ("127.0.0.1", "localhost"))):
    sys.exit("uso: abuso1_motores.py sqlite | pg postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo local)")

NOMBRE = "abuso1_" + uuid.uuid4().hex[:8]
TMP = tempfile.mkdtemp(prefix=NOMBRE)
if MOTOR == "pg":
    import psycopg2
    URL = ADMIN.rsplit("/", 1)[0] + "/" + NOMBRE
    DB_URL = URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ARCHIVO = os.path.join(TMP, "base.db")
    DB_URL = f"sqlite+aiosqlite:///{ARCHIVO}"

# El JSONL lo escribe la app al lado del repo: se mide cuánto crece y se deja
# como estaba.
JSONL = os.path.join(REPO, "logs", "ui_events.jsonl")
FALLAS = []
CLAVE = "Clave-sintetica-1!"
# Cuántos pedidos se mandan para ver si aparece un límite. Más que cualquier
# número razonable para una persona; si con esto no hay 429, no hay límite.
INTENTOS = 30


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def admin(consulta):
    con = psycopg2.connect(ADMIN)
    con.autocommit = True
    try:
        con.cursor().execute(consulta)
    finally:
        con.close()


def sql(consulta, *args):
    if MOTOR == "pg":
        with psycopg2.connect(URL) as con, con.cursor() as cur:
            cur.execute(consulta, args)
            return cur.fetchall() if cur.description else None
    con = sqlite3.connect(ARCHIVO)
    try:
        cur = con.execute(consulta.replace("%s", "?"), args)
        filas = cur.fetchall()
        con.commit()
        return filas
    finally:
        con.close()


def puerto_libre():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


PUERTO = puerto_libre()
LOG = os.path.join(TMP, "uvicorn.log")


def arrancar():
    env = {**os.environ, "DATABASE_URL": DB_URL, "ENVIRONMENT": "testing",
           "EMAIL_VERIFICATION_REQUIRED": "false",
           "JWT_SECRET_KEY": "clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
           "GEMINI_API_KEY": "test-key", "VUCE_MODE": "fake", "TARIFAR_MODE": "fake", "AFIP_MODE": "fake",
           "DOLARAPI_BASE": "http://127.0.0.1:9/v1/dolares", "CDI_DATA_DIR": os.path.join(TMP, "data"),
           "PYTHONPATH": REPO}
    env.pop("PYTEST_CURRENT_TEST", None)
    env.pop("REDIS_URL", None)
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "proyecto_maria.main:app", "--port", str(PUERTO),
                             "--no-proxy-headers"],
                            cwd=REPO, env=env, stdout=open(LOG, "w"), stderr=subprocess.STDOUT)
    for _ in range(1200):
        if proc.poll() is not None:
            break
        with open(LOG) as f:
            if "Application startup complete" in f.read():
                return proc
        time.sleep(0.1)
    with open(LOG) as f:
        print(f.read()[-3000:])
    proc.terminate()
    sys.exit("el servidor no arrancó")


def pedir(ruta, cuerpo=None, ip=None, inventada=None, token=None, crudo=None):
    """`ip` es la del cliente según el proxy (la última de X-Forwarded-For);
    `inventada` es lo que el cliente pone adelante."""
    h = {}
    xff = ", ".join(x for x in (inventada, ip) if x)
    if xff:
        h["X-Forwarded-For"] = xff
    if cuerpo is not None or crudo is not None:
        h["Content-Type"] = "application/json"
    if token:
        h["Authorization"] = f"Bearer {token}"
    data = crudo if crudo is not None else (json.dumps(cuerpo).encode() if cuerpo is not None else None)
    req = urllib.request.Request(f"http://127.0.0.1:{PUERTO}{ruta}", method="POST", headers=h, data=data)
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}


def registrar(u, ip):
    return pedir("/auth/register", {"username": u, "password": CLAVE, "email": f"{u}@example.com", "name": "Abuso"},
                 ip=ip)


def tam_jsonl():
    return os.path.getsize(JSONL) if os.path.exists(JSONL) else 0


def s4_login():
    victima = "ab1_victima"
    s, b = registrar(victima, "203.0.113.10")
    assert s == 200, (s, b)

    # a. el atacante (198.51.100.20) rota lo que inventa a la izquierda
    codigos = [pedir("/auth/login", {"username": victima, "password": "otra-cosa-1!"},
                     ip="198.51.100.20", inventada=f"10.66.0.{n}")[0] for n in range(1, INTENTOS + 1)]
    print(f"INFO  | S4a: {INTENTOS} logins fallidos rotando X-Forwarded-For: {sorted(set(codigos))}")
    chequear(429 in codigos, "S4a: rotar la IP inventada no esquiva el bloqueo de login")

    # b. otro atacante (198.51.100.30) inventa la IP de la víctima
    for _ in range(8):
        pedir("/auth/login", {"username": victima, "password": "otra-cosa-1!"},
              ip="198.51.100.30", inventada="203.0.113.10")
    s, b = pedir("/auth/login", {"username": victima, "password": CLAVE}, ip="203.0.113.10")
    print(f"INFO  | S4b: login correcto de la víctima después: {s} {b.get('detail', '')!r}")
    chequear(s == 200, "S4b: inventar la IP de otro no lo bloquea")


def s5_eventos():
    s, b = registrar("ab1_eventos", "203.0.113.11")
    assert s == 200, (s, b)
    s, b = pedir("/auth/login", {"username": "ab1_eventos", "password": CLAVE}, ip="203.0.113.11")
    assert s == 200, (s, b)
    token = b["access_token"]

    def grande(marca):
        return json.dumps({"action": "ab1_grande", "screen": "x", "relleno": marca + "A" * (5 * 1024 * 1024)}).encode()

    def filas(marca):
        return sql("select owner_username, length(props) from telemetry_events where props like %s",
                   f"%{marca}%")

    for ruta in ("/api/ui/event", "/api/session/state"):
        marca = uuid.uuid4().hex
        antes = tam_jsonl()
        s, _ = pedir(ruta, crudo=grande(marca), ip="203.0.113.12")
        crecio = tam_jsonl() - antes
        f = filas(marca)
        print(f"INFO  | S5 {ruta}: 5 MB sin sesión → {s}, JSONL +{crecio} bytes, filas {f}")
        chequear(not f and crecio < 64 * 1024, f"S5 {ruta}: un evento de 5 MB sin sesión no se guarda")

        marca = uuid.uuid4().hex
        antes = tam_jsonl()
        s, _ = pedir(ruta, crudo=grande(marca), ip="203.0.113.11", token=token)
        crecio = tam_jsonl() - antes
        f = filas(marca)
        print(f"INFO  | S5 {ruta}: 5 MB con sesión → {s}, JSONL +{crecio} bytes, filas {f}")
        chequear(not f and crecio < 64 * 1024, f"S5 {ruta}: un evento de 5 MB con sesión no se guarda")

        marca = uuid.uuid4().hex
        s, _ = pedir(ruta, {"action": "ab1_inventada", "screen": "x", "m": marca}, ip="203.0.113.12")
        f = filas(marca)
        print(f"INFO  | S5 {ruta}: evento chico sin sesión con una acción inventada → {s}, filas {f}")
        chequear(not f, f"S5 {ruta}: un evento sin sesión con una acción cualquiera no se guarda")

        marca = uuid.uuid4().hex
        s, _ = pedir(ruta, {"action": "ab1_chico", "screen": "x", "m": marca}, ip="203.0.113.11", token=token)
        f = filas(marca)
        chequear(f and f[0][0] == "ab1_eventos", f"S5 {ruta}: un evento chico con sesión se guarda a su nombre ({f})")


def s6_recuperar():
    s, b = registrar("ab1_recupera", "203.0.113.13")
    assert s == 200, (s, b)
    codigos = [pedir("/auth/recover-username", {"email": "ab1_recupera@example.com"}, ip="198.51.100.40")[0]
               for _ in range(INTENTOS)]
    print(f"INFO  | S6: {INTENTOS} pedidos de recuperar usuario desde una IP: {sorted(set(codigos))}")
    chequear(429 in codigos, "S6: recuperar usuario tiene límite por IP")

    s, b = registrar("ab1_recupera", "203.0.113.14")
    print(f"INFO  | S6: registrar un usuario que existe → {s} {b.get('detail')!r}")
    s, b = pedir("/auth/register", {"username": "ab1_otro_nombre", "password": CLAVE,
                                    "email": "ab1_recupera@example.com"}, ip="203.0.113.14")
    print(f"INFO  | S6: registrar un email que existe → {s} {b.get('detail')!r}")


def c9_registro():
    codigos, nuevos = [], []
    for n in range(INTENTOS):
        u = f"ab1_prueba_{n}"
        s, _ = registrar(u, "198.51.100.50")
        codigos.append(s)
        if s == 200:
            nuevos.append(u)
    print(f"INFO  | C9: {INTENTOS} registros desde una IP: {sorted(set(codigos))}, altas: {len(nuevos)}")
    if nuevos:
        f = sql("select billing_status, count(*) from users where username like %s group by billing_status",
                "ab1_prueba_%")
        print(f"INFO  | C9: estado de las altas: {f}")
    chequear(429 in codigos, "C9: registrarse tiene límite por IP")


proc = None
jsonl_original = tam_jsonl()
try:
    if MOTOR == "pg":
        admin(f'create database "{NOMBRE}"')
    proc = arrancar()
    print(f"motor: {MOTOR}, servidor en :{PUERTO}")
    s4_login()
    s5_eventos()
    s6_recuperar()
    c9_registro()
finally:
    if proc:
        proc.terminate()
        proc.wait(30)
    if MOTOR == "pg":
        admin(f'drop database if exists "{NOMBRE}" with (force)')
    if os.path.exists(JSONL) and tam_jsonl() > jsonl_original:
        with open(JSONL, "r+b") as fh:
            fh.truncate(jsonl_original)

print(f"\n{MOTOR}: {'FALLAS: ' + str(len(FALLAS)) if FALLAS else 'todo OK'}")
sys.exit(1 if FALLAS else 0)
