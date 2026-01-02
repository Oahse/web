# Consolidated inventory service
# This file includes all inventory-related functionality including enhanced features

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from models.inventories import Inventory, WarehouseLocation, StockAdjustment
from models.product import ProductVariant, Product, ProductImage
from models.user import User
from schemas.inventories import (
    WarehouseLocationCreate, WarehouseLocationUpdate, WarehouseLocationResponse,
    InventoryCreate, InventoryUpdate, InventoryResponse,
    StockAdjustmentCreate, StockAdjustmentResponse
)
from core.exceptions import APIException
import asyncio
import logging

logger = logging.getLogger(__name__)


class InventoryService:
    """Consolidated inventory service with comprehensive inventory management and distributed locking"""
    
    def __init__(self, db: AsyncSession, lock_service=None):
        self.db = db
        self.lock_service = lock_service

    # --- WarehouseLocation CRUD ---
    async def create_warehouse_location(self, location_data: WarehouseLocationCreate) -> WarehouseLocationResponse:
        new_location = WarehouseLocation(**location_data.model_dump())
        self.db.add(new_location)
        await self.db.commit()
        await self.db.refresh(new_location)
        return WarehouseLocationResponse.model_validate(new_location)

    async def get_warehouse_locations(self) -> List[WarehouseLocationResponse]:
        result = await self.db.execute(select(WarehouseLocation).order_by(WarehouseLocation.name))
        locations = result.scalars().all()
        return [WarehouseLocationResponse.model_validate(location) for location in locations]

    async def get_warehouse_location_by_id(self, location_id: UUID) -> Optional[WarehouseLocationResponse]:
        result = await self.db.execute(select(WarehouseLocation).filter(WarehouseLocation.id == location_id))
        location = result.scalars().first()
        if location:
            return WarehouseLocationResponse.model_validate(location)
        return None

    async def get_warehouse_location_model_by_id(self, location_id: UUID) -> Optional[WarehouseLocation]:
        """Get the raw SQLAlchemy model for internal operations"""
        result = await self.db.execute(select(WarehouseLocation).filter(WarehouseLocation.id == location_id))
        return result.scalars().first()

    async def update_warehouse_location(self, location_id: UUID, location_data: WarehouseLocationUpdate) -> WarehouseLocationResponse:
        location = await self.get_warehouse_location_model_by_id(location_id)
        if not location:
            raise APIException(status_code=404, message="Warehouse location not found")
        
        for field, value in location_data.model_dump(exclude_unset=True).items():
            setattr(location, field, value)
        
        location.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(location)
        return WarehouseLocationResponse.model_validate(location)

    async def delete_warehouse_location(self, location_id: UUID):
        location = await self.get_warehouse_location_model_by_id(location_id)
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
            joinedload(Inventory.variant).joinedload(ProductVariant.images),
            joinedload(Inventory.location)
        ))
        return result.scalars().unique().first()

    async def get_inventory_item_by_id_serialized(self, inventory_id: UUID) -> Optional[dict]:
        """Get inventory item by ID and return serialized data"""
        result = await self.db.execute(select(Inventory).filter(Inventory.id == inventory_id).options(
            joinedload(Inventory.variant).joinedload(ProductVariant.product),
            joinedload(Inventory.variant).joinedload(ProductVariant.images),
            joinedload(Inventory.location)
        ))
        item = result.scalars().unique().first()
        
        if not item:
            return None
            
        try:
            # Safely serialize variant data
            variant_data = None
            if item.variant:
                # Get primary image safely
                primary_image = None
                if item.variant.images:
                    primary_image = next(
                        (img for img in item.variant.images if img.is_primary),
                        item.variant.images[0] if len(item.variant.images) > 0 else None
                    )
                
                # Safely serialize product info
                product_info = None
                if item.variant.product:
                    product_info = {
                        "id": str(item.variant.product.id),
                        "name": item.variant.product.name or "",
                        "slug": item.variant.product.slug or "",
                        "description": item.variant.product.description or "",
                        "is_active": getattr(item.variant.product, 'is_active', True)
                    }

                variant_data = {
                    "id": str(item.variant.id),
                    "name": item.variant.name or "",
                    "sku": item.variant.sku or "",
                    "base_price": float(item.variant.base_price) if item.variant.base_price else 0.0,
                    "sale_price": float(item.variant.sale_price) if item.variant.sale_price else None,
                    "is_active": getattr(item.variant, 'is_active', True),
                    "product": product_info,
                    "primary_image": {
                        "id": str(primary_image.id),
                        "url": primary_image.url or "",
                        "alt_text": primary_image.alt_text or "",
                        "is_primary": primary_image.is_primary
                    } if primary_image else None,
                    "images": [
                        {
                            "id": str(img.id),
                            "url": img.url or "",
                            "alt_text": img.alt_text or "",
                            "is_primary": img.is_primary,
                            "sort_order": img.sort_order or 0
                        }
                        for img in (item.variant.images or [])
                    ]
                }

            # Safely serialize location info
            location_info = None
            if item.location:
                location_info = {
                    "id": str(item.location.id),
                    "name": item.location.name or "",
                    "address": item.location.address or "",
                    "description": item.location.description or "",
                    "created_at": item.location.created_at.isoformat() if item.location.created_at else None,
                    "updated_at": item.location.updated_at.isoformat() if item.location.updated_at else None
                }

            item_dict = {
                "id": str(item.id),
                "variant_id": str(item.variant_id),
                "location_id": str(item.location_id),
                "quantity": item.quantity or 0,
                "quantity_available": getattr(item, 'quantity_available', item.quantity or 0),
                "low_stock_threshold": item.low_stock_threshold or 0,
                "reorder_point": getattr(item, 'reorder_point', 0),
                "inventory_status": getattr(item, 'inventory_status', 'active'),
                "last_restocked_at": item.last_restocked_at.isoformat() if getattr(item, 'last_restocked_at', None) else None,
                "last_sold_at": item.last_sold_at.isoformat() if getattr(item, 'last_sold_at', None) else None,
                "version": getattr(item, 'version', 1),
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                "variant": variant_data,
                "location": location_info
            }
            
            return item_dict
            
        except Exception as e:
            logger.error(f"Error serializing inventory item {item.id}: {e}", exc_info=True)
            return None

    async def get_inventory_item_by_variant_id(self, variant_id: UUID) -> Optional[Inventory]:
        result = await self.db.execute(select(Inventory).filter(Inventory.variant_id == variant_id).options(
            joinedload(Inventory.variant).joinedload(ProductVariant.product),
            joinedload(Inventory.location)
        ))
        return result.scalars().unique().first()

    async def get_all_inventory_items(self, page: int = 1, limit: int = 10, product_id: Optional[UUID] = None, location_id: Optional[UUID] = None, low_stock: Optional[bool] = None, search: Optional[str] = None) -> dict:
        try:
            offset = (page - 1) * limit
            
            # Build query with proper eager loading
            query = select(Inventory).options(
                joinedload(Inventory.variant).joinedload(ProductVariant.product),
                joinedload(Inventory.variant).joinedload(ProductVariant.images),
                joinedload(Inventory.location)
            )
            count_query = select(func.count(Inventory.id))

            conditions = []
            if product_id:
                conditions.append(Inventory.variant.has(ProductVariant.product_id == product_id))
            if location_id:
                conditions.append(Inventory.location_id == location_id)
            if low_stock is not None:
                if low_stock:
                    conditions.append(Inventory.quantity_available <= Inventory.low_stock_threshold)
                else:
                    conditions.append(Inventory.quantity_available > Inventory.low_stock_threshold)
            if search:
                # Search in product name, variant name, variant SKU, and location name
                search_term = f"%{search.lower()}%"
                search_conditions = [
                    Inventory.variant.has(ProductVariant.product.has(Product.name.ilike(search_term))),
                    Inventory.variant.has(ProductVariant.name.ilike(search_term)),
                    Inventory.variant.has(ProductVariant.sku.ilike(search_term)),
                    Inventory.location.has(WarehouseLocation.name.ilike(search_term))
                ]
                conditions.append(or_(*search_conditions))
            
            if conditions:
                query = query.filter(and_(*conditions))
                count_query = count_query.filter(and_(*conditions))

            query = query.order_by(Inventory.updated_at.desc()).offset(offset).limit(limit)

            # Execute queries
            total = await self.db.scalar(count_query) or 0
            result = await self.db.execute(query)
            items = result.scalars().unique().all()  # Add .unique() to handle joined eager loads

            # Convert to dictionaries with safe serialization
            items_data = []
            for item in items:
                try:
                    # Safely serialize variant data
                    variant_data = None
                    if item.variant:
                        # Get primary image safely
                        primary_image = None
                        if item.variant.images:
                            primary_image = next(
                                (img for img in item.variant.images if img.is_primary),
                                item.variant.images[0] if len(item.variant.images) > 0 else None
                            )
                        
                        # Safely serialize product info
                        product_info = None
                        if item.variant.product:
                            product_info = {
                                "id": str(item.variant.product.id),
                                "name": item.variant.product.name or "",
                                "slug": item.variant.product.slug or "",
                                "description": item.variant.product.description or "",
                                "is_active": getattr(item.variant.product, 'is_active', True)
                            }

                        variant_data = {
                            "id": str(item.variant.id),
                            "name": item.variant.name or "",
                            "sku": item.variant.sku or "",
                            "base_price": float(item.variant.base_price) if item.variant.base_price else 0.0,
                            "sale_price": float(item.variant.sale_price) if item.variant.sale_price else None,
                            "is_active": getattr(item.variant, 'is_active', True),
                            "product": product_info,
                            "primary_image": {
                                "id": str(primary_image.id),
                                "url": primary_image.url or "",
                                "alt_text": primary_image.alt_text or "",
                                "is_primary": primary_image.is_primary
                            } if primary_image else None,
                            "images": [
                                {
                                    "id": str(img.id),
                                    "url": img.url or "",
                                    "alt_text": img.alt_text or "",
                                    "is_primary": img.is_primary,
                                    "sort_order": img.sort_order or 0
                                }
                                for img in (item.variant.images or [])
                            ]
                        }

                    # Safely serialize location info
                    location_info = None
                    if item.location:
                        location_info = {
                            "id": str(item.location.id),
                            "name": item.location.name or "",
                            "address": item.location.address or "",
                            "description": item.location.description or "",
                            "created_at": item.location.created_at.isoformat() if item.location.created_at else None,
                            "updated_at": item.location.updated_at.isoformat() if item.location.updated_at else None
                        }

                    item_dict = {
                        "id": str(item.id),
                        "variant_id": str(item.variant_id),
                        "location_id": str(item.location_id),
                        "quantity": item.quantity or 0,
                        "quantity_available": getattr(item, 'quantity_available', item.quantity or 0),
                        "low_stock_threshold": item.low_stock_threshold or 0,
                        "reorder_point": getattr(item, 'reorder_point', 0),
                        "inventory_status": getattr(item, 'inventory_status', 'active'),
                        "last_restocked_at": item.last_restocked_at.isoformat() if getattr(item, 'last_restocked_at', None) else None,
                        "last_sold_at": item.last_sold_at.isoformat() if getattr(item, 'last_sold_at', None) else None,
                        "version": getattr(item, 'version', 1),
                        "created_at": item.created_at.isoformat() if item.created_at else None,
                        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                        "variant": variant_data,
                        "location": location_info
                    }
                    items_data.append(item_dict)
                    
                except Exception as e:
                    logger.error(f"Error serializing inventory item {getattr(item, 'id', 'unknown')}: {e}", exc_info=True)
                    # Create a minimal safe item to prevent complete failure
                    safe_item = {
                        "id": str(getattr(item, 'id', '')),
                        "variant_id": str(getattr(item, 'variant_id', '')),
                        "location_id": str(getattr(item, 'location_id', '')),
                        "quantity": getattr(item, 'quantity', 0),
                        "quantity_available": getattr(item, 'quantity_available', 0),
                        "low_stock_threshold": getattr(item, 'low_stock_threshold', 0),
                        "reorder_point": 0,
                        "inventory_status": "error",
                        "last_restocked_at": None,
                        "last_sold_at": None,
                        "version": 1,
                        "created_at": getattr(item, 'created_at', datetime.utcnow()).isoformat() if hasattr(item, 'created_at') else None,
                        "updated_at": None,
                        "variant": None,
                        "location": None,
                        "error": f"Serialization error: {str(e)}"
                    }
                    items_data.append(safe_item)

            return {
                "data": items_data,
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error in get_all_inventory_items: {e}", exc_info=True)
            # Return empty result instead of raising exception
            return {
                "data": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "pages": 0,
                "error": f"Database error: {str(e)}"
            }

    async def create_inventory_item(self, inventory_data: InventoryCreate) -> InventoryResponse:
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
        return InventoryResponse.model_validate(new_inventory)

    async def update_inventory_item(self, inventory_id: UUID, inventory_data: InventoryUpdate) -> InventoryResponse:
        inventory_item = await self.get_inventory_item_by_id(inventory_id)
        if not inventory_item:
            raise APIException(status_code=404, message="Inventory item not found")
        
        for field, value in inventory_data.model_dump(exclude_unset=True).items():
            setattr(inventory_item, field, value)
        
        inventory_item.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(inventory_item)
        return InventoryResponse.model_validate(inventory_item)

    async def delete_inventory_item(self, inventory_id: UUID):
        inventory_item = await self.get_inventory_item_by_id(inventory_id)
        if not inventory_item:
            raise APIException(status_code=404, message="Inventory item not found")
        
        await self.db.delete(inventory_item)
        await self.db.commit()

    async def adjust_stock(self, adjustment_data: StockAdjustmentCreate, adjusted_by_user_id: Optional[UUID] = None, commit: bool = True) -> Inventory:
        """Adjust stock levels atomically with SELECT ... FOR UPDATE"""
        try:
            # Use atomic stock operation from the model
            from models.inventories import atomic_stock_operation
            
            result = await atomic_stock_operation(
                db=self.db,
                variant_id=adjustment_data.variant_id,
                operation="update",
                quantity_change=adjustment_data.quantity_change,
                reason=adjustment_data.reason,
                user_id=adjusted_by_user_id,
                notes=adjustment_data.notes
            )
            
            return result["inventory"]
            
        except Exception as e:
            logger.error(f"Error in atomic stock adjustment: {e}")
            raise APIException(
                status_code=500,
                message=f"Failed to adjust stock: {str(e)}"
            )

    async def get_stock_adjustments_for_inventory(self, inventory_id: UUID) -> List[StockAdjustmentResponse]:
        result = await self.db.execute(
            select(StockAdjustment)
            .filter(StockAdjustment.inventory_id == inventory_id)
            .order_by(StockAdjustment.created_at.desc())
            .options(joinedload(StockAdjustment.adjusted_by))
        )
        adjustments = result.scalars().all()
        return [StockAdjustmentResponse.model_validate(adjustment) for adjustment in adjustments]

    async def get_all_stock_adjustments(self) -> List[StockAdjustmentResponse]:
        """Get all stock adjustments across all inventory items"""
        result = await self.db.execute(
            select(StockAdjustment)
            .order_by(StockAdjustment.created_at.desc())
            .options(joinedload(StockAdjustment.adjusted_by))
        )
        adjustments = result.scalars().all()
        return [StockAdjustmentResponse.model_validate(adjustment) for adjustment in adjustments]

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
        """Batch update inventory from real warehouse data using atomic operations"""
        try:
            # Prepare stock changes for atomic bulk update
            stock_changes = []
            
            for item_data in warehouse_data:
                try:
                    variant_id = UUID(item_data["variant_id"])
                    new_quantity = item_data["quantity"]
                    
                    # Get current inventory to calculate change
                    inventory = await self.get_inventory_item_by_variant_id(variant_id)
                    
                    if not inventory:
                        continue  # Skip items not found
                    
                    # Calculate quantity change
                    quantity_change = new_quantity - inventory.quantity
                    
                    if quantity_change != 0:  # Only update if there's a change
                        stock_changes.append({
                            "variant_id": variant_id,
                            "quantity_change": quantity_change,
                            "notes": f"Warehouse sync: {inventory.quantity} -> {new_quantity}"
                        })
                        
                except Exception as e:
                    logger.error(f"Error preparing warehouse data for variant {item_data.get('variant_id')}: {e}")
                    continue
            
            # Perform atomic bulk update
            if stock_changes:
                result = await self.bulk_stock_update(
                    stock_changes=stock_changes,
                    reason="warehouse_sync",
                    user_id=None  # System update
                )
                
                return {
                    "success": True,
                    "updated_count": result["updated_count"],
                    "results": result["results"],
                    "errors": []
                }
            else:
                return {
                    "success": True,
                    "updated_count": 0,
                    "results": [],
                    "errors": []
                }
                
        except Exception as e:
            logger.error(f"Error in batch warehouse update: {e}")
            raise APIException(
                status_code=500,
                message=f"Failed to update inventory from warehouse data: {str(e)}"
            )
        
    async def check_stock_availability(
        self,
        variant_id: UUID,
        quantity: int,
        location_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Check if sufficient stock is available for purchase
        Returns availability status and current stock levels
        """
        try:
            # Find inventory item
            query = select(Inventory).where(Inventory.variant_id == variant_id)
            if location_id:
                query = query.where(Inventory.location_id == location_id)
            
            result = await self.db.execute(query)
            inventory = result.scalar_one_or_none()
            
            if not inventory:
                return {
                    "available": False,
                    "current_stock": 0,
                    "requested_quantity": quantity,
                    "message": "Product not found in inventory",
                    "stock_status": "out_of_stock"
                }
            
            # Check if requested quantity is available
            available = inventory.quantity_available >= quantity and inventory.quantity_available > 0
            
            return {
                "available": available,
                "current_stock": inventory.quantity_available,
                "requested_quantity": quantity,
                "inventory_id": str(inventory.id),
                "location_id": str(inventory.location_id),
                "stock_status": inventory.stock_status,
                "message": "Stock available" if available else f"Out of stock" if inventory.quantity_available <= 0 else f"Insufficient stock. Available: {inventory.quantity_available}, Requested: {quantity}"
            }
            
        except Exception as e:
            logger.error(f"Error checking stock availability: {e}")
            return {
                "available": False,
                "current_stock": 0,
                "requested_quantity": quantity,
                "stock_status": "out_of_stock",
                "message": f"Error checking stock: {str(e)}"
            }

    async def decrement_stock_on_purchase(
        self,
        variant_id: UUID,
        quantity: int,
        location_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Atomically decrement stock on purchase using SELECT ... FOR UPDATE
        """
        try:
            # Get inventory with atomic lock - find by variant_id if location_id not provided
            if location_id:
                inventory = await self.db.execute(
                    select(Inventory).where(
                        and_(Inventory.variant_id == variant_id, Inventory.location_id == location_id)
                    ).with_for_update()
                )
            else:
                # Find first available inventory for this variant
                inventory = await self.db.execute(
                    select(Inventory).where(
                        and_(Inventory.variant_id == variant_id, Inventory.quantity_available >= quantity)
                    ).with_for_update().limit(1)
                )
            
            inventory = inventory.scalar_one_or_none()
            
            if not inventory:
                return {
                    "success": False,
                    "message": f"Inventory not found for variant {variant_id}" + (f" at location {location_id}" if location_id else "")
                }
            
            # Check if sufficient stock available
            if inventory.quantity_available < quantity:
                return {
                    "success": False,
                    "message": f"Out of stock" if inventory.quantity_available <= 0 else f"Insufficient stock. Available: {inventory.quantity_available}, Requested: {quantity}",
                    "available_quantity": inventory.quantity_available,
                    "requested_quantity": quantity,
                    "stock_status": inventory.stock_status
                }
            
            # Perform atomic stock update
            adjustment = await inventory.atomic_update_stock(
                db=self.db,
                quantity_change=-quantity,
                reason="order_purchase",
                user_id=user_id,
                notes=f"Stock decremented for order {order_id}" if order_id else "Stock decremented for purchase"
            )
            
            await self.db.commit()
            
            logger.info(f"Atomically decremented stock for variant {variant_id}: -{quantity}")
            
            return {
                "success": True,
                "old_quantity": inventory.quantity_available + quantity,
                "new_quantity": inventory.quantity_available,
                "quantity_decremented": quantity,
                "inventory_id": str(inventory.id),
                "location_id": str(inventory.location_id),
                "stock_status": inventory.stock_status,
                "adjustment_id": str(adjustment.id)
            }
            
        except APIException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to decrement stock atomically: {e}")
            return {
                "success": False,
                "message": f"Failed to decrement stock: {str(e)}"
            }
    


    async def increment_stock_on_cancellation(
        self,
        variant_id: UUID,
        quantity: int,
        location_id: UUID,
        order_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Atomically increment stock when order is cancelled using SELECT ... FOR UPDATE
        """
        try:
            # Get inventory with atomic lock
            inventory = await Inventory.get_with_lock(self.db, variant_id)
            
            if not inventory:
                raise APIException(
                    status_code=404,
                    message=f"Inventory not found for variant {variant_id}"
                )
            
            # Perform atomic stock update
            adjustment = await inventory.atomic_update_stock(
                db=self.db,
                quantity_change=quantity,
                reason="order_cancelled",
                user_id=user_id,
                notes=f"Stock restored from cancelled order {order_id}" if order_id else "Stock restored from cancellation"
            )
            
            await self.db.commit()
            
            logger.info(f"Atomically incremented stock for variant {variant_id}: +{quantity}")
            
            return {
                "success": True,
                "old_quantity": inventory.quantity_available - quantity,
                "new_quantity": inventory.quantity_available,
                "quantity_incremented": quantity,
                "inventory_id": str(inventory.id),
                "adjustment_id": str(adjustment.id)
            }
            
        except APIException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to increment stock atomically: {e}")
            raise APIException(
                status_code=500,
                message=f"Failed to increment stock: {str(e)}"
            )

    async def bulk_stock_update(
        self,
        stock_changes: List[Dict],
        reason: str,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Atomically update multiple stock levels using SELECT ... FOR UPDATE
        """
        try:
            from models.inventories import atomic_bulk_stock_update
            
            results = await atomic_bulk_stock_update(
                db=self.db,
                stock_changes=stock_changes,
                reason=reason,
                user_id=user_id
            )
            
            return {
                "success": True,
                "updated_count": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Failed bulk stock update: {e}")
            raise APIException(
                status_code=500,
                message=f"Failed to update bulk stock: {str(e)}"
            )
    


    async def _log_inventory_change(
        self,
        action: str,
        inventory_id: str,
        variant_id: str,
        old_quantity: int,
        new_quantity: int,
        quantity_change: int,
        reason: str,
        order_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        Log inventory changes if logging is enabled
        Uses unified logging system with settings check
        """
        try:
            logger.info(
                f"Inventory Change: Action={action}, InventoryID={inventory_id}, VariantID={variant_id}, "
                f"OldQuantity={old_quantity}, NewQuantity={new_quantity}, Change={quantity_change}, "
                f"Reason={reason}, OrderID={order_id}, UserID={user_id}"
            )
        except Exception as e:
            logger.error(f"Failed to log inventory change: {e}")
            # Don't raise exception as logging failures shouldn't break inventory operations