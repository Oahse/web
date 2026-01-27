from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class ShippingMethodBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    estimated_days: int = Field(..., ge=1)
    is_active: bool = True


class ShippingMethodCreate(ShippingMethodBase):
    pass


class ShippingMethodUpdate(ShippingMethodBase):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    estimated_days: Optional[int] = None
    is_active: Optional[bool] = None


class ShippingMethodInDB(ShippingMethodBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
