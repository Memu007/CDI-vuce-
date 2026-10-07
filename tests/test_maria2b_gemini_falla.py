"""MARIA-2b: con clave, pero Gemini caído, con clave inválida o con una
respuesta ilegible, el lector no dice «No se encontró tabla de items»: da el
mismo 503 con su `code` que MARIA-2, para que la pantalla ofrezca la carga
manual. Si Gemini responde bien pero sin productos, sigue el 400 de siempre.

En las dos copias del lector. Gemini falso; ni Gemini real ni internet.
"""
import io
import json
import sys
import types

import pytest

CODIGO = "lectura_automatica_no_disponible"
COPIAS = ["pymupdf", "pdf_directo"]


def _pdf_en_blanco() -> bytes:
    from PyPDF2 import PdfWriter

    w = PdfWriter()
    w.add_blank_page(width=595, height=842)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def _fitz_falso():
    class _Pix:
        def tobytes(self, fmt):
            return b"\xff\xd8\xff\xd9"

    class _Pagina:
        def get_pixmap(self, matrix=None):
            return _Pix()

    class _Doc:
        def __len__(self):
            return 1

        def __getitem__(self, i):
            return _Pagina()

        def close(self):
            pass

    return types.SimpleNamespace(open=lambda **kw: _Doc(), Matrix=lambda a, b: None)


def _gemini(monkeypatch, copia, responder):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("ENABLE_PDF_LLM_FALLBACK", "true")
    monkeypatch.setattr("time.sleep", lambda s: None)

    class _Modelo:
        def __init__(self, nombre):
            pass

        def generate_content(self, partes):
            return responder()

    falso = types.SimpleNamespace(configure=lambda **kw: None, GenerativeModel=_Modelo)
    google = sys.modules.get("google") or types.ModuleType("google")
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setattr(google, "generativeai", falso, raising=False)
    monkeypatch.setitem(sys.modules, "google.generativeai", falso)
    monkeypatch.setitem(sys.modules, "fitz", _fitz_falso() if copia == "pymupdf" else None)


def _subir(client):
    return client.post("/upload_pdf/public",
                       files={"file": ("factura.pdf", _pdf_en_blanco(), "application/pdf")})


def _clave_invalida():
    raise RuntimeError("400 API key not valid. Please pass a valid API key.")


def _caido():
    raise ConnectionError("503 The model is overloaded")


def _ilegible():
    return types.SimpleNamespace(text="esto no es JSON")


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("falla", [_clave_invalida, _caido, _ilegible],
                         ids=["clave_invalida", "gemini_caido", "respuesta_ilegible"])
def test_gemini_falla_da_el_503_de_carga_manual(client, auth_override, monkeypatch, copia, falla):
    _gemini(monkeypatch, copia, falla)
    r = _subir(client)

    assert r.status_code == 503, r.text
    assert r.json().get("code") == CODIGO
    assert "cargá los productos a mano" in r.json().get("detail", "")
    assert "API key" not in r.text  # nada interno hacia la pantalla


@pytest.mark.parametrize("copia", COPIAS)
def test_gemini_responde_sin_productos_sigue_el_400(client, auth_override, monkeypatch, copia):
    _gemini(monkeypatch, copia, lambda: types.SimpleNamespace(
        text=json.dumps({"operacion": {}, "items": []})))
    r = _subir(client)

    assert r.status_code == 400, r.text
    assert r.json().get("code") != CODIGO
