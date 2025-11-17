from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from services.notification import NotificationService
from models.user import User
from services.auth import AuthService

from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_auth_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    return await AuthService.get_current_user(token, db)

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

@router.get("/")
async def get_user_notifications(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    read: Optional[bool] = None,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Get notifications for the current user."""
    try:
        notification_service = NotificationService(db)
        notifications = await notification_service.get_user_notifications(str(current_user.id), page, limit, read)
        return Response(success=True, data=notifications)
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to fetch notifications: {str(e)}"
        )

@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a notification as read."""
    try:
        notification_service = NotificationService(db)
        notification = await notification_service.mark_notification_as_read(notification_id, str(current_user.id))
        return Response(success=True, data=notification, message="Notification marked as read")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to mark notification as read: {str(e)}"
        )

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_auth_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a notification."""
    try:
        notification_service = NotificationService(db)
        await notification_service.delete_notification(notification_id, str(current_user.id))
        return Response(success=True, message="Notification deleted successfully")
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Failed to delete notification: {str(e)}"
        )
