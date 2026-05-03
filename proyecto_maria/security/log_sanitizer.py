"""
Log Sanitization Module

Prevents:
- Information Exposure (CWE-209)
- Sensitive Data in Logs
"""

import re
from typing import Any, Dict, List

# Sensitive field names to redact
SENSITIVE_FIELDS = [
    'password', 'passwd', 'pwd',
    'token', 'jwt', 'access_token', 'refresh_token',
    'secret', 'api_key', 'apikey',
    'credit_card', 'cc', 'cvv',
    'ssn', 'social_security',
    'private_key', 'privatekey'
]

# Patterns to redact in strings
SENSITIVE_PATTERNS = [
    # Credit card numbers
    (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '****-****-****-****'),
    # Email addresses (partial redaction)
    (r'([a-zA-Z0-9._%+-]{2})[a-zA-Z0-9._%+-]+(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', r'\1***\2'),
    # JWT tokens
    (r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+', '***JWT_REDACTED***'),
    # API keys (common formats)
    (r'\b[A-Za-z0-9]{32,}\b', '***API_KEY_REDACTED***'),
]


def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize dictionary by redacting sensitive fields.

    Args:
        data: Dictionary to sanitize

    Returns:
        Sanitized dictionary with sensitive fields redacted

    Example:
        >>> sanitize_dict({"username": "admin", "password": "secret123"})
        {'username': 'admin', 'password': '***REDACTED***'}
    """
    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        # Check if key is sensitive
        if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
            sanitized[key] = '***REDACTED***'
        # Recursively sanitize nested dicts
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        # Recursively sanitize lists
        elif isinstance(value, list):
            sanitized[key] = [sanitize_dict(item) if isinstance(item, dict) else item for item in value]
        # Sanitize strings
        elif isinstance(value, str):
            sanitized[key] = sanitize_string(value)
        else:
            sanitized[key] = value

    return sanitized


def sanitize_string(text: str) -> str:
    """
    Sanitize string by redacting sensitive patterns.

    Args:
        text: String to sanitize

    Returns:
        Sanitized string

    Example:
        >>> sanitize_string("My email is user@example.com")
        'My email is us***@example.com'
    """
    if not isinstance(text, str):
        return text

    sanitized = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        sanitized = re.sub(pattern, replacement, sanitized)

    return sanitized


def sanitize_log_data(data: Any) -> Any:
    """
    Sanitize any data structure for logging.

    Args:
        data: Data to sanitize (dict, list, str, etc.)

    Returns:
        Sanitized data

    Example:
        >>> sanitize_log_data({"user": "admin", "token": "abc123"})
        {'user': 'admin', 'token': '***REDACTED***'}
    """
    if isinstance(data, dict):
        return sanitize_dict(data)
    elif isinstance(data, list):
        return [sanitize_log_data(item) for item in data]
    elif isinstance(data, str):
        return sanitize_string(data)
    else:
        return data


def get_safe_error_message(error: Exception, debug: bool = False) -> str:
    """
    Get safe error message for logging/display.

    Args:
        error: Exception object
        debug: If True, include full error details (for development)

    Returns:
        Safe error message

    Example:
        >>> get_safe_error_message(ValueError("Invalid password"))
        'An error occurred'
        >>> get_safe_error_message(ValueError("Invalid password"), debug=True)
        'ValueError: Invalid password'
    """
    if debug:
        # Development mode: show full error
        return f"{type(error).__name__}: {str(error)}"
    else:
        # Production mode: generic error
        # Never expose internal paths, stack traces, or sensitive info
        return "An error occurred processing your request"
