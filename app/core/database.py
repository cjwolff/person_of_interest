from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import logging
from app.core.config import get_settings
from ..models.base import Base

settings = get_settings()
logger = logging.getLogger(__name__)

# Create async engine with proper connection settings
engine = create_async_engine(
    settings.database_url,
    echo=settings.DB_ECHO_LOG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    connect_args={
        "statement_timeout": settings.DB_STATEMENT_TIMEOUT,
        "idle_in_transaction_session_timeout": settings.DB_IDLE_TIMEOUT
    }
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def init_db():
    """Initialize database tables with error handling"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

@asynccontextmanager
async def get_db():
    """Dependency for getting async database sessions with proper cleanup"""
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()

async def cleanup_db_connections():
    """Cleanup database connections on shutdown"""
    try:
        await engine.dispose()
        logger.info("Database connections cleaned up")
    except Exception as e:
        logger.error(f"Error cleaning up database connections: {e}")