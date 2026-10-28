"""Qué sufijos de valor pide cada posición SIM y su unidad estadística
(SUFIJOS-1), del arancel de ARCA.

La tabla se arma con `scripts/import_arancel_sufijos.py` desde el ZIP del
Arancel Integrado (`sufijos_*.txt` y `nomenclador_*.txt`) y vive en
`data/sufijos_arca.json.gz`. No hay red: si la tabla falta o la posición no
está, no se completa nada y quien llama lo marca para el despachante.

La fecha del arancel viaja con cada consulta («arancel de ARCA del
07/10/2026»): donde se completa algo, la pantalla dice de dónde salió.
"""

from __future__ import annotations

import gzip
import json
import re
import unicodedata
from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from proyecto_maria.core.ncm_catalog import DATA_DIR

TABLA = DATA_DIR / "sufijos_arca.json.gz"
LARGO_SIM = 11  # dígitos de la posición SIM, sin la letra de control


def _digitos(codigo) -> str:
    return re.sub(r"\D", "", str(codigo or ""))


def _partes(posicion) -> tuple[str, str] | None:
    """(11 dígitos, letra de control o "") de una posición SIM escrita con o
    sin puntos y espacios; None si no es una (una NCM de 8, letras de más)."""
    texto = re.sub(r"[.\s]", "", str(posicion or "")).upper()
    partes = re.fullmatch(r"(\d{%d})([A-Z]?)" % LARGO_SIM, texto)
    return partes.groups() if partes else None


def parse_sufijos(lineas: Iterable[str]) -> dict[str, list[list[str]]]:
    """{nivel en dígitos: [[código, descripción], ...]} de `sufijos_*.txt`.

    Cada sufijo es `3@<nivel>@<código>@<norma>@<descripción>`; el nivel es un
    capítulo (`39`), una partida (`39.20`), una subpartida (`3920.43`) o una
    posición SIM sin letra (`3920.10.99.110`). Una línea que no empieza con
    `3@` es la descripción de la de arriba partida en dos: se une."""
    niveles: dict[str, list[list[str]]] = defaultdict(list)
    ultimo = None
    for linea in lineas:
        campos = linea.rstrip("\r\n").split("@")
        if len(campos) == 5 and campos[0] == "3":
            nivel, codigo = _digitos(campos[1]), campos[2].strip().upper()
            if not nivel or not re.fullmatch(r"[A-Z]{2}(?:[0-9]{2})?", codigo):
                raise ValueError(f"Sufijo que no se entiende: «{linea[:80]}»")
            ultimo = [codigo, " ".join(campos[4].split())]
            niveles[nivel].append(ultimo)
        elif linea.strip():
            if ultimo is None:
                raise ValueError(f"Continuación sin sufijo arriba: «{linea[:80]}»")
            ultimo[1] = f"{ultimo[1]} {' '.join(linea.split())}"
    return dict(niveles)


def parse_unidades(lineas: Iterable[str]) -> dict[str, list[str]]:
    """{posición SIM en dígitos: [letra de control, unidad estadística]} de
    `nomenclador_*.txt` (líneas `2@`; la unidad es el noveno campo)."""
    unidades = {}
    for linea in lineas:
        campos = linea.split("@")
        if len(campos) < 9 or campos[0] != "2":
            continue
        codigo = campos[1].strip()
        if len(_digitos(codigo)) != LARGO_SIM or not campos[8].strip():
            continue
        letra = codigo[-1].upper() if codigo[-1].isalpha() else ""
        unidades[_digitos(codigo)] = [letra, campos[8].strip()]
    return unidades


@lru_cache(maxsize=2)
def cargar(ruta: Path = TABLA) -> dict:
    """La tabla generada; vacía si no está o no se puede leer (entonces nada
    se completa)."""
    try:
        with gzip.open(ruta, "rt", encoding="utf-8") as fh:
            tabla = json.load(fh)
    except (OSError, EOFError, ValueError):
        return {}
    return tabla if isinstance(tabla, dict) else {}


def es_sim(posicion) -> bool:
    """¿Es una posición SIM completa (11 dígitos, con o sin la letra)?"""
    return _partes(posicion) is not None


def fuente(tabla: dict) -> str:
    """«arancel de ARCA del 07/10/2026», con la fecha de la tabla."""
    fecha = str(tabla.get("fecha") or "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        return "arancel de ARCA"
    anio, mes, dia = fecha.split("-")
    return f"arancel de ARCA del {dia}/{mes}/{anio}"


def escrita(posicion) -> str:
    """La posición SIM como la escribe el arancel: «3920.10.10.100F». Si no
    es una posición SIM, tal como vino."""
    partes = _partes(posicion)
    if not partes:
        return str(posicion or "").strip().upper()
    d, letra = partes
    return f"{d[:4]}.{d[4:6]}.{d[6:8]}.{d[8:]}{letra}"


def letra_de_control(posicion, tabla: dict | None = None) -> str:
    """La letra de control que el arancel le da a la posición, si la que
    vino es otra; "" si coincide, no vino o la posición no está."""
    tabla = cargar() if tabla is None else tabla
    partes = _partes(posicion)
    fila = (tabla.get("unidades") or {}).get(partes[0]) if partes else None
    if not fila or not partes[1] or not fila[0] or partes[1] == fila[0]:
        return ""
    return fila[0]


def consultar(posicion, tabla: dict | None = None) -> dict | None:
    """Lo que la tabla dice de una posición SIM, o None si no está (una NCM
    de 8 dígitos, una letra de control que no es la suya, una posición que
    el arancel no tiene o la tabla que falta).

    Devuelve la unidad estadística, los sufijos de valor libre (`AA`
    marca, `AI` código…) y los de opción cerrada agrupados (`PB01`,
    `PB02`…: se elige uno), con la fuente."""
    tabla = cargar() if tabla is None else tabla
    partes = _partes(posicion)
    fila = (tabla.get("unidades") or {}).get(partes[0]) if partes else None
    if not fila or letra_de_control(posicion, tabla):
        return None
    digitos = partes[0]
    texto = str(posicion or "").strip().upper()
    abiertos, cerrados = [], defaultdict(list)
    vistos = set()
    for largo in range(2, LARGO_SIM + 1):
        for codigo, descripcion in (tabla.get("sufijos") or {}).get(digitos[:largo], []):
            if codigo in vistos:
                continue
            vistos.add(codigo)
            if len(codigo) == 2:
                abiertos.append({"codigo": codigo, "descripcion": descripcion})
            else:
                cerrados[codigo[:2]].append({"codigo": codigo, "descripcion": descripcion})
    return {
        "posicion": texto,
        "unidad_estadistica": fila[1],
        "sufijos": abiertos,
        "opciones": [{"grupo": g, "opciones": ops} for g, ops in cerrados.items()],
        "fuente": fuente(tabla),
    }


def faltan(consulta: dict, presentes: Iterable[str]) -> list[str]:
    """Lo que la posición pide y el sufijo no trae, para decirlo. `presentes`
    son los códigos del sufijo (`AA`, `PB02`…); de una opción cerrada basta
    uno del grupo."""
    grupos = {str(c)[:2].upper() for c in presentes}
    lista = [f"{s['codigo']} ({s['descripcion']})" for s in consulta["sufijos"]
             if s["codigo"] not in grupos]
    for g in consulta["opciones"]:
        if g["grupo"] not in grupos:
            cuales = ", ".join(o["codigo"] for o in g["opciones"][:6])
            mas = "…" if len(g["opciones"]) > 6 else ""
            lista.append(f"{g['grupo']} (elegí uno: {cuales}{mas})")
    return lista


# Lo que la IA lee de la factura y a qué sufijo va. En todo el arancel `AA`
# es la marca, `AB` el modelo y `AI` el código de producto o artículo; los
# demás cambian de sentido según la posición (`ZA` es un espesor en una y
# una cilindrada en otra), así que no se completan solos.
COMPLETA = (("AA", ("marca",)), ("AB", ("modelo",)), ("AI", ("codigo_parte",)))


# Un número con decimales: un solo punto o coma entre dígitos, que no sea
# parte de una cadena como «1.2.3» (un código, no un número). [0-9] y no \d,
# que en Python también toma dígitos que no son ASCII.
_DECIMAL = r"(?<![0-9])(?<![0-9][.,])([0-9]+)[.,]([0-9]+)(?![.,]?[0-9])"
_DECIMAL_O_SIGNO = re.compile(rf"{_DECIMAL}|[^A-Za-z0-9 ]")


def caracteres_del_maria(texto) -> str:
    """Letras sin tilde, números, espacios y la coma de un número con
    decimales; lo demás, espacio. El MARIA rechazó guiones y puntos el 24/10
    y el despachante confirmó el 28/10 que un número puede llevar coma
    (SUFIJOS-2): «2.5» sale «2,5», no «2 5», que es otro número."""
    sin_tildes = "".join(c for c in unicodedata.normalize("NFKD", str(texto or ""))
                         if not unicodedata.combining(c))
    return _DECIMAL_O_SIGNO.sub(lambda m: f"{m[1]},{m[2]}" if m[1] else " ", sin_tildes)


def valor_de_sufijo(texto) -> str:
    """El valor tal como entra entre paréntesis, sin espacios de más."""
    return " ".join(caracteres_del_maria(texto).split())


def proponer(item: dict, consulta: dict | None, tope: int = 120) -> dict:
    """El sufijo que se propone para un renglón y lo que queda para el
    despachante. Sin consulta (la posición no está en la tabla) no se
    propone nada."""
    if not consulta:
        return {"sufijo": "", "completados": [], "faltan": []}
    pide = {s["codigo"] for s in consulta["sufijos"]}
    partes, completados = [], []
    for codigo, campos in COMPLETA:
        if codigo not in pide:
            continue
        valor = next((v for v in (valor_de_sufijo(item.get(c)) for c in campos) if v), "")
        if valor and len("-".join(partes + [f"{codigo}({valor})"])) + 1 <= tope:
            partes.append(f"{codigo}({valor})")
            completados.append(codigo)
    return {
        "sufijo": "-".join(partes) + "-" if partes else "",
        "completados": completados,
        "faltan": faltan(consulta, completados),
    }
