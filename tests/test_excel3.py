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


def test_un_flete_sin_monto_no_hereda_la_descripcion_del_grupo():
    """«Freight cost» en la columna Item, con medidas y sin monto: no es un
    renglón del grupo de arriba."""
    r = _subir(_libro([
        ["Item"] + E,
        [1, "DT-1", "LONA DEMO", 2, 10, 1, 20, 1.5, 30],
        ["Freight cost", None, None, 2, 10, 1, 1, None, None],
    ]), "p.xlsx")
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    assert [i["descripcion"] for i in data["items"]] == ["LONA DEMO, ancho 2 m x largo 10 m"], data["items"]
    assert "flete" not in data["operacion"], data["operacion"]


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
