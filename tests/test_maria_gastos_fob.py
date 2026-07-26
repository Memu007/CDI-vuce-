"""Gastos respecto del FOB: qué campo va según la condición de venta.

Hallazgo (2026-07-26): el generador emitía siempre `GTOS-POS-FOB` con
flete + seguro. En una operación EXW eso es el campo equivocado con el número
equivocado.

La regla (información complementaria del SIM, por el convenio AFIP-BCRA):

  - Condición **EXW** → `GTOS-ANT-FOB`: los gastos hasta el FOB.
  - Grupos **C y D** (CFR, CIF, CPT, CIP, DAP, DPU, DDP) → `GTOS-POS-FOB`:
    la diferencia entre la condición de venta pactada y el FOB declarado.

El importe es esa diferencia, no flete + seguro. Coinciden en CIF; en EXW no.
Por eso se acepta `gastos_fob` explícito, y sin él sólo se calcula en los
grupos C/D, donde la equivalencia se sostiene.

Las dos referencias reales lo confirman:
  - `maria_golden_anon.TXT`          → DDP → `GTOS-POS-FOB`
  - `maria_golden_subitems_anon.TXT` → EXW → `GTOS-ANT-FOB=150.00`
    (y su flete + seguro da 440.47, o sea que NO es esa cuenta)
"""

import os
import re

from proyecto_maria.core.maria_generator import generate_maria_txt

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")

ITEM = {
    "pieza": "1",
    "descripcion": "Equipo de demostracion para prueba",
    "ncm": "84714900100D",
    "cantidad": 6,
    "valor_unitario": 1197.00,
    "peso_kg": 33.0,
    "origen": "310",
    "unidad": "07",
}

BASE = dict(
    operation_id="002720126",
    items=[ITEM],
    flete=365.00,
    seguro=75.47,
    sbt_sufijo_valor="AA(Demo)-CA00-",
    fecha_emision="22/06/2026",
)


def _gastos(txt: str):
    """Devuelve (campo, importe) del [CPL] de gastos, o (None, None)."""
    plano = txt.replace("\r\n", "\n")
    m = re.search(r"CCPL=(GTOS-\w+-FOB)\s*\nMCPL=([\d.]+)", plano)
    return (m.group(1), m.group(2)) if m else (None, None)


# ====================================================================
# Qué campo corresponde a cada condición de venta
# ====================================================================

def test_exw_usa_gastos_anteriores_al_fob():
    campo, importe = _gastos(generate_maria_txt(incoterm="EXW", gastos_fob=150.0, **BASE))
    assert campo == "GTOS-ANT-FOB"
    assert importe == "150.00"


def test_grupo_d_usa_gastos_posteriores_al_fob():
    campo, _ = _gastos(generate_maria_txt(incoterm="DDP", **BASE))
    assert campo == "GTOS-POS-FOB"


def test_grupo_c_usa_gastos_posteriores_al_fob():
    for ic in ("CIF", "CFR", "CPT", "CIP"):
        campo, _ = _gastos(generate_maria_txt(incoterm=ic, **BASE))
        assert campo == "GTOS-POS-FOB", ic


# ====================================================================
# De dónde sale el importe
# ====================================================================

def test_el_importe_explicito_manda_siempre():
    _, importe = _gastos(generate_maria_txt(incoterm="DDP", gastos_fob=99.5, **BASE))
    assert importe == "99.50", "el dato que carga el despachante no se pisa"


def test_en_grupos_c_d_sin_importe_se_calcula_flete_mas_seguro():
    """Comportamiento histórico, que sigue siendo correcto en C/D."""
    _, importe = _gastos(generate_maria_txt(incoterm="DDP", **BASE))
    assert importe == "440.47"  # 365.00 + 75.47


def test_en_exw_sin_importe_no_se_inventa_un_numero():
    """Fuera de C/D no se puede deducir: mejor no declarar que declarar mal."""
    campo, importe = _gastos(generate_maria_txt(incoterm="EXW", **BASE))
    assert campo is None and importe is None


def test_fob_puro_no_declara_gastos():
    """Si la condición ya es FOB no hay diferencia contra el FOB."""
    campo, _ = _gastos(generate_maria_txt(incoterm="FOB", **BASE))
    assert campo is None


# ====================================================================
# Contra las referencias reales
# ====================================================================

def test_las_referencias_reales_respetan_la_regla():
    casos = [
        ("maria_golden_anon.TXT", "DDP", "GTOS-POS-FOB"),
        ("maria_golden_subitems_anon.TXT", "EXW", "GTOS-ANT-FOB"),
    ]
    for nombre, incoterm, campo_esperado in casos:
        contenido = open(os.path.join(FIXTURES, nombre), encoding="utf-8").read()
        assert f"CDDTINCOTE={incoterm}" in contenido.replace("\r\n", "\n"), nombre
        campo, _ = _gastos(contenido)
        assert campo == campo_esperado, nombre


def test_en_el_archivo_real_exw_los_gastos_no_son_flete_mas_seguro():
    """La evidencia de que el importe no se puede calcular: 150 != 440.47."""
    ruta = os.path.join(FIXTURES, "maria_golden_subitems_anon.TXT")
    contenido = open(ruta, encoding="utf-8").read().replace("\r\n", "\n")
    _, importe = _gastos(contenido)
    flete = float(re.search(r"MDDTFLE=([\d.]+)", contenido).group(1))
    seguro = float(re.search(r"MDDTASS=([\d.]+)", contenido).group(1))
    assert float(importe) == 150.00
    assert abs(float(importe) - (flete + seguro)) > 1
