"""
Property-based tests for subscription product removal functionality
Feature: subscription-product-management, Property 1: Product Removal Updates Subscription State
"""
import pytest
import asyncio
from hypothesis import given, strategies as st, settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from core.database import Base
from core.config import settings
from core.utils.uuid_utils import uuid7
from services.enhanced_subscription_service import EnhancedSubscriptionService
from models.subscriptions import Subscription, SubscriptionProduct
from models.discounts import ProductRemovalAudit
from models.user import User
from models.product import Product, Category, ProductVariant
from datetime import datetime, timedelta
from decimal import Decimal


# Test database setup
@pytest.fixture(scope="module")
async def test_engine():
    """Create test database engine"""
    test_db_url = settings.SQLALCHEMY_DATABASE_URI.replace("/banwee_db", "/banwee_test_db")
    engine = create_async_engine(test_db_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create test database session"""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_user(test_session):
    """Create test user"""
    user = User(
        id=uuid7(),
        email="test@example.com",
        firstname="Test",
        lastname="User",
        hashed_password="hashed_password",
        role="Customer",
        verified=True,
        is_active=True
    )
    test_session.add(user)
    await test_session.commit()
    return user


@pytest.fixture
async def test_category(test_session):
    """Create test category"""
    category = Category(
        id=uuid7(),
        name="Test Category",
        is_active=True
    )
    test_session.add(category)
    await test_session.commit()
    return category


@pytest.fixture
async def test_products(test_session, test_user, test_category):
    """Create test products"""
    products = []
    for i in range(3):
        product = Product(
            id=uuid7(),
            name=f"Test Product {i+1}",
            slug=f"test-product-{i+1}",
            category_id=test_category.id,
            supplier_id=test_user.id,
            product_status="active",
            availability_status="available",
            dietary_tags=[]
        )
        test_session.add(product)
        products.append(product)
    
    await test_session.commit()
    return products


@pytest.fixture
async def test_subscription_with_products(test_session, test_user, test_products):
    """Create test subscription with multiple products"""
    subscription = Subscription(
        id=uuid7(),
        user_id=test_user.id,
        plan_id="basic",
        status="active",
        price=50.0,
        currency="USD",
        billing_cycle="monthly",
        subtotal=40.0,
        shipping_cost=5.0,
        tax_amount=3.0,
        tax_rate=0.075,
        discount_amount=0.0,
        total=48.0
    )
    test_session.add(subscription)
    await test_session.flush()
    
    # Add subscription products
    subscription_products = []
    for i, product in enumerate(test_products):
        sp = SubscriptionProduct(
            id=uuid7(),
            subscription_id=subscription.id,
            product_id=product.id,
            quantity=1,
            unit_price=15.0,
            total_price=15.0
        )
        test_session.add(sp)
        subscription_products.append(sp)
    
    await test_session.commit()
    return subscription, subscription_products


# Hypothesis strategies
@st.composite
def product_removal_scenario(draw):
    """Generate valid product removal scenarios"""
    return {
        "reason": draw(st.one_of(
            st.none(),
            st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pc", "Pd", "Zs")))
        )),
        "should_succeed": draw(st.booleans())
    }


class TestProductRemovalProperties:
    """Property-based tests for product removal functionality"""

    @given(removal_data=product_removal_scenario())
    @settings(max_examples=10, deadline=15000)
    @pytest.mark.asyncio
    async def test_product_removal_updates_subscription_state(
        self, 
        test_session, 
        test_user, 
        test_subscription_with_products,
        removal_data
    ):
        """
        Property 1: Product Removal Updates Subscription State
        For any active subscription with multiple products, removing a product should result in 
        the product being absent from the subscription and the subscription totals being 
        recalculated and persisted correctly.
        **Validates: Requirements 1.1, 1.4**
        """
        subscription, subscription_products = test_subscription_with_products
        service = EnhancedSubscriptionService(test_session)
        
        # Ensure we have multiple products
        assert len(subscription_products) >= 2, "Need multiple products for removal test"
        
        # Get initial state
        initial_product_count = len([sp for sp in subscription_products if sp.is_active])
        initial_total = subscription.total
        product_to_remove = subscription_products[0]
        
        # Remove the product
        updated_subscription = await service.remove_product(
            subscription_id=subscription.id,
            product_id=product_to_remove.product_id,
            user_id=test_user.id,
            reason=removal_data["reason"]
        )
        
        # Verify product is marked as removed
        await test_session.refresh(product_to_remove)
        assert product_to_remove.removed_at is not None
        assert product_to_remove.removed_by == test_user.id
        
        # Verify subscription state is updated
        assert updated_subscription.id == subscription.id
        
        # Verify product count decreased
        remaining_products_result = await test_session.execute(
            select(SubscriptionProduct).where(
                SubscriptionProduct.subscription_id == subscription.id
            )
        )
        remaining_products = remaining_products_result.scalars().all()
        active_products = [sp for sp in remaining_products if sp.is_active]
        
        assert len(active_products) == initial_product_count - 1
        
        # Verify audit trail was created
        audit_result = await test_session.execute(
            select(ProductRemovalAudit).where(
                ProductRemovalAudit.subscription_id == subscription.id
            )
        )
        audit = audit_result.scalar_one_or_none()
        
        assert audit is not None
        assert audit.product_id == product_to_remove.product_id
        assert audit.removed_by == test_user.id
        assert audit.reason == (removal_data["reason"] or "User requested removal")
        
        # Verify totals were recalculated (should be less than initial)
        await test_session.refresh(updated_subscription)
        assert updated_subscription.total <= initial_total
        assert updated_subscription.subtotal is not None
        assert updated_subscription.total >= 0  # Non-negative invariant

    @pytest.mark.asyncio
    async def test_cannot_remove_last_product(
        self, 
        test_session, 
        test_user, 
        test_products
    ):
        """
        Property 2: Subscription Validity Preservation
        For any subscription with only one product, attempting to remove it should fail
        and maintain the subscription in a valid state.
        **Validates: Requirements 1.2**
        """
        # Create subscription with only one product
        subscription = Subscription(
            id=uuid7(),
            user_id=test_user.id,
            plan_id="basic",
            status="active",
            price=20.0,
            currency="USD",
            billing_cycle="monthly",
            subtotal=15.0,
            shipping_cost=5.0,
            tax_amount=0.0,
            tax_rate=0.0,
            discount_amount=0.0,
            total=20.0
        )
        test_session.add(subscription)
        await test_session.flush()
        
        # Add only one product
        subscription_product = SubscriptionProduct(
            id=uuid7(),
            subscription_id=subscription.id,
            product_id=test_products[0].id,
            quantity=1,
            unit_price=15.0,
            total_price=15.0
        )
        test_session.add(subscription_product)
        await test_session.commit()
        
        service = EnhancedSubscriptionService(test_session)
        
        # Attempt to remove the only product should fail
        with pytest.raises(HTTPException) as exc_info:
            await service.remove_product(
                subscription_id=subscription.id,
                product_id=test_products[0].id,
                user_id=test_user.id
            )
        
        assert exc_info.value.status_code == 400
        assert "last product" in str(exc_info.value.detail).lower()
        
        # Verify subscription state is unchanged
        await test_session.refresh(subscription)
        await test_session.refresh(subscription_product)
        
        assert subscription.status == "active"
        assert subscription_product.removed_at is None
        assert subscription.total == 20.0

    @pytest.mark.asyncio
    async def test_product_removal_authorization(
        self, 
        test_session, 
        test_subscription_with_products
    ):
        """
        Property 16: Authorization and State Validation
        For any product removal request, the system should validate user permissions 
        and subscription state before processing the request.
        **Validates: Requirements 7.1**
        """
        subscription, subscription_products = test_subscription_with_products
        service = EnhancedSubscriptionService(test_session)
        
        # Create unauthorized user
        unauthorized_user = User(
            id=uuid7(),
            email="unauthorized@example.com",
            firstname="Unauthorized",
            lastname="User",
            hashed_password="hashed_password",
            role="Customer",
            verified=True,
            is_active=True
        )
        test_session.add(unauthorized_user)
        await test_session.commit()
        
        # Attempt to remove product with unauthorized user should fail
        with pytest.raises(HTTPException) as exc_info:
            await service.remove_product(
                subscription_id=subscription.id,
                product_id=subscription_products[0].product_id,
                user_id=unauthorized_user.id
            )
        
        assert exc_info.value.status_code == 404  # Subscription not found for this user
        
        # Verify no changes were made
        await test_session.refresh(subscription_products[0])
        assert subscription_products[0].removed_at is None

    @pytest.mark.asyncio
    async def test_product_removal_inactive_subscription(
        self, 
        test_session, 
        test_user, 
        test_subscription_with_products
    ):
        """
        Test that product removal fails for inactive subscriptions
        **Validates: Requirements 7.1**
        """
        subscription, subscription_products = test_subscription_with_products
        service = EnhancedSubscriptionService(test_session)
        
        # Make subscription inactive
        subscription.status = "cancelled"
        await test_session.commit()
        
        # Attempt to remove product from inactive subscription should fail
        with pytest.raises(HTTPException) as exc_info:
            await service.remove_product(
                subscription_id=subscription.id,
                product_id=subscription_products[0].product_id,
                user_id=test_user.id
            )
        
        assert exc_info.value.status_code == 400
        assert "inactive subscription" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_product_removal_nonexistent_product(
        self, 
        test_session, 
        test_user, 
        test_subscription_with_products
    ):
        """
        Test that removing a non-existent product fails gracefully
        **Validates: Requirements 7.4**
        """
        subscription, subscription_products = test_subscription_with_products
        service = EnhancedSubscriptionService(test_session)
        
        # Attempt to remove non-existent product
        nonexistent_product_id = uuid7()
        
        with pytest.raises(HTTPException) as exc_info:
            await service.remove_product(
                subscription_id=subscription.id,
                product_id=nonexistent_product_id,
                user_id=test_user.id
            )
        
        assert exc_info.value.status_code == 404
        assert "not found in subscription" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_product_removal_totals_recalculation(
        self, 
        test_session, 
        test_user, 
        test_subscription_with_products
    ):
        """
        Test that subscription totals are properly recalculated after product removal
        **Validates: Requirements 1.4**
        """
        subscription, subscription_products = test_subscription_with_products
        service = EnhancedSubscriptionService(test_session)
        
        # Record initial totals
        initial_subtotal = subscription.subtotal
        initial_total = subscription.total
        product_to_remove = subscription_products[0]
        product_price = product_to_remove.total_price
        
        # Remove product
        updated_subscription = await service.remove_product(
            subscription_id=subscription.id,
            product_id=product_to_remove.product_id,
            user_id=test_user.id
        )
        
        # Verify totals were recalculated
        expected_subtotal = initial_subtotal - product_price
        
        # Allow for small floating point differences
        assert abs(updated_subscription.subtotal - expected_subtotal) < 0.01
        assert updated_subscription.total < initial_total
        assert updated_subscription.total >= 0  # Non-negative invariant
        
        # Verify all pricing fields are consistent
        calculated_total = (
            updated_subscription.subtotal + 
            updated_subscription.shipping_cost + 
            updated_subscription.tax_amount - 
            updated_subscription.discount_amount
        )
        assert abs(updated_subscription.total - calculated_total) < 0.01