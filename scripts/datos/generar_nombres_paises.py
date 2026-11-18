"""Genera `const NOMBRES` de proyecto_maria/static/v2/paises_maria.js: el nombre
corriente de cada país de la tabla oficial, en inglés y en castellano.

Uso (fuera del producto; pycountry NO es dependencia):
    python -m venv /tmp/venv-iso && /tmp/venv-iso/bin/pip install pycountry
    /tmp/venv-iso/bin/python scripts/datos/generar_nombres_paises.py

Los nombres salen de la norma ISO 3166-1 (nombre, nombre oficial y nombre común,
con su traducción al castellano) más los de uso corriente de EXTRAS. El país
de la tabla lo da su sigla de dos letras en ALIASES, o TERRITORIOS para los
que no tienen. tests/test_paises_nombres.py comprueba que ningún nombre
choque con el de otro país.
"""
import gettext
import importlib.metadata
import json
import pathlib
import re

import pycountry

RAIZ = pathlib.Path(__file__).resolve().parents[2]
JS = RAIZ / "proyecto_maria" / "static" / "v2" / "paises_maria.js"

# Códigos de la tabla sin sigla de dos letras. Afuera: Jersey y Guernsey (telas:
# «212 NEW JERSEY») y los territorios que la tabla no tiene aparte.
TERRITORIOS = {
    "PR": 223, "CV": 150, "VA": 431, "TL": 358, "AW": 242, "FK": 254, "PS": 357,
    "AI": 652, "AS": 695, "BM": 663, "CC": 673, "CK": 654, "CX": 672, "GI": 665,
    "GL": 666, "GU": 667, "IM": 676, "KY": 671, "MS": 686, "NF": 677, "NU": 687,
    "PF": 656, "PM": 680, "PN": 690, "SH": 694, "SJ": 696, "TC": 678, "TK": 699,
    "VG": 682, "VI": 683,
}

# Nombres de uso corriente que la norma no trae. Sin siglas de dos letras nuevas.
EXTRAS = {
    "US": (["USA", "U.S.A."], ["EE.UU.", "E.E.U.U.", "Estados Unidos de Norteamérica"]),
    "NL": (["Holland", "The Netherlands"], ["Holanda"]),
    "GB": (["Great Britain", "England", "Northern Ireland"],
           ["Inglaterra", "Gran Bretaña", "Irlanda del Norte"]),
    "RU": (["Russia"], ["Rusia"]),
    "TR": (["Turkey"], []),
    "KR": (["Republic of Korea"], ["República de Corea"]),
    "KP": ([], ["Corea del Norte"]),
    "CI": (["Ivory Coast"], ["Costa de Marfil"]),
    "MK": (["Macedonia"], []),
    "SZ": (["Swaziland"], ["Suazilandia"]),
    "MM": (["Burma"], []),
    "VA": (["Vatican", "Vatican City"], ["Vaticano", "Ciudad del Vaticano"]),
    "CV": (["Cape Verde"], []),
    "TL": (["East Timor"], []),
    "FK": (["Falkland Islands"], ["Islas Malvinas", "Malvinas"]),
    "PS": (["Palestine"], ["Palestina"]),
    "CD": (["Democratic Republic of the Congo", "DR Congo"], ["República Democrática del Congo"]),
    "BN": (["Brunei"], ["Brunéi"]),
    "AE": (["UAE", "U.A.E."], ["Emiratos Árabes"]),
    "SA": ([], ["Arabia Saudita"]),
    "MO": (["Macau"], []),
    "SH": (["Saint Helena"], []),
    "IR": ([], ["Irán"]),
    "TW": ([], ["Taiwán"]),
    "FM": (["Micronesia"], ["Micronesia"]),
}

# Nombres de la norma que no entran, con el porqué.
EXCLUIDOS = {
    "República de Sudáfrica",           # es el nombre de la tabla del 143, no del 159
    "República Popular Democrática de",  # traducción cortada de Corea del Norte
    "Islas Vírgenes, de EEUU.",          # traducción rota; queda «Islas Vírgenes de los Estados Unidos»
}


def _siglas(js: str) -> dict:
    aliases = json.loads(re.search(r"const ALIASES = (\{.*?\});", js).group(1))
    return {k: int(v) for k, v in aliases.items() if len(k) == 2 and k.isalpha()}


def _nombres(pais, es) -> tuple:
    norma = [getattr(pais, campo, None) for campo in ("name", "official_name", "common_name")]
    en = [n for n in norma if n]
    castellano = [es(n) for n in norma[:2] if n]
    extra_en, extra_es = EXTRAS.get(pais.alpha_2, ([], []))

    def limpios(nombres):
        con_y_sin_puntos = (forma for n in nombres if n not in EXCLUIDOS for forma in (n, n.replace(".", "")))
        return list(dict.fromkeys(con_y_sin_puntos))
    return limpios(en + extra_en), limpios(castellano + extra_es)


def main():
    js = JS.read_text(encoding="utf-8")
    codigos = {**_siglas(js), **TERRITORIOS}
    es = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["es"]).gettext
    nombres = {}
    for pais in pycountry.countries:
        if pais.alpha_2 in codigos:
            en, castellano = _nombres(pais, es)
            nombres[f"{codigos[pais.alpha_2]:03d}"] = {"en": en, "es": castellano}
    filas = ",\n".join(f"        {json.dumps(c)}: {json.dumps(nombres[c], ensure_ascii=False)}" for c in sorted(nombres))
    version = importlib.metadata.version("pycountry")
    bloque = (f"    // Generado por scripts/datos/generar_nombres_paises.py (pycountry {version}): no editar a mano.\n"
              f"    const NOMBRES = {{\n{filas}\n    }};\n")
    previo = re.compile(r"    // Generado por scripts/datos/generar_nombres_paises\.py.*?\n    \};\n", re.S)
    if previo.search(js):
        js = previo.sub(lambda _: bloque, js)
    else:
        js = re.sub(r"(    const ALIASES = .*?\n)", lambda m: m.group(1) + bloque, js, count=1)
    JS.write_text(js, encoding="utf-8")
    print(f"{len(nombres)} países escritos en {JS.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
