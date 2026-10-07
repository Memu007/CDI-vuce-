"""
Generador de archivos TXT en formato MARIA para Sistema SIM de AFIP.
"""
import json
import math
import re
import unicodedata
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

# Condiciones de venta de los grupos C y D de Incoterms. En estas, la
# informacion complementaria del SIM pide `GTOS-POS-FOB` (diferencia entre la
# condicion pactada y el FOB declarado). En EXW pide `GTOS-ANT-FOB` (gastos
# hasta el FOB). Los grupos E y F quedan afuera de la regla explicita, asi que
# ahi el importe se toma solo si el despachante lo declara.
_INCOTERMS_GRUPO_C_D = {"CFR", "CIF", "CPT", "CIP", "DAP", "DPU", "DDP", "DAT", "DAF", "DES", "DEQ", "DDU"}

# Códigos de país oficiales del Sistema MARIA (AFIP - "Códigos María").
# Fuente: TABLA PAISES V.0 25082010.xlsx (tabla oficial VUCE).
# Tabla anterior tenia ~30 países; ahora 207 + alias ISO 2 letras + inglés.
PAISES_INDEC = {
    # África
    "BURKINA FASO": 101, "BF": 101, "ARGELIA": 102, "DZ": 102,
    "BOTSWANA": 103, "BW": 103, "BURUNDI": 104, "BI": 104,
    "CAMERUN": 105, "CM": 105, "REP CENTROAFRICANA": 107, "CF": 107,
    "CONGO": 108, "CG": 108,
    "REP DEMOCRAT DEL CONGO EX ZAIRE": 109, "CD": 109,
    "COSTA DE MARFIL": 110, "CI": 110,
    "CHAD": 111, "TD": 111, "BENIN": 112, "BJ": 112,
    "EGIPTO": 113, "EG": 113, "GABON": 115, "GA": 115,
    "GAMBIA": 116, "GM": 116, "GHANA": 117, "GH": 117,
    "GUINEA": 118, "GN": 118, "GUINEA ECUATORIAL": 119, "GQ": 119,
    "KENYA": 120, "KE": 120, "LESOTHO": 121, "LS": 121,
    "LIBERIA": 122, "LR": 122, "LIBIA": 123, "LY": 123,
    "MADAGASCAR": 124, "MG": 124, "MALAWI": 125, "MW": 125,
    "MALI": 126, "ML": 126, "MARRUECOS": 127, "MA": 127,
    "MAURICIO,ISLAS": 128, "MU": 128, "MAURITANIA": 129, "MR": 129,
    "NIGER": 130, "NE": 130, "NIGERIA": 131, "NG": 131,
    "ZIMBABWE": 132, "ZW": 132, "RWANDA": 133, "RW": 133,
    "SENEGAL": 134, "SN": 134, "SIERRA LEONA": 135, "SL": 135,
    "SOMALIA": 136, "SO": 136, "SWAZILANDIA": 137, "SZ": 137,
    "SUDAN": 138, "SD": 138, "TANZANIA": 139, "TZ": 139,
    "TOGO": 140, "TG": 140, "TUNEZ": 141, "TN": 141,
    "UGANDA": 142, "UG": 142, "REPUBLICA DE SUDAFRICA": 143,
    "ZAMBIA": 144, "ZM": 144, "ANGOLA": 149, "AO": 149,
    "MOZAMBIQUE": 151, "MZ": 151, "SEYCHELLES": 152, "SC": 152,
    "DJIBOUTI": 153, "DJ": 153, "COMORAS": 155, "KM": 155,
    "GUINEA BISSAU": 156, "GW": 156,
    "STO TOME Y PRINCIPE": 157, "ST": 157, "NAMIBIA": 158, "NA": 158,
    "SUDAFRICA": 159, "ZA": 159, "ERITREA": 160, "ER": 160,
    "ETIOPIA": 161, "ET": 161,
    # América
    "ARGENTINA": 200, "AR": 200,
    "BARBADOS": 201, "BB": 201, "BOLIVIA": 202, "BO": 202,
    "BRASIL": 203, "BR": 203,
    "CANADA": 204, "CA": 204,
    "COLOMBIA": 205, "CO": 205,
    "COSTA RICA": 206, "CR": 206, "CUBA": 207, "CU": 207,
    "CHILE": 208, "CL": 208,
    "DOMINICANA,REP": 209, "DO": 209, "ECUADOR": 210, "EC": 210,
    "EL SALVADOR": 211, "SV": 211, "ESTADOS UNIDOS": 212, "US": 212, "USA": 212, "EEUU": 212,
    "GUATEMALA": 213, "GT": 213, "GUYANA": 214, "GY": 214,
    "HAITI": 215, "HT": 215, "HONDURAS": 216, "HN": 216,
    "JAMAICA": 217, "JM": 217, "MEXICO": 218, "MX": 218,
    "NICARAGUA": 219, "NI": 219, "PANAMA": 220, "PA": 220,
    "PARAGUAY": 221, "PY": 221,
    "PERU": 222, "PE": 222,
    "TRINIDAD Y TOBAGO": 224, "TT": 224,
    "URUGUAY": 225, "UY": 225,
    "VENEZUELA": 226, "VE": 226,
    "SURINAME": 232, "SR": 232, "DOMINICA": 233, "DM": 233,
    "SANTA LUCIA": 234, "LC": 234,
    "SAN VICENTE Y LAS GRANADINAS": 235, "VC": 235,
    "BELICE": 236, "BZ": 236,
    "ANTIGUA Y BARBUDA": 237, "AG": 237,
    "S CRISTOBAL Y NEVIS": 238, "KN": 238,
    "BAHAMAS": 239, "BS": 239, "GRANADA": 240, "GD": 240,
    # Asia
    "AFGANISTAN": 301, "AF": 301, "ARABIA SAUDITA": 302, "SA": 302,
    "BAHREIN": 303, "BH": 303,
    "MYANMAR(EX-BIRMANIA)": 304, "MM": 304, "BUTAN": 305, "BT": 305,
    "CAMBODYA(EX-KAMPUCHE": 306, "KH": 306,
    "SRI LANKA": 307, "LK": 307, "COREA DEMOCRATICA": 308, "KP": 308,
    "COREA REPUBLICANA": 309, "KR": 309,
    "CHINA": 310, "CN": 310,
    "CHIPRE": 311, "CY": 311, "FILIPINAS": 312, "PH": 312,
    "TAIWAN": 313, "TW": 313,
    "INDIA": 315, "IN": 315,
    "INDONESIA": 316, "ID": 316,
    "IRAK": 317, "IQ": 317, "IRAN": 318, "IR": 318,
    "ISRAEL": 319, "IL": 319,
    "JAPON": 320, "JP": 320,
    "JORDANIA": 321, "JO": 321, "QATAR": 322, "QA": 322,
    "KUWAIT": 323, "KW": 323, "LAOS": 324, "LA": 324,
    "LIBANO": 325, "LB": 325, "MALASIA": 326, "MY": 326,
    "MALDIVAS ISLAS": 327, "MV": 327, "OMAN": 328, "OM": 328,
    "MONGOLIA": 329, "MN": 329,
    "NEPAL": 330, "NP": 330, "EMIRATOS ARABES,UNID": 331, "AE": 331,
    "PAKISTAN": 332, "PK": 332,
    "SINGAPUR": 333, "SG": 333, "SIRIA": 334, "SY": 334,
    "THAILANDIA": 335, "TH": 335,
    "TURQUIA": 336, "TR": 336, "VIETNAM": 337, "VN": 337,
    "REG ADM ESP DE CHINA": 341, "HK": 341, "MACAO(REG ADM ESPEC)": 344, "MO": 344,
    "BANGLADESH": 345, "BD": 345, "BRUNEI": 346, "BN": 346,
    "REPUBLICA DE YEMEN": 348, "YE": 348,
    "ARMENIA": 349, "AM": 349, "AZERBAIJAN": 350, "AZ": 350,
    "GEORGIA": 351, "GE": 351,
    "KAZAJSTAN": 352, "KZ": 352, "KIRGUIZISTAN": 353, "KG": 353,
    "TAYIKISTAN": 354, "TJ": 354,
    "TURKMENISTAN": 355, "TM": 355, "UZBEKISTAN": 356, "UZ": 356,
    # Europa
    "ALBANIA": 401, "AL": 401, "ALEMANIA FEDERAL": 402, "ALEMANIA ORIENTAL": 403,
    "ANDORRA": 404, "AD": 404, "AUSTRIA": 405, "AT": 405,
    "BELGICA": 406, "BE": 406, "BULGARIA": 407, "BG": 407,
    "CHECOSLOVAQUIA": 408, "DINAMARCA": 409, "DK": 409,
    "ESPANA": 410, "ES": 410,
    "FINLANDIA": 411, "FI": 411, "FRANCIA": 412, "FR": 412,
    "GRECIA": 413, "GR": 413, "HUNGRIA": 414, "HU": 414,
    "IRLANDA": 415, "IE": 415, "ISLANDIA": 416, "IS": 416,
    "ITALIA": 417, "IT": 417,
    "LIECHTENSTEIN": 418, "LI": 418, "LUXEMBURGO": 419, "LU": 419,
    "MALTA": 420, "MT": 420,
    "MONACO": 421, "MC": 421, "NORUEGA": 422, "NO": 422,
    "PAISES BAJOS": 423, "NL": 423,
    "POLONIA": 424, "PL": 424, "PORTUGAL": 425, "PT": 425,
    "REINO UNIDO": 426, "GB": 426, "UK": 426,
    "RUMANIA": 427, "RO": 427, "SAN MARINO": 428, "SM": 428,
    "SUECIA": 429, "SE": 429, "SUIZA": 430, "CH": 430,
    "HOLANDA": 434, "NL": 434, "ALEMANIA,REP FED": 438, "DE": 438,
    "BIELORRUSIA": 439, "BY": 439, "ESTONIA": 440, "EE": 440,
    "LETONIA": 441, "LV": 441,
    "LITUANIA": 442, "LT": 442, "MOLDAVIA": 443, "MD": 443,
    "RUSIA": 444, "RU": 444, "UCRANIA": 445, "UA": 445,
    "BOSNIA HERZEGOVINA": 446, "BA": 446, "CROACIA": 447, "HR": 447,
    "ESLOVAQUIA": 448, "SK": 448,
    "ESLOVENIA": 449, "SI": 449, "MACEDONIA": 450, "MK": 450,
    "REP CHECA": 451, "CZ": 451,
    "MONTENEGRO": 453, "ME": 453, "SERBIA": 454, "RS": 454,
    # Oceanía
    "AUSTRALIA": 501, "AU": 501, "NAURU": 503, "NR": 503,
    "NUEVA ZELANDIA": 504, "NZ": 504,
    "VANATU": 505, "VU": 505, "SAMOA OCCIDENTAL": 506, "WS": 506,
    "FIJI, ISLAS": 512, "FJ": 512,
    "PAPUA NUEVA GUINEA": 513, "PG": 513, "KIRIBATI, ISLAS": 514, "KI": 514,
    "MICRONESIA,EST FEDER": 515, "FM": 515, "PALAU": 516, "PW": 516,
    "TUVALU": 517, "TV": 517,
    "SALOMON,ISLAS": 518, "SB": 518, "TONGA": 519, "TO": 519,
    "MARSHALL,ISLAS": 520, "MH": 520, "MARIANAS,ISLAS": 521, "MP": 521,
}

# Alias en ingles / variantes de escritura -> MISMO codigo ya verificado arriba.
PAISES_ALIAS = {
    "Brazil": 203, "Germany": 438, "Japan": 320, "Spain": 410,
    "France": 412, "Italy": 417,
    "England": 426, "Great Britain": 426, "United Kingdom": 426,
    "Korea": 309, "South Korea": 309, "North Korea": 308,
    "China (Mainland)": 310, "Mainland China": 310,
    "P.R. China": 310, "PR China": 310, "RP China": 310,
    "Republica Popular China": 310, "República Popular China": 310,
    "Estados Unidos de America": 212, "United States of America": 212,
    "EE.UU.": 212, "EEUU.": 212,
    "Canada": 204, "Canadá": 204, "Mexico": 218, "México": 218,
    "Peru": 222, "Perú": 222, "Taiwan": 313, "Taiwán": 313,
    "Japón": 320, "España": 410, "Alemania": 438,
    "Tailandia": 335, "Thailand": 335, "Malasia": 326, "Malaysia": 326,
    "Corea": 309, "Corea del Sur": 309, "Corea del Norte": 308,
    "Argentina": 200, "Bolivia": 202, "Chile": 208, "Colombia": 205,
    "Ecuador": 210, "Paraguay": 221, "Uruguay": 225, "Venezuela": 226,
}
PAISES_INDEC = {**PAISES_INDEC, **PAISES_ALIAS}


def _normalizar_pais(pais: str) -> str:
    """Normaliza un nombre/código de país para comparar sin sorpresas:
    mayúsculas, sin acentos, sin puntos, espacios colapsados.
    Ej: 'EE.UU.' -> 'EEUU', 'España' -> 'ESPANA', 'P.R. China' -> 'PR CHINA'.
    """
    if not pais:
        return ""
    s = unicodedata.normalize("NFKD", str(pais))
    s = "".join(c for c in s if not unicodedata.combining(c))  # saca acentos
    s = s.upper().replace(".", " ")
    s = " ".join(s.split())  # colapsa espacios
    return s


# Lookup normalizado precomputado (clave normalizada -> código).
_PAISES_NORM = {_normalizar_pais(k): v for k, v in PAISES_INDEC.items()}

# Códigos de Tipo de Unidades oficiales del Sistema MARIA (AFIP).
# Solo las unidades de comercio mas comunes; el resto cae al default 07 (UNIDAD).
UNIDADES_MARIA = {
    "01": "01",  # passthrough si ya viene el codigo
    "kg": "01", "kgs": "01", "kilo": "01", "kilos": "01",
    "kilogramo": "01", "kilogramos": "01",
    "m": "02", "mt": "02", "mts": "02", "metro": "02", "metros": "02",
    "m2": "03", "metro cuadrado": "03",
    "m3": "04", "metro cubico": "04",
    "l": "05", "lt": "05", "lts": "05", "litro": "05", "litros": "05",
    "u": "07", "un": "07", "und": "07", "unid": "07",
    "unidad": "07", "unidades": "07",
    "pc": "07", "pcs": "07", "pieza": "07", "piezas": "07",
    "pieces": "07", "unit": "07", "units": "07", "ea": "07", "each": "07",
    "par": "08", "pares": "08", "pair": "08", "pairs": "08",
    "docena": "09", "docenas": "09", "dozen": "09",
    "millar": "11", "millares": "11",
    "gr": "14", "gramo": "14", "gramos": "14",
    "ton": "29", "tn": "29", "tonelada": "29", "toneladas": "29",
}


def get_unidad_codigo(unidad: str) -> str:
    """Mapea una unidad de medida a su código oficial MARIA (2 dígitos).
    Default: '07' (UNIDAD) si no se reconoce. Antes estaba hardcodeado a '07'
    para TODO, declarando "unidades" aunque la mercaderia fuera por kg/litro/etc.
    """
    if not unidad:
        return "07"
    clave = str(unidad).strip().lower()
    if clave.isdigit():  # ya vino el codigo numerico
        return clave.zfill(2)
    return UNIDADES_MARIA.get(clave, "07")


PAIS_DEFAULT_IMPORT = 310  # China (codigo oficial MARIA) cuando no se reconoce


# --- Lo que decide el despachante (MARIA-4) ------------------------------
# Estado de la mercadería (CARTUSO), por producto. Nombres del despachante
# (respuesta 1, 2026-10-06 21:20); el orden → código 1 a 6 lo confirma la
# prueba en su Kit. Los archivos reales: el de 2026 trae 2 con origen China y
# el de 2025, 3 con origen Argentina. Única copia de esta tabla.
ESTADOS_MERCADERIA = {
    1: "Nuevo sin uso argentino",
    2: "Nuevo sin uso importado",
    3: "Sin uso argentino",
    4: "Sin uso importado",
    5: "Usado argentino (incluye reacondicionado)",
    6: "Usado importado (incluye reacondicionado)",
}
ESTADO_POR_DEFECTO_IMPORTADO = 2
# Los nombres dicen si la mercadería es argentina o importada: el estado
# tiene que corresponder al origen (devolución de la PM sobre MARIA-4).
ESTADOS_ARGENTINOS = {1, 3, 5}
ESTADOS_IMPORTADOS = {2, 4, 6}

# IVA adicional (IVAADICIONAL1): reventa o uso particular (respuesta 2,
# 21:34; archivo de 2026). La reducción o exclusión es una «ventaja» que se
# elige en el Kit (22:12): no va en el TXT.
IVA_ADICIONAL = {"NO_VALIDA": "Reventa", "IVAAD1": "Uso particular"}
IVA_ADICIONAL_POR_DEFECTO = "NO_VALIDA"

# Empresa de digitalización (ARDIG-CUIT-PSAD), por operación (respuesta 5,
# 21:42 y 22:15; los dos archivos reales).
EMPRESAS_DIGITALIZACION = {"PSAD06": "Modoc", "PSAD01": "Lakaut"}
EMPRESA_DIGITALIZACION_POR_DEFECTO = "PSAD06"

PAIS_ARGENTINA = 200

# MARIA-3. Condiciones en las que se declaran los gastos anteriores al FOB
# (`GTOS-ANT-FOB`): EXW por la nota del SIM y el archivo real de 2026; FCA por
# la respuesta 6 del despachante; FAS por la misma regla (la diferencia entre
# el FOB y la condición pactada es anterior al FOB).
INCOTERMS_GASTOS_ANTERIORES = {"EXW", "FCA", "FAS"}


# Tope de un importe (gastos, flete, seguro): más que esto no es un importe,
# es un error de carga (devolución de MARIA-3: «1e308» llegaba al TXT). Un
# billón deja pasar montos reales en monedas de poco valor (CLP, JPY).
IMPORTE_MAXIMO = 1_000_000_000_000


def importe_valido(valor, nombre: str):
    """El importe como número, o None si no vino. Un importe no finito,
    negativo o absurdo es un error con mensaje propio (400)."""
    if valor is None:
        return None
    try:
        importe = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{nombre}: «{str(valor)[:20]}» no es un importe.")
    if not math.isfinite(importe) or importe < 0 or importe > IMPORTE_MAXIMO:
        raise ValueError(
            f"{nombre}: «{str(valor)[:20]}» no es un importe válido "
            f"(entre 0 y {IMPORTE_MAXIMO:,}).".replace(",", ".")
        )
    return importe


def _importe_de_gastos(valor, campo: str):
    return importe_valido(valor, f"Gastos ({campo})")


def gastos_fob_para_el_txt(incoterm, gastos_fob=None, gastos_anteriores_fob=None):
    """Importe de gastos respecto del FOB que va al TXT, o None.

    `gastos_fob` explícito manda (como antes). Si no, los gastos anteriores al
    FOB de la pantalla van sólo con EXW, FCA o FAS, y sólo desde un centavo:
    un 0 o un campo vacío no se declara (se avisa en los supuestos). Un
    importe inválido en cualquiera de los dos es un error."""
    explicito = _importe_de_gastos(gastos_fob, "gastos_fob")
    anteriores = _importe_de_gastos(gastos_anteriores_fob, "gastos anteriores a FOB")
    if explicito is not None:
        return explicito
    if str(incoterm or "").strip().upper() not in INCOTERMS_GASTOS_ANTERIORES:
        return None
    if anteriores is None or round(anteriores, 2) <= 0:
        return None
    return anteriores


def fecha_de_la_factura(raw) -> str:
    """Fecha de emisión en DD/MM/AAAA, o "" si no es una fecha.

    Acepta DD/MM/AAAA (día y mes de una o dos cifras), DD/MM/AA (año 20AA) y
    AAAA-MM-DD, sólo con cifras 0-9. Sin una fecha válida no se genera
    (devolución de MARIA-3): nunca se pone la de hoy."""
    texto = str(raw or "").strip()
    m = (re.fullmatch(r"([0-9]{1,2})/([0-9]{1,2})/([0-9]{4}|[0-9]{2})", texto)
         or re.fullmatch(r"([0-9]{4})-([0-9]{2})-([0-9]{2})", texto))
    if not m:
        return ""
    if "-" in texto:
        anio, mes, dia = (int(g) for g in m.groups())
    else:
        dia, mes, anio = (int(g) for g in m.groups())
        if len(m.group(3)) == 2:
            anio += 2000          # una factura de «69» es de 2069, no de 1969
    try:
        fecha = datetime(anio, mes, dia)
    except ValueError:
        return ""
    # Un año como 0026 no es una fecha de factura.
    return fecha.strftime("%d/%m/%Y") if fecha.year >= 1900 else ""


_PAISES_PANTALLA = Path(__file__).resolve().parents[1] / "static" / "v2" / "paises_maria.js"


@lru_cache(maxsize=1)
def codigos_tabla_oficial() -> frozenset:
    """Los códigos de país de la tabla oficial MARIA (TABLA PAISES V.0
    25082010.xlsx, 309 países). Una sola copia: la que usa la pantalla."""
    js = _PAISES_PANTALLA.read_text(encoding="utf-8")
    m = re.search(r"const COUNTRIES = (\[.*?\]);", js)
    if not m:
        raise RuntimeError(f"No se encontró la tabla de países (const COUNTRIES) en {_PAISES_PANTALLA}")
    return frozenset(int(p["code"]) for p in json.loads(m.group(1)))


def _codigo_de_la_tabla(texto: str) -> bool:
    """Un código de país: sólo cifras 0-9 y en la tabla oficial («²», «٢٢٢» o
    «99999» no son países)."""
    return bool(re.fullmatch(r"[0-9]+", texto)) and int(texto) in codigos_tabla_oficial()


def procedencia_de(item: dict) -> str:
    """La procedencia propia del producto: la primera no vacía entre
    `pais_procedencia` y `procedencia` (una en blanco no tapa la otra)."""
    for clave in ("pais_procedencia", "procedencia"):
        valor = str(item.get(clave) or "").strip()
        if valor:
            return valor
    return ""


def _estado_item(item: dict, idx, pais_codigo: int) -> int:
    """Estado (CARTUSO) del ítem: el elegido, o 2 si el origen es extranjero.
    Con origen argentino no hay valor por defecto: no se inventa."""
    raw = item.get("estado")
    desc = str(item.get("descripcion") or "").strip()[:40]
    idx = f"{idx} ({desc})" if desc else idx
    if raw in (None, ""):
        if pais_codigo == PAIS_ARGENTINA:
            raise ValueError(
                f"Ítem {idx}: el origen es argentino; elegí el estado de la mercadería "
                f"(no hay uno por defecto)."
            )
        return ESTADO_POR_DEFECTO_IMPORTADO
    try:
        estado = int(str(raw).strip())
    except ValueError:
        estado = 0
    if estado not in ESTADOS_MERCADERIA:
        raise ValueError(f"Ítem {idx}: estado de la mercadería «{raw}» no válido (1 a 6).")
    argentino = pais_codigo == PAIS_ARGENTINA
    if (argentino and estado in ESTADOS_IMPORTADOS) or (not argentino and estado in ESTADOS_ARGENTINOS):
        raise ValueError(
            f"Ítem {idx}: el estado «{ESTADOS_MERCADERIA[estado]}» no corresponde al origen "
            f"({'argentino' if argentino else 'extranjero'}); elegí otro."
        )
    return estado


def _iva_adicional(valor, donde: str) -> str:
    codigo = str(valor or "").strip().upper()
    if codigo not in IVA_ADICIONAL:
        raise ValueError(f"{donde}: IVA adicional «{valor}» no válido (NO_VALIDA o IVAAD1).")
    return codigo


def pais_reconocido(pais) -> bool:
    """True si el país se reconoce con certeza (código numérico o match exacto
    en la tabla verificada). NO cuenta el fallback por prefijo ni el default,
    que son adivinanzas. Sirve para que el sistema AVISE en vez de meter un
    código de origen errado en el TXT aduanero (ej: 'XX', 'Vietnam').
    """
    if pais is None or str(pais).strip() == "":
        return False
    texto = str(pais).strip()
    if any(c.isdigit() for c in texto):
        return _codigo_de_la_tabla(texto)
    return _normalizar_pais(pais) in _PAISES_NORM


def pais_de_la_tabla(pais) -> bool:
    """Como `pais_reconocido`, pero un código numérico tiene que estar en la
    tabla oficial de la pantalla (MARIA-3, procedencia: «99999» no es un país)."""
    return pais_reconocido(pais)


def get_pais_codigo(pais: str) -> int:
    """Obtiene el código de país oficial MARIA para un nombre/código.

    Estrategia: normaliza (mayúsculas, sin acentos ni puntos) y busca match
    EXACTO primero (evita la colisión histórica donde 'China' devolvía Chile
    y 'España' devolvía Estados Unidos). Si no hay exacto, prueba prefijo
    estricto (>=4 chars) como último recurso. Si nada matchea, devuelve el
    default; usar `pais_reconocido()` para detectar ese caso y avisar.
    """
    if not pais:
        return PAIS_DEFAULT_IMPORT

    # Si ya es un número, devolverlo
    if re.fullmatch(r"[0-9]+", str(pais).strip()):
        return int(str(pais).strip())

    norm = _normalizar_pais(pais)
    # 1) Match exacto normalizado
    if norm in _PAISES_NORM:
        return _PAISES_NORM[norm]
    # 2) Fallback por prefijo estricto (>=4 chars) solo si no hubo exacto
    if len(norm) >= 4:
        prefijo = norm[:4]
        for key_norm, code in _PAISES_NORM.items():
            if key_norm.startswith(prefijo):
                return code

    return PAIS_DEFAULT_IMPORT


def _exacto(valor) -> Decimal:
    """El número escrito, en decimal exacto: 2,675 es 2,675 y no su
    aproximación binaria. No finito o fuera del tope: ValueError (400)."""
    if isinstance(valor, Decimal):
        numero = valor
    else:
        crudo = float(valor or 0)
        if not math.isfinite(crudo):
            raise ValueError(f"Importe «{valor}» no válido: revisá cantidades y valores.")
        numero = Decimal(repr(crudo))
    if not numero.is_finite() or abs(numero) > IMPORTE_MAXIMO:
        raise ValueError(f"Importe «{valor}» no válido: revisá cantidades y valores.")
    return numero


def centavos(valor) -> Decimal:
    """Un importe del TXT al centavo, con la mitad hacia arriba (MARIA-5)."""
    return _exacto(valor).quantize(Decimal("0.01"), ROUND_HALF_UP)


def valor_de_la_linea(item: dict) -> Decimal:
    """El valor de una línea sin redondear: el valor total, o cantidad ×
    unitario multiplicados en decimal exacto (3 × 3,335 = 10,005)."""
    if item.get('valor_total'):
        valor = _exacto(item['valor_total'])
    else:
        valor = _exacto(_exacto(item.get('cantidad', 1)) * _exacto(item.get('valor_unitario', 0)))
    if valor < 0:
        raise ValueError(f"Valor «{valor}» negativo: revisá cantidades y valores.")
    return valor


def repartir(total: Decimal, pesos: list) -> list:
    """Reparte `total` (al centavo) en proporción a `pesos`, de modo que la
    suma dé exactamente `total` (MARIA-5). Cada parte se trunca al centavo y
    los centavos que faltan van a las de mayor resto; si empatan, a la de
    mayor peso y después a la primera."""
    pesos = [Fraction(Decimal(str(p))) for p in pesos]
    if any(p < 0 for p in pesos):
        raise ValueError("No se puede repartir sobre un valor negativo.")
    suma = sum(pesos)
    if suma <= 0 or not pesos:
        return [Decimal("0.00")] * len(pesos)
    total_c = int(total * 100)
    partes = [total_c * p / suma for p in pesos]
    enteras = [int(x) for x in partes]
    orden = sorted(range(len(pesos)), key=lambda i: (-(partes[i] - enteras[i]), -pesos[i], i))
    for i in orden[:total_c - sum(enteras)]:
        enteras[i] += 1
    return [Decimal(c) / 100 for c in enteras]


def _fob_de(item: dict) -> Decimal:
    """El FOB de una línea al centavo (MARIA-5)."""
    return centavos(valor_de_la_linea(item))


def peso_de_la_linea(item: dict) -> float:
    """El peso neto total de la línea, que va en QARTKGRNET (MARIA-5; respuesta
    3 del despachante). `peso_kg`, si viene, ya es el total (así lo mandan la
    v1 y los archivos reales); si no, `peso_unitario` × cantidad (la v2)."""
    total = item.get('peso_kg')
    try:
        if total not in (None, ''):
            return float(total or 0)
        return float(item.get('peso_unitario') or 0) * float(item.get('cantidad', 1) or 0)
    except (TypeError, ValueError):
        raise ValueError(f"El peso «{str(total if total not in (None, '') else item.get('peso_unitario'))[:20]}» "
                         f"de «{str(item.get('descripcion') or '')[:40]}» no es un número.")


def peso_valido(peso, donde) -> float:
    """El peso neto de la línea para QARTKGRNET, con la misma guarda que los
    importes (devolución de MARIA-5): no finito, negativo, por encima del tope
    o que redondea a 0.000 es un error con mensaje propio (400)."""
    try:
        kilos = float(peso)
    except (TypeError, ValueError):
        raise ValueError(f"Item {donde}: el peso «{str(peso)[:20]}» no es un número.")
    if not math.isfinite(kilos):
        raise ValueError(f"Item {donde}: el peso «{str(peso)[:20]}» no es un número válido.")
    if kilos > IMPORTE_MAXIMO:
        raise ValueError(
            f"Item {donde}: el peso «{str(peso)[:20]}» no es válido: pasa el tope de "
            f"{IMPORTE_MAXIMO:,} kg (revisá el peso y la cantidad).".replace(",", ".")
        )
    if kilos < 0:
        raise ValueError(f"Item {donde}: el peso «{str(peso)[:20]}» es negativo.")
    if round(kilos, 3) <= 0:
        raise ValueError(
            f"Item {donde}: el peso «{str(peso)[:20]}» no es válido: tiene que ser "
            f"de al menos 0.001 kg (revisá el peso y la cantidad)."
        )
    return kilos


def fob_total_del_txt(items: list, grupos: list | None = None) -> Decimal:
    """El MDDTFOB que va a salir en el TXT: los productos de un grupo suman su
    valor y la línea se redondea una vez; el resto, cada uno al centavo. La
    validación muestra este número (devolución de MARIA-5: una sola cuenta)."""
    grupos = grupos if grupos is not None else [it.get('grupo_id') for it in items]
    lineas: dict = {}
    for n, (item, gid) in enumerate(zip(items, grupos)):
        clave = ('grupo', gid) if gid is not None else ('item', n)
        lineas[clave] = lineas.get(clave, Decimal(0)) + valor_de_la_linea(item)
    return sum((centavos(v) for v in lineas.values()), Decimal('0.00'))


def generate_maria_txt(operation_id: str, items: list, 
                       moneda: str = "DOL", 
                       incoterm: str = "FOB",
                       cuit_agr: str = "",
                       vendedor_nombre: str = "",
                       vendedor_id: str = "",
                       comprador_nombre: str = "",
                       comprador_cuit: str = "",
                       comprador_domicilio: str = "",
                       comprador_fecha_inic_activ: str = "",
                       flete: float = 0,
                       seguro: float = 0,
                       # Gastos respecto del FOB (ver bloque [CPL] mas abajo).
                       # None = calcular/omitir segun la condicion de venta.
                       gastos_fob: float | None = None,
                       # Transport data
                       bl_numero: str = "",
                       puerto_origen: str = "",
                       puerto_destino: str = "ARBUE",
                       buque_nombre: str = "",
                       viaje_numero: str = "",
                       fecha_embarque: str = "",
                       fecha_emision: str = "",
                       # Sufijo de valor [SBT]. OBLIGATORIO: específico de cada importador.
                       sbt_sufijo_valor: str = "",
                       # Container data
                       contenedor_numero: str = "",
                       contenedor_tipo: str = "",
                       contenedor_peso: float = 0,
                       # Aduana config
                       aduana_codigo: str = "001",
                       tipo_destinacion: str = "IC04",
                       # Lo que decide el despachante (MARIA-4)
                       banco_bcra: str = "",
                       empresa_digitalizacion: str = EMPRESA_DIGITALIZACION_POR_DEFECTO,
                       iva_adicional: str = IVA_ADICIONAL_POR_DEFECTO) -> str:
    """
    Genera archivo TXT en formato MARIA.
    
    Args:
        operation_id: ID de la operación (ej: "001790125")
        items: Lista de items con campos:
            - ncm/pieza: Código NCM
            - cantidad: Cantidad
            - valor_unitario: Precio unitario
            - valor_total: Precio total (opcional, se calcula)
            - peso_kg: Peso neto total de la línea en kg (o peso_unitario)
            - pais_origen/origen: País de origen
        moneda: Código de moneda (DOL, EUR)
        incoterm: Término comercial (FOB, DDP, CIF, EXW)
        cuit_agr: CUIT del despachante (opcional)
        vendedor_nombre: Nombre del proveedor/vendedor
        vendedor_id: ID/CUIT del vendedor
        comprador_nombre: Nombre del importador
        comprador_cuit: CUIT del importador
        flete: Costo de flete en USD
        seguro: Costo de seguro en USD
    
    Returns:
        String con contenido del archivo TXT (CRLF line endings)
    """
    lines = []

    # MARIA-4: validar lo que decide el despachante antes de armar nada.
    banco_bcra = str(banco_bcra or "").strip()
    if banco_bcra and not re.fullmatch(r"[0-9]{3}", banco_bcra):
        raise ValueError(f"Banco «{banco_bcra}» no válido: va el código de entidad del BCRA (3 dígitos).")
    empresa_digitalizacion = str(empresa_digitalizacion or EMPRESA_DIGITALIZACION_POR_DEFECTO).strip().upper()
    if empresa_digitalizacion not in EMPRESAS_DIGITALIZACION:
        raise ValueError(
            f"Empresa de digitalización «{empresa_digitalizacion}» no válida (PSAD06 Modoc o PSAD01 Lakaut)."
        )
    iva_adicional = _iva_adicional(iva_adicional or IVA_ADICIONAL_POR_DEFECTO, "Operación")
    # Con C y D los gastos salen de flete + seguro: un importe inválido no
    # llega al TXT por ese camino (revisión de la devolución de MARIA-3).
    flete = centavos(importe_valido(flete or 0, "Flete"))
    seguro = centavos(importe_valido(seguro or 0, "Seguro"))

    # === [DDT] Cabecera ===
    # Normalizamos config de aduana/destinacion con defaults seguros (Ezeiza IC04)
    aduana_codigo = (str(aduana_codigo or "").strip() or "001")[:3]
    tipo_destinacion = (str(tipo_destinacion or "").strip().upper() or "IC04")[:4]

    lines.append("[DDT]")
    lines.append(f"ISTA={tipo_destinacion}")
    lines.append(f"IDSO={operation_id}")
    lines.append("CDDTEXE=01")
    lines.append(f"CDDTBUR={aduana_codigo}")
    lines.append(f"CDDTTYPDEC={tipo_destinacion}")
    if cuit_agr:
        lines.append(f"CDDTAGR={cuit_agr}")
    lines.append("CDDTIMPEXP=I")
    if vendedor_nombre:
        # Extraer solo el nombre si viene con ID entre parentesis (hack para sample)
        lines.append(f"LDDTNOMFOD={vendedor_nombre}")
    if comprador_cuit:
        lines.append(f"NDDTIMMIOE={comprador_cuit}")
    if comprador_nombre:
        lines.append(f"LDDTNOMIOE={comprador_nombre}")
    
    # Monedas (Hardcoded DOL como en sample si es dolar)
    dev_divisa = moneda if moneda != 'DOL' else 'DOL'
    lines.append(f"CDDTDEVASS={dev_divisa}")
    lines.append(f"CDDTDEVFLE={dev_divisa}")
    lines.append(f"CDDTDEVFOB={dev_divisa}")
    
    lines.append(f"MDDTASS={seguro:.2f}")
    lines.append(f"MDDTFLE={flete:.2f}")
    # El FOB de la carátula es la suma de los ítems ya agrupados: se escribe
    # al final, cuando se conocen.
    linea_fob_total = len(lines)
    lines.append("MDDTFOB=")
    
    # Transit ID (si existe, usar operation_id prefix)
    lines.append(f"NDDTIMMTRN={operation_id[:5] if len(operation_id)>=5 else '00000'}")
    
    lines.append(f"CDDTINCOTE={incoterm}")
    # Fecha de embarque: solo si hay dato real. Antes se inventaba hoy+365, lo que
    # metia una fecha falsa en la declaracion. Mejor omitir y que el despachante
    # la complete en el Kit SIM. (El TXT es clave=valor, omitir una linea es seguro.)
    fecha_emb_header = str(fecha_embarque or "").strip()
    if fecha_emb_header:
        lines.append(f"DDDTVENEMB={fecha_emb_header}")
    lines.append("CDDTIVA=S")
    lines.append("")
    
    # === [CPL] Campos Complementarios Globales ===
    
    # 1. Ref Interna
    lines.append("[CPL]")
    lines.append("NART=0000")
    lines.append("ICPLDIF=S")
    lines.append("CCPL=NRO.REF.INTERNA ")
    lines.append(f"MCPL={operation_id:<40}")
    lines.append("")
    
    # 2. Fecha de emisión de la factura. Sin una fecha válida no se genera
    # (devolución de MARIA-3): antes salía la fecha de hoy (D15).
    fecha_factura = fecha_de_la_factura(fecha_emision)
    if not fecha_factura:
        leida = str(fecha_emision or "").strip()[:20]
        raise ValueError(
            "Falta la fecha de emisión de la factura (DD/MM/AAAA)"
            + (f": «{leida}» no es una fecha" if leida else "")
            + ". Sin ella no se genera el TXT."
        )

    # Año de dos dígitos para el IEXT de cada ítem (`00272-01/26`). Sale del
    # año de la factura, que a esta altura es válida.
    #
    # Antes estaba escrito a mano como "25". Silenciosamente iba a poner /25 en
    # toda declaración generada de 2026 en adelante: el TXT sale igual, no
    # falla nada, y el error aparece recién en la aduana.
    anio_iext = fecha_factura[-2:]
    lines.append("[CPL]")
    lines.append("NART=0000")
    lines.append("ICPLDIF=D")
    lines.append("CCPL=FECHAEMISIONFACT")
    lines.append(f"MCPL={fecha_factura:<40}")
    lines.append("")
    
    # 3. Gastos respecto del FOB.
    #
    # Cual de los dos campos va depende de la condicion de venta (convenio
    # AFIP-BCRA, informacion complementaria a nivel caratula):
    #
    #   - Condicion EXW  -> `GTOS-ANT-FOB`: los gastos hasta el FOB.
    #   - Grupos C y D   -> `GTOS-POS-FOB`: la diferencia entre la condicion de
    #     venta pactada y el FOB declarado.
    #
    # El importe NO es flete + seguro por definicion: es la diferencia entre el
    # valor en la condicion pactada y el FOB. Para CIF coinciden, para EXW no.
    # Por eso se acepta `gastos_fob` explicito y solo se cae al calculo viejo
    # en los grupos C/D, donde la equivalencia se sostiene.
    #
    # Antes se emitia siempre `GTOS-POS-FOB` con flete + seguro: en una
    # operacion EXW eso era el campo equivocado con el numero equivocado.
    incoterm_norm = str(incoterm or "").strip().upper()
    grupo_cd = incoterm_norm in _INCOTERMS_GRUPO_C_D
    campo_gastos = "GTOS-POS-FOB    " if grupo_cd else "GTOS-ANT-FOB    "

    if gastos_fob is not None:
        importe_gastos = f"{centavos(_importe_de_gastos(gastos_fob, 'gastos_fob')):.2f}"
    elif grupo_cd:
        # Formato 2 decimales para evitar artefactos float
        # (str(3221.66+50) podia dar "3271.6600000000003").
        importe_gastos = f"{flete + seguro:.2f}"
    else:
        # Fuera de los grupos C/D no se puede deducir de flete + seguro y no se
        # inventa un numero: se omite el bloque. El dato es complementario e
        # informativo; el despachante lo carga si corresponde.
        importe_gastos = None

    if importe_gastos is not None:
        lines.append("[CPL]")
        lines.append("NART=0000")
        lines.append("ICPLDIF=D")
        lines.append(f"CCPL={campo_gastos}")
        lines.append(f"MCPL={importe_gastos:<40}")
        lines.append("")
    
    # 4. Banco (por operación). Sin banco no se emite: así viene el archivo
    # real de 2025; el de 2026 lo trae acá, antes de ARDIG-SETI-OPC.
    if banco_bcra:
        lines.append("[CPL]")
        lines.append("NART=0000")
        lines.append("ICPLDIF=S")
        lines.append("CCPL=BANCOSARGENTINA ")
        lines.append(f"MCPL={banco_bcra:<40}")
        lines.append("")

    # Digitalización
    lines.append("[CPL]")
    lines.append("NART=0000")
    lines.append("ICPLDIF=S")
    lines.append("CCPL=ARDIG-SETI-OPC  ")
    lines.append(f"MCPL={'PSAD':<40}")
    lines.append("")
    
    lines.append("[CPL]")
    lines.append("NART=0000")
    lines.append("ICPLDIF=S")
    lines.append("CCPL=ARDIG-CUIT-PSAD ")
    lines.append(f"MCPL={empresa_digitalizacion:<40}")
    lines.append("")
    
    # 5. Proveedor
    if vendedor_id:
        lines.append("[CPL]")
        lines.append("NART=0000")
        lines.append("ICPLDIF=D")
        lines.append("CCPL=IDTRIB-PROVEEDOR")
        lines.append(f"MCPL={vendedor_id:<40}")
        lines.append("")
    
    # 6. Fecha Inicio Actividad (del cliente). Si no viene, NO se emite el bloque.
    # Antes caia el default "13/07/2016" (dato de OTRO cliente del sample) en
    # CUALQUIER declaracion. Mejor omitir y que el despachante lo complete a mano
    # que meter datos falsos de otra empresa en la declaracion aduanera.
    fecha_ini_act = str(comprador_fecha_inic_activ or "").strip()
    if fecha_ini_act:
        lines.append("[CPL]")
        lines.append("NART=0000")
        lines.append("ICPLDIF=D")
        lines.append("CCPL=FECHA INIC.ACTIV")
        lines.append(f"MCPL={fecha_ini_act:<40}")
        lines.append("")

    # 7. Domicilio Establecimiento (del cliente). Mismo criterio: si no viene se
    # omite. Antes caia "DR. SALVADOR MAZZA 1996" (domicilio de otro cliente).
    # MARIA tiene ancho 40 chars maximo para MCPL; recortamos preservando inicio.
    domicilio_est = str(comprador_domicilio or "").strip()[:40]
    if domicilio_est:
        lines.append("[CPL]")
        lines.append("NART=0000")
        lines.append("ICPLDIF=D")
        lines.append("CCPL=DOMICIL.ESTABLEC")
        lines.append(f"MCPL={domicilio_est:<40}")
        lines.append("")
    
    # === [DVD] Documento Vinculado (Factura) ===
    lines.append("[DVD]")
    lines.append("NART=0000")
    lines.append("CDVDDOC=FACTURACOMERCIAL")
    lines.append("CDVDPRSDOC=S")
    # Referencia factura
    ref_factura = f"E{operation_id[-3:]}-1" if len(operation_id) > 3 else "E001-1"
    lines.append(f"LDVDREFDOC={ref_factura:<28}")
    lines.append("")
    
    # === [ART] Por cada item (con agrupación por grupo_id) ===
    # Si varios items tienen el mismo grupo_id, se exportan como un solo [ART]:
    # NCM del primero, descripción concatenada, cantidad/valor/peso sumados.

    # Indexar grupos y conservar la posición de su primera fila. Antes los
    # grupos se agregaban al final del TXT, distinto de lo aprobado en pantalla.
    grupos_dict = {}
    for it in items:
        if it.get('grupo_id') is None:
            continue
        gid = it['grupo_id']
        grupos_dict.setdefault(gid, []).append(it)

    # El número de un producto en la pantalla (su lugar en el pedido); con
    # grupos antes, no es el de su línea del TXT. Los errores de los
    # sub-ítems lo usan para caer bajo el sub-ítem que falla (SUBITEMS-1).
    lugar_en_el_pedido = {id(it): k for k, it in enumerate(items, 1)}
    items_export = []
    grupos_emitidos = set()
    for item in items:
        gid = item.get('grupo_id')
        if gid is None:
            items_export.append(item)
            continue
        if gid in grupos_emitidos:
            continue
        grupos_emitidos.add(gid)
        grupo_items = grupos_dict[gid]

        # Defensa en profundidad: el frontend lo valida, pero el endpoint de
        # generación también puede llamarse directamente.
        ncms = {str(it.get('ncm') or it.get('pieza') or '').replace('.', '').replace(' ', '').upper() for it in grupo_items}
        origenes = {str(it.get('pais_origen') or it.get('origen') or '').strip().upper() for it in grupo_items}
        unidades = {str(it.get('unidad') or it.get('unidad_medida') or it.get('um') or '').strip().upper() for it in grupo_items}
        if any(it.get('subitems') for it in grupo_items):
            raise ValueError(f"Grupo {gid}: un producto agrupado no lleva sub-ítems; "
                             f"desagrupalo para cargarlos.")
        if len(ncms) != 1:
            raise ValueError(f"Grupo {gid}: todos los ítems deben tener la misma NCM")
        if len(origenes) != 1:
            raise ValueError(f"Grupo {gid}: todos los ítems deben tener el mismo origen")
        if len(unidades) != 1:
            raise ValueError(f"Grupo {gid}: todos los ítems deben tener la misma unidad de medida")
        # Se comparan los valores que salen en el TXT, no cómo se escribieron.
        pais_grupo = get_pais_codigo(next(iter(origenes)))
        estados = {_estado_item(it, f"del grupo {gid}", pais_grupo) for it in grupo_items}
        ivas = {
            _iva_adicional(it.get('iva_adicional'), f"Grupo {gid}") if it.get('iva_adicional') else iva_adicional
            for it in grupo_items
        }
        if len(estados) != 1:
            raise ValueError(f"Grupo {gid}: todos los ítems deben tener el mismo estado de la mercadería")
        if len(ivas) != 1:
            raise ValueError(f"Grupo {gid}: todos los ítems deben tener el mismo IVA adicional")

        # Combinar los items del grupo en uno solo
        primero = grupo_items[0]
        combined = dict(primero)
        combined['descripcion'] = ' + '.join(
            str(it.get('descripcion', '')).strip() for it in grupo_items
        )
        combined['cantidad'] = sum(float(it.get('cantidad', 1)) for it in grupo_items)
        combined['valor_total'] = sum((valor_de_la_linea(it) for it in grupo_items), Decimal(0))
        combined['peso_kg'] = sum(peso_de_la_linea(it) for it in grupo_items)
        # valor_unitario promedio del grupo
        total_cant = combined['cantidad']
        combined['valor_unitario'] = float(combined['valor_total']) / total_cant if total_cant > 0 else 0
        items_export.append(combined)

    # Las cuentas al centavo (MARIA-5): la suma de los ítems da exactamente
    # el FOB, el flete y el seguro de la carátula.
    fobs = [_fob_de(it) for it in items_export]
    fletes = repartir(flete, fobs)
    seguros = repartir(seguro, fobs)
    lines[linea_fob_total] = f"MDDTFOB={sum(fobs, Decimal('0.00')):.2f}"

    for idx, item in enumerate(items_export, 1):
        # Obtener valores
        ncm_raw = str(item.get('ncm') or item.get('pieza', '')).strip()
        # Formatear NCM con puntos: 84798999900H -> 8479.89.99.900H
        # Preservar letra de control si existe
        ncm = ncm_raw
        if len(ncm_raw) >= 8 and '.' not in ncm_raw:
             # Basic formatting logic
             base = ncm_raw[:8]
             suffix = ncm_raw[8:]
             formatted_base = f"{base[:4]}.{base[4:6]}.{base[6:8]}"
             if suffix:
                 ncm = f"{formatted_base}.{suffix}"
             else:
                 ncm = formatted_base
        elif '.' in ncm_raw:
             # Ya viene con puntos (ej: "8471.30.00.900 R") — normalizar espacios
             ncm = ncm_raw.replace(' ', '')
        
        descripcion = str(item.get('descripcion', '')).strip()
        cantidad = float(item.get('cantidad', 1))
        valor_unit = float(item.get('valor_unitario', 0))
        valor_total = fobs[idx - 1]
        peso_kg = peso_de_la_linea(item)
        pais = item.get('pais_origen') or item.get('origen', 'CN')
        pais_codigo = get_pais_codigo(pais)
        # Procedencia: pais desde donde se despacha. Si no viene, se asume el
        # mismo que el origen (caso mas comun) en vez de un hardcode (antes 222,
        # que ademas con la tabla oficial es PERU, no EEUU como decia el sample).
        # El fallback se avisa en `supuestos_declarados()`: en el archivo real
        # de referencia origen y procedencia difieren (200 vs 222), asi que
        # asumirlos iguales en silencio no es gratis.
        pais_proc = procedencia_de(item) or pais
        pais_proc_codigo = get_pais_codigo(pais_proc)
        # Unidad de medida del item (con fallback a 07=UNIDAD si no viene).
        unidad_codigo = get_unidad_codigo(
            item.get('unidad') or item.get('unidad_medida') or item.get('um'))
        
        flete_item = fletes[idx - 1]
        seguro_item = seguros[idx - 1]
        base_imponible = valor_total + flete_item + seguro_item
        
        lines.append("[ART]")
        lines.append(f"NART={idx:04d}")
        lines.append(f"NARTEXT={idx:04d}")
        lines.append("CARTTYP=N")
        lines.append(f"IESPNCE={ncm}")
        lines.append(f"IDDT={operation_id}")
        lines.append(f"IARTESPAPU={operation_id}{idx:04d}")
        # S cuando el ítem se declara partido en sub-ítems, N cuando va entero.
        # Los dos archivos de referencia lo confirman: el que tiene un solo
        # [SBT] dice N, el que tiene dos dice S.
        lines.append("CARTSBITEM=S" if item.get("subitems") else "CARTSBITEM=N")
        lines.append(f"CARTUSO={_estado_item(item, idx, pais_codigo)}")
        lines.append(f"QARTKGRNET={peso_valido(peso_kg, idx):.3f}")
        lines.append(f"CARTPAYORI={pais_codigo}")
        lines.append(f"CARTPAYPRC={pais_proc_codigo}") # Procedencia (default = origen)
        lines.append(f"CARTUNTDCL={unidad_codigo}") # Unidad declarada (oficial MARIA)
        lines.append(f"QARTUNTDCL={cantidad:.2f}")
        lines.append(f"CARTUNTEST={unidad_codigo}")
        lines.append(f"QARTUNTEST={cantidad:.2f}")
        lines.append(f"MARTFOB={valor_total:.2f}")
        lines.append(f"MARTASS={seguro_item:.2f}")
        lines.append(f"MARTFLE={flete_item:.2f}")
        lines.append(f"MARTBASIMP={base_imponible:.2f}")
        lines.append(f"MARTUNITAR={valor_unit:.4f}")
        lines.append("CARTPAGREG=N")
        lines.append("CARTCALDST=N")
        # IEXT es vital para relacionar con SBT
        # Formato: primeros 5 chars del operation_id + guion + numero item/año
        iext_prefix = operation_id[:5] if len(operation_id) >= 5 else operation_id.zfill(5)
        lines.append(f"IEXT={iext_prefix}-{idx:02d}/{anio_iext}")
        lines.append("")
        
        # [CPL] Items
        lines.append("[CPL]")
        lines.append(f"NART={idx:04d}")
        lines.append("ICPLDIF=S")
        lines.append("CCPL=GANANCIASOP3    ")
        lines.append(f"MCPL={'COMERC':<40}")
        lines.append("")
        
        lines.append("[CPL]")
        lines.append(f"NART={idx:04d}")
        lines.append("ICPLDIF=S")
        lines.append("CCPL=IVAADICIONAL1   ")
        iva_item = (
            _iva_adicional(item.get("iva_adicional"), f"Ítem {idx}")
            if item.get("iva_adicional") else iva_adicional
        )
        lines.append(f"MCPL={iva_item:<40}")
        lines.append("")
        
        # [SBT] Sufijos de valor.
        #
        # Un ítem puede declararse entero (un solo [SBT]) o partido en varios
        # sub-ítems, uno por modelo/marca, cada uno con su cantidad y su FOB.
        # El manual de PreDespacho lo llama "separar en Ítem o no": es una
        # decisión del despachante, no algo que se deduzca solo.
        #
        # Referencia real con dos sub-ítems:
        # `tests/fixtures/maria_golden_subitems_anon.TXT`.
        sufijo_sbt = (sbt_sufijo_valor or "").strip()
        subitems = item.get("subitems") or []

        if not subitems and not sufijo_sbt:
            raise ValueError(
                "Falta el sufijo de valor SBT (CSBTSVL). "
                "Este dato es obligatorio y depende del importador. "
                "Contactá al despachante para obtenerlo."
            )

        if not subitems:
            # Ítem entero: un solo bloque, sin montos (numeración desde 0000).
            lines.append("[SBT]")
            lines.append(f"IDDT={operation_id}")
            lines.append(f"NART={idx:04d}")
            lines.append("ISBT=0000")
            lines.append(f"IEXT={idx}-1")
            lines.append(f"CSBTSVL={sufijo_sbt}")
            lines.append("")
        else:
            n_item = lugar_en_el_pedido.get(id(item), idx)
            # Partido en sub-ítems: numeración desde 0001, cada uno con su
            # cantidad, unitario y FOB.
            #
            # Las cuentas tienen que cerrar contra el ítem, si no la aduana
            # rechaza la declaración. Se valida acá y se corta: mejor un error
            # en pantalla que un TXT que no cuadra.
            # Cada sub-ítem con su cantidad y su valor: el error dice cuál
            # falla (SUBITEMS-1). Una cantidad negativa compensada por otra
            # haría cerrar la suma.
            for n, sub in enumerate(subitems, start=1):
                for campo, nombre, defecto in (("cantidad", "la cantidad", 0),
                                               ("valor_unitario", "el valor unitario", valor_unit)):
                    crudo = sub.get(campo, defecto)
                    try:
                        numero = float(crudo or 0)
                    except (TypeError, ValueError):
                        numero = float("nan")
                    if not math.isfinite(numero) or numero <= 0:
                        raise ValueError(
                            f"Item {n_item}, sub-ítem {n}: {nombre} «{str(crudo)[:20]}» tiene que ser "
                            f"un número mayor que 0."
                        )
                # QSBTUNTDCL va con dos decimales: 0,004 saldría 0,00 y tres
                # de 0,3333 sumarían 0,99 contra el 1,00 del ítem.
                cant_sub = float(sub.get("cantidad") or 0)
                if abs(cant_sub - round(cant_sub, 2)) > 1e-9:
                    raise ValueError(
                        f"Item {n_item}, sub-ítem {n}: la cantidad «{str(sub.get('cantidad'))[:20]}» tiene más "
                        f"de dos decimales; el TXT la declara con dos."
                    )
            suma_cant = sum(float(s.get("cantidad", 0) or 0) for s in subitems)
            # El valor de cada sub-ítem sin redondear; el MARTFOB se reparte
            # entre ellos al centavo, así los MSBTFOB suman exactamente el
            # MARTFOB (MARIA-5).
            crudos_sub = [
                valor_de_la_linea({"cantidad": s.get("cantidad", 0) or 0,
                                   "valor_unitario": s.get("valor_unitario", valor_unit) or 0})
                for s in subitems
            ]
            suma_fob = sum(crudos_sub, Decimal(0))
            fobs_sub = repartir(valor_total, crudos_sub)
            # La tolerancia compara exacto con exacto (devolución de MARIA-5):
            # la suma sin redondear contra el valor del ítem sin redondear.
            valor_exacto = valor_de_la_linea(item)
            if abs(suma_cant - cantidad) > 0.001:
                raise ValueError(
                    f"Item {n_item}: las cantidades de los sub-ítems suman {suma_cant:g} "
                    f"pero el ítem declara {cantidad:g}. Tienen que coincidir."
                )
            if abs(suma_fob - valor_exacto) > Decimal("0.01"):
                raise ValueError(
                    f"Item {n_item}: los valores de los sub-ítems suman {suma_fob:.2f} "
                    f"pero el ítem declara {valor_total:.2f}. Tienen que coincidir."
                )

            for n, sub in enumerate(subitems, start=1):
                sufijo = (sub.get("sufijo") or sufijo_sbt or "").strip()
                if not sufijo:
                    raise ValueError(
                        f"Item {n_item}, sub-ítem {n}: falta el sufijo de valor (CSBTSVL)."
                    )
                sub_cant = float(sub.get("cantidad", 0) or 0)
                sub_unit = float(sub.get("valor_unitario", valor_unit) or 0)
                lines.append("[SBT]")
                lines.append(f"IDDT={operation_id}")
                lines.append(f"NART={idx:04d}")
                lines.append(f"ISBT={n:04d}")
                lines.append(f"MSBTFOB={fobs_sub[n - 1]:.2f}")
                lines.append(f"QSBTUNTDCL={sub_cant:.2f}")
                lines.append(f"MSBTUNITAR={sub_unit:.4f}")
                lines.append(f"IEXT={idx}-{n}")
                lines.append(f"CSBTSVL={sufijo}")
                lines.append(f"QSBTUNTEST={sub_cant:.2f}")
                lines.append("")

    return "\r\n".join(lines)


def _sim_position_error(ncm_raw: str) -> str | None:
    """Devuelve el motivo si no es una posición SIM de 11 dígitos + DC."""
    raw = str(ncm_raw or "").strip()
    compact = re.sub(r"[.\s]", "", raw).upper()
    if re.fullmatch(r"\d{11}[A-Z]", compact):
        return None
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 8:
        return "la NCM tiene 8 dígitos, pero faltan los 3 dígitos SIM y la letra de control (DC)"
    if len(digits) == 11 and not re.search(r"[A-Za-z]", raw):
        return "falta la letra de control (DC)"
    return "debe tener 11 dígitos (NCM 8 + SIM 3) y una letra de control (DC)"


def errores_de_procedencia(items: list, desde: int = 1) -> list:
    """La procedencia propia de cada producto que no se reconoce. El mismo
    texto sale como error al generar y como aviso antes (veredicto de MARIA-3)."""
    errores = []
    for idx, item in enumerate(items or [], start=desde):
        if not isinstance(item, dict):
            continue
        procedencia = procedencia_de(item)
        if procedencia and not pais_reconocido(procedencia):
            errores.append(f"Item {idx}: Procedencia no reconocida '{procedencia}'. Debe indicar un país válido.")
    return errores


def validate_items_for_maria(items: list) -> tuple[bool, list]:
    """
    Valida que los items tengan los campos necesarios para generar MARIA.
    
    Returns:
        (válido, lista_de_errores)
    """
    errors = []
    
    for idx, item in enumerate(items, 1):
        ncm = item.get('ncm') or item.get('pieza', '')
        if not ncm:
            errors.append(f"Item {idx}: Falta NCM/Pieza")
        else:
            sim_error = _sim_position_error(ncm)
            if sim_error:
                errors.append(f"Item {idx}: Posición SIM incompleta: {sim_error}.")
        
        cantidad = item.get('cantidad')
        if not cantidad or float(cantidad) <= 0:
            errors.append(f"Item {idx}: Cantidad inválida")
        
        valor = item.get('valor_unitario') or item.get('valor_total')
        if not valor or float(valor) <= 0:
            errors.append(f"Item {idx}: Valor inválido")
            
        origen = item.get('origen')
        if not origen:
            errors.append(f"Item {idx}: Falta origen/país de origen")
        elif not pais_reconocido(origen):
            errors.append(f"Item {idx}: Origen no reconocido '{origen}'. Debe indicar un país válido.")
        errors.extend(errores_de_procedencia([item], desde=idx))
    
    return len(errors) == 0, errors


INCOTERMS_VALIDOS = {"FOB", "CIF", "DDP", "EXW", "FCA", "FAS", "CFR", "CPT", "CIP", "DAP", "DPU"}


def _dos_decimales(valor):
    """Un importe como sale en el TXT (al centavo), para que el aviso diga el
    mismo número; si no es un importe, como venga (el TXT dará el error)."""
    try:
        return centavos(valor or 0)
    except (TypeError, ValueError, ArithmeticError):
        try:
            return float(valor or 0)
        except (TypeError, ValueError):
            return 0.0


def supuestos_declarados(
    items: list,
    incoterm: str = "FOB",
    gastos_fob: float | None = None,
    flete: float = 0,
    seguro: float = 0,
    iva_adicional: str | None = None,
    banco_bcra: str = "",
    empresa_digitalizacion: str | None = None,
    gastos_anteriores_fob: float | None = None,
    fecha_emision: str = "",
    vendedor_nombre: str | None = None,
    comprador_nombre: str | None = None,
    comprador_cuit: str | None = None,
    moneda: str | None = None,
) -> list:
    """Lista los campos que el sistema declaró SIN preguntarle al despachante.

    Por qué existe: el generador tiene valores que elige solo (por defecto,
    heredados o calculados). Cuando alguno no corresponde, el TXT sale igual
    de válido a la vista, ninguna validación se queja, y el error aparece
    recién en la aduana. Ya pasó con el año del `IEXT`, que estuvo escrito a
    mano como "25".

    La premisa del producto es "la IA recomienda, el humano confirma". Un
    valor asumido en silencio la rompe igual que uno inventado. Esto los
    pone a la vista antes de generar, sin bloquear.

    Devuelve mensajes en castellano llano, listos para mostrar.
    """
    avisos = []

    # --- Gastos respecto del FOB -----------------------------------------
    incoterm_norm = str(incoterm or "").strip().upper()
    grupo_cd = incoterm_norm in _INCOTERMS_GRUPO_C_D
    if gastos_fob is None:
        if grupo_cd:
            avisos.append(
                f"Gastos a FOB: se declaró {_dos_decimales(flete) + _dos_decimales(seguro):.2f} (flete + seguro) en "
                f"GTOS-POS-FOB. Si la diferencia contra la condición {incoterm_norm} "
                f"pactada es otra, cargala a mano."
            )
        elif incoterm_norm in INCOTERMS_GASTOS_ANTERIORES:
            avisos.append(
                f"Gastos a FOB: no se declararon. Con condición {incoterm_norm} van los "
                f"gastos anteriores a FOB (GTOS-ANT-FOB): cargalos en «Gastos anteriores "
                f"a FOB» si los hubo."
            )
        elif incoterm_norm and incoterm_norm != "FOB":
            avisos.append(
                f"Gastos a FOB: no se declararon. Con condición {incoterm_norm} el "
                f"importe no se puede calcular del flete y el seguro; si "
                f"corresponde declararlo, cargalo a mano."
            )
    try:
        anteriores = float(gastos_anteriores_fob or 0)
    except (TypeError, ValueError):
        anteriores = 0
    if anteriores > 0 and incoterm_norm not in INCOTERMS_GASTOS_ANTERIORES:
        avisos.append(
            f"Gastos anteriores a FOB: cargaste {anteriores:.2f}, pero con condición "
            f"{incoterm_norm or 'sin elegir'} no van al TXT (sólo con EXW, FCA o FAS)."
        )

    # --- Carátula vacía (MARIA-1d) ----------------------------------------
    # Sólo si quien llama pasa estos datos (el endpoint): None = no evaluar.
    caratula = (vendedor_nombre, comprador_nombre, comprador_cuit, moneda)
    if items and any(v is not None for v in caratula):
        faltan = [nombre for nombre, valor in (
            ("vendedor (LDDTNOMFOD)", vendedor_nombre),
            ("nombre del importador (LDDTNOMIOE)", comprador_nombre),
            ("CUIT del importador (NDDTIMMIOE)", comprador_cuit),
            ("moneda (CDDTDEVFOB)", moneda),
            ("incoterm (CDDTINCOTE)", incoterm),
        ) if not str(valor or "").strip()]
        if faltan:
            avisos.append(
                "Datos de la carátula vacíos: " + ", ".join(faltan) + ". Esas líneas salen "
                "vacías o no salen; cargalos en la revisión antes de pegar el archivo en el Kit."
            )

    # --- Fecha de emisión (MARIA-3) ----------------------------------------
    fecha_ok = fecha_de_la_factura(fecha_emision)
    if not fecha_ok:
        leida = str(fecha_emision or "").strip()
        avisos.append(
            "Fecha de emisión: " + (f"«{leida[:20]}» no es una fecha (DD/MM/AAAA); "
                                    if leida else "no se leyó de la factura; ")
            + "sin una fecha válida no se genera el TXT. Cargala en la revisión."
        )
    else:
        fecha = datetime.strptime(fecha_ok, "%d/%m/%Y")
        hoy = datetime.now()
        if fecha > hoy + timedelta(days=1):
            avisos.append(f"Fecha de emisión: {fecha_ok} es futura; revisá que sea la de la factura.")
        elif fecha < hoy - timedelta(days=730):
            avisos.append(
                f"Fecha de emisión: {fecha_ok} es de hace más de dos años; revisá que sea la de la factura."
            )

    # --- Defaults a nivel ítem -------------------------------------------
    sin_procedencia = []
    sin_unidad = []
    for idx, item in enumerate(items or [], start=1):
        if not isinstance(item, dict):
            continue
        # Mismo orden que el generador: pais_origen primero.
        origen = item.get("pais_origen") or item.get("origen")
        proc = procedencia_de(item)
        if origen and not proc:
            sin_procedencia.append(str(idx))
        if not (item.get("unidad") or item.get("unidad_medida") or item.get("um")):
            sin_unidad.append(str(idx))

    if sin_procedencia:
        avisos.append(
            f"Procedencia: en el/los ítem(s) {', '.join(sin_procedencia)} se declaró "
            f"la misma que el origen. Si la mercadería se embarcó desde otro país, "
            f"cargala en «Procedencia» (sale del documento de transporte): son campos distintos."
        )
    if sin_unidad:
        avisos.append(
            f"Unidad de medida: en el/los ítem(s) {', '.join(sin_unidad)} se declaró "
            f"07 (unidad) por defecto."
        )

    # --- Lo que decide el despachante (MARIA-4) ---------------------------
    sin_estado = [
        str(idx) for idx, item in enumerate(items or [], start=1)
        if isinstance(item, dict) and item.get("estado") in (None, "")
        and get_pais_codigo(item.get("pais_origen") or item.get("origen")) != PAIS_ARGENTINA
    ]
    if sin_estado:
        avisos.append(
            f"Estado de la mercadería: en el/los ítem(s) {', '.join(sin_estado)} se declaró "
            f"{ESTADO_POR_DEFECTO_IMPORTADO} ({ESTADOS_MERCADERIA[ESTADO_POR_DEFECTO_IMPORTADO].lower()}) "
            f"por defecto."
        )
    if items and not iva_adicional:
        avisos.append(
            "IVA adicional: se declaró reventa (NO_VALIDA) por defecto. Si la mercadería "
            "es para uso particular, cambialo."
        )
    if items:
        avisos.append(
            "IVA adicional: si corresponde reducción o exclusión, se elige en «Ventajas» "
            "del Kit; no va en el TXT."
        )
    if items and not str(banco_bcra or "").strip():
        avisos.append(
            "Banco: no se declaró (la línea BANCOSARGENTINA no sale). Cargá el banco del "
            "cliente si corresponde."
        )
    if items and not empresa_digitalizacion:
        avisos.append(
            "Empresa de digitalización: se declaró Modoc (PSAD06) por defecto."
        )

    return avisos


def validate_for_kit_maria(items: list) -> tuple[list, list]:
    """Valida reglas específicas de KIT Maria que validate_items_for_maria no cubre.

    Returns:
        (errores, advertencias) — los errores bloquean la generación,
        las advertencias se incluyen en la respuesta pero no bloquean.
    """
    errores = []
    _warn_groups: dict[str, list[int]] = {}

    def _track_warn(msg: str, idx: int):
        _warn_groups.setdefault(msg, []).append(idx)

    for idx, item in enumerate(items, 1):
        ncm_raw = str(item.get("ncm") or item.get("pieza", "") or "").strip()
        sim_error = _sim_position_error(ncm_raw) if ncm_raw else None
        if sim_error:
            errores.append(f"Item {idx}: Posición SIM incompleta: {sim_error}.")

        # Descripción: mínimo 10 caracteres
        desc = str(item.get("descripcion", "") or "").strip()
        if len(desc) < 10:
            errores.append(f"Item {idx}: Descripción muy corta ({len(desc)} chars). KIT Maria requiere mínimo 10.")

        # Peso > 0
        peso = peso_de_la_linea(item)
        if peso <= 0:
            errores.append(f"Item {idx}: Peso inválido (≤0). KIT Maria lo rechaza.")

        # Incoterm válido
        incoterm = str(item.get("incoterm", "") or "").strip().upper()
        if incoterm and incoterm not in INCOTERMS_VALIDOS:
            errores.append(f"Item {idx}: Incoterm '{incoterm}' no válido. Debe ser uno de: {', '.join(sorted(INCOTERMS_VALIDOS))}.")

        # Moneda: código de 3 letras
        moneda = str(item.get("moneda", "") or "").strip().upper()
        if moneda and (len(moneda) != 3 or not moneda.isalpha()):
            errores.append(f"Item {idx}: Moneda '{moneda}' no válida. Debe ser código de 3 letras (DOL, EUR, etc.).")

    # Agrupar advertencias: 1 item → "Item #5: ...", 2-3 → "Items #2, #7: ...", 4+ → conteo
    advertencias = []
    for msg, idxs in _warn_groups.items():
        refs = [f"#{i}" for i in idxs]
        if len(idxs) == 1:
            advertencias.append(f"Item {refs[0]}: {msg}")
        elif len(idxs) <= 3:
            advertencias.append(f"Items {', '.join(refs)}: {msg}")
        else:
            advertencias.append(f"{msg} en {len(idxs)} ítems.")

    return errores, advertencias
