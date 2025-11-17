from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class OrderItemCreate(BaseModel):
    variant_id: str
    quantity: int

class AddressCreate(BaseModel):
    street: str
    city: str
    state: str
    country: str
    post_code: str

class CheckoutRequest(BaseModel):
    shipping_address_id: UUID
    shipping_method_id: UUID
    payment_method_id: UUID
    notes: Optional[str] = None

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]
    shipping_address: AddressCreate
    billing_address: Optional[AddressCreate] = None
    payment_method: str
    notes: Optional[str] = None

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None

class OrderItemResponse(BaseModel):
    id: str
    variant_id: str
    quantity: int
    price_per_unit: float
    total_price: float
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: str
    user_id: str
    status: str
    total_amount: float
    currency: str
    tracking_number: Optional[str]
    estimated_delivery: Optional[str]
    items: List[OrderItemResponse]
    created_at: str = Field(..., description="ISO format datetime string")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }