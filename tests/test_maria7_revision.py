"""MARIA-7: lo que encontró la autorrevisión antes de entregar.

Cada caso es un hueco de la primera versión: la revisión volvía a dar vuelta
la fecha, un año de dos cifras se adivinaba, m² escrito de otras formas
caía en 07, una identificación china toda
en números se tomaba por cuenta del banco, y los avisos no anticipaban la
factura larga. Datos inventados.
"""
import io
import json
import re
import subprocess
from pathlib import Path

import pytest

from proyecto_maria import pdf_extractor
from proyecto_maria.core import maria_generator as mg
from tests.test_maria1a_lectura_factura import _pdf_en_blanco
from tests.test_maria7_rechazos_24_10 import LONA, _gen, _pedido, _registrar_con_cuit, _valor

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "proyecto_maria" / "static" / "v2" / "screens"


# ------------------------------------------- la fecha en la revisión


def _normalizar_en_la_revision(fechas):
    """Corre `normalizeDateForInput` de review.js en node, sacada del fuente."""
    fuente = (V2 / "review.js").read_text(encoding="utf-8")
    m = re.search(r"\n(\s*)function normalizeDateForInput\(raw\) \{.*?\n\1\}", fuente, re.S)
    assert m, "no está normalizeDateForInput en review.js"
    codigo = m.group(0) + f"\nconsole.log(JSON.stringify({json.dumps(fechas)}.map(normalizeDateForInput)));"
    salida = subprocess.run(["node", "-e", codigo], check=True, capture_output=True, text=True)
    return json.loads(salida.stdout)


def test_la_revision_respeta_el_orden_que_dejo_el_lector():
    """El lector deja DD/MM/AAAA; la revisión no la vuelve a dar vuelta."""
    assert _normalizar_en_la_revision(
        ["20/10/2026", "07/08/2026", "7/8/2026", "2026/08/07", "2026-8-7"]
    ) == ["20/10/2026", "07/08/2026", "07/08/2026", "07/08/2026", "07/08/2026"]


def test_la_revision_sin_separadores_sigue_como_antes():
    assert _normalizar_en_la_revision(["20261007", "07102026", "", "a confirmar"]) == [
        "07/10/2026", "07/10/2026", "", "a confirmar"]


# ---------------------------------------------- año de dos cifras


@pytest.mark.parametrize("escrita", ["26/08/07", "07/08/26", "26-08-07"])
def test_un_anio_de_dos_cifras_no_se_adivina(escrita):
    fecha, aviso = pdf_extractor._fecha_leida(escrita)
    assert fecha == ""
    assert "tiene el año con dos cifras" in aviso and "no se adivina" in aviso


# --------------------------------------- metro cuadrado, más formas


@pytest.mark.parametrize("escrita", ["㎡", "m^2", "MTK", "m2.", "sq.m", "Sq M", "square meters"])
def test_metro_cuadrado_escrito_de_otras_formas(escrita):
    assert _valor(_gen([dict(LONA, unidad=escrita)]), "CARTUNTDCL") == ["03"]


# ---------------------------------------- identificación del proveedor


@pytest.mark.parametrize("tributaria", [
    "913300007123450010",     # código chino de crédito social, todo en números
    "BR12345678000199",       # con prefijo de país, no es un IBAN
])
def test_una_identificacion_que_parece_cuenta_pero_no_es_sale(tributaria):
    assert not mg.parece_cuenta_bancaria(tributaria)
    assert _valor(_gen(vendedor_id=tributaria), "MCPL").count(f"{tributaria:<40}") == 1


def test_un_iban_valido_sigue_siendo_cuenta_y_uno_con_un_digito_cambiado_no():
    assert mg.parece_cuenta_bancaria("GB82WEST12345698765432")
    assert not mg.parece_cuenta_bancaria("GB83WEST12345698765432")


def test_dieciocho_digitos_que_no_cierran_el_verificador_son_cuenta():
    assert mg.parece_cuenta_bancaria("913300007123450011")


# ------------------------------------------- factura más larga que el campo


def test_la_factura_mas_larga_que_el_campo_se_avisa_antes_de_generar(client):
    larga = "INV-" + "1234567890" * 3
    avisos = mg.supuestos_declarados([dict(LONA)], numero_factura=larga)
    assert any(f"tiene {len(larga)} caracteres y en LDVDREFDOC entran 28" in a for a in avisos)
    _registrar_con_cuit(client, "maria7_factura_larga")
    r = client.post("/generate_maria/avisos", json=dict(_pedido(), numero_factura=larga))
    assert r.status_code == 200, r.text
    assert any("en LDVDREFDOC entran 28" in a for a in r.json()["avisos"])


# --------------------------------------------- kilos con sub-ítems


def test_el_mensaje_de_kilos_con_subitems_dice_como_salir():
    subs = [{"cantidad": 300, "valor_unitario": 1.85}, {"cantidad": 450, "valor_unitario": 1.85}]
    with pytest.raises(ValueError) as e:
        _gen([dict(LONA, unidad="kg", peso_kg=465.125, subitems=subs)])
    assert "con la cantidad igual al kilo neto al centésimo (465.13)" in str(e.value)


# -------------------------------------- la fecha llega con su título


def test_upload_separa_la_pregunta_por_la_fecha(auth_override, client, monkeypatch):
    import proyecto_maria.main as main
    leido = {"documento": {"tipo": "factura_comercial", "operacion": "importacion", "destinacion": ""},
             "operacion": {"fecha_emision": "", "avisos_fecha": ["Fecha de emisión: pregunta."]},
             "items": [{"descripcion": "X", "cantidad": 1, "valor_unitario": 1}]}
    monkeypatch.setattr(main, "lectura_automatica_disponible", lambda: True)
    monkeypatch.setattr(main, "process_pdf", lambda contenido: leido)
    monkeypatch.setattr("proyecto_maria.core.ai_quota.enforce_pdf_quota", lambda usuario: None)
    r = client.post("/upload_pdf/public", files={"file": ("f.pdf", io.BytesIO(_pdf_en_blanco()), "application/pdf")})
    assert r.status_code == 200, r.text
    assert (r.json()["avisos"], r.json()["avisos_fecha"]) == ([], ["Fecha de emisión: pregunta."])


def test_la_pantalla_muestra_la_fecha_con_el_titulo_de_la_factura():
    """El toast se titula «Revisá la factura» si hay algo de la factura."""
    fuente = (V2 / "upload.js").read_text(encoding="utf-8")
    assert "sinLeer.unshift.apply(sinLeer, data.avisos_fecha)" in fuente


# ----------------------------------- la unidad del producto en el HTML


def test_la_unidad_del_producto_se_escapa_en_la_lista():
    fuente = (V2 / "despachante.js").read_text(encoding="utf-8")
    assert "'<option value=\"' + CDI.escapeHtml(v) + '\"'" in fuente
