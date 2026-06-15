import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from proyecto_maria.config import get_settings

settings = get_settings()
_log = logging.getLogger("maria.auth")


def _current_environment() -> str:
    return getattr(settings, "environment", os.getenv("ENVIRONMENT", "production"))


def _is_testing_runtime() -> bool:
    """Solo permitimos el bypass de auth si estamos REALMENTE corriendo tests.

    Antes alcanzaba con `ENVIRONMENT=testing`; eso era veneno latente:
    si Railway recibia esa variable por error, cualquier request sin token
    pasaba como admin. Ahora exigimos ademas estar dentro de pytest
    (variable `PYTEST_CURRENT_TEST` que pytest setea solo durante el run).
    """
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


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes or settings.jwt_exp_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    """
    Decode and validate JWT token.

    Raises HTTPException with 401 if token is invalid, expired, or malformed.
    """
    try:
        # Decode with signature verification
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_signature": True, "verify_exp": True}
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token malformado"
        )
    except Exception as e:
        # Catch any other JWT-related errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error de autenticación"
        )


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> dict:
    if credentials is None:
        # Defensa en profundidad: si por error llegamos aca sin estar en
        # pytest real, devolvemos 401 en vez de un admin fake.
        if not _is_testing_runtime():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Autenticación requerida",
            )
        _log.warning("auth.jwt_utils: returning testing user (PYTEST runtime)")
        # Ola 4 MVP: solo existe Premium. El fallback de tests usa premium
        # para no romper validaciones de plan, con rol mínimo operador.
        return {
            "sub": "testing-user",
            "roles": ["operador"],
            "plan": "premium",
            "environment": _current_environment(),
        }
    return decode_token(credentials.credentials)

