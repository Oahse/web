from sqlalchemy import Column, String, Boolean, DateTime, Float, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from core.database import BaseModel, CHAR_LENGTH


class Promocode(BaseModel):
    __tablename__ = "promocodes"

    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    discount_type = Column(String(20), nullable=False)  # percentage, fixed
    value = Column(Float, nullable=False)  # 10 for 10% or $10
    minimum_order_amount = Column(Float, nullable=True)
    maximum_discount_amount = Column(Float, nullable=True)
    usage_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime(timezone=True), nullable=True)
    valid_until = Column(DateTime(timezone=True), nullable=True)