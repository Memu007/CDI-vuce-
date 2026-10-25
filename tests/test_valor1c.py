"""VALOR-1c: lo que quedó de VALOR-1b y MARIA-9.

1. Un seguro que calculó el sistema con otras cuentas no llega al TXT sin
   que la persona elija recalcularlo o dejarlo.
2. D18 (b): el sufijo general que nadie usa no se controla ni se avisa.
3. El error de kilos nombra a todos cuando el cero sale del ajuste.
4. Sin productos, un error claro en los dos endpoints.
5. Casos que distinguen mutaciones que antes seguían en verde.

Datos inventados, con la forma de la factura del 24/10.
"""
import json
import uuid

import pytest

from proyecto_maria.core import maria_generator as mg
from tests.test_maria7_rechazos_24_10 import LONA, _gen, _registrar_con_cuit, _valor
from tests.test_maria9_kilos import _renglon
from tests.test_valor1 import VALOR, _correr, _funciones, _pantalla, _pedido_con

# FOB 1.387,50 y flete 7.925: el 1 % da 93,13. 14,88 es el de flete 100.
VIEJO = "Seguro: lo calculó el sistema con otros importes; con los de ahora da 93,13 y la operación lleva 14,88."


# ------------------------------------- 1. el seguro calculado con otras cuentas


def test_un_seguro_calculado_con_otras_cuentas_no_genera(client):
    _registrar_con_cuit(client, "valor1c_viejo")
    r = client.post("/generate_maria", json=_pedido_con([LONA], seguro=14.88, seguro_calculado=True))
    assert r.status_code == 400, r.text
    assert r.json()["detail"].startswith(VIEJO), r.text
    assert "«Ajustes y seguro»" in r.json()["detail"]


def test_los_avisos_lo_dicen_antes_con_el_mismo_texto(client):
    _registrar_con_cuit(client, "valor1c_aviso")
    pedido = _pedido_con([LONA], seguro=14.88, seguro_calculado=True)
    avisos = client.post("/generate_maria/avisos", json=pedido).json()["avisos"]
    detalle = client.post("/generate_maria", json=pedido).json()["detail"]
    assert detalle in avisos


def test_un_seguro_calculado_con_las_cuentas_de_ahora_genera(client):
    _registrar_con_cuit(client, "valor1c_al_dia")
    pedido = _pedido_con([LONA], seguro=93.13, seguro_calculado=True)
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 200, r.text
    assert _valor(r.json()["content"], "MDDTASS") == ["93.13"]
    assert not [a for a in client.post("/generate_maria/avisos", json=pedido).json()["avisos"]
                if a.startswith("Seguro: ")]


def test_un_seguro_que_no_calculo_el_sistema_no_se_toca(client):
    # El de la factura o el que se escribió a mano (review.js borra la marca).
    _registrar_con_cuit(client, "valor1c_propio")
    r = client.post("/generate_maria", json=_pedido_con([LONA], seguro=14.88))
    assert r.status_code == 200, r.text
    assert _valor(r.json()["content"], "MDDTASS") == ["14.88"]


def test_si_no_se_pueden_hacer_las_cuentas_tampoco_genera(client):
    _registrar_con_cuit(client, "valor1c_sin_cuentas")
    pedido = _pedido_con([LONA], seguro=14.88, seguro_calculado=True, ajustes_deducir=5000)
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 400, r.text
    detalle = r.json()["detail"]
    assert detalle.startswith("Seguro: lo calculó el sistema y ahora no se puede comprobar: "
                              "Los ajustes a deducir (5.000,00) superan"), detalle
    assert detalle in client.post("/generate_maria/avisos", json=pedido).json()["avisos"]
    # Sin la marca, el ajuste no frena el TXT (VALOR-1).
    sin = client.post("/generate_maria", json={**pedido, "seguro_calculado": False})
    assert sin.status_code == 200, sin.text


def test_el_pedido_dice_si_el_seguro_lo_calculo_el_sistema():
    # Sin el campo, el servidor no tiene cómo saberlo.
    pedido = "console.log(JSON.stringify([buildMariaRequest().seguro_calculado]));"
    assert _pantalla({"seguro": 14.88, "seguro_calculado": True}, pedido, VALOR, salida_propia=True) == [True]
    assert _pantalla({"seguro": 14.88}, pedido, VALOR, salida_propia=True) == [False]


def test_con_otras_cuentas_se_ofrece_dejarlo_como_esta():
    r = _pantalla({"seguro": 14.88, "seguro_calculado": True}, "",
                  {**VALOR, "seguro": 14.88})
    assert r["els"]["valorDejarSeguro"]["hidden"] is False
    assert r["els"]["valorCalcularSeguro"]["hidden"] is False


@pytest.mark.parametrize("op,valor", [
    pytest.param({"seguro": 93.13, "seguro_calculado": True}, {**VALOR, "seguro": 93.13}, id="al_dia"),
    pytest.param({"seguro": 14.88}, {**VALOR, "seguro": 14.88}, id="no_lo_calculo"),
    pytest.param({}, VALOR, id="sin_seguro"),
])
def test_si_no_hay_nada_viejo_no_se_ofrece_dejarlo(op, valor):
    r = _pantalla(op, "", valor)
    assert r["els"]["valorDejarSeguro"]["hidden"] is True


def test_con_las_cuentas_en_error_tambien_se_puede_dejar():
    # Si no, el servidor no deja generar y no hay cómo salir.
    r = _pantalla({"seguro": 14.88, "seguro_calculado": True}, "", {"error": "x"})
    assert r["els"]["valorDejarSeguro"]["hidden"] is False


def test_dejarlo_saca_la_marca_y_pide_las_cuentas_de_nuevo():
    r = _pantalla({"seguro": 14.88, "seguro_calculado": True}, "dejarSeguro();",
                  {**VALOR, "seguro": 14.88})
    assert r["op"] == {"seguro": 14.88}
    assert r["refrescos"] == 1
    assert r["els"]["valorDejarSeguro"]["hidden"] is True


def test_el_boton_de_dejarlo_esta_enlazado():
    r = _pantalla({"seguro": 14.88, "seguro_calculado": True},
                  "enlazarValor(); els.valorDejarSeguro.listeners.click();",
                  {**VALOR, "seguro": 14.88})
    assert "seguro_calculado" not in r["op"]


def _generar_en_pantalla(detalle):
    """generateMaria de verdad, con un servidor que contesta `detalle`."""
    stubs = ("let generateInFlight = false; let lastMaria = null; let sbtError = null;\n"
             "let fueA = null; let mostrado = null; CDI.goTo = p => { fueA = p; }; CDI.track = () => {};\n"
             "function showReadyError(m) { mostrado = m; } function buildMariaRequest() { return {}; }\n"
             "CDI.state.items = [{}]; console.error = () => {};\n"
             f"CDI.api = async () => ({{ok: false, statusText: 'x', json: async () => ({{detail: {json.dumps(detalle)}}})}});\n")
    codigo = stubs + _funciones("finalize.js", ["generateMaria"]) + (
        "\ngenerateMaria().then(() => console.log(JSON.stringify({fueA, mostrado})));")
    return _correr(codigo, {})


def test_si_el_servidor_lo_frena_se_vuelve_a_las_cuentas():
    r = _generar_en_pantalla(VIEJO + " Recalculalo o dejalo como está en «Ajustes y seguro».")
    assert r["fueA"] == "validating"


@pytest.mark.parametrize("detalle", [
    "Item 1: algo",
    # El seguro mal escrito empieza igual y se corrige en la revisión.
    "Seguro: «abc» no es un importe.",
])
def test_otro_error_se_queda_en_la_pantalla_de_generar(detalle):
    # Que la vuelta no dependa de cualquier error.
    assert _generar_en_pantalla(detalle)["fueA"] is None


# --------------------------------------------- 2. D18: el general que nadie usa


def _cada_uno_con_el_suyo(general):
    # Dos renglones de la misma posición: van juntos, cada uno con su sufijo.
    pedido = _pedido_con([LONA, dict(LONA, descripcion="Lona de PVC azul 620 g")], sbt_sufijo_valor=general)
    pedido["items"][0]["sufijo"] = "AA(MARCA)-AI(GRIS)-"
    pedido["items"][1]["sufijo"] = "AA(MARCA)-AI(AZUL)-"
    return pedido


def test_un_general_que_nadie_usa_no_frena_ni_se_avisa(client):
    _registrar_con_cuit(client, "valor1c_d18")
    pedido = _cada_uno_con_el_suyo("AA(X=Y)")
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 200, r.text
    assert "X=Y" not in r.json()["content"] and "X Y" not in r.json()["content"]
    avisos = client.post("/generate_maria/avisos", json=pedido).json()["avisos"]
    assert not [a for a in avisos if "operación" in a and "ufijo" in a], avisos
    assert not [a for a in avisos if "X Y" in a or "X=Y" in a], avisos


@pytest.mark.parametrize("general,dice", [
    ("AA(MARCA)-AB(MOD=1)-", "no puede contener «=»"),
    ("AA(X)-AB(Y\x7f)-", "saltos de línea ni caracteres de control"),
    ("A" * 121, "120 caracteres"),
])
def test_un_general_que_se_usa_sigue_controlado(client, general, dice):
    _registrar_con_cuit(client, f"valor1c_d18_{uuid.uuid4().hex[:8]}")
    pedido = _pedido_con([LONA], sbt_sufijo_valor=general)
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 400 and dice in r.text, r.text


# --------------------------------------------- 3. kilos: el cero del ajuste


def test_si_el_ajuste_deja_en_cero_a_uno_que_no_era_chico_se_nombran_todos():
    # 0,005 + 0,005 + 0,005 + 0,004 = 0,019 → 0,02; solos dan 0,01 + 0,01 +
    # 0,01 + 0,00 = 0,03. El centavo que sobra se le saca al primero, que
    # queda en cero sin ser el chico: el 4 solo no explica el error.
    with pytest.raises(ValueError) as error:
        _gen([_renglon(n, p) for n, p in enumerate((0.005, 0.005, 0.005, 0.004))])
    assert str(error.value).startswith("Item 1: los renglones 1, 2, 3 y 4 son tan chicos que"), str(error.value)


OTRO = dict(LONA, pieza="39211390900F", descripcion="Espuma de PVC", unidad="kg", unidad_estadistica="01")


@pytest.mark.parametrize("renglones,mensaje", [
    # El número es el renglón del pedido, no el lugar dentro del ítem.
    pytest.param([OTRO, _renglon(1, 300.0), _renglon(2, 0.004)], "Item 2: el renglón 3 es", id="despues_de_otro"),
    pytest.param([_renglon(1, 300.0), OTRO, _renglon(2, 0.004)], "Item 1: el renglón 3 es", id="intercalado"),
])
def test_el_error_de_kilos_nombra_el_renglon_del_pedido(renglones, mensaje):
    with pytest.raises(ValueError) as error:
        _gen(renglones)
    assert str(error.value).startswith(mensaje), str(error.value)


# --------------------------------------------------------- 4. sin productos


SIN_PRODUCTOS = "No hay productos para generar: volvé a cargar la factura."


@pytest.mark.parametrize("general", ["", "AA(MARCA)-"])
def test_sin_productos_no_se_genera(client, general):
    _registrar_con_cuit(client, f"valor1c_vacio_{uuid.uuid4().hex[:8]}")
    pedido = {**_pedido_con([LONA], sbt_sufijo_valor=general), "items": []}
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 400 and r.json()["detail"] == SIN_PRODUCTOS, r.text
    avisos = client.post("/generate_maria/avisos", json=pedido)
    assert avisos.status_code == 200 and SIN_PRODUCTOS in avisos.json()["avisos"], avisos.text


# ------------------------------------------- 5. casos que distinguen mutaciones


def test_el_seguro_sugerido_usa_el_flete_al_centavo():
    # 1 % de (1.000 + 0,50) = 10,005 → 10,01; con el flete sin redondear,
    # 1 % de 1.000,495 = 10,00495 → 10,00.
    v = mg.cuentas_del_valor([{"cantidad": 1, "valor_unitario": 1000}], flete=0.495)
    assert v["flete"] == 0.50 and v["seguro_sugerido"] == 10.01


def test_un_cambio_en_los_productos_invalida_las_cuentas():
    r = _pantalla({}, "CDI.state.items.push({pieza: 'X', cantidad: 1}); calcularSeguro();", VALOR)
    assert "seguro" not in r["op"]
    assert r["refrescos"] == 1


def test_al_entrar_a_validar_no_quedan_las_cuentas_de_antes():
    stubs = ("let ultimoValor = null; let cuentasCon = null; let vLoading = null;\n"
             "function enlazarAvisos() {} function enlazarValor() {} function init() {}\n")
    codigo = stubs + _funciones("finalize.js", ["ajusteMalEscrito", "importeEscrito", "otroDeducir", "seguroSinLeer",
                                                "ajusteDelPedido", "pintarValor", "onEnterValidating"]) + (
        f"\npintarValor({json.dumps(VALOR)}, 'firma de otra operación');"
        "\nonEnterValidating();"
        "\nconsole.log(JSON.stringify({ultimoValor, cuentasCon, cuentas: els.valorCuentas.innerHTML,"
        " boton: els.valorCalcularSeguro.hidden}));")
    r = _correr(codigo, {})
    assert r == {"ultimoValor": None, "cuentasCon": None, "cuentas": "", "boton": True}


def test_el_iva_adicional_de_la_operacion_junta_los_renglones(client):
    """Uno con IVAAD1 propio y otro que lo toma de la operación van juntos,
    cada uno con su sufijo: el general no hace falta."""
    _registrar_con_cuit(client, "valor1c_iva")
    pedido = _cada_uno_con_el_suyo("")
    pedido["iva_adicional"] = "IVAAD1"
    pedido["items"][0]["iva_adicional"] = "IVAAD1"
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 200, r.text
    assert r.json()["content"].count("[ART]") == 1


def test_los_avisos_usan_la_procedencia_de_la_operacion(client):
    _registrar_con_cuit(client, "valor1c_proc")
    pedido = _pedido_con([LONA], procedencia="UY")
    con = client.post("/generate_maria/avisos", json=pedido).json()["supuestos"]
    sin = client.post("/generate_maria/avisos", json={**pedido, "procedencia": ""}).json()["supuestos"]
    assert [a for a in sin if a.startswith("Procedencia: ")]
    assert not [a for a in con if a.startswith("Procedencia: ")], con
