from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import BaseModel, GUID
from typing import Dict, Any, List
from datetime import datetime


class VariantTrackingEntry(BaseModel):
    """Track when variants are added to subscriptions"""
    __tablename__ = "variant_tracking_entries"
    __table_args__ = {'extend_existing': True}

    # Core tracking information
    variant_id = Column(GUID(), ForeignKey("product_variants.id"), nullable=False, index=True)
    subscription_id = Column(GUID(), ForeignKey("subscriptions.id"), nullable=False, index=True)
    
    # Price tracking
    price_at_time = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Tracking metadata
    action_type = Column(String(50), nullable=False, default="added")  # "added", "removed", "price_changed"
    tracking_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Additional context
    entry_metadata = Column(JSON, nullable=True)
    
    # Relationships
    variant = relationship("ProductVariant", backref="tracking_entries")
    subscription = relationship("Subscription", backref="variant_tracking_entries")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tracking entry to dictionary"""
        return {
            "id": str(self.id),
            "variant_id": str(self.variant_id),
            "subscription_id": str(self.subscription_id),
            "price_at_time": self.price_at_time,
            "currency": self.currency,
            "action_type": self.action_type,
            "tracking_timestamp": self.tracking_timestamp.isoformat() if self.tracking_timestamp else None,
            "metadata": self.entry_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class VariantPriceHistory(BaseModel):
    """Track price changes for variants over time"""
    __tablename__ = "variant_price_history"
    __table_args__ = {'extend_existing': True}

    # Variant reference
    variant_id = Column(GUID(), ForeignKey("product_variants.id"), nullable=False, index=True)
    
    # Price information
    old_price = Column(Float, nullable=True)
    new_price = Column(Float, nullable=False)
    old_sale_price = Column(Float, nullable=True)
    new_sale_price = Column(Float, nullable=True)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Change metadata
    change_reason = Column(String(100), nullable=True)
    changed_by_user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    effective_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Impact tracking
    affected_subscriptions_count = Column(Integer, nullable=False, default=0)
    
    # Additional context
    price_metadata = Column(JSON, nullable=True)
    
    # Relationships
    variant = relationship("ProductVariant", backref="price_history")
    changed_by = relationship("User", backref="variant_price_changes")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert price history to dictionary"""
        return {
            "id": str(self.id),
            "variant_id": str(self.variant_id),
            "old_price": self.old_price,
            "new_price": self.new_price,
            "old_sale_price": self.old_sale_price,
            "new_sale_price": self.new_sale_price,
            "currency": self.currency,
            "change_reason": self.change_reason,
            "changed_by_user_id": str(self.changed_by_user_id) if self.changed_by_user_id else None,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "affected_subscriptions_count": self.affected_subscriptions_count,
            "metadata": self.price_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class VariantAnalytics(BaseModel):
    """Aggregated analytics for product variants"""
    __tablename__ = "variant_analytics"
    __table_args__ = {'extend_existing': True}

    # Variant reference
    variant_id = Column(GUID(), ForeignKey("product_variants.id"), nullable=False, index=True)
    
    # Time period for analytics
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False, default="daily")  # "daily", "weekly", "monthly"
    
    # Subscription metrics
    total_subscriptions = Column(Integer, nullable=False, default=0)
    new_subscriptions = Column(Integer, nullable=False, default=0)
    canceled_subscriptions = Column(Integer, nullable=False, default=0)
    active_subscriptions = Column(Integer, nullable=False, default=0)
    
    # Revenue metrics
    total_revenue = Column(Float, nullable=False, default=0.0)
    average_subscription_duration_days = Column(Integer, nullable=False, default=0)
    
    # Performance metrics
    churn_rate = Column(Float, nullable=False, default=0.0)
    popularity_rank = Column(Integer, nullable=True)
    
    # Currency
    currency = Column(String(3), nullable=False, default="USD")
    
    # Additional metrics
    additional_metrics = Column(JSON, nullable=True)
    
    # Relationships
    variant = relationship("ProductVariant", backref="analytics")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert variant analytics to dictionary"""
        return {
            "id": str(self.id),
            "variant_id": str(self.variant_id),
            "date": self.date.isoformat() if self.date else None,
            "period_type": self.period_type,
            "total_subscriptions": self.total_subscriptions,
            "new_subscriptions": self.new_subscriptions,
            "canceled_subscriptions": self.canceled_subscriptions,
            "active_subscriptions": self.active_subscriptions,
            "total_revenue": self.total_revenue,
            "average_subscription_duration_days": self.average_subscription_duration_days,
            "churn_rate": self.churn_rate,
            "popularity_rank": self.popularity_rank,
            "currency": self.currency,
            "additional_metrics": self.additional_metrics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class VariantSubstitution(BaseModel):
    """Track variant substitution suggestions and usage"""
    __tablename__ = "variant_substitutions"
    __table_args__ = {'extend_existing': True}

    # Original and substitute variants
    original_variant_id = Column(GUID(), ForeignKey("product_variants.id"), nullable=False, index=True)
    substitute_variant_id = Column(GUID(), ForeignKey("product_variants.id"), nullable=False, index=True)
    
    # Substitution metadata
    similarity_score = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    substitution_reason = Column(String(100), nullable=True)  # "out_of_stock", "discontinued", "price_match"
    
    # Usage tracking
    times_suggested = Column(Integer, nullable=False, default=0)
    times_accepted = Column(Integer, nullable=False, default=0)
    acceptance_rate = Column(Float, nullable=False, default=0.0)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Additional context
    substitution_metadata = Column(JSON, nullable=True)
    
    # Relationships
    original_variant = relationship("ProductVariant", foreign_keys=[original_variant_id], backref="substitution_suggestions")
    substitute_variant = relationship("ProductVariant", foreign_keys=[substitute_variant_id], backref="substitute_for")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert variant substitution to dictionary"""
        return {
            "id": str(self.id),
            "original_variant_id": str(self.original_variant_id),
            "substitute_variant_id": str(self.substitute_variant_id),
            "similarity_score": self.similarity_score,
            "substitution_reason": self.substitution_reason,
            "times_suggested": self.times_suggested,
            "times_accepted": self.times_accepted,
            "acceptance_rate": self.acceptance_rate,
            "is_active": self.is_active,
            "metadata": self.substitution_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }