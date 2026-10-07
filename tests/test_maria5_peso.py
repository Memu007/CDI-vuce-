"""MARIA-5, punto 1 (M1): QARTKGRNET es el peso neto total de la línea.

Prueba: respuesta 3 del despachante (PREGUNTAS-DESPACHANTE.md: «el peso se
declara por cada ítem o subítem») y el archivo real de 2026 (6 equipos, 33 kg).
`peso_kg`, si viene, ya es el total de la línea (así lo mandan la v1 y los
archivos reales); si no viene, el total es `peso_unitario` × cantidad (lo que
manda la pantalla v2 y lo que ya muestra la validación).
"""
import re

import pytest

from tests.test_maria_subitems import ITEM_BASE, SUF_A
from tests.test_generar_maria_txt import _gen


def _pesos(txt):
    return re.findall(r"^QARTKGRNET=(\S+)", txt, re.M)


def test_diez_notebooks_de_dos_kilos_y_medio_declaran_25():
    txt = _gen("OP_PESO", [{"pieza": "84713012", "descripcion": "Notebook de prueba", "cantidad": 10,
                            "valor_unitario": 500, "peso_unitario": 2.5, "origen": "CN"}])
    assert _pesos(txt) == ["25.000"]


def test_el_peso_total_que_ya_viene_no_se_multiplica():
    """La v1 manda peso_kg = unitario × cantidad: no se multiplica otra vez."""
    txt = _gen("OP_PESO", [{"pieza": "84713012", "descripcion": "Notebook de prueba", "cantidad": 10,
                            "valor_unitario": 500, "peso_kg": 25, "peso_unitario": 2.5, "origen": "CN"}])
    assert _pesos(txt) == ["25.000"]


def test_un_grupo_suma_el_total_de_cada_linea():
    items = [
        {"pieza": "94037000", "descripcion": "Silla de madera", "cantidad": 2,
         "valor_unitario": 50, "peso_unitario": 3, "origen": "CN", "grupo_id": 1},
        {"pieza": "94037000", "descripcion": "Mesa de madera", "cantidad": 2,
         "valor_unitario": 20, "peso_unitario": 1, "origen": "CN", "grupo_id": 1},
    ]
    assert _pesos(_gen("OP_GRUPO", items)) == ["8.000"]


@pytest.mark.parametrize("item, total", [
    ({"cantidad": 10, "peso_unitario": 2.5}, 25.0),
    ({"cantidad": 6, "peso_kg": 33}, 33.0),
    ({"cantidad": 6, "peso_kg": 33, "peso_unitario": 5.5}, 33.0),
    ({"cantidad": 3, "peso_kg": None, "peso_unitario": 2}, 6.0),
    ({"cantidad": 3, "peso_kg": "", "peso_unitario": 2}, 6.0),
    ({"cantidad": 3}, 0.0),
    ({"cantidad": "4", "peso_unitario": "0.25"}, 1.0),
])
def test_peso_de_la_linea(item, total):
    from proyecto_maria.core.maria_generator import peso_de_la_linea
    assert peso_de_la_linea(item) == pytest.approx(total)


def test_el_pedido_de_la_pantalla_da_lo_que_muestra_la_validacion(client, auth_override):
    """`buildMariaRequest` manda peso_unitario; la validación muestra el total."""
    item = {k: v for k, v in ITEM_BASE.items() if k != "peso_kg"}
    item.update(estado=2, cantidad=6, peso_unitario=5.5)
    pedido = {"operation_id": "OP1", "items": [item], "fecha_emision": "22/06/2026",
              "sbt_sufijo_valor": SUF_A}
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 200, r.text
    assert _pesos(r.json()["content"]) == ["33.000"]
