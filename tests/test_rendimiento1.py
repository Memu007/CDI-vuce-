"""RENDIMIENTO-1: leer un PDF (o pedirle un NCM a Gemini) no frena el sitio.

Con un solo proceso, una llamada sincrónica dentro de una ruta async deja a
todos los demás esperando. Las pruebas simulan una lectura lenta que bloquea
(time.sleep, como un parser o una llamada de red sincrónica) y miden cuánto
tarda /health mientras tanto.
"""
import asyncio
import os
import time
from pathlib import Path

import httpx
import pytest

from proyecto_maria import main

PDF = (Path(__file__).parent / "test_factura.pdf").read_bytes()
LENTO_S = 1.5
USUARIO = {"username": "rend1", "roles": ["operador"], "effective_owner": "rend1",
           "plan": "premium", "billing_status": "active"}


@pytest.fixture(autouse=True)
def _entorno(monkeypatch):
    from proyecto_maria.core import ai_quota
    from proyecto_maria.core.rate_limit import limiter
    monkeypatch.setattr(limiter, "enabled", False)
    monkeypatch.setattr(main, "lectura_automatica_disponible", lambda: True)
    monkeypatch.setattr(ai_quota, "enforce_pdf_quota", lambda *a, **k: None)
    main.app.dependency_overrides[main.get_current_user] = lambda: dict(USUARIO)
    yield
    main.app.dependency_overrides.pop(main.get_current_user, None)


INICIO = {}


def _bloquear():
    """Lo que hace una lectura lenta sincrónica: anota cuándo empezó y
    retiene el hilo que la corre."""
    INICIO["t"] = time.monotonic()
    time.sleep(LENTO_S)


def _lectura_lenta(*_a, **_k):
    _bloquear()
    return {"items": [{"descripcion": "x", "cantidad": 1}],
            "operacion": {"vendedor_nombre": "Proveedor"}}


async def _health_mientras(pedido_lento):
    """Lanza el pedido lento y, apenas empieza la lectura lenta, pide /health.

    Devuelve (segundos desde que empezó la lectura hasta que /health
    respondió, respuesta del pedido lento). Si la lectura bloquea el
    servidor, nada más corre hasta que termina: la demora es de LENTO_S o más.
    """
    INICIO.clear()
    transport = httpx.ASGITransport(app=main.app)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        lento = asyncio.create_task(pedido_lento(c))
        limite = time.monotonic() + 10
        while "t" not in INICIO:
            assert time.monotonic() < limite, "la lectura lenta nunca empezó"
            await asyncio.sleep(0.005)
        h = await c.get("/health")
        demora = time.monotonic() - INICIO["t"]
        assert h.status_code == 200
        return demora, await lento


def _subir(c):
    return c.post("/upload_pdf/public",
                  files={"file": ("factura.pdf", PDF, "application/pdf")})


def test_health_responde_mientras_se_lee_un_pdf(monkeypatch):
    monkeypatch.setattr(main, "process_pdf", _lectura_lenta)
    demora, r = asyncio.run(_health_mientras(_subir))
    assert r.status_code == 200, r.text[:200]
    assert demora < 0.5, f"/health tardó {demora:.2f} s mientras se leía un PDF"


def test_health_responde_mientras_se_lee_el_texto_del_pdf(monkeypatch):
    """El texto crudo (para adivinar el vendedor) también se lee aparte."""
    import proyecto_maria.pdf_extractor as ext
    monkeypatch.setattr(main, "process_pdf",
                        lambda *_: {"items": [{"descripcion": "x"}], "operacion": {}})
    monkeypatch.setattr(ext, "extraer_texto_pdf_seguro", lambda *_: (_bloquear(), "")[1])
    demora, r = asyncio.run(_health_mientras(_subir))
    assert r.status_code == 200, r.text[:200]
    assert demora < 0.5, f"/health tardó {demora:.2f} s mientras se leía el texto"


def test_lectura_con_tiempo_maximo_y_error_claro(monkeypatch):
    monkeypatch.setenv("PDF_READ_TIMEOUT_S", "0.3")
    monkeypatch.setattr(main, "process_pdf", _lectura_lenta)

    async def _pedir():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            t0 = time.monotonic()
            r = await _subir(c)
            return r, time.monotonic() - t0

    r, demora = asyncio.run(_pedir())
    assert r.status_code == 504, f"{r.status_code} {r.text[:200]}"
    # Mismo formato que el resto de los errores de la subida (MARIA-2): la
    # pantalla muestra `detail` como texto y distingue por `code`.
    cuerpo = r.json()
    assert cuerpo["code"] == "lectura_pdf_demasiado_larga", cuerpo
    assert isinstance(cuerpo["detail"], str) and "tardó demasiado" in cuerpo["detail"], cuerpo
    assert demora < LENTO_S, f"la respuesta esperó toda la lectura ({demora:.2f} s)"


def test_health_responde_mientras_gemini_sugiere_ncm(monkeypatch):
    monkeypatch.setattr(main, "_suggest_ncm_with_gemini",
                        lambda *_a, **_k: (_bloquear(), [])[1])

    def _sugerir(c):
        return c.post("/api/ncm/sugerir",
                      json={"descripcion": "artefacto inventado para la prueba qwz"})

    demora, r = asyncio.run(_health_mientras(_sugerir))
    assert r.status_code == 200, r.text[:200]
    assert demora < 0.5, f"/health tardó {demora:.2f} s mientras Gemini sugería"


def _pdf_armado() -> bytes:
    """Una página cuyo contenido termina en un comentario sin fin de línea.

    Con PyPDF2 3.0.1, leer su texto no termina nunca (X3 de la auditoría)."""
    import io
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, NameObject
    w = PdfWriter()
    pagina = w.add_blank_page(200, 200)
    contenido = DecodedStreamObject()
    contenido.set_data(b"BT /F1 12 Tf (hola) Tj ET %")
    pagina[NameObject("/Contents")] = w._add_object(contenido)
    buf = io.BytesIO()
    w.write(buf)
    return buf.getvalue()


def test_pdf_armado_se_lee_sin_colgarse(monkeypatch):
    """Por el camino de pypdf: pdfminer y OCR no sacan texto, así que el
    lector de respaldo tiene que abrirlo (con PyPDF2 3.0.1 no terminaba)."""
    import concurrent.futures
    import pdfminer.high_level
    import pypdf
    import proyecto_maria.pdf_extractor as ext
    usado = []
    original = pypdf.PdfReader
    monkeypatch.setattr(pypdf, "PdfReader", lambda *a, **k: (usado.append(1), original(*a, **k))[1])
    monkeypatch.setattr(pdfminer.high_level, "extract_text", lambda *a, **k: "")
    monkeypatch.setattr(ext, "_ocr_pdf_text", lambda *_: "")
    with concurrent.futures.ThreadPoolExecutor(1) as ex:
        texto = ex.submit(ext._extract_pdf_text, _pdf_armado()).result(timeout=20)
    assert isinstance(texto, str)
    assert usado, "el PDF armado no pasó por pypdf"
    # Y validarlo (abrirlo y contar páginas) también termina.
    from proyecto_maria.security.file_security import _abrir_pdf
    with concurrent.futures.ThreadPoolExecutor(1) as ex:
        assert ex.submit(_abrir_pdf, _pdf_armado()).result(timeout=20) == (False, 1)


def test_ya_no_se_usa_pyPDF2_ni_python_jose():
    """El lector viejo y la librería de tokens sin uso no vuelven."""
    raiz = Path(__file__).resolve().parents[1]
    req = (raiz / "requirements.txt").read_text()
    lineas = [l.split("#")[0].strip().lower() for l in req.splitlines()]
    assert not any(l.startswith(("pypdf2", "python-jose")) for l in lineas)
    for archivo in (raiz / "proyecto_maria").rglob("*.py"):
        if "tests" in archivo.parts:
            continue
        texto = archivo.read_text(encoding="utf-8", errors="ignore")
        import re
        usa = re.search(r"^\s*(?:from|import)\s+(?:PyPDF2|jose)\b|__import__\(['\"](?:PyPDF2|jose)",
                        texto, re.MULTILINE)
        assert not usa, (archivo, usa and usa.group(0))


def test_health_responde_mientras_se_valida_el_pdf(monkeypatch):
    """Abrir el PDF para validarlo (antes de leerlo) también va aparte."""
    from proyecto_maria.security import file_security
    monkeypatch.setattr(file_security, "_abrir_pdf", lambda *_: (_bloquear(), (False, 1))[1])
    monkeypatch.setattr(main, "process_pdf",
                        lambda *_: {"items": [{"descripcion": "x"}], "operacion": {"vendedor_nombre": "P"}})
    demora, r = asyncio.run(_health_mientras(_subir))
    assert r.status_code == 200, r.text[:200]
    assert demora < 0.5, f"/health tardó {demora:.2f} s mientras se validaba el PDF"


def _subir_y_medir():
    """(respuesta, segundos hasta la respuesta), medidos adentro del loop: al
    cerrarse, el loop espera a los hilos que siguen corriendo y eso no es
    tiempo de respuesta."""
    async def _ir():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            t0 = time.monotonic()
            r = await _subir(c)
            return r, time.monotonic() - t0
    return asyncio.run(_ir())


def _subir_sincronico(monkeypatch):
    return _subir_y_medir()[0]


def test_validar_el_pdf_tiene_tiempo_maximo(monkeypatch):
    from proyecto_maria.security import file_security
    monkeypatch.setenv("PDF_VALIDATE_TIMEOUT_S", "0.3")
    monkeypatch.setattr(file_security, "_abrir_pdf", lambda *_: (_bloquear(), (False, 1))[1])
    r, demora = _subir_y_medir()
    assert r.status_code == 400, r.text[:200]
    assert "tardó demasiado" in r.json()["detail"]
    assert demora < LENTO_S, f"respondió a los {demora:.2f} s"


def test_tiempo_de_validacion_mal_escrito_no_rechaza_todo(monkeypatch):
    monkeypatch.setenv("PDF_VALIDATE_TIMEOUT_S", "30s")
    monkeypatch.setattr(main, "process_pdf",
                        lambda *_: {"items": [{"descripcion": "x"}], "operacion": {"vendedor_nombre": "P"}})
    r = _subir_sincronico(monkeypatch)
    assert r.status_code == 200, r.text[:200]


def test_texto_del_vendedor_tiene_tiempo_maximo(monkeypatch):
    """La adivinanza del vendedor es opcional: si tarda, se sigue sin ella, y
    con un tiempo propio más corto que el de la lectura del PDF."""
    import proyecto_maria.pdf_extractor as ext
    monkeypatch.setenv("PDF_READ_TIMEOUT_S", "30")
    monkeypatch.setenv("PDF_VENDOR_TIMEOUT_S", "0.3")
    monkeypatch.setattr(main, "process_pdf",
                        lambda *_: {"items": [{"descripcion": "x"}], "operacion": {}})
    monkeypatch.setattr(ext, "extraer_texto_pdf_seguro", lambda *_: (_bloquear(), "")[1])
    r, demora = _subir_y_medir()
    assert r.status_code == 200, r.text[:200]
    assert demora < LENTO_S, f"respondió a los {demora:.2f} s"


def test_error_de_tiempo_adentro_del_lector_no_es_lectura_lenta(monkeypatch):
    def _falla(*_):
        raise TimeoutError("se cortó la conexión")
    monkeypatch.setattr(main, "process_pdf", _falla)
    r = _subir_sincronico(monkeypatch)
    assert r.status_code == 500, r.text[:200]
    assert "lectura_pdf_demasiado_larga" not in r.text


def test_pdf_encriptado_dice_que_esta_encriptado():
    import io
    from pypdf import PdfWriter
    from fastapi.testclient import TestClient
    w = PdfWriter()
    w.add_blank_page(200, 200)
    w.encrypt("una-clave")
    buf = io.BytesIO()
    w.write(buf)
    r = TestClient(main.app).post(
        "/upload_pdf/public", files={"file": ("x.pdf", buf.getvalue(), "application/pdf")})
    assert r.status_code == 400, r.text[:200]
    assert "Encrypted PDFs are not allowed" in r.json()["detail"]


def test_pdfs_lentos_no_traban_a_ncm_ni_a_la_validacion(monkeypatch):
    """Las lecturas de PDF tienen su propio grupo de hilos. Aunque las
    lentas lo llenen (y sigan corriendo después del 504), sugerir un NCM y
    validar otro PDF no hacen cola detrás de ellas."""
    import concurrent.futures
    from proyecto_maria.security.file_security import validate_file_upload
    from starlette.datastructures import UploadFile
    monkeypatch.setenv("PDF_READ_TIMEOUT_S", "0.3")
    monkeypatch.setenv("PDF_READ_WORKERS", "2")
    monkeypatch.setattr(main, "_POOL_LECTURA_PDF", None, raising=False)
    monkeypatch.setattr(main, "process_pdf", lambda *_: (time.sleep(3), {})[1])
    monkeypatch.setattr(main, "_suggest_ncm_with_gemini", lambda *_a, **_k: [])

    async def _escenario():
        # El grupo de hilos por defecto, chico como en un servidor de 1 CPU.
        asyncio.get_running_loop().set_default_executor(
            concurrent.futures.ThreadPoolExecutor(2))
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            lentos = await asyncio.gather(*[_subir(c) for _ in range(4)])
            assert {r.status_code for r in lentos} == {504}
            t0 = time.monotonic()
            r = await c.post("/api/ncm/sugerir",
                             json={"descripcion": "artefacto inventado para la prueba qwz"})
            demora_ncm = time.monotonic() - t0
            assert r.status_code == 200, r.text[:200]
            t0 = time.monotonic()
            await validate_file_upload(
                UploadFile(file=__import__("io").BytesIO(PDF), filename="otro.pdf"), "pdf")
            demora_validar = time.monotonic() - t0
            return demora_ncm, demora_validar

    demora_ncm, demora_validar = asyncio.run(_escenario())
    assert demora_ncm < 1.0, f"/api/ncm/sugerir esperó {demora_ncm:.2f} s detrás de los PDFs lentos"
    assert demora_validar < 1.0, f"validar otro PDF esperó {demora_validar:.2f} s"


def test_gemini_sin_respuesta_no_cuelga_la_sugerencia(monkeypatch):
    monkeypatch.setenv("NCM_GEMINI_TIMEOUT_S", "0.3")
    monkeypatch.setattr(main, "_suggest_ncm_with_gemini",
                        lambda *_a, **_k: (_bloquear(), [{"ncm": "x"}])[1])

    async def _ir():
        transport = httpx.ASGITransport(app=main.app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
            t0 = time.monotonic()
            r = await c.post("/api/ncm/sugerir",
                             json={"descripcion": "artefacto inventado para la prueba qwz"})
            return r, time.monotonic() - t0

    r, demora = asyncio.run(_ir())
    assert r.status_code == 200, r.text[:200]
    assert demora < LENTO_S, f"esperó a Gemini {demora:.2f} s"
