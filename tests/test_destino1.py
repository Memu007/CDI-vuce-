"""DESTINO-1: el destino de la mercadería sale en el TXT de a pares.

El MARIA hace dos preguntas por ítem y las respuestas van juntas
(`PREGUNTAS-DESPACHANTE.md`, «Respuestas del 2026-10-28»):

| Destino                    | GANANCIASOP3 | IVAADICIONAL1 |
|----------------------------|--------------|---------------|
| Comercialización o reventa | COMERC       | NO_VALIDA     |
| Bien de uso de la empresa  | BDEUSO       | IVAAD2        |
| Bien de uso de una persona | USOPAR       | IVAAD1        |

Se elige por operación, con cambio por ítem; por defecto, comercialización.
El dato que se guarda y viaja sigue siendo el de IVAADICIONAL1
(`iva_adicional`): uno guardado con IVAAD1 se lee como bien de uso de una
persona. Antes `GANANCIASOP3` salía siempre COMERC, y «uso particular» daba
COMERC + IVAAD1, un par que no está en la tabla.
"""
import pytest

from proyecto_maria.core.maria_generator import supuestos_declarados
from tests.test_maria1b_controles import _entorno, _generar  # noqa: F401 (fixture)
from tests.test_maria4_despachante import _cpl, _gen
from tests.test_maria_subitems import ITEM_BASE

PARES = {"NO_VALIDA": "COMERC", "IVAAD2": "BDEUSO", "IVAAD1": "USOPAR"}


def _pares(txt: str) -> dict:
    """{NART: (GANANCIASOP3, IVAADICIONAL1)} de cada ítem. Cada ítem trae una
    sola de cada una, y el par tiene que estar en la tabla."""
    por_item: dict = {}
    for nart, ccpl, mcpl in _cpl(txt):
        if ccpl in ("GANANCIASOP3", "IVAADICIONAL1"):
            por_item.setdefault(nart, {}).setdefault(ccpl, []).append(mcpl)
    pares = {}
    for nart, campos in por_item.items():
        assert len(campos.get("GANANCIASOP3", [])) == 1, f"ítem {nart}: {campos}"
        assert len(campos.get("IVAADICIONAL1", [])) == 1, f"ítem {nart}: {campos}"
        pares[nart] = (campos["GANANCIASOP3"][0], campos["IVAADICIONAL1"][0])
    fuera = {n: p for n, p in pares.items() if PARES.get(p[1]) != p[0]}
    assert not fuera, f"pares fuera de la tabla del despachante: {fuera}"
    return pares


@pytest.mark.parametrize("iva, ganancias", PARES.items())
def test_cada_destino_por_operacion_sale_con_su_par(iva, ganancias):
    assert _pares(_gen(iva_adicional=iva)) == {"0001": (ganancias, iva)}


@pytest.mark.parametrize("iva, ganancias", PARES.items())
def test_cada_destino_por_item_sale_con_su_par(iva, ganancias):
    assert _pares(_gen([dict(ITEM_BASE, iva_adicional=iva)])) == {"0001": (ganancias, iva)}


def test_por_defecto_comercializacion_y_se_avisa():
    assert _pares(_gen()) == {"0001": ("COMERC", "NO_VALIDA")}
    avisos = " ".join(supuestos_declarados([dict(ITEM_BASE)], incoterm="FOB")).lower()
    assert "comercialización o reventa (comerc + no_valida) por defecto" in avisos, avisos


def test_lo_elegido_no_se_avisa_como_por_defecto():
    avisos = " ".join(supuestos_declarados([dict(ITEM_BASE)], incoterm="FOB",
                                           iva_adicional="IVAAD2")).lower()
    assert "destino de la mercadería" not in avisos, avisos


def test_cada_item_cambia_el_de_la_operacion():
    """La operación es de bien de uso de una persona; el segundo ítem es de la
    empresa y el tercero se revende. El primero toma el de la operación."""
    items = [dict(ITEM_BASE), dict(ITEM_BASE, iva_adicional="IVAAD2"),
             dict(ITEM_BASE, iva_adicional="NO_VALIDA")]
    assert _pares(_gen(items, iva_adicional="IVAAD1")) == {
        "0001": ("USOPAR", "IVAAD1"),
        "0002": ("BDEUSO", "IVAAD2"),
        "0003": ("COMERC", "NO_VALIDA"),
    }


def test_un_item_sin_destino_toma_el_por_defecto_aunque_otro_cambie():
    items = [dict(ITEM_BASE), dict(ITEM_BASE, iva_adicional="IVAAD2")]
    assert _pares(_gen(items)) == {"0001": ("COMERC", "NO_VALIDA"), "0002": ("BDEUSO", "IVAAD2")}


def test_un_grupo_con_destinos_distintos_no_se_genera():
    items = [dict(ITEM_BASE, grupo_id=1, iva_adicional="IVAAD1"),
             dict(ITEM_BASE, grupo_id=1, iva_adicional="IVAAD2")]
    with pytest.raises(ValueError, match="mismo destino"):
        _gen(items)


# Los códigos de GANANCIASOP3 no son un valor de `iva_adicional`: el dato es
# el de IVAADICIONAL1 y el otro sale de la tabla.
NO_VALIDOS = ["IVAAD3", "IVAAD", "COMERC", "BDEUSO", "USOPAR", "uso particular"]


@pytest.mark.parametrize("valor", NO_VALIDOS)
def test_un_destino_por_operacion_que_no_esta_en_la_tabla_no_genera(valor):
    with pytest.raises(ValueError, match="Operación: destino de la mercadería .* no válido"):
        _gen(iva_adicional=valor)


@pytest.mark.parametrize("valor", NO_VALIDOS)
def test_un_destino_por_item_que_no_esta_en_la_tabla_no_genera(valor):
    with pytest.raises(ValueError, match="Ítem 1: destino de la mercadería .* no válido"):
        _gen([dict(ITEM_BASE, iva_adicional=valor)])


# --- Por la ruta, como lo pide la pantalla ---------------------------------

@pytest.mark.parametrize("iva, ganancias", PARES.items())
def test_por_la_ruta_cada_destino_sale_con_su_par(iva, ganancias):
    r = _generar(iva_adicional=iva)
    assert r.status_code == 200, r.text[:400]
    assert _pares(r.json()["content"]) == {"0001": (ganancias, iva)}


def test_por_la_ruta_un_destino_que_no_esta_en_la_tabla_da_400_sin_archivo():
    r = _generar(item={"iva_adicional": "BDEUSO"})
    assert r.status_code == 400, r.text[:400]
    assert "Ítem 1: destino de la mercadería «BDEUSO» no válido" in r.text, r.text[:400]
    assert "content" not in r.json()
