from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from core.database import BaseModel, CHAR_LENGTH, GUID
from datetime import datetime

class WarehouseLocation(BaseModel):
    __tablename__ = "warehouse_locations"
    __table_args__ = {'extend_existing': True}

    name = Column(String(CHAR_LENGTH), nullable=False)
    address = Column(String(CHAR_LENGTH), nullable=True)
    description = Column(Text, nullable=True)

    inventories = relationship("models.inventory.Inventory", back_populates="location")

class Inventory(BaseModel):
    __tablename__ = "inventory"
    __table_args__ = {'extend_existing': True}

    variant_id = Column(GUID(), ForeignKey("product_variants.id"), nullable=False, unique=True) # One-to-one with ProductVariant
    location_id = Column(GUID(), ForeignKey("warehouse_locations.id"), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=10, nullable=False) # Configurable threshold for alerts

    # Relationships
    variant = relationship("models.product.ProductVariant", back_populates="inventory")
    location = relationship("models.inventory.WarehouseLocation", back_populates="inventories")
    adjustments = relationship("models.inventory.StockAdjustment", back_populates="inventory", cascade="all, delete-orphan")

class StockAdjustment(BaseModel):
    __tablename__ = "stock_adjustments"
    __table_args__ = {'extend_existing': True}

    inventory_id = Column(GUID(), ForeignKey("inventory.id"), nullable=False)
    quantity_change = Column(Integer, nullable=False) # Positive for add, negative for remove
    reason = Column(String(CHAR_LENGTH), nullable=False) # e.g., "initial_stock", "received", "sold", "returned", "damaged"
    adjusted_by_user_id = Column(GUID(), ForeignKey("users.id"), nullable=True) # Who made the adjustment
    notes = Column(Text, nullable=True)

    # Relationships
    inventory = relationship("models.inventory.Inventory", back_populates="adjustments")
    adjusted_by = relationship("models.user.User") # Assuming User model exists and back_populates is not needed if this is one-way
