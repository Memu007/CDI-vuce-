"""SESION-1 (S3) contra un servidor real (uvicorn), en Postgres y en SQLite.

tests/test_sesion1.py cubre lo mismo con TestClient sobre SQLite; acá se
levanta la app de verdad, con su base propia y descartable, y se recorre:
1. cambiar la contraseña cierra todas las sesiones y devuelve un token nuevo;
2. resetearla cierra todas, también la vigente;
3. cerrar sesión (/auth/logout y /logout, con Bearer o con cookie) revoca ese
   token, y un token ya revocado no saca a la sesión vigente;
4. cambiar el email sin la contraseña, con una equivocada o vaciándolo falla
   y no cambia nada; con la correcta cambia; guardar el mismo email no la pide;
5. ninguna sesión revocada vuelve a entrar;
6. (sólo pg) un cambio de clave que entra entre que el login validó la clave
   y escribe el jti gana: el login da 401 y no pisa el jti. La fila queda
   bloqueada hasta ver al login esperándola en pg_stat_activity. En SQLite lo
   cubre tests/test_sesion1.py.
7. (sólo pg) por cada ruta que cuenta intentos, y el perfil, más pedidos a la vez
   que conexiones tiene el pool: ninguno da 500 y otro usuario entra en menos de 2 s.
Antes de cambiar y de resetear se pone active_jti en NULL (como un usuario de
antes de la columna), que es el caso en el que revocar resucitaba sesiones.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/sesion1_motores.py sqlite
  python scripts/testing/sesion1_motores.py pg postgresql://cdi@127.0.0.1:55432/postgres
En pg crea una base propia con esa conexión y la borra al terminar.
"""
import asyncio
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from urllib.parse import urlparse

import httpx

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


def login(clave, usuario=U):
    s, b = pedir("/auth/login", {"username": usuario, "password": clave})
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
    s, b = pedir("/api/user/change-password", {"current_password": P1, "new_password": P2}, token=t2)
    chequear(s == 200, f"cambiar la clave da 200 ({s})")
    chequear(entra(t1) == 401, "cambiar la clave cierra la otra sesión")
    chequear(entra(t2) == 401, "cambiar la clave cierra también el token con el que se cambió")
    chequear(entra(b.get("access_token")) == 200, "quien cambió la clave sigue con el token nuevo")
    chequear(active_jti() is not None, "después de cambiar la clave active_jti no queda NULL")
    revocadas += [t1, t2, b.get("access_token")]

    # 2. resetear la contraseña
    t3 = login(P2)
    chequear(entra(t3) == 200, "el login nuevo entra")
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

    if MOTOR == "pg":
        carrera_del_login()
        contar_no_agota_el_pool()
    else:
        print("NO CORRIDO | 6. la carrera del login: en SQLite la cubre tests/test_sesion1.py")
        print("NO CORRIDO | 7. el pool: SQLite no tiene pool de conexiones que agotar")


def carrera_del_login():
    con = psycopg2.connect(URL)
    respuesta = {}
    try:
        cur = con.cursor()
        cur.execute("select 1 from users where username=%s for update", (U,))
        hilo = threading.Thread(target=lambda: respuesta.update(r=pedir(
            "/auth/login", {"username": U, "password": P3})))
        hilo.start()
        esperando, limite = False, time.monotonic() + 60
        while not esperando and hilo.is_alive() and time.monotonic() < limite:
            esperando = bool(sql("select 1 from pg_stat_activity where datname=%s and wait_event_type='Lock'"
                                 " and query ilike 'update users%%'", NOMBRE))
            time.sleep(0.05)
        chequear(esperando, "6. el login validó la clave y espera la fila para escribir el jti")
        cur.execute("update users set password='hash-de-otra-clave', active_jti='jti-del-cambio'"
                    " where username=%s", (U,))
        con.commit()
        hilo.join(60)
    finally:
        con.close()
    s, b = respuesta.get("r", (None, {}))
    chequear(s == 401 and "access_token" not in b,
             f"6. el login con la clave vieja no abre sesión después del cambio ({s})")
    chequear(active_jti() == "jti-del-cambio", f"6. el login no pisó el jti del cambio ({active_jti()!r})")


# El pool de la app es de 20 + 30 conexiones.
A_LA_VEZ = 80


async def _a_la_vez(metodo, ruta, cuerpo, token, otro):
    """A_LA_VEZ pedidos y el login de otro usuario salen juntos, en un solo
    cliente: el estado de cada uno y lo que tardó el del otro."""
    async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{PUERTO}", timeout=90,
                                 limits=httpx.Limits(max_connections=A_LA_VEZ + 1)) as c:
        async def uno(n):
            h = {"X-Forwarded-For": f"10.98.{n >> 8}.{n & 255}"}
            if token:
                h["Authorization"] = f"Bearer {token}"
            try:
                return (await c.request(metodo, ruta, json=cuerpo, headers=h)).status_code
            except httpx.HTTPError as e:
                return type(e).__name__

        async def el_otro():
            inicio = time.monotonic()
            try:
                r = await c.post("/auth/login", json={"username": otro, "password": P1},
                                 headers={"X-Forwarded-For": "10.97.0.1"})
                return r.status_code, time.monotonic() - inicio
            except httpx.HTTPError as e:
                return type(e).__name__, time.monotonic() - inicio
        *estados, (s_otro, demora) = await asyncio.gather(*(uno(n) for n in range(A_LA_VEZ)), el_otro())
    return estados, s_otro, demora


def contar_no_agota_el_pool():
    # La carrera del login dejó a U con una clave que nadie sabe.
    atacado, otro = "ses1_motor_pool", "ses1_motor_otro"
    for u in (atacado, otro):
        s, b = pedir("/auth/register", {"username": u, "password": P1, "email": f"{u}@example.com", "name": u})
        assert s == 200, (s, b)
    t = login(P1, atacado)
    for metodo, ruta, cuerpo, con_token in (
        ("GET", "/api/user/profile", None, True),
        ("PUT", "/api/user/profile", {"email": "pool@example.com", "current_password": "mala-1!"}, True),
        ("POST", "/api/user/change-password", {"current_password": "mala-1!", "new_password": P1}, True),
        # Un usuario que no existe cuenta sin pasar por bcrypt, que es CPU y no pool.
        ("POST", "/auth/login", {"username": "ses1_motor_nadie", "password": "mala-1!"}, False),
        ("POST", "/auth/request-password-reset", {"email": "nadie@example.com"}, False),
    ):
        sql("delete from limites_auth")
        estados, s_otro, demora = asyncio.run(_a_la_vez(metodo, ruta, cuerpo, t if con_token else None, otro))
        cuenta = {x: estados.count(x) for x in set(estados)}
        chequear(500 not in cuenta and all(isinstance(x, int) for x in cuenta),
                 f"7. {A_LA_VEZ} {metodo} {ruta} a la vez: ningún 500 ({cuenta})")
        chequear(s_otro == 200 and demora < 2,
                 f"7. con {metodo} {ruta} a la vez otro usuario entra en menos de 2 s ({s_otro}, {demora:.1f} s)")

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
