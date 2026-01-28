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


class SubscriptionProduct(BaseModel):
    """Individual products within subscriptions with removal tracking"""
    __tablename__ = "subscription_products"
    __table_args__ = (
        # Indexes for search and performance
        Index('idx_subscription_products_subscription_id', 'subscription_id'),
        Index('idx_subscription_products_product_id', 'product_id'),
        Index('idx_subscription_products_removed_at', 'removed_at'),
        Index('idx_subscription_products_removed_by', 'removed_by'),
        # Composite indexes for common queries
        Index('idx_subscription_products_sub_product', 'subscription_id', 'product_id'),
        Index('idx_subscription_products_active', 'subscription_id', 'removed_at'),
        {'extend_existing': True}
    )

    subscription_id = Column(GUID(), ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(GUID(), ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    added_at = Column(DateTime(timezone=True), server_default="NOW()", nullable=False)
    
    # Removal tracking columns
    removed_at = Column(DateTime(timezone=True), nullable=True)
    removed_by = Column(GUID(), ForeignKey("users.id"), nullable=True)

    # Relationships
    subscription = relationship("Subscription", back_populates="subscription_products", lazy="select")
    product = relationship("Product", lazy="select")
    removed_by_user = relationship("User", lazy="select")

    def to_dict(self) -> Dict[str, Any]:
        """Convert subscription product to dictionary for API responses"""
        return {
            "id": str(self.id),
            "subscription_id": str(self.subscription_id),
            "product_id": str(self.product_id),
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "total_price": self.total_price,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "removed_at": self.removed_at.isoformat() if self.removed_at else None,
            "removed_by": str(self.removed_by) if self.removed_by else None,
            "is_active": self.removed_at is None,
            "product": self.product.to_dict() if self.product else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def is_active(self) -> bool:
        """Check if product is still active in subscription"""
        return self.removed_at is None


class Subscription(BaseModel):
    """Simplified subscription model with essential pricing fields only"""
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
    status = Column(String(50), default="active")  # active, cancelled, expired, paused
    price = Column(Float, nullable=True)
    currency = Column(String(3), default="USD")
    billing_cycle = Column(String(20), default="monthly")  # weekly, monthly, yearly
    auto_renew = Column(Boolean, default=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Essential fields for variant tracking and simplified cost breakdown
    variant_ids = Column(JSON, nullable=True)  # List of variant UUIDs for tracking
    cost_breakdown = Column(JSON, nullable=True)  # Simplified cost calculation breakdown
    
    # Simplified cost fields - complete pricing structure
    subtotal = Column(Float, nullable=True, default=0.0)  # Sum of all product prices
    shipping_cost = Column(Float, nullable=True, default=0.0)  # Shipping cost
    tax_amount = Column(Float, nullable=True, default=0.0)  # Tax amount calculated
    tax_rate = Column(Float, nullable=True, default=0.0)  # Tax rate applied (e.g., 0.08 for 8%)
    discount_amount = Column(Float, nullable=True, default=0.0)  # Total discount amount
    total = Column(Float, nullable=True, default=0.0)  # Final total amount
    
    # Subscription lifecycle
    paused_at = Column(DateTime(timezone=True), nullable=True)
    pause_reason = Column(Text, nullable=True)
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    
    # Minimal metadata for variant quantities only
    variant_quantities = Column(JSON, nullable=True)  # {variant_id: quantity}
    
    # Validation tracking columns
    tax_validated_at = Column(DateTime(timezone=True), nullable=True)
    shipping_validated_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    products = relationship(
        "ProductVariant",
        secondary=subscription_product_association,
        backref="subscriptions_containing",
        lazy="selectin"
    )
    variant_tracking_entries = relationship("VariantTrackingEntry", back_populates="subscription", lazy="select")
    orders = relationship("Order", back_populates="subscription", lazy="select")
    applied_discounts = relationship("SubscriptionDiscount", back_populates="subscription", lazy="select")
    subscription_products = relationship("SubscriptionProduct", back_populates="subscription", lazy="select")
    
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
            "subtotal": self.subtotal,
            "shipping_cost": self.shipping_cost,
            "tax_amount": self.tax_amount,
            "tax_rate": self.tax_rate,
            "discount_amount": self.discount_amount,
            "total": self.total,
            "paused_at": self.paused_at.isoformat() if self.paused_at else None,
            "pause_reason": self.pause_reason,
            "next_billing_date": self.next_billing_date.isoformat() if self.next_billing_date else None,
            "variant_quantities": self.variant_quantities or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_products and self.products:
            # Create products array matching the frontend interface
            products_dict = {}
            
            # Group variants by product to avoid duplicates
            for variant in self.products:
                try:
                    # Safely access the product relationship
                    if hasattr(variant, 'product') and variant.product:
                        product_id = str(variant.product.id)
                        if product_id not in products_dict:
                            # Get primary image from variant
                            image_url = None
                            if hasattr(variant, 'images') and variant.images:
                                primary_image = next((img for img in variant.images if img.is_primary), 
                                                   variant.images[0] if variant.images else None)
                                if primary_image:
                                    image_url = primary_image.url
                            
                            products_dict[product_id] = {
                                "id": product_id,
                                "name": variant.product.name,
                                "price": float(variant.product.min_price) if variant.product.min_price else float(variant.base_price),
                                "current_price": float(getattr(variant, 'current_price', variant.base_price)),
                                "image": image_url
                            }
                except Exception:
                    # Skip this variant if there's an issue accessing the product
                    continue
            
            data["products"] = list(products_dict.values())
            
        return data