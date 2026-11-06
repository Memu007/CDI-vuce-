"""MARIA-9, punto 3: los bordes del sufijo y de la unidad que ninguna
prueba fijaba. Cada uno con el caso de un lado y del otro del borde, para
que un cambio de «>» por «>=» o de «{2}» por «+» dé rojo. Datos inventados
con la forma de la factura de lonas.
"""
import pytest

from proyecto_maria.core import maria_generator as mg
from tests.test_maria7_rechazos_24_10 import LONA, _gen, _pedido, _registrar_con_cuit, _valor

NO_SE_SEPARA = r"^Sufijo de valor de la operación: .* no se puede separar en códigos"


def _de_largo(n):
    """Un sufijo limpio (sale igual) de `n` caracteres."""
    return "AA(" + "X" * (n - 5) + ")-"


# ------------------------------------------------------- el tope de 120


def test_el_generador_deja_120_caracteres_y_no_121():
    assert _valor(_gen(sbt_sufijo_valor=_de_largo(120)), "CSBTSVL") == [_de_largo(120)]
    # 120 como vino, 121 con el guion que se agrega: el endpoint lo deja
    # pasar y el tope es el del generador.
    vino = "AA(X)AB(" + "Y" * 111 + ")"
    assert len(vino) == 120
    with pytest.raises(ValueError, match=r"de la operación: separado con guiones queda de 121 caracteres"):
        _gen(sbt_sufijo_valor=vino)
    assert len(_valor(_gen(sbt_sufijo_valor=vino[:-2] + ")"), "CSBTSVL")[0]) == 120


@pytest.mark.parametrize("largo,pasa", [(120, True), (121, False)])
def test_el_endpoint_deja_120_caracteres_y_no_121(client, largo, pasa):
    _registrar_con_cuit(client, f"maria9_tope_{largo}")
    r = client.post("/generate_maria", json=dict(_pedido(), sbt_sufijo_valor=_de_largo(largo)))
    if pasa:
        assert r.status_code == 200, r.text
        assert _valor(r.json()["content"], "CSBTSVL") == [_de_largo(120)]
    else:
        assert r.status_code == 400, r.text
        assert r.json()["detail"] == "El sufijo de valor SBT no puede superar los 120 caracteres."


# ------------------------------------- la forma de cada código del sufijo


def test_un_codigo_numerico_tiene_dos_cifras_y_no_tres():
    assert _valor(_gen(sbt_sufijo_valor="AA(X)-CA10-"), "CSBTSVL") == ["AA(X)-CA10-"]
    with pytest.raises(ValueError, match=NO_SE_SEPARA + r" \(cerca de «0-»\)"):
        _gen(sbt_sufijo_valor="AA(X)-CA100-")


def test_un_codigo_tiene_dos_letras_y_no_una():
    assert _valor(_gen(sbt_sufijo_valor="AA(X)-"), "CSBTSVL") == ["AA(X)-"]
    with pytest.raises(ValueError, match=NO_SE_SEPARA + r" \(cerca de «A\(X\)-»\)"):
        _gen(sbt_sufijo_valor="A(X)-")


def test_el_punto_y_coma_separa_un_codigo_del_otro():
    assert mg.limpiar_sufijo("AA(X);AB(Y)-") == ("AA(X)-AB(Y)-", True)
    assert _valor(_gen(sbt_sufijo_valor="AA(X);AB(Y)-"), "CSBTSVL") == ["AA(X)-AB(Y)-"]


# ------------------------------------------- las unidades con su código


@pytest.mark.parametrize("unidad", ["05", "99"])
def test_una_unidad_con_su_codigo_sale_igual_y_no_se_avisa(unidad):
    items = [dict(LONA, unidad=unidad)]
    assert _valor(_gen(items), "CARTUNTDCL") == [unidad]
    avisos = mg.supuestos_declarados(items)
    assert not any(a.startswith("Unidad de medida:") for a in avisos), avisos


def test_una_unidad_que_no_se_reconoce_se_avisa():
    # El otro lado del borde: sin esto, un aviso que nunca sale pasaría.
    avisos = mg.supuestos_declarados([dict(LONA, unidad="zz")])
    assert any(a.startswith("Unidad de medida: en el/los ítem(s) 1 («zz») la unidad no se reconoce")
               for a in avisos), avisos
