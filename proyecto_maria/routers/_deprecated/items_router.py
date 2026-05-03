"""
Items Router - Corrección Rápida Post-Extracción
Endpoints para editar, duplicar y modificar items de una operación

Feature #2: Permite corregir items después de extraer PDF
- Edición individual de items
- Operaciones batch (aplicar NCM a todos, etc.)
- Duplicar items
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/items", tags=["items"])


# ==================== MODELOS ====================

class ItemUpdate(BaseModel):
    """Request para actualizar un item"""
    pieza: Optional[str] = Field(None, description="NCM/HS Code")
    descripcion: Optional[str] = Field(None, description="Descripción del producto")
    origen: Optional[str] = Field(None, description="País de origen")
    cantidad: Optional[float] = Field(None, gt=0, description="Cantidad")
    valor_unitario: Optional[float] = Field(None, gt=0, description="Valor FOB unitario")
    peso_unitario: Optional[float] = Field(None, gt=0, description="Peso unitario en KG")
    marca: Optional[str] = Field(None, description="Marca")
    modelo: Optional[str] = Field(None, description="Modelo")


class BatchUpdateRequest(BaseModel):
    """Request para actualización batch de items"""
    operation: str = Field(..., description="Operación: 'apply_ncm', 'apply_origen', 'apply_value', 'delete'")
    value: Optional[Any] = Field(None, description="Valor a aplicar")
    filter: Optional[Dict[str, Any]] = Field(None, description="Filtro para seleccionar items")
    item_ids: Optional[List[str]] = Field(None, description="IDs específicos de items a modificar")


class DuplicateItemRequest(BaseModel):
    """Request para duplicar un item"""
    cantidad: Optional[float] = Field(None, gt=0, description="Nueva cantidad (opcional)")
    modificaciones: Optional[ItemUpdate] = Field(None, description="Modificaciones adicionales")


# ==================== STORAGE IN-MEMORY ====================
# Simulación de DB para vibe coding rápido
# TODO: Migrar a DataStore cuando esté listo

_operations_store: Dict[str, Dict] = {}
_items_store: Dict[str, Dict] = {}


def _get_item(item_id: str) -> Dict:
    """Helper: Obtener item por ID"""
    if item_id not in _items_store:
        raise HTTPException(status_code=404, detail=f"Item {item_id} no encontrado")
    return _items_store[item_id]


def _get_operation(operation_id: str) -> Dict:
    """Helper: Obtener operación por ID"""
    if operation_id not in _operations_store:
        raise HTTPException(status_code=404, detail=f"Operación {operation_id} no encontrada")
    return _operations_store[operation_id]


# ==================== ENDPOINTS ====================

@router.put("/{item_id}")
async def update_item(item_id: str, updates: ItemUpdate):
    """
    Actualizar campos individuales de un item

    **Caso de uso**: Despachante extrae PDF pero necesita corregir 2-3 items

    **Ejemplo**:
    ```json
    PUT /api/items/item-123
    {
      "pieza": "84713010",
      "cantidad": 15,
      "peso_unitario": 3.0
    }
    ```

    **Response**:
    ```json
    {
      "success": true,
      "item": {
        "id": "item-123",
        "pieza": "84713010",
        "descripcion": "Laptop Dell",
        "cantidad": 15,
        "peso_unitario": 3.0,
        ...
      }
    }
    ```
    """
    try:
        item = _get_item(item_id)

        # Aplicar actualizaciones (solo campos no-None)
        update_data = updates.model_dump(exclude_none=True)

        for field, value in update_data.items():
            if field == "origen":
                value = value.upper()[:3]  # Normalizar origen
            item[field] = value

        # Recalcular total
        if "cantidad" in update_data or "valor_unitario" in update_data:
            item["total"] = round(item["cantidad"] * item["valor_unitario"], 2)

        logger.info(f"✅ Item {item_id} actualizado: {list(update_data.keys())}")

        return {
            "success": True,
            "item": item,
            "updated_fields": list(update_data.keys())
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error actualizando item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-update")
async def batch_update_items(request: BatchUpdateRequest):
    """
    Actualización batch de múltiples items

    **Operaciones soportadas**:
    - `apply_ncm`: Aplicar mismo NCM a múltiples items
    - `apply_origen`: Aplicar mismo origen a múltiples items
    - `apply_value`: Aplicar mismo valor a campo específico
    - `multiply_quantity`: Multiplicar cantidades por factor
    - `delete`: Eliminar items seleccionados

    **Ejemplo 1: Aplicar NCM a todos los "laptops"**:
    ```json
    POST /api/items/batch-update
    {
      "operation": "apply_ncm",
      "value": "84713010",
      "filter": {
        "descripcion_contains": "laptop"
      }
    }
    ```

    **Ejemplo 2: Cambiar origen de items específicos**:
    ```json
    {
      "operation": "apply_origen",
      "value": "BR",
      "item_ids": ["item-1", "item-2", "item-3"]
    }
    ```

    **Ejemplo 3: Duplicar cantidades**:
    ```json
    {
      "operation": "multiply_quantity",
      "value": 2.0,
      "filter": {"origen": "CN"}
    }
    ```
    """
    try:
        # Seleccionar items a modificar
        items_to_update = []

        if request.item_ids:
            # Por IDs específicos
            items_to_update = [_get_item(item_id) for item_id in request.item_ids]

        elif request.filter:
            # Por filtro
            for item_id, item in _items_store.items():
                match = True

                # Filtro por descripción
                if "descripcion_contains" in request.filter:
                    desc_filter = request.filter["descripcion_contains"].lower()
                    if desc_filter not in item.get("descripcion", "").lower():
                        match = False

                # Filtro por origen
                if "origen" in request.filter:
                    if item.get("origen") != request.filter["origen"]:
                        match = False

                # Filtro por NCM
                if "pieza" in request.filter:
                    if item.get("pieza") != request.filter["pieza"]:
                        match = False

                if match:
                    items_to_update.append(item)

        else:
            raise HTTPException(status_code=400, detail="Debe especificar item_ids o filter")

        if not items_to_update:
            return {
                "success": True,
                "items_updated": 0,
                "message": "No se encontraron items que coincidan con el filtro"
            }

        # Aplicar operación
        updated_count = 0

        if request.operation == "apply_ncm":
            for item in items_to_update:
                item["pieza"] = request.value
                updated_count += 1

        elif request.operation == "apply_origen":
            for item in items_to_update:
                item["origen"] = str(request.value).upper()[:3]
                updated_count += 1

        elif request.operation == "apply_value":
            # Formato: {"field": "marca", "value": "LENOVO"}
            if not isinstance(request.value, dict) or "field" not in request.value:
                raise HTTPException(status_code=400, detail="apply_value requiere {field, value}")

            field = request.value["field"]
            value = request.value["value"]

            for item in items_to_update:
                if field in item:
                    item[field] = value
                    updated_count += 1

        elif request.operation == "multiply_quantity":
            factor = float(request.value)
            for item in items_to_update:
                item["cantidad"] = round(item["cantidad"] * factor, 2)
                item["total"] = round(item["cantidad"] * item["valor_unitario"], 2)
                updated_count += 1

        elif request.operation == "delete":
            for item in items_to_update:
                item_id = item["id"]
                del _items_store[item_id]
                updated_count += 1

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Operación '{request.operation}' no soportada"
            )

        logger.info(f"✅ Batch update: {request.operation} aplicado a {updated_count} items")

        return {
            "success": True,
            "operation": request.operation,
            "items_updated": updated_count,
            "items": items_to_update if request.operation != "delete" else []
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en batch update: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{item_id}/duplicate")
async def duplicate_item(item_id: str, request: DuplicateItemRequest):
    """
    Duplicar un item con modificaciones opcionales

    **Caso de uso**: Mismo producto pero diferente cantidad/origen

    **Ejemplo**:
    ```json
    POST /api/items/item-123/duplicate
    {
      "cantidad": 5,
      "modificaciones": {
        "origen": "BR"
      }
    }
    ```

    **Response**:
    ```json
    {
      "success": true,
      "original_item": {...},
      "duplicated_item": {
        "id": "item-456",  # Nuevo ID
        "cantidad": 5,     # Modificado
        "origen": "BR",    # Modificado
        ...                # Resto copiado del original
      }
    }
    ```
    """
    try:
        import uuid

        original_item = _get_item(item_id)

        # Crear copia del item
        new_item = original_item.copy()
        new_item["id"] = str(uuid.uuid4())

        # Aplicar modificación de cantidad si se especifica
        if request.cantidad is not None:
            new_item["cantidad"] = request.cantidad
            new_item["total"] = round(new_item["cantidad"] * new_item["valor_unitario"], 2)

        # Aplicar modificaciones adicionales
        if request.modificaciones:
            mods = request.modificaciones.model_dump(exclude_none=True)
            for field, value in mods.items():
                if field == "origen":
                    value = value.upper()[:3]
                new_item[field] = value

            # Recalcular total si cambió cantidad o valor
            if "cantidad" in mods or "valor_unitario" in mods:
                new_item["total"] = round(new_item["cantidad"] * new_item["valor_unitario"], 2)

        # Guardar nuevo item
        _items_store[new_item["id"]] = new_item

        logger.info(f"✅ Item {item_id} duplicado → {new_item['id']}")

        return {
            "success": True,
            "original_item": original_item,
            "duplicated_item": new_item
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error duplicando item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{item_id}")
async def get_item(item_id: str):
    """
    Obtener detalles de un item específico

    **Response**:
    ```json
    {
      "success": true,
      "item": {
        "id": "item-123",
        "pieza": "84713010",
        "descripcion": "Laptop Dell",
        "origen": "CN",
        "cantidad": 10,
        "valor_unitario": 500.0,
        "peso_unitario": 2.5,
        "total": 5000.0
      }
    }
    ```
    """
    try:
        item = _get_item(item_id)

        return {
            "success": True,
            "item": item
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{item_id}")
async def delete_item(item_id: str):
    """
    Eliminar un item

    **Response**:
    ```json
    {
      "success": true,
      "message": "Item item-123 eliminado",
      "deleted_item": {...}
    }
    ```
    """
    try:
        item = _get_item(item_id)
        del _items_store[item_id]

        logger.info(f"✅ Item {item_id} eliminado")

        return {
            "success": True,
            "message": f"Item {item_id} eliminado",
            "deleted_item": item
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error eliminando item {item_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HELPERS PARA TESTING ====================

@router.post("/_test/seed")
async def seed_test_data():
    """
    Endpoint de testing: Crear datos de prueba
    Solo para desarrollo - remover en producción
    """
    import uuid

    # Limpiar store
    _items_store.clear()
    _operations_store.clear()

    # Crear operación de prueba
    op_id = str(uuid.uuid4())
    _operations_store[op_id] = {
        "id": op_id,
        "client_id": "test-client-123",
        "total_items": 0
    }

    # Crear items de prueba
    test_items = [
        {
            "id": str(uuid.uuid4()),
            "operation_id": op_id,
            "pieza": "84713010",
            "descripcion": "LAPTOP DELL INSPIRON 15",
            "origen": "CN",
            "cantidad": 10.0,
            "valor_unitario": 500.0,
            "peso_unitario": 2.5,
            "marca": "DELL",
            "modelo": "INSPIRON 15",
            "total": 5000.0
        },
        {
            "id": str(uuid.uuid4()),
            "operation_id": op_id,
            "pieza": "85171200",
            "descripcion": "CELULAR SAMSUNG GALAXY S21",
            "origen": "KR",
            "cantidad": 20.0,
            "valor_unitario": 300.0,
            "peso_unitario": 0.3,
            "marca": "SAMSUNG",
            "modelo": "GALAXY S21",
            "total": 6000.0
        },
        {
            "id": str(uuid.uuid4()),
            "operation_id": op_id,
            "pieza": "40111000",
            "descripcion": "NEUMATICOS 185/65 R15",
            "origen": "BR",
            "cantidad": 100.0,
            "valor_unitario": 80.0,
            "peso_unitario": 8.5,
            "marca": "PIRELLI",
            "modelo": "P4",
            "total": 8000.0
        }
    ]

    for item in test_items:
        _items_store[item["id"]] = item

    _operations_store[op_id]["total_items"] = len(test_items)

    return {
        "success": True,
        "message": "Test data creado",
        "operation_id": op_id,
        "items": test_items
    }
