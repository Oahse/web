import sys
import os
import pytest
import asyncio
from typing import AsyncGenerator

# Add the backend directory to the Python path
# This is necessary for pytest to find the 'main' module and other packages
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from main import app
from core.database import get_db, Base, initialize_db, db_manager
from core.config import settings



import random

# Use PostgreSQL in Docker for testing
# Make the database name unique per test session
unique_db_name = f"banwee_test_db_{random.randint(0, 1000000)}"
SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://banwee:banwee_password@localhost:5432/{unique_db_name}"


@pytest.fixture(scope="session")
async def async_engine():
    """Provides a session-scoped async SQLAlchemy engine."""
    engine = create_async_engine(
        SQLALCHEMY_DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        poolclass=None  # Disable pooling for tests to avoid connection issues
    )
    yield engine
    await engine.dispose()

TestingSessionLocal = None # Initialize to None, will be set in fixture


import psycopg2 # NEW: Import psycopg2 for synchronous DDL operations

# Use PostgreSQL in Docker for testing
# Make the database name unique per test session
unique_db_name = f"banwee_test_db_{random.randint(0, 1000000)}"
SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://banwee:banwee_password@localhost:5432/{unique_db_name}"

BASE_DB_URL_SYNC = "postgresql://banwee:banwee_password@localhost:5432/postgres" # Connect to a default database to create/drop test databases

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database(async_engine):
    """Sets up the test database schema once per session."""
    global TestingSessionLocal

    # 1. Synchronously connect to the base database (e.g., 'postgres') to create/drop the unique test database
    sync_conn = None
    try:
        sync_conn = psycopg2.connect(BASE_DB_URL_SYNC)
        sync_conn.autocommit = True
        sync_cursor = sync_conn.cursor()

        # Terminate any existing connections to the test database that might prevent dropping
        sync_cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{unique_db_name}';")
        
        # Drop and create database
        sync_cursor.execute(f"DROP DATABASE IF EXISTS {unique_db_name}")
        sync_cursor.execute(f"CREATE DATABASE {unique_db_name}")
        print(f"Created test database: {unique_db_name}")
    except Exception as e:
        print(f"Error during synchronous db creation/dropping: {e}")
        raise # Fail test setup if critical
    finally:
        if sync_cursor:
            sync_cursor.close()
        if sync_conn:
            sync_conn.close()

    # Now proceed with the unique test database (asynchronously)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession, expire_on_commit=False)
    
    # Initialize the global database objects for the application
    initialize_db(settings.SQLALCHEMY_DATABASE_URI, env_is_local=True)
    db_manager.set_engine_and_session_factory(async_engine, TestingSessionLocal)

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) # Drop existing tables in the unique DB (should be empty anyway)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all) # Drop tables after tests

    # 3. Synchronously connect to the base database again to drop the unique test database
    sync_conn = None
    try:
        sync_conn = psycopg2.connect(BASE_DB_URL_SYNC)
        sync_conn.autocommit = True
        sync_cursor = sync_conn.cursor()
        
        sync_cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{unique_db_name}';")
        sync_cursor.execute(f"DROP DATABASE IF EXISTS {unique_db_name}")
        print(f"Dropped test database: {unique_db_name}")
    except Exception as e:
        print(f"Error during synchronous db dropping: {e}")
        raise # Fail test setup if critical
    finally:
        if sync_cursor:
            sync_cursor.close()
        if sync_conn:
            sync_conn.close()

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    """Custom event loop for pytest-asyncio with session scope."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# @pytest.fixture(scope="function", autouse=True)
# async def db_setup_and_teardown(request):
#     """Setup and teardown database for each test function."""
#     # Don't create/drop tables for every test - too slow
#     # Instead, just ensure tables exist
#     try:
#         async with engine.begin() as conn:
#             await conn.run_sync(Base.metadata.create_all)
#     except Exception:
#         pass  # Tables might already exist
#     
#     # Clean up test data BEFORE each test to ensure clean state
#     try:
#         async with TestingSessionLocal() as session:
#             from sqlalchemy import text
#             
#             # Use TRUNCATE CASCADE for faster and more reliable cleanup
#             # This will delete all data and reset sequences
#             tables_to_truncate = [
#                 "activity_logs", "notifications", "reviews", "tracking_events",
#                 "transactions", "order_items", "orders", "product_images",
#                 "product_variants", "products", "payment_methods", "addresses",
#                 "cart_items", "carts", "wishlist_items", "wishlists", "users", "categories"
#             ]
#             
#             for table in tables_to_truncate:
#                 try:
#                     await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
#                 except Exception:
#                     pass  # Table might not exist or might be empty
#             
#             # Delete test categories (don't delete users as they have many dependencies)
#             # await session.execute(text("DELETE FROM categories WHERE name LIKE 'Test Category%'"))
#             await session.commit()
#     except Exception as e:
#         print(f"Warning: Pre-test cleanup failed: {e}")
#     
#     yield
#     
#     # Clean up test data after each test to avoid conflicts
#     # Only clean up if the test didn't explicitly skip cleanup
#     if not hasattr(request, 'param') or request.param != 'skip_cleanup':
#         try:
#             async with TestingSessionLocal() as session:
#                 # Import models with correct paths
#                 import sys
#                 import os
#                 # Add backend directory to path if not already there
#                 backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#                 if backend_dir not in sys.path:
#                     sys.path.insert(0, backend_dir)
#                 
#                 from sqlalchemy import delete, text
#                 
#                 # Use TRUNCATE CASCADE for faster and more reliable cleanup
#                 tables_to_truncate = [
#                     "activity_logs", "notifications", "reviews", "tracking_events",
#                     "transactions", "order_items", "orders", "product_images",
#                     "product_variants", "products", "payment_methods", "addresses",
#                     "cart_items", "carts", "wishlist_items", "wishlists", "users", "categories"
#                 ]
#                 
#                 for table in tables_to_truncate:
#                     try:
#                         await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
#                     except Exception:
#                         pass  # Table might not exist or might be empty
#                 
#                 # Delete test categories
#                 # await session.execute(text("DELETE FROM categories WHERE name LIKE 'Test Category%'"))
#                 await session.commit()
#         except Exception as e:
#             # If cleanup fails, log but don't fail the test
#             print(f"Warning: Test cleanup failed: {e}")

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session
    await session.close()

@pytest.fixture
def client() -> TestClient:
    return TestClient(app)

@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

def get_unique_name(base_name: str) -> str:
    """Generate a unique name for test data."""
    import time
    import random
    timestamp = int(time.time() * 1000000)
    random_suffix = random.randint(1000, 9999)
    return f"{base_name} {timestamp}{random_suffix}"

@pytest.fixture
async def test_category(db_session: AsyncSession):
    """Create a unique test category for each test."""
    from models.category import Category
    from uuid import uuid4
    
    # Create unique category name
    category_name = get_unique_name("Test Category")
    
    category = Category(
        id=uuid4(),
        name=category_name,
        description="Test category description",
        is_active=True
    )
    
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    
    return category

@pytest.fixture
async def auth_headers(db_session: AsyncSession) -> dict:
    """Create a test user and return auth headers"""
    from models.user import User
    from core.utils.auth.jwt_auth import JWTManager
    from uuid import uuid4
    import bcrypt
    from sqlalchemy import select
    import time
    
    # Use unique email for each test to avoid conflicts
    test_email = f"test_{int(time.time() * 1000000)}@example.com"
    
    # Check if user already exists (shouldn't happen with unique email, but just in case)
    result = await db_session.execute(select(User).where(User.email == test_email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        test_user = existing_user
    else:
        # Create a test supplier user
        test_user = User(
            id=uuid4(),
            email=test_email,
            firstname="Test",
            lastname="User",
            role="Supplier",
            active=True,
            verified=True,
            hashed_password=bcrypt.hashpw("testpassword123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        )
        
        db_session.add(test_user)
        await db_session.commit()
        await db_session.refresh(test_user)
    
    # Create access token using stored email
    jwt_manager = JWTManager()
    access_token = jwt_manager.create_access_token(data={"sub": test_email})
    
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
async def admin_auth_headers(db_session: AsyncSession) -> dict:
    """Create a test admin user and return auth headers"""
    from models.user import User
    from core.utils.auth.jwt_auth import JWTManager
    from uuid import uuid4
    import bcrypt
    from sqlalchemy import select
    import time

    # Use unique email for each test to avoid conflicts
    admin_email = f"admin_{int(time.time() * 1000000)}@example.com"

    # Check if user already exists
    result = await db_session.execute(select(User).where(User.email == admin_email))
    existing_admin = result.scalar_one_or_none()

    if existing_admin:
        test_admin = existing_admin
    else:
        # Create a test admin user
        test_admin = User(
            id=uuid4(),
            email=admin_email,
            firstname="Admin",
            lastname="User",
            role="Admin", # Set role to Admin
            active=True,
            verified=True,
            hashed_password=bcrypt.hashpw("adminpassword123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        )

        db_session.add(test_admin)
        await db_session.commit()
        await db_session.refresh(test_admin)

    # Create access token using stored email
    jwt_manager = JWTManager()
    access_token = jwt_manager.create_access_token(data={"sub": admin_email, "role": "Admin"})

    return {"Authorization": f"Bearer {access_token}"}
