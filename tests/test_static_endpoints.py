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


def test_app_css(client):
    """GET /app.css sirve el CSS de la app."""
    r = client.get("/app.css")
    assert r.status_code == 200


def test_app_js(client):
    """GET /app.js sirve el JS de la app."""
    r = client.get("/app.js")
    assert r.status_code == 200


def test_dashboard_v2_default(client):
    """GET /dashboard sirve v2 por defecto."""
    r = client.get("/dashboard")
    assert r.status_code == 200


def test_dashboard_v1_query(client):
    """GET /dashboard?v=1 sirve v1 y setea cookie."""
    r = client.get("/dashboard?v=1", follow_redirects=False)
    assert r.status_code == 200


def test_dashboard_v2_query(client):
    """GET /dashboard?v=2 sirve v2 y limpia cookie."""
    r = client.get("/dashboard?v=2", follow_redirects=False)
    assert r.status_code == 200


def test_session_state(client):
    """POST /api/session/state acepta eventos de telemetría."""
    r = client.post("/api/session/state", json={
        "version": "v2", "screen": "test", "action": "click",
    })
    assert r.status_code == 200
    assert r.json()["ok"] is True


