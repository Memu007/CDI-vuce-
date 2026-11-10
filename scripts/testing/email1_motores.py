"""EMAIL-1 contra un servidor real (uvicorn), en Postgres y en SQLite, con
datos inventados.

Cada chequeo dice lo que tiene que pasar cuando el email se busca sin mirar
mayúsculas: sobre el código de antes del arreglo, los de búsqueda dan FALLA, y
esa FALLA es la reproducción. Los de registro, alta de estudio e invitación ya
daban OK antes: quedan como guardia.
1. recuperar usuario, recuperar contraseña y el login encuentran la cuenta
   aunque el email venga con otras mayúsculas o espacios;
2. recuperar responde lo mismo exista o no el email (se compara el cuerpo
   quitando la pista de desarrollo, que en producción no sale);
3. un «par» (dos cuentas viejas con el mismo email en distintas mayúsculas,
   armado con SQL porque el registro ya no lo deja crear): el que coincide
   exacto gana; si ninguno coincide exacto no se elige ninguno, no se manda
   ningún correo y el login da 401;
4. el perfil no deja tomar un email ajeno con otras mayúsculas, y una cuenta
   de un par guarda su perfil sin que se le reescriba el email;
5. registro, alta de estudio e invitación no crean un email que ya existe con
   otras mayúsculas.

Los correos no salen: sin SMTP la app los escribe en su log («To: ...»), y de
ahí se lee a quién iban.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/email1_motores.py sqlite
  python scripts/testing/email1_motores.py pg postgresql://cdi@127.0.0.1:55432/postgres
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
    sys.exit("uso: email1_motores.py sqlite | pg postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo local)")

NOMBRE = "email1_" + uuid.uuid4().hex[:8]
TMP = tempfile.mkdtemp(prefix=NOMBRE)
if MOTOR == "pg":
    import psycopg2
    URL = ADMIN.rsplit("/", 1)[0] + "/" + NOMBRE
    DB_URL = URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ARCHIVO = os.path.join(TMP, "base.db")
    DB_URL = f"sqlite+aiosqlite:///{ARCHIVO}"

FALLAS = []
CLAVE = "Clave-sintetica-1!"
DOMINIO = uuid.uuid4().hex[:8] + ".ejemplo.test"
IP = [0]


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
           "REGISTER_TEST_EMAIL_REPLACE": "true", "REGISTER_TEST_EMAILS": f"kiki@{DOMINIO}",
           "JWT_SECRET_KEY": "clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
           "GEMINI_API_KEY": "test-key", "VUCE_MODE": "fake", "TARIFAR_MODE": "fake", "AFIP_MODE": "fake",
           "DOLARAPI_BASE": "http://127.0.0.1:9/v1/dolares", "CDI_DATA_DIR": os.path.join(TMP, "data"),
           "PYTHONPATH": REPO, "PYTHONUNBUFFERED": "1"}
    for k in ("PYTEST_CURRENT_TEST", "REDIS_URL", "SMTP_SERVER", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD",
              "SMTP_FROM_EMAIL"):
        env.pop(k, None)
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


def pedir(ruta, cuerpo=None, token=None, metodo="POST"):
    """Cada pedido viene de una IP distinta (al final de X-Forwarded-For, como
    la agrega el proxy): los límites por IP no son lo que se prueba acá."""
    IP[0] += 1
    h = {"X-Forwarded-For": f"2001:db8::e:{IP[0]:x}", "Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    data = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(f"http://127.0.0.1:{PUERTO}{ruta}", method=metodo, headers=h, data=data)
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except ValueError:
            return e.code, {}


def destinatarios():
    """A quién iba cada correo, en orden, según el log del servidor."""
    with open(LOG) as f:
        return [x[4:].strip() for x in f if x.startswith("To: ")]


def correos_nuevos(antes):
    return destinatarios()[antes:]


def cuenta(email):
    """Una cuenta registrada por la API; después el email se fija por SQL, así
    se arman los pares que el registro ya no deja crear."""
    u = "em1_" + uuid.uuid4().hex[:8]
    s, b = pedir("/auth/register", {"username": u, "password": CLAVE, "email": f"{u}@{DOMINIO}", "name": "Em"})
    assert s == 200, (s, b)
    sql("update users set email = %s where username = %s", email, u)
    return u


def token(u):
    s, b = pedir("/auth/login", {"username": u, "password": CLAVE})
    assert s == 200, (s, b)
    return b["access_token"]


def email_de(u):
    return sql("select email from users where username = %s", u)[0][0]


def sin_pista(b):
    return {k: v for k, v in b.items() if not k.startswith("dev_")}


def busqueda():
    ana = cuenta(f"ana@{DOMINIO}")
    beto = cuenta(f"Beto@{DOMINIO}")
    for pedido, dueno in ((f"Ana@{DOMINIO.upper()}", ana), (f"beto@{DOMINIO}", beto),
                          (f"  ANA@{DOMINIO}  ", ana)):
        n = len(destinatarios())
        s, b = pedir("/auth/recover-username", {"email": pedido})
        a = correos_nuevos(n)
        print(f"INFO  | recuperar usuario {pedido!r}: {s} pista={b.get('dev_username_hint')!r} correos a {a}")
        chequear(s == 200 and b.get("dev_username_hint") == dueno and a == [email_de(dueno)],
                 f"recuperar usuario encuentra {pedido.strip()!r} y escribe a la dirección guardada")
        n = len(destinatarios())
        s, b = pedir("/auth/request-password-reset", {"email": pedido})
        a = correos_nuevos(n)
        guardados = [t for (t,) in sql("select token from password_reset_tokens where user_username = %s", dueno)]
        print(f"INFO  | recuperar contraseña {pedido!r}: {s} pista={'sí' if b.get('dev_token_hint') else 'no'} "
              f"correos a {a}")
        chequear(s == 200 and b.get("dev_token_hint") in guardados and a == [email_de(dueno)],
                 f"recuperar contraseña encuentra {pedido.strip()!r} y el token es de esa cuenta")
    s, b = pedir("/auth/login", {"username": f"BETO@{DOMINIO.upper()}", "password": CLAVE})
    print(f"INFO  | login con BETO@...: {s}")
    chequear(s == 200 and b["user"]["username"] == beto, "el login por email no mira mayúsculas")

    for ruta in ("/auth/recover-username", "/auth/request-password-reset"):
        _, existe = pedir(ruta, {"email": f"ANA@{DOMINIO}"})
        _, nadie = pedir(ruta, {"email": f"nadie@{DOMINIO}"})
        chequear(sin_pista(existe) == sin_pista(nadie), f"{ruta}: la respuesta no cambia exista o no el email")


def pares():
    fede, FEDE = cuenta(f"Fede@{DOMINIO}"), cuenta(f"FEDE@{DOMINIO}")
    for pedido, dueno in ((f"Fede@{DOMINIO}", fede), (f"FEDE@{DOMINIO}", FEDE)):
        n = len(destinatarios())
        s, b = pedir("/auth/recover-username", {"email": pedido})
        chequear(b.get("dev_username_hint") == dueno and correos_nuevos(n) == [pedido],
                 f"par: el exacto {pedido.split('@')[0]}@ gana en recuperar usuario")
    n = len(destinatarios())
    rutas = ("/auth/recover-username", "/auth/request-password-reset")
    respuestas = [(pedir(r, {"email": f"fede@{DOMINIO}"}), pedir(r, {"email": f"nadie@{DOMINIO}"})) for r in rutas]
    a = correos_nuevos(n)
    tokens = sql("select count(*) from password_reset_tokens where user_username in (%s, %s)", fede, FEDE)[0][0]
    print(f"INFO  | par sin exacto: {[par[0] for par in respuestas]}, correos {a}, tokens {tokens}")
    chequear(a == [] and tokens == 0 and all(par == (200, nadie[1]) and nadie[0] == 200
                                             for par, nadie in respuestas),
             "par sin exacto: no se elige ninguna, no sale correo y la respuesta es la de un email que no existe")
    codigos = [pedir("/auth/login", {"username": e, "password": CLAVE})[0]
               for e in (f"FEDE@{DOMINIO}", f"fede@{DOMINIO}")]
    print(f"INFO  | par y login (exacto, sin exacto): {codigos}")
    chequear(codigos == [200, 401], "par: el login exacto entra y el ambiguo da 401")

    s, b = pedir("/api/user/profile", {"name": "Nuevo", "email": f"fede@{DOMINIO}"}, token(fede), "PUT")
    print(f"INFO  | par guarda el perfil: {s} {b.get('detail', '')!r}, email queda {email_de(fede)!r}")
    chequear(s == 200 and email_de(fede) == f"Fede@{DOMINIO}" and email_de(FEDE) == f"FEDE@{DOMINIO}",
             "par: el perfil se guarda sin reescribir el email de ninguna de las dos")


def perfil():
    cuenta(f"Gabi@{DOMINIO}")
    otro = cuenta(f"otro@{DOMINIO}")
    t = token(otro)
    for pedido in (f"gabi@{DOMINIO}", f"GABI@{DOMINIO}"):
        s, b = pedir("/api/user/profile", {"email": pedido, "current_password": CLAVE}, t, "PUT")
        print(f"INFO  | perfil toma {pedido}: {s} {b.get('detail', '')!r}")
        chequear(s == 400 and email_de(otro) == f"otro@{DOMINIO}", f"el perfil no toma un email ajeno ({pedido})")
    s, _ = pedir("/api/user/profile", {"email": f"libre@{DOMINIO}", "current_password": CLAVE}, t, "PUT")
    chequear(s == 200 and email_de(otro) == f"libre@{DOMINIO}", "el perfil cambia a un email libre")


def altas():
    cuenta(f"Ines@{DOMINIO}")
    s, _ = pedir("/auth/register", {"username": "em1_" + uuid.uuid4().hex[:8], "password": CLAVE,
                                    "email": f"INES@{DOMINIO}", "name": "I"})
    chequear(s == 400, "el registro no crea un email que existe con otras mayúsculas")
    s, _ = pedir("/api/organizations/create", {"name": "Estudio", "username": "em1_" + uuid.uuid4().hex[:8],
                                               "password": CLAVE, "email": f"ines@{DOMINIO}"})
    chequear(s == 400, "el alta de estudio no crea un email que existe con otras mayúsculas")

    dueno = "em1_" + uuid.uuid4().hex[:8]
    s, b = pedir("/api/organizations/create", {"name": "Estudio", "username": dueno, "password": CLAVE,
                                               "email": f"Lia@{DOMINIO}"})
    assert s == 200, (s, b)
    s, b = pedir("/api/organizations/invite", {"email": f"LIA@{DOMINIO}"}, token(dueno))
    chequear(s == 400 and "miembro" in b.get("detail", ""), "no se invita a un miembro con otras mayúsculas")

    a, b_ = cuenta(f"Kiki@{DOMINIO}"), cuenta(f"kiki@{DOMINIO}")
    s, b = pedir("/auth/register", {"username": "em1_" + uuid.uuid4().hex[:8], "password": CLAVE,
                                    "email": f"KIKI@{DOMINIO}", "name": "K"})
    print(f"INFO  | registro de prueba con reemplazo sobre un par: {s} {b.get('detail', '')!r}; "
          f"quedan {email_de(a)!r} y {email_de(b_)!r}")
    chequear(s == 200 and "+archivado-" in email_de(a) and "+archivado-" in email_de(b_),
             "el registro de prueba con reemplazo archiva las dos cuentas del par")


proc = None
try:
    if MOTOR == "pg":
        admin(f'create database "{NOMBRE}"')
    proc = arrancar()
    print(f"motor: {MOTOR}, servidor en :{PUERTO}")
    busqueda()
    pares()
    perfil()
    altas()
finally:
    if proc:
        proc.terminate()
        proc.wait(30)
    if MOTOR == "pg":
        admin(f'drop database if exists "{NOMBRE}" with (force)')

print(f"\n{MOTOR}: {'FALLAS: ' + str(len(FALLAS)) if FALLAS else 'todo OK'}")
sys.exit(1 if FALLAS else 0)
