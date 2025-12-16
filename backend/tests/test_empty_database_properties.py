"""
Property-based tests for empty database support.

Feature: docker-full-functionality
Tests that the application handles empty database gracefully.

These tests create their own isolated databases and don't use conftest fixtures.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import random
import psycopg2
import sys
import os

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import application components
from core.database import Base, initialize_db, db_manager
from main import app
from httpx import AsyncClient

# Import all models to register them with Base.metadata
from models.user import User, Address
from models.product import Product, ProductVariant, ProductImage, Category
from models.cart import Cart, CartItem
from models.order import Order, OrderItem, TrackingEvent
from models.payment import PaymentMethod
from models.transaction import Transaction
from models.review import Review
from models.notification import Notification
from models.wishlist import Wishlist, WishlistItem
from models.blog import BlogPost, BlogCategory, BlogTag, Comment, BlogPostTag
from models.subscription import Subscription
from models.inventory import Inventory, StockAdjustment, WarehouseLocation
from models.activity_log import ActivityLog
from models.settings import SystemSettings
from models.promocode import Promocode
from models.shipping import ShippingMethod


def get_test_db_url():
    """Generate unique test database URL"""
    import time
    unique_db_name = f"banwee_empty_test_{int(time.time() * 1000000)}_{random.randint(0, 1000000)}"
    return f"postgresql+asyncpg://banwee:banwee_password@localhost:5432/{unique_db_name}", unique_db_name


# Override fixtures to prevent conftest from running
@pytest.fixture(scope="function")
def async_engine():
    return None

@pytest.fixture(scope="function", autouse=False)
async def setup_test_database():
    yield


@pytest.mark.asyncio
async def test_property_33_migration_with_empty_database():
    """
    Feature: docker-full-functionality, Property 33: Migration with empty database
    
    For any application startup with an empty database, all migrations should run 
    successfully without errors.
    
    Validates: Requirements 13.1
    """
    # Create unique test database
    test_db_url, test_db_name = get_test_db_url()
    base_url = "postgresql://banwee:banwee_password@localhost:5432/postgres"
    
    # Connect to postgres database to create test database
    conn = psycopg2.connect(base_url)
    conn.autocommit = True
    cursor = conn.cursor()
    engine = None
    
    try:
        # Terminate existing connections and drop database if exists
        cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{test_db_name}';")
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        cursor.execute(f"CREATE DATABASE {test_db_name}")
        
        # Create engine and run migrations
        engine = create_async_engine(test_db_url, echo=False, pool_pre_ping=True, poolclass=None)
        
        # Clear metadata state to avoid conflicts between test runs
        Base.metadata.clear()
        
        # Re-import models to rebuild metadata
        from models.user import User, Address
        from models.product import Product, ProductVariant, ProductImage, Category
        from models.cart import Cart, CartItem
        from models.order import Order, OrderItem, TrackingEvent
        from models.payment import PaymentMethod
        from models.transaction import Transaction
        from models.review import Review
        from models.notification import Notification
        from models.wishlist import Wishlist, WishlistItem
        from models.blog import BlogPost, BlogCategory, BlogTag, Comment, BlogPostTag
        from models.subscription import Subscription
        from models.inventory import Inventory, StockAdjustment, WarehouseLocation
        from models.activity_log import ActivityLog
        from models.settings import SystemSettings
        from models.promocode import Promocode
        from models.shipping import ShippingMethod
        
        # Run migrations (create all tables)
        async with engine.begin() as conn_async:
            await conn_async.run_sync(Base.metadata.create_all)
        
        # Verify no errors occurred - if we got here, migrations succeeded
        assert True, "Migrations completed successfully on empty database"
        
    finally:
        # Cleanup
        if engine:
            await engine.dispose()
        # Terminate connections before dropping
        cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{test_db_name}';")
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        cursor.close()
        conn.close()


@pytest.mark.asyncio
async def test_property_34_schema_creation():
    """
    Feature: docker-full-functionality, Property 34: Schema creation
    
    For any application startup with an empty database, all required tables and 
    indexes should be created after migrations.
    
    Validates: Requirements 13.2
    """
    # Create unique test database
    test_db_url, test_db_name = get_test_db_url()
    base_url = "postgresql://banwee:banwee_password@localhost:5432/postgres"
    
    # Connect to postgres database to create test database
    conn = psycopg2.connect(base_url)
    conn.autocommit = True
    cursor = conn.cursor()
    engine = None
    
    try:
        # Terminate existing connections and drop database if exists
        cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{test_db_name}';")
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        cursor.execute(f"CREATE DATABASE {test_db_name}")
        
        # Create engine and run migrations
        engine = create_async_engine(test_db_url, echo=False, pool_pre_ping=True, poolclass=None)
        
        # Clear metadata state to avoid conflicts between test runs
        Base.metadata.clear()
        
        # Re-import models to rebuild metadata
        from models.user import User, Address
        from models.product import Product, ProductVariant, ProductImage, Category
        from models.cart import Cart, CartItem
        from models.order import Order, OrderItem, TrackingEvent
        from models.payment import PaymentMethod
        from models.transaction import Transaction
        from models.review import Review
        from models.notification import Notification
        from models.wishlist import Wishlist, WishlistItem
        from models.blog import BlogPost, BlogCategory, BlogTag, Comment, BlogPostTag
        from models.subscription import Subscription
        from models.inventory import Inventory, StockAdjustment, WarehouseLocation
        from models.activity_log import ActivityLog
        from models.settings import SystemSettings
        from models.promocode import Promocode
        from models.shipping import ShippingMethod
        
        # Run migrations (create all tables)
        async with engine.begin() as conn_async:
            await conn_async.run_sync(Base.metadata.create_all)
        
        # Verify tables were created
        async with engine.connect() as conn_async:
            # Get list of tables
            result = await conn_async.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in result.fetchall()]
            
            # Check that essential tables exist
            essential_tables = [
                'users', 'products', 'categories', 'orders', 
                'cart_items', 'product_variants', 'addresses'
            ]
            
            for table in essential_tables:
                assert table in tables, f"Essential table '{table}' was not created"
        
    finally:
        # Cleanup
        if engine:
            await engine.dispose()
        # Terminate connections before dropping
        cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{test_db_name}';")
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        cursor.close()
        conn.close()


@pytest.mark.asyncio
async def test_property_35_empty_database_error_handling():
    """
    Feature: docker-full-functionality, Property 35: Empty database error handling
    
    For any application startup with an empty database, no errors should be thrown 
    due to missing data.
    
    Validates: Requirements 13.3
    """
    # Create unique test database
    test_db_url, test_db_name = get_test_db_url()
    base_url = "postgresql://banwee:banwee_password@localhost:5432/postgres"
    
    # Connect to postgres database to create test database
    conn = psycopg2.connect(base_url)
    conn.autocommit = True
    cursor = conn.cursor()
    engine = None
    
    try:
        # Terminate existing connections and drop database if exists
        cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{test_db_name}';")
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        cursor.execute(f"CREATE DATABASE {test_db_name}")
        
        # Create engine and session
        engine = create_async_engine(test_db_url, echo=False, pool_pre_ping=True)
        TestingSessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Run migrations
        async with engine.begin() as conn_async:
            await conn_async.run_sync(Base.metadata.create_all)
        
        # Initialize database manager
        initialize_db(test_db_url, env_is_local=True)
        db_manager.set_engine_and_session_factory(engine, TestingSessionLocal)
        
        # Override get_db dependency
        async def override_get_db():
            async with TestingSessionLocal() as session:
                yield session
        
        from core.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        
        # Test that the application starts without errors
        # by making a simple request to the root endpoint
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")
            assert response.status_code == 200, "Application failed to start with empty database"
        
        # Cleanup
        app.dependency_overrides.clear()
        
    finally:
        # Cleanup
        if engine:
            await engine.dispose()
        # Terminate connections before dropping
        cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{test_db_name}';")
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        cursor.close()
        conn.close()


@pytest.mark.asyncio
@settings(max_examples=10, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    endpoint=st.sampled_from([
        "/api/v1/products/",
        "/api/v1/products/categories",
        "/api/v1/products/home",
    ])
)
async def test_property_36_empty_response_handling(endpoint: str):
    """
    Feature: docker-full-functionality, Property 36: Empty response handling
    
    For any API endpoint called with an empty database, the response should be 
    an empty array or null, not an error.
    
    Validates: Requirements 13.4
    """
    # Create unique test database
    test_db_url, test_db_name = get_test_db_url()
    base_url = "postgresql://banwee:banwee_password@localhost:5432/postgres"
    
    # Connect to postgres database to create test database
    conn = psycopg2.connect(base_url)
    conn.autocommit = True
    cursor = conn.cursor()
    engine = None
    
    try:
        # Terminate existing connections and drop database if exists
        cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{test_db_name}';")
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        cursor.execute(f"CREATE DATABASE {test_db_name}")
        
        # Create engine and session
        engine = create_async_engine(test_db_url, echo=False, pool_pre_ping=True)
        TestingSessionLocal = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=engine, 
            class_=AsyncSession, 
            expire_on_commit=False
        )
        
        # Run migrations
        async with engine.begin() as conn_async:
            await conn_async.run_sync(Base.metadata.create_all)
        
        # Initialize database manager
        initialize_db(test_db_url, env_is_local=True)
        db_manager.set_engine_and_session_factory(engine, TestingSessionLocal)
        
        # Override get_db dependency
        async def override_get_db():
            async with TestingSessionLocal() as session:
                yield session
        
        from core.database import get_db
        app.dependency_overrides[get_db] = override_get_db
        
        # Test endpoint with empty database
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(endpoint)
            
            # Should return 200, not an error
            assert response.status_code == 200, \
                f"Endpoint {endpoint} returned error {response.status_code} with empty database"
            
            # Parse response
            data = response.json()
            
            # Should have success=True
            assert data.get("success") is True, \
                f"Endpoint {endpoint} returned success=False with empty database"
            
            # Data should be empty array or contain empty arrays
            response_data = data.get("data")
            if isinstance(response_data, list):
                # Direct array response
                assert response_data == [], \
                    f"Endpoint {endpoint} should return empty array with empty database"
            elif isinstance(response_data, dict):
                # Object with arrays inside
                for key, value in response_data.items():
                    if isinstance(value, list):
                        assert value == [], \
                            f"Endpoint {endpoint} field '{key}' should be empty array with empty database"
                    elif key == "total":
                        assert value == 0, \
                            f"Endpoint {endpoint} total should be 0 with empty database"
        
        # Cleanup
        app.dependency_overrides.clear()
        
    finally:
        # Cleanup
        if engine:
            await engine.dispose()
        # Terminate connections before dropping
        cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{test_db_name}';")
        cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
        cursor.close()
        conn.close()
