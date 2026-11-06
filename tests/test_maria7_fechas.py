"""MARIA-7, punto 8: la fecha de la factura en el orden correcto.

El 24/10 una factura que decía `2026/08/07` (7 de agosto) salió `08/07/2026`
en el TXT. El lector le pedía a Gemini la fecha ya convertida a DD/MM/AAAA y
la conversión quedaba en sus manos. Ahora Gemini la copia tal cual y el
orden lo decide `_fecha_leida`: con el año adelante, año/mes/día; con el año
al final y día y mes de 12 o menos, no se adivina, se pregunta (Emi,
2026-10-24). Datos inventados.
"""
import inspect
import io

import pytest

from proyecto_maria import pdf_extractor
from tests.test_generar_maria_txt import ITEMS_OK, _gen
from tests.test_maria1a_lectura_factura import COPIAS, _leer, _pdf_en_blanco


def _leida(monkeypatch, copia, fecha):
    factura = {"operacion": {"numero_factura": "INV-2026/0457", "fecha_emision": fecha},
               "items": [{"descripcion": "Lona de PVC gris", "cantidad": 750, "valor_unitario": 1.85,
                          "origen": "CN"}]}
    operacion = _leer(monkeypatch, copia, factura)["operacion"]
    return operacion["fecha_emision"], operacion.get("avisos_fecha", [])


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("escrita", ["2026/08/07", "2026-08-07", "2026.8.7", "2026年08月07日"])
def test_con_el_anio_adelante_es_anio_mes_dia_y_llega_asi_al_txt(monkeypatch, copia, escrita):
    fecha, avisos = _leida(monkeypatch, copia, escrita)
    assert (fecha, avisos) == ("07/08/2026", [])
    txt = _gen("OP123456", ITEMS_OK, fecha_emision=fecha)
    assert "\r\nMCPL=07/08/2026" in txt


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("escrita, esperada", [
    ("13/08/2026", "13/08/2026"),      # el 13 sólo puede ser el día
    ("08/13/2026", "13/08/2026"),      # factura de Estados Unidos: mes/día
    ("05/05/2026", "05/05/2026"),      # día y mes iguales: no hay duda
    ("Aug 7, 2026", "07/08/2026"),     # con el mes en letras tampoco
    ("7 de agosto de 2026", "07/08/2026"),
    ("07-Aug-2026", "07/08/2026"),
])
def test_cuando_el_orden_se_puede_saber_no_se_pregunta(monkeypatch, copia, escrita, esperada):
    assert _leida(monkeypatch, copia, escrita) == (esperada, [])


@pytest.mark.parametrize("copia", COPIAS)
def test_ambigua_no_se_adivina_se_pregunta(monkeypatch, copia):
    fecha, avisos = _leida(monkeypatch, copia, "07/08/2026")
    assert fecha == ""
    assert avisos == ["Fecha de emisión: «07/08/2026» puede ser el 7 de agosto o el 8 de julio; "
                      "no se adivina. Cargala en la revisión (DD/MM/AAAA)."]


@pytest.mark.parametrize("escrita", ["2026/02/30", "00/05/2026", "fecha a confirmar"])
def test_lo_que_no_es_fecha_sale_vacio_con_aviso(escrita):
    fecha, aviso = pdf_extractor._fecha_leida(escrita)
    assert fecha == ""
    assert aviso.startswith(f"Fecha de emisión: «{escrita}» ")


@pytest.mark.parametrize("vacia", [None, "", "N/A"])
def test_sin_fecha_no_hay_aviso_de_orden(vacia):
    # Que falta la fecha ya lo dicen la revisión y los avisos de generate.
    assert pdf_extractor._fecha_leida(vacia) == ("", "")


def test_a_gemini_se_le_pide_la_fecha_tal_cual_en_las_dos_copias():
    fuente = inspect.getsource(pdf_extractor._extract_with_gemini_vision)
    assert "fecha_emision: Fecha de la factura (formato DD/MM/YYYY)" not in fuente
    assert fuente.count("NO la conviertas ni cambies el orden de día, mes y año.") == 2


def test_la_pregunta_llega_a_la_pantalla(auth_override, client, monkeypatch):
    import proyecto_maria.main as main
    leido = {"documento": {"tipo": "factura_comercial", "operacion": "importacion", "destinacion": ""},
             "operacion": {"fecha_emision": "", "avisos_fecha": ["Fecha de emisión: pregunta de prueba."],
                           "avisos_peso": ["Peso de «X»: aviso de prueba."]},
             "items": [{"descripcion": "X", "cantidad": 1, "valor_unitario": 1}]}
    monkeypatch.setattr(main, "lectura_automatica_disponible", lambda: True)
    monkeypatch.setattr(main, "process_pdf", lambda contenido: leido)
    monkeypatch.setattr("proyecto_maria.core.ai_quota.enforce_pdf_quota", lambda usuario: None)
    r = client.post("/upload_pdf/public", files={"file": ("f.pdf", io.BytesIO(_pdf_en_blanco()), "application/pdf")})
    assert r.status_code == 200, r.text
    # Cada una con su título en la pantalla: la fecha es de la factura.
    assert r.json()["avisos"] == ["Peso de «X»: aviso de prueba."]
    assert r.json()["avisos_fecha"] == ["Fecha de emisión: pregunta de prueba."]
    assert "avisos_fecha" not in r.json()["operacion"]
