import pytest


def test_list_clientes_includes_total_operaciones_and_ultimo(auth_override, client):
    r = client.get("/api/clientes")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    for c in data["clientes"]:
        assert "total_operaciones" in c
        assert "ultimo_movimiento" in c


def test_client_metrics_includes_todos_los_kpis(auth_override, client):
    # Crear cliente
    r = client.post("/api/clientes", json={"nombre": "Plan02 KPI", "cuit": "30123456789"})
    assert r.status_code == 200
    cid = r.json()["cliente"]["id"]
    # Crear operación manual
    r2 = client.post("/api/operations/manual", json={
        "client_id": cid,
        "items": [{"descripcion": "Cable", "cantidad": 10, "valor_unitario": 5, "origen": "CN"}]
    })
    assert r2.status_code == 200
    # Métricas
    r3 = client.get(f"/api/clientes/{cid}/metricas")
    assert r3.status_code == 200
    data = r3.json()
    assert data["total_operaciones"] == 1
    assert data["total_items"] == 1
    assert data["promedio_items_por_operacion"] == 1.0
    assert data["origen_frecuente"] == "CN"


def test_export_csv_requires_auth(client):
    r = client.get("/api/clientes/abc/export.csv")
    assert r.status_code == 401


def test_export_csv_returns_csv_with_ops(auth_override, client):
    r = client.post("/api/clientes", json={"nombre": "Plan02 CSV", "cuit": "30111222333"})
    assert r.status_code == 200, r.text
    cid = r.json()["cliente"]["id"]
    r_op = client.post("/api/operations/manual", json={
        "client_id": cid,
        "items": [{"descripcion": "Cable", "cantidad": 10, "valor_unitario": 5, "origen": "CN"}]
    })
    assert r_op.status_code == 200, r_op.text
    r2 = client.get(f"/api/clientes/{cid}/export.csv")
    assert r2.status_code == 200
    assert r2.headers.get("content-type") == "text/csv; charset=utf-8-sig"
    body = r2.content.decode("utf-8-sig")
    assert "fecha,op_id,total_items,valor_total,ncms,origenes" in body
    assert "CN" in body
