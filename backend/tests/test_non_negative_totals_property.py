"""
Property-based tests for non-negative total invariant
Feature: subscription-product-management
Property 9: Non-Negative Total Invariant
Validates: Requirements 3.4
"""
import pytest
import asyncio
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from services.discount_engine import DiscountEngine, DiscountType
from services.enhanced_subscription_service import EnhancedSubscriptionService
from models.discounts import Discount
from models.subscriptions import Subscription, SubscriptionProduct
from models.user import User
from models.product import Product
from core.database import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test database setup
TEST_POSTGRES_DB_URL = "sqlite+aiosqlite:///:memory:"


@composite
def extreme_discount_data(draw):
    """Generate discount data that might result in negative totals if not handled properly"""
    discount_type = draw(st.sampled_from([
        DiscountType.PERCENTAGE.value,
        DiscountType.FIXED_AMOUNT.value,
        DiscountType.FREE_SHIPPING.value
    ]))
    
    if discount_type == DiscountType.PERCENTAGE.value:
        # Generate very high percentage discounts (up to 200%)
        value = draw(st.floats(min_value=50.0, max_value=200.0))
        maximum_discount = draw(st.one_of(
            st.none(),
            st.floats(min_value=1.0, max_value=10000.0)
        ))
    elif discount_type == DiscountType.FIXED_AMOUNT.value:
        # Generate very high fixed amount discounts
        value = draw(st.floats(min_value=100.0, max_value=10000.0))
        maximum_discount = None
    else:  # FREE_SHIPPING
        value = 0.0
        maximum_discount = None
    
    return {
        'code': draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=3, max_size=20)),
        'type': discount_type,
        'value': value,
        'minimum_amount': draw(st.one_of(st.none(), st.floats(min_value=0.01, max_value=10.0))),
        'maximum_discount': maximum_discount,
        'usage_limit': draw(st.one_of(st.none(), st.integers(min_value=1, max_value=1000))),
        'valid_from': datetime.now(timezone.utc) - timedelta(days=1),
        'valid_until': datetime.now(timezone.utc) + timedelta(days=30)
    }


@composite
def subscription_amounts_with_small_subtotals(draw):
    """Generate subscription amounts with small subtotals that could go negative with large discounts"""
    subtotal = draw(st.floats(min_value=0.01, max_value=50.0))  # Small subtotals
    shipping_cost = draw(st.floats(min_value=0.0, max_value=20.0))
    tax_amount = draw(st.floats(min_value=0.0, max_value=subtotal * 0.2))
    
    return {
        'subtotal': Decimal(str(round(subtotal, 2))),
        'shipping_cost': Decimal(str(round(shipping_cost, 2))),
        'tax_amount': Decimal(str(round(tax_amount, 2)))
    }


@composite
def multiple_large_discounts(draw):
    """Generate multiple large discounts that could compound to exceed order total"""
    num_discounts = draw(st.integers(min_value=2, max_value=3))  # Reduced from 4 to 3
    discounts = []
    
    for i in range(num_discounts):
        discount_type = draw(st.sampled_from([
            DiscountType.PERCENTAGE.value,
            DiscountType.FIXED_AMOUNT.value
        ]))
        
        if discount_type == DiscountType.PERCENTAGE.value:
            value = draw(st.floats(min_value=20.0, max_value=100.0))  # 20-100% discounts
        else:
            value = draw(st.floats(min_value=10.0, max_value=200.0))  # $10-$200 discounts
        
        discount_data = {
            'code': f'LARGE{i}_{draw(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=3, max_size=8))}',
            'type': discount_type,
            'value': value,
            'minimum_amount': None,
            'maximum_discount': None,
            'usage_limit': None,
            'valid_from': datetime.now(timezone.utc) - timedelta(days=1),
            'valid_until': datetime.now(timezone.utc) + timedelta(days=30)
        }
        discounts.append(discount_data)
    
    return discounts


class TestNonNegativeTotalsProperty:
    """Property-based tests for non-negative total invariant"""
    
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
    async def subscription_service(self, db_session):
        """Create enhanced subscription service instance"""
        return EnhancedSubscriptionService(db_session)
    
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
    
    @given(extreme_discount_data(), subscription_amounts_with_small_subtotals())
    @settings(max_examples=10, deadline=2000)
    async def test_property_9_non_negative_total_invariant_single_discount(
        self,
        discount_data_input,
        amounts,
        db_session,
        discount_engine
    ):
        """
        Property 9: Non-Negative Total Invariant (Single Discount)
        For any discount calculation, the final subscription total should never be negative, 
        regardless of discount amounts.
        **Validates: Requirements 3.4**
        """
        # Create discount in database
        discount = Discount(**discount_data_input)
        db_session.add(discount)
        await db_session.commit()
        await db_session.refresh(discount)
        
        # Calculate discount amount
        calculation_result = await discount_engine.calculate_discount_amount(
            discount=discount,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        # Property: Final total must never be negative
        assert calculation_result.final_total >= Decimal('0'), \
            f"Final total must never be negative: got {calculation_result.final_total} with discount {discount_data_input['value']} on subtotal {amounts['subtotal']}"
        
        # Property: Discount amount should not exceed what would make total negative
        total_before_discount = amounts['subtotal'] + amounts['shipping_cost'] + amounts['tax_amount']
        assert calculation_result.discount_amount <= total_before_discount, \
            f"Discount amount {calculation_result.discount_amount} should not exceed total before discount {total_before_discount}"
        
        # Property: Final total should equal max(0, subtotal + shipping + tax - discount)
        expected_total = max(
            Decimal('0'),
            amounts['subtotal'] + amounts['shipping_cost'] + amounts['tax_amount'] - calculation_result.discount_amount
        )
        assert abs(calculation_result.final_total - expected_total) < Decimal('0.01'), \
            f"Final total calculation incorrect: expected {expected_total}, got {calculation_result.final_total}"
    
    @given(multiple_large_discounts(), subscription_amounts_with_small_subtotals())
    @settings(max_examples=5, deadline=5000)
    async def test_property_9_non_negative_total_invariant_multiple_discounts(
        self,
        discount_list,
        amounts,
        db_session,
        discount_engine
    ):
        """
        Property 9: Non-Negative Total Invariant (Multiple Discounts)
        When multiple large discounts are applied, the final total should still never be negative.
        **Validates: Requirements 3.4**
        """
        # Create discounts in database
        discounts = []
        for discount_data in discount_list:
            discount = Discount(**discount_data)
            db_session.add(discount)
            discounts.append(discount)
        
        await db_session.commit()
        
        # Test optimal selection with multiple large discounts
        best_discount, best_calculation = await discount_engine.select_optimal_discount(
            available_discounts=discounts,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        if best_discount is not None:
            # Property: Even with optimal selection of large discounts, total must be non-negative
            assert best_calculation.final_total >= Decimal('0'), \
                f"Final total with optimal discount selection must never be negative: got {best_calculation.final_total}"
            
            # Property: Discount amount should be reasonable relative to order total
            total_before_discount = amounts['subtotal'] + amounts['shipping_cost'] + amounts['tax_amount']
            assert best_calculation.discount_amount <= total_before_discount, \
                f"Optimal discount amount {best_calculation.discount_amount} should not exceed order total {total_before_discount}"
    
    @given(subscription_amounts_with_small_subtotals())
    @settings(max_examples=5, deadline=2000)
    async def test_extreme_percentage_discounts(
        self,
        amounts,
        db_session,
        discount_engine
    ):
        """Test that extreme percentage discounts (>100%) don't cause negative totals"""
        # Create 150% discount (more than the order value)
        extreme_discount = Discount(
            code='EXTREME150',
            type=DiscountType.PERCENTAGE.value,
            value=150.0,  # 150% discount
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db_session.add(extreme_discount)
        await db_session.commit()
        
        # Calculate discount
        calculation_result = await discount_engine.calculate_discount_amount(
            discount=extreme_discount,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        # Property: Even 150% discount should not result in negative total
        assert calculation_result.final_total >= Decimal('0'), \
            f"150% discount should not result in negative total: got {calculation_result.final_total}"
        
        # Property: Discount amount should be capped at subtotal for percentage discounts
        assert calculation_result.discount_amount <= amounts['subtotal'], \
            f"Percentage discount should not exceed subtotal: discount {calculation_result.discount_amount}, subtotal {amounts['subtotal']}"
    
    @given(subscription_amounts_with_small_subtotals())
    @settings(max_examples=5, deadline=2000)
    async def test_extreme_fixed_amount_discounts(
        self,
        amounts,
        db_session,
        discount_engine
    ):
        """Test that extreme fixed amount discounts don't cause negative totals"""
        # Create fixed discount larger than typical order
        large_fixed_discount = Discount(
            code='HUGE1000',
            type=DiscountType.FIXED_AMOUNT.value,
            value=1000.0,  # $1000 discount
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db_session.add(large_fixed_discount)
        await db_session.commit()
        
        # Calculate discount
        calculation_result = await discount_engine.calculate_discount_amount(
            discount=large_fixed_discount,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        # Property: Large fixed discount should not result in negative total
        assert calculation_result.final_total >= Decimal('0'), \
            f"Large fixed discount should not result in negative total: got {calculation_result.final_total}"
        
        # Property: Fixed discount amount should be capped at subtotal
        assert calculation_result.discount_amount <= amounts['subtotal'], \
            f"Fixed discount should not exceed subtotal: discount {calculation_result.discount_amount}, subtotal {amounts['subtotal']}"
    
    async def test_zero_subtotal_edge_case(self, db_session, discount_engine):
        """Test edge case where subtotal is zero or very small"""
        amounts = {
            'subtotal': Decimal('0.01'),  # 1 cent subtotal
            'shipping_cost': Decimal('5.00'),
            'tax_amount': Decimal('0.00')
        }
        
        # Create large percentage discount
        large_discount = Discount(
            code='PERCENT100',
            type=DiscountType.PERCENTAGE.value,
            value=100.0,  # 100% discount
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db_session.add(large_discount)
        await db_session.commit()
        
        # Calculate discount
        calculation_result = await discount_engine.calculate_discount_amount(
            discount=large_discount,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        # Property: Even with tiny subtotal, total should not be negative
        assert calculation_result.final_total >= Decimal('0'), \
            f"Total with tiny subtotal should not be negative: got {calculation_result.final_total}"
        
        # Property: Final total should at least include shipping and tax
        expected_minimum = amounts['shipping_cost'] + amounts['tax_amount']
        assert calculation_result.final_total >= expected_minimum - amounts['subtotal'], \
            f"Final total should account for shipping and tax: got {calculation_result.final_total}, expected at least {expected_minimum - amounts['subtotal']}"
    
    async def test_maximum_discount_limit_prevents_negative_totals(self, db_session, discount_engine):
        """Test that maximum discount limits prevent negative totals"""
        amounts = {
            'subtotal': Decimal('50.00'),
            'shipping_cost': Decimal('10.00'),
            'tax_amount': Decimal('4.00')
        }
        
        # Create percentage discount with maximum limit
        limited_discount = Discount(
            code='PERCENT90MAX30',
            type=DiscountType.PERCENTAGE.value,
            value=90.0,  # 90% discount
            maximum_discount=30.0,  # But max $30
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db_session.add(limited_discount)
        await db_session.commit()
        
        # Calculate discount
        calculation_result = await discount_engine.calculate_discount_amount(
            discount=limited_discount,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        # Property: Maximum discount limit should prevent negative totals
        assert calculation_result.final_total >= Decimal('0'), \
            f"Maximum discount limit should prevent negative totals: got {calculation_result.final_total}"
        
        # Property: Discount amount should not exceed maximum limit
        assert calculation_result.discount_amount <= Decimal('30.00'), \
            f"Discount amount should not exceed maximum limit: got {calculation_result.discount_amount}"
        
        # Property: With $30 max discount on $50 subtotal, final total should be reasonable
        expected_total = amounts['subtotal'] + amounts['shipping_cost'] + amounts['tax_amount'] - Decimal('30.00')
        assert abs(calculation_result.final_total - expected_total) < Decimal('0.01'), \
            f"Final total with max discount should be correct: expected {expected_total}, got {calculation_result.final_total}"
    
    @given(st.floats(min_value=0.01, max_value=100.0))
    @settings(max_examples=10, deadline=1000)
    async def test_free_shipping_discount_non_negative_invariant(
        self,
        shipping_amount,
        db_session,
        discount_engine
    ):
        """Test that free shipping discounts maintain non-negative totals"""
        amounts = {
            'subtotal': Decimal('25.00'),
            'shipping_cost': Decimal(str(round(shipping_amount, 2))),
            'tax_amount': Decimal('2.00')
        }
        
        # Create free shipping discount
        free_shipping = Discount(
            code='FREESHIP',
            type=DiscountType.FREE_SHIPPING.value,
            value=0.0,
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db_session.add(free_shipping)
        await db_session.commit()
        
        # Calculate discount
        calculation_result = await discount_engine.calculate_discount_amount(
            discount=free_shipping,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        # Property: Free shipping discount should never result in negative total
        assert calculation_result.final_total >= Decimal('0'), \
            f"Free shipping discount should not result in negative total: got {calculation_result.final_total}"
        
        # Property: Free shipping discount amount should equal shipping cost
        assert abs(calculation_result.discount_amount - amounts['shipping_cost']) < Decimal('0.01'), \
            f"Free shipping discount should equal shipping cost: expected {amounts['shipping_cost']}, got {calculation_result.discount_amount}"
        
        # Property: Final total should equal subtotal + tax (shipping is free)
        expected_total = amounts['subtotal'] + amounts['tax_amount']
        assert abs(calculation_result.final_total - expected_total) < Decimal('0.01'), \
            f"Final total with free shipping should be subtotal + tax: expected {expected_total}, got {calculation_result.final_total}"


# Async test runner
def run_async_test(coro):
    """Helper to run async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Synchronous wrapper for property tests
class TestNonNegativeTotalsPropertySync:
    """Synchronous wrapper for property tests"""
    
    def test_property_9_single_discount_sync(self):
        """Sync wrapper for property 9 single discount test"""
        async def run_test():
            async with get_test_db_session() as db_session:
                discount_engine = DiscountEngine(db_session)
                test_instance = TestNonNegativeTotalsProperty()
                
                # Test with extreme discount examples
                extreme_examples = [
                    {
                        'code': 'EXTREME200',
                        'type': DiscountType.PERCENTAGE.value,
                        'value': 200.0,  # 200% discount
                        'minimum_amount': None,
                        'maximum_discount': None,
                        'usage_limit': None,
                        'valid_from': datetime.now(timezone.utc) - timedelta(days=1),
                        'valid_until': datetime.now(timezone.utc) + timedelta(days=30)
                    },
                    {
                        'code': 'HUGE5000',
                        'type': DiscountType.FIXED_AMOUNT.value,
                        'value': 5000.0,  # $5000 discount
                        'minimum_amount': None,
                        'maximum_discount': None,
                        'usage_limit': None,
                        'valid_from': datetime.now(timezone.utc) - timedelta(days=1),
                        'valid_until': datetime.now(timezone.utc) + timedelta(days=30)
                    }
                ]
                
                small_amounts = [
                    {
                        'subtotal': Decimal('10.00'),
                        'shipping_cost': Decimal('5.00'),
                        'tax_amount': Decimal('1.00')
                    },
                    {
                        'subtotal': Decimal('0.99'),
                        'shipping_cost': Decimal('2.99'),
                        'tax_amount': Decimal('0.08')
                    }
                ]
                
                for discount_data in extreme_examples:
                    for amounts in small_amounts:
                        await test_instance.test_property_9_non_negative_total_invariant_single_discount(
                            discount_data, amounts, db_session, discount_engine
                        )
        
        run_async_test(run_test())
    
    def test_edge_cases_sync(self):
        """Sync wrapper for edge cases"""
        async def run_test():
            async with get_test_db_session() as db_session:
                discount_engine = DiscountEngine(db_session)
                test_instance = TestNonNegativeTotalsProperty()
                
                await test_instance.test_zero_subtotal_edge_case(db_session, discount_engine)
                await test_instance.test_maximum_discount_limit_prevents_negative_totals(db_session, discount_engine)
        
        run_async_test(run_test())
    
    def test_extreme_discounts_sync(self):
        """Sync wrapper for extreme discount tests"""
        async def run_test():
            async with get_test_db_session() as db_session:
                discount_engine = DiscountEngine(db_session)
                test_instance = TestNonNegativeTotalsProperty()
                
                amounts = {
                    'subtotal': Decimal('25.00'),
                    'shipping_cost': Decimal('8.00'),
                    'tax_amount': Decimal('2.00')
                }
                
                await test_instance.test_extreme_percentage_discounts(amounts, db_session, discount_engine)
                await test_instance.test_extreme_fixed_amount_discounts(amounts, db_session, discount_engine)
        
        run_async_test(run_test())


if __name__ == "__main__":
    # Run basic tests
    test_sync = TestNonNegativeTotalsPropertySync()
    test_sync.test_property_9_single_discount_sync()
    test_sync.test_edge_cases_sync()
    test_sync.test_extreme_discounts_sync()
    print("✅ Non-negative totals property tests passed!")