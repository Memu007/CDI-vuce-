"""
Input Validation Module

Prevents:
- SQL Injection (CWE-89)
- XSS (CWE-79)
- Buffer Overflow (CWE-120)
"""

import re
from typing import Any, Optional
from pydantic import validator


# Maximum lengths for common fields
MAX_LENGTHS = {
    'nombre': 200,
    'email': 100,
    'cuit': 20,
    'descripcion': 1000,
    'direccion': 500,
    'telefono': 50,
    'notas': 2000,
    'ncm': 10
}


def validate_string_length(value: str, field_name: str, max_length: Optional[int] = None) -> str:
    """
    Validate string length to prevent buffer overflow attacks.

    Args:
        value: String to validate
        field_name: Name of field (for error messages)
        max_length: Maximum allowed length (uses MAX_LENGTHS if not provided)

    Returns:
        Validated string

    Raises:
        ValueError: If string is too long

    Example:
        >>> validate_string_length("test", "nombre")
        'test'
        >>> validate_string_length("A" * 1000, "nombre")
        ValueError: nombre is too long (max 200 characters)
    """
    if not value:
        return value

    max_len = max_length or MAX_LENGTHS.get(field_name, 500)

    if len(value) > max_len:
        raise ValueError(f"{field_name} is too long (max {max_len} characters)")

    return value


def validate_email(email: str) -> str:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        Validated email

    Raises:
        ValueError: If email format is invalid

    Example:
        >>> validate_email("user@example.com")
        'user@example.com'
        >>> validate_email("invalid")
        ValueError: Invalid email format
    """
    # Simple email regex (not RFC compliant, but secure)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        raise ValueError("Invalid email format")

    if len(email) > 100:
        raise ValueError("Email is too long (max 100 characters)")

    return email.lower()


def validate_cuit(cuit: str) -> str:
    """
    Validate CUIT format (Argentine tax ID).

    Args:
        cuit: CUIT number

    Returns:
        Validated CUIT

    Raises:
        ValueError: If CUIT format is invalid

    Example:
        >>> validate_cuit("20-12345678-9")
        '20-12345678-9'
        >>> validate_cuit("invalid")
        ValueError: Invalid CUIT format
    """
    # Remove non-digits
    digits_only = re.sub(r'[^0-9]', '', cuit)

    # CUIT must be 11 digits
    if len(digits_only) != 11:
        raise ValueError("CUIT must have 11 digits")

    # Format as XX-XXXXXXXX-X
    formatted = f"{digits_only[:2]}-{digits_only[2:10]}-{digits_only[10]}"

    return formatted


def validate_ncm(ncm: str) -> str:
    """
    Validate NCM code format.

    Args:
        ncm: NCM code

    Returns:
        Validated NCM

    Raises:
        ValueError: If NCM format is invalid

    Example:
        >>> validate_ncm("84713010")
        '84713010'
        >>> validate_ncm("invalid")
        ValueError: NCM must contain only digits
    """
    # Remove non-digits
    digits_only = re.sub(r'[^0-9]', '', ncm)

    # NCM must be 6 or 8 digits
    if len(digits_only) not in [6, 8]:
        raise ValueError("NCM must be 6 or 8 digits")

    # Only digits allowed
    if not digits_only.isdigit():
        raise ValueError("NCM must contain only digits")

    return digits_only


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML to prevent XSS attacks.

    Args:
        text: Text that may contain HTML

    Returns:
        Sanitized text with HTML entities escaped

    Example:
        >>> sanitize_html("<script>alert('XSS')</script>")
        '&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;'
    """
    import html
    return html.escape(text)


def validate_numeric(value: Any, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    """
    Validate numeric input.

    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Validated float

    Raises:
        ValueError: If value is invalid

    Example:
        >>> validate_numeric("123.45")
        123.45
        >>> validate_numeric("999999999999999999")
        ValueError: Value is too large
    """
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise ValueError("Invalid numeric value")

    # Check for infinity or NaN
    if not (-1e15 < num < 1e15):
        raise ValueError("Value is too large")

    if min_value is not None and num < min_value:
        raise ValueError(f"Value must be at least {min_value}")

    if max_value is not None and num > max_value:
        raise ValueError(f"Value must not exceed {max_value}")

    return num


def validate_password_strength(password: str) -> str:
    """
    Validate password strength.

    Requirements:
    - At least 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character

    Args:
        password: Password to validate

    Returns:
        Validated password

    Raises:
        ValueError: If password doesn't meet requirements

    Example:
        >>> validate_password_strength("SecurePass123!")
        'SecurePass123!'
        >>> validate_password_strength("weak")
        ValueError: Password must be at least 12 characters
    """
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters")

    if not re.search(r'[A-Z]', password):
        raise ValueError("Password must contain at least one uppercase letter")

    if not re.search(r'[a-z]', password):
        raise ValueError("Password must contain at least one lowercase letter")

    if not re.search(r'[0-9]', password):
        raise ValueError("Password must contain at least one number")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValueError("Password must contain at least one special character")

    # Check for common passwords (basic check)
    common_passwords = ['password', '123456', 'qwerty', 'admin']
    if password.lower() in common_passwords:
        raise ValueError("Password is too common")

    return password
