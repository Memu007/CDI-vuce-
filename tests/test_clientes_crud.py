"""Tests CRUD de clientes: get, update, favorito, delete.

Cubren endpoints de main.py que no estaban testeados,
para llegar al threshold de cobertura >=38%."""
import uuid

import pytest


def _crear_cliente(auth_override, client, nombre=None, cuit=None):
    """Crea un cliente y devuelve su ID."""
    nombre = nombre or f"CRUD_{uuid.uuid4().hex[:8]}"
    body = {"nombre": nombre}
    if cuit:
        body["cuit"] = cuit
    r = client.post("/api/clientes", json=body)
    assert r.status_code == 200, r.text
    return r.json()["cliente"]["id"], nombre


def test_get_cliente_by_id(auth_override, client):
    """GET /api/clientes/{id} devuelve el cliente correcto."""
    cid, nombre = _crear_cliente(auth_override, client)
    r = client.get(f"/api/clientes/{cid}")
    assert r.status_code == 200
    data = r.json()
    assert data["nombre"] == nombre
    assert data["id"] == cid


def test_get_cliente_alias_ingles(auth_override, client):
    """GET /api/clients/{id} (alias histórico) funciona igual."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.get(f"/api/clients/{cid}")
    assert r.status_code == 200


def test_get_cliente_ajeno_devuelve_404(auth_override, client):
    """Un cliente de otro usuario no se puede ver."""
    from proyecto_maria.main import app, get_current_user

    fake_b = dict(auth_override)
    fake_b["username"] = f"other_{uuid.uuid4().hex[:8]}"
    app.dependency_overrides[get_current_user] = lambda: fake_b
    cid, _ = _crear_cliente(auth_override, client)
    app.dependency_overrides[get_current_user] = lambda: auth_override

    r = client.get(f"/api/clientes/{cid}")
    assert r.status_code == 404


def test_update_cliente(auth_override, client):
    """PUT /api/clientes/{id} actualiza campos."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.put(f"/api/clientes/{cid}", json={
        "nombre": "Nombre Actualizado",
        "cuit": "30555555555",
        "telefono": "11-5555-5555",
        "direccion": "Av. Test 123",
        "notas": "Cliente de prueba",
    })
    assert r.status_code == 200
    data = r.json()["cliente"]
    assert data["nombre"] == "Nombre Actualizado"
    assert data["cuit"] == "30555555555"


def test_update_cliente_campos_adicionales(auth_override, client):
    """PUT con default_origin, preferred_currency, auto_ncm_enabled."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.put(f"/api/clientes/{cid}", json={
        "default_origin": "CN",
        "preferred_currency": "USD",
        "auto_ncm_enabled": True,
        "fecha_inic_activ": "01/01/2020",
    })
    assert r.status_code == 200


def test_toggle_favorito(auth_override, client):
    """POST /api/clientes/{id}/favorito alterna el estado."""
    cid, _ = _crear_cliente(auth_override, client)
    r1 = client.post(f"/api/clientes/{cid}/favorito")
    assert r1.status_code == 200
    assert r1.json()["favorito"] is True

    r2 = client.post(f"/api/clientes/{cid}/favorito")
    assert r2.status_code == 200
    assert r2.json()["favorito"] is False


def test_delete_cliente(auth_override, client):
    """DELETE /api/clientes/{id} elimina el cliente."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.delete(f"/api/clientes/{cid}")
    assert r.status_code == 200

    # Confirmar que ya no existe
    r2 = client.get(f"/api/clientes/{cid}")
    assert r2.status_code == 404


def test_delete_cliente_ajeno_404(auth_override, client):
    """No se puede borrar un cliente de otro usuario."""
    from proyecto_maria.main import app, get_current_user

    fake_b = dict(auth_override)
    fake_b["username"] = f"other_{uuid.uuid4().hex[:8]}"
    app.dependency_overrides[get_current_user] = lambda: fake_b
    cid, _ = _crear_cliente(auth_override, client)
    app.dependency_overrides[get_current_user] = lambda: auth_override

    r = client.delete(f"/api/clientes/{cid}")
    assert r.status_code == 404


def test_list_clientes_vacio(auth_override, client):
    """GET /api/clientes devuelve lista aunque no haya clientes."""
    r = client.get("/api/clientes")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert isinstance(data["clientes"], list)


def test_list_clientes_con_datos(auth_override, client):
    """GET /api/clientes devuelve los clientes creados."""
    _crear_cliente(auth_override, client, nombre="ListaAlpha")
    _crear_cliente(auth_override, client, nombre="ListaBeta")
    r = client.get("/api/clientes")
    assert r.status_code == 200
    nombres = [c["nombre"] for c in r.json()["clientes"]]
    assert "ListaAlpha" in nombres
    assert "ListaBeta" in nombres


def test_get_cliente_por_cuit_exacto(auth_override, client):
    """GET /api/clientes/by-cuit/{cuit} encuentra por CUIT normalizado."""
    cid, _ = _crear_cliente(auth_override, client, cuit="30666666666")
    r = client.get("/api/clientes/by-cuit/30-666-66666-6")
    assert r.status_code == 200
    data = r.json()
    assert data["match"] == "exact"
    assert data["cliente"]["id"] == cid


def test_get_cliente_por_cuit_no_encontrado(auth_override, client):
    """GET /api/clientes/by-cuit/{cuit} devuelve match=none si no existe."""
    r = client.get("/api/clientes/by-cuit/30-999-99999-9")
    assert r.status_code == 200
    assert r.json()["match"] == "none"


def test_get_cliente_por_cuit_invalido_400(auth_override, client):
    """CUIT con < 11 dígitos → 400."""
    r = client.get("/api/clientes/by-cuit/123")
    assert r.status_code == 400


def test_auth_current_user(auth_override, client):
    """GET /auth/current_user devuelve los datos del usuario logueado."""
    r = client.get("/auth/current_user")
    assert r.status_code == 200
    data = r.json()
    assert data["username"] == "test_user"


def test_get_client_operations_vacio(auth_override, client):
    """GET /api/clientes/{id}/operaciones devuelve lista vacía si no hay ops."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.get(f"/api/clientes/{cid}/operaciones")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["operaciones"] == []


def test_get_client_operations_ajeno_404(auth_override, client):
    """No se pueden ver operaciones de un cliente ajeno."""
    from proyecto_maria.main import app, get_current_user

    fake_b = dict(auth_override)
    fake_b["username"] = f"other_{uuid.uuid4().hex[:8]}"
    app.dependency_overrides[get_current_user] = lambda: fake_b
    cid, _ = _crear_cliente(auth_override, client)
    app.dependency_overrides[get_current_user] = lambda: auth_override

    r = client.get(f"/api/clientes/{cid}/operaciones")
    assert r.status_code == 404


def test_get_client_metrics_vacio(auth_override, client):
    """GET /api/clientes/{id}/metricas devuelve ceros si no hay ops."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.get(f"/api/clientes/{cid}/metricas")
    assert r.status_code == 200
    data = r.json()
    assert data["total_operaciones"] == 0
    assert data["total_items"] == 0


def test_get_client_metrics_ajeno_404(auth_override, client):
    """Métricas de cliente ajeno → 404."""
    from proyecto_maria.main import app, get_current_user

    fake_b = dict(auth_override)
    fake_b["username"] = f"other_{uuid.uuid4().hex[:8]}"
    app.dependency_overrides[get_current_user] = lambda: fake_b
    cid, _ = _crear_cliente(auth_override, client)
    app.dependency_overrides[get_current_user] = lambda: auth_override

    r = client.get(f"/api/clientes/{cid}/metricas")
    assert r.status_code == 404


def test_get_cliente_inexistente_404(auth_override, client):
    """GET /api/clientes/{id} con ID inexistente → 404."""
    r = client.get("/api/clientes/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_update_cliente_inexistente_404(auth_override, client):
    """PUT a cliente inexistente → 404."""
    r = client.put("/api/clientes/00000000-0000-0000-0000-000000000000",
                   json={"nombre": "X"})
    assert r.status_code == 404


def test_toggle_favorito_inexistente_404(auth_override, client):
    """Favorito en cliente inexistente → 404."""
    r = client.post("/api/clientes/00000000-0000-0000-0000-000000000000/favorito")
    assert r.status_code == 404


def test_delete_cliente_inexistente_404(auth_override, client):
    """DELETE cliente inexistente → 404."""
    r = client.delete("/api/clientes/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


def test_export_csv_cliente_vacio(auth_override, client):
    """GET /api/clientes/{id}/export.csv devuelve CSV con headers aunque no haya ops."""
    cid, _ = _crear_cliente(auth_override, client, nombre="ExportTest")
    r = client.get(f"/api/clientes/{cid}/export.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    assert "fecha" in r.text  # header row


def test_export_csv_ajeno_404(auth_override, client):
    """Export CSV de cliente ajeno → 404."""
    from proyecto_maria.main import app, get_current_user

    fake_b = dict(auth_override)
    fake_b["username"] = f"other_{uuid.uuid4().hex[:8]}"
    app.dependency_overrides[get_current_user] = lambda: fake_b
    cid, _ = _crear_cliente(auth_override, client)
    app.dependency_overrides[get_current_user] = lambda: auth_override

    r = client.get(f"/api/clientes/{cid}/export.csv")
    assert r.status_code == 404


def test_get_column_mapping_vacio(auth_override, client):
    """GET column_mapping devuelve {} si no hay mapping guardado."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.get(f"/api/clientes/{cid}/column_mapping")
    assert r.status_code == 200
    data = r.json()
    assert data["mapping"] == {}
    assert "canonicos" in data


def test_set_and_get_column_mapping(auth_override, client):
    """POST column_mapping guarda y GET lo recupera."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.post(f"/api/clientes/{cid}/column_mapping", json={
        "mapping": {"Codigo": "pieza", "Pais": "origen", "Cant": "cantidad"}
    })
    assert r.status_code == 200
    data = r.json()
    assert data["mapping"]["Codigo"] == "pieza"

    r2 = client.get(f"/api/clientes/{cid}/column_mapping")
    assert r2.status_code == 200
    assert r2.json()["mapping"]["Codigo"] == "pieza"


def test_set_column_mapping_invalido_ignora(auth_override, client):
    """POST con canonicos inválidos los ignora."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.post(f"/api/clientes/{cid}/column_mapping", json={
        "mapping": {"Col": "no_existe", "OK": "pieza"}
    })
    assert r.status_code == 200
    mapping = r.json()["mapping"]
    assert "Col" not in mapping
    assert mapping["OK"] == "pieza"


def test_delete_column_mapping(auth_override, client):
    """DELETE column_mapping borra el mapping."""
    cid, _ = _crear_cliente(auth_override, client)
    client.post(f"/api/clientes/{cid}/column_mapping", json={"mapping": {"X": "pieza"}})
    r = client.delete(f"/api/clientes/{cid}/column_mapping")
    assert r.status_code == 200
    assert r.json()["mapping"] == {}


def test_get_catalogo_columnas_vacio(auth_override, client):
    """GET catalogo/columnas devuelve {} y status cuando no hay mapping."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.get(f"/api/clientes/{cid}/catalogo/columnas")
    assert r.status_code == 200
    data = r.json()
    assert data["columnas"] == {}
    assert data["status"]["completo"] is False


def test_put_catalogo_columnas(auth_override, client):
    """PUT catalogo/columnas guarda el mapping y devuelve status."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.put(f"/api/clientes/{cid}/catalogo/columnas", json={
        "columnas": {"Codigo": "pieza", "Desc": "descripcion", "Pais": "origen",
                      "Cant": "cantidad", "Valor": "valor_unitario", "Peso": "peso_unitario"}
    })
    assert r.status_code == 200
    data = r.json()
    assert data["status"]["completo"] is True
    assert data["status"]["detectadas"] == 6


def test_delete_catalogo_columnas(auth_override, client):
    """DELETE catalogo/columnas borra el mapping."""
    cid, _ = _crear_cliente(auth_override, client)
    client.put(f"/api/clientes/{cid}/catalogo/columnas", json={"columnas": {"X": "pieza"}})
    r = client.delete(f"/api/clientes/{cid}/catalogo/columnas")
    assert r.status_code == 200
    assert r.json()["columnas"] == {}


def test_get_catalogo_productos_vacio(auth_override, client):
    """GET catalogo/productos devuelve lista vacía si no hay productos."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.get(f"/api/clientes/{cid}/catalogo/productos")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert isinstance(data["productos"], list)


def test_create_manual_operation(auth_override, client):
    """POST /api/operations/manual crea una operación con items."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.post("/api/operations/manual", json={
        "client_id": cid,
        "items": [
            {"descripcion": "Laptop", "cantidad": 2, "valor_unitario": 500,
             "pieza": "84713000", "origen": "CN", "peso_unitario": 2.5},
            {"descripcion": "Mouse", "cantidad": 10, "valor_unitario": 15,
             "pieza": "84716060", "origen": "CN"},
        ],
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["success"] is True
    assert data["total_items"] == 2
    assert data["client_id"] == cid


def test_create_manual_operation_sin_client_id(auth_override, client):
    """POST /api/operations/manual sin client_id → 400."""
    r = client.post("/api/operations/manual", json={
        "items": [{"descripcion": "X", "cantidad": 1, "valor_unitario": 10}],
    })
    assert r.status_code == 400


def test_create_manual_operation_sin_items(auth_override, client):
    """POST /api/operations/manual sin items → 400."""
    cid, _ = _crear_cliente(auth_override, client)
    r = client.post("/api/operations/manual", json={
        "client_id": cid,
        "items": [],
    })
    assert r.status_code == 400


def test_create_manual_operation_cliente_ajeno(auth_override, client):
    """POST /api/operations/manual con cliente ajeno → 404."""
    from proyecto_maria.main import app, get_current_user

    fake_b = dict(auth_override)
    fake_b["username"] = f"other_{uuid.uuid4().hex[:8]}"
    app.dependency_overrides[get_current_user] = lambda: fake_b
    cid, _ = _crear_cliente(auth_override, client)
    app.dependency_overrides[get_current_user] = lambda: auth_override

    r = client.post("/api/operations/manual", json={
        "client_id": cid,
        "items": [{"descripcion": "X", "cantidad": 1, "valor_unitario": 10}],
    })
    assert r.status_code == 404


def test_list_clientes_con_operaciones(auth_override, client):
    """GET /api/clientes con operaciones cubre aggregate queries."""
    cid, _ = _crear_cliente(auth_override, client, nombre="ConOps")
    client.post("/api/operations/manual", json={
        "client_id": cid,
        "items": [
            {"descripcion": "Test", "cantidad": 3, "valor_unitario": 100,
             "pieza": "84713000", "origen": "CN"},
        ],
    })
    r = client.get("/api/clientes")
    assert r.status_code == 200
    nombres = [c["nombre"] for c in r.json()["clientes"]]
    assert "ConOps" in nombres


def test_get_client_operations_con_datos(auth_override, client):
    """GET /api/clientes/{id}/operaciones con operaciones reales."""
    cid, _ = _crear_cliente(auth_override, client)
    client.post("/api/operations/manual", json={
        "client_id": cid,
        "items": [{"descripcion": "X", "cantidad": 1, "valor_unitario": 50}],
    })
    r = client.get(f"/api/clientes/{cid}/operaciones")
    assert r.status_code == 200
    ops = r.json()["operaciones"]
    assert len(ops) >= 1


def test_get_client_metrics_con_datos(auth_override, client):
    """GET /api/clientes/{id}/metricas con operaciones reales."""
    cid, _ = _crear_cliente(auth_override, client)
    client.post("/api/operations/manual", json={
        "client_id": cid,
        "items": [{"descripcion": "X", "cantidad": 5, "valor_unitario": 200,
                   "pieza": "84713000", "origen": "CN"}],
    })
    r = client.get(f"/api/clientes/{cid}/metricas")
    assert r.status_code == 200
    data = r.json()
    assert data["total_operaciones"] >= 1
    assert data["total_items"] >= 1


def test_export_csv_con_datos(auth_override, client):
    """GET /api/clientes/{id}/export.csv con operaciones."""
    cid, _ = _crear_cliente(auth_override, client, nombre="ExportConOps")
    client.post("/api/operations/manual", json={
        "client_id": cid,
        "items": [{"descripcion": "X", "cantidad": 2, "valor_unitario": 100,
                   "pieza": "84713000", "origen": "CN"}],
    })
    r = client.get(f"/api/clientes/{cid}/export.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    assert "84713000" in r.text
