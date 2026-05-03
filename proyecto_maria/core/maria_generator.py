"""
Generador de archivos TXT en formato MARIA para Sistema SIM de AFIP.
"""
from datetime import datetime, timedelta

# Códigos de país INDEC
PAISES_INDEC = {
    "AR": 200, "Argentina": 200,
    "BR": 203, "Brasil": 203,
    "CL": 208, "Chile": 208,
    "CN": 218, "China": 218,
    "US": 212, "USA": 212, "Estados Unidos": 212,
    "UY": 286, "Uruguay": 286,
    "VE": 226, "Venezuela": 226,
    "MX": 214, "Mexico": 214, "México": 214,
    "DE": 212, "Alemania": 212,
    "IT": 213, "Italia": 213,
    "ES": 210, "España": 210,
    "FR": 211, "Francia": 211,
    "JP": 217, "Japón": 217, "Japon": 217,
    "KR": 220, "Corea": 220, "Corea del Sur": 220,
    "TW": 221, "Taiwan": 221, "Taiwán": 221,
}

def get_pais_codigo(pais: str) -> int:
    """Obtiene el código INDEC para un país."""
    if not pais:
        return 218  # China por defecto
    
    # Si ya es un número, devolverlo
    if str(pais).isdigit():
        return int(pais)
    
    # Buscar en el diccionario
    pais_upper = pais.strip().upper()
    for key, code in PAISES_INDEC.items():
        if key.upper() == pais_upper or key.upper().startswith(pais_upper[:2]):
            return code
    
    return 218  # China por defecto


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
    # Fecha embarque default futura si no hay
    fecha_emb_header = fecha_embarque if fecha_embarque else (datetime.now() + timedelta(days=365)).strftime("%d/%m/%Y")
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
    
    # 3. Gastos Post FOB (Total Flete + Seguro)
    gastos_post_fob = flete + seguro
    lines.append("[CPL]")
    lines.append("NART=0000")
    lines.append("ICPLDIF=D")
    lines.append("CCPL=GTOS-POS-FOB    ")
    lines.append(f"MCPL={str(gastos_post_fob):<40}")
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
    
    # 6. Fecha Inicio Actividad (del cliente, con fallback al default historico)
    fecha_ini_act = (str(comprador_fecha_inic_activ or "").strip()
                     or "13/07/2016")
    lines.append("[CPL]")
    lines.append("NART=0000")
    lines.append("ICPLDIF=D")
    lines.append("CCPL=FECHA INIC.ACTIV")
    lines.append(f"MCPL={fecha_ini_act:<40}")
    lines.append("")

    # 7. Domicilio Establecimiento (del cliente, con fallback al default historico)
    domicilio_est = (str(comprador_domicilio or "").strip()
                     or "DR. SALVADOR MAZZA 1996")
    # MARIA tiene ancho 40 chars maximo para MCPL; recortamos preservando fin
    domicilio_est = domicilio_est[:40]
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
        lines.append(f"CARTPAYPRC={222}") # Procedencia default EEUU (Sample) o parametrizable
        lines.append("CARTUNTDCL=07") # Unidades (07 = Unidades)
        lines.append(f"QARTUNTDCL={cantidad:.2f}")
        lines.append("CARTUNTEST=07")
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
        # Sufijos de valor hardcoded por ahora, podrian venir de UI
        lines.append("CSBTSVL=AA(VOWYNNS)-AB(VITTO)-CA00-")
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
    
    return len(errors) == 0, errors
