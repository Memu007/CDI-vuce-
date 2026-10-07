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


def test_extraccion_con_ncm_leida_como_numero_decimal():
    """Si la planilla llega con la NCM como número decimal (84713000.0, lo que
    hace pandas con una fila vacía en el medio si no se lee como texto), sale
    sin «.0»."""
    import pandas as pd
    df = pd.DataFrame({"pieza": [84713000.0, float("nan"), 85171300.0],
                       "descripcion": ["Laptop", None, "Telefono"],
                       "origen": ["CN", None, "CN"], "cantidad": [1.0, None, 2.0],
                       "valor_unitario": [10.0, None, 20.0], "peso_unitario": [1.0, None, 2.0]})
    items = main.extract_items_from_excel(df, "x.xlsx")
    assert [i.pieza for i in items] == ["84713000", "85171300"]


def test_productos_que_empiezan_con_total_no_se_pierden():
    r = _subir([H,
                ["84713000", "Laptop", "CN", 10, 350, 1.5],
                ["27101932", "TOTAL QUARTZ 9000 5W40 4L", "FR", 200, 12.5, 3.6],
                ["90158090", "Total Station Leica TS07", "CH", 1, 9800, 5],
                ["TOTAL-XL", "Camiseta total fit", "CN", 5, 10, 0.2],
                ["", "Subtotal 8471.30.00", "", 10, 3500, 15],
                ["", "TOTAL", "", 10, 3500, 15]])
    assert r.status_code == 200, r.text[:300]
    descripciones = [i["descripcion"] for i in r.json()["items"]]
    assert descripciones == ["Laptop", "TOTAL QUARTZ 9000 5W40 4L", "Total Station Leica TS07",
                             "Camiseta total fit"], descripciones


def test_total_flete_y_condiciones_no_son_productos():
    """«FOB TOTAL» es un total (no se cuenta); «Freight» y «Payment terms» sin
    NCM ni origen no son mercadería: no entran (sumarían al FOB) y se avisan."""
    r = _subir([H,
                ["84713000", "Laptop", "CN", 10, 350, 1.5],
                ["", "FOB TOTAL", "", 10, 3500, 15],
                ["", "Freight", "", 1, 500, None],
                ["", "Payment terms: T/T 30 days", "", None, None, None]])
    assert r.status_code == 200, r.text[:300]
    assert [i["descripcion"] for i in r.json()["items"]] == ["Laptop"], r.json()["items"]
    assert r.json()["filas_descartadas_numeros"] == [4, 5], r.json()


def test_mapeo_corregido_a_mano_gana_sobre_lo_detectado():
    """El usuario corrigió en su catálogo que el precio unitario es «Precio
    Unit. USD»; el archivo también trae «Valor» (el total de la fila)."""
    cid = _cliente_con_mapeo({"Precio Unit. USD": "valor_unitario"})
    r = _subir([["NCM", "Descripcion", "Origen", "Cantidad", "Precio Unit. USD", "Valor", "Peso Neto"],
                ["84713000", "Laptop", "CN", 10, 350, 3500, 1.5]], cliente_id=cid)
    assert r.status_code == 200, r.text[:300]
    assert r.json()["items"][0]["valor_unitario"] == 350, r.json()["items"]


def test_celda_en_la_ultima_fila_no_recorre_un_millon_de_filas():
    import openpyxl, time as _t
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(H)
    ws.append(["84713000", "Laptop", "CN", 10, 350, 1.5])
    ws.cell(row=1048576, column=7, value="x")
    buf = io.BytesIO()
    wb.save(buf)
    t0 = _t.monotonic()
    r = TestClient(main.app).post("/upload_excel_v2/", files={"file": ("p.xlsx", buf.getvalue(), "application/octet-stream")})
    demora = _t.monotonic() - t0
    assert r.status_code == 200, r.text[:300]
    assert len(r.json()["items"]) == 1
    assert demora < 8, f"tardó {demora:.1f} s"


def test_demasiadas_filas_se_rechazan_con_mensaje_claro(monkeypatch):
    monkeypatch.setattr(main, "_MAX_FILAS_EXCEL", 3)
    filas = [H] + [["84713000", f"Laptop {i}", "CN", 1, 10, 1] for i in range(5)]
    r = _subir(filas)
    assert r.status_code == 400, r.text[:300]
    assert "filas" in r.json()["detail"], r.json()


def test_xlsx_que_se_descomprime_a_gigas_se_rechaza_antes_de_abrirlo(monkeypatch):
    import zipfile
    from proyecto_maria.security import file_security
    abrir = []
    monkeypatch.setattr(file_security, "_contar_hojas_excel", lambda *a: abrir.append(1) or 1)
    # Un .xlsx de verdad (pasa el control de tipo) con un relleno que
    # descomprimido ocupa 150 MB.
    import openpyxl
    sano = io.BytesIO()
    openpyxl.Workbook().save(sano)
    original = zipfile.ZipFile(io.BytesIO(sano.getvalue()))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre in original.namelist():
            z.writestr(nombre, original.read(nombre))
        z.writestr("xl/relleno.xml", " " * (150 * 1024 * 1024))
    r = TestClient(main.app).post("/upload_excel_v2/", files={"file": ("bomba.xlsx", buf.getvalue(), "application/octet-stream")})
    assert r.status_code == 400, r.text[:300]
    assert "descomprimido" in r.json()["detail"], r.json()
    assert not abrir, "se abrió el Excel antes de mirar cuánto pesa descomprimido"


def test_mapeo_guardado_completa_lo_que_no_se_detecta():
    """Lo detectado gana, pero una columna que sólo el cliente sabe qué es
    («Glosa» para la descripción) se sigue tomando de su mapeo guardado."""
    cid = _cliente_con_mapeo({"Glosa": "descripcion"})
    r = _subir([["NCM", "Glosa", "Origen", "Cantidad", "Precio Unitario", "Peso Neto"],
                ["84713000", "Laptop", "CN", 10, 350, 1.5]], cliente_id=cid)
    assert r.status_code == 200, r.text[:300]
    assert r.json()["items"][0]["descripcion"] == "Laptop", r.json()["items"]


def test_productos_sin_ncm_ni_origen_entran_aunque_otra_fila_los_traiga():
    """Factura con la NCM vacía (la completa el despachante) y el origen sólo
    en una fila: entran todos, con lo que falta vacío."""
    r = _subir([H,
                ["", "Valvula esfera 1/2", "", 10, 12, 0.3],
                ["", "Valvula esfera 3/4", "", 10, 15, 0.4],
                ["", "Junta torica", "IN", 100, 0.2, 0.01]])
    assert r.status_code == 200, r.text[:300]
    assert [i["descripcion"] for i in r.json()["items"]] == [
        "Valvula esfera 1/2", "Valvula esfera 3/4", "Junta torica"], r.json()["items"]
    assert r.json()["filas_descartadas"] == 0, r.json()


@pytest.mark.parametrize("total", ["TOTAL USD", "Total FOB", "TOTAL (USD)", "Totale", "合计",
                                   "Summe", "Gesamt", "Grand Total:", "TOTAL DE LA FACTURA"])
def test_filas_de_total_con_moneda_o_idioma_no_entran(total):
    r = _subir([H,
                ["", "Valvula esfera 1/2", "", 10, 12, 0.3],
                ["", total, "", 10, 120, 3]])
    assert r.status_code == 200, r.text[:300]
    assert [i["descripcion"] for i in r.json()["items"]] == ["Valvula esfera 1/2"], r.json()["items"]


def test_total_en_la_columna_de_codigo_no_entra():
    r = _subir([H,
                ["A-001", "LED panel 60x60", "CN", 100, 2.5, 0.5],
                ["TOTAL AMOUNT", None, None, 100, None, 50]])
    assert r.status_code == 200, r.text[:300]
    assert [i["pieza"] for i in r.json()["items"]] == ["A-001"], r.json()["items"]


def test_peso_neto_y_bruto_entre_parentesis_no_se_confunden():
    r = _subir([["NCM", "Descripcion", "Origen", "Cantidad", "Precio Unitario", "Peso (neto)", "Peso (bruto)"],
                ["84713000", "Laptop", "CN", 10, 350, 1.5, 2.2]])
    assert r.status_code == 200, r.text[:300]
    assert r.json()["items"][0]["peso_unitario"] == 1.5, r.json()["items"]


def test_el_indice_del_xlsx_se_mira_fuera_del_hilo_del_servidor(monkeypatch):
    import threading
    from proyecto_maria.security import file_security
    hilos = []
    original = file_security._excel_descomprimido_bytes

    def _espia(contents):
        hilos.append(threading.current_thread() is threading.main_thread())
        return original(contents)
    monkeypatch.setattr(file_security, "_excel_descomprimido_bytes", _espia)
    r = _subir([H, ["84713000", "Laptop", "CN", 10, 350, 1.5]])
    assert r.status_code == 200, r.text[:300]
    assert hilos == [False], hilos
