from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ShippingMethodBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    estimated_days: int = Field(..., ge=1)
    is_active: bool = True
    
    # Country-specific fields
    available_countries: Optional[List[str]] = Field(None, description="List of country codes where available. If null, available worldwide")
    restricted_countries: Optional[List[str]] = Field(None, description="List of country codes where NOT available")
    regions: Optional[List[str]] = Field(None, description="Supported regions like 'EU', 'North America'")
    
    # Advanced pricing
    min_order_amount: Optional[float] = Field(None, ge=0, description="Minimum order amount required")
    max_weight_kg: Optional[float] = Field(None, gt=0, description="Maximum weight in kg")
    price_per_kg: Optional[float] = Field(None, ge=0, description="Additional price per kg over base weight")
    base_weight_kg: float = Field(1.0, gt=0, description="Base weight included in base price")
    
    # Metadata
    carrier: Optional[str] = Field(None, description="Shipping carrier name")
    tracking_url_template: Optional[str] = Field(None, description="URL template for tracking")


class ShippingMethodCreate(ShippingMethodBase):
    pass


class ShippingMethodUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    estimated_days: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    
    # Country-specific fields
    available_countries: Optional[List[str]] = None
    restricted_countries: Optional[List[str]] = None
    regions: Optional[List[str]] = None
    
    # Advanced pricing
    min_order_amount: Optional[float] = Field(None, ge=0)
    max_weight_kg: Optional[float] = Field(None, gt=0)
    price_per_kg: Optional[float] = Field(None, ge=0)
    base_weight_kg: Optional[float] = Field(None, gt=0)
    
    # Metadata
    carrier: Optional[str] = None
    tracking_url_template: Optional[str] = None


class ShippingMethodInDB(ShippingMethodBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShippingMethodAvailability(BaseModel):
    """Response for checking shipping method availability for a specific location"""
    method: ShippingMethodInDB
    available: bool
    reason: Optional[str] = None  # Reason if not available
    calculated_price: float  # Final price including weight-based pricing
