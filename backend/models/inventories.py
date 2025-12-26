"""
Consolidated inventory models
Includes: WarehouseLocation, Inventory, StockAdjustment, InventoryReservation
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from core.database import BaseModel, CHAR_LENGTH, GUID
from datetime import datetime, timedelta
from typing import Dict, Any


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
    
    # GOLDEN RULE 7: Optimistic locking
    version = Column(Integer, default=0)

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


class InventoryReservation(BaseModel):
    """
    GOLDEN RULE 3: Inventory Management - Reserve stock during checkout
    Prevents overselling by reserving inventory before payment confirmation
    """
    __tablename__ = "inventory_reservations"
    __table_args__ = {'extend_existing': True}
    
    inventory_id = Column(GUID(), ForeignKey("inventory.id"), nullable=False, index=True)
    order_id = Column(GUID(), ForeignKey("orders.id"), nullable=True, index=True)
    quantity = Column(Integer, nullable=False)
    # reserved, confirmed, cancelled, expired
    status = Column(String(50), nullable=False, default="reserved", index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    inventory = relationship("Inventory")
    order = relationship("Order")
    
    def is_expired(self) -> bool:
        """Check if reservation has expired"""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "inventory_id": str(self.inventory_id),
            "order_id": str(self.order_id) if self.order_id else None,
            "quantity": self.quantity,
            "status": self.status,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }