"""ORDEN-1: el orden de los productos en la pantalla es el orden del TXT.

La pantalla manda los productos en el orden en que quedaron (`CDI.state.items`)
y el generador numera los ítems en ese orden: un producto suelto sale donde
está; un grupo armado a mano y los renglones de la misma posición (MARIA-8)
salen en un solo ítem, donde está su primer renglón. Estas pruebas cambian el
orden de los productos y comparan el TXT con el original: tiene que ser el
mismo salvo el orden de los ítems y sus números. Datos inventados.
"""
import random
import re
from decimal import Decimal

import pytest

from tests.test_maria7_rechazos_24_10 import LONA, _gen
from tests.test_maria_subitems import SUF_A, SUF_B

# Seis productos distinguibles: dos lonas de la misma posición (un ítem con
# dos sub-ítems, MARIA-8), dos teléfonos en un grupo armado a mano, un equipo
# con dos subítems cargados a mano y un cable suelto. Ningún FOB repetido: con
# dos iguales el centavo que sobra del flete va al que queda primero (ver el
# último caso).
LONA_GRIS = dict(LONA, descripcion="Lona de PVC gris 620 g", cantidad=750.5,
                 valor_unitario=1.853, peso_kg=465.125)
LONA_AZUL = dict(LONA, descripcion="Lona de PVC azul 620 g", cantidad=312.25,
                 valor_unitario=2.071, peso_kg=191.437)
# El equipo viene partido a mano en dos subítems (SUBITEMS-1): van adentro del
# producto y se mueven con él.
EQUIPO = dict(LONA, pieza="84714900100D", descripcion="Equipo portatil demo",
              cantidad=3, valor_unitario=411.11, peso_kg=7.221, unidad="u",
              subitems=[{"cantidad": 1, "valor_unitario": 411.11, "sufijo": SUF_A},
                        {"cantidad": 2, "valor_unitario": 411.11, "sufijo": SUF_B}])
TEL_1 = dict(LONA, pieza="85171300100F", descripcion="Telefono demo uno",
             cantidad=7, valor_unitario=99.97, peso_kg=1.123, unidad="u", grupo_id=1)
TEL_2 = dict(LONA, pieza="85171300100F", descripcion="Telefono demo dos",
             cantidad=2, valor_unitario=55.51, peso_kg=0.377, unidad="u", grupo_id=1)
CABLE = dict(LONA, pieza="85444200900E", descripcion="Cable demo", cantidad=40,
             valor_unitario=0.733, peso_kg=3.913, unidad="u")

ORIGINAL = [LONA_GRIS, EQUIPO, LONA_AZUL, TEL_1, TEL_2, CABLE]


def _numero_del_item(bloque: str) -> str | None:
    m = re.search(r"^NART=(\d+)\r?$", bloque, re.M)
    return m.group(1) if m and m.group(1) != "0000" else None


def _partes(txt: str):
    """La cabecera (todo bloque que no es de un ítem) y los ítems en orden, cada
    uno como su [ART] seguido de sus [CPL] y sus [SBT]."""
    cabecera, items = [], {}
    for bloque in txt.split("\r\n\r\n"):
        # El último bloque del TXT termina en un salto: no es parte del ítem.
        bloque = bloque.strip("\r\n")
        n = _numero_del_item(bloque)
        if n is None:
            cabecera.append(bloque)
        else:
            items.setdefault(n, []).append(bloque)
    return cabecera, list(items.values())


def _sin_numeros(bloque: str) -> str:
    """El bloque sin lo que cambia con el lugar del ítem: su número, su número
    de artículo, su número de declaración y el de factura de sus sub-ítems."""
    bloque = re.sub(r"^(NART|NARTEXT|IARTESPAPU)=\d+", r"\1=#", bloque, flags=re.M)
    bloque = re.sub(r"^IEXT=FAC_I-\d+/", "IEXT=FAC_I-#/", bloque, flags=re.M)
    return re.sub(r"^IEXT=\d+-", "IEXT=#-", bloque, flags=re.M)


def _item_sin_numeros(bloques: list) -> str:
    return "\r\n\r\n".join(_sin_numeros(b) for b in bloques)


def _lugares(items: list) -> list:
    """Cada producto, con la llave de su ítem del TXT: el grupo, la posición
    (MARIA-8) o él mismo. Lo hace a mano, sin el generador."""
    por_posicion = {}
    for it in items:
        if it.get("grupo_id") is None:
            por_posicion.setdefault(it["pieza"], []).append(it)
    llaves = []
    for it in items:
        if it.get("grupo_id") is not None:
            llaves.append(("grupo", it["grupo_id"]))
        elif len(por_posicion[it["pieza"]]) > 1:
            llaves.append(("posicion", it["pieza"]))
        else:
            llaves.append(("producto", it["descripcion"]))
    return llaves


def _orden_de_los_items(items: list) -> list:
    """El orden de los ítems del TXT: el de su primer producto."""
    return list(dict.fromkeys(_lugares(items)))


def _item_de_cada_llave(items: list, txt: str) -> dict:
    _, bloques = _partes(txt)
    orden = _orden_de_los_items(items)
    assert len(orden) == len(bloques)
    return dict(zip(orden, bloques))


# Órdenes posibles en la pantalla: los teléfonos del grupo se mueven juntos y
# las dos lonas siguen en el mismo orden entre sí (el orden de sus sub-ítems
# es el otro caso).
REORDENADOS = {
    "al revés salvo las lonas": [CABLE, TEL_1, TEL_2, LONA_GRIS, EQUIPO, LONA_AZUL],
    "el grupo primero": [TEL_1, TEL_2, LONA_GRIS, EQUIPO, LONA_AZUL, CABLE],
    "la lona azul arriba de todo": [LONA_GRIS, LONA_AZUL, EQUIPO, TEL_1, TEL_2, CABLE],
    "el último arriba": [CABLE, LONA_GRIS, EQUIPO, LONA_AZUL, TEL_1, TEL_2],
    "las lonas separadas por el grupo": [EQUIPO, LONA_GRIS, TEL_1, TEL_2, CABLE, LONA_AZUL],
}


@pytest.mark.parametrize("nombre", list(REORDENADOS))
def test_el_txt_reordenado_es_el_original_salvo_el_orden_de_los_items(nombre):
    reordenado = REORDENADOS[nombre]
    txt_original, txt_nuevo = _gen(ORIGINAL), _gen(reordenado)
    cabecera_original, _ = _partes(txt_original)
    cabecera_nueva, items_nuevos = _partes(txt_nuevo)

    assert cabecera_nueva == cabecera_original
    del_original = _item_de_cada_llave(ORIGINAL, txt_original)
    esperado = [_item_sin_numeros(del_original[k]) for k in _orden_de_los_items(reordenado)]
    assert [_item_sin_numeros(b) for b in items_nuevos] == esperado


@pytest.mark.parametrize("nombre", list(REORDENADOS))
def test_los_items_quedan_numerados_corridos(nombre):
    _, items = _partes(_gen(REORDENADOS[nombre]))
    numeros = [f"{n:04d}" for n in range(1, len(items) + 1)]
    assert [re.search(r"^NARTEXT=(\d+)", b[0], re.M).group(1) for b in items] == numeros
    for n, bloques in zip(range(1, len(items) + 1), items):
        assert re.search(rf"^IARTESPAPU=\d+{n:04d}\r?$", bloques[0], re.M)
        assert re.search(rf"^IEXT=FAC_I-{n:02d}/", bloques[0], re.M)
        for sbt in _sbts(bloques):
            assert re.search(rf"^IEXT={n}-\d+\r?$", sbt, re.M), sbt


def _sbts(bloques: list) -> list:
    return [b for b in bloques if b.startswith("[SBT]")]


def _sbts_por_item(txt: str) -> list:
    """El NART de cada [SBT], en el orden del TXT."""
    return [_numero_del_item(b) for b in txt.split("\r\n\r\n") if b.startswith("[SBT]")]


@pytest.mark.parametrize("nombre", list(REORDENADOS))
def test_los_subitems_quedan_juntos_bajo_su_item(nombre):
    txt = _gen(REORDENADOS[nombre])
    nart = _sbts_por_item(txt)
    # Cada ítem tiene sus sub-ítems seguidos: el NART no vuelve a aparecer.
    assert nart == sorted(nart)
    _, items = _partes(txt)
    lonas = [b for b in items if "3921.90.19.900Z" in b[0]]
    assert len(lonas) == 1 and len(_sbts(lonas[0])) == 2
    equipos = [b for b in items if "8471.49.00.100D" in b[0]]
    assert len(equipos) == 1 and len(_sbts(equipos[0])) == 2


def _fob_de_los_sbt(bloques: list) -> list:
    return [re.search(r"^MSBTFOB=(.*?)\r?$", b, re.M).group(1) for b in _sbts(bloques)]


def test_dos_renglones_de_la_misma_posicion_dados_vuelta_cambian_solo_sus_subitems():
    """Con la lona azul arriba de la gris, el ítem es el mismo y sus dos
    sub-ítems salen en el orden nuevo, numerados de nuevo."""
    reordenado = [LONA_AZUL, EQUIPO, LONA_GRIS, TEL_1, TEL_2, CABLE]
    txt_original, txt_nuevo = _gen(ORIGINAL), _gen(reordenado)
    assert _partes(txt_nuevo)[0] == _partes(txt_original)[0]
    _, originales = _partes(txt_original)
    _, nuevos = _partes(txt_nuevo)
    assert _fob_de_los_sbt(nuevos[0]) == list(reversed(_fob_de_los_sbt(originales[0])))
    # Fuera de los sub-ítems de la lona, nada cambia.
    assert [_item_sin_numeros(b) for b in nuevos[1:]] == \
        [_item_sin_numeros(b) for b in originales[1:]]
    assert _sin_numeros(nuevos[0][0]) == _sin_numeros(originales[0][0])

    def sin_numero_de_subitem(b):
        return re.sub(r"^(ISBT=\d+|IEXT=#-\d+)\r?$", "", _sin_numeros(b), flags=re.M)
    assert sorted(map(sin_numero_de_subitem, nuevos[0][1:])) == \
        sorted(map(sin_numero_de_subitem, originales[0][1:]))


# ------------------------------------------------------------ al azar


def _producto_al_azar(rng, n):
    pieza = rng.choice(["39219019900Z", "84714900100D", "85444200900E", "73181500900H"])
    return dict(LONA, pieza=pieza, descripcion=f"Producto demo {n}",
                cantidad=rng.randint(1, 900) + rng.randint(0, 999) / 1000,
                valor_unitario=rng.randint(1, 50000) / 1000,
                peso_kg=rng.randint(1, 900000) / 1000, unidad="u")


def _unidades_al_azar(rng):
    """Productos de la pantalla en unidades que se arrastran: un suelto o un
    grupo armado a mano (sus miembros, seguidos)."""
    unidades, n = [], 0
    for gid in range(1, 4):
        unidades.append([_producto_al_azar(rng, n := n + 1)])
        grupo = dict(_producto_al_azar(rng, n := n + 1), grupo_id=gid)
        unidades.append([grupo] + [dict(_producto_al_azar(rng, n := n + 1),
                                        pieza=grupo["pieza"], grupo_id=gid)
                                   for _ in range(rng.randint(1, 2))])
    for _ in range(6):
        unidades.append([_producto_al_azar(rng, n := n + 1)])
    return unidades


def _sin_orden_de_subitems(bloques: list) -> str:
    def sin_numero(b):
        return re.sub(r"^(ISBT=\d+|IEXT=#-\d+)\r?$", "", _sin_numeros(b), flags=re.M)
    return "\r\n\r\n".join([_sin_numeros(bloques[0])] + sorted(map(sin_numero, bloques[1:])))


@pytest.mark.parametrize("semilla", range(8))
def test_al_azar_el_txt_reordenado_es_el_original_salvo_el_orden(semilla):
    """Productos y órdenes al azar (con semilla fija): los mismos ítems, en el
    orden de su primer producto, con los sub-ítems juntos. Dentro de un ítem
    de varios renglones el orden de los sub-ítems puede cambiar."""
    rng = random.Random(semilla)
    unidades = _unidades_al_azar(rng)
    original = [p for u in unidades for p in u]
    fobs = [Decimal(str(p["cantidad"])) * Decimal(str(p["valor_unitario"])) for p in original]
    assert len(set(fobs)) == len(fobs), "dos FOB iguales: el centavo del flete depende del orden"
    rng.shuffle(unidades)
    reordenado = [p for u in unidades for p in u]

    txt_original, txt_nuevo = _gen(original), _gen(reordenado)
    assert _partes(txt_nuevo)[0] == _partes(txt_original)[0]
    del_original = _item_de_cada_llave(original, txt_original)
    esperado = [_sin_orden_de_subitems(del_original[k]) for k in _orden_de_los_items(reordenado)]
    assert [_sin_orden_de_subitems(b) for b in _partes(txt_nuevo)[1]] == esperado
    nart = _sbts_por_item(txt_nuevo)
    assert nart == sorted(nart)


# ------------------------------------------- lo que el orden sí cambia (D)


@pytest.mark.xfail(strict=False, reason=(
    "ORDEN-1, D del informe: con dos FOB iguales, repartir() le da el centavo "
    "sobrante del flete al primero; reordenarlos lo pasa al otro. Es del "
    "generador (maria_generator.py), que esta pieza no toca."))
def test_con_dos_fob_iguales_el_flete_de_cada_item_no_depende_del_orden():
    a = dict(LONA, pieza="84714900100D", descripcion="Equipo demo A", cantidad=1,
             valor_unitario=10, peso_kg=1, unidad="u")
    b = dict(LONA, pieza="85171300100F", descripcion="Telefono demo B", cantidad=1,
             valor_unitario=10, peso_kg=1, unidad="u")

    def flete_de_cada_uno(items):
        _, bloques = _partes(_gen(items, flete=0.01, seguro=0.01))
        return {re.search(r"^IESPNCE=(.*?)\r?$", art[0], re.M).group(1):
                re.search(r"^MARTFLE=(.*?)\r?$", art[0], re.M).group(1) for art in bloques}

    assert flete_de_cada_uno([a, b]) == flete_de_cada_uno([b, a])
