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
    # Respuesta 3 del despachante y D23 de la Dev 2 (regla de MARIA-5): el neto
    # y el total son de la línea y se dividen por la cantidad; neto > total > de
    # una unidad > bruto.
    assert r.json()["items"][0]["peso_unitario"] == 1.5, r.json()["items"][0]


def test_peso_bruto_o_total_no_se_toma_como_peso_unitario():
    """El bruto o el total no entran como peso de una unidad: se dividen por la
    cantidad, y el bruto, con aviso (respuesta 3 del despachante y D23 de la
    Dev 2, que reemplazan lo de EXCEL-1: quedaba vacío)."""
    for col in ("Peso Bruto", "Peso Total"):
        r = _subir([["NCM", "Descripcion", "Origen", "Cantidad", "Precio Unitario", col],
                    ["84713000", "Laptop 14 pulgadas", "CN", 10, 350, 25]])
        assert r.status_code == 200, (col, r.text[:300])
        assert r.json()["items"][0]["peso_unitario"] == 2.5, (col, r.json()["items"][0])
        if col == "Peso Bruto":
            assert any("bruto" in a for a in r.json()["avisos"]), r.json()["avisos"]


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
    # Respuesta 3 del despachante y D23 de la Dev 2 (regla de MARIA-5): el neto
    # y el total son de la línea y se dividen por la cantidad; neto > total > de
    # una unidad > bruto.
    assert (item["cantidad"], item["valor_unitario"], item["peso_unitario"]) == (10, 350, 0.15), item


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
    # Respuesta 3 del despachante y D23 de la Dev 2 (regla de MARIA-5): el neto
    # y el total son de la línea y se dividen por la cantidad; neto > total > de
    # una unidad > bruto.
    assert (item["cantidad"], item["peso_unitario"]) == (10, 0.15), item


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
    # Respuesta 3 del despachante y D23 de la Dev 2 (regla de MARIA-5): el neto
    # y el total son de la línea y se dividen por la cantidad; neto > total > de
    # una unidad > bruto.
    assert r.json()["items"][0]["peso_unitario"] == 0.15, r.json()["items"]


def test_el_indice_del_xlsx_se_mira_fuera_del_hilo_del_servidor(monkeypatch):
    from proyecto_maria.security import file_security
    hilos = []
    original = file_security._excel_descomprimido_bytes

    def _espia(contents):
        # ¿Corre dentro del bucle que atiende los pedidos?
        try:
            asyncio.get_running_loop()
            hilos.append(True)
        except RuntimeError:
            hilos.append(False)
        return original(contents)
    monkeypatch.setattr(file_security, "_excel_descomprimido_bytes", _espia)
    r = _subir([H, ["84713000", "Laptop", "CN", 10, 350, 1.5]])
    assert r.status_code == 200, r.text[:300]
    assert hilos == [False], hilos


def test_peso_ambiguo_entre_parentesis_queda_vacio_y_no_se_adivina():
    """«Peso (kg)» y «Peso (bruto)»: no se elige por el orden de las columnas.
    Con la regla de MARIA-5 (respuesta 3 y D23: de una unidad > bruto) se usa
    «Peso (kg)» y el aviso nombra el bruto ignorado (antes quedaba vacío)."""
    r = _subir([["NCM", "Descripcion", "Origen", "Cantidad", "Precio Unitario", "Peso (bruto)", "Peso (kg)"],
                ["84713000", "Laptop", "CN", 10, 350, 2.2, 1.5]])
    assert r.status_code == 200, r.text[:300]
    assert r.json()["items"][0]["peso_unitario"] == 1.5, r.json()["items"]
    assert any("«Peso (bruto)»" in a for a in r.json()["avisos"]), r.json()["avisos"]


# ---- Devolución de la PM (2026-10-07) ----

def test_mapeo_aprendido_no_pisa_el_precio_unitario_ni_el_peso_neto():
    """Con cliente_id, como manda la pantalla: «Valor» y «Peso» aprendidos con
    la lista vieja no pisan «Precio Unitario» ni «Peso Neto»."""
    cid = _cliente_con_mapeo({"NCM": "pieza", "Descripcion": "descripcion", "Origen": "origen",
                              "Cantidad": "cantidad", "Valor": "valor_unitario", "Peso": "peso_unitario"})
    r = _subir([["NCM", "Descripcion", "Origen", "Cantidad", "Precio Unitario", "Valor", "Peso", "Peso Neto"],
                ["84713000", "Laptop", "CN", 10, 350, 3500, 25, 15]], cliente_id=cid)
    assert r.status_code == 200, r.text[:300]
    item = r.json()["items"][0]
    # Respuesta 3 del despachante y D23 de la Dev 2 (regla de MARIA-5): el neto
    # y el total son de la línea y se dividen por la cantidad; neto > total > de
    # una unidad > bruto.
    assert (item["valor_unitario"], item["peso_unitario"]) == (350, 1.5), item


def test_validar_el_excel_usa_su_propio_grupo_de_hilos(monkeypatch):
    import threading
    from proyecto_maria.security import file_security
    hilos = []
    original = file_security._abrir_excel

    def _espia(*a):
        hilos.append(threading.current_thread().name)
        return original(*a)
    monkeypatch.setattr(file_security, "_abrir_excel", _espia)
    r = _subir([H, ["84713000", "Laptop", "CN", 10, 350, 1.5]])
    assert r.status_code == 200, r.text[:300]
    assert len(hilos) == 1 and hilos[0].startswith("validar-excel"), hilos


def test_la_fila_de_ejemplo_de_la_plantilla_no_entra():
    r = _subir([H,
                ["84713000", "Laptop 14 pulgadas modelo X", "CN", 10, 350.0, 1.5],
                ["85171300", "Telefono", "CN", 5, 100, 0.2]])
    assert r.status_code == 200, r.text[:300]
    assert [i["descripcion"] for i in r.json()["items"]] == ["Telefono"], r.json()["items"]


def test_catalogo_con_dos_columnas_para_el_mismo_campo_no_se_guarda():
    cid = _cliente_con_mapeo({})
    r = TestClient(main.app).put(f"/api/clientes/{cid}/catalogo/columnas",
                                 json={"columnas": {"Precio": "valor_unitario", "Valor": "valor_unitario"}})
    assert r.status_code == 400, r.text[:300]
    assert "Dos columnas" in r.json()["detail"], r.json()


def test_mapeo_viejo_con_dos_columnas_para_el_mismo_campo_avisa_y_no_da_500():
    cid = _cliente_con_mapeo({"Precio": "valor_unitario", "Importe": "valor_unitario"})
    r = _subir([["NCM", "Descripcion", "Origen", "Cantidad", "Precio", "Importe", "Peso Neto"],
                ["84713000", "Laptop", "CN", 10, 350, 3500, 1.5]], cliente_id=cid)
    assert r.status_code == 200, r.text[:300]
    assert r.json()["items"][0]["valor_unitario"] == 350, r.json()["items"]
    assert any("dos columnas" in a for a in r.json()["avisos_mapeo"]), r.json()


def test_columna_con_el_nombre_del_campo_y_mapeo_a_otra_no_da_500():
    """Corrección a mano con un nombre propio («Unidades pedidas») y el
    archivo trae además una columna «cantidad»: manda la corrección."""
    cid = _cliente_con_mapeo({"Unidades pedidas": "cantidad"})
    r = _subir([["NCM", "Descripcion", "Origen", "cantidad", "Unidades pedidas", "Precio Unitario", "Peso Neto"],
                ["84713000", "Laptop", "CN", 1, 10, 350, 1.5]], cliente_id=cid)
    assert r.status_code == 200, r.text[:300]
    assert r.json()["items"][0]["cantidad"] == 10, r.json()["items"]


def test_lo_que_llamaba_a_las_rutas_borradas():
    import pathlib
    raiz = pathlib.Path(main.__file__).resolve().parent.parent
    app_js = (raiz / "proyecto_maria/static/app.js").read_text(encoding="utf-8")
    assert "/upload_excel/public" not in app_js
    assert "El Excel se sube en la pantalla nueva" in app_js
    smoke = (raiz / "scripts/testing/smoke_test.sh").read_text(encoding="utf-8")
    assert '/upload_excel"' not in smoke and "/upload_excel_v2/" in smoke


@pytest.mark.parametrize("usar_mapeo,cantidad,estado", [
    (None, 10, 200), ("true", 10, 200), ("false", 1, 200), ("invalido", None, 422),
])
def test_use_mapping_conserva_default_y_booleanos_explicitos(usar_mapeo, cantidad, estado):
    cid = _cliente_con_mapeo({"Unidades pedidas": "cantidad"})
    form = {"cliente_id": cid}
    if usar_mapeo is not None:
        form["use_mapping"] = usar_mapeo
    r = _subir([["NCM", "Descripcion", "Origen", "cantidad", "Unidades pedidas", "Precio Unitario", "Peso Neto"],
                ["84713000", "Laptop sintetica", "CN", 1, 10, 350, 1.5]], **form)
    assert r.status_code == estado, r.text[:300]
    if estado == 200:
        assert r.json()["items"][0]["cantidad"] == cantidad, r.json()["items"]
    else:
        assert r.json()["detail"][0]["loc"] == ["body", "use_mapping"]
