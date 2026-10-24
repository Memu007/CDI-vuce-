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


POSICIONES = ["84713012", "84713019", "84714100", "84715010", "84716052",
              "84717012", "84718000", "84719012", "84733041"]


def _campo(txt, clave):
    return [Decimal(v) for v in re.findall(rf"^{clave}=(\S+)", txt, re.M)]


def _cierra(txt):
    for item, cabecera in (("MARTFOB", "MDDTFOB"), ("MARTFLE", "MDDTFLE"), ("MARTASS", "MDDTASS")):
        assert sum(_campo(txt, item)) == _campo(txt, cabecera)[0], (item, _campo(txt, item))
    for fob, fle, ass, base in zip(*(_campo(txt, c) for c in ("MARTFOB", "MARTFLE", "MARTASS", "MARTBASIMP"))):
        assert fob + fle + ass == base
    # Los sub-ítems de un ítem con renglones juntos suman su FOB (MARIA-8).
    bloques = [dict(ln.split("=", 1) for ln in b.strip("\r\n").split("\r\n")[1:])
               for b in txt.split("\r\n\r\n") if b.strip("\r\n").startswith("[")]
    arts = [b for b in bloques if "MARTFOB" in b]
    for art in arts:
        sbts = [b for b in bloques if "MSBTFOB" in b and b["NART"] == art["NART"]]
        if sbts:
            assert sum(Decimal(b["MSBTFOB"]) for b in sbts) == Decimal(art["MARTFOB"]), art["NART"]


def test_el_flete_de_diez_suma_diez():
    # Posiciones distintas: desde MARIA-8 la misma posición va en un solo ítem.
    txt = _gen("OP_CENT", [_item(100), _item(100, pieza="84713019"), _item(400, pieza="84714100")],
               flete=10, seguro=10)
    assert _campo(txt, "MARTFLE") == [Decimal("1.67"), Decimal("1.66"), Decimal("6.67")]
    _cierra(txt)


@pytest.mark.parametrize("semilla", range(40))
def test_cualquier_reparto_cierra(semilla):
    azar = random.Random(semilla)
    # Unitarios con tres decimales: líneas con fracciones de centavo.
    items = []
    for _ in range(azar.randint(1, 9)):
        cantidad = azar.randint(1, 7)
        # Nueve posiciones: hasta nueve ítems, y a veces renglones juntos (MARIA-8).
        items.append(_item(1, cantidad=cantidad, valor_unitario=round(azar.uniform(0.001, 900), 3),
                           pieza=azar.choice(POSICIONES)))
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


@pytest.mark.parametrize("cantidad, unitario, fob", [(3, 3.335, "10.01"), (5, 1.787, "8.94"),
                                                     (25, 9.0498, "226.25"), (5, 4.821, "24.11")])
def test_cantidad_por_unitario_en_decimal_exacto(cantidad, unitario, fob):
    """Revisión adversaria: 3 × 3,335 en binario es 10,00499…; el exacto, 10,005."""
    txt = _gen("OP_EXACTO", [_item(1, cantidad=cantidad, valor_unitario=unitario)])
    assert _campo(txt, "MARTFOB") == _campo(txt, "MDDTFOB") == [Decimal(fob)]


@pytest.mark.parametrize("cantidad, unitario, partes", [(100, 0.0149, [50, 50]), (3, 3.335, [1, 1, 1])])
def test_los_subitems_cierran_sin_rechazar_un_pedido_valido(cantidad, unitario, partes):
    """Revisión adversaria: con MSBTFOB redondeados por separado, un pedido que
    antes salía pasaba a error. El MARTFOB se reparte al centavo."""
    item = _item(1, cantidad=cantidad, valor_unitario=unitario,
                 subitems=[{"cantidad": c, "valor_unitario": unitario, "sufijo": "AA(1)-CA00"} for c in partes])
    txt = _gen("OP_SUB", [item])
    assert sum(_campo(txt, "MSBTFOB")) == _campo(txt, "MARTFOB")[0]


@pytest.mark.parametrize("extra", [{"valor_unitario": 1e27}, {"valor_total": 1e30}, {"valor_total": -2}])
def test_un_importe_imposible_da_error_y_no_500(client, auth_override, extra):
    from tests.test_maria_subitems import ITEM_BASE, SUF_A
    item = {k: v for k, v in ITEM_BASE.items() if k != "subitems"}
    item.update(estado=2, **extra)
    r = client.post("/generate_maria", json={"operation_id": "OP1", "items": [item],
                                             "fecha_emision": "22/06/2026", "sbt_sufijo_valor": SUF_A})
    assert r.status_code == 400, r.text


def test_repartir_no_acepta_negativos():
    from proyecto_maria.core.maria_generator import repartir
    with pytest.raises(ValueError):
        repartir(Decimal("0.10"), [7, -2, -2])
