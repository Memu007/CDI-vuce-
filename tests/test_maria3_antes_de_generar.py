"""MARIA-3: avisos antes de generar, gastos anteriores al FOB, procedencia y
fecha de emisión.

- Gastos anteriores al FOB: con EXW, FCA y FAS se declaran en `GTOS-ANT-FOB`
  (respuesta 6 del despachante; nota del SIM; el archivo real de 2026 trae
  `GTOS-ANT-FOB=150.00` con EXW). El campo de la pantalla ahora llega al TXT.
- Procedencia: se carga por operación (Código Aduanero, art. 15: sale del
  documento de transporte). El archivo real de 2025 trae origen 200 y
  procedencia 222.
- Fecha de emisión: la de la factura; si no se leyó, vacía y con aviso, nunca
  la de hoy.
- Los avisos se piden antes de generar (`/generate_maria/avisos`).
- Flete o seguro «N/A», «-», «FREE», «included», «Prepaid» y país «Unknown» o
  «?» no son datos sin leer.
"""
import os
from datetime import datetime, timedelta

import pytest

from proyecto_maria.core.maria_generator import (
    INCOTERMS_VALIDOS,
    generate_maria_txt,
    supuestos_declarados,
    validate_for_kit_maria,
)
from tests.test_generar_maria_txt import GOLDEN_INPUTS, _GOLDEN_PATH
from tests.test_maria4_despachante import _valor
from tests.test_maria_subitems import COMUN, ITEM_BASE, REFERENCIA, SUF_A, SUF_B


def _cuerpo(**kw):
    base = dict(
        operation_id="002720126", items=[dict(ITEM_BASE, estado=2)],
        incoterm="EXW", flete=365.0, seguro=75.47, fecha_emision="22/06/2026",
        aduana_codigo="073", sbt_sufijo_valor=SUF_A,
        banco_bcra="191", empresa_digitalizacion="PSAD01", iva_adicional="NO_VALIDA",
    )
    base.update(kw)
    return base


def _generar(client, **kw):
    r = client.post("/generate_maria", json=_cuerpo(**kw))
    assert r.status_code == 200, r.text
    return r.json()


def _texto(avisos):
    return " | ".join(avisos).lower()


# --- Gastos anteriores al FOB --------------------------------------------------

@pytest.mark.parametrize("incoterm", ["EXW", "FCA", "FAS"])
def test_gastos_anteriores_de_la_pantalla_llegan_al_txt(client, auth_override, incoterm):
    data = _generar(client, incoterm=incoterm, gastos_anteriores_fob=150)
    assert _valor(data["content"], "GTOS-ANT-FOB") == ["150.00"]
    assert _valor(data["content"], "GTOS-POS-FOB") == []
    assert "gastos a fob" not in _texto(data["supuestos"])


def test_el_archivo_real_de_2026_sale_igual_con_los_gastos_de_la_pantalla(client, auth_override):
    """Los 150 de gastos anteriores al FOB, cargados en la pantalla, salen como
    en el archivo real; los bloques de productos siguen idénticos."""
    from tests.test_maria_subitems import _bloques_sbt

    subitems = [
        {"cantidad": 2, "valor_unitario": 1197.00, "sufijo": SUF_A},
        {"cantidad": 4, "valor_unitario": 1197.00, "sufijo": SUF_B},
    ]
    data = _generar(client, items=[dict(ITEM_BASE, estado=2, subitems=subitems)],
                    gastos_anteriores_fob=150)
    real = open(REFERENCIA, encoding="utf-8").read()
    assert _valor(data["content"], "GTOS-ANT-FOB") == _valor(real, "GTOS-ANT-FOB") == ["150.00"]
    assert _bloques_sbt(data["content"]) == _bloques_sbt(real)


@pytest.mark.parametrize("incoterm", ["FOB", "CIF", "DDP"])
def test_gastos_anteriores_con_otra_condicion_no_van_y_se_avisa(client, auth_override, incoterm):
    data = _generar(client, incoterm=incoterm, gastos_anteriores_fob=150)
    assert "150.00" not in [m for m in _valor(data["content"], "GTOS-ANT-FOB")
                            + _valor(data["content"], "GTOS-POS-FOB")]
    assert _valor(data["content"], "GTOS-ANT-FOB") == []
    texto = _texto(data["supuestos"])
    assert "gastos anteriores" in texto and incoterm.lower() in texto and "no van al txt" in texto


@pytest.mark.parametrize("gastos", [None, 0])
def test_exw_sin_gastos_anteriores_no_inventa_y_avisa(client, auth_override, gastos):
    data = _generar(client, incoterm="FCA", gastos_anteriores_fob=gastos)
    assert _valor(data["content"], "GTOS-ANT-FOB") == []
    texto = _texto(data["supuestos"])
    assert "gastos anteriores a fob" in texto and "fca" in texto


def test_fas_es_una_condicion_valida():
    assert "FAS" in INCOTERMS_VALIDOS
    item = dict(ITEM_BASE, incoterm="FAS", descripcion="Equipo de demostracion")
    errores, _ = validate_for_kit_maria([item])
    assert not [e for e in errores if "Incoterm" in e]


def test_gastos_fob_explicito_sigue_mandando(client, auth_override):
    """El campo viejo `gastos_fob` (explícito) no cambia de significado."""
    data = _generar(client, incoterm="DDP", gastos_fob=99, gastos_anteriores_fob=150)
    assert _valor(data["content"], "GTOS-POS-FOB") == ["99.00"]


# --- Procedencia ------------------------------------------------------------------

def test_procedencia_por_operacion_llega_a_cada_producto(client, auth_override):
    data = _generar(client, procedencia="UY",
                    items=[dict(ITEM_BASE, estado=2), dict(ITEM_BASE, estado=2, pieza="2")],
                    sbt_sufijo_valor=SUF_A)
    lineas = [ln for ln in data["content"].split("\r\n") if ln.startswith("CARTPAYPRC=")]
    assert lineas == ["CARTPAYPRC=225", "CARTPAYPRC=225"]
    assert "procedencia" not in _texto(data["supuestos"])


def test_la_procedencia_del_producto_gana_sobre_la_de_la_operacion(client, auth_override):
    data = _generar(client, procedencia="UY",
                    items=[dict(ITEM_BASE, estado=2, pais_procedencia="PE")])
    assert "CARTPAYPRC=222" in data["content"]


def test_procedencia_no_reconocida_se_rechaza(client, auth_override):
    r = client.post("/generate_maria", json=_cuerpo(procedencia="Narnia"))
    assert r.status_code == 400, r.text
    assert "Procedencia" in r.text and "Narnia" in r.text


def test_sin_procedencia_sigue_igual_al_origen_y_se_avisa(client, auth_override):
    data = _generar(client)
    assert "CARTPAYPRC=310" in data["content"]
    assert "procedencia" in _texto(data["supuestos"])


def test_el_archivo_real_de_2025_sale_identico_con_la_procedencia_de_la_pantalla(client, auth_override):
    """Origen 200 y procedencia 222 (Perú) cargada por operación: el archivo
    sale entero igual al real."""
    item = {k: v for k, v in GOLDEN_INPUTS["items"][0].items() if k != "pais_procedencia"}
    cuerpo = dict(GOLDEN_INPUTS, items=[item], procedencia="PE")
    r = client.post("/generate_maria", json=cuerpo)
    assert r.status_code == 200, r.text
    with open(_GOLDEN_PATH, "r", newline="") as f:
        assert r.json()["content"] == f.read()


# --- Fecha de emisión ------------------------------------------------------------

def _fecha_txt(txt):
    return _valor(txt, "FECHAEMISIONFACT")


def _hoy_o_ayer():
    hoy = datetime.now()
    return {d.strftime("%d/%m/%Y") for d in (hoy, hoy - timedelta(days=1))}


@pytest.mark.parametrize("fecha", ["", "   ", "None", "DD/MM/YYYY", "32/13/2025", "mañana", "1/7/2025", "18/07/202"])
def test_sin_fecha_leida_sale_vacia_nunca_la_de_hoy(fecha):
    txt = generate_maria_txt(items=[dict(ITEM_BASE)], **{**COMUN, "fecha_emision": fecha,
                                                          "sbt_sufijo_valor": SUF_A})
    assert _fecha_txt(txt) == [""]
    for hoy in _hoy_o_ayer():
        assert hoy not in txt


@pytest.mark.parametrize("fecha, sale", [
    ("22/06/2026", "22/06/2026"),
    ("2026-06-22", "22/06/2026"),
    (" 18/07/2025 ", "18/07/2025"),
    ("18/07/25", "18/07/2025"),
])
def test_la_fecha_de_la_factura_sale_en_el_txt(fecha, sale):
    txt = generate_maria_txt(items=[dict(ITEM_BASE)], **{**COMUN, "fecha_emision": fecha,
                                                          "sbt_sufijo_valor": SUF_A})
    assert _fecha_txt(txt) == [sale]


def test_sin_fecha_se_avisa(client, auth_override):
    data = _generar(client, fecha_emision="")
    texto = _texto(data["supuestos"])
    assert "fecha de emisión" in texto and "vacía" in texto
    assert "fecha de emisión" not in _texto(_generar(client)["supuestos"])


def test_supuestos_avisan_una_fecha_que_no_es_fecha():
    texto = _texto(supuestos_declarados([dict(ITEM_BASE)], fecha_emision="None"))
    assert "fecha de emisión" in texto


# --- Los avisos, antes de generar ----------------------------------------------

def test_los_avisos_se_piden_antes_de_generar(client, auth_override):
    cuerpo = _cuerpo(fecha_emision="", incoterm="FCA", sbt_sufijo_valor="")
    r = client.post("/generate_maria/avisos", json=cuerpo)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "content" not in data and "download_url" not in data
    texto = _texto(data["avisos"])
    assert "fecha de emisión" in texto
    assert "gastos anteriores a fob" in texto
    assert "procedencia" in texto


@pytest.mark.parametrize("gastos, procedencia", [(None, ""), (150, "PE")])
def test_los_avisos_previos_son_los_mismos_que_al_generar(client, auth_override, gastos, procedencia):
    cuerpo = _cuerpo(fecha_emision="", procedencia=procedencia, gastos_anteriores_fob=gastos,
                     iva_adicional=None, banco_bcra="")
    antes = client.post("/generate_maria/avisos", json=cuerpo).json()["avisos"]
    despues = client.post("/generate_maria", json=cuerpo).json()["warnings"]
    assert antes == despues


def test_los_avisos_previos_no_escriben_archivo(client, auth_override, tmp_path, monkeypatch):
    import proyecto_maria.main as m

    escritos = []
    monkeypatch.setattr(m, "_user_downloads_dir", lambda u: escritos.append(u) or str(tmp_path))
    r = client.post("/generate_maria/avisos", json=_cuerpo())
    assert r.status_code == 200, r.text
    assert escritos == [] and os.listdir(tmp_path) == []


def test_los_avisos_previos_sin_sesion_dan_401(client):
    client.cookies.clear()
    r = client.post("/generate_maria/avisos", json=_cuerpo())
    assert r.status_code == 401, r.text


# --- Sin avisos de más (revisión de MARIA-1c) -----------------------------------

@pytest.mark.parametrize("copia", ["pymupdf", "pdf_directo"])
@pytest.mark.parametrize("operacion", [
    {"flete": "N/A", "seguro": "-"},
    {"flete": "FREE", "seguro": "included"},
    {"flete": "Prepaid", "seguro": " n/a "},
    {"flete": "Included.", "seguro": "free"},
    {"vendedor_pais": "Unknown"},
    {"vendedor_pais": "?"},
], ids=["na_guion", "free_included", "prepaid_na", "mayusculas_punto", "unknown", "pregunta"])
def test_no_aplica_no_es_un_dato_sin_leer(monkeypatch, copia, operacion):
    from tests.test_maria1a_lectura_factura import COPIAS, _leer
    from tests.test_maria1c_avisos_lectura import _factura

    assert copia in COPIAS
    r = _leer(monkeypatch, copia, _factura(**operacion))
    op = r["operacion"]
    assert op["campos_sin_leer"] == []
    assert op["flete"] == 0 and op["seguro"] == 0
    assert op["vendedor_pais"] == ""


@pytest.mark.parametrize("copia", ["pymupdf", "pdf_directo"])
def test_lo_ilegible_se_sigue_marcando(monkeypatch, copia):
    from tests.test_maria1a_lectura_factura import _leer
    from tests.test_maria1c_avisos_lectura import _factura

    r = _leer(monkeypatch, copia, _factura(flete="freight 1.2.3", seguro="N/A 30",
                                           vendedor_pais="Unknown land"))
    assert r["operacion"]["campos_sin_leer"] == ["flete", "seguro", "vendedor_pais"]


@pytest.mark.parametrize("copia", ["pymupdf", "pdf_directo"])
@pytest.mark.parametrize("fecha", [None, ""])
def test_la_fecha_que_no_vino_queda_vacia(monkeypatch, copia, fecha):
    from tests.test_maria1a_lectura_factura import _leer
    from tests.test_maria1c_avisos_lectura import _factura

    r = _leer(monkeypatch, copia, _factura(fecha_emision=fecha))
    assert r["operacion"]["fecha_emision"] == ""
