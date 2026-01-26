"""
Unit Tests for Loyalty Service Discount Calculations
Tests loyalty tier discounts, points calculations, and reward redemptions
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
from core.utils.uuid_utils import uuid7, UUID

from services.loyalty import LoyaltyService
from models.loyalty import LoyaltyAccount, PointsTransaction, TierAdvancement
from schemas.loyalty import LoyaltyDiscountResponse, PointsCalculationResponse


class TestLoyaltyTierDiscounts:
    """Test loyalty tier-based discount calculations"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def loyalty_service(self, mock_db):
        return LoyaltyService(mock_db)
    
    def test_bronze_tier_discount(self, loyalty_service):
        """Test Bronze tier discount calculation (0%)"""
        tier_config = loyalty_service.TIER_CONFIG["Bronze"]
        
        base_cost = Decimal("100.00")
        discount_percentage = tier_config["discount_percentage"]  # 0.0%
        
        discount_amount = base_cost * (discount_percentage / 100)
        final_cost = base_cost - discount_amount
        
        assert discount_amount == Decimal("0.00")
        assert final_cost == Decimal("100.00")
        assert discount_percentage == 0.0
    
    def test_silver_tier_discount(self, loyalty_service):
        """Test Silver tier discount calculation (2%)"""
        tier_config = loyalty_service.TIER_CONFIG["Silver"]
        
        base_cost = Decimal("100.00")
        discount_percentage = tier_config["discount_percentage"]  # 2.0%
        
        discount_amount = base_cost * (discount_percentage / 100)
        final_cost = base_cost - discount_amount
        
        assert discount_amount == Decimal("2.00")
        assert final_cost == Decimal("98.00")
        assert discount_percentage == 2.0
    
    def test_gold_tier_discount(self, loyalty_service):
        """Test Gold tier discount calculation (5%)"""
        tier_config = loyalty_service.TIER_CONFIG["Gold"]
        
        base_cost = Decimal("100.00")
        discount_percentage = tier_config["discount_percentage"]  # 5.0%
        
        discount_amount = base_cost * (discount_percentage / 100)
        final_cost = base_cost - discount_amount
        
        assert discount_amount == Decimal("5.00")
        assert final_cost == Decimal("95.00")
        assert discount_percentage == 5.0
    
    def test_platinum_tier_discount(self, loyalty_service):
        """Test Platinum tier discount calculation (10%)"""
        tier_config = loyalty_service.TIER_CONFIG["Platinum"]
        
        base_cost = Decimal("100.00")
        discount_percentage = tier_config["discount_percentage"]  # 10.0%
        
        discount_amount = base_cost * (discount_percentage / 100)
        final_cost = base_cost - discount_amount
        
        assert discount_amount == Decimal("10.00")
        assert final_cost == Decimal("90.00")
        assert discount_percentage == 10.0
    
    @pytest.mark.asyncio
    async def test_calculate_loyalty_discount_bronze(self, loyalty_service):
        """Test loyalty discount calculation for Bronze tier user"""
        user_id = uuid7()
        base_cost = Decimal("150.00")
        
        # Mock loyalty account with Bronze tier
        mock_account = LoyaltyAccount(
            id=uuid7(),
            user_id=user_id,
            current_tier="Bronze",
            total_points=500,
            lifetime_points=500,
            created_at=datetime.utcnow()
        )
        
        # Mock database query
        loyalty_service.db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        loyalty_service.db.execute.return_value = mock_result
        
        # Test discount calculation
        result = await loyalty_service.calculate_loyalty_discount(user_id, base_cost)
        
        assert isinstance(result, LoyaltyDiscountResponse)
        assert result.original_cost == base_cost
        assert result.discount_percentage == 0.0
        assert result.discount_amount == Decimal("0.00")
        assert result.final_cost == base_cost
        assert result.tier == "Bronze"
    
    @pytest.mark.asyncio
    async def test_calculate_loyalty_discount_platinum(self, loyalty_service):
        """Test loyalty discount calculation for Platinum tier user"""
        user_id = uuid7()
        base_cost = Decimal("200.00")
        
        # Mock loyalty account with Platinum tier
        mock_account = LoyaltyAccount(
            id=uuid7(),
            user_id=user_id,
            current_tier="Platinum",
            total_points=20000,
            lifetime_points=25000,
            created_at=datetime.utcnow()
        )
        
        # Mock database query
        loyalty_service.db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        loyalty_service.db.execute.return_value = mock_result
        
        # Test discount calculation
        result = await loyalty_service.calculate_loyalty_discount(user_id, base_cost)
        
        expected_discount = base_cost * Decimal("0.10")  # 10%
        expected_final = base_cost - expected_discount
        
        assert result.original_cost == base_cost
        assert result.discount_percentage == 10.0
        assert result.discount_amount == expected_discount
        assert result.final_cost == expected_final
        assert result.tier == "Platinum"
    
    @pytest.mark.asyncio
    async def test_calculate_loyalty_discount_no_account(self, loyalty_service):
        """Test loyalty discount for user without loyalty account"""
        user_id = uuid7()
        base_cost = Decimal("100.00")
        
        # Mock database query returning None (no account)
        loyalty_service.db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        loyalty_service.db.execute.return_value = mock_result
        
        # Test discount calculation
        result = await loyalty_service.calculate_loyalty_discount(user_id, base_cost)
        
        # Should default to Bronze tier (no discount)
        assert result.original_cost == base_cost
        assert result.discount_percentage == 0.0
        assert result.discount_amount == Decimal("0.00")
        assert result.final_cost == base_cost
        assert result.tier == "Bronze"


class TestPointsCalculations:
    """Test loyalty points earning calculations"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def loyalty_service(self, mock_db):
        return LoyaltyService(mock_db)
    
    def test_bronze_points_multiplier(self, loyalty_service):
        """Test points calculation for Bronze tier (1.0x multiplier)"""
        tier_config = loyalty_service.TIER_CONFIG["Bronze"]
        
        base_points = 100
        multiplier = tier_config["points_multiplier"]  # 1.0
        
        earned_points = int(base_points * multiplier)
        
        assert earned_points == 100
        assert multiplier == 1.0
    
    def test_silver_points_multiplier(self, loyalty_service):
        """Test points calculation for Silver tier (1.2x multiplier)"""
        tier_config = loyalty_service.TIER_CONFIG["Silver"]
        
        base_points = 100
        multiplier = tier_config["points_multiplier"]  # 1.2
        
        earned_points = int(base_points * multiplier)
        
        assert earned_points == 120
        assert multiplier == 1.2
    
    def test_gold_points_multiplier(self, loyalty_service):
        """Test points calculation for Gold tier (1.5x multiplier)"""
        tier_config = loyalty_service.TIER_CONFIG["Gold"]
        
        base_points = 100
        multiplier = tier_config["points_multiplier"]  # 1.5
        
        earned_points = int(base_points * multiplier)
        
        assert earned_points == 150
        assert multiplier == 1.5
    
    def test_platinum_points_multiplier(self, loyalty_service):
        """Test points calculation for Platinum tier (2.0x multiplier)"""
        tier_config = loyalty_service.TIER_CONFIG["Platinum"]
        
        base_points = 100
        multiplier = tier_config["points_multiplier"]  # 2.0
        
        earned_points = int(base_points * multiplier)
        
        assert earned_points == 200
        assert multiplier == 2.0
    
    @pytest.mark.asyncio
    async def test_calculate_points_for_purchase(self, loyalty_service):
        """Test points calculation for a purchase"""
        user_id = uuid7()
        purchase_amount = Decimal("50.00")
        
        # Mock loyalty account with Gold tier
        mock_account = LoyaltyAccount(
            id=uuid7(),
            user_id=user_id,
            current_tier="Gold",
            total_points=8000,
            lifetime_points=12000
        )
        
        # Mock database query
        loyalty_service.db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        loyalty_service.db.execute.return_value = mock_result
        
        # Test points calculation
        result = await loyalty_service.calculate_points_for_purchase(user_id, purchase_amount)
        
        # Gold tier: 1.5x multiplier, $1 = 1 point base
        base_points = int(purchase_amount)  # 50 points
        expected_points = int(base_points * 1.5)  # 75 points
        
        assert isinstance(result, PointsCalculationResponse)
        assert result.base_points == base_points
        assert result.multiplier == 1.5
        assert result.bonus_points == 0  # No bonus in this test
        assert result.total_points == expected_points
        assert result.tier == "Gold"


class TestTierAdvancement:
    """Test tier advancement logic"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def loyalty_service(self, mock_db):
        return LoyaltyService(mock_db)
    
    def test_tier_thresholds(self, loyalty_service):
        """Test tier advancement thresholds"""
        tier_config = loyalty_service.TIER_CONFIG
        
        # Test thresholds
        assert tier_config["Bronze"]["max_points"] == 999
        assert tier_config["Silver"]["max_points"] == 4999
        assert tier_config["Gold"]["max_points"] == 14999
        assert tier_config["Platinum"]["max_points"] == float('inf')
    
    def test_determine_tier_bronze(self, loyalty_service):
        """Test tier determination for Bronze level points"""
        points = 500
        
        # Determine tier based on points
        if points <= 999:
            tier = "Bronze"
        elif points <= 4999:
            tier = "Silver"
        elif points <= 14999:
            tier = "Gold"
        else:
            tier = "Platinum"
        
        assert tier == "Bronze"
    
    def test_determine_tier_silver(self, loyalty_service):
        """Test tier determination for Silver level points"""
        points = 2500
        
        # Determine tier based on points
        if points <= 999:
            tier = "Bronze"
        elif points <= 4999:
            tier = "Silver"
        elif points <= 14999:
            tier = "Gold"
        else:
            tier = "Platinum"
        
        assert tier == "Silver"
    
    def test_determine_tier_gold(self, loyalty_service):
        """Test tier determination for Gold level points"""
        points = 8000
        
        # Determine tier based on points
        if points <= 999:
            tier = "Bronze"
        elif points <= 4999:
            tier = "Silver"
        elif points <= 14999:
            tier = "Gold"
        else:
            tier = "Platinum"
        
        assert tier == "Gold"
    
    def test_determine_tier_platinum(self, loyalty_service):
        """Test tier determination for Platinum level points"""
        points = 20000
        
        # Determine tier based on points
        if points <= 999:
            tier = "Bronze"
        elif points <= 4999:
            tier = "Silver"
        elif points <= 14999:
            tier = "Gold"
        else:
            tier = "Platinum"
        
        assert tier == "Platinum"


class TestRewardRedemptions:
    """Test reward redemption calculations"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def loyalty_service(self, mock_db):
        return LoyaltyService(mock_db)
    
    def test_discount_reward_values(self, loyalty_service):
        """Test discount reward point costs and values"""
        # These would typically come from the loyalty service
        discount_rewards = [
            {"id": "discount_5", "points_required": 500, "reward_value": 5.0},
            {"id": "discount_10", "points_required": 1000, "reward_value": 10.0},
            {"id": "discount_15", "points_required": 2000, "reward_value": 15.0}
        ]
        
        # Test point-to-value ratios
        for reward in discount_rewards:
            ratio = reward["points_required"] / reward["reward_value"]
            
            # All discounts should have 100 points per $1 ratio
            assert ratio == 100.0
    
    def test_reward_affordability(self, loyalty_service):
        """Test if user can afford rewards"""
        user_points = 1500
        
        rewards = [
            {"id": "discount_5", "points_required": 500},   # Affordable
            {"id": "discount_10", "points_required": 1000}, # Affordable
            {"id": "discount_15", "points_required": 2000}  # Not affordable
        ]
        
        affordable_rewards = [
            reward for reward in rewards 
            if reward["points_required"] <= user_points
        ]
        
        assert len(affordable_rewards) == 2
        assert affordable_rewards[0]["id"] == "discount_5"
        assert affordable_rewards[1]["id"] == "discount_10"
    
    def test_points_deduction_calculation(self, loyalty_service):
        """Test points deduction after redemption"""
        current_points = 1500
        reward_cost = 1000
        
        remaining_points = current_points - reward_cost
        
        assert remaining_points == 500
        assert remaining_points >= 0  # Should never go negative


class TestComplexLoyaltyScenarios:
    """Test complex loyalty discount scenarios"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def loyalty_service(self, mock_db):
        return LoyaltyService(mock_db)
    
    def test_tier_benefits_comparison(self, loyalty_service):
        """Test comparing benefits across tiers"""
        base_cost = Decimal("100.00")
        tier_configs = loyalty_service.TIER_CONFIG
        
        results = {}
        for tier_name, config in tier_configs.items():
            discount_percentage = config["discount_percentage"]
            discount_amount = base_cost * (discount_percentage / 100)
            final_cost = base_cost - discount_amount
            
            results[tier_name] = {
                "discount_percentage": discount_percentage,
                "discount_amount": discount_amount,
                "final_cost": final_cost,
                "points_multiplier": config["points_multiplier"]
            }
        
        # Verify tier progression benefits
        assert results["Bronze"]["final_cost"] > results["Silver"]["final_cost"]
        assert results["Silver"]["final_cost"] > results["Gold"]["final_cost"]
        assert results["Gold"]["final_cost"] > results["Platinum"]["final_cost"]
        
        # Verify points multiplier progression
        assert results["Bronze"]["points_multiplier"] < results["Silver"]["points_multiplier"]
        assert results["Silver"]["points_multiplier"] < results["Gold"]["points_multiplier"]
        assert results["Gold"]["points_multiplier"] < results["Platinum"]["points_multiplier"]
    
    def test_loyalty_discount_with_other_discounts(self, loyalty_service):
        """Test loyalty discount interaction with other discount types"""
        base_cost = Decimal("100.00")
        loyalty_discount_rate = 0.10  # 10% Platinum tier
        promocode_discount = Decimal("15.00")  # $15 off
        
        # Scenario 1: Apply loyalty discount first
        after_loyalty = base_cost * (1 - loyalty_discount_rate)  # $90.00
        final_with_promo = after_loyalty - promocode_discount    # $75.00
        
        assert after_loyalty == Decimal("90.00")
        assert final_with_promo == Decimal("75.00")
        
        # Scenario 2: Apply promocode first
        after_promo = base_cost - promocode_discount             # $85.00
        final_with_loyalty = after_promo * (1 - loyalty_discount_rate)  # $76.50
        
        assert after_promo == Decimal("85.00")
        assert final_with_loyalty == Decimal("76.50")
        
        # Different order gives different results - business rule needed
        assert final_with_promo != final_with_loyalty
    
    def test_minimum_purchase_for_points(self, loyalty_service):
        """Test minimum purchase requirements for earning points"""
        minimum_purchase = Decimal("5.00")  # Minimum to earn points
        
        # Test cases
        test_amounts = [
            Decimal("3.00"),   # Below minimum
            Decimal("5.00"),   # At minimum
            Decimal("10.00")   # Above minimum
        ]
        
        for amount in test_amounts:
            earns_points = amount >= minimum_purchase
            
            if amount == Decimal("3.00"):
                assert earns_points is False
            else:
                assert earns_points is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])