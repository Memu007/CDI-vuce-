import logging
import os
import uuid
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


def _token_de_la_request(request: Request) -> str | None:
    """El JWT de la sesión: la cookie del frontend web o, si no hay, el header
    Bearer de las integraciones. Sin el prefijo «Bearer »."""
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]
    return token or None


def revocar_sesiones(user: User) -> None:
    """Revoca todas las sesiones del usuario.

    El mecanismo es `active_jti`: sólo entra el token con ese jti. Nunca se
    escribe NULL, porque NULL quiere decir «aceptar cualquier token» (usuarios
    de antes de la columna) y revocar resucitaría todas las sesiones viejas.
    Para revocarlas todas se guarda un jti nuevo que ningún token tiene.
    """
    user.active_jti = uuid.uuid4().hex


def firmar_token(datos: dict) -> str:
    """El único lugar que firma un token: con la misma clave que lo abre."""
    return jwt.encode(datos, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def datos_del_token(token: str) -> dict | None:
    """El contenido de un JWT nuestro con la firma y el vencimiento verificados,
    o None. Es el único lugar que abre un token; uno sin vencimiento no vale."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm],
                          options={"require": ["exp"]})
    except jwt.PyJWTError:
        return None


async def sesion_de_la_request(request: Request, db: AsyncSession) -> tuple[User, dict] | None:
    """El usuario y el contenido del token si es la sesión vigente, o None.
    Un token con `type` (el de verificar el email) no es una sesión."""
    token = _token_de_la_request(request)
    payload = datos_del_token(token) if token else None
    if payload is None or payload.get("type") is not None or not payload.get("sub"):
        return None
    user = (await db.execute(select(User).where(User.username == payload["sub"]))).scalars().first()
    if user is None:
        return None
    # NULL: usuario de antes de la columna, cualquier token suyo vale.
    if user.active_jti is not None and payload.get("jti") != user.active_jti:
        return None
    return user, payload


async def revocar_sesion_de_la_request(request: Request, db: AsyncSession) -> None:
    """Revoca el token con el que se llama sólo si es la sesión vigente: uno
    viejo o inválido no puede sacar a la que sí vale."""
    sesion = await sesion_de_la_request(request, db)
    if sesion is None:
        return
    revocar_sesiones(sesion[0])
    await db.commit()


async def get_current_user(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Obtiene el usuario actual centralizado.
    Soporta:
    - Test runner bypass
    - Cookie auth (frontend web)
    - Bearer Auth (integraciones API)
    """
    token = _token_de_la_request(request)

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

    sesion = await sesion_de_la_request(request, db)
    if sesion is None:
        raise HTTPException(status_code=401, detail="Sesión inválida o vencida")
    user = sesion[0]
    # CSRFMiddleware le emite el csrf_token a esta sesión si le falta.
    request.state.sesion_valida = True

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
