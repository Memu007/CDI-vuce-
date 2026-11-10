"""ORG-1 contra un Postgres de verdad: asyncpg devuelve `expires_at` con zona
(SQLite, sin zona) y ahí estaba el 500. Además, sólo Postgres deja ver qué
hacen dos registros a la vez con el bloqueo del estudio (`FOR UPDATE`).

Comprueba:
1. validar, registrarse e invitar con invitaciones vigentes, vencidas y usadas
   responden sin 500;
2. la invitación sólo sirve para el email invitado, y el intento con otro email
   no la gasta;
3. el tope de usuarios del plan, al invitar y al registrarse;
4. un solo uso y el tope bajo carrera: dos registros a la vez con la misma
   invitación, dos registros con invitaciones distintas por el último lugar
   del estudio, y dos invitaciones enviadas a la vez por ese último lugar;
5. un email, una cuenta (D40): no se invita un email que ya tiene cuenta, y
   al registrarse se usan las otras invitaciones de ese email en el estudio.

uso (con un Postgres local y descartable, nunca el de producción):
  python scripts/testing/org1_postgres.py postgresql://cdi@127.0.0.1:55432/<base>
"""
import asyncio
import os
import sys
import threading
import time
import uuid
from urllib.parse import urlparse

URL = sys.argv[1] if len(sys.argv) > 1 else ""
_host = urlparse(URL).hostname or ""
if not URL.startswith("postgresql://") or _host not in ("127.0.0.1", "localhost"):
    sys.exit("uso: org1_postgres.py postgresql://usuario@127.0.0.1:<puerto>/<base>  (sólo un Postgres local)")

os.environ.update(
    DATABASE_URL=URL, ENVIRONMENT="testing", EMAIL_VERIFICATION_REQUIRED="false",
    JWT_SECRET_KEY="clave-solo-para-esta-prueba-con-mas-de-32-caracteres",
    GEMINI_API_KEY="test-key", VUCE_MODE="fake", TARIFAR_MODE="fake", AFIP_MODE="fake",
    DOLARAPI_BASE="http://127.0.0.1:9/v1/dolares",
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import psycopg2  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import proyecto_maria.main as main_mod  # noqa: E402
from proyecto_maria.core.rate_limit import limiter  # noqa: E402
from proyecto_maria.services import billing_service  # noqa: E402

limiter.enabled = False
FALLAS = []
CLAVE = "SecureP@ss1"
PREMIUM = billing_service.PLANS["premium"]
TOPE_REAL = PREMIUM["users"]


def chequear(ok, que):
    print(("OK    | " if ok else "FALLA | ") + que)
    if not ok:
        FALLAS.append(que)


def sql(consulta, *args):
    with psycopg2.connect(URL) as con, con.cursor() as cur:
        cur.execute(consulta, args)
        return cur.fetchall() if cur.description else None


def azar(prefijo):
    return f"{prefijo}{uuid.uuid4().hex[:8]}"


def email():
    return f"{azar('o1m_')}@example.com"


def estado(token):
    return sql("select status from invitations where token=%s", token)[0][0]


def usuarios(correo):
    return sql("select username, organization_id from users where email=%s", correo)


def miembros(org_id):
    return sql("select count(*) from users where organization_id=%s", org_id)[0][0]


def detalle(r):
    try:
        return r.json().get("detail", "")
    except ValueError:
        return r.text[:120]


with TestClient(main_mod.app, raise_server_exceptions=False) as c:

    class Estudio:
        def __init__(self):
            self.dueno = azar("o1d_")
            c.cookies.clear()
            r = c.post("/api/organizations/create", json={
                "name": "Estudio ORG-1", "username": self.dueno, "password": CLAVE,
                "email": f"{self.dueno}@example.com"})
            assert r.status_code == 200, r.text
            self.sesion = dict(c.cookies)
            self.org_id = usuarios(f"{self.dueno}@example.com")[0][1]

        def invitar(self, correo):
            c.cookies.clear()
            for k, v in self.sesion.items():
                c.cookies.set(k, v)
            return c.post("/api/organizations/invite", json={"email": correo})

        def token(self, correo):
            r = self.invitar(correo)
            assert r.status_code == 200, r.text
            return r.json()["invite_link"].split("invite=")[1]

    def registrar(correo, token):
        c.cookies.clear()
        return c.post("/auth/register", json={"username": azar("o1u_"), "password": CLAVE,
                                              "email": correo, "invite_token": token})

    def validar(token):
        return c.get(f"/api/invitations/{token}")

    # --- 1. sin 500
    est = Estudio()
    a = email()
    tok = est.token(a)
    r = validar(tok)
    chequear(r.status_code == 200, f"validar una invitación vigente ({r.status_code} {detalle(r)})")
    r = registrar(a, tok)
    chequear(r.status_code == 200 and usuarios(a)[0][1] == est.org_id and estado(tok) == "accepted",
             f"registrarse con la invitación entra al estudio y la gasta ({r.status_code} {detalle(r)})")
    r = validar(tok)
    chequear(r.status_code == 400 and "ya fue usada" in detalle(r), f"validar una usada ({r.status_code} {detalle(r)})")

    b = email()
    tok = est.token(b)
    sql("update invitations set expires_at = now() - interval '1 minute' where token=%s", tok)
    r = registrar(b, tok)
    chequear(r.status_code == 400 and "expiró" in detalle(r) and not usuarios(b),
             f"registrarse con una vencida que nadie validó ({r.status_code} {detalle(r)})")
    r = validar(tok)
    chequear(r.status_code == 400 and "expiró" in detalle(r) and estado(tok) == "expired",
             f"validar una vencida la marca vencida ({r.status_code} {detalle(r)})")
    r = est.invitar(email())
    chequear(r.status_code == 200, f"invitar con una pendiente vencida en el estudio ({r.status_code} {detalle(r)})")

    # --- 2. atada al email
    est = Estudio()
    a = email()
    tok = est.token(a)
    for intruso in (email(), a.replace("@", "+x@"), a + ".ar"):
        r = registrar(intruso, tok)
        chequear(r.status_code == 400 and "otro email" in detalle(r) and not usuarios(intruso),
                 f"otro email ({intruso.split('@')[0][-6:]}@…) no entra ({r.status_code} {detalle(r)})")
    chequear(estado(tok) == "pending" and miembros(est.org_id) == 1, "y la invitación sigue pendiente")
    r = registrar("  " + a.upper() + " ", tok)
    chequear(r.status_code == 200 and usuarios(a)[0][1] == est.org_id,
             f"el email invitado, con mayúsculas y espacios, entra ({r.status_code} {detalle(r)})")

    # --- 3. tope del plan
    try:
        PREMIUM["users"] = 2
        est = Estudio()
        a = email()
        tok = est.token(a)
        r = est.invitar(email())
        chequear(r.status_code == 400 and "los 2 usuarios" in detalle(r),
                 f"tope 2: dueño + una pendiente, la segunda no ({r.status_code} {detalle(r)})")
        chequear(est.invitar(a).status_code == 200, "reinvitar a la pendiente no ocupa otro lugar")

        PREMIUM["users"] = 3
        est = Estudio()
        a, b = email(), email()
        tok_a, tok_b = est.token(a), est.token(b)
        PREMIUM["users"] = 2
        r = registrar(a, tok_a)
        chequear(r.status_code == 200, f"tope 2: el primero entra ({r.status_code} {detalle(r)})")
        r = registrar(b, tok_b)
        chequear(r.status_code == 400 and "los 2 usuarios" in detalle(r) and estado(tok_b) == "pending"
                 and not usuarios(b), f"el estudio lleno no deja entrar y no gasta la invitación ({r.status_code} {detalle(r)})")

        # --- 4. un solo uso, con dos registros a la vez
        hash_real = main_mod.hash_password

        def carrera(altas):
            barrera = threading.Barrier(len(altas), timeout=60)

            def _hash_y_esperar(clave):
                h = hash_real(clave)
                barrera.wait()
                return h

            main_mod.hash_password = _hash_y_esperar
            res = [None] * len(altas)

            def uno(i, correo, token):
                r = c.post("/auth/register", json={"username": azar("o1u_"), "password": CLAVE,
                                                   "email": correo, "invite_token": token})
                res[i] = (r.status_code, detalle(r))

            try:
                hilos = [threading.Thread(target=uno, args=(i, *alta)) for i, alta in enumerate(altas)]
                for h in hilos:
                    h.start()
                for h in hilos:
                    h.join(timeout=120)
            finally:
                main_mod.hash_password = hash_real
            return sorted(r for r in res if r)

        PREMIUM["users"] = TOPE_REAL
        est = Estudio()
        a = email()
        tok = est.token(a)
        c.cookies.clear()
        res = carrera([(a, tok), (a, tok)])
        chequear([s for s, _ in res] == [200, 400] and "ya fue usada" in res[1][1]
                 and len(usuarios(a)) == 1 and estado(tok) == "accepted",
                 f"misma invitación a la vez: entra uno y el otro recibe 400 ({res})")

        PREMIUM["users"] = 3
        est = Estudio()
        a, b = email(), email()
        tok_a, tok_b = est.token(a), est.token(b)
        PREMIUM["users"] = 2
        c.cookies.clear()
        res = carrera([(a, tok_a), (b, tok_b)])
        estados = sorted([estado(tok_a), estado(tok_b)])
        chequear([s for s, _ in res] == [200, 400] and "los 2 usuarios" in res[1][1]
                 and miembros(est.org_id) == 2 and estados == ["accepted", "pending"],
                 f"dos invitaciones por el último lugar: entra una ({res}, miembros {miembros(est.org_id)}, {estados})")

        # --- 4b. dos invitaciones enviadas a la vez por el último lugar. Cada
        # una, ya pasado el control del tope, espera en su commit hasta que la
        # otra también llegue al commit (sin bloqueo: las dos contaron el mismo
        # lugar libre) o quede frenada en el bloqueo del estudio
        # (pg_stat_activity). El plazo sólo corre si no pasa ninguna de las dos.
        from sqlalchemy.ext.asyncio import AsyncSession
        from proyecto_maria.database.models import Invitation
        commit_real = AsyncSession.commit
        en_el_commit = []

        async def _commit_con_la_otra_a_la_par(self):
            if any(isinstance(o, Invitation) for o in self.new):
                en_el_commit.append(1)
                hasta = time.monotonic() + 20
                while time.monotonic() < hasta and len(en_el_commit) < 2 and not sql(
                        "select count(*) from pg_stat_activity where datname = current_database()"
                        " and wait_event_type = 'Lock'")[0][0]:
                    await asyncio.sleep(0.05)  # sin frenar el loop: la otra tiene que poder avanzar
            return await commit_real(self)

        PREMIUM["users"] = 2
        est = Estudio()
        a, b = email(), email()
        res = [None, None]

        def invitar_a_la_vez(i, correo):
            r = c.post("/api/organizations/invite", json={"email": correo})
            res[i] = (r.status_code, detalle(r))

        AsyncSession.commit = _commit_con_la_otra_a_la_par
        try:
            hilos = [threading.Thread(target=invitar_a_la_vez, args=(i, x)) for i, x in enumerate((a, b))]
            for h in hilos:
                h.start()
            for h in hilos:
                h.join(timeout=120)
        finally:
            AsyncSession.commit = commit_real
        res = sorted(r for r in res if r)
        pendientes = sql("select count(*) from invitations where org_id=%s and status='pending'", est.org_id)[0][0]
        chequear([s for s, _ in res] == [200, 400] and "ocupa los 2" in res[1][1] and pendientes == 1,
                 f"dos invitaciones a la vez por el último lugar: sale una ({res}, pendientes {pendientes})")

        # --- 5. un email, una cuenta (D40)
        YA_TIENE_CUENTA = "Ese email ya tiene una cuenta en CDI y no se puede invitar como miembro nuevo."
        PREMIUM["users"] = 3
        for donde in ("este estudio", "otro estudio", "sin estudio", "guardada con mayúsculas"):
            est = Estudio()
            a = email()
            if donde == "este estudio":
                registrar(a, est.token(a))
            elif donde == "otro estudio":
                registrar(a, Estudio().token(a))
            else:
                c.cookies.clear()
                c.post("/auth/register", json={"username": azar("o1u_"), "password": CLAVE, "email": a})
            chequear(len(usuarios(a)) == 1, f"cuenta {donde}: creada")
            if donde == "guardada con mayúsculas":
                # Una cuenta de antes de EMAIL-1 puede tener el email con mayúsculas.
                sql("update users set email=%s where email=%s", a.upper(), a)
                chequear(len(usuarios(a.upper())) == 1, "  la cuenta queda con el email en mayúsculas")
            r = est.invitar(f" {a.upper()} ")
            pend = sql("select count(*) from invitations where org_id=%s and email=%s and status='pending'", est.org_id, a)[0][0]
            chequear(r.status_code == 400 and detalle(r) == YA_TIENE_CUENTA and pend == 0,
                     f"invitar un email con cuenta {donde}: 400 sin invitación ({r.status_code} {detalle(r)})")
            libres = 3 - miembros(est.org_id)
            oks = [est.invitar(email()).status_code for _ in range(libres)]
            r = est.invitar(email())
            chequear(oks == [200] * libres and r.status_code == 400,
                     f"  y no ocupa lugar: {libres} libres, {oks}, la siguiente {r.status_code}")

        PREMIUM["users"] = TOPE_REAL
        est, otro = Estudio(), Estudio()
        a = email()
        tok1, tok2 = est.token(a), est.token(a.upper())
        ajena, de_otro = est.token(email()), otro.token(a)
        # Una de antes de EMAIL-1, con mayúsculas y espacios: el registro la acepta.
        vieja = est.token(a)
        sql("update invitations set email=%s where token=%s", f"  {a.upper()} ", vieja)
        r = registrar(a, tok2)
        chequear(r.status_code == 200 and estado(tok1) == "accepted" and "ya fue usada" in detalle(validar(tok1))
                 and estado(vieja) == "accepted"
                 and estado(ajena) == "pending" and estado(de_otro) == "pending",
                 f"registrarse usa las otras del mismo email en ese estudio, y sólo esas ({r.status_code} "
                 f"{estado(tok1)} {estado(vieja)} {estado(ajena)} {estado(de_otro)})")

        est = Estudio()
        a, sacado = email(), azar("o1u_")
        tok1, tok2 = est.token(a), est.token(a)
        c.cookies.clear()
        r = c.post("/auth/register", json={"username": sacado, "password": CLAVE, "email": a, "invite_token": tok1})
        suya = dict(c.cookies)
        chequear(r.status_code == 200, f"el sacado: entra con la primera ({r.status_code} {detalle(r)})")
        c.cookies.clear()
        for k, v in est.sesion.items():
            c.cookies.set(k, v)
        r = c.delete(f"/api/organizations/members/{sacado}")
        chequear(r.status_code == 200, f"el sacado: el dueño lo saca ({r.status_code} {detalle(r)})")
        c.cookies.clear()
        for k, v in suya.items():
            c.cookies.set(k, v)
        r = c.put("/api/user/profile", json={"email": email(), "current_password": CLAVE})
        chequear(r.status_code == 200 and not usuarios(a), f"el sacado: cambia su email ({r.status_code} {detalle(r)})")
        r = registrar(a, tok2)
        chequear(r.status_code == 400 and "ya fue usada" in detalle(r) and not usuarios(a)
                 and miembros(est.org_id) == 1,
                 f"el sacado no vuelve a entrar con la segunda ({r.status_code} {detalle(r)}, miembros {miembros(est.org_id)})")

        est = Estudio()
        a = email()
        tok1, tok2 = est.token(a), est.token(a)
        c.cookies.clear()
        res = carrera([(a, tok1), (a, tok2)])
        chequear([s for s, _ in res] == [200, 400] and "ya fue usada" in res[1][1] and len(usuarios(a)) == 1
                 and {estado(tok1), estado(tok2)} == {"accepted"},
                 f"dos invitaciones del mismo email a la vez: entra uno y el otro recibe 400 ({res})")

        PREMIUM["users"] = 3
        est = Estudio()
        a, nuevo = email(), email()
        tok = est.token(a)
        c.cookies.clear()
        r = c.post("/auth/register", json={"username": azar("o1u_"), "password": CLAVE, "email": a,
                                           "invite_token": tok})
        chequear(r.status_code == 200, f"el miembro entra con su invitación ({r.status_code} {detalle(r)})")
        suya = dict(c.cookies)
        tok_nuevo = est.token(nuevo)
        c.cookies.clear()
        for k, v in suya.items():
            c.cookies.set(k, v)
        r = c.put("/api/user/profile", json={"email": nuevo, "current_password": CLAVE})
        ok_perfil = r.status_code == 200 and estado(tok_nuevo) == "pending"
        r1, r2 = est.invitar(email()), est.invitar(email())
        chequear(ok_perfil and r1.status_code == 200 and r2.status_code == 400,
                 f"una pendiente al email de un miembro no ocupa lugar ({ok_perfil}, {r1.status_code}, {r2.status_code})")
    finally:
        PREMIUM["users"] = TOPE_REAL

print(f"fallas: {len(FALLAS)}")
sys.exit(1 if FALLAS else 0)
