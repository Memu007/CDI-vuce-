"""ABUSO-1 (S4, S5, S6 y C9 de AUDITORIA-2026-10-06) contra un servidor real
(uvicorn), en Postgres y en SQLite, con datos inventados.

Cada chequeo dice lo que tiene que pasar cuando el abuso está cerrado: sobre
el código de antes del arreglo da FALLA, y esa FALLA es la reproducción.
1. S4: rotar una IP inventada en X-Forwarded-For no esquiva el bloqueo de
   login, y mandar la IP de otro no lo bloquea a él;
2. S5: un evento demasiado grande da 413 (según el log del servidor: el
   cliente puede ver el corte de la conexión) y no se guarda ni en la tabla ni
   en logs/ui_events.jsonl; uno sin sesión tampoco se guarda;
3. S6: recuperar usuario tiene límite;
4. C9: registrarse tiene límite (cada alta da 14 días de prueba);
5. la tabla `limites_auth` existe al arrancar y cuenta sin perder pedidos
   simultáneos (INSERT ... ON CONFLICT atómico);
6. recuperar usuario corta en silencio al cuarto pedido de la hora para un
   mismo email, venga de la IP que venga;
7. los eventos tienen 120 por minuto por ruta, y sin sesión se guardan los de
   la lista;
8. una IP de 100 a 332 caracteres (la clave de la tabla tiene 120) no rompe
   ninguna de las cuatro rutas con contador y sigue contando;
9. 120 logins malos, y después 120 buenos, a la vez no dan 500 ni agotan el pool: /health contesta
   mientras tanto (el login cuenta con la conexión del pedido, no con otra).
   Los 500 se exigen sólo en PG: en SQLite se informan;
10. un surrogate suelto o un NUL en el JSON de login, reset, recuperar o el
   token de restablecer no da 500, tampoco en el 422.

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
import threading
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
    except (urllib.error.URLError, ConnectionError) as e:
        # Si el servidor contesta antes de leer todo el cuerpo y cierra, el
        # cliente puede ver el corte en vez de la respuesta: lo que contestó
        # sale de su log (codigo_en_el_servidor).
        return 0, {"corte": str(e)}


def health():
    t = time.monotonic()
    try:
        s = urllib.request.urlopen(f"http://127.0.0.1:{PUERTO}/health", timeout=120).status
    except (urllib.error.URLError, ConnectionError) as e:
        s = str(e)
    return s, time.monotonic() - t


def codigo_en_el_servidor(ruta):
    """El código de la última respuesta del servidor a `ruta`, según su log."""
    marca = f'"POST {ruta} HTTP/1.1" '
    with open(LOG) as f:
        lineas = [x for x in f if marca in x]
    return int(lineas[-1].split(marca, 1)[1].split()[0]) if lineas else None


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
        srv = codigo_en_el_servidor(ruta)
        print(f"INFO  | S5 {ruta}: 5 MB sin sesión → cliente {s}, servidor {srv}, JSONL +{crecio} bytes, filas {f}")
        chequear(srv == 413 and not f and crecio < 64 * 1024,
                 f"S5 {ruta}: un evento de 5 MB sin sesión da 413 y no se guarda")

        marca = uuid.uuid4().hex
        antes = tam_jsonl()
        s, _ = pedir(ruta, crudo=grande(marca), ip="203.0.113.11", token=token)
        crecio = tam_jsonl() - antes
        f = filas(marca)
        srv = codigo_en_el_servidor(ruta)
        print(f"INFO  | S5 {ruta}: 5 MB con sesión → cliente {s}, servidor {srv}, JSONL +{crecio} bytes, filas {f}")
        chequear(srv == 413 and not f and crecio < 64 * 1024,
                 f"S5 {ruta}: un evento de 5 MB con sesión da 413 y no se guarda")

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


def tabla():
    if MOTOR == "pg":
        f = sql("select column_name from information_schema.columns where table_name = 'limites_auth'")
    else:
        f = sql("select name from pragma_table_info('limites_auth')")
    columnas = sorted(c for (c,) in f)
    print(f"INFO  | tabla limites_auth al arrancar: {columnas}")
    chequear(columnas == ["bloqueado_hasta", "clave", "cuenta", "vence"], "la tabla limites_auth existe al arrancar")


def simultaneos(n, pedido):
    """Larga `n` pedidos a la vez (arrancan juntos con una barrera) y devuelve
    los códigos."""
    barrera, codigos = threading.Barrier(n), [None] * n

    def uno(i):
        barrera.wait()
        codigos[i] = pedido(i)[0]
    hilos = [threading.Thread(target=uno, args=(i,)) for i in range(n)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(120)
    return codigos


def cuenta(clave):
    f = sql("select cuenta from limites_auth where clave = %s", clave)
    return f[0][0] if f else None


def concurrencia():
    # Registro: cada pedido suma uno, pase o no; los que ven 1..5 pasan.
    ip = "198.51.100.70"
    codigos = simultaneos(20, lambda i: registrar(f"ab1_sim_{i}", ip))
    c = cuenta(f"registro:h:{ip}")
    print(f"INFO  | concurrencia: 20 registros simultáneos → {sorted(codigos)}, cuenta {c}")
    chequear(c == 20 and codigos.count(200) == 5 and codigos.count(429) == 15,
             "concurrencia: 20 registros simultáneos cuentan 20 y pasan 5")

    # Recuperar contraseña: los que pasan el chequeo a la vez suman y se cortan
    # si la cuenta pasa de cinco; los que llegan con el bloqueo no suman.
    ip = "198.51.100.71"
    codigos = simultaneos(20, lambda i: pedir("/auth/request-password-reset",
                                              {"email": f"nadie{i}@example.com"}, ip=ip))
    c = cuenta(f"reset:{ip}")
    print(f"INFO  | concurrencia: 20 recuperar contraseña simultáneos → {sorted(codigos)}, cuenta {c}")
    chequear(codigos.count(200) == 5 and codigos.count(429) == 15 and c is not None and 5 <= c <= 20,
             "concurrencia: 20 recuperar contraseña simultáneos pasan 5")


def s6_por_email():
    s, b = registrar("ab1_mail", "203.0.113.15")
    assert s == 200, (s, b)
    respuestas = [pedir("/auth/recover-username", {"email": "ab1_mail@example.com"}, ip=f"203.0.113.{20 + n}")
                  for n in range(4)]
    print(f"INFO  | S6: 4 recuperar usuario para un email desde 4 IPs → "
          f"{[(s, sorted(b)) for s, b in respuestas]}")
    # Sin SMTP, el modo dev devuelve el usuario cuando busca y no puede mandar:
    # el cuarto no busca, así que no lo trae.
    chequear([s for s, _ in respuestas] == [200] * 4
             and ["dev_username_hint" in b for _, b in respuestas] == [True, True, True, False]
             and len({b["message"] for _, b in respuestas}) == 1,
             "S6: el cuarto pedido de la hora para un email contesta lo mismo y no busca ni manda")


def eventos():
    s, b = registrar("ab1_lote", "203.0.113.16")
    assert s == 200, (s, b)
    token = pedir("/auth/login", {"username": "ab1_lote", "password": CLAVE}, ip="203.0.113.16")[1]["access_token"]
    ip = "203.0.113.17"
    codigos = [pedir("/api/ui/event", {"action": "ab1_lote"}, ip=ip, token=token)[0] for _ in range(121)]
    otra = pedir("/api/session/state", {"action": "ab1_lote"}, ip=ip, token=token)[0]
    print(f"INFO  | eventos: 121 a /api/ui/event → 200×{codigos.count(200)}, último {codigos[-1]}; la otra ruta {otra}")
    chequear(codigos.count(200) == 120 and codigos[-1] == 429 and otra == 200,
             "eventos: 120 por minuto por ruta")
    for ruta in ("/api/ui/event", "/api/session/state"):
        marca = uuid.uuid4().hex
        s, b = pedir(ruta, {"action": "hero_cta_clicked", "m": marca}, ip="203.0.113.18")
        f = sql("select owner_username, action from telemetry_events where props like %s", f"%{marca}%")
        chequear(s == 200 and b.get("ok") is True and f == [(None, "hero_cta_clicked")],
                 f"eventos {ruta}: uno de la lista sin sesión se guarda ({f})")


def ip_larga():
    # La última entrada de X-Forwarded-For la escribe el cliente si no hay
    # proxy delante, o si el de Railway no agrega la suya.
    # Con su prefijo, la primera clave queda en 120 o menos, dos entre 121 y
    # 300 y la última por encima.
    for largo in (100, 200, 287, 332):
        ip = ("x" * largo + uuid.uuid4().hex)[-largo:]
        rutas = [("/auth/login", {"username": "nadie", "password": "x"}),
                 ("/auth/request-password-reset", {"email": "nadie@example.com"}),
                 ("/auth/recover-username", {"email": "nadie@example.com"}),
                 ("/auth/register", {"username": f"ab1_larga{largo}", "password": CLAVE,
                                     "email": f"ab1_larga{largo}@example.com", "name": "Ab"})]
        codigos = [pedir(r, c, ip=ip)[0] for r, c in rutas]
        login = [pedir("/auth/login", {"username": "nadie", "password": "x"}, ip=ip)[0] for _ in range(5)]
        print(f"INFO  | IP de {largo} caracteres: login, reset, recuperar, registro → {codigos}; 5 logins más → {login}")
        chequear(codigos == [401, 200, 200, 200], f"una IP de {largo} caracteres no rompe las rutas con contador")
        chequear(login == [401] * 4 + [429], f"una IP de {largo} caracteres también se bloquea al quinto fallo")


def login_concurrente():
    """Logins malos (suman fallo) y buenos (limpian el contador) a la vez: los
    dos caminos usan la conexión del pedido y no agotan el pool."""
    for usuario, clave, que in (("ab1_pool", "otra-cosa-1!", "malos"), ("ab1_pool_ok", CLAVE, "buenos")):
        s, b = registrar(usuario, "203.0.113.30")
        assert s == 200, (s, b)
        salud, en_carga = [], threading.Event()
        def medir():
            en_carga.wait(120)
            salud.append(health())
        hilo = threading.Thread(target=medir)
        hilo.start()
        def uno(i):
            if i == 60:
                en_carga.set()
            return pedir("/auth/login", {"username": usuario, "password": clave}, ip=f"10.77.{i // 250}.{i % 250}")
        codigos = simultaneos(120, uno)
        en_carga.set()
        hilo.join(120)
        print(f"INFO  | 120 logins {que} a la vez → {sorted(set(codigos))} (500: {codigos.count(500)}); /health {salud}")
        # SQLite tiene un solo escritor y también da «database is locked» con el código
        # anterior: ahí la cuenta se muestra y no falla; la condición es la de PG.
        if MOTOR == "pg":
            chequear(not set(codigos) & {500, 0, None}, f"120 logins {que} a la vez no dan 500")
        chequear(salud and salud[0][0] == 200 and salud[0][1] < 15,
                 f"/health contesta en menos de 15 s durante los logins {que}")


def surrogate():
    for ruta, crudo, pasa in (("/auth/recover-username", b'{"email": "a\\ud800@example.com"}', 200),
                              ("/auth/request-password-reset", b'{"email": "a\\udfff\\u0000@example.com"}', 200),
                              ("/auth/login", b'{"username": "a\\ud800\\u0000", "password": "x"}', 401),
                              ("/auth/reset-password", b'{"token": "a\\ud800\\u0000", "new_password": "Abcdef12!"}', 400),
                              ("/auth/login", b'{"password": "x\\ud800"}', 422)):
        s, _ = pedir(ruta, crudo=crudo, ip=f"203.0.113.{40 + pasa % 7}")
        chequear(s == pasa, f"surrogate o NUL en {ruta}: {s}, esperado {pasa}")


proc = None
jsonl_original = tam_jsonl()
try:
    if MOTOR == "pg":
        admin(f'create database "{NOMBRE}"')
    proc = arrancar()
    print(f"motor: {MOTOR}, servidor en :{PUERTO}")
    tabla()
    concurrencia()
    s6_por_email()
    eventos()
    ip_larga()
    login_concurrente()
    surrogate()
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
