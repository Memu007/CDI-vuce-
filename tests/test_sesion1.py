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
from sqlalchemy import select, text

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
    asyncio.run(_vaciar_limites())
    yield


async def _vaciar_limites():
    async with conn.AsyncSessionLocal() as s:
        await s.execute(text("delete from limites_auth"))
        await s.commit()


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


def _poner(username, **campos):
    async def _f(s):
        u = (await s.execute(select(User).where(User.username == username))).scalars().first()
        for campo, valor in campos.items():
            setattr(u, campo, valor)
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

def test_cambiar_clave_rota_la_sesion_de_quien_la_cambia():
    """La otra sesión y una copia del token de quien cambió quedan afuera; quien
    cambió sigue con el token nuevo de la respuesta."""
    u, _ = _usuario()
    otra, propia = _login(u), _login(u)
    _poner(u, active_jti=None)  # las dos valen, como un usuario de antes de la columna
    assert (_entra(otra), _entra(propia)) == (200, 200)

    r = _http().post("/api/user/change-password", headers=_bearer(propia),
                     json={"current_password": CLAVE, "new_password": CLAVE2})
    assert r.status_code == 200, r.text
    nueva = r.json()["access_token"]
    assert (_entra(otra), _entra(propia), _entra(nueva)) == (401, 401, 200)
    assert _entra(_login(u, CLAVE2)) == 200
    assert _entra(propia) == 401


def test_cambiar_clave_con_cookie_conserva_el_navegador():
    u, _ = _usuario()
    otra = _login(u)
    nav, copia = _cliente_con_cookie(u)
    _poner(u, active_jti=None)
    r = nav.post("/api/user/change-password", json={"current_password": CLAVE, "new_password": CLAVE2})
    assert r.status_code == 200, r.text
    assert nav.get("/api/user/profile").status_code == 200
    assert (_entra(otra), _entra(copia)) == (401, 401), "la copia de la cookie sigue entrando"


def test_cambiar_clave_mal_no_revoca_nada():
    u, _ = _usuario()
    t = _login(u)
    antes = _fila(u).active_jti
    r = _http().post("/api/user/change-password", headers=_bearer(t),
                     json={"current_password": "otra-cosa-1!", "new_password": CLAVE2})
    # 400 y no 401: el frontend toma un 401 como sesión vencida y manda al login.
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == "La contraseña actual es incorrecta"
    assert _fila(u).active_jti == antes
    assert _entra(t) == 200


def test_el_login_no_pisa_una_clave_que_cambio_mientras_validaba(monkeypatch):
    """Un reset entra entre que el login validó la clave y escribe el jti: el
    login no abre sesión con la clave vieja ni pisa el jti del reset."""
    from anyio.from_thread import run as en_el_loop
    u, _ = _usuario()
    real = main_mod.verify_password

    async def _reset_en_el_medio(s):
        fila = (await s.execute(select(User).where(User.username == u))).scalars().first()
        fila.password, fila.active_jti = "hash-de-otra-clave", "jti-del-reset"

    def validar(clave, hash_guardado):
        ok = real(clave, hash_guardado)
        en_el_loop(_en_sesion, _reset_en_el_medio)
        return ok

    monkeypatch.setattr(main_mod, "verify_password", validar)
    r = _http().post("/auth/login", json={"username": u, "password": CLAVE})
    assert r.status_code == 401, r.text
    assert "access_token" not in r.cookies
    assert _fila(u).active_jti == "jti-del-reset"


async def _en_sesion(fn):
    async with conn.AsyncSessionLocal() as s:
        await fn(s)
        await s.commit()


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
    _poner(u, active_jti=None)
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
    r = _http().post("/api/user/change-password", headers=_bearer(_login(u)),
                     json={"current_password": CLAVE, "new_password": CLAVE2})
    assert r.status_code == 200
    c = r.json()["access_token"]
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


def test_perfil_pide_la_clave_aunque_el_email_estuviera_vacio():
    for antes in (None, ""):
        u, _ = _usuario()
        t = _login(u)
        _poner(u, email=antes)
        r = _put_perfil(t, {"email": f"atacante-{u}@example.com"})
        assert r.status_code == 400, (antes, r.text)
        assert _fila(u).email == antes


def test_perfil_rechaza_una_clave_actual_que_no_es_texto():
    u, mail = _usuario()
    t = _login(u)
    for clave in (123, ["x"], {"a": 1}, True):
        r = _put_perfil(t, {"email": f"otro-{u}@example.com", "current_password": clave})
        assert r.status_code == 400, (clave, r.text)
        assert r.json()["detail"] == "Para cambiar el email ingresá tu contraseña actual", clave
    assert _fila(u).email == mail


def test_la_clave_actual_tiene_tope_de_intentos():
    """Cinco intentos con la clave equivocada, entre el perfil y el cambio de
    clave, cuentan juntos: el siguiente da 429 aunque traiga la buena."""
    u, mail = _usuario()
    t = _login(u)

    def cambiar_clave(clave):
        return _http().post("/api/user/change-password", headers=_bearer(t),
                            json={"current_password": clave, "new_password": CLAVE2})

    def cambiar_email(clave):
        return _put_perfil(t, {"email": f"otro-{u}@example.com", "current_password": clave})

    fallos = [ruta("otra-cosa-1!").status_code
              for ruta in (cambiar_clave, cambiar_email, cambiar_clave, cambiar_email, cambiar_clave)]
    assert fallos == [400] * 5
    assert (cambiar_clave(CLAVE).status_code, cambiar_email(CLAVE).status_code) == (429, 429)
    assert _fila(u).email == mail
    assert _entra(_login(u)) == 200, "el tope cambió la clave"


# --- un solo lugar decide si un token vale -----------------------------------

def _token_firmado(payload, clave=None):
    import jwt
    from datetime import datetime, timedelta, timezone
    datos = {"exp": datetime.now(timezone.utc) + timedelta(minutes=5), **payload}
    return jwt.encode(datos, clave or main_mod.SECRET_KEY, algorithm=main_mod.ALGORITHM)


def _rutas_que_leen_la_sesion(token):
    """Qué contesta cada lugar que lee la sesión, con el token en el header y
    en la cookie: (perfil, /auth/me, telemetría) para cada uno."""
    evento = {"action": "prueba_sesion1", "screen": "t"}
    salida = []
    for por in ("header", "cookie"):
        c = _http()
        headers = {}
        if por == "header":
            headers = _bearer(token)
        else:
            c.cookies.set("access_token", f"Bearer {token}")
        salida.append((c.get("/api/user/profile", headers=headers).status_code,
                       c.get("/auth/me", headers=headers).status_code,
                       c.post("/api/ui/event", headers=headers, json=evento).json().get("ok")))
    return salida


def _borrar_eventos(u):
    async def _f(s):
        await s.execute(text("delete from telemetry_events where owner_username = :u"), {"u": u})
    _consulta(_f)


def test_ningun_lugar_acepta_un_token_que_no_es_la_sesion_vigente():
    u, _ = _usuario()
    revocado, vigente = _login(u), _login(u)
    try:
        assert _rutas_que_leen_la_sesion(vigente) == [(200, 200, True)] * 2
        no_valen = {
            "revocado": revocado,
            "otra firma": _token_firmado({"sub": u, "jti": _fila(u).active_jti}, clave="otra-clave-x" * 4),
            "verificación de email": main_mod.build_email_verification_token(u),
        }
        for nombre, token in no_valen.items():
            if nombre != "revocado":
                _poner(u, active_jti=None)  # sin jti, cualquier sesión bien firmada vale
            assert _rutas_que_leen_la_sesion(token) == [(401, 401, False)] * 2, nombre
    finally:
        _borrar_eventos(u)


def test_la_cookie_le_gana_al_header():
    u, _ = _usuario()
    revocado = _login(u)
    nav, vigente = _cliente_con_cookie(u)
    assert nav.get("/api/user/profile", headers=_bearer(revocado)).status_code == 200
    nav.cookies.set("access_token", f"Bearer {revocado}")
    assert nav.get("/api/user/profile", headers=_bearer(vigente)).status_code == 401


def test_verificar_el_email_no_abre_sesion():
    u, _ = _usuario()
    _poner(u, is_verified=False)
    token = main_mod.build_email_verification_token(u)
    for vez in (1, 2):
        c = _http()
        r = c.get("/auth/verify-email", params={"token": token}, follow_redirects=False)
        assert r.status_code in (302, 303, 307), (vez, r.text)
        assert "access_token" not in c.cookies, f"vez {vez}: el link de verificación abrió sesión"
    assert _fila(u).is_verified


# --- cerrar sesión ------------------------------------------------------------

def test_cerrar_sesion_de_un_usuario_sin_jti_revoca():
    u, _ = _usuario()
    t = _login(u)
    _poner(u, active_jti=None)
    assert _http().post("/auth/logout", headers=_bearer(t)).status_code == 200
    assert _entra(t) == 401


def test_cerrar_sesion_borra_la_cookie_aunque_falle_la_base():
    from sqlalchemy.exc import OperationalError

    class _BaseCaida:
        async def execute(self, *a, **k):
            raise OperationalError("select", {}, Exception("base caída"))

        async def commit(self):
            pass

        async def rollback(self):
            pass

    async def _db():
        yield _BaseCaida()

    u, _ = _usuario()
    nav, _ = _cliente_con_cookie(u)
    app.dependency_overrides[main_mod.get_db] = _db
    try:
        r = nav.post("/auth/logout")
    finally:
        app.dependency_overrides.pop(main_mod.get_db, None)
    assert r.status_code == 200, r.text
    assert "access_token" not in nav.cookies


def test_un_solo_lugar_lee_el_token_y_emite_la_cookie():
    """Cualquier otro jwt.decode o cookie de sesión en el producto es un lugar
    más que puede olvidarse de mirar el tipo o el jti."""
    import ast
    import pathlib
    import warnings
    raiz = pathlib.Path(main_mod.__file__).parent
    hallados = []

    def recorrer(nodo, archivo, funcion):
        for hijo in ast.iter_child_nodes(nodo):
            dentro = hijo.name if isinstance(hijo, (ast.FunctionDef, ast.AsyncFunctionDef)) else funcion
            if isinstance(hijo, ast.Call) and isinstance(hijo.func, ast.Attribute):
                f = hijo.func
                if f.attr == "decode" and isinstance(f.value, ast.Name) and f.value.id == "jwt":
                    hallados.append(("jwt.decode", archivo, dentro))
                valores = [*hijo.args, *(k.value for k in hijo.keywords if k.arg == "key")]
                if f.attr == "set_cookie" and any(
                        isinstance(v, ast.Constant) and v.value == "access_token" for v in valores[:1] + valores[-1:]):
                    hallados.append(("cookie", archivo, dentro))
            if isinstance(hijo, ast.ImportFrom) and hijo.module == "jwt":
                hallados.append(("from jwt import", archivo, dentro))
            recorrer(hijo, archivo, dentro)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)  # escapes viejos de otros archivos
        for archivo in sorted(raiz.rglob("*.py")):
            recorrer(ast.parse(archivo.read_text(encoding="utf-8")), str(archivo.relative_to(raiz)), None)
    assert sorted(hallados) == [("cookie", "main.py", "abrir_sesion"),
                                ("jwt.decode", "auth/dependencies.py", "datos_del_token")], hallados
