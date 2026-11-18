"""Los países se reconocen por su nombre corriente en inglés y en castellano, en el lector de
despachos y en el de facturas, y la letra de ancho completo se lee como la común."""
import json
import re
import shutil

import pytest

from proyecto_maria.core import maria_generator
from proyecto_maria.core.despacho_lector import origen_iso2
from proyecto_maria.pdf_extractor import _iso2_por_codigo_maria, _origen_desde_factura
from tests.test_catalogo3 import _de_la_pantalla


def _nombres():
    m = re.search(r"const NOMBRES = (\{.*?\});", maria_generator._PAISES_PANTALLA.read_text(encoding="utf-8"), re.S)
    return {int(c): idiomas for c, idiomas in json.loads(m.group(1)).items()}


def _sigla(codigo):
    return _iso2_por_codigo_maria().get(codigo, f"{codigo:03d}")


def test_cada_pais_se_reconoce_por_su_nombre_en_ingles_y_en_castellano():
    tabla, nombres = maria_generator._tabla_oficial(), _nombres()
    assert [c for c in _iso2_por_codigo_maria() if not (nombres.get(c, {}).get("en") and nombres[c]["es"])] == []
    malos = []
    for codigo, idiomas in nombres.items():
        otro = 310 if tabla[codigo] != tabla[310] else 203
        for nombre in {n for idioma in idiomas.values() for n in (*idioma, *(x.replace(".", "") for x in idioma))}:
            leido = (maria_generator.codigo_de_pais(nombre), _origen_desde_factura(nombre), origen_iso2(nombre),
                     origen_iso2(f"{codigo} {nombre}"), origen_iso2(f"{otro} {nombre}"))
            sigla = _iso2_por_codigo_maria().get(codigo, nombre)
            if leido != (codigo, sigla, sigla, _sigla(codigo), None):
                malos.append((codigo, nombre, leido))
    assert malos == []


def test_un_nombre_nuevo_no_cambia_el_pais_de_un_nombre_que_ya_se_reconocia():
    # Los alias de la pantalla y los del servidor mandan; ninguno pasa a ser otro país.
    js = maria_generator._PAISES_PANTALLA.read_text(encoding="utf-8")
    viejos = {k: int(v) for k, v in json.loads(re.search(r"const ALIASES = (\{.*?\});", js).group(1)).items()}
    viejos.update(maria_generator._PAISES_NORM)
    nuevos = {(maria_generator._normalizar_pais(n), c) for c, i in _nombres().items() for idioma in i.values()
              for n in idioma}
    assert {(n, c, viejos[n]) for n, c in nuevos if n in viejos and viejos[n] != c} == set()
    # Dos nombres con las mismas palabras son el mismo país: el lector de despachos los lee igual.
    por_palabras = {}
    for n, c in {*nuevos, *viejos.items()}:
        por_palabras.setdefault(tuple(re.findall(r"\w+", n)), set()).add(maria_generator.codigo_de_pais(f"{c:03d}"))
    assert {p: c for p, c in por_palabras.items() if len(c) > 1} == {}


@pytest.mark.skipif(not shutil.which("node"), reason="sin node")
def test_la_pantalla_reconoce_los_mismos_nombres_que_el_servidor():
    valores = [f"{prefijo}{n}" for c, i in _nombres().items() for idioma in i.values() for n in idioma
               for prefijo in ("", f"{c:03d} · ", "310 · ")]
    servidor = [str(maria_generator.codigo_de_pais(v) or "") for v in valores]
    assert [(v, p, s) for v, p, s in zip(valores, _de_la_pantalla(valores), servidor) if p != s] == []


@pytest.mark.parametrize("nombre", ["Netherlands", "The Netherlands", "NETHERLANDS", "Holland", "Holanda",
                                    "Países Bajos", "PAISES BAJOS"])
def test_paises_bajos_es_423_solo_con_423_o_con_434(nombre):
    assert [origen_iso2(f"{codigo}{nombre}") for codigo in ("", "423 ", "434 ", "423 · ", "434 - ")] == ["NL"] * 5
    assert (_origen_desde_factura(nombre), maria_generator.codigo_de_pais(nombre)) == ("NL", 423)
    assert [origen_iso2(f"{codigo} {nombre}") for codigo in (310, 406, 241)] == [None] * 3


# Lo común → ancho completo: «310 BR» → «３１０ ＢＲ».
ANCHO = {c - 0xFEE0: c for c in range(0xFF01, 0xFF5F)}


@pytest.mark.parametrize("escrito", ["310 BR", "310 CN", "310", "434", "203 BRASIL", "310 · CHINA", "BR", "CN",
                                     "USA", "212 UNITED STATES", "310 MADE IN USA"])
def test_la_letra_ancha_se_lee_como_la_comun(escrito):
    ancho = escrito.translate(ANCHO)
    assert ancho != escrito
    assert (origen_iso2(ancho), _origen_desde_factura(ancho)) == (origen_iso2(escrito), _origen_desde_factura(escrito))


# Nombres que son palabras comunes o parte de otro nombre → lo que guarda el lector de despachos
# (None: sin origen, con aviso). Sin código adelante, el de facturas lee lo mismo.
DIFICILES = {
    "GEORGIA": "GE", "351 GEORGIA": "GE", "212 GEORGIA": None, "212 NEW JERSEY": "US", "JERSEY": None,
    "TURKEY": "TR", "336 TURKEY": "TR", "436 TURKEY": "436", "212 TURKEY": None, "310 TURKEY": None,
    "CHAD": "TD", "111 CHAD": "TD", "212 CHAD": None,
    "NIGER": "NE", "NIGERIA": "NG", "130 NIGER": "NE", "131 NIGERIA": "NG", "130 NIGERIA": None, "131 NIGER": None,
    "GUINEA": "GN", "EQUATORIAL GUINEA": "GQ", "GUINEA-BISSAU": "GW", "PAPUA NEW GUINEA": "PG",
    "118 GUINEA": "GN", "119 EQUATORIAL GUINEA": "GQ", "156 GUINEA-BISSAU": "GW", "513 PAPUA NEW GUINEA": "PG",
    "118 EQUATORIAL GUINEA": None, "118 PAPUA NUEVA GUINEA": None, "119 GUINEA": None,
    "DOMINICA": "DM", "DOMINICAN REPUBLIC": "DO", "REPUBLICA DOMINICANA": "DO", "209 DOMINICAN REPUBLIC": "DO",
    "233 DOMINICA": "DM", "233 DOMINICAN REPUBLIC": None, "209 DOMINICA": None, "435 República Dominicana": None,
    "CONGO": "CG", "REPUBLIC OF THE CONGO": "CG", "DEMOCRATIC REPUBLIC OF THE CONGO": "CD", "DR CONGO": "CD",
    "108 REPUBLIC OF THE CONGO": "CG", "109 DEMOCRATIC REPUBLIC OF THE CONGO": "CD",
    "108 DEMOCRATIC REPUBLIC OF THE CONGO": None, "109 REPUBLIC OF THE CONGO": None, "109 CONGO": None,
    "KOREA": "KR", "SOUTH KOREA": "KR", "NORTH KOREA": "KP", "309 SOUTH KOREA": "KR", "308 NORTH KOREA": "KP",
    "309 KOREA, REPUBLIC OF": "KR", "308 KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF": "KP",
    "308 SOUTH KOREA": None, "309 NORTH KOREA": None, "308 KOREA": None,
    # Las de la tarea, «MADE IN USA» y nombres que contienen el de otro país.
    "310 UNITED STATES": None, "U.S.A.": "US", "212 U.S.A.": "US", "212 MADE IN USA": "US",
    "310 MADE IN USA": None, "426 NORTHERN IRELAND": "GB", "415 NORTHERN IRELAND": None, "IRELAND": "IE",
    "695 AMERICAN SAMOA": "695", "506 AMERICAN SAMOA": None, "506 SAMOA": "WS",
    "218 ESTADOS UNIDOS MEXICANOS": "MX", "212 ESTADOS UNIDOS MEXICANOS": None,
    "143 REPUBLICA DE SUDAFRICA": "143", "143 SUDAFRICA": None, "REPUBLIC OF SOUTH AFRICA": None,
    "695 SAMOA AMERICANA": "695", "683 UNITED STATES VIRGIN ISLANDS": "683", "241 NETHERLANDS ANTILLES": "241",
}


def test_los_nombres_dificiles_dan_su_pais_o_ninguno():
    assert {t: o for t, v in DIFICILES.items() if (o := origen_iso2(t)) != v} == {}
    sin_codigo = [t for t in DIFICILES if not t[0].isdigit()]
    assert {t: o for t in sin_codigo if (o := _origen_desde_factura(t)) != (DIFICILES[t] or "")} == {}
