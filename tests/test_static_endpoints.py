"""Tests de endpoints estáticos y públicos de main.py.

Cubren endpoints síncronos que sirven archivos (landing, robots, sitemap, CSS, JS)
sin necesidad de DB ni auth, para sumar líneas a la cobertura de main.py."""


def test_robots_txt(client):
    """GET /robots.txt devuelve texto plano."""
    r = client.get("/robots.txt")
    assert r.status_code == 200


def test_sitemap_xml(client):
    """GET /sitemap.xml devuelve XML."""
    r = client.get("/sitemap.xml")
    assert r.status_code == 200


def test_root_landing(client):
    """GET / sirve la landing page."""
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


def test_landing_nueva_redirect(client):
    """GET /landing_nueva redirige a /."""
    r = client.get("/landing_nueva", follow_redirects=False)
    assert r.status_code == 307


def test_web_interface(client):
    """GET /web sirve la landing page."""
    r = client.get("/web")
    assert r.status_code == 200


def test_estilos_landing_css(client):
    """GET /estilos_landing.css sirve el CSS."""
    r = client.get("/estilos_landing.css")
    assert r.status_code == 200


def test_app_v2_css(client):
    """GET /static/v2/app_v2.css sirve el CSS de la app."""
    r = client.get("/static/v2/app_v2.css")
    assert r.status_code == 200


def test_dashboard_sirve_v2(client):
    """GET /dashboard sirve la v2, la única interfaz."""
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "/static/v2/app_v2.js" in r.text


def test_dashboard_ignora_v1_y_borra_la_cookie_vieja(client):
    """Ni `?v=1` ni la cookie `cdi_ui=v1` de la transición traen la v1: se sirve
    v2 y la cookie se borra. Las rutas /app.js y /app.css ya no existen."""
    r = client.get("/dashboard?v=1", cookies={"cdi_ui": "v1"}, follow_redirects=False)
    assert r.status_code == 200
    assert "/static/v2/app_v2.js" in r.text
    assert "/app.js?v=" not in r.text
    set_cookie = r.headers.get("set-cookie", "")
    assert "cdi_ui=" in set_cookie and ("Max-Age=0" in set_cookie or "expires=" in set_cookie.lower())
    assert client.get("/app.js").status_code == 404
    assert client.get("/app.css").status_code == 404


def test_session_state(client):
    """POST /api/session/state acepta eventos de telemetría."""
    r = client.post("/api/session/state", json={
        "version": "v2", "screen": "test", "action": "click",
    })
    assert r.status_code == 200
    assert r.json()["ok"] is True


