import secrets
from datetime import datetime, timedelta, timezone
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from proyecto_maria.database.models import Operation, PublicQuote, OperationItem
from proyecto_maria.auth.dependencies import get_current_user, get_db
from proyecto_maria.core.rate_limit import limiter, get_client_ip
from proyecto_maria.core.tarifar_connector import CLIENT as TARIFAR_CLIENT
from proyecto_maria.core.dolar_service import get_dolar_snapshot

router = APIRouter(prefix="/api/quotes", tags=["quotes"])

@router.post("/share")
async def share_quote(
    request: Request,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user)
):
    operation_id = payload.get("operation_id")
    if not operation_id:
        raise HTTPException(status_code=400, detail="operation_id es requerido")

    # Read operation from DB
    result = await db.execute(
        select(Operation).where(
            Operation.id == operation_id,
            Operation.owner_username == user["username"]
        )
    )
    op = result.scalars().first()
    if not op:
        raise HTTPException(status_code=404, detail="Operación no encontrada")

    # Read items
    items_res = await db.execute(
        select(OperationItem).where(OperationItem.operation_id == operation_id)
    )
    items = items_res.scalars().all()

    # Get TC
    tc = await get_dolar_snapshot()
    tc_usd = tc.get("oficial", {}).get("venta", 1000.0)

    # Prepare items for tarifar_connector
    calc_items = [
        {
            "ncm": i.pieza,
            "valor_fob": i.valor_unitario * i.cantidad,
            "cantidad": i.cantidad,
            "peso_unitario": i.peso_unitario,
            "origen": i.origen
        }
        for i in items
    ]

    # Calculate aranceles (async wrapper and try/except)
    try:
        calculo = await asyncio.to_thread(
            TARIFAR_CLIENT.calcular_aranceles, calc_items, tc_usd
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="tarifar_unavailable",
            headers={"Retry-After": "300"}
        )

    # Attach calculo details to items
    # Build dictionary to match securely by NCM
    calc_by_ncm = {
        c_item["item"]["ncm"]: c_item["calculo"]
        for c_item in calculo.get("items", [])
        if "item" in c_item and "ncm" in c_item["item"] and "calculo" in c_item
    }

    items_snapshot = []
    for i in items:
        item_calc = calc_by_ncm.get(i.pieza, {})
        items_snapshot.append({
            "pieza": i.pieza,
            "descripcion": i.descripcion,
            "origen": i.origen,
            "cantidad": i.cantidad,
            "valor_unitario": i.valor_unitario,
            "peso_unitario": i.peso_unitario,
            "alicuotas": item_calc.get("alicuotas", {}),
            "costo_total": item_calc.get("costo_total", 0.0)
        })

    # Create snapshot data
    snapshot = {
        "operation": {
            "id": op.id,
            "op_code": op.op_code,
            "currency": op.currency,
            "total_value": op.total_value,
            "total_items": op.total_items,
            "total_weight": op.total_weight,
            "created_at": op.created_at.isoformat() if op.created_at else None,
            "extra": op.extra
        },
        "tipo_cambio": tc_usd,
        "costo_total_operacion": calculo.get("costo_total", 0.0),
        "items": items_snapshot,
        "branding": {
            "company_name": user.get("name") or user["username"]
        }
    }

    token = secrets.token_urlsafe(16)
    expires = datetime.now(timezone.utc) + timedelta(days=30)

    quote = PublicQuote(
        token_id=token,
        operation_id=op.id,
        snapshot_data=snapshot,
        expires_at=expires
    )
    db.add(quote)
    await db.commit()

    return {
        "success": True,
        "token": token,
        "expires_at": expires.isoformat(),
        "share_url": f"/quotes/{token}"
    }

@router.get("/public/{hash}")
@limiter.limit("10/minute", key_func=get_client_ip)
async def get_public_quote(request: Request, hash: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PublicQuote).where(PublicQuote.token_id == hash))
    quote = result.scalars().first()

    if not quote:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")

    if quote.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        # Lazy cleanup
        await db.delete(quote)
        await db.commit()
        raise HTTPException(status_code=410, detail="El presupuesto ha expirado")

    # Leer estado y canal en vivo de la operación
    live_estado = None
    live_canal = None
    if quote.operation_id:
        op_res = await db.execute(
            select(Operation).where(Operation.id == quote.operation_id)
        )
        op_live = op_res.scalars().first()
        if op_live:
            live_estado = op_live.estado
            live_canal = op_live.canal

    return {
        "success": True,
        "snapshot": quote.snapshot_data,
        "expires_at": quote.expires_at.isoformat(),
        "live_estado": live_estado,
        "live_canal": live_canal
    }
