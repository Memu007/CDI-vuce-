"""
Generador de archivos TXT en formato MARIA para Sistema SIM de AFIP.
"""
import re
import unicodedata
from datetime import datetime

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


def pais_reconocido(pais) -> bool:
    """True si el país se reconoce con certeza (código numérico o match exacto
    en la tabla verificada). NO cuenta el fallback por prefijo ni el default,
    que son adivinanzas. Sirve para que el sistema AVISE en vez de meter un
    código de origen errado en el TXT aduanero (ej: 'XX', 'Vietnam').
    """
    if pais is None or str(pais).strip() == "":
        return False
    if str(pais).strip().isdigit():
        return True
    return _normalizar_pais(pais) in _PAISES_NORM


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
    if str(pais).strip().isdigit():
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
                       tipo_destinacion: str = "IC04") -> str:
    """
    Genera archivo TXT en formato MARIA.
    
    Args:
        operation_id: ID de la operación (ej: "001790125")
        items: Lista de items con campos:
            - ncm/pieza: Código NCM
            - cantidad: Cantidad
            - valor_unitario: Precio unitario
            - valor_total: Precio total (opcional, se calcula)
            - peso_kg: Peso en kg
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
    
    # Calcular totales
    fob_total = sum(
        float(item.get('valor_total') or 
              float(item.get('cantidad', 1)) * float(item.get('valor_unitario', 0)))
        for item in items
    )
    
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
    lines.append(f"MDDTFOB={fob_total:.2f}")
    
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
    
    # 2. Fecha Emision Factura (se usa la del PDF si viene; sino hoy como fallback)
    fecha_factura = (str(fecha_emision or "").strip()
                     or datetime.now().strftime("%d/%m/%Y"))
    lines.append("[CPL]")
    lines.append("NART=0000")
    lines.append("ICPLDIF=D")
    lines.append("CCPL=FECHAEMISIONFACT")
    lines.append(f"MCPL={fecha_factura:<40}")
    lines.append("")
    
    # 3. Gastos Post FOB (Total Flete + Seguro). Formato 2 decimales para evitar
    # artefactos float (str(3221.66+50) podia dar "3271.6600000000003").
    gastos_post_fob = f"{flete + seguro:.2f}"
    lines.append("[CPL]")
    lines.append("NART=0000")
    lines.append("ICPLDIF=D")
    lines.append("CCPL=GTOS-POS-FOB    ")
    lines.append(f"MCPL={gastos_post_fob:<40}")
    lines.append("")
    
    # 4. Defaults PSAD (Hardcoded por ahora, configurable a futuro)
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
    lines.append(f"MCPL={'PSAD06':<40}")
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
        if len(ncms) != 1:
            raise ValueError(f"Grupo {gid}: todos los ítems deben tener la misma NCM")
        if len(origenes) != 1:
            raise ValueError(f"Grupo {gid}: todos los ítems deben tener el mismo origen")
        if len(unidades) != 1:
            raise ValueError(f"Grupo {gid}: todos los ítems deben tener la misma unidad de medida")

        # Combinar los items del grupo en uno solo
        primero = grupo_items[0]
        combined = dict(primero)
        combined['descripcion'] = ' + '.join(
            str(it.get('descripcion', '')).strip() for it in grupo_items
        )
        combined['cantidad'] = sum(float(it.get('cantidad', 1)) for it in grupo_items)
        combined['valor_total'] = sum(
            float(it.get('valor_total') or float(it.get('cantidad', 1)) * float(it.get('valor_unitario', 0)))
            for it in grupo_items
        )
        combined['peso_kg'] = sum(
            float(it.get('peso_kg', it.get('peso_unitario', 0)) or 0) for it in grupo_items
        )
        # valor_unitario promedio del grupo
        total_cant = combined['cantidad']
        combined['valor_unitario'] = combined['valor_total'] / total_cant if total_cant > 0 else 0
        items_export.append(combined)

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
        valor_total = float(item.get('valor_total') or cantidad * valor_unit)
        peso_kg = float(item.get('peso_kg', item.get('peso_unitario', 0)) or 0)
        pais = item.get('pais_origen') or item.get('origen', 'CN')
        pais_codigo = get_pais_codigo(pais)
        # Procedencia: pais desde donde se despacha. Si no viene, se asume el
        # mismo que el origen (caso mas comun) en vez de un hardcode (antes 222,
        # que ademas con la tabla oficial es PERU, no EEUU como decia el sample).
        pais_proc = (item.get('pais_procedencia') or item.get('procedencia') or pais)
        pais_proc_codigo = get_pais_codigo(pais_proc)
        # Unidad de medida del item (con fallback a 07=UNIDAD si no viene).
        unidad_codigo = get_unidad_codigo(
            item.get('unidad') or item.get('unidad_medida') or item.get('um'))
        
        # Calcular proporcional de flete y seguro
        proporcion = valor_total / fob_total if fob_total > 0 else 0
        flete_item = flete * proporcion
        seguro_item = seguro * proporcion
        base_imponible = valor_total + flete_item + seguro_item
        
        lines.append("[ART]")
        lines.append(f"NART={idx:04d}")
        lines.append(f"NARTEXT={idx:04d}")
        lines.append("CARTTYP=N")
        lines.append(f"IESPNCE={ncm}")
        lines.append(f"IDDT={operation_id}")
        lines.append(f"IARTESPAPU={operation_id}{idx:04d}")
        lines.append("CARTSBITEM=N") # Ojo: sample dice N pero tiene [SBT]
        lines.append("CARTUSO=3")
        lines.append(f"QARTKGRNET={peso_kg:.3f}")
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
        lines.append(f"IEXT={iext_prefix}-{idx:02d}/25") 
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
        lines.append(f"MCPL={'IVAAD1':<40}")
        lines.append("")
        
        # [SBT] Subitems (Sufijos de valor)
        # Sufijo de valor: OBLIGATORIO. Sin este dato no se puede generar el TXT
        # porque es específico de cada importador (regla del despachante).
        sufijo_sbt = (sbt_sufijo_valor or "").strip()
        if not sufijo_sbt:
            raise ValueError(
                "Falta el sufijo de valor SBT (CSBTSVL). "
                "Este dato es obligatorio y depende del importador. "
                "Contactá al despachante para obtenerlo."
            )
        lines.append("[SBT]")
        lines.append(f"IDDT={operation_id}")
        lines.append(f"NART={idx:04d}")
        lines.append("ISBT=0000")
        lines.append(f"IEXT={idx}-1")
        lines.append(f"CSBTSVL={sufijo_sbt}")
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
    
    return len(errors) == 0, errors


INCOTERMS_VALIDOS = {"FOB", "CIF", "DDP", "EXW", "FCA", "CFR", "CPT", "CIP", "DAP", "DPU"}


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
        peso = float(item.get("peso_kg", item.get("peso_unitario", 0)) or 0)
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
