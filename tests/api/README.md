# API Tests - Quick Start Guide

## Overview

Comprehensive test suite for all 100+ API endpoints in the CDI project.

## Files

- **test_endpoints.py** - Main test file with 103 tests
- **TEST_SUMMARY.md** - Detailed test results and analysis
- **ENDPOINTS_INVENTORY.md** - Complete endpoint inventory

## Quick Start

### Run All Tests
```bash
pytest tests/api/test_endpoints.py -v
```

### Run Specific Test Class
```bash
# Run only calculator tests
pytest tests/api/test_endpoints.py::TestCalculatorEndpoints -v

# Run only health tests
pytest tests/api/test_endpoints.py::TestHealthEndpoints -v

# Run only client tests
pytest tests/api/test_endpoints.py::TestClientEndpoints -v
```

### Run Tests by Keyword
```bash
# Run all tests with "health" in name
pytest tests/api/test_endpoints.py -k "health" -v

# Run all tests with "calculator" in name
pytest tests/api/test_endpoints.py -k "calculator" -v

# Exclude auth-required tests
pytest tests/api/test_endpoints.py -k "not (history or template)" -v
```

### Run Tests with Markers
```bash
# Run only API tests
pytest tests/api/test_endpoints.py -m api -v
```

### Show Only Passing Tests
```bash
pytest tests/api/test_endpoints.py -v --tb=no -q
```

### Show Only Failing Tests
```bash
pytest tests/api/test_endpoints.py -v --lf
```

### Generate HTML Report
```bash
pytest tests/api/test_endpoints.py --html=report.html --self-contained-html
```

### Run with Coverage
```bash
pytest tests/api/test_endpoints.py --cov=proyecto_maria --cov-report=html
```

## Test Organization

### By Router/Feature
- **Health & Status** (3 tests)
- **Calculator** (10 tests) - Import cost calculations
- **History** (5 tests) - Operation history (Premium)
- **Items** (9 tests) - Item CRUD operations
- **Validation** (4 tests) - Pre-submission validation
- **Templates** (8 tests) - Operation templates (Premium)
- **Client** (14 tests) - Client management
- **PDF** (3 tests) - PDF extraction and processing
- **Admin** (8 tests) - Monitoring and metrics
- **NCM** (11 tests) - NCM information and notes
- **External APIs** (7 tests) - VUCE, Tarifar, AFIP
- **Cache** (3 tests) - Redis cache management
- **Logging** (2 tests) - Log management
- **Monitoring** (3 tests) - System monitoring
- **Gemini** (3 tests) - Gemini AI metrics
- **Backup** (3 tests) - Backup/restore operations
- **Analytics** (2 tests) - Usage tracking
- **Database** (2 tests) - Database management

## Test Results

### Current Status
- ✅ **89 tests passing** (86%)
- ⚠️ **14 tests failing** (14%)
  - 9 require authentication (expected)
  - 3 need payload fixes
  - 1 missing dependency (asyncpg)
  - 1 logic issue (NCM validation)

### Most Important Tests

#### Always Should Pass
```bash
pytest tests/api/test_endpoints.py::TestHealthEndpoints::test_health_endpoint_returns_200 -v
pytest tests/api/test_endpoints.py::TestCalculatorEndpoints::test_valor_plaza_calculation -v
pytest tests/api/test_endpoints.py::TestValidationEndpoints::test_validate_operation_success -v
```

#### Premium Features (Require Auth)
```bash
pytest tests/api/test_endpoints.py::TestHistoryEndpoints -v
pytest tests/api/test_endpoints.py::TestTemplatesEndpoints -v
```

## Common Issues

### Issue: 403 Forbidden
**Cause**: Endpoint requires authentication
**Solution**: This is expected behavior for Premium endpoints

### Issue: 422 Unprocessable Entity
**Cause**: Invalid payload structure
**Solution**: Check the endpoint's Pydantic model requirements

### Issue: ModuleNotFoundError: asyncpg
**Cause**: PostgreSQL driver not installed
**Solution**:
```bash
pip install asyncpg
# or mock the database calls in tests
```

## Examples

### Test a Single Endpoint
```python
# In test_endpoints.py
def test_calculator_valor_plaza(client):
    payload = {
        "ncm": "84713010",
        "origen": "CN",
        "fob_unitario": 500.0,
        "cantidad": 10.0
    }
    response = client.post("/api/calculator/valor-plaza", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### Run This Test
```bash
pytest tests/api/test_endpoints.py::TestCalculatorEndpoints::test_valor_plaza_calculation -v
```

## Continuous Integration

### Add to CI/CD Pipeline
```yaml
# .github/workflows/test.yml
- name: Run API Tests
  run: |
    pytest tests/api/test_endpoints.py -v --junitxml=junit/test-results.xml
```

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/api/test_endpoints.py -v --tb=short
```

## Development Workflow

### 1. Add New Endpoint
When you add a new endpoint:

1. Add the endpoint to the router
2. Add a test to `test_endpoints.py`
3. Run the test: `pytest tests/api/test_endpoints.py::YourTestClass::your_test -v`
4. Verify it passes

### 2. Fix Failing Test
When a test fails:

1. Run the specific test: `pytest tests/api/test_endpoints.py::TestClass::test_name -v`
2. Check the error message
3. Fix the code or test
4. Re-run to verify

### 3. Regression Testing
Before deploying:

```bash
# Run all tests
pytest tests/api/test_endpoints.py -v

# Check for regressions
pytest tests/api/test_endpoints.py --lf -v
```

## Debugging

### Verbose Output
```bash
pytest tests/api/test_endpoints.py -vv
```

### Show Prints
```bash
pytest tests/api/test_endpoints.py -v -s
```

### Stop on First Failure
```bash
pytest tests/api/test_endpoints.py -v -x
```

### Debug with PDB
```bash
pytest tests/api/test_endpoints.py -v --pdb
```

### Show Full Traceback
```bash
pytest tests/api/test_endpoints.py -v --tb=long
```

## Performance

### Fast Tests Only
```bash
# Run only fast tests (exclude slow external APIs)
pytest tests/api/test_endpoints.py -k "not external" -v
```

### Parallel Execution
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest tests/api/test_endpoints.py -v -n auto
```

## Documentation

For detailed information:
- **TEST_SUMMARY.md** - Test results and analysis
- **ENDPOINTS_INVENTORY.md** - Complete endpoint list

## Support

Issues? Check:
1. Is the server running?
2. Are dependencies installed?
3. Is the test database initialized?
4. Are environment variables set?

---

**Last Updated**: 2025-10-30
**Total Tests**: 103
**Success Rate**: 86%
**Endpoints Covered**: 100+
