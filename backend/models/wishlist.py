from sqlalchemy import Column, String, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, selectinload
from core.database import BaseModel, CHAR_LENGTH


class Wishlist(BaseModel):
    __tablename__ = "wishlists"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(CHAR_LENGTH), nullable=False)
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="wishlists")
    items = relationship("WishlistItem", back_populates="wishlist", cascade="all, delete-orphan", lazy="selectin")


class WishlistItem(BaseModel):
    __tablename__ = "wishlist_items"

    wishlist_id = Column(UUID(as_uuid=True), ForeignKey("wishlists.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=True)
    quantity = Column(Integer, default=1)

    # Relationships
    wishlist = relationship("Wishlist", back_populates="items")
    product = relationship("Product", back_populates="wishlist_items")
    variant = relationship("ProductVariant", foreign_keys=[variant_id])
    
    @property
    def added_at(self):
        """Use created_at as added_at for compatibility"""
        return self.created_at