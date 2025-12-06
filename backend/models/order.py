from sqlalchemy import Column, String, ForeignKey, Float, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from core.database import BaseModel, GUID


class Order(BaseModel):
    __tablename__ = "orders"
    __table_args__ = {'extend_existing': True}

    user_id = Column(GUID(), ForeignKey(
        "users.id"), nullable=False)
    # pending, confirmed, shipped, delivered, cancelled
    status = Column(String(50), default="pending")
    total_amount = Column(Float, nullable=False)
    shipping_address_id = Column(
        GUID(), ForeignKey("addresses.id"), nullable=True)
    shipping_method_id = Column(GUID(), ForeignKey(
        "shipping_methods.id"), nullable=True)
    payment_method_id = Column(GUID(), ForeignKey(
        "payment_methods.id"), nullable=True)
    promocode_id = Column(GUID(), ForeignKey(
        "promocodes.id"), nullable=True)
    carrier_name = Column(String(100), nullable=True)
    tracking_number = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships with lazy loading
    user = relationship("models.user.User", back_populates="orders")
    items = relationship("models.order.OrderItem", back_populates="order",
                         cascade="all, delete-orphan", lazy="selectin")
    tracking_events = relationship(
        "models.order.TrackingEvent", back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    transactions = relationship("models.transaction.Transaction", back_populates="order")


class OrderItem(BaseModel):
    __tablename__ = "order_items"
    __table_args__ = {'extend_existing': True}

    order_id = Column(GUID(), ForeignKey(
        "orders.id"), nullable=False)
    variant_id = Column(GUID(), ForeignKey(
        "product_variants.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    # Relationships
    order = relationship("models.order.Order", back_populates="items")
    variant = relationship("models.product.ProductVariant", back_populates="order_items")


class TrackingEvent(BaseModel):
    __tablename__ = "tracking_events"
    __table_args__ = {'extend_existing': True}

    order_id = Column(GUID(), ForeignKey(
        "orders.id"), nullable=False)
    status = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)

    # Relationships
    order = relationship("models.order.Order", back_populates="tracking_events")
