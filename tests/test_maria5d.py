"""MARIA-5d (PARA-DEV-2.md, veredicto de 1cdfe49).

1. Un bruto que dice «unitario», «unit», «per unit» o «por unidad» es bruto
   de una unidad: no se divide por la cantidad, va último y lleva el aviso de
   bruto (antes, «Peso bruto unitario» = 3 en 10 unidades daba 0,3 kg).
2. «Peso kg/u», «Peso c/u» y «Peso U.» dicen que son por unidad: no son
   dudosas.
"""
import io

import pytest

from tests.test_maria5_peso_excel import COLUMNAS, _make_excel_bytes, _subir

BRUTOS_DE_UNA_UNIDAD = ["Peso bruto unitario", "Gross weight per unit", "Peso bruto por unidad",
                        "Gross unit weight", "Peso Bruto Unit."]


@pytest.mark.parametrize("columna", BRUTOS_DE_UNA_UNIDAD)
def test_el_bruto_de_una_unidad_no_se_divide(auth_override, client, columna):
    data = _subir(client, [columna], [3])
    assert data["items"][0]["peso_unitario"] == pytest.approx(3), data
    avisos = data["avisos"]
    assert any("bruto" in a and f"«{columna}»" in a for a in avisos), avisos
    assert not any("toda la línea" in a or "se dividió" in a for a in avisos), avisos


@pytest.mark.parametrize("columna", BRUTOS_DE_UNA_UNIDAD)
def test_el_bruto_de_una_unidad_va_ultimo(auth_override, client, columna):
    for otras, pesos in ((["Peso"], [2.5]), (["Peso neto"], [25]), (["Peso por caja"], [2.5])):
        data = _subir(client, [columna, *otras], [3, *pesos])
        assert data["items"][0]["peso_unitario"] == pytest.approx(2.5), (otras, data)


def test_el_bruto_de_la_linea_se_sigue_dividiendo(auth_override, client):
    data = _subir(client, ["Peso bruto"], [30])
    assert data["items"][0]["peso_unitario"] == pytest.approx(3.0)
    assert any("bruto" in a for a in data["avisos"]), data["avisos"]


def test_un_mapeo_guardado_al_bruto_de_una_unidad_no_divide(auth_override, client):
    r = client.post("/api/clientes", json={"nombre": "Cliente Bruto Unitario", "cuit": "30123456790"})
    cid = r.json().get("id") or r.json().get("cliente", {}).get("id")
    r = client.post(f"/api/clientes/{cid}/column_mapping",
                    json={"mapping": {"Pieza": "pieza", "Descripcion": "descripcion", "Origen": "origen",
                                      "Cantidad": "cantidad", "Valor Unitario": "valor_unitario",
                                      "Bruto unitario": "peso_unitario"}})
    assert r.status_code == 200, r.text
    excel = _make_excel_bytes(COLUMNAS + ["Bruto unitario"], [["84713000", "Notebook", "CN", 10, 350.0, 3]])
    r = client.post("/upload_excel_v2/", data={"cliente_id": cid, "use_mapping": "true"},
                    files={"file": ("p.xlsx", io.BytesIO(excel),
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    assert r.json()["items"][0]["peso_unitario"] == pytest.approx(3), r.json()
    assert any("bruto" in a for a in r.json()["avisos"]), r.json()["avisos"]


@pytest.mark.parametrize("columna", ["Peso kg/u", "Peso c/u", "Peso U.", "Peso (kg/u)", "PESO C/U"])
def test_las_que_dicen_por_unidad_no_son_dudosas(auth_override, client, columna):
    data = _subir(client, [columna], [2.5])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5), data
    assert not any("Revisala" in a for a in data["avisos"]), data["avisos"]
