"""
Property-based tests for subscription validity preservation
Feature: subscription-product-management, Property 2: Subscription Validity Preservation
"""
import pytest
import asyncio
from hypothesis import given, strategies as st, settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from core.database import Base
from core.config import settings as app_settings
from core.utils.uuid_utils import uuid7
from services.enhanced_subscription_service import EnhancedSubscriptionService
from models.subscriptions import Subscription, SubscriptionProduct
from models.user import User
from models.product import Product, Category
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi import HTTPException


# Test database setup
@pytest.fixture(scope="module")
async def test_engine():
    """Create test database engine"""
    # Use localhost for local testing instead of postgres hostname
    local_db_url = app_settings.SQLALCHEMY_DATABASE_URI.replace("postgres:5432", "localhost:5432")
    test_db_url = local_db_url.replace("/banwee_db", "/banwee_test_db")
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


# Hypothesis strategies
@st.composite
def subscription_configuration(draw):
    """Generate valid subscription configurations"""
    num_products = draw(st.integers(min_value=2, max_value=5))
    
    return {
        "num_products": num_products,
        "plan_id": draw(st.sampled_from(["basic", "premium", "enterprise"])),
        "billing_cycle": draw(st.sampled_from(["monthly", "yearly"])),
        "currency": draw(st.sampled_from(["USD", "EUR", "GBP"])),
        "product_prices": [
            draw(st.floats(min_value=5.0, max_value=50.0)) 
            for _ in range(num_products)
        ],
        "shipping_cost": draw(st.floats(min_value=0.0, max_value=20.0)),
        "tax_rate": draw(st.floats(min_value=0.0, max_value=0.15))
    }


@st.composite
def product_removal_sequence(draw):
    """Generate sequences of product removals"""
    max_removals = draw(st.integers(min_value=1, max_value=3))
    
    return {
        "max_removals": max_removals,
        "removal_reasons": [
            draw(st.one_of(
                st.none(),
                st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")))
            ))
            for _ in range(max_removals)
        ]
    }


class TestSubscriptionValidityProperties:
    """Property-based tests for subscription validity preservation"""

    @given(
        config=subscription_configuration(),
        removal_seq=product_removal_sequence()
    )
    @settings(max_examples=15, deadline=20000)
    @pytest.mark.asyncio
    async def test_subscription_validity_preservation(
        self, 
        test_session, 
        test_user, 
        test_category,
        config,
        removal_seq
    ):
        """
        Property 2: Subscription Validity Preservation
        For any subscription with more than one product, removing a single product should 
        maintain the subscription in a valid, active state.
        **Validates: Requirements 1.2**
        """
        # Ensure we have enough products to test removal
        from hypothesis import assume
        assume(config["num_products"] > removal_seq["max_removals"])
        
        # Create products
        products = []
        for i in range(config["num_products"]):
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
        
        # Create subscription
        subtotal = sum(config["product_prices"])
        tax_amount = subtotal * config["tax_rate"]
        total = subtotal + config["shipping_cost"] + tax_amount
        
        subscription = Subscription(
            id=uuid7(),
            user_id=test_user.id,
            plan_id=config["plan_id"],
            status="active",
            price=total,
            currency=config["currency"],
            billing_cycle=config["billing_cycle"],
            subtotal=subtotal,
            shipping_cost=config["shipping_cost"],
            tax_amount=tax_amount,
            tax_rate=config["tax_rate"],
            discount_amount=0.0,
            total=total
        )
        test_session.add(subscription)
        await test_session.flush()
        
        # Add subscription products
        subscription_products = []
        for i, (product, price) in enumerate(zip(products, config["product_prices"])):
            sp = SubscriptionProduct(
                id=uuid7(),
                subscription_id=subscription.id,
                product_id=product.id,
                quantity=1,
                unit_price=price,
                total_price=price
            )
            test_session.add(sp)
            subscription_products.append(sp)
        
        await test_session.commit()
        
        service = EnhancedSubscriptionService(test_session)
        
        # Record initial state
        initial_product_count = len(subscription_products)
        initial_status = subscription.status
        
        # Remove products one by one (but not all)
        products_removed = 0
        for i in range(min(removal_seq["max_removals"], initial_product_count - 1)):
            product_to_remove = subscription_products[i]
            reason = removal_seq["removal_reasons"][i]
            
            # Remove product
            updated_subscription = await service.remove_product(
                subscription_id=subscription.id,
                product_id=product_to_remove.product_id,
                user_id=test_user.id,
                reason=reason
            )
            
            products_removed += 1
            
            # Verify subscription remains valid and active
            assert updated_subscription.status == "active"
            assert updated_subscription.id == subscription.id
            
            # Verify subscription has positive total
            assert updated_subscription.total > 0
            
            # Verify at least one product remains
            remaining_products_result = await test_session.execute(
                select(SubscriptionProduct).where(
                    SubscriptionProduct.subscription_id == subscription.id
                )
            )
            remaining_products = remaining_products_result.scalars().all()
            active_products = [sp for sp in remaining_products if sp.is_active]
            
            expected_remaining = initial_product_count - products_removed
            assert len(active_products) == expected_remaining
            assert len(active_products) > 0  # Always at least one product
            
            # Verify subscription totals are consistent
            assert updated_subscription.subtotal >= 0
            assert updated_subscription.total >= updated_subscription.subtotal
            
            # Verify subscription metadata is valid
            assert updated_subscription.currency == config["currency"]
            assert updated_subscription.plan_id == config["plan_id"]
            assert updated_subscription.billing_cycle == config["billing_cycle"]

    @pytest.mark.asyncio
    async def test_subscription_validity_with_minimum_products(
        self, 
        test_session, 
        test_user, 
        test_category
    ):
        """
        Test subscription validity when reducing to minimum number of products
        **Validates: Requirements 1.2**
        """
        # Create exactly 2 products
        products = []
        for i in range(2):
            product = Product(
                id=uuid7(),
                name=f"Minimum Product {i+1}",
                slug=f"minimum-product-{i+1}",
                category_id=test_category.id,
                supplier_id=test_user.id,
                product_status="active",
                availability_status="available",
                dietary_tags=[]
            )
            test_session.add(product)
            products.append(product)
        
        await test_session.commit()
        
        # Create subscription with 2 products
        subscription = Subscription(
            id=uuid7(),
            user_id=test_user.id,
            plan_id="basic",
            status="active",
            price=30.0,
            currency="USD",
            billing_cycle="monthly",
            subtotal=25.0,
            shipping_cost=5.0,
            tax_amount=0.0,
            tax_rate=0.0,
            discount_amount=0.0,
            total=30.0
        )
        test_session.add(subscription)
        await test_session.flush()
        
        # Add both products
        for i, product in enumerate(products):
            sp = SubscriptionProduct(
                id=uuid7(),
                subscription_id=subscription.id,
                product_id=product.id,
                quantity=1,
                unit_price=12.5,
                total_price=12.5
            )
            test_session.add(sp)
        
        await test_session.commit()
        
        service = EnhancedSubscriptionService(test_session)
        
        # Remove one product (should succeed)
        updated_subscription = await service.remove_product(
            subscription_id=subscription.id,
            product_id=products[0].id,
            user_id=test_user.id
        )
        
        # Verify subscription is still valid with one product
        assert updated_subscription.status == "active"
        assert updated_subscription.total > 0
        
        # Verify exactly one product remains
        remaining_products_result = await test_session.execute(
            select(SubscriptionProduct).where(
                SubscriptionProduct.subscription_id == subscription.id
            )
        )
        remaining_products = remaining_products_result.scalars().all()
        active_products = [sp for sp in remaining_products if sp.is_active]
        
        assert len(active_products) == 1
        assert active_products[0].product_id == products[1].id
        
        # Attempt to remove the last product (should fail)
        with pytest.raises(HTTPException) as exc_info:
            await service.remove_product(
                subscription_id=subscription.id,
                product_id=products[1].id,
                user_id=test_user.id
            )
        
        assert exc_info.value.status_code == 400
        assert "last product" in str(exc_info.value.detail).lower()
        
        # Verify subscription state is unchanged after failed removal
        await test_session.refresh(updated_subscription)
        assert updated_subscription.status == "active"

    @given(
        num_products=st.integers(min_value=3, max_value=8),
        product_prices=st.lists(
            st.floats(min_value=1.0, max_value=100.0), 
            min_size=3, 
            max_size=8
        )
    )
    @settings(max_examples=10, deadline=15000)
    @pytest.mark.asyncio
    async def test_subscription_validity_multiple_removals(
        self, 
        test_session, 
        test_user, 
        test_category,
        num_products,
        product_prices
    ):
        """
        Test subscription validity when removing multiple products sequentially
        **Validates: Requirements 1.2**
        """
        from hypothesis import assume
        assume(len(product_prices) == num_products)
        assume(num_products >= 3)  # Need at least 3 to test multiple removals
        
        # Create products
        products = []
        for i in range(num_products):
            product = Product(
                id=uuid7(),
                name=f"Multi Product {i+1}",
                slug=f"multi-product-{i+1}",
                category_id=test_category.id,
                supplier_id=test_user.id,
                product_status="active",
                availability_status="available",
                dietary_tags=[]
            )
            test_session.add(product)
            products.append(product)
        
        await test_session.commit()
        
        # Create subscription
        subtotal = sum(product_prices)
        subscription = Subscription(
            id=uuid7(),
            user_id=test_user.id,
            plan_id="premium",
            status="active",
            price=subtotal + 10.0,  # Add shipping
            currency="USD",
            billing_cycle="monthly",
            subtotal=subtotal,
            shipping_cost=10.0,
            tax_amount=0.0,
            tax_rate=0.0,
            discount_amount=0.0,
            total=subtotal + 10.0
        )
        test_session.add(subscription)
        await test_session.flush()
        
        # Add subscription products
        for product, price in zip(products, product_prices):
            sp = SubscriptionProduct(
                id=uuid7(),
                subscription_id=subscription.id,
                product_id=product.id,
                quantity=1,
                unit_price=price,
                total_price=price
            )
            test_session.add(sp)
        
        await test_session.commit()
        
        service = EnhancedSubscriptionService(test_session)
        
        # Remove products until only one remains
        products_to_remove = num_products - 1
        
        for i in range(products_to_remove):
            # Remove product
            updated_subscription = await service.remove_product(
                subscription_id=subscription.id,
                product_id=products[i].id,
                user_id=test_user.id,
                reason=f"Removal {i+1}"
            )
            
            # Verify subscription remains valid
            assert updated_subscription.status == "active"
            assert updated_subscription.total > 0
            
            # Verify correct number of products remain
            remaining_products_result = await test_session.execute(
                select(SubscriptionProduct).where(
                    SubscriptionProduct.subscription_id == subscription.id
                )
            )
            remaining_products = remaining_products_result.scalars().all()
            active_products = [sp for sp in remaining_products if sp.is_active]
            
            expected_remaining = num_products - (i + 1)
            assert len(active_products) == expected_remaining
            
            # Verify subscription totals are recalculated correctly
            expected_subtotal = sum(product_prices[i+1:])
            # Allow for small floating point differences
            assert abs(updated_subscription.subtotal - expected_subtotal) < 0.01
        
        # Verify final state: exactly one product remains
        final_products_result = await test_session.execute(
            select(SubscriptionProduct).where(
                SubscriptionProduct.subscription_id == subscription.id
            )
        )
        final_products = final_products_result.scalars().all()
        final_active_products = [sp for sp in final_products if sp.is_active]
        
        assert len(final_active_products) == 1
        assert final_active_products[0].product_id == products[-1].id  # Last product should remain

    @pytest.mark.asyncio
    async def test_subscription_validity_with_paused_status(
        self, 
        test_session, 
        test_user, 
        test_category
    ):
        """
        Test that paused subscriptions can still have products removed while maintaining validity
        **Validates: Requirements 1.2**
        """
        # Create products
        products = []
        for i in range(3):
            product = Product(
                id=uuid7(),
                name=f"Paused Product {i+1}",
                slug=f"paused-product-{i+1}",
                category_id=test_category.id,
                supplier_id=test_user.id,
                product_status="active",
                availability_status="available",
                dietary_tags=[]
            )
            test_session.add(product)
            products.append(product)
        
        await test_session.commit()
        
        # Create paused subscription
        subscription = Subscription(
            id=uuid7(),
            user_id=test_user.id,
            plan_id="basic",
            status="paused",  # Paused status
            price=45.0,
            currency="USD",
            billing_cycle="monthly",
            subtotal=40.0,
            shipping_cost=5.0,
            tax_amount=0.0,
            tax_rate=0.0,
            discount_amount=0.0,
            total=45.0,
            paused_at=datetime.utcnow(),
            pause_reason="User requested pause"
        )
        test_session.add(subscription)
        await test_session.flush()
        
        # Add products
        for i, product in enumerate(products):
            sp = SubscriptionProduct(
                id=uuid7(),
                subscription_id=subscription.id,
                product_id=product.id,
                quantity=1,
                unit_price=13.33,
                total_price=13.33
            )
            test_session.add(sp)
        
        await test_session.commit()
        
        service = EnhancedSubscriptionService(test_session)
        
        # Remove product from paused subscription
        updated_subscription = await service.remove_product(
            subscription_id=subscription.id,
            product_id=products[0].id,
            user_id=test_user.id
        )
        
        # Verify subscription remains paused but valid
        assert updated_subscription.status == "paused"
        assert updated_subscription.total > 0
        assert updated_subscription.paused_at is not None
        assert updated_subscription.pause_reason == "User requested pause"
        
        # Verify product was removed
        remaining_products_result = await test_session.execute(
            select(SubscriptionProduct).where(
                SubscriptionProduct.subscription_id == subscription.id
            )
        )
        remaining_products = remaining_products_result.scalars().all()
        active_products = [sp for sp in remaining_products if sp.is_active]
        
        assert len(active_products) == 2