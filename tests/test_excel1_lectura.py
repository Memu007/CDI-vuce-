"""EXCEL-1: /upload_excel_v2/ lee bien la planilla (el único camino al TXT).

Cada caso sale del relevamiento de EXCEL-1: con el Excel armado, lo que la
ruta devuelve antes y lo que tiene que devolver.
"""
import asyncio
import io
import uuid

import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main

USUARIO = {"username": "exc1l", "roles": ["operador"], "effective_owner": "exc1l",
           "plan": "premium", "billing_status": "active"}
H = ["pieza", "descripcion", "origen", "cantidad", "valor_unitario", "peso_unitario"]


def _xlsx(filas) -> bytes:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    for f in filas:
        ws.append(f)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture(autouse=True)
def _entorno(monkeypatch):
    from proyecto_maria.core.rate_limit import limiter
    monkeypatch.setattr(limiter, "enabled", False)
    main.app.dependency_overrides[main.get_current_user] = lambda: dict(USUARIO)
    yield
    main.app.dependency_overrides.pop(main.get_current_user, None)


def _subir(filas, nombre="planilla.xlsx", **form):
    r = TestClient(main.app).post(
        "/upload_excel_v2/", data=form,
        files={"file": (nombre, _xlsx(filas),
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    return r


def test_precio_unitario_gana_sobre_valor_total():
    r = _subir([["NCM", "Descripcion", "Origen", "Cantidad", "Precio Unitario", "Valor", "Peso"],
                ["84713000", "Laptop 14 pulgadas", "CN", 10, 350, 3500, 1.5]])
    assert r.status_code == 200, r.text[:300]
    assert r.json()["items"][0]["valor_unitario"] == 350, r.json()["items"][0]


def test_peso_neto_gana_sobre_bruto():
    r = _subir([["NCM", "Descripcion", "Origen", "Cantidad", "Precio Unitario", "Peso Bruto", "Peso Neto"],
                ["84713000", "Laptop 14 pulgadas", "CN", 10, 350, 25, 15]])
    assert r.status_code == 200, r.text[:300]
    assert r.json()["items"][0]["peso_unitario"] == 15, r.json()["items"][0]


def test_peso_bruto_o_total_no_se_toma_como_peso_unitario():
    """Sin peso neto ni unitario, el peso queda vacío (0) y la fila igual entra:
    el TXT lo frena con «Peso inválido» y el usuario lo completa."""
    for col in ("Peso Bruto", "Peso Total"):
        r = _subir([["NCM", "Descripcion", "Origen", "Cantidad", "Precio Unitario", col],
                    ["84713000", "Laptop 14 pulgadas", "CN", 10, 350, 25]])
        assert r.status_code == 200, (col, r.text[:300])
        assert r.json()["items"][0]["peso_unitario"] in (0, None), (col, r.json()["items"][0])


def test_fila_de_subtotal_no_entra_como_item():
    r = _subir([H,
                ["84713000", "Laptop 14 pulgadas", "CN", 10, 350, 1.5],
                ["84713000", "Subtotal 8471.30.00", "CN", 10, 3500, 15],
                ["", "TOTAL GENERAL", "CN", 10, 3500, 15]])
    assert r.status_code == 200, r.text[:300]
    descripciones = [i["descripcion"] for i in r.json()["items"]]
    assert descripciones == ["Laptop 14 pulgadas"], descripciones


def test_extension_en_mayusculas():
    r = _subir([H, ["84713000", "Laptop 14 pulgadas", "CN", 10, 350, 1.5]], nombre="OPERACION.XLSX")
    assert r.status_code == 200, r.text[:300]


def test_encabezados_con_unidades_entre_parentesis():
    r = _subir([["Posición Arancelaria", "Descripción", "País", "Cant.", "Precio Unitario (USD)", "Peso Neto (kg)"],
                ["84713000", "Laptop 14 pulgadas", "CN", 10, 350, 1.5]])
    assert r.status_code == 200, r.text[:300]
    item = r.json()["items"][0]
    assert (item["cantidad"], item["valor_unitario"], item["peso_unitario"]) == (10, 350, 1.5), item


def test_filas_descartadas_se_avisan():
    r = _subir([H,
                ["84713000", "Laptop 14 pulgadas", "CN", 10, 350, 1.5],
                ["85171300", "Telefono celular", "", 20, 100, 0.2],
                ["85176200", "Router", "CN", "diez", 50, 0.3],
                [None, None, None, None, None, None]])
    assert r.status_code == 200, r.text[:300]
    cuerpo = r.json()
    assert len(cuerpo["items"]) == 1
    assert cuerpo.get("filas_descartadas") == 2, cuerpo


def _cliente_con_mapeo(mapeo) -> str:
    from proyecto_maria.database.connection import AsyncSessionLocal
    from proyecto_maria.database.models import Client

    cid = str(uuid.uuid4())

    async def _crear():
        async with AsyncSessionLocal() as s:
            s.add(Client(id=cid, owner_username=USUARIO["username"], name="Cliente Excel",
                         cuit="30712345678", column_mapping=mapeo))
            await s.commit()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_crear())
    finally:
        loop.close()
    return cid


def test_mapeo_guardado_no_deja_afuera_encabezados_nuevos():
    """El cliente aprendió «Cantidad» y «Peso Bruto»; ahora sube «Qty» y
    «Peso Neto». Lo detectado completa lo que el mapeo no cubre."""
    cid = _cliente_con_mapeo({"Cantidad": "cantidad", "Peso Bruto": "peso_unitario",
                              "NCM": "pieza", "Descripcion": "descripcion",
                              "Origen": "origen", "Precio": "valor_unitario"})
    r = _subir([["NCM", "Descripcion", "Origen", "Qty", "Precio", "Peso Neto"],
                ["84713000", "Laptop 14 pulgadas", "CN", 10, 350, 1.5]], cliente_id=cid)
    assert r.status_code == 200, r.text[:300]
    item = r.json()["items"][0]
    assert (item["cantidad"], item["peso_unitario"]) == (10, 1.5), item
