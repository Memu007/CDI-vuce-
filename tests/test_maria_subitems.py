"""Sub-ítems: un ítem partido en varios modelos bajo la misma NCM.

Contexto (2026-07-26): comparando contra un MARIA.TXT real apareció que una
factura puede declarar un ítem partido en varios sub-ítems —por ejemplo 2
unidades de un modelo y 4 de otro, misma NCM— cada uno con su cantidad, su
valor unitario y su FOB. El generador emitía siempre un solo `[SBT]` sin
montos, así que esa factura no se podía declarar como corresponde.

El manual de PreDespacho lo llama "separar en Ítem o no": es una decisión del
despachante. Por eso los sub-ítems son opcionales y, sin ellos, el generador
sigue emitiendo exactamente lo de antes.

Referencia: `tests/fixtures/maria_golden_subitems_anon.TXT`.
"""

import os
import re

import pytest

from proyecto_maria.core.maria_generator import generate_maria_txt

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
REFERENCIA = os.path.join(FIXTURES, "maria_golden_subitems_anon.TXT")

SUF_A = ("AA(DemoPouchs)-AB(MODELO-A 001)-ZA(016384)-ZB(004400)-ZC(000256)"
         "-ZD(000001)-CA00-NA00-NB00-NC01-ND01-NE00-NF01-")
SUF_B = SUF_A.replace("MODELO-A 001", "MODELO-B 002")

ITEM_BASE = {
    "pieza": "1",
    "descripcion": "Equipo de demostracion para prueba",
    "ncm": "84714900100D",
    "cantidad": 6,
    "valor_unitario": 1197.00,
    "peso_kg": 33.0,
    "origen": "310",
    "unidad": "07",
}

COMUN = dict(
    operation_id="002720126",
    moneda="DOL",
    incoterm="EXW",
    flete=365.00,
    seguro=75.47,
    fecha_emision="22/06/2026",
    aduana_codigo="073",
)


def _generar(item_extra=None, **kw):
    item = dict(ITEM_BASE)
    if item_extra:
        item.update(item_extra)
    return generate_maria_txt(items=[item], **{**COMUN, **kw})


def _bloques_sbt(txt: str):
    """Devuelve los bloques [SBT] como listas de líneas, normalizadas."""
    partes = txt.replace("\r\n", "\n").split("[SBT]")[1:]
    return [
        [ln.strip() for ln in p.split("[")[0].strip().split("\n") if ln.strip()]
        for p in partes
    ]


# ====================================================================
# Contra la referencia real
# ====================================================================

def test_los_sbt_salen_iguales_a_la_referencia_real():
    """El corazón de esta funcionalidad: reproducir el archivo que anda."""
    subitems = [
        {"cantidad": 2, "valor_unitario": 1197.00, "sufijo": SUF_A},
        {"cantidad": 4, "valor_unitario": 1197.00, "sufijo": SUF_B},
    ]
    generado = _bloques_sbt(_generar({"subitems": subitems}))
    esperado = _bloques_sbt(open(REFERENCIA, encoding="utf-8").read())

    assert generado == esperado, "los bloques [SBT] no coinciden con el archivo real"


def test_marca_el_item_como_partido():
    subitems = [
        {"cantidad": 2, "valor_unitario": 1197.00, "sufijo": SUF_A},
        {"cantidad": 4, "valor_unitario": 1197.00, "sufijo": SUF_B},
    ]
    txt = _generar({"subitems": subitems})
    assert "CARTSBITEM=S" in txt


# ====================================================================
# Sin sub-ítems: nada cambia respecto de antes
# ====================================================================

def test_sin_subitems_sigue_saliendo_un_solo_bloque():
    txt = _generar(sbt_sufijo_valor="AA(Demo)-CA00-")
    bloques = _bloques_sbt(txt)
    assert len(bloques) == 1
    assert "ISBT=0000" in bloques[0]
    assert "CARTSBITEM=N" in txt
    # Sin sub-ítems no se declaran montos por sufijo.
    assert not any(ln.startswith("MSBTFOB") for ln in bloques[0])


def test_sin_subitems_y_sin_sufijo_sigue_siendo_error():
    with pytest.raises(ValueError, match="sufijo de valor"):
        _generar()


# ====================================================================
# Las cuentas tienen que cerrar (si no, la aduana rechaza)
# ====================================================================

def test_cantidades_que_no_suman_el_total_se_rechazan():
    subitems = [
        {"cantidad": 2, "valor_unitario": 1197.00, "sufijo": SUF_A},
        {"cantidad": 3, "valor_unitario": 1197.00, "sufijo": SUF_B},  # 5, no 6
    ]
    with pytest.raises(ValueError, match="cantidades de los sub-ítems"):
        _generar({"subitems": subitems})


def test_valores_que_no_suman_el_total_se_rechazan():
    subitems = [
        {"cantidad": 2, "valor_unitario": 1000.00, "sufijo": SUF_A},
        {"cantidad": 4, "valor_unitario": 1197.00, "sufijo": SUF_B},
    ]
    with pytest.raises(ValueError, match="valores de los sub-ítems"):
        _generar({"subitems": subitems})


def test_subitem_sin_sufijo_se_rechaza():
    subitems = [
        {"cantidad": 2, "valor_unitario": 1197.00, "sufijo": SUF_A},
        {"cantidad": 4, "valor_unitario": 1197.00},
    ]
    with pytest.raises(ValueError, match="falta el sufijo"):
        _generar({"subitems": subitems})


def test_las_cuentas_del_archivo_generado_cierran():
    """Suma de los FOB de sub-ítems == FOB del ítem."""
    subitems = [
        {"cantidad": 1, "valor_unitario": 1197.00, "sufijo": SUF_A},
        {"cantidad": 5, "valor_unitario": 1197.00, "sufijo": SUF_B},
    ]
    # El TXT usa fin de línea de Windows (\r\n), como pide el Kit MARIA.
    txt = _generar({"subitems": subitems}).replace("\r\n", "\n")
    fobs = [float(m) for m in re.findall(r"^MSBTFOB=([\d.]+)$", txt, re.MULTILINE)]
    art_fob = float(re.search(r"^MARTFOB=([\d.]+)$", txt, re.MULTILINE).group(1))
    assert abs(sum(fobs) - art_fob) < 0.01

    cants = [float(m) for m in re.findall(r"^QSBTUNTDCL=([\d.]+)$", txt, re.MULTILINE)]
    art_cant = float(re.search(r"^QARTUNTDCL=([\d.]+)$", txt, re.MULTILINE).group(1))
    assert abs(sum(cants) - art_cant) < 0.01
