"""ORG-1: invitaciones al estudio.

1. Sin 500 en las dos bases: Postgres devuelve `expires_at` con zona y SQLite
   sin zona. Acá se corre cada caso de las dos formas: la de SQLite tal cual y
   la de Postgres inyectando la zona al leer la invitación (evento `load`).
   El Postgres de verdad lo cubre scripts/testing/org1_postgres.py.
2. Atada al email: sólo se registra el email invitado; si no, 400 y la
   invitación sigue pendiente.
3. Tope del plan: miembros (el dueño incluido) más invitaciones pendientes
   sin vencer, con el tope de `billing_service.get_plan`.
4. Un solo uso: la invitación se gasta en la misma transacción que el alta,
   y sólo si seguía pendiente.

Cada caso crea su propio estudio con nombres al azar y no toca datos de otros.
"""
import asyncio
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, select, update
from sqlalchemy.orm.attributes import set_committed_value

import proyecto_maria.database.connection as _conn
import proyecto_maria.main as main_mod
from proyecto_maria.database.models import Invitation, Organization, User
from proyecto_maria.main import app
from proyecto_maria.services import billing_service

CLAVE = "SecureP@ss1"


# ---------------------------------------------------------------- entorno

def _con_zona(target, _context):
    """Lo que devuelve asyncpg: `expires_at` con zona (UTC)."""
    if target.expires_at is not None and target.expires_at.tzinfo is None:
        set_committed_value(target, "expires_at", target.expires_at.replace(tzinfo=timezone.utc))


@pytest.fixture(params=["sqlite_sin_zona", "postgres_con_zona"])
def zona(request):
    if request.param == "postgres_con_zona":
        event.listen(Invitation, "load", _con_zona)
        event.listen(Invitation, "refresh", _con_zona)
        yield request.param
        event.remove(Invitation, "load", _con_zona)
        event.remove(Invitation, "refresh", _con_zona)
    else:
        yield request.param


@pytest.fixture(autouse=True)
def _sin_verificacion_de_email(monkeypatch):
    monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False


def _tope(monkeypatch, n):
    monkeypatch.setitem(billing_service.PLANS["premium"], "users", n)


# ---------------------------------------------------------------- base

def _db(consulta):
    async def _correr():
        async with _conn.AsyncSessionLocal() as s:
            resultado = await consulta(s)
            await s.commit()
            return resultado
    return asyncio.run(_correr())


def _invitacion(token):
    async def q(s):
        inv = (await s.execute(select(Invitation).where(Invitation.token == token))).scalars().first()
        return {"status": inv.status, "email": inv.email, "org_id": inv.org_id}
    return _db(q)


def _usuarios(email):
    async def q(s):
        res = await s.execute(select(User.username, User.organization_id).where(User.email == email))
        return [tuple(f) for f in res.all()]
    return _db(q)


def _miembros(org_id):
    async def q(s):
        res = await s.execute(select(User.username).where(User.organization_id == org_id))
        return sorted(u for (u,) in res.all())
    return _db(q)


def _cambiar_invitacion(token, **valores):
    async def q(s):
        await s.execute(update(Invitation).where(Invitation.token == token).values(**valores))
    _db(q)


def _cambiar_estudio(org_id, **valores):
    async def q(s):
        await s.execute(update(Organization).where(Organization.id == org_id).values(**valores))
    _db(q)


# ---------------------------------------------------------------- flujo

def _azar(prefijo):
    return f"{prefijo}{uuid.uuid4().hex[:8]}"


class Estudio:
    """Un estudio nuevo con su dueño logueado en `self.c`."""

    def __init__(self):
        self.c = TestClient(app)
        self.dueno = _azar("o1d_")
        r = self.c.post("/api/organizations/create", json={
            "name": "Estudio ORG-1", "username": self.dueno, "password": CLAVE,
            "email": f"{self.dueno}@example.com"})
        assert r.status_code == 200, r.text
        [(_, self.org_id)] = _usuarios(f"{self.dueno}@example.com")
        assert self.org_id

    def invitar(self, email):
        return self.c.post("/api/organizations/invite", json={"email": email})

    def invitar_ok(self, email):
        r = self.invitar(email)
        assert r.status_code == 200, r.text
        return r.json()["invite_link"].split("invite=")[1]

    def quitar(self, username):
        return self.c.delete(f"/api/organizations/members/{username}")


def _email():
    return f"{_azar('o1m_')}@example.com"


def _registrar(email, token, username=None, cliente=None):
    cliente = cliente or TestClient(app)
    return cliente.post("/auth/register", json={
        "username": username or _azar("o1u_"), "password": CLAVE,
        "email": email, "invite_token": token})


def _validar(token):
    return TestClient(app).get(f"/api/invitations/{token}")


# ================================================================ 1. sin 500

def test_validar_invitacion_vigente(zona):
    est = Estudio()
    email = _email()
    tok = est.invitar_ok(email)
    r = _validar(tok)
    assert r.status_code == 200, r.text
    assert r.json()["email"] == email and r.json()["org_id"] == est.org_id


def test_validar_invitacion_vencida_400_y_queda_vencida(zona):
    est = Estudio()
    tok = est.invitar_ok(_email())
    _cambiar_invitacion(tok, expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    r = _validar(tok)
    assert r.status_code == 400 and "expiró" in r.json()["detail"], r.text
    assert _invitacion(tok)["status"] == "expired"


def test_validar_invitacion_usada_400(zona):
    est = Estudio()
    email = _email()
    tok = est.invitar_ok(email)
    assert _registrar(email, tok).status_code == 200
    r = _validar(tok)
    assert r.status_code == 400 and "ya fue usada" in r.json()["detail"], r.text


def test_registro_con_invitacion_vigente_entra_al_estudio(zona):
    """Guarda: invitación válida, email correcto y lugar libre entran como hoy."""
    est = Estudio()
    email = _email()
    tok = est.invitar_ok(email)
    usuario = _azar("o1u_")
    r = _registrar(email, tok, username=usuario)
    assert r.status_code == 200, r.text
    assert r.json().get("access_token")
    assert _usuarios(email) == [(usuario, est.org_id)]
    assert _invitacion(tok)["status"] == "accepted"


@pytest.mark.parametrize("estado", ["pending", "expired"])
def test_registro_con_invitacion_vencida_400_sin_alta(zona, estado):
    """Vencida sin que nadie la haya validado (pending) o ya marcada."""
    est = Estudio()
    email = _email()
    tok = est.invitar_ok(email)
    _cambiar_invitacion(tok, status=estado, expires_at=datetime.now(timezone.utc) - timedelta(seconds=5))
    r = _registrar(email, tok)
    assert r.status_code == 400 and "expiró" in r.json()["detail"], r.text
    assert _usuarios(email) == []


def test_invitar_con_otras_pendientes_vencidas_y_vigentes(zona, monkeypatch):
    """Invitar compara fechas de las pendientes: no puede romper con zona."""
    _tope(monkeypatch, 4)
    est = Estudio()
    vieja = est.invitar_ok(_email())
    _cambiar_invitacion(vieja, expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    est.invitar_ok(_email())
    r = est.invitar(_email())
    assert r.status_code == 200, r.text


# ================================================================ 2. atada al email

@pytest.mark.parametrize("otro", [
    "{nuevo}",
    "{local}+x@example.com",
    "{local}@example.com.ar",
    "{local}@otro.com",
])
def test_registro_con_otro_email_400_y_la_invitacion_sigue(zona, otro):
    est = Estudio()
    email = _email()
    tok = est.invitar_ok(email)
    intruso = otro.format(local=email.split("@")[0], nuevo=_email())
    usuario = _azar("o1u_")
    r = _registrar(intruso, tok, username=usuario)
    assert r.status_code == 400 and "otro email" in r.json()["detail"], r.text
    assert _usuarios(intruso) == []
    assert _miembros(est.org_id) == [est.dueno]
    assert _invitacion(tok)["status"] == "pending"
    # La persona invitada todavía puede usarla.
    assert _registrar(email, tok).status_code == 200


def test_registro_con_mayusculas_y_espacios_del_email_invitado(zona):
    est = Estudio()
    local = _azar("o1m_")
    tok = est.invitar_ok(f"{local}@Example.com")
    r = _registrar(f"  {local.upper()}@EXAMPLE.COM ", tok)
    assert r.status_code == 200, r.text
    assert _usuarios(f"{local}@example.com")[0][1] == est.org_id


def test_invitacion_sin_email_no_deja_entrar_a_nadie(zona):
    est = Estudio()
    tok = est.invitar_ok(_email())
    _cambiar_invitacion(tok, email="")
    email = _email()
    r = _registrar(email, tok)
    assert r.status_code == 400 and "otro email" in r.json()["detail"], r.text
    assert _usuarios(email) == []
    assert _invitacion(tok)["status"] == "pending"


# ================================================================ 3. tope del plan

@pytest.mark.parametrize("tope", [2, 3, 4])
def test_invitar_hasta_el_tope_del_plan(zona, monkeypatch, tope):
    """El tope sale del plan (no un 3 fijo) y el dueño ocupa un lugar."""
    _tope(monkeypatch, tope)
    est = Estudio()
    for _ in range(tope - 1):
        est.invitar_ok(_email())
    r = est.invitar(_email())
    assert r.status_code == 400, r.text
    assert f"los {tope} usuarios" in r.json()["detail"]


def test_tope_uno_el_duenio_ya_lo_ocupa(monkeypatch):
    _tope(monkeypatch, 1)
    est = Estudio()
    r = est.invitar(_email())
    assert r.status_code == 400 and "los 1 usuarios" in r.json()["detail"], r.text


def test_reinvitar_un_email_pendiente_no_ocupa_otro_lugar(monkeypatch):
    _tope(monkeypatch, 3)
    est = Estudio()
    a, b = _email(), _email()
    est.invitar_ok(a)
    est.invitar_ok(b)
    # Lleno (dueño + 2 pendientes): reinvitar a uno de ellos se puede...
    tok_a2 = est.invitar_ok(a.upper())
    # ...pero no suma a nadie nuevo.
    assert est.invitar(_email()).status_code == 400
    assert _registrar(a, tok_a2).status_code == 200


def test_invitacion_pendiente_vencida_no_ocupa_lugar(zona, monkeypatch):
    _tope(monkeypatch, 2)
    est = Estudio()
    tok = est.invitar_ok(_email())
    assert est.invitar(_email()).status_code == 400
    _cambiar_invitacion(tok, expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    assert est.invitar(_email()).status_code == 200


def test_miembro_que_entro_ocupa_su_lugar(monkeypatch):
    _tope(monkeypatch, 2)
    est = Estudio()
    email = _email()
    assert _registrar(email, est.invitar_ok(email)).status_code == 200
    r = est.invitar(_email())
    assert r.status_code == 400 and "los 2 usuarios" in r.json()["detail"], r.text


def test_registro_con_el_estudio_lleno_400_sin_gastar_la_invitacion(zona, monkeypatch):
    _tope(monkeypatch, 3)
    est = Estudio()
    a, b = _email(), _email()
    tok_a, tok_b = est.invitar_ok(a), est.invitar_ok(b)
    _tope(monkeypatch, 2)  # el plan bajó después de invitar
    assert _registrar(a, tok_a).status_code == 200
    r = _registrar(b, tok_b)
    assert r.status_code == 400 and "los 2 usuarios" in r.json()["detail"], r.text
    assert _usuarios(b) == []
    assert _invitacion(tok_b)["status"] == "pending"
    assert len(_miembros(est.org_id)) == 2
    # Con lugar, la misma invitación entra.
    _tope(monkeypatch, 3)
    assert _registrar(b, tok_b).status_code == 200
    assert len(_miembros(est.org_id)) == 3


def test_quitar_un_miembro_libera_su_lugar(monkeypatch):
    _tope(monkeypatch, 2)
    est = Estudio()
    email = _email()
    usuario = _azar("o1u_")
    assert _registrar(email, est.invitar_ok(email), username=usuario).status_code == 200
    assert est.invitar(_email()).status_code == 400
    r = est.quitar(usuario)
    assert r.status_code == 200, r.text
    assert est.invitar(_email()).status_code == 200


def test_estudio_sin_plan_usa_el_tope_premium(monkeypatch):
    _tope(monkeypatch, 2)
    est = Estudio()
    _cambiar_estudio(est.org_id, plan=None)
    a = _email()
    tok = est.invitar_ok(a)
    r = est.invitar(_email())
    assert r.status_code == 400 and "los 2 usuarios" in r.json()["detail"], r.text
    assert _registrar(a, tok).status_code == 200


# ================================================================ 4. un solo uso

def test_reusar_una_invitacion_usada_400(zona):
    est = Estudio()
    email = _email()
    tok = est.invitar_ok(email)
    assert _registrar(email, tok).status_code == 200
    r = _registrar(email, tok)
    assert r.status_code == 400, r.text
    assert len(_usuarios(email)) == 1


def _ruta_de_la_base():
    url = os.environ["DATABASE_URL"]
    return url.split(":///", 1)[1]


def test_invitacion_gastada_entre_la_lectura_y_el_alta_no_crea_usuario(monkeypatch):
    """Otro registro la gasta justo después de que este la leyó pendiente.

    Determinístico: antes de la primera escritura de `invitations` de este
    registro, una conexión aparte la marca usada y confirma.
    """
    est = Estudio()
    email = _email()
    tok = est.invitar_ok(email)
    hecho = []

    def _otro_registro_la_gasta(conn, cursor, statement, parameters, context, executemany):
        if not hecho and statement.lstrip().upper().startswith("UPDATE INVITATIONS"):
            hecho.append(True)
            with sqlite3.connect(_ruta_de_la_base(), timeout=30) as otra:
                otra.execute("UPDATE invitations SET status='accepted' WHERE token=?", (tok,))

    motor = _conn.engine.sync_engine
    event.listen(motor, "before_cursor_execute", _otro_registro_la_gasta)
    try:
        r = _registrar(email, tok)
    finally:
        event.remove(motor, "before_cursor_execute", _otro_registro_la_gasta)
    assert hecho, "el registro nunca escribió la invitación"
    assert r.status_code == 400 and "ya fue usada" in r.json()["detail"], r.text
    assert _usuarios(email) == []


def _carrera(monkeypatch, altas):
    """Corre los registros a la vez: todos esperan juntos después del hash."""
    barrera = threading.Barrier(len(altas), timeout=60)
    hash_real = main_mod.hash_password

    def _hash_y_esperar(clave):
        h = hash_real(clave)
        barrera.wait()
        return h

    monkeypatch.setattr(main_mod, "hash_password", _hash_y_esperar)
    respuestas = [None] * len(altas)

    def _uno(i, email, token):
        cliente = TestClient(app, raise_server_exceptions=False)
        respuestas[i] = _registrar(email, token, cliente=cliente)

    hilos = [threading.Thread(target=_uno, args=(i, e, t)) for i, (e, t) in enumerate(altas)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=120)
    assert all(not h.is_alive() for h in hilos), "un registro quedó colgado"
    return sorted((r.status_code, r.json().get("detail", "")) for r in respuestas)


def test_carrera_dos_registros_con_la_misma_invitacion(monkeypatch):
    est = Estudio()
    email = _email()
    tok = est.invitar_ok(email)
    resultado = _carrera(monkeypatch, [(email, tok), (email, tok)])
    assert [s for s, _ in resultado] == [200, 400], resultado
    assert "ya fue usada" in resultado[1][1]
    assert len(_usuarios(email)) == 1
    assert _usuarios(email)[0][1] == est.org_id
    assert _invitacion(tok)["status"] == "accepted"


def test_carrera_dos_invitaciones_por_el_ultimo_lugar(monkeypatch):
    _tope(monkeypatch, 3)
    est = Estudio()
    a, b = _email(), _email()
    tok_a, tok_b = est.invitar_ok(a), est.invitar_ok(b)
    _tope(monkeypatch, 2)  # queda un solo lugar
    resultado = _carrera(monkeypatch, [(a, tok_a), (b, tok_b)])
    assert [s for s, _ in resultado] == [200, 400], resultado
    assert "los 2 usuarios" in resultado[1][1]
    assert len(_miembros(est.org_id)) == 2
    estados = sorted([_invitacion(tok_a)["status"], _invitacion(tok_b)["status"]])
    assert estados == ["accepted", "pending"]


# ---------------------------------------------------------------- email que el registro no acepta

@pytest.mark.parametrize("malo", ["ana@estudio", "josé@x.com", "a b@x.com", "@x.com", "ana@.com",
                                  "a" * 95 + "@x.com"])
def test_invitar_un_email_que_el_registro_rechaza_400_sin_ocupar_lugar(monkeypatch, malo):
    """La invitación fija el email (ORG-1b): si el registro no lo acepta, nadie puede usarla
    y ocuparía un lugar 7 días. Se rechaza al invitar, con el mismo criterio que el registro."""
    _tope(monkeypatch, 2)
    est = Estudio()
    r = est.invitar(malo)
    assert r.status_code == 400, r.text
    assert "formato" in r.json()["detail"], r.text
    # No quedó pendiente: el único lugar libre sigue libre.
    est.invitar_ok(_email())


def test_todo_email_que_se_puede_invitar_se_puede_registrar(monkeypatch):
    _tope(monkeypatch, 10)
    est = Estudio()
    for bueno in ("Ana.Perez+cdi@Mi-Estudio.com.ar", " x_y%z@a.io "):
        tok = est.invitar_ok(bueno)
        assert _registrar(bueno.strip(), tok).status_code == 200


# ================================================================ 5. un email, una cuenta (D40)
# Al invitar, un email que ya tiene cuenta da 400 y no ocupa lugar, con la
# misma respuesta si la cuenta es de este estudio, de otro o de ninguno. Al
# registrarse con una invitación, las otras pendientes de ese email en ese
# estudio quedan usadas.

YA_TIENE_CUENTA = "Ese email ya tiene una cuenta en CDI y no se puede invitar como miembro nuevo."


def _pendientes(org_id, email):
    async def q(s):
        res = await s.execute(select(Invitation.token).where(
            Invitation.org_id == org_id, Invitation.email == email, Invitation.status == "pending"))
        return [t for (t,) in res.all()]
    return _db(q)


@pytest.mark.parametrize("donde", ["este estudio", "otro estudio", "sin estudio", "vieja en mayusculas"])
def test_invitar_un_email_que_ya_tiene_cuenta_400_sin_ocupar_lugar(monkeypatch, donde):
    _tope(monkeypatch, 3)
    est = Estudio()
    email = _email()
    if donde == "este estudio":
        assert _registrar(email, est.invitar_ok(email)).status_code == 200
    elif donde == "otro estudio":
        otro = Estudio()
        assert _registrar(email, otro.invitar_ok(email)).status_code == 200
    else:
        r = TestClient(app).post("/auth/register", json={
            "username": _azar("o1u_"), "password": CLAVE, "email": email})
        assert r.status_code == 200, r.text
    if donde == "vieja en mayusculas":
        # Una cuenta de antes de EMAIL-1 puede tener el email con mayúsculas.
        async def q(s):
            await s.execute(update(User).where(User.email == email).values(email=email.upper()))
        _db(q)
        assert _usuarios(email.upper()) != []
    r = est.invitar(f" {email.upper()} ")
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == YA_TIENE_CUENTA, r.text
    assert _pendientes(est.org_id, email) == []
    # Los lugares libres siguen libres, y no hay uno más.
    for _ in range(3 - len(_miembros(est.org_id))):
        est.invitar_ok(_email())
    assert est.invitar(_email()).status_code == 400


def test_registrarse_con_una_invitacion_usa_las_otras_del_mismo_email(zona):
    est, otro = Estudio(), Estudio()
    email = _email()
    tok1, tok2 = est.invitar_ok(email), est.invitar_ok(email.upper())
    de_otro_email = est.invitar_ok(_email())
    de_otro_estudio = otro.invitar_ok(email)
    assert _registrar(email, tok2).status_code == 200
    assert _invitacion(tok1)["status"] == "accepted"
    r = _validar(tok1)
    assert r.status_code == 400 and "ya fue usada" in r.json()["detail"], r.text
    # Sólo las de ese email en ese estudio.
    assert _invitacion(de_otro_email)["status"] == "pending"
    assert _invitacion(de_otro_estudio)["status"] == "pending"



def test_registrarse_usa_tambien_una_vieja_con_mayusculas_y_espacios(zona):
    """Una invitación guardada antes de EMAIL-1 puede tener el email con
    mayúsculas o espacios, y el registro la acepta igual: también queda usada."""
    est = Estudio()
    email = _email()
    vieja = est.invitar_ok(email)
    _cambiar_invitacion(vieja, email=f"  {email.upper()} ")
    assert _registrar(email, est.invitar_ok(email)).status_code == 200
    assert _invitacion(vieja)["status"] == "accepted"

def test_si_el_alta_no_entra_las_otras_del_mismo_email_siguen_pendientes(zona, monkeypatch):
    _tope(monkeypatch, 3)
    est = Estudio()
    a, b = _email(), _email()
    tok_a1, tok_a2, tok_b = est.invitar_ok(a), est.invitar_ok(a), est.invitar_ok(b)
    _tope(monkeypatch, 2)
    assert _registrar(b, tok_b).status_code == 200
    r = _registrar(a, tok_a1)
    assert r.status_code == 400 and "los 2 usuarios" in r.json()["detail"], r.text
    assert sorted(_pendientes(est.org_id, a)) == sorted([tok_a1, tok_a2])


def test_el_sacado_no_vuelve_a_entrar_con_otra_invitacion_vieja(zona):
    """Devolución de la PM (17:05), el recorrido entero: dos invitaciones al
    mismo email, entra con la primera, el dueño lo saca, se cambia el email en
    el perfil y prueba con la segunda."""
    est = Estudio()
    email = _email()
    tok1, tok2 = est.invitar_ok(email), est.invitar_ok(email)
    sacado = _azar("o1u_")
    suyo = TestClient(app)
    assert _registrar(email, tok1, username=sacado, cliente=suyo).status_code == 200
    assert est.quitar(sacado).status_code == 200
    r = suyo.put("/api/user/profile", json={"email": _email(), "current_password": CLAVE})
    assert r.status_code == 200, r.text
    assert _usuarios(email) == []  # el email invitado quedó libre
    r = _registrar(email, tok2)
    assert r.status_code == 400 and "ya fue usada" in r.json()["detail"], r.text
    assert _usuarios(email) == []
    assert _miembros(est.org_id) == [est.dueno]


def test_carrera_dos_registros_con_dos_invitaciones_del_mismo_email(monkeypatch):
    est = Estudio()
    email = _email()
    tok1, tok2 = est.invitar_ok(email), est.invitar_ok(email)
    resultado = _carrera(monkeypatch, [(email, tok1), (email, tok2)])
    assert [s for s, _ in resultado] == [200, 400], resultado
    assert "ya fue usada" in resultado[1][1]
    assert len(_usuarios(email)) == 1
    assert {_invitacion(tok1)["status"], _invitacion(tok2)["status"]} == {"accepted"}


def test_dos_pendientes_al_mismo_email_entra_con_una_y_la_otra_no_ocupa_lugar(monkeypatch):
    """El caso de la PM (17:05, agregado 3). Con la regla 2 de la D40 la otra
    queda usada, así que este caso ya no mira la resta de los miembros: la
    mira el siguiente."""
    _tope(monkeypatch, 3)
    est = Estudio()
    email = _email()
    est.invitar_ok(email)
    assert _registrar(email, est.invitar_ok(email)).status_code == 200
    est.invitar_ok(_email())  # dueño + miembro + esta: lleno
    assert est.invitar(_email()).status_code == 400


def test_una_pendiente_al_email_de_un_miembro_no_ocupa_lugar(monkeypatch):
    """La pendiente que la D40 no usa: un miembro se cambia el email en el
    perfil al de una invitación pendiente. Nadie la puede usar (el email ya
    tiene cuenta) y la persona ya cuenta como miembro: no ocupa otro lugar."""
    _tope(monkeypatch, 3)
    est = Estudio()
    email, nuevo = _email(), _email()
    miembro = TestClient(app)
    assert _registrar(email, est.invitar_ok(email), cliente=miembro).status_code == 200
    est.invitar_ok(nuevo)  # dueño + miembro + pendiente: lleno
    r = miembro.put("/api/user/profile", json={"email": nuevo, "current_password": CLAVE})
    assert r.status_code == 200, r.text
    assert _pendientes(est.org_id, nuevo)  # sigue pendiente
    est.invitar_ok(_email())  # el lugar que la pendiente no ocupa
    assert est.invitar(_email()).status_code == 400


# ================================================================ 6. guardas de invitar, validar y sacar

def _sin_estudio(email=None):
    """Una cuenta registrada sin invitación, con su sesión en el cliente que devuelve."""
    cliente, usuario = TestClient(app), _azar("o1u_")
    r = cliente.post("/auth/register", json={"username": usuario, "password": CLAVE,
                                             "email": email or _email()})
    assert r.status_code == 200, r.text
    return cliente, usuario


def _miembro(est, usuario=None):
    """Un miembro nuevo del estudio, con su sesión en el cliente que devuelve."""
    cliente, email = TestClient(app), _email()
    r = _registrar(email, est.invitar_ok(email), username=usuario, cliente=cliente)
    assert r.status_code == 200, r.text
    return cliente, email


def test_invitar_o_sacar_sin_estudio_400():
    cliente, _ = _sin_estudio()
    for r in (cliente.post("/api/organizations/invite", json={"email": _email()}),
              cliente.delete(f"/api/organizations/members/{_azar('o1u_')}")):
        assert r.status_code == 400, r.text
        assert r.json()["detail"] == "No pertenecés a un estudio"


def test_un_miembro_no_puede_invitar_403():
    est = Estudio()
    cliente, _ = _miembro(est)
    email = _email()
    r = cliente.post("/api/organizations/invite", json={"email": email})
    assert r.status_code == 403, r.text
    assert _pendientes(est.org_id, email) == []


def test_la_invitacion_vence_a_los_7_dias():
    r = Estudio().invitar(_email())
    assert r.status_code == 200, r.text
    vence = datetime.fromisoformat(r.json()["expires_at"])
    vence = vence if vence.tzinfo else vence.replace(tzinfo=timezone.utc)
    assert abs(vence - (datetime.now(timezone.utc) + timedelta(days=7))) < timedelta(minutes=1)


def test_validar_con_el_estudio_borrado_404():
    """Sólo en SQLite: en Postgres la clave foránea no deja borrar el estudio con invitaciones."""
    tok = Estudio().invitar_ok(_email())
    _cambiar_invitacion(tok, org_id=str(uuid.uuid4()))
    r = TestClient(app, raise_server_exceptions=False).get(f"/api/invitations/{tok}")
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "El estudio ya no existe"


def test_sacar_a_alguien_de_otro_estudio_404_y_sigue_en_el_suyo():
    est, otro = Estudio(), Estudio()
    usuario = _azar("o1u_")
    _, email = _miembro(otro, usuario)
    r = est.quitar(usuario)
    assert r.status_code == 404, r.text
    assert _usuarios(email) == [(usuario, otro.org_id)]


def test_sacar_no_borra_al_usuario():
    est = Estudio()
    usuario = _azar("o1u_")
    _, email = _miembro(est, usuario)
    assert est.quitar(usuario).status_code == 200
    assert _usuarios(email) == [(usuario, None)]
    r = TestClient(app).post("/auth/login", json={"username": usuario, "password": CLAVE})
    assert r.status_code == 200, r.text


def test_el_duenio_no_se_saca_a_si_mismo_y_el_estudio_queda_igual(monkeypatch):
    """La guarda va antes de Mercado Pago: un dueño con la suscripción pendiente no la pierde.
    Con otras mayúsculas o espacios también es el dueño: si la búsqueda los ignorara, la guarda no lo vería."""
    est = Estudio()
    _miembro(est)
    suscripcion = f"pend-{est.dueno}"

    async def con_suscripcion(s):
        await s.execute(update(User).where(User.username == est.dueno).values(mp_preapproval_id=suscripcion))
    _db(con_suscripcion)
    a_mp = []
    for funcion in ("_leer_suscripcion_mp", "_cancelar_suscripcion_mp"):
        monkeypatch.setattr(main_mod, funcion, lambda *_, f=funcion: a_mp.append(f) or "pending")

    def estado():
        async def q(s):
            dueno = select(Organization.owner_username).where(Organization.id == est.org_id)
            sus = select(User.mp_preapproval_id).where(User.username == est.dueno)
            return (await s.execute(dueno)).scalar_one(), (await s.execute(sus)).scalar_one()
        return _db(q), _miembros(est.org_id)

    antes = estado()
    assert antes[0] == (est.dueno, suscripcion) and est.dueno in antes[1] and len(antes[1]) == 2
    guarda = (400, "No podés removerte a vos mismo del estudio")
    parecidos = {guarda, (404, "Ese usuario no es miembro del estudio")}
    for nombre in (est.dueno, est.dueno.upper(), f" {est.dueno}", f"{est.dueno} "):
        r = est.quitar(nombre)
        assert (r.status_code, r.json().get("detail")) in ({guarda} if nombre == est.dueno else parecidos), (nombre, r.text)
        assert (estado(), a_mp) == (antes, []), nombre


def test_mine_lista_sólo_los_miembros_del_estudio_y_quién_es_dueño():
    est, otro = Estudio(), Estudio()
    usuario = _azar("o1u_")
    cliente, _ = _miembro(est, usuario)
    _miembro(otro)
    for sesion, es_dueno in ((est.c, True), (cliente, False)):
        r = sesion.get("/api/organizations/mine")
        assert r.status_code == 200, r.text
        org = r.json()["organization"]
        assert org["is_owner"] is es_dueno
        assert sorted((m["username"], m["is_owner"]) for m in org["members"]) == sorted(
            [(est.dueno, True), (usuario, False)])


@pytest.mark.parametrize("como", ["sin link", "con la invitacion de otro estudio", "perfil",
                                  "vieja en mayusculas"])
def test_una_pendiente_cuyo_email_ya_tiene_cuenta_no_ocupa_lugar(monkeypatch, como):
    _tope(monkeypatch, 3)
    est = Estudio()
    email = _email()
    est.invitar_ok(email)
    est.invitar_ok(_email())  # dueño + 2 pendientes: lleno
    if como == "con la invitacion de otro estudio":
        assert _registrar(email, Estudio().invitar_ok(email)).status_code == 200
    elif como == "perfil":
        cliente, _ = _sin_estudio()
        r = cliente.put("/api/user/profile", json={"email": email, "current_password": CLAVE})
        assert r.status_code == 200, r.text
    else:
        _sin_estudio(email)
    if como == "vieja en mayusculas":
        async def q(s):
            await s.execute(update(User).where(User.email == email).values(email=email.upper()))
        _db(q)
    assert _pendientes(est.org_id, email)  # sigue pendiente, pero nadie la puede usar
    est.invitar_ok(_email())  # el lugar que la pendiente no ocupa
    assert est.invitar(_email()).status_code == 400


@pytest.mark.parametrize("estado", ["expired", "pending"])
def test_una_invitacion_vencida_sigue_vencida_cuando_entra_con_otra(zona, estado):
    """Ya marcada, o vencida por fecha sin que nadie la haya validado."""
    est = Estudio()
    email = _email()
    vencida, vigente = est.invitar_ok(email), est.invitar_ok(email)
    _cambiar_invitacion(vencida, status=estado, expires_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    assert _registrar(email, vigente).status_code == 200
    assert _invitacion(vencida)["status"] == estado
    r = _validar(vencida)
    assert r.status_code == 400 and "expiró" in r.json()["detail"], r.text


def test_una_pendiente_a_una_cuenta_con_espacios_ocupa_lugar(monkeypatch):
    """El registro no ve como suya una cuenta guardada con espacios: la
    invitación se puede usar y ocupa su lugar."""
    _tope(monkeypatch, 3)
    est = Estudio()
    email = _email()
    tok = est.invitar_ok(email)
    est.invitar_ok(_email())  # dueño + 2 pendientes: lleno
    _sin_estudio(email)

    async def q(s):
        await s.execute(update(User).where(User.email == email).values(email=f" {email} "))
    _db(q)
    assert est.invitar(_email()).status_code == 400
    assert _registrar(email, tok).status_code == 200


def test_con_el_estudio_lleno_un_email_con_cuenta_dice_que_ya_tiene_cuenta(monkeypatch):
    _tope(monkeypatch, 2)
    est = Estudio()
    est.invitar_ok(_email())  # lleno
    email = _email()
    _sin_estudio(email)
    r = est.invitar(email)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == YA_TIENE_CUENTA


def test_si_falla_usar_las_otras_invitaciones_no_se_crea_la_cuenta():
    """Usar las otras pendientes del email va en la misma transacción que el alta."""
    est = Estudio()
    email = _email()
    otra, tok = est.invitar_ok(email), est.invitar_ok(email)

    def _falla(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("UPDATE INVITATIONS") and "lower(trim(" in statement:
            raise RuntimeError("falla al usar las otras invitaciones")

    motor = _conn.engine.sync_engine
    event.listen(motor, "before_cursor_execute", _falla)
    try:
        r = _registrar(email, tok, cliente=TestClient(app, raise_server_exceptions=False))
    finally:
        event.remove(motor, "before_cursor_execute", _falla)
    assert r.status_code != 200, r.text
    assert _usuarios(email) == []
    assert sorted(_pendientes(est.org_id, email)) == sorted([otra, tok])
