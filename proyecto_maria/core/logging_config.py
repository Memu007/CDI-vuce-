"""
Structured logging configuration for MARIA project
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_obj[key] = value
        
        return json.dumps(log_obj, ensure_ascii=False)

class ContextFilter(logging.Filter):
    """Filter to add context information to log records"""
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}
    
    def filter(self, record):
        for key, value in self.context.items():
            setattr(record, key, value)
        return True

def setup_logging(
    level: str = "INFO",
    log_dir: str = "logs",
    enable_json: bool = True,
    enable_console: bool = True,
    enable_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """Setup structured logging for MARIA"""
    
    # Create logs directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        if enable_json:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File handler with rotation
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_path / "maria.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        if enable_json:
            file_handler.setFormatter(JSONFormatter())
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    # Error file handler (only ERROR and CRITICAL)
    if enable_file:
        error_handler = logging.handlers.RotatingFileHandler(
            log_path / "maria-errors.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        if enable_json:
            error_handler.setFormatter(JSONFormatter())
        else:
            error_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            error_handler.setFormatter(error_formatter)
        
        logger.addHandler(error_handler)
    
    # Add context filter
    context_filter = ContextFilter({
        'service': 'maria',
        'version': '1.0.0',
        'environment': os.getenv('ENVIRONMENT', 'development')
    })
    logger.addFilter(context_filter)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)

def log_api_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    response_time_ms: float,
    client_ip: str = None,
    user_id: str = None,
    error: str = None
):
    """Log API request with structured data"""
    extra = {
        'event_type': 'api_request',
        'method': method,
        'path': path,
        'status_code': status_code,
        'response_time_ms': response_time_ms,
        'client_ip': client_ip,
        'user_id': user_id
    }
    
    if error:
        extra['error'] = error
        logger.error(f"API {method} {path} - {status_code} - {response_time_ms}ms", extra=extra)
    else:
        logger.info(f"API {method} {path} - {status_code} - {response_time_ms}ms", extra=extra)

def log_llm_request(
    logger: logging.Logger,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    response_time_ms: float,
    success: bool = True,
    error: str = None
):
    """Log LLM request with structured data"""
    extra = {
        'event_type': 'llm_request',
        'model': model,
        'prompt_tokens': prompt_tokens,
        'completion_tokens': completion_tokens,
        'total_tokens': prompt_tokens + completion_tokens,
        'response_time_ms': response_time_ms,
        'success': success
    }
    
    if error:
        extra['error'] = error
        logger.error(f"LLM {model} - {prompt_tokens + completion_tokens} tokens - {response_time_ms}ms", extra=extra)
    else:
        logger.info(f"LLM {model} - {prompt_tokens + completion_tokens} tokens - {response_time_ms}ms", extra=extra)

def log_database_operation(
    logger: logging.Logger,
    operation: str,
    table: str,
    duration_ms: float,
    affected_rows: int = None,
    success: bool = True,
    error: str = None
):
    """Log database operation with structured data"""
    extra = {
        'event_type': 'database_operation',
        'operation': operation,
        'table': table,
        'duration_ms': duration_ms,
        'affected_rows': affected_rows,
        'success': success
    }
    
    if error:
        extra['error'] = error
        logger.error(f"DB {operation} {table} - {duration_ms}ms", extra=extra)
    else:
        logger.info(f"DB {operation} {table} - {duration_ms}ms", extra=extra)

def log_cache_operation(
    logger: logging.Logger,
    operation: str,
    key: str,
    hit: bool = None,
    ttl_seconds: int = None,
    success: bool = True,
    error: str = None
):
    """Log cache operation with structured data"""
    extra = {
        'event_type': 'cache_operation',
        'operation': operation,
        'key': key,
        'cache_hit': hit,
        'ttl_seconds': ttl_seconds,
        'success': success
    }
    
    if error:
        extra['error'] = error
        logger.error(f"Cache {operation} {key}", extra=extra)
    else:
        logger.debug(f"Cache {operation} {key}", extra=extra)

# Configuration based on environment variables
LOGGING_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'log_dir': os.getenv('LOG_DIR', 'logs'),
    'enable_json': os.getenv('LOG_JSON', 'true').lower() == 'true',
    'enable_console': os.getenv('LOG_CONSOLE', 'true').lower() == 'true',
    'enable_file': os.getenv('LOG_FILE', 'true').lower() == 'true',
    'max_bytes': int(os.getenv('LOG_MAX_BYTES', '10485760')),  # 10MB
    'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5'))
}
