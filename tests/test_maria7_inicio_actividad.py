"""MARIA-7, punto 9: la fecha de inicio de actividad del cliente en el TXT.

El alta del cliente y la revisión la guardan `AAAA-MM-DD` (campo de fecha del
navegador) y el generador la copiaba tal cual al MCPL de `FECHA INIC.ACTIV`.
Los dos golden la tienen `DD/MM/AAAA`. Datos inventados.
"""
import pytest

from tests.test_maria7_rechazos_24_10 import _gen, _pedido, _registrar_con_cuit


def _inicio_actividad(txt: str) -> str:
    lineas = txt.split("\r\n")
    i = lineas.index("CCPL=FECHA INIC.ACTIV")
    assert lineas[i + 1].startswith("MCPL=")
    return lineas[i + 1][len("MCPL="):]


@pytest.mark.parametrize("guardada", ["2015-03-01", "01/03/2015", " 2015-03-01 "])
def test_sale_dd_mm_aaaa_con_el_ancho_de_siempre(guardada):
    assert _inicio_actividad(_gen(comprador_fecha_inic_activ=guardada)) == f"{'01/03/2015':<40}"


@pytest.mark.parametrize("guardada", ["no es fecha", "2015-02-30", "31/02/2015", "03/01/15", "2015/03/01 algo"])
def test_lo_que_no_es_fecha_no_se_adivina_y_dice_donde_corregirla(guardada):
    with pytest.raises(ValueError) as e:
        _gen(comprador_fecha_inic_activ=guardada)
    mensaje = str(e.value)
    assert f"«{guardada.strip()}»" in mensaje
    assert "«Clientes»" in mensaje and "«Inicio de actividad»" in mensaje


def test_sin_fecha_el_bloque_no_sale_como_antes():
    assert "CCPL=FECHA INIC.ACTIV" not in _gen(comprador_fecha_inic_activ="")


def test_el_pedido_de_la_pantalla_sale_convertido(client):
    _registrar_con_cuit(client, "maria7_inicio_actividad")
    r = client.post("/generate_maria", json=dict(_pedido(), comprador_fecha_inic_activ="2015-03-01"))
    assert r.status_code == 200, r.text
    assert _inicio_actividad(r.json()["content"]) == f"{'01/03/2015':<40}"
    r = client.post("/generate_maria", json=dict(_pedido(), comprador_fecha_inic_activ="marzo"))
    assert r.status_code == 400, r.text
    assert "Inicio de actividad" in r.text
