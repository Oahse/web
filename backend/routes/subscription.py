from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from schemas.subscription import SubscriptionCreate, SubscriptionUpdate
from services.subscription import SubscriptionService
from models.user import User
from services.auth import AuthService

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    return await AuthService.get_current_user(token, db)

router = APIRouter(prefix="/api/v1/subscriptions", tags=["Subscriptions"])


@router.post("/")
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new subscription."""
    try:
        subscription_service = SubscriptionService(db)
        subscription = await subscription_service.create_subscription(subscription_data, current_user.id)
        return Response(success=True, data=subscription, message="Subscription created successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to create subscription: {str(e)}"
        )


@router.get("/")
async def get_subscriptions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's subscriptions."""
    try:
        subscription_service = SubscriptionService(db)
        subscriptions = await subscription_service.get_user_subscriptions(current_user.id, page, limit)
        return Response(success=True, data=subscriptions)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch subscriptions: {str(e)}"
        )


@router.get("/{subscription_id}")
async def get_subscription(
    subscription_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific subscription."""
    try:
        subscription_service = SubscriptionService(db)
        subscription = await subscription_service.get_subscription_by_id(subscription_id, current_user.id)
        if not subscription:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Subscription not found"
            )
        return Response(success=True, data=subscription)
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch subscription: {str(e)}"
        )


@router.put("/{subscription_id}")
async def update_subscription(
    subscription_id: UUID,
    subscription_data: SubscriptionUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a subscription."""
    try:
        subscription_service = SubscriptionService(db)
        subscription = await subscription_service.update_subscription(subscription_id, subscription_data, current_user.id, background_tasks)
        return Response(success=True, data=subscription, message="Subscription updated successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to update subscription: {str(e)}"
        )


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: UUID,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a subscription."""
    try:
        subscription_service = SubscriptionService(db)
        await subscription_service.delete_subscription(subscription_id, current_user.id)
        return Response(success=True, message="Subscription deleted successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete subscription: {str(e)}"
        )
