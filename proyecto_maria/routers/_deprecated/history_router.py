"""
Router para historial de operaciones (Premium)
Permite consultar operaciones anteriores agrupadas por NCM
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/history", tags=["history"])

# DataStore global - se inyecta desde server_funcional.py
_datastore = None

def set_datastore(ds):
    """Inyectar DataStore desde el servidor principal"""
    global _datastore
    _datastore = ds

def get_datastore():
    """Dependency para obtener DataStore"""
    if _datastore is None:
        raise HTTPException(status_code=500, detail="DataStore no inicializado")
    return _datastore


# Import auth después para evitar conflictos circulares
try:
    from proyecto_maria.auth import require_plan
except ImportError:
    # Fallback sin autenticación (solo para desarrollo)
    def require_plan(plans):
        def dependency(user_plan: str = "premium"):
            return user_plan
        return dependency


@router.get("/operations")
async def get_operations_history(
    days: int = Query(default=30, ge=1, le=365, description="Días hacia atrás"),
    limit: int = Query(default=100, ge=1, le=1000, description="Máximo de operaciones"),
    user_plan: str = Depends(require_plan(["premium"]))
):
    """
    Obtener historial de operaciones (solo Premium)

    Returns:
        List[Dict]: Lista de operaciones con metadata
    """
    ds = get_datastore()

    # Calcular fecha límite
    fecha_desde = datetime.now() - timedelta(days=days)

    # Obtener todas las operaciones
    all_operations = ds.get_all_operations()

    # Filtrar por fecha y limitar
    filtered_ops = [
        op for op in all_operations
        if op.get("timestamp") and
        datetime.fromisoformat(op["timestamp"].replace("Z", "+00:00")) >= fecha_desde
    ]

    # Ordenar por timestamp descendente (más reciente primero)
    filtered_ops.sort(
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )

    # Limitar cantidad
    result = filtered_ops[:limit]

    return {
        "operations": result,
        "total": len(result),
        "days": days,
        "fecha_desde": fecha_desde.isoformat()
    }


@router.get("/operations/by-ncm/{ncm}")
async def get_operations_by_ncm(
    ncm: str,
    limit: int = Query(default=50, ge=1, le=500),
    user_plan: str = Depends(require_plan(["premium"]))
):
    """
    Obtener operaciones que contienen un NCM específico (solo Premium)

    Args:
        ncm: Código NCM (4-8 dígitos)
        limit: Cantidad máxima de resultados

    Returns:
        Dict con operaciones que incluyen ese NCM
    """
    ds = get_datastore()

    # Normalizar NCM (primeros 4 dígitos para agrupación)
    ncm_prefix = ncm[:4] if len(ncm) >= 4 else ncm

    all_operations = ds.get_all_operations()

    # Filtrar operaciones que contengan items con ese NCM
    matching_ops = []
    for op in all_operations:
        items = op.get("items", [])
        # Buscar si algún item tiene ese NCM
        has_ncm = any(
            item.get("tariff_code", "").startswith(ncm_prefix)
            for item in items
        )
        if has_ncm:
            matching_ops.append(op)

    # Ordenar por timestamp descendente
    matching_ops.sort(
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )

    result = matching_ops[:limit]

    return {
        "ncm": ncm,
        "operations": result,
        "total": len(result)
    }


@router.get("/stats")
async def get_history_stats(
    days: int = Query(default=30, ge=1, le=365),
    user_plan: str = Depends(require_plan(["premium"]))
):
    """
    Obtener estadísticas del historial (solo Premium)

    Returns:
        Dict con métricas: total operaciones, items procesados, NCMs únicos, etc.
    """
    ds = get_datastore()

    # Calcular fecha límite
    fecha_desde = datetime.now() - timedelta(days=days)

    all_operations = ds.get_all_operations()

    # Filtrar por fecha
    filtered_ops = [
        op for op in all_operations
        if op.get("timestamp") and
        datetime.fromisoformat(op["timestamp"].replace("Z", "+00:00")) >= fecha_desde
    ]

    # Calcular estadísticas
    total_operations = len(filtered_ops)
    total_items = sum(len(op.get("items", [])) for op in filtered_ops)

    # NCMs únicos
    unique_ncms = set()
    for op in filtered_ops:
        for item in op.get("items", []):
            tariff = item.get("tariff_code", "")
            if tariff and len(tariff) >= 4:
                unique_ncms.add(tariff[:4])

    # Clientes únicos (si existe campo client_id)
    unique_clients = set()
    for op in filtered_ops:
        client_id = op.get("client_id")
        if client_id:
            unique_clients.add(client_id)

    # Operaciones por día (últimos 7 días)
    ops_by_day = {}
    for i in range(7):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        ops_by_day[day] = 0

    for op in filtered_ops:
        timestamp = op.get("timestamp", "")
        if timestamp:
            day = timestamp[:10]  # Formato YYYY-MM-DD
            if day in ops_by_day:
                ops_by_day[day] += 1

    return {
        "total_operations": total_operations,
        "total_items": total_items,
        "unique_ncms": len(unique_ncms),
        "unique_clients": len(unique_clients),
        "days": days,
        "ops_by_day": ops_by_day,
        "avg_items_per_operation": round(total_items / total_operations, 2) if total_operations > 0 else 0
    }


@router.get("/ncms/frequent")
async def get_frequent_ncms(
    limit: int = Query(default=10, ge=1, le=50),
    days: int = Query(default=30, ge=1, le=365),
    user_plan: str = Depends(require_plan(["premium"]))
):
    """
    Obtener NCMs más frecuentes en el historial (solo Premium)

    Returns:
        List[Dict]: NCMs ordenados por frecuencia con contador
    """
    ds = get_datastore()

    # Calcular fecha límite
    fecha_desde = datetime.now() - timedelta(days=days)

    all_operations = ds.get_all_operations()

    # Filtrar por fecha
    filtered_ops = [
        op for op in all_operations
        if op.get("timestamp") and
        datetime.fromisoformat(op["timestamp"].replace("Z", "+00:00")) >= fecha_desde
    ]

    # Contar NCMs (primeros 4 dígitos)
    ncm_counter = {}
    for op in filtered_ops:
        for item in op.get("items", []):
            tariff = item.get("tariff_code", "")
            if tariff and len(tariff) >= 4:
                ncm_4 = tariff[:4]
                ncm_counter[ncm_4] = ncm_counter.get(ncm_4, 0) + 1

    # Ordenar por frecuencia descendente
    sorted_ncms = sorted(
        ncm_counter.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]

    result = [
        {"ncm": ncm, "count": count}
        for ncm, count in sorted_ncms
    ]

    return {
        "ncms": result,
        "total_unique": len(ncm_counter),
        "days": days
    }


@router.delete("/operations/{operation_id}")
async def delete_operation(
    operation_id: str,
    user_plan: str = Depends(require_plan(["premium"]))
):
    """
    Eliminar una operación del historial (solo Premium)

    Args:
        operation_id: ID de la operación a eliminar
    """
    ds = get_datastore()

    # Verificar que la operación existe
    operation = ds.get_operation_by_id(operation_id)
    if not operation:
        raise HTTPException(status_code=404, detail="Operación no encontrada")

    # Eliminar
    success = ds.delete_operation(operation_id)

    if not success:
        raise HTTPException(status_code=500, detail="Error al eliminar operación")

    return {
        "message": "Operación eliminada exitosamente",
        "operation_id": operation_id
    }
