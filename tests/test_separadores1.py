"""SEPARADORES-1: el flete y el seguro de la factura con punto o coma.

«3.480» y «3.480,00» son tres mil cuatrocientos ochenta; «3,48» es tres con
cuarenta y ocho. Un flete o un seguro no lleva tres decimales: un único
separador seguido de tres cifras separa miles. Si la misma factura usa ese
separador como decimal, no se adivina: queda sin leer y la pantalla lo pide.

Antes el flete del 24/10 salió mil veces más chico (MDDTFLE=3.48 por 3480).
Datos sintéticos con la misma forma; Gemini falso.
"""
import inspect
import json
import re

import pytest

from proyecto_maria import pdf_extractor
from tests.test_generar_maria_txt import _gen
from tests.test_maria1a_lectura_factura import COPIAS, _leer


def _factura(flete, seguro="", **item):
    return {
        "operacion": {"numero_factura": "SEP-1", "vendedor_pais": "CN", "flete": flete, "seguro": seguro},
        "items": [dict({"descripcion": "pieza", "cantidad": "10", "valor_unitario": "250",
                        "peso_kg": "1", "origen": "CN"}, **item)],
    }


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("flete, esperado", [
    ("3.480", 3480.0), ("3.480,00", 3480.0), ("3,48", 3.48), ("3,480", 3480.0),
    ("USD 3.480", 3480.0), ("1.234.567", 1234567.0), ("3480", 3480.0), ("3.48", 3.48),
    ("0,480", 0.48),
])
def test_flete_sin_otra_pista(monkeypatch, copia, flete, esperado):
    r = _leer(monkeypatch, copia, _factura(flete))
    assert r["operacion"]["flete"] == pytest.approx(esperado)
    assert "flete" not in r["operacion"].get("campos_sin_leer", [])


@pytest.mark.parametrize("copia", COPIAS)
def test_seguro_tambien(monkeypatch, copia):
    r = _leer(monkeypatch, copia, _factura("", seguro="1.250"))
    assert r["operacion"]["seguro"] == pytest.approx(1250.0)


@pytest.mark.parametrize("copia", COPIAS)
def test_factura_con_coma_decimal(monkeypatch, copia):
    """La factura escribe 2,45: «3.480» es miles sin dudas."""
    r = _leer(monkeypatch, copia, _factura("3.480", valor_unitario="2,45"))
    assert r["operacion"]["flete"] == pytest.approx(3480.0)


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("flete", ["3.480", "1,250"])
def test_contradiccion_queda_sin_leer(monkeypatch, copia, flete):
    """La factura usa el mismo separador como decimal (2.45 o 2,45): «3.480»
    podría ser 3,48. No se adivina: vacío y avisado."""
    sep = flete[1]
    r = _leer(monkeypatch, copia, _factura(flete, valor_unitario=f"2{sep}45"))
    assert r["operacion"]["flete"] == 0.0
    assert "flete" in r["operacion"]["campos_sin_leer"]


@pytest.mark.parametrize("copia", COPIAS)
def test_sin_flete_no_se_avisa(monkeypatch, copia):
    r = _leer(monkeypatch, copia, _factura(""))
    assert r["operacion"]["flete"] == 0.0
    assert "flete" not in r["operacion"].get("campos_sin_leer", [])


def test_los_dos_prompts_piden_flete_y_seguro_como_texto():
    """Si Gemini convierte «3.480» a número, llega 3.48 y ya no se puede
    corregir. Las dos copias del prompt lo piden tal cual, como texto."""
    fuente = inspect.getsource(pdf_extractor._extract_with_gemini_vision)
    for campo in ("flete", "seguro"):
        lineas = re.findall(rf"^\s*1[12]\. {campo}: .*$", fuente, re.M)
        assert len(lineas) == 2, lineas
        assert all("tal como aparece" in ln and "número, 0" not in ln for ln in lineas), lineas
        assert f'"{campo}": 0.00' not in fuente


@pytest.mark.parametrize("copia", COPIAS)
def test_el_txt_sale_con_el_flete_entero(monkeypatch, copia):
    """Sin otra pista en la factura: antes salía MDDTFLE=3.48."""
    r = _leer(monkeypatch, copia, _factura("3.480", seguro="1.250"))
    op = r["operacion"]
    items = [{"pieza": "84713012", "descripcion": "Equipo de prueba generico", "cantidad": 10,
              "valor_unitario": 250, "peso_unitario": 1, "origen": "CN"}]
    txt = _gen("OP_SEP", items, flete=op["flete"], seguro=op["seguro"])
    assert re.findall(r"^MDDTFLE=(\S+)", txt, re.M) == ["3480.00"]
    assert re.findall(r"^MDDTASS=(\S+)", txt, re.M) == ["1250.00"]


@pytest.mark.parametrize("texto, decimal, esperado", [
    ("3.480", None, 3480.0), ("3.480", ",", 3480.0), ("3.480", ".", None),
    ("1,250", None, 1250.0), ("1,250", ".", 1250.0), ("1,250", ",", None),
    ("3,48", None, 3.48), ("3.480,00", ".", 3480.0), ("12.5", None, 12.5),
    ("1234.567", None, None), ("0.125", None, 0.125), (3.48, None, 3.48), ("", None, None),
])
def test_monto_de_la_factura(texto, decimal, esperado):
    assert pdf_extractor._monto_factura(texto, decimal) == (pytest.approx(esperado) if esperado else None)


# ---------- La pantalla: lo que la persona escribe a mano ----------

from tests.test_valor1 import ROOT, _correr, _funciones  # noqa: E402

MONTOS_JS = ROOT / "proyecto_maria" / "static" / "v2" / "montos_ar.js"


def _js(codigo, op=None):
    return _correr(codigo, op or {})


@pytest.mark.parametrize("escrito, valor", [
    ("3.480", 3480), ("3.480,00", 3480), ("3,48", 3.48), ("3480", 3480), ("3.48", 3.48),
    ("1.234.567", 1234567), ("1.234.567,5", 1234567.5), ("1,234,567.50", 1234567.5),
    ("0,125", 0.125), ("12.5", 12.5), (" 7925 ", 7925), ("-3,5", -3.5), (3.48, 3.48),
    ("", None), (None, None),
])
def test_la_pantalla_lee_el_monto(escrito, valor):
    r = _js(f"console.log(JSON.stringify(CDI.montos.leer({json.dumps(escrito)})));")
    assert r == {"valor": valor, "error": None}


@pytest.mark.parametrize("escrito, error", [
    ("1,500", "¿1.500 o 1,5?"), ("3,480", "¿3.480 o 3,48?"),
    ("abc", "Debe ser un numero."), ("1e3", "Debe ser un numero."), ("3.", "Debe ser un numero."),
    ("1.23.4", "no cierran"), ("1.234,56.7", "no cierran"), ("12,34.5", "no cierran"),
])
def test_lo_que_no_se_puede_leer_se_dice(escrito, error):
    r = _js(f"console.log(JSON.stringify(CDI.montos.leer({json.dumps(escrito)})));")
    assert r["valor"] is None and error in r["error"], r


@pytest.mark.parametrize("n, texto", [(3480, "3480"), (3.48, "3,48"), (1.125, "1,1250"), (0, "0"), (12.5, "12,5")])
def test_lo_que_se_muestra_se_vuelve_a_leer_igual(n, texto):
    r = _js(f"const t = CDI.montos.escribir({n}); console.log(JSON.stringify([t, CDI.montos.leer(t).valor]));")
    assert r == [texto, n]


def _revision(nombres):
    return ("const MONTOS = ['flete', 'seguro', 'gastos_anteriores_fob'];\n"
            "const MONEDA_ALIAS = {}; function normalizeDateForInput(v) { return v; }\n"
            # La de antes (toFixed(2)), para que el rojo sobre la revisión vieja diga el valor.
            "function formatNumber(n) { return n === Math.floor(n) ? String(n) : n.toFixed(2); }\n" +
            _funciones("review.js", nombres))


@pytest.mark.parametrize("campo", ["flete", "seguro", "gastos_anteriores_fob"])
def test_la_revision_muestra_el_monto_entero(campo):
    """Antes el campo mostraba «3.48» para un flete «3.480» (Number) y eso
    era lo que se guardaba y salía en el TXT."""
    r = _js(_revision(["normalizeValueForField"]) + f"""
console.log(JSON.stringify([normalizeValueForField('{campo}', '3.480'), normalizeValueForField('{campo}', 3.48)]));""")
    assert r == ["3480", "3,48"]


def test_la_revision_guarda_el_monto_entero():
    r = _js(_revision(["montoDelCampo", "validarMonto"]) + """
console.log(JSON.stringify({
  guardado: montoDelCampo('3.480'), aviso: validarMonto('3.480'),
  ambiguo: montoDelCampo('1,500'), avisoAmbiguo: validarMonto('1,500'), negativo: validarMonto('-5'),
  vacio: montoDelCampo(''), sinAviso: validarMonto(''),
}));""")
    assert r["guardado"] == 3480 and r["aviso"] is None
    assert r["ambiguo"] == "1,500" and r["avisoAmbiguo"].startswith("¿1.500 o 1,5?")
    assert r["negativo"] == "No puede ser negativo."
    assert r["vacio"] == 0 and r["sinAviso"] is None


@pytest.mark.parametrize("escrito, valor", [("1.500", 1500), ("1.500,25", 1500.25), ("87,5", 87.5), ("1,500", "1,500")])
def test_un_ajuste_con_punto_de_miles(escrito, valor):
    """VALOR-1: antes «1.500» viajaba como 1,5 (Number)."""
    r = _js(_funciones("finalize.js", ["ajusteDelPedido"]) + f"\nconsole.log(JSON.stringify(ajusteDelPedido({json.dumps(escrito)})));")
    assert r == valor


def test_el_pedido_lleva_los_montos_enteros():
    """buildMariaRequest: flete, seguro, gastos y ajustes con punto de miles."""
    r = _js(_funciones("finalize.js", ["montoDelPedido", "ajusteDelPedido", "ajusteMalEscrito"]) + """
console.log(JSON.stringify({
  flete: montoDelPedido('3.480'), numero: montoDelPedido(3480), vacio: montoDelPedido(''),
  ajuste: ajusteDelPedido('1.500'), ajusteVacio: ajusteDelPedido(''), ajusteMal: ajusteDelPedido('1,500'),
  avisoMal: ajusteMalEscrito('1,500'), avisoBasura: ajusteMalEscrito('x'), sinAviso: ajusteMalEscrito('1.500'),
}));""")
    assert r["flete"] == 3480 and r["numero"] == 3480 and r["vacio"] == 0
    assert r["ajuste"] == 1500 and r["ajusteVacio"] is None and r["ajusteMal"] == "1,500"
    assert r["avisoMal"].startswith("¿1.500 o 1,5?") and r["avisoBasura"] == "no es un número."
    assert r["sinAviso"] is None
    fuente = (ROOT / "proyecto_maria" / "static" / "v2" / "screens" / "finalize.js").read_text(encoding="utf-8")
    pedido = re.search(r"function buildMariaRequest\(\) \{.*?\n    \}", fuente, re.S).group(0)
    for campo in ("flete", "seguro", "gastos_anteriores_fob"):
        assert f"{campo}: montoDelPedido(op.{campo})" in pedido


def test_los_campos_aceptan_punto_y_coma():
    """Un campo numérico del navegador no acepta «3.480,00»: los cinco son de
    texto, y montos_ar.js carga antes que las pantallas que lo usan."""
    html = (ROOT / "proyecto_maria" / "templates" / "dashboard_v2.html").read_text(encoding="utf-8")
    for patron in (r'name="flete"', r'name="seguro"', r'name="gastos_anteriores_fob"',
                   r'id="valorIncluir"', r'id="valorDeducir"'):
        etiqueta = re.search(rf"<input[^>]*{patron}[^>]*>", html).group(0)
        assert 'type="text"' in etiqueta and 'inputmode="decimal"' in etiqueta, etiqueta
    scripts = re.findall(r'<script src="/static/v2/([^"?]+)', html)
    assert scripts.index("montos_ar.js") < scripts.index("screens/review.js") < scripts.index("screens/finalize.js")
    assert MONTOS_JS.exists()


@pytest.mark.parametrize("campo", ["flete", "seguro", "gastos_anteriores_fob"])
def test_la_revision_tiene_donde_decir_el_error(campo):
    """La pregunta de «1,500» se escribe en `[data-error-for=campo]`: sin ese
    lugar, el campo se pone rojo y nadie dice por qué."""
    html = (ROOT / "proyecto_maria" / "templates" / "dashboard_v2.html").read_text(encoding="utf-8")
    assert f'data-error-for="{campo}"' in html
