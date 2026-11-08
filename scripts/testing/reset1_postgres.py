"""RESET-1 contra un Postgres de verdad: el link de reset se consume atómico.

Una conexión traba la fila del usuario; dos pedidos quedan en cola detrás y
se sueltan juntos. Comprueba que:
1. el mismo link usado dos veces a la vez cambia la clave una sola vez: un
   200 y un 400;
2. un cambio de email que llega primero mata el link que se usa a la vez:
   el perfil da 200, el reset 400 y la clave no cambia;
3. un link pedido a la vez que un cambio de email que llega primero no sale,
   o no sirve: sin trabar la cuenta, el pedido lee el email viejo y guarda el
   link después del cambio;
4. el tope por cuenta del pedido se cuenta antes de trabar la cuenta: un
   cambio de email que entra justo después de contar no deja salir el link.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/reset1_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
"""
import asyncio
import concurrent.futures
import os
import sys
import time
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_u = urlparse(URL)
if not URL.startswith("postgresql://") or _u.hostname not in ("127.0.0.1", "localhost"):
    sys.exit("uso: reset1_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

BASE = f"reset1_{uuid.uuid4().hex[:8]}"
URL_BASE = _u._replace(path=f"/{BASE}").geturl()
os.environ.update(
    DATABASE_URL=URL_BASE, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import psycopg2  # noqa: E402

FALLAS = []
CLAVE, CLAVE2, CLAVE3 = "Clave-sintetica-1!", "Clave-sintetica-2!", "Clave-sintetica-3!"


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def admin(consulta):
    con = psycopg2.connect(URL)
    con.autocommit = True
    try:
        with con.cursor() as cur:
            cur.execute(consulta)
    finally:
        con.close()


def sql(consulta, *args):
    with psycopg2.connect(URL_BASE) as con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall()


def esperan_un_bloqueo(n):
    """Hasta que n conexiones de la base esperan un bloqueo (60 s como mucho)."""
    hasta = time.monotonic() + 60
    while time.monotonic() < hasta:
        if sql("select count(*) from pg_stat_activity where datname=%s and wait_event_type='Lock'",
               BASE)[0][0] >= n:
            return True
        time.sleep(0.01)
    return False


def a_la_vez(username, primero, segundo):
    """Traba la fila del usuario, deja `primero` y después `segundo` en cola
    detrás de la traba y los suelta juntos."""
    traba = psycopg2.connect(URL_BASE)
    try:
        with traba.cursor() as cur:
            cur.execute("select 1 from users where username=%s for update", (username,))
        with concurrent.futures.ThreadPoolExecutor(2) as ex:
            r1 = ex.submit(primero)
            en_cola = esperan_un_bloqueo(1)
            r2 = ex.submit(segundo)
            en_cola = en_cola and esperan_un_bloqueo(2)
            traba.rollback()
            return en_cola, r1.result(timeout=120), r2.result(timeout=120)
    finally:
        traba.close()


try:
    admin(f'create database "{BASE}"')
    from fastapi.testclient import TestClient  # noqa: E402
    import proyecto_maria.main as main_mod  # noqa: E402
    from proyecto_maria.core.rate_limit import limiter  # noqa: E402
    limiter.enabled = False

    with TestClient(main_mod.app, raise_server_exceptions=False) as c:
        def usuario():
            u = "r1_" + uuid.uuid4().hex[:10]
            mail = f"{u}@example.com"
            r = c.post("/auth/register", json={"username": u, "password": CLAVE, "email": mail, "name": "R"})
            assert r.status_code in (200, 201), r.text
            return u, mail

        def link(mail):
            return c.post("/auth/request-password-reset", json={"email": mail}).json()["dev_token_hint"]

        def resetear(token, nueva):
            return lambda: c.post("/auth/reset-password", json={"token": token, "new_password": nueva})

        def clave_es(u, clave):
            return main_mod.verify_password(clave, sql("select password from users where username=%s", u)[0][0])

        # 1. el mismo link dos veces a la vez
        u, mail = usuario()
        token = link(mail)
        en_cola, r1, r2 = a_la_vez(u, resetear(token, CLAVE2), resetear(token, CLAVE3))
        codigos = sorted([r1.status_code, r2.status_code])
        chequear(en_cola and codigos == [200, 400] and clave_es(u, CLAVE2),
                 f"el mismo link dos veces a la vez cambia la clave una vez: en cola {en_cola}, "
                 f"{r1.status_code} {r2.status_code}, clave de la primera {clave_es(u, CLAVE2)}")

        # 2. cambio de email primero, el link a la vez
        u, mail = usuario()
        token = link(mail)
        sesion = c.post("/auth/login", json={"username": u, "password": CLAVE}).json()["access_token"]

        def cambiar_email():
            return c.put("/api/user/profile", headers={"Authorization": f"Bearer {sesion}"},
                         json={"email": "otro_" + mail, "current_password": CLAVE})
        en_cola, r_perfil, r_reset = a_la_vez(u, cambiar_email, resetear(token, CLAVE3))
        chequear(en_cola and r_perfil.status_code == 200 and r_reset.status_code == 400 and clave_es(u, CLAVE),
                 f"el cambio de email que llega primero mata el link: en cola {en_cola}, perfil "
                 f"{r_perfil.status_code}, reset {r_reset.status_code} {r_reset.text[:120]}, "
                 f"clave sin cambiar {clave_es(u, CLAVE)}")

        # 3. el link se pide a la vez que el cambio de email, detrás de él
        u, mail = usuario()
        sesion = c.post("/auth/login", json={"username": u, "password": CLAVE}).json()["access_token"]
        en_cola, r_perfil, r_link = a_la_vez(
            u, cambiar_email, lambda: c.post("/auth/request-password-reset", json={"email": mail}))
        token = r_link.json().get("dev_token_hint")
        r_reset = resetear(token, CLAVE3)() if token else None
        chequear(en_cola and r_perfil.status_code == 200 and r_link.status_code == 200
                 and (r_reset is None or r_reset.status_code == 400) and clave_es(u, CLAVE),
                 f"el link pedido a la vez que el cambio de email no sirve: en cola {en_cola}, perfil "
                 f"{r_perfil.status_code}, pedido {r_link.status_code}, reset "
                 f"{r_reset.status_code if r_reset else 'sin link'}, clave sin cambiar {clave_es(u, CLAVE)}")

        # 4. el tope por cuenta se cuenta antes de trabar: contar hace commit y,
        # con la cuenta ya trabada, soltaría la traba. El cambio de email corre
        # justo después de contar; si la traba se soltó, el link sale igual.
        u, mail = usuario()
        sesion = c.post("/auth/login", json={"username": u, "password": CLAVE}).json()["access_token"]
        contar = main_mod.limites_auth.contar
        perfil = []

        async def contar_y_cambiar_email(db, clave, ventana):
            n = await contar(db, clave, ventana)
            if clave.startswith("reset:cuenta:") and not perfil:
                perfil.append(await asyncio.wait_for(asyncio.to_thread(cambiar_email), 30))
            return n
        main_mod.limites_auth.contar, limiter.enabled = contar_y_cambiar_email, True
        try:
            r_link = c.post("/auth/request-password-reset", json={"email": mail})
        finally:
            main_mod.limites_auth.contar, limiter.enabled = contar, False
        token = r_link.json().get("dev_token_hint")
        r_reset = resetear(token, CLAVE3)() if token else None
        chequear(perfil and perfil[0].status_code == 200 and r_link.status_code == 200
                 and (r_reset is None or r_reset.status_code == 400) and clave_es(u, CLAVE),
                 f"el tope por cuenta no suelta la traba: perfil {perfil[0].status_code if perfil else 'no corrió'}, "
                 f"pedido {r_link.status_code}, reset {r_reset.status_code if r_reset else 'sin link'}, "
                 f"clave sin cambiar {clave_es(u, CLAVE)}")
finally:
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
