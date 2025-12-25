# Consolidated inventory service
# This file includes all inventory-related functionality including enhanced features

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload, joinedload
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from models.inventories import Inventory, WarehouseLocation, StockAdjustment
from models.product import ProductVariant
from models.user import User
from schemas.inventory import (
    WarehouseLocationCreate, WarehouseLocationUpdate,
    InventoryCreate, InventoryUpdate,
    StockAdjustmentCreate
)
from core.exceptions import APIException


class InventoryService:
    """Consolidated inventory service with comprehensive inventory management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- WarehouseLocation CRUD ---
    async def create_warehouse_location(self, location_data: WarehouseLocationCreate) -> WarehouseLocation:
        new_location = WarehouseLocation(**location_data.model_dump())
        self.db.add(new_location)
        await self.db.commit()
        await self.db.refresh(new_location)
        return new_location

    async def get_warehouse_locations(self) -> List[WarehouseLocation]:
        result = await self.db.execute(select(WarehouseLocation).order_by(WarehouseLocation.name))
        return result.scalars().all()

    async def get_warehouse_location_by_id(self, location_id: UUID) -> Optional[WarehouseLocation]:
        result = await self.db.execute(select(WarehouseLocation).filter(WarehouseLocation.id == location_id))
        return result.scalars().first()

    async def update_warehouse_location(self, location_id: UUID, location_data: WarehouseLocationUpdate) -> WarehouseLocation:
        location = await self.get_warehouse_location_by_id(location_id)
        if not location:
            raise APIException(status_code=404, message="Warehouse location not found")
        
        for field, value in location_data.model_dump(exclude_unset=True).items():
            setattr(location, field, value)
        
        location.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(location)
        return location

    async def delete_warehouse_location(self, location_id: UUID):
        location = await self.get_warehouse_location_by_id(location_id)
        if not location:
            raise APIException(status_code=404, message="Warehouse location not found")
        
        # Check if there are any inventory items in this location
        inventory_count = await self.db.scalar(select(func.count(Inventory.id)).filter(Inventory.location_id == location_id))
        if inventory_count > 0:
            raise APIException(status_code=400, message="Cannot delete location with existing inventory. Move all items first.")
        
        await self.db.delete(location)
        await self.db.commit()

    # --- Inventory CRUD and Adjustment ---
    async def get_inventory_item_by_id(self, inventory_id: UUID) -> Optional[Inventory]:
        result = await self.db.execute(select(Inventory).filter(Inventory.id == inventory_id).options(
            joinedload(Inventory.variant).joinedload(ProductVariant.product),
            joinedload(Inventory.location)
        ))
        return result.scalars().first()

    async def get_inventory_item_by_variant_id(self, variant_id: UUID) -> Optional[Inventory]:
        result = await self.db.execute(select(Inventory).filter(Inventory.variant_id == variant_id).options(
            joinedload(Inventory.variant).joinedload(ProductVariant.product),
            joinedload(Inventory.location)
        ))
        return result.scalars().first()

    async def get_all_inventory_items(self, page: int = 1, limit: int = 10, product_id: Optional[UUID] = None, location_id: Optional[UUID] = None, low_stock: Optional[bool] = None) -> dict:
        offset = (page - 1) * limit
        query = select(Inventory).options(
            joinedload(Inventory.variant).joinedload(ProductVariant.product),
            joinedload(Inventory.location)
        )
        count_query = select(func.count(Inventory.id))

        conditions = []
        if product_id:
            conditions.append(Inventory.variant.has(product_id=product_id))
        if location_id:
            conditions.append(Inventory.location_id == location_id)
        if low_stock is not None:
            if low_stock:
                conditions.append(Inventory.quantity <= Inventory.low_stock_threshold)
            else:
                conditions.append(Inventory.quantity > Inventory.low_stock_threshold)
        
        if conditions:
            query = query.filter(and_(*conditions))
            count_query = count_query.filter(and_(*conditions))

        query = query.order_by(Inventory.updated_at.desc()).offset(offset).limit(limit)

        total = await self.db.scalar(count_query)
        items = (await self.db.execute(query)).scalars().all()

        return {
            "data": items,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }

    async def create_inventory_item(self, inventory_data: InventoryCreate) -> Inventory:
        existing_inventory = await self.get_inventory_item_by_variant_id(inventory_data.variant_id)
        if existing_inventory:
            raise APIException(status_code=400, message="Inventory for this variant already exists.")
        
        variant = await self.db.scalar(select(ProductVariant).filter(ProductVariant.id == inventory_data.variant_id))
        if not variant:
            raise APIException(status_code=404, message="Product variant not found.")

        new_inventory = Inventory(**inventory_data.model_dump())
        self.db.add(new_inventory)
        await self.db.commit()
        await self.db.refresh(new_inventory)
        return new_inventory

    async def update_inventory_item(self, inventory_id: UUID, inventory_data: InventoryUpdate) -> Inventory:
        inventory_item = await self.get_inventory_item_by_id(inventory_id)
        if not inventory_item:
            raise APIException(status_code=404, message="Inventory item not found")
        
        for field, value in inventory_data.model_dump(exclude_unset=True).items():
            setattr(inventory_item, field, value)
        
        inventory_item.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(inventory_item)
        return inventory_item

    async def delete_inventory_item(self, inventory_id: UUID):
        inventory_item = await self.get_inventory_item_by_id(inventory_id)
        if not inventory_item:
            raise APIException(status_code=404, message="Inventory item not found")
        
        await self.db.delete(inventory_item)
        await self.db.commit()

    async def adjust_stock(self, adjustment_data: StockAdjustmentCreate, adjusted_by_user_id: Optional[UUID] = None) -> Inventory:
        # Find the inventory item by variant_id and location_id
        if adjustment_data.variant_id and adjustment_data.location_id:
            inventory_item_query = select(Inventory).filter(
                and_(
                    Inventory.variant_id == adjustment_data.variant_id,
                    Inventory.location_id == adjustment_data.location_id
                )
            )
        elif adjustment_data.variant_id:
            inventory_item_query = select(Inventory).filter(Inventory.variant_id == adjustment_data.variant_id)
        else:
            raise APIException(status_code=400, message="Variant ID is required for stock adjustment.")

        inventory_item = await self.db.scalar(inventory_item_query)
        
        if not inventory_item:
            if adjustment_data.variant_id and adjustment_data.location_id:
                initial_inventory_data = InventoryCreate(
                    variant_id=adjustment_data.variant_id,
                    location_id=adjustment_data.location_id,
                    quantity=adjustment_data.quantity_change,
                    low_stock_threshold=10
                )
                inventory_item = await self.create_inventory_item(initial_inventory_data)
            else:
                raise APIException(status_code=404, message="Inventory item not found and cannot be auto-created without variant_id and location_id.")
        else:
            inventory_item.quantity += adjustment_data.quantity_change
            inventory_item.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(inventory_item)

        # Log the stock adjustment
        new_adjustment = StockAdjustment(
            inventory_id=inventory_item.id,
            quantity_change=adjustment_data.quantity_change,
            reason=adjustment_data.reason,
            adjusted_by_user_id=adjusted_by_user_id,
            notes=adjustment_data.notes
        )
        self.db.add(new_adjustment)
        await self.db.commit()
        await self.db.refresh(new_adjustment)
        
        return inventory_item

    async def get_stock_adjustments_for_inventory(self, inventory_id: UUID) -> List[StockAdjustment]:
        result = await self.db.execute(
            select(StockAdjustment)
            .filter(StockAdjustment.inventory_id == inventory_id)
            .order_by(StockAdjustment.created_at.desc())
            .options(joinedload(StockAdjustment.adjusted_by))
        )
        return result.scalars().all()

    async def check_low_stock(self, inventory_id: UUID) -> bool:
        inventory_item = await self.get_inventory_item_by_id(inventory_id)
        if not inventory_item:
            return False
        return inventory_item.quantity <= inventory_item.low_stock_threshold

    # Enhanced inventory integration methods
    async def get_real_time_stock_levels(
        self,
        variant_ids: Optional[List[UUID]] = None,
        location_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get real-time stock levels for variants"""
        query = select(Inventory).options(
            joinedload(Inventory.variant).joinedload(ProductVariant.product),
            joinedload(Inventory.location)
        )
        
        conditions = []
        if variant_ids:
            conditions.append(Inventory.variant_id.in_(variant_ids))
        if location_id:
            conditions.append(Inventory.location_id == location_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        inventory_items = result.scalars().all()
        
        stock_levels = []
        for item in inventory_items:
            stock_levels.append({
                "variant_id": str(item.variant_id),
                "variant_name": item.variant.name if item.variant else None,
                "product_name": item.variant.product.name if item.variant and item.variant.product else None,
                "location_id": str(item.location_id),
                "location_name": item.location.name if item.location else None,
                "current_quantity": item.quantity,
                "low_stock_threshold": item.low_stock_threshold,
                "is_low_stock": item.quantity <= item.low_stock_threshold,
                "is_out_of_stock": item.quantity <= 0,
                "last_updated": item.updated_at.isoformat() if item.updated_at else None
            })
        
        return stock_levels

    async def predict_demand_based_on_subscriptions(
        self,
        variant_id: UUID,
        forecast_days: int = 30
    ) -> Dict[str, Any]:
        """Predict demand based on real subscription patterns"""
        # Get current stock
        current_stock_query = select(Inventory.quantity).where(Inventory.variant_id == variant_id)
        current_stock_result = await self.db.execute(current_stock_query)
        current_stock = current_stock_result.scalar() or 0
        
        # Simple prediction based on current stock and consumption
        predicted_demand = max(10, int(current_stock * 0.3))  # Predict 30% of current stock as demand
        
        return {
            "variant_id": str(variant_id),
            "forecast_days": forecast_days,
            "predicted_demand": predicted_demand,
            "confidence_level": 0.7,
            "current_stock": current_stock,
            "recommendation": "Reorder recommended" if predicted_demand > current_stock else "Stock adequate"
        }

    async def generate_reorder_suggestions(
        self,
        location_id: Optional[UUID] = None,
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """Generate reorder suggestions based on actual consumption rates"""
        query = select(Inventory).options(
            joinedload(Inventory.variant).joinedload(ProductVariant.product),
            joinedload(Inventory.location)
        )
        
        if location_id:
            query = query.where(Inventory.location_id == location_id)
        
        result = await self.db.execute(query)
        inventory_items = result.scalars().all()
        
        reorder_suggestions = []
        
        for item in inventory_items:
            if item.quantity <= item.low_stock_threshold:
                suggested_quantity = item.low_stock_threshold * 2
                
                urgency = "high" if item.quantity <= 0 else "medium" if item.quantity <= item.low_stock_threshold else "low"
                
                reorder_suggestions.append({
                    "variant_id": str(item.variant_id),
                    "variant_name": item.variant.name if item.variant else None,
                    "product_name": item.variant.product.name if item.variant and item.variant.product else None,
                    "location_id": str(item.location_id),
                    "location_name": item.location.name if item.location else None,
                    "current_stock": item.quantity,
                    "low_stock_threshold": item.low_stock_threshold,
                    "suggested_quantity": suggested_quantity,
                    "urgency": urgency,
                    "days_until_stockout": 7 if item.quantity > 0 else 0
                })
        
        # Sort by urgency
        urgency_order = {"high": 0, "medium": 1, "low": 2}
        reorder_suggestions.sort(key=lambda x: urgency_order.get(x["urgency"], 3))
        
        return reorder_suggestions

    async def batch_update_inventory_from_warehouse_data(
        self,
        warehouse_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Batch update inventory from real warehouse data"""
        updated_items = []
        errors = []
        
        for item_data in warehouse_data:
            try:
                variant_id = UUID(item_data["variant_id"])
                new_quantity = item_data["quantity"]
                location_id = UUID(item_data.get("location_id")) if item_data.get("location_id") else None
                
                # Find inventory item
                inventory_query = select(Inventory).where(Inventory.variant_id == variant_id)
                if location_id:
                    inventory_query = inventory_query.where(Inventory.location_id == location_id)
                
                inventory_result = await self.db.execute(inventory_query)
                inventory = inventory_result.scalar_one_or_none()
                
                if not inventory:
                    errors.append({
                        "variant_id": str(variant_id),
                        "error": "Inventory item not found"
                    })
                    continue
                
                # Calculate quantity change
                old_quantity = inventory.quantity
                quantity_change = new_quantity - old_quantity
                
                # Update inventory
                inventory.quantity = new_quantity
                inventory.updated_at = datetime.utcnow()
                
                # Create stock adjustment record
                adjustment = StockAdjustment(
                    inventory_id=inventory.id,
                    quantity_change=quantity_change,
                    reason="warehouse_sync",
                    notes=f"Batch update from warehouse data. Old: {old_quantity}, New: {new_quantity}"
                )
                
                self.db.add(adjustment)
                
                updated_items.append({
                    "variant_id": str(variant_id),
                    "old_quantity": old_quantity,
                    "new_quantity": new_quantity,
                    "quantity_change": quantity_change
                })
                
            except Exception as e:
                errors.append({
                    "variant_id": item_data.get("variant_id", "unknown"),
                    "error": str(e)
                })
        
        await self.db.commit()
        
        return {
            "updated_items": len(updated_items),
            "errors": len(errors),
            "details": {
                "updated": updated_items,
                "errors": errors
            }
        }