"""
Security Tests

Tests for security modules:
- File sanitization
- Path traversal prevention
- Input validation
- Log sanitization
"""

import pytest
from proyecto_maria.security.file_security import (
    sanitize_filename,
    validate_file_path,
    get_safe_temp_filename
)
from proyecto_maria.security.input_validation import (
    validate_string_length,
    validate_email,
    validate_cuit,
    validate_ncm,
    validate_password_strength
)
from proyecto_maria.security.log_sanitizer import (
    sanitize_dict,
    sanitize_string,
    sanitize_log_data
)
from pathlib import Path
from fastapi import HTTPException


class TestFileSecurity:
    """Test file security functions"""

    def test_sanitize_filename_removes_path_traversal(self):
        """Test that path traversal attempts are sanitized"""
        assert sanitize_filename("../../etc/passwd") == "passwd"
        assert sanitize_filename("../../../secret.txt") == "secret.txt"
        # Note: On Linux, backslashes are not path separators
        result = sanitize_filename("..\\..\\windows\\system32")
        assert result.startswith("_")  # Leading dots removed, backslashes replaced
        assert "windows" in result and "system32" in result

    def test_sanitize_filename_removes_command_injection(self):
        """Test that command injection attempts are sanitized"""
        assert sanitize_filename("test'; rm -rf /; echo '.pdf") == "__echo__.pdf"
        assert sanitize_filename("file.pdf && cat /etc/passwd") == "passwd"

    def test_sanitize_filename_allows_safe_characters(self):
        """Test that safe characters are preserved"""
        assert sanitize_filename("test_file-123.pdf") == "test_file-123.pdf"
        assert sanitize_filename("invoice.2024.xlsx") == "invoice.2024.xlsx"

    def test_sanitize_filename_removes_leading_dots(self):
        """Test that hidden files are prevented"""
        assert sanitize_filename(".hidden") == "hidden"
        assert sanitize_filename("...secret") == "secret"

    def test_validate_file_path_prevents_traversal(self, tmp_path):
        """Test that path traversal is prevented"""
        base_dir = str(tmp_path)

        # Valid path should work
        safe_path = validate_file_path(base_dir, "file.pdf")
        assert str(safe_path).startswith(base_dir)

        # Path traversal attempts are sanitized and kept within base_dir
        safe_path = validate_file_path(base_dir, "../../etc/passwd")
        assert str(safe_path).startswith(base_dir)
        # The filename should be sanitized to just "passwd"
        assert safe_path.name == "passwd"

    def test_get_safe_temp_filename(self):
        """Test safe temporary filename generation"""
        filename = get_safe_temp_filename("invoice.pdf")
        assert "upload_" in filename
        assert "invoice.pdf" in filename
        assert len(filename) > 20  # Has timestamp and random token


class TestInputValidation:
    """Test input validation functions"""

    def test_validate_string_length_accepts_valid(self):
        """Test that valid strings are accepted"""
        assert validate_string_length("test", "nombre") == "test"
        assert validate_string_length("a" * 199, "nombre") == "a" * 199

    def test_validate_string_length_rejects_too_long(self):
        """Test that too-long strings are rejected"""
        with pytest.raises(ValueError, match="too long"):
            validate_string_length("a" * 201, "nombre")

    def test_validate_email_accepts_valid(self):
        """Test that valid emails are accepted"""
        assert validate_email("user@example.com") == "user@example.com"
        assert validate_email("test.user+tag@domain.co.uk") == "test.user+tag@domain.co.uk"

    def test_validate_email_rejects_invalid(self):
        """Test that invalid emails are rejected"""
        with pytest.raises(ValueError, match="Invalid email"):
            validate_email("invalid")
        with pytest.raises(ValueError):
            validate_email("@example.com")
        with pytest.raises(ValueError):
            validate_email("user@")

    def test_validate_cuit_accepts_valid(self):
        """Test that valid CUIT is accepted"""
        assert validate_cuit("20-12345678-9") == "20-12345678-9"
        assert validate_cuit("20123456789") == "20-12345678-9"  # Formats automatically

    def test_validate_cuit_rejects_invalid(self):
        """Test that invalid CUIT is rejected"""
        with pytest.raises(ValueError, match="11 digits"):
            validate_cuit("123")
        with pytest.raises(ValueError):
            validate_cuit("invalid")

    def test_validate_ncm_accepts_valid(self):
        """Test that valid NCM is accepted"""
        assert validate_ncm("84713010") == "84713010"
        assert validate_ncm("847130") == "847130"

    def test_validate_ncm_rejects_invalid(self):
        """Test that invalid NCM is rejected"""
        with pytest.raises(ValueError, match="6 or 8 digits"):
            validate_ncm("123")
        with pytest.raises(ValueError):
            validate_ncm("invalid")

    def test_validate_password_strength_accepts_strong(self):
        """Test that strong passwords are accepted"""
        assert validate_password_strength("SecurePass123!@#") == "SecurePass123!@#"
        assert validate_password_strength("Abc123!@#Xyz") == "Abc123!@#Xyz"

    def test_validate_password_strength_rejects_weak(self):
        """Test that weak passwords are rejected"""
        # Too short
        with pytest.raises(ValueError, match="12 characters"):
            validate_password_strength("Short1!")

        # No uppercase
        with pytest.raises(ValueError, match="uppercase"):
            validate_password_strength("lowercase123!")

        # No lowercase
        with pytest.raises(ValueError, match="lowercase"):
            validate_password_strength("UPPERCASE123!")

        # No digit
        with pytest.raises(ValueError, match="number"):
            validate_password_strength("NoDigitsHere!")

        # No special char
        with pytest.raises(ValueError, match="special character"):
            validate_password_strength("NoSpecial123")

        # Note: Common password check only catches exact matches of very weak passwords
        # Those would fail other checks first (length, complexity), so not tested here


class TestLogSanitizer:
    """Test log sanitization functions"""

    def test_sanitize_dict_redacts_sensitive_fields(self):
        """Test that sensitive fields are redacted"""
        data = {
            "username": "admin",
            "password": "secret123",
            "token": "abc123xyz"
        }
        sanitized = sanitize_dict(data)

        assert sanitized["username"] == "admin"
        assert sanitized["password"] == "***REDACTED***"
        assert sanitized["token"] == "***REDACTED***"

    def test_sanitize_dict_handles_nested(self):
        """Test that nested dicts are sanitized"""
        data = {
            "user": {
                "username": "admin",
                "password": "secret"
            },
            "api_key": "xyz123"
        }
        sanitized = sanitize_dict(data)

        assert sanitized["user"]["username"] == "admin"
        assert sanitized["user"]["password"] == "***REDACTED***"
        assert sanitized["api_key"] == "***REDACTED***"

    def test_sanitize_string_redacts_email(self):
        """Test that emails are partially redacted"""
        text = "Contact us at user@example.com"
        sanitized = sanitize_string(text)

        assert "us***@example.com" in sanitized
        assert "user@example.com" not in sanitized

    def test_sanitize_string_redacts_jwt(self):
        """Test that JWT tokens are redacted"""
        text = "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        sanitized = sanitize_string(text)

        assert "***JWT_REDACTED***" in sanitized
        assert "eyJ" not in sanitized

    def test_sanitize_log_data_handles_mixed_types(self):
        """Test that mixed data types are handled"""
        data = {
            "users": [
                {"username": "admin", "password": "secret1"},
                {"username": "user", "password": "secret2"}
            ],
            "count": 2
        }
        sanitized = sanitize_log_data(data)

        assert sanitized["count"] == 2
        assert sanitized["users"][0]["password"] == "***REDACTED***"
        assert sanitized["users"][1]["password"] == "***REDACTED***"
