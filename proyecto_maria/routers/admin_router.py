"""
Admin Router - Endpoints administrativos para monitoreo y debugging
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
import psutil
import time
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Dict, Any, List

from pydantic import BaseModel, Field, StrictInt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, text, or_
from proyecto_maria.auth.dependencies import get_current_user, get_db
from proyecto_maria.auth.roles import roles_de
from proyecto_maria.database.candados import cuenta_bloqueada
from proyecto_maria.database.models import CreditoAdmin, User, Operation, Organization
from proyecto_maria.services import billing_service

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
) -> Dict[str, Any]:
    """
    Extrae datos de retención de cohortes para los usuarios activos o en trial.
    El control de admin lo pone el router al montarse (require_admin).
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


# Lo que paga: la cuenta o, si es de un estudio, el estudio. Se leen sólo estas
# columnas, así ningún secreto llega a la ruta y no hay objeto que guardar.
_SALDO = ("plan", "billing_status", "trial_ends_at", "ops_used_this_period",
          "extra_ops_remaining", "extra_ops_expires_at", "last_topup_at")


def _iso(fecha):
    return fecha and billing_service.como_utc(fecha).isoformat()


def _cuenta_en_la_lista(fila) -> Dict[str, Any]:
    del_estudio = fila.org_id is not None
    saldo = {c: getattr(fila, ("org_" if del_estudio else "") + c) for c in _SALDO}
    vencidos = billing_service.extra_vencidos(saldo["extra_ops_expires_at"])
    return {
        "usuario": fila.username,
        "email": fila.email,
        "admin": "admin" in roles_de({"roles": fila.roles}),
        "estudio": fila.org_name,
        "saldo_del_estudio": del_estudio,
        "plan": saldo["plan"],
        "cobro": billing_service.cobro_efectivo(SimpleNamespace(**saldo)),
        "cobro_hasta": _iso(saldo["trial_ends_at"]),
        "operaciones_del_periodo": saldo["ops_used_this_period"] or 0,
        "creditos_extra": 0 if vencidos else saldo["extra_ops_remaining"] or 0,
        "creditos_vencen": None if vencidos else _iso(saldo["extra_ops_expires_at"]),
        "ultima_recarga": _iso(saldo["last_topup_at"]),
    }


@router.get('/usuarios')
async def listar_usuarios(
    buscar: str = Query("", max_length=100),
    desde: int = Query(0, ge=0, le=1_000_000),
    cuantos: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Las cuentas con su plan y sus créditos, por páginas. Sólo lee.
    El control de admin lo pone el router al montarse (require_admin)."""
    filtro = []
    if buscar.strip():
        # Las dos minúsculas en la base: Python y Postgres no bajan igual todas las letras.
        filtro.append(or_(User.username.icontains(buscar.strip(), autoescape=True),
                          User.email.icontains(buscar.strip(), autoescape=True)))
    total = (await db.execute(select(func.count()).select_from(User).where(*filtro))).scalar_one()
    filas = await db.execute(_consulta(*filtro).order_by(User.username).offset(desde).limit(cuantos))
    return {"total": total, "desde": desde, "cuantos": cuantos,
            "usuarios": [_cuenta_en_la_lista(f) for f in filas]}


def _consulta(*filtro):
    columnas = [User.username, User.email, User.roles, Organization.id.label("org_id"),
                Organization.name.label("org_name")]
    columnas += [getattr(User, c) for c in _SALDO] + [getattr(Organization, c).label("org_" + c) for c in _SALDO]
    return select(*columnas).outerjoin(Organization, Organization.id == User.organization_id).where(*filtro)


class _Carga(BaseModel):
    cantidad: StrictInt = Field(ge=1, le=billing_service.EXTRA_OPS_MAX)
    pedido: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


@router.post('/usuarios/{username}/creditos')
async def cargar_creditos(
    username: str,
    carga: _Carga,
    admin=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Suma créditos extra a la cuenta que paga, una sola vez por pedido.
    El pedido se busca antes que el tope: el reintento de una carga que llenó a 100 no choca."""
    bloqueada = await cuenta_bloqueada(db, username)
    if bloqueada is None:
        raise HTTPException(status_code=404, detail="No existe esa cuenta")
    db_user, cuenta = bloqueada
    previa = await db.get(CreditoAdmin, carga.pedido)
    ya = previa is not None
    if not ya:
        entra, vigentes = billing_service.acreditar_extra(cuenta, carga.cantidad, datetime.now(timezone.utc))
        if not entra:
            await db.rollback()
            tope = billing_service.EXTRA_OPS_MAX
            raise HTTPException(status_code=409, detail=(
                f"Ya tiene {vigentes} operaciones extra y el tope es {tope}: entran como mucho {tope - vigentes}."))
        previa = CreditoAdmin(pedido=carga.pedido, admin=admin["username"], usuario=username,
                              cuenta=f"org:{cuenta.id}" if cuenta is not db_user else username,
                              cantidad=carga.cantidad, vigentes_antes=vigentes)
        db.add(previa)
        try:
            await db.commit()
        except IntegrityError:
            # Otro pedido con la misma clave entró primero: se deshace lo sumado y se responde con el suyo.
            await db.rollback()
            previa, ya = await db.get(CreditoAdmin, carga.pedido), True
    if (previa.usuario, previa.cantidad) != (username, carga.cantidad):
        await db.rollback()
        raise HTTPException(status_code=409, detail="ese pedido ya se usó para otra carga")
    await db.commit()
    fila = (await db.execute(_consulta(User.username == username))).one()
    return {**_cuenta_en_la_lista(fila), "ya_aplicado": ya,
            "carga": {"pedido": previa.pedido, "cantidad": previa.cantidad,
                      "vigentes_antes": previa.vigentes_antes, "admin": previa.admin}}
