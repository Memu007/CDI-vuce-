import pytest


def test_search_clientes_by_name(auth_override, client):
    # Crear clientes de prueba
    client.post("/api/clientes", json={"nombre": "Acme Argentina SRL", "cuit": "30111111111"})
    client.post("/api/clientes", json={"nombre": "Beta Importadora", "cuit": "30222222222"})

    r = client.get("/api/clientes/search?q=acme")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert len(data["clientes"]) == 1
    assert data["clientes"][0]["nombre"] == "Acme Argentina SRL"


def test_search_clientes_by_cuit_partial(auth_override, client):
    client.post("/api/clientes", json={"nombre": "Gamma SA", "cuit": "30-33333333-3"})

    r = client.get("/api/clientes/search?q=333333")
    assert r.status_code == 200
    data = r.json()
    assert len(data["clientes"]) == 1
    assert data["clientes"][0]["nombre"] == "Gamma SA"


def test_search_clientes_empty_query_returns_422(auth_override, client):
    r = client.get("/api/clientes/search?q=")
    assert r.status_code == 422


def test_search_clientes_requires_auth(client):
    r = client.get("/api/clientes/search?q=acme")
    assert r.status_code == 401


def test_search_clientes_isolated_by_owner(auth_override, client):
    """Cada usuario ve solo sus propios clientes, no los de otros."""
    from proyecto_maria.main import app, get_current_user
    import uuid

    # Usuario A (test_user del fixture) crea un cliente con nombre único
    suffix = uuid.uuid4().hex[:8]
    nombre_a = f"AcmeAislado_{suffix}"
    client.post("/api/clientes", json={"nombre": nombre_a, "cuit": f"30{suffix[:8]}01"})

    # Usuario B: cambiar el override temporalmente
    fake_b = dict(auth_override)
    fake_b["username"] = f"other_user_{suffix}"
    fake_b["effective_owner"] = f"other_user_{suffix}"

    # Crear cliente como usuario B
    app.dependency_overrides[get_current_user] = lambda: fake_b
    nombre_b = f"BetaAislado_{suffix}"
    client.post("/api/clientes", json={"nombre": nombre_b, "cuit": f"30{suffix[:8]}02"})

    # Restaurar usuario A
    app.dependency_overrides[get_current_user] = lambda: auth_override

    # Usuario A busca por el sufijo único — solo debe ver su cliente
    r = client.get(f"/api/clientes/search?q={suffix}")
    assert r.status_code == 200
    data = r.json()
    nombres = [c["nombre"] for c in data["clientes"]]
    assert nombre_a in nombres
    assert nombre_b not in nombres

    # Usuario B busca — solo debe ver su cliente
    app.dependency_overrides[get_current_user] = lambda: fake_b
    r2 = client.get(f"/api/clientes/search?q={suffix}")
    assert r2.status_code == 200
    data2 = r2.json()
    nombres2 = [c["nombre"] for c in data2["clientes"]]
    assert nombre_b in nombres2
    assert nombre_a not in nombres2

    # Restaurar override original
    app.dependency_overrides[get_current_user] = lambda: auth_override
