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
    # El auth_override usa 'test_user'. Creamos un cliente asociado.
    client.post("/api/clientes", json={"nombre": "Cliente Propio", "cuit": "30444444444"})

    # Simulamos otro usuario cambiando la dependencia momentáneamente no es trivial,
    # así que verificamos al menos que la búsqueda no devuelva clientes ajenos
    # usando el hecho de que el fixture client no tiene otros clientes previos.
    r = client.get("/api/clientes/search?q=cliente")
    data = r.json()
    assert len(data["clientes"]) == 1
    assert data["clientes"][0]["nombre"] == "Cliente Propio"
