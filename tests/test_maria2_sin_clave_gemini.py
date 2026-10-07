"""MARIA-2: sin clave de Gemini (o con el lector con IA apagado) el lector de
PDF no inventa productos.

Antes, `_extract_with_gemini_vision` devolvía dos ítems «ITEM DEMOSTRACION»
que llegaban a la pantalla y al TXT sin marca. Ahora el endpoint responde
503 con un código que el frontend distingue y cero productos.

Nada de Gemini real ni internet: sin clave el lector no llama a nadie, y el
caso con clave inventada reemplaza el modelo por uno falso.
"""
import io
import json
import sys
import types

import pytest

from proyecto_maria import pdf_extractor


CODIGO = "lectura_automatica_no_disponible"


def _pdf_en_blanco() -> bytes:
    from PyPDF2 import PdfWriter

    w = PdfWriter()
    w.add_blank_page(width=595, height=842)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def _subir(client):
    return client.post(
        "/upload_pdf/public",
        files={"file": ("factura.pdf", _pdf_en_blanco(), "application/pdf")},
    )


def _sin_demo(texto: str):
    assert "DEMOSTRACION" not in texto
    assert "GEMINI_API_KEY" not in texto


@pytest.mark.parametrize(
    "entorno",
    [
        {"GEMINI_API_KEY": None},
        {"GEMINI_API_KEY": "", "ENABLE_PDF_LLM_FALLBACK": "true"},
        {"GEMINI_API_KEY": "test-key", "ENABLE_PDF_LLM_FALLBACK": "false"},
    ],
    ids=["sin_clave", "clave_vacia", "lector_apagado"],
)
def test_endpoint_sin_lector_no_inventa_productos(client, auth_override, monkeypatch, entorno):
    for k, v in entorno.items():
        if v is None:
            monkeypatch.delenv(k, raising=False)
        else:
            monkeypatch.setenv(k, v)

    r = _subir(client)

    assert r.status_code == 503, r.text
    body = r.json()
    assert body.get("codigo") == CODIGO
    assert "cargá los productos a mano" in body.get("detail", "")
    assert not body.get("items")
    _sin_demo(r.text)


def test_lector_sin_clave_levanta_error_propio(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(pdf_extractor.LecturaAutomaticaNoDisponible):
        pdf_extractor.process_pdf(_pdf_en_blanco())


def test_robust_extract_sin_clave_devuelve_cero_items(monkeypatch):
    """Camino viejo (sólo lo usan pruebas): PDF sin texto → lector con IA.
    Sin clave no inventa nada."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert pdf_extractor.robust_extract_pdf_items(_pdf_en_blanco()) == []


def test_con_clave_inventada_sigue_leyendo_con_el_modelo(client, auth_override, monkeypatch):
    """Con clave, el lector sigue yendo al modelo como antes (falso acá)."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("ENABLE_PDF_LLM_FALLBACK", "true")

    respuesta = {
        "operacion": {"numero_factura": "F-1", "vendedor_nombre": "Proveedor Inventado"},
        "items": [{"descripcion": "Tornillo M6", "cantidad": 3, "valor_unitario": 2.5,
                   "peso_kg": 0.1, "origen": "CN"}],
    }
    llamadas = []

    class _Modelo:
        def __init__(self, nombre):
            llamadas.append(nombre)

        def generate_content(self, partes):
            return types.SimpleNamespace(text=json.dumps(respuesta))

    falso = types.SimpleNamespace(configure=lambda **kw: None, GenerativeModel=_Modelo)
    google = sys.modules.get("google") or types.ModuleType("google")
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setattr(google, "generativeai", falso, raising=False)
    monkeypatch.setitem(sys.modules, "google.generativeai", falso)
    monkeypatch.setattr("time.sleep", lambda s: None)

    r = _subir(client)

    assert r.status_code == 200, r.text
    assert llamadas, "el lector no llamó al modelo"
    items = r.json()["items"]
    assert [i["descripcion"] for i in items] == ["Tornillo M6"]
    _sin_demo(r.text)


def test_sin_lector_no_gasta_cuota_diaria(client, auth_override, monkeypatch):
    """Una subida que no se puede leer no descuenta un PDF de la cuota."""
    from proyecto_maria.core import ai_quota

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    clave = (auth_override["username"], ai_quota._today_key())
    antes = ai_quota._counter.get(clave, 0)

    assert _subir(client).status_code == 503

    assert ai_quota._counter.get(clave, 0) == antes
