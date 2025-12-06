from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload, joinedload
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from models.inventory import Inventory, WarehouseLocation, StockAdjustment
from models.product import ProductVariant
from models.user import User # For adjusted_by_user_id relationship
from schemas.inventory import (
    WarehouseLocationCreate, WarehouseLocationUpdate,
    InventoryCreate, InventoryUpdate,
    StockAdjustmentCreate
)
from core.exceptions import APIException


class InventoryService:
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
            "data": items, # These will be converted to response schemas by the router
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
        # For simplicity, if only variant_id is provided, assume default location or first found inventory item
        # In a more complex system, explicit inventory_id would be required or a robust location selection
        
        # If adjustment is by variant_id and location_id
        if adjustment_data.variant_id and adjustment_data.location_id:
            inventory_item_query = select(Inventory).filter(
                and_(
                    Inventory.variant_id == adjustment_data.variant_id,
                    Inventory.location_id == adjustment_data.location_id
                )
            )
        elif adjustment_data.variant_id:
            # Fallback to finding any inventory item for the variant
            inventory_item_query = select(Inventory).filter(Inventory.variant_id == adjustment_data.variant_id)
        else:
            raise APIException(status_code=400, message="Variant ID is required for stock adjustment.")

        inventory_item = await self.db.scalar(inventory_item_query)
        
        if not inventory_item:
            # If inventory item doesn't exist, create it with initial quantity
            if adjustment_data.variant_id and adjustment_data.location_id:
                initial_inventory_data = InventoryCreate(
                    variant_id=adjustment_data.variant_id,
                    location_id=adjustment_data.location_id,
                    quantity=adjustment_data.quantity_change,
                    low_stock_threshold=10 # Default
                )
                inventory_item = await self.create_inventory_item(initial_inventory_data)
                # No need to create stock adjustment for initial creation here, as it's part of creation.
                # Or, create a separate adjustment for 'initial_stock' reason.
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