"""ADMIN-1: lo de administración, sólo para el admin.

La prueba no lleva una lista de rutas escrita a mano: recorre las rutas que la
app publica (su esquema OpenAPI, que incluye los routers montados) y elige las
de administración por dónde viven o cómo están marcadas:

- todo lo que cuelga de /api/admin/, /api/dev/ o /dev/;
- toda función global (actúa sobre el sistema, no sobre un estudio) marcada
  con tags=["admin"], esté donde esté.

Para cada una, un usuario común recibe 403 y un pedido sin sesión 401. Si a
cualquiera se le saca require_admin, el usuario común pasa el control y la
prueba lo nombra.
"""
import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from proyecto_maria import main

PREFIJOS_ADMIN = ("/api/admin/", "/api/dev/", "/dev/")

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
            if ruta.startswith(PREFIJOS_ADMIN) or "admin" in (op.get("tags") or []):
                rutas.add((metodo.upper(), ruta))
    # Las rutas propias de la app que se esconden del esquema
    # (include_in_schema=False) no aparecen arriba: se suman acá.
    for r in main.app.routes:
        if isinstance(r, APIRoute) and not r.include_in_schema:
            if r.path.startswith(PREFIJOS_ADMIN) or "admin" in (r.tags or []):
                rutas.update((m, r.path) for m in r.methods if m != "HEAD")
    return sorted(rutas)


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


def test_admin_por_admin_usernames_entra(rutas, monkeypatch):
    """Quien es admin por ADMIN_USERNAMES (sin el rol) también entra."""
    monkeypatch.setenv("ADMIN_USERNAMES", "jefe_admin1")
    _con_usuario({**USUARIO_COMUN, "username": "jefe_admin1", "effective_owner": "jefe_admin1"})
    try:
        r = TestClient(main.app).get("/api/admin/stats/summary")
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)
    assert r.status_code == 200, r.text[:200]


def test_admin_borra_errores_viejos(rutas):
    """El admin sigue pudiendo limpiar el registro (el falso de _sin_efectos)."""
    _con_usuario(USUARIO_ADMIN)
    try:
        r = TestClient(main.app).post("/api/admin/errors/clear-old")
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)
    assert r.status_code == 200, r.text[:200]
    assert r.json()["removed_count"] == 0
