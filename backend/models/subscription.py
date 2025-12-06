from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import BaseModel, GUID


class Subscription(BaseModel):
    __tablename__ = "subscriptions"
    __table_args__ = {'extend_existing': True}

    user_id = Column(GUID(), ForeignKey(
        "users.id"), nullable=False)
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

    # Relationships
    user = relationship("models.user.User", back_populates="subscriptions")
