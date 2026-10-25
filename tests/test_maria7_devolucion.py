"""Devolución de MARIA-7 (PARA-DEV-2.md, veredicto del 2026-10-24).

Un bloque por punto. Sintéticos con la forma de la factura del 24/10; los
datos reales no entran al repositorio.
"""
import re

import pytest

from proyecto_maria.core import maria_generator as mg
from tests.test_maria7_rechazos_24_10 import LONA, SUFIJO, _gen, _valor

# ------------------------------------------------ 1. Sufijos que se funden

# Cada sufijo conserva su código y su valor; entre uno y otro, «-».
SE_SEPARAN = [
    ("AA(ROJO) AB(AZUL)-CA00-", "AA(ROJO)-AB(AZUL)-CA00-"),      # espacio entre sufijos
    ("AA(ROJO)AB(AZUL)-CA00-", "AA(ROJO)-AB(AZUL)-CA00-"),       # nada entre sufijos
    ("AA(ROJO),AB(AZUL)-CA00-", "AA(ROJO)-AB(AZUL)-CA00-"),      # coma
    ("AA(ROJO)--AB(AZUL)-CA00-", "AA(ROJO)-AB(AZUL)-CA00-"),     # dos guiones
    ("AA(ROJO)CA00NA00-", "AA(ROJO)-CA00-NA00-"),                # códigos sin valor pegados
    ("AA(ROJO) AB(AZUL)", "AA(ROJO)-AB(AZUL)"),                  # sin guion final, como vino
]

# No se pueden delimitar: no se genera.
NO_SE_DELIMITAN = [
    "AA(SIN CIERRE-CA00-",          # paréntesis sin cerrar
    "AI(150CM(X)50M)-",             # un «(» dentro del valor
    "AA(ROJO))-CA00-",              # un «)» de más
    "AA(ROJO)-AB-CA00-",            # un código sin valor
    "AA(ROJO)-CA0-",                # un código con un solo dígito
    "(ROJO)-CA00-",                 # un valor sin código
]


@pytest.mark.parametrize("entrada,limpio", SE_SEPARAN)
def test_limpiar_sufijo_separa_cada_sufijo(entrada, limpio):
    assert mg.limpiar_sufijo(entrada) == (limpio, True)


@pytest.mark.parametrize("bien", [SUFIJO.replace("-GREY.008", " GREY 008"), "AA(DEMO)-AB(DEMO)-CA00-",
                                  "AA(1)-CA00", "CA00-NA00-NB00-", "AA(Demo)-CA00-"])
def test_un_sufijo_bien_escrito_sale_igual(bien):
    assert mg.limpiar_sufijo(bien) == (bien, False)


@pytest.mark.parametrize("malo", NO_SE_DELIMITAN)
def test_limpiar_sufijo_rechaza_lo_que_no_se_delimita(malo):
    with pytest.raises(ValueError, match="no se puede separar"):
        mg.limpiar_sufijo(malo)


@pytest.mark.parametrize("entrada,limpio", SE_SEPARAN)
def test_en_el_sbt_de_la_operacion_cada_sufijo_sale_con_su_valor(entrada, limpio):
    assert _valor(_gen(sbt_sufijo_valor=entrada), "CSBTSVL") == [limpio]


@pytest.mark.parametrize("entrada,limpio", SE_SEPARAN)
def test_en_el_subitem_cada_sufijo_sale_con_su_valor(entrada, limpio):
    item = dict(LONA, subitems=[{"cantidad": 500, "valor_unitario": 1.85, "sufijo": entrada},
                                {"cantidad": 250, "valor_unitario": 1.85, "sufijo": "AA(OK)-CA00-"}])
    assert _valor(_gen([item]), "CSBTSVL") == [limpio, "AA(OK)-CA00-"]


@pytest.mark.parametrize("entrada,limpio", SE_SEPARAN)
def test_en_el_renglon_cada_sufijo_sale_con_su_valor(entrada, limpio):
    # Dos renglones de la misma posición van en un ítem con dos sub-ítems (MARIA-8).
    renglones = [dict(LONA, cantidad=500, peso_kg=300, sufijo=entrada),
                 dict(LONA, cantidad=250, peso_kg=165.125, sufijo="AA(OK)-CA00-")]
    assert _valor(_gen(renglones), "CSBTSVL") == [limpio, "AA(OK)-CA00-"]


@pytest.mark.parametrize("malo", NO_SE_DELIMITAN)
def test_un_sufijo_que_no_se_delimita_no_genera_y_dice_donde(malo):
    with pytest.raises(ValueError, match=r"Sufijo de valor de la operación.*no se puede separar"):
        _gen(sbt_sufijo_valor=malo)
    item = dict(LONA, subitems=[{"cantidad": 500, "valor_unitario": 1.85, "sufijo": "AA(OK)-"},
                                {"cantidad": 250, "valor_unitario": 1.85, "sufijo": malo}])
    with pytest.raises(ValueError, match=r"ítem 1, sub-ítem 2.*no se puede separar"):
        _gen([item])
    renglones = [dict(LONA, cantidad=500, peso_kg=300, sufijo="AA(OK)-"),
                 dict(LONA, cantidad=250, peso_kg=165.125, sufijo=malo)]
    with pytest.raises(ValueError, match=r"renglón 2.*no se puede separar"):
        _gen(renglones)


def test_el_error_del_sufijo_llega_como_400(client):
    from tests.test_maria7_rechazos_24_10 import _pedido, _registrar_con_cuit
    _registrar_con_cuit(client, "maria7_dev_sufijo")
    pedido = dict(_pedido(), sbt_sufijo_valor="AA(SIN CIERRE-CA00-")
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 400, r.text
    assert "no se puede separar" in r.text


def test_el_aviso_dice_que_se_separo_y_no_rompe_con_un_sufijo_malo():
    avisos = mg.supuestos_declarados([dict(LONA)], sbt_sufijo_valor="AA(ROJO) AB(AZUL)-CA00-")
    assert any("Sufijo de valor:" in a and "AA(ROJO)-AB(AZUL)-CA00-" in a for a in avisos)
    # El aviso no reemplaza al error: con un sufijo malo no sale aviso del
    # sufijo y los demás salen igual que con uno bien escrito.
    assert (mg.supuestos_declarados([dict(LONA)], sbt_sufijo_valor="AA(SIN CIERRE-")
            == mg.supuestos_declarados([dict(LONA)], sbt_sufijo_valor="AA(DEMO)-CA00-"))


def test_un_sufijo_que_separado_pasa_de_120_caracteres_no_genera():
    # 120 caracteres pasan el tope del endpoint; con los guiones, 143.
    with pytest.raises(ValueError, match=r"de la operación.*143 caracteres.*120"):
        _gen(sbt_sufijo_valor="AA(X)" * 24)
    assert len(_valor(_gen(sbt_sufijo_valor="AA(X)" * 20), "CSBTSVL")[0]) == 119


# ------------------------------------- 2. D2 (b): el kilo neto al centésimo


def test_con_la_estadistica_en_kilos_el_kilo_neto_sale_al_centesimo():
    # 465,125: milésimo 5, el caso de medio centésimo.
    txt = _gen([dict(LONA, unidad_estadistica="01")])
    assert _valor(txt, "QARTKGRNET") == ["465.130"]
    assert _valor(txt, "QARTUNTEST") == ["465.13"]


def test_con_renglones_en_kilos_el_kilo_neto_es_la_cantidad_estadistica():
    renglones = [dict(LONA, cantidad=500, peso_kg=300.005, unidad_estadistica="01", sufijo="AA(A)-"),
                 dict(LONA, cantidad=250, peso_kg=165.124, unidad_estadistica="01", sufijo="AA(B)-")]
    txt = _gen(renglones)
    # 465,129 de kilo neto: la cantidad estadística, al centésimo, y el kilo neto igual.
    assert _valor(txt, "QARTUNTEST") == ["465.13"]
    assert _valor(txt, "QARTKGRNET") == ["465.130"]


@pytest.mark.parametrize("peso", [0.001, 0.004])
def test_con_la_estadistica_en_kilos_un_kilo_neto_que_da_cero_al_centesimo_no_genera(peso):
    with pytest.raises(ValueError, match=r"Item 1: .*al centésimo da 0\.00"):
        _gen([dict(LONA, peso_kg=peso, unidad_estadistica="01")])


def test_con_la_estadistica_en_kilos_medio_centesimo_sale():
    txt = _gen([dict(LONA, peso_kg=0.005, unidad_estadistica="01")])
    assert _valor(txt, "QARTKGRNET") == ["0.010"]


def test_sin_kilos_en_la_estadistica_el_kilo_neto_sigue_con_sus_milesimos():
    txt = _gen()
    assert _valor(txt, "QARTKGRNET") == ["465.125"]


def test_la_salida_que_sugiere_el_mensaje_de_kilos_con_subitems_cierra():
    """MARIA-8: el mensaje sugiere declarar en kilos con la cantidad igual al
    kilo neto al centésimo. Esa salida tiene que dar un TXT que el MARIA
    acepte: kilo neto igual a la cantidad estadística."""
    item = dict(LONA, peso_kg=10.005, unidad="kg", cantidad=5, valor_unitario=2,
                subitems=[{"cantidad": 2, "valor_unitario": 2, "sufijo": "AA(X)-"},
                          {"cantidad": 3, "valor_unitario": 2, "sufijo": "AA(Y)-"}])
    with pytest.raises(ValueError, match=r"al centésimo \(10\.01\)") as error:
        _gen([item])
    assert "10.01" in str(error.value)
    sugerido = dict(item, cantidad=10.01, valor_unitario=1,
                    subitems=[{"cantidad": 5, "valor_unitario": 1, "sufijo": "AA(X)-"},
                              {"cantidad": 5.01, "valor_unitario": 1, "sufijo": "AA(Y)-"}])
    txt = _gen([sugerido])
    assert _valor(txt, "QARTKGRNET") == ["10.010"]
    assert _valor(txt, "QARTUNTEST") == ["10.01"]


# ------------------------------- 3. Palabras de cuenta, sólo palabras enteras

PALABRAS = ["IBAN", "SWIFT", "BIC", "ACCOUNT", "ACCT", "CUENTA", "CTA", "BANK", "BANCO"]


@pytest.mark.parametrize("palabra", PALABRAS)
def test_una_palabra_que_contiene_la_de_cuenta_no_es_cuenta(palabra):
    tributaria = f"VAT AR{palabra}-1234567"
    assert not mg.parece_cuenta_bancaria(tributaria)
    assert _valor(_gen(vendedor_id=tributaria), "MCPL").count(f"{tributaria:<40}") == 1


@pytest.mark.parametrize("tributaria", ["ARABIC TRADING 123", "VAT ARABIC-1234567", "ZA-ACTA 12345"])
def test_los_casos_de_la_reproduccion_salen(tributaria):
    assert not mg.parece_cuenta_bancaria(tributaria)
    assert "IDTRIB-PROVEEDOR" in _gen(vendedor_id=tributaria)


@pytest.mark.parametrize("cuenta", ["ICBC_ACCOUNT 6222", "NRO_CUENTA 6222", "1_BANK 6222", "N1IBAN 6222"])
def test_la_palabra_pegada_a_un_numero_o_guion_bajo_sigue_siendo_cuenta(cuenta):
    # El borde es «no hay una letra adelante»: «_» y los dígitos no tapan la palabra.
    assert mg.parece_cuenta_bancaria(cuenta)
    assert "IDTRIB-PROVEEDOR" not in _gen(vendedor_id=cuenta)


@pytest.mark.parametrize("palabra", PALABRAS + ["A/C"])
def test_la_palabra_sola_sigue_siendo_cuenta(palabra):
    assert mg.parece_cuenta_bancaria(f"{palabra} 0012345678")
    assert mg.parece_cuenta_bancaria(f"{palabra.lower()}: 0012345678")


# ----------------------- 4. El grupo compara la unidad estadística por código


@pytest.mark.parametrize("unas", [("1", "01"), ("kg", "01"), ("KGS", "1"), ("", "07"), ("unidad", "")])
def test_un_grupo_con_la_misma_unidad_estadistica_escrita_distinto_genera(unas):
    items = [dict(LONA, unidad="u", cantidad=1, peso_kg=1, grupo_id=1, unidad_estadistica=e) for e in unas]
    txt = _gen(items)
    assert len(_valor(txt, "CARTUNTEST")) == 1


def test_un_grupo_con_unidades_estadisticas_distintas_sigue_dando_error():
    items = [dict(LONA, unidad="u", cantidad=1, peso_kg=1, grupo_id=1, unidad_estadistica=e)
             for e in ("01", "07")]
    with pytest.raises(ValueError, match="misma unidad estadística"):
        _gen(items)


@pytest.mark.parametrize("unas", [("kg", "KGS"), ("1", "01"), ("u", "")])
def test_un_grupo_con_la_misma_unidad_declarada_escrita_distinto_genera(unas):
    # La misma familia que la estadística: se compara el código que sale.
    items = [dict(LONA, unidad=u, cantidad=1, peso_kg=1, grupo_id=1) for u in unas]
    assert len(_valor(_gen(items), "CARTUNTDCL")) == 1


def test_un_grupo_con_unidades_declaradas_distintas_sigue_dando_error():
    items = [dict(LONA, unidad=u, cantidad=1, peso_kg=1, grupo_id=1) for u in ("kg", "u")]
    with pytest.raises(ValueError, match="misma unidad de medida"):
        _gen(items)


# --------------------- 5. D6: la unidad que no se reconoce se avisa (sale 07)


@pytest.mark.parametrize("leida", ["bolsa", "rollo", "CAJA X 12"])
def test_una_unidad_que_no_se_reconoce_sale_07_y_se_avisa(leida):
    item = dict(LONA, unidad=leida)
    assert _valor(_gen([item]), "CARTUNTDCL") == ["07"]
    avisos = mg.supuestos_declarados([dict(LONA), item], sbt_sufijo_valor=SUFIJO)
    unidad = [a for a in avisos if a.startswith("Unidad de medida")]
    assert len(unidad) == 1 and f"«{leida}»" in unidad[0] and "ítem(s) 2" in unidad[0]


@pytest.mark.parametrize("conocida", ["m²", "kg", "Sq.M.", "01", "PCS"])
def test_una_unidad_que_se_reconoce_no_se_avisa(conocida):
    avisos = mg.supuestos_declarados([dict(LONA, unidad=conocida)], sbt_sufijo_valor=SUFIJO)
    assert not any(a.startswith("Unidad de medida") for a in avisos)
