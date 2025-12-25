from sqlalchemy import Column, String, Boolean, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import BaseModel, GUID


class Cart(BaseModel):
    __tablename__ = "carts"
    __table_args__ = {'extend_existing': True}

    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), nullable=True)  # For guest carts
    promocode_id = Column(GUID(), ForeignKey(
        "promocodes.id"), nullable=True)
    discount_amount = Column(Float, default=0.0)

    # Relationships
    items = relationship("CartItem", back_populates="cart",
                         cascade="all, delete-orphan", lazy="selectin")
    promocode = relationship("Promocode", foreign_keys=[promocode_id])

    def get_item(self, variant_id):
        """Get cart item by variant ID"""
        for item in self.items:
            if item.variant_id == variant_id:
                return item
        return None

    def subtotal(self) -> float:
        """Calculate cart subtotal"""
        return sum(item.total_price for item in self.items if not getattr(item, 'saved_for_later', False))

    def tax_amount(self) -> float:
        """Calculate tax amount (10% for now)"""
        return self.subtotal() * 0.1

    def shipping_amount(self) -> float:
        """Calculate shipping amount"""
        subtotal = self.subtotal()
        return 0.0 if subtotal >= 50 else 10.0  # Free shipping over $50

    def total_amount(self, discount: float = None) -> float:
        """Calculate total amount"""
        discount_amt = discount or self.discount_amount or 0.0
        return self.subtotal() + self.tax_amount() + self.shipping_amount() - discount_amt

    def item_count(self) -> int:
        """Get total item count"""
        return sum(item.quantity for item in self.items if not getattr(item, 'saved_for_later', False))

    def validate(self) -> dict:
        """Validate cart items"""
        issues = []
        for item in self.items:
            if hasattr(item.variant, 'stock') and item.variant.stock < item.quantity:
                issues.append({
                    "item_id": str(item.id),
                    "issue": "insufficient_stock",
                    "message": f"Only {item.variant.stock} items available"
                })

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def to_dict(self) -> dict:
        """Convert cart to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "session_id": self.session_id,
            "promocode_id": str(self.promocode_id) if self.promocode_id else None,
            "discount_amount": self.discount_amount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CartItem(BaseModel):
    __tablename__ = "cart_items"
    __table_args__ = {'extend_existing': True}

    cart_id = Column(GUID(), ForeignKey(
        "carts.id"), nullable=False)
    variant_id = Column(GUID(), ForeignKey(
        "product_variants.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    price_per_unit = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    saved_for_later = Column(Boolean, default=False)

    # Relationships
    cart = relationship("Cart", back_populates="items")
    variant = relationship("ProductVariant", back_populates="cart_items")

    def recalc_total(self):
        """Recalculate total price"""
        self.total_price = self.price_per_unit * self.quantity

    def to_dict(self) -> dict:
        """Convert cart item to dictionary for API responses"""
        return {
            "id": str(self.id),
            "cart_id": str(self.cart_id),
            "variant_id": str(self.variant_id),
            "quantity": self.quantity,
            "price_per_unit": self.price_per_unit,
            "total_price": self.total_price,
            "saved_for_later": self.saved_for_later,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
