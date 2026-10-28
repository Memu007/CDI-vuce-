"""SUFIJOS-2 (D7 de MARIA-7, respuesta del despachante del 28/10).

- En un sufijo de código libre un número puede llevar coma: `AF(2.5)` sale
  `AF(2,5)` y no `AF(2 5)`, que es otro número.
- Un sufijo que pide número (los `Z`: peso, capacidad, cantidad…) no lleva
  decimales: no se redondea en silencio, se dice dónde y no se genera.
- Ninguno vacío: `AA()` no se genera.

Sintéticos con la forma de la factura del 24/10; los datos reales no entran
al repositorio.
"""
import pytest

from proyecto_maria.core import maria_generator as mg
from proyecto_maria.core import sufijos_arca
from tests.test_maria7_rechazos_24_10 import LONA, _gen, _valor

# ------------------------------------------- 1. La coma en un sufijo libre

CON_COMA = [
    ("AF(2.5)-CA00-", "AF(2,5)-CA00-"),            # el punto decimal pasa a coma
    ("AA(LONA)-AJ(ROLLO 1.5 M)-", "AA(LONA)-AJ(ROLLO 1,5 M)-"),
    ("AJ(0.75)-", "AJ(0,75)-"),
]


@pytest.mark.parametrize("entrada,limpio", CON_COMA)
def test_un_numero_con_decimales_en_un_sufijo_libre_sale_con_coma(entrada, limpio):
    assert mg.limpiar_sufijo(entrada) == (limpio, True)


@pytest.mark.parametrize("bien", ["AF(2,5)-CA00-", "AJ(ROLLO 1,5 M)-"])
def test_un_sufijo_libre_que_ya_trae_la_coma_sale_igual(bien):
    assert mg.limpiar_sufijo(bien) == (bien, False)


@pytest.mark.parametrize("entrada,limpio", CON_COMA)
def test_la_coma_llega_al_txt_en_la_operacion_el_subitem_y_el_renglon(entrada, limpio):
    assert _valor(_gen(sbt_sufijo_valor=entrada), "CSBTSVL") == [limpio]
    item = dict(LONA, subitems=[{"cantidad": 500, "valor_unitario": 1.85, "sufijo": entrada},
                                {"cantidad": 250, "valor_unitario": 1.85, "sufijo": "AA(OK)-CA00-"}])
    assert _valor(_gen([item]), "CSBTSVL") == [limpio, "AA(OK)-CA00-"]
    renglones = [dict(LONA, cantidad=500, peso_kg=300, sufijo=entrada),
                 dict(LONA, cantidad=250, peso_kg=165.125, sufijo="AA(OK)-CA00-")]
    assert _valor(_gen(renglones), "CSBTSVL") == [limpio, "AA(OK)-CA00-"]


def test_la_coma_entre_dos_sufijos_sigue_separandolos():
    # La coma dentro del paréntesis es del número; fuera, separa sufijos.
    assert mg.limpiar_sufijo("AF(2,5),AB(AZUL)-") == ("AF(2,5)-AB(AZUL)-", True)


def test_la_coma_que_no_es_de_un_numero_sigue_siendo_espacio():
    assert mg.limpiar_sufijo("AA(ROJO, AZUL)-")[0] == "AA(ROJO  AZUL)-"


def test_un_codigo_con_varios_puntos_no_se_toma_como_numero():
    # «1.2.3» no es un número con decimales: sale como antes de SUFIJOS-2.
    assert mg.limpiar_sufijo("AI(V1.2.3)-")[0] == "AI(V1 2 3)-"


def test_el_aviso_dice_que_el_numero_sale_con_coma():
    avisos = mg.supuestos_declarados([dict(LONA, sufijo="AF(2.5)-")], sbt_sufijo_valor="")
    assert any("ítem 1" in a and "AF(2,5)-" in a for a in avisos), avisos


def test_la_propuesta_del_arancel_tambien_lleva_la_coma():
    assert sufijos_arca.valor_de_sufijo("Rollo 1.5 m") == "Rollo 1,5 m"


# -------------------------------------- 2. Un sufijo que pide número, entero

CON_DECIMALES = ["ZA(2.5)-", "ZA(2,5)-", "AA(X)-ZB(16.384)-CA00-", "ZC(0.5)"]


@pytest.mark.parametrize("malo", CON_DECIMALES)
def test_un_sufijo_que_pide_numero_no_acepta_decimales(malo):
    with pytest.raises(ValueError, match=r"Sufijo de valor del ítem 3: «Z[ABC]\(.*pide un número sin decimales.*no se genera"):
        mg.limpiar_sufijo(malo, " del ítem 3")


@pytest.mark.parametrize("malo", CON_DECIMALES)
def test_los_decimales_no_generan_y_dicen_donde(malo):
    with pytest.raises(ValueError, match=r"de la operación.*pide un número sin decimales"):
        _gen(sbt_sufijo_valor=malo)
    with pytest.raises(ValueError, match=r"del ítem 1.*pide un número sin decimales"):
        _gen([dict(LONA, sufijo=malo)])
    item = dict(LONA, subitems=[{"cantidad": 500, "valor_unitario": 1.85, "sufijo": "AA(OK)-"},
                                {"cantidad": 250, "valor_unitario": 1.85, "sufijo": malo}])
    with pytest.raises(ValueError, match=r"ítem 1, sub-ítem 2.*pide un número sin decimales"):
        _gen([item])
    renglones = [dict(LONA, cantidad=500, peso_kg=300, sufijo="AA(OK)-"),
                 dict(LONA, cantidad=250, peso_kg=165.125, sufijo=malo)]
    with pytest.raises(ValueError, match=r"renglón 2.*pide un número sin decimales"):
        _gen(renglones)


def test_un_sufijo_que_pide_numero_entero_sale_igual():
    # La forma del archivo real de 2026 (sintética): números enteros con ceros.
    bien = "AA(DEMO)-AB(MODELO A 001)-ZA(016384)-ZB(004400)-ZC(000256)-ZD(000001)-CA00-NC01-"
    assert mg.limpiar_sufijo(bien) == (bien, False)
    assert _valor(_gen(sbt_sufijo_valor=bien), "CSBTSVL") == [bien]


# ------------------------------------------------------- 3. Ninguno vacío

VACIOS = ["AA()-CA00-", "AA(   )-", "AA(DEMO)-AB()-", "AA(--)-"]


@pytest.mark.parametrize("vacio", VACIOS)
def test_un_sufijo_vacio_no_se_genera(vacio):
    with pytest.raises(ValueError, match=r"Sufijo de valor del ítem 2: «A[AB]\(.*está vacío.*no se genera"):
        mg.limpiar_sufijo(vacio, " del ítem 2")


@pytest.mark.parametrize("vacio", VACIOS)
def test_un_sufijo_vacio_no_genera_y_dice_donde(vacio):
    with pytest.raises(ValueError, match=r"de la operación.*está vacío"):
        _gen(sbt_sufijo_valor=vacio)
    with pytest.raises(ValueError, match=r"del ítem 1.*está vacío"):
        _gen([dict(LONA, sufijo=vacio)])
    renglones = [dict(LONA, cantidad=500, peso_kg=300, sufijo="AA(OK)-"),
                 dict(LONA, cantidad=250, peso_kg=165.125, sufijo=vacio)]
    with pytest.raises(ValueError, match=r"renglón 2.*está vacío"):
        _gen(renglones)


# ----------------------------------------------------- 4. Por el endpoint

@pytest.mark.parametrize("usuario,malo,texto", [("sufijos2_decimal", "ZA(2.5)-CA00-", "pide un número sin decimales"),
                                                ("sufijos2_vacio", "AA()-CA00-", "está vacío")])
def test_el_error_llega_como_400(client, usuario, malo, texto):
    from tests.test_maria7_rechazos_24_10 import _pedido, _registrar_con_cuit
    _registrar_con_cuit(client, usuario)
    r = client.post("/generate_maria", json=dict(_pedido(), sbt_sufijo_valor=malo))
    assert r.status_code == 400, r.text
    assert texto in r.text


def test_por_el_endpoint_la_coma_llega_al_txt(client):
    from tests.test_maria7_rechazos_24_10 import _pedido, _registrar_con_cuit
    _registrar_con_cuit(client, "sufijos2_coma")
    r = client.post("/generate_maria", json=dict(_pedido(), sbt_sufijo_valor="AF(2.5)-CA00-"))
    assert r.status_code == 200, r.text
    assert "CSBTSVL=AF(2,5)-CA00-" in r.text
