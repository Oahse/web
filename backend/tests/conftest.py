"""
Test configuration and fixtures for the Banwee backend
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from fastapi.testclient import TestClient
from httpx import AsyncClient
import redis.asyncio as redis
from unittest.mock import AsyncMock, MagicMock, patch

from main import app
from core.db import get_db, BaseModel
from core.cache import get_redis
from core.config import settings
from models.user import User, UserRole
from models.product import Product, ProductVariant, Category
from models.cart import Cart, CartItem
from models.orders import Order, OrderItem
from models.payments import PaymentMethod, PaymentIntent, Transaction
from models.shipping import ShippingMethod
from models.tax_rates import TaxRate
from models.inventories import Inventory, WarehouseLocation
from services.auth import AuthService
from uuid import uuid4
from datetime import datetime, timedelta
from decimal import Decimal

# Test database URL - using the same Neon PostgreSQL database with asyncpg driver
TEST_DATABASE_URL = "postgresql+asyncpg://neondb_owner:npg_qI9D0igTcRXw@ep-plain-morning-ah8l56gm-pooler.c-3.us-east-1.aws.neon.tech/neondb?ssl=require"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=5,
    max_overflow=10
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Set up test database tables in a test schema."""
    # Import all models to ensure they're registered with Base
    from models import user, product, cart, orders, payments, shipping, tax_rates, inventories, loyalty, analytics, admin, discounts, promocode, refunds, review, subscriptions, variant_tracking, wishlist, validation_rules
    
    async with test_engine.begin() as conn:
        # Create test schema
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS test_schema"))
        
        # Set search path to use test schema
        await conn.execute(text("SET search_path TO test_schema"))
        
        # Drop all tables first (clean slate)
        await conn.run_sync(BaseModel.metadata.drop_all)
        # Create all tables in test schema
        await conn.run_sync(BaseModel.metadata.create_all)
    yield
    # Cleanup after all tests
    async with test_engine.begin() as conn:
        # Drop test schema and all its contents
        await conn.execute(text("DROP SCHEMA IF EXISTS test_schema CASCADE"))


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with TestSessionLocal() as session:
        try:
            # Set search path to test schema for this session
            await session.execute(text("SET search_path TO test_schema"))
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture
async def mock_redis():
    """Mock Redis client."""
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = True
    mock_redis.exists.return_value = False
    mock_redis.expire.return_value = True
    return mock_redis


@pytest.fixture
def client(db_session, mock_redis):
    """Create test client with dependency overrides."""
    def override_get_db():
        return db_session
    
    def override_get_redis():
        return mock_redis
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(db_session, mock_redis):
    """Create async test client."""
    def override_get_db():
        return db_session
    
    def override_get_redis():
        return mock_redis
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# User fixtures
@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        firstname="Test",
        lastname="User",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        role=UserRole.CUSTOMER,
        verified=True,
        is_active=True,
        phone="+1234567890",
        country="US"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    user = User(
        id=uuid4(),
        email="admin@example.com",
        firstname="Admin",
        lastname="User",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        role=UserRole.ADMIN,
        verified=True,
        is_active=True,
        phone="+1234567891",
        country="US"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def supplier_user(db_session: AsyncSession) -> User:
    """Create a supplier user."""
    user = User(
        id=uuid4(),
        email="supplier@example.com",
        firstname="Supplier",
        lastname="User",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        role=UserRole.SUPPLIER,
        verified=True,
        is_active=True,
        phone="+1234567892",
        country="US"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# Authentication fixtures
@pytest_asyncio.fixture
async def auth_headers(test_user: User, db_session: AsyncSession) -> dict:
    """Create authentication headers for test user."""
    auth_service = AuthService(db_session)
    token = auth_service.create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def admin_auth_headers(admin_user: User, db_session: AsyncSession) -> dict:
    """Create authentication headers for admin user."""
    auth_service = AuthService(db_session)
    token = auth_service.create_access_token(data={"sub": str(admin_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def supplier_auth_headers(supplier_user: User, db_session: AsyncSession) -> dict:
    """Create authentication headers for supplier user."""
    auth_service = AuthService(db_session)
    token = auth_service.create_access_token(data={"sub": str(supplier_user.id)})
    return {"Authorization": f"Bearer {token}"}


# Product fixtures
@pytest_asyncio.fixture
async def test_category(db_session: AsyncSession) -> Category:
    """Create a test category."""
    category = Category(
        id=uuid4(),
        name="Electronics",
        description="Electronic products",
        is_active=True
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest_asyncio.fixture
async def test_product(db_session: AsyncSession, test_category: Category) -> Product:
    """Create a test product."""
    product = Product(
        id=uuid4(),
        name="Test Product",
        description="A test product",
        category_id=test_category.id,
        brand="Test Brand",
        is_active=True,
        is_featured=False
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest_asyncio.fixture
async def test_variant(db_session: AsyncSession, test_product: Product) -> ProductVariant:
    """Create a test product variant."""
    variant = ProductVariant(
        id=uuid4(),
        product_id=test_product.id,
        name="Test Variant",
        sku="TEST-001",
        base_price=Decimal("99.99"),
        sale_price=Decimal("79.99"),
        weight=Decimal("1.0"),
        is_active=True
    )
    db_session.add(variant)
    await db_session.commit()
    await db_session.refresh(variant)
    return variant


# Inventory fixtures
@pytest_asyncio.fixture
async def test_warehouse(db_session: AsyncSession) -> WarehouseLocation:
    """Create a test warehouse location."""
    warehouse = WarehouseLocation(
        id=uuid4(),
        name="Main Warehouse",
        address="123 Test St",
        city="Test City",
        state="TS",
        country="US",
        postal_code="12345",
        is_active=True
    )
    db_session.add(warehouse)
    await db_session.commit()
    await db_session.refresh(warehouse)
    return warehouse


@pytest_asyncio.fixture
async def test_inventory(db_session: AsyncSession, test_variant: ProductVariant, test_warehouse: WarehouseLocation) -> Inventory:
    """Create test inventory."""
    inventory = Inventory(
        id=uuid4(),
        variant_id=test_variant.id,
        warehouse_id=test_warehouse.id,
        quantity_available=100,
        quantity_reserved=0,
        reorder_point=10,
        reorder_quantity=50
    )
    db_session.add(inventory)
    await db_session.commit()
    await db_session.refresh(inventory)
    return inventory


# Cart fixtures
@pytest_asyncio.fixture
async def test_cart(db_session: AsyncSession, test_user: User) -> Cart:
    """Create a test cart."""
    cart = Cart(
        id=uuid4(),
        user_id=test_user.id,
        session_id=None
    )
    db_session.add(cart)
    await db_session.commit()
    await db_session.refresh(cart)
    return cart


@pytest_asyncio.fixture
async def test_cart_item(db_session: AsyncSession, test_cart: Cart, test_variant: ProductVariant) -> CartItem:
    """Create a test cart item."""
    cart_item = CartItem(
        id=uuid4(),
        cart_id=test_cart.id,
        variant_id=test_variant.id,
        quantity=2
    )
    db_session.add(cart_item)
    await db_session.commit()
    await db_session.refresh(cart_item)
    return cart_item


# Shipping fixtures
@pytest_asyncio.fixture
async def test_shipping_method(db_session: AsyncSession) -> ShippingMethod:
    """Create a test shipping method."""
    shipping_method = ShippingMethod(
        id=uuid4(),
        name="Standard Shipping",
        description="5-7 business days",
        base_cost=Decimal("9.99"),
        per_kg_cost=Decimal("2.00"),
        estimated_days_min=5,
        estimated_days_max=7,
        is_active=True
    )
    db_session.add(shipping_method)
    await db_session.commit()
    await db_session.refresh(shipping_method)
    return shipping_method


# Tax fixtures
@pytest_asyncio.fixture
async def test_tax_rate(db_session: AsyncSession) -> TaxRate:
    """Create a test tax rate."""
    tax_rate = TaxRate(
        id=uuid4(),
        country="US",
        state="CA",
        rate=Decimal("0.0875"),  # 8.75%
        is_active=True
    )
    db_session.add(tax_rate)
    await db_session.commit()
    await db_session.refresh(tax_rate)
    return tax_rate


# Payment fixtures
@pytest_asyncio.fixture
async def test_payment_method(db_session: AsyncSession, test_user: User) -> PaymentMethod:
    """Create a test payment method."""
    payment_method = PaymentMethod(
        id=uuid4(),
        user_id=test_user.id,
        type="card",
        provider="stripe",
        stripe_payment_method_id="pm_test_123",
        last_four="4242",
        brand="visa",
        expiry_month=12,
        expiry_year=2025,
        is_default=True,
        is_active=True
    )
    db_session.add(payment_method)
    await db_session.commit()
    await db_session.refresh(payment_method)
    return payment_method


# Mock external services
@pytest.fixture
def mock_stripe():
    """Mock Stripe API."""
    with patch('stripe.PaymentMethod') as mock_pm, \
         patch('stripe.PaymentIntent') as mock_pi, \
         patch('stripe.Token') as mock_token:
        
        # Mock PaymentMethod
        mock_pm.retrieve.return_value = MagicMock(
            id="pm_test_123",
            type="card",
            card=MagicMock(
                last4="4242",
                brand="visa",
                exp_month=12,
                exp_year=2025
            )
        )
        
        # Mock PaymentIntent
        mock_pi.create.return_value = MagicMock(
            id="pi_test_123",
            status="requires_confirmation",
            amount=1000,
            currency="usd"
        )
        
        # Mock Token
        mock_token.retrieve.return_value = MagicMock(
            id="tok_test_123",
            card=MagicMock(
                last4="4242",
                brand="visa",
                exp_month=12,
                exp_year=2025
            )
        )
        
        yield {
            'payment_method': mock_pm,
            'payment_intent': mock_pi,
            'token': mock_token
        }


@pytest.fixture
def mock_email():
    """Mock email service."""
    with patch('core.utils.messages.email.send_email') as mock_send:
        mock_send.return_value = True
        yield mock_send


# Test data factories
class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def user_data(**kwargs):
        """Create user test data."""
        default_data = {
            "email": "test@example.com",
            "firstname": "Test",
            "lastname": "User",
            "password": "TestPassword123!",
            "phone": "+1234567890",
            "country": "US"
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def product_data(**kwargs):
        """Create product test data."""
        default_data = {
            "name": "Test Product",
            "description": "A test product",
            "brand": "Test Brand",
            "is_active": True,
            "is_featured": False
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def variant_data(**kwargs):
        """Create variant test data."""
        default_data = {
            "name": "Test Variant",
            "sku": "TEST-001",
            "base_price": "99.99",
            "sale_price": "79.99",
            "weight": "1.0",
            "is_active": True
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def order_data(**kwargs):
        """Create order test data."""
        default_data = {
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "country": "US",
                "postal_code": "12345"
            },
            "billing_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "TS",
                "country": "US",
                "postal_code": "12345"
            }
        }
        default_data.update(kwargs)
        return default_data


@pytest.fixture
def test_data_factory():
    """Provide test data factory."""
    return TestDataFactory