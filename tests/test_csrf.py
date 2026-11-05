"""CSRF double-submit cookie: middleware + cookies de sesion.

Usa el flujo real de register (deja access_token + csrf_token en el client)
porque el middleware solo actua cuando la sesion va por cookie.
"""
import os
import uuid

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("EMAIL_VERIFICATION_REQUIRED", "false")

from proyecto_maria.main import app  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _init_db_once():
    # Dispara el lifespan para crear las tablas en el engine de tests.
    with TestClient(app) as _:
        pass


@pytest.fixture()
def cookie_client():
    client = TestClient(app)
    username = f"csrf_{uuid.uuid4().hex[:10]}"
    resp = client.post("/auth/register", json={
        "username": username,
        "password": "testpass123",
        "email": f"{username}@test.cdi",
        "name": username,
    })
    assert resp.status_code == 200, resp.text
    return client


def test_register_sets_csrf_cookie(cookie_client):
    assert cookie_client.cookies.get("csrf_token")


def test_report_only_no_bloquea_sin_header(cookie_client, monkeypatch):
    monkeypatch.delenv("CSRF_ENFORCE", raising=False)
    resp = cookie_client.post("/api/backup/localStorage", json={"x": 1})
    assert resp.status_code == 200


def test_enforce_bloquea_sin_header(cookie_client, monkeypatch):
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    resp = cookie_client.post("/api/backup/localStorage", json={"x": 1})
    assert resp.status_code == 403
    assert resp.json()["code"] == "csrf_failed"


def test_enforce_pasa_con_header_valido(cookie_client, monkeypatch):
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    token = cookie_client.cookies.get("csrf_token")
    resp = cookie_client.post(
        "/api/backup/localStorage",
        json={"x": 1},
        headers={"X-CSRF-Token": token},
    )
    assert resp.status_code == 200


def test_enforce_bloquea_header_invalido(cookie_client, monkeypatch):
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    resp = cookie_client.post(
        "/api/backup/localStorage",
        json={"x": 1},
        headers={"X-CSRF-Token": "token-falso"},
    )
    assert resp.status_code == 403


def test_enforce_no_afecta_bearer_sin_cookie(monkeypatch, sin_bypass_de_test):
    # Sin cookie de sesion el middleware no aplica (no es atacable via CSRF).
    # Necesita `sin_bypass_de_test`: bajo pytest la app autentica sola cuando no
    # hay token, y el nombre de este test no matchea los patrones que apagan ese
    # atajo (VUCE-3). Sin apagarlo, el pedido entra igual y da 200 en vez de 401.
    # Verificado con el atajo apagado (= producción): el producto devuelve 401.
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    client = TestClient(app)
    resp = client.post("/api/backup/localStorage", json={"x": 1})
    assert resp.status_code == 401  # rebota por auth, no por CSRF


@pytest.mark.parametrize("ruta", ["/auth/logout", "/logout"])
def test_logout_con_token_borra_las_dos_cookies(cookie_client, monkeypatch, ruta):
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    resp = cookie_client.post(ruta, headers={"X-CSRF-Token": cookie_client.cookies.get("csrf_token")})
    assert resp.status_code == 200, resp.text
    assert not cookie_client.cookies.get("access_token")
    assert not cookie_client.cookies.get("csrf_token")


RUTAS_SIN_TOKEN = [
    ("DELETE", "/api/catalog/x/productos/abc-webhook", None, False),
    ("POST", "/api/payments/webhook/x", {}, False),
    ("POST", "/healthx", {}, False),
    ("POST", "/staticx", {}, False),
    ("POST", "/auth/loginx", {}, False),
    ("POST", "/auth/login", {"username": "nadie", "password": "x"}, True),
    ("POST", "/auth/request-password-reset", {"email": "nadie@test.cdi"}, True),
    ("POST", "/auth/recover-username", {"email": "nadie@test.cdi"}, True),
    ("POST", "/auth/reset-password", {"token": "x", "new_password": "otraClave123"}, True),
]


@pytest.mark.parametrize("metodo,ruta,cuerpo,exenta", RUTAS_SIN_TOKEN, ids=[f"{m} {r}" for m, r, _, _ in RUTAS_SIN_TOKEN])
def test_sin_token_solo_pasan_las_rutas_exentas_exactas(cookie_client, monkeypatch, metodo, ruta, cuerpo, exenta):
    # Con una cookie de sesión vieja, las rutas públicas que no usan la sesión
    # tienen que andar; cualquier otra ruta, aunque se le parezca, pide el token.
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    resp = cookie_client.request(metodo, ruta, json=cuerpo)
    pidio_token = resp.json().get("code") == "csrf_failed"
    assert pidio_token != exenta, f"{metodo} {ruta} sin token dio {resp.status_code}: {resp.text}"


@pytest.mark.parametrize("ruta,con_token,esperado", [
    ("/auth/logout", False, 403),
    ("/auth/logout", True, 200),
    ("/api/session/state", False, 403),
    ("/api/session/state", True, 200),
])
def test_enforce_pide_token_a_logout_y_telemetria(cookie_client, monkeypatch, ruta, con_token, esperado):
    monkeypatch.setenv("CSRF_ENFORCE", "true")
    headers = {"Origin": "https://otro-sitio.example"}
    if con_token:
        headers = {"X-CSRF-Token": cookie_client.cookies.get("csrf_token")}
    resp = cookie_client.post(ruta, json={"event": "csrf1", "payload": {}}, headers=headers)
    assert resp.status_code == esperado, resp.text
    cerro = ruta == "/auth/logout" and esperado == 200
    assert bool(cookie_client.cookies.get("access_token")) != cerro


@pytest.mark.parametrize("enforce", ["true", "false"])
@pytest.mark.parametrize("ruta", ["/auth/logout", "/logout"])
def test_logout_desde_otro_sitio_no_borra_la_sesion(monkeypatch, ruta, enforce):
    # Así llega un <form> de otro sitio: la cookie SameSite=Strict no viaja,
    # pero el navegador sí aplica los Set-Cookie de borrado de la respuesta.
    monkeypatch.setenv("CSRF_ENFORCE", enforce)
    resp = TestClient(app).post(ruta, headers={"Origin": "https://otro-sitio.example"})
    assert resp.status_code == 200, resp.text
    borrados = resp.headers.get("set-cookie", "")
    assert "access_token" not in borrados and "csrf_token" not in borrados, borrados
