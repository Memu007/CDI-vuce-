"""SEGURO-2: lo que antes sólo se avisaba ahora frena la generación hasta que
se corrige.

1. Un seguro que la factura traía y no se pudo leer, mientras no se complete.
   Un 0 escrito a propósito sí genera.
2. El 1 % que se dejó como estaba, con un incoterm que ya lleva el seguro en
   el precio.

Datos inventados, con la forma de la factura del 24/10.
"""
import pytest

from tests.test_maria7_rechazos_24_10 import LONA, _registrar_con_cuit, _valor
from tests.test_seguro1 import EN_EL_PRECIO, SUGERIDO, VALOR_CIF
from tests.test_valor1 import VALOR, _correr, _funciones, _pantalla, _pedido_con
from tests.test_valor1c import _generar_en_pantalla

COMPLETAR = "Seguro: no pudimos leerlo de la factura. Completalo en la revisión; si la factura no trae seguro, escribí 0."


# ------------------------------------------------------- 1. para completar


@pytest.mark.parametrize("incoterm,seguro", [
    ("CIF", ""), ("CIF", 0), ("FOB", ""), ("CFR", 14.88),
])
def test_un_seguro_sin_leer_no_genera_y_los_avisos_lo_dicen(client, incoterm, seguro):
    _registrar_con_cuit(client, f"seguro2_{incoterm}_{str(seguro).replace('.', '_')}")
    pedido = _pedido_con([LONA], incoterm=incoterm, seguro=seguro, seguro_para_completar=True)
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == COMPLETAR
    assert COMPLETAR in client.post("/generate_maria/avisos", json=pedido).json()["avisos"]


def test_el_cero_escrito_a_proposito_genera(client):
    _registrar_con_cuit(client, "seguro2_cero")
    pedido = _pedido_con([LONA], incoterm="CIF", seguro=0)
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 200, r.text
    assert _valor(r.json()["content"], "MDDTASS") == ["0.00"]
    assert COMPLETAR not in client.post("/generate_maria/avisos", json=pedido).json()["avisos"]


@pytest.mark.parametrize("op,manda", [
    pytest.param({"campos_sin_leer": ["seguro"]}, True, id="sin_leer"),
    pytest.param({"campos_sin_leer": ["seguro"], "campos_completados": ["seguro"]}, False, id="completado"),
    pytest.param({"campos_sin_leer": ["flete"]}, False, id="otro_campo"),
    pytest.param({}, False, id="sin_lista"),
])
def test_el_pedido_dice_si_el_seguro_sigue_para_completar(op, manda):
    pedido = "console.log(JSON.stringify(buildMariaRequest().seguro_para_completar));"
    assert _pantalla({"incoterm": "CIF", **op}, pedido, VALOR_CIF, salida_propia=True) is manda


def test_si_el_servidor_pide_completarlo_se_vuelve_a_la_revision():
    assert _generar_en_pantalla(COMPLETAR)["fueA"] == "review"


def _seguro_sin_leer():
    return _funciones("finalize.js", ["seguroSinLeer"]) + "\nCDI.seguroSinLeer = seguroSinLeer;\n"


@pytest.mark.parametrize("op,campo,se_ve", [
    pytest.param({"seguro": 0, "campos_sin_leer": ["seguro"]}, "seguro", "", id="sin_leer"),
    pytest.param({"flete": 30, "campos_sin_leer": ["seguro", "flete"]}, "flete", "30", id="flete_sin_leer"),
    pytest.param({"seguro": 0, "campos_sin_leer": ["seguro"], "campos_completados": ["seguro"]}, "seguro", "0",
                 id="cero_escrito"),
    pytest.param({"seguro": 0, "campos_sin_leer": ["flete"]}, "seguro", "0", id="leido"),
])
def test_un_campo_sin_leer_se_ve_vacio_en_la_revision(op, campo, se_ve):
    # Un 0 a la vista parece leído, y escribir el mismo 0 no lo completaría.
    codigo = "const MONTOS = ['flete', 'seguro', 'gastos_anteriores_fob'];\n" + _seguro_sin_leer() + _funciones(
        "review.js", ["normalizeValueForField", "valorEnLaRevision"]) + (
        f"\nconsole.log(JSON.stringify(valorEnLaRevision({campo!r}, CDI.state.operacion)));")
    assert _correr(codigo, op) == se_ve


def test_la_revision_muestra_vacio_el_seguro_sin_leer_y_lo_deja_en_0():
    codigo = (
        "const FIELDS = ['seguro', 'flete'];\nlet initialPdfValues = {}, fieldsFromUserDefaults = {};\n"
        "const campos = {seguro: {type: 'number', value: ''}, flete: {type: 'number', value: ''}};\n"
        "const form = {querySelector: s => campos[s.match(/name=\"(\\w+)\"/)[1]]};\n"
        "function init() {} function applyClienteActivo() {} function maybeShowPendingImporterBanner() {}\n"
        "function $() { return null; } function hasTransportData() { return false; }\n"
        "function hasAduanaCustom() { return false; } function renderMetaPill() {} function recomputeHints() {}\n"
        "function validateAll() {} function renderIncotermWarning() {} function renderProrrateoPanel() {}\n"
        "const MONTOS = ['flete', 'seguro', 'gastos_anteriores_fob'];\n" + _seguro_sin_leer()
        + _funciones("review.js", ["montoDelCampo", "normalizeValueForField", "valorEnLaRevision",
                                   "applyUserDefaults", "populate"])
        + "\npopulate();\nconsole.log(JSON.stringify([campos.seguro.value, campos.flete.value, "
          "CDI.state.operacion.seguro]));")
    assert _correr(codigo, {"seguro": 0, "flete": 30, "campos_sin_leer": ["seguro"]}) == ["", "30", 0]


@pytest.mark.parametrize("valor,completado", [("0", True), ("15", True), ("", False)])
def test_escribir_el_seguro_sin_leer_lo_completa(valor, completado):
    codigo = _stubs_de_la_revision() + (
        f"\nonFieldChange({{target: {{name: 'seguro', type: 'number', value: {valor!r}}}}});"
        "\nconsole.log(JSON.stringify(CDI.state.operacion.campos_completados));")
    assert _correr(codigo, {"seguro": 0, "campos_sin_leer": ["seguro"]}) == (["seguro"] if completado else [])


# ----------------------------------------------------------- 2. el 1 % dejado


def test_el_uno_por_ciento_dejado_no_genera_con_cif(client):
    _registrar_con_cuit(client, "seguro2_dejado_cif")
    pedido = _pedido_con([LONA], incoterm="CIF", seguro=14.88, seguro_dejado=True)
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == EN_EL_PRECIO
    assert EN_EL_PRECIO in client.post("/generate_maria/avisos", json=pedido).json()["avisos"]


def test_el_uno_por_ciento_dejado_genera_con_cfr(client):
    # Dejarlo es elegirlo: con otros importes no se vuelve a frenar.
    _registrar_con_cuit(client, "seguro2_dejado_cfr")
    pedido = _pedido_con([LONA], incoterm="CFR", seguro=14.88, seguro_dejado=True)
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 200, r.text
    assert _valor(r.json()["content"], "MDDTASS") == ["14.88"]


def test_el_pedido_dice_si_el_seguro_se_dejo():
    pedido = "console.log(JSON.stringify([buildMariaRequest().seguro_dejado]));"
    assert _pantalla({"seguro": 14.88, "seguro_dejado": True}, pedido, VALOR, salida_propia=True) == [True]
    assert _pantalla({"seguro": 14.88}, pedido, VALOR, salida_propia=True) == [False]


def test_el_dejado_se_borra_al_pasar_a_cif_y_queda_para_completar():
    op = {"incoterm": "CIF", "seguro": 14.88, "seguro_dejado": True}
    r = _pantalla(op, "", {**VALOR_CIF, "seguro": 14.88})
    assert r["op"]["seguro"] == "" and "seguro_dejado" not in r["op"]
    assert r["op"]["campos_sin_leer"] == ["seguro"]
    assert r["refrescos"] == 1 and r["semaforos"] == 1


def test_recalcularlo_ya_no_es_el_dejado():
    op = {"seguro": 14.88, "seguro_dejado": True}
    r = _pantalla(op, "calcularSeguro();", {**VALOR, "seguro": 14.88})
    assert r["op"]["seguro"] == SUGERIDO and r["op"]["seguro_calculado"] is True
    assert "seguro_dejado" not in r["op"]


def _stubs_de_la_revision():
    stubs = ("let form = {}; const initialPdfValues = {};\n"
             "function updateFieldHint() {} function validateField() {} function renderMissingCount() {}\n"
             "function updateContinueEnabled() {} function renderIncotermWarning() {} function renderProrrateoPanel() {}\n")
    return stubs + "const MONTOS = ['flete', 'seguro', 'gastos_anteriores_fob'];\n" + _funciones(
        "review.js", ["montoDelCampo", "onFieldChange"])


def test_escribirlo_a_mano_ya_no_es_el_dejado():
    codigo = _stubs_de_la_revision() + (
        "\nonFieldChange({target: {name: 'seguro', type: 'number', value: '15'}});"
        "\nconsole.log(JSON.stringify(CDI.state.operacion));")
    assert _correr(codigo, {"seguro": 14.88, "seguro_dejado": True}) == {"seguro": 15}
