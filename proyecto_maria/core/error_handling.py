"""
Robust error handling and retry logic for MARIA project
"""

import asyncio
import time
import logging
from typing import Any, Callable, Optional, Dict, List, Type
from functools import wraps
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Types of errors for different handling strategies"""
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"
    VALIDATION = "validation"
    DATABASE = "database"
    CACHE = "cache"
    LLM = "llm"
    EXTERNAL_API = "external_api"

@dataclass
class RetryConfig:
    """Configuration for retry logic"""
    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_backoff: bool = True
    jitter: bool = True
    retry_on: List[Type[Exception]] = None
    
    def __post_init__(self):
        if self.retry_on is None:
            self.retry_on = [Exception]

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    expected_exception: Type[Exception] = Exception

class CircuitBreaker:
    """Circuit breaker implementation for external services"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.success_count = 0
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker"""
        return (
            self.state == CircuitBreakerState.OPEN and
            time.time() - self.last_failure_time >= self.config.recovery_timeout
        )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker {func.__name__} entering HALF_OPEN state")
            else:
                raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful call"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 3:  # Require 3 successes to close
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker reset to CLOSED state")
        else:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

def retry_async(config: RetryConfig):
    """Decorator for async functions with retry logic"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if this exception should be retried
                    should_retry = any(isinstance(e, exc_type) for exc_type in config.retry_on)
                    
                    if not should_retry or attempt == config.max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {attempt + 1} attempts: {e}")
                        raise
                    
                    # Calculate delay
                    delay = config.base_delay
                    if config.exponential_backoff:
                        delay = min(config.base_delay * (2 ** attempt), config.max_delay)
                    
                    if config.jitter:
                        import random
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    logger.warning(f"Function {func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
                    await asyncio.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator

def retry_sync(config: RetryConfig):
    """Decorator for sync functions with retry logic"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if this exception should be retried
                    should_retry = any(isinstance(e, exc_type) for exc_type in config.retry_on)
                    
                    if not should_retry or attempt == config.max_attempts - 1:
                        logger.error(f"Function {func.__name__} failed after {attempt + 1} attempts: {e}")
                        raise
                    
                    # Calculate delay
                    delay = config.base_delay
                    if config.exponential_backoff:
                        delay = min(config.base_delay * (2 ** attempt), config.max_delay)
                    
                    if config.jitter:
                        import random
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    logger.warning(f"Function {func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s")
                    time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator

class ErrorHandler:
    """Centralized error handling for different error types"""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, str] = {}
        self.error_tracker = None  # Lazy-loaded

    def _get_error_tracker(self):
        """Lazy-load error tracker to avoid circular imports"""
        if self.error_tracker is None:
            try:
                from proyecto_maria.core.error_notes_tracker import get_error_tracker
                self.error_tracker = get_error_tracker()
            except ImportError:
                logger.warning("ErrorNotesTracker not available, tracking disabled")
                self.error_tracker = False  # Mark as unavailable
        return self.error_tracker if self.error_tracker is not False else None

    def get_circuit_breaker(self, service_name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create circuit breaker for a service"""
        if service_name not in self.circuit_breakers:
            if config is None:
                config = CircuitBreakerConfig()
            self.circuit_breakers[service_name] = CircuitBreaker(config)
        return self.circuit_breakers[service_name]

    def handle_error(self, error: Exception, error_type: ErrorType, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle error and return structured response"""
        error_key = f"{error_type.value}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = str(error)

        # Log with context
        log_context = {
            'error_type': error_type.value,
            'error_class': type(error).__name__,
            'error_count': self.error_counts[error_key],
            **(context or {})
        }
        logger.error(f"Error handled: {error}", extra=log_context)

        # Track error for internal improvements (nuevo)
        tracker = self._get_error_tracker()
        if tracker and context:
            try:
                tracker.track_error(error, context)
            except Exception as track_error:
                logger.warning(f"Error tracking failed: {track_error}")
        
        # Return appropriate response based on error type
        if error_type == ErrorType.NETWORK:
            return {
                "success": False,
                "error_type": "network_error",
                "message": "Error de conectividad. Intenta nuevamente.",
                "retry_suggested": True
            }
        elif error_type == ErrorType.RATE_LIMIT:
            return {
                "success": False,
                "error_type": "rate_limit",
                "message": "Límite de requests excedido. Intenta en unos minutos.",
                "retry_suggested": True,
                "retry_after": 60
            }
        elif error_type == ErrorType.API_ERROR:
            return {
                "success": False,
                "error_type": "api_error",
                "message": "Error en servicio externo. Intenta nuevamente.",
                "retry_suggested": True
            }
        elif error_type == ErrorType.VALIDATION:
            return {
                "success": False,
                "error_type": "validation_error",
                "message": "Datos inválidos. Revisa la información enviada.",
                "retry_suggested": False
            }
        elif error_type == ErrorType.DATABASE:
            return {
                "success": False,
                "error_type": "database_error",
                "message": "Error de base de datos. Intenta nuevamente.",
                "retry_suggested": True
            }
        elif error_type == ErrorType.LLM:
            return {
                "success": False,
                "error_type": "llm_error",
                "message": "Error en procesamiento de IA. Intenta nuevamente.",
                "retry_suggested": True
            }
        else:
            return {
                "success": False,
                "error_type": "unknown_error",
                "message": "Error inesperado. Intenta nuevamente.",
                "retry_suggested": True
            }
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        return {
            "error_counts": dict(self.error_counts),
            "last_errors": dict(self.last_errors),
            "circuit_breaker_states": {
                name: breaker.state.value 
                for name, breaker in self.circuit_breakers.items()
            }
        }

# Global error handler instance
error_handler = ErrorHandler()

# Common retry configurations
NETWORK_RETRY = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    exponential_backoff=True,
    retry_on=[ConnectionError, TimeoutError]
)

API_RETRY = RetryConfig(
    max_attempts=5,
    base_delay=2.0,
    max_delay=30.0,
    exponential_backoff=True,
    retry_on=[Exception]  # Retry on any exception for APIs
)

LLM_RETRY = RetryConfig(
    max_attempts=2,
    base_delay=5.0,
    exponential_backoff=False,
    retry_on=[Exception]
)

DATABASE_RETRY = RetryConfig(
    max_attempts=3,
    base_delay=0.5,
    exponential_backoff=True,
    retry_on=[Exception]
)

# Circuit breaker configurations
GEMINI_CIRCUIT_BREAKER = CircuitBreakerConfig(
    failure_threshold=3,
    recovery_timeout=120.0
)

VUCE_CIRCUIT_BREAKER = CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout=300.0
)

AFIP_CIRCUIT_BREAKER = CircuitBreakerConfig(
    failure_threshold=3,
    recovery_timeout=180.0
)
