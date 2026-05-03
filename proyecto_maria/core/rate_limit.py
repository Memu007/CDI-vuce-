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

# Initialize the global limiter
limiter = Limiter(
    key_func=get_remote_address,
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
