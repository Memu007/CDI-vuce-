from pydantic import BaseModel, field_validator, computed_field, ConfigDict
from typing import List, Optional

class Item(BaseModel):
    """Define la estructura de cada ítem en una operación para formato AVG.

    Incluye los 13 campos requeridos por la planilla AVG real de AFIP/VUCE:
    Pieza, Descripcion, Origen, Peso Unitario, Cantidad, Valor Unitario,
    Marca, Modelo, Version, otros, separador, ventaja, TOTAL

    NOTA: Se removieron tipos Strict para máxima compatibilidad con frontend.
    Pydantic hace coerción automática de tipos (ej: "123" -> 123, null -> "")
    """
    # Permite campos extras del frontend sin error
    model_config = ConfigDict(extra='ignore')
    
    # Campos principales - SIN Strict types para permitir coerción automática
    pieza: str = ""  # NCM/HS Code (ahora con default para evitar errores)
    codigo_parte: str = ""  # Código de parte/SKU del proveedor
    descripcion: str = ""  # Descripción del producto
    origen: str = "XX"  # País de origen (código 2-3 letras)
    peso_unitario: float = 0.0  # Peso unitario en KG
    cantidad: float = 0.0  # Cantidad de piezas
    valor_unitario: float = 0.0  # Valor FOB unitario en USD

    # Campos adicionales para AVG completo (todos con defaults)
    marca: str = ""  # Marca del producto (TUPER, Synergy, etc.)
    modelo: str = ""  # Modelo/Part Number (NT50T, PN 4559940, etc.)
    version: str = ""  # Versión/Especificación técnica
    otros: str = ""  # Otros datos técnicos/normas/estándares
    separador: str = ""  # Campo separador (uso interno AVG)
    ventaja: str = ""  # Ventajas/Características especiales
    
    # Campos extras del frontend (ignorados pero aceptados)
    tariff_group: Optional[str] = None
    order_index: Optional[int] = None
    vision_model: Optional[str] = None
    source_page: Optional[int] = None
    llm_provider: Optional[str] = None

    @computed_field
    @property
    def total(self) -> float:
        """Campo TOTAL calculado automáticamente (cantidad × valor_unitario)"""
        return round(float(self.cantidad) * float(self.valor_unitario), 2)

    @field_validator('pieza')
    @classmethod
    def validate_ncm(cls, v):
        """Valida que el NCM tenga un formato básico válido"""
        if v and len(str(v).strip()) >= 4:
            return str(v).strip()
        return v

    @field_validator('origen')
    @classmethod
    def validate_origin(cls, v):
        """Normaliza el código de país de origen"""
        if v:
            return str(v).strip().upper()[:3]  # Máximo 3 caracteres
        return "XX"  # Default si no se especifica

    @field_validator('cantidad', 'valor_unitario', 'peso_unitario', mode='before')
    @classmethod
    def coerce_to_float(cls, v):
        """Convierte cualquier valor a float, con fallback a 0.0"""
        if v is None or v == "" or (isinstance(v, str) and v.strip() == ""):
            return 0.0
        try:
            return float(v)
        except (ValueError, TypeError):
            return 0.0

class OperationPayload(BaseModel):
    """Define la carga de datos que se recibe para procesar una operación."""
    operation_id: str
    items: List[Item]

    @field_validator('operation_id')
    @classmethod
    def operation_id_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('operation_id no puede estar vacío')
        return v

