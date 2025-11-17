from sqlalchemy import Column, String, Boolean, Float, Text, Integer
from core.database import BaseModel, CHAR_LENGTH


class ShippingMethod(BaseModel):
    __tablename__ = "shipping_methods"

    name = Column(String(CHAR_LENGTH), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    estimated_days = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)