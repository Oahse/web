from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from schemas.product import ProductVariantResponse


class CostBreakdownSchema(BaseModel):
    """Schema for subscription cost breakdown"""
    subtotal: float
    shipping_cost: float
    tax_amount: float
    tax_rate: float
    total_amount: float
    currency: str
    product_variants: List[Dict[str, Any]] = []  # List of variant prices
    calculation_timestamp: str


class SubscriptionBase(BaseModel):
    user_id: Optional[UUID] = None
    name: str = Field(..., min_length=1)
    status: str = Field(..., min_length=1)
    price: Optional[float] = None
    currency: str = Field(default="USD", min_length=3, max_length=3)
    billing_cycle: str = Field(default="monthly", pattern="^(weekly|monthly|yearly)$")
    auto_renew: bool = True
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    next_billing_date: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    pause_reason: Optional[str] = None


class SubscriptionCreate(BaseModel):
    """Schema for creating a new subscription"""
    name: str = Field(..., min_length=1, description="Subscription name")
    product_variant_ids: List[UUID] = Field(..., min_items=1, description="List of product variant IDs to include")
    variant_quantities: Optional[Dict[str, int]] = Field(None, description="Quantities for each variant (variant_id: quantity)")
    delivery_type: str = Field(default="standard", pattern="^(standard|express|overnight)$")
    delivery_address_id: Optional[UUID] = Field(None, description="Delivery address ID for tax calculation")
    payment_method_id: Optional[UUID] = Field(None, description="Payment method for initial payment")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    billing_cycle: str = Field(default="monthly", pattern="^(weekly|monthly|yearly)$")
    auto_renew: bool = Field(default=True, description="Whether to automatically place orders periodically")

    @validator('product_variant_ids')
    def validate_product_variants(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one product variant must be specified')
        return v
    
    @validator('variant_quantities')
    def validate_variant_quantities(cls, v, values):
        if v is not None:
            # Ensure all quantities are positive
            for variant_id, quantity in v.items():
                if quantity <= 0:
                    raise ValueError(f'Quantity for variant {variant_id} must be positive')
        return v


class SubscriptionUpdate(BaseModel):
    """Schema for updating an existing subscription"""
    name: Optional[str] = Field(None, min_length=1)
    product_variant_ids: Optional[List[UUID]] = None
    delivery_type: Optional[str] = Field(None, pattern="^(standard|express|overnight)$")
    delivery_address_id: Optional[UUID] = None
    billing_cycle: Optional[str] = Field(None, pattern="^(weekly|monthly|yearly)$")
    auto_renew: Optional[bool] = None
    pause_reason: Optional[str] = None

    @validator('product_variant_ids')
    def validate_product_variants(cls, v):
        # Allow empty list or None for basic subscription updates
        # Only validate if it's provided and not empty
        if v is not None and len(v) == 0:
            # If empty list is provided, set to None to skip variant updates
            return None
        return v


class SubscriptionAddProducts(BaseModel):
    """Schema for adding products to a subscription"""
    variant_ids: List[UUID] = Field(..., min_items=1, description="List of variant IDs to add")

    @validator('variant_ids')
    def validate_variant_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one variant ID must be specified')
        return v


class SubscriptionRemoveProducts(BaseModel):
    """Schema for removing products from a subscription"""
    variant_ids: List[UUID] = Field(..., min_items=1, description="List of variant IDs to remove")

    @validator('variant_ids')
    def validate_variant_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one variant ID must be specified')
        return v


class SubscriptionUpdateQuantity(BaseModel):
    """Schema for updating variant quantity in a subscription"""
    variant_id: UUID = Field(..., description="Variant ID to update quantity for")
    quantity: int = Field(..., ge=1, le=100, description="New quantity (1-100)")

    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        if v > 100:
            raise ValueError('Quantity cannot exceed 100')
        return v


class SubscriptionQuantityChange(BaseModel):
    """Schema for incrementing/decrementing variant quantity"""
    variant_id: UUID = Field(..., description="Variant ID to change quantity for")
    change: int = Field(..., ge=-99, le=99, description="Quantity change (-99 to +99)")

    @validator('change')
    def validate_change(cls, v):
        if v == 0:
            raise ValueError('Change cannot be zero')
        return v


class SubscriptionCostCalculationRequest(BaseModel):
    """Schema for calculating subscription cost"""
    variant_ids: List[UUID] = Field(..., min_items=1, description="List of product variant IDs")
    delivery_type: str = Field(default="standard", pattern="^(standard|express|overnight)$")
    delivery_address_id: Optional[UUID] = Field(None, description="Delivery address ID for tax calculation")
    currency: str = Field(default="USD", min_length=3, max_length=3)

    @validator('variant_ids')
    def validate_variant_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one variant ID must be specified')
        return v


class SubscriptionPause(BaseModel):
    """Schema for pausing a subscription"""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for pausing the subscription")


class SubscriptionResponse(SubscriptionBase):
    """Schema for subscription response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    variant_ids: Optional[List[str]] = []
    cost_breakdown: Optional[Dict[str, Any]] = None
    shipping_cost: Optional[float] = None
    tax_amount: Optional[float] = None
    tax_rate: Optional[float] = None
    discount_amount: Optional[float] = None
    subtotal: Optional[float] = None
    total: Optional[float] = None
    products: List[ProductVariantResponse] = []

    model_config = ConfigDict(from_attributes=True)


class SubscriptionDetailResponse(SubscriptionResponse):
    """Detailed subscription response with additional information"""
    user_email: Optional[str] = None
    delivery_address: Optional[Dict[str, Any]] = None
    payment_method: Optional[Dict[str, Any]] = None
    recent_orders: List[Dict[str, Any]] = []
    renewal_history: List[Dict[str, Any]] = []


class SubscriptionListResponse(BaseModel):
    """Schema for paginated subscription list"""
    subscriptions: List[SubscriptionResponse]
    pagination: Dict[str, Any]


class SubscriptionCostCalculationResponse(BaseModel):
    """Schema for subscription cost calculation response"""
    cost_breakdown: CostBreakdownSchema
    estimated_total: float
    currency: str
    calculation_timestamp: datetime


class SubscriptionRenewalResponse(BaseModel):
    """Schema for subscription renewal response"""
    status: str
    subscription_id: UUID
    order_id: Optional[UUID] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    next_billing_date: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: Optional[int] = None


class SubscriptionAnalyticsResponse(BaseModel):
    """Schema for subscription analytics"""
    period: Dict[str, str]
    metrics: Dict[str, Any]


class SubscriptionRenewalScheduleResponse(BaseModel):
    """Schema for renewal schedule"""
    subscription_id: UUID
    user_id: UUID
    user_email: Optional[str] = None
    name: str
    next_billing_date: datetime
    amount: float
    currency: str
    billing_cycle: str
    days_until_renewal: int


class DiscountApplicationRequest(BaseModel):
    """Schema for applying discount to subscription"""
    discount_code: str = Field(..., min_length=1, max_length=50, description="Discount code to apply")

    @validator('discount_code')
    def validate_discount_code(cls, v):
        if not v or not v.strip():
            raise ValueError('Discount code cannot be empty')
        return v.strip().upper()


class BulkRenewalProcessResponse(BaseModel):
    """Schema for bulk renewal processing response"""
    processed: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = []
    processed_subscriptions: List[SubscriptionRenewalResponse] = []