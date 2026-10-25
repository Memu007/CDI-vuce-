"""SEPARADORES-1b: un monto ilegible no viaja como 0, y «1234.567» se pregunta.

1. D19 (b): si la pantalla no puede leer el flete, el seguro, los gastos o un
   ajuste, el pedido lleva el texto tal cual y el servidor lo rechaza con un
   mensaje (ni 0 silencioso, ni 422 crudo, ni 500). Un texto que Python lee a
   su manera («3.480» → 3,48; «1e3» → 1000) tampoco pasa.
2. Un separador seguido de tres cifras, con cuatro o más cifras adelante
   («4500.000», «98765,432»): no es un grupo de miles bien formado. En la
   factura, con la pista decimal en contra, queda sin leer (antes 4500000);
   en la pantalla se pregunta, como «1,500» (antes 4500,0).

Datos inventados; Gemini falso.
"""
import hashlib
import json
import re

import pytest

from proyecto_maria import pdf_extractor
from tests.test_maria1a_lectura_factura import COPIAS, _leer
from tests.test_maria7_rechazos_24_10 import _pedido, _registrar_con_cuit
from tests.test_separadores1 import _factura, _js
from tests.test_valor1 import _funciones

# Familia: separador y tres cifras, con lo de adelante que no es un grupo de
# miles (cuatro o más cifras). Ejemplos distintos de los de la tarea.
FAMILIA = ["4500.000", "98765,432", "2500.125", "12345,250"]

# Lo que no cambia, en la factura: (texto, pista, lectura de hoy).
GUARDAS_FACTURA = [
    ("3.480", None, 3480.0), ("3.480", ",", 3480.0),
    ("3.480,00", None, 3480.0), ("3.480,00", ".", 3480.0),
    ("1.234.567", None, 1234567.0), ("1.234.567", ".", 1234567.0),
    ("1,234.56", None, 1234.56), ("1,234.56", ",", 1234.56),
    ("3,48", None, 3.48), ("3,48", ".", 3.48),
    ("0,500", None, 0.5), ("0,500", ".", 0.5),
    ("01,500", ",", 1.5),
    ("1.234,567", None, 1234.567), ("1.234,567", ".", 1234.567),
    # La pista a favor: la factura escribe con punto decimal, «4500.000» es 4500.
    ("4500.000", ".", 4500.0), ("98765,432", ",", 98765.432), ("4 500.000", ".", 4500.0),
    ("1 234,56", ",", 1234.56), ("1 234,56", None, 1234.56),
]

# Lo que no cambia, en la pantalla.
GUARDAS_PANTALLA = [
    ("3.480", 3480), ("3.480,00", 3480), ("1.234.567", 1234567), ("1,234.56", 1234.56),
    ("3,48", 3.48), ("0,500", 0.5), ("01,500", 1.5), ("1.234,567", 1234.567),
]


# ---------------------------------------------------------------- la factura


@pytest.mark.parametrize("texto", FAMILIA)
def test_en_la_factura_con_la_pista_en_contra_queda_sin_leer(texto):
    """Antes «4500.000» con la coma decimal daba 4500000."""
    en_contra = "," if texto[-4] == "." else "."
    assert pdf_extractor._monto_factura(texto, en_contra) is None
    assert pdf_extractor._monto_factura(texto, None) is None


@pytest.mark.parametrize("texto, en_contra", [
    ("4 500.000", ","), ("4'500.000", ","), ("4\u202f500.000", ","), ("4\u00a0500.000", ","),
    ("12 345,250", "."),
])
def test_en_la_factura_con_grupos_de_espacio_tambien(texto, en_contra):
    """_numero_factura saca esos separadores: «4 500.000» con la coma decimal
    también daba 4500000."""
    assert pdf_extractor._monto_factura(texto, en_contra) is None


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("flete, unitario", [("4500.000", "2,45"), ("12345,250", "2.45")])
def test_en_la_factura_se_avisa_y_no_llega_multiplicado(monkeypatch, copia, flete, unitario):
    r = _leer(monkeypatch, copia, _factura(flete, valor_unitario=unitario))
    assert r["operacion"]["flete"] == 0.0
    assert "flete" in r["operacion"]["campos_sin_leer"]


@pytest.mark.parametrize("texto, decimal, esperado", GUARDAS_FACTURA)
def test_en_la_factura_lo_demas_sigue_como_hoy(texto, decimal, esperado):
    assert pdf_extractor._monto_factura(texto, decimal) == pytest.approx(esperado)


def test_los_precios_no_cambian():
    """_numero_factura (precios y cantidades) no se toca: tres decimales ahí
    son normales."""
    assert pdf_extractor._numero_factura("4500.000", ".") == 4500.0
    assert pdf_extractor._numero_factura("4500,000", ",") == 4500.0
    assert pdf_extractor._numero_factura("4500.000", ",") == 4500000.0


# ---------------------------------------------------------------- la pantalla


def _leer_js(escrito):
    return _js(f"console.log(JSON.stringify(CDI.montos.leer({json.dumps(escrito)})));")


@pytest.mark.parametrize("escrito, pregunta", [
    ("4500.000", "¿4.500.000 o 4.500,000?"), ("98765,432", "¿98.765.432 o 98.765,432?"),
    ("2500.125", "¿2.500.125 o 2.500,125?"), ("12345,250", "¿12.345.250 o 12.345,250?"),
    ("-2500.125", "¿2.500.125 o 2.500,125?"),
])
def test_en_la_pantalla_se_pregunta(escrito, pregunta):
    """Antes «2500.125» se leía 2500,125 sin preguntar."""
    r = _leer_js(escrito)
    assert r["valor"] is None and r["error"].startswith(pregunta), r


@pytest.mark.parametrize("escrito, valor", GUARDAS_PANTALLA)
def test_en_la_pantalla_lo_demas_sigue_como_hoy(escrito, valor):
    assert _leer_js(escrito) == {"valor": valor, "error": None}


def test_las_dos_respuestas_a_la_pregunta_se_leen_sin_dudas():
    r = _js("console.log(JSON.stringify(['2.500.125', '2.500,125'].map(t => CDI.montos.leer(t))));")
    assert r == [{"valor": 2500125, "error": None}, {"valor": 2500.125, "error": None}]


# ------------------------------------------------- D19: el pedido y el servidor

PEDIDO_JS = _funciones("finalize.js", ["montoDelPedido", "ajusteDelPedido"])


def _del_pedido(funcion, escrito):
    return _js(PEDIDO_JS + f"\nconsole.log(JSON.stringify({funcion}({json.dumps(escrito)})));")


@pytest.mark.parametrize("funcion", ["montoDelPedido", "ajusteDelPedido"])
@pytest.mark.parametrize("escrito", ["1,500", "2500.125", "abc", " 3,480 "])
def test_lo_que_la_pantalla_no_lee_viaja_tal_cual(funcion, escrito):
    """Antes el monto viajaba como 0 y el ajuste como nada."""
    assert _del_pedido(funcion, escrito) == escrito.strip()


@pytest.mark.parametrize("funcion, escrito, valor", [
    ("montoDelPedido", "3.480", 3480), ("montoDelPedido", "", 0), ("montoDelPedido", 3480, 3480),
    ("montoDelPedido", None, 0), ("ajusteDelPedido", "1.500", 1500), ("ajusteDelPedido", "", None),
])
def test_lo_que_se_lee_o_esta_vacio_viaja_como_hoy(funcion, escrito, valor):
    assert _del_pedido(funcion, escrito) == valor


# Textos que la pantalla no manda como número y Python leería a su manera
# (o no leería): ninguno llega al TXT.
def _usuario(request):
    """Un usuario por caso, válido (3-30 letras) aunque el caso lleve comas o «١٥٠»."""
    return "sep1b_" + hashlib.sha1(request.node.nodeid.encode()).hexdigest()[:16]


ILEGIBLES = ["1,500", "3.480", "2500.125", "1e3", "1_000", "abc", ".5", "+5", "١٥٠"]
# Los gastos se nombran distinto según quién los mira primero (los controles,
# «Gastos (gastos_anteriores_fob)»; las cuentas, «Gastos (gastos anteriores a
# FOB)»): de hoy, no de esta pieza.
CAMPOS = [("flete", "Flete: "), ("seguro", "Seguro: "), ("gastos_anteriores_fob", "Gastos (gastos")]


@pytest.mark.parametrize("campo, nombre", CAMPOS)
@pytest.mark.parametrize("escrito", ILEGIBLES)
def test_el_servidor_no_genera_con_un_monto_ilegible(client, request, campo, nombre, escrito):
    _registrar_con_cuit(client, _usuario(request))
    r = client.post("/generate_maria", json={**_pedido(), "incoterm": "EXW", campo: escrito})
    assert r.status_code == 400, r.text
    assert f"«{escrito}» no es un importe." in r.text and nombre in r.text, r.text
    assert "MDDTFLE" not in r.text


@pytest.mark.parametrize("campo, nombre", CAMPOS)
@pytest.mark.parametrize("escrito", ["1,500", "1e3"])
def test_los_avisos_dicen_cual_es_el_monto_ilegible(client, request, campo, nombre, escrito):
    _registrar_con_cuit(client, _usuario(request))
    r = client.post("/generate_maria/avisos", json={**_pedido(), "incoterm": "EXW", campo: escrito})
    assert r.status_code == 400, r.text
    detalle = r.json()["detail"]
    assert detalle.startswith(nombre) and detalle.endswith(f"«{escrito}» no es un importe."), detalle


def test_el_monto_que_arma_la_pantalla_lo_rechaza_el_servidor(client):
    """Punta a punta: el «1,500» que la pantalla no pudo leer, como lo arma
    buildMariaRequest, no sale como flete 0."""
    _registrar_con_cuit(client, "sep1b_punta")
    flete = _del_pedido("montoDelPedido", "1,500")
    r = client.post("/generate_maria", json={**_pedido(), "flete": flete})
    assert r.status_code == 400 and "Flete: «1,500» no es un importe." in r.text, r.text


def test_un_ajuste_ilegible_se_dice_en_las_cuentas_y_sin_seguro_calculado_no_frena_el_txt(client):
    """VALOR-1b sigue: el ajuste no va al TXT (D12). Antes «3.480» se tomaba
    como 3,48 sin aviso."""
    _registrar_con_cuit(client, "sep1b_ajuste")
    r = client.post("/generate_maria/avisos", json={**_pedido(), "ajustes_deducir": "3.480"})
    assert r.status_code == 200, r.text
    assert r.json()["valor"] == {"error": "Ajustes a deducir: «3.480» no es un importe."}
    sin = client.post("/generate_maria", json=_pedido())
    con = client.post("/generate_maria", json={**_pedido(), "ajustes_deducir": "3.480"})
    assert sin.status_code == con.status_code == 200, con.text
    assert con.content == sin.content


def test_con_el_seguro_calculado_un_ajuste_ilegible_frena_hasta_que_se_elija(client):
    """D20: el seguro que calculó el sistema no se puede comprobar con un
    ajuste ilegible (VALOR-1c): el TXT espera a que se corrija el ajuste o se
    deje el seguro. Antes la pantalla mandaba el ajuste como nada y no frenaba."""
    _registrar_con_cuit(client, "sep1b_calculado")
    sugerido = client.post("/generate_maria/avisos", json=_pedido()).json()["valor"]["seguro_sugerido"]
    calculado = {**_pedido(), "seguro": sugerido, "seguro_calculado": True}
    assert client.post("/generate_maria", json=calculado).status_code == 200
    r = client.post("/generate_maria", json={**calculado, "ajustes_deducir": "1,500"})
    assert r.status_code == 400, r.text
    assert "no se puede comprobar: Ajustes a deducir: «1,500» no es un importe." in r.text, r.text
    dejado = client.post("/generate_maria", json={**calculado, "seguro_calculado": False, "ajustes_deducir": "1,500"})
    assert dejado.status_code == 200, dejado.text


@pytest.mark.parametrize("escrito, txt", [("3221.66", "3221.66"), (" 150 ", "150.00"), ("7925", "7925.00"),
                                          (7925.5, "7925.50"), ("0.5", "0.50")])
def test_un_importe_escrito_sin_dudas_se_sigue_tomando(client, request, escrito, txt):
    """Otros clientes (la v1, una API) mandan texto con punto decimal."""
    _registrar_con_cuit(client, _usuario(request))
    r = client.post("/generate_maria", json={**_pedido(), "flete": escrito})
    assert r.status_code == 200, r.text
    assert re.findall(r"^MDDTFLE=(\S+)", r.json()["content"], re.M) == [txt]


def test_un_importe_vacio_cuenta_como_cero(client):
    _registrar_con_cuit(client, "sep1b_vacio")
    r = client.post("/generate_maria", json={**_pedido(), "flete": "  "})
    assert r.status_code == 200, r.text
    assert re.findall(r"^MDDTFLE=(\S+)", r.json()["content"], re.M) == ["0.00"]
