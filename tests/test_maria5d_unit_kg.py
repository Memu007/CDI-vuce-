"""MARIA-5d: devolución PM del 2026-10-19, sólo datos inventados.

El bruto expresamente unitario conserva sus kg, con o sin mapeo guardado.
El peso cargado llega al TXT por HTTP: 10 x 3 kg declara 30 kg la línea.
"""
import io
import re

import pytest

from tests.test_maria5_peso_excel import COLUMNAS, _make_excel_bytes, _subir

COLUMNAS_UNITARIAS = ["Peso bruto unit (kg)", "Gross weight unit (kg)", "Unit gross weight"]


def _subir_con_mapeo(client, columna, peso):
    r = client.post("/api/clientes", json={"nombre": "Cliente Bruto Demo", "cuit": "30123456790"})
    assert r.status_code == 200, r.text
    cid = r.json().get("id") or r.json().get("cliente", {}).get("id")
    r = client.post(f"/api/clientes/{cid}/column_mapping", json={"mapping": {
        "Pieza": "pieza", "Descripcion": "descripcion", "Origen": "origen", "Cantidad": "cantidad",
        "Valor Unitario": "valor_unitario", columna: "peso_unitario"}})
    assert r.status_code == 200, r.text
    excel = _make_excel_bytes(COLUMNAS + [columna], [["84713000", "Notebook", "CN", 10, 350.0, peso]])
    r = client.post("/upload_excel_v2/", data={"cliente_id": cid, "use_mapping": "true"},
                    files={"file": ("demo.xlsx", io.BytesIO(excel),
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    assert r.json()["applied_mapping"], r.json()
    return r.json()


def _peso_del_txt(client, data):
    # Como el pedido de la v2: manda peso_unitario, no un total fabricado por la prueba.
    item = data["items"][0]
    pedido = {"operation_id": "OP_BRUTO_DEMO", "items": [{
        "pieza": "84714900100D", "estado": 2, "descripcion": item["descripcion"] + " de prueba",
        "origen": item["origen"], "cantidad": item["cantidad"],
        "valor_unitario": item["valor_unitario"], "peso_unitario": item["peso_unitario"]}],
        "fecha_emision": "01/10/2026", "sbt_sufijo_valor": "AA(DEMO)-CA00-",
        "moneda": "DOL", "incoterm": "FOB", "comprador_cuit": "30999999995"}
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 200, r.text
    return re.findall(r"^QARTKGRNET=(\S+)", r.json()["content"], re.M)


@pytest.mark.parametrize("guardado", [False, True], ids=["automatico", "mapeo_guardado"])
@pytest.mark.parametrize("columna", COLUMNAS_UNITARIAS)
def test_bruto_unitario_con_unidad_de_medida(auth_override, client, columna, guardado):
    data = _subir_con_mapeo(client, columna, 3) if guardado else _subir(client, [columna], [3])
    assert data["items"][0]["peso_unitario"] == pytest.approx(3), data
    assert _peso_del_txt(client, data) == ["30.000"]
    assert any("bruto" in a and f"«{columna}»" in a for a in data["avisos"]), data
    assert not any("toda la línea" in a or "se dividió" in a for a in data["avisos"]), data


@pytest.mark.parametrize("columna", ["Peso bruto total unit (kg)", "Gross weight total units (kg)",
                                     "Peso bruto unidades (kg)", "Unit gross weight linea", "Unit gross weight per line", "Unit gross weight line"])
def test_bruto_total_o_plural_sigue_dividiendose(auth_override, client, columna):
    data = _subir(client, [columna], [30])
    assert data["items"][0]["peso_unitario"] == pytest.approx(3), data
    assert _peso_del_txt(client, data) == ["30.000"]
    assert any("se dividió" in a for a in data["avisos"]), data


@pytest.mark.parametrize("columna", COLUMNAS_UNITARIAS)
def test_neto_sigue_ganando_al_bruto_unitario(auth_override, client, columna):
    data = _subir(client, [columna, "Peso neto"], [3, 25])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5), data
    assert _peso_del_txt(client, data) == ["25.000"]
