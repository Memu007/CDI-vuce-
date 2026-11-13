"""DOC-1: clasificación sintética en ambas lecturas; cero servicios externos."""
import io

import pytest

from tests.test_maria1a_lectura_factura import COPIAS, _leer, _pdf_en_blanco

FACTURA = {"tipo": "factura_comercial", "operacion": "importacion", "destinacion": "IC04"}


def _respuesta(documento):
    return {"documento": documento, "operacion": {"numero_factura": "SINT-1"},
            "items": [{"descripcion": "Equipo sintético", "cantidad": 1, "valor_unitario": 10}]}


@pytest.mark.parametrize("copia", COPIAS)
def test_factura_conserva_clasificacion(monkeypatch, copia):
    r = _leer(monkeypatch, copia, _respuesta(FACTURA), clasificar=False)
    assert r["documento"] == FACTURA
    assert r["operacion"]["tipo_destinacion"] == "IC04"
    assert len(r["items"]) == 1


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("documento", [None, {}, {"tipo": "desconocido"},
    dict(FACTURA, tipo="despacho_aduanero"), dict(FACTURA, operacion="exportacion"),
    dict(FACTURA, destinacion=" EC02 "), dict(FACTURA, tipo="otro")])
def test_rechazo_no_reintenta_ni_cae_fallback(monkeypatch, copia, documento):
    from proyecto_maria import pdf_extractor as lector
    llamadas = []
    # Contar json.loads equivale a respuestas del modelo efectivamente interpretadas.
    original = lector.json.loads
    def contar(*args, **kwargs):
        llamadas.append(1)
        return original(*args, **kwargs)
    monkeypatch.setattr(lector.json, "loads", contar)
    monkeypatch.setattr(lector, "_fallback_image_extraction", lambda *_: pytest.fail("rechazo cayó a fallback"))
    with pytest.raises(ValueError, match="factura comercial de importación"):
        _leer(monkeypatch, copia, _respuesta(documento), clasificar=False)
    assert len(llamadas) == 1


@pytest.mark.parametrize("documento", [None, {}, dict(FACTURA, tipo="despacho_aduanero"), dict(FACTURA, destinacion="EC02")])
def test_endpoint_rechaza_antes_de_heuristica(auth_override, client, monkeypatch, documento):
    import proyecto_maria.main as main
    monkeypatch.setattr(main, "lectura_automatica_disponible", lambda: True)
    monkeypatch.setattr(main, "process_pdf", lambda _: _respuesta(documento))
    monkeypatch.setattr("proyecto_maria.core.ai_quota.enforce_pdf_quota", lambda _: None)
    monkeypatch.setattr("proyecto_maria.pdf_extractor.detect_vendor_from_text", lambda _: pytest.fail("heurística tras rechazo"))
    r = client.post("/upload_pdf/public", files={"file": ("factura.pdf", io.BytesIO(_pdf_en_blanco()), "application/pdf")})
    assert r.status_code == 422, r.text
    assert r.json()["code"] == "documento_no_admitido"
    assert "items" not in r.json()


@pytest.mark.parametrize("ruta", ["/generate_maria", "/generate_maria/avisos"])
@pytest.mark.parametrize("destinacion, es_exportacion", [
    ("EC02", True), (" ec01 ", True), ("EC99", True),
    # Lo que va adelante del código no lo vuelve de importación.
    *((adelante + "EC01", True) for adelante in
      ("\x00", "\x1f", "\x85", "\t", "\xa0", "\u2028", "\u200b", "\u2060", "\ufeff", "\u200b ", "\u3164", "\uffa0", "-")),
    ("\uff25\uff23" + "01", True),
    pytest.param(" " * 70 + "EC01", True, id="70blancos-EC01"),
    pytest.param("\t" * 70 + "EC01", True, id="70tabs-EC01"),
    ("IC04", False),
])
def test_ec_directa_nunca_entra_a_importacion(auth_override, client, ruta, destinacion, es_exportacion):
    r = client.post(ruta, json={"operation_id": "SINTETICA", "items": [], "tipo_destinacion": destinacion})
    assert ("exportación" in str(r.json().get("detail"))) is es_exportacion, r.text
    # Sin ítems generar da 400 igual; los avisos de una importación salen.
    assert r.status_code == (400 if es_exportacion or ruta == "/generate_maria" else 200), r.text


@pytest.mark.parametrize("destinacion", ["EC02", " ec01 ", "EC99", "\u200bEC01", "\u3164EC01"])
def test_generador_directo_rechaza_ec(destinacion):
    from tests.test_generar_maria_txt import _gen
    with pytest.raises(ValueError, match="exportación"):
        _gen("SINT-EC", [], tipo_destinacion=destinacion)


@pytest.mark.parametrize("copia", COPIAS)
@pytest.mark.parametrize("lugar, campo, valor", [
    ("raiz", "tipo_destinacion", " EC02 "), ("operacion", "tipo_destinacion", "ec01"),
    ("raiz", "tipo_documento", "despacho_aduanero"),
    ("operacion", "tipo_documento", "desconocido")])
def test_clasificacion_contradictoria_se_rechaza(monkeypatch, copia, lugar, campo, valor):
    respuesta = _respuesta(FACTURA)
    (respuesta if lugar == "raiz" else respuesta["operacion"])[campo] = valor
    with pytest.raises(ValueError, match="factura comercial de importación"):
        _leer(monkeypatch, copia, respuesta, clasificar=False)


def test_rechazo_levantado_en_worker_llega_como_422(auth_override, client, monkeypatch):
    import proyecto_maria.main as main
    from proyecto_maria.pdf_extractor import DocumentoNoAdmitido, MENSAJE_DOCUMENTO_NO_ADMITIDO
    monkeypatch.setattr(main, "lectura_automatica_disponible", lambda: True)
    monkeypatch.setattr("proyecto_maria.core.ai_quota.enforce_pdf_quota", lambda _: None)
    def rechazar(_):
        raise DocumentoNoAdmitido(MENSAJE_DOCUMENTO_NO_ADMITIDO)
    monkeypatch.setattr(main, "process_pdf", rechazar)
    r = client.post("/upload_pdf/public", files={"file": ("comercial.pdf", io.BytesIO(_pdf_en_blanco()), "application/pdf")})
    assert r.status_code == 422, r.text
    assert r.json() == {"detail": MENSAJE_DOCUMENTO_NO_ADMITIDO, "code": "documento_no_admitido"}
