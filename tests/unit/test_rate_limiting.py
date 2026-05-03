import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# Import the actual project limiter
from proyecto_maria.core.rate_limit import limiter

# Create an isolated mock app for testing the limiter
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/test-limit")
@limiter.limit("2/minute")
def mock_limit_endpoint(request: Request):
    return {"status": "ok"}

def test_limiter_blocks_requests():
    # Explicitly enable the limiter because conftest.py disables it globally
    limiter.enabled = True
    
    client = TestClient(app)
    
    status_codes = []
    
    # Hit the test endpoint 5 times. The limit is 2/minute.
    for _ in range(5):
        response = client.get("/test-limit")
        status_codes.append(response.status_code)
    
    # First 2 requests should succeed (200), subsequent ones should be blocked (429)
    assert status_codes[0] == 200
    assert status_codes[1] == 200
    assert status_codes[2] == 429
    assert status_codes[3] == 429
    
    assert 429 in status_codes, "Rate limit was not enforced"
