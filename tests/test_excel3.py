"""EXCEL-3 (2026-10-24): la proforma china se lee tal como viene.

El 24/10 una proforma .xls de un proveedor chino dio «No se pudieron extraer
items». El sintético (`tests/proforma_china_sintetica.py`) tiene su misma
forma con datos inventados; la real no entra al repositorio.
"""
import os

import pytest
from fastapi.testclient import TestClient

from proyecto_maria import main
from tests import proforma_china_sintetica as pi
from tests.test_excel1_lectura import _cliente_con_mapeo, _entorno  # noqa: F401
from tests.test_excel2 import _libro

XLS = os.path.join(os.path.dirname(__file__), "fixtures", "proforma_china_sintetica.xls")


def _subir(contenido: bytes, nombre: str, **form):
    return TestClient(main.app).post(
        "/upload_excel_v2/", data=form,
        files={"file": (nombre, contenido, "application/octet-stream")})


def _subir_xls(**form):
    with open(XLS, "rb") as f:
        return _subir(f.read(), "proforma.xls", **form)


def _como_se_lee(data: dict) -> None:
    """Lo que tiene que devolver la proforma, en .xls o .xlsx."""
    items, op = data["items"], data["operacion"]
    esperados = pi.renglones()
    # 2. Cada renglón es un producto, con su grupo, su ancho y su largo.
    assert len(items) == len(esperados) == 48, [i["descripcion"] for i in items]
    for it, r in zip(items, esperados):
        ancho = f"{r['ancho']:g}".replace(".", ",")
        assert it["descripcion"] == f"{r['espec']}, ancho {ancho} m x largo {r['largo']} m", it
        assert it["codigo_parte"] == r["codigo"], it
        # 6. «1st container» no es un código; la proforma no trae NCM.
        assert it["pieza"] == "", it
        # 3. La cantidad está en la unidad del precio (m²), no en rollos.
        assert it["cantidad"] == pytest.approx(r["m2"]) and it["valor_unitario"] == pytest.approx(r["precio"]), it
        assert it.get("unidad") == "m2", it
        # 4. El bruto es de toda la línea: por m², multiplicado da el de la línea.
        assert it["peso_unitario"] * it["cantidad"] == pytest.approx(r["bruto"]), it
    # Lo que suman los productos es la mercadería de la proforma, sin flete
    # ni descuento ni totales.
    assert sum(i["cantidad"] * i["valor_unitario"] for i in items) == pytest.approx(
        sum(r["importe"] for r in esperados))
    # 5. El flete y el descuento se ofrecen en la operación, leídos.
    assert op["flete"] == pi.FLETE and op["descuento"] == -pi.DESCUENTO, op
    fila_total = pi.FILA_ENCABEZADO + len(esperados) + 1
    assert op["filas_excel_descuento"] == [fila_total + 1], op
    assert op["filas_excel_flete"] == [fila_total + 2], op
    # Sin leer, sólo el texto del pago y el banco, que no tiene números.
    assert op.get("filas_excel_sin_leer") == [fila_total + 5, fila_total + 6, fila_total + 7], op
    avisos = " | ".join(data["avisos_mapeo"])
    assert "«SM.TOTAL (sqm)»" in avisos and "«QTY (Rolls)»" in avisos, avisos
    assert "Flete" in avisos and "Descuento" in avisos, avisos


def test_la_proforma_xls_se_lee_tal_como_viene():
    r = _subir_xls()
    assert r.status_code == 200, r.text[:300]
    _como_se_lee(r.json())


@pytest.mark.parametrize("etiquetas_en", [0, 2], ids=["en_item", "en_specification"])
def test_la_proforma_xlsx_se_lee_igual(etiquetas_en):
    """Total, Discount y Freight en la columna Item o en Specification."""
    r = _subir(_libro(pi.filas(etiquetas_en)), "proforma.xlsx")
    assert r.status_code == 200, r.text[:300]
    _como_se_lee(r.json())


def test_con_la_especificacion_combinada_hacia_abajo_cada_renglon_conserva_su_codigo():
    """En .xlsx el grupo suele venir combinado (C12:C23): la descripción se
    copia por la combinada y el código sale del primer renglón."""
    desde = pi.FILA_ENCABEZADO + 1
    combinar = tuple(f"{col}{desde + 12 * g}:{col}{desde + 12 * g + 11}"
                     for g in range(len(pi.GRUPOS)) for col in "BC")
    r = _subir(_libro(pi.filas(), combinar=combinar), "proforma.xlsx")
    assert r.status_code == 200, r.text[:300]
    _como_se_lee(r.json())


def test_el_xls_guardado_es_el_sintetico():
    """El .xls de fixtures se escribió con `filas()`: si cambia uno, el otro."""
    import xlrd
    hoja = xlrd.open_workbook(XLS).sheet_by_index(0)
    for i, fila in enumerate(pi.filas()):
        leida = hoja.row_values(i) if i < hoja.nrows else []
        leida = [None if v == "" else v for v in leida]
        leida += [None] * (len(fila) - len(leida))
        assert [v for v in leida[:len(fila)]] == fila, i + 1
        assert all(v is None for v in leida[len(fila):]), i + 1
    assert hoja.nrows == len(pi.filas())


def test_el_mapeo_guardado_con_la_cantidad_en_rollos_no_gana():
    """Un cliente que aprendió «QTY (Rolls)» como cantidad antes de EXCEL-3:
    con el precio por m², la cantidad sigue siendo la de m²."""
    cid = _cliente_con_mapeo({"QTY (Rolls)": "cantidad"})
    r = _subir_xls(cliente_id=cid)
    assert r.status_code == 200, r.text[:300]
    _como_se_lee(r.json())
    # Sin el aviso viejo que decía que se usó la de rollos.
    assert not any("se usó la columna «QTY (Rolls)»" in a for a in r.json()["avisos_mapeo"]), r.json()["avisos_mapeo"]


# ------------------------------------------------- lo que no se hereda

E = ["Part No.", "Specification", "Width(m)", "Length (m)", "QTY (Rolls)", "SM.TOTAL (sqm)",
     "Unit price (USD/sqm)", "Total Amount(USD)"]


def test_un_subtotal_sin_rotulo_ni_medidas_no_es_un_producto():
    """Sin medidas propias un renglón no hereda la descripción de arriba:
    un subtotal sin rótulo se avisa como fila sin leer, no suma al FOB."""
    r = _subir(_libro([
        E,
        ["DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
        [None, None, 2, 15, 1, 30, 1.5, 45],
        [None, None, None, None, 2, 50, None, 75],
    ]), "p.xlsx")
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert [i["cantidad"] for i in data["items"]] == [20, 30], data["items"]
    assert data["filas_descartadas_numeros"] == [4], data


def test_un_renglon_con_precio_y_sin_medidas_no_hereda():
    """Con su precio pero sin medidas propias tampoco hereda: sólo un renglón
    con su largo es del grupo (EXCEL-3b separa esto del precio)."""
    data = _leer([
        E,
        ["DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
        [None, None, 2, 15, 1, 30, 1.5, 45],
        [None, None, None, None, 2, 50, 1.5, 75],
    ])
    assert [i["cantidad"] for i in data["items"]] == [20, 30], data["items"]
    assert data["filas_descartadas_numeros"] == [4], data


def test_un_flete_sin_monto_no_hereda_la_descripcion_del_grupo():
    """«Freight cost» en la columna Item, con cantidad y sin monto: no es un
    renglón del grupo de arriba ni un flete; queda como fila sin leer."""
    r = _subir(_libro([
        ["Item"] + E,
        [1, "DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
        ["Freight cost", None, None, None, None, 1, 1, None, None],
    ]), "p.xlsx")
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert [i["descripcion"] for i in data["items"]] == ["LONA DEMO"], data["items"]
    assert "flete" not in data["operacion"], data["operacion"]
    assert data["filas_descartadas_numeros"] == [3], data


def test_un_precio_por_unidad_sin_otra_columna_no_cambia_la_cantidad():
    """Precio por pieza y una cantidad que no dice su unidad: como antes, sin
    aviso ni unidad (el TXT declara unidad)."""
    r = _subir(_libro([
        ["NCM", "Descripcion", "Qty", "Unit price (USD/pcs)"],
        ["84713000", "LAPTOP DEMO", 10, 350],
    ]), "p.xlsx")
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data["items"][0]["cantidad"] == 10 and "unidad" not in data["items"][0], data["items"]
    assert not any("cantidad" in a.lower() for a in data["avisos_mapeo"]), data["avisos_mapeo"]


def test_precio_por_kilo_no_toma_el_peso_como_cantidad():
    """El bruto en kilos no es lo vendido (y el neto es el peso): la cantidad
    queda la de la planilla y se avisa."""
    r = _subir(_libro([
        ["NCM", "Descripcion", "Cantidad (bags)", "Unit price (USD/kg)", "Net Weight (kg)",
         "Gross Weight (kg)"],
        ["11010000", "HARINA DEMO", 40, 0.5, 1000, 1010],
    ]), "p.xlsx")
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert data["items"][0]["cantidad"] == 40 and "unidad" not in data["items"][0], data["items"]
    assert any("por kg" in a for a in data["avisos_mapeo"]), data["avisos_mapeo"]


def test_un_descuento_negativo_en_el_precio_sin_importe_tambien_se_lee():
    r = _subir(_libro([
        ["NCM", "Descripcion", "Cantidad", "Precio Unitario"],
        ["84713000", "LAPTOP DEMO", 10, 350],
        [None, "Discount", 1, -120.5],
    ]), "p.xlsx")
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert [i["descripcion"] for i in data["items"]] == ["LAPTOP DEMO"], data["items"]
    assert data["operacion"]["descuento"] == 120.5, data["operacion"]


# ------------------------------------------- autorrevisión (subagente y /code-review)

def _leer(filas):
    r = _subir(_libro(filas), "p.xlsx")
    assert r.status_code == 200, r.text[:300]
    return r.json()


def test_una_columna_cantidad_con_mayuscula_no_tapa_la_de_m2():
    """«Cantidad» y el precio por m²: antes quedaba la de rollos con un aviso
    que decía lo contrario (FOB de 6,75 en vez de 216)."""
    data = _leer([
        ["Part No.", "Specification", "Width(m)", "Length (m)", "Cantidad", "SM.TOTAL (sqm)",
         "Unit price (USD/sqm)", "Total Amount(USD)"],
        ["A1", "LONA", 3.2, 10, 5, 160, 1.35, 216],
    ])
    assert data["items"][0]["cantidad"] == 160 and data["items"][0]["unidad"] == "m2", data["items"]


def test_un_producto_que_empieza_con_discount_sigue_siendo_producto():
    data = _leer([
        ["Descripcion", "Cantidad", "Precio Unitario"],
        ["Laptop", 10, 350],
        ["Discount tag labels", 100, 2.5],
        ["Rebate pad", 10, 35],
    ])
    assert [i["descripcion"] for i in data["items"]] == ["Laptop", "Discount tag labels", "Rebate pad"], data
    assert "descuento" not in data["operacion"], data["operacion"]


def test_un_descuento_en_porcentaje_no_se_lee_como_monto_ni_como_producto():
    data = _leer([
        ["NCM", "Descripcion", "Cantidad", "Precio Unitario"],
        ["84713000", "Laptop", 10, 350],
        [None, "Discount 5%", None, 5],
    ])
    assert [i["descripcion"] for i in data["items"]] == ["Laptop"], data["items"]
    assert "descuento" not in data["operacion"], data["operacion"]
    assert data["filas_descartadas_numeros"] == [3], data


def test_mt_no_se_declara_como_metros():
    """«MT» en comercio exterior es tonelada métrica: no se adivina."""
    data = _leer([
        ["NCM", "Description", "Origin", "Quantity (MT)", "Unit price (USD/MT)"],
        ["39021000", "PP RESIN DEMO", "CN", 25, 1200],
    ])
    assert data["items"][0]["cantidad"] == 25 and "unidad" not in data["items"][0], data["items"]


@pytest.mark.parametrize("encabezado, fila, cantidad", [
    (["Description", "Width(m)", "Length (m)", "Area per roll (sqm)", "QTY (Rolls)", "Unit price (USD/sqm)"],
     ["LONA DEMO", 3.2, 10, 32, 5, 1.35], 5),
    (["Description", "Length (m)", "QTY (Rolls)", "Unit price (USD/m)"], ["CABLE DEMO", 100, 5, 2.0], 5),
    (["Description", "Qty (cartons)", "Unit price (USD/pc)", "Pcs per carton (pcs)"], ["VASO DEMO", 10, 0.5, 100], 10),
], ids=["area_de_un_rollo", "largo_de_un_rollo", "piezas_por_caja"])
def test_la_medida_de_un_rollo_o_una_caja_no_es_la_cantidad(encabezado, fila, cantidad):
    """Sólo una columna de la línea («total») reemplaza la cantidad: con la de
    un rollo el FOB quedaba dividido por los rollos. Se avisa."""
    data = _leer([encabezado, fila])
    assert data["items"][0]["cantidad"] == cantidad and "unidad" not in data["items"][0], data["items"]
    assert any("revisá la cantidad" in a for a in data["avisos_mapeo"]), data["avisos_mapeo"]


def test_el_peso_bruto_abreviado_no_es_la_cantidad():
    data = _leer([
        ["Description", "Qty (bags)", "Unit price (USD/kg)", "Total G.W. (kgs)"],
        ["HARINA DEMO", 40, 0.5, 1010],
    ])
    assert data["items"][0]["cantidad"] == 40, data["items"]


def test_item_con_el_nombre_del_producto_sigue_siendo_la_descripcion():
    """«Item» con el nombre y «Specification» con el detalle técnico: el
    nombre no se pierde (en la proforma «Item» es «1st container» o un número)."""
    data = _leer([
        ["NCM", "Item", "Specification", "Origin", "Qty", "Price"],
        ["84137000", "Bomba centrifuga", "220V 1HP", "CN", 5, 100],
        ["84137000", "Bomba sumergible", "220V 2HP", "CN", 2, 150],
    ])
    assert [i["descripcion"] for i in data["items"]] == ["Bomba centrifuga", "Bomba sumergible"], data["items"]


def test_las_medidas_no_se_pegan_a_una_factura_comun():
    data = _leer([
        ["NCM", "Descripcion", "Origen", "Cantidad", "Precio", "Largo (mm)", "Ancho (mm)"],
        ["73064000", "Tubo acero", "CN", 10, 5, 6000, 100],
        ["73064000", "Tubo acero liviano", "CN", 10, 4, 6000, 80],
    ])
    assert [i["descripcion"] for i in data["items"]] == ["Tubo acero", "Tubo acero liviano"], data["items"]


def test_una_medida_larga_no_sale_en_notacion_cientifica():
    data = _leer([
        ["Part No.", "Specification", "Width(m)", "Length (m)", "SM.TOTAL (sqm)", "Unit price (USD/sqm)"],
        ["D1", "LONA DEMO", 2.123456, 1234567, 10, 1.5],
        [None, None, 2.123456, 15, 30, 1.5],
    ])
    assert data["items"][0]["descripcion"] == "LONA DEMO, ancho 2,123456 m x largo 1234567 m", data["items"]


@pytest.mark.parametrize("nota", ["Remarks", "Item"])
def test_una_nota_de_flete_en_otra_columna_de_un_renglon_no_lo_saca(nota):
    """En «Item» la nota sí cuenta como rótulo (ahí vienen Freight y Discount
    de la proforma), pero un renglón con sus medidas sigue siendo mercadería."""
    data = _leer([
        ["Part No.", "Specification", "Width(m)", "Length (m)", "SM.TOTAL (sqm)", "Unit price (USD/sqm)",
         "Total Amount(USD)", nota],
        ["D1", "LONA DEMO", 2, 10, 20, 1.5, 30, None],
        [None, None, 2, 15, 30, 1.5, 45, "Freight included"],
        [None, None, 2, 20, 40, 1.5, 60, "Discount 5% applied"],
    ])
    assert [i["cantidad"] for i in data["items"]] == [20, 30, 40], data["items"]
    assert "flete" not in data["operacion"] and "descuento" not in data["operacion"], data["operacion"]


def test_un_descuento_con_moneda_adelante_se_lee():
    data = _leer([
        ["NCM", "Descripcion", "Cantidad", "Precio Unitario", "Importe"],
        ["84713000", "Laptop", 10, 350, 3500],
        [None, "Discount", None, None, "USD -850"],
    ])
    assert [i["descripcion"] for i in data["items"]] == ["Laptop"], data["items"]
    assert data["operacion"]["descuento"] == 850, data["operacion"]


def test_un_flete_negativo_no_se_suma_como_flete():
    data = _leer([
        ["NCM", "Descripcion", "Cantidad", "Precio Unitario", "Importe"],
        ["84713000", "Laptop", 10, 350, 3500],
        [None, "Freight refund", None, None, -100],
    ])
    assert "flete" not in data["operacion"], data["operacion"]
    assert data["filas_descartadas_numeros"] == [3], data


def test_con_un_codigo_distinto_en_cada_renglon_la_descripcion_no_se_hereda():
    """Cambia a propósito en EXCEL-3b (#3): un código nuevo sin especificación
    es otro producto; no toma la del de arriba y queda sin leer, avisado."""
    data = _leer([
        ["Part No.", "Specification", "Width(m)", "Length (m)", "SM.TOTAL (sqm)", "Unit price (USD/sqm)"],
        ["D1-10", "LONA DEMO", 2, 10, 20, 1.5],
        ["D1-15", None, 2, 15, 30, 1.5],
    ])
    assert [i["codigo_parte"] for i in data["items"]] == ["D1-10"], data
    assert data["filas_descartadas_numeros"] == [3], data


# ------------------------------------------- EXCEL-3b (lo que dejó el adversario)

@pytest.mark.parametrize("subtotal", [
    [None, None, None, 25, 2, 50, None, 75],
    [None, None, 2, 25, 2, 50, None, 75],
], ids=["con_largo", "con_ancho_y_largo"])
def test_un_subtotal_sin_rotulo_ni_precio_con_medidas_no_es_un_producto(subtotal):
    """#2: sin precio propio un renglón no hereda el grupo aunque traiga un
    largo: queda sin leer, como en la base, y no suma cantidad."""
    data = _leer([
        E,
        ["DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
        [None, None, 2, 15, 1, 30, 1.5, 45],
        subtotal,
    ])
    assert [i["cantidad"] for i in data["items"]] == [20, 30], data["items"]
    assert data["filas_descartadas_numeros"] == [4], data


@pytest.mark.parametrize("monto, nota, campo", [
    (100, "Freight included", "flete"),
    (-50, "Discount", "descuento"),
], ids=["flete", "descuento"])
def test_un_texto_en_otra_columna_no_vuelve_flete_o_descuento_a_un_renglon(monto, nota, campo):
    """#5: «Freight included» o «Discount» en Remarks de un renglón sin
    descripción no es un flete ni un descuento: queda sin leer."""
    # Remarks antes del importe: el texto de la nota es el primero de la fila.
    data = _leer([
        ["NCM", "Descripcion", "Cantidad", "Precio Unitario", "Remarks", "Importe"],
        ["84713000", "Laptop", 10, 350, None, 3500],
        [None, None, None, None, nota, monto],
    ])
    assert campo not in data["operacion"], data["operacion"]
    assert data["filas_descartadas_numeros"] == [3], data


def test_la_unidad_que_sale_del_encabezado_del_precio_se_avisa():
    """#7: «Qty (M)» y «USD/M»: la unidad viaja (en lonas «M» es metro) y se
    avisa cuál se tomó y de dónde."""
    data = _leer([
        ["NCM", "Description", "Origin", "Qty (M)", "Unit price (USD/M)"],
        ["39269090", "CINTA DEMO", "CN", 100, 0.5],
    ])
    assert data["items"][0]["unidad"] == "m", data["items"]
    assert any("«Unit price (USD/M)»" in a and "metros" in a for a in data["avisos_mapeo"]), data["avisos_mapeo"]


def test_una_unidad_que_sale_solo_de_la_cantidad_no_avisa_del_precio():
    data = _leer([
        ["NCM", "Description", "Origin", "Qty (pcs)", "Unit price"],
        ["84137000", "BOMBA DEMO", "CN", 5, 100],
    ])
    assert not any("se leyó de los encabezados" in a for a in data["avisos_mapeo"]), data["avisos_mapeo"]


def test_un_flete_sin_monto_corta_el_grupo():
    """#4: «Freight cost» en la especificación, sin monto: el renglón de abajo
    no hereda «Freight cost» ni el grupo de antes del flete."""
    data = _leer([
        E,
        ["DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
        [None, "Freight cost", None, None, 1, None, None, None],
        [None, None, 2, 15, 1, 30, 1.5, 45],
    ])
    # Sin renglones agrupados la descripción va sin medidas (EXCEL-3).
    assert [i["descripcion"] for i in data["items"]] == ["LONA DEMO"], data["items"]
    assert data["filas_descartadas_numeros"] == [3, 4], data
    assert not any("tomaron la del renglón de arriba" in a for a in data["avisos_mapeo"]), data["avisos_mapeo"]


def test_un_descuento_leido_corta_el_grupo():
    """#4: después de un descuento leído, un renglón sin descripción no es
    del grupo de arriba."""
    data = _leer([
        E,
        ["DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
        [None, "Discount", None, None, None, None, None, -50],
        [None, None, 2, 15, 1, 30, 1.5, 45],
    ])
    assert [i["cantidad"] for i in data["items"]] == [20], data["items"]
    assert data["operacion"]["descuento"] == 50, data["operacion"]
    assert data["filas_descartadas_numeros"] == [4], data


def test_un_codigo_nuevo_sin_especificacion_no_hereda_la_del_grupo_anterior():
    """#3: «DT-2» sin especificación es otro producto: no toma «LONA DEMO»
    (ni él ni los renglones de su grupo); quedan sin leer, avisados."""
    data = _leer([
        E,
        ["DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
        ["DT-2", None, 2, 15, 1, 30, 1.5, 45],
        [None, None, 2, 20, 1, 40, 1.5, 60],
    ])
    assert [i["codigo_parte"] for i in data["items"]] == ["DT-1"], data["items"]
    assert data["filas_descartadas_numeros"] == [3, 4], data


@pytest.mark.parametrize("fila", [
    [None, "Descuento comercial", None, None, -500],
    [None, "Discount for early payment", 1, -500, None],
    # Con precio propio sólo el importe negativo lo distingue de un producto.
    [None, "Descuento comercial", 1, 500, -500],
], ids=["importe", "precio", "precio_e_importe"])
def test_un_descuento_con_texto_y_monto_negativo_se_avisa_y_no_es_producto(fila):
    """#1: no entra como producto de valor 0 (ni negativo): queda sin leer."""
    data = _leer([
        ["NCM", "Descripcion", "Cantidad", "Precio Unitario", "Importe"],
        ["84713000", "Laptop", 10, 350, 3500],
        fila,
    ])
    assert [i["descripcion"] for i in data["items"]] == ["Laptop"], data["items"]
    assert "descuento" not in data["operacion"], data["operacion"]
    assert data["filas_descartadas_numeros"] == [3], data


def test_un_largo_escrito_con_su_unidad_no_la_repite():
    """#9: «1,5m» en la columna «Length (m)» sale «largo 1,5m», no «1,5m m»."""
    data = _leer([
        E,
        ["DT-1", "LONA DEMO", 2, "1,5m", 1, 3, 1.5, 4.5],
        [None, None, 2, 10, 1, 20, 1.5, 30],
    ])
    assert data["items"][0]["descripcion"] == "LONA DEMO, ancho 2 m x largo 1,5m", data["items"]


# ---------------------------- EXCEL-3b (segunda vuelta del adversario)

@pytest.mark.parametrize("columna", ["No.", "Item No.", "S/N", "Part No."])
def test_el_flete_y_el_descuento_con_el_rotulo_a_la_izquierda_se_leen(columna):
    """#1: el rótulo en la columna de la izquierda (no sólo «Item») se lee,
    como en la base."""
    data = _leer([
        [columna, "Description", "Qty", "Unit price", "Amount"],
        ["1", "LAPTOP DEMO", 10, 350, 3500],
        ["Freight", None, None, None, 800],
        ["Discount", None, None, None, -50],
    ])
    assert [i["descripcion"] for i in data["items"]] == ["LAPTOP DEMO"], data["items"]
    assert data["operacion"]["flete"] == 800 and data["operacion"]["descuento"] == 50, data["operacion"]


def test_un_producto_discount_abre_su_grupo():
    """#5: «Discount tag labels» es un producto: el renglón de abajo es suyo."""
    data = _leer([
        E,
        ["DT-1", "Discount tag labels", 2, 10, 1, 20, 1.5, 30],
        [None, None, 2, 15, 1, 30, 1.5, 45],
    ])
    assert [i["descripcion"] for i in data["items"]] == [
        "Discount tag labels, ancho 2 m x largo 10 m",
        "Discount tag labels, ancho 2 m x largo 15 m"], data["items"]
    assert "descuento" not in data["operacion"], data["operacion"]


def test_con_la_especificacion_y_el_precio_combinados_cada_renglon_conserva_codigo_y_medidas():
    """#4: con el precio combinado los de abajo no tienen precio propio, pero
    la especificación combinada los hace del grupo: entran con su código y sus
    medidas (el precio vacío lo marca la revisión, como en la base)."""
    data = _leer_combinado([
        E,
        ["DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
        [None, None, 2, 15, 1, 30, None, None],
        [None, None, 2, 20, 1, 40, None, None],
    ], ("B2:B4", "G2:G4"))
    assert [(i["codigo_parte"], i["descripcion"]) for i in data["items"]] == [
        ("DT-1", "LONA DEMO, ancho 2 m x largo 10 m"),
        ("DT-1", "LONA DEMO, ancho 2 m x largo 15 m"),
        ("DT-1", "LONA DEMO, ancho 2 m x largo 20 m")], data["items"]


def _leer_combinado(filas, combinar):
    r = _subir(_libro(filas, combinar=combinar), "p.xlsx")
    assert r.status_code == 200, r.text[:300]
    return r.json()


XLS_COMBINADA = os.path.join(os.path.dirname(__file__), "fixtures", "combinada_con_codigo.xls")
FILAS_COMBINADA = [
    E,
    ["DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
    ["DT-2", None, 2, 15, 1, 30, 1.5, 45],
    ["DT-3", None, 2, 20, 1, 40, 1.5, 60],
]


def escribir_xls_combinada(ruta: str) -> None:
    """La especificación combinada en B2:B4 (hace falta xlwt, que no está en
    requirements.txt: el .xls ya está en fixtures)."""
    import xlwt
    wb = xlwt.Workbook()
    ws = wb.add_sheet("PI")
    for i, fila in enumerate(FILAS_COMBINADA):
        for j, v in enumerate(fila):
            if v is not None and not (j == 1 and i > 1):
                ws.write(i, j, v)
    ws.merge(1, 3, 1, 1)
    wb.save(ruta)


def test_el_xls_combinado_guardado_es_el_de_las_filas():
    import xlrd
    libro = xlrd.open_workbook(XLS_COMBINADA, formatting_info=True)
    hoja = libro.sheet_by_index(0)
    assert hoja.merged_cells == [(1, 4, 1, 2)]
    assert [[None if v == "" else v for v in hoja.row_values(i)] for i in range(hoja.nrows)] == FILAS_COMBINADA


def test_un_xls_con_la_especificacion_combinada_y_un_codigo_por_renglon_da_un_producto_por_renglon():
    """#2: en .xls también se leen las combinadas: «DT-2» y «DT-3» son del
    grupo de «LONA DEMO», como en el .xlsx."""
    with open(XLS_COMBINADA, "rb") as f:
        r = _subir(f.read(), "p.xls")
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert [(i["codigo_parte"], i["descripcion"]) for i in data["items"]] == [
        ("DT-1", "LONA DEMO, ancho 2 m x largo 10 m"),
        ("DT-2", "LONA DEMO, ancho 2 m x largo 15 m"),
        ("DT-3", "LONA DEMO, ancho 2 m x largo 20 m")], data["items"]


def test_un_largo_con_rango_conserva_su_unidad():
    """#10: «48-50» en «Length (m)» no es un número, pero no trae unidad:
    sale «largo 48-50 m»."""
    data = _leer([
        E,
        ["DT-1", "LONA DEMO", 2, "48-50", 1, 98, 1.5, 147],
        [None, None, 2, 10, 1, 20, 1.5, 30],
    ])
    assert data["items"][0]["descripcion"] == "LONA DEMO, ancho 2 m x largo 48-50 m", data["items"]


def test_la_unidad_de_la_cantidad_y_el_precio_se_avisa_con_las_dos_columnas():
    """#9: «Qty (M)» y «USD/M»: la unidad sale de los dos encabezados, y el
    aviso los nombra a los dos."""
    data = _leer([
        ["NCM", "Description", "Origin", "Qty (M)", "Unit price (USD/M)"],
        ["39269090", "CINTA DEMO", "CN", 100, 0.5],
    ])
    assert any("«Qty (M)»" in a and "«Unit price (USD/M)»" in a for a in data["avisos_mapeo"]), data["avisos_mapeo"]


def test_un_descuento_con_texto_que_queda_sin_leer_corta_el_grupo():
    """#5: «Descuento comercial -50» queda sin leer y el renglón de abajo no
    es del grupo de arriba."""
    data = _leer([
        E,
        ["DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
        [None, "Descuento comercial", None, None, None, None, None, -50],
        [None, None, 2, 15, 1, 30, 1.5, 45],
    ])
    assert [i["cantidad"] for i in data["items"]] == [20], data["items"]
    assert data["filas_descartadas_numeros"] == [3, 4], data


# ------------------------------- EXCEL-3b (segunda vuelta del adversario)

@pytest.mark.parametrize("flete", [
    [3, "Freight charges", None, 1, 800, 800],
    ["Freight", None, None, 1, 800, 800],
], ids=["descripcion", "item"])
def test_un_origen_combinado_que_alcanza_al_flete_no_lo_vuelve_producto(flete):
    """«China» combinada hasta el renglón del flete no le da origen: el flete
    se lee en la operación y no suma al FOB como producto."""
    data = _leer_combinado([
        ["Item", "Description", "Origin", "Qty", "Unit price", "Amount"],
        [1, "LAPTOP DEMO", "China", 10, 350, 3500],
        [2, "MOUSE DEMO", None, 10, 5, 50],
        flete,
    ], ("C2:C4",))
    assert [i["descripcion"] for i in data["items"]] == ["LAPTOP DEMO", "MOUSE DEMO"], data["items"]
    # El origen combinado sigue valiendo para los productos (EXCEL-2).
    assert [i["origen"] for i in data["items"]] == ["CN", "CN"], data["items"]
    assert data["operacion"].get("flete") == 800, data["operacion"]


def test_un_origen_combinado_que_alcanza_al_seguro_no_lo_vuelve_producto():
    """El seguro sin NCM ni origen propio se avisa como sin leer (EXCEL-1),
    aunque «China» venga combinada hasta su fila."""
    data = _leer_combinado([
        ["Item", "Description", "Origin", "Qty", "Unit price", "Amount"],
        [1, "LAPTOP DEMO", "China", 10, 350, 3500],
        [2, "Insurance", None, 1, 40, 40],
    ], ("C2:C3",))
    assert [i["descripcion"] for i in data["items"]] == ["LAPTOP DEMO"], data["items"]
    assert data["filas_descartadas_numeros"] == [3], data


def test_una_descripcion_combinada_que_alcanza_al_flete_no_lo_vuelve_producto():
    """La descripción copiada no es el rótulo de la fila: «Freight» en Item
    sigue siendo el flete."""
    data = _leer_combinado([
        ["Item", "Description", "Origin", "Qty", "Unit price", "Amount"],
        [1, "LAPTOP DEMO", "China", 10, 350, 3500],
        ["Freight", None, None, 1, 800, 800],
    ], ("B2:B3",))
    assert [i["descripcion"] for i in data["items"]] == ["LAPTOP DEMO"], data["items"]
    assert data["operacion"].get("flete") == 800, data["operacion"]


def test_una_especificacion_combinada_que_alcanza_al_subtotal_no_lo_vuelve_producto():
    """«Subtotal» en Part No. con la especificación combinada hasta su fila
    sigue siendo un subtotal, no un renglón del grupo."""
    data = _leer_combinado([
        E,
        ["DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
        [None, None, 2, 15, 1, 30, 1.5, 45],
        ["Subtotal", None, None, 25, 2, 50, None, 75],
        ["DT-9", "LONA OTRA", 3, 10, 1, 30, 3, 90],
    ], ("B2:B4",))
    assert [i["cantidad"] for i in data["items"]] == [20, 30, 30], data["items"]
    assert "Subtotal" not in [i["codigo_parte"] for i in data["items"]], data["items"]


@pytest.mark.parametrize("nota", ["Discount applies to rolls below", "Descuento comercial"])
def test_una_nota_de_descuento_sin_precio_no_abre_un_grupo(nota):
    """Un texto de descuento sin precio propio no es la descripción de los
    renglones de abajo: quedan sin leer, como sin el texto."""
    data = _leer([
        E,
        ["DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
        [None, nota, None, None, None, None, None, None],
        [None, None, 2, 15, 1, 30, 1.5, 45],
    ])
    assert [i["descripcion"] for i in data["items"]] == ["LONA DEMO"], data["items"]
    assert data["filas_descartadas_numeros"] == [3, 4], data


# ------------------------------- EXCEL-3c (devolución de EXCEL-3b)

PROFORMA = ["Item", "Description", "Origin", "Qty", "Unit price", "Amount"]
RENGLONES_PVC = ["Item", "Part No.", "Specification", "Width(m)", "Length (m)", "QTY (Rolls)",
                 "SM.TOTAL (sqm)", "Unit price (USD/sqm)", "Total Amount(USD)"]


def _total(items):
    return round(sum(i["cantidad"] * i["valor_unitario"] for i in items), 2)


@pytest.mark.parametrize("combinar", [("C2:C4",), ()], ids=["origen_combinado", "sin_combinar"])
@pytest.mark.parametrize("productos", [
    ["Payment terminal POS", "Handling cart"],
    ["Seguro de puerta", "Insurance card printer"],
], ids=["payment_handling", "seguro_insurance"])
def test_un_producto_con_una_palabra_de_cargo_y_su_descripcion_se_lee(productos, combinar):
    """R1: con el origen combinado, un producto cuya descripción propia empieza
    con «Payment», «Handling» o «Seguro» es mercadería, como en la base."""
    data = _leer_combinado([
        PROFORMA,
        [1, "Widget A", "CN", 10, 5, 50],
        [2, productos[0], "CN", 3, 100, 300],
        [3, productos[1], "CN", 2, 40, 80],
    ], combinar)
    assert [i["descripcion"] for i in data["items"]] == ["Widget A"] + productos, data["items"]
    assert _total(data["items"]) == 430, data["items"]
    assert not data["filas_descartadas_numeros"], data


@pytest.mark.parametrize("rotulo", [
    ["Insurance", None, None, 1, 40, 40],
    ["Seguro", None, None, None, None, 40],
    ["Payment 30% TT", None, None, 1, 100, 100],
    ["Bank charges", None, None, 1, 25, 25],
    ["Handling fee", None, None, 1, 30, 30],
    ["Gastos bancarios", None, None, 1, 15, 15],
], ids=["insurance", "seguro", "payment", "bank", "handling", "gastos"])
@pytest.mark.parametrize("forma", [
    "descripcion", "descripcion_y_origen", "origen_rotulo_en_item", "origen_rotulo_en_descripcion",
])
def test_un_cargo_no_entra_como_producto_aunque_venga_una_combinada(rotulo, forma):
    """B1 y familia: el seguro, el pago, los gastos o el handling, con el
    rótulo en Item o en la descripción, no se vuelven producto porque la
    descripción o el origen de arriba vengan combinados hasta su fila: queda
    sin leer, avisado (EXCEL-1)."""
    if forma == "descripcion":
        filas, combinar = [[None, None, "China", 10, 5, 50], rotulo], ("B2:B4",)
    elif forma == "descripcion_y_origen":
        filas, combinar = [[None, None, None, 10, 5, 50], rotulo], ("B2:B4", "C2:C4")
    elif forma == "origen_rotulo_en_item":
        filas, combinar = [[2, "MOUSE DEMO", None, 10, 5, 50], rotulo], ("C2:C4",)
    else:
        filas, combinar = [[2, "MOUSE DEMO", None, 10, 5, 50], [3] + rotulo[:1] + rotulo[2:]], ("C2:C4",)
    data = _leer_combinado([PROFORMA, [1, "LAPTOP DEMO", "China", 10, 350, 3500]] + filas, combinar)
    assert len(data["items"]) == 2, data["items"]
    assert _total(data["items"]) == 3550, data["items"]
    assert data["filas_descartadas_numeros"] == [4], data


def test_una_cabecera_sin_codigo_le_da_la_descripcion_a_los_renglones_con_codigo():
    """R2: «PVC BLUE» sin código y renglones «DT-1A», «DT-1B» sin
    especificación: heredan la descripción, como en la base."""
    data = _leer([
        RENGLONES_PVC,
        [1, None, "PVC BLUE", 3.2, 10, 2, 64, 1.35, 86.4],
        [None, "DT-1A", None, 3.2, 15, 3, 144, 1.35, 194.4],
        [None, "DT-1B", None, 3.2, 20, 3, 192, 1.35, 259.2],
    ])
    assert [i["codigo_parte"] for i in data["items"]] == ["", "DT-1A", "DT-1B"], data["items"]
    assert all(i["descripcion"].startswith("PVC BLUE, ") for i in data["items"]), data["items"]
    assert _total(data["items"]) == 540, data["items"]
    assert not data["filas_descartadas_numeros"], data


def test_un_codigo_que_empieza_con_el_del_grupo_no_hereda():
    """G3, por ahora: «DT-1-15» bajo «DT-1» es otro código y no se sabe si
    es el mismo material (en la proforma, DT-650-BL y DT-650-WH son colores
    distintos); queda sin leer, avisado, como un código nuevo (EXCEL-3b)."""
    data = _leer([
        RENGLONES_PVC,
        [1, "DT-1", "PVC BLUE", 3.2, 10, 2, 64, 1.35, 86.4],
        [None, "DT-1-15", None, 3.2, 15, 3, 144, 1.35, 194.4],
        [None, "DT-1-20", None, 3.2, 20, 3, 192, 1.35, 259.2],
    ])
    assert [i["codigo_parte"] for i in data["items"]] == ["DT-1"], data["items"]
    assert data["filas_descartadas_numeros"] == [3, 4], data


def _grupo_sin_precio_abajo(combinar):
    return _leer_combinado([
        RENGLONES_PVC,
        [1, "DT-1", "PVC BLUE", 3.2, 10, 2, 64, 1.35, 86.4],
        [None, None, None, 3.2, 15, 3, 144, None, None],
        [None, None, None, 3.2, 20, 3, 192, None, None],
        ["Total", None, None, None, None, 8, 400, None, 540],
    ], combinar)


@pytest.mark.parametrize("combinar", [("C2:C4",), ("C2:C4", "I2:I4")],
                         ids=["precio_solo_arriba", "precio_combinado"])
def test_los_renglones_que_entran_sin_precio_se_avisan_al_subir(combinar):
    """D12 (a): con la especificación combinada, los renglones de abajo
    entran con su cantidad y sin precio: no se inventa, se avisa al subir."""
    data = _grupo_sin_precio_abajo(combinar)
    assert [i["valor_unitario"] for i in data["items"]] == [1.35, 0, 0], data["items"]
    avisos = " | ".join(data["avisos_mapeo"])
    assert "2 renglón(es) entraron sin precio" in avisos and "desde la fila 3" in avisos, avisos


@pytest.mark.parametrize("combinar", [(), ("I2:I4",)], ids=["nada", "precio_combinado"])
def test_sin_la_especificacion_combinada_los_renglones_sin_precio_quedan_sin_leer(combinar):
    """D12, el resto: sin descripción ni precio propio el renglón no hereda
    (EXCEL-3b) y queda sin leer, avisado; no hay aviso de precio."""
    data = _grupo_sin_precio_abajo(combinar)
    assert len(data["items"]) == 1 and data["filas_descartadas_numeros"] == [3, 4], data
    assert "sin precio" not in " | ".join(data["avisos_mapeo"]), data["avisos_mapeo"]
