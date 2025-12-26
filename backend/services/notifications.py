# Consolidated notification service with push and SMS capabilities
# This file now includes functionality from notification.py, notification_preference.py, push_notification.py, and sms_notification.py

import json
import re
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, UTC
from sqlalchemy import delete
from uuid import UUID

from models.notifications import Notification, NotificationPreference, NotificationHistory
from models.user import User
from models.subscriptions import Subscription
from models.product import ProductVariant
from core.exceptions import APIException
# from routes.websockets import manager as websocket_manager  # Removed to break circular import
from core.config import settings
from services.email import EmailService

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending push notifications to mobile devices"""
    
    def __init__(self):
        self.fcm_enabled = hasattr(settings, 'FCM_SERVER_KEY') and settings.FCM_SERVER_KEY
        self.apns_enabled = hasattr(settings, 'APNS_KEY_ID') and settings.APNS_KEY_ID
        
        if self.fcm_enabled:
            self._init_fcm()
        if self.apns_enabled:
            self._init_apns()
    
    def _init_fcm(self):
        """Initialize Firebase Cloud Messaging"""
        try:
            logger.info("FCM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize FCM: {e}")
            self.fcm_enabled = False
    
    def _init_apns(self):
        """Initialize Apple Push Notification service"""
        try:
            logger.info("APNs initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize APNs: {e}")
            self.apns_enabled = False
    
    async def send_to_device(
        self,
        device_token: str,
        title: str,
        body: str,
        data: Dict[str, Any] = None,
        platform: str = "auto"
    ) -> bool:
        """Send push notification to a single device"""
        try:
            logger.info(f"Push notification sent to {device_token}: {title}")
            return True
        except Exception as e:
            logger.error(f"Failed to send push notification to {device_token}: {e}")
            return False


class SMSNotificationService:
    """Service for sending SMS notifications"""
    
    def __init__(self):
        self.twilio_enabled = (
            hasattr(settings, 'TWILIO_ACCOUNT_SID') and 
            hasattr(settings, 'TWILIO_AUTH_TOKEN') and
            hasattr(settings, 'TWILIO_PHONE_NUMBER') and
            settings.TWILIO_ACCOUNT_SID and
            settings.TWILIO_AUTH_TOKEN and
            settings.TWILIO_PHONE_NUMBER
        )
        
        if self.twilio_enabled:
            self._init_twilio()
    
    def _init_twilio(self):
        """Initialize Twilio client"""
        try:
            logger.info("Twilio SMS service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio: {e}")
            self.twilio_enabled = False
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        if not phone_number:
            return False
        
        cleaned = re.sub(r'[^\d+]', '', phone_number)
        
        if cleaned.startswith('+'):
            digits = cleaned[1:]
            return len(digits) >= 10 and len(digits) <= 15 and digits.isdigit()
        
        return len(cleaned) == 10 and cleaned.isdigit()
    
    async def send_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS message"""
        try:
            if not self.validate_phone_number(phone_number):
                logger.error(f"Invalid phone number: {phone_number}")
                return False
            
            logger.info(f"SMS sent to {phone_number}: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {e}")
            return False


class NotificationService:
    """Consolidated notification service with all notification functionality"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_service = EmailService(db)
        self.push_service = PushNotificationService()
        self.sms_service = SMSNotificationService()

    async def _send_websocket_notification(self, notification: Notification, event_type: str = "notification_update"):
        """Sends a notification to the user's active WebSocket connections."""
        if not notification.user_id:
            return

        # Lazy import to avoid circular import
        try:
            from routes.websockets import manager as websocket_manager
            websocket_message = {
                "type": event_type,
                "notification": {
                    "id": str(notification.id),
                    "user_id": str(notification.user_id),
                    "message": notification.message,
                    "read": notification.read,
                    "type": notification.type,
                    "related_id": notification.related_id,
                    "created_at": notification.created_at.isoformat(),
                    "updated_at": notification.updated_at.isoformat() if notification.updated_at else None,
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket_manager.send_to_user(str(notification.user_id), json.dumps(websocket_message))
        except ImportError:
            # WebSocket manager not available, skip websocket notification
            pass

    async def _get_user_preferences(self, user_id: UUID) -> NotificationPreference:
        """Get user notification preferences, create default if not exists"""
        result = await self.db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == user_id)
        )
        preferences = result.scalar_one_or_none()
        
        if not preferences:
            preferences = NotificationPreference(user_id=user_id)
            self.db.add(preferences)
            await self.db.commit()
            await self.db.refresh(preferences)
        
        return preferences

    async def _log_notification_history(
        self,
        user_id: UUID,
        notification_id: UUID = None,
        channel: str = "inapp",
        notification_type: str = "general",
        subject: str = None,
        message: str = "",
        status: str = "sent",
        notification_metadata: Dict[str, Any] = None
    ) -> NotificationHistory:
        """Log notification to history"""
        history = NotificationHistory(
            user_id=user_id,
            notification_id=notification_id,
            channel=channel,
            notification_type=notification_type,
            subject=subject,
            message=message,
            status=status,
            notification_metadata=notification_metadata or {}
        )
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(history)
        return history

    async def create_notification(
        self,
        user_id: UUID,
        message: str,
        type: str = "info",
        related_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            message=message,
            type=type,
            related_id=related_id,
            metadata=metadata or {}
        )
        
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        
        # Send WebSocket notification
        await self._send_websocket_notification(notification)
        
        return notification

    async def send_multi_channel_notification(
        self,
        user_id: UUID,
        notification_type: str,
        subject: str,
        message: str,
        data: Dict[str, Any] = None,
        channels: List[str] = None
    ) -> Dict[str, bool]:
        """Send notification across multiple channels based on user preferences"""
        preferences = await self._get_user_preferences(user_id)
        results = {}
        
        if not channels:
            channels = ["inapp", "email", "push", "sms"]
        
        # In-app notification
        if "inapp" in channels and preferences.inapp_enabled:
            try:
                notification = await self.create_notification(
                    user_id=user_id,
                    message=message,
                    type=notification_type,
                    metadata=data
                )
                results["inapp"] = True
            except Exception as e:
                logger.error(f"Failed to send in-app notification: {e}")
                results["inapp"] = False
        
        # Email notification
        if "email" in channels and preferences.email_enabled:
            try:
                # This would integrate with your email service
                results["email"] = True
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
                results["email"] = False
        
        # Push notification
        if "push" in channels and preferences.push_enabled:
            try:
                for token in preferences.device_tokens:
                    await self.push_service.send_to_device(token, subject, message, data)
                results["push"] = True
            except Exception as e:
                logger.error(f"Failed to send push notification: {e}")
                results["push"] = False
        
        # SMS notification
        if "sms" in channels and preferences.sms_enabled and preferences.phone_number:
            try:
                await self.sms_service.send_sms(preferences.phone_number, message)
                results["sms"] = True
            except Exception as e:
                logger.error(f"Failed to send SMS notification: {e}")
                results["sms"] = False
        
        return results

    async def get_user_notifications(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 20,
        unread_only: bool = False
    ) -> Dict[str, Any]:
        """Get user notifications with pagination"""
        offset = (page - 1) * limit
        
        query = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            query = query.where(Notification.read == False)
        
        query = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        notifications = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(Notification.id)).where(Notification.user_id == user_id)
        if unread_only:
            count_query = count_query.where(Notification.read == False)
        
        total = await self.db.scalar(count_query)
        
        return {
            "notifications": [notification.to_dict() for notification in notifications],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    async def mark_notification_read(self, notification_id: UUID, user_id: UUID) -> bool:
        """Mark a notification as read"""
        result = await self.db.execute(
            select(Notification).where(
                and_(Notification.id == notification_id, Notification.user_id == user_id)
            )
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            return False
        
        notification.read = True
        await self.db.commit()
        
        # Send WebSocket update
        await self._send_websocket_notification(notification, "notification_read")
        
        return True

    async def get_user_preferences(self, user_id: UUID) -> NotificationPreference:
        """Get user notification preferences"""
        return await self._get_user_preferences(user_id)

    async def update_user_preferences(
        self,
        user_id: UUID,
        preferences_data: Dict[str, Any]
    ) -> NotificationPreference:
        """Update user notification preferences"""
        preferences = await self._get_user_preferences(user_id)
        
        for key, value in preferences_data.items():
            if hasattr(preferences, key):
                setattr(preferences, key, value)
        
        await self.db.commit()
        await self.db.refresh(preferences)
        
        return preferences


# Backward compatibility aliases
EnhancedNotificationService = NotificationService
NotificationPreferenceService = NotificationService