"""SESION-1 (S3) contra un servidor real (uvicorn), en Postgres y en SQLite.

tests/test_sesion1.py cubre lo mismo con TestClient sobre SQLite; acá se
levanta la app de verdad, con su base propia y descartable, y se recorre:
1. cambiar la contraseña cierra las otras sesiones y conserva la propia;
2. resetearla cierra todas, también la vigente;
3. cerrar sesión (/auth/logout y /logout, con Bearer o con cookie) revoca ese
   token, y un token ya revocado no saca a la sesión vigente;
4. cambiar el email sin la contraseña, con una equivocada o vaciándolo falla
   y no cambia nada; con la correcta cambia; guardar el mismo email no la pide;
5. ninguna sesión revocada vuelve a entrar.
Antes de cambiar y de resetear se pone active_jti en NULL (como un usuario de
antes de la columna), que es el caso en el que revocar resucitaba sesiones.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/sesion1_motores.py sqlite
  python scripts/testing/sesion1_motores.py pg postgresql://cdi@127.0.0.1:55432/postgres
En pg crea una base propia con esa conexión y la borra al terminar.
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
    sys.exit("uso: sesion1_motores.py sqlite | pg postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo local)")

NOMBRE = "sesion1_" + uuid.uuid4().hex[:8]
TMP = tempfile.mkdtemp(prefix=NOMBRE)
if MOTOR == "pg":
    import psycopg2
    URL = ADMIN.rsplit("/", 1)[0] + "/" + NOMBRE
    DB_URL = URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ARCHIVO = os.path.join(TMP, "base.db")
    DB_URL = f"sqlite+aiosqlite:///{ARCHIVO}"

FALLAS = []
P1, P2, P3 = "Clave-sintetica-1!", "Clave-sintetica-2!", "Clave-sintetica-3!"
U, MAIL = "ses1_motor", "ses1-motor@example.com"


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
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "proyecto_maria.main:app", "--port", str(PUERTO)],
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


PEDIDOS = iter(range(1, 1 << 16))


def pedir(ruta, cuerpo=None, token=None, cookie=None, metodo=None):
    # El login admite 5 por minuto por IP, y la IP sale de X-Forwarded-For:
    # cada pedido trae una propia para que el límite no corte el recorrido.
    n = next(PEDIDOS)
    h = {"X-Forwarded-For": f"10.99.{n >> 8}.{n & 255}"}
    if cuerpo is not None:
        h["Content-Type"] = "application/json"
    if token:
        h["Authorization"] = f"Bearer {token}"
    if cookie:
        h["Cookie"] = f'access_token="Bearer {cookie}"'
    req = urllib.request.Request(f"http://127.0.0.1:{PUERTO}{ruta}", method=metodo, headers=h,
                                 data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
    try:
        r = urllib.request.urlopen(req, timeout=30)
        return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}


def login(clave):
    s, b = pedir("/auth/login", {"username": U, "password": clave})
    assert s == 200, (s, b)
    return b["access_token"]


def entra(t):
    return pedir("/api/user/profile", token=t)[0]


def active_jti():
    return sql("select active_jti from users where username=%s", U)[0][0]


def fila():
    return sql("select email, name from users where username=%s", U)[0]


def recorrer():
    s, b = pedir("/auth/register", {"username": U, "password": P1, "email": MAIL, "name": "Motor"})
    assert s == 200, (s, b)
    revocadas = []

    # 1. cambiar la contraseña
    t1, t2 = login(P1), login(P1)
    sql("update users set active_jti=NULL where username=%s", U)
    s, _ = pedir("/api/user/change-password", {"current_password": P1, "new_password": P2}, token=t2)
    chequear(s == 200, f"cambiar la clave da 200 ({s})")
    chequear(entra(t1) == 401, "cambiar la clave cierra la otra sesión")
    chequear(entra(t2) == 200, "cambiar la clave conserva la sesión de quien la cambió")
    chequear(active_jti() is not None, "después de cambiar la clave active_jti no queda NULL")
    revocadas.append(t1)

    # 2. resetear la contraseña
    t3 = login(P2)
    chequear((entra(t3), entra(t2)) == (200, 401), "el login nuevo entra y revoca la anterior")
    revocadas.append(t2)
    sql("update users set active_jti=NULL where username=%s", U)
    s, _ = pedir("/auth/request-password-reset", {"email": MAIL})
    tok = sql("select token from password_reset_tokens where user_username=%s and is_used=%s", U, False)[0][0]
    s2, _ = pedir("/auth/reset-password", {"token": tok, "new_password": P3})
    chequear((s, s2) == (200, 200), f"pedir y aplicar el reset dan 200 ({s}, {s2})")
    chequear(entra(t3) == 401, "resetear la clave cierra la sesión vigente")
    chequear(all(entra(t) == 401 for t in revocadas), "resetear la clave no resucita las revocadas")
    chequear(active_jti() is not None, "después del reset active_jti no queda NULL")
    revocadas.append(t3)

    # 3. cerrar sesión
    for ruta in ("/auth/logout", "/logout"):
        t = login(P3)
        chequear(entra(t) == 200, f"{ruta}: la sesión nueva entra")
        s, _ = pedir(ruta, {}, token=t)
        chequear(s == 200 and entra(t) == 401, f"{ruta} con Bearer revoca ese token ({s})")
        revocadas.append(t)
        t = login(P3)
        s, _ = pedir(ruta, {}, cookie=t)
        chequear(s == 200 and entra(t) == 401, f"{ruta} con cookie revoca ese token ({s})")
        revocadas.append(t)
        vigente = login(P3)
        s, _ = pedir(ruta, {}, token=revocadas[0])
        chequear(s == 200 and entra(vigente) == 200, f"{ruta} con un token revocado no saca la vigente ({s})")
        s, _ = pedir(ruta, {}, token="no-es-un-jwt")
        chequear(s == 200 and entra(vigente) == 200, f"{ruta} con basura da 200 y no toca nada ({s})")

    # 4. cambiar el email
    t = login(P3)
    antes = fila()
    for cuerpo, detalle, que in (
        ({"name": "Otro", "email": "atacante@example.com"},
         "Para cambiar el email ingresá tu contraseña actual", "sin la contraseña"),
        ({"name": "Otro", "email": "atacante@example.com", "current_password": "otra-cosa-1!"},
         "La contraseña actual es incorrecta", "con una contraseña equivocada"),
        ({"email": ""}, "Para cambiar el email ingresá tu contraseña actual", "vaciándolo sin la contraseña"),
    ):
        s, b = pedir("/api/user/profile", cuerpo, token=t, metodo="PUT")
        chequear(s == 400 and b.get("detail") == detalle and fila() == antes,
                 f"cambiar el email {que} da 400 y no cambia nada ({s}, {b.get('detail')!r})")
    s, b = pedir("/api/user/profile", {"name": "Motor", "email": f"  {MAIL.upper()} "}, token=t, metodo="PUT")
    chequear(s == 200 and fila() == antes, f"guardar el mismo email no pide la contraseña ({s})")
    s, b = pedir("/api/user/profile", {"email": "Nuevo-Motor@Example.com", "current_password": P3},
                 token=t, metodo="PUT")
    chequear(s == 200 and fila()[0] == "nuevo-motor@example.com",
             f"cambiar el email con la contraseña lo cambia ({s})")
    chequear(entra(t) == 200, "cambiar el email no cierra la propia sesión")

    # 5. ninguna revocada vuelve
    chequear([entra(x) for x in revocadas] == [401] * len(revocadas),
             f"ninguna de las {len(revocadas)} sesiones revocadas vuelve a entrar")


proc = None
try:
    if MOTOR == "pg":
        admin(f'create database "{NOMBRE}"')
    proc = arrancar()
    print(f"motor: {MOTOR}, servidor en :{PUERTO}")
    recorrer()
finally:
    if proc:
        proc.terminate()
        proc.wait(30)
    if MOTOR == "pg":
        admin(f'drop database if exists "{NOMBRE}" with (force)')

print(f"\n{MOTOR}: {'FALLAS: ' + str(len(FALLAS)) if FALLAS else 'todo OK'}")
sys.exit(1 if FALLAS else 0)
