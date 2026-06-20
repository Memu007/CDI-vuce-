"""
Admin Router - Endpoints administrativos para monitoreo y debugging
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import psutil
import time
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text
from proyecto_maria.auth.dependencies import get_db
from proyecto_maria.auth.roles import require_role
from proyecto_maria.database.models import User, Operation

router = APIRouter(prefix='/api/admin', tags=['admin'])

# Track de inicio del servidor
_server_start_time = time.time()


@router.get('/health/detailed')
async def detailed_health_check() -> Dict[str, Any]:
    """
    Health check extendido con métricas del sistema.

    Returns:
        Dict con status, uptime, recursos, errores, etc.
    """
    try:
        from proyecto_maria.core.error_notes_tracker import get_error_tracker
        error_tracker = get_error_tracker()
        error_insights = error_tracker.get_error_insights()
    except Exception as e:
        error_insights = {'error': f'Error tracker not available: {str(e)}'}

    # Sistema
    uptime_seconds = int(time.time() - _server_start_time)
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return {
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'version': '1.0.0',
        'uptime': {
            'seconds': uptime_seconds,
            'human': _format_uptime(uptime_seconds)
        },
        'system': {
            'cpu_percent': cpu_percent,
            'memory': {
                'total_mb': memory.total // (1024 * 1024),
                'available_mb': memory.available // (1024 * 1024),
                'used_percent': memory.percent
            },
            'disk': {
                'total_gb': disk.total // (1024 * 1024 * 1024),
                'free_gb': disk.free // (1024 * 1024 * 1024),
                'used_percent': disk.percent
            }
        },
        'errors': {
            'total_tracked': error_insights.get('summary', {}).get('total_errors_tracked', 0),
            'last_24h': error_insights.get('summary', {}).get('errors_last_24h', 0),
            'critical': error_insights.get('summary', {}).get('critical_issues', 0),
            'high': error_insights.get('summary', {}).get('high_priority_issues', 0),
            'medium': error_insights.get('summary', {}).get('medium_priority_issues', 0),
            'low': error_insights.get('summary', {}).get('low_priority_issues', 0)
        }
    }


@router.get('/errors/insights')
async def get_error_insights() -> Dict[str, Any]:
    """
    Obtiene insights completos de errores trackeados.

    Returns:
        Dict con summary, top_errors, suggested_improvements
    """
    try:
        from proyecto_maria.core.error_notes_tracker import get_error_tracker
        error_tracker = get_error_tracker()
        return error_tracker.get_error_insights()
    except Exception as e:
        raise HTTPException(500, f'Error tracker not available: {str(e)}')


@router.get('/errors/top/{limit}')
async def get_top_errors(limit: int = 10) -> Dict[str, Any]:
    """
    Obtiene los top N errores más frecuentes.

    Args:
        limit: Número de errores a retornar (default: 10)

    Returns:
        Lista de top errores
    """
    try:
        from proyecto_maria.core.error_notes_tracker import get_error_tracker
        error_tracker = get_error_tracker()
        insights = error_tracker.get_error_insights()

        return {
            'top_errors': insights.get('top_errors', [])[:limit],
            'count': min(limit, len(insights.get('top_errors', [])))
        }
    except Exception as e:
        raise HTTPException(500, f'Error tracker not available: {str(e)}')


@router.post('/errors/clear-old')
async def clear_old_errors(days: int = 30) -> Dict[str, Any]:
    """
    Limpia errores más viejos que N días.

    Args:
        days: Días de retención (default: 30)

    Returns:
        Número de errores eliminados
    """
    try:
        from proyecto_maria.core.error_notes_tracker import get_error_tracker
        error_tracker = get_error_tracker()
        removed = error_tracker.clear_old_notes(days=days)

        return {
            'success': True,
            'removed_count': removed,
            'retention_days': days
        }
    except Exception as e:
        raise HTTPException(500, f'Error tracker not available: {str(e)}')


@router.get('/metrics/prometheus')
async def prometheus_metrics():
    """
    Endpoint de métricas en formato Prometheus.

    Compatible con Prometheus scraping y Grafana.
    """
    try:
        from proyecto_maria.core.error_notes_tracker import get_error_tracker
        error_tracker = get_error_tracker()
        insights = error_tracker.get_error_insights()
    except Exception:
        insights = {'summary': {}}

    # Sistema
    uptime_seconds = int(time.time() - _server_start_time)
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    # Errores
    total_errors = insights.get('summary', {}).get('total_errors_tracked', 0)
    errors_24h = insights.get('summary', {}).get('errors_last_24h', 0)
    critical_errors = insights.get('summary', {}).get('critical_issues', 0)

    # Formato Prometheus
    metrics = f"""# HELP cdi_uptime_seconds Server uptime in seconds
# TYPE cdi_uptime_seconds gauge
cdi_uptime_seconds {uptime_seconds}

# HELP cdi_cpu_percent CPU usage percentage
# TYPE cdi_cpu_percent gauge
cdi_cpu_percent {cpu_percent}

# HELP cdi_memory_used_percent Memory usage percentage
# TYPE cdi_memory_used_percent gauge
cdi_memory_used_percent {memory.percent}

# HELP cdi_disk_used_percent Disk usage percentage
# TYPE cdi_disk_used_percent gauge
cdi_disk_used_percent {disk.percent}

# HELP cdi_errors_total Total errors tracked
# TYPE cdi_errors_total counter
cdi_errors_total {total_errors}

# HELP cdi_errors_last_24h Errors in last 24 hours
# TYPE cdi_errors_last_24h gauge
cdi_errors_last_24h {errors_24h}

# HELP cdi_errors_critical Critical errors count
# TYPE cdi_errors_critical gauge
cdi_errors_critical {critical_errors}
"""

    from fastapi.responses import Response
    return Response(content=metrics, media_type='text/plain')


@router.get('/logs/recent/{limit}')
async def get_recent_logs(limit: int = 100) -> Dict[str, Any]:
    """
    Obtiene logs recientes del archivo de log.

    Args:
        limit: Número de líneas a retornar (default: 100)

    Returns:
        Lista de logs recientes
    """
    try:
        import json
        from pathlib import Path

        log_file = Path('logs/maria.log')
        if not log_file.exists():
            return {'logs': [], 'message': 'Log file not found'}

        # Leer últimas N líneas
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        recent_lines = lines[-limit:]

        # Parsear JSON logs
        logs = []
        for line in recent_lines:
            try:
                log_obj = json.loads(line.strip())
                logs.append(log_obj)
            except json.JSONDecodeError:
                # Si no es JSON, agregar como texto plano
                logs.append({'message': line.strip()})

        return {
            'logs': logs,
            'count': len(logs),
            'total_lines': len(lines)
        }
    except Exception as e:
        raise HTTPException(500, f'Error reading logs: {str(e)}')


@router.get('/stats/summary')
async def get_stats_summary() -> Dict[str, Any]:
    """
    Resumen ejecutivo de estadísticas del sistema.

    Combina health, errors, y métricas en un solo endpoint.
    """
    try:
        from proyecto_maria.core.error_notes_tracker import get_error_tracker
        error_tracker = get_error_tracker()
        error_insights = error_tracker.get_error_insights()
    except Exception:
        error_insights = {'summary': {}, 'top_errors': []}

    uptime_seconds = int(time.time() - _server_start_time)
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()

    return {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'status': 'healthy' if error_insights.get('summary', {}).get('critical_issues', 0) == 0 else 'degraded',
        'uptime_hours': uptime_seconds // 3600,
        'resources': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'healthy': cpu_percent < 80 and memory.percent < 85
        },
        'errors': {
            'last_24h': error_insights.get('summary', {}).get('errors_last_24h', 0),
            'critical': error_insights.get('summary', {}).get('critical_issues', 0),
            'top_error': error_insights.get('top_errors', [{}])[0].get('error_type', 'None') if error_insights.get('top_errors') else 'None'
        },
        'recommendations': error_insights.get('suggested_improvements', [])[:3]
    }


def _format_uptime(seconds: int) -> str:
    """Formatea uptime en formato legible"""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if days > 0:
        parts.append(f'{days}d')
    if hours > 0:
        parts.append(f'{hours}h')
    if minutes > 0:
        parts.append(f'{minutes}m')
    if secs > 0 or not parts:
        parts.append(f'{secs}s')

    return ' '.join(parts)


@router.get('/test/sentry')
async def test_sentry_integration() -> Dict[str, Any]:
    """
    Endpoint de prueba para verificar que Sentry captura errores.

    IMPORTANTE: Solo usar en desarrollo/testing. Eliminar en producción.

    Returns:
        Error intencional para testing
    """
    try:
        from proyecto_maria.sentry_integration import capture_message, add_breadcrumb

        # Agregar breadcrumb
        add_breadcrumb(
            "Testing Sentry integration",
            category="test",
            level="info",
            data={"test_type": "manual"}
        )

        # Enviar mensaje de prueba
        capture_message(
            "Sentry integration test - This is a test message",
            level="info",
            context={
                "tags": {"test": "true", "endpoint": "/api/admin/test/sentry"},
                "extra": {"timestamp": datetime.utcnow().isoformat()}
            }
        )

        # Lanzar error de prueba
        raise Exception("🧪 Sentry test error - This is an intentional error to test Sentry integration")

    except Exception as e:
        # El error será capturado automáticamente por Sentry
        # debido a la integración FastAPI
        raise HTTPException(500, f"Test error captured by Sentry: {str(e)}")

@router.get('/cohort-retention')
async def get_cohort_retention(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(require_role('admin'))
) -> Dict[str, Any]:
    """
    Extrae datos de retención de cohortes para los usuarios activos o en trial.
    SOLO LECTURA. No expone PII sensible ni tokens.
    """
    # 1. Obtener los usuarios relevantes
    users_result = await db.execute(
        select(User).where(User.billing_status.in_(['active', 'trial']))
    )
    users = users_result.scalars().all()
    
    cohort_data = []
    
    for u in users:
        # 2. Obtener la última operación
        last_op_result = await db.execute(
            select(Operation.created_at)
            .where(Operation.owner_username == u.username)
            .order_by(desc(Operation.created_at))
            .limit(1)
        )
        last_op = last_op_result.scalar_one_or_none()
        
        # 3. Obtener el agrupamiento por mes de las operaciones
        # Usamos extract() para compatibilidad con PostgreSQL y SQLite
        from sqlalchemy import extract, String
        ops_by_month_result = await db.execute(
            select(
                (extract('year', Operation.created_at) * 100 +
                 extract('month', Operation.created_at)).cast(String).label('month'),
                func.count().label('count')
            )
            .where(Operation.owner_username == u.username)
            .group_by('month')
            .order_by('month')
        )
        
        ops_by_month = []
        for row in ops_by_month_result:
            month_raw = str(row.month).split('.')[0] # handle float return from extract sometimes
            if len(month_raw) == 6:
                formatted_month = f"{month_raw[:4]}-{month_raw[4:6]}"
            else:
                formatted_month = month_raw
            ops_by_month.append({"month": formatted_month, "count": row.count})
        
        cohort_data.append({
            "username": u.username,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "billing_status": u.billing_status,
            "ops_used_this_period": u.ops_used_this_period,
            "billing_period_started_at": u.billing_period_started_at.isoformat() if u.billing_period_started_at else None,
            "last_topup_at": u.last_topup_at.isoformat() if u.last_topup_at else None,
            "last_operation_at": last_op.isoformat() if last_op else None,
            "operations_by_month": ops_by_month
        })
        
    return {
        "success": True,
        "cohorts": cohort_data
    }
