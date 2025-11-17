from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text, Column, DateTime, func, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, OperationalError
import asyncio
import time
import uuid
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from core.config import settings
from core.utils.logging import structured_logger
from core.exceptions.api_exceptions import DatabaseException, APIException

Base = declarative_base()
CHAR_LENGTH = 255

class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """
    impl = CHAR

    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value

class BaseModel(Base):
    """Base model with UUID primary key and timestamps"""
    __abstract__ = True
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Database connection configuration
SQLALCHEMY_DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)

# Enhanced engine configuration with connection pooling and resilience
engine_db = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=settings.ENVIRONMENT == "local",  # Only echo in local development
    pool_pre_ping=True,  # Validate connections before use
    pool_recycle=3600,   # Recycle connections every hour
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Maximum overflow connections
    pool_timeout=30,     # Timeout for getting connection from pool
    connect_args={
        "check_same_thread": False if "sqlite" in SQLALCHEMY_DATABASE_URL else {}
    }
)

# Session factory for the database (Async)
AsyncSessionDB = sessionmaker(
    bind=engine_db,
    class_=AsyncSession,
    expire_on_commit=False
)


class DatabaseManager:
    """Enhanced database manager with connection resilience and monitoring."""
    
    def __init__(self):
        self.engine = engine_db
        self.session_factory = AsyncSessionDB
        self._connection_failures = 0
        self._last_health_check = 0
        self._health_check_interval = 60  # Check health every 60 seconds
        
    async def health_check(self) -> dict:
        """Perform database health check."""
        start_time = time.time()
        
        try:
            async with self.session_factory() as session:
                # Simple query to test connection
                result = await session.execute(text("SELECT 1"))
                result.fetchone()
                
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                structured_logger.info(
                    message="Database health check successful",
                    metadata={
                        "response_time_ms": response_time,
                        "connection_failures": self._connection_failures,
                    }
                )
                
                self._connection_failures = 0  # Reset failure count on success
                self._last_health_check = time.time()
                
                return {
                    "status": "healthy",
                    "response_time_ms": response_time,
                    "connection_failures": self._connection_failures,
                    "last_check": self._last_health_check,
                }
                
        except Exception as e:
            self._connection_failures += 1
            response_time = (time.time() - start_time) * 1000
            
            structured_logger.error(
                message="Database health check failed",
                metadata={
                    "response_time_ms": response_time,
                    "connection_failures": self._connection_failures,
                    "error_type": type(e).__name__,
                },
                exception=e,
            )
            
            return {
                "status": "unhealthy",
                "response_time_ms": response_time,
                "connection_failures": self._connection_failures,
                "error": str(e),
                "last_check": time.time(),
            }
    
    async def get_connection_pool_status(self) -> dict:
        """Get connection pool status information."""
        pool = self.engine.pool
        
        try:
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                # Note: 'invalid' method may not be available in all pool types
                "invalid": getattr(pool, 'invalid', lambda: 0)(),
            }
        except Exception as e:
            # Fallback for pool types that don't support all methods
            return {
                "pool_size": getattr(pool, 'size', lambda: 0)(),
                "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
                "overflow": getattr(pool, 'overflow', lambda: 0)(),
                "invalid": 0,
                "error": f"Pool status partially unavailable: {str(e)}",
            }
    
    @asynccontextmanager
    async def get_session_with_retry(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        backoff_factor: float = 2.0,
    ) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with retry logic and exponential backoff."""
        
        for attempt in range(max_retries + 1):
            try:
                async with self.session_factory() as session:
                    if attempt > 0:
                        structured_logger.info(
                            message=f"Database connection successful on attempt {attempt + 1}",
                            metadata={"attempt": attempt + 1, "max_retries": max_retries}
                        )
                    yield session
                    return
                    
            except (SQLAlchemyError, DisconnectionError, OperationalError) as e:
                self._connection_failures += 1
                
                if attempt == max_retries:
                    structured_logger.error(
                        message=f"Database connection failed after {max_retries + 1} attempts",
                        metadata={
                            "attempt": attempt + 1,
                            "max_retries": max_retries,
                            "total_failures": self._connection_failures,
                        },
                        exception=e,
                    )
                    raise DatabaseException(
                        message=f"Database connection failed after {max_retries + 1} attempts: {str(e)}",
                        metadata={
                            "attempts": max_retries + 1,
                            "error_type": type(e).__name__,
                        }
                    )
                
                # Calculate delay with exponential backoff
                delay = retry_delay * (backoff_factor ** attempt)
                
                structured_logger.warning(
                    message=f"Database connection failed on attempt {attempt + 1}, retrying in {delay}s",
                    metadata={
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "retry_delay": delay,
                        "error_type": type(e).__name__,
                    },
                    exception=e,
                )
                
                await asyncio.sleep(delay)


# Global database manager instance
db_manager = DatabaseManager()


# Enhanced dependency to get the async session with retry logic
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with enhanced error handling and retry logic."""
    
    try:
        async with db_manager.get_session_with_retry() as session:
            structured_logger.info(
                message="Database session created successfully",
            )
            yield session
            
    except DatabaseException:
        # Re-raise database exceptions (already logged)
        raise
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 401, 403, etc.) without wrapping
        raise
        
    except APIException:
        # Re-raise API exceptions without wrapping
        raise
        
    except (ValueError, ValidationError, RequestValidationError) as e:
        # Re-raise validation errors (including Pydantic validation errors)
        raise
        
    except SQLAlchemyError as e:
        # Handle database-specific errors
        structured_logger.error(
            message=f"Database error in session: {str(e)}",
            exception=e,
        )
        raise DatabaseException(
            message=f"Database error: {str(e)}",
        )
        
    except Exception as e:
        # Handle any other unexpected exceptions (but not HTTP/API exceptions)
        structured_logger.error(
            message=f"Unexpected error in database session: {str(e)}",
            exception=e,
        )
        raise DatabaseException(
            message=f"Database session error: {str(e)}",
        )


# Dependency for database health checks
async def get_db_health() -> dict:
    """Get database health status."""
    return await db_manager.health_check()


# Dependency for connection pool status
async def get_db_pool_status() -> dict:
    """Get database connection pool status."""
    return await db_manager.get_connection_pool_status()
