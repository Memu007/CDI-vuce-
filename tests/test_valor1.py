"""VALOR-1: ajustes a incluir y a deducir, FOB casillero y seguro sugerido.

Los ajustes los carga la persona (el sistema no decide qué se descuenta) y
sólo sirven para las cuentas: el TXT lleva el FOB de la factura hasta saber
en qué campo van (D12). El seguro sugerido es el 1 % de (FOB casillero +
flete). Datos inventados, con la forma de la factura del 24/10.
"""
import json
import re
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest

from proyecto_maria.core import maria_generator as mg
from tests.test_maria7_rechazos_24_10 import LONA, _pedido, _registrar_con_cuit, _valor

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "proyecto_maria" / "static" / "v2" / "screens"


def _cuentas(items, **kw):
    # Por el módulo: contra la base, cada caso falla por su cuenta.
    return mg.cuentas_del_valor(items, **kw)


# --------------------------------------------------------- las cuentas


def test_fob_casillero_es_el_de_la_factura_mas_lo_que_se_incluye_menos_lo_que_se_deduce():
    items = [{"cantidad": 750, "valor_unitario": 1.85}]  # 1.387,50
    v = _cuentas(items, flete=100, ajustes_incluir=12.5, ajustes_deducir=50)
    assert v["fob_factura"] == 1387.50
    assert v["ajustes_incluir"] == 12.50 and v["ajustes_deducir"] == 50.00
    assert v["fob_casillero"] == 1350.00
    # 1 % de (1.350 + 100)
    assert v["seguro_sugerido"] == 14.50


def test_sin_ajustes_el_casillero_es_el_fob_de_la_factura():
    v = _cuentas([{"cantidad": 750, "valor_unitario": 1.85}], flete=7925, seguro=12.4)
    assert v["fob_casillero"] == v["fob_factura"] == 1387.50
    assert v["flete"] == 7925.00 and v["seguro"] == 12.40
    assert v["seguro_sugerido"] == 93.13  # 1 % de 9.312,50 = 93,125 → 93,13


def test_el_seguro_sugerido_redondea_la_mitad_hacia_arriba():
    # 1 % de 1.000,50 = 10,005: al par daría 10,00.
    v = _cuentas([{"cantidad": 1, "valor_unitario": 1000.5}])
    assert v["seguro_sugerido"] == 10.01


def test_los_ajustes_van_al_centavo_con_la_mitad_hacia_arriba():
    v = _cuentas([{"cantidad": 1, "valor_unitario": 1000}], ajustes_deducir=50.005, ajustes_incluir=0.125)
    assert v["ajustes_deducir"] == 50.01 and v["ajustes_incluir"] == 0.13
    assert v["fob_casillero"] == 950.12


def test_la_base_del_seguro_se_cambia_en_un_solo_lugar(monkeypatch):
    """D12b: si el despachante dice que el 1 % va sobre el FOB antes del
    descuento, alcanza con cambiar BASE_SEGURO_SUGERIDO."""
    items = [{"cantidad": 1, "valor_unitario": 1000}]
    v = _cuentas(items, flete=100, ajustes_deducir=200)
    assert v["seguro_sugerido"] == 9.00 and v["base_seguro"] == "FOB casillero"
    monkeypatch.setattr(mg, "BASE_SEGURO_SUGERIDO", "fob_factura")
    v = _cuentas(items, flete=100, ajustes_deducir=200)
    assert v["seguro_sugerido"] == 11.00 and v["base_seguro"] == "FOB de la factura"
    assert v["fob_casillero"] == 800.00


def test_deducir_mas_que_el_fob_no_es_un_casillero():
    with pytest.raises(ValueError, match=r"Los ajustes a deducir \(2\.000,00\) superan el FOB de la factura más "
                                         r"los ajustes a incluir \(1\.010,00\)"):
        _cuentas([{"cantidad": 1, "valor_unitario": 1000}], ajustes_incluir=10, ajustes_deducir=2000)


def test_deducir_justo_el_fob_da_casillero_cero():
    v = _cuentas([{"cantidad": 1, "valor_unitario": 1000}], ajustes_deducir=1000)
    assert v["fob_casillero"] == 0.0


@pytest.mark.parametrize("campo,nombre", [("ajustes_incluir", "Ajustes a incluir"),
                                          ("ajustes_deducir", "Ajustes a deducir")])
@pytest.mark.parametrize("malo", [-1, float("nan"), float("inf"), "abc", 1e13])
def test_un_ajuste_invalido_dice_cual(campo, nombre, malo):
    with pytest.raises(ValueError, match=nombre):
        _cuentas([{"cantidad": 1, "valor_unitario": 10}], **{campo: malo})


# --------------------------- el FOB de la factura es el MDDTFOB del TXT


DOS_LONAS = [dict(LONA), {**LONA, "cantidad": 3, "valor_unitario": 3.335, "peso_kg": 2.0}]


def _pedido_con(items, **kw):
    p = _pedido()
    p["items"] = [{
        "pieza": it["pieza"], "descripcion": it["descripcion"], "origen": "CN",
        "cantidad": it["cantidad"], "valor_unitario": it["valor_unitario"],
        "peso_unitario": it["peso_kg"] / it["cantidad"], "unidad": it["unidad"],
        "grupo_id": it.get("grupo_id"),
    } for it in items]
    p.update(kw)
    return p


@pytest.mark.parametrize("items", [
    pytest.param([dict(LONA)], id="una_linea"),
    # MARIA-8: la misma posición va en un ítem con sub-ítems.
    pytest.param(DOS_LONAS, id="misma_posicion"),
    # Un grupo suma y redondea una vez: 10,005 + 10,005 = 20,01 (y no 20,02).
    pytest.param([{**LONA, "cantidad": 3, "valor_unitario": 3.335, "peso_kg": 1.0, "grupo_id": 1,
                   "descripcion": "Lona de PVC A"},
                  {**LONA, "cantidad": 3, "valor_unitario": 3.335, "peso_kg": 1.0, "grupo_id": 1,
                   "descripcion": "Lona de PVC B"}], id="grupo"),
    pytest.param([{**LONA, "cantidad": 3, "valor_unitario": 3.335, "peso_kg": 1.0},
                  {**LONA, "pieza": "39219090000X", "cantidad": 3, "valor_unitario": 3.335,
                   "peso_kg": 1.0}], id="cada_una_al_centavo"),
])
def test_el_fob_de_la_factura_es_el_mddtfob_del_txt(client, items, request):
    _registrar_con_cuit(client, "valor1_" + request.node.callspec.id)
    pedido = _pedido_con(items, ajustes_deducir=1)
    r = client.post("/generate_maria/avisos", json=pedido)
    assert r.status_code == 200, r.text
    fob = r.json()["valor"]["fob_factura"]
    g = client.post("/generate_maria", json=pedido)
    assert g.status_code == 200, g.text
    assert _valor(g.json()["content"], "MDDTFOB") == [f"{fob:.2f}"]


def test_el_txt_es_el_mismo_con_y_sin_ajustes(client):
    _registrar_con_cuit(client, "valor1_txt")
    sin = client.post("/generate_maria", json=_pedido())
    con = client.post("/generate_maria", json={**_pedido(), "ajustes_incluir": 300, "ajustes_deducir": 120.5})
    assert sin.status_code == con.status_code == 200, (sin.text, con.text)
    assert sin.json()["content"] == con.json()["content"]
    assert _valor(con.json()["content"], "MDDTFOB") == ["1387.50"]


def test_un_ajuste_que_no_cierra_no_frena_la_generacion(client):
    """Los ajustes no van al TXT: un casillero negativo se ve en la tarjeta,
    pero el TXT sale igual."""
    _registrar_con_cuit(client, "valor1_no_frena")
    r = client.post("/generate_maria", json={**_pedido(), "ajustes_deducir": 999999})
    assert r.status_code == 200, r.text


# ------------------------------------------------ los avisos de antes


def test_los_avisos_traen_las_cuentas_y_dicen_que_el_casillero_va_a_mano(client):
    _registrar_con_cuit(client, "valor1_avisos")
    r = client.post("/generate_maria/avisos", json={**_pedido(), "ajustes_deducir": 87.5})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["valor"] == {
        "fob_factura": 1387.5, "ajustes_incluir": 0.0, "ajustes_deducir": 87.5,
        "fob_casillero": 1300.0, "flete": 7925.0, "seguro": 12.4, "seguro_sugerido": 92.25,
        "base_seguro": "FOB casillero",
    }
    # Que no parezca que ya se descuenta (respuesta de la PM a D12).
    assert ("El TXT todavía lleva el FOB de la factura (DOL 1.387,50); el FOB casillero con los ajustes "
            "(DOL 1.300,00) va al TXT en una próxima versión.") in data["avisos"]


def test_sin_ajustes_no_hay_aviso_del_casillero(client):
    _registrar_con_cuit(client, "valor1_sin_aviso")
    r = client.post("/generate_maria/avisos", json=_pedido())
    assert r.status_code == 200, r.text
    assert r.json()["valor"]["fob_casillero"] == 1387.5
    assert not any("FOB casillero" in a for a in r.json()["avisos"])


def test_un_ajuste_invalido_va_en_la_tarjeta_y_no_tapa_los_otros_avisos(client):
    _registrar_con_cuit(client, "valor1_invalido")
    r = client.post("/generate_maria/avisos", json={**_pedido(cuit_agr=""), "ajustes_incluir": -5})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["valor"] == {"error": "Ajustes a incluir: «-5.0» no es un importe válido "
                                      "(entre 0 y 1.000.000.000.000)."}
    assert not any("FOB casillero" in a for a in data["avisos"])


def test_un_casillero_negativo_va_en_la_tarjeta(client):
    _registrar_con_cuit(client, "valor1_negativo")
    r = client.post("/generate_maria/avisos", json={**_pedido(), "ajustes_deducir": 2000})
    assert r.status_code == 200, r.text
    assert r.json()["valor"]["error"].startswith("Los ajustes a deducir (2.000,00) superan")


# ------------------------------------------------------ la pantalla


def _funciones(archivo, nombres):
    fuente = (V2 / archivo).read_text(encoding="utf-8")
    partes = []
    for nombre in nombres:
        m = re.search(rf"\n(\s*)function {nombre}\([^)]*\) \{{.*?\n\1\}}", fuente, re.S)
        assert m, f"no está {nombre} en {archivo}"
        partes.append(m.group(0))
    return "\n".join(partes)


# Un DOM mínimo: cada id es un objeto con value, hidden y textContent.
DOM = """
const els = {};
function el(id) { return els[id] || (els[id] = { id, value: '', hidden: true, textContent: '', innerHTML: '',
    style: {}, validity: {}, listeners: {}, addEventListener(t, f) { this.listeners[t] = f; } }); }
const document = { activeElement: null, getElementById: el };
let refrescos = 0;
function refrescarAvisos() { refrescos++; }
let avisosTimer = null;
const CDI = { state: { operacion: OP, items: [] }, escapeHtml: s => String(s) };
"""


def _correr(codigo, op):
    salida = subprocess.run(["node", "-e", DOM.replace("OP", json.dumps(op)) + codigo],
                            check=True, capture_output=True, text=True)
    return json.loads(salida.stdout)


def _pantalla(op, despues, valor=None):
    nombres = ["ajusteMalEscrito", "importeEscrito", "usarDescuento", "calcularSeguro", "pintarValor"]
    codigo = ("let ultimoValor = null;\n" + _funciones("finalize.js", nombres) +
              f"\npintarValor({json.dumps(valor)});\n{despues}\n"
              "console.log(JSON.stringify({op: CDI.state.operacion, refrescos,"
              " els: Object.fromEntries(Object.entries(els).map(([k, v]) =>"
              " [k, {value: v.value, hidden: v.hidden, textContent: v.textContent, innerHTML: v.innerHTML}]))}));")
    return _correr(codigo, op)


VALOR = {"fob_factura": 1387.5, "ajustes_incluir": 0.0, "ajustes_deducir": 0.0, "fob_casillero": 1387.5,
         "flete": 7925.0, "seguro": 0.0, "seguro_sugerido": 93.13, "base_seguro": "FOB casillero"}


def test_el_descuento_de_la_planilla_se_ofrece_y_no_se_pone_solo():
    r = _pantalla({"descuento": 87.5, "filas_excel_descuento": [14]}, "", VALOR)
    assert "ajustes_deducir" not in r["op"]
    assert r["els"]["valorDeducir"]["value"] == ""
    assert r["els"]["valorDescuento"]["hidden"] is False
    assert r["els"]["valorDescuentoTexto"]["textContent"] == "La planilla trae un descuento de 87,50 (fila 14)."


def test_el_boton_pone_el_descuento_como_ajuste_a_deducir():
    r = _pantalla({"descuento": 87.5}, "usarDescuento();", VALOR)
    assert r["op"]["ajustes_deducir"] == "87.5"
    assert r["els"]["valorDeducir"]["value"] == "87.5"
    assert r["refrescos"] == 1


def test_sin_descuento_no_se_ofrece_nada():
    r = _pantalla({}, "", VALOR)
    assert r["els"]["valorDescuento"]["hidden"] is True


def test_el_boton_del_seguro_pone_el_sugerido_y_aparece_sin_seguro():
    r = _pantalla({}, "calcularSeguro();", VALOR)
    assert r["els"]["valorCalcularSeguro"]["hidden"] is False
    assert r["els"]["valorCalcularSeguro"]["textContent"] == "Calcular seguro (1 % de FOB casillero + flete): 93,13"
    assert r["op"]["seguro"] == 93.13 and r["op"]["seguro_calculado"] is True
    assert r["refrescos"] == 1


def test_despues_de_calcular_el_seguro_la_nota_dice_la_base():
    # Lo que se pinta cuando vuelve la cuenta con el seguro nuevo.
    r = _pantalla({}, "calcularSeguro(); pintarValor({...ultimoValor, seguro: 93.13});", VALOR)
    assert r["els"]["valorCalcularSeguro"]["hidden"] is True
    assert r["els"]["valorSeguroNota"]["textContent"] == "Seguro calculado: 1 % de (FOB casillero + flete)."


def test_el_boton_nombra_la_base_que_dice_el_servidor():
    r = _pantalla({}, "", {**VALOR, "base_seguro": "FOB de la factura", "seguro_sugerido": 93.13})
    assert r["els"]["valorCalcularSeguro"]["textContent"] == (
        "Calcular seguro (1 % de FOB de la factura + flete): 93,13")


def test_con_seguro_de_la_factura_no_se_ofrece_calcularlo():
    r = _pantalla({"seguro": 12.4}, "", {**VALOR, "seguro": 12.4})
    assert r["els"]["valorCalcularSeguro"]["hidden"] is True
    assert r["els"]["valorSeguroNota"]["textContent"] == "La operación ya trae seguro."


def test_un_seguro_calculado_con_otros_importes_se_ofrece_recalcular():
    r = _pantalla({"seguro": 93.13, "seguro_calculado": True},
                  "", {**VALOR, "seguro": 93.13, "seguro_sugerido": 92.25})
    assert r["els"]["valorCalcularSeguro"]["hidden"] is False
    assert r["els"]["valorCalcularSeguro"]["textContent"].startswith("Recalcular seguro")
    assert r["els"]["valorSeguroNota"]["textContent"] == "El seguro se calculó con otros importes."


def test_las_cuentas_se_ven_y_el_error_tambien():
    r = _pantalla({}, "", VALOR)
    assert "= FOB casillero" in r["els"]["valorCuentas"]["innerHTML"]
    assert "1.387,50" in r["els"]["valorCuentas"]["innerHTML"]
    r = _pantalla({"ajustes_deducir": "mal escrito"}, "", {"error": "Ajustes a deducir: x"})
    assert r["els"]["valorError"]["hidden"] is False
    assert r["els"]["valorError"]["textContent"] == "Ajustes a deducir: no es un número. Ajustes a deducir: x"
    assert r["els"]["valorCuentas"]["innerHTML"] == ""
    assert r["els"]["valorCalcularSeguro"]["hidden"] is True


def test_el_pedido_manda_los_ajustes_y_nunca_algo_que_frene_el_txt():
    codigo = _funciones("finalize.js", ["ajusteDelPedido"]) + (
        "\nconsole.log(JSON.stringify(['', null, undefined, '12.5', 'mal escrito', '1e999', 0, '0']"
        ".map(ajusteDelPedido)));")
    assert _correr(codigo, {}) == [None, None, None, 12.5, None, None, 0, 0]
    fuente = (V2 / "finalize.js").read_text(encoding="utf-8")
    pedido = re.search(r"function buildMariaRequest\(\) \{.*?\n    \}", fuente, re.S).group(0)
    assert "ajustes_incluir: ajusteDelPedido(op.ajustes_incluir)" in pedido
    assert "ajustes_deducir: ajusteDelPedido(op.ajustes_deducir)" in pedido


def test_un_seguro_escrito_a_mano_deja_de_ser_el_calculado():
    stubs = ("let form = {}; const initialPdfValues = {};\n"
             "function updateFieldHint() {} function validateField() {} function renderMissingCount() {}\n"
             "function updateContinueEnabled() {} function renderIncotermWarning() {} function renderProrrateoPanel() {}\n")
    codigo = stubs + _funciones("review.js", ["onFieldChange"]) + (
        "\nonFieldChange({target: {name: 'seguro', type: 'number', value: '15'}});"
        "\nconsole.log(JSON.stringify(CDI.state.operacion));")
    assert _correr(codigo, {"seguro": 93.13, "seguro_calculado": True}) == {"seguro": 15}
