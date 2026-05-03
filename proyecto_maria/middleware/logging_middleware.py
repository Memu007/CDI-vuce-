"""
Logging middleware for FastAPI
"""

import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
from ..core.logging_config import log_api_request, get_logger

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests"""
    
    def __init__(self, app, logger_name: str = "api"):
        super().__init__(app)
        self.logger = get_logger(logger_name)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get client IP
        client_ip = request.client.host if request.client else None
        if "x-forwarded-for" in request.headers:
            client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
        
        # Process request
        try:
            response = await call_next(request)
            response_time_ms = (time.time() - start_time) * 1000
            
            # Log successful request
            log_api_request(
                self.logger,
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                response_time_ms=round(response_time_ms, 2),
                client_ip=client_ip
            )
            
            return response
            
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            
            # Log error
            log_api_request(
                self.logger,
                method=request.method,
                path=str(request.url.path),
                status_code=500,
                response_time_ms=round(response_time_ms, 2),
                client_ip=client_ip,
                error=str(e)
            )
            
            raise
