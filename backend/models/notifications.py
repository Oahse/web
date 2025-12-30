"""
Consolidated notification models
Includes: Notification, NotificationPreference, NotificationHistory
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Text, JSON, Index, Integer, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from core.database import BaseModel, CHAR_LENGTH, GUID
from enum import Enum


class NotificationType(str, Enum):
    """Notification types"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    INAPP = "inapp"


class NotificationStatus(str, Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"


class Notification(BaseModel):
    """Core notification model for in-app notifications"""
    __tablename__ = "notifications"
    __table_args__ = (
        # Indexes for search and performance
        Index('idx_notifications_user_id', 'user_id'),
        Index('idx_notifications_read', 'read'),
        Index('idx_notifications_type', 'type'),
        Index('idx_notifications_related_id', 'related_id'),
        Index('idx_notifications_created_at', 'created_at'),
        # Composite indexes for common queries
        Index('idx_notifications_user_read', 'user_id', 'read'),
        Index('idx_notifications_user_type', 'user_id', 'type'),
        {'extend_existing': True}
    )

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    # Notification type using enum
    type = Column(SQLEnum(NotificationType), default=NotificationType.INFO)
    # e.g., order_id, product_id, subscription_id
    related_id = Column(String(CHAR_LENGTH), nullable=True)
    # Additional context data
    notification_details_metadata = Column(JSON, default=dict)

    user = relationship("User", back_populates="notifications")
    notification_history = relationship("NotificationHistory", back_populates="notification", lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "message": self.message,
            "read": self.read,
            "type": self.type,
            "related_id": self.related_id,
            "notification_details_metadata": self.notification_details_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class NotificationPreference(BaseModel):
    """User notification preferences for all channels"""
    __tablename__ = "notification_preferences"
    __table_args__ = (
        # Indexes for search and performance
        Index('idx_notification_preferences_user_id', 'user_id'),
        Index('idx_notification_preferences_email_enabled', 'email_enabled'),
        Index('idx_notification_preferences_sms_enabled', 'sms_enabled'),
        Index('idx_notification_preferences_push_enabled', 'push_enabled'),
        {'extend_existing': True}
    )

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Email notification preferences
    email_enabled = Column(Boolean, default=True)
    email_subscription_changes = Column(Boolean, default=True)
    email_payment_confirmations = Column(Boolean, default=True)
    email_payment_failures = Column(Boolean, default=True)
    email_variant_unavailable = Column(Boolean, default=True)
    email_promotional = Column(Boolean, default=False)
    
    # SMS notification preferences
    sms_enabled = Column(Boolean, default=False)
    sms_payment_failures = Column(Boolean, default=False)
    sms_urgent_alerts = Column(Boolean, default=False)
    phone_number = Column(String(CHAR_LENGTH), nullable=True)
    
    # Push notification preferences
    push_enabled = Column(Boolean, default=True)
    push_subscription_changes = Column(Boolean, default=True)
    push_payment_confirmations = Column(Boolean, default=True)
    push_payment_failures = Column(Boolean, default=True)
    push_variant_unavailable = Column(Boolean, default=True)
    
    # In-app notification preferences
    inapp_enabled = Column(Boolean, default=True)
    inapp_subscription_changes = Column(Boolean, default=True)
    inapp_payment_confirmations = Column(Boolean, default=True)
    inapp_payment_failures = Column(Boolean, default=True)
    inapp_variant_unavailable = Column(Boolean, default=True)
    
    # Device tokens for push notifications
    device_tokens = Column(JSON, default=list)  # List of device tokens
    
    user = relationship("User", back_populates="notification_preferences")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "email_enabled": self.email_enabled,
            "email_subscription_changes": self.email_subscription_changes,
            "email_payment_confirmations": self.email_payment_confirmations,
            "email_payment_failures": self.email_payment_failures,
            "email_variant_unavailable": self.email_variant_unavailable,
            "email_promotional": self.email_promotional,
            "sms_enabled": self.sms_enabled,
            "sms_payment_failures": self.sms_payment_failures,
            "sms_urgent_alerts": self.sms_urgent_alerts,
            "phone_number": self.phone_number,
            "push_enabled": self.push_enabled,
            "push_subscription_changes": self.push_subscription_changes,
            "push_payment_confirmations": self.push_payment_confirmations,
            "push_payment_failures": self.push_payment_failures,
            "push_variant_unavailable": self.push_variant_unavailable,
            "inapp_enabled": self.inapp_enabled,
            "inapp_subscription_changes": self.inapp_subscription_changes,
            "inapp_payment_confirmations": self.inapp_payment_confirmations,
            "inapp_payment_failures": self.inapp_payment_failures,
            "inapp_variant_unavailable": self.inapp_variant_unavailable,
            "device_tokens": self.device_tokens,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class NotificationHistory(BaseModel):
    """History of all notifications sent across all channels"""
    __tablename__ = "notification_history"
    __table_args__ = (
        # Indexes for search and performance
        Index('idx_notification_history_user_id', 'user_id'),
        Index('idx_notification_history_notification_id', 'notification_id'),
        Index('idx_notification_history_channel', 'channel'),
        Index('idx_notification_history_type', 'notification_type'),
        Index('idx_notification_history_status', 'status'),
        Index('idx_notification_history_created_at', 'created_at'),
        # Composite indexes for common queries
        Index('idx_notification_history_user_channel', 'user_id', 'channel'),
        Index('idx_notification_history_user_status', 'user_id', 'status'),
        Index('idx_notification_history_channel_status', 'channel', 'status'),
        {'extend_existing': True}
    )

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    notification_id = Column(GUID(), ForeignKey("notifications.id"), nullable=True)
    
    # Notification details
    channel = Column(SQLEnum(NotificationChannel), nullable=False)  # email, sms, push, inapp
    notification_type = Column(String(CHAR_LENGTH), nullable=False)  # subscription_change, payment_confirmation, etc.
    subject = Column(String(CHAR_LENGTH), nullable=True)
    message = Column(Text, nullable=False)
    
    # Delivery status
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)  # pending, sent, delivered, failed
    delivery_attempts = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Metadata for additional tracking
    history_metadata = Column(JSON, default=dict)
    
    user = relationship("User", back_populates="notification_history")
    notification = relationship("Notification", back_populates="notification_history")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "notification_id": str(self.notification_id) if self.notification_id else None,
            "channel": self.channel,
            "notification_type": self.notification_type,
            "subject": self.subject,
            "message": self.message,
            "status": self.status,
            "delivery_attempts": self.delivery_attempts,
            "error_message": self.error_message,
            "history_metadata": self.history_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }