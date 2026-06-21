"""
Security Middleware

Implements:
- Enhanced security headers (CSP, HSTS, etc.)
- Request logging with sanitization
- Rate limiting per endpoint type
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
import time
import logging
from typing import Callable

logger = logging.getLogger("maria.security")


class EnhancedSecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add comprehensive security headers to all responses.

    Headers added:
    - Content-Security-Policy (CSP)
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Strict-Transport-Security (HSTS)
    - Referrer-Policy
    - Permissions-Policy
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Content Security Policy
        # Allows scripts/styles from self and trusted CDNs only
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline'",  # TODO fase 2: migrar inline scripts a .js externos y sacar unsafe-inline
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data:",
            "font-src 'self'",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers['Content-Security-Policy'] = '; '.join(csp_directives)

        # Prevent MIME-sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # Enable XSS filter in older browsers
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # HSTS - Force HTTPS en producción (OWASP A2)
        import os
        is_prod = os.getenv("ENVIRONMENT", "development") == "production"
        if is_prod or os.getenv("ENABLE_HSTS", "false").lower() == "true":
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions policy (formerly Feature-Policy)
        permissions = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()"
        ]
        response.headers['Permissions-Policy'] = ', '.join(permissions)

        # Remove server header to avoid fingerprinting
        if 'Server' in response.headers:
            del response.headers['Server']



        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all requests with sanitized data.

    Logs:
    - Method and path
    - Response status
    - Response time
    - Errors (sanitized)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'client_ip': request.client.host if request.client else 'unknown'
            }
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate response time
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Response: {response.status_code} in {duration:.3f}s",
                extra={
                    'status_code': response.status_code,
                    'duration_ms': int(duration * 1000),
                    'path': request.url.path
                }
            )

            # Warn on slow responses
            if duration > 3.0:
                logger.warning(
                    f"Slow response: {request.url.path} took {duration:.2f}s",
                    extra={
                        'path': request.url.path,
                        'duration': duration,
                        'threshold': 3.0
                    }
                )

            return response

        except Exception as e:
            # Calculate response time even for errors
            duration = time.time() - start_time

            # Log error (sanitized)
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    'method': request.method,
                    'path': request.url.path,
                    'duration_ms': int(duration * 1000),
                    'error_type': type(e).__name__
                },
                exc_info=False  # Don't include full traceback in logs
            )

            # Re-raise exception
            raise


class RateLimitByEndpointMiddleware(BaseHTTPMiddleware):
    """
    Apply different rate limits based on endpoint type.

    Tiers:
    - Light endpoints (health, static): 120/min
    - Medium endpoints (API queries): 60/min
    - Heavy endpoints (uploads, calculations): 10/min
    """

    # Endpoint categorization
    HEAVY_ENDPOINTS = [
        '/upload_pdf',
        '/upload_excel',
        '/process_operation',
        '/api/calculator/comparar-origenes'
    ]

    MEDIUM_ENDPOINTS = [
        '/api/calculator/',
        '/api/clientes/',
        '/api/validation/'
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        In-memory Rate Limiting implementation (Fixed Window).
        """
        from fastapi import HTTPException
        
        # Simple in-memory storage for demo purposes
        # In production this should be Redis
        if not hasattr(self, '_limits'):
            self._limits = {}
            self._last_cleanup = time.time()

        # Cleanup old entries every minute
        now = time.time()
        if now - self._last_cleanup > 60:
            self._limits = {}  # Brutal reset is fine for simple validation
            self._last_cleanup = now
            
        client_ip = request.client.host if request.client else 'unknown'
        path = request.url.path
        
        # No bypass for any IP in production (OWASP A5)
        import os
        if os.getenv("ENVIRONMENT", "development") != "production" and client_ip in ["127.0.0.1", "localhost"]:
            return await call_next(request)

        # Determine limits
        limit = 120  # Default light
        if any(path.startswith(heavy) for heavy in self.HEAVY_ENDPOINTS):
            limit = 10
        elif any(path.startswith(medium) for medium in self.MEDIUM_ENDPOINTS):
            limit = 60
            
        # Key: "ip:minute_timestamp"
        current_minute = int(now / 60)
        key = f"{client_ip}:{current_minute}"
        
        current_count = self._limits.get(key, 0)
        
        if current_count >= limit:
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            return Response(
                content="Rate limit exceeded", 
                status_code=429,
                media_type="text/plain"
            )
            
        self._limits[key] = current_count + 1
        
        response = await call_next(request)
        return response
