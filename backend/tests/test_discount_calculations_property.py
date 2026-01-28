"""
Property-based tests for discount calculations and validation
Feature: subscription-product-management
Property 6: Discount Application and Calculation
Property 10: Discount Code Validation
Validates: Requirements 3.1, 3.5
"""
import pytest
import asyncio
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.discount_engine import DiscountEngine, DiscountType
from models.discounts import Discount, SubscriptionDiscount
from models.subscriptions import Subscription
from models.user import User
from core.database import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test database setup
TEST_POSTGRES_DB_URL = "sqlite+aiosqlite:///:memory:"


# Test data generators
@composite
def discount_data(draw):
    """Generate valid discount data for testing"""
    discount_type = draw(st.sampled_from([
        DiscountType.PERCENTAGE.value,
        DiscountType.FIXED_AMOUNT.value,
        DiscountType.FREE_SHIPPING.value
    ]))
    
    if discount_type == DiscountType.PERCENTAGE.value:
        value = draw(st.floats(min_value=1.0, max_value=100.0))
        maximum_discount = draw(st.one_of(
            st.none(),
            st.floats(min_value=1.0, max_value=1000.0)
        ))
    elif discount_type == DiscountType.FIXED_AMOUNT.value:
        value = draw(st.floats(min_value=0.01, max_value=500.0))
        maximum_discount = None
    else:  # FREE_SHIPPING
        value = 0.0
        maximum_discount = None
    
    return {
        'code': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=3, max_size=20)),
        'type': discount_type,
        'value': value,
        'minimum_amount': draw(st.one_of(st.none(), st.floats(min_value=0.01, max_value=100.0))),
        'maximum_discount': maximum_discount,
        'usage_limit': draw(st.one_of(st.none(), st.integers(min_value=1, max_value=1000))),
        'valid_from': datetime.now(timezone.utc) - timedelta(days=1),
        'valid_until': datetime.now(timezone.utc) + timedelta(days=30)
    }


@composite
def subscription_amounts(draw):
    """Generate valid subscription amounts for testing"""
    subtotal = draw(st.floats(min_value=1.0, max_value=1000.0))
    shipping_cost = draw(st.floats(min_value=0.0, max_value=50.0))
    tax_amount = draw(st.floats(min_value=0.0, max_value=subtotal * 0.2))
    
    return {
        'subtotal': Decimal(str(round(subtotal, 2))),
        'shipping_cost': Decimal(str(round(shipping_cost, 2))),
        'tax_amount': Decimal(str(round(tax_amount, 2)))
    }


class TestDiscountCalculationsProperty:
    """Property-based tests for discount calculations"""
    
    @pytest.fixture
    async def db_session(self):
        """Get test database session"""
        engine = create_async_engine(
            TEST_POSTGRES_DB_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
        
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        async with async_session() as session:
            yield session
        
        await engine.dispose()
    
    @pytest.fixture
    async def discount_engine(self, db_session):
        """Create discount engine instance"""
        return DiscountEngine(db_session)
    
    @pytest.fixture
    async def test_user(self, db_session):
        """Create test user"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    
    @given(discount_data(), subscription_amounts())
    @settings(max_examples=10, deadline=2000)
    async def test_property_6_discount_application_and_calculation(
        self,
        discount_data_input,
        amounts,
        db_session,
        discount_engine
    ):
        """
        Property 6: Discount Application and Calculation
        For any valid discount code applied to a subscription, the discount should be 
        validated, calculated correctly, and the subscription total should be updated appropriately.
        **Validates: Requirements 3.1, 3.5**
        """
        # Create discount in database
        discount = Discount(**discount_data_input)
        db_session.add(discount)
        await db_session.commit()
        await db_session.refresh(discount)
        
        # Test discount validation
        validation_result = await discount_engine.validate_discount_code(
            discount_code=discount.code,
            subtotal=amounts['subtotal']
        )
        
        # Property: Valid discount codes should always validate successfully
        assert validation_result.is_valid, f"Valid discount {discount.code} should validate"
        assert validation_result.discount is not None
        assert validation_result.discount.code == discount.code
        
        # Test discount calculation
        calculation_result = await discount_engine.calculate_discount_amount(
            discount=discount,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        # Property: Discount calculations should be mathematically correct
        if discount.type == DiscountType.PERCENTAGE.value:
            expected_discount = amounts['subtotal'] * (Decimal(str(discount.value)) / Decimal('100'))
            if discount.maximum_discount:
                expected_discount = min(expected_discount, Decimal(str(discount.maximum_discount)))
            assert abs(calculation_result.discount_amount - expected_discount) < Decimal('0.01'), \
                f"Percentage discount calculation incorrect: expected {expected_discount}, got {calculation_result.discount_amount}"
        
        elif discount.type == DiscountType.FIXED_AMOUNT.value:
            expected_discount = min(Decimal(str(discount.value)), amounts['subtotal'])
            assert abs(calculation_result.discount_amount - expected_discount) < Decimal('0.01'), \
                f"Fixed amount discount calculation incorrect: expected {expected_discount}, got {calculation_result.discount_amount}"
        
        elif discount.type == DiscountType.FREE_SHIPPING.value:
            expected_discount = amounts['shipping_cost']
            assert abs(calculation_result.discount_amount - expected_discount) < Decimal('0.01'), \
                f"Free shipping discount calculation incorrect: expected {expected_discount}, got {calculation_result.discount_amount}"
        
        # Property: Final total should never be negative
        assert calculation_result.final_total >= Decimal('0'), \
            f"Final total should never be negative: {calculation_result.final_total}"
        
        # Property: Discount amount should never be negative
        assert calculation_result.discount_amount >= Decimal('0'), \
            f"Discount amount should never be negative: {calculation_result.discount_amount}"
        
        # Property: Final total should equal subtotal + shipping + tax - discount (but not less than 0)
        expected_total = max(
            Decimal('0'),
            amounts['subtotal'] + amounts['shipping_cost'] + amounts['tax_amount'] - calculation_result.discount_amount
        )
        assert abs(calculation_result.final_total - expected_total) < Decimal('0.01'), \
            f"Final total calculation incorrect: expected {expected_total}, got {calculation_result.final_total}"
    
    @given(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50))
    @settings(max_examples=5, deadline=1000)
    async def test_property_10_discount_code_validation(
        self,
        random_code,
        db_session,
        discount_engine
    ):
        """
        Property 10: Discount Code Validation
        For any discount code submission, the system should validate it against 
        current promotional rules and reject invalid codes.
        **Validates: Requirements 3.5**
        """
        # Test validation of non-existent discount code
        validation_result = await discount_engine.validate_discount_code(
            discount_code=random_code
        )
        
        # Property: Non-existent discount codes should always be invalid
        assert not validation_result.is_valid, \
            f"Non-existent discount code {random_code} should be invalid"
        assert validation_result.error_message is not None
        assert "Invalid discount code" in validation_result.error_message
        assert validation_result.discount is None
    
    @given(discount_data(), subscription_amounts())
    @settings(max_examples=5, deadline=2000)
    async def test_expired_discount_validation(
        self,
        discount_data_input,
        amounts,
        db_session,
        discount_engine
    ):
        """Test that expired discounts are properly rejected"""
        # Create expired discount
        discount_data_input['valid_until'] = datetime.now(timezone.utc) - timedelta(days=1)
        discount = Discount(**discount_data_input)
        db_session.add(discount)
        await db_session.commit()
        
        # Test validation
        validation_result = await discount_engine.validate_discount_code(
            discount_code=discount.code,
            subtotal=amounts['subtotal']
        )
        
        # Property: Expired discounts should always be invalid
        assert not validation_result.is_valid, \
            f"Expired discount {discount.code} should be invalid"
        assert "expired" in validation_result.error_message.lower()
    
    @given(discount_data(), subscription_amounts())
    @settings(max_examples=5, deadline=2000)
    async def test_minimum_amount_validation(
        self,
        discount_data_input,
        amounts,
        db_session,
        discount_engine
    ):
        """Test minimum amount requirement validation"""
        # Set minimum amount higher than subtotal
        discount_data_input['minimum_amount'] = float(amounts['subtotal']) + 10.0
        discount = Discount(**discount_data_input)
        db_session.add(discount)
        await db_session.commit()
        
        # Test validation
        validation_result = await discount_engine.validate_discount_code(
            discount_code=discount.code,
            subtotal=amounts['subtotal']
        )
        
        # Property: Discounts with unmet minimum amounts should be invalid
        assert not validation_result.is_valid, \
            f"Discount {discount.code} with unmet minimum should be invalid"
        assert "minimum" in validation_result.error_message.lower()
    
    @given(discount_data())
    @settings(max_examples=5, deadline=2000)
    async def test_usage_limit_validation(
        self,
        discount_data_input,
        db_session,
        discount_engine
    ):
        """Test usage limit validation"""
        # Set usage limit to 1 and used count to 1 (exhausted)
        discount_data_input['usage_limit'] = 1
        discount = Discount(**discount_data_input)
        discount.used_count = 1
        db_session.add(discount)
        await db_session.commit()
        
        # Test validation
        validation_result = await discount_engine.validate_discount_code(
            discount_code=discount.code
        )
        
        # Property: Discounts that have reached usage limit should be invalid
        assert not validation_result.is_valid, \
            f"Discount {discount.code} at usage limit should be invalid"
        assert "usage limit" in validation_result.error_message.lower()
    
    @given(st.lists(discount_data(), min_size=2, max_size=3), subscription_amounts())
    @settings(max_examples=5, deadline=5000)
    async def test_optimal_discount_selection(
        self,
        discount_list,
        amounts,
        db_session,
        discount_engine
    ):
        """Test optimal discount selection property"""
        # Create multiple discounts
        discounts = []
        for discount_data_input in discount_list:
            discount = Discount(**discount_data_input)
            db_session.add(discount)
            discounts.append(discount)
        
        await db_session.commit()
        
        # Test optimal selection
        best_discount, best_calculation = await discount_engine.select_optimal_discount(
            available_discounts=discounts,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        if best_discount is not None:
            # Property: Selected discount should provide maximum savings
            for discount in discounts:
                if discount.id != best_discount.id:
                    other_calculation = await discount_engine.calculate_discount_amount(
                        discount=discount,
                        subtotal=amounts['subtotal'],
                        shipping_cost=amounts['shipping_cost'],
                        tax_amount=amounts['tax_amount']
                    )
                    assert best_calculation.discount_amount >= other_calculation.discount_amount, \
                        f"Selected discount should provide maximum savings: {best_calculation.discount_amount} >= {other_calculation.discount_amount}"
    
    @given(discount_data(), subscription_amounts())
    @settings(max_examples=5, deadline=2000)
    async def test_discount_amount_bounds(
        self,
        discount_data_input,
        amounts,
        db_session,
        discount_engine
    ):
        """Test that discount amounts are within reasonable bounds"""
        discount = Discount(**discount_data_input)
        db_session.add(discount)
        await db_session.commit()
        
        calculation_result = await discount_engine.calculate_discount_amount(
            discount=discount,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        # Property: Discount amount should not exceed the total order value
        total_order_value = amounts['subtotal'] + amounts['shipping_cost'] + amounts['tax_amount']
        assert calculation_result.discount_amount <= total_order_value, \
            f"Discount amount {calculation_result.discount_amount} should not exceed total order value {total_order_value}"
        
        # Property: For percentage discounts, amount should not exceed subtotal (unless free shipping)
        if discount.type == DiscountType.PERCENTAGE.value:
            assert calculation_result.discount_amount <= amounts['subtotal'], \
                f"Percentage discount {calculation_result.discount_amount} should not exceed subtotal {amounts['subtotal']}"
        
        # Property: For fixed amount discounts, amount should not exceed the discount value or subtotal
        if discount.type == DiscountType.FIXED_AMOUNT.value:
            assert calculation_result.discount_amount <= Decimal(str(discount.value)), \
                f"Fixed discount {calculation_result.discount_amount} should not exceed discount value {discount.value}"
            assert calculation_result.discount_amount <= amounts['subtotal'], \
                f"Fixed discount {calculation_result.discount_amount} should not exceed subtotal {amounts['subtotal']}"
        
        # Property: For free shipping discounts, amount should equal shipping cost
        if discount.type == DiscountType.FREE_SHIPPING.value:
            assert abs(calculation_result.discount_amount - amounts['shipping_cost']) < Decimal('0.01'), \
                f"Free shipping discount {calculation_result.discount_amount} should equal shipping cost {amounts['shipping_cost']}"


# Async test runner
def run_async_test(coro):
    """Helper to run async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Convert async tests to sync for hypothesis
class TestDiscountCalculationsPropertySync:
    """Synchronous wrapper for property tests"""
    
    def test_property_6_sync(self):
        """Sync wrapper for property 6 test"""
        async def run_test():
            engine = create_async_engine(
                TEST_POSTGRES_DB_URL,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False}
            )
            
            async with engine.begin() as conn:
                await conn.run_sync(BaseModel.metadata.create_all)
            
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            
            async with async_session() as db_session:
                discount_engine = DiscountEngine(db_session)
                test_instance = TestDiscountCalculationsProperty()
                
                # Run a few examples manually since hypothesis doesn't work well with async
                discount_data_examples = [
                    {
                        'code': 'TEST10',
                        'type': DiscountType.PERCENTAGE.value,
                        'value': 10.0,
                        'minimum_amount': None,
                        'maximum_discount': None,
                        'usage_limit': None,
                        'valid_from': datetime.now(timezone.utc) - timedelta(days=1),
                        'valid_until': datetime.now(timezone.utc) + timedelta(days=30)
                    },
                    {
                        'code': 'SAVE20',
                        'type': DiscountType.FIXED_AMOUNT.value,
                        'value': 20.0,
                        'minimum_amount': 50.0,
                        'maximum_discount': None,
                        'usage_limit': 100,
                        'valid_from': datetime.now(timezone.utc) - timedelta(days=1),
                        'valid_until': datetime.now(timezone.utc) + timedelta(days=30)
                    },
                    {
                        'code': 'FREESHIP',
                        'type': DiscountType.FREE_SHIPPING.value,
                        'value': 0.0,
                        'minimum_amount': None,
                        'maximum_discount': None,
                        'usage_limit': None,
                        'valid_from': datetime.now(timezone.utc) - timedelta(days=1),
                        'valid_until': datetime.now(timezone.utc) + timedelta(days=30)
                    }
                ]
                
                amounts_examples = [
                    {
                        'subtotal': Decimal('100.00'),
                        'shipping_cost': Decimal('10.00'),
                        'tax_amount': Decimal('8.00')
                    },
                    {
                        'subtotal': Decimal('75.50'),
                        'shipping_cost': Decimal('5.99'),
                        'tax_amount': Decimal('6.04')
                    }
                ]
                
                for discount_data_input in discount_data_examples:
                    for amounts in amounts_examples:
                        await test_instance.test_property_6_discount_application_and_calculation(
                            discount_data_input, amounts, db_session, discount_engine
                        )
            
            await engine.dispose()
        
        run_async_test(run_test())
    
    def test_property_10_sync(self):
        """Sync wrapper for property 10 test"""
        async def run_test():
            engine = create_async_engine(
                TEST_POSTGRES_DB_URL,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False}
            )
            
            async with engine.begin() as conn:
                await conn.run_sync(BaseModel.metadata.create_all)
            
            async_session = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            
            async with async_session() as db_session:
                discount_engine = DiscountEngine(db_session)
                test_instance = TestDiscountCalculationsProperty()
                
                # Test with some random codes
                random_codes = ['INVALID1', 'NOTFOUND', 'EXPIRED123', 'FAKE']
                
                for code in random_codes:
                    await test_instance.test_property_10_discount_code_validation(
                        code, db_session, discount_engine
                    )
            
            await engine.dispose()
        
        run_async_test(run_test())


if __name__ == "__main__":
    # Run basic tests
    test_sync = TestDiscountCalculationsPropertySync()
    test_sync.test_property_6_sync()
    test_sync.test_property_10_sync()
    print("✅ Discount calculation property tests passed!")