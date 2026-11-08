"""
Configuración de conexión a la base de datos para el proyecto María.
Este módulo maneja la conexión a PostgreSQL usando SQLAlchemy con async.
"""

import os
from proyecto_maria.config import es_desarrollo
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import async_sessionmaker

# Configuración de logging
logger = logging.getLogger(__name__)

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fuera de desarrollo, NUNCA caer a SQLite: el disco del contenedor (Railway) es
    # efímero y se perdería la base de todos los estudios en cada deploy, con un
    # warning que nadie mira. Se corta ruidosamente y temprano.
    if not es_desarrollo():
        raise RuntimeError(
            "DATABASE_URL no está definida y ENVIRONMENT no es de desarrollo. La app no "
            "arranca sin base persistente: en Railway el disco es efímero y caer "
            "a SQLite perdería los datos en cada deploy. Definí DATABASE_URL "
            "(postgresql://...)."
        )
    # Fallback a SQLite sólo para desarrollo local.
    basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(basedir, 'maria_data.db')}"
    logger.warning(f"DATABASE_URL not set, using SQLite (dev): {DATABASE_URL}")

# Railway/Heroku dan postgresql:// pero SQLAlchemy async necesita postgresql+asyncpg://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Detectar si es SQLite (no soporta connection pooling)
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Echo de SQL: opt-in via env var. Antes era `not IS_PRODUCTION` y en dev
# imprimia ~15 lineas por request a stdout. Con uvicorn --reload + WatchFiles
# eso se traducia en lag percibido en flujos que encadenan varias requests
# (p.ej. alta de cliente, que toca list+metricas+operaciones).
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() in ("true", "1", "yes")

# Configurar engine según el tipo de DB
if IS_SQLITE:
    # SQLite: sin pooling (desarrollo local)
    engine = create_async_engine(
        DATABASE_URL,
        echo=SQL_ECHO,
        future=True,
    )
else:
    # PostgreSQL: con connection pooling para 2000+ usuarios
    engine = create_async_engine(
        DATABASE_URL,
        echo=SQL_ECHO,
        future=True,
        pool_size=20,
        max_overflow=30,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
    )

# Crear la fábrica de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base para los modelos declarativos
Base = declarative_base()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Obtiene una sesión asíncrona de la base de datos.
    
    Returns:
        AsyncGenerator[AsyncSession, None]: Sesión asíncrona de la base de datos
    """
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "async_sessionmaker no está disponible. "
            "Actualiza SQLAlchemy a la versión 1.4.24 o superior."
        )

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Error en la sesión de base de datos: {str(e)}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Inicializa la base de datos creando todas las tablas.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(sembrar_inicio_registro_mp)
    except IntegrityError:
        pass  # otro proceso que arrancaba a la vez ya la sembró


def sembrar_inicio_registro_mp(conn) -> None:
    """Anota desde cuándo se registra cada pago de Mercado Pago, una sola vez.

    Es el primer pago registrado, si ya había (COBRO-MP-1 estuvo desplegado
    sin esta tabla), o ahora. Los pagos aprobados antes los aplicó el código
    que sólo recordaba el último: el webhook no los vuelve a aplicar.
    """
    from sqlalchemy import func, select
    from proyecto_maria.database.models import InicioRegistroPagosMP, PagoMercadoPagoAplicado
    inicio = InicioRegistroPagosMP.__table__
    if conn.execute(select(inicio.c.id).where(inicio.c.id == 1)).first() is not None:
        return
    pagos = PagoMercadoPagoAplicado.__table__
    desde = conn.execute(select(func.min(pagos.c.aplicado_en))).scalar()
    conn.execute(inicio.insert().values(id=1, desde=desde or datetime.now(timezone.utc)))


async def test_connection() -> bool:
    """
    Prueba la conexión a la base de datos.
    
    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    try:
        async with get_async_session() as session:
            # Usar text() para la consulta SQL
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {str(e)}")
        return False


async def close_db() -> None:
    """
    Cierra todas las conexiones a la base de datos.
    """
    await engine.dispose()
