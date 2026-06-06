"""
Generador de archivos TXT en formato MARIA para EXPORTACIÓN.
Sistema SIM de AFIP - Destinaciones de Exportación.
"""

from datetime import datetime

# Códigos de país oficiales del Sistema MARIA: una sola tabla (la de importación)
# para que import y export no diverjan. La tabla anterior tenia codigos MAL.
from proyecto_maria.core.maria_generator import PAISES_INDEC, get_unidad_codigo

# Tipos de destinación de exportación
TIPOS_DESTINACION_EXPORT = {
    "EC01": "Exportación a consumo definitiva",
    "EC02": "Exportación suspensiva temporal",
    "EC03": "Exportación por rancho",
    "EC04": "Exportación por mensajería/courier",
    "EC05": "Reexportación",
}


def get_pais_codigo(pais: str) -> int:
    """Obtiene el código INDEC para un país."""
    if not pais:
        return 212  # USA por defecto para export
    
    if str(pais).isdigit():
        return int(pais)
    
    # Dos pasadas: primero match EXACTO (case-insensitive) para no colisionar.
    # Antes, el startswith de 2 letras devolvia el pais equivocado: p.ej.
    # "China" matcheaba "Chile" (208) y "Colombia" caia en "Corea" (220).
    pais_upper = pais.strip().upper()
    for key, code in PAISES_INDEC.items():
        if key.upper() == pais_upper:
            return code
    # Segunda pasada: prefijo estricto (>=3 chars) como fallback, solo si no hubo exacto.
    prefijo = pais_upper[:4]
    if len(prefijo) >= 3:
        for key, code in PAISES_INDEC.items():
            if key.upper().startswith(prefijo):
                return code

    return 212  # USA por defecto


def generate_maria_export_txt(
    operation_id: str,
    items: list,
    moneda: str = "DOL",
    incoterm: str = "FOB",
    cuit_exportador: str = "",
    exportador_nombre: str = "",
    comprador_nombre: str = "",
    comprador_pais: str = "US",
    comprador_id: str = "",
    flete: float = 0,
    seguro: float = 0,
    tipo_destinacion: str = "EC01",
    aduana_salida: str = "001",  # Buenos Aires por defecto
    medio_transporte: str = "01",  # Marítimo
) -> str:
    """
    Genera archivo TXT en formato MARIA para EXPORTACIÓN.
    
    Args:
        operation_id: ID de la operación (ej: "EXP001790125")
        items: Lista de items con campos:
            - ncm/pieza: Código NCM
            - cantidad: Cantidad
            - valor_unitario: Precio unitario FOB
            - peso_kg: Peso en kg
            - descripcion: Descripción del producto
        moneda: Código de moneda (DOL, EUR)
        incoterm: Término comercial (FOB, CIF, CFR, EXW)
        cuit_exportador: CUIT del exportador
        exportador_nombre: Nombre/Razón social del exportador
        comprador_nombre: Nombre del comprador extranjero
        comprador_pais: País del comprador
        comprador_id: ID tributario del comprador
        flete: Costo de flete internacional
        seguro: Costo de seguro internacional
        tipo_destinacion: Tipo de destinación (EC01, EC02, etc.)
        aduana_salida: Código de aduana de salida
        medio_transporte: Código de medio de transporte
    
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
    
    peso_total = sum(float(item.get('peso_kg', 0) or 0) for item in items)
    cantidad_total = sum(float(item.get('cantidad', 0) or 0) for item in items)
    
    # === [DDT] Cabecera - EXPORTACIÓN ===
    lines.append("[DDT]")
    lines.append(f"ISTA={tipo_destinacion}")  # Tipo de exportación
    lines.append(f"IDSO={operation_id}")
    lines.append(f"CDDTEXE={aduana_salida}")  # Aduana de salida
    lines.append(f"CDDTBUR={aduana_salida}")
    lines.append(f"CDDTTYPDEC={tipo_destinacion}")
    lines.append("CDDTIMPEXP=E")  # E = Exportación (diferencia clave con import)
    lines.append(f"CDDTDEVFOB={moneda}")
    lines.append(f"MDDTFOB={fob_total:.2f}")
    
    if flete > 0:
        lines.append(f"MDDTFLE={flete:.2f}")
    if seguro > 0:
        lines.append(f"MDDTASS={seguro:.2f}")
    
    lines.append(f"CDDTINCOTE={incoterm}")
    lines.append(f"CDDTMEDTRA={medio_transporte}")  # Medio de transporte
    
    # Datos del exportador (vendedor nacional)
    if exportador_nombre:
        lines.append(f"LDDTNOMIOE={exportador_nombre}")  # IOE = Importador/Exportador
    if cuit_exportador:
        lines.append(f"NDDTIMMIOE={cuit_exportador}")
    
    # Datos del comprador/destinatario (extranjero)
    if comprador_nombre:
        lines.append(f"LDDTNOMFOD={comprador_nombre}")  # FOD = destinatario
    if comprador_id:
        lines.append(f"CDDTIDFOD={comprador_id}")
    
    pais_destino_codigo = get_pais_codigo(comprador_pais)
    lines.append(f"CDDTPAYDST={pais_destino_codigo}")  # País destino
    
    lines.append("CDDTIVA=S")
    lines.append("")
    
    # === [CPL] Campos Complementarios ===
    # Referencia interna
    lines.append("[CPL]")
    lines.append("NART=0000")
    lines.append("ICPLDIF=S")
    lines.append("CCPL=NRO.REF.INTERNA ")
    lines.append(f"MCPL={operation_id:<40}")
    lines.append("")
    
    # Fecha de factura/permiso
    fecha_actual = datetime.now().strftime("%d/%m/%Y")
    lines.append("[CPL]")
    lines.append("NART=0000")
    lines.append("ICPLDIF=D")
    lines.append("CCPL=FECHAEMISIONFACT")
    lines.append(f"MCPL={fecha_actual:<40}")
    lines.append("")
    
    # País destino final
    lines.append("[CPL]")
    lines.append("NART=0000")
    lines.append("ICPLDIF=S")
    lines.append("CCPL=PAIS-DESTINO    ")
    lines.append(f"MCPL={comprador_pais:<40}")
    lines.append("")
    
    # === [DVD] Documento Vinculado (Factura de Exportación) ===
    lines.append("[DVD]")
    lines.append("NART=0000")
    lines.append("CDVDDOC=FACTURAEXPORT  ")  # Factura de exportación
    lines.append("CDVDPRSDOC=S")
    lines.append(f"LDVDREFDOC={operation_id[:28]:<28}")
    lines.append("")
    
    # === [ART] Por cada item de exportación ===
    for idx, item in enumerate(items, 1):
        ncm = str(item.get('ncm') or item.get('pieza', '')).strip()
        codigo_parte = str(item.get('codigo_parte', '')).strip()
        descripcion = str(item.get('descripcion', '')).strip()
        cantidad = float(item.get('cantidad', 1))
        valor_unit = float(item.get('valor_unitario', 0))
        valor_total = float(item.get('valor_total') or cantidad * valor_unit)
        peso_kg = float(item.get('peso_kg', item.get('peso_unitario', 0)) or 0)
        
        # Para exportación, el país origen siempre es Argentina
        pais_origen_codigo = 200  # Argentina
        # Unidad de medida del item (fallback 07=UNIDAD). Antes era 07 fijo con
        # comentario "kilogramos" (el comentario mentia: 07 es UNIDAD, no kg).
        unidad_codigo = get_unidad_codigo(
            item.get('unidad') or item.get('unidad_medida') or item.get('um'))
        
        # Calcular proporcional de flete y seguro
        proporcion = valor_total / fob_total if fob_total > 0 else 0
        flete_item = flete * proporcion
        seguro_item = seguro * proporcion
        
        lines.append("[ART]")
        lines.append(f"NART={idx:04d}")
        lines.append(f"NARTEXT={idx:04d}")
        lines.append("CARTTYP=N")
        lines.append(f"IESPNCE={ncm}")
        lines.append(f"IDDT={operation_id}")
        lines.append(f"IARTESPAPU={operation_id}{idx:04d}")
        lines.append("CARTSBITEM=N")
        lines.append("CARTUSO=3")
        lines.append(f"QARTKGRNET={peso_kg:.3f}")
        lines.append(f"CARTPAYORI={pais_origen_codigo}")  # Argentina
        lines.append(f"CARTPAYDST={pais_destino_codigo}")  # País destino
        lines.append(f"CARTUNTDCL={unidad_codigo}")  # Unidad declarada (oficial MARIA)
        lines.append(f"QARTUNTDCL={cantidad:.2f}")
        lines.append(f"CARTUNTEST={unidad_codigo}")
        lines.append(f"QARTUNTEST={cantidad:.2f}")
        lines.append(f"MARTFOB={valor_total:.2f}")
        
        if flete_item > 0:
            lines.append(f"MARTFLE={flete_item:.2f}")
        if seguro_item > 0:
            lines.append(f"MARTASS={seguro_item:.2f}")
        
        lines.append(f"MARTUNITAR={valor_unit:.4f}")
        lines.append("CARTPAGREG=N")
        lines.append("CARTCALDST=N")
        
        if codigo_parte:
            lines.append(f"IEXT={codigo_parte[:15]}")
        lines.append("")
        
        # CPL para descripción del item
        if descripcion and len(descripcion) > 10:
            lines.append("[CPL]")
            lines.append(f"NART={idx:04d}")
            lines.append("ICPLDIF=S")
            lines.append("CCPL=DESCRIPCION    ")
            lines.append(f"MCPL={descripcion[:40]:<40}")
            lines.append("")
    
    # Unir con CRLF (Windows line endings para MARIA)
    return "\r\n".join(lines)


def validate_items_for_export(items: list) -> tuple[bool, list]:
    """
    Valida que los items tengan los campos necesarios para generar MARIA export.
    
    Returns:
        (válido, lista_de_errores)
    """
    errors = []
    
    if not items:
        errors.append("No hay items para exportar")
        return False, errors
    
    for idx, item in enumerate(items, 1):
        ncm = item.get('ncm') or item.get('pieza', '')
        if not ncm:
            errors.append(f"Item {idx}: Falta NCM/Pieza")
        elif len(str(ncm).replace('.', '').replace(' ', '')) < 8:
            errors.append(f"Item {idx}: NCM debe tener al menos 8 dígitos")
        
        cantidad = item.get('cantidad')
        if not cantidad or float(cantidad) <= 0:
            errors.append(f"Item {idx}: Cantidad inválida o faltante")
        
        valor = item.get('valor_unitario') or item.get('valor_total')
        if not valor or float(valor) <= 0:
            errors.append(f"Item {idx}: Valor FOB inválido o faltante")
        
        descripcion = item.get('descripcion', '')
        if not descripcion or len(descripcion) < 5:
            errors.append(f"Item {idx}: Descripción muy corta o faltante")
    
    return len(errors) == 0, errors


def calculate_export_retenciones(items: list, tipo_producto: str = "general") -> dict:
    """
    Calcula retenciones a la exportación.
    
    Args:
        items: Lista de items
        tipo_producto: Tipo de producto (soja, trigo, maiz, general, industrial)
    
    Returns:
        Dict con derechos de exportación calculados
    """
    # Alícuotas de retenciones (simplificado)
    ALICUOTAS = {
        "soja": 0.33,       # 33% para soja
        "trigo": 0.12,      # 12% para trigo
        "maiz": 0.12,       # 12% para maíz
        "carne": 0.09,      # 9% para carne
        "industrial": 0.05, # 5% para manufacturas
        "general": 0.00,    # 0% para otros
    }
    
    fob_total = sum(
        float(item.get('valor_total') or 
              float(item.get('cantidad', 1)) * float(item.get('valor_unitario', 0)))
        for item in items
    )
    
    alicuota = ALICUOTAS.get(tipo_producto.lower(), 0.00)
    retencion = fob_total * alicuota
    
    return {
        "fob_total": round(fob_total, 2),
        "tipo_producto": tipo_producto,
        "alicuota_percent": alicuota * 100,
        "retencion_usd": round(retencion, 2),
        "fob_neto": round(fob_total - retencion, 2),
    }
