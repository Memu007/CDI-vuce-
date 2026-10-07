"""MARIA-5, D22 (a): el peso que trae el Excel.

«Peso total» y «Peso neto» son de toda la línea: se dividen por la cantidad
(el TXT multiplica el unitario por la cantidad). «Peso» y «Weight» son de una
unidad, como dice la plantilla. «Peso bruto» no entra como neto en silencio:
si es la única columna de peso, se usa dividida por la cantidad y se avisa.
"""
import io

import pytest

from tests.test_clientes_plan04 import _make_excel_bytes

COLUMNAS = ["Pieza", "Descripcion", "Origen", "Cantidad", "Valor Unitario"]


def _subir(client, columnas_peso, pesos):
    excel = _make_excel_bytes(COLUMNAS + columnas_peso,
                              [["84713000", "Notebook", "CN", 10, 350.0, *pesos]])
    r = client.post("/upload_excel_v2/", files={"file": ("p.xlsx", io.BytesIO(excel),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize("columna, peso, unitario", [
    ("Peso total", 25, 2.5),
    ("Peso neto", 25, 2.5),
    ("PESO_TOTAL", 25, 2.5),
    ("Peso", 2.5, 2.5),
    ("Weight", 2.5, 2.5),
    ("Peso Unitario", 2.5, 2.5),
])
def test_el_peso_de_la_linea_se_divide(auth_override, client, columna, peso, unitario):
    data = _subir(client, [columna], [peso])
    assert data["items"][0]["peso_unitario"] == pytest.approx(unitario)
    assert not any("bruto" in a for a in data.get("avisos", []))


def test_el_bruto_solo_se_usa_dividido_y_con_aviso(auth_override, client):
    data = _subir(client, ["Peso bruto"], [30])
    assert data["items"][0]["peso_unitario"] == pytest.approx(3.0)
    assert any("bruto" in a and "neto" in a for a in data["avisos"]), data.get("avisos")


def test_con_neto_y_bruto_se_usa_el_neto(auth_override, client):
    data = _subir(client, ["Peso bruto", "Peso neto"], [30, 25])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)
    assert not any("bruto" in a for a in data.get("avisos", []))


def test_con_unitario_y_total_se_usa_el_unitario(auth_override, client):
    data = _subir(client, ["Peso total", "Peso unitario"], [25, 2.5])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)


def test_el_mapeo_guardado_del_cliente_tambien_divide(auth_override, client):
    r = client.post("/api/clientes", json={"nombre": "Cliente Peso Total", "cuit": "30123456789"})
    assert r.status_code == 200, r.text
    cid = r.json().get("id") or r.json().get("cliente", {}).get("id")
    excel = _make_excel_bytes(COLUMNAS + ["Peso total"], [["84713000", "Notebook", "CN", 10, 350.0, 25]])
    for _ in range(2):  # la segunda vez, con el mapeo aprendido
        r = client.post("/upload_excel_v2/", data={"cliente_id": cid, "use_mapping": "true"},
                        files={"file": ("p.xlsx", io.BytesIO(excel),
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
        assert r.status_code == 200, r.text
        assert r.json()["items"][0]["peso_unitario"] == pytest.approx(2.5)


@pytest.mark.parametrize("columna", ["Peso total kg", "Net weight", "Total weight", "Peso Neto Total"])
def test_variantes_del_peso_de_la_linea(auth_override, client, columna):
    """Revisión adversaria: con unidad o en inglés, también es de la línea."""
    data = _subir(client, [columna], [25])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)


def test_un_mapeo_guardado_con_otro_nombre_tambien_divide(auth_override, client):
    r = client.post("/api/clientes", json={"nombre": "Cliente Peso Kg", "cuit": "30123456790"})
    cid = r.json().get("id") or r.json().get("cliente", {}).get("id")
    r = client.post(f"/api/clientes/{cid}/column_mapping",
                    json={"mapping": {"Pieza": "pieza", "Descripcion": "descripcion", "Origen": "origen",
                                      "Cantidad": "cantidad", "Valor Unitario": "valor_unitario",
                                      "Peso Total Linea": "peso_unitario"}})
    assert r.status_code == 200, r.text
    excel = _make_excel_bytes(COLUMNAS + ["Peso Total Linea"], [["84713000", "Notebook", "CN", 10, 350.0, 25]])
    r = client.post("/upload_excel_v2/", data={"cliente_id": cid, "use_mapping": "true"},
                    files={"file": ("p.xlsx", io.BytesIO(excel),
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    assert r.json()["items"][0]["peso_unitario"] == pytest.approx(2.5)


def test_un_peso_que_no_es_numero_se_avisa(auth_override, client):
    excel = _make_excel_bytes(COLUMNAS + ["Peso total"], [["84713000", "Notebook", "CN", 4, 350.0, "abc"],
                                                         ["84713001", "Monitor", "CN", 2, 100.0, 6]])
    r = client.post("/upload_excel_v2/", files={"file": ("p.xlsx", io.BytesIO(excel),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    assert any("no es un número" in a for a in r.json()["avisos"]), r.json()["avisos"]
