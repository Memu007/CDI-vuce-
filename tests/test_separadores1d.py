"""SEPARADORES-1d: lo que dejaron D24 y D25 de SEPARADORES-1c.

1. (D24) La regla de miles de 1c también en `_numero_factura`: cantidad,
   valor unitario y pesos. Un número que sólo se puede leer como miles con
   grupos mal formados queda sin leer, vacío, como «12x3», y la revisión lo
   marca como hoy (antes «0.500.000» daba 500000 en la cantidad). Lo bien
   formado se lee igual.
2. (D25) Aviso no bloqueante cuando el flete o el seguro tienen más de dos
   decimales: qué se escribió y qué lleva el TXT («2500,1250» → «El TXT
   lleva 2500,13»). No cambia lo que se lee ni lo que sale en el TXT.

Datos inventados; Gemini falso.
"""
import hashlib
import json
import re

import pytest

from proyecto_maria import main, pdf_extractor
from proyecto_maria.core.maria_generator import centavos
from tests.test_maria1a_lectura_factura import COPIAS, _leer
from tests.test_maria7_rechazos_24_10 import _pedido, _registrar_con_cuit
from tests.test_separadores1 import _factura, _js
from tests.test_valor1 import _correr, _funciones


# ------------------------------------------------- 1. cantidades, precios y pesos

# (texto, pista): sólo se leen como miles, con grupos mal formados. Ninguno es
# de los ejemplos de la tarea ni de 1c.
MAL_FORMADOS = [
    # cero adelante
    ("0.500.000", None), ("0.500.000", ","), ("012.500", ","), ("001,250", "."),
    ("04 500", None), ("0 750", None), ("03.250,5", None), ("USD 0750.000", ","),
    # cabeza de cuatro cifras o más, con dos grupos o con decimales
    ("9500,000,000", None), ("9500,000,000", "."), ("12345.678,90", None),
    ("12345.678,90", ","), ("2500.000.000 kg", None), ("1500.000", ","),
]


@pytest.mark.parametrize("texto, pista", MAL_FORMADOS)
def test_un_numero_de_la_factura_con_miles_mal_formados_queda_sin_leer(texto, pista):
    """Antes «0.500.000» daba 500000 y «9500,000,000» 9500000000."""
    assert pdf_extractor._numero_factura(texto, pista) is None


# Siguen como hoy.
GUARDAS = [
    ("0750.000", ".", 750.0), ("1.250", ",", 1250.0), ("0.125", None, 0.125),
    ("1.500,00", None, 1500.0), ("1 500,00", None, 1500.0), ("0,750", None, 0.75),
    ("12.000", ",", 12000.0), ("1,250.75", None, 1250.75), ("10", None, 10.0),
    ("2.45", None, 2.45), ("0.20", None, 0.2), ("1,500", ".", 1500.0), ("007", None, 7.0),
    ("1.234.567", None, 1234567.0), ("1 234", None, 1234.0), ("0,5", ",", 0.5),
    ("100.000,000", None, 100000.0), ("1.234,567", None, 1234.567), ("USD 3.480", ",", 3480.0),
    (1500, None, 1500.0), (0.5, None, 0.5),
]


@pytest.mark.parametrize("texto, pista, esperado", GUARDAS)
def test_lo_bien_formado_se_lee_como_hoy(texto, pista, esperado):
    assert pdf_extractor._numero_factura(texto, pista) == pytest.approx(esperado)


@pytest.mark.parametrize("texto", ["12x3", "1/2", "2.5e3", "abc"])
def test_lo_que_no_es_un_numero_sigue_sin_leerse(texto):
    assert pdf_extractor._numero_factura(texto, None) is None


@pytest.mark.parametrize("texto, pista", [("0750.000", ","), ("7500.000.000", None), ("02 750", None)])
def test_el_flete_sigue_sin_leerse_como_en_1c(texto, pista):
    """La regla se mudó a `_numero_factura`: el flete y el seguro, igual."""
    assert pdf_extractor._monto_factura(texto, pista) is None


ITEM_MAL = {"cantidad": "0.500.000", "valor_unitario": "0.750.000", "peso_kg": "2500.000.000 kg"}


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("campo, leido", [
    ("cantidad", "cantidad"), ("valor_unitario", "valor_unitario"), ("peso_kg", "peso_unitario"),
])
def test_en_la_factura_queda_vacio_y_no_multiplicado(monkeypatch, copia, campo, leido):
    """Antes la cantidad «0.500.000» llegaba como 500000 al FOB del TXT."""
    r = _leer(monkeypatch, copia, _factura("100", **{campo: ITEM_MAL[campo]}))
    assert r["items"][0][leido] == 0.0, r["items"]


@pytest.mark.parametrize("copia", COPIAS)
def test_lo_bien_formado_de_la_factura_llega_igual(monkeypatch, copia):
    r = _leer(monkeypatch, copia, _factura("100", cantidad="1.500", valor_unitario="2,45", peso_kg="0,20"))
    item = r["items"][0]
    assert (item["cantidad"], item["valor_unitario"], item["peso_unitario"]) == (1500.0, 2.45, 0.2)


ITEM_SEMAFORO = {"pieza": "84713012", "descripcion": "MAQUINA DEMO", "origen": "CN",
                 "cantidad": 1, "valor_unitario": 10, "peso_unitario": 1}


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("campo, leido, error", [
    ("cantidad", "cantidad", "La cantidad debe ser mayor a cero."),
    ("valor_unitario", "valor_unitario", "El valor unitario debe ser mayor a cero."),
    ("peso_kg", "peso_unitario", "El peso unitario debe ser mayor a cero."),
])
def test_la_revision_lo_marca_como_hoy(monkeypatch, client, copia, campo, leido, error):
    """Punta a punta: lo que dejó la lectura, en el semáforo."""
    r = _leer(monkeypatch, copia, _factura("100", **{campo: ITEM_MAL[campo]}))
    item = dict(ITEM_SEMAFORO, **{leido: r["items"][0][leido]})
    s = client.post("/api/validate/smart", json={"items": [item], "operacion": {"moneda": "DOL", "incoterm": "FOB"}})
    assert s.status_code == 200, s.text
    assert any(error in e for e in s.json()["errores"]), s.json()


def test_en_la_planilla_tampoco_se_multiplica():
    """La planilla lee con `_numero_factura`: una celda de texto con miles
    mal formados queda vacía, como «12x3», y no por mil."""
    import pandas as pd
    df = pd.DataFrame({"pieza": ["84713000", "85171300"], "descripcion": ["Laptop", "Telefono"],
                       "origen": ["CN", "CN"], "cantidad": ["0.500.000", "1.500"],
                       "valor_unitario": ["10", "012.500"], "peso_unitario": ["1", "2"]})
    items = main.extract_items_from_excel(df, "x.xlsx")
    assert [(i.cantidad, i.valor_unitario) for i in items] == [(0.0, 10.0), (1500.0, 0.0)]


# ------------------------------------------------- 2. más de dos decimales

def _aviso_js():
    return _funciones("finalize.js", ["alCentavoDelTxt", "avisosDeLosMontos"])


def _avisos_de(op):
    return _js(_aviso_js() + f"\nconsole.log(JSON.stringify(avisosDeLosMontos({json.dumps(op)})));")


@pytest.mark.parametrize("op, escrito, txt", [
    ({"flete": 2500.125}, "Flete: escribiste «2500,1250».", "El TXT lleva 2500,13."),
    ({"seguro": 12.34567}, "Seguro: escribiste «12,34567».", "El TXT lleva 12,35."),
    ({"flete": 2.675}, "Flete: escribiste «2,6750».", "El TXT lleva 2,68."),   # Math.round daría 2,67
    ({"seguro": 1.005}, "Seguro: escribiste «1,0050».", "El TXT lleva 1,01."),  # Math.round daría 1,00
    ({"flete": "1.234,567"}, "Flete: escribiste «1.234,567».", "El TXT lleva 1234,57."),
    ({"flete": 0.004}, "Flete: escribiste «0,0040».", "El TXT lleva 0,00."),
    # Una cuenta de una planilla (0,1 + 0,2) también tiene más: se dice qué lleva.
    ({"seguro": 0.1 + 0.2}, "Seguro: escribiste «0,30000000000000004».", "El TXT lleva 0,30."),
])
def test_con_mas_de_dos_decimales_se_avisa_que_lleva_el_txt(op, escrito, txt):
    avisos = _avisos_de(op)
    assert len(avisos) == 1, avisos
    assert avisos[0].startswith(escrito) and avisos[0].endswith(txt), avisos


def test_el_flete_y_el_seguro_avisan_cada_uno():
    avisos = _avisos_de({"flete": 10.555, "seguro": 3.1416})
    assert [a.split(":")[0] for a in avisos] == ["Flete", "Seguro"]


@pytest.mark.parametrize("op", [
    {"flete": 2500.12}, {"flete": 2500.1}, {"flete": 2500}, {"flete": 0}, {"flete": "3.480,50"},
    {"flete": "3,48"}, {"flete": ""}, {"flete": None}, {},
    # Lo que no se lee o es negativo ya lo frena la revisión: acá no se suma nada.
    {"flete": "1,500"}, {"flete": "abc"}, {"flete": -2.125},
    # Otros importes no son el flete ni el seguro.
    {"gastos_anteriores_fob": 1.125, "ajustes_incluir": 3.335},
])
def test_con_dos_decimales_o_menos_no_hay_aviso(op):
    assert _avisos_de(op) == []


def test_mil_doscientos_treinta_y_cuatro_con_567_se_sigue_aceptando():
    assert _js("console.log(JSON.stringify(CDI.montos.leer('1.234,567')));") == {"valor": 1234.567, "error": None}


# Importes con más de dos decimales: el redondeo de la pantalla tiene que dar
# lo mismo que centavos() del generador, que es lo que va al TXT.
IMPORTES = [2500.125, 2.675, 1.005, 0.125, 0.135, 1.115, 10.555, 1234.567, 0.004, 0.005, 0.0049999,
            999.995, 99999999.995, 123456789.125, 3.14159265, 1e-7, 5e-7, 0.000001, 7.0005, 16.665,
            1.0000000000000002, 2500.1250000001, 999999999999.995, 0.1 + 0.2]


def test_la_pantalla_redondea_igual_que_el_generador():
    js = _js(_aviso_js() + f"\nconsole.log(JSON.stringify({json.dumps(IMPORTES)}.map(alCentavoDelTxt)));")
    esperado = [str(centavos(v)).replace(".", ",") for v in IMPORTES]
    assert js == esperado


def test_con_dos_decimales_o_menos_la_pantalla_no_redondea():
    js = _js(_aviso_js() + "\nconsole.log(JSON.stringify([2500.12, 2500.1, 2500, 0, 0.01, 1e21].map(alCentavoDelTxt)));")
    assert js == [None] * 6


@pytest.mark.parametrize("flete, txt", [(2500.125, "2500.13"), (2.675, "2.68"), (12.34567, "12.35")])
def test_lo_que_dice_el_aviso_es_lo_que_sale_en_el_txt(client, request, flete, txt):
    """Punta a punta: el aviso y el MDDTFLE del TXT dicen lo mismo, y el TXT
    sale como antes (2500,125 → 2500.13)."""
    _registrar_con_cuit(client, "sep1d_" + hashlib.sha1(request.node.nodeid.encode()).hexdigest()[:16])
    r = client.post("/generate_maria", json={**_pedido(), "flete": flete})
    assert r.status_code == 200, r.text
    assert re.findall(r"^MDDTFLE=(\S+)", r.json()["content"], re.M) == [txt]
    aviso = _avisos_de({"flete": flete})[0]
    assert re.search(r"El TXT lleva ([\d,]+)\.$", aviso).group(1) == txt.replace(".", ",")


def test_el_aviso_va_junto_a_los_otros_avisos_no_bloqueantes():
    """refrescarAvisos de verdad: el aviso del flete va con los de la
    pantalla y los del servidor, y no frena nada."""
    stubs = ("let avisosSeq = 0; const SIN_CUENTAS = 'x';\n"
             "function stripLeadingIcon(s) { return s; } function extractItemRef() { return ''; }\n"
             "function buildMariaRequest() { return {}; } function firmaDelPedido() { return '{}'; }\n"
             "function pintarValor() {}\n"
             "CDI.state.items = [{}];\n"
             "CDI.despachante = { avisos: () => ['Del despachante.'] };\n"
             "CDI.api = async () => ({ ok: true, json: async () => ({ avisos: ['Del servidor.'], valor: null }) });\n")
    codigo = stubs + _aviso_js() + "\n" + _funciones("finalize.js", ["refrescarAvisos"]) + (
        "\n(async () => { await refrescarAvisos();"
        " console.log(JSON.stringify({panel: els.validatingAvisosPanel.hidden,"
        " lista: els.validatingAvisosList.innerHTML, cuenta: els.validatingAvisosCount.textContent})); })();")
    r = _correr(codigo, {"flete": 2500.125})
    assert r["panel"] is False
    assert r["cuenta"] == "· 3"
    assert "Del despachante." in r["lista"] and "Del servidor." in r["lista"]
    assert "Flete: escribiste «2500,1250»." in r["lista"] and "El TXT lleva 2500,13." in r["lista"]
