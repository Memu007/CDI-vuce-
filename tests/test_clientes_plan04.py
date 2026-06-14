import io
import pytest
from fastapi.testclient import TestClient


def _make_excel_bytes(headers: list, rows: list[list]) -> bytes:
    """Crea un archivo Excel .xlsx en memoria con openpyxl."""
    try:
        from openpyxl import Workbook
    except ImportError:
        pytest.skip("openpyxl no está instalado")
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_upload_excel_aprende_y_persiste_column_mapping(auth_override, client):
    """Subir Excel con cliente_id debe detectar y guardar columnas en DB."""
    # Crear cliente
    r = client.post("/api/clientes", json={"nombre": "Plan04 Excel", "cuit": "30123456780"})
    assert r.status_code == 200, r.text
    cid = r.json()["cliente"]["id"]

    # Verificar que no tiene mapping
    r = client.get(f"/api/clientes/{cid}/catalogo/columnas")
    assert r.status_code == 200
    assert r.json()["columnas"] == {}
    assert r.json()["status"]["detectadas"] == 0

    # Subir Excel con headers alternativos
    excel = _make_excel_bytes(
        ["CODIGO", "PRODUCTO", "PAIS", "QTY", "PRECIO", "PESO"],
        [["84713000", "Laptop", "CN", 10, 350.0, 1.5]],
    )
    r = client.post(
        "/upload_excel_v2/",
        data={"cliente_id": cid, "use_mapping": "true"},
        files={"file": ("test.xlsx", io.BytesIO(excel), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["items_count"] == 1
    assert data["catalogo"]["columnas_detectadas"] == 6
    assert data["catalogo"]["completo"] is True

    # Verificar persistencia: nuevo request debe traer el mapping
    r = client.get(f"/api/clientes/{cid}/catalogo/columnas")
    assert r.status_code == 200
    cols = r.json()["columnas"]
    assert cols.get("CODIGO") == "pieza"
    assert cols.get("PRODUCTO") == "descripcion"
    assert cols.get("PAIS") == "origen"
    assert cols.get("QTY") == "cantidad"
    assert cols.get("PRECIO") == "valor_unitario"
    assert cols.get("PESO") == "peso_unitario"


def test_upload_excel_usa_mapping_persistido(auth_override, client):
    """Segundo upload del mismo cliente usa el mapping guardado."""
    r = client.post("/api/clientes", json={"nombre": "Plan04 Excel 2", "cuit": "30123456781"})
    assert r.status_code == 200
    cid = r.json()["cliente"]["id"]

    # Guardar mapping manualmente
    r = client.put(
        f"/api/clientes/{cid}/catalogo/columnas",
        json={"columnas": {"COD": "pieza", "DESC": "descripcion", "PAIS": "origen", "CANT": "cantidad", "VAL": "valor_unitario", "PES": "peso_unitario"}},
    )
    assert r.status_code == 200

    # Subir Excel con esos headers exactos
    excel = _make_excel_bytes(
        ["COD", "DESC", "PAIS", "CANT", "VAL", "PES"],
        [["84713000", "Laptop", "CN", 10, 350.0, 1.5]],
    )
    r = client.post(
        "/upload_excel_v2/",
        data={"cliente_id": cid, "use_mapping": "true"},
        files={"file": ("test2.xlsx", io.BytesIO(excel), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert r.status_code == 200, r.text
    assert r.json()["applied_mapping"] is True
    assert r.json()["items_count"] == 1


def test_catalogo_productos_endpoints(auth_override, client):
    """Aprender productos desde operación y listarlos en el catálogo."""
    r = client.post("/api/clientes", json={"nombre": "Plan04 Productos", "cuit": "30123456782"})
    assert r.status_code == 200
    cid = r.json()["cliente"]["id"]

    # Guardar operación con items
    r = client.post(
        f"/api/clientes/{cid}/operaciones",
        json={
            "operation_id": "OP_TEST_001",
            "source": "manual",
            "currency": "USD",
            "resumen": {"items": 2, "valor_total": 1000},
            "items": [
                {"pieza": "84713000", "descripcion": "Laptop 14 pulgadas", "origen": "CN", "cantidad": 10, "valor_unitario": 350, "peso_unitario": 1.5},
                {"pieza": "84713001", "descripcion": "Mouse inalambrico", "origen": "BR", "cantidad": 20, "valor_unitario": 15, "peso_unitario": 0.2},
            ],
        },
    )
    assert r.status_code == 200, r.text

    # Listar productos
    r = client.get(f"/api/clientes/{cid}/catalogo/productos")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    descripciones = {p["descripcion"] for p in data["productos"]}
    assert "Laptop 14 pulgadas" in descripciones
    assert "Mouse inalambrico" in descripciones


def test_catalog_lookup_usa_memoria_cliente(auth_override, client):
    """El lookup combinado debe devolver matches del cliente."""
    r = client.post("/api/clientes", json={"nombre": "Plan04 Lookup", "cuit": "30123456783"})
    assert r.status_code == 200
    cid = r.json()["cliente"]["id"]

    # Aprender producto
    r = client.post(
        f"/api/clientes/{cid}/catalogo/productos/learn",
        json={
            "items": [
                {"ncm": "84713000", "descripcion": "Laptop 14 pulgadas modelo X", "origen": "CN", "cantidad": 10, "valor_unitario": 350, "peso_unitario": 1.5},
            ],
        },
    )
    assert r.status_code == 200, r.text

    # Lookup con descripción similar
    r = client.post(
        "/api/catalog/lookup",
        json={
            "items": [{"descripcion": "Laptop 14 pulgadas modelo X"}],
            "vendor_name": "",
            "client_id": cid,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["aplicados_cliente"] >= 1
    assert data["items"][0]["source"] == "cliente"
    assert data["items"][0]["ncm"] == "84713000"


def test_catalogo_columnas_crud(auth_override, client):
    """PUT/GET/DELETE de columnas del catálogo."""
    r = client.post("/api/clientes", json={"nombre": "Plan04 CRUD", "cuit": "30123456784"})
    assert r.status_code == 200
    cid = r.json()["cliente"]["id"]

    r = client.put(
        f"/api/clientes/{cid}/catalogo/columnas",
        json={"columnas": {"A": "pieza", "B": "descripcion"}},
    )
    assert r.status_code == 200
    assert r.json()["status"]["detectadas"] == 2
    assert r.json()["status"]["completo"] is False

    r = client.get(f"/api/clientes/{cid}/catalogo/columnas")
    assert r.status_code == 200
    assert r.json()["columnas"]["A"] == "pieza"

    r = client.delete(f"/api/clientes/{cid}/catalogo/columnas")
    assert r.status_code == 200
    assert r.json()["columnas"] == {}

    r = client.get(f"/api/clientes/{cid}/catalogo/columnas")
    assert r.status_code == 200
    assert r.json()["columnas"] == {}
