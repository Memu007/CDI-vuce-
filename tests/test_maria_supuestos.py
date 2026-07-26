"""Lo que el sistema declara sin preguntar tiene que quedar a la vista.

Por qué existe (2026-07-26): esta sesión encontró cuatro campos que el
generador elegía solo y que nadie veía — el año del `IEXT` escrito a mano, la
procedencia igualada al origen, `CARTUSO` fijo en 3 e `IVAADICIONAL1` fijo en
`IVAAD1`. Todos producen un TXT válido a la vista; el error aparece en la
aduana.

La premisa del producto es "la IA recomienda, el humano confirma". Un valor
asumido en silencio la rompe igual que uno inventado. Estos avisos no
bloquean: ponen los supuestos arriba de la mesa antes de generar.
"""

import pytest

from proyecto_maria.core.maria_generator import supuestos_declarados

ITEM = {
    "pieza": "1",
    "descripcion": "Equipo de demostracion",
    "ncm": "84714900100D",
    "cantidad": 6,
    "valor_unitario": 1197.00,
    "peso_kg": 33.0,
    "origen": "310",
    "unidad": "07",
}


def _texto(avisos):
    return " | ".join(avisos).lower()


# ====================================================================
# Procedencia: el hallazgo del archivo real (origen 200, procedencia 222)
# ====================================================================

def test_avisa_cuando_la_procedencia_se_asume_igual_al_origen():
    avisos = supuestos_declarados([ITEM], incoterm="FOB")
    assert "procedencia" in _texto(avisos)
    assert "1" in _texto(avisos)


def test_no_avisa_si_la_procedencia_vino_declarada():
    item = {**ITEM, "procedencia": "222"}
    avisos = supuestos_declarados([item], incoterm="FOB")
    assert "procedencia" not in _texto(avisos)


def test_identifica_cual_item_es():
    items = [{**ITEM, "procedencia": "222"}, ITEM, ITEM]
    avisos = supuestos_declarados(items, incoterm="FOB")
    proc = [a for a in avisos if a.lower().startswith("procedencia")][0]
    assert "2, 3" in proc, "tiene que decir qué ítems, no un aviso genérico"


# ====================================================================
# Gastos a FOB
# ====================================================================

def test_avisa_que_los_gastos_se_calcularon_en_grupos_c_d():
    avisos = supuestos_declarados([ITEM], incoterm="DDP", flete=365.0, seguro=75.47)
    texto = _texto(avisos)
    assert "gastos a fob" in texto and "440.47" in texto


def test_avisa_que_no_se_declararon_gastos_fuera_de_c_d():
    avisos = supuestos_declarados([ITEM], incoterm="EXW", flete=365.0, seguro=75.47)
    texto = _texto(avisos)
    assert "gastos a fob" in texto and "no se declararon" in texto


def test_no_avisa_de_gastos_si_el_despachante_los_cargo():
    avisos = supuestos_declarados([ITEM], incoterm="EXW", gastos_fob=150.0)
    assert "gastos a fob" not in _texto(avisos)


def test_fob_puro_no_genera_aviso_de_gastos():
    avisos = supuestos_declarados([ITEM], incoterm="FOB")
    assert "gastos a fob" not in _texto(avisos)


# ====================================================================
# Constantes que hoy no se pueden elegir
# ====================================================================

def test_avisa_los_campos_que_van_fijos():
    texto = _texto(supuestos_declarados([ITEM], incoterm="FOB"))
    assert "cartuso" in texto, "el uso va fijo en 3 y el despachante debe saberlo"
    assert "iva" in texto, "IVAADICIONAL1 va fijo en IVAAD1"


def test_avisa_la_unidad_por_defecto():
    item = {k: v for k, v in ITEM.items() if k != "unidad"}
    assert "unidad" in _texto(supuestos_declarados([item], incoterm="FOB"))


def test_sin_items_no_avisa_nada_de_items():
    avisos = supuestos_declarados([], incoterm="FOB")
    assert not any("cartuso" in a.lower() for a in avisos)


# ====================================================================
# Los avisos son para leer, no para descifrar
# ====================================================================

def test_los_avisos_estan_en_castellano_llano():
    for aviso in supuestos_declarados([ITEM], incoterm="EXW"):
        assert len(aviso) > 25, f"aviso demasiado corto para entenderse: {aviso!r}"
        assert not aviso.startswith(("ERROR", "WARN", "[")), aviso


def test_no_explota_con_items_mal_formados():
    """Nunca puede romper la generación: es informativo."""
    assert isinstance(supuestos_declarados([None, "texto", {}], incoterm="FOB"), list)
    assert isinstance(supuestos_declarados(None, incoterm=""), list)
