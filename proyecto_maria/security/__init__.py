"""
Security utilities for CDI Sistema MARÍA

This module contains security functions to prevent common vulnerabilities:
- Path traversal prevention
- Filename sanitization
- Input validation
- File type validation
"""

__all__ = [
    'sanitize_filename',
    'validate_file_path',
    'validate_file_upload',
    'sanitize_log_data'
]
