import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import CHAR, Column, DateTime, TypeDecorator, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import DisconnectionError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()
CHAR_LENGTH = 255


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(36), storing as stringified UUID values with hyphens.
    """
    impl = CHAR

    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        # Always use PostgreSQL - convert UUID to string
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            # Always return UUID object for consistency
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


class BaseModel(Base):
    """Base model with UUID primary key and timestamps"""
    __abstract__ = True

    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# Database connection configuration - NOW INITIALIZED LATER
engine_db = None
AsyncSessionDB = None


class DatabaseManager:
    """Enhanced database manager with connection resilience and monitoring."""

    def __init__(self):
        self.engine = None
        self.session_factory = None
        self._connection_failures = 0
        self._last_health_check = 0
        self._health_check_interval = 60  # Check health every 60 seconds

    def initialize(self, database_uri: str, env_is_local: bool):
        """Initializes the database engine and session factory."""
        global engine_db, AsyncSessionDB
        if self.engine and self.session_factory:  # Prevent re-initialization
            return

        engine_db = create_async_engine(
            database_uri,
            echo=env_is_local,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30
        )

        AsyncSessionDB = sessionmaker(
            bind=engine_db,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self.set_engine_and_session_factory(engine_db, AsyncSessionDB)

    def set_engine_and_session_factory(self, engine, session_factory):
        self.engine = engine
        self.session_factory = session_factory

    @asynccontextmanager
    async def get_session_with_retry(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with retry logic and exponential backoff."""
        if not self.session_factory:
            raise Exception("Database session factory not initialized.")

        for attempt in range(max_retries + 1):
            try:
                async with self.session_factory() as session:
                    if attempt > 0:
                        logger.info(
                            f"Database connection successful on attempt {attempt + 1}"
                        )
                    yield session
                    return

            except (SQLAlchemyError, DisconnectionError, OperationalError) as e:
                self._connection_failures += 1

                if attempt == max_retries:
                    logger.error(
                        f"Database connection failed after {max_retries + 1} attempts: {e}"
                    )
                    raise Exception(
                        f"Database connection failed after {max_retries + 1} attempts: {str(e)}"
                    )

                # Calculate delay with exponential backoff
                delay = retry_delay * (backoff_factor ** attempt)

                logger.warning(
                    f"Database connection failed on attempt {attempt + 1}, retrying in {delay}s: {e}"
                )

                await asyncio.sleep(delay)


# Global database manager instance
db_manager = DatabaseManager()


def initialize_db(database_uri: str, env_is_local: bool):
    """Initializes the database manager with engine and session factory."""
    db_manager.initialize(database_uri, env_is_local)


# Enhanced dependency to get the async session with retry logic
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with enhanced error handling and retry logic."""
    # Ensure database is initialized before getting a session
    if not db_manager.session_factory:
        raise Exception("Database session factory not initialized.")

    try:
        async with db_manager.get_session_with_retry() as session:
            logger.info("Database session created successfully")
            yield session

    except Exception as e:
        logger.error(f"Unexpected error in database session: {str(e)}")
        raise