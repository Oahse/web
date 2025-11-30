from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime


class PaymentMethodBase(BaseModel):
    type: str = Field(...,
                      description="Type of payment method (e.g., credit_card, paypal)")
    provider: str = Field(...,
                          description="Payment provider (e.g., Visa, PayPal)")
    last_four: Optional[str] = Field(
        None, max_length=4, description="Last four digits of the card number")
    expiry_month: Optional[int] = Field(
        None, ge=1, le=12, description="Card expiry month")
    expiry_year: Optional[int] = Field(
        None, ge=2000, description="Card expiry year")
    is_default: bool = Field(
        False, description="Whether this is the default payment method")


class PaymentMethodCreate(PaymentMethodBase):
    stripe_token: Optional[str] = Field(
        None, description="Stripe token for card tokenization")


class PaymentMethodUpdate(PaymentMethodBase):
    type: Optional[str] = None
    provider: Optional[str] = None


class PaymentMethodResponse(PaymentMethodBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
