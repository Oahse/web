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
