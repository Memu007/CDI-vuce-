"""MARIA-5, punto 2 (M9): las cuentas del TXT cierran al centavo.

El flete y el seguro se reparten entre los ítems de modo que la suma de los
ítems dé exactamente el de la carátula (antes: FOB 100, 100 y 400 con flete 10
daban 1,67 + 1,67 + 6,67 = 10,01). FOB, seguro, flete y base imponible de cada
ítem cierran entre sí, con el mismo redondeo (al centavo, mitad hacia arriba).
"""
import random
import re
from decimal import Decimal

import pytest

from tests.test_generar_maria_txt import _gen


def _item(fob, cantidad=1, **extra):
    return dict({"pieza": "84713012", "descripcion": "Equipo de prueba generico", "cantidad": cantidad,
                 "valor_unitario": fob / cantidad, "peso_unitario": 1, "origen": "CN"}, **extra)


def _campo(txt, clave):
    return [Decimal(v) for v in re.findall(rf"^{clave}=(\S+)", txt, re.M)]


def _cierra(txt):
    for item, cabecera in (("MARTFOB", "MDDTFOB"), ("MARTFLE", "MDDTFLE"), ("MARTASS", "MDDTASS")):
        assert sum(_campo(txt, item)) == _campo(txt, cabecera)[0], (item, _campo(txt, item))
    for fob, fle, ass, base in zip(*(_campo(txt, c) for c in ("MARTFOB", "MARTFLE", "MARTASS", "MARTBASIMP"))):
        assert fob + fle + ass == base


def test_el_flete_de_diez_suma_diez():
    txt = _gen("OP_CENT", [_item(100), _item(100), _item(400)], flete=10, seguro=10)
    assert _campo(txt, "MARTFLE") == [Decimal("1.67"), Decimal("1.66"), Decimal("6.67")]
    _cierra(txt)


@pytest.mark.parametrize("semilla", range(40))
def test_cualquier_reparto_cierra(semilla):
    azar = random.Random(semilla)
    items = [_item(round(azar.uniform(0.01, 5000), 2), cantidad=azar.randint(1, 7))
             for _ in range(azar.randint(1, 9))]
    txt = _gen("OP_AZAR", items, flete=round(azar.uniform(0, 999), 2), seguro=round(azar.uniform(0, 99), 2))
    _cierra(txt)


def test_un_grupo_cierra_contra_la_cabecera():
    items = [_item(10.005, grupo_id=1), _item(10.005, grupo_id=1), _item(0.333, cantidad=3)]
    txt = _gen("OP_GRUPO", items, flete=1, seguro=1)
    _cierra(txt)


def test_el_redondeo_es_mitad_hacia_arriba():
    """2,675 en binario es 2,67499…: con :.2f salía 2,67."""
    txt = _gen("OP_MITAD", [_item(2.675)], flete=0.125, seguro=0)
    assert _campo(txt, "MARTFOB") == [Decimal("2.68")]
    assert _campo(txt, "MDDTFLE") == [Decimal("0.13")]


def test_sin_fob_no_se_reparte_ni_se_rompe():
    txt = _gen("OP_CERO", [_item(0.001)], flete=5, seguro=0)
    assert _campo(txt, "MARTFOB") == [Decimal("0.00")]


@pytest.mark.parametrize("campo, valor", [("valor_unitario", float("nan")), ("valor_total", float("inf")),
                                           ("cantidad", float("nan"))])
def test_un_importe_que_no_es_numero_no_llega_al_txt(campo, valor):
    """Antes salía `MARTFOB=nan` en el TXT."""
    with pytest.raises(ValueError, match="no válido"):
        _gen("OP_NAN", [_item(5, **{campo: valor})])


def test_la_validacion_muestra_el_fob_del_txt():
    """El mismo redondeo en la pantalla de validación que en el TXT."""
    from proyecto_maria.core.validations import run_smart_validations
    from proyecto_maria.models.operations import Item
    filas = [_item(0.335), _item(0.335), _item(2.675)]
    txt = _gen("OP_VAL", filas)
    items = [Item(pieza="84713012", descripcion=f["descripcion"], origen="CN", cantidad=f["cantidad"],
                  valor_unitario=f["valor_unitario"], peso_unitario=1) for f in filas]
    total = run_smart_validations(items)["estadisticas"]["total_valor_usd"]
    assert Decimal(str(total)) == _campo(txt, "MDDTFOB")[0] == Decimal("3.36")
