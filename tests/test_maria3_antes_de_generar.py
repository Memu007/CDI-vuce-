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


@pytest.mark.parametrize("procedencia", ["Narnia", "99999", "12", "²", "٢٢٢", "2²2"])
@pytest.mark.parametrize("ruta", ["/generate_maria", "/generate_maria/avisos"])
def test_procedencia_no_reconocida_se_rechaza(client, auth_override, procedencia, ruta):
    r = client.post(ruta, json=_cuerpo(procedencia=procedencia))
    assert r.status_code == 400, r.text
    detalle = r.json()["detail"]
    assert detalle.startswith("Procedencia") and procedencia in detalle
    assert "invalid literal" not in detalle


def _codigos_de_la_pantalla():
    import json
    import pathlib
    import re
    js = (pathlib.Path(__file__).resolve().parents[1] / "proyecto_maria" / "static" / "v2"
          / "paises_maria.js").read_text(encoding="utf-8")
    return [c["code"] for c in json.loads(re.search(r"const COUNTRIES = (\[.*?\]);", js).group(1))]


def test_la_procedencia_acepta_todos_los_paises_de_la_pantalla():
    """Devolución: una sola tabla. Los 309 códigos que ofrece la pantalla
    (TABLA PAISES V.0 25082010.xlsx) son procedencias válidas."""
    from proyecto_maria.core.maria_generator import pais_de_la_tabla
    codigos = _codigos_de_la_pantalla()
    assert len(codigos) == 309
    assert [c for c in codigos if not pais_de_la_tabla(c)] == []


@pytest.mark.parametrize("codigo", ["668", "436", "435", "223", "150", "242", "254", "358"])
def test_procedencias_que_antes_se_rechazaban(client, auth_override, codigo):
    assert f"CARTPAYPRC={codigo}" in _generar(client, procedencia=codigo)["content"]


def test_procedencia_de_item_en_blanco_no_pisa_la_de_la_operacion(client, auth_override):
    items = [dict(ITEM_BASE, estado=2, pais_procedencia="  "), dict(ITEM_BASE, estado=2, procedencia=" ")]
    data = _generar(client, procedencia="UY", items=items)
    assert [ln for ln in data["content"].split("\r\n") if ln.startswith("CARTPAYPRC=")] == \
        ["CARTPAYPRC=225", "CARTPAYPRC=225"]


def test_procedencia_por_codigo_de_la_tabla(client, auth_override):
    assert "CARTPAYPRC=222" in _generar(client, procedencia="222")["content"]


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


@pytest.mark.parametrize("fecha", ["", "   ", "None", "DD/MM/YYYY", "32/13/2025", "mañana", "18/07/202", "18-07-2025",
                                   "05/03/0026", "01/01/0001"])
def test_sin_fecha_valida_no_se_genera(fecha):
    """Devolución: sin una fecha de emisión válida no se genera (como con el
    estado): ni la de hoy, ni vacía, ni el año del IEXT sacado de otro lado."""
    with pytest.raises(ValueError, match="fecha de emisión"):
        generate_maria_txt(items=[dict(ITEM_BASE)], **{**COMUN, "fecha_emision": fecha,
                                                        "sbt_sufijo_valor": SUF_A})


def test_sin_fecha_el_endpoint_da_400_y_no_genera(client, auth_override):
    r = client.post("/generate_maria", json=_cuerpo(fecha_emision=""))
    assert r.status_code == 400, r.text
    assert "fecha de emisión" in r.text
    for hoy in _hoy_o_ayer():
        assert hoy not in r.text


@pytest.mark.parametrize("fecha, sale", [
    ("22/06/2026", "22/06/2026"),
    ("2026-06-22", "22/06/2026"),
    (" 18/07/2025 ", "18/07/2025"),
    ("18/07/25", "18/07/2025"),
    ("1/7/2025", "01/07/2025"),
    ("01/01/69", "01/01/2069"),
])
def test_la_fecha_de_la_factura_sale_en_el_txt(fecha, sale):
    txt = generate_maria_txt(items=[dict(ITEM_BASE)], **{**COMUN, "fecha_emision": fecha,
                                                          "sbt_sufijo_valor": SUF_A})
    assert _fecha_txt(txt) == [sale]


@pytest.mark.parametrize("fecha, anio", [("01/02/2024", "/24"), ("2023-12-31", "/23"), ("05/05/30", "/30")])
def test_el_anio_del_iext_sale_de_la_fecha_valida(fecha, anio):
    txt = generate_maria_txt(items=[dict(ITEM_BASE)], **{**COMUN, "fecha_emision": fecha,
                                                          "sbt_sufijo_valor": SUF_A})
    iext = [ln for ln in txt.split("\r\n") if ln.startswith("IEXT=") and "/" in ln]
    assert iext and all(ln.endswith(anio) for ln in iext), iext


@pytest.mark.parametrize("fecha", ["Fecha 18/07/2025", "Jul/18/2025", "18/07/٢٥"])
def test_texto_suelto_con_barra_no_da_el_anio(fecha):
    with pytest.raises(ValueError, match="fecha de emisión"):
        generate_maria_txt(items=[dict(ITEM_BASE)], **{**COMUN, "fecha_emision": fecha,
                                                        "sbt_sufijo_valor": SUF_A})


def test_sin_fecha_los_avisos_previos_la_piden(client, auth_override):
    r = client.post("/generate_maria/avisos", json=_cuerpo(fecha_emision=""))
    assert r.status_code == 200, r.text
    texto = _texto(r.json()["avisos"])
    assert "fecha de emisión" in texto and "no se genera" in texto
    assert "fecha de emisión" not in _texto(_generar(client)["supuestos"])


def _dias(n):
    return (datetime.now() + timedelta(days=n)).strftime("%d/%m/%Y")


@pytest.mark.parametrize("dias, dice", [(40, "futura"), (-3 * 366, "más de dos años")])
def test_fecha_futura_o_vieja_se_avisa(dias, dice):
    texto = _texto(supuestos_declarados([dict(ITEM_BASE)], fecha_emision=_dias(dias)))
    assert "fecha de emisión" in texto and dice in texto


@pytest.mark.parametrize("dias", [0, -30, -700])
def test_fecha_reciente_no_se_avisa(dias):
    assert "fecha de emisión" not in _texto(supuestos_declarados([dict(ITEM_BASE)], fecha_emision=_dias(dias)))


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
    cuerpo = _cuerpo(fecha_emision="01/01/2020", procedencia=procedencia, gastos_anteriores_fob=gastos,
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


def test_gastos_de_menos_de_un_centavo_no_se_declaran():
    from proyecto_maria.core.maria_generator import gastos_fob_para_el_txt
    assert gastos_fob_para_el_txt("EXW", None, 0.004) is None


GASTOS_INVALIDOS = [float("inf"), float("nan"), -5, 1e308, -float("inf")]


@pytest.mark.parametrize("gastos", GASTOS_INVALIDOS, ids=["inf", "nan", "negativo", "1e308", "-inf"])
@pytest.mark.parametrize("campo, incoterm", [("gastos_anteriores_fob", "EXW"), ("gastos_fob", "DDP")])
@pytest.mark.parametrize("ruta", ["/generate_maria", "/generate_maria/avisos"])
def test_gastos_que_no_son_un_importe_dan_400(client, auth_override, gastos, campo, incoterm, ruta):
    """Devolución: un importe no finito, negativo o absurdo no llega al TXT,
    tampoco por `gastos_fob`: 400 con mensaje propio."""
    r = client.post(ruta, json=_cuerpo(incoterm=incoterm, **{campo: gastos}))
    assert r.status_code == 400, r.text
    assert "Gastos" in r.json()["detail"]


@pytest.mark.parametrize("gastos", GASTOS_INVALIDOS, ids=["inf", "nan", "negativo", "1e308", "-inf"])
def test_el_generador_tampoco_acepta_gastos_invalidos(gastos):
    with pytest.raises(ValueError, match="Gastos"):
        generate_maria_txt(items=[dict(ITEM_BASE)], **{**COMUN, "gastos_fob": gastos,
                                                        "sbt_sufijo_valor": SUF_A})


# --- Revisión de la devolución ---------------------------------------------------

@pytest.mark.parametrize("campo, valor", [("flete", float("inf")), ("flete", -500), ("seguro", float("nan")),
                                          ("seguro", 1e308)])
@pytest.mark.parametrize("ruta", ["/generate_maria", "/generate_maria/avisos"])
def test_flete_o_seguro_que_no_son_un_importe_dan_400(client, auth_override, campo, valor, ruta):
    """Con CIF los gastos salen de flete + seguro: un importe inválido no
    llega al TXT por ese camino."""
    r = client.post(ruta, json=_cuerpo(incoterm="CIF", **{campo: valor}))
    assert r.status_code == 400, r.text
    assert campo.capitalize() in r.json()["detail"]


@pytest.mark.parametrize("campo", ["pais_procedencia", "origen"])
@pytest.mark.parametrize("valor", ["99999", "²", "٢٢٢"])
def test_codigo_raro_en_el_producto_da_400_con_mensaje_propio(client, auth_override, campo, valor):
    r = client.post("/generate_maria", json=_cuerpo(items=[dict(ITEM_BASE, estado=2, **{campo: valor})]))
    assert r.status_code == 400, r.text
    assert "invalid literal" not in r.text and valor in r.text


def test_procedencia_de_item_en_blanco_no_tapa_la_otra_clave(client, auth_override):
    item = dict(ITEM_BASE, estado=2, pais_procedencia="  ", procedencia="PE")
    assert "CARTPAYPRC=222" in _generar(client, procedencia="UY", items=[item])["content"]
    assert "CARTPAYPRC=222" in _generar(client, items=[item])["content"]


def test_gastos_grandes_en_moneda_de_poco_valor_pasan(client, auth_override):
    data = _generar(client, incoterm="EXW", moneda="CLP", gastos_anteriores_fob=1_200_000_000)
    assert _valor(data["content"], "GTOS-ANT-FOB") == ["1200000000.00"]


def test_sin_productos_los_avisos_tambien_piden_la_fecha(client, auth_override):
    r = client.post("/generate_maria/avisos", json=_cuerpo(items=[], fecha_emision=""))
    assert "fecha de emisión" in _texto(r.json()["avisos"])
