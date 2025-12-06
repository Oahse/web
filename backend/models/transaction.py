from sqlalchemy import Column, String, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import BaseModel, GUID


class Transaction(BaseModel):
    __tablename__ = "transactions"
    __table_args__ = {'extend_existing': True}

    user_id = Column(GUID(), ForeignKey(
        "users.id"), nullable=False)
    order_id = Column(GUID(), ForeignKey(
        "orders.id"), nullable=True)
    stripe_payment_intent_id = Column(String(225), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    # pending, succeeded, failed, cancelled
    status = Column(String(50), nullable=False)
    # payment, refund, payout
    transaction_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    meta_data = Column(Text, nullable=True)  # JSON string for additional data

    # Relationships
    user = relationship("models.user.User", back_populates="transactions")
    order = relationship("models.order.Order", back_populates="transactions")
