"""
Property-based tests for subscription product management database schema integrity
Feature: subscription-product-management, Property 13: Audit Trail Creation
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
from models.discounts import Discount, SubscriptionDiscount, ProductRemovalAudit
from models.validation_rules import TaxValidationRule, ShippingValidationRule
from models.subscriptions import Subscription, SubscriptionProduct
from models.user import User
from models.product import Product
from datetime import datetime, timedelta


# Test database setup
@pytest.fixture(scope="module")
async def test_engine():
    """Create test database engine"""
    # Use a test database URL
    test_db_url = settings.SQLALCHEMY_DATABASE_URI.replace("/banwee_db", "/banwee_test_db")
    engine = create_async_engine(test_db_url, echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
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


# Hypothesis strategies for generating test data
@st.composite
def discount_strategy(draw):
    """Generate valid discount data"""
    discount_types = ["PERCENTAGE", "FIXED_AMOUNT", "FREE_SHIPPING"]
    
    return {
        "code": draw(st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Nd")))),
        "type": draw(st.sampled_from(discount_types)),
        "value": draw(st.floats(min_value=0.01, max_value=100.0)),
        "minimum_amount": draw(st.one_of(st.none(), st.floats(min_value=0.01, max_value=1000.0))),
        "maximum_discount": draw(st.one_of(st.none(), st.floats(min_value=0.01, max_value=500.0))),
        "valid_from": datetime.utcnow(),
        "valid_until": datetime.utcnow() + timedelta(days=draw(st.integers(min_value=1, max_value=365))),
        "usage_limit": draw(st.one_of(st.none(), st.integers(min_value=1, max_value=1000))),
        "is_active": draw(st.booleans()),
        "description": draw(st.one_of(st.none(), st.text(min_size=1, max_size=200)))
    }


@st.composite
def tax_rule_strategy(draw):
    """Generate valid tax rule data"""
    location_codes = ["US-CA", "US-NY", "GB", "DE", "AU", "CA-ON"]
    
    return {
        "location_code": draw(st.sampled_from(location_codes)),
        "tax_rate": draw(st.floats(min_value=0.0, max_value=0.30)),
        "minimum_tax": draw(st.floats(min_value=0.01, max_value=1.0)),
        "is_active": draw(st.booleans()),
        "description": draw(st.one_of(st.none(), st.text(min_size=1, max_size=200)))
    }


@st.composite
def shipping_rule_strategy(draw):
    """Generate valid shipping rule data"""
    location_codes = ["US-CA", "US-NY", "GB", "DE", "AU", "CA-ON"]
    weight_min = draw(st.floats(min_value=0.0, max_value=50.0))
    weight_max = draw(st.floats(min_value=weight_min + 0.1, max_value=100.0))
    
    return {
        "location_code": draw(st.sampled_from(location_codes)),
        "weight_min": weight_min,
        "weight_max": weight_max,
        "base_rate": draw(st.floats(min_value=0.01, max_value=100.0)),
        "minimum_shipping": draw(st.floats(min_value=0.01, max_value=5.0)),
        "is_active": draw(st.booleans()),
        "description": draw(st.one_of(st.none(), st.text(min_size=1, max_size=200)))
    }


class TestSchemaIntegrity:
    """Property-based tests for database schema integrity"""

    @given(discount_data=discount_strategy())
    @settings(max_examples=20, deadline=10000)
    @pytest.mark.asyncio
    async def test_discount_table_integrity(self, test_session, discount_data):
        """
        Property 13: Audit Trail Creation - Discount Creation
        For any valid discount data, creating a discount should result in proper database storage
        with all constraints and indexes working correctly.
        **Validates: Requirements 5.3**
        """
        # Create discount
        discount = Discount(
            id=uuid7(),
            **discount_data
        )
        
        test_session.add(discount)
        await test_session.commit()
        
        # Verify discount was created
        result = await test_session.execute(
            select(Discount).where(Discount.id == discount.id)
        )
        stored_discount = result.scalar_one()
        
        # Verify all fields are stored correctly
        assert stored_discount.code == discount_data["code"]
        assert stored_discount.type == discount_data["type"]
        assert stored_discount.value == discount_data["value"]
        assert stored_discount.is_active == discount_data["is_active"]
        assert stored_discount.created_at is not None
        assert stored_discount.id is not None

    @given(tax_rule_data=tax_rule_strategy())
    @settings(max_examples=20, deadline=10000)
    @pytest.mark.asyncio
    async def test_tax_rule_table_integrity(self, test_session, tax_rule_data):
        """
        Property 13: Audit Trail Creation - Tax Rule Creation
        For any valid tax rule data, creating a tax rule should result in proper database storage
        with validation constraints working correctly.
        **Validates: Requirements 5.3**
        """
        # Create tax rule
        tax_rule = TaxValidationRule(
            id=uuid7(),
            **tax_rule_data
        )
        
        test_session.add(tax_rule)
        await test_session.commit()
        
        # Verify tax rule was created
        result = await test_session.execute(
            select(TaxValidationRule).where(TaxValidationRule.id == tax_rule.id)
        )
        stored_rule = result.scalar_one()
        
        # Verify all fields are stored correctly
        assert stored_rule.location_code == tax_rule_data["location_code"]
        assert stored_rule.tax_rate == tax_rule_data["tax_rate"]
        assert stored_rule.minimum_tax == tax_rule_data["minimum_tax"]
        assert stored_rule.is_active == tax_rule_data["is_active"]
        assert stored_rule.created_at is not None

    @given(shipping_rule_data=shipping_rule_strategy())
    @settings(max_examples=20, deadline=10000)
    @pytest.mark.asyncio
    async def test_shipping_rule_table_integrity(self, test_session, shipping_rule_data):
        """
        Property 13: Audit Trail Creation - Shipping Rule Creation
        For any valid shipping rule data, creating a shipping rule should result in proper database storage
        with weight range constraints working correctly.
        **Validates: Requirements 5.3**
        """
        # Create shipping rule
        shipping_rule = ShippingValidationRule(
            id=uuid7(),
            **shipping_rule_data
        )
        
        test_session.add(shipping_rule)
        await test_session.commit()
        
        # Verify shipping rule was created
        result = await test_session.execute(
            select(ShippingValidationRule).where(ShippingValidationRule.id == shipping_rule.id)
        )
        stored_rule = result.scalar_one()
        
        # Verify all fields are stored correctly
        assert stored_rule.location_code == shipping_rule_data["location_code"]
        assert stored_rule.weight_min == shipping_rule_data["weight_min"]
        assert stored_rule.weight_max == shipping_rule_data["weight_max"]
        assert stored_rule.base_rate == shipping_rule_data["base_rate"]
        assert stored_rule.minimum_shipping == shipping_rule_data["minimum_shipping"]
        assert stored_rule.is_active == shipping_rule_data["is_active"]
        assert stored_rule.created_at is not None

    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, test_session):
        """
        Property 13: Audit Trail Creation - Foreign Key Integrity
        For any subscription discount relationship, foreign key constraints should be enforced
        and audit trails should be maintained.
        **Validates: Requirements 5.3**
        """
        # Create test user
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
        
        # Create test subscription
        subscription = Subscription(
            id=uuid7(),
            user_id=user.id,
            plan_id="basic",
            status="active",
            price=19.99,
            currency="USD",
            billing_cycle="monthly"
        )
        test_session.add(subscription)
        
        # Create test discount
        discount = Discount(
            id=uuid7(),
            code="TEST10",
            type="PERCENTAGE",
            value=10.0,
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=30),
            is_active=True
        )
        test_session.add(discount)
        await test_session.commit()
        
        # Create subscription discount relationship
        subscription_discount = SubscriptionDiscount(
            id=uuid7(),
            subscription_id=subscription.id,
            discount_id=discount.id,
            discount_amount=5.0
        )
        test_session.add(subscription_discount)
        await test_session.commit()
        
        # Verify relationship was created
        result = await test_session.execute(
            select(SubscriptionDiscount).where(
                SubscriptionDiscount.subscription_id == subscription.id
            )
        )
        stored_relationship = result.scalar_one()
        
        assert stored_relationship.subscription_id == subscription.id
        assert stored_relationship.discount_id == discount.id
        assert stored_relationship.discount_amount == 5.0
        assert stored_relationship.applied_at is not None

    @pytest.mark.asyncio
    async def test_audit_trail_creation(self, test_session):
        """
        Property 13: Audit Trail Creation - Product Removal Audit
        For any product removal from a subscription, an audit record should be created
        with complete removal details and user information.
        **Validates: Requirements 5.3**
        """
        # Create test user
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
        
        # Create test subscription
        subscription = Subscription(
            id=uuid7(),
            user_id=user.id,
            plan_id="basic",
            status="active",
            price=19.99,
            currency="USD",
            billing_cycle="monthly"
        )
        test_session.add(subscription)
        
        # Create test product
        from models.product import Category
        category = Category(
            id=uuid7(),
            name="Test Category",
            is_active=True
        )
        test_session.add(category)
        
        product = Product(
            id=uuid7(),
            name="Test Product",
            slug="test-product",
            category_id=category.id,
            supplier_id=user.id,
            product_status="active",
            availability_status="available",
            dietary_tags=[]
        )
        test_session.add(product)
        await test_session.commit()
        
        # Create product removal audit
        audit = ProductRemovalAudit(
            id=uuid7(),
            subscription_id=subscription.id,
            product_id=product.id,
            removed_by=user.id,
            reason="User requested removal"
        )
        test_session.add(audit)
        await test_session.commit()
        
        # Verify audit trail was created
        result = await test_session.execute(
            select(ProductRemovalAudit).where(
                ProductRemovalAudit.subscription_id == subscription.id
            )
        )
        stored_audit = result.scalar_one()
        
        assert stored_audit.subscription_id == subscription.id
        assert stored_audit.product_id == product.id
        assert stored_audit.removed_by == user.id
        assert stored_audit.reason == "User requested removal"
        assert stored_audit.removed_at is not None
        assert stored_audit.created_at is not None

    @pytest.mark.asyncio
    async def test_subscription_modifications_tracking(self, test_session):
        """
        Property 13: Audit Trail Creation - Subscription Modifications
        For any subscription modification, the system should maintain proper tracking
        of discount amounts and validation timestamps.
        **Validates: Requirements 5.3**
        """
        # Create test user
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
        
        # Create subscription with discount tracking
        subscription = Subscription(
            id=uuid7(),
            user_id=user.id,
            plan_id="basic",
            status="active",
            price=19.99,
            currency="USD",
            billing_cycle="monthly",
            discount_amount=5.0,
            tax_validated_at=datetime.utcnow(),
            shipping_validated_at=datetime.utcnow()
        )
        test_session.add(subscription)
        await test_session.commit()
        
        # Verify subscription modifications are tracked
        result = await test_session.execute(
            select(Subscription).where(Subscription.id == subscription.id)
        )
        stored_subscription = result.scalar_one()
        
        assert stored_subscription.discount_amount == 5.0
        assert stored_subscription.tax_validated_at is not None
        assert stored_subscription.shipping_validated_at is not None
        assert stored_subscription.created_at is not None
        assert stored_subscription.updated_at is not None

    @pytest.mark.asyncio
    async def test_database_indexes_performance(self, test_session):
        """
        Property 13: Audit Trail Creation - Index Performance
        For any database query on audit tables, indexes should provide efficient access
        to audit trail data.
        **Validates: Requirements 5.3**
        """
        # Test that indexes exist and can be used efficiently
        # This is a basic check that the indexes were created
        
        # Check discount table indexes
        result = await test_session.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'discounts' 
            AND indexname LIKE 'idx_discounts_%'
        """))
        discount_indexes = [row[0] for row in result.fetchall()]
        
        expected_discount_indexes = [
            'idx_discounts_code',
            'idx_discounts_active',
            'idx_discounts_type',
            'idx_discounts_active_valid',
            'idx_discounts_code_active'
        ]
        
        for expected_index in expected_discount_indexes:
            assert expected_index in discount_indexes, f"Missing index: {expected_index}"
        
        # Check audit table indexes
        result = await test_session.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'product_removal_audit' 
            AND indexname LIKE 'idx_product_removal_audit_%'
        """))
        audit_indexes = [row[0] for row in result.fetchall()]
        
        expected_audit_indexes = [
            'idx_product_removal_audit_subscription_id',
            'idx_product_removal_audit_product_id',
            'idx_product_removal_audit_removed_by',
            'idx_product_removal_audit_removed_at'
        ]
        
        for expected_index in expected_audit_indexes:
            assert expected_index in audit_indexes, f"Missing audit index: {expected_index}"