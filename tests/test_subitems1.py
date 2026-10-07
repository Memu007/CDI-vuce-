"""SUBITEMS-1: los controles de siempre valen para cada subítem, y el error
dice qué subítem falla. Un producto agrupado no lleva subítems (el grupo es
una sola línea del TXT y sus subítems no tendrían contra qué sumar).
"""
import pytest

from tests.test_maria_subitems import ITEM_BASE, SUF_A, SUF_B, _generar


def _subs(*pares):
    sufijos = [SUF_A, SUF_B, SUF_A, SUF_B]
    return [{"cantidad": c, "valor_unitario": v, "sufijo": sufijos[n]} for n, (c, v) in enumerate(pares)]


@pytest.mark.parametrize("pares, subitem, dice", [
    # La suma da 6 y 7182, pero un subítem tiene cantidad negativa o cero.
    (((7, 1197), (-1, 1197)), 2, "cantidad"),
    (((6, 1197), (0, 1197)), 2, "cantidad"),
    # Un valor unitario en cero o negativo.
    (((2, 0), (4, 1795.5)), 1, "valor unitario"),
    (((2, -100), (4, 1845.5)), 1, "valor unitario"),
])
def test_el_error_dice_que_subitem_falla(pares, subitem, dice):
    with pytest.raises(ValueError) as e:
        _generar({"subitems": _subs(*pares)})
    assert f"sub-ítem {subitem}" in str(e.value) and dice in str(e.value), str(e.value)


def test_el_error_llega_a_la_pantalla(client, auth_override):
    item = dict(ITEM_BASE, estado=2, subitems=_subs((7, 1197), (-1, 1197)))
    r = client.post("/generate_maria", json={
        "operation_id": "OP1", "items": [item], "fecha_emision": "22/06/2026", "sbt_sufijo_valor": SUF_A,
        "moneda": "DOL", "incoterm": "EXW", "comprador_cuit": "30999999995"})
    assert r.status_code == 400, r.text
    assert "sub-ítem 2" in r.text, r.text


def test_un_producto_agrupado_no_lleva_subitems():
    otro = dict(ITEM_BASE, descripcion="Otro equipo de demostracion", cantidad=2, grupo_id=1)
    with pytest.raises(ValueError, match="Grupo 1.*sub-ítems"):
        from tests.test_maria_subitems import COMUN
        from proyecto_maria.core.maria_generator import generate_maria_txt
        generate_maria_txt(items=[dict(ITEM_BASE, grupo_id=1, subitems=_subs((2, 1197), (4, 1197))), otro],
                           **COMUN, sbt_sufijo_valor=SUF_A)


def test_los_subitems_validos_siguen_generando():
    txt = _generar({"subitems": _subs((2, 1197), (4, 1197))})
    assert "CARTSBITEM=S" in txt and txt.count("[SBT]") == 2


# --- Revisión adversaria ---------------------------------------------------

@pytest.mark.parametrize("pares", [((9.996, 1), (0.004, 1)), ((0.3333, 3), (0.3333, 3), (0.3334, 3))])
def test_una_cantidad_con_mas_de_dos_decimales_no_sale_redondeada(pares):
    """El TXT declara la cantidad del subítem con dos decimales: 0,004 saldría
    0,00 y tres de 0,3333 sumarían 0,99 contra 1,00."""
    cantidad = round(sum(c for c, _ in pares), 6)
    with pytest.raises(ValueError, match="sub-ítem .*dos decimales"):
        _generar({"cantidad": cantidad, "valor_unitario": pares[0][1], "subitems": _subs(*pares)})


def _pedir(client, subitems, **extra):
    item = dict(ITEM_BASE, estado=2, subitems=subitems)
    return client.post("/generate_maria", json={
        "operation_id": "OP1", "items": [item], "fecha_emision": "22/06/2026", "sbt_sufijo_valor": SUF_A,
        "moneda": "DOL", "incoterm": "EXW", "comprador_cuit": "30999999995", **extra})


@pytest.mark.parametrize("sufijo", ["CSBTSVL=S2", "S2\nX", "A" * 121])
def test_el_error_del_sufijo_dice_que_subitem(client, auth_override, sufijo):
    subs = _subs((2, 1197), (4, 1197))
    subs[1]["sufijo"] = sufijo
    r = _pedir(client, subs)
    assert r.status_code == 400, r.text
    assert "sub-ítem 2" in r.text, r.text


@pytest.mark.parametrize("subitems", [[1], "abc", [{"cantidad": 6, "valor_unitario": 1197, "sufijo": 5}]])
def test_un_pedido_mal_armado_da_400_y_no_500(client, auth_override, subitems):
    r = _pedir(client, subitems)
    assert r.status_code == 400, r.text


# --- Devolución (PARA-DEV-2.md, punto 7) -----------------------------------

@pytest.mark.parametrize("subitems", [5, True, 3.5, {"cantidad": 6}])
def test_subitems_que_no_son_una_lista_dan_400_y_no_500(client, auth_override, subitems):
    """Los controles de antes de generar corren primero y no pueden reventar
    con la forma del pedido: el control de forma dice qué ítem está mal."""
    r = _pedir(client, subitems)
    assert r.status_code == 400, r.text
    assert "Item 1" in r.text and "sub-ítems" in r.text, r.text


@pytest.mark.parametrize("subitems", [5, True])
def test_la_validacion_no_revienta_con_subitems_raros(client, auth_override, subitems):
    item = dict(ITEM_BASE, estado=2, subitems=subitems)
    r = client.post("/api/validate/smart", json={
        "items": [item], "operacion": {"moneda": "DOL", "incoterm": "EXW", "comprador_cuit": "30999999995"}})
    assert r.status_code == 200, r.text


# --- Devolución (punto 10): el error cae bajo su sub-ítem ------------------

def _con_un_grupo_antes(subitems):
    """Dos productos agrupados (una línea del TXT) y, tercero en la
    pantalla, el producto partido en sub-ítems: segunda línea del TXT."""
    a = dict(ITEM_BASE, descripcion="Equipo agrupado uno", cantidad=1, valor_unitario=10, grupo_id=1)
    b = dict(ITEM_BASE, descripcion="Equipo agrupado dos", cantidad=1, valor_unitario=10, grupo_id=1)
    return [a, b, dict(ITEM_BASE, subitems=subitems)]


@pytest.mark.parametrize("pares", [((7, 1197), (-1, 1197)), ((2, 1197), (4, 0)), ((2, 1197), (3.996, 1197))])
def test_el_error_del_subitem_dice_el_numero_de_la_pantalla(pares):
    """Con un grupo antes, «Item 3» es el producto de la pantalla, no la
    línea 2 del TXT: la pantalla lo pone bajo ese sub-ítem."""
    from tests.test_maria_subitems import COMUN
    from proyecto_maria.core.maria_generator import generate_maria_txt
    with pytest.raises(ValueError) as e:
        generate_maria_txt(items=_con_un_grupo_antes(_subs(*pares)), **COMUN, sbt_sufijo_valor=SUF_A)
    assert str(e.value).startswith("Item 3, sub-ítem 2: "), str(e.value)


def test_el_error_del_sufijo_del_endpoint_usa_el_mismo_numero(client, auth_override):
    subs = _subs((2, 1197), (4, 1197))
    subs[1]["sufijo"] = "CSBTSVL=S2"
    items = [dict(it, estado=2) for it in _con_un_grupo_antes(subs)]
    r = client.post("/generate_maria", json={
        "operation_id": "OP1", "items": items, "fecha_emision": "22/06/2026", "sbt_sufijo_valor": SUF_A,
        "moneda": "DOL", "incoterm": "EXW", "comprador_cuit": "30999999995"})
    assert r.status_code == 400 and r.json()["detail"].startswith("Item 3, sub-ítem 2: "), r.text
