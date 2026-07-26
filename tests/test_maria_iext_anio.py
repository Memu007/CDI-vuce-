"""El año del campo IEXT sale de la factura, no está escrito a mano.

Hallazgo (2026-07-26, comparando contra un MARIA.TXT real de 2026): el
generador armaba `IEXT=00272-01/25` con el "25" fijo en el código. El TXT salía
igual de válido a la vista —no falla ninguna validación nuestra— pero toda
declaración de 2026 en adelante llevaba el año equivocado. Un error de este
tipo aparece recién en la aduana, con el nombre del cliente encima.

Referencias reales (anonimizadas) en `tests/fixtures/`:
  - `maria_golden_anon.TXT`          → factura 18/07/2025 → `IEXT=00099-01/25`
  - `maria_golden_subitems_anon.TXT` → factura 22/06/2026 → `IEXT=00272-01/26`
"""

import os
import re
from datetime import datetime

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
    items=[ITEM],
    moneda="DOL",
    incoterm="EXW",
    flete=365.00,
    seguro=75.47,
    sbt_sufijo_valor="AA(Demo)-CA00-",
)


def _iext_del_art(txt: str) -> str:
    """Devuelve el IEXT del bloque [ART] (el de [SBT] tiene otro formato)."""
    art = txt.split("[ART]", 1)[1].split("[CPL]", 1)[0]
    return re.search(r"^IEXT=(.+)$", art, re.MULTILINE).group(1).strip()


def test_anio_sale_de_la_fecha_de_factura():
    txt = generate_maria_txt(operation_id="002720126",
                             fecha_emision="22/06/2026", **BASE)
    assert _iext_del_art(txt) == "00272-01/26"


def test_factura_de_otro_anio_no_arrastra_el_anterior():
    """El caso que rompía: 2025 hardcodeado servía por casualidad en 2025."""
    txt = generate_maria_txt(operation_id="000999001",
                             fecha_emision="18/07/2025", **BASE)
    assert _iext_del_art(txt) == "00099-01/25"


def test_sin_fecha_de_factura_usa_el_anio_actual():
    txt = generate_maria_txt(operation_id="002720126", **BASE)
    esperado = datetime.now().strftime("%y")
    assert _iext_del_art(txt) == f"00272-01/{esperado}"


def test_fecha_rara_no_rompe_la_generacion():
    """Si la fecha viene ilegible, cae al año actual en vez de explotar."""
    txt = generate_maria_txt(operation_id="002720126",
                             fecha_emision="fecha ilegible", **BASE)
    assert _iext_del_art(txt).endswith("/" + datetime.now().strftime("%y"))


def test_las_referencias_reales_son_coherentes():
    """Las dos referencias tienen que cumplir la regla que dice el test.

    Si mañana alguien agrega otra referencia con otro criterio de año, este
    test avisa que la regla ya no es única.
    """
    casos = [
        ("maria_golden_anon.TXT", "18/07/2025", "/25"),
        ("maria_golden_subitems_anon.TXT", "22/06/2026", "/26"),
    ]
    for nombre, fecha, sufijo in casos:
        contenido = open(os.path.join(FIXTURES, nombre), encoding="utf-8").read()
        assert f"MCPL={fecha}" in contenido.replace("\r\n", "\n"), nombre
        assert _iext_del_art(contenido).endswith(sufijo), nombre
