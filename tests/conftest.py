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
from sqlalchemy.pool import NullPool  # noqa: E402
import proyecto_maria.database.connection as _conn  # noqa: E402
from proyecto_maria.database.connection import init_db  # noqa: E402

# Engine sin pool (NullPool): una conexión nueva por uso, cerrada al terminar.
#
# Antes se usaba StaticPool —una sola conexión compartida por todo el proceso—
# para evitar "database is locked". El problema: `TestClient`, usado sin
# `with`, abre un event loop NUEVO en cada request. Una conexión de aiosqlite
# queda atada al loop donde nació, así que al reusarla desde otro loop su
# cierre queda colgado (`CancelledError` al cerrar) y el proceso no termina
# nunca. Eso era el cuelgue de los tests de billing/trial.
#
# Con NullPool cada request abre y cierra su conexión dentro de su propio
# loop. El "database is locked" lo cubre `busy_timeout=30000` (abajo).
_test_engine = create_async_engine(
    os.environ['DATABASE_URL'],
    future=True,
    poolclass=NullPool,
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
import threading  # noqa: E402


def pytest_sessionstart(session):
    """Crear tablas antes de la sesión de tests (idempotente con checkfirst)."""
    asyncio.run(init_db())


def pytest_sessionfinish(session, exitstatus):
    """Cerrar el engine al terminar.

    `aiosqlite` atiende cada conexión con un hilo propio que NO es daemon. Con
    StaticPool esa conexión queda abierta toda la sesión, y si no se cierra el
    intérprete se queda esperando ese hilo para siempre: los tests terminan en
    verde pero el proceso nunca sale. Se veía al correr un archivo suelto.
    """
    try:
        asyncio.run(_test_engine.dispose())
    except Exception:
        # Si ya está cerrado o el loop murió, no hay nada que hacer acá: no
        # queremos convertir una limpieza en un fallo de la suite.
        pass

    # Apagar las conexiones de aiosqlite que quedaron huérfanas.
    #
    # `TestClient`, usado sin `with`, abre un event loop nuevo por request. Si
    # una conexión sigue abierta cuando ese loop muere, su cierre queda a
    # medias y el hilo que la atiende se queda esperando trabajo para siempre.
    # Como no es daemon, el intérprete no termina: los tests dan verde y el
    # proceso nunca sale. (Daemonizarlos no sirve: Python no deja cambiar eso
    # en un hilo ya arrancado.)
    #
    # El hilo sí corta solo si recibe el centinela de parada de aiosqlite, así
    # que se lo mandamos a mano. Es limpieza de test: en producción la app no
    # usa TestClient ni cambia de event loop.
    try:
        import gc
        import aiosqlite
        from aiosqlite.core import _STOP_RUNNING_SENTINEL

        huerfanas = [
            o for o in gc.get_objects()
            if isinstance(o, aiosqlite.Connection)
            and getattr(o, "_thread", None) is not None
            and o._thread.is_alive()
        ]
        for conexion in huerfanas:
            try:
                conexion._tx.put_nowait((None, lambda: _STOP_RUNNING_SENTINEL))
            except Exception:
                pass
        for conexion in huerfanas:
            conexion._thread.join(timeout=2)
    except Exception:
        pass


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

@pytest.fixture(autouse=True)
def _apagar_bypass_en_tests_de_auth(request, monkeypatch):
    """Los tests que prueban "sin sesión → 401" corren sin el atajo de pytest.

    La app, bajo pytest, autentica sola cuando no hay token (ver
    `auth/dependencies.py`). Cómodo para el resto de la suite, pero convierte
    en imposible cualquier test de "esto exige login": el pedido entra igual.

    Hasta 2026-07-26 había **23 tests así** que nunca podían pasar, y no se
    notaba porque los archivos que los contenían se colgaban antes de llegar.
    Toda la cobertura de "este endpoint pide autenticación" era humo.

    En vez de tocar los 23 a mano, se apaga el atajo automáticamente en
    cualquier test cuyo nombre hable de falta de sesión. Los que se escriban
    de acá en adelante quedan cubiertos solos.
    """
    nombre = request.node.name.lower()
    if any(p in nombre for p in ("sin_auth", "sin_token", "sin_sesion",
                                 "requires_auth", "requiere_auth", "_401")):
        import proyecto_maria.auth.dependencies as deps
        monkeypatch.setattr(deps, "_is_testing_runtime", lambda: False)


@pytest.fixture
def sin_bypass_de_test(monkeypatch):
    """Apaga el atajo de autenticación que la app usa cuando corre bajo pytest.

    `get_current_user` devuelve un usuario falso si no hay token y estamos en
    pytest (ver `auth/dependencies.py`). Eso es cómodo para el resto de los
    tests, pero hace **imposible** probar que un pedido sin sesión se rechaza:
    siempre entra. Con esta fixture el endpoint pasa por el camino real y
    devuelve 401.

    El atajo exige `ENVIRONMENT=testing` **y** `PYTEST_CURRENT_TEST`, así que
    en producción no existe (verificado atacando la imagen: sin login todo
    responde 401).
    """
    import proyecto_maria.auth.dependencies as deps
    monkeypatch.setattr(deps, "_is_testing_runtime", lambda: False)


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
