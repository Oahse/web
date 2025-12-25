import pytest
import asyncio
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import BaseModel
from models.user import User
from models.loyalty import LoyaltyAccount, PointsTransaction
from models.subscription import Subscription
from services.loyalty import LoyaltyService


# Test database setup
TEST_POSTGRES_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture
async def db_session():
    """Create a test database session"""
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
async def test_user(db_session: AsyncSession):
    """Create a test user"""
    user = User(
        id=uuid4(),
        email="test@example.com",
        firstname="Test",
        lastname="User",
        hashed_password="hashed_password",
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def loyalty_service(db_session: AsyncSession):
    """Create a loyalty service instance"""
    return LoyaltyService(db_session)


class TestLoyaltyService:
    """Test cases for LoyaltyService"""
    
    async def test_get_or_create_loyalty_account(self, loyalty_service: LoyaltyService, test_user: User):
        """Test creating a new loyalty account"""
        # First call should create account
        account = await loyalty_service.get_or_create_loyalty_account(test_user.id)
        
        assert account is not None
        assert account.user_id == test_user.id
        assert account.tier == "bronze"
        assert account.total_points == 0
        assert account.available_points == 0
        
        # Second call should return existing account
        account2 = await loyalty_service.get_or_create_loyalty_account(test_user.id)
        assert account.id == account2.id
    
    async def test_calculate_points_earned(self, loyalty_service: LoyaltyService):
        """Test points calculation for different tiers"""
        subscription_value = Decimal("50.00")
        
        # Test bronze tier
        bronze_calc = await loyalty_service.calculate_points_earned(subscription_value, "bronze")
        assert bronze_calc.base_points == 500  # 50 * 10
        assert bronze_calc.tier_bonus_points == 0  # 1.0 multiplier
        assert bronze_calc.total_points == 500
        
        # Test silver tier
        silver_calc = await loyalty_service.calculate_points_earned(subscription_value, "silver")
        assert silver_calc.base_points == 500
        assert silver_calc.tier_bonus_points == 100  # 500 * (1.2 - 1.0)
        assert silver_calc.total_points == 600
        
        # Test gold tier
        gold_calc = await loyalty_service.calculate_points_earned(subscription_value, "gold")
        assert gold_calc.base_points == 500
        assert gold_calc.tier_bonus_points == 250  # 500 * (1.5 - 1.0)
        assert gold_calc.total_points == 750
        
        # Test platinum tier
        platinum_calc = await loyalty_service.calculate_points_earned(subscription_value, "platinum")
        assert platinum_calc.base_points == 500
        assert platinum_calc.tier_bonus_points == 500  # 500 * (2.0 - 1.0)
        assert platinum_calc.total_points == 1000
    
    async def test_award_subscription_points(self, loyalty_service: LoyaltyService, test_user: User, db_session: AsyncSession):
        """Test awarding points for subscription"""
        # Create a test subscription
        subscription = Subscription(
            id=uuid4(),
            user_id=test_user.id,
            price=50.0,
            currency="USD",
            billing_cycle="monthly",
            status="active"
        )
        db_session.add(subscription)
        await db_session.commit()
        
        # Award points
        transaction = await loyalty_service.award_subscription_points(
            user_id=test_user.id,
            subscription_id=subscription.id,
            subscription_value=Decimal("50.00"),
            description="Test subscription points"
        )
        
        assert transaction is not None
        assert transaction.points_amount == 500  # Bronze tier: 50 * 10 * 1.0
        assert transaction.transaction_type == "earned"
        assert transaction.reason_code == "subscription_purchase"
        
        # Check loyalty account was updated
        account = await loyalty_service.get_or_create_loyalty_account(test_user.id)
        assert account.total_points == 500
        assert account.available_points == 500
        assert account.points_earned_lifetime == 500
    
    async def test_calculate_loyalty_discount(self, loyalty_service: LoyaltyService, test_user: User):
        """Test loyalty discount calculation"""
        base_cost = Decimal("100.00")
        
        # Test bronze tier (0% discount)
        discount = await loyalty_service.calculate_loyalty_discount(test_user.id, base_cost)
        assert discount.discount_percentage == 0.0
        assert discount.discount_amount == Decimal("0.00")
        assert discount.final_cost == base_cost
        assert discount.tier == "bronze"
        
        # Manually set user to silver tier for testing
        account = await loyalty_service.get_or_create_loyalty_account(test_user.id)
        account.tier = "silver"
        await loyalty_service.db.commit()
        
        # Test silver tier (2% discount)
        discount = await loyalty_service.calculate_loyalty_discount(test_user.id, base_cost)
        assert discount.discount_percentage == 2.0
        assert discount.discount_amount == Decimal("2.00")
        assert discount.final_cost == Decimal("98.00")
        assert discount.tier == "silver"
    
    async def test_get_available_rewards(self, loyalty_service: LoyaltyService, test_user: User):
        """Test getting available rewards"""
        # Set user to have enough points for some rewards
        account = await loyalty_service.get_or_create_loyalty_account(test_user.id)
        account.available_points = 1000
        account.tier = "silver"
        await loyalty_service.db.commit()
        
        rewards = await loyalty_service.get_available_rewards(test_user.id)
        
        # Should have rewards that user can afford with silver tier
        assert len(rewards) > 0
        
        # All rewards should be affordable
        for reward in rewards:
            assert reward.points_required <= 1000
            assert reward.is_available is True
    
    async def test_redeem_points(self, loyalty_service: LoyaltyService, test_user: User):
        """Test points redemption"""
        # Set user to have enough points
        account = await loyalty_service.get_or_create_loyalty_account(test_user.id)
        account.available_points = 1000
        account.total_points = 1000
        await loyalty_service.db.commit()
        
        # Get available rewards
        rewards = await loyalty_service.get_available_rewards(test_user.id)
        assert len(rewards) > 0
        
        # Redeem first available reward
        reward = rewards[0]
        redemption = await loyalty_service.redeem_points(
            user_id=test_user.id,
            reward_id=reward.id,
            points_to_redeem=reward.points_required
        )
        
        assert redemption is not None
        assert redemption.points_redeemed == reward.points_required
        assert redemption.reward_id == reward.id
        assert redemption.remaining_points == 1000 - reward.points_required
        assert redemption.redemption_code is not None
    
    async def test_process_referral_bonus(self, loyalty_service: LoyaltyService, test_user: User, db_session: AsyncSession):
        """Test referral bonus processing"""
        # Create referee user
        referee = User(
            id=uuid4(),
            email="referee@example.com",
            firstname="Referee",
            lastname="User",
            hashed_password="hashed_password",
            is_verified=True
        )
        db_session.add(referee)
        
        # Create subscription that qualifies for referral
        subscription = Subscription(
            id=uuid4(),
            user_id=referee.id,
            price=50.0,  # Above minimum threshold
            currency="USD",
            billing_cycle="monthly",
            status="active"
        )
        db_session.add(subscription)
        await db_session.commit()
        
        # Process referral bonus
        bonus = await loyalty_service.process_referral_bonus(
            referrer_id=test_user.id,
            referee_id=referee.id,
            subscription_id=subscription.id
        )
        
        assert bonus is not None
        assert bonus.referrer_bonus_points == 500  # From config
        assert bonus.referee_bonus_points == 250   # From config
        
        # Check both accounts were updated
        referrer_account = await loyalty_service.get_or_create_loyalty_account(test_user.id)
        referee_account = await loyalty_service.get_or_create_loyalty_account(referee.id)
        
        assert referrer_account.total_points == 500
        assert referrer_account.successful_referrals == 1
        assert referee_account.total_points == 250
    
    async def test_get_personalized_offers(self, loyalty_service: LoyaltyService, test_user: User):
        """Test personalized offers generation"""
        offers = await loyalty_service.get_personalized_offers(test_user.id, limit=3)
        
        assert isinstance(offers, list)
        assert len(offers) <= 3
        
        # Check offer structure
        if offers:
            offer = offers[0]
            assert hasattr(offer, 'id')
            assert hasattr(offer, 'title')
            assert hasattr(offer, 'description')
            assert hasattr(offer, 'offer_type')
            assert hasattr(offer, 'valid_until')
            assert hasattr(offer, 'personalization_reason')


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])