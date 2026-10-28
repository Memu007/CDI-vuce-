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
