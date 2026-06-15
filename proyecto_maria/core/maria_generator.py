"""
Generador de archivos TXT en formato MARIA para Sistema SIM de AFIP.
"""
import unicodedata
from datetime import datetime

# Códigos de país oficiales del Sistema MARIA (AFIP - "Códigos María").
# Fuente: https://www.afip.gob.ar/genericos/documentos/codigos-maria.pdf
# OJO: la tabla anterior tenia casi todos los codigos MAL (China=218 era Mexico,
# Alemania=212 era EEUU, España=210 era Ecuador, etc.), metiendo el pais de
# origen equivocado en CADA declaracion aduanera.
PAISES_INDEC = {
    "AR": 200, "Argentina": 200,
    "BO": 202, "Bolivia": 202,
    "BR": 203, "Brasil": 203,
    "CA": 204, "Canada": 204, "Canadá": 204,
    "CO": 205, "Colombia": 205,
    "CL": 208, "Chile": 208,
    "EC": 210, "Ecuador": 210,
    "US": 212, "USA": 212, "EEUU": 212, "Estados Unidos": 212,
    "MX": 218, "Mexico": 218, "México": 218,
    "PY": 221, "Paraguay": 221,
    "PE": 222, "Peru": 222, "Perú": 222,
    "UY": 225, "Uruguay": 225,
    "VE": 226, "Venezuela": 226,
    "KP": 308, "Corea del Norte": 308,
    "KR": 309, "Corea": 309, "Corea del Sur": 309,
    "CN": 310, "China": 310,
    "TW": 313, "Taiwan": 313, "Taiwán": 313,
    "IN": 315, "India": 315,
    "JP": 320, "Japón": 320, "Japon": 320,
    "ES": 410, "España": 410, "Espana": 410,
    "FR": 412, "Francia": 412,
    "IT": 417, "Italia": 417,
    "GB": 426, "Reino Unido": 426, "UK": 426,
    "DE": 438, "Alemania": 438,
    "VN": 337, "Vietnam": 337,
    "TH": 335, "Tailandia": 335, "Thailand": 335,
    "ID": 316, "Indonesia": 316,
    "MY": 326, "Malasia": 326, "Malaysia": 326,
}

# Alias en ingles / variantes de escritura -> MISMO codigo ya verificado arriba.
# IMPORTANTE: NO agregar paises nuevos aca sin el codigo oficial MARIA verificado.
# Si un pais no esta en la tabla, get_pais_codigo lo marca como NO reconocido
# (pais_reconocido == False) para que el sistema avise en vez de adivinar.
PAISES_ALIAS = {
    "Brazil": 203,
    "Germany": 438,
    "Japan": 320,
    "Spain": 410,
    "France": 412,
    "Italy": 417,
    "England": 426, "Great Britain": 426, "United Kingdom": 426,
    "Korea": 309, "South Korea": 309, "North Korea": 308,
    "China (Mainland)": 310, "Mainland China": 310,
    "P.R. China": 310, "PR China": 310, "RP China": 310,
    "Republica Popular China": 310, "República Popular China": 310,
    "Estados Unidos de America": 212, "United States of America": 212,
    "EE.UU.": 212, "EEUU.": 212,
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
                       # Sufijo de valor [SBT]. Default = valor legacy del sample
                       # (VOWYNNS). OJO: es especifico de ese cliente; la regla real
                       # por importador esta pendiente de confirmar con el despachante.
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
    
    # === [ART] Por cada item ===
    for idx, item in enumerate(items, 1):
        # Obtener valores
        ncm_raw = str(item.get('ncm') or item.get('pieza', '')).strip()
        # Formatear NCM con puntos: 84798999900H -> 8479.89.99.900H
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
        lines.append("[SBT]")
        lines.append(f"IDDT={operation_id}")
        lines.append(f"NART={idx:04d}")
        lines.append("ISBT=0000")
        lines.append(f"IEXT={idx}-1") # Referencia dummy
        # Sufijo de valor: usa el parametro si viene; sino el legacy del sample.
        # El default contiene "VOWYNNS" (cliente del sample) -> es un leak para
        # otros clientes; la regla real por importador esta pendiente de despachante.
        sufijo_sbt = sbt_sufijo_valor.strip() or "AA(VOWYNNS)-AB(VITTO)-CA00-"
        lines.append(f"CSBTSVL={sufijo_sbt}")
        lines.append("")

    return "\r\n".join(lines)


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
