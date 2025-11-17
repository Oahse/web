from pydantic import BaseModel, Field
from typing import List
from datetime import datetime
from uuid import UUID
from schemas.product import ProductVariantResponse

class AddToCartRequest(BaseModel):
    variant_id: str
    quantity: int

class ApplyPromocodeRequest(BaseModel):
    code: str

class CartItemResponse(BaseModel):
    id: UUID
    variant: ProductVariantResponse
    quantity: int
    price_per_unit: float
    total_price: float
    created_at: str = Field(..., description="ISO format datetime string")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    subtotal: float
    tax_amount: float
    shipping_amount: float
    total_amount: float
    currency: str = "USD"

    class Config:
        from_attributes = True

class UpdateCartItemRequest(BaseModel):
    quantity: int