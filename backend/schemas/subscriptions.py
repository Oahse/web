from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

from schemas.product import ProductVariantResponse


class SubscriptionBase(BaseModel):
    user_id: Optional[str] = None
    plan_id: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    price: Optional[float] = None
    currency: Optional[str] = None
    billing_cycle: Optional[str] = None
    auto_renew: bool = True
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(SubscriptionBase):
    plan_id: Optional[str] = None
    status: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    billing_cycle: Optional[str] = None
    auto_renew: Optional[bool] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


class SubscriptionResponse(SubscriptionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    products: List[ProductVariantResponse] = []

    model_config = ConfigDict(from_attributes=True)