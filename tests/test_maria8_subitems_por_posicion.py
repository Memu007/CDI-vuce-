"""MARIA-8: cada renglón de la factura es un sub-ítem.

El TXT que el MARIA cargó el 24/10 tenía un solo ítem (`CARTSBITEM=S`) con un
[SBT] por renglón de la factura: cada uno con su FOB, su cantidad, su precio,
sus kilos (QSBTUNTEST) y su sufijo. CDI sacaba un ítem por renglón. Los
renglones con la misma posición SIM, origen, procedencia y estado van ahora
en un solo ítem, y las sumas del ítem cierran exactas: el redondeo sobrante va
al sub-ítem más grande. Datos inventados con la forma de la factura de lonas.
"""
from decimal import Decimal

import pytest

from proyecto_maria.core import maria_generator as mg
from tests.test_maria7_rechazos_24_10 import LONA, _gen, _pedido, _registrar_con_cuit, _valor

ANCHOS = ("150", "200")
COLORES = ("GREY", "BLUE", "GREEN")


def _renglon(ancho, color, cantidad, unitario, kilos, **extra):
    return dict(
        LONA, descripcion=f"Lona de PVC 620 g {color} {ancho} cm", cantidad=cantidad,
        valor_unitario=unitario, peso_kg=kilos, unidad_estadistica="kg",
        sufijo=f"AA(MARCA)-AI(620G-{color} {ancho}CMX50M)-", **extra,
    )


def _lonas():
    """Doce renglones, dos anchos y tres colores, dos lotes de cada uno.

    Once pesan 38,765 kg (38,77 al centésimo) y uno 50,125 (50,13): los doce
    centésimos suman 476,60 y el total, 476,540 kg, da 476,54. Los seis
    centavos de más se le restan al más pesado. Las cantidades, de tres
    decimales, hacen lo mismo con QSBTUNTDCL."""
    renglones = []
    for lote in (1, 2):
        for ancho in ANCHOS:
            for color in COLORES:
                renglones.append(_renglon(ancho, color, 75.005 if lote == 1 else 60.0,
                                          1.85 if ancho == "150" else 2.05, 38.765))
    renglones[4] = dict(renglones[4], cantidad=100.0, peso_kg=50.125)
    return renglones


def _bloques(txt: str, nombre: str) -> list:
    """Cada bloque [nombre] del TXT como diccionario campo → valor."""
    bloques = []
    for crudo in txt.split("\r\n\r\n"):
        lineas = crudo.strip("\r\n").split("\r\n")
        if lineas[0] == f"[{nombre}]":
            bloques.append(dict(linea.split("=", 1) for linea in lineas[1:]))
    return bloques


def _sumar(bloques, campo):
    return sum((Decimal(b[campo]) for b in bloques), Decimal("0"))


# ------------------------------------------------ un ítem con doce sub-ítems


def test_doce_renglones_de_una_posicion_son_un_item_con_doce_subitems():
    txt = _gen(_lonas())
    arts, sbts = _bloques(txt, "ART"), _bloques(txt, "SBT")
    assert len(arts) == 1
    assert arts[0]["CARTSBITEM"] == "S"
    assert [s["ISBT"] for s in sbts] == [f"{n:04d}" for n in range(1, 13)]
    assert {s["NART"] for s in sbts} == {"0001"}
    assert [s["IEXT"] for s in sbts] == [f"1-{n}" for n in range(1, 13)]


def test_cada_subitem_lleva_lo_de_su_renglon():
    renglones = _lonas()
    sbts = _bloques(_gen(renglones), "SBT")
    for renglon, sbt in zip(renglones, sbts):
        assert Decimal(sbt["MSBTFOB"]) == mg._fob_de(renglon)
        assert sbt["MSBTUNITAR"] == f"{renglon['valor_unitario']:.4f}"
        assert sbt["CSBTSVL"] == mg.limpiar_sufijo(renglon["sufijo"])[0]
    assert len({s["CSBTSVL"] for s in sbts}) == 6


def test_las_sumas_del_item_cierran_exactas():
    txt = _gen(_lonas())
    art, sbts = _bloques(txt, "ART")[0], _bloques(txt, "SBT")
    assert Decimal(art["MARTFOB"]) == _sumar(sbts, "MSBTFOB")
    assert Decimal(art["QARTUNTDCL"]) == _sumar(sbts, "QSBTUNTDCL")
    assert Decimal(art["QARTUNTEST"]) == _sumar(sbts, "QSBTUNTEST")
    assert _valor(txt, "MDDTFOB") == [art["MARTFOB"]]


def test_los_kilos_son_los_de_cada_renglon_y_el_sobrante_va_al_mas_pesado():
    txt = _gen(_lonas())
    art, sbts = _bloques(txt, "ART")[0], _bloques(txt, "SBT")
    assert art["QARTKGRNET"] == "476.540"
    assert art["CARTUNTEST"] == "01" and art["QARTUNTEST"] == "476.54"
    kilos = [s["QSBTUNTEST"] for s in sbts]
    assert kilos[4] == "50.07"                       # 50,13 menos los seis centavos
    assert kilos[:4] + kilos[5:] == ["38.77"] * 11


def test_la_cantidad_tambien_cierra_y_el_sobrante_va_al_mas_grande():
    """Cinco renglones de 75,005 m² salen 75,01 cada uno: los centésimos suman
    835,05 y la suma exacta, 835,025, da 835,03. El más grande (100) da los
    dos centavos."""
    txt = _gen(_lonas())
    art, sbts = _bloques(txt, "ART")[0], _bloques(txt, "SBT")
    assert art["QARTUNTDCL"] == "835.03"
    cantidades = [s["QSBTUNTDCL"] for s in sbts]
    assert cantidades[4] == "99.98"
    assert cantidades[:4] == ["75.01"] * 4 and cantidades[5] == "75.01"
    assert cantidades[6:] == ["60.00"] * 6


def test_en_la_unidad_declarada_la_estadistica_es_la_cantidad():
    renglones = [dict(r, unidad_estadistica="m²") for r in _lonas()]
    txt = _gen(renglones)
    art, sbts = _bloques(txt, "ART")[0], _bloques(txt, "SBT")
    assert art["CARTUNTEST"] == "03"
    assert [s["QSBTUNTEST"] for s in sbts] == [s["QSBTUNTDCL"] for s in sbts]
    assert art["QARTUNTEST"] == art["QARTUNTDCL"]


def test_el_flete_y_el_seguro_van_al_item_y_la_base_cierra():
    txt = _gen(_lonas())
    art = _bloques(txt, "ART")[0]
    assert (art["MARTFLE"], art["MARTASS"]) == ("7925.00", "12.40")
    assert Decimal(art["MARTBASIMP"]) == Decimal(art["MARTFOB"]) + Decimal("7937.40")


def test_el_unitario_del_item_es_el_fob_sobre_la_cantidad():
    art = _bloques(_gen(_lonas()), "ART")[0]
    assert art["MARTUNITAR"] == f"{Decimal(art['MARTFOB']) / Decimal('835.03'):.4f}"


# ------------------------------------------------------- cuándo se separan


def test_dos_posiciones_son_dos_items():
    renglones = _lonas()
    for r in renglones[6:]:
        r["pieza"] = "39211390900F"
    txt = _gen(renglones)
    arts, sbts = _bloques(txt, "ART"), _bloques(txt, "SBT")
    assert [a["IESPNCE"] for a in arts] == ["3921.90.19.900Z", "3921.13.90.900F"]
    assert [a["CARTSBITEM"] for a in arts] == ["S", "S"]
    assert [(s["NART"], s["ISBT"]) for s in sbts] == (
        [("0001", f"{n:04d}") for n in range(1, 7)] + [("0002", f"{n:04d}") for n in range(1, 7)])
    for art, de_el in ((arts[0], sbts[:6]), (arts[1], sbts[6:])):
        assert Decimal(art["MARTFOB"]) == _sumar(de_el, "MSBTFOB")
        assert Decimal(art["QARTUNTEST"]) == _sumar(de_el, "QSBTUNTEST")


def test_la_posicion_se_compara_sin_puntos_ni_espacios():
    renglones = _lonas()[:2]
    renglones[1]["pieza"] = "3921.90.19.900 z"
    assert len(_bloques(_gen(renglones), "ART")) == 1


def test_el_item_va_donde_aparece_su_primer_renglon():
    otra = dict(_renglon("150", "GREY", 10, 3.0, 5.0), pieza="39211390900F")
    renglones = _lonas()[:2]
    txt = _gen([renglones[0], otra, renglones[1]])
    arts = _bloques(txt, "ART")
    assert [a["IESPNCE"] for a in arts] == ["3921.90.19.900Z", "3921.13.90.900F"]
    assert [a["CARTSBITEM"] for a in arts] == ["S", "N"]


@pytest.mark.parametrize("cambio", [
    {"origen": "TW", "pais_procedencia": "CN"},   # la procedencia de los otros es su origen, CN
    {"pais_procedencia": "TW"},
    {"estado": "4"},
    {"unidad": "kg"},
    {"unidad_estadistica": "m²"},
    {"iva_adicional": "IVAAD1"},
], ids=["origen", "procedencia", "estado", "unidad", "unidad_estadistica", "iva"])
def test_lo_que_cambia_el_item_lo_separa(cambio):
    renglones = _lonas()[:3]
    renglones[1] = dict(renglones[1], **cambio)
    arts = _bloques(_gen(renglones), "ART")
    assert len(arts) == 2
    assert [a["CARTSBITEM"] for a in arts] == ["S", "N"]


def test_un_renglon_solo_sale_como_antes():
    txt = _gen([dict(LONA)])
    assert _valor(txt, "CARTSBITEM") == ["N"]
    assert _valor(txt, "ISBT") == ["0000"]


def test_un_grupo_a_mano_y_los_subitems_a_mano_no_se_mezclan():
    """El grupo a mano es un producto sin detalle y el producto con sub-ítems
    a mano ya trae los suyos: los dos quedan como antes, aunque tengan la
    misma posición que otro renglón."""
    a, b, c, d = (dict(r, cantidad=40, unidad_estadistica="m²") for r in _lonas()[:4])
    a["grupo_id"] = b["grupo_id"] = "g1"
    b["sufijo"] = a["sufijo"]  # un grupo, un solo sufijo (SUFIJOS-1)
    c["subitems"] = [{"cantidad": 15, "valor_unitario": 1.85}, {"cantidad": 25, "valor_unitario": 1.85}]
    txt = _gen([a, b, c, d])
    arts = _bloques(txt, "ART")
    assert [a["CARTSBITEM"] for a in arts] == ["N", "S", "N"]
    assert [s["ISBT"] for s in _bloques(txt, "SBT")] == ["0000", "0001", "0002", "0000"]


# --------------------------------------------------------------- sufijos


def test_sin_sufijo_propio_el_renglon_lleva_el_de_la_operacion():
    renglones = _lonas()[:3]
    del renglones[1]["sufijo"]
    sbts = _bloques(_gen(renglones), "SBT")
    assert sbts[1]["ISBT"] == "0002"
    assert sbts[1]["CSBTSVL"] == mg.limpiar_sufijo(
        "AA(MARCA)-AI(620G-GREY.008 150CMX50M)-")[0]


def test_con_todos_los_sufijos_propios_no_hace_falta_el_de_la_operacion():
    sbts = _bloques(_gen(_lonas(), sbt_sufijo_valor=""), "SBT")
    assert len(sbts) == 12


def test_sin_ningun_sufijo_el_error_dice_el_numero_de_la_pantalla():
    """Los renglones 1 y 2 van en el ítem 1 y los 3 y 4 en el 2: el que no
    tiene sufijo es el 3, y la pantalla lleva al renglón por «Item N»."""
    renglones = _lonas()[:4]
    for r in renglones[2:]:
        r["pieza"] = "39211390900F"
    del renglones[2]["sufijo"]
    with pytest.raises(ValueError, match=r"^Item 3: falta el sufijo"):
        _gen(renglones, sbt_sufijo_valor="")


def test_el_sufijo_del_renglon_se_limpia():
    renglones = _lonas()[:2]
    renglones[1]["sufijo"] = "AA(MARCA)-AI(620G-BLUE.010 150CMX50M)-"
    sbt = _bloques(_gen(renglones), "SBT")[1]
    assert (sbt["ISBT"], sbt["CSBTSVL"]) == ("0002", "AA(MARCA)-AI(620G BLUE 010 150CMX50M)-")


# ---------------------------------------------------------------- errores


def test_un_renglon_sin_peso_dice_su_numero_en_la_pantalla():
    renglones = _lonas()[:3]
    renglones[2]["peso_kg"] = 0
    with pytest.raises(ValueError, match=r"^Item 3: el peso"):
        _gen(renglones)


def test_un_renglon_con_estado_que_no_corresponde_dice_su_numero():
    renglones = _lonas()[:3]
    renglones[0]["estado"] = "9"
    renglones[1]["estado"] = "9"
    with pytest.raises(ValueError, match=r"^Ítem 1 .*no válido"):
        _gen(renglones)


def test_el_peso_de_un_item_despues_de_los_juntos_dice_su_numero_en_la_pantalla():
    """Los renglones 1 y 2 son el ítem 1 del TXT; el 3 es el ítem 2, pero en
    la pantalla es el renglón 3."""
    renglones = _lonas()[:2] + [dict(LONA, pieza="39211390900F", peso_kg=0)]
    with pytest.raises(ValueError, match=r"^Item 3: el peso"):
        _gen(renglones)


@pytest.mark.parametrize("cantidad", [0, -5, 0.004])
def test_un_renglon_sin_cantidad_no_es_un_subitem(cantidad):
    """Un sub-ítem a mano con cantidad 0 ya era un error; uno automático
    salía QSBTUNTDCL=0.00 con FOB. 0,004 también sale 0,00."""
    renglones = _lonas()[:3]
    renglones[1] = dict(renglones[1], cantidad=cantidad, valor_unitario=None, valor_total=5)
    with pytest.raises(ValueError, match=r"^Item 2: la cantidad .*mayor que 0"):
        _gen(renglones)


def test_el_unitario_del_item_es_el_fob_sobre_la_cantidad_declarada():
    """3 + 7,005 = 10,005, que se declara 10,01: el unitario tiene que ser
    12,44 / 10,01 = 1,2428 y no 12,44 / 10,005 = 1,2434."""
    renglones = [dict(LONA, cantidad=3, valor_unitario=1.24, sufijo="AA(A)-"),
                 dict(LONA, cantidad=7.005, valor_unitario=1.245, sufijo="AA(B)-")]
    art = _bloques(_gen(renglones), "ART")[0]
    assert (art["QARTUNTDCL"], art["MARTFOB"], art["MARTUNITAR"]) == ("10.01", "12.44", "1.2428")


def test_los_renglones_sin_posicion_no_se_juntan():
    """La pieza puede llegar vacía (la completa el despachante): dos
    productos sin posición no son la misma posición."""
    renglones = [dict(r, pieza="") for r in _lonas()[:2]]
    arts = _bloques(_gen(renglones), "ART")
    assert [a["CARTSBITEM"] for a in arts] == ["N", "N"]


def test_kilos_que_al_restar_quedarian_negativos_no_se_generan():
    """Doce renglones de 0,005 kg salen 0,01 cada uno (0,12) contra un total
    de 0,06: al más grande le tocaría −0,05."""
    renglones = [dict(r, peso_kg=0.005) for r in _lonas()]
    with pytest.raises(ValueError, match="kilos"):
        _gen(renglones)


def test_el_fob_de_medio_centavo_sube_y_el_item_cierra():
    """3 × 3,335 = 10,005: sube a 10,01 (no al par, 10,00) y el ítem suma eso."""
    renglones = [dict(LONA, cantidad=3, valor_unitario=3.335, sufijo="AA(A)-"),
                 dict(LONA, cantidad=1, valor_unitario=1, sufijo="AA(B)-")]
    txt = _gen(renglones)
    art, sbts = _bloques(txt, "ART")[0], _bloques(txt, "SBT")
    assert [s["MSBTFOB"] for s in sbts] == ["10.01", "1.00"]
    assert art["MARTFOB"] == "11.01"


def test_si_empatan_el_sobrante_va_al_primero():
    """Tres renglones de 1,005 m² salen 1,01 cada uno (3,03) contra 3,02."""
    renglones = [dict(LONA, cantidad=1.005, valor_unitario=2, sufijo=f"AA({s})-") for s in "ABC"]
    sbts = _bloques(_gen(renglones), "SBT")
    assert [s["QSBTUNTDCL"] for s in sbts] == ["1.00", "1.01", "1.01"]


def test_un_renglon_con_total_y_sin_unitario():
    renglones = [dict(LONA, cantidad=4, valor_unitario=None, valor_total=9, sufijo="AA(A)-"),
                 dict(LONA, cantidad=1, valor_unitario=1, sufijo="AA(B)-")]
    sbt = _bloques(_gen(renglones), "SBT")[0]
    assert (sbt["MSBTFOB"], sbt["QSBTUNTDCL"], sbt["MSBTUNITAR"]) == ("9.00", "4.00", "2.2500")


def test_declarada_en_kilos_la_cantidad_y_los_kilos_son_de_cada_renglon():
    renglones = [dict(LONA, unidad="kg", unidad_estadistica="kg", cantidad=100, peso_kg=98.5, sufijo="AA(A)-"),
                 dict(LONA, unidad="kg", unidad_estadistica="kg", cantidad=50, peso_kg=49.25, sufijo="AA(B)-")]
    txt = _gen(renglones)
    art, sbts = _bloques(txt, "ART")[0], _bloques(txt, "SBT")
    assert [(s["QSBTUNTDCL"], s["QSBTUNTEST"]) for s in sbts] == [("100.00", "98.50"), ("50.00", "49.25")]
    assert (art["QARTUNTDCL"], art["QARTUNTEST"]) == ("150.00", "147.75")


def test_el_estado_que_no_corresponde_en_el_tercer_renglon_dice_el_tres():
    renglones = _lonas()[:3]
    renglones[2]["estado"] = "9"
    with pytest.raises(ValueError, match=r"^Ítem 3 .*no válido"):
        _gen(renglones)


def test_kilos_de_un_renglon_que_al_centesimo_dan_cero_no_se_generan():
    """0,004 kg sale QSBTUNTEST=0.00 con FOB."""
    renglones = [dict(r, peso_kg=0.004) for r in _lonas()[:2]] + [dict(_lonas()[2], peso_kg=200)]
    with pytest.raises(ValueError, match="kilos"):
        _gen(renglones)


# -------------------------------------------------------- avisos y pantalla


def _dichos(numeros):
    """Los renglones como los dice un aviso: «1, 2 y 3»."""
    *antes, ultimo = (str(n) for n in numeros)
    return f"{', '.join(antes)} y {ultimo}"


def _aviso_de_que_van_juntos(cuales, cuantos):
    return (f"Sub-ítems: los renglones {cuales} van en un solo ítem con {cuantos} sub-ítems "
            "(misma posición SIM, origen, procedencia y estado).")


def _aviso_del_mismo_sufijo(cuales, cuantos, sufijo):
    return (f"Sufijo de valor: en el ítem de los renglones {cuales} los {cuantos} sub-ítems llevan "
            f"el mismo sufijo («{sufijo}»). Si cada renglón lleva el suyo (marca, modelo, color), cargalo en "
            "«Sufijo de valor» de cada producto, en «Lo que decide el despachante».")


def _de_los_items(avisos):
    """Los dos avisos de cada ítem de varios renglones, en el orden en que salen."""
    return [a for a in avisos if a.startswith("Sub-ítems:") or "llevan el mismo sufijo" in a]


POSICIONES = {"A": LONA["pieza"], "B": "39211390900F", "C": "39211200900X"}
# caso: (la posición de cada renglón, los renglones que los avisos dicen de cada ítem de varios,
# las posiciones en las que cada renglón lleva su sufijo: de esas no sale el aviso del mismo sufijo)
JUNTOS = {
    "seguidos": ("AAAB", {"A": "1, 2 y 3"}, ""),
    "salteados": ("ABA", {"A": "1 y 3"}, ""),
    "tres_items": ("ABCCAB", {"A": "1 y 5", "B": "2 y 6", "C": "3 y 4"}, ""),
    "doce_renglones": ("A" * 12, {"A": "1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 y 12"}, ""),
    "cada_renglon_su_sufijo": ("ABAB", {"A": "1 y 3", "B": "2 y 4"}, "B"),
}


@pytest.mark.parametrize("caso", JUNTOS)
def test_los_avisos_dicen_que_renglones_van_juntos(caso):
    posiciones, juntos, con_el_suyo = JUNTOS[caso]
    # Cada posición lleva su sufijo: el renglón de otro ítem que queda en el medio no cuenta.
    renglones = [dict(LONA, pieza=POSICIONES[letra], sufijo=f"AA({letra}{n if letra in con_el_suyo else ''})-")
                 for n, letra in enumerate(posiciones)]
    avisos = mg.supuestos_declarados(renglones, sbt_sufijo_valor="AA(X)-")
    # De cada ítem sale el aviso de los sub-ítems y, pegado, el del sufijo si llevan todos el mismo.
    assert _de_los_items(avisos) == [
        aviso for letra, cuales in juntos.items() for aviso in (
            _aviso_de_que_van_juntos(cuales, posiciones.count(letra)),
            *([] if letra in con_el_suyo else [
                _aviso_del_mismo_sufijo(cuales, posiciones.count(letra), f"AA({letra})-")]))]


SUCIO, LIMPIO = "AA(MARCA)-AI(620G-BLUE.010 150CMX50M)-", "AA(MARCA)-AI(620G BLUE 010 150CMX50M)-"
# caso: (el sufijo propio de cada renglón, el de la operación, lo que el aviso
# muestra entre «» o None si no sale). Se compara lo que sale en el TXT: limpio.
MISMO_SUFIJO = {
    "heredan": ((None, None, None), "AA(MARCA)-", "AA(MARCA)-"),
    "propios_vacios_heredan": (("", " ", None), "AA(MARCA)-", "AA(MARCA)-"),
    "dos_renglones": ((None, None), "AA(MARCA)-", "AA(MARCA)-"),
    "cinco_renglones": ((None,) * 5, "AA(MARCA)-", "AA(MARCA)-"),
    "heredan_uno_que_se_limpia": ((None, None, None), SUCIO, LIMPIO),
    "uno_trae_el_limpio_y_el_resto_hereda": ((LIMPIO, None, None), SUCIO, LIMPIO),
    "propios_iguales": ((SUCIO, LIMPIO, SUCIO), "", LIMPIO),
    "espacios_al_borde": (("AA(A) ", None, None), " AA(A)\t", "AA(A)"),
    "largo": ((None, None, None), "AA(" + "X" * 100 + ")-", "AA(" + "X" * 77),
    "propios_iguales_sin_usar_el_de_la_operacion": (("AA(A)-",) * 3, "AA(OK)-AB(XXX", "AA(A)-"),
    "solo_el_ultimo_distinto": (("AA(A)-", "AA(A)-", "AA(B)-"), "AA(A)-", None),
    # De doce renglones, uno solo distinto, en cada puesto: se comparan los doce.
    **{f"de_doce_solo_el_{puesto}_distinto": (
        ("AA(A)-",) * (puesto - 1) + ("AA(B)-",) + ("AA(A)-",) * (12 - puesto), "AA(A)-", None)
       for puesto in range(1, 13)},
    "uno_propio_y_el_resto_hereda_otro": (("AA(A)-", None, None), "AA(B)-", None),
    "uno_propio_y_el_resto_ninguno": (("AA(A)-", None, None), "", None),
    "ninguno": ((None, None, None), "", None),
    "uno_propio_no_se_separa": (("AA(A)-", "AA(OK)-AB(XXX", "AA(A)-"), "AA(A)-", None),
    "el_de_la_operacion_no_se_separa": ((None, None, None), "AA(OK)-AB(XXX", None),
}


@pytest.mark.parametrize("caso", MISMO_SUFIJO)
def test_los_avisos_dicen_si_todos_los_subitems_llevan_el_mismo_sufijo(caso):
    propios, de_la_operacion, muestra = MISMO_SUFIJO[caso]
    renglones = [{k: v for k, v in r.items() if k != "sufijo"} for r in _lonas()[:len(propios)]]
    for renglon, propio in zip(renglones, propios):
        if propio is not None:
            renglon["sufijo"] = propio
    # Después va otro ítem, de tres renglones y un solo sufijo: su aviso sale siempre y
    # segundo, tenga o no el suyo el ítem de antes y aunque los dos lleven el mismo sufijo.
    renglones += [dict(LONA, pieza="39211390900F", sufijo="AA(MARCA)-") for _ in range(3)]
    n = len(propios)
    este, el_otro = _dichos(range(1, n + 1)), _dichos(range(n + 1, n + 4))
    avisos = mg.supuestos_declarados(renglones, sbt_sufijo_valor=de_la_operacion)
    # El de los sub-ítems sale de los dos ítems y en su lugar, lleven el sufijo que lleven.
    assert _de_los_items(avisos) == [
        _aviso_de_que_van_juntos(este, n),
        *([] if muestra is None else [_aviso_del_mismo_sufijo(este, n, muestra)]),
        _aviso_de_que_van_juntos(el_otro, 3),
        _aviso_del_mismo_sufijo(el_otro, 3, "AA(MARCA)-")]


def _aviso_de_que_se_limpio(de_quien, sale):
    return (f"Sufijo de valor{de_quien}: entre un código y otro va un guion y dentro de los "
            f"paréntesis van sólo letras, números, espacios y la coma de un número; sale «{sale}».")


def _aviso_de_que_falta_el_codigo(donde):
    return (f"Sufijo de valor del {donde}: según el arancel de ARCA del 07/10/2026, la posición "
            "3921.90.19.900Z pide AI (CODIGO DE PRODUCTO O ARTICULO), y no está.")


# caso: (la posición de cada renglón, en minúscula si va en un grupo a mano; cómo nombran los
# avisos a cada renglón, en su orden. Fuera de un grupo, el que no está no trae sufijo)
SE_LIMPIO = {
    # El 3 usa el sufijo de la operación; el 4 y el 5 van solos y se avisan en su orden.
    "seguidos": ("AAABC", {4: "ítem 4", 5: "ítem 5", 1: "renglón 1", 2: "renglón 2"}),
    # El ítem tiene seis renglones; el 3 y el 6, de otras posiciones, quedan en el medio, y el 6
    # usa el sufijo de la operación.
    "salteados": ("AABAACAA", {3: "ítem 3", 1: "renglón 1", 2: "renglón 2", 4: "renglón 4",
                               5: "renglón 5", 7: "renglón 7", 8: "renglón 8"}),
    # Un grupo no se junta con nadie y se avisa una vez.
    "un_grupo_en_el_medio": ("AaaA", {2: "grupo ga", 1: "renglón 1", 4: "renglón 4"}),
    # Los renglones de cada ítem se nombran una vez, como renglones, sea el ítem que sea.
    "tres_items": ("ABCCAB", {1: "renglón 1", 5: "renglón 5", 2: "renglón 2", 6: "renglón 6",
                              3: "renglón 3", 4: "renglón 4"}),
}


@pytest.mark.parametrize("caso", SE_LIMPIO)
def test_los_avisos_dicen_si_se_limpio_el_sufijo_de_un_renglon(caso):
    posiciones, nombres = SE_LIMPIO[caso]
    # Cada sufijo está mal escrito (el punto sale como espacio) y es distinto de los otros. El de
    # un grupo es uno solo, sin el código de artículo que el arancel pide; el de la operación lo trae.
    renglones = []
    for n, letra in enumerate(posiciones, start=1):
        grupo = {"grupo_id": f"g{letra}"} if letra.islower() else {}
        sufijo = f"AA(M.{letra})-" if grupo else f"AA(M.{n})-AI(C{n})-"
        propio = {"sufijo": sufijo} if grupo or n in nombres else {}
        renglones.append(dict(LONA, pieza=POSICIONES[letra.upper()], **grupo, **propio))
    _gen(renglones, sbt_sufijo_valor="AA(X.0)-AI(Y)-")  # los avisos son de un pedido que genera
    avisos = mg.supuestos_declarados(renglones, sbt_sufijo_valor="AA(X.0)-AI(Y)-")
    # El de la operación se avisa primero, una vez, y sólo si algún renglón lo usa.
    lo_usan = [renglon for renglon in renglones if "sufijo" not in renglon]
    se_limpio = [_aviso_de_que_se_limpio("", "AA(X 0)-AI(Y)-")] if lo_usan else []
    se_limpio += [_aviso_de_que_se_limpio(f" del {donde}", renglones[n - 1]["sufijo"].replace(".", " "))
                  for n, donde in nombres.items()]
    falta = [_aviso_de_que_falta_el_codigo(donde)
             for n, donde in nombres.items() if "grupo_id" in renglones[n - 1]]
    assert [a for a in avisos if a.startswith("Sufijo de valor")] == se_limpio + falta


@pytest.mark.parametrize("caso, sufijo, dice", [
    ("igual", "CSBTSVL=AA(MARCA)-", "«=»"),
    ("largo", "A" * 121, "120 caracteres"),
    ("control", "AA(MA\x85RCA)-", "caracteres de control"),
    ("no_texto", {"a": 1}, "tiene que ser un texto"),
])
def test_el_sufijo_de_un_renglon_se_valida_como_los_otros(client, caso, sufijo, dice):
    _registrar_con_cuit(client, f"maria8_sufijo_{caso}")
    pedido = _pedido()
    pedido["items"] = [dict(pedido["items"][0], sufijo="AA(MARCA)-"),
                       dict(pedido["items"][0], sufijo=sufijo)]
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 400, r.text
    assert "Item 2" in r.text and dice in r.text


def test_el_pedido_de_la_pantalla_sale_en_un_item(client):
    _registrar_con_cuit(client, "maria8_pantalla")
    pedido = _pedido()
    pedido["items"] = [dict(pedido["items"][0], cantidad=10 + k, descripcion=f"Lona de PVC {k}")
                       for k in range(3)]
    r = client.post("/generate_maria", json=pedido)
    assert r.status_code == 200, r.text
    txt = r.json()["content"]
    assert _valor(txt, "CARTSBITEM") == ["S"]
    assert _valor(txt, "ISBT") == ["0001", "0002", "0003"]
