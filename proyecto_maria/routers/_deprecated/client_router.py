"""
Client Management Router - Modular client endpoints

This module contains all client management endpoints and related functionality
extracted from server_funcional.py to reduce its size and improve maintainability.

Protected Endpoints (require authentication):
- GET /api/clientes - List all clients
- POST /api/clientes - Create new client
- PUT /api/clientes/{cliente_id} - Update client
- DELETE /api/clientes/{cliente_id} - Delete client

Public Endpoints (no authentication):
- GET /api/clientes/public - List clients (public)
- POST /api/clientes/public - Create client (public)
- POST /api/clientes/demo - Create demo clients

Client Operations:
- POST /api/clientes/{cliente_id}/favorito - Mark as favorite
- GET /api/clientes/{cliente_id}/operaciones - Get operations
- POST /api/clientes/{cliente_id}/operaciones - Add operation
- POST /api/clientes/{cliente_id}/operaciones/demo - Add demo operations
- GET /api/clientes/{cliente_id}/metricas - Get metrics
- GET /api/clientes/{cliente_id}/export.csv - Export to CSV

Column Mapping:
- GET /api/clientes/{cliente_id}/column_mapping - Get mapping
- POST /api/clientes/{cliente_id}/column_mapping - Set mapping
- DELETE /api/clientes/{cliente_id}/column_mapping - Delete mapping

Template Generation:
- POST /api/clientes/{cliente_id}/plantilla - Generate client template
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict
import os
import json

# Project imports
import sys

# Setup path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import auth
try:
    from proyecto_maria.auth import require_role
except ImportError:
    from ..auth import require_role

# Security modules (Blue Team hardening)
try:
    from proyecto_maria.security.input_validation import (
        validate_email,
        validate_cuit,
        validate_string_length,
        sanitize_html
    )
    from proyecto_maria.security.log_sanitizer import get_safe_error_message
    SECURITY_MODULES_AVAILABLE = True
except ImportError:
    print("⚠️ Security modules not available in client_router, using basic security only")
    SECURITY_MODULES_AVAILABLE = False

# Import DataStore - use lazy loading to avoid circular imports
# DataStore will be injected from server_funcional.py
DataStore = None
store = None

def get_store():
    """Get the global DataStore instance from server_funcional.py"""
    global store, DataStore
    if store is None:
        # Import DataStore from the legacy database.py file
        try:
            import importlib.util
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database.py')
            spec = importlib.util.spec_from_file_location("legacy_database", db_path)
            legacy_db = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(legacy_db)
            DataStore = legacy_db.DataStore
            store = DataStore()
        except Exception as e:
            print(f"Warning: Could not load DataStore: {e}")
            # Create a dummy store for testing
            class DummyStore:
                def list_clients(self): return []
                def create_client(self, data): return data
                def update_client(self, id, data): return data
                def delete_client(self, id): return True
                def get_client(self, id): return {}
                def set_favorite(self, id, fav): pass
                def get_operations_by_client(self, id): return []
                def add_operation(self, id, data): return data
                def compute_metrics(self, id): return {}
                def build_csv(self, id): return ""
                def get_column_mapping(self, id): return {}
                def set_column_mapping(self, id, mapping): return True
            store = DummyStore()
    return store

# Create router
router = APIRouter(tags=["Client Management"])

# Constants
DATA_DIR = os.getenv('DATA_DIR', 'data')
os.makedirs(DATA_DIR, exist_ok=True)


# === MODELS ===

class Cliente(BaseModel):
    nombre: str
    email: str = ""
    telefono: str = ""
    direccion: str = ""
    notas: str = ""


# === HELPER FUNCTIONS ===

def audit_log(user: Dict, action: str, detail: Dict) -> None:
    """Simple audit logging function"""
    import logging
    logger = logging.getLogger("maria.client_router")
    logger.info(json.dumps({
        "action": action,
        "user": user.get("sub") if user else "anonymous",
        "roles": user.get("roles") if user else [],
        "detail": detail,
    }))


# === PROTECTED ENDPOINTS (REQUIRE AUTHENTICATION) ===

@router.get('/api/clientes')
async def get_clientes(user=Depends(require_role("operador"))):
    """List all clients"""
    audit_log(user, "list_clients", {})
    return {"clientes": get_store().list_clients()}


@router.post('/api/clientes')
async def crear_cliente(cliente: Cliente, user=Depends(require_role("operador"))):
    """Create new client"""
    created = get_store().create_client(cliente.dict())
    audit_log(user, "create_client", {"cliente_id": created.get("id")})
    return {"mensaje": "Cliente creado exitosamente", "cliente": created}


@router.put('/api/clientes/{cliente_id}')
async def actualizar_cliente(cliente_id: str, cliente: Cliente, user=Depends(require_role("operador"))):
    """Update existing client"""
    try:
        updated = get_store().update_client(cliente_id, cliente.dict())
        audit_log(user, "update_client", {"cliente_id": cliente_id})
        return {"mensaje": "Cliente actualizado exitosamente", "cliente": updated}
    except KeyError:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")


@router.delete('/api/clientes/{cliente_id}')
async def eliminar_cliente(cliente_id: str, user=Depends(require_role("operador"))):
    """Delete client"""
    ok = get_store().delete_client(cliente_id)
    audit_log(user, "delete_client", {"cliente_id": cliente_id})
    if not ok:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"mensaje": "Cliente eliminado exitosamente"}


# === PUBLIC ENDPOINTS (NO AUTHENTICATION) ===

@router.post('/api/clientes/demo')
@router.post('/api/clientes/demo/')
async def crear_clientes_demo():
    """Create demo clients for testing"""
    demo_clients = [
        {
            "id": "demo-1",
            "nombre": "Importadora DEMO S.A.",
            "cuit": "20-12345678-9",
            "email": "demo@importadora.com.ar",
            "telefono": "011-4000-1234",
            "direccion": "Av. Corrientes 1234, CABA",
            "favorito": True,
            "notas": "Cliente demo para testing",
            "ultima_operacion": "2025-09-25"
        },
        {
            "id": "demo-2",
            "nombre": "Comercial BETA LTDA",
            "cuit": "30-98765432-1",
            "email": "contacto@beta.com.ar",
            "telefono": "011-5000-5678",
            "direccion": "Av. Santa Fe 5678, CABA",
            "favorito": False,
            "notas": "Especialista en electrónicos",
            "ultima_operacion": "2025-09-20"
        },
        {
            "id": "demo-3",
            "nombre": "Global Trade Solutions",
            "cuit": "27-11223344-5",
            "email": "info@globaltrade.com.ar",
            "telefono": "011-6000-9012",
            "direccion": "Puerto Madero 123, CABA",
            "favorito": True,
            "notas": "Importador mayorista",
            "ultima_operacion": "2025-09-22"
        }
    ]

    return {
        "success": True,
        "clients": demo_clients,
        "count": len(demo_clients)
    }


@router.get('/api/clientes/public')
@router.get('/api/clientes/public/')
async def get_clientes_public():
    """Get clients without authentication for frontend"""
    try:
        clientes = get_store().list_clients()
        return {
            "success": True,
            "clientes": clientes,
            "count": len(clientes)
        }
    except Exception as e:
        return {
            "success": False,
            "detail": str(e),
            "clientes": []
        }


@router.post('/api/clientes/public')
@router.post('/api/clientes/public/')
async def crear_cliente_public(request: Request):
    """
    Create client without authentication for frontend
    SECURITY: Input validation for email, CUIT, and field lengths
    """
    try:
        data = await request.json()

        # Validate minimum data
        if not data.get('nombre') or not data.get('email'):
            return {
                "success": False,
                "detail": "Nombre y email son requeridos"
            }

        # Security: Validate and sanitize inputs
        if SECURITY_MODULES_AVAILABLE:
            try:
                # Validate email format
                data['email'] = validate_email(data['email'])

                # Validate nombre length
                data['nombre'] = validate_string_length(data['nombre'], 'name', max_length=100)

                # Sanitize HTML in nombre to prevent XSS
                data['nombre'] = sanitize_html(data['nombre'])

                # Validate CUIT if present
                if data.get('cuit'):
                    data['cuit'] = validate_cuit(data['cuit'])

                # Validate other string fields
                if data.get('razon_social'):
                    data['razon_social'] = validate_string_length(data['razon_social'], 'name', max_length=200)
                    data['razon_social'] = sanitize_html(data['razon_social'])

                if data.get('direccion'):
                    data['direccion'] = validate_string_length(data['direccion'], 'address', max_length=300)
                    data['direccion'] = sanitize_html(data['direccion'])

            except ValueError as ve:
                return {
                    "success": False,
                    "detail": str(ve)
                }

        # Create client
        created = get_store().create_client(data)

        return {
            "success": True,
            "mensaje": "Cliente creado exitosamente",
            "cliente": created
        }
    except Exception as e:
        # Security: Safe error message
        if SECURITY_MODULES_AVAILABLE:
            safe_msg = get_safe_error_message(e, debug=False)
            return {
                "success": False,
                "detail": safe_msg
            }
        else:
            return {
                "success": False,
                "detail": str(e)
            }


@router.put('/api/clientes/public/{cliente_id}')
async def actualizar_cliente_public(cliente_id: str, cliente: Cliente):
    """Update client without authentication for frontend"""
    try:
        updated = get_store().update_client(cliente_id, cliente.dict())
        return {"success": True, "mensaje": "Cliente actualizado exitosamente", "cliente": updated}
    except KeyError:
        return {"success": False, "detail": "Cliente no encontrado"}
    except Exception as e:
        return {"success": False, "detail": str(e)}


@router.delete('/api/clientes/public/{cliente_id}')
async def eliminar_cliente_public(cliente_id: str):
    """Delete client without authentication for frontend"""
    try:
        ok = get_store().delete_client(cliente_id)
        if not ok:
            return {"success": False, "detail": "Cliente no encontrado"}
        return {"success": True, "mensaje": "Cliente eliminado exitosamente"}
    except Exception as e:
        return {"success": False, "detail": str(e)}


@router.post('/api/clientes/{cliente_id}/favorito')
async def marcar_favorito(cliente_id: str, request: Request):
    """Mark client as favorite"""
    body = await request.json()
    favorito = bool(body.get('favorito', False))
    # Validate existence
    if not get_store().get_client(cliente_id):
        return {"error": "Cliente no encontrado"}, 404
    get_store().set_favorite(cliente_id, favorito)
    return {"mensaje": "Favorito actualizado", "cliente": get_store().get_client(cliente_id)}


# === CLIENT OPERATIONS ===

@router.get('/api/clientes/{cliente_id}/operaciones')
async def get_operaciones_cliente(cliente_id: str):
    """Get all operations for a client"""
    return {"cliente_id": cliente_id, "operaciones": get_store().get_operations_by_client(cliente_id)}


@router.post('/api/clientes/{cliente_id}/operaciones')
async def add_operacion_cliente(cliente_id: str, request: Request):
    """Add operation to client"""
    payload = await request.json()
    operacion = get_store().add_operation(cliente_id, payload)
    return {"mensaje": "Operación guardada", "operacion": operacion}


@router.post('/api/clientes/{cliente_id}/operaciones/demo')
async def add_operaciones_demo(cliente_id: str):
    """Generate demo operations to visualize history"""
    demo_items = [
        {"pieza": "84713010", "descripcion": "Laptop", "origen": "CN", "cantidad": 10, "valor_unitario": 800, "peso_unitario": 2.2},
        {"pieza": "85171200", "descripcion": "Teléfonos", "origen": "VN", "cantidad": 25, "valor_unitario": 120, "peso_unitario": 0.3},
    ]
    for _ in range(3):
        get_store().add_operation(cliente_id, {"items": demo_items})
    return {"mensaje": "Operaciones demo creadas"}


@router.get('/api/clientes/{cliente_id}/metricas')
async def metrics_cliente(cliente_id: str):
    """Get metrics for client"""
    return get_store().compute_metrics(cliente_id)


@router.get('/api/clientes/{cliente_id}/export.csv')
async def export_csv(cliente_id: str):
    """Export client data to CSV"""
    csv_content = get_store().build_csv(cliente_id)
    return Response(
        content=csv_content,
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="cliente_{cliente_id}.csv"'}
    )


# === COLUMN MAPPING ===

@router.get('/api/clientes/{cliente_id}/column_mapping')
async def get_column_mapping(cliente_id: str):
    """Get column mapping for client"""
    try:
        return {"cliente_id": cliente_id, "mapping": get_store().get_column_mapping(cliente_id)}
    except Exception as e:
        return {"cliente_id": cliente_id, "mapping": {}, "detail": str(e)}


@router.post('/api/clientes/{cliente_id}/column_mapping')
async def set_column_mapping(cliente_id: str, request: Request):
    """Set column mapping for client"""
    data = await request.json()
    mapping = data.get('mapping') or {}
    ok = get_store().set_column_mapping(cliente_id, mapping)
    return {"success": bool(ok), "cliente_id": cliente_id, "mapping": get_store().get_column_mapping(cliente_id)}


@router.delete('/api/clientes/{cliente_id}/column_mapping')
async def delete_column_mapping(cliente_id: str):
    """Delete column mapping for client"""
    try:
        get_store().set_column_mapping(cliente_id, {})
        return {"success": True, "cliente_id": cliente_id, "mapping": {}}
    except Exception as e:
        return {"success": False, "detail": str(e)}


# === TEMPLATE GENERATION ===

@router.post('/api/clientes/{cliente_id}/plantilla')
async def generar_plantilla_cliente(cliente_id: str):
    """Generate Excel template for client using column mapping"""
    try:
        mapping = get_store().get_column_mapping(cliente_id) or {}
        allowed = ['pieza', 'descripcion', 'origen', 'cantidad', 'valor_unitario', 'peso_unitario']
        # Invert mapping: canonical -> source header
        inv: dict[str, str] = {}
        for src, canon in mapping.items():
            if canon in allowed and src:
                inv[canon] = src

        headers = [inv.get(c, c) for c in allowed]

        import pandas as pd
        from datetime import datetime
        GENERATED_DIR = os.path.join(DATA_DIR, 'generated')
        os.makedirs(GENERATED_DIR, exist_ok=True)

        df = pd.DataFrame(columns=headers)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'PLANTILLA_CLIENTE_{cliente_id}_{ts}.xlsx'
        path = os.path.join(GENERATED_DIR, filename)
        df.to_excel(path, index=False)

        return {
            'success': True,
            'filename': filename,
            'download_url': f'/download/{filename}',
            'columns': headers,
        }
    except Exception as e:
        return {'success': False, 'detail': str(e)}


# ==================== AUTO-COMPLETADO INTELIGENTE ====================

@router.post('/api/clientes/detect')
async def detect_client(text: str):
    """
    Detectar cliente automáticamente del texto del PDF
    Busca por CUIT o nombre de empresa
    """
    from ..services.client_service import ClientService

    try:
        client_data = await ClientService.detect_client_from_text(text)

        if client_data:
            # Obtener productos frecuentes para sugerencias
            suggestions = await ClientService.get_frequent_products(
                client_data['client_id'],
                limit=10
            )

            return {
                'success': True,
                'client': client_data,
                'suggestions': {
                    'productos_frecuentes': suggestions,
                    'ncm_mas_usado': suggestions[0]['ncm'] if suggestions else None,
                    'origen_frecuente': suggestions[0]['origen_frecuente'] if suggestions else 'XX'
                }
            }
        else:
            return {
                'success': False,
                'message': 'Cliente no detectado en el texto'
            }

    except Exception as e:
        return {'success': False, 'detail': str(e)}


@router.get('/api/clientes/{cliente_id}/productos-frecuentes')
async def get_frequent_products(cliente_id: str, limit: int = 20):
    """
    Obtener productos frecuentes del cliente para auto-completado
    """
    from ..services.client_service import ClientService

    try:
        products = await ClientService.get_frequent_products(cliente_id, limit)

        return {
            'success': True,
            'productos': products,
            'total': len(products)
        }

    except Exception as e:
        return {'success': False, 'detail': str(e)}


class AutocompleteRequest(BaseModel):
    client_id: str
    items: list


@router.post('/api/items/autocomplete')
async def autocomplete_items(request: AutocompleteRequest):
    """
    Auto-completar items basándose en el historial del cliente
    """
    from ..services.client_service import ClientService

    try:
        completed_items = await ClientService.autocomplete_items(
            request.client_id,
            request.items
        )

        # Contar items auto-completados
        autocompleted_count = sum(1 for item in completed_items if item.get('autocompleted'))

        return {
            'success': True,
            'items': completed_items,
            'total_items': len(completed_items),
            'autocompleted_count': autocompleted_count,
            'autocomplete_rate': round(autocompleted_count / len(completed_items) * 100, 1) if completed_items else 0
        }

    except Exception as e:
        return {'success': False, 'detail': str(e)}


class UpdateHistoryRequest(BaseModel):
    client_id: str
    items: list


@router.post('/api/clientes/{cliente_id}/update-history')
async def update_product_history(cliente_id: str, items: list):
    """
    Actualizar historial de productos del cliente
    Se llama después de confirmar una operación
    """
    from ..services.client_service import ClientService

    try:
        await ClientService.update_product_history(cliente_id, items)

        return {
            'success': True,
            'message': f'Historial actualizado con {len(items)} items'
        }

    except Exception as e:
        return {'success': False, 'detail': str(e)}
