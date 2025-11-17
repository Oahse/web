from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PromocodeBase(BaseModel):
    code: str = Field(..., min_length=1)
    discount_type: str = Field(..., description="e.g., 'fixed', 'percentage', 'shipping'")
    value: float = Field(..., gt=0)
    is_active: bool = True
    expiration_date: Optional[datetime] = None

class PromocodeCreate(PromocodeBase):
    pass

class PromocodeUpdate(PromocodeBase):
    code: Optional[str] = None
    discount_type: Optional[str] = None
    value: Optional[float] = None

class PromocodeInDB(PromocodeBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
