from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from core.database import get_db
from core.utils.response import Response
from core.exceptions import APIException
from core.dependencies import require_admin_or_supplier
from models.user import User

from schemas.inventories import (
    WarehouseLocationCreate, WarehouseLocationUpdate, WarehouseLocationResponse,
    InventoryCreate, InventoryUpdate, InventoryResponse,
    StockAdjustmentCreate, StockAdjustmentResponse
)
from services.inventories import InventoryService

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory Management"])


# --- WarehouseLocation Endpoints ---
@router.post("/locations", response_model=WarehouseLocationResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse_location(
    location_data: WarehouseLocationCreate,
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db)
):
    """Create a new warehouse location (Admin/Supplier access)."""
    try:
        service = InventoryService(db)
        location = await service.create_warehouse_location(location_data)
        return Response(success=True, data=location, message="Warehouse location created successfully")
    except APIException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create location: {e}")


@router.get("/locations", response_model=List[WarehouseLocationResponse])
async def get_all_warehouse_locations(
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db)
):
    """Get all warehouse locations (Admin/Supplier access)."""
    try:
        service = InventoryService(db)
        locations = await service.get_warehouse_locations()
        return Response(success=True, data=locations)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch locations: {e}")


@router.get("/locations/{location_id}", response_model=WarehouseLocationResponse)
async def get_warehouse_location(
    location_id: UUID,
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific warehouse location by ID (Admin/Supplier access)."""
    try:
        service = InventoryService(db)
        location = await service.get_warehouse_location_by_id(location_id)
        if not location:
            raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="Warehouse location not found")
        return Response(success=True, data=location)
    except APIException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch location: {e}")


@router.put("/locations/{location_id}", response_model=WarehouseLocationResponse)
async def update_warehouse_location(
    location_id: UUID,
    location_data: WarehouseLocationUpdate,
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db)
):
    """Update a warehouse location (Admin/Supplier access)."""
    try:
        service = InventoryService(db)
        location = await service.update_warehouse_location(location_id, location_data)
        return Response(success=True, data=location, message="Warehouse location updated successfully")
    except APIException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update location: {e}")


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warehouse_location(
    location_id: UUID,
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db)
):
    """Delete a warehouse location (Admin/Supplier access)."""
    try:
        service = InventoryService(db)
        await service.delete_warehouse_location(location_id)
        return Response(success=True, message="Warehouse location deleted successfully")
    except APIException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete location: {e}")


# --- Inventory Item Endpoints ---
@router.post("/", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    inventory_data: InventoryCreate,
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db)
):
    """Create a new inventory item (Admin/Supplier access)."""
    try:
        service = InventoryService(db)
        item = await service.create_inventory_item(inventory_data)
        return Response(success=True, data=item, message="Inventory item created successfully")
    except APIException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create inventory item: {e}")


@router.get("/", response_model=List[InventoryResponse])
async def get_all_inventory_items(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    product_id: Optional[UUID] = Query(None),
    location_id: Optional[UUID] = Query(None),
    low_stock: Optional[bool] = Query(None),
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db)
):
    """Get all inventory items with filters (Admin/Supplier access)."""
    try:
        service = InventoryService(db)
        items = await service.get_all_inventory_items(page, limit, product_id, location_id, low_stock)
        return Response(success=True, data=items)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch inventory items: {e}")


@router.get("/{inventory_id}", response_model=InventoryResponse)
async def get_inventory_item(
    inventory_id: UUID,
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific inventory item by ID (Admin/Supplier access)."""
    try:
        service = InventoryService(db)
        item = await service.get_inventory_item_by_id(inventory_id)
        if not item:
            raise APIException(status_code=status.HTTP_404_NOT_FOUND, message="Inventory item not found")
        return Response(success=True, data=item)
    except APIException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch inventory item: {e}")


@router.put("/{inventory_id}", response_model=InventoryResponse)
async def update_inventory_item(
    inventory_id: UUID,
    inventory_data: InventoryUpdate,
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db)
):
    """Update an inventory item (Admin/Supplier access)."""
    try:
        service = InventoryService(db)
        item = await service.update_inventory_item(inventory_id, inventory_data)
        return Response(success=True, data=item, message="Inventory item updated successfully")
    except APIException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update inventory item: {e}")


@router.delete("/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    inventory_id: UUID,
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db)
):
    """Delete an inventory item (Admin/Supplier access)."""
    try:
        service = InventoryService(db)
        await service.delete_inventory_item(inventory_id)
        return Response(success=True, message="Inventory item deleted successfully")
    except APIException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete inventory item: {e}")


# --- Stock Adjustment Endpoints ---
@router.post("/adjustments", response_model=InventoryResponse, status_code=status.HTTP_200_OK)
async def adjust_stock(
    adjustment_data: StockAdjustmentCreate,
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db)
):
    """Adjust stock quantity for an inventory item (Admin/Supplier access)."""
    try:
        service = InventoryService(db)
        updated_inventory = await service.adjust_stock(adjustment_data, adjusted_by_user_id=current_user.id)
        return Response(success=True, data=updated_inventory, message="Stock adjusted successfully")
    except APIException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to adjust stock: {e}")


@router.get("/{inventory_id}/adjustments", response_model=List[StockAdjustmentResponse])
async def get_stock_adjustments(
    inventory_id: UUID,
    current_user: User = Depends(require_admin_or_supplier),
    db: AsyncSession = Depends(get_db)
):
    """Get all stock adjustments for an inventory item (Admin/Supplier access)."""
    try:
        service = InventoryService(db)
        adjustments = await service.get_stock_adjustments_for_inventory(inventory_id)
        return Response(success=True, data=adjustments)
    except APIException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch stock adjustments: {e}")