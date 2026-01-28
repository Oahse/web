from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from core.utils.uuid_utils import uuid7
from datetime import datetime, timedelta
from decimal import Decimal
import json

from models.loyalty import LoyaltyAccount, PointsTransaction
from models.user import User
from models.subscriptions import Subscription
from models.orders import Order
from schemas.loyalty import (
    LoyaltyAccountCreate, LoyaltyAccountUpdate, LoyaltyAccountResponse,
    PointsTransactionCreate, PointsTransactionResponse,
    PointsCalculationResponse, ReferralBonusResponse, AvailableReward,
    RedemptionResponse, LoyaltyDiscountResponse, TierAdvancementResponse,
    PersonalizedOffer, LoyaltyAnalyticsResponse
)
from core.exceptions import APIException
from core.logging import structured_logger
from core.config import settings


class LoyaltyService:
    """Service for managing customer loyalty and rewards system"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
        # Tier configuration
        self.tier_config = {
            "bronze": {
                "min_points": 0,
                "max_points": 999,
                "points_multiplier": 1.0,
                "discount_percentage": 0.0,
                "benefits": {
                    "early_access": False,
                    "exclusive_products": False,
                    "birthday_bonus": 50
                }
            },
            "silver": {
                "min_points": 1000,
                "max_points": 4999,
                "points_multiplier": 1.2,
                "discount_percentage": 2.0,
                "benefits": {
                    "early_access": False,
                    "exclusive_products": False,
                    "birthday_bonus": 100
                }
            },
            "gold": {
                "min_points": 5000,
                "max_points": 14999,
                "points_multiplier": 1.5,
                "discount_percentage": 5.0,
                "benefits": {
                    "early_access": True,
                    "exclusive_products": False,
                    "birthday_bonus": 200
                }
            },
            "platinum": {
                "min_points": 15000,
                "max_points": float('inf'),
                "points_multiplier": 2.0,
                "discount_percentage": 10.0,
                "benefits": {
                    "early_access": True,
                    "exclusive_products": True,
                    "birthday_bonus": 500
                }
            }
        }
        
        # Points earning rates (points per dollar spent)
        self.base_points_rate = 10  # 10 points per $1 spent
        
        # Referral bonus configuration
        self.referral_config = {
            "referrer_bonus": 500,  # Points for successful referrer
            "referee_bonus": 250,   # Points for new referee
            "minimum_subscription_value": 25.0  # Minimum subscription value to qualify
        }

    # ============================================================================
    # LOYALTY ACCOUNT MANAGEMENT
    # ============================================================================

    async def get_or_create_loyalty_account(self, user_id: UUID, for_update: bool = False) -> LoyaltyAccount:
        """Get existing loyalty account or create new one for user with optional locking"""
        try:
            # Check if loyalty account exists with optional lock
            query = select(LoyaltyAccount).where(LoyaltyAccount.user_id == user_id)
            if for_update:
                query = query.with_for_update()
                
            result = await self.db.execute(query)
            loyalty_account = result.scalar_one_or_none()
            
            if not loyalty_account:
                # Create new loyalty account
                loyalty_account = LoyaltyAccount(
                    id=uuid7(),
                    user_id=user_id,
                    tier="bronze",
                    tier_benefits=self.tier_config["bronze"]["benefits"]
                )
                self.db.add(loyalty_account)
                await self.db.commit()
                await self.db.refresh(loyalty_account)
                
                structured_logger.info(
                    message="Created new loyalty account",
                    metadata={"user_id": str(user_id), "loyalty_account_id": str(loyalty_account.id)}
                )
            
            return loyalty_account
            
        except Exception as e:
            structured_logger.error(
                message="Failed to get or create loyalty account",
                metadata={"user_id": str(user_id)},
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to access loyalty account"
            )

    async def get_loyalty_account(self, user_id: UUID) -> Optional[LoyaltyAccountResponse]:
        """Get loyalty account for user"""
        try:
            loyalty_account = await self.get_or_create_loyalty_account(user_id)
            return LoyaltyAccountResponse.from_orm(loyalty_account)
            
        except Exception as e:
            structured_logger.error(
                message="Failed to get loyalty account",
                metadata={"user_id": str(user_id)},
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to retrieve loyalty account"
            )

    async def update_loyalty_account(
        self,
        user_id: UUID,
        update_data: LoyaltyAccountUpdate
    ) -> LoyaltyAccountResponse:
        """Update loyalty account"""
        try:
            loyalty_account = await self.get_or_create_loyalty_account(user_id)
            
            # Update fields
            for field, value in update_data.dict(exclude_unset=True).items():
                if hasattr(loyalty_account, field):
                    setattr(loyalty_account, field, value)
            
            loyalty_account.updated_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(loyalty_account)
            
            return LoyaltyAccountResponse.from_orm(loyalty_account)
            
        except Exception as e:
            structured_logger.error(
                message="Failed to update loyalty account",
                metadata={"user_id": str(user_id)},
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to update loyalty account"
            )

    # ============================================================================
    # POINTS CALCULATION AND EARNING
    # ============================================================================

    async def calculate_points_earned(
        self,
        subscription_value: Decimal,
        user_tier: str
    ) -> PointsCalculationResponse:
        """
        Calculate points earned based on subscription value and user tier.
        
        Args:
            subscription_value: Subscription value for points calculation
            user_tier: User tier for calculation
            
        Returns:
            PointsCalculationResponse with detailed calculation
        """
        try:
            # Validate tier
            if user_tier not in self.tier_config:
                raise APIException(
                    status_code=400,
                    message=f"Invalid tier: {user_tier}"
                )
            
            tier_info = self.tier_config[user_tier]
            
            # Calculate base points (points per dollar)
            base_points = int(subscription_value * self.base_points_rate)
            
            # Apply tier multiplier
            tier_multiplier = tier_info["points_multiplier"]
            tier_bonus_points = round(base_points * (tier_multiplier - 1.0))
            total_points = base_points + tier_bonus_points
            
            calculation_details = {
                "subscription_value": float(subscription_value),
                "base_points_rate": self.base_points_rate,
                "tier": user_tier,
                "tier_multiplier": tier_multiplier,
                "base_calculation": f"{float(subscription_value)} × {self.base_points_rate} = {base_points}",
                "tier_bonus_calculation": f"{base_points} × ({tier_multiplier} - 1.0) = {tier_bonus_points}",
                "total_calculation": f"{base_points} + {tier_bonus_points} = {total_points}"
            }
            
            return PointsCalculationResponse(
                base_points=base_points,
                tier_bonus_points=tier_bonus_points,
                total_points=total_points,
                tier_multiplier=tier_multiplier,
                calculation_details=calculation_details
            )
            
        except APIException:
            raise
        except Exception as e:
            structured_logger.error(
                message="Failed to calculate points earned",
                metadata={
                    "subscription_value": float(subscription_value),
                    "user_tier": user_tier
                },
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to calculate points"
            )

    async def award_subscription_points(
        self,
        user_id: UUID,
        subscription_id: UUID,
        subscription_value: Decimal,
        description: str = "Points earned from subscription"
    ) -> PointsTransactionResponse:
        """Award points for subscription activity"""
        try:
            # Get loyalty account
            loyalty_account = await self.get_or_create_loyalty_account(user_id)
            
            # Calculate points
            points_calc = await self.calculate_points_earned(
                subscription_value, loyalty_account.tier
            )
            
            # Create points transaction
            transaction = PointsTransaction(
                id=uuid7(),
                loyalty_account_id=loyalty_account.id,
                subscription_id=subscription_id,
                transaction_type="earned",
                points_amount=points_calc.total_points,
                description=description,
                reason_code="subscription_purchase",
                related_amount=float(subscription_value),
                currency="USD",
                transaction_metadata={
                    "calculation_details": points_calc.calculation_details,
                    "tier_at_earning": loyalty_account.tier
                }
            )
            
            # Update loyalty account points
            loyalty_account.total_points += points_calc.total_points
            loyalty_account.available_points += points_calc.total_points
            loyalty_account.points_earned_lifetime += points_calc.total_points
            
            self.db.add(transaction)
            
            # Check for tier advancement
            await self._check_and_process_tier_advancement(loyalty_account)
            
            await self.db.commit()
            await self.db.refresh(transaction)
            
            structured_logger.info(
                message="Awarded subscription points",
                metadata={
                    "user_id": str(user_id),
                    "subscription_id": str(subscription_id),
                    "points_awarded": points_calc.total_points,
                    "subscription_value": float(subscription_value)
                }
            )
            
            return PointsTransactionResponse.from_orm(transaction)
            
        except Exception as e:
            structured_logger.error(
                message="Failed to award subscription points",
                metadata={
                    "user_id": str(user_id),
                    "subscription_id": str(subscription_id),
                    "subscription_value": float(subscription_value)
                },
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to award points"
            )

    # ============================================================================
    # REFERRAL SYSTEM
    # ============================================================================

    async def process_referral_bonus(
        self,
        referrer_id: UUID,
        referee_id: UUID,
        subscription_id: UUID
    ) -> ReferralBonusResponse:
        """
        Process referral bonus for successful referrals.
        
        Args:
            referrer_id: ID of the user making the referral
            referee_id: ID of the user being referred
            subscription_id: Subscription ID that triggered the bonus
            
        Returns:
            ReferralBonusResponse with bonus details
        """
        try:
            # Validate that users are different
            if referrer_id == referee_id:
                raise APIException(
                    status_code=400,
                    message="Users cannot refer themselves"
                )
            
            # Get subscription to validate minimum value
            subscription_result = await self.db.execute(
                select(Subscription).where(Subscription.id == subscription_id)
            )
            subscription = subscription_result.scalar_one_or_none()
            
            if not subscription:
                raise APIException(
                    status_code=404,
                    message="Subscription not found"
                )
            
            # Check minimum subscription value
            if subscription.price < self.referral_config["minimum_subscription_value"]:
                raise APIException(
                    status_code=400,
                    message=f"Subscription value must be at least ${self.referral_config['minimum_subscription_value']}"
                )
            
            # Get loyalty accounts
            referrer_account = await self.get_or_create_loyalty_account(referrer_id)
            referee_account = await self.get_or_create_loyalty_account(referee_id)
            
            # Check if referral already processed
            existing_referral = await self.db.execute(
                select(PointsTransaction).where(
                    and_(
                        PointsTransaction.loyalty_account_id.in_([referrer_account.id, referee_account.id]),
                        PointsTransaction.subscription_id == subscription_id,
                        PointsTransaction.reason_code == "referral_bonus"
                    )
                )
            )
            
            if existing_referral.scalar_one_or_none():
                raise APIException(
                    status_code=400,
                    message="Referral bonus already processed for this subscription"
                )
            
            # Create referrer bonus transaction
            referrer_transaction = PointsTransaction(
                id=uuid7(),
                loyalty_account_id=referrer_account.id,
                subscription_id=subscription_id,
                transaction_type="referral",
                points_amount=self.referral_config["referrer_bonus"],
                description=f"Referral bonus for referring user {referee_id}",
                reason_code="referral_bonus",
                related_amount=subscription.price,
                currency=subscription.currency or "USD",
                transaction_metadata={
                    "referral_type": "referrer",
                    "referee_id": str(referee_id),
                    "subscription_value": subscription.price
                }
            )
            
            # Create referee bonus transaction
            referee_transaction = PointsTransaction(
                id=uuid7(),
                loyalty_account_id=referee_account.id,
                subscription_id=subscription_id,
                transaction_type="bonus",
                points_amount=self.referral_config["referee_bonus"],
                description=f"Welcome bonus for being referred by user {referrer_id}",
                reason_code="referral_bonus",
                related_amount=subscription.price,
                currency=subscription.currency or "USD",
                transaction_metadata={
                    "referral_type": "referee",
                    "referrer_id": str(referrer_id),
                    "subscription_value": subscription.price
                }
            )
            
            # Update loyalty accounts
            referrer_account.total_points += self.referral_config["referrer_bonus"]
            referrer_account.available_points += self.referral_config["referrer_bonus"]
            referrer_account.points_earned_lifetime += self.referral_config["referrer_bonus"]
            referrer_account.referrals_made += 1
            referrer_account.successful_referrals += 1
            
            referee_account.total_points += self.referral_config["referee_bonus"]
            referee_account.available_points += self.referral_config["referee_bonus"]
            referee_account.points_earned_lifetime += self.referral_config["referee_bonus"]
            
            self.db.add(referrer_transaction)
            self.db.add(referee_transaction)
            
            # Check for tier advancement for both accounts
            await self._check_and_process_tier_advancement(referrer_account)
            await self._check_and_process_tier_advancement(referee_account)
            
            await self.db.commit()
            await self.db.refresh(referrer_transaction)
            await self.db.refresh(referee_transaction)
            
            bonus_details = {
                "referrer_id": str(referrer_id),
                "referee_id": str(referee_id),
                "subscription_id": str(subscription_id),
                "subscription_value": subscription.price,
                "referrer_new_total": referrer_account.total_points,
                "referee_new_total": referee_account.total_points,
                "processed_at": datetime.utcnow().isoformat()
            }
            
            structured_logger.info(
                message="Processed referral bonus",
                metadata=bonus_details
            )
            
            return ReferralBonusResponse(
                referrer_bonus_points=self.referral_config["referrer_bonus"],
                referee_bonus_points=self.referral_config["referee_bonus"],
                referrer_transaction_id=referrer_transaction.id,
                referee_transaction_id=referee_transaction.id,
                bonus_details=bonus_details
            )
            
        except APIException:
            raise
        except Exception as e:
            structured_logger.error(
                message="Failed to process referral bonus",
                metadata={
                    "referrer_id": str(referrer_id),
                    "referee_id": str(referee_id),
                    "subscription_id": str(subscription_id)
                },
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to process referral bonus"
            )

    # ============================================================================
    # REWARDS AND REDEMPTION
    # ============================================================================

    async def get_available_rewards(self, user_id: UUID) -> List[AvailableReward]:
        """
        Get available rewards for user based on their points and tier.
        
        Args:
            user_id: User ID to get rewards for
            
        Returns:
            List of available rewards
        """
        try:
            loyalty_account = await self.get_or_create_loyalty_account(user_id)
            
            # Define available rewards based on tier and points
            all_rewards = [
                {
                    "id": "discount_5",
                    "name": "5% Discount",
                    "description": "Get 5% off your next subscription",
                    "points_required": 500,
                    "reward_type": "discount",
                    "reward_value": 5.0,
                    "terms_and_conditions": "Valid for one subscription payment. Cannot be combined with other offers.",
                    "min_tier": "bronze"
                },
                {
                    "id": "discount_10",
                    "name": "10% Discount",
                    "description": "Get 10% off your next subscription",
                    "points_required": 1000,
                    "reward_type": "discount",
                    "reward_value": 10.0,
                    "terms_and_conditions": "Valid for one subscription payment. Cannot be combined with other offers.",
                    "min_tier": "silver"
                },
                {
                    "id": "free_shipping",
                    "name": "Free Shipping",
                    "description": "Free shipping on your next order",
                    "points_required": 300,
                    "reward_type": "free_shipping",
                    "reward_value": 15.0,
                    "terms_and_conditions": "Valid for one order. Standard shipping only.",
                    "min_tier": "bronze"
                },
                {
                    "id": "discount_15",
                    "name": "15% Discount",
                    "description": "Get 15% off your next subscription",
                    "points_required": 2000,
                    "reward_type": "discount",
                    "reward_value": 15.0,
                    "terms_and_conditions": "Valid for one subscription payment. Cannot be combined with other offers.",
                    "min_tier": "gold"
                },
                {
                    "id": "free_month",
                    "name": "Free Month",
                    "description": "Get one month of subscription free",
                    "points_required": 5000,
                    "reward_type": "free_subscription",
                    "reward_value": 50.0,
                    "terms_and_conditions": "Valid for one billing cycle. Based on current subscription value.",
                    "min_tier": "platinum"
                },
                {
                    "id": "exclusive_access",
                    "name": "Exclusive Product Access",
                    "description": "Early access to new products",
                    "points_required": 1500,
                    "reward_type": "exclusive_access",
                    "reward_value": 0.0,
                    "terms_and_conditions": "Access to exclusive products for 30 days.",
                    "min_tier": "gold"
                }
            ]
            
            # Filter rewards based on user's tier and available points
            tier_hierarchy = ["bronze", "silver", "gold", "platinum"]
            user_tier_level = tier_hierarchy.index(loyalty_account.tier)
            
            available_rewards = []
            for reward_data in all_rewards:
                min_tier_level = tier_hierarchy.index(reward_data["min_tier"])
                
                # Check if user's tier qualifies and they have enough points
                if (user_tier_level >= min_tier_level and 
                    loyalty_account.available_points >= reward_data["points_required"]):
                    
                    reward = AvailableReward(
                        id=reward_data["id"],
                        name=reward_data["name"],
                        description=reward_data["description"],
                        points_required=reward_data["points_required"],
                        reward_type=reward_data["reward_type"],
                        reward_value=reward_data["reward_value"],
                        terms_and_conditions=reward_data["terms_and_conditions"],
                        is_available=True,
                        metadata={
                            "min_tier": reward_data["min_tier"],
                            "user_tier": loyalty_account.tier,
                            "user_points": loyalty_account.available_points
                        }
                    )
                    available_rewards.append(reward)
            
            return available_rewards
            
        except Exception as e:
            structured_logger.error(
                message="Failed to get available rewards",
                metadata={"user_id": str(user_id)},
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to retrieve available rewards"
            )

    async def redeem_points(
        self,
        user_id: UUID,
        reward_id: str,
        points_to_redeem: int
    ) -> RedemptionResponse:
        """
        Redeem points for a reward.
        
        Args:
            user_id: User ID redeeming points
            reward_id: Reward ID to redeem
            points_to_redeem: Number of points to redeem
            
        Returns:
            RedemptionResponse with redemption details
        """
        try:
            loyalty_account = await self.get_or_create_loyalty_account(user_id, for_update=True)
            
            # Check if user has enough points (with locked account)
            if loyalty_account.available_points < points_to_redeem:
                raise APIException(
                    status_code=400,
                    message=f"Insufficient points. Available: {loyalty_account.available_points}, Required: {points_to_redeem}"
                )
            
            # Get available rewards to validate the reward
            available_rewards = await self.get_available_rewards(user_id)
            reward = next((r for r in available_rewards if r.id == reward_id), None)
            
            if not reward:
                raise APIException(
                    status_code=404,
                    message="Reward not found or not available"
                )
            
            if points_to_redeem != reward.points_required:
                raise APIException(
                    status_code=400,
                    message=f"Invalid points amount. Required: {reward.points_required}"
                )
            
            # Generate redemption code
            redemption_code = f"BANWEE-{reward_id.upper()}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Create redemption transaction
            transaction = PointsTransaction(
                id=uuid7(),
                loyalty_account_id=loyalty_account.id,
                transaction_type="redeemed",
                points_amount=-points_to_redeem,  # Negative for redemption
                description=f"Redeemed {reward.name}",
                reason_code="reward_redemption",
                status="completed",
                transaction_metadata={
                    "reward_id": reward_id,
                    "reward_name": reward.name,
                    "reward_type": reward.reward_type,
                    "reward_value": reward.reward_value,
                    "redemption_code": redemption_code
                }
            )
            
            # Update loyalty account
            loyalty_account.available_points -= points_to_redeem
            loyalty_account.points_redeemed_lifetime += points_to_redeem
            
            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(transaction)
            
            # Calculate expiry date (30 days from redemption)
            expiry_date = datetime.utcnow() + timedelta(days=30)
            
            redemption_details = {
                "reward_id": reward_id,
                "reward_name": reward.name,
                "reward_type": reward.reward_type,
                "redemption_code": redemption_code,
                "redeemed_at": datetime.utcnow().isoformat(),
                "expires_at": expiry_date.isoformat(),
                "user_tier": loyalty_account.tier,
                "remaining_points": loyalty_account.available_points
            }
            
            structured_logger.info(
                message="Points redeemed successfully",
                metadata={
                    "user_id": str(user_id),
                    "reward_id": reward_id,
                    "points_redeemed": points_to_redeem,
                    "redemption_code": redemption_code
                }
            )
            
            return RedemptionResponse(
                transaction_id=transaction.id,
                reward_id=reward_id,
                points_redeemed=points_to_redeem,
                reward_value=reward.reward_value,
                remaining_points=loyalty_account.available_points,
                redemption_code=redemption_code,
                expiry_date=expiry_date,
                redemption_details=redemption_details
            )
            
        except APIException:
            raise
        except Exception as e:
            structured_logger.error(
                message="Failed to redeem points",
                metadata={
                    "user_id": str(user_id),
                    "reward_id": reward_id,
                    "points_to_redeem": points_to_redeem
                },
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to redeem points"
            )

    # ============================================================================
    # TIER MANAGEMENT
    # ============================================================================

    async def _check_and_process_tier_advancement(self, loyalty_account: LoyaltyAccount) -> Optional[TierAdvancementResponse]:
        """Check if user qualifies for tier advancement and process it"""
        try:
            current_tier = loyalty_account.tier
            current_points = loyalty_account.total_points
            
            # Determine new tier based on points
            new_tier = current_tier
            for tier, config in self.tier_config.items():
                if (current_points >= config["min_points"] and 
                    current_points <= config["max_points"]):
                    new_tier = tier
                    break
            
            # If tier changed, update account
            if new_tier != current_tier:
                old_tier = current_tier
                loyalty_account.tier = new_tier
                loyalty_account.tier_benefits = self.tier_config[new_tier]["benefits"]
                
                # Calculate progress in new tier
                tier_config = self.tier_config[new_tier]
                if tier_config["max_points"] == float('inf'):
                    loyalty_account.tier_progress = 1.0
                else:
                    points_in_tier = current_points - tier_config["min_points"]
                    tier_range = tier_config["max_points"] - tier_config["min_points"]
                    loyalty_account.tier_progress = min(1.0, points_in_tier / tier_range)
                
                # Create advancement transaction
                advancement_transaction = PointsTransaction(
                    id=uuid7(),
                    loyalty_account_id=loyalty_account.id,
                    transaction_type="bonus",
                    points_amount=0,  # No points awarded, just tracking
                    description=f"Tier advancement from {old_tier} to {new_tier}",
                    reason_code="tier_advancement",
                    transaction_metadata={
                        "old_tier": old_tier,
                        "new_tier": new_tier,
                        "advancement_points": current_points,
                        "new_benefits": loyalty_account.tier_benefits
                    }
                )
                
                self.db.add(advancement_transaction)
                
                structured_logger.info(
                    message="User tier advanced",
                    metadata={
                        "user_id": str(loyalty_account.user_id),
                        "old_tier": old_tier,
                        "new_tier": new_tier,
                        "total_points": current_points
                    }
                )
                
                return TierAdvancementResponse(
                    old_tier=old_tier,
                    new_tier=new_tier,
                    tier_progress=loyalty_account.tier_progress,
                    new_benefits=loyalty_account.tier_benefits,
                    advancement_date=datetime.utcnow(),
                    celebration_message=f"Congratulations! You've been promoted to {new_tier.title()} tier!"
                )
            else:
                # Update progress in current tier
                tier_config = self.tier_config[current_tier]
                if tier_config["max_points"] == float('inf'):
                    loyalty_account.tier_progress = 1.0
                else:
                    points_in_tier = current_points - tier_config["min_points"]
                    tier_range = tier_config["max_points"] - tier_config["min_points"]
                    loyalty_account.tier_progress = min(1.0, points_in_tier / tier_range)
            
            return None
            
        except Exception as e:
            structured_logger.error(
                message="Failed to check tier advancement",
                metadata={"loyalty_account_id": str(loyalty_account.id)},
                exception=e
            )
            return None

    # ============================================================================
    # LOYALTY DISCOUNT INTEGRATION
    # ============================================================================

    async def calculate_loyalty_discount(
        self,
        user_id: UUID,
        base_cost: Decimal
    ) -> LoyaltyDiscountResponse:
        """
        Calculate loyalty discount for subscription cost.
        
        Args:
            user_id: User ID for loyalty calculation
            base_cost: Base cost before discount
            
        Returns:
            LoyaltyDiscountResponse with discount details
        """
        try:
            loyalty_account = await self.get_or_create_loyalty_account(user_id)
            
            # Get tier discount percentage
            tier_config = self.tier_config[loyalty_account.tier]
            discount_percentage = tier_config["discount_percentage"]
            
            # Calculate discount amount
            discount_amount = base_cost * Decimal(str(discount_percentage / 100))
            final_cost = base_cost - discount_amount
            
            discount_details = {
                "tier": loyalty_account.tier,
                "tier_discount_percentage": discount_percentage,
                "base_cost": float(base_cost),
                "discount_calculation": f"{float(base_cost)} × {discount_percentage}% = {float(discount_amount)}",
                "final_cost": float(final_cost),
                "savings": float(discount_amount)
            }
            
            return LoyaltyDiscountResponse(
                discount_amount=discount_amount,
                discount_percentage=discount_percentage,
                final_cost=final_cost,
                tier=loyalty_account.tier,
                discount_details=discount_details
            )
            
        except Exception as e:
            structured_logger.error(
                message="Failed to calculate loyalty discount",
                metadata={
                    "user_id": str(user_id),
                    "base_cost": float(base_cost)
                },
                exception=e
            )
            # Return no discount on error
            return LoyaltyDiscountResponse(
                discount_amount=Decimal('0'),
                discount_percentage=0.0,
                final_cost=base_cost,
                tier="bronze",
                discount_details={"error": "Failed to calculate discount"}
            )

    # ============================================================================
    # PERSONALIZED OFFERS
    # ============================================================================

    async def get_personalized_offers(
        self,
        user_id: UUID,
        limit: int = 5
    ) -> List[PersonalizedOffer]:
        """
        Generate personalized offers based on purchase history and preferences.
        
        Args:
            user_id: User ID for personalized offers
            limit: Maximum number of offers to return
            
        Returns:
            List of personalized offers
        """
        try:
            loyalty_account = await self.get_or_create_loyalty_account(user_id)
            
            # Get user's subscription history
            subscription_history = await self.db.execute(
                select(Subscription).where(
                    Subscription.user_id == user_id
                ).order_by(desc(Subscription.created_at)).limit(10)
            )
            subscriptions = subscription_history.scalars().all()
            
            offers = []
            
            # Tier-based offers
            if loyalty_account.tier == "bronze":
                offers.append(PersonalizedOffer(
                    id="tier_upgrade_silver",
                    title="Upgrade to Silver Tier",
                    description="Earn just 200 more points to unlock Silver benefits!",
                    offer_type="tier_progress",
                    bonus_points=50,
                    valid_until=datetime.utcnow() + timedelta(days=30),
                    personalization_reason="You're close to Silver tier"
                ))
            
            # Subscription-based offers
            if len(subscriptions) > 0:
                avg_subscription_value = sum(s.price or 0 for s in subscriptions) / len(subscriptions)
                
                if avg_subscription_value > 50:
                    offers.append(PersonalizedOffer(
                        id="premium_subscriber_bonus",
                        title="Premium Subscriber Bonus",
                        description="Double points on your next subscription!",
                        offer_type="bonus_points",
                        bonus_points=int(avg_subscription_value * 20),  # 2x normal rate
                        valid_until=datetime.utcnow() + timedelta(days=14),
                        personalization_reason="Based on your premium subscription history"
                    ))
            
            # Referral offers
            if loyalty_account.referrals_made == 0:
                offers.append(PersonalizedOffer(
                    id="first_referral_bonus",
                    title="First Referral Bonus",
                    description="Refer a friend and get 750 bonus points!",
                    offer_type="referral_bonus",
                    bonus_points=750,
                    valid_until=datetime.utcnow() + timedelta(days=60),
                    personalization_reason="You haven't made any referrals yet"
                ))
            
            # Loyalty milestone offers
            if loyalty_account.total_points > 0 and loyalty_account.total_points % 1000 < 100:
                milestone = ((loyalty_account.total_points // 1000) + 1) * 1000
                offers.append(PersonalizedOffer(
                    id=f"milestone_{milestone}",
                    title=f"Milestone Reward - {milestone} Points",
                    description=f"You're close to {milestone} points! Get 15% off when you reach it.",
                    offer_type="milestone_discount",
                    discount_percentage=15.0,
                    valid_until=datetime.utcnow() + timedelta(days=45),
                    personalization_reason=f"You're approaching the {milestone} points milestone"
                ))
            
            # Birthday offers (simplified - would need user birthday in real implementation)
            offers.append(PersonalizedOffer(
                id="birthday_special",
                title="Birthday Month Special",
                description="Celebrate with us! Extra points on all purchases this month.",
                offer_type="birthday_bonus",
                bonus_points=self.tier_config[loyalty_account.tier]["benefits"]["birthday_bonus"],
                valid_until=datetime.utcnow() + timedelta(days=30),
                personalization_reason="It's your birthday month!"
            ))
            
            return offers[:limit]
            
        except Exception as e:
            structured_logger.error(
                message="Failed to get personalized offers",
                metadata={"user_id": str(user_id), "limit": limit},
                exception=e
            )
            return []

    # ============================================================================
    # ANALYTICS AND REPORTING
    # ============================================================================

    async def get_loyalty_analytics(self) -> LoyaltyAnalyticsResponse:
        """Get comprehensive loyalty program analytics"""
        try:
            # Total and active members
            total_members_result = await self.db.execute(
                select(func.count(LoyaltyAccount.id))
            )
            total_members = total_members_result.scalar_one()
            
            active_members_result = await self.db.execute(
                select(func.count(LoyaltyAccount.id)).where(
                    LoyaltyAccount.status == "active"
                )
            )
            active_members = active_members_result.scalar_one()
            
            # Tier distribution
            tier_distribution_result = await self.db.execute(
                select(LoyaltyAccount.tier, func.count(LoyaltyAccount.id)).group_by(
                    LoyaltyAccount.tier
                )
            )
            tier_distribution = dict(tier_distribution_result.fetchall())
            
            # Points statistics
            points_stats_result = await self.db.execute(
                select(
                    func.sum(LoyaltyAccount.points_earned_lifetime),
                    func.sum(LoyaltyAccount.points_redeemed_lifetime),
                    func.avg(LoyaltyAccount.total_points)
                )
            )
            points_stats = points_stats_result.fetchone()
            
            total_points_issued = points_stats[0] or 0
            total_points_redeemed = points_stats[1] or 0
            average_points_per_member = float(points_stats[2] or 0)
            
            # Top earners
            top_earners_result = await self.db.execute(
                select(LoyaltyAccount.user_id, LoyaltyAccount.points_earned_lifetime, LoyaltyAccount.tier)
                .order_by(desc(LoyaltyAccount.points_earned_lifetime))
                .limit(10)
            )
            top_earners = [
                {
                    "user_id": str(row[0]),
                    "points_earned": row[1],
                    "tier": row[2]
                }
                for row in top_earners_result.fetchall()
            ]
            
            # Redemption trends (simplified)
            redemption_trends = {
                "total_redemptions": total_points_redeemed,
                "redemption_rate": (total_points_redeemed / total_points_issued * 100) if total_points_issued > 0 else 0,
                "average_redemption_per_member": total_points_redeemed / active_members if active_members > 0 else 0
            }
            
            # Referral statistics
            referral_stats_result = await self.db.execute(
                select(
                    func.sum(LoyaltyAccount.referrals_made),
                    func.sum(LoyaltyAccount.successful_referrals)
                )
            )
            referral_stats = referral_stats_result.fetchone()
            
            referral_statistics = {
                "total_referrals_made": referral_stats[0] or 0,
                "successful_referrals": referral_stats[1] or 0,
                "referral_success_rate": (referral_stats[1] / referral_stats[0] * 100) if referral_stats[0] and referral_stats[0] > 0 else 0,
                "average_referrals_per_member": (referral_stats[0] / active_members) if active_members > 0 else 0
            }
            
            return LoyaltyAnalyticsResponse(
                total_members=total_members,
                active_members=active_members,
                tier_distribution=tier_distribution,
                total_points_issued=total_points_issued,
                total_points_redeemed=total_points_redeemed,
                average_points_per_member=average_points_per_member,
                top_earners=top_earners,
                redemption_trends=redemption_trends,
                referral_statistics=referral_statistics
            )
            
        except Exception as e:
            structured_logger.error(
                message="Failed to get loyalty analytics",
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to retrieve loyalty analytics"
            )

    # ============================================================================
    # POINTS TRANSACTION HISTORY
    # ============================================================================

    async def get_points_history(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get points transaction history for user"""
        try:
            loyalty_account = await self.get_or_create_loyalty_account(user_id)
            
            # Build query
            query = select(PointsTransaction).where(
                PointsTransaction.loyalty_account_id == loyalty_account.id
            )
            
            if transaction_type:
                query = query.where(PointsTransaction.transaction_type == transaction_type)
            
            query = query.order_by(desc(PointsTransaction.created_at)).offset(offset).limit(limit)
            
            # Get transactions
            result = await self.db.execute(query)
            transactions = result.scalars().all()
            
            # Get total count
            count_query = select(func.count(PointsTransaction.id)).where(
                PointsTransaction.loyalty_account_id == loyalty_account.id
            )
            if transaction_type:
                count_query = count_query.where(PointsTransaction.transaction_type == transaction_type)
            
            total_count_result = await self.db.execute(count_query)
            total_count = total_count_result.scalar_one()
            
            return {
                "transactions": [PointsTransactionResponse.from_orm(t) for t in transactions],
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + len(transactions)) < total_count,
                "account_summary": {
                    "total_points": loyalty_account.total_points,
                    "available_points": loyalty_account.available_points,
                    "tier": loyalty_account.tier,
                    "points_earned_lifetime": loyalty_account.points_earned_lifetime,
                    "points_redeemed_lifetime": loyalty_account.points_redeemed_lifetime
                }
            }
            
        except Exception as e:
            structured_logger.error(
                message="Failed to get points history",
                metadata={
                    "user_id": str(user_id),
                    "limit": limit,
                    "offset": offset,
                    "transaction_type": transaction_type
                },
                exception=e
            )
            raise APIException(
                status_code=500,
                message="Failed to retrieve points history"
            )