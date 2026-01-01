# Consolidated notification routes
# This file includes all notification-related routes

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from core.dependencies import get_current_user
from core.exceptions import APIException
from core.utils.response import Response
from models.user import User
from models.notifications import Notification, NotificationPreference
from services.notifications import NotificationService
from schemas.notifications import (
    NotificationResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    NotificationCreate,
    NotificationListResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
async def get_user_notifications(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    limit: int = 20,
    unread_only: bool = False
):
    """Get user notifications with pagination"""
    logger.info(f"API Call: get_user_notifications for user {current_user.id}")
    try:
        service = NotificationService(db)
        notifications = await service.get_user_notifications(
            user_id=current_user.id,
            page=page,
            limit=limit,
            unread_only=unread_only
        )
        logger.info(f"API Call Success: get_user_notifications for user {current_user.id}")
        return Response.success(data=notifications)
    except APIException as e:
        logger.error(f"API Exception in get_user_notifications for user {current_user.id}: {e.message}", exc_info=True)
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in get_user_notifications for user {current_user.id}: {e}", exc_info=True)
        raise APIException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                           message="An unexpected error occurred while fetching notifications.")


@router.post("/")
async def create_notification(
    notification_data: NotificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new notification (admin only)"""
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create notifications"
        )
    
    service = NotificationService(db)
    notification = await service.create_notification(
        user_id=notification_data.user_id,
        message=notification_data.message,
        type=notification_data.type,
        related_id=notification_data.related_id,
        metadata=notification_data.metadata
    )
    
    return Response.success(data=NotificationResponse.from_orm(notification))


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a notification as read"""
    service = NotificationService(db)
    success = await service.mark_notification_read(notification_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    
    return {"message": "Notification marked as read"}


@router.get("/preferences")
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user notification preferences"""
    service = NotificationService(db)
    preferences = await service.get_user_preferences(current_user.id)
    return Response.success(data=NotificationPreferenceResponse.from_orm(preferences))


@router.put("/preferences")
async def update_notification_preferences(
    preferences_data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user notification preferences"""
    service = NotificationService(db)
    preferences = await service.update_user_preferences(
        user_id=current_user.id,
        preferences_data=preferences_data.dict(exclude_unset=True)
    )
    return Response.success(data=NotificationPreferenceResponse.from_orm(preferences))


@router.post("/send-multi-channel")
async def send_multi_channel_notification(
    user_id: UUID,
    notification_type: str,
    subject: str,
    message: str,
    channels: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send notification across multiple channels (admin only)"""
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can send multi-channel notifications"
        )
    
    service = NotificationService(db)
    results = await service.send_multi_channel_notification(
        user_id=user_id,
        notification_type=notification_type,
        subject=subject,
        message=message,
        channels=channels
    )
    
    return {"results": results}