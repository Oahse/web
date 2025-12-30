"""
Consolidated subscription models
Includes: Subscription and related subscription models
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Float, Table, JSON, Text, Integer, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import BaseModel, GUID, Base
from typing import Dict, Any

# Association table for many-to-many relationship between Subscription and ProductVariant
subscription_product_association = Table(
    "subscription_product_association",
    Base.metadata,
    Column("subscription_id", GUID(), ForeignKey("subscriptions.id"), primary_key=True),
    Column("product_variant_id", GUID(), ForeignKey("product_variants.id"), primary_key=True),
    extend_existing=True
)


class Subscription(BaseModel):
    """Enhanced subscription model with comprehensive tracking"""
    __tablename__ = "subscriptions"
    __table_args__ = (
        # Indexes for search and performance
        Index('idx_subscriptions_user_id', 'user_id'),
        Index('idx_subscriptions_plan_id', 'plan_id'),
        Index('idx_subscriptions_status', 'status'),
        Index('idx_subscriptions_billing_cycle', 'billing_cycle'),
        Index('idx_subscriptions_auto_renew', 'auto_renew'),
        Index('idx_subscriptions_current_period_end', 'current_period_end'),
        Index('idx_subscriptions_next_billing_date', 'next_billing_date'),
        Index('idx_subscriptions_cancelled_at', 'cancelled_at'),
        Index('idx_subscriptions_created_at', 'created_at'),
        # Composite indexes for common queries
        Index('idx_subscriptions_user_status', 'user_id', 'status'),
        Index('idx_subscriptions_status_billing', 'status', 'next_billing_date'),
        Index('idx_subscriptions_plan_status', 'plan_id', 'status'),
        {'extend_existing': True}
    )

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    plan_id = Column(String(100), nullable=False)  # basic, premium, enterprise
    # active, cancelled, expired, paused
    status = Column(String(50), default="active")
    price = Column(Float, nullable=True)
    currency = Column(String(3), default="USD")
    billing_cycle = Column(String(20), default="monthly")  # monthly, yearly
    auto_renew = Column(Boolean, default=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Enhanced fields for variant tracking and cost breakdown
    variant_ids = Column(JSON, nullable=True)  # List of variant UUIDs for tracking
    cost_breakdown = Column(JSON, nullable=True)  # Detailed cost calculation breakdown
    delivery_type = Column(String(50), nullable=True, default="standard")  # "standard", "express", "overnight"
    delivery_address_id = Column(GUID(), nullable=True)  # Reference to delivery address
    
    # Cost calculation tracking
    cost_calculation_version = Column(String(50), nullable=True)  # Track pricing rule version used
    admin_percentage_applied = Column(Float, nullable=True)  # Admin percentage at time of calculation
    delivery_cost_applied = Column(Float, nullable=True)  # Delivery cost at time of calculation
    tax_rate_applied = Column(Float, nullable=True)  # Tax rate applied
    tax_amount = Column(Float, nullable=True)  # Tax amount calculated
    
    # Loyalty integration
    loyalty_points_earned = Column(Integer, nullable=False, default=0)
    loyalty_discount_applied = Column(Float, nullable=True, default=0.0)
    
    # Subscription lifecycle
    paused_at = Column(DateTime(timezone=True), nullable=True)
    pause_reason = Column(Text, nullable=True)
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata for additional tracking
    subscription_metadata = Column(JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    # New relationship for products included in this specific subscription
    products = relationship(
        "ProductVariant",
        secondary=subscription_product_association,
        backref="subscriptions_containing",
        lazy="selectin"
    )
    variant_tracking_entries = relationship("VariantTrackingEntry", back_populates="subscription", lazy="select")
    
    def to_dict(self, include_products=False) -> Dict[str, Any]:
        """Convert subscription to dictionary for API responses"""
        data = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "plan_id": self.plan_id,
            "status": self.status,
            "price": self.price,
            "currency": self.currency,
            "billing_cycle": self.billing_cycle,
            "auto_renew": self.auto_renew,
            "current_period_start": self.current_period_start.isoformat() if self.current_period_start else None,
            "current_period_end": self.current_period_end.isoformat() if self.current_period_end else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "variant_ids": self.variant_ids,
            "cost_breakdown": self.cost_breakdown,
            "delivery_type": self.delivery_type,
            "delivery_address_id": str(self.delivery_address_id) if self.delivery_address_id else None,
            "cost_calculation_version": self.cost_calculation_version,
            "admin_percentage_applied": self.admin_percentage_applied,
            "delivery_cost_applied": self.delivery_cost_applied,
            "tax_rate_applied": self.tax_rate_applied,
            "tax_amount": self.tax_amount,
            "loyalty_points_earned": self.loyalty_points_earned,
            "loyalty_discount_applied": self.loyalty_discount_applied,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            "pause_reason": self.pause_reason,
            "next_billing_date": self.next_billing_date.isoformat() if self.next_billing_date else None,
            "metadata": self.subscription_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_products and self.products:
            data["products"] = [product.to_dict() for product in self.products]
            
        return data