from sqlalchemy import Column, String, Boolean, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, selectinload
from core.database import BaseModel, CHAR_LENGTH


class Transaction(BaseModel):
    __tablename__ = "transactions"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    stripe_payment_intent_id = Column(String(CHAR_LENGTH), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(50), nullable=False)  # pending, succeeded, failed, cancelled
    transaction_type = Column(String(50), nullable=False)  # payment, refund, payout
    description = Column(Text, nullable=True)
    meta_data = Column(Text, nullable=True)  # JSON string for additional data

    # Relationships
    user = relationship("User", back_populates="transactions")
    order = relationship("Order", back_populates="transactions")