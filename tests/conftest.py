import pytest
import tempfile
from fastapi.testclient import TestClient
import os
from dotenv import load_dotenv

# Load .env BEFORE importing app (needs DATABASE_URL)
load_dotenv()

# Override environment for testing
os.environ['ENVIRONMENT'] = 'testing'
os.environ['SENTRY_DSN'] = ''  # Disable Sentry in tests
# DB en archivo temporal (no in-memory): SQLite in-memory crea una DB nueva
# por cada conexión async, lo que rompe tests que abren más de una sesión.
# Archivo en /tmp se borra al final del proceso de tests (lo limpia OS).
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix='.db', prefix='cdi_pytest_')
os.close(_test_db_fd)
os.environ['DATABASE_URL'] = f'sqlite+aiosqlite:///{_test_db_path}'

from proyecto_maria.main import app  # noqa: E402
from proyecto_maria.database.connection import engine as _test_engine  # noqa: E402
from sqlalchemy import event  # noqa: E402

# Configurar SQLite para que tolere accesos concurrentes durante los tests.
# Sin esto, operaciones bloqueantes como bcrypt (~300ms) provocan
# "database is locked" cuando otra request quiere escribir en paralelo.
# Usamos busy_timeout (espera en vez de fallar) en lugar de WAL: cambiar a
# WAL requiere lock exclusivo y falla si otra suite dejó conexiones abiertas.
@event.listens_for(_test_engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA busy_timeout=30000")  # 30s: esperar el lock, no fallar
    cursor.close()
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
