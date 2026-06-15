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
from sqlalchemy import event  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
import proyecto_maria.database.connection as _conn  # noqa: E402
from proyecto_maria.database.connection import init_db  # noqa: E402

# Reemplazar el engine por uno con StaticPool: una sola conexión compartida
# para todo el proceso de tests. Razón: SQLite con múltiples conexiones async
# escribiendo en paralelo (p.ej. bcrypt ~300ms + registros concurrentes)
# dispara "database is locked". StaticPool serializa el acceso y lo elimina.
_test_engine = create_async_engine(
    os.environ['DATABASE_URL'],
    future=True,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False, "timeout": 30},
)
_conn.engine = _test_engine
_conn.AsyncSessionLocal = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False,
)


@event.listens_for(_test_engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA busy_timeout=30000")  # 30s: esperar el lock, no fallar
    cursor.close()
import asyncio  # noqa: E402


def pytest_sessionstart(session):
    """Crear tablas antes de la sesión de tests (idempotente con checkfirst)."""
    asyncio.run(init_db())


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


@pytest.fixture
def auth_override():
    """Autentica los endpoints sobreescribiendo la dependencia get_current_user.

    Evita escribir en la DB (sin locks ni flakiness por orden de tests).
    Devuelve el dict de user falso por si el test quiere inspeccionarlo.
    Limpia el override al terminar.
    """
    from proyecto_maria.main import get_current_user
    from proyecto_maria.database.connection import AsyncSessionLocal
    from proyecto_maria.database.models import User as DBUser
    from sqlalchemy import select
    import asyncio

    fake_user = {
        "username": "test_user",
        "name": "Test User",
        "email": "test_user@test.cdi",
        "cuit": "",
        "plan": "premium",
        "is_verified": True,
        "billing_status": "active",
        "trial_ends_at": None,
        "default_aduana_codigo": "",
        "default_puerto_destino": "",
        "default_tipo_destinacion": "",
        "team_owner_username": None,
        "effective_owner": "test_user",
    }
    
    async def _ensure_test_user_exists():
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(DBUser).where(DBUser.username == "test_user"))
            u = res.scalars().first()
            if not u:
                u = DBUser(
                    username="test_user",
                    password="dummy_password_hash",
                    name="Test User",
                    email="test_user@test.cdi",
                    plan="premium",
                    billing_status="active",
                    is_verified=True,
                )
                session.add(u)
                await session.commit()
                
    asyncio.run(_ensure_test_user_exists())
    
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield fake_user
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment between tests"""
    yield
    # Cleanup after test
    pass
