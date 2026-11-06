"""EMAIL-1: el email se busca sin mirar mayúsculas.

Recuperar usuario, recuperar contraseña y el login por email comparaban el
email tal cual: quien escribía `Ana@Ejemplo.test` no encontraba la cuenta de
`ana@ejemplo.test`. El perfil buscaba el duplicado igual, así que dejaba tomar
un email que ya existía con otras mayúsculas. El registro, el alta de estudio
y las invitaciones ya comparaban en minúsculas: acá quedan como guardia.

Las cuentas que ya comparten email con distintas mayúsculas (un «par») no se
tocan. Mientras Emi no decida (D38), el que coincide exacto gana; si ninguno
coincide exacto y hay más de uno, no se manda nada y la respuesta es la misma.

Acá corre en SQLite; el mismo recorrido contra un servidor real, en Postgres y
en SQLite, está en `scripts/testing/email1_motores.py`.
"""
import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

import proyecto_maria.database.connection as conn
import proyecto_maria.main as main_mod
from proyecto_maria.database.models import PasswordResetToken, User
from proyecto_maria.main import app, hash_password

CLAVE = "Clave-sintetica-1!"
RECUPERAR = "/auth/recover-username"
RESET = "/auth/request-password-reset"


@pytest.fixture(scope="module", autouse=True)
def _tablas():
    with TestClient(app):
        pass
    yield


@pytest.fixture(autouse=True)
def _limpio(monkeypatch):
    """Contadores en cero y el correo capturado: `send_email` devuelve False
    (sin SMTP), así la respuesta de desarrollo trae la pista de qué cuenta
    encontró."""
    monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
    from proyecto_maria.core.rate_limit import limiter
    limiter.reset()
    asyncio.run(_sql("delete from limites_auth"))
    enviados = []
    monkeypatch.setattr(main_mod, "send_email", lambda a, asunto, cuerpo: enviados.append((a, cuerpo)) and False)
    yield enviados
    limiter.reset()


async def _sql(consulta, **args):
    async with conn.AsyncSessionLocal() as s:
        await s.execute(text(consulta), args)
        await s.commit()


def _ip():
    h = uuid.uuid4().hex
    return {"X-Forwarded-For": f"2001:db8::{h[:4]}:{h[4:8]}"}


def _nombre():
    return "em1_" + uuid.uuid4().hex[:8]


def _cuenta(email):
    """Crea la cuenta directo en la base: así se arman los pares que el
    registro ya no deja crear."""
    u = _nombre()

    async def _crear():
        async with conn.AsyncSessionLocal() as s:
            s.add(User(username=u, email=email, password=hash_password(CLAVE), name=u,
                       plan="premium", is_verified=True, billing_status="trial", roles=[]))
            await s.commit()
    asyncio.run(_crear())
    return u


def _email_de(u):
    async def _leer():
        async with conn.AsyncSessionLocal() as s:
            return (await s.execute(select(User.email).where(User.username == u))).scalar_one()
    return asyncio.run(_leer())


def _tokens_de(u):
    async def _leer():
        async with conn.AsyncSessionLocal() as s:
            r = await s.execute(select(PasswordResetToken.token).where(PasswordResetToken.user_username == u))
            return set(r.scalars().all())
    return asyncio.run(_leer())


def _token(c, u):
    r = c.post("/auth/login", headers=_ip(), json={"username": u, "password": CLAVE})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _dominio():
    return f"{uuid.uuid4().hex[:8]}.ejemplo.test"


# --- Recuperar usuario y contraseña con otras mayúsculas ---------------------

@pytest.mark.parametrize("guardado, pedido", (
    ("ana@{d}", "Ana@{D}"),          # registrada en minúsculas, escrita con mayúsculas
    ("Beto@{D}", "beto@{d}"),        # cuenta vieja guardada con mayúsculas
    ("caro@{d}", "  CARO@{D}  "),    # con espacios alrededor
))
def test_recuperar_usuario_sin_mayusculas(guardado, pedido, _limpio):
    d = _dominio()
    u = _cuenta(guardado.format(d=d, D=d.upper()))
    with TestClient(app) as c:
        r = c.post(RECUPERAR, headers=_ip(), json={"email": pedido.format(d=d, D=d.upper())})
    assert r.status_code == 200, r.text
    assert r.json().get("dev_username_hint") == u
    # El correo va a la dirección guardada de esa cuenta, no a la escrita.
    assert [a for a, _ in _limpio] == [_email_de(u)]


@pytest.mark.parametrize("guardado, pedido", (
    ("ana@{d}", "Ana@{D}"),
    ("Beto@{D}", "beto@{d}"),
    ("caro@{d}", "  CARO@{D}  "),
))
def test_recuperar_contrasena_sin_mayusculas(guardado, pedido, _limpio):
    d = _dominio()
    u = _cuenta(guardado.format(d=d, D=d.upper()))
    with TestClient(app) as c:
        r = c.post(RESET, headers=_ip(), json={"email": pedido.format(d=d, D=d.upper())})
    assert r.status_code == 200, r.text
    assert r.json().get("dev_token_hint") in _tokens_de(u)
    assert [a for a, _ in _limpio] == [_email_de(u)]


def test_login_por_email_sin_mayusculas():
    d = _dominio()
    u = _cuenta(f"dani@{d}")
    with TestClient(app) as c:
        r = c.post("/auth/login", headers=_ip(), json={"username": f"DANI@{d.upper()}", "password": CLAVE})
    assert r.status_code == 200, r.text
    assert r.json()["user"]["username"] == u


# --- La respuesta no dice si el email existe ---------------------------------

@pytest.mark.parametrize("ruta", (RECUPERAR, RESET))
def test_la_respuesta_no_cambia_exista_o_no(ruta, monkeypatch, _limpio):
    """En producción (sin pistas de desarrollo) la respuesta es la misma para
    un email que existe con otras mayúsculas, uno que no existe y uno que
    coincide con un par sin coincidir exacto."""
    monkeypatch.setattr(main_mod, "IS_PRODUCTION", True)
    monkeypatch.setattr(main_mod, "IS_TESTING", False)
    monkeypatch.setenv("FRONTEND_URL", "https://cdi.ejemplo.test")
    d = _dominio()
    _cuenta(f"eva@{d}")
    _cuenta(f"Par@{d}")
    _cuenta(f"PAR@{d}")
    with TestClient(app) as c:
        respuestas = [c.post(ruta, headers=_ip(), json={"email": e})
                      for e in (f"EVA@{d}", f"nadie@{d}", f"par@{d}")]
    assert {(r.status_code, r.text) for r in respuestas} == {(respuestas[1].status_code, respuestas[1].text)}
    assert respuestas[1].status_code == 200
    # Y efectivamente se mandó sólo el que existe sin ambigüedad.
    assert [a for a, _ in _limpio] == [f"eva@{d}"]


# --- Pares que ya existen: no se tocan y nadie toma la cuenta del otro -------

def _par():
    d = _dominio()
    return d, _cuenta(f"Fede@{d}"), _cuenta(f"FEDE@{d}")


@pytest.mark.parametrize("ruta, pista", ((RECUPERAR, "dev_username_hint"), (RESET, "dev_token_hint")))
def test_par_el_exacto_gana(ruta, pista, _limpio):
    d, a, b = _par()
    with TestClient(app) as c:
        ra = c.post(ruta, headers=_ip(), json={"email": f"Fede@{d}"}).json()
        rb = c.post(ruta, headers=_ip(), json={"email": f"FEDE@{d}"}).json()
    if pista == "dev_username_hint":
        assert (ra[pista], rb[pista]) == (a, b)
    else:
        assert ra[pista] in _tokens_de(a) and rb[pista] in _tokens_de(b)
    # Cada correo va a la dirección de su propia cuenta y nombra sólo a esa.
    assert [x for x, _ in _limpio] == [f"Fede@{d}", f"FEDE@{d}"]
    if pista == "dev_username_hint":
        assert a in _limpio[0][1] and b not in _limpio[0][1]
        assert b in _limpio[1][1] and a not in _limpio[1][1]


@pytest.mark.parametrize("ruta, pista", ((RECUPERAR, "dev_username_hint"), (RESET, "dev_token_hint")))
def test_par_sin_exacto_no_manda_nada(ruta, pista, _limpio):
    d, a, b = _par()
    with TestClient(app) as c:
        r = c.post(ruta, headers=_ip(), json={"email": f"fede@{d}"})
    assert r.status_code == 200 and pista not in r.json(), r.text
    assert _limpio == []
    assert _tokens_de(a) == set() and _tokens_de(b) == set()


@pytest.mark.parametrize("ruta, pista", ((RESET, "dev_token_hint"), (RECUPERAR, "dev_username_hint")))
def test_la_pista_de_dev_solo_en_el_entorno_de_prueba(ruta, pista, monkeypatch, _limpio):
    """Sin SMTP, la pista de desarrollo (el token de reset o el usuario) vuelve
    en la respuesta sólo en el entorno de prueba (RESET-2). Si ENVIRONMENT
    falta, no es producción pero tampoco es prueba: el token no se filtra."""
    d = _dominio()
    _cuenta(f"gise@{d}")
    # ENVIRONMENT ausente o 'development': ni producción ni prueba.
    monkeypatch.setattr(main_mod, "IS_PRODUCTION", False)
    monkeypatch.setattr(main_mod, "IS_TESTING", False)
    with TestClient(app) as c:
        r = c.post(ruta, headers=_ip(), json={"email": f"gise@{d}"})
    assert r.status_code == 200, r.text
    assert pista not in r.json(), r.json()


def test_par_login():
    """El exacto entra con su clave; sin exacto, el par no entra por email
    (con el usuario sí)."""
    d, a, b = _par()
    with TestClient(app) as c:
        exacto = c.post("/auth/login", headers=_ip(), json={"username": f"FEDE@{d}", "password": CLAVE})
        ambiguo = c.post("/auth/login", headers=_ip(), json={"username": f"fede@{d}", "password": CLAVE})
        por_usuario = c.post("/auth/login", headers=_ip(), json={"username": a, "password": CLAVE})
    assert exacto.status_code == 200 and exacto.json()["user"]["username"] == b
    assert ambiguo.status_code == 401
    assert por_usuario.status_code == 200


def test_par_el_perfil_se_guarda_sin_tocar_el_email():
    """La pantalla de perfil siempre manda el email: guardar el nombre de una
    cuenta del par no puede fallar por el email de la otra ni cambiar el suyo."""
    d, a, b = _par()
    with TestClient(app) as c:
        r = c.put("/api/user/profile", headers=_token(c, a), json={"name": "Nuevo", "email": f"Fede@{d}"})
    assert r.status_code == 200, r.text
    assert (_email_de(a), _email_de(b)) == (f"Fede@{d}", f"FEDE@{d}")


# --- Nadie crea un email que ya existe con otras mayúsculas ------------------

@pytest.mark.parametrize("existente", ("gabi@{d}", "Gabi@{D}"))
def test_perfil_no_toma_un_email_ajeno(existente):
    d = _dominio()
    dueno = _cuenta(existente.format(d=d, D=d.upper()))
    otro = _cuenta(f"otro@{d}")
    with TestClient(app) as c:
        r = c.put("/api/user/profile", headers=_token(c, otro),
                  json={"email": f"GABI@{d.upper()}", "current_password": CLAVE})
    assert r.status_code == 400, r.text
    assert _email_de(otro) == f"otro@{d}"
    assert _email_de(dueno) == existente.format(d=d, D=d.upper())


def test_perfil_cambiar_a_un_email_libre_sigue_andando():
    d = _dominio()
    u = _cuenta(f"hugo@{d}")
    with TestClient(app) as c:
        r = c.put("/api/user/profile", headers=_token(c, u),
                  json={"email": f"Hugo.Nuevo@{d}", "current_password": CLAVE})
    assert r.status_code == 200, r.text
    assert _email_de(u) == f"hugo.nuevo@{d}"


@pytest.mark.parametrize("existente", ("ines@{d}", "Ines@{D}"))
def test_registro_no_crea_un_email_existente(existente):
    d = _dominio()
    _cuenta(existente.format(d=d, D=d.upper()))
    with TestClient(app) as c:
        r = c.post("/auth/register", headers=_ip(),
                   json={"username": _nombre(), "password": CLAVE, "email": f"INES@{d.upper()}", "name": "I"})
    assert r.status_code == 400, r.text


def test_alta_de_estudio_no_crea_un_email_existente():
    d = _dominio()
    _cuenta(f"Juan@{d}")
    with TestClient(app) as c:
        r = c.post("/api/organizations/create", headers=_ip(),
                   json={"name": "Estudio", "username": _nombre(), "password": CLAVE, "email": f"juan@{d}"})
    assert r.status_code == 400, r.text


def test_registro_de_prueba_con_reemplazo_archiva_todo_el_par(monkeypatch):
    """Con REGISTER_TEST_EMAIL_REPLACE el registro libera un email de prueba ya
    usado. Si el email era de un par, tiene que liberar las dos cuentas: si
    libera una sola, la nueva queda con el email de la otra."""
    d = _dominio()
    a, b = _cuenta(f"Kiki@{d}"), _cuenta(f"kiki@{d}")
    monkeypatch.setenv("REGISTER_TEST_EMAIL_REPLACE", "true")
    monkeypatch.setenv("REGISTER_TEST_EMAILS", f"kiki@{d}")
    with TestClient(app) as c:
        r = c.post("/auth/register", headers=_ip(),
                   json={"username": _nombre(), "password": CLAVE, "email": f"KIKI@{d}", "name": "K"})
    assert r.status_code == 200, r.text
    assert "+archivado-" in _email_de(a) and "+archivado-" in _email_de(b)


def test_invitacion_a_un_miembro_con_otras_mayusculas(monkeypatch):
    with TestClient(app) as c:
        dueno = _nombre()
        d = _dominio()
        r = c.post("/api/organizations/create", headers=_ip(),
                   json={"name": "Estudio", "username": dueno, "password": CLAVE, "email": f"lia@{d}"})
        assert r.status_code == 200, r.text
        # Una cuenta vieja: el alta de hoy guarda en minúsculas, ésta no.
        asyncio.run(_sql("update users set email = :e where username = :u", e=f"Lia@{d}", u=dueno))
        r = c.post("/api/organizations/invite", headers=_token(c, dueno), json={"email": f"LIA@{d.upper()}"})
    assert r.status_code == 400 and "miembro" in r.text, r.text


def test_registro_con_invitacion_acepta_otras_mayusculas():
    with TestClient(app) as c:
        dueno = _nombre()
        d = _dominio()
        r = c.post("/api/organizations/create", headers=_ip(),
                   json={"name": "Estudio", "username": dueno, "password": CLAVE, "email": f"dueno@{d}"})
        assert r.status_code == 200, r.text
        r = c.post("/api/organizations/invite", headers=_token(c, dueno), json={"email": f"mili@{d}"})
        assert r.status_code == 200, r.text
        token = r.json()["invite_link"].split("invite=")[1]
        r = c.post("/auth/register", headers=_ip(),
                   json={"username": _nombre(), "password": CLAVE, "email": f"Mili@{d.upper()}", "name": "M",
                         "invite_token": token})
    assert r.status_code == 200, r.text
