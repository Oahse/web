"""
Property-based tests for validation fallback mechanisms
Feature: subscription-product-management, Property 11: Non-Zero Tax and Shipping Calculations
Feature: subscription-product-management, Property 12: Validation Fallback Application
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
from services.validation_service import ValidationService
from models.validation_rules import TaxValidationRule, ShippingValidationRule
from models.subscriptions import SubscriptionProduct
from models.user import User
from models.product import Product, Category
from decimal import Decimal
from typing import List


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
async def validation_service(test_session):
    """Create validation service with test data"""
    service = ValidationService(test_session)
    
    # Create some test validation rules
    await service.create_validation_rules()
    
    return service


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
def tax_validation_scenario(draw):
    """Generate tax validation scenarios"""
    return {
        "original_amount": draw(st.floats(min_value=0.0, max_value=0.0)),  # Always zero to trigger fallback
        "location_code": draw(st.sampled_from(["US", "US-CA", "GB", "DE", "FR", "UNKNOWN"])),
        "subtotal": draw(st.floats(min_value=10.0, max_value=1000.0)),
    }


@st.composite
def shipping_validation_scenario(draw):
    """Generate shipping validation scenarios"""
    num_products = draw(st.integers(min_value=1, max_value=5))
    return {
        "original_amount": draw(st.floats(min_value=0.0, max_value=0.0)),  # Always zero to trigger fallback
        "num_products": num_products,
        "location_code": draw(st.sampled_from(["US", "GB", "DE", "FR", "UNKNOWN"])),
        "product_quantities": [draw(st.integers(min_value=1, max_value=3)) for _ in range(num_products)]
    }


@st.composite
def fallback_context_scenario(draw):
    """Generate fallback context scenarios"""
    calculation_type = draw(st.sampled_from(["tax", "shipping"]))
    
    if calculation_type == "tax":
        context = {
            "location_code": draw(st.sampled_from(["US", "US-CA", "GB", "UNKNOWN"])),
            "subtotal": draw(st.floats(min_value=5.0, max_value=500.0))
        }
    else:  # shipping
        context = {
            "location_code": draw(st.sampled_from(["US", "GB", "UNKNOWN"])),
            "products": []  # Will be populated in test
        }
    
    return {
        "calculation_type": calculation_type,
        "context": context
    }


class TestValidationFallbackProperties:
    """Property-based tests for validation fallback mechanisms"""

    @given(scenario=tax_validation_scenario())
    @settings(max_examples=10, deadline=15000)
    @pytest.mark.asyncio
    async def test_non_zero_tax_calculations(
        self, 
        validation_service, 
        scenario
    ):
        """
        Property 11: Non-Zero Tax and Shipping Calculations
        For any taxable transaction, the tax calculation should return a non-zero amount,
        applying fallback rates when necessary.
        **Validates: Requirements 4.1, 4.2, 7.3**
        """
        original_amount = Decimal(str(scenario["original_amount"]))
        location_code = scenario["location_code"]
        subtotal = Decimal(str(scenario["subtotal"]))
        
        # Validate tax amount (should trigger fallback since original is zero)
        validated_amount = await validation_service.validate_tax_amount(
            amount=original_amount,
            location_code=location_code,
            subtotal=subtotal
        )
        
        # Property: Tax amount should always be non-zero for taxable transactions
        assert validated_amount > 0, f"Tax amount should be non-zero, got {validated_amount}"
        
        # Property: Validated amount should be reasonable (not excessive)
        max_reasonable_tax = subtotal * Decimal('0.30')  # 30% max tax rate
        assert validated_amount <= max_reasonable_tax, f"Tax amount {validated_amount} exceeds reasonable maximum {max_reasonable_tax}"
        
        # Property: Minimum tax should be applied
        assert validated_amount >= Decimal('0.01'), f"Tax amount {validated_amount} below minimum"
        
        # Property: For known locations, tax should be calculated based on subtotal
        if location_code in ["US", "US-CA", "GB"]:
            # Should be more than just minimum tax for substantial subtotals
            if subtotal > 50:
                assert validated_amount > Decimal('0.01'), f"Tax for substantial subtotal should exceed minimum"

    @given(scenario=shipping_validation_scenario())
    @settings(max_examples=10, deadline=15000)
    @pytest.mark.asyncio
    async def test_non_zero_shipping_calculations(
        self, 
        validation_service,
        test_user,
        test_category,
        scenario
    ):
        """
        Property 11: Non-Zero Tax and Shipping Calculations
        For any physical product shipment, the shipping calculation should return a non-zero amount,
        applying fallback rates when necessary.
        **Validates: Requirements 4.1, 4.2, 7.3**
        """
        original_amount = Decimal(str(scenario["original_amount"]))
        location_code = scenario["location_code"]
        num_products = scenario["num_products"]
        quantities = scenario["product_quantities"]
        
        # Create test products
        products = []
        for i in range(num_products):
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
            
            # Create subscription product
            subscription_product = SubscriptionProduct(
                id=uuid7(),
                subscription_id=uuid7(),  # Dummy subscription ID
                product_id=product.id,
                quantity=quantities[i],
                unit_price=10.0,
                total_price=10.0 * quantities[i]
            )
            products.append(subscription_product)
        
        # Validate shipping amount (should trigger fallback since original is zero)
        validated_amount = await validation_service.validate_shipping_amount(
            amount=original_amount,
            products=products,
            location_code=location_code
        )
        
        # Property: Shipping amount should always be non-zero for physical products
        assert validated_amount > 0, f"Shipping amount should be non-zero, got {validated_amount}"
        
        # Property: Shipping should have reasonable minimum
        assert validated_amount >= Decimal('2.00'), f"Shipping amount {validated_amount} below reasonable minimum"
        
        # Property: Shipping should scale with number of products (roughly)
        expected_min_shipping = Decimal('2.00') + (Decimal('0.50') * num_products)
        # Allow some flexibility in the calculation
        assert validated_amount >= expected_min_shipping * Decimal('0.5'), f"Shipping {validated_amount} too low for {num_products} products"
        
        # Property: Shipping should not be excessively high
        max_reasonable_shipping = Decimal('50.00')  # $50 max for test scenarios
        assert validated_amount <= max_reasonable_shipping, f"Shipping amount {validated_amount} exceeds reasonable maximum"

    @given(scenario=fallback_context_scenario())
    @settings(max_examples=10, deadline=15000)
    @pytest.mark.asyncio
    async def test_validation_fallback_application(
        self, 
        validation_service,
        test_user,
        test_category,
        scenario
    ):
        """
        Property 12: Validation Fallback Application
        For any tax or shipping calculation that would inappropriately return zero,
        the validation service should detect this, log the error, and apply appropriate fallback rates.
        **Validates: Requirements 4.3, 4.4, 4.5**
        """
        calculation_type = scenario["calculation_type"]
        context = scenario["context"]
        
        # For shipping context, add mock products
        if calculation_type == "shipping":
            products = []
            for i in range(2):  # Create 2 test products
                product = Product(
                    id=uuid7(),
                    name=f"Fallback Product {i+1}",
                    slug=f"fallback-product-{i+1}",
                    category_id=test_category.id,
                    supplier_id=test_user.id,
                    product_status="active",
                    availability_status="available",
                    dietary_tags=[]
                )
                
                subscription_product = SubscriptionProduct(
                    id=uuid7(),
                    subscription_id=uuid7(),
                    product_id=product.id,
                    quantity=1,
                    unit_price=15.0,
                    total_price=15.0
                )
                products.append(subscription_product)
            
            context["products"] = products
        
        # Apply fallback rates
        fallback_amount = await validation_service.apply_fallback_rates(
            calculation_type=calculation_type,
            context=context
        )
        
        # Property: Fallback should always return a positive amount
        assert fallback_amount > 0, f"Fallback amount should be positive, got {fallback_amount}"
        
        # Property: Fallback should be reasonable for the calculation type
        if calculation_type == "tax":
            # Tax fallback should be reasonable relative to subtotal
            subtotal = context.get("subtotal", 100)
            max_tax = Decimal(str(subtotal)) * Decimal('0.25')  # 25% max
            assert fallback_amount <= max_tax, f"Tax fallback {fallback_amount} exceeds reasonable maximum"
            assert fallback_amount >= Decimal('0.01'), f"Tax fallback {fallback_amount} below minimum"
        
        elif calculation_type == "shipping":
            # Shipping fallback should be within reasonable bounds
            assert fallback_amount >= Decimal('2.00'), f"Shipping fallback {fallback_amount} below reasonable minimum"
            assert fallback_amount <= Decimal('30.00'), f"Shipping fallback {fallback_amount} exceeds reasonable maximum"
        
        # Property: Known locations should have different rates than unknown locations
        location_code = context.get("location_code", "UNKNOWN")
        if location_code != "UNKNOWN":
            # Known locations should generally have reasonable rates
            if calculation_type == "tax":
                # Known tax locations should have rates between 0.01 and reasonable maximum
                assert fallback_amount >= Decimal('0.01')
            elif calculation_type == "shipping":
                # Known shipping locations should have base rates
                assert fallback_amount >= Decimal('2.00')

    @pytest.mark.asyncio
    async def test_validation_error_recovery(
        self, 
        validation_service
    ):
        """
        Test that validation service handles errors gracefully and provides fallback values
        **Validates: Requirements 4.5**
        """
        # Test with invalid calculation type
        fallback_amount = await validation_service.apply_fallback_rates(
            calculation_type="invalid_type",
            context={}
        )
        
        # Should return minimal fallback
        assert fallback_amount == Decimal('0.01')
        
        # Test with empty context
        tax_fallback = await validation_service.apply_fallback_rates(
            calculation_type="tax",
            context={}
        )
        
        # Should handle missing context gracefully
        assert tax_fallback > 0
        
        shipping_fallback = await validation_service.apply_fallback_rates(
            calculation_type="shipping",
            context={}
        )
        
        # Should handle missing context gracefully
        assert shipping_fallback > 0

    @pytest.mark.asyncio
    async def test_comprehensive_subscription_validation(
        self, 
        validation_service,
        test_user,
        test_category
    ):
        """
        Test comprehensive validation of subscription amounts
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
        """
        # Create test products
        products = []
        for i in range(3):
            product = Product(
                id=uuid7(),
                name=f"Comprehensive Product {i+1}",
                slug=f"comprehensive-product-{i+1}",
                category_id=test_category.id,
                supplier_id=test_user.id,
                product_status="active",
                availability_status="available",
                dietary_tags=[]
            )
            
            subscription_product = SubscriptionProduct(
                id=uuid7(),
                subscription_id=uuid7(),
                product_id=product.id,
                quantity=1,
                unit_price=20.0,
                total_price=20.0
            )
            products.append(subscription_product)
        
        # Test with zero amounts (should trigger fallbacks)
        validation_result = await validation_service.validate_subscription_amounts(
            subscription_id=str(uuid7()),
            tax_amount=Decimal('0.00'),
            shipping_amount=Decimal('0.00'),
            location_code="US-CA",
            subtotal=Decimal('60.00'),
            products=products
        )
        
        # Verify validation result structure
        assert 'subscription_id' in validation_result
        assert 'validated_tax' in validation_result
        assert 'validated_shipping' in validation_result
        assert 'tax_fallback_applied' in validation_result
        assert 'shipping_fallback_applied' in validation_result
        
        # Verify fallbacks were applied
        assert validation_result['tax_fallback_applied'] == True
        assert validation_result['shipping_fallback_applied'] == True
        
        # Verify amounts are non-zero
        assert validation_result['validated_tax'] > 0
        assert validation_result['validated_shipping'] > 0
        
        # Verify amounts are reasonable
        assert validation_result['validated_tax'] <= 60.0 * 0.25  # Max 25% tax
        assert validation_result['validated_shipping'] <= 50.0  # Max $50 shipping

    @pytest.mark.asyncio
    async def test_validation_rules_creation(
        self, 
        validation_service
    ):
        """
        Test creation of validation rules
        **Validates: Requirements 4.3, 4.4**
        """
        # Create custom validation rules
        custom_tax_rules = [
            {
                'location_code': 'TEST',
                'tax_rate': 0.10,
                'minimum_tax': 0.05,
                'description': 'Test tax rule'
            }
        ]
        
        custom_shipping_rules = [
            {
                'location_code': 'TEST',
                'weight_min': 0.0,
                'weight_max': 5.0,
                'base_rate': 8.00,
                'minimum_shipping': 3.00,
                'description': 'Test shipping rule'
            }
        ]
        
        result = await validation_service.create_validation_rules(
            tax_rules=custom_tax_rules,
            shipping_rules=custom_shipping_rules
        )
        
        # Verify rules were created
        assert result['tax_rules'] >= 1
        assert result['shipping_rules'] >= 1
        assert len(result['errors']) == 0
        
        # Test that the rules work
        tax_amount = await validation_service.validate_tax_amount(
            amount=Decimal('0.00'),
            location_code='TEST',
            subtotal=Decimal('100.00')
        )
        
        # Should use the custom rule
        assert tax_amount >= Decimal('0.05')  # Minimum tax from custom rule
        
        # Create mock products for shipping test
        mock_products = [
            SubscriptionProduct(
                id=uuid7(),
                subscription_id=uuid7(),
                product_id=uuid7(),
                quantity=1,
                unit_price=10.0,
                total_price=10.0
            )
        ]
        
        shipping_amount = await validation_service.validate_shipping_amount(
            amount=Decimal('0.00'),
            products=mock_products,
            location_code='TEST'
        )
        
        # Should use the custom rule
        assert shipping_amount >= Decimal('3.00')  # Minimum shipping from custom rule