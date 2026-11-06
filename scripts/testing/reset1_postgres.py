"""RESET-1 contra un Postgres de verdad: el link de reset se consume atómico.

Una conexión traba la fila del usuario; dos pedidos quedan en cola detrás y
se sueltan juntos. Comprueba que:
1. el mismo link usado dos veces a la vez cambia la clave una sola vez: un
   200 y un 400;
2. un cambio de email que llega primero mata el link que se usa a la vez:
   el perfil da 200, el reset 400 y la clave no cambia;
3. un link pedido a la vez que un cambio de email, que leyó la cuenta antes
   del cambio y la guarda después, no sirve: un disparador de esta base de
   prueba frena el guardado del link hasta que se suelta;
4. un link pedido detrás de un cambio de email que ya trabó la cuenta no
   sale, o no sirve.

uso (con un Postgres local y descartable, nunca el de producción; el usuario
tiene que poder crear bases):
  python scripts/testing/reset1_postgres.py postgresql://cdi@127.0.0.1:55432/postgres
"""
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


def esperan_un_bloqueo(n, o_termina=None):
    """Hasta que n conexiones de la base esperan un bloqueo, o `o_termina`
    termina (60 s como mucho)."""
    hasta = time.monotonic() + 60
    while time.monotonic() < hasta:
        if (o_termina is not None and o_termina.done()) or sql(
                "select count(*) from pg_stat_activity where datname=%s and wait_event_type='Lock'",
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

        def el_pedido_no_sirve(que, u, en_cola, r_perfil, r_link):
            token = r_link.json().get("dev_token_hint")
            r_reset = resetear(token, CLAVE3)() if token else None
            chequear(en_cola and r_perfil.status_code == 200 and r_link.status_code == 200
                     and (r_reset is None or r_reset.status_code == 400) and clave_es(u, CLAVE),
                     f"{que} no sirve: en cola {en_cola}, perfil {r_perfil.status_code}, pedido "
                     f"{r_link.status_code}, reset {r_reset.status_code if r_reset else 'sin link'}, "
                     f"clave sin cambiar {clave_es(u, CLAVE)}")

        # 3. el link se pide con el email viejo y se guarda después del cambio
        sql("""create function frenar_link() returns trigger language plpgsql as
               $$ begin perform pg_advisory_xact_lock(7311); return new; end $$;
               create trigger frenar_link before insert on password_reset_tokens
               for each row execute function frenar_link(); select 1""")
        u, mail = usuario()
        sesion = c.post("/auth/login", json={"username": u, "password": CLAVE}).json()["access_token"]
        freno = psycopg2.connect(URL_BASE)
        try:
            with freno.cursor() as cur:
                cur.execute("select pg_advisory_lock(7311)")
            with concurrent.futures.ThreadPoolExecutor(2) as ex:
                r_link = ex.submit(lambda: c.post("/auth/request-password-reset", json={"email": mail}))
                en_cola = esperan_un_bloqueo(1)
                r_perfil = ex.submit(cambiar_email)
                en_cola = en_cola and esperan_un_bloqueo(2, o_termina=r_perfil)
                with freno.cursor() as cur:
                    cur.execute("select pg_advisory_unlock(7311)")
                r_link, r_perfil = r_link.result(timeout=120), r_perfil.result(timeout=120)
        finally:
            freno.close()
        el_pedido_no_sirve("el link pedido mientras se guarda el cambio de email", u, en_cola, r_perfil, r_link)

        # 4. el cambio de email traba la cuenta primero y el link se pide detrás
        u, mail = usuario()
        sesion = c.post("/auth/login", json={"username": u, "password": CLAVE}).json()["access_token"]
        en_cola, r_perfil, r_link = a_la_vez(
            u, cambiar_email, lambda: c.post("/auth/request-password-reset", json={"email": mail}))
        el_pedido_no_sirve("el link pedido detrás del cambio de email", u, en_cola, r_perfil, r_link)
finally:
    try:
        admin(f'drop database if exists "{BASE}" with (force)')
    except Exception as e:
        print(f"no se pudo borrar la base {BASE}: {e}")

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
