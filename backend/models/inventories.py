"""
Consolidated inventory models
Includes: WarehouseLocation, Inventory, StockAdjustment
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from core.database import BaseModel, CHAR_LENGTH, GUID
from datetime import datetime


class WarehouseLocation(BaseModel):
    """Warehouse locations for inventory management"""
    __tablename__ = "warehouse_locations"
    __table_args__ = {'extend_existing': True}

    name = Column(String(CHAR_LENGTH), nullable=False)
    address = Column(String(CHAR_LENGTH), nullable=True)
    description = Column(Text, nullable=True)

    inventories = relationship("Inventory", back_populates="location")


class Inventory(BaseModel):
    """Product variant inventory tracking"""
    __tablename__ = "inventory"
    __table_args__ = {'extend_existing': True}

    variant_id = Column(GUID(), ForeignKey("product_variants.id"), nullable=False, unique=True)
    location_id = Column(GUID(), ForeignKey("warehouse_locations.id"), nullable=False)
    quantity = Column(Integer, default=0, nullable=False)
    low_stock_threshold = Column(Integer, default=10, nullable=False)

    # Relationships
    variant = relationship("ProductVariant", back_populates="inventory")
    location = relationship("WarehouseLocation", back_populates="inventories")
    adjustments = relationship("StockAdjustment", back_populates="inventory", cascade="all, delete-orphan")


class StockAdjustment(BaseModel):
    """Stock adjustment records for audit trail"""
    __tablename__ = "stock_adjustments"
    __table_args__ = {'extend_existing': True}

    inventory_id = Column(GUID(), ForeignKey("inventory.id"), nullable=False)
    quantity_change = Column(Integer, nullable=False)  # Positive for add, negative for remove
    reason = Column(String(CHAR_LENGTH), nullable=False)  # e.g., "initial_stock", "received", "sold", "returned", "damaged"
    adjusted_by_user_id = Column(GUID(), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    inventory = relationship("Inventory", back_populates="adjustments")
    adjusted_by = relationship("User")