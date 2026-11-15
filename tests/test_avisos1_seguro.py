"""Lo que la persona lee del seguro, y dónde lo lee.

1. El 1 % que se borra al pasar a un incoterm con el seguro en el precio no se
   explica como un seguro que no se pudo leer de la factura.
2. Cada 400 de generar que cambia de pantalla deja el motivo a la vista en la
   pantalla donde cae la persona.

Datos inventados.
"""
import json
from pathlib import Path

import pytest

from tests.test_maria7_rechazos_24_10 import LONA, _registrar_con_cuit
from tests.test_seguro1 import EN_EL_PRECIO, VALOR_CIF
from tests.test_seguro2 import COMPLETAR, _stubs_de_la_revision
from tests.test_valor1 import VALOR, _correr, _funciones, _pantalla, _pedido_con

BORRADO = ("Seguro: el que calculó el sistema se borró al cambiar el incoterm. "
           "Cargá el de la factura en la revisión; si la factura no trae seguro, escribí 0.")
NO_SE_LEYO = "no pudimos leerlo"


# ------------------------------------------------- 1. el texto del borrado


def test_el_seguro_borrado_no_genera_y_dice_lo_que_paso(client):
    _registrar_con_cuit(client, "avisos1_borrado")
    pedido = _pedido_con([LONA], incoterm="CIF", seguro="", seguro_para_completar=True, seguro_borrado=True)
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == BORRADO
    avisos = client.post("/generate_maria/avisos", json=pedido).json()["avisos"]
    assert BORRADO in avisos and not any(NO_SE_LEYO in a for a in avisos)


def test_pasar_a_cif_marca_el_borrado_y_la_nota_lo_dice():
    op = {"incoterm": "CIF", "seguro": 14.88, "seguro_calculado": True}
    # La respuesta de los avisos que sigue al borrado vuelve a pintar la nota.
    r = _pantalla(op, f"pintarValor({json.dumps(VALOR_CIF)}, firmaDeAhora());", {**VALOR_CIF, "seguro": 14.88})
    assert r["op"]["seguro_borrado"] is True
    nota = r["els"]["valorSeguroNota"]["textContent"]
    assert NO_SE_LEYO not in nota.lower() and "se borró" in nota and "escribí 0" in nota
    pedido = "console.log(JSON.stringify(buildMariaRequest().seguro_borrado));"
    assert _pantalla(op, pedido, {**VALOR_CIF, "seguro": 14.88}, salida_propia=True) is True


def test_de_vuelta_a_fob_el_borrado_sigue_diciendo_lo_que_paso():
    op = {"incoterm": "FOB", "seguro": "", "seguro_borrado": True, "campos_sin_leer": ["seguro"]}
    nota = _pantalla(op, "", VALOR)["els"]["valorSeguroNota"]["textContent"]
    assert NO_SE_LEYO not in nota.lower() and "se borró" in nota


@pytest.mark.parametrize("borrado,dice", [(True, "se borró"), (False, "No pudimos leer el seguro")])
def test_el_semaforo_dice_si_el_seguro_se_borro_o_no_se_leyo(borrado, dice):
    fuente = (Path(__file__).parent.parent / "proyecto_maria/static/v2/screens/semaforo.js").read_text(encoding="utf-8")
    nombres = "var NOMBRES_SIN_LEER = {" + fuente.split("var NOMBRES_SIN_LEER = {", 1)[1].split("};", 1)[0] + "};\n"
    codigo = nombres + _funciones("semaforo.js", ["camposSinLeer"]) + "\nconsole.log(JSON.stringify(camposSinLeer()));"
    [aviso] = _correr(codigo, {"seguro_borrado": borrado, "campos_sin_leer": ["seguro"]})
    assert dice in aviso and "no pudimos leer" not in aviso.lower() if borrado else dice in aviso


def test_un_seguro_que_no_se_leyo_sigue_diciendolo():
    op = {"incoterm": "CIF", "seguro": "", "campos_sin_leer": ["seguro"]}
    r = _pantalla(op, "", VALOR_CIF)
    assert "seguro_borrado" not in r["op"]
    assert "No pudimos leerlo" in r["els"]["valorSeguroNota"]["textContent"]


@pytest.mark.parametrize("como", ["recalcularlo", "escribirlo"])
def test_la_marca_de_borrado_se_va(como):
    op = {"seguro": "", "seguro_borrado": True, "campos_sin_leer": ["seguro"]}
    if como == "recalcularlo":
        r = _pantalla(op, "calcularSeguro();", VALOR)["op"]
    else:
        r = _correr(_stubs_de_la_revision() + (
            "\nonFieldChange({target: {name: 'seguro', type: 'number', value: '15'}});"
            "\nconsole.log(JSON.stringify(CDI.state.operacion));"), op)
    assert "seguro_borrado" not in r


def test_vaciar_el_campo_deja_la_marca_de_borrado():
    r = _correr(_stubs_de_la_revision() + (
        "\nonFieldChange({target: {name: 'seguro', type: 'number', value: ''}});"
        "\nconsole.log(JSON.stringify(CDI.state.operacion));"),
        {"seguro": "", "seguro_borrado": True, "campos_sin_leer": ["seguro"]})
    assert r["seguro_borrado"] is True


# ------------------------------------- 2. el motivo, donde cae la persona


def _form_de_la_revision():
    # El campo y su error, y la revisión que al entrar los vuelve a validar.
    return ("const campo = {classes: new Set(), classList: {add(c) { campo.classes.add(c); },"
            " remove(c) { campo.classes.delete(c); }}, scrollIntoView() { campo.visto = true; }};\n"
            "const errSeguro = {textContent: '', hidden: true};\n"
            "const form = {querySelector: s => s === '[name=\"seguro\"]' ? campo :"
            " s === '[data-error-for=\"seguro\"]' ? errSeguro : null};\n")


def test_marcar_en_la_revision_pone_el_motivo_junto_al_campo():
    codigo = _form_de_la_revision() + _funciones("review.js", ["marcarEnLaRevision"]) + (
        "\nmarcarEnLaRevision('seguro', 'el motivo');"
        "\nconsole.log(JSON.stringify([errSeguro.textContent, errSeguro.hidden, [...campo.classes], !!campo.visto]));")
    assert _correr(codigo, {}) == ["el motivo", False, ["is-error"], True]


def test_la_revision_exporta_la_marca():
    fuente = (Path(__file__).parent.parent / "proyecto_maria/static/v2/screens/review.js").read_text(encoding="utf-8")
    assert "CDI.marcarEnLaRevision = marcarEnLaRevision;" in fuente


def _generar(detalle):
    """generateMaria de verdad ante un 400; cada pantalla, al entrar, borra lo
    que se le marcó antes, como hace la revisión al volver a validar."""
    stubs = (_form_de_la_revision() + _funciones("review.js", ["marcarEnLaRevision"]) +
             "\nCDI.marcarEnLaRevision = marcarEnLaRevision;\n"
             "let generateInFlight = false; let lastMaria = null; let fueA = null; let enNcm = null;\n"
             "let pedidaMientrasOtra = false; let lastValidation = null; function onEnterReady() {}\n"
             "const sbtError = {textContent: '', hidden: true};\n"
             "CDI.goTo = p => { fueA = p; if (p === 'review') { errSeguro.hidden = true; errSeguro.textContent = ''; }\n"
             "  if (p === 'validating') sbtError.hidden = true; };\n"
             "CDI.track = () => {}; function showReadyError() {} function buildMariaRequest() { return {}; }\n"
             "CDI.ncmBatch = {marcarErrorDeSubitem(i, s, d) { enNcm = d; return true; }};\n"
             "CDI.state.items = [{}]; console.error = () => {};\n"
             f"CDI.api = async () => ({{ok: false, statusText: 'x', json: async () => ({{detail: {json.dumps(detalle)}}})}});\n")
    codigo = stubs + _funciones("finalize.js", ["fotoDeLaPantalla", "generateMaria"]) + (
        "\ngenerateMaria().then(() => console.log(JSON.stringify({fueA, enNcm,"
        " sbt: sbtError.hidden ? null : sbtError.textContent,"
        " revision: errSeguro.hidden ? null : errSeguro.textContent})));")
    return _correr(codigo, {})


# Lo que se lee en «Ajustes y seguro» lo pintan los avisos al entrar; que los
# avisos lo traen lo prueba el servidor (test_seguro2, y el borrado arriba).
@pytest.mark.parametrize("detalle,pantalla,donde", [
    pytest.param("Item 1, sub-ítem 2: el NCM no va.", "ncm", "enNcm", id="subitem"),
    pytest.param("Sufijo de valor de la operación: falta AA00.", "validating", "sbt", id="sufijo"),
    pytest.param(EN_EL_PRECIO, "validating", None, id="seguro_en_el_precio"),
    pytest.param(COMPLETAR, "review", "revision", id="seguro_sin_leer"),
    pytest.param(BORRADO, "review", "revision", id="seguro_borrado"),
])
def test_cada_400_que_cambia_de_pantalla_deja_el_motivo_a_la_vista(detalle, pantalla, donde):
    r = _generar(detalle)
    assert r["fueA"] == pantalla
    if donde:
        assert r[donde] == detalle


def test_la_pista_del_seguro_pide_el_0_si_la_factura_no_lo_trae():
    html = (Path(__file__).parent.parent / "proyecto_maria/templates/dashboard_v2.html").read_text(encoding="utf-8")
    pista = html.split('name="seguro"', 1)[1].split('</span>', 1)[0]
    assert "Si la factura no trae seguro, escribí 0." in pista and "Dejar en 0 si no aplica" not in pista
