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


def test_filas_con_datos_faltantes_entran_vacias_y_no_inventadas():
    """Criterio de MARIA-1a: lo que falta o no se puede leer queda vacío (0 o
    ""), la fila no se pierde y no se inventa nada (ni cantidad 1 ni «XX»).
    El semáforo de la revisión marca lo vacío."""
    r = _subir([H,
                ["84713000", "Laptop 14 pulgadas", "CN", 10, 350, 1.5],
                ["85171300", "Telefono celular", "", 20, 100, 0.2],
                ["85176200", "Router", "CN", "diez", 50, 0.3],
                [None, "Mouse (sin NCM aun)", "CN", 100, 5, 0.1],
                [None, None, None, None, None, None]])
    assert r.status_code == 200, r.text[:300]
    items = r.json()["items"]
    assert [i["descripcion"] for i in items] == [
        "Laptop 14 pulgadas", "Telefono celular", "Router", "Mouse (sin NCM aun)"], items
    assert items[1]["origen"] == "", items[1]
    assert items[2]["cantidad"] == 0, items[2]
    assert items[3]["pieza"] == "", items[3]
    assert r.json().get("filas_descartadas") == 0, r.json()


def test_filas_sin_descripcion_ni_ncm_se_avisan():
    r = _subir([H,
                ["84713000", "Laptop 14 pulgadas", "CN", 10, 350, 1.5],
                [None, None, "CN", 5, 20, 0.1]])
    assert r.status_code == 200, r.text[:300]
    assert len(r.json()["items"]) == 1
    assert r.json().get("filas_descartadas") == 1, r.json()
    assert r.json().get("filas_descartadas_numeros") == [3], r.json()


@pytest.mark.parametrize("texto,esperado", [
    ("1.500", 0), ("1.234,56", 1234.56), ("1,5", 1.5), ("10 pcs", 10), ("USD 350", 350),
])
def test_numeros_escritos_como_texto(texto, esperado):
    """Con la regla de MARIA-1a: separador de miles, coma decimal, unidad de
    cuenta al lado. «1.500» sin otra pista en la planilla puede ser mil
    quinientos o uno y medio: queda vacío (0) en vez de adivinarse; antes
    salía 1,5."""
    r = _subir([H, ["84713000", "Laptop 14 pulgadas", "CN", texto, 350, 1.5]])
    assert r.status_code == 200, r.text[:300]
    assert r.json()["items"][0]["cantidad"] == esperado, r.json()["items"][0]


def test_ncm_numerica_no_sale_con_punto_cero():
    r = _subir([H,
                [84713000, "Laptop 14 pulgadas", "CN", 10, 350, 1.5],
                [None, None, None, None, None, None],
                [85171300, "Telefono celular", "CN", 20, 100, 0.2]])
    assert r.status_code == 200, r.text[:300]
    assert [i["pieza"] for i in r.json()["items"]] == ["84713000", "85171300"], r.json()["items"]


@pytest.mark.parametrize("pais,codigo", [
    ("China", "CN"), ("Chile", "CL"), ("Argentina", "AR"), ("CHN", "CN"), ("Narnia", ""),
])
def test_pais_por_nombre_no_se_corta(pais, codigo):
    r = _subir([H, ["84713000", "Laptop 14 pulgadas", pais, 10, 350, 1.5]])
    assert r.status_code == 200, r.text[:300]
    assert r.json()["items"][0]["origen"] == codigo, r.json()["items"][0]


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


def test_miles_con_pista_en_la_planilla():
    """Si otro número de la planilla muestra la coma decimal («350,00»), el
    «1.500» es mil quinientos."""
    r = _subir([H, ["84713000", "Laptop 14 pulgadas", "CN", "1.500", "350,00", "1,5"]])
    assert r.status_code == 200, r.text[:300]
    item = r.json()["items"][0]
    assert (item["cantidad"], item["valor_unitario"], item["peso_unitario"]) == (1500, 350, 1.5), item


@pytest.mark.parametrize("ruta", ["/upload_excel/", "/upload_excel/public", "/api/clientes/import"])
def test_rutas_de_excel_sin_llamador_ya_no_existen(ruta):
    """D13: sin pantalla que las use, se borran (no llegaban al TXT)."""
    r = TestClient(main.app).post(ruta, files={"file": ("a.xlsx", _xlsx([H]), "application/octet-stream")})
    assert r.status_code in (404, 405), f"{ruta}: {r.status_code}"
