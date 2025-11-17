from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SubscriptionBase(BaseModel):
    user_id: Optional[str] = None
    plan_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    auto_renew: bool = True

class SubscriptionCreate(SubscriptionBase):
    pass

class SubscriptionUpdate(SubscriptionBase):
    plan_id: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    auto_renew: Optional[bool] = None

class SubscriptionInDB(SubscriptionBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
