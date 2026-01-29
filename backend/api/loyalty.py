from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from core.db import get_db
from core.dependencies import get_current_user
from core.utils.response import Response
from models.user import User
from services.loyalty import LoyaltyService
from schemas.loyalty import (
    LoyaltyAccountResponse, LoyaltyAccountUpdate,
    PointsCalculationRequest, PointsCalculationResponse,
    ReferralBonusRequest, ReferralBonusResponse,
    AvailableReward, RedemptionRequest, RedemptionResponse,
    LoyaltyDiscountRequest, LoyaltyDiscountResponse,
    PersonalizedOfferRequest, PersonalizedOffer,
    LoyaltyAnalyticsResponse
)
from core.errors import APIException

router = APIRouter(prefix="/loyalty", tags=["loyalty"])


@router.get("/account")
async def get_loyalty_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's loyalty account"""
    loyalty_service = LoyaltyService(db)
    account = await loyalty_service.get_loyalty_account(current_user.id)
    return Response.success(data=account)


@router.put("/account")
async def update_loyalty_account(
    update_data: LoyaltyAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's loyalty account"""
    loyalty_service = LoyaltyService(db)
    account = await loyalty_service.update_loyalty_account(current_user.id, update_data)
    return Response.success(data=account)


@router.post("/calculate-points")
async def calculate_points(
    request: PointsCalculationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Calculate points for a given subscription value and tier"""
    loyalty_service = LoyaltyService(db)
    result = await loyalty_service.calculate_points_earned(
        subscription_value=request.subscription_value,
        user_tier=request.user_tier
    )
    return Response.success(data=result)


@router.post("/referral-bonus")
async def process_referral_bonus(
    request: ReferralBonusRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Process referral bonus for successful referrals"""
    loyalty_service = LoyaltyService(db)
    result = await loyalty_service.process_referral_bonus(
        referrer_id=request.referrer_id,
        referee_id=request.referee_id,
        subscription_id=request.subscription_id
    )
    return Response.success(data=result)


@router.get("/rewards")
async def get_available_rewards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available rewards for current user"""
    loyalty_service = LoyaltyService(db)
    rewards = await loyalty_service.get_available_rewards(current_user.id)
    return Response.success(data=rewards)


@router.post("/redeem")
async def redeem_points(
    request: RedemptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Redeem points for a reward"""
    # Ensure user can only redeem their own points
    if request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot redeem points for another user")
    
    loyalty_service = LoyaltyService(db)
    result = await loyalty_service.redeem_points(
        user_id=request.user_id,
        reward_id=request.reward_id,
        points_to_redeem=request.points_to_redeem
    )
    return Response.success(data=result)


@router.post("/calculate-discount")
async def calculate_loyalty_discount(
    request: LoyaltyDiscountRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Calculate loyalty discount for a given cost"""
    # Ensure user can only calculate discount for themselves
    if request.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot calculate discount for another user")
    
    loyalty_service = LoyaltyService(db)
    result = await loyalty_service.calculate_loyalty_discount(
        user_id=request.user_id,
        base_cost=request.base_cost
    )
    return Response.success(data=result)


@router.get("/offers")
async def get_personalized_offers(
    limit: int = Query(default=5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized offers for current user"""
    loyalty_service = LoyaltyService(db)
    offers = await loyalty_service.get_personalized_offers(
        user_id=current_user.id,
        limit=limit
    )
    return Response.success(data=offers)


@router.get("/history")
async def get_points_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    transaction_type: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get points transaction history for current user"""
    loyalty_service = LoyaltyService(db)
    history = await loyalty_service.get_points_history(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        transaction_type=transaction_type
    )
    return Response.success(data=history)


@router.get("/analytics")
async def get_loyalty_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get loyalty program analytics (admin only)"""
    # Check if user is admin (simplified check - in production you'd have proper role checking)
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    loyalty_service = LoyaltyService(db)
    analytics = await loyalty_service.get_loyalty_analytics()
    return Response.success(data=analytics)


@router.post("/admin/award-points")
async def admin_award_points(
    user_id: UUID,
    points: int,
    description: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Award points to a user (admin only)"""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    loyalty_service = LoyaltyService(db)
    
    # Get loyalty account
    loyalty_account = await loyalty_service.get_or_create_loyalty_account(user_id)
    
    # Create manual points transaction
    from models.loyalty import PointsTransaction
    from datetime import datetime
    
    transaction = PointsTransaction(
        loyalty_account_id=loyalty_account.id,
        transaction_type="adjustment",
        points_amount=points,
        description=description,
        reason_code="admin_adjustment",
        transaction_metadata={
            "admin_user_id": str(current_user.id),
            "admin_username": current_user.email,
            "adjustment_date": datetime.utcnow().isoformat()
        }
    )
    
    # Update loyalty account
    loyalty_account.total_points += points
    loyalty_account.available_points += points
    if points > 0:
        loyalty_account.points_earned_lifetime += points
    
    db.add(transaction)
    await db.commit()
    
    return Response.success(data={
        "message": f"Successfully awarded {points} points to user {user_id}",
        "transaction_id": str(transaction.id),
        "new_total_points": loyalty_account.total_points
    })


# Integration endpoints for other services
@router.post("/internal/award-subscription-points")
async def award_subscription_points_internal(
    user_id: UUID,
    subscription_id: UUID,
    subscription_value: float,
    description: str = "Points earned from subscription",
    db: AsyncSession = Depends(get_db)
):
    """
    Internal endpoint for awarding subscription points.
    This would typically be called by the subscription service.
    """
    loyalty_service = LoyaltyService(db)
    return await loyalty_service.award_subscription_points(
        user_id=user_id,
        subscription_id=subscription_id,
        subscription_value=Decimal(str(subscription_value)),
        description=description
    )


@router.get("/internal/discount/{user_id}")
async def get_loyalty_discount_internal(
    user_id: UUID,
    base_cost: float,
    db: AsyncSession = Depends(get_db)
):
    """
    Internal endpoint for getting loyalty discount.
    This would typically be called by the subscription cost calculator.
    """
    loyalty_service = LoyaltyService(db)
    return await loyalty_service.calculate_loyalty_discount(
        user_id=user_id,
        base_cost=Decimal(str(base_cost))
    )