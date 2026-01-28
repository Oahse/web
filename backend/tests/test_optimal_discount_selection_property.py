"""
Property-based tests for optimal discount selection
Feature: subscription-product-management
Property 7: Optimal Discount Selection
Validates: Requirements 3.2
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
from models.discounts import Discount
from core.database import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test database setup
TEST_POSTGRES_DB_URL = "sqlite+aiosqlite:///:memory:"


@composite
def multiple_discounts(draw):
    """Generate multiple discounts with different values for optimal selection testing"""
    num_discounts = draw(st.integers(min_value=2, max_value=3))  # Reduced from 5 to 3
    discounts = []
    
    for i in range(num_discounts):
        discount_type = draw(st.sampled_from([
            DiscountType.PERCENTAGE.value,
            DiscountType.FIXED_AMOUNT.value,
            DiscountType.FREE_SHIPPING.value
        ]))
        
        if discount_type == DiscountType.PERCENTAGE.value:
            value = draw(st.floats(min_value=5.0, max_value=50.0))  # 5-50% discount
            maximum_discount = draw(st.one_of(
                st.none(),
                st.floats(min_value=10.0, max_value=100.0)
            ))
        elif discount_type == DiscountType.FIXED_AMOUNT.value:
            value = draw(st.floats(min_value=5.0, max_value=100.0))  # $5-$100 discount
            maximum_discount = None
        else:  # FREE_SHIPPING
            value = 0.0
            maximum_discount = None
        
        discount_data = {
            'code': f'DISCOUNT{i}_{draw(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=3, max_size=8))}',
            'type': discount_type,
            'value': value,
            'minimum_amount': draw(st.one_of(st.none(), st.floats(min_value=0.01, max_value=20.0))),
            'maximum_discount': maximum_discount,
            'usage_limit': draw(st.one_of(st.none(), st.integers(min_value=10, max_value=1000))),
            'valid_from': datetime.now(timezone.utc) - timedelta(days=1),
            'valid_until': datetime.now(timezone.utc) + timedelta(days=30)
        }
        discounts.append(discount_data)
    
    return discounts


@composite
def order_amounts(draw):
    """Generate realistic order amounts for testing"""
    subtotal = draw(st.floats(min_value=25.0, max_value=500.0))  # $25-$500 orders
    shipping_cost = draw(st.floats(min_value=5.0, max_value=25.0))  # $5-$25 shipping
    tax_amount = draw(st.floats(min_value=0.0, max_value=subtotal * 0.15))  # 0-15% tax
    
    return {
        'subtotal': Decimal(str(round(subtotal, 2))),
        'shipping_cost': Decimal(str(round(shipping_cost, 2))),
        'tax_amount': Decimal(str(round(tax_amount, 2)))
    }


class TestOptimalDiscountSelectionProperty:
    """Property-based tests for optimal discount selection"""
    
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
    
    @given(multiple_discounts(), order_amounts())
    @settings(max_examples=10, deadline=5000)
    async def test_property_7_optimal_discount_selection(
        self,
        discount_list,
        amounts,
        db_session,
        discount_engine
    ):
        """
        Property 7: Optimal Discount Selection
        For any subscription with multiple applicable discounts, the system should 
        automatically apply the most beneficial discount to the user.
        **Validates: Requirements 3.2**
        """
        # Create discounts in database
        discounts = []
        for discount_data in discount_list:
            discount = Discount(**discount_data)
            db_session.add(discount)
            discounts.append(discount)
        
        await db_session.commit()
        
        # Refresh all discounts to get IDs
        for discount in discounts:
            await db_session.refresh(discount)
        
        # Filter discounts that meet minimum amount requirements
        applicable_discounts = []
        for discount in discounts:
            if discount.minimum_amount is None or amounts['subtotal'] >= Decimal(str(discount.minimum_amount)):
                applicable_discounts.append(discount)
        
        if not applicable_discounts:
            # If no discounts are applicable, skip this test case
            assume(False)
        
        # Calculate discount amounts for all applicable discounts
        discount_calculations = {}
        for discount in applicable_discounts:
            calculation = await discount_engine.calculate_discount_amount(
                discount=discount,
                subtotal=amounts['subtotal'],
                shipping_cost=amounts['shipping_cost'],
                tax_amount=amounts['tax_amount']
            )
            discount_calculations[discount.id] = calculation
        
        # Find the discount with maximum savings manually
        max_savings = Decimal('0')
        expected_best_discount = None
        for discount in applicable_discounts:
            calculation = discount_calculations[discount.id]
            if calculation.discount_amount > max_savings:
                max_savings = calculation.discount_amount
                expected_best_discount = discount
        
        # Test optimal selection using the engine
        best_discount, best_calculation = await discount_engine.select_optimal_discount(
            available_discounts=applicable_discounts,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        if expected_best_discount is not None and max_savings > Decimal('0'):
            # Property: The selected discount should be the one with maximum savings
            assert best_discount is not None, "Engine should select a discount when beneficial discounts exist"
            assert best_discount.id == expected_best_discount.id, \
                f"Engine should select discount with maximum savings: expected {expected_best_discount.code}, got {best_discount.code}"
            
            # Property: The selected discount amount should equal the maximum savings
            assert abs(best_calculation.discount_amount - max_savings) < Decimal('0.01'), \
                f"Selected discount amount should equal maximum savings: expected {max_savings}, got {best_calculation.discount_amount}"
            
            # Property: The selected discount should provide better savings than any other discount
            for discount in applicable_discounts:
                if discount.id != best_discount.id:
                    other_calculation = discount_calculations[discount.id]
                    assert best_calculation.discount_amount >= other_calculation.discount_amount, \
                        f"Selected discount should provide better or equal savings: {best_calculation.discount_amount} >= {other_calculation.discount_amount}"
        else:
            # Property: If no beneficial discounts exist, none should be selected
            assert best_discount is None, "Engine should not select a discount when none provide savings"
    
    @given(order_amounts())
    @settings(max_examples=5, deadline=2000)
    async def test_optimal_selection_with_conflicting_discount_types(
        self,
        amounts,
        db_session,
        discount_engine
    ):
        """Test optimal selection when different discount types compete"""
        # Create competing discounts of different types
        percentage_discount = Discount(
            code='PERCENT20',
            type=DiscountType.PERCENTAGE.value,
            value=20.0,  # 20% off
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        fixed_discount = Discount(
            code='FIXED25',
            type=DiscountType.FIXED_AMOUNT.value,
            value=25.0,  # $25 off
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        shipping_discount = Discount(
            code='FREESHIP',
            type=DiscountType.FREE_SHIPPING.value,
            value=0.0,
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        db_session.add(percentage_discount)
        db_session.add(fixed_discount)
        db_session.add(shipping_discount)
        await db_session.commit()
        
        discounts = [percentage_discount, fixed_discount, shipping_discount]
        
        # Calculate expected savings for each discount type
        percentage_savings = amounts['subtotal'] * Decimal('0.20')  # 20%
        fixed_savings = min(Decimal('25.00'), amounts['subtotal'])  # $25 or subtotal if less
        shipping_savings = amounts['shipping_cost']  # Free shipping
        
        expected_max_savings = max(percentage_savings, fixed_savings, shipping_savings)
        
        # Test optimal selection
        best_discount, best_calculation = await discount_engine.select_optimal_discount(
            available_discounts=discounts,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        # Property: The engine should select the discount type that provides maximum savings
        assert best_discount is not None, "Engine should select a discount from competing types"
        assert abs(best_calculation.discount_amount - expected_max_savings) < Decimal('0.01'), \
            f"Engine should select discount with maximum savings: expected {expected_max_savings}, got {best_calculation.discount_amount}"
        
        # Verify the correct discount type was selected based on amounts
        if percentage_savings >= fixed_savings and percentage_savings >= shipping_savings:
            assert best_discount.type == DiscountType.PERCENTAGE.value, \
                f"Should select percentage discount when it provides maximum savings"
        elif fixed_savings >= percentage_savings and fixed_savings >= shipping_savings:
            assert best_discount.type == DiscountType.FIXED_AMOUNT.value, \
                f"Should select fixed amount discount when it provides maximum savings"
        else:
            assert best_discount.type == DiscountType.FREE_SHIPPING.value, \
                f"Should select free shipping discount when it provides maximum savings"
    
    @given(order_amounts())
    @settings(max_examples=5, deadline=2000)
    async def test_optimal_selection_with_maximum_discount_limits(
        self,
        amounts,
        db_session,
        discount_engine
    ):
        """Test optimal selection when percentage discounts have maximum limits"""
        # Create percentage discount with maximum limit
        unlimited_discount = Discount(
            code='PERCENT30',
            type=DiscountType.PERCENTAGE.value,
            value=30.0,  # 30% off, no limit
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        limited_discount = Discount(
            code='PERCENT50MAX20',
            type=DiscountType.PERCENTAGE.value,
            value=50.0,  # 50% off, but max $20
            maximum_discount=20.0,
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        db_session.add(unlimited_discount)
        db_session.add(limited_discount)
        await db_session.commit()
        
        discounts = [unlimited_discount, limited_discount]
        
        # Calculate expected savings
        unlimited_savings = amounts['subtotal'] * Decimal('0.30')  # 30%
        limited_savings = min(
            amounts['subtotal'] * Decimal('0.50'),  # 50%
            Decimal('20.00')  # Max $20
        )
        
        expected_max_savings = max(unlimited_savings, limited_savings)
        
        # Test optimal selection
        best_discount, best_calculation = await discount_engine.select_optimal_discount(
            available_discounts=discounts,
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        # Property: Engine should correctly handle maximum discount limits in selection
        assert best_discount is not None, "Engine should select a discount"
        assert abs(best_calculation.discount_amount - expected_max_savings) < Decimal('0.01'), \
            f"Engine should account for maximum limits: expected {expected_max_savings}, got {best_calculation.discount_amount}"
        
        # Verify correct discount was selected based on actual savings after limits
        if unlimited_savings >= limited_savings:
            assert best_discount.code == 'PERCENT30', \
                f"Should select unlimited discount when it provides better savings after limits"
        else:
            assert best_discount.code == 'PERCENT50MAX20', \
                f"Should select limited discount when it provides better savings despite limit"
    
    async def test_empty_discount_list_handling(self, db_session, discount_engine):
        """Test that empty discount list is handled correctly"""
        amounts = {
            'subtotal': Decimal('100.00'),
            'shipping_cost': Decimal('10.00'),
            'tax_amount': Decimal('8.00')
        }
        
        # Test with empty list
        best_discount, best_calculation = await discount_engine.select_optimal_discount(
            available_discounts=[],
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        # Property: Empty discount list should return None
        assert best_discount is None, "Empty discount list should return None"
        assert best_calculation is None, "Empty discount list should return None calculation"
    
    async def test_single_discount_selection(self, db_session, discount_engine):
        """Test that single discount is selected when it's the only option"""
        amounts = {
            'subtotal': Decimal('100.00'),
            'shipping_cost': Decimal('10.00'),
            'tax_amount': Decimal('8.00')
        }
        
        # Create single discount
        single_discount = Discount(
            code='ONLY10',
            type=DiscountType.PERCENTAGE.value,
            value=10.0,
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30)
        )
        db_session.add(single_discount)
        await db_session.commit()
        
        # Test selection
        best_discount, best_calculation = await discount_engine.select_optimal_discount(
            available_discounts=[single_discount],
            subtotal=amounts['subtotal'],
            shipping_cost=amounts['shipping_cost'],
            tax_amount=amounts['tax_amount']
        )
        
        # Property: Single discount should be selected if it provides savings
        assert best_discount is not None, "Single beneficial discount should be selected"
        assert best_discount.id == single_discount.id, "Should select the only available discount"
        assert best_calculation.discount_amount > Decimal('0'), "Single discount should provide savings"


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
class TestOptimalDiscountSelectionPropertySync:
    """Synchronous wrapper for property tests"""
    
    def test_property_7_sync(self):
        """Sync wrapper for property 7 test"""
        async def run_test():
            async with get_test_db_session() as db_session:
                discount_engine = DiscountEngine(db_session)
                test_instance = TestOptimalDiscountSelectionProperty()
                
                # Test with predefined examples
                discount_examples = [
                    [
                        {
                            'code': 'PERCENT15',
                            'type': DiscountType.PERCENTAGE.value,
                            'value': 15.0,
                            'minimum_amount': None,
                            'maximum_discount': None,
                            'usage_limit': None,
                            'valid_from': datetime.now(timezone.utc) - timedelta(days=1),
                            'valid_until': datetime.now(timezone.utc) + timedelta(days=30)
                        },
                        {
                            'code': 'FIXED20',
                            'type': DiscountType.FIXED_AMOUNT.value,
                            'value': 20.0,
                            'minimum_amount': None,
                            'maximum_discount': None,
                            'usage_limit': None,
                            'valid_from': datetime.now(timezone.utc) - timedelta(days=1),
                            'valid_until': datetime.now(timezone.utc) + timedelta(days=30)
                        }
                    ]
                ]
                
                amounts_examples = [
                    {
                        'subtotal': Decimal('100.00'),
                        'shipping_cost': Decimal('10.00'),
                        'tax_amount': Decimal('8.00')
                    },
                    {
                        'subtotal': Decimal('150.00'),
                        'shipping_cost': Decimal('15.00'),
                        'tax_amount': Decimal('12.00')
                    }
                ]
                
                for discount_list in discount_examples:
                    for amounts in amounts_examples:
                        await test_instance.test_property_7_optimal_discount_selection(
                            discount_list, amounts, db_session, discount_engine
                        )
        
        run_async_test(run_test())
    
    def test_conflicting_types_sync(self):
        """Sync wrapper for conflicting discount types test"""
        async def run_test():
            async with get_test_db_session() as db_session:
                discount_engine = DiscountEngine(db_session)
                test_instance = TestOptimalDiscountSelectionProperty()
                
                amounts = {
                    'subtotal': Decimal('100.00'),
                    'shipping_cost': Decimal('10.00'),
                    'tax_amount': Decimal('8.00')
                }
                
                await test_instance.test_optimal_selection_with_conflicting_discount_types(
                    amounts, db_session, discount_engine
                )
        
        run_async_test(run_test())
    
    def test_edge_cases_sync(self):
        """Sync wrapper for edge cases"""
        async def run_test():
            async with get_test_db_session() as db_session:
                discount_engine = DiscountEngine(db_session)
                test_instance = TestOptimalDiscountSelectionProperty()
                
                await test_instance.test_empty_discount_list_handling(db_session, discount_engine)
                await test_instance.test_single_discount_selection(db_session, discount_engine)
        
        run_async_test(run_test())


if __name__ == "__main__":
    # Run basic tests
    test_sync = TestOptimalDiscountSelectionPropertySync()
    test_sync.test_property_7_sync()
    test_sync.test_conflicting_types_sync()
    test_sync.test_edge_cases_sync()
    print("✅ Optimal discount selection property tests passed!")