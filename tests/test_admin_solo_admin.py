"""ADMIN-1: lo de administración, sólo para el admin.

La prueba no lleva una lista de rutas escrita a mano: recorre las rutas que la
app publica (su esquema OpenAPI, que incluye los routers montados) y elige las
de administración por dónde viven o cómo están marcadas:

- todo lo que cuelga de /api/admin/, /api/dev/ o /dev/, y esas tres rutas
  exactas, sin la barra final;
- toda función global (actúa sobre el sistema, no sobre un estudio) marcada
  con tags=["admin"], esté donde esté.

Para cada una, un usuario común recibe 403 y un pedido sin sesión 401. Si a
cualquiera se le saca require_admin, el usuario común pasa el control y la
prueba lo nombra. Un WebSocket bajo esas rutas no tiene que aceptar la conexión
de un usuario común ni de alguien sin sesión (AISLAMIENTO-2).
"""
import anyio
import pytest
from fastapi.routing import APIRoute, APIWebSocketRoute
from starlette.routing import Mount, Route, WebSocketRoute
from fastapi.testclient import TestClient

from proyecto_maria import main

PREFIJOS_ADMIN = ("/api/admin/", "/api/dev/", "/dev/")


def _es_de_admin(ruta):
    """Cuelga de un prefijo de admin, o es el prefijo exacto sin la barra."""
    return ruta.startswith(PREFIJOS_ADMIN) or ruta.rstrip("/") + "/" in PREFIJOS_ADMIN


USUARIO_COMUN = {
    "username": "comun_admin1", "roles": ["operador"],
    "effective_owner": "comun_admin1", "plan": "premium",
    "billing_status": "active",
}
USUARIO_ADMIN = {
    "username": "admin_admin1", "roles": ["admin"],
    "effective_owner": "admin_admin1", "plan": "premium",
    "billing_status": "active",
}


def _rutas_de_admin():
    """(método, ruta) de cada ruta de admin o global, leídas de la app."""
    # El router de admin se monta al arrancar la app (lifespan): sin esto el
    # esquema no lo tendría.
    with TestClient(main.app):
        pass
    # El esquema se arma una vez y queda guardado. Si otra prueba lo armó
    # antes del arranque, le faltaría /api/admin/*: se arma de nuevo.
    main.app.openapi_schema = None
    esquema = main.app.openapi()
    rutas = set()
    for ruta, operaciones in esquema["paths"].items():
        for metodo, op in operaciones.items():
            if _es_de_admin(ruta) or "admin" in (op.get("tags") or []):
                rutas.add((metodo.upper(), ruta))
    # Las rutas propias de la app que se esconden del esquema
    # (include_in_schema=False) no aparecen arriba: se suman acá.
    # Lo mismo con las rutas crudas de Starlette (app.router.add_route), que no
    # pasan por las dependencias de FastAPI ni salen en el esquema (ADMIN-2).
    for r in main.app.routes:
        if isinstance(r, APIRoute) and not r.include_in_schema:
            if _es_de_admin(r.path) or "admin" in (r.tags or []):
                rutas.update((m, r.path) for m in r.methods if m != "HEAD")
        elif isinstance(r, Route) and not isinstance(r, APIRoute):
            if _es_de_admin(r.path):
                rutas.update((m, r.path) for m in (r.methods or {"GET"}) if m != "HEAD")
    return sorted(rutas)


def _websockets_de_admin():
    """WebSockets bajo rutas de admin: no son Route y el recorrido de arriba
    no los ve."""
    return sorted(
        r.path for r in main.app.routes
        if isinstance(r, (WebSocketRoute, APIWebSocketRoute)) and _es_de_admin(r.path)
    )


def _acepta_websocket(ruta):
    """True si la app manda websocket.accept. Se mira lo que manda la app y no
    lo que ve un cliente de prueba: el de Starlette levanta el error de un
    WebSocket que acepta y enseguida falla como si no lo hubiera aceptado.
    Cerrarla, negarla o fallar antes de aceptar no es aceptar."""
    concreta = _concreta(ruta)
    scope = {
        "type": "websocket", "asgi": {"version": "3.0"}, "scheme": "ws",
        "http_version": "1.1", "path": concreta, "raw_path": concreta.encode(),
        "root_path": "", "query_string": b"", "headers": [(b"host", b"testserver")],
        "client": ("testclient", 50000), "server": ("testserver", 80),
        "subprotocols": [], "state": {},
    }
    entradas = [{"type": "websocket.connect"}]
    enviados = []

    async def receive():
        return entradas.pop(0) if entradas else {"type": "websocket.disconnect", "code": 1000}

    async def send(mensaje):
        enviados.append(mensaje["type"])

    async def conectar():
        # Uno que acepta y se queda mandando no traba la prueba.
        with anyio.move_on_after(5):
            await main.app(scope, receive, send)

    try:
        anyio.run(conectar)
    except Exception:
        pass
    return "websocket.accept" in enviados


def _montajes_sobre_admin():
    """Apps montadas aparte (app.mount) que cubren rutas de admin.

    Una app montada no hereda require_admin ni se puede recorrer desde afuera:
    bajo /api/admin/, /api/dev/ o /dev/ no tiene que haber ninguna."""
    malas = []
    for r in main.app.routes:
        if isinstance(r, Mount):
            base = r.path.rstrip("/") + "/"
            if any(base.startswith(p) or p.startswith(base) for p in PREFIJOS_ADMIN):
                malas.append(r.path or "/")
    return malas


def _concreta(ruta):
    """Rellena los parámetros de la ruta: {limit} → 1, el resto → x."""
    import re
    return re.sub(r"\{[^}]+\}", lambda m: "1" if m.group(0) == "{limit}" else "x", ruta)


def _pedir(client, metodo, ruta):
    kwargs = {"json": {}} if metodo in ("POST", "PUT", "PATCH", "DELETE") else {}
    return client.request(metodo, _concreta(ruta), **kwargs)


@pytest.fixture(scope="module")
def rutas():
    rutas = _rutas_de_admin()
    # Ancla: si el recorrido dejara de ver el router de admin o las
    # funciones globales marcadas, la prueba pasaría sin probar nada.
    assert ("POST", "/api/admin/errors/clear-old") in rutas, rutas
    assert ("POST", "/api/ncm/cache/refresh") in rutas, rutas
    assert ("GET", "/api/dev/stats") in rutas, rutas
    return rutas


class _RegistroFalso:
    """Si un control fallara, borrar errores no toca el registro real."""
    def clear_old_notes(self, days):
        return 0

    def get_error_insights(self):
        return {"summary": {}, "top_errors": [], "suggested_improvements": []}


@pytest.fixture(autouse=True)
def _sin_efectos(monkeypatch):
    import proyecto_maria.core.error_notes_tracker as tracker
    monkeypatch.setattr(tracker, "get_error_tracker", lambda: _RegistroFalso())


def _con_usuario(usuario):
    main.app.dependency_overrides[main.get_current_user] = lambda: dict(usuario)


def test_usuario_comun_recibe_403_en_toda_ruta_de_admin(rutas):
    _con_usuario(USUARIO_COMUN)
    try:
        client = TestClient(main.app)
        abiertas = []
        for metodo, ruta in rutas:
            r = _pedir(client, metodo, ruta)
            if r.status_code != 403:
                abiertas.append(f"{metodo} {ruta} → {r.status_code}")
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)
    assert not abiertas, "rutas de admin abiertas a un usuario común:\n" + "\n".join(abiertas)


def test_ninguna_app_montada_sobre_rutas_de_admin(rutas):
    malas = _montajes_sobre_admin()
    assert not malas, f"apps montadas sobre rutas de admin, sin require_admin: {malas}"


def test_websocket_de_admin_no_acepta_a_un_usuario_comun(rutas):
    _con_usuario(USUARIO_COMUN)
    try:
        abiertos = [r for r in _websockets_de_admin() if _acepta_websocket(r)]
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)
    assert not abiertos, f"WebSockets de admin que aceptan a un usuario común: {abiertos}"


def test_websocket_de_admin_no_acepta_sin_sesion(rutas):
    # El nombre apaga el atajo de autenticación de pytest (conftest).
    abiertos = [r for r in _websockets_de_admin() if _acepta_websocket(r)]
    assert not abiertos, f"WebSockets de admin que aceptan sin sesión: {abiertos}"


def test_sin_sesion_recibe_401_en_toda_ruta_de_admin(rutas):
    # El nombre apaga el atajo de autenticación de pytest (conftest).
    client = TestClient(main.app)
    abiertas = []
    for metodo, ruta in rutas:
        r = _pedir(client, metodo, ruta)
        if r.status_code != 401:
            abiertas.append(f"{metodo} {ruta} → {r.status_code}")
    assert not abiertas, "rutas de admin sin pedir sesión:\n" + "\n".join(abiertas)


# El admin sigue entrando. Sólo lecturas: las escrituras (borrar errores,
# migrar, refrescar el cache contra fuentes externas) no se disparan desde
# una prueba; su control es el mismo require_admin que ya pasa acá.
RUTAS_ADMIN_LECTURA = [
    "/dev/dashboard",
    "/api/dev/stats",
    "/api/admin/health/detailed",
    "/api/admin/errors/insights",
    "/api/admin/errors/top/5",
    "/api/admin/metrics/prometheus",
    "/api/admin/logs/recent/5",
    "/api/admin/stats/summary",
    "/api/admin/cohort-retention",
]


@pytest.mark.parametrize("ruta", RUTAS_ADMIN_LECTURA)
def test_admin_sigue_entrando(rutas, ruta):
    _con_usuario(USUARIO_ADMIN)
    try:
        r = TestClient(main.app).get(ruta)
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)
    assert r.status_code == 200, f"{ruta}: {r.status_code} {r.text[:200]}"


@pytest.mark.parametrize("ruta", RUTAS_ADMIN_LECTURA)
def test_admin_por_admin_usernames_entra(rutas, ruta, monkeypatch):
    """Quien es admin por ADMIN_USERNAMES (sin el rol) entra a lo mismo (ADMIN-2)."""
    monkeypatch.setenv("ADMIN_USERNAMES", "jefe_admin1")
    _con_usuario({**USUARIO_COMUN, "username": "jefe_admin1", "effective_owner": "jefe_admin1"})
    try:
        r = TestClient(main.app).get(ruta)
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)
    assert r.status_code == 200, f"{ruta}: {r.status_code} {r.text[:200]}"


def test_admin_borra_errores_viejos(rutas):
    """El admin sigue pudiendo limpiar el registro (el falso de _sin_efectos)."""
    _con_usuario(USUARIO_ADMIN)
    try:
        r = TestClient(main.app).post("/api/admin/errors/clear-old")
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)
    assert r.status_code == 200, r.text[:200]
    assert r.json()["removed_count"] == 0


def test_admin_refresca_cache_ncm(rutas, monkeypatch):
    """El admin sigue refrescando el cache de NCM (fuente externa simulada)."""
    import proyecto_maria.core.ncm_service as ncm_service

    async def _falso(ncm, valor_fob=100.0, refresh=False):
        return {"ncm": ncm, "source": "prueba", "refresh": refresh}

    monkeypatch.setattr(ncm_service, "get_ncm_completo", _falso)
    _con_usuario(USUARIO_ADMIN)
    try:
        r = TestClient(main.app).post("/api/ncm/cache/refresh", json={"ncm": "84713012"})
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)
    assert r.status_code == 200, r.text[:200]
    assert r.json()["source"] == "prueba"
