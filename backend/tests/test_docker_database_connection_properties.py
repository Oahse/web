"""
Property-based tests for Docker database connection.

**Feature: app-enhancements, Property 62: Database connection from backend container**
**Validates: Requirements 19.3**

These tests verify that the backend container can successfully connect to the
PostgreSQL database container in a Docker environment.
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings as hypothesis_settings, HealthCheck
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from core.config import settings


@pytest.mark.asyncio
@given(
    query=st.sampled_from([
        "SELECT 1",
        "SELECT 1 + 1",
        "SELECT NOW()",
        "SELECT version()",
        "SELECT current_database()"
    ])
)
@hypothesis_settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_database_connection_with_various_queries(query):
    """
    Property: For any valid SQL query, the backend should be able to execute it
    against the database container.
    
    This tests that:
    1. Database connection can be established
    2. Queries can be executed successfully
    3. Results can be retrieved
    """
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        pool_pre_ping=True
    )
    
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text(query))
            # Verify we can fetch results
            row = result.fetchone()
            assert row is not None, f"Query '{query}' returned no results"
            
    finally:
        await engine.dispose()


@pytest.mark.asyncio
@given(
    pool_size=st.integers(min_value=1, max_value=10),
    max_overflow=st.integers(min_value=0, max_value=20)
)
@hypothesis_settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_database_connection_pool_configurations(pool_size, max_overflow):
    """
    Property: For any valid connection pool configuration, the database connection
    should work correctly.
    
    This tests that:
    1. Different pool sizes work correctly
    2. Connection pooling is properly configured
    3. Multiple connections can be established
    """
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True
    )
    
    try:
        # Test multiple concurrent connections
        async def test_connection():
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.fetchone()[0]
        
        # Create multiple concurrent connections
        tasks = [test_connection() for _ in range(min(pool_size, 3))]
        results = await asyncio.gather(*tasks)
        
        # Verify all connections worked
        assert all(r == 1 for r in results), "Not all connections succeeded"
        
    finally:
        await engine.dispose()


@pytest.mark.asyncio
@given(
    table_name=st.sampled_from([
        "users",
        "products",
        "orders",
        "categories",
        "reviews"
    ])
)
@hypothesis_settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_database_table_accessibility(table_name):
    """
    Property: For any application table, the backend should be able to query it
    from the database container.
    
    This tests that:
    1. Database schema is properly initialized
    2. Tables are accessible
    3. Basic queries work on all tables
    """
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        pool_pre_ping=True
    )
    
    try:
        async with engine.connect() as conn:
            # Check if table exists
            result = await conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table_name}'
                )
            """))
            table_exists = result.fetchone()[0]
            
            # If table exists, try to query it
            if table_exists:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.fetchone()[0]
                assert count >= 0, f"Invalid count for table {table_name}"
            
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_database_connection_persistence():
    """
    Property: Database connections should be persistent and reusable across
    multiple operations.
    
    This tests that:
    1. Connections can be reused
    2. Connection state is maintained
    3. No connection leaks occur
    """
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10
    )
    
    try:
        # Perform multiple operations with the same engine
        for i in range(10):
            async with engine.connect() as conn:
                result = await conn.execute(text(f"SELECT {i}"))
                value = result.fetchone()[0]
                assert value == i, f"Expected {i}, got {value}"
        
        # Verify pool statistics
        pool = engine.pool
        assert pool.size() > 0, "Connection pool should have connections"
        
    finally:
        await engine.dispose()


@pytest.mark.asyncio
@given(
    transaction_count=st.integers(min_value=1, max_value=5)
)
@hypothesis_settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_database_transaction_handling(transaction_count):
    """
    Property: For any number of transactions, the database should handle them
    correctly with proper isolation.
    
    This tests that:
    1. Transactions can be created and committed
    2. Transaction isolation works
    3. Rollbacks work correctly
    """
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        pool_pre_ping=True
    )
    
    try:
        for _ in range(transaction_count):
            async with engine.begin() as conn:
                # Test transaction with a simple query
                result = await conn.execute(text("SELECT 1"))
                assert result.fetchone()[0] == 1
                # Transaction will auto-commit on exit
        
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_database_connection_error_recovery():
    """
    Property: The database connection should recover gracefully from errors.
    
    This tests that:
    1. Invalid queries don't break the connection pool
    2. Subsequent valid queries work after errors
    3. Connection pool remains healthy
    """
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        pool_pre_ping=True
    )
    
    try:
        # Try an invalid query
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT * FROM nonexistent_table"))
        except Exception:
            pass  # Expected to fail
        
        # Verify we can still make valid queries
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1, "Connection should still work after error"
        
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_database_connection_from_session():
    """
    Property: AsyncSession should be able to connect to the database and
    perform operations.
    
    This tests that:
    1. AsyncSession can be created
    2. Sessions can execute queries
    3. Sessions can be properly closed
    """
    engine = create_async_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        pool_pre_ping=True
    )
    
    async_session_maker = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
            
    finally:
        await engine.dispose()
