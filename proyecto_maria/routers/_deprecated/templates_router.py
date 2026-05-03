"""
Templates Router - Plantillas de Operaciones
Feature #4: Despacho Express - Repetir operaciones recurrentes en 30 segundos

Permite guardar operaciones como plantillas y reutilizarlas cambiando solo:
- Cantidades
- Valores unitarios
- Fecha

Ideal para:
- Importaciones mensuales del mismo proveedor
- Clientes con productos recurrentes
- Operaciones repetitivas (ej: 100 neumáticos cada mes)
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import uuid

# Import auth middleware
try:
    from proyecto_maria.auth import require_plan
except ImportError:
    from ..auth import require_plan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/templates", tags=["templates"])


# ==================== MODELOS ====================

class ItemOverride(BaseModel):
    """Override para un item específico en la plantilla"""
    item_index: int = Field(..., description="Índice del item en la plantilla (0-based)")
    cantidad: Optional[float] = Field(None, gt=0)
    valor_unitario: Optional[float] = Field(None, gt=0)
    peso_unitario: Optional[float] = Field(None, gt=0)


class OperationTemplate(BaseModel):
    """Plantilla de operación"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str = Field(..., description="ID del cliente")
    template_name: str = Field(..., description="Nombre de la plantilla")
    description: Optional[str] = Field(None, description="Descripción de la plantilla")

    # Items de la plantilla (estructura completa)
    items: List[Dict[str, Any]] = Field(..., description="Items template")

    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None
    times_used: int = 0

    # Tags para búsqueda
    tags: List[str] = Field(default_factory=list)


class CreateTemplateRequest(BaseModel):
    """Request para crear plantilla desde operación"""
    operation_id: str = Field(..., description="ID de la operación a guardar como plantilla")
    template_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = Field(default_factory=list)


class UseTemplateRequest(BaseModel):
    """Request para usar una plantilla"""
    template_id: str = Field(..., description="ID de la plantilla")
    overrides: Optional[List[ItemOverride]] = Field(default_factory=list, description="Modificaciones a items")
    global_multiply: Optional[float] = Field(None, gt=0, description="Multiplicar todas las cantidades por este factor")


# ==================== STORAGE ====================
# In-memory storage para vibe coding rápido
# TODO: Migrar a PostgreSQL

_templates_store: Dict[str, OperationTemplate] = {}


# Importar stores de otros routers
try:
    from proyecto_maria.routers.items_router import _items_store, _operations_store
except ImportError:
    # Fallback si no se puede importar
    _items_store = {}
    _operations_store = {}


# ==================== ENDPOINTS ====================

@router.post("/from-operation")
async def create_template_from_operation(
    request: CreateTemplateRequest,
    user: dict = Depends(require_plan("premium"))
):
    """
    Guardar una operación como plantilla reutilizable

    **Caso de uso**: Importación mensual de 100 neumáticos desde Brasil

    **Ejemplo**:
    ```json
    POST /api/templates/from-operation
    {
      "operation_id": "op-123",
      "template_name": "Importación mensual neumáticos BR",
      "description": "100 neumáticos Pirelli desde Brasil (MERCOSUR)",
      "tags": ["neumaticos", "brasil", "mensual"]
    }
    ```

    **Response**:
    ```json
    {
      "success": true,
      "template": {
        "id": "tpl-456",
        "template_name": "Importación mensual neumáticos BR",
        "items": [...],  // Todos los items de la operación
        "times_used": 0
      }
    }
    ```
    """
    try:
        # Verificar que la operación existe
        if request.operation_id not in _operations_store:
            raise HTTPException(status_code=404, detail=f"Operación {request.operation_id} no encontrada")

        operation = _operations_store[request.operation_id]

        # Obtener todos los items de la operación
        operation_items = [
            item for item in _items_store.values()
            if item.get("operation_id") == request.operation_id
        ]

        if not operation_items:
            raise HTTPException(
                status_code=400,
                detail="La operación no tiene items para guardar como plantilla"
            )

        # Crear plantilla
        template = OperationTemplate(
            client_id=operation.get("client_id", "unknown"),
            template_name=request.template_name,
            description=request.description,
            items=operation_items,
            tags=request.tags or []
        )

        # Guardar en store
        _templates_store[template.id] = template

        logger.info(f"✅ Plantilla creada: {template.template_name} ({len(operation_items)} items)")

        return {
            "success": True,
            "template": template.model_dump(),
            "message": f"Plantilla '{template.template_name}' creada con {len(operation_items)} items"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando plantilla: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_templates(
    client_id: Optional[str] = None,
    tag: Optional[str] = None,
    user: dict = Depends(require_plan("premium"))
):
    """
    Listar todas las plantillas disponibles

    **Filtros**:
    - `client_id`: Filtrar por cliente
    - `tag`: Filtrar por tag

    **Ejemplo**:
    ```
    GET /api/templates?client_id=client-123
    GET /api/templates?tag=mensual
    ```

    **Response**:
    ```json
    {
      "success": true,
      "templates": [
        {
          "id": "tpl-1",
          "template_name": "Importación mensual neumáticos",
          "items_count": 3,
          "times_used": 5,
          "last_used": "2025-09-30T10:00:00",
          "tags": ["neumaticos", "brasil"]
        }
      ],
      "total": 1
    }
    ```
    """
    try:
        templates = list(_templates_store.values())

        # Filtrar por client_id
        if client_id:
            templates = [t for t in templates if t.client_id == client_id]

        # Filtrar por tag
        if tag:
            templates = [t for t in templates if tag in t.tags]

        # Ordenar por más usado
        templates.sort(key=lambda t: t.times_used, reverse=True)

        # Formato resumido
        templates_summary = [
            {
                "id": t.id,
                "template_name": t.template_name,
                "description": t.description,
                "items_count": len(t.items),
                "times_used": t.times_used,
                "last_used": t.last_used,
                "tags": t.tags,
                "created_at": t.created_at
            }
            for t in templates
        ]

        return {
            "success": True,
            "templates": templates_summary,
            "total": len(templates_summary)
        }

    except Exception as e:
        logger.error(f"❌ Error listando plantillas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{template_id}")
async def get_template(
    template_id: str,
    user: dict = Depends(require_plan("premium"))
):
    """
    Obtener detalles completos de una plantilla

    **Response**:
    ```json
    {
      "success": true,
      "template": {
        "id": "tpl-456",
        "template_name": "Importación mensual neumáticos",
        "items": [
          {
            "pieza": "40111000",
            "descripcion": "NEUMATICOS 185/65 R15",
            "origen": "BR",
            "cantidad": 100,
            "valor_unitario": 80.0
          }
        ],
        "times_used": 5
      }
    }
    ```
    """
    try:
        if template_id not in _templates_store:
            raise HTTPException(status_code=404, detail=f"Plantilla {template_id} no encontrada")

        template = _templates_store[template_id]

        return {
            "success": True,
            "template": template.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo plantilla: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/use")
async def use_template(
    request: UseTemplateRequest,
    user: dict = Depends(require_plan("premium"))
):
    """
    Crear nueva operación desde plantilla

    **Caso de uso**: Es el 1ro del mes, repetir importación de neumáticos pero esta vez 150 unidades

    **Ejemplo 1: Cambiar cantidades específicas**:
    ```json
    POST /api/templates/use
    {
      "template_id": "tpl-456",
      "overrides": [
        {"item_index": 0, "cantidad": 150}  // 100 → 150 neumáticos
      ]
    }
    ```

    **Ejemplo 2: Multiplicar todo x2**:
    ```json
    {
      "template_id": "tpl-456",
      "global_multiply": 2.0  // Duplicar todas las cantidades
    }
    ```

    **Ejemplo 3: Cambiar cantidad y precio**:
    ```json
    {
      "template_id": "tpl-456",
      "overrides": [
        {
          "item_index": 0,
          "cantidad": 150,
          "valor_unitario": 85.0  // Precio subió
        }
      ]
    }
    ```

    **Response**:
    ```json
    {
      "success": true,
      "operation": {
        "id": "op-789",
        "items": [
          {
            "id": "item-new-1",
            "pieza": "40111000",
            "cantidad": 150,  // Modificado
            "valor_unitario": 80.0,
            "total": 12000.0  // Recalculado
          }
        ]
      },
      "template_used": "Importación mensual neumáticos",
      "changes_applied": ["cantidad modificada en item 0"]
    }
    ```
    """
    try:
        # Verificar que la plantilla existe
        if request.template_id not in _templates_store:
            raise HTTPException(status_code=404, detail=f"Plantilla {request.template_id} no encontrada")

        template = _templates_store[request.template_id]

        # Crear nueva operación
        new_operation_id = str(uuid.uuid4())
        new_operation = {
            "id": new_operation_id,
            "client_id": template.client_id,
            "template_id": template.id,
            "template_name": template.template_name,
            "total_items": len(template.items)
        }

        _operations_store[new_operation_id] = new_operation

        # Copiar items de la plantilla
        new_items = []
        changes_applied = []

        for idx, template_item in enumerate(template.items):
            # Crear copia del item
            new_item = template_item.copy()
            new_item["id"] = str(uuid.uuid4())
            new_item["operation_id"] = new_operation_id

            # Aplicar global multiply si existe
            if request.global_multiply:
                old_cantidad = new_item["cantidad"]
                new_item["cantidad"] = round(old_cantidad * request.global_multiply, 2)
                changes_applied.append(f"Item {idx}: cantidad {old_cantidad}→{new_item['cantidad']} (x{request.global_multiply})")

            # Aplicar overrides específicos
            if request.overrides:
                for override in request.overrides:
                    if override.item_index == idx:
                        if override.cantidad is not None:
                            old_val = new_item["cantidad"]
                            new_item["cantidad"] = override.cantidad
                            changes_applied.append(f"Item {idx}: cantidad {old_val}→{override.cantidad}")

                        if override.valor_unitario is not None:
                            old_val = new_item["valor_unitario"]
                            new_item["valor_unitario"] = override.valor_unitario
                            changes_applied.append(f"Item {idx}: valor_unitario {old_val}→{override.valor_unitario}")

                        if override.peso_unitario is not None:
                            old_val = new_item["peso_unitario"]
                            new_item["peso_unitario"] = override.peso_unitario
                            changes_applied.append(f"Item {idx}: peso_unitario {old_val}→{override.peso_unitario}")

            # Recalcular total
            new_item["total"] = round(new_item["cantidad"] * new_item["valor_unitario"], 2)

            # Guardar nuevo item
            _items_store[new_item["id"]] = new_item
            new_items.append(new_item)

        # Actualizar estadísticas de la plantilla
        template.times_used += 1
        template.last_used = datetime.now().isoformat()

        logger.info(f"✅ Operación creada desde plantilla '{template.template_name}' ({len(new_items)} items)")

        return {
            "success": True,
            "operation": {
                "id": new_operation_id,
                "template_name": template.template_name,
                "items": new_items
            },
            "template_used": template.template_name,
            "changes_applied": changes_applied if changes_applied else ["Ningún cambio, plantilla original"],
            "total_items": len(new_items),
            "total_value": sum(item["total"] for item in new_items)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error usando plantilla: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{template_id}")
async def update_template(
    template_id: str,
    updates: Dict[str, Any],
    user: dict = Depends(require_plan("premium"))
):
    """
    Actualizar plantilla (nombre, descripción, tags)

    **Ejemplo**:
    ```json
    PUT /api/templates/tpl-456
    {
      "template_name": "Importación neumáticos BR (actualizado)",
      "tags": ["neumaticos", "brasil", "mensual", "prioritario"]
    }
    ```
    """
    try:
        if template_id not in _templates_store:
            raise HTTPException(status_code=404, detail=f"Plantilla {template_id} no encontrada")

        template = _templates_store[template_id]

        # Actualizar campos permitidos
        if "template_name" in updates:
            template.template_name = updates["template_name"]
        if "description" in updates:
            template.description = updates["description"]
        if "tags" in updates:
            template.tags = updates["tags"]

        logger.info(f"✅ Plantilla {template_id} actualizada")

        return {
            "success": True,
            "template": template.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando plantilla: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{template_id}")
async def delete_template(
    template_id: str,
    user: dict = Depends(require_plan("premium"))
):
    """
    Eliminar una plantilla

    **Response**:
    ```json
    {
      "success": true,
      "message": "Plantilla eliminada",
      "deleted_template": {...}
    }
    ```
    """
    try:
        if template_id not in _templates_store:
            raise HTTPException(status_code=404, detail=f"Plantilla {template_id} no encontrada")

        template = _templates_store[template_id]
        del _templates_store[template_id]

        logger.info(f"✅ Plantilla {template_id} eliminada")

        return {
            "success": True,
            "message": f"Plantilla '{template.template_name}' eliminada",
            "deleted_template": template.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error eliminando plantilla: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TESTING HELPER ====================

@router.get("/_stats")
async def get_templates_stats(
    user: dict = Depends(require_plan("premium"))
):
    """
    Estadísticas de uso de plantillas (para admin/monitoring)

    **Response**:
    ```json
    {
      "total_templates": 5,
      "total_uses": 25,
      "most_used": {
        "template_name": "Importación neumáticos BR",
        "times_used": 15
      }
    }
    ```
    """
    try:
        templates = list(_templates_store.values())
        total_uses = sum(t.times_used for t in templates)

        most_used = max(templates, key=lambda t: t.times_used) if templates else None

        return {
            "success": True,
            "stats": {
                "total_templates": len(templates),
                "total_uses": total_uses,
                "most_used": {
                    "template_name": most_used.template_name,
                    "times_used": most_used.times_used
                } if most_used else None
            }
        }

    except Exception as e:
        logger.error(f"❌ Error obteniendo stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
