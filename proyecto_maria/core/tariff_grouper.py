"""
🏷️ AGRUPADOR DE POSICIONES ARANCELARIAS
Módulo para agrupar productos por posición arancelaria antes de generar Excel AVG
"""

from typing import Dict, List, Tuple
from models.operations import Item
from collections import defaultdict
import re

class TariffGroup:
    """
    Representa un grupo de productos bajo la misma posición arancelaria
    """
    def __init__(self, position_code: str, description: str = ""):
        self.position_code = position_code  # Ej: "8471" 
        self.description = description      # Ej: "Máquinas de procesamiento de datos"
        self.items: List[Item] = []
        self.total_quantity = 0.0
        self.total_value = 0.0
        
    def add_item(self, item: Item):
        """Agrega un item al grupo y actualiza totales"""
        self.items.append(item)
        self.total_quantity += item.cantidad
        self.total_value += (item.cantidad * item.valor_unitario)
        
    def get_summary(self) -> Dict:
        """Retorna resumen del grupo para la interfaz"""
        return {
            "position_code": self.position_code,
            "description": self.description,
            "items_count": len(self.items),
            "total_quantity": self.total_quantity,
            "total_value": self.total_value,
            "items": [item.model_dump() for item in self.items]
        }

def extract_tariff_position(ncm_code: str) -> str:
    """
    Extrae la posición arancelaria (primeros 4 dígitos) de un código NCM
    
    Ejemplos:
    - "84713010" → "8471"
    - "85176290" → "8517"
    - "90318090" → "9031"
    """
    # Limpiar el código NCM de espacios y caracteres no numéricos
    clean_ncm = re.sub(r'[^\d]', '', str(ncm_code))
    
    # Tomar primeros 4 dígitos
    if len(clean_ncm) >= 4:
        return clean_ncm[:4]
    else:
        return "0000"  # Código por defecto para NCMs inválidos

def get_tariff_description(position_code: str) -> str:
    """
    Retorna descripción de la posición arancelaria basada en nomenclatura estándar
    
    Este es un mapeo básico de las posiciones más comunes.
    En versión premium se podría conectar con API oficial.
    """
    descriptions = {
        "8471": "Máquinas de procesamiento de datos y sus unidades",
        "8517": "Aparatos eléctricos de telefonía o telegrafía",
        "8542": "Circuitos electrónicos integrados",
        "9031": "Instrumentos y aparatos de medida o control",
        "8528": "Monitores y proyectores sin aparato receptor",
        "8504": "Transformadores eléctricos, convertidores",
        "8473": "Partes y accesorios de máquinas de procesamiento",
        "8518": "Micrófonos y altavoces; amplificadores",
        "8544": "Hilos, cables y demás conductores aislados",
        "8536": "Aparatos para corte, seccionamiento o protección"
    }
    
    return descriptions.get(position_code, f"Posición arancelaria {position_code}")

def group_items_by_tariff(items: List[Item]) -> Dict[str, TariffGroup]:
    """
    🎯 FUNCIÓN PRINCIPAL: Agrupa items por posición arancelaria
    
    Args:
        items: Lista de items extraídos del Excel/PDF
    
    Returns:
        Dict con grupos organizados por posición arancelaria
        
    Ejemplo de resultado:
    {
        "8471": TariffGroup(items=[laptop1, laptop2], total_value=15000),
        "8517": TariffGroup(items=[router1, phone1], total_value=8500),
        "9031": TariffGroup(items=[sensor1], total_value=125)
    }
    """
    groups = {}
    
    for item in items:
        # Extraer posición arancelaria del NCM
        position = extract_tariff_position(item.pieza)
        
        # Crear grupo si no existe
        if position not in groups:
            description = get_tariff_description(position)
            groups[position] = TariffGroup(position, description)
        
        # Agregar item al grupo
        groups[position].add_item(item)
    
    return groups

def create_grouping_summary(groups: Dict[str, TariffGroup]) -> Dict:
    """
    Crea resumen para mostrar en la interfaz de agrupación
    
    Retorna información que el despachante necesita ver antes de
    generar el Excel final, incluyendo estadísticas por grupo.
    """
    total_items = sum(len(group.items) for group in groups.values())
    total_value = sum(group.total_value for group in groups.values())
    
    summary = {
        "total_groups": len(groups),
        "total_items": total_items,
        "total_value": total_value,
        "groups": []
    }
    
    # Ordenar grupos por valor total (descendente)
    sorted_groups = sorted(groups.items(), key=lambda x: x[1].total_value, reverse=True)
    
    for position_code, group in sorted_groups:
        group_summary = group.get_summary()
        summary["groups"].append(group_summary)
    
    return summary

def validate_grouping(groups: Dict[str, TariffGroup]) -> Tuple[bool, List[str]]:
    """
    Valida que la agrupación sea correcta antes de generar Excel
    
    Verifica:
    - Todos los grupos tienen al menos 1 item
    - No hay posiciones arancelarias inválidas
    - Totales son consistentes
    """
    errors = []
    
    for position_code, group in groups.items():
        # Validar que el grupo no esté vacío
        if len(group.items) == 0:
            errors.append(f"Grupo {position_code} está vacío")
            
        # Validar código de posición
        if not re.match(r'^\d{4}$', position_code):
            errors.append(f"Código de posición inválido: {position_code}")
            
        # Validar que los totales sean positivos
        if group.total_value <= 0:
            errors.append(f"Grupo {position_code} tiene valor total inválido: {group.total_value}")
    
    return len(errors) == 0, errors

def merge_groups_if_needed(groups: Dict[str, TariffGroup], max_groups: int = 10) -> Dict[str, TariffGroup]:
    """
    Si hay demasiados grupos pequeños, los consolida para simplificar
    
    Esto es útil cuando hay muchas posiciones con pocos items cada una.
    Mantiene los grupos grandes y consolida los pequeños.
    """
    if len(groups) <= max_groups:
        return groups  # No necesita consolidación
    
    # Ordenar por valor total
    sorted_groups = sorted(groups.items(), key=lambda x: x[1].total_value, reverse=True)
    
    # Mantener los grupos más grandes
    main_groups = dict(sorted_groups[:max_groups-1])
    
    # Consolidar grupos pequeños en "OTROS"
    other_items = []
    for _, group in sorted_groups[max_groups-1:]:
        other_items.extend(group.items)
    
    if other_items:
        otros_group = TariffGroup("OTROS", "Otras posiciones arancelarias")
        for item in other_items:
            otros_group.add_item(item)
        main_groups["OTROS"] = otros_group
    
    return main_groups

# === FUNCIONES DE UTILIDAD ===

def get_most_common_origin(items: List[Item]) -> str:
    """Retorna el país de origen más común en una lista de items"""
    origins = [item.origen for item in items]
    return max(set(origins), key=origins.count) if origins else "XX"

def calculate_group_statistics(groups: Dict[str, TariffGroup]) -> Dict:
    """Calcula estadísticas útiles para el despachante"""
    stats = {
        "total_groups": len(groups),
        "total_items": sum(len(group.items) for group in groups.values()),
        "total_value": sum(group.total_value for group in groups.values()),
        "largest_group": None,
        "most_valuable_group": None
    }
    
    if groups:
        # Grupo con más items
        largest = max(groups.items(), key=lambda x: len(x[1].items))
        stats["largest_group"] = {
            "position": largest[0],
            "items_count": len(largest[1].items)
        }
        
        # Grupo con más valor
        most_valuable = max(groups.items(), key=lambda x: x[1].total_value)
        stats["most_valuable_group"] = {
            "position": most_valuable[0],
            "total_value": most_valuable[1].total_value
        }
    
    return stats

