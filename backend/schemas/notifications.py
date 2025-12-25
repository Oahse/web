from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class NotificationBase(BaseModel):
    message: str
    read: bool = False
    type: str = "info"
    related_id: Optional[str] = None


class NotificationCreate(NotificationBase):
    user_id: str


class NotificationUpdate(NotificationBase):
    pass


class NotificationInDB(NotificationBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationResponse(NotificationInDB):
    """Response schema for notifications"""
    pass


# Notification Preferences
class NotificationPreferenceBase(BaseModel):
    email_notifications: bool = True
    sms_notifications: bool = False
    push_notifications: bool = True
    marketing_emails: bool = False


class NotificationPreferenceCreate(NotificationPreferenceBase):
    user_id: str


class NotificationPreferenceUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    marketing_emails: Optional[bool] = None


class NotificationPreferenceResponse(NotificationPreferenceBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)