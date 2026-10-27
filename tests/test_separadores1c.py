"""SEPARADORES-1c: lo que dejó la revisión de SEPARADORES-1b (H1 a H3).

1. En la factura, una lectura de miles exige grupos bien formados: la cabeza
   de una a tres cifras sin cero adelante y cada grupo de tres. Si el monto
   sólo se lee como miles con grupos mal formados, queda sin leer (antes
   «0750.000» con la coma decimal daba 750000). En la pantalla, «01234.500»
   pregunta.
2. Lo que la pantalla no lee nunca llega al TXT como blanco: el servidor
   toma como blanco sólo lo que la pantalla también toma como blanco (antes
   «\\x85» llegaba tal cual y el TXT salía con MDDTFLE=0.00).
3. La pregunta no sugiere una forma que se lea distinto: las dos lecturas
   se escriben con escribir() (antes «2.500,125», «4.500,000» y sin el
   signo).

Datos inventados; Gemini falso.
"""
import hashlib
import json
import re

import pytest

from proyecto_maria import pdf_extractor
from proyecto_maria.core.maria_generator import importe_valido
from tests.test_maria1a_lectura_factura import COPIAS, _leer
from tests.test_maria7_rechazos_24_10 import _pedido, _registrar_con_cuit
from tests.test_separadores1 import _factura, _js
from tests.test_valor1 import _funciones


def _usuario(request):
    return "sep1c_" + hashlib.sha1(request.node.nodeid.encode()).hexdigest()[:16]


# ------------------------------------------------- 1. la factura: grupos de miles

# (texto, pista): sólo se leen como miles, con grupos mal formados.
MAL_FORMADOS = [
    # cero adelante
    ("0750.000", ","), ("02500.000", ","), ("03,250", "."), ("007,125", "."),
    ("02 750", None), ("0 750,00", ","),
    # cabeza de cuatro cifras o más, con dos grupos o con decimales
    ("7500.000.000", ","), ("7500.000.000", "."), ("7500.000.000", None),
    ("12345,678,000", None), ("7500.000,50", ","), ("7500.000,50", None),
    ("12345,678.90", "."), ("12345,678.90", None),
]


@pytest.mark.parametrize("texto, pista", MAL_FORMADOS)
def test_en_la_factura_miles_mal_formados_quedan_sin_leer(texto, pista):
    """Antes «0750.000» con «,» daba 750000 y «7500.000.000» 7500000000."""
    assert pdf_extractor._monto_factura(texto, pista) is None


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("flete, unitario", [("0750.000", "2,45"), ("7500.000.000", "2.45")])
def test_en_la_factura_se_avisa_y_no_llega_multiplicado(monkeypatch, copia, flete, unitario):
    r = _leer(monkeypatch, copia, _factura(flete, valor_unitario=unitario))
    assert r["operacion"]["flete"] == 0.0
    assert "flete" in r["operacion"]["campos_sin_leer"]


# Siguen como hoy: lo de la tarea y otros de la misma familia.
GUARDAS_FACTURA = [
    ("0500.000", ".", 500.0), ("0750.000", ".", 750.0),
    ("01,500", ",", 1.5), ("03,250", ",", 3.25),
    ("0,500", None, 0.5), ("0,500", ".", 0.5), ("0.750", ",", 0.75),
    ("3.480", ",", 3480.0), ("7.500.000", None, 7500000.0), ("7.500.000,50", None, 7500000.5),
    ("12,345,678.90", None, 12345678.9), ("1 234 567,25", ",", 1234567.25),
    ("4 500.000", ".", 4500.0), ("1.234,567", None, 1234.567), ("3480", None, 3480.0),
]


@pytest.mark.parametrize("texto, pista, esperado", GUARDAS_FACTURA)
def test_en_la_factura_lo_demas_sigue_como_hoy(texto, pista, esperado):
    assert pdf_extractor._monto_factura(texto, pista) == pytest.approx(esperado)


# ------------------------------------------------- 1 y 3. la pantalla: la pregunta


def _leer_js(escrito):
    return _js(f"console.log(JSON.stringify(CDI.montos.leer({json.dumps(escrito)})));")


@pytest.mark.parametrize("escrito, pregunta", [
    # 1: cero adelante con cuatro cifras o más
    ("01234.500", "¿1234500 o 1234,5?"), ("0750.000", "¿750000 o 750?"), ("00987,650", "¿987650 o 987,65?"),
    # 3: las dos lecturas como las escribe escribir(), con el signo
    ("2500.125", "¿2500125 o 2500,1250?"), ("4500.000", "¿4500000 o 4500?"),
    ("-1234.500", "¿-1234500 o -1234,5?"), ("7125,375", "¿7125375 o 7125,3750?"),
    ("-98765.000", "¿-98765000 o -98765?"),
    # la rama de la coma tampoco pierde el signo
    ("-3,480", "¿-3.480 o -3,48?"), ("-1,125", "¿-1.125 o -1,1250?"),
])
def test_en_la_pantalla_se_pregunta_con_formas_que_se_leen_igual(escrito, pregunta):
    """Antes «01234.500» se leía 1234,5 sin preguntar; «2500.125» proponía
    «2.500,125» (tres decimales) y «-1234.500» perdía el signo."""
    r = _leer_js(escrito)
    assert r["valor"] is None and r["error"].startswith(pregunta), r


@pytest.mark.parametrize("escrito, miles_esperado", [
    ("2500.125", 2500125), ("4500.000", 4500000), ("-1234.500", -1234500), ("01234.500", 1234500),
    ("7125,375", 7125375), ("-98765.000", -98765000), ("-3,480", -3480), ("-1,125", -1125),
])
def test_las_dos_formas_que_propone_se_leen_como_dice(escrito, miles_esperado):
    """Cada forma de la pregunta, escrita tal cual, se lee sin dudas y da lo
    que la pregunta dice: el miles es el número sin separador; el decimal,
    el mismo dividido por mil."""
    r = _js(f"""
        const e = CDI.montos.leer({json.dumps(escrito)}).error || '';
        const m = e.match(/^¿(\\S+) o (\\S+)\\?/);
        console.log(JSON.stringify(m ? [m[1], m[2]].map(t => CDI.montos.leer(t)) : e));
    """)
    assert isinstance(r, list), f"no pregunta: {r!r}"
    miles, decimal = r
    assert miles["error"] is None and decimal["error"] is None, r
    assert miles["valor"] == miles_esperado, r
    assert decimal["valor"] == pytest.approx(miles_esperado / 1000), r


@pytest.mark.parametrize("escrito, error", [
    ("01.500.000", "no cierran"), ("0.500,00", "no cierran"), ("07,250,000", "no cierran"),
])
def test_en_la_pantalla_miles_con_cero_adelante_no_cierran(escrito, error):
    """Antes «01.500.000» se leía 1500000."""
    r = _leer_js(escrito)
    assert r["valor"] is None and error in r["error"], r


@pytest.mark.parametrize("escrito, valor", [
    ("01,500", 1.5), ("012.500", 12.5), ("0,500", 0.5), ("0000.500", 0.5), ("00,250", 0.25),
    ("3.480", 3480), ("1.234.567", 1234567), ("1.234,567", 1234.567), ("2.500.125", 2500125),
    ("1234.50", 1234.5), ("-3,5", -3.5),
])
def test_en_la_pantalla_lo_demas_sigue_como_hoy(escrito, valor):
    assert _leer_js(escrito) == {"valor": valor, "error": None}


def test_una_cifra_larga_pegada_no_traba_ni_propone_otro_numero():
    """Con más de quince cifras el número ya no se escribe exacto: no se
    propone una forma con otras cifras. Y sigue sin trabar la pantalla."""
    r = _js("const t0 = Date.now(); const r = CDI.montos.leer('1'.repeat(199998) + '.125');"
            "const s = CDI.montos.leer('1234567890123.125');"
            "console.log(JSON.stringify({ms: Date.now() - t0, largo: r, dieciseis: s}));")
    assert r["ms"] < 1000, r
    assert r["largo"] == {"valor": None, "error": "Debe ser un numero."}, r
    assert r["dieciseis"] == {"valor": None, "error": "Debe ser un numero."}, r


# ------------------------------------------------- 2. la idea de «en blanco»


def _trim_de_js():
    """Los caracteres que trim() de la pantalla saca, de todo el plano básico."""
    return set(_js("const f = []; for (let i = 0; i < 0x10000; i++) {"
                   " const c = String.fromCharCode(i); if (c.trim() === '') f.push(i); }"
                   " console.log(JSON.stringify(f));"))


def _blanco_del_servidor(c):
    try:
        return importe_valido(c, "Flete") is None
    except ValueError:
        return False


def test_lo_que_el_servidor_toma_como_blanco_la_pantalla_tambien():
    """Así, un texto que la pantalla no pudo leer (y manda tal cual) nunca es
    blanco para el servidor. Antes \\x85 y \\x1c a \\x1f lo eran."""
    js = _trim_de_js()
    servidor = {i for i in range(0x10000) if _blanco_del_servidor(chr(i))}
    assert servidor <= js, sorted(hex(i) for i in servidor - js)
    # y los espacios comunes siguen siendo blanco
    assert {ord(c) for c in " \t\n\r\u00a0"} <= servidor


PEDIDO_JS = _funciones("finalize.js", ["montoDelPedido", "ajusteDelPedido"])

RAROS = ["\x85", "\x1c", "\x1f", " \x1d ", "\x85150", "150\x1e"]
CAMPOS = [("flete", "Flete: "), ("seguro", "Seguro: "), ("gastos_anteriores_fob", "Gastos (gastos")]


@pytest.mark.parametrize("campo, nombre", CAMPOS)
@pytest.mark.parametrize("escrito", RAROS)
def test_lo_que_la_pantalla_no_lee_no_sale_como_cero(client, request, campo, nombre, escrito):
    """Punta a punta: el pedido como lo arma la pantalla, y el servidor no
    genera. Antes «\\x85» salía MDDTFLE=0.00 y «\\x85150» 150.00."""
    monto = _js(PEDIDO_JS + f"\nconsole.log(JSON.stringify(montoDelPedido({json.dumps(escrito)})));")
    assert isinstance(monto, str), monto  # la pantalla no lo leyó
    _registrar_con_cuit(client, _usuario(request))
    r = client.post("/generate_maria", json={**_pedido(), "incoterm": "EXW", campo: monto})
    assert r.status_code == 400, r.text
    assert "no es un importe." in r.text and nombre in r.text, r.text
    assert "MDDTFLE" not in r.text


@pytest.mark.parametrize("escrito", ["\x85", "\x1f"])
def test_los_avisos_tampoco_lo_toman_como_cero(client, request, escrito):
    _registrar_con_cuit(client, _usuario(request))
    r = client.post("/generate_maria/avisos", json={**_pedido(), "flete": escrito})
    assert r.status_code == 400 and r.json()["detail"].startswith("Flete: "), r.text


def test_un_ajuste_con_un_caracter_raro_se_dice_en_las_cuentas(client):
    _registrar_con_cuit(client, "sep1c_ajuste")
    r = client.post("/generate_maria/avisos", json={**_pedido(), "ajustes_deducir": "\x85"})
    assert r.status_code == 200, r.text
    assert r.json()["valor"]["error"].startswith("Ajustes a deducir: «"), r.json()["valor"]


@pytest.mark.parametrize("escrito, txt", [
    ("", "0.00"), ("  ", "0.00"), ("\t\n", "0.00"), ("\u00a0", "0.00"), (" 150\u00a0", "150.00"),
    ("\u3000150 ", "150.00"),
])
def test_vacio_o_con_espacios_comunes_sigue_siendo_cero_o_el_numero(client, request, escrito, txt):
    _registrar_con_cuit(client, _usuario(request))
    r = client.post("/generate_maria", json={**_pedido(), "flete": escrito})
    assert r.status_code == 200, r.text
    assert re.findall(r"^MDDTFLE=(\S+)", r.json()["content"], re.M) == [txt]


def test_la_pantalla_manda_cero_con_espacios_comunes():
    r = _js(PEDIDO_JS + "\nconsole.log(JSON.stringify(['', '  ', '\\u00a0', ' 150\\u00a0'].map(montoDelPedido)));")
    assert r == [0, 0, 0, 150]
