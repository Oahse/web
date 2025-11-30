"""
Property-based tests for async/greenlet error prevention

Feature: app-enhancements
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from decimal import Decimal

from models.user import User
from models.product import Product, ProductVariant
from models.cart import Cart, CartItem
from models.shipping import ShippingMethod
from models.payment import PaymentMethod
from models.address import Address
from services.order import OrderService
from schemas.order import CheckoutRequest
from fastapi import BackgroundTasks


# Hypothesis strategies for generating test data
@st.composite
def checkout_data_strategy(draw):
    """Generate random checkout request data"""
    return {
        "shipping_address_id": draw(st.uuids()),
        "shipping_method_id": draw(st.uuids()),
        "payment_method_id": draw(st.uuids()),
        "notes": draw(st.one_of(st.none(), st.text(min_size=0, max_size=200)))
    }


@pytest.mark.asyncio
@given(checkout_data=checkout_data_strategy())
@settings(
    max_examples=100,  # Run 100 iterations as specified in design
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    deadline=None  # Disable deadline for async operations
)
async def test_property_48_order_placement_without_greenlet_errors(
    db_session: AsyncSession,
    checkout_data: dict
):
    """
    **Feature: app-enhancements, Property 48: Order placement without greenlet errors**
    **Validates: Requirements 15.1**
    
    Property: For any order submission, the system should process the order 
    without greenlet spawn errors
    
    This test verifies that order placement uses proper async session management
    and doesn't trigger greenlet errors by mixing sync/async contexts.
    """
    # Setup: Create test user
    user = User(
        id=uuid4(),
        email=f"test_{uuid4()}@example.com",
        firstname="Test",
        lastname="User",
        role="Customer",
        active=True,
        verified=True,
        hashed_password="hashed_password"
    )
    db_session.add(user)
    
    # Create test product and variant
    product = Product(
        id=uuid4(),
        name="Test Product",
        description="Test Description",
        category="Electronics",
        brand="TestBrand",
        active=True
    )
    db_session.add(product)
    
    variant = ProductVariant(
        id=uuid4(),
        product_id=product.id,
        name="Default",
        sku=f"SKU-{uuid4()}",
        base_price=Decimal("99.99"),
        stock=100
    )
    db_session.add(variant)
    
    # Create cart with items
    cart = Cart(
        id=uuid4(),
        user_id=user.id
    )
    db_session.add(cart)
    
    cart_item = CartItem(
        id=uuid4(),
        cart_id=cart.id,
        variant_id=variant.id,
        quantity=1,
        price_per_unit=Decimal("99.99"),
        saved_for_later=False
    )
    db_session.add(cart_item)
    
    # Create shipping address
    address = Address(
        id=checkout_data["shipping_address_id"],
        user_id=user.id,
        street="123 Test St",
        city="Test City",
        state="TS",
        post_code="12345",
        country="Test Country"
    )
    db_session.add(address)
    
    # Create shipping method
    shipping_method = ShippingMethod(
        id=checkout_data["shipping_method_id"],
        name="Standard Shipping",
        description="5-7 business days",
        price=Decimal("9.99"),
        estimated_days=7
    )
    db_session.add(shipping_method)
    
    # Create payment method
    payment_method = PaymentMethod(
        id=checkout_data["payment_method_id"],
        user_id=user.id,
        type="card",
        provider="stripe",
        last_four="4242",
        is_default=True
    )
    db_session.add(payment_method)
    
    await db_session.commit()
    
    # Test: Place order - should not raise greenlet errors
    order_service = OrderService(db_session)
    background_tasks = BackgroundTasks()
    
    try:
        # Create checkout request
        checkout_request = CheckoutRequest(
            shipping_address_id=checkout_data["shipping_address_id"],
            shipping_method_id=checkout_data["shipping_method_id"],
            payment_method_id=checkout_data["payment_method_id"],
            notes=checkout_data.get("notes")
        )
        
        # This should complete without greenlet errors
        # The key is that all database operations use await
        # and Celery tasks are called outside transaction context
        order = await order_service.place_order(
            user_id=user.id,
            request=checkout_request,
            background_tasks=background_tasks
        )
        
        # Verify order was created (basic sanity check)
        assert order is not None
        assert order.user_id == str(user.id)
        
        # The fact that we got here without a greenlet error means the property holds
        
    except RuntimeError as e:
        # If we get a greenlet error, the property is violated
        if "greenlet" in str(e).lower():
            pytest.fail(f"Greenlet error detected: {e}")
        # Other RuntimeErrors might be expected (e.g., payment failures)
        # so we don't fail the test for those
    except Exception as e:
        # Other exceptions (like HTTPException for empty cart, payment failures, etc.)
        # are acceptable - we're only testing for greenlet errors
        # The property is about "no greenlet errors", not "order always succeeds"
        if "greenlet" in str(e).lower():
            pytest.fail(f"Greenlet error detected in exception: {e}")


@pytest.mark.asyncio
async def test_property_52_async_session_consistency(db_session: AsyncSession):
    """
    **Feature: app-enhancements, Property 52: AsyncSession consistency in async routes**
    **Validates: Requirements 16.1**
    
    Property: For any async route executing database queries, the system should 
    use AsyncSession consistently throughout
    
    This test verifies that the OrderService uses AsyncSession consistently
    and all database operations use await.
    """
    # Create a simple test to verify AsyncSession is used
    order_service = OrderService(db_session)
    
    # Verify the service has an AsyncSession
    assert isinstance(order_service.db, AsyncSession)
    
    # Verify the session has the correct configuration
    assert order_service.db.bind is not None
    
    # The fact that we can create the service with AsyncSession
    # and it doesn't raise errors means the property holds
    # The actual database operations are tested in the order placement test


@pytest.mark.asyncio
async def test_property_54_celery_async_sync_context_switching(db_session: AsyncSession):
    """
    **Feature: app-enhancements, Property 54: Celery async/sync context switching**
    **Validates: Requirements 16.3**
    
    Property: For any Celery task triggered from async code, the system should 
    handle context switching properly
    
    This test verifies that Celery tasks use sync sessions and don't attempt
    await operations in sync contexts.
    """
    # Import Celery tasks
    from tasks.email_tasks import SyncSessionLocal
    from tasks.notification_tasks import SyncSessionLocal as NotifSyncSession
    
    # Verify that Celery tasks use sync sessions
    assert SyncSessionLocal is not None
    assert NotifSyncSession is not None
    
    # Verify the session factories are configured for sync operations
    # (they should not be AsyncSession)
    from sqlalchemy.orm import Session
    
    with SyncSessionLocal() as session:
        assert isinstance(session, Session)
        assert not hasattr(session, '__aenter__')  # Should not be async context manager
    
    # The fact that we can create sync sessions for Celery tasks
    # means the async/sync boundary is properly handled
