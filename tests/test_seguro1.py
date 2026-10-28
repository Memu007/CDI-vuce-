"""SEGURO-1: con CIF, CIP, DPU, DAP y DDP el seguro ya está en el precio.

Con esos incoterms el sistema no sugiere el 1 % y no hay botón «Calcular
seguro». El seguro se sigue declarando: el de la factura o el que escribe la
persona, y sale en el TXT como siempre. La regla vive en el servidor; la
pantalla sigue lo que dice. Si el seguro lo calculó el sistema y el incoterm
pasa a uno de los cinco, se borra y queda para completar.

Datos inventados, con la forma de la factura del 24/10.
"""
import pytest

from proyecto_maria.core import maria_generator as mg
from tests.test_maria7_rechazos_24_10 import LONA, _registrar_con_cuit, _valor
from tests.test_valor1 import VALOR, _pantalla, _pedido_con

LOS_CINCO = ["CIF", "CIP", "DPU", "DAP", "DDP"]
CON_BOTON = ["CFR", "CPT", "FOB", "EXW", "FCA", "FAS"]
# FOB 1.387,50 y flete 7.925 (los de _pedido): el 1 % da 93,13.
SUGERIDO = 93.13
EN_EL_PRECIO = ("Seguro: lo calculó el sistema, pero con CIF el seguro ya está en el precio "
                "y no se calcula. Cargá el de la factura en la revisión.")
VALOR_CIF = {**VALOR, "seguro_sugerido": None, "seguro_en_el_precio": True}


def _cuentas(incoterm):
    return mg.cuentas_del_valor([dict(LONA)], flete=7925, incoterm=incoterm)


# ------------------------------------------------------------- la regla


@pytest.mark.parametrize("incoterm", LOS_CINCO)
def test_con_los_cinco_no_hay_sugerencia(incoterm):
    v = _cuentas(incoterm)
    assert v["seguro_sugerido"] is None and v["seguro_en_el_precio"] is True


@pytest.mark.parametrize("incoterm", CON_BOTON)
def test_con_los_demas_sigue_el_uno_por_ciento(incoterm):
    v = _cuentas(incoterm)
    assert v["seguro_sugerido"] == SUGERIDO and v["seguro_en_el_precio"] is False


@pytest.mark.parametrize("incoterm", ["cif", " Cif ", "\tdap\n", "dDp "])
def test_mayusculas_minusculas_y_espacios_dan_lo_mismo(incoterm):
    assert _cuentas(incoterm)["seguro_sugerido"] is None


@pytest.mark.parametrize("incoterm", ["", None, "  ", "XYZ", "C I F"])
def test_vacio_o_desconocido_como_antes(incoterm):
    assert _cuentas(incoterm)["seguro_sugerido"] == SUGERIDO
    # Sin incoterm, como lo llamaba VALOR-1.
    assert mg.cuentas_del_valor([dict(LONA)], flete=7925)["seguro_sugerido"] == SUGERIDO


# ------------------------------------------------------------ el servidor


@pytest.mark.parametrize("incoterm,sugerido", [
    *[pytest.param(i, None, id=i) for i in LOS_CINCO],
    pytest.param("CFR", SUGERIDO, id="CFR"),
    pytest.param("CPT", SUGERIDO, id="CPT"),
    pytest.param(" cif ", None, id="cif_con_espacios"),
])
def test_los_avisos_traen_la_regla_del_servidor(client, incoterm, sugerido):
    _registrar_con_cuit(client, f"seguro1_avisos_{incoterm.strip().lower()}_{len(incoterm)}")
    r = client.post("/generate_maria/avisos", json=_pedido_con([LONA], incoterm=incoterm))
    assert r.status_code == 200, r.text
    assert r.json()["valor"]["seguro_sugerido"] == sugerido
    assert r.json()["valor"]["seguro_en_el_precio"] is (sugerido is None)


@pytest.mark.parametrize("incoterm", ["CIF", "cif "])
def test_una_operacion_cif_lleva_su_seguro_en_el_txt(client, incoterm):
    _registrar_con_cuit(client, f"seguro1_cif_{len(incoterm)}")
    r = client.post("/generate_maria", json=_pedido_con([LONA], incoterm=incoterm, seguro=14.88))
    assert r.status_code == 200, r.text
    assert _valor(r.json()["content"], "MDDTASS") == ["14.88"]
    assert _valor(r.json()["content"], "CDDTINCOTE") == ["CIF"]


def test_un_seguro_calculado_con_cif_no_genera(client):
    _registrar_con_cuit(client, "seguro1_calculado_cif")
    pedido = _pedido_con([LONA], incoterm="CIF", seguro=SUGERIDO, seguro_calculado=True)
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 400, r.text
    assert r.json()["detail"] == EN_EL_PRECIO
    assert EN_EL_PRECIO in client.post("/generate_maria/avisos", json=pedido).json()["avisos"]


def test_con_cif_y_las_cuentas_en_error_dice_lo_del_incoterm(client):
    # No se ofrece dejarlo: con CIF el 1 % no va, haya cuentas o no.
    _registrar_con_cuit(client, "seguro1_cif_error")
    pedido = _pedido_con([LONA], incoterm="CIF", seguro=SUGERIDO, seguro_calculado=True,
                         ajustes_deducir=5000)
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 400 and r.json()["detail"] == EN_EL_PRECIO, r.text
    valor = client.post("/generate_maria/avisos", json=pedido).json()["valor"]
    assert valor["seguro_en_el_precio"] is True and valor["error"].startswith("Los ajustes a deducir")


def test_con_las_cuentas_en_error_y_cfr_el_error_queda_como_antes(client):
    _registrar_con_cuit(client, "seguro1_cfr_error")
    pedido = _pedido_con([LONA], incoterm="CFR", ajustes_deducir=5000)
    valor = client.post("/generate_maria/avisos", json=pedido).json()["valor"]
    assert list(valor) == ["error"]


@pytest.mark.parametrize("incoterm,codigo,asegurado", [
    # El calculado con CFR, ya con CIF: no se genera.
    pytest.param("CIF", 400, None, id="cfr_a_cif"),
    # El mismo con CFR otra vez: genera como antes.
    pytest.param("CFR", 200, ["93.13"], id="cif_a_cfr"),
])
def test_el_cambio_de_incoterm_con_el_seguro_calculado(client, incoterm, codigo, asegurado):
    _registrar_con_cuit(client, f"seguro1_cambio_{incoterm}")
    r = client.post("/generate_maria", json=_pedido_con([LONA], incoterm=incoterm, seguro=SUGERIDO,
                                                        seguro_calculado=True))
    assert r.status_code == codigo, r.text
    if asegurado:
        assert _valor(r.json()["content"], "MDDTASS") == asegurado


def test_el_seguro_escrito_queda_con_cif(client):
    # El mismo importe que el 1 %, pero escrito: es de la persona.
    _registrar_con_cuit(client, "seguro1_escrito_cif")
    r = client.post("/generate_maria", json=_pedido_con([LONA], incoterm="CIF", seguro=SUGERIDO))
    assert r.status_code == 200, r.text
    assert _valor(r.json()["content"], "MDDTASS") == ["93.13"]


# ------------------------------------------------------------- la pantalla


def test_con_cif_no_hay_boton_ni_dejarlo():
    r = _pantalla({"incoterm": "CIF"}, "", VALOR_CIF)
    assert r["els"]["valorCalcularSeguro"]["hidden"] is True
    assert r["els"]["valorDejarSeguro"]["hidden"] is True
    assert r["els"]["valorSeguroNota"]["textContent"] == (
        "Con CIF el seguro ya está en el precio: el sistema no lo calcula. "
        "Si la factura lo trae, cargalo en la revisión.")


def test_la_pantalla_sigue_al_servidor_y_no_al_incoterm():
    # CIF en la operación, pero el servidor ofrece el 1 %: hay botón.
    r = _pantalla({"incoterm": "CIF"}, "", VALOR)
    assert r["els"]["valorCalcularSeguro"]["hidden"] is False


def test_con_cif_el_boton_no_pone_nada():
    r = _pantalla({"incoterm": "CIF"}, "calcularSeguro();", VALOR_CIF)
    assert "seguro" not in r["op"] and "seguro_calculado" not in r["op"]
    assert r["refrescos"] == 0


def test_con_cif_y_un_seguro_sin_leer_la_nota_lo_pide():
    r = _pantalla({"incoterm": "CIF", "campos_sin_leer": ["seguro"]}, "", VALOR_CIF)
    assert r["els"]["valorSeguroNota"]["textContent"] == (
        "Con CIF el seguro ya está en el precio: el sistema no lo calcula. "
        "No pudimos leerlo de la factura: completalo en la revisión.")


@pytest.mark.parametrize("valor", [
    pytest.param(VALOR_CIF, id="con_cuentas"),
    pytest.param({"error": "x", "seguro_en_el_precio": True}, id="cuentas_en_error"),
])
def test_el_calculado_se_borra_al_pasar_a_cif_y_queda_para_completar(valor):
    op = {"incoterm": "CIF", "seguro": SUGERIDO, "seguro_calculado": True,
          "campos_sin_leer": ["seguro", "flete"], "campos_completados": ["seguro", "flete"]}
    r = _pantalla(op, "", {**valor, "seguro": SUGERIDO} if "error" not in valor else valor)
    assert r["op"]["seguro"] == "" and "seguro_calculado" not in r["op"]
    # El mismo mecanismo que un campo sin leer (MARIA-1c).
    assert r["op"]["campos_sin_leer"] == ["seguro", "flete"]
    assert r["op"]["campos_completados"] == ["flete"]
    # Las cuentas se vuelven a pedir sin la marca, y el semáforo se entera.
    assert r["refrescos"] == 1 and r["semaforos"] == 1
    assert r["els"]["valorDejarSeguro"]["hidden"] is True
    assert r["els"]["valorCalcularSeguro"]["hidden"] is True


def test_el_calculado_que_se_borra_sin_lista_de_sin_leer_la_arma():
    op = {"incoterm": "CIF", "seguro": SUGERIDO, "seguro_calculado": True}
    r = _pantalla(op, "", {**VALOR_CIF, "seguro": SUGERIDO})
    assert r["op"]["campos_sin_leer"] == ["seguro"]
    assert r["op"]["seguro"] == ""


def test_el_seguro_escrito_no_se_toca_al_pasar_a_cif():
    op = {"incoterm": "CIF", "seguro": SUGERIDO}
    r = _pantalla(op, "", {**VALOR_CIF, "seguro": SUGERIDO})
    assert r["op"] == op and r["refrescos"] == 0
    assert r["els"]["valorSeguroNota"]["textContent"] == (
        "Con CIF el seguro ya está en el precio: el sistema no lo calcula.")
    assert r["els"]["valorCalcularSeguro"]["hidden"] is True


def test_con_cuentas_de_otro_pedido_no_se_borra():
    # Las cuentas llegaron para un pedido que ya no es el de ahora.
    op = {"incoterm": "CIF", "seguro": SUGERIDO, "seguro_calculado": True}
    r = _pantalla(op, "pintarValor({...VALOR, seguro_sugerido: null, seguro_en_el_precio: true, seguro: 93.13}, 'otro pedido');", None)
    assert r["op"] == op and r["refrescos"] == 0


def test_de_cif_a_cfr_vuelve_el_boton_y_no_pone_nada_solo():
    r = _pantalla({"incoterm": "CFR"}, "", VALOR)
    assert r["els"]["valorCalcularSeguro"]["hidden"] is False
    assert "seguro" not in r["op"]


@pytest.mark.parametrize("incoterm", ["CIF", "CFR"])
def test_sin_respuesta_de_los_avisos_no_se_ofrece_dejarlo(incoterm):
    # Los avisos dieron 400 o no llegaron: la pantalla no sabe si el
    # incoterm lleva el seguro en el precio. «Dejar» sacaría la marca y el
    # 1 % saldría en un TXT CIF; cuando los avisos contesten, se decide.
    op = {"incoterm": incoterm, "seguro": SUGERIDO, "seguro_calculado": True}
    r = _pantalla(op, "", {"error": "No se pudieron hacer las cuentas: mirá los avisos."})
    assert r["els"]["valorDejarSeguro"]["hidden"] is True
    assert r["op"] == op
