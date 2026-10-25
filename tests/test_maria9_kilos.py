"""MARIA-9, punto 4: cuando un renglón es tan chico que sus kilos al
centésimo dan cero, el error nombra ese renglón y no a todos los que van
juntos en el ítem. Datos inventados con la forma de la factura de lonas.
"""
import pytest

from tests.test_maria7_rechazos_24_10 import LONA, _gen


def _renglon(n, peso_kg):
    return dict(LONA, cantidad=10 + n, peso_kg=peso_kg, unidad="kg", unidad_estadistica="01",
                descripcion=f"Lona de PVC {n}", sufijo=f"AA(MARCA)-AI(COLOR {n})-")


@pytest.mark.parametrize("pesos,mensaje", [
    ((300.0, 0.004), "Item 1: el renglón 2 es tan chico que"),
    ((0.004, 300.0), "Item 1: el renglón 1 es tan chico que"),
    ((300.0, 0.004, 0.003), "Item 1: los renglones 2 y 3 son tan chicos que"),
    ((0.004, 300.0, 120.0, 0.003), "Item 1: los renglones 1 y 4 son tan chicos que"),
], ids=["uno_al_final", "uno_al_principio", "dos_al_final", "dos_en_las_puntas"])
def test_el_error_nombra_sólo_los_renglones_chicos(pesos, mensaje):
    with pytest.raises(ValueError) as error:
        _gen([_renglon(n, p) for n, p in enumerate(pesos)])
    assert str(error.value).startswith(mensaje), str(error.value)
