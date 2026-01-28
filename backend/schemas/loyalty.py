from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class LoyaltyAccountBase(BaseModel):
    """Base loyalty account schema"""
    tier: str = Field(default="bronze", description="Customer tier (bronze, silver, gold, platinum)")
    status: str = Field(default="active", description="Account status")
    tier_benefits: Optional[Dict[str, Any]] = Field(default=None, description="Tier-specific benefits")
    loyalty_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    @validator('tier')
    def validate_tier(cls, v):
        valid_tiers = ["bronze", "silver", "gold", "platinum"]
        if v not in valid_tiers:
            raise ValueError(f"Tier must be one of: {valid_tiers}")
        return v

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["active", "suspended", "closed"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class LoyaltyAccountCreate(LoyaltyAccountBase):
    """Schema for creating a loyalty account"""
    user_id: UUID = Field(..., description="User ID for the loyalty account")


class LoyaltyAccountUpdate(LoyaltyAccountBase):
    """Schema for updating a loyalty account"""
    tier: Optional[str] = None
    status: Optional[str] = None


class LoyaltyAccountResponse(LoyaltyAccountBase):
    """Schema for loyalty account response"""
    id: UUID
    user_id: UUID
    total_points: int
    available_points: int
    tier_progress: float = Field(..., description="Progress to next tier (0.0 to 1.0)")
    points_earned_lifetime: int
    points_redeemed_lifetime: int
    referrals_made: int
    successful_referrals: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PointsTransactionBase(BaseModel):
    """Base points transaction schema"""
    transaction_type: str = Field(..., description="Type of transaction (earned, redeemed, bonus, referral, adjustment)")
    points_amount: int = Field(..., description="Points amount (positive for earned, negative for redeemed)")
    description: str = Field(..., description="Transaction description")
    reason_code: Optional[str] = Field(default=None, description="Reason code for the transaction")
    related_amount: Optional[float] = Field(default=None, description="Dollar amount that generated points")
    currency: str = Field(default="USD", description="Currency for related amount")
    expires_at: Optional[str] = Field(default=None, description="Expiration date for earned points")
    status: str = Field(default="completed", description="Transaction status")
    transaction_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        valid_types = ["earned", "redeemed", "bonus", "referral", "adjustment"]
        if v not in valid_types:
            raise ValueError(f"Transaction type must be one of: {valid_types}")
        return v

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["pending", "completed", "cancelled", "expired"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {valid_statuses}")
        return v


class PointsTransactionCreate(PointsTransactionBase):
    """Schema for creating a points transaction"""
    loyalty_account_id: UUID = Field(..., description="Loyalty account ID")
    subscription_id: Optional[UUID] = Field(default=None, description="Related subscription ID")
    order_id: Optional[UUID] = Field(default=None, description="Related order ID")


class PointsTransactionResponse(PointsTransactionBase):
    """Schema for points transaction response"""
    id: UUID
    loyalty_account_id: UUID
    subscription_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PointsCalculationRequest(BaseModel):
    """Schema for points calculation request"""
    subscription_value: Decimal = Field(..., description="Subscription value for points calculation")
    user_tier: str = Field(..., description="User tier for calculation")

    @validator('user_tier')
    def validate_tier(cls, v):
        valid_tiers = ["bronze", "silver", "gold", "platinum"]
        if v not in valid_tiers:
            raise ValueError(f"Tier must be one of: {valid_tiers}")
        return v


class PointsCalculationResponse(BaseModel):
    """Schema for points calculation response"""
    base_points: int = Field(..., description="Base points earned")
    tier_bonus_points: int = Field(..., description="Bonus points from tier")
    total_points: int = Field(..., description="Total points earned")
    tier_multiplier: float = Field(..., description="Tier multiplier applied")
    calculation_details: Dict[str, Any] = Field(..., description="Detailed calculation breakdown")


class ReferralBonusRequest(BaseModel):
    """Schema for referral bonus request"""
    referrer_id: UUID = Field(..., description="ID of the user making the referral")
    referee_id: UUID = Field(..., description="ID of the user being referred")
    subscription_id: UUID = Field(..., description="Subscription ID that triggered the bonus")


class ReferralBonusResponse(BaseModel):
    """Schema for referral bonus response"""
    referrer_bonus_points: int = Field(..., description="Points awarded to referrer")
    referee_bonus_points: int = Field(..., description="Points awarded to referee")
    referrer_transaction_id: UUID = Field(..., description="Transaction ID for referrer bonus")
    referee_transaction_id: UUID = Field(..., description="Transaction ID for referee bonus")
    bonus_details: Dict[str, Any] = Field(..., description="Detailed bonus information")


class AvailableReward(BaseModel):
    """Schema for available reward"""
    id: str = Field(..., description="Reward ID")
    name: str = Field(..., description="Reward name")
    description: str = Field(..., description="Reward description")
    points_required: int = Field(..., description="Points required to redeem")
    reward_type: str = Field(..., description="Type of reward (discount, free_product, etc.)")
    reward_value: float = Field(..., description="Value of the reward")
    currency: str = Field(default="USD", description="Currency for reward value")
    terms_and_conditions: Optional[str] = Field(default=None, description="Terms and conditions")
    expiry_date: Optional[datetime] = Field(default=None, description="Reward expiry date")
    is_available: bool = Field(default=True, description="Whether reward is currently available")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional reward metadata")


class RedemptionRequest(BaseModel):
    """Schema for points redemption request"""
    user_id: UUID = Field(..., description="User ID redeeming points")
    reward_id: str = Field(..., description="Reward ID to redeem")
    points_to_redeem: int = Field(..., description="Number of points to redeem")


class RedemptionResponse(BaseModel):
    """Schema for points redemption response"""
    transaction_id: UUID = Field(..., description="Transaction ID for the redemption")
    reward_id: str = Field(..., description="Redeemed reward ID")
    points_redeemed: int = Field(..., description="Points redeemed")
    reward_value: float = Field(..., description="Value of redeemed reward")
    remaining_points: int = Field(..., description="Remaining points after redemption")
    redemption_code: Optional[str] = Field(default=None, description="Redemption code if applicable")
    expiry_date: Optional[datetime] = Field(default=None, description="Expiry date for the redeemed reward")
    redemption_details: Dict[str, Any] = Field(..., description="Detailed redemption information")


class LoyaltyDiscountRequest(BaseModel):
    """Schema for loyalty discount calculation request"""
    user_id: UUID = Field(..., description="User ID for discount calculation")
    base_cost: Decimal = Field(..., description="Base cost before discount")


class LoyaltyDiscountResponse(BaseModel):
    """Schema for loyalty discount response"""
    discount_amount: Decimal = Field(..., description="Discount amount")
    discount_percentage: float = Field(..., description="Discount percentage")
    final_cost: Decimal = Field(..., description="Final cost after discount")
    tier: str = Field(..., description="User tier used for calculation")
    discount_details: Dict[str, Any] = Field(..., description="Detailed discount information")


class TierAdvancementResponse(BaseModel):
    """Schema for tier advancement response"""
    old_tier: str = Field(..., description="Previous tier")
    new_tier: str = Field(..., description="New tier")
    tier_progress: float = Field(..., description="Progress in new tier")
    new_benefits: Dict[str, Any] = Field(..., description="New tier benefits")
    advancement_date: datetime = Field(..., description="Date of tier advancement")
    celebration_message: str = Field(..., description="Congratulatory message")


class PersonalizedOfferRequest(BaseModel):
    """Schema for personalized offer request"""
    user_id: UUID = Field(..., description="User ID for personalized offers")
    limit: int = Field(default=5, description="Maximum number of offers to return")


class PersonalizedOffer(BaseModel):
    """Schema for personalized offer"""
    id: str = Field(..., description="Offer ID")
    title: str = Field(..., description="Offer title")
    description: str = Field(..., description="Offer description")
    offer_type: str = Field(..., description="Type of offer (discount, bonus_points, etc.)")
    discount_percentage: Optional[float] = Field(default=None, description="Discount percentage if applicable")
    bonus_points: Optional[int] = Field(default=None, description="Bonus points if applicable")
    minimum_purchase: Optional[float] = Field(default=None, description="Minimum purchase amount")
    valid_until: datetime = Field(..., description="Offer expiry date")
    terms: Optional[str] = Field(default=None, description="Offer terms and conditions")
    personalization_reason: str = Field(..., description="Why this offer was personalized for the user")


class LoyaltyAnalyticsResponse(BaseModel):
    """Schema for loyalty analytics response"""
    total_members: int = Field(..., description="Total loyalty program members")
    active_members: int = Field(..., description="Active loyalty program members")
    tier_distribution: Dict[str, int] = Field(..., description="Distribution of members by tier")
    total_points_issued: int = Field(..., description="Total points issued")
    total_points_redeemed: int = Field(..., description="Total points redeemed")
    average_points_per_member: float = Field(..., description="Average points per member")
    top_earners: List[Dict[str, Any]] = Field(..., description="Top point earners")
    redemption_trends: Dict[str, Any] = Field(..., description="Redemption trends and patterns")
    referral_statistics: Dict[str, Any] = Field(..., description="Referral program statistics")