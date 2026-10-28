"""SESION-1 (hallazgo S3 de AUDITORIA-2026-10-06): cambiar o resetear la
contraseña y cerrar sesión revocan de verdad las sesiones que corresponden, una
sesión revocada no vuelve y cambiar el email pide la contraseña actual.

El mecanismo es el único que ya había: `users.active_jti` guarda el jti del
token vigente y `get_current_user` rechaza cualquier otro. Antes, cambiar o
resetear la clave lo ponía en NULL, y NULL quiere decir «aceptar cualquier
token» (compatibilidad con usuarios de antes de la columna): revocar
resucitaba todas las sesiones viejas. Cerrar sesión sólo borraba la cookie.

Acá corre en SQLite; el mismo recorrido contra un servidor real, en Postgres y
en SQLite, está en `scripts/testing/sesion1_motores.py`.
"""
import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

import proyecto_maria.database.connection as conn
import proyecto_maria.main as main_mod
from proyecto_maria.database.models import PasswordResetToken, User
from proyecto_maria.main import app

CLAVE, CLAVE2, CLAVE3 = "Clave-sintetica-1!", "Clave-sintetica-2!", "Clave-sintetica-3!"


@pytest.fixture(scope="module", autouse=True)
def _tablas():
    """El lifespan crea las tablas y corre las migraciones (como en
    test_billing_autoservicio.py)."""
    with TestClient(app):
        pass
    yield


@pytest.fixture(autouse=True)
def _sin_limites(monkeypatch):
    monkeypatch.setenv("EMAIL_VERIFICATION_REQUIRED", "false")
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    main_mod.login_attempts.clear()
    main_mod.reset_attempts.clear()
    yield


def _http():
    return TestClient(app)


def _consulta(fn):
    async def _correr():
        async with conn.AsyncSessionLocal() as s:
            r = await fn(s)
            await s.commit()
            return r
    return asyncio.run(_correr())


def _fila(username):
    async def _f(s):
        return (await s.execute(select(User).where(User.username == username))).scalars().first()
    return _consulta(_f)


def _poner_active_jti(username, valor):
    async def _f(s):
        u = (await s.execute(select(User).where(User.username == username))).scalars().first()
        u.active_jti = valor
    _consulta(_f)


def _usuario():
    """Registra un usuario propio de la prueba y devuelve (username, email)."""
    u = "ses1_" + uuid.uuid4().hex[:10]
    mail = f"{u}@example.com"
    r = _http().post("/auth/register", json={"username": u, "password": CLAVE, "email": mail, "name": "Ses"})
    assert r.status_code in (200, 201), r.text
    return u, mail


def _login(u, clave=CLAVE):
    r = _http().post("/auth/login", json={"username": u, "password": clave})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _bearer(t):
    return {"Authorization": f"Bearer {t}"}


def _entra(t):
    """Código de una ruta protegida con ese token (200 entra, 401 no)."""
    return _http().get("/api/user/profile", headers=_bearer(t)).status_code


def _cliente_con_cookie(u, clave=CLAVE):
    """Un navegador: login que deja la cookie access_token. Devuelve el
    cliente y el token que quedó en la cookie."""
    c = _http()
    r = c.post("/auth/login", json={"username": u, "password": clave})
    assert r.status_code == 200, r.text
    return c, r.json()["access_token"]


# --- cambiar la contraseña -------------------------------------------------

def test_cambiar_clave_revoca_las_otras_y_conserva_la_propia():
    u, _ = _usuario()
    vieja, propia = _login(u), _login(u)
    _poner_active_jti(u, None)  # las dos valen, como un usuario de antes de la columna
    assert (_entra(vieja), _entra(propia)) == (200, 200)

    r = _http().post("/api/user/change-password", headers=_bearer(propia),
                     json={"current_password": CLAVE, "new_password": CLAVE2})
    assert r.status_code == 200, r.text
    assert _entra(vieja) == 401, "la otra sesión sigue entrando después de cambiar la clave"
    assert _entra(propia) == 200, "cambiar la clave cerró la sesión de quien la cambió"
    assert _fila(u).active_jti is not None

    nueva = _login(u, CLAVE2)
    assert _entra(nueva) == 200
    assert _entra(vieja) == 401


def test_cambiar_clave_con_cookie_conserva_el_navegador():
    u, _ = _usuario()
    otra = _login(u)
    nav, _ = _cliente_con_cookie(u)
    _poner_active_jti(u, None)
    r = nav.post("/api/user/change-password", json={"current_password": CLAVE, "new_password": CLAVE2})
    assert r.status_code == 200, r.text
    assert nav.get("/api/user/profile").status_code == 200
    assert _entra(otra) == 401


def test_cambiar_clave_mal_no_revoca_nada():
    u, _ = _usuario()
    t = _login(u)
    antes = _fila(u).active_jti
    r = _http().post("/api/user/change-password", headers=_bearer(t),
                     json={"current_password": "otra-cosa-1!", "new_password": CLAVE2})
    assert r.status_code == 401
    assert _fila(u).active_jti == antes
    assert _entra(t) == 200


# --- resetear la contraseña ------------------------------------------------

def _resetear(u, mail, nueva):
    assert _http().post("/auth/request-password-reset", json={"email": mail}).status_code == 200

    async def _token(s):
        q = select(PasswordResetToken).where(PasswordResetToken.user_username == u,
                                              PasswordResetToken.is_used == False)  # noqa: E712
        return (await s.execute(q)).scalars().first().token
    r = _http().post("/auth/reset-password", json={"token": _consulta(_token), "new_password": nueva})
    assert r.status_code == 200, r.text


def test_resetear_clave_revoca_todas_las_sesiones():
    u, mail = _usuario()
    vieja, ultima = _login(u), _login(u)
    _poner_active_jti(u, None)
    _resetear(u, mail, CLAVE2)
    assert _entra(ultima) == 401, "la sesión vigente sigue entrando después del reset"
    assert _entra(vieja) == 401, "una sesión vieja volvió a entrar después del reset"
    assert _fila(u).active_jti is not None

    nueva = _login(u, CLAVE2)
    assert _entra(nueva) == 200
    assert (_entra(vieja), _entra(ultima)) == (401, 401)


# --- cerrar sesión -------------------------------------------------------

@pytest.mark.parametrize("ruta", ["/auth/logout", "/logout"])
def test_cerrar_sesion_con_bearer_revoca_la_propia(ruta):
    u, _ = _usuario()
    t = _login(u)
    r = _http().post(ruta, headers=_bearer(t))
    assert r.status_code == 200
    assert _entra(t) == 401, f"{ruta}: el token sigue entrando después de cerrar sesión"
    nueva = _login(u)
    assert _entra(nueva) == 200
    assert _entra(t) == 401


@pytest.mark.parametrize("ruta", ["/auth/logout", "/logout"])
def test_cerrar_sesion_con_cookie_revoca_la_propia(ruta):
    u, _ = _usuario()
    nav, t = _cliente_con_cookie(u)
    assert nav.post(ruta).status_code == 200
    assert _entra(t) == 401, f"{ruta}: la cookie robada sigue entrando después de cerrar sesión"


@pytest.mark.parametrize("ruta", ["/auth/logout", "/logout"])
def test_cerrar_sesion_con_un_token_revocado_no_saca_la_vigente(ruta):
    u, _ = _usuario()
    vieja, vigente = _login(u), _login(u)
    assert _entra(vieja) == 401
    assert _http().post(ruta, headers=_bearer(vieja)).status_code == 200
    assert _entra(vigente) == 200, f"{ruta}: un token ya revocado cerró la sesión vigente"


def test_cerrar_sesion_sin_token_o_con_basura_da_200():
    assert _http().post("/auth/logout").status_code == 200
    assert _http().post("/logout", headers=_bearer("no-es-un-jwt")).status_code == 200


# --- una revocada no vuelve -------------------------------------------------

def test_una_sesion_revocada_no_vuelve():
    """Cada acción revoca y ninguna de las siguientes devuelve la vida a las
    anteriores. Se mira antes del último login, que por sí solo ya revoca."""
    u, mail = _usuario()
    a = _login(u)
    b = _login(u)                                     # a, revocada por el login
    _http().post("/auth/logout", headers=_bearer(b))  # b, por cerrar sesión
    assert (_entra(a), _entra(b)) == (401, 401)
    c = _login(u)
    r = _http().post("/api/user/change-password", headers=_bearer(c),
                     json={"current_password": CLAVE, "new_password": CLAVE2})
    assert r.status_code == 200
    assert (_entra(a), _entra(b), _entra(c)) == (401, 401, 200)
    _resetear(u, mail, CLAVE3)                        # c, por el reset
    assert (_entra(a), _entra(b), _entra(c)) == (401, 401, 401)
    _http().post("/logout", headers=_bearer(a))
    _http().post("/auth/logout", headers=_bearer(c))
    assert (_entra(a), _entra(b), _entra(c)) == (401, 401, 401)
    d = _login(u, CLAVE3)
    assert (_entra(a), _entra(b), _entra(c), _entra(d)) == (401, 401, 401, 200)


# --- cambiar el email ------------------------------------------------------

def _put_perfil(t, cuerpo):
    return _http().put("/api/user/profile", headers=_bearer(t), json=cuerpo)


def test_cambiar_email_sin_clave_falla_y_no_cambia_nada():
    u, mail = _usuario()
    t = _login(u)
    r = _put_perfil(t, {"name": "Otro nombre", "email": f"atacante-{u}@example.com"})
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "Para cambiar el email ingresá tu contraseña actual"
    fila = _fila(u)
    assert (fila.email, fila.name) == (mail, "Ses")


def test_cambiar_email_con_clave_equivocada_falla_y_no_cambia_nada():
    u, mail = _usuario()
    t = _login(u)
    r = _put_perfil(t, {"name": "Otro nombre", "email": f"atacante-{u}@example.com",
                        "current_password": "otra-cosa-1!"})
    # 400 y no 401: el frontend toma un 401 como sesión vencida y manda al login.
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "La contraseña actual es incorrecta"
    fila = _fila(u)
    assert (fila.email, fila.name) == (mail, "Ses")


def test_vaciar_el_email_tambien_pide_la_clave():
    u, mail = _usuario()
    t = _login(u)
    r = _put_perfil(t, {"email": ""})
    assert r.status_code == 400
    assert r.json()["detail"] == "Para cambiar el email ingresá tu contraseña actual"
    assert _fila(u).email == mail


def test_cambiar_email_con_la_clave_cambia():
    u, _ = _usuario()
    t = _login(u)
    nuevo = f"{u}-nuevo@example.com"
    r = _put_perfil(t, {"email": nuevo.upper(), "current_password": CLAVE})
    assert r.status_code == 200, r.text
    assert r.json()["profile"]["email"] == nuevo
    assert _fila(u).email == nuevo
    assert _entra(t) == 200


def test_guardar_el_perfil_con_el_mismo_email_no_pide_clave():
    """La pantalla de perfil siempre manda el email: si no cambió (ni por
    mayúsculas ni por espacios), guardar el nombre no pide la clave."""
    u, mail = _usuario()
    t = _login(u)
    r = _put_perfil(t, {"name": "Nuevo", "email": f"  {mail.upper()} "})
    assert r.status_code == 200, r.text
    fila = _fila(u)
    assert (fila.email, fila.name) == (mail, "Nuevo")
