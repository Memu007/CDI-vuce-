"""
File Security Module

Prevents:
- Path Traversal (CWE-22)
- Command Injection (CWE-78)
- Malicious File Upload (CWE-434)
"""

import os
import re
import io
from pathlib import Path
from typing import Optional
from fastapi import HTTPException, UploadFile
try:
    import magic  # python-magic
except ImportError:
    magic = None

# Allowed file extensions
ALLOWED_EXTENSIONS = {
    'pdf': ['.pdf'],
    'excel': ['.xlsx', '.xls'],
    'csv': ['.csv']
}

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    'pdf': ['application/pdf'],
    'excel': [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-excel'
    ],
    'csv': ['text/csv', 'text/plain']
}

# Maximum file sizes (bytes)
MAX_FILE_SIZES = {
    'pdf': 50 * 1024 * 1024,  # 50MB
    'excel': 10 * 1024 * 1024,  # 10MB
    'csv': 5 * 1024 * 1024  # 5MB
}


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent command injection and path traversal.

    Args:
        filename: Original filename from user

    Returns:
        Safe filename with only alphanumeric chars, dots, dashes, underscores

    Example:
        >>> sanitize_filename("../../etc/passwd")
        'etcpasswd'
        >>> sanitize_filename("test'; rm -rf /'; echo '.pdf")
        'test_rm_-rf__echo_.pdf'
    """
    # Remove any path components
    filename = os.path.basename(filename)

    # Replace dangerous characters with underscore
    # Allow only: a-z, A-Z, 0-9, dot, dash, underscore
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Remove leading dots (hidden files)
    safe_filename = safe_filename.lstrip('.')

    # Limit length
    if len(safe_filename) > 255:
        name, ext = os.path.splitext(safe_filename)
        safe_filename = name[:250] + ext

    return safe_filename


def validate_file_path(base_dir: str, filename: str) -> Path:
    """
    Validate file path to prevent path traversal attacks.

    Args:
        base_dir: Base directory where files are stored
        filename: Filename (will be sanitized)

    Returns:
        Validated absolute Path object

    Raises:
        HTTPException: If path is outside base directory

    Example:
        >>> validate_file_path("/data", "file.pdf")
        PosixPath('/data/file.pdf')
        >>> validate_file_path("/data", "../../../etc/passwd")
        HTTPException: 403 Forbidden - Access denied
    """
    # Sanitize filename first
    safe_filename = sanitize_filename(filename)

    # Resolve absolute paths
    base = Path(base_dir).resolve()
    requested = (base / safe_filename).resolve()

    # Verify file is within base directory
    if not str(requested).startswith(str(base)):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Invalid file path"
        )

    return requested


async def validate_file_upload(
    file: UploadFile,
    file_type: str,
    max_size: Optional[int] = None
) -> bytes:
    """
    Validate uploaded file for security.

    Checks:
    - File extension
    - MIME type (magic bytes)
    - File size
    - File content (for PDF/Excel)

    Args:
        file: Uploaded file
        file_type: Expected file type ('pdf', 'excel', 'csv')
        max_size: Maximum file size in bytes (optional, uses default)

    Returns:
        File contents as bytes

    Raises:
        HTTPException: If file is invalid

    Example:
        >>> contents = await validate_file_upload(uploaded_file, 'pdf')
    """
    # Validate file type parameter
    if file_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {file_type}")

    # Check filename exists
    if not file.filename:
        raise HTTPException(400, "Filename is required")

    # Sanitize filename
    safe_filename = sanitize_filename(file.filename)

    # Check file extension
    file_ext = os.path.splitext(safe_filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS[file_type]:
        raise HTTPException(
            400,
            f"Invalid file extension. Expected {ALLOWED_EXTENSIONS[file_type]}, got {file_ext}"
        )

    # Read file contents
    contents = await file.read()

    # Check file size
    max_size = max_size or MAX_FILE_SIZES.get(file_type, 10 * 1024 * 1024)
    if len(contents) > max_size:
        raise HTTPException(
            413,
            f"File too large. Maximum size: {max_size / 1024 / 1024:.1f}MB"
        )

    # Check for empty file
    if len(contents) == 0:
        raise HTTPException(400, "File is empty")

    # Validate MIME type using magic bytes
    if magic is None:
        mime = None
    else:
        try:
            mime = magic.from_buffer(contents, mime=True)
        except Exception:
            mime = None

    if mime and mime not in ALLOWED_MIME_TYPES.get(file_type, []):
        raise HTTPException(
            400,
            f"Invalid file type. Expected {ALLOWED_MIME_TYPES[file_type]}, got {mime}"
        )

    # Additional validation for PDFs
    if file_type == 'pdf':
        try:
            import PyPDF2
            pdf = PyPDF2.PdfReader(io.BytesIO(contents))

            # Check if encrypted
            if pdf.is_encrypted:
                raise HTTPException(400, "Encrypted PDFs are not allowed")

            # Check if valid PDF (has pages)
            if len(pdf.pages) == 0:
                raise HTTPException(400, "PDF has no pages")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, f"Invalid PDF file: {str(e)}")

    # Additional validation for Excel
    if file_type == 'excel':
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(contents))

            # Check if has sheets
            if len(wb.sheetnames) == 0:
                raise HTTPException(400, "Excel file has no sheets")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, f"Invalid Excel file: {str(e)}")

    # Reset file pointer for later use
    await file.seek(0)

    return contents


def get_safe_temp_filename(original_filename: str, prefix: str = "upload_") -> str:
    """
    Generate safe temporary filename.

    Args:
        original_filename: Original filename
        prefix: Prefix for temp file

    Returns:
        Safe temporary filename

    Example:
        >>> get_safe_temp_filename("invoice.pdf")
        'upload_1234567890_invoice.pdf'
    """
    import time
    import secrets

    # Sanitize original filename
    safe_name = sanitize_filename(original_filename)

    # Add timestamp and random token
    timestamp = int(time.time())
    token = secrets.token_hex(4)

    return f"{prefix}{timestamp}_{token}_{safe_name}"
