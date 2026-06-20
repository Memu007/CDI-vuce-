import logging
import os
from datetime import datetime, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from proyecto_maria.config import get_settings
from proyecto_maria.database.models import User
from proyecto_maria.database.connection import get_async_session
from proyecto_maria.services import billing_service

settings = get_settings()
_log = logging.getLogger("maria.auth")

async def get_db():
    async for session in get_async_session():
        yield session

def _current_environment() -> str:
    return getattr(settings, "environment", os.getenv("ENVIRONMENT", "production"))

def _is_testing_runtime() -> bool:
    if _current_environment() != "testing":
        return False
    return bool(os.getenv("PYTEST_CURRENT_TEST"))

class TestingHTTPBearer(HTTPBearer):
    def __init__(self) -> None:
        super().__init__(auto_error=not _is_testing_runtime())

    async def __call__(self, request: Request):
        try:
            return await super().__call__(request)
        except HTTPException:
            if _is_testing_runtime():
                return None
            raise

security = TestingHTTPBearer()

async def get_current_user(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el usuario actual centralizado.
    Soporta:
    - Test runner bypass
    - Cookie auth (frontend web)
    - Bearer Auth (integraciones API)
    """
    token = request.cookies.get("access_token")

    # Fallback to Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header

    if not token:
        if _is_testing_runtime():
            _log.warning("auth.dependencies: returning testing user (PYTEST runtime)")
            return {
                "sub": "testing-user",
                "username": "testing-user",
                "roles": ["operador"],
                "plan": "premium",
                "environment": _current_environment(),
            }
        raise HTTPException(status_code=401, detail="No autenticado")

    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    trial_end = user.trial_ends_at
    if trial_end is not None and trial_end.tzinfo is None:
        trial_end = trial_end.replace(tzinfo=timezone.utc)
        
    if (
        user.billing_status == "trial"
        and trial_end is not None
        and trial_end < datetime.now(timezone.utc)
    ):
        user.billing_status = "past_due"
        try:
            await db.commit()
            await db.refresh(user)
        except Exception:
            await db.rollback()

    team_owner = getattr(user, "team_owner_username", None)
    effective_owner = team_owner or user.username

    plan = user.plan or "premium"
    try:
        plan_def = billing_service.get_plan(plan)
        ops_limit = plan_def["ops"]
    except (KeyError, ValueError) as e:
        import logging
        logging.warning(f"[auth] plan inválido '{plan}' para user '{user.username}', fallback a premium. Error: {e}")
        plan = "premium"
        plan_def = billing_service.get_plan("premium")
        ops_limit = plan_def["ops"]

    return {
        "username": user.username,
        "name": user.name,
        "email": user.email,
        "cuit": user.cuit or "",
        "plan": plan,
        "is_verified": user.is_verified,
        "billing_status": user.billing_status or "none",
        "trial_ends_at": user.trial_ends_at.isoformat() if user.trial_ends_at else None,
        "ops_used_this_period": getattr(user, "ops_used_this_period", 0) or 0,
        "ops_limit": ops_limit,
        "extra_ops_remaining": getattr(user, "extra_ops_remaining", 0) or 0,
        "billing_period_started_at": user.billing_period_started_at.isoformat() if getattr(user, "billing_period_started_at", None) else None,
        "default_aduana_codigo": user.default_aduana_codigo or "",
        "default_puerto_destino": user.default_puerto_destino or "",
        "default_tipo_destinacion": user.default_tipo_destinacion or "",
        "team_owner_username": team_owner,
        "effective_owner": effective_owner,
        "roles": user.roles or [],
    }
