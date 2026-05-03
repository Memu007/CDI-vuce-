"""
Validation Router - Validación Pre-envío con Alertas
Feature #3: Validar operaciones antes de generar AVG para AFIP

Validaciones implementadas:
- NCM válido (6-8 dígitos numéricos)
- Origen válido (código ISO2/3)
- Valores dentro de rangos razonables
- Peso unitario consistente
- Items duplicados (mismo NCM + descripción)
- Permisos especiales requeridos (químicos, alimentos, etc.)

Sistema de alertas:
- 🔴 CRÍTICO: Bloquea envío, debe corregirse
- 🟡 WARNING: Sospechoso, revisar antes de enviar
- 🟢 OK: Todo correcto
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/validation", tags=["validation"])


# ==================== MODELOS ====================

class ValidationIssue(BaseModel):
    """Un problema de validación detectado"""
    level: str = Field(..., description="critical, warning, info")
    item_index: Optional[int] = Field(None, description="Índice del item afectado")
    field: Optional[str] = Field(None, description="Campo afectado")
    message: str = Field(..., description="Descripción del problema")
    suggestion: Optional[str] = Field(None, description="Sugerencia para corregir")


class ValidationRequest(BaseModel):
    """Request para validar operación"""
    items: List[Dict[str, Any]] = Field(..., description="Items a validar")
    strict_mode: bool = Field(False, description="Modo estricto (más restricciones)")


class ValidationResponse(BaseModel):
    """Response de validación"""
    valid: bool = Field(..., description="¿Es válida la operación?")
    can_submit: bool = Field(..., description="¿Se puede enviar a AFIP?")
    issues: List[ValidationIssue] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=dict)


# ==================== VALIDADORES ====================

def validate_ncm(ncm: str) -> Optional[ValidationIssue]:
    """Validar formato de NCM"""
    if not ncm or not ncm.strip():
        return ValidationIssue(
            level="critical",
            field="pieza",
            message="NCM vacío o inválido",
            suggestion="Ingrese código NCM de 6-8 dígitos"
        )

    ncm_clean = str(ncm).strip()

    if not re.match(r'^\d{6,8}$', ncm_clean):
        return ValidationIssue(
            level="critical",
            field="pieza",
            message=f"NCM '{ncm}' tiene formato inválido (debe ser 6-8 dígitos numéricos)",
            suggestion="Verificar código NCM en base de datos AFIP/Tarifar"
        )

    # Warning para NCMs sospechosos
    if ncm_clean.startswith("9999"):
        return ValidationIssue(
            level="warning",
            field="pieza",
            message=f"NCM '{ncm}' parece ser un código genérico",
            suggestion="Verificar que sea el código correcto"
        )

    return None


def validate_origen(origen: str) -> Optional[ValidationIssue]:
    """Validar código de país de origen"""
    if not origen or not origen.strip():
        return ValidationIssue(
            level="critical",
            field="origen",
            message="Origen vacío",
            suggestion="Ingrese código de país (ej: CN, BR, US)"
        )

    origen_clean = origen.strip().upper()

    # Debe ser 2-3 letras
    if not re.match(r'^[A-Z]{2,3}$', origen_clean):
        return ValidationIssue(
            level="critical",
            field="origen",
            message=f"Origen '{origen}' inválido (debe ser código ISO2/3)",
            suggestion="Usar código de 2-3 letras (ej: CN, BRA, USA)"
        )

    # Warning para orígenes poco comunes
    common_origins = ["CN", "BR", "US", "DE", "IT", "KR", "VN", "MX", "AR", "PY", "UY", "CL"]
    if origen_clean not in common_origins and len(origen_clean) == 2:
        return ValidationIssue(
            level="info",
            field="origen",
            message=f"Origen '{origen}' es poco común",
            suggestion="Verificar que el código de país sea correcto"
        )

    return None


def validate_cantidad(cantidad: float, descripcion: str = "") -> Optional[ValidationIssue]:
    """Validar cantidad"""
    if cantidad <= 0:
        return ValidationIssue(
            level="critical",
            field="cantidad",
            message=f"Cantidad inválida: {cantidad}",
            suggestion="La cantidad debe ser mayor a 0"
        )

    # Warning para cantidades sospechosamente grandes
    if cantidad > 100000:
        return ValidationIssue(
            level="warning",
            field="cantidad",
            message=f"Cantidad muy alta: {cantidad:,.0f} unidades",
            suggestion="Verificar que la cantidad sea correcta"
        )

    # Warning para cantidades con muchos decimales (probable error)
    if isinstance(cantidad, float) and len(str(cantidad).split('.')[-1]) > 3:
        return ValidationIssue(
            level="warning",
            field="cantidad",
            message=f"Cantidad con muchos decimales: {cantidad}",
            suggestion="Redondear a 2-3 decimales máximo"
        )

    return None


def validate_valor_unitario(valor: float, descripcion: str = "") -> Optional[ValidationIssue]:
    """Validar valor unitario FOB"""
    if valor <= 0:
        return ValidationIssue(
            level="critical",
            field="valor_unitario",
            message=f"Valor unitario inválido: {valor}",
            suggestion="El valor debe ser mayor a 0"
        )

    # Warning para valores muy bajos (posible error)
    if valor < 0.01:
        return ValidationIssue(
            level="warning",
            field="valor_unitario",
            message=f"Valor unitario muy bajo: USD {valor}",
            suggestion="Verificar que el valor sea correcto (¿falta multiplicar?)"
        )

    # Warning para valores muy altos
    if valor > 1000000:
        return ValidationIssue(
            level="warning",
            field="valor_unitario",
            message=f"Valor unitario muy alto: USD {valor:,.2f}",
            suggestion="Verificar que sea el valor unitario y no el total"
        )

    return None


def validate_peso_unitario(peso: float, descripcion: str = "") -> Optional[ValidationIssue]:
    """Validar peso unitario"""
    if peso <= 0:
        return ValidationIssue(
            level="critical",
            field="peso_unitario",
            message=f"Peso unitario inválido: {peso}",
            suggestion="El peso debe ser mayor a 0"
        )

    # Warning para pesos muy bajos (probable error)
    if peso < 0.001:
        return ValidationIssue(
            level="warning",
            field="peso_unitario",
            message=f"Peso unitario muy bajo: {peso} kg",
            suggestion="Verificar unidad de medida (¿está en gramos?)"
        )

    # Warning para pesos muy altos
    if peso > 10000:
        return ValidationIssue(
            level="warning",
            field="peso_unitario",
            message=f"Peso unitario muy alto: {peso:,.2f} kg",
            suggestion="Verificar que sea el peso unitario y no el total"
        )

    return None


def check_duplicates(items: List[Dict]) -> List[ValidationIssue]:
    """Detectar items duplicados (mismo NCM + descripción)"""
    issues = []
    seen = {}

    for idx, item in enumerate(items):
        ncm = item.get("pieza", "").strip()
        desc = item.get("descripcion", "").strip().lower()
        key = f"{ncm}_{desc[:30]}"  # Primeros 30 caracteres de descripción

        if key in seen:
            issues.append(ValidationIssue(
                level="warning",
                item_index=idx,
                field="pieza",
                message=f"Item duplicado detectado (NCM {ncm})",
                suggestion=f"¿Es el mismo producto que item {seen[key]}? Considerar consolidar"
            ))
        else:
            seen[key] = idx

    return issues


def check_special_permissions(ncm: str, descripcion: str) -> Optional[ValidationIssue]:
    """Verificar si requiere permisos especiales (SENASA, ANMAT, etc.)"""
    # NCMs que requieren permisos especiales
    special_ncms = {
        "0201": ("SENASA", "Carnes frescas"),
        "0202": ("SENASA", "Carnes congeladas"),
        "03": ("SENASA", "Pescados"),
        "07": ("SENASA", "Hortalizas"),
        "08": ("SENASA", "Frutas"),
        "28": ("ANMAT", "Productos químicos"),
        "29": ("ANMAT", "Productos químicos orgánicos"),
        "30": ("ANMAT", "Productos farmacéuticos"),
        "84": (None, None),  # Maquinaria - generalmente OK
        "85": (None, None),  # Aparatos eléctricos - generalmente OK
    }

    ncm_prefix = ncm[:2] if len(ncm) >= 2 else ""

    if ncm_prefix in special_ncms:
        authority, category = special_ncms[ncm_prefix]
        if authority:
            return ValidationIssue(
                level="warning",
                field="pieza",
                message=f"NCM {ncm} requiere permiso especial de {authority}",
                suggestion=f"Verificar permisos de {authority} para {category}"
            )

    # Keywords en descripción que pueden requerir permisos
    desc_lower = descripcion.lower()
    if any(word in desc_lower for word in ["alimento", "medicamento", "droga", "químico", "carne", "pescado"]):
        return ValidationIssue(
            level="warning",
            field="descripcion",
            message="Producto puede requerir permisos especiales",
            suggestion="Verificar con SENASA, ANMAT o autoridad competente"
        )

    return None


# ==================== ENDPOINTS ====================

@router.post("/validate-operation")
async def validate_operation(request: ValidationRequest):
    """
    Validar operación completa antes de enviar a AFIP

    **Ejemplo**:
    ```json
    POST /api/validation/validate-operation
    {
      "items": [
        {
          "pieza": "84713010",
          "descripcion": "LAPTOP DELL",
          "origen": "CN",
          "cantidad": 10,
          "valor_unitario": 500,
          "peso_unitario": 2.5
        }
      ],
      "strict_mode": false
    }
    ```

    **Response**:
    ```json
    {
      "valid": true,
      "can_submit": true,
      "issues": [],
      "summary": {
        "critical": 0,
        "warning": 0,
        "info": 0
      }
    }
    ```

    **Sistema de alertas**:
    - 🔴 **CRITICAL**: Bloquea envío, debe corregirse
    - 🟡 **WARNING**: Sospechoso, revisar antes de enviar
    - 🟢 **OK**: Todo correcto, puede enviar
    """
    try:
        issues: List[ValidationIssue] = []

        # Validar cada item
        for idx, item in enumerate(request.items):
            # Validar NCM
            if issue := validate_ncm(item.get("pieza", "")):
                issue.item_index = idx
                issues.append(issue)

            # Validar origen
            if issue := validate_origen(item.get("origen", "")):
                issue.item_index = idx
                issues.append(issue)

            # Validar cantidad
            if issue := validate_cantidad(
                item.get("cantidad", 0),
                item.get("descripcion", "")
            ):
                issue.item_index = idx
                issues.append(issue)

            # Validar valor unitario
            if issue := validate_valor_unitario(
                item.get("valor_unitario", 0),
                item.get("descripcion", "")
            ):
                issue.item_index = idx
                issues.append(issue)

            # Validar peso unitario
            if issue := validate_peso_unitario(
                item.get("peso_unitario", 0),
                item.get("descripcion", "")
            ):
                issue.item_index = idx
                issues.append(issue)

            # Verificar permisos especiales
            if issue := check_special_permissions(
                item.get("pieza", ""),
                item.get("descripcion", "")
            ):
                issue.item_index = idx
                issues.append(issue)

        # Validaciones globales
        duplicate_issues = check_duplicates(request.items)
        issues.extend(duplicate_issues)

        # Calcular resumen
        summary = {
            "critical": len([i for i in issues if i.level == "critical"]),
            "warning": len([i for i in issues if i.level == "warning"]),
            "info": len([i for i in issues if i.level == "info"])
        }

        # Determinar si es válida
        has_critical = summary["critical"] > 0
        can_submit = not has_critical

        if request.strict_mode:
            # En modo estricto, warnings también bloquean
            can_submit = can_submit and summary["warning"] == 0

        logger.info(f"✅ Validación completada: {len(request.items)} items, {len(issues)} issues")

        return {
            "valid": not has_critical,
            "can_submit": can_submit,
            "issues": [issue.model_dump() for issue in issues],
            "summary": summary,
            "total_items": len(request.items),
            "strict_mode": request.strict_mode
        }

    except Exception as e:
        logger.error(f"❌ Error en validación: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quick-check")
async def quick_check(items: List[Dict[str, Any]]):
    """
    Check rápido de validación (solo críticos)

    **Response**:
    ```json
    {
      "ok": true,
      "critical_issues": 0
    }
    ```
    """
    try:
        request = ValidationRequest(items=items, strict_mode=False)
        result = await validate_operation(request)

        return {
            "ok": result["summary"]["critical"] == 0,
            "critical_issues": result["summary"]["critical"],
            "warning_issues": result["summary"]["warning"]
        }

    except Exception as e:
        logger.error(f"❌ Error en quick check: {e}")
        raise HTTPException(status_code=500, detail=str(e))
