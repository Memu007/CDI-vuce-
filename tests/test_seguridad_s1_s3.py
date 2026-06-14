"""S1: endpoints legacy de pagos eliminados. S3: /api/dev/* solo admin."""
import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main


@pytest.fixture(scope="module", autouse=True)
def _init_db_once():
    with TestClient(main.app) as _:
        pass


# --- S1: endpoints legacy borrados ---

@pytest.mark.parametrize("method,path", [
    ("post", "/api/payments/create-preference"),
    ("post", "/api/payments/bitcoin/create"),
    ("get", "/api/payments/bitcoin/checkout/abc"),
    ("post", "/api/payments/bitcoin/confirm/abc"),
])
def test_endpoints_legacy_eliminados(method, path):
    client = TestClient(main.app)
    kwargs = {"json": {}} if method == "post" else {}
    resp = getattr(client, method)(path, **kwargs)
    # 404 (ruta no existe) o 405 (metodo no permitido) — ya no es 200/4xx-auth
    assert resp.status_code in (404, 405), f"{path} sigue vivo: {resp.status_code}"


# --- S3: /api/dev/* exige admin ---

DEV_ENDPOINTS = [
    ("get", "/api/dev/stats"),
    ("get", "/api/dev/wave1-kpis"),
    ("get", "/api/dev/test-clientes"),
    ("post", "/api/dev/run-migrations"),
    ("get", "/api/dev/users-schema"),
]


@pytest.mark.parametrize("method,path", DEV_ENDPOINTS)
def test_dev_sin_auth_401(method, path):
    client = TestClient(main.app)
    resp = getattr(client, method)(path)
    assert resp.status_code == 401


@pytest.mark.parametrize("method,path", DEV_ENDPOINTS)
def test_dev_user_no_admin_403(method, path):
    # auth_override (conftest) inyecta un user NO admin
    main.app.dependency_overrides[main.get_current_user] = lambda: {
        "username": "test_user", "roles": [], "effective_owner": "test_user",
        "plan": "premium", "billing_status": "active",
    }
    try:
        client = TestClient(main.app)
        resp = getattr(client, method)(path)
        assert resp.status_code == 403
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)


@pytest.mark.parametrize("method,path", DEV_ENDPOINTS)
def test_dev_admin_pasa(method, path):
    main.app.dependency_overrides[main.get_current_user] = lambda: {
        "username": "admin_user", "roles": ["admin"], "effective_owner": "admin_user",
        "plan": "premium", "billing_status": "active",
    }
    try:
        client = TestClient(main.app)
        resp = getattr(client, method)(path)
        # admin pasa el guard: cualquier cosa menos 401/403
        assert resp.status_code not in (401, 403), f"{path}: {resp.status_code}"
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)
