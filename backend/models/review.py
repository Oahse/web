from sqlalchemy import Column, Boolean, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import BaseModel, GUID


class Review(BaseModel):
    __tablename__ = "reviews"

    product_id = Column(GUID(), ForeignKey(
        "products.id"), nullable=False)
    user_id = Column(GUID(), ForeignKey(
        "users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)
    is_verified_purchase = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=True)

    # Relationships
    product = relationship("Product", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
