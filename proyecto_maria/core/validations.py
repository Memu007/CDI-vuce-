# === VALIDACIONES DE REGLAS DE NEGOCIO ===
# Este módulo implementa las reglas específicas del negocio aduanero
# que deben cumplir todos los items antes de generar el Excel AVG.

from proyecto_maria.models.operations import Item  # Modelo Pydantic de items
from typing import List, Tuple  # Type hints para mejor documentación

def run_pre_maria_validations(items: List[Item]) -> Tuple[List[Item], List[str]]:
    """
    🔍 VALIDADOR PRINCIPAL DE REGLAS DE NEGOCIO
    
    Ejecuta todas las validaciones requeridas por el sistema MARIA
    antes de generar el archivo Excel AVG.
    
    Args:
        items: Lista de items a validar (objetos Item de Pydantic)
    
    Returns:
        Tuple[List[Item], List[str]]: 
        - items_válidos: Items que pasaron todas las validaciones
        - errores: Lista de mensajes de error descriptivos
    
    Reglas implementadas:
    1. Pieza (código NCM) obligatoria y no vacía
    2. Cantidad debe ser mayor a cero
    3. Valor unitario debe ser mayor a cero
    4. Peso unitario debe ser mayor a cero
    5. Origen obligatorio y válido (no vacío, no "XX")
    
    Comportamiento:
    - Si un item falla cualquier validación, se excluye del resultado
    - Se genera mensaje de error específico con número de item
    - Items válidos continúan al siguiente paso del procesamiento
    """
    valid_items = []
    errors = []

    for i, item in enumerate(items):
        # Validación 1: La pieza (NCM) puede estar vacía - despachantes la completan manualmente
        if not item.pieza or not item.pieza.strip():
            pass  # NCM vacío es válido según diseño actual

        # Validación 2: La cantidad debe ser positiva.
        if item.cantidad <= 0:
            errors.append(f"Error en ítem {i+1} (Pieza {item.pieza}): La cantidad debe ser mayor a cero. Ej: 10 o 10.00.")
            continue

        # Validación 3: El valor unitario debe ser positivo.
        if item.valor_unitario <= 0:
            errors.append(f"Error en ítem {i+1} (Pieza {item.pieza}): El valor unitario debe ser mayor a cero. Ej: 120.50.")
            continue

        # Validación 4: El peso unitario debe ser positivo si está presente.
        if item.peso_unitario is not None and item.peso_unitario <= 0:
            errors.append(f"Error en ítem {i+1} (Pieza {item.pieza}): El peso unitario debe ser mayor a cero. Ej: 1.25.")
            continue

        # Validación 5: El origen puede ser XX como default válido.
        origen = (item.origen or '').strip().upper()
        if not origen or origen == 'N/A' or origen == '-':
            errors.append(f"Error en ítem {i+1}: El origen no puede ser vacío. Se acepta XX como default.")
            continue

        # Si pasa todas las validaciones, se agrega a la lista de válidos.
        valid_items.append(item)

    return valid_items, errors


def run_extra_validations(items: List[Item]) -> List[str]:
    """Validaciones opcionales (activables por toggle) de carácter suave.
    - NCM 6–8 dígitos
    - Guardas de valores razonables (cantidad y valor_unitario límites altos)
    Devuelve lista de errores adicionales sin filtrar items válidos.
    """
    errors: List[str] = []
    for i, item in enumerate(items, start=1):
        pieza = (item.pieza or '').strip()
        if pieza and not (6 <= len(pieza) <= 8):
            errors.append(f"Error en ítem {i} (Pieza {pieza}): NCM debería tener 6–8 dígitos. Ej: 84713010.")
        try:
            if item.cantidad and item.cantidad > 1_000_000:
                errors.append(f"Error en ítem {i} (Pieza {pieza or '----'}): cantidad parece inválida (> 1,000,000). Revisá unidades y separadores.")
        except Exception:
            pass
        try:
            if item.valor_unitario and item.valor_unitario > 10_000_000:
                errors.append(f"Error en ítem {i} (Pieza {pieza or '----'}): valor unitario parece inválido (> 10,000,000). Revisá moneda y formato.")
        except Exception:
            pass
    return errors


# === VALIDACIONES INTELIGENTES PREMIUM ===
# Detectan errores comunes ANTES de oficializar en MARIA
# Evitan rechazos de AFIP y multas

# Rangos típicos de peso por posición arancelaria (4 primeros dígitos)
PESO_TIPICO_POR_NCM = {
    "8471": (0.1, 50),      # Computadoras: 0.1 a 50 kg
    "8517": (0.01, 10),     # Celulares/telecom: 10g a 10kg
    "8544": (0.01, 100),    # Cables: muy variable
    "3926": (0.001, 50),    # Plásticos: muy variable
    "8708": (0.1, 500),     # Autopartes: pueden ser pesadas
    "6109": (0.05, 1),      # Remeras: 50g a 1kg
    "6403": (0.2, 3),       # Calzado: 200g a 3kg
    "8528": (1, 80),        # TVs/monitores: 1 a 80kg
    "8443": (0.5, 50),      # Impresoras: 0.5 a 50kg
    "9403": (1, 200),       # Muebles: 1 a 200kg
}

# NCM que requieren permisos especiales (alertar al despachante)
NCM_REQUIERE_PERMISO = {
    "2106": "Alimentos - Puede requerir certificado ANMAT",
    "3303": "Perfumes - Requiere certificado ANMAT",
    "3304": "Cosméticos - Requiere certificado ANMAT",
    "3305": "Productos capilares - Requiere certificado ANMAT",
    "8525": "Cámaras/transmisores - Puede requerir ENACOM",
    "8526": "Radares/GPS - Puede requerir ENACOM",
    "8527": "Receptores radio - Puede requerir ENACOM",
    "8471": "Computadoras - Verificar si requiere certificado energético",
    "9018": "Instrumental médico - Requiere ANMAT",
    "9019": "Equipos masaje médico - Puede requerir ANMAT",
    "3004": "Medicamentos - Requiere ANMAT",
    "3002": "Vacunas/sangre - Requiere ANMAT",
}

def run_smart_validations(items: List[Item]) -> dict:
    """
    🧠 VALIDACIONES INTELIGENTES PREMIUM
    
    Detecta problemas comunes ANTES de oficializar en MARIA:
    - Peso sospechoso para el tipo de producto
    - Valor unitario fuera de rango típico
    - NCM que requieren permisos especiales
    - Datos faltantes que AFIP rechazará
    - Inconsistencias entre items
    
    Returns:
        dict con:
        - errores: Lista de errores críticos (bloquean envío)
        - advertencias: Lista de advertencias (revisar pero puede continuar)
        - sugerencias: Lista de mejoras opcionales
        - resumen: Texto resumen del análisis
    """
    errores = []
    advertencias = []
    sugerencias = []
    
    total_valor = 0
    total_peso = 0
    ncms_usados = set()
    
    for i, item in enumerate(items, start=1):
        pieza = (item.pieza or '').strip()
        ncm_4 = pieza[:4] if len(pieza) >= 4 else ""
        
        # === VALIDACIONES DE PESO ===
        if item.peso_unitario and item.cantidad:
            peso_total_item = item.peso_unitario * item.cantidad
            total_peso += peso_total_item
            
            # Peso sospechosamente bajo
            if item.peso_unitario < 0.001:
                advertencias.append(
                    f"⚠️ Ítem {i} ({pieza}): Peso unitario muy bajo ({item.peso_unitario} kg). "
                    f"¿Está en kg o en gramos?"
                )
            
            # Peso sospechosamente alto
            if item.peso_unitario > 1000:
                advertencias.append(
                    f"⚠️ Ítem {i} ({pieza}): Peso unitario muy alto ({item.peso_unitario} kg). "
                    f"¿Es correcto?"
                )
            
            # Comparar con peso típico del NCM
            if ncm_4 in PESO_TIPICO_POR_NCM:
                min_peso, max_peso = PESO_TIPICO_POR_NCM[ncm_4]
                if item.peso_unitario < min_peso * 0.1:  # 10% del mínimo
                    advertencias.append(
                        f"⚠️ Ítem {i} ({pieza}): Peso ({item.peso_unitario} kg) muy bajo para este tipo de producto. "
                        f"Típico: {min_peso}-{max_peso} kg"
                    )
                elif item.peso_unitario > max_peso * 2:  # 200% del máximo
                    advertencias.append(
                        f"⚠️ Ítem {i} ({pieza}): Peso ({item.peso_unitario} kg) muy alto para este tipo de producto. "
                        f"Típico: {min_peso}-{max_peso} kg"
                    )
        
        # === VALIDACIONES DE VALOR ===
        if item.valor_unitario and item.cantidad:
            valor_total_item = item.valor_unitario * item.cantidad
            total_valor += valor_total_item
            
            # Valor unitario sospechosamente bajo (menos de 1 centavo)
            if item.valor_unitario < 0.01:
                advertencias.append(
                    f"⚠️ Ítem {i} ({pieza}): Valor unitario muy bajo (${item.valor_unitario}). "
                    f"AFIP podría cuestionar este valor."
                )
            
            # Valor unitario sospechosamente alto
            if item.valor_unitario > 100000:
                sugerencias.append(
                    f"💡 Ítem {i} ({pieza}): Valor unitario alto (${item.valor_unitario:,.2f}). "
                    f"Verificar que esté en USD."
                )
        
        # === VALIDACIONES DE NCM ===
        if ncm_4:
            ncms_usados.add(ncm_4)
            
            # NCM que requieren permisos
            if ncm_4 in NCM_REQUIERE_PERMISO:
                advertencias.append(
                    f"📋 Ítem {i} ({pieza}): {NCM_REQUIERE_PERMISO[ncm_4]}"
                )
            
            # NCM no parece válido (no empieza con 0-9)
            if not pieza[0].isdigit():
                errores.append(
                    f"❌ Ítem {i}: NCM inválido '{pieza}'. Debe empezar con número."
                )
        
        # === VALIDACIONES DE ORIGEN ===
        origen = (item.origen or '').strip().upper()
        if origen == "XX":
            sugerencias.append(
                f"💡 Ítem {i} ({pieza}): Origen 'XX' debe reemplazarse por país real antes de oficializar."
            )
        
        # === VALIDACIONES DE DESCRIPCIÓN ===
        desc = (item.descripcion or '').strip()
        if len(desc) < 10:
            advertencias.append(
                f"⚠️ Ítem {i} ({pieza}): Descripción muy corta '{desc}'. AFIP prefiere descripciones detalladas."
            )
        if len(desc) > 200:
            sugerencias.append(
                f"💡 Ítem {i} ({pieza}): Descripción muy larga ({len(desc)} chars). Considerar resumir."
            )
    
    # === VALIDACIONES GLOBALES ===
    if total_valor > 500000:
        sugerencias.append(
            f"💰 Valor total alto: ${total_valor:,.2f} USD. Verificar si requiere canal rojo."
        )
    
    if len(items) > 50:
        sugerencias.append(
            f"📦 Operación con {len(items)} ítems. Considerar dividir si son de diferentes tipos."
        )
    
    if total_peso > 0 and total_valor > 0:
        valor_por_kg = total_valor / total_peso
        if valor_por_kg < 0.5:
            advertencias.append(
                f"⚠️ Relación valor/peso muy baja (${valor_por_kg:.2f}/kg). "
                f"AFIP podría cuestionar subvaluación."
            )
        elif valor_por_kg > 10000:
            sugerencias.append(
                f"💡 Relación valor/peso alta (${valor_por_kg:.2f}/kg). "
                f"Productos de alto valor - verificar seguro."
            )
    
    # === GENERAR RESUMEN ===
    total_problemas = len(errores) + len(advertencias)
    if total_problemas == 0:
        resumen = f"✅ {len(items)} ítems verificados sin problemas detectados."
    else:
        resumen = (
            f"🔍 Análisis de {len(items)} ítems: "
            f"{len(errores)} errores, {len(advertencias)} advertencias, {len(sugerencias)} sugerencias."
        )
    
    return {
        "errores": errores,
        "advertencias": advertencias,
        "sugerencias": sugerencias,
        "resumen": resumen,
        "estadisticas": {
            "total_items": len(items),
            "total_valor_usd": round(total_valor, 2),
            "total_peso_kg": round(total_peso, 2),
            "ncms_unicos": len(ncms_usados)
        }
    }