from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Text, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.db import BaseModel, GUID
from typing import Dict, Any


class LoyaltyAccount(BaseModel):
    """Customer loyalty account with points and tier tracking"""
    __tablename__ = "loyalty_accounts"
    __table_args__ = (
        # Indexes for search and performance
        Index('idx_loyalty_accounts_user_id', 'user_id'),
        Index('idx_loyalty_accounts_tier', 'tier'),
        Index('idx_loyalty_accounts_status', 'status'),
        Index('idx_loyalty_accounts_total_points', 'total_points'),
        Index('idx_loyalty_accounts_available_points', 'available_points'),
        {'extend_existing': True}
    )

    # User reference
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Points balance
    total_points = Column(Integer, nullable=False, default=0)
    available_points = Column(Integer, nullable=False, default=0)  # Points available for redemption
    
    # Tier information
    tier = Column(String(20), nullable=False, default="bronze")  # "bronze", "silver", "gold", "platinum"
    tier_progress = Column(Float, nullable=False, default=0.0)  # Progress to next tier (0.0 to 1.0)
    
    # Lifetime statistics
    points_earned_lifetime = Column(Integer, nullable=False, default=0)
    points_redeemed_lifetime = Column(Integer, nullable=False, default=0)
    referrals_made = Column(Integer, nullable=False, default=0)
    successful_referrals = Column(Integer, nullable=False, default=0)
    
    # Tier benefits (JSON: {"discount_percentage": 5, "early_access": true})
    tier_benefits = Column(JSON, nullable=True)
    
    # Account status
    status = Column(String(20), nullable=False, default="active")  # "active", "suspended", "closed"
    
    # Metadata for additional tracking
    loyalty_metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="loyalty_account")
    points_transactions = relationship("PointsTransaction", back_populates="loyalty_account", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert loyalty account to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "total_points": self.total_points,
            "available_points": self.available_points,
            "tier": self.tier,
            "tier_progress": self.tier_progress,
            "points_earned_lifetime": self.points_earned_lifetime,
            "points_redeemed_lifetime": self.points_redeemed_lifetime,
            "referrals_made": self.referrals_made,
            "successful_referrals": self.successful_referrals,
            "tier_benefits": self.tier_benefits,
            "status": self.status,
            "metadata": self.loyalty_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PointsTransaction(BaseModel):
    """Individual points transaction record"""
    __tablename__ = "points_transactions"
    __table_args__ = (
        # Indexes for search and performance
        Index('idx_points_transactions_loyalty_account_id', 'loyalty_account_id'),
        Index('idx_points_transactions_subscription_id', 'subscription_id'),
        Index('idx_points_transactions_order_id', 'order_id'),
        Index('idx_points_transactions_type', 'transaction_type'),
        Index('idx_points_transactions_status', 'status'),
        Index('idx_points_transactions_reason_code', 'reason_code'),
        Index('idx_points_transactions_created_at', 'created_at'),
        # Composite indexes for common queries
        Index('idx_points_transactions_account_type', 'loyalty_account_id', 'transaction_type'),
        Index('idx_points_transactions_account_status', 'loyalty_account_id', 'status'),
        {'extend_existing': True}
    )

    # Loyalty account reference
    loyalty_account_id = Column(GUID(), ForeignKey("loyalty_accounts.id"), nullable=False, index=True)
    
    # Related subscription (if applicable)
    subscription_id = Column(GUID(), nullable=True, index=True)
    
    # Related order (if applicable)
    order_id = Column(GUID(), nullable=True, index=True)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False)  # "earned", "redeemed", "bonus", "referral", "adjustment"
    points_amount = Column(Integer, nullable=False)  # Positive for earned, negative for redeemed
    
    # Description and reason
    description = Column(Text, nullable=False)
    reason_code = Column(String(50), nullable=True)  # "subscription_purchase", "referral_bonus", "tier_bonus", etc.
    
    # Related transaction details
    related_amount = Column(Float, nullable=True)  # Dollar amount that generated points (if applicable)
    currency = Column(String(3), nullable=True, default="USD")
    
    # Expiration (for earned points)
    expires_at = Column(String(50), nullable=True)  # ISO date string for when points expire
    
    # Status
    status = Column(String(20), nullable=False, default="completed")  # "pending", "completed", "cancelled", "expired"
    
    # Metadata for additional tracking
    transaction_metadata = Column(JSON, nullable=True)
    
    # Relationships
    loyalty_account = relationship("LoyaltyAccount", back_populates="points_transactions")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert points transaction to dictionary"""
        return {
            "id": str(self.id),
            "loyalty_account_id": str(self.loyalty_account_id),
            "subscription_id": str(self.subscription_id) if self.subscription_id else None,
            "order_id": str(self.order_id) if self.order_id else None,
            "transaction_type": self.transaction_type,
            "points_amount": self.points_amount,
            "description": self.description,
            "reason_code": self.reason_code,
            "related_amount": self.related_amount,
            "currency": self.currency,
            "expires_at": self.expires_at,
            "status": self.status,
            "metadata": self.transaction_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }