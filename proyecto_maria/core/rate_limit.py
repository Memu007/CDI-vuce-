"""
Rate limiting configuration for CDI Sistema MARÍA.
Uses slowapi with RedisStorage for distributed rate limiting across instances.
"""
import os
import logging
from slowapi import Limiter
from slowapi.util import get_remote_address
from limits.storage import RedisStorage, MemoryStorage
from proyecto_maria.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

def _get_storage():
    """Returns the appropriate storage backend based on environment configuration."""
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            storage = RedisStorage(redis_url)
            logger.info("Using RedisStorage for rate limiting")
            return storage
        except Exception as e:
            logger.error(f"Failed to initialize RedisStorage, falling back to MemoryStorage: {e}")
    else:
        logger.info("REDIS_URL not configured, using MemoryStorage for rate limiting")
    
    return MemoryStorage()

def _saltos_de_proxy() -> int:
    """Cuántos proxies de confianza agregan una entrada a X-Forwarded-For
    (TRUSTED_PROXY_HOPS; 1 por defecto, el de Railway). Inválido o negativo
    cuenta como 1."""
    try:
        saltos = int(os.getenv("TRUSTED_PROXY_HOPS", "1"))
    except ValueError:
        return 1
    return saltos if saltos >= 0 else 1


def _entradas_xff(request) -> list:
    # Varios headers X-Forwarded-For valen lo mismo que uno solo unido por comas.
    unidos = ",".join(request.headers.getlist("x-forwarded-for"))
    return [p.strip() for p in unidos.split(",") if p.strip()]


def get_client_ip(request: "fastapi.Request") -> str:
    """IP del cliente para los límites: la que agregó el último proxy de
    confianza, contando desde el final de X-Forwarded-For. Las entradas de
    adelante las escribe quien manda el pedido y no se usan: con la primera,
    cada pedido podía inventarse una IP nueva (o la de otro)."""
    saltos = _saltos_de_proxy()
    partes = _entradas_xff(request) if saltos else []
    if partes:
        return partes[0] if len(partes) < saltos else partes[-saltos]
    return request.client.host if request.client else "127.0.0.1"


def log_429(request, motivo: str) -> None:
    """Deja en el log la IP tomada y cuántas entradas traía X-Forwarded-For,
    para ver si la cuenta de saltos coincide con la del proxy."""
    logger.warning("429 %s: ip=%s entradas_xff=%d ruta=%s", motivo, get_client_ip(request),
                   len(_entradas_xff(request)), request.url.path)


# Initialize the global limiter
limiter = Limiter(
    key_func=get_client_ip,
    storage_uri=_get_storage().storage_url if isinstance(_get_storage(), RedisStorage) else "memory://",
    # Fallback to defaults; actual limits applied per route
)

def get_dynamic_rate_limit():
    """
    Returns a rate limit string (e.g., '10/minute') dynamically.
    For more complex logic, this function could inspect the Request to
    determine 'basic' vs 'premium' rate limits from the config.
    """
    # Simply using the basic limit as the default dynamic string
    return settings.rate_limit_basic
