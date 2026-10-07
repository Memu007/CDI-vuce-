"""MARIA-5, devolución de la PM (2026-10-07), puntos 1 a 4 y 6.

1. Dos pesos para la misma línea: gana el total neto, con aviso (lector y Excel).
2. Un peso que no es número nunca saca una fila del Excel.
3. El peso, con la misma guarda que los importes en el generador.
4. Subítems: la tolerancia compara exacto con exacto.
6. Una sola cuenta: la validación y el aviso de gastos redondean como el TXT.
El punto 5 (grupo en la v2) está en `scripts/testing/pantalla_maria5.js`.
"""
import io
import random
from decimal import Decimal

import pytest

from tests.test_generar_maria_txt import _gen
from tests.test_maria1a_lectura_factura import COPIAS, _leer
from tests.test_maria5_centavos import _campo, _item
from tests.test_maria5_peso_excel import COLUMNAS, _subir
from tests.test_clientes_plan04 import _make_excel_bytes


# --- 1. Lector -------------------------------------------------------------

def _leido(monkeypatch, copia, **peso):
    factura = {"operacion": {"numero_factura": "F-5"},
               "items": [dict({"descripcion": "Notebook de prueba", "cantidad": 10, "valor_unitario": 500,
                               "origen": "CN"}, **peso)]}
    resultado = _leer(monkeypatch, copia, factura)
    return resultado["items"][0], resultado["operacion"].get("avisos_peso", [])


@pytest.mark.parametrize("copia", COPIAS)
def test_el_total_copiado_en_los_dos_campos_gana_el_de_la_linea(monkeypatch, copia):
    item, avisos = _leido(monkeypatch, copia, peso_unitario=25, peso_total_linea=25)
    assert (item["peso_unitario"], item["peso_total"]) == pytest.approx((2.5, 25))
    assert len(avisos) == 1 and "250" in avisos[0] and "25 kg" in avisos[0], avisos
    item = dict(item, pieza="84713012")
    item.pop("peso_total")
    assert "QARTKGRNET=25.000" in _gen("OP_LECTOR", [item])


@pytest.mark.parametrize("copia", COPIAS)
def test_si_no_coinciden_gana_el_de_la_linea_con_aviso(monkeypatch, copia):
    item, avisos = _leido(monkeypatch, copia, peso_unitario=2.5, peso_total_linea=26)
    assert (item["peso_unitario"], item["peso_total"]) == pytest.approx((2.6, 26))
    assert len(avisos) == 1 and "26 kg" in avisos[0] and "Notebook de prueba" in avisos[0], avisos


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("peso", [{"peso_unitario": 2.5, "peso_total_linea": 25},
                                  {"peso_unitario": 0.333, "peso_total_linea": 3.33},
                                  {"peso_total_linea": 25}, {"peso_unitario": 2.5}])
def test_si_coinciden_no_hay_aviso(monkeypatch, copia, peso):
    _, avisos = _leido(monkeypatch, copia, **peso)
    assert avisos == []


def test_el_aviso_del_lector_llega_a_la_pantalla(auth_override, client, monkeypatch):
    import proyecto_maria.main as main
    leido = {"operacion": {"avisos_peso": ["Peso de «X»: aviso de prueba."]},
             "items": [{"descripcion": "X", "cantidad": 1, "valor_unitario": 1}]}
    monkeypatch.setattr(main, "lectura_automatica_disponible", lambda: True)
    monkeypatch.setattr(main, "process_pdf", lambda contenido: leido)
    monkeypatch.setattr("proyecto_maria.core.ai_quota.enforce_pdf_quota", lambda usuario: None)
    from tests.test_maria1a_lectura_factura import _pdf_en_blanco
    r = client.post("/upload_pdf/public", files={"file": ("f.pdf", io.BytesIO(_pdf_en_blanco()), "application/pdf")})
    assert r.status_code == 200, r.text
    assert r.json()["avisos"] == ["Peso de «X»: aviso de prueba."]
    assert "avisos_peso" not in r.json()["operacion"]


# --- 1. Excel --------------------------------------------------------------

@pytest.mark.parametrize("unidad, linea", [("Peso", "Peso neto"), ("Weight", "Net Weight"),
                                           ("Peso unitario", "Peso total")])
def test_excel_con_dos_pesos_gana_el_de_la_linea(auth_override, client, unidad, linea):
    data = _subir(client, [unidad, linea], [30, 25])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)
    texto = " ".join(data["avisos"])
    assert f"«{linea}»" in texto and f"«{unidad}»" in texto, data["avisos"]
    assert "300" in texto and "25" in texto, data["avisos"]


def test_excel_el_neto_le_gana_al_total(auth_override, client):
    data = _subir(client, ["Peso total", "Peso neto"], [30, 25])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)
    assert any("«Peso neto»" in a and "«Peso total»" in a for a in data["avisos"]), data["avisos"]


def test_excel_el_neto_le_gana_al_bruto_y_a_la_unidad(auth_override, client):
    data = _subir(client, ["Peso bruto", "Peso", "Peso neto"], [40, 2.5, 25])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)
    assert not any("bruto dividido" in a for a in data["avisos"]), data["avisos"]


def test_excel_si_coinciden_no_avisa_la_diferencia(auth_override, client):
    data = _subir(client, ["Peso unitario", "Peso total"], [2.5, 25])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)
    assert not any("no da" in a for a in data["avisos"]), data["avisos"]


def test_excel_el_mapeo_guardado_no_le_gana_al_neto(auth_override, client):
    r = client.post("/api/clientes", json={"nombre": "Cliente Dos Pesos", "cuit": "30123456791"})
    cid = r.json().get("id") or r.json().get("cliente", {}).get("id")
    r = client.post(f"/api/clientes/{cid}/column_mapping",
                    json={"mapping": {"Pieza": "pieza", "Descripcion": "descripcion", "Origen": "origen",
                                      "Cantidad": "cantidad", "Valor Unitario": "valor_unitario",
                                      "Peso": "peso_unitario"}})
    assert r.status_code == 200, r.text
    excel = _make_excel_bytes(COLUMNAS + ["Peso", "Peso neto"], [["84713000", "Notebook", "CN", 10, 350.0, 30, 25]])
    r = client.post("/upload_excel_v2/", data={"cliente_id": cid, "use_mapping": "true"},
                    files={"file": ("p.xlsx", io.BytesIO(excel),
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    assert r.json()["items"][0]["peso_unitario"] == pytest.approx(2.5)


# --- 2. Un peso que no es número no saca la fila ---------------------------

@pytest.mark.parametrize("columna", ["Peso unitario", "Peso", "Weight", "Peso total", "Peso bruto"])
def test_un_peso_en_texto_no_saca_la_fila(auth_override, client, columna):
    excel = _make_excel_bytes(COLUMNAS + [columna], [["84713000", "Notebook", "CN", 4, 350.0, "2,5"],
                                                    ["84713001", "Monitor", "CN", 2, 100.0, 6]])
    r = client.post("/upload_excel_v2/", files={"file": ("p.xlsx", io.BytesIO(excel),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    assert [it["descripcion"] for it in items] == ["Notebook", "Monitor"]
    assert items[0]["peso_unitario"] == 0
    assert any("no es un número" in a for a in r.json()["avisos"]), r.json()["avisos"]


# --- 3. La guarda del peso en el generador ---------------------------------

@pytest.mark.parametrize("peso", [{"peso_unitario": float("nan")}, {"peso_unitario": float("inf")},
                                  {"peso_unitario": 1e300}, {"peso_kg": 2e12}, {"peso_kg": 0.0004},
                                  {"peso_unitario": 0.0001, "cantidad": 4}, {"peso_kg": -1}, {"peso_kg": 0},
                                  {"peso_kg": "abc"}])
def test_un_peso_imposible_no_llega_al_txt(peso):
    with pytest.raises(ValueError, match="[Pp]eso"):
        _gen("OP_PESO", [_item(10, **peso)])


@pytest.mark.parametrize("peso", [{"peso_kg": float("nan")}, {"peso_kg": 1e300}, {"peso_kg": 0.0004}])
def test_un_peso_imposible_da_400(client, auth_override, peso):
    from tests.test_maria_subitems import ITEM_BASE, SUF_A
    item = {k: v for k, v in ITEM_BASE.items() if k != "subitems"}
    item.update(estado=2, **peso)
    r = client.post("/generate_maria", content=__import__("json").dumps(
        {"operation_id": "OP1", "items": [item], "fecha_emision": "22/06/2026", "sbt_sufijo_valor": SUF_A},
        allow_nan=True), headers={"Content-Type": "application/json"})
    assert r.status_code == 400, r.text


def test_un_peso_chico_que_no_redondea_a_cero_sale():
    assert "QARTKGRNET=0.001" in _gen("OP_PESO", [_item(10, peso_kg=0.0005)])


# --- 4. Subítems: exacto con exacto ----------------------------------------

def _con_subitems(cantidad, unitario, partes):
    return _item(1, cantidad=cantidad, valor_unitario=unitario,
                 subitems=[{"cantidad": c, "valor_unitario": u, "sufijo": "AA(1)-CA00"} for c, u in partes])


def test_el_caso_de_la_pm_genera():
    txt = _gen("OP_SUB", [_con_subitems(7, 2.675, [(2, 2.675), (2.5, 2.6722), (2.5, 2.675)])])
    assert sum(_campo(txt, "MSBTFOB")) == _campo(txt, "MARTFOB")[0] == Decimal("18.73")


@pytest.mark.parametrize("semilla", range(3))
def test_ningun_pedido_que_pasaba_antes_da_error(semilla):
    """El criterio de antes (`8e819dd`): floats sin redondear, tolerancia 0,01.
    Lo que pasaba ese control tiene que seguir generando."""
    azar = random.Random(semilla)
    probados = 0
    for _ in range(1500):
        unitario = round(azar.uniform(0.01, 50), azar.choice([2, 3, 4]))
        partes = [round(azar.uniform(0.5, 5) * 2) / 2 for _ in range(azar.randint(2, 4))]
        subs = [(c, round(unitario + azar.choice([0, 0, 0.0001, -0.0001, 0.0002, -0.0003, 0.001]), 4))
                for c in partes]
        cantidad = sum(partes)
        antes = abs(sum(c * u for c, u in subs) - cantidad * unitario) <= 0.01
        if not antes:
            continue
        probados += 1
        txt = _gen("OP_SUB", [_con_subitems(cantidad, unitario, subs)])
        assert sum(_campo(txt, "MSBTFOB")) == _campo(txt, "MARTFOB")[0]
    assert probados > 500


def test_una_diferencia_real_sigue_dando_error():
    with pytest.raises(ValueError, match="sub-ítems suman"):
        _gen("OP_SUB", [_con_subitems(4, 10, [(2, 10), (2, 10.01)])])


# --- 6. Una sola cuenta ----------------------------------------------------

def _fila(fob, grupo=None):
    fila = _item(fob)
    if grupo is not None:
        fila["grupo_id"] = grupo
    return fila


def test_la_validacion_con_grupos_muestra_el_fob_del_txt(client, auth_override):
    """Tres productos de 6,675 en un grupo: el TXT declara una línea de 20,03
    (redondeada una vez); antes la validación sumaba 6,68 × 3 = 20,04."""
    filas = [_fila(6.675, grupo=1), _fila(6.675, grupo=1), _fila(6.675, grupo=1), _fila(0.335)]
    txt = _gen("OP_VAL", filas)
    r = client.post("/api/validate/smart", json={"items": filas})
    assert r.status_code == 200, r.text
    assert Decimal(str(r.json()["estadisticas"]["total_valor_usd"])) == _campo(txt, "MDDTFOB")[0] == Decimal("20.37")


@pytest.mark.parametrize("semilla", range(3))
def test_la_validacion_y_el_txt_dan_lo_mismo_al_azar(semilla):
    from proyecto_maria.core.validations import run_smart_validations
    from proyecto_maria.models.operations import Item
    azar = random.Random(semilla)
    for _ in range(200):
        filas = [_fila(round(azar.uniform(0.001, 99), 3), grupo=azar.choice([None, None, 1, 2]))
                 for _ in range(azar.randint(1, 8))]
        txt = _gen("OP_VAL", filas)
        items = [Item(**f) for f in filas]
        total = run_smart_validations(items, grupos=[f.get("grupo_id") for f in filas])
        assert Decimal(str(total["estadisticas"]["total_valor_usd"])) == _campo(txt, "MDDTFOB")[0], filas


def test_el_aviso_de_gastos_dice_lo_que_dice_el_txt():
    from proyecto_maria.core.maria_generator import supuestos_declarados
    txt = _gen("OP_GTOS", [_item(100)], incoterm="CIF", flete=5.005, seguro=6.005)
    assert "MCPL=11.02" in txt
    avisos = supuestos_declarados([_item(100)], incoterm="CIF", flete=5.005, seguro=6.005)
    assert any("11.02" in a for a in avisos) and not any("11.01" in a for a in avisos), avisos


# --- Revisión adversaria de la devolución ----------------------------------

@pytest.mark.parametrize("columnas, pesos", [
    (["Peso neto unitario"], [2.5]),
    (["Peso neto unitario", "Peso bruto"], [2.5, 30]),
    (["Net weight per unit", "Gross weight"], [2.5, 30]),
    (["Peso", "Peso neto unitario"], [3, 2.5]),
    (["Peso neto unitario", "Peso neto total"], [2.5, 25]),
])
def test_el_peso_neto_de_una_unidad_con_otro_nombre(auth_override, client, columnas, pesos):
    data = _subir(client, columnas, pesos)
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)
    assert not any("trae sólo" in a for a in data["avisos"]), data["avisos"]


def test_una_columna_de_pesos_argentinos_no_es_peso(auth_override, client):
    data = _subir(client, ["Pesos ARS", "Peso"], [1000, 2.5])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)
    assert not any("Pesos" in a for a in data["avisos"]), data["avisos"]


@pytest.mark.parametrize("texto", ["inf", "Infinity", "-inf"])
def test_un_peso_infinito_en_texto_no_da_500(auth_override, client, texto):
    excel = _make_excel_bytes(COLUMNAS + ["Peso neto"], [["84713000", "Notebook", "CN", 4, 350.0, texto],
                                                        ["84713001", "Monitor", "CN", 2, 100.0, 6]])
    r = client.post("/upload_excel_v2/", files={"file": ("p.xlsx", io.BytesIO(excel),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    assert [it["peso_unitario"] for it in r.json()["items"]] == [0, 3]
    assert any("no es un número" in a for a in r.json()["avisos"]), r.json()["avisos"]


def test_el_mapeo_guardado_gana_entre_columnas_de_una_unidad(auth_override, client):
    r = client.post("/api/clientes", json={"nombre": "Cliente Kg", "cuit": "30123456792"})
    cid = r.json().get("id") or r.json().get("cliente", {}).get("id")
    r = client.post(f"/api/clientes/{cid}/column_mapping",
                    json={"mapping": {"Pieza": "pieza", "Descripcion": "descripcion", "Origen": "origen",
                                      "Cantidad": "cantidad", "Valor Unitario": "valor_unitario",
                                      "Kg": "peso_unitario"}})
    assert r.status_code == 200, r.text
    excel = _make_excel_bytes(COLUMNAS + ["Peso", "Kg"], [["84713000", "Notebook", "CN", 10, 350.0, 9, 2.5]])
    r = client.post("/upload_excel_v2/", data={"cliente_id": cid, "use_mapping": "true"},
                    files={"file": ("p.xlsx", io.BytesIO(excel),
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    assert r.json()["items"][0]["peso_unitario"] == pytest.approx(2.5)


def test_el_aviso_nombra_la_columna_como_viene(auth_override, client):
    data = _subir(client, ["peso_unitario", "Peso neto"], [3, 25])
    assert data["items"][0]["peso_unitario"] == pytest.approx(2.5)
    texto = " ".join(data["avisos"])
    assert "«peso_unitario»" in texto and "(ignorada)" not in texto, data["avisos"]


def test_un_peso_enorme_dice_que_es_enorme():
    with pytest.raises(ValueError, match="tope"):
        _gen("OP_PESO", [_item(10, peso_kg=1e300)])
