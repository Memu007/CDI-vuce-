import pytest
from fastapi.testclient import TestClient
import os
from dotenv import load_dotenv

# Load .env BEFORE importing app (needs DATABASE_URL)
load_dotenv()

# Override environment for testing
os.environ['ENVIRONMENT'] = 'testing'
os.environ['SENTRY_DSN'] = ''  # Disable Sentry in tests
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///:memory:' # Use in-memory DB for tests

from proyecto_maria.main import app  # noqa: E402
import asyncio

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture()
def client(monkeypatch):
    """
    TestClient configurado para la app.
    Overriding env vars to disable dependencies like limits and background syncs.
    """
    monkeypatch.setenv("DISABLE_DB_INIT", "true")
    monkeypatch.setenv("TESTING", "true")
    
    from proyecto_maria.core.rate_limit import limiter
    limiter.enabled = False
    
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test-token"}

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment between tests"""
    yield
    # Cleanup after test
    pass
