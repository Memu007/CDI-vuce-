"""RENDIMIENTO-1b: un PDF armado no deja a nadie sin lectura.

La adivinanza del vendedor lee el texto del PDF sólo con pypdf: pdfminer se
cuelga para siempre con un PDF armado (un /Length que se apunta a sí mismo),
y un hilo colgado no se puede cortar. Y un tiempo máximo en 0 o negativo
cae al valor por defecto, igual que uno mal escrito.
"""
import asyncio
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from proyecto_maria import main

AQUI = Path(__file__).parent
PDF = (AQUI / "test_factura.pdf").read_bytes()
USUARIO = {"username": "rend1b", "roles": ["operador"], "effective_owner": "rend1b",
           "plan": "premium", "billing_status": "active"}


def test_pdfs_armados_en_paralelo_y_despues_uno_bueno_se_lee():
    env = {**os.environ, "PDF_READ_WORKERS": "4", "PDF_VENDOR_TIMEOUT_S": "1",
           "PDF_READ_TIMEOUT_S": "3"}
    try:
        p = subprocess.run([sys.executable, str(AQUI / "escenario_pdf_armado.py")],
                           capture_output=True, text=True, timeout=60, env=env)
    except subprocess.TimeoutExpired:
        pytest.fail("el escenario no terminó en 60 s: la lectura se volvió a colgar")
    lineas = [l for l in p.stdout.splitlines() if l.startswith("{")]
    assert lineas, f"sin resultado:\n{p.stdout[-800:]}\n{p.stderr[-1500:]}"
    r = json.loads(lineas[-1])
    assert r["armados"] == [200, 200, 200, 200], r
    assert r["bueno"] == 200, r
    assert r["bueno_s"] < 3, r


@pytest.fixture
def _entorno(monkeypatch):
    from proyecto_maria.core import ai_quota
    from proyecto_maria.core.rate_limit import limiter
    monkeypatch.setattr(limiter, "enabled", False)
    monkeypatch.setattr(main, "lectura_automatica_disponible", lambda: True)
    monkeypatch.setattr(ai_quota, "enforce_pdf_quota", lambda *a, **k: None)
    monkeypatch.setattr(main, "_POOL_LECTURA_PDF", None)
    main.app.dependency_overrides[main.get_current_user] = lambda: dict(USUARIO)
    yield
    main.app.dependency_overrides.pop(main.get_current_user, None)


def _pdf_con_texto(lineas) -> bytes:
    """Un PDF de una página con esas líneas de texto (Helvetica)."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
    w = PdfWriter()
    pagina = w.add_blank_page(600, 800)
    fuente = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                               NameObject("/Subtype"): NameObject("/Type1"),
                               NameObject("/BaseFont"): NameObject("/Helvetica")})
    pagina[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): w._add_object(fuente)})})
    cuerpo = "".join(f"BT /F1 12 Tf 50 {750 - 20 * i} Td ({t}) Tj ET\n" for i, t in enumerate(lineas))
    contenido = DecodedStreamObject()
    contenido.set_data(cuerpo.encode("latin-1"))
    pagina[NameObject("/Contents")] = w._add_object(contenido)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def _subir(datos):
    async def _ir():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            return await c.post("/upload_pdf/public",
                                files={"file": ("f.pdf", datos, "application/pdf")})
    return asyncio.run(_ir())


def test_el_vendedor_se_adivina_sin_pdfminer_ni_pdfplumber(_entorno, monkeypatch):
    import pdfminer.high_level
    import pdfplumber

    llamados = []

    def _prohibido(*_a, **_k):
        # Se anota y se falla: el código viejo atrapaba cualquier error del
        # lector y seguía, así que sólo fallar no alcanzaba para verlo.
        llamados.append(1)
        raise RuntimeError("pdfminer/pdfplumber no se usan con un PDF del usuario")
    monkeypatch.setattr(pdfminer.high_level, "extract_text", _prohibido)
    monkeypatch.setattr(pdfplumber, "open", _prohibido)
    monkeypatch.setattr(main, "process_pdf", lambda *_: {"items": [{"descripcion": "x"}], "operacion": {}})
    r = _subir(_pdf_con_texto(["COMMERCIAL INVOICE", "VENDOR: ACME TRADING CO LTD", "Item 1"]))
    assert r.status_code == 200, r.text[:200]
    assert r.json()["operacion"].get("vendedor_nombre") == "ACME TRADING CO LTD", r.json()["operacion"]
    assert not llamados, "la adivinanza del vendedor le pasó el PDF a pdfminer o pdfplumber"


@pytest.mark.parametrize("valor", ["0", "-5"])
def test_tiempo_de_lectura_en_cero_o_negativo_usa_el_de_siempre(_entorno, monkeypatch, valor):
    monkeypatch.setenv("PDF_READ_TIMEOUT_S", valor)
    monkeypatch.setattr(main, "process_pdf",
                        lambda *_: {"items": [{"descripcion": "x"}], "operacion": {"vendedor_nombre": "P"}})
    r = _subir(PDF)
    assert r.status_code == 200, r.text[:200]


@pytest.mark.parametrize("valor", ["0", "-5"])
def test_tiempo_de_validacion_en_cero_o_negativo_usa_el_de_siempre(_entorno, monkeypatch, valor):
    monkeypatch.setenv("PDF_VALIDATE_TIMEOUT_S", valor)
    monkeypatch.setattr(main, "process_pdf",
                        lambda *_: {"items": [{"descripcion": "x"}], "operacion": {"vendedor_nombre": "P"}})
    r = _subir(PDF)
    assert r.status_code == 200, r.text[:200]


@pytest.mark.parametrize("valor", ["0", "-5"])
def test_tiempo_del_vendedor_en_cero_o_negativo_usa_el_de_siempre(_entorno, monkeypatch, valor):
    monkeypatch.setenv("PDF_VENDOR_TIMEOUT_S", valor)
    monkeypatch.setattr(main, "process_pdf", lambda *_: {"items": [{"descripcion": "x"}], "operacion": {}})
    r = _subir(_pdf_con_texto(["VENDOR: ACME TRADING CO LTD"]))
    assert r.status_code == 200, r.text[:200]
    assert r.json()["operacion"].get("vendedor_nombre") == "ACME TRADING CO LTD", r.json()["operacion"]


@pytest.mark.parametrize("valor", ["0", "-5"])
def test_tiempo_de_gemini_en_cero_o_negativo_usa_el_de_siempre(_entorno, monkeypatch, valor):
    monkeypatch.setenv("NCM_GEMINI_TIMEOUT_S", valor)
    monkeypatch.setattr(main, "_suggest_ncm_with_gemini",
                        lambda *_a, **_k: [{"ncm": "8471.30.12", "descripcion": "x", "confianza": 0.9}])

    async def _ir():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            return await c.post("/api/ncm/sugerir",
                                json={"descripcion": "artefacto inventado para la prueba qwz"})
    r = asyncio.run(_ir())
    assert r.status_code == 200, r.text[:200]
    assert r.json().get("sugerencias"), r.json()


def _pdf_con_contenido_enorme(megas: float) -> bytes:
    """Una página con un content stream de texto sin comprimir de ~megas MB:
    pypdf tarda más que lineal en sacarle el texto (revisor de RENDIMIENTO-1b)."""
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
    w = PdfWriter()
    pagina = w.add_blank_page(600, 800)
    fuente = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                               NameObject("/Subtype"): NameObject("/Type1"),
                               NameObject("/BaseFont"): NameObject("/Helvetica")})
    pagina[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): w._add_object(fuente)})})
    linea = b"BT /F1 12 Tf 50 700 Td (aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa) Tj ET\n"
    contenido = DecodedStreamObject()
    contenido.set_data(linea * int(megas * 1024 * 1024 / len(linea)))
    pagina[NameObject("/Contents")] = w._add_object(contenido)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def test_texto_del_vendedor_no_se_traba_con_un_contenido_enorme():
    from proyecto_maria.pdf_extractor import extraer_texto_pdf_seguro
    datos = _pdf_con_contenido_enorme(3)
    t0 = time.monotonic()
    extraer_texto_pdf_seguro(datos)
    demora = time.monotonic() - t0
    assert demora < 1.0, f"sacar el texto de una página de 3 MB tardó {demora:.2f} s"


def test_el_vendedor_se_busca_en_las_primeras_paginas():
    """Con un PDF normal de dos páginas, el texto de la primera sigue estando."""
    from proyecto_maria.pdf_extractor import extraer_texto_pdf_seguro, detect_vendor_from_text
    texto = extraer_texto_pdf_seguro(_pdf_con_texto(["VENDOR: ACME TRADING CO LTD", "Item 1"]))
    assert detect_vendor_from_text(texto) == "ACME TRADING CO LTD"


@pytest.mark.parametrize("valor", ["inf", "1e309", "nan", "  "])
def test_tiempos_infinitos_o_raros_usan_el_de_siempre(monkeypatch, valor):
    from proyecto_maria.security import file_security
    for variable in ("PDF_READ_TIMEOUT_S", "PDF_VALIDATE_TIMEOUT_S",
                     "PDF_VENDOR_TIMEOUT_S", "NCM_GEMINI_TIMEOUT_S"):
        monkeypatch.setenv(variable, valor)
    assert main._pdf_read_timeout_s() == 120.0
    assert main._pdf_vendor_timeout_s() == 15.0
    assert main._segundos_de_entorno("NCM_GEMINI_TIMEOUT_S", 30.0) == 30.0
    assert file_security._pdf_validate_timeout_s() == 30.0
