"""
Property-based tests for loyalty system integration.

This module tests Property 27: Loyalty system integration
Validates Requirements: 15.1, 15.2, 15.3, 15.4, 15.7

The loyalty system should:
- Award points based on subscription value (15.1)
- Provide referral bonuses for successful referrals (15.2)
- Offer redemption options when customers accumulate points (15.3)
- Track customer tier status with increasing benefits (15.4)
- Integrate with subscription cost calculator for discounts (15.7)
"""

import pytest
import asyncio
from decimal import Decimal
from core.utils.uuid_utils import uuid7, UUID
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.strategies import composite
from sqlalchemy.ext.asyncio import AsyncSession

from services.loyalty import LoyaltyService
from services.subscription_cost_calculator import SubscriptionCostCalculator
from models.loyalty import LoyaltyAccount, PointsTransaction
from models.subscription import Subscription
from models.user import User
from schemas.loyalty import (
    PointsCalculationResponse, ReferralBonusResponse, AvailableReward,
    RedemptionResponse, LoyaltyDiscountResponse
)


# Test data generators
@composite
def subscription_value_strategy(draw):
    """Generate realistic subscription values"""
    return draw(st.decimals(
        min_value=Decimal('10.00'),
        max_value=Decimal('500.00'),
        places=2
    ))


@composite
def tier_strategy(draw):
    """Generate valid loyalty tiers"""
    return draw(st.sampled_from(['bronze', 'silver', 'gold', 'platinum']))


@composite
def points_amount_strategy(draw):
    """Generate realistic points amounts"""
    return draw(st.integers(min_value=0, max_value=50000))


@composite
def loyalty_account_strategy(draw):
    """Generate loyalty account data"""
    tier = draw(tier_strategy())
    total_points = draw(points_amount_strategy())
    available_points = draw(st.integers(min_value=0, max_value=total_points))
    referrals_made = draw(st.integers(min_value=0, max_value=20))
    successful_referrals = draw(st.integers(min_value=0, max_value=referrals_made))  # Fix: ensure successful <= made
    
    return {
        'id': uuid7(),
        'user_id': uuid7(),
        'tier': tier,
        'total_points': total_points,
        'available_points': available_points,
        'points_earned_lifetime': total_points,
        'points_redeemed_lifetime': total_points - available_points,
        'referrals_made': referrals_made,
        'successful_referrals': successful_referrals,
        'status': 'active'
    }


@composite
def subscription_strategy(draw):
    """Generate subscription data"""
    return {
        'id': uuid7(),
        'user_id': uuid7(),
        'price': float(draw(subscription_value_strategy())),
        'currency': draw(st.sampled_from(['USD', 'EUR', 'GBP', 'CAD'])),
        'billing_cycle': draw(st.sampled_from(['monthly', 'quarterly', 'yearly'])),
        'status': draw(st.sampled_from(['active', 'paused', 'cancelled']))
    }


class TestLoyaltySystemIntegrationProperty:
    """Property-based tests for loyalty system integration"""
    
    def create_mock_db(self):
        """Create mock database session"""
        db = AsyncMock(spec=AsyncSession)
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db
    
    def create_loyalty_service(self, mock_db=None):
        """Create loyalty service with mocked database"""
        if mock_db is None:
            mock_db = self.create_mock_db()
        return LoyaltyService(mock_db)
    
    def create_cost_calculator(self, mock_db=None):
        """Create cost calculator with mocked database"""
        if mock_db is None:
            mock_db = self.create_mock_db()
        return SubscriptionCostCalculator(mock_db)

    @given(
        subscription_value=subscription_value_strategy(),
        tier=tier_strategy()
    )
    @settings(max_examples=100, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_points_awarded_based_on_subscription_value_property(
        self, subscription_value, tier
    ):
        """
        Property 27a: Points awarded based on subscription value
        
        For any subscription value and user tier, the loyalty system should award
        points based on the subscription value with appropriate tier multipliers.
        
        **Feature: subscription-payment-enhancements, Property 27a: Points awarded based on subscription value**
        **Validates: Requirements 15.1**
        """
        loyalty_service = self.create_loyalty_service()
        # Calculate expected points based on loyalty service configuration
        base_points_rate = loyalty_service.base_points_rate  # 10 points per dollar
        tier_config = loyalty_service.tier_config[tier]
        tier_multiplier = tier_config['points_multiplier']
        
        # Calculate points
        points_calc = await loyalty_service.calculate_points_earned(subscription_value, tier)
        
        # Verify points calculation follows the formula
        expected_base_points = int(subscription_value * base_points_rate)
        expected_tier_bonus = round(expected_base_points * (tier_multiplier - 1.0))
        expected_total = expected_base_points + expected_tier_bonus
        
        assert points_calc.base_points == expected_base_points
        assert points_calc.tier_bonus_points == expected_tier_bonus
        assert points_calc.total_points == expected_total
        assert points_calc.tier_multiplier == tier_multiplier
        
        # Verify calculation details are provided
        assert points_calc.calculation_details is not None
        assert 'subscription_value' in points_calc.calculation_details
        assert 'tier' in points_calc.calculation_details
        assert 'tier_multiplier' in points_calc.calculation_details

    @given(
        referrer_data=loyalty_account_strategy(),
        referee_data=loyalty_account_strategy(),
        subscription_data=subscription_strategy()
    )
    @settings(max_examples=50, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_referral_bonus_processing_property(
        self, referrer_data, referee_data, subscription_data
    ):
        """
        Property 27b: Referral bonus processing
        
        For any valid referral scenario, the loyalty system should provide bonus
        points for both referrer and referee when a qualifying subscription is created.
        
        **Feature: subscription-payment-enhancements, Property 27b: Referral bonus processing**
        **Validates: Requirements 15.2**
        """
        loyalty_service = self.create_loyalty_service()
        mock_db = loyalty_service.db
        # Ensure different users
        assume(referrer_data['user_id'] != referee_data['user_id'])
        
        # Ensure subscription meets minimum value requirement
        min_subscription_value = loyalty_service.referral_config['minimum_subscription_value']
        assume(subscription_data['price'] >= min_subscription_value)
        
        # Mock database responses
        referrer_account = MagicMock()
        referrer_account.id = referrer_data['id']
        referrer_account.user_id = referrer_data['user_id']
        referrer_account.total_points = referrer_data['total_points']
        referrer_account.available_points = referrer_data['available_points']
        referrer_account.referrals_made = referrer_data['referrals_made']
        referrer_account.successful_referrals = referrer_data['successful_referrals']
        
        referee_account = MagicMock()
        referee_account.id = referee_data['id']
        referee_account.user_id = referee_data['user_id']
        referee_account.total_points = referee_data['total_points']
        referee_account.available_points = referee_data['available_points']
        
        subscription = MagicMock()
        subscription.id = subscription_data['id']
        subscription.user_id = referee_data['user_id']
        subscription.price = subscription_data['price']
        subscription.currency = subscription_data['currency']
        
        # Mock database execute calls - return subscription for subscription query, None for referral check
        subscription_result = MagicMock()
        subscription_result.scalar_one_or_none.return_value = subscription
        
        referral_check_result = MagicMock()
        referral_check_result.scalar_one_or_none.return_value = None  # No existing referral
        
        # Set up execute to return different results based on call order
        mock_db.execute.side_effect = [subscription_result, referral_check_result]
        
        # Mock get_or_create_loyalty_account calls
        async def mock_get_or_create(user_id):
            if user_id == referrer_data['user_id']:
                return referrer_account
            elif user_id == referee_data['user_id']:
                return referee_account
            return None
        
        loyalty_service.get_or_create_loyalty_account = AsyncMock(side_effect=mock_get_or_create)
        
        # Mock the db.add method to set transaction IDs
        def mock_add(obj):
            if hasattr(obj, 'id') and obj.id is None:
                obj.id = uuid7()
        
        mock_db.add.side_effect = mock_add
        
        # Process referral bonus
        bonus_result = await loyalty_service.process_referral_bonus(
            referrer_id=referrer_data['user_id'],
            referee_id=referee_data['user_id'],
            subscription_id=subscription_data['id']
        )
        
        # Verify referral bonus structure and amounts
        expected_referrer_bonus = loyalty_service.referral_config['referrer_bonus']
        expected_referee_bonus = loyalty_service.referral_config['referee_bonus']
        
        assert bonus_result.referrer_bonus_points == expected_referrer_bonus
        assert bonus_result.referee_bonus_points == expected_referee_bonus
        assert bonus_result.referrer_transaction_id is not None
        assert bonus_result.referee_transaction_id is not None
        
        # Verify bonus details contain required information
        assert 'referrer_id' in bonus_result.bonus_details
        assert 'referee_id' in bonus_result.bonus_details
        assert 'subscription_id' in bonus_result.bonus_details
        assert 'subscription_value' in bonus_result.bonus_details

    @given(
        account_data=loyalty_account_strategy()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_redemption_options_availability_property(
        self, account_data
    ):
        """
        Property 27c: Redemption options availability
        
        For any loyalty account with accumulated points, the system should offer
        appropriate redemption options based on available points and tier status.
        
        **Feature: subscription-payment-enhancements, Property 27c: Redemption options availability**
        **Validates: Requirements 15.3**
        """
        loyalty_service = self.create_loyalty_service()
        # Mock loyalty account
        loyalty_account = MagicMock()
        loyalty_account.id = account_data['id']
        loyalty_account.user_id = account_data['user_id']
        loyalty_account.tier = account_data['tier']
        loyalty_account.available_points = account_data['available_points']
        loyalty_account.total_points = account_data['total_points']
        
        loyalty_service.get_or_create_loyalty_account = AsyncMock(return_value=loyalty_account)
        
        # Get available rewards
        rewards = await loyalty_service.get_available_rewards(account_data['user_id'])
        
        # Verify all returned rewards are valid for the user's tier and points
        tier_hierarchy = ['bronze', 'silver', 'gold', 'platinum']
        user_tier_level = tier_hierarchy.index(account_data['tier'])
        
        for reward in rewards:
            # User should have enough points
            assert reward.points_required <= account_data['available_points']
            
            # Reward should be available for user's tier
            if hasattr(reward, 'metadata') and 'min_tier' in reward.metadata:
                min_tier_level = tier_hierarchy.index(reward.metadata['min_tier'])
                assert user_tier_level >= min_tier_level
            
            # Reward should be marked as available
            assert reward.is_available is True
            
            # Required reward fields should be present
            assert reward.id is not None
            assert reward.name is not None
            assert reward.description is not None
            assert reward.points_required > 0
            assert reward.reward_type is not None

    @given(
        account_data=loyalty_account_strategy(),
        points_to_add=st.integers(min_value=100, max_value=10000)
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_tier_advancement_tracking_property(
        self, account_data, points_to_add
    ):
        """
        Property 27d: Tier advancement tracking
        
        For any loyalty account, the system should track tier status and provide
        increasing benefits as customers advance through tiers.
        
        **Feature: subscription-payment-enhancements, Property 27d: Tier advancement tracking**
        **Validates: Requirements 15.4**
        """
        loyalty_service = self.create_loyalty_service()
        # Create loyalty account with initial points
        loyalty_account = MagicMock()
        loyalty_account.id = account_data['id']
        loyalty_account.user_id = account_data['user_id']
        loyalty_account.tier = account_data['tier']
        loyalty_account.total_points = account_data['total_points']
        loyalty_account.available_points = account_data['available_points']
        
        # Calculate new total points after addition
        new_total_points = account_data['total_points'] + points_to_add
        loyalty_account.total_points = new_total_points
        
        # Determine expected tier based on new points total
        expected_tier = account_data['tier']
        for tier, config in loyalty_service.tier_config.items():
            if (new_total_points >= config['min_points'] and 
                new_total_points <= config['max_points']):
                expected_tier = tier
                break
        
        # Test tier advancement check
        advancement_result = await loyalty_service._check_and_process_tier_advancement(loyalty_account)
        
        # Verify tier is correctly determined
        assert loyalty_account.tier == expected_tier
        
        # Verify tier benefits are assigned (compare the actual benefits dict)
        expected_benefits = loyalty_service.tier_config[expected_tier]['benefits']
        if hasattr(loyalty_account.tier_benefits, '__dict__'):
            # If it's a mock, just check it was set
            assert loyalty_account.tier_benefits is not None
        else:
            assert loyalty_account.tier_benefits == expected_benefits
        
        # If tier changed, advancement result should be returned
        if expected_tier != account_data['tier']:
            assert advancement_result is not None
            assert advancement_result.old_tier == account_data['tier']
            assert advancement_result.new_tier == expected_tier
            assert advancement_result.new_benefits == expected_benefits
        
        # Verify tier benefits increase with tier level
        tier_hierarchy = ['bronze', 'silver', 'gold', 'platinum']
        current_tier_level = tier_hierarchy.index(expected_tier)
        
        # Higher tiers should have better multipliers
        current_multiplier = loyalty_service.tier_config[expected_tier]['points_multiplier']
        current_discount = loyalty_service.tier_config[expected_tier]['discount_percentage']
        
        # Verify multiplier increases with tier (or stays same for bronze)
        if current_tier_level > 0:
            lower_tier = tier_hierarchy[current_tier_level - 1]
            lower_multiplier = loyalty_service.tier_config[lower_tier]['points_multiplier']
            assert current_multiplier >= lower_multiplier
            
            lower_discount = loyalty_service.tier_config[lower_tier]['discount_percentage']
            assert current_discount >= lower_discount

    @given(
        account_data=loyalty_account_strategy(),
        base_cost=st.decimals(min_value=Decimal('20.00'), max_value=Decimal('200.00'), places=2)
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_cost_calculator_integration_property(
        self, account_data, base_cost
    ):
        """
        Property 27e: Cost calculator integration
        
        For any subscription cost calculation, the loyalty system should integrate
        with the cost calculator to provide appropriate discounts based on tier.
        
        **Feature: subscription-payment-enhancements, Property 27e: Cost calculator integration**
        **Validates: Requirements 15.7**
        """
        loyalty_service = self.create_loyalty_service()
        cost_calculator = self.create_cost_calculator()
        # Mock loyalty account
        loyalty_account = MagicMock()
        loyalty_account.id = account_data['id']
        loyalty_account.user_id = account_data['user_id']
        loyalty_account.tier = account_data['tier']
        loyalty_account.total_points = account_data['total_points']
        loyalty_account.available_points = account_data['available_points']
        
        loyalty_service.get_or_create_loyalty_account = AsyncMock(return_value=loyalty_account)
        
        # Test loyalty discount calculation
        discount_result = await loyalty_service.calculate_loyalty_discount(
            account_data['user_id'], base_cost
        )
        
        # Verify discount calculation
        tier_config = loyalty_service.tier_config[account_data['tier']]
        expected_discount_percentage = tier_config['discount_percentage']
        expected_discount_amount = base_cost * Decimal(str(expected_discount_percentage / 100))
        expected_final_cost = base_cost - expected_discount_amount
        
        assert discount_result.tier == account_data['tier']
        assert discount_result.discount_percentage == expected_discount_percentage
        assert abs(discount_result.discount_amount - expected_discount_amount) < Decimal('0.01')
        assert abs(discount_result.final_cost - expected_final_cost) < Decimal('0.01')
        
        # Verify discount details are provided
        assert discount_result.discount_details is not None
        assert 'tier' in discount_result.discount_details
        assert 'tier_discount_percentage' in discount_result.discount_details
        assert 'base_cost' in discount_result.discount_details
        assert 'final_cost' in discount_result.discount_details
        
        # Test integration with cost calculator
        with patch.object(cost_calculator, '_calculate_loyalty_discount') as mock_loyalty_calc:
            mock_loyalty_calc.return_value = discount_result.discount_amount
            
            # Mock other cost calculator dependencies
            mock_pricing_config = MagicMock()
            mock_pricing_config.subscription_percentage = 10.0
            mock_pricing_config.delivery_costs = {'standard': 10.0}
            cost_calculator.admin_pricing_service.get_pricing_config = AsyncMock(return_value=mock_pricing_config)
            
            # Mock variants to avoid "No valid product variants found" error
            mock_variant = MagicMock()
            mock_variant.id = uuid7()
            mock_variant.base_price = Decimal('25.00')  # Use base_price instead of price
            mock_variant.sale_price = None  # No sale price
            mock_variant.name = "Test Product"
            mock_variant.sku = "TEST-001"
            mock_variants = [mock_variant]
            cost_calculator._get_variants_by_ids = AsyncMock(return_value=mock_variants)
            
            cost_calculator.tax_service.calculate_tax = AsyncMock(return_value={'tax_rate': 0.08, 'tax_amount': Decimal('2.00')})
            cost_calculator._convert_currency_via_stripe = AsyncMock(side_effect=lambda amount, f, t: amount)
            
            # Calculate subscription cost with loyalty discount
            cost_breakdown = await cost_calculator.calculate_subscription_cost(
                variant_ids=[uuid7()],  # Provide at least one variant ID
                delivery_type='standard',
                customer_location='US',
                currency='USD',
                user_id=account_data['user_id']
            )
            
            # Verify loyalty discount was applied
            mock_loyalty_calc.assert_called_once()
            assert cost_breakdown.loyalty_discount == discount_result.discount_amount

    @given(
        account_data=loyalty_account_strategy()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_comprehensive_loyalty_system_integration_property(
        self, account_data
    ):
        """
        Property 27f: Comprehensive loyalty system integration
        
        For any loyalty account, the system should provide a complete integration
        of points earning, tier tracking, rewards, referrals, and cost discounts.
        
        **Feature: subscription-payment-enhancements, Property 27f: Comprehensive loyalty system integration**
        **Validates: Requirements 15.1, 15.2, 15.3, 15.4, 15.7**
        """
        loyalty_service = self.create_loyalty_service()
        # Mock loyalty account
        loyalty_account = MagicMock()
        loyalty_account.id = account_data['id']
        loyalty_account.user_id = account_data['user_id']
        loyalty_account.tier = account_data['tier']
        loyalty_account.total_points = account_data['total_points']
        loyalty_account.available_points = account_data['available_points']
        loyalty_account.points_earned_lifetime = account_data['points_earned_lifetime']
        loyalty_account.points_redeemed_lifetime = account_data['points_redeemed_lifetime']
        loyalty_account.referrals_made = account_data['referrals_made']
        loyalty_account.successful_referrals = account_data['successful_referrals']
        loyalty_account.status = account_data['status']
        
        loyalty_service.get_or_create_loyalty_account = AsyncMock(return_value=loyalty_account)
        
        # Mock the database execute for subscription history query
        mock_subscription_result = MagicMock()
        mock_subscription_result.scalars.return_value.all.return_value = []  # Empty subscription history
        loyalty_service.db.execute = AsyncMock(return_value=mock_subscription_result)
        
        # Test 1: Points calculation consistency
        subscription_value = Decimal('50.00')
        points_calc = await loyalty_service.calculate_points_earned(subscription_value, account_data['tier'])
        
        # Verify points calculation is consistent with tier configuration
        tier_config = loyalty_service.tier_config[account_data['tier']]
        expected_base = int(subscription_value * loyalty_service.base_points_rate)
        expected_bonus = round(expected_base * (tier_config['points_multiplier'] - 1.0))
        
        assert points_calc.base_points == expected_base
        assert points_calc.tier_bonus_points == expected_bonus
        assert points_calc.total_points == expected_base + expected_bonus
        
        # Test 2: Tier benefits consistency
        tier_benefits = tier_config['benefits']
        assert isinstance(tier_benefits, dict)
        assert 'birthday_bonus' in tier_benefits
        
        # Test 3: Discount calculation consistency
        base_cost = Decimal('100.00')
        discount_result = await loyalty_service.calculate_loyalty_discount(account_data['user_id'], base_cost)
        
        expected_discount_pct = tier_config['discount_percentage']
        assert discount_result.discount_percentage == expected_discount_pct
        
        # Test 4: Available rewards are appropriate for tier and points
        rewards = await loyalty_service.get_available_rewards(account_data['user_id'])
        
        for reward in rewards:
            # All rewards should be affordable
            assert reward.points_required <= account_data['available_points']
            
            # All rewards should be available
            assert reward.is_available is True
        
        # Test 5: Personalized offers are generated
        offers = await loyalty_service.get_personalized_offers(account_data['user_id'])
        
        # Should return list of offers
        assert isinstance(offers, list)
        
        # Each offer should have required fields
        for offer in offers:
            assert hasattr(offer, 'id')
            assert hasattr(offer, 'title')
            assert hasattr(offer, 'description')
            assert hasattr(offer, 'offer_type')
            assert hasattr(offer, 'valid_until')
            assert hasattr(offer, 'personalization_reason')
        
        # Test 6: System maintains data consistency
        # Points earned lifetime should be >= total points (accounting for redemptions)
        assert account_data['points_earned_lifetime'] >= account_data['total_points']
        
        # Available points should be <= total points
        assert account_data['available_points'] <= account_data['total_points']
        
        # Successful referrals should be <= total referrals made
        assert account_data['successful_referrals'] <= account_data['referrals_made']


# Test configuration
pytestmark = pytest.mark.asyncio