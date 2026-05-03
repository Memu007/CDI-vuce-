"""
Middleware de validación de planes de suscripción.

Permite restringir endpoints según el plan del usuario (basic, premium, etc.)
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status
from proyecto_maria.auth.jwt_utils import get_current_user


def require_plan(*allowed_plans: str):
    """
    Decorator para restringir acceso a endpoints según plan de suscripción.

    Args:
        *allowed_plans: Lista de planes permitidos (ej: "premium", "enterprise")

    Usage:
        @app.get("/api/premium-feature")
        async def premium_endpoint(user: Annotated[dict, Depends(require_plan("premium"))]):
            return {"data": "premium content"}

    Raises:
        HTTPException 403: Si el usuario no tiene un plan permitido
    """
    normalized_plans: list[str] = []
    for plan in allowed_plans or ():
        if isinstance(plan, (list, tuple, set)):
            normalized_plans.extend(str(p).lower() for p in plan)
        else:
            normalized_plans.append(str(plan).lower())

    async def checker(user: Annotated[dict, Depends(get_current_user)]):
        user_plan = str(user.get("plan", "basic")).lower()

        if normalized_plans and user_plan not in normalized_plans:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Esta función requiere plan {' o '.join(normalized_plans)}. Tu plan actual: {user_plan}"
            )

        return user

    return checker


def get_user_plan(user: Annotated[dict, Depends(get_current_user)]) -> str:
    """
    Helper para obtener el plan del usuario actual.

    Returns:
        str: Plan del usuario (basic, premium, etc.)
    """
    return user.get("plan", "basic")


def validate_file_size(file_size_bytes: int, user_plan: str) -> tuple[bool, str]:
    """
    Valida el tamaño de un archivo según el plan del usuario.

    Args:
        file_size_bytes: Tamaño del archivo en bytes
        user_plan: Plan del usuario ('basic' o 'premium')

    Returns:
        tuple: (es_válido, mensaje_error)
    """
    from proyecto_maria.config import get_settings
    settings = get_settings()

    # Convertir bytes a MB
    file_size_mb = file_size_bytes / (1024 * 1024)

    if user_plan == 'basic':
        max_size = settings.max_file_size_basic_mb
        if file_size_mb > max_size:
            return False, f"Plan Basic: archivo demasiado grande ({file_size_mb:.1f}MB). Máximo: {max_size}MB"
    else:  # premium
        max_size = settings.max_file_size_premium_mb
        if file_size_mb > max_size:
            return False, f"Archivo demasiado grande ({file_size_mb:.1f}MB). Máximo: {max_size}MB"

    return True, ""


def validate_file_magic_bytes(file_content: bytes, expected_types: list[str]) -> tuple[bool, str]:
    """
    Valida el tipo de archivo real mediante magic bytes (no solo extensión).

    Args:
        file_content: Primeros bytes del archivo
        expected_types: Tipos esperados ['pdf', 'xlsx', 'xls']

    Returns:
        tuple: (es_válido, tipo_detectado)
    """
    # Magic bytes para tipos comunes
    magic_bytes_map = {
        'pdf': b'%PDF',
        'xlsx': b'PK\x03\x04',  # ZIP-based (Excel moderno)
        'xls': b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1',  # OLE2 (Excel antiguo)
        'zip': b'PK\x03\x04',
    }

    # Verificar magic bytes
    for file_type in expected_types:
        magic = magic_bytes_map.get(file_type)
        if magic and file_content.startswith(magic):
            return True, file_type

    # Si llegamos aquí, el archivo no coincide con ningún tipo esperado
    detected_hex = file_content[:8].hex() if len(file_content) >= 8 else "desconocido"
    return False, f"Tipo de archivo no válido. Magic bytes: {detected_hex}"
