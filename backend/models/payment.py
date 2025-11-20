from sqlalchemy import Column, String, Boolean, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import BaseModel, GUID


class PaymentMethod(BaseModel):
    __tablename__ = "payment_methods"

    user_id = Column(GUID(), ForeignKey(
        "users.id"), nullable=False)
    # card, bank_account, mobile_money
    type = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=False)  # stripe, paypal, momo
    last_four = Column(String(4), nullable=True)
    expiry_month = Column(Integer, nullable=True)
    expiry_year = Column(Integer, nullable=True)
    brand = Column(String(50), nullable=True)  # visa, mastercard, etc.
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    meta_data = Column(Text, nullable=True)  # JSON string for additional data

    # Relationships
    user = relationship("User", back_populates="payment_methods")
