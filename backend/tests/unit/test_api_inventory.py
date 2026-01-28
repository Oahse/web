"""
Tests for inventory API endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from decimal import Decimal

from models.inventories import Inventory, WarehouseLocation, StockAdjustment
from models.product import ProductVariant
from models.user import User


class TestInventoryAPI:
    """Test inventory API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_inventory_success(self, async_client: AsyncClient, admin_auth_headers: dict, test_inventory: Inventory):
        """Test getting inventory information."""
        response = await async_client.get(f"/inventory/variants/{test_inventory.variant_id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["variant_id"] == str(test_inventory.variant_id)
        assert data["data"]["quantity_available"] == test_inventory.quantity_available
        assert data["data"]["quantity_reserved"] == test_inventory.quantity_reserved
    
    @pytest.mark.asyncio
    async def test_get_inventory_unauthorized(self, async_client: AsyncClient, auth_headers: dict, test_inventory: Inventory):
        """Test getting inventory as non-admin user."""
        response = await async_client.get(f"/inventory/variants/{test_inventory.variant_id}", headers=auth_headers)
        
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "permission" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_get_inventory_not_found(self, async_client: AsyncClient, admin_auth_headers: dict):
        """Test getting inventory for nonexistent variant."""
        fake_id = uuid4()
        response = await async_client.get(f"/inventory/variants/{fake_id}", headers=admin_auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_update_inventory_success(self, async_client: AsyncClient, admin_auth_headers: dict, test_inventory: Inventory):
        """Test updating inventory levels."""
        update_data = {
            "quantity_available": 150,
            "reorder_point": 25,
            "reorder_quantity": 75
        }
        
        response = await async_client.put(f"/inventory/variants/{test_inventory.variant_id}", json=update_data, headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["quantity_available"] == 150
        assert data["data"]["reorder_point"] == 25
        assert data["data"]["reorder_quantity"] == 75
    
    @pytest.mark.asyncio
    async def test_adjust_stock_success(self, async_client: AsyncClient, admin_auth_headers: dict, test_inventory: Inventory):
        """Test stock adjustment."""
        adjustment_data = {
            "adjustment_type": "increase",
            "quantity": 50,
            "reason": "Restocking",
            "notes": "Weekly restock"
        }
        
        response = await async_client.post(f"/inventory/variants/{test_inventory.variant_id}/adjust", json=adjustment_data, headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["adjustment_type"] == "increase"
        assert data["data"]["quantity"] == 50
        assert data["data"]["reason"] == "Restocking"
    
    @pytest.mark.asyncio
    async def test_adjust_stock_decrease(self, async_client: AsyncClient, admin_auth_headers: dict, test_inventory: Inventory):
        """Test stock decrease adjustment."""
        adjustment_data = {
            "adjustment_type": "decrease",
            "quantity": 10,
            "reason": "Damaged goods",
            "notes": "Items damaged during shipping"
        }
        
        response = await async_client.post(f"/inventory/variants/{test_inventory.variant_id}/adjust", json=adjustment_data, headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["adjustment_type"] == "decrease"
        assert data["data"]["quantity"] == 10
    
    @pytest.mark.asyncio
    async def test_adjust_stock_insufficient_quantity(self, async_client: AsyncClient, admin_auth_headers: dict, test_inventory: Inventory):
        """Test stock adjustment with insufficient quantity."""
        adjustment_data = {
            "adjustment_type": "decrease",
            "quantity": test_inventory.quantity_available + 10,  # More than available
            "reason": "Test",
            "notes": "Should fail"
        }
        
        response = await async_client.post(f"/inventory/variants/{test_inventory.variant_id}/adjust", json=adjustment_data, headers=admin_auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "insufficient" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_get_low_stock_items(self, async_client: AsyncClient, admin_auth_headers: dict, db_session: AsyncSession, test_variant: ProductVariant, test_warehouse: WarehouseLocation):
        """Test getting low stock items."""
        # Create inventory with low stock
        low_stock_inventory = Inventory(
            id=uuid4(),
            variant_id=test_variant.id,
            warehouse_id=test_warehouse.id,
            quantity_available=5,  # Below reorder point
            quantity_reserved=0,
            reorder_point=10,
            reorder_quantity=50
        )
        db_session.add(low_stock_inventory)
        await db_session.commit()
        
        response = await async_client.get("/inventory/low-stock", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        
        # Check if our low stock item is in the results
        low_stock_items = [item for item in data["data"] if item["variant_id"] == str(test_variant.id)]
        assert len(low_stock_items) >= 1
    
    @pytest.mark.asyncio
    async def test_get_stock_movements(self, async_client: AsyncClient, admin_auth_headers: dict, test_inventory: Inventory):
        """Test getting stock movement history."""
        response = await async_client.get(f"/inventory/variants/{test_inventory.variant_id}/movements", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    @pytest.mark.asyncio
    async def test_get_reorder_suggestions(self, async_client: AsyncClient, admin_auth_headers: dict):
        """Test getting reorder suggestions."""
        response = await async_client.get("/inventory/reorder-suggestions", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


class TestWarehouseAPI:
    """Test warehouse API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_warehouses(self, async_client: AsyncClient, admin_auth_headers: dict, test_warehouse: WarehouseLocation):
        """Test getting warehouses."""
        response = await async_client.get("/inventory/warehouses", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        
        warehouse_data = data["data"][0]
        assert warehouse_data["id"] == str(test_warehouse.id)
        assert warehouse_data["name"] == test_warehouse.name
    
    @pytest.mark.asyncio
    async def test_create_warehouse(self, async_client: AsyncClient, admin_auth_headers: dict):
        """Test creating warehouse."""
        warehouse_data = {
            "name": "New Warehouse",
            "address": "456 New St",
            "city": "New City",
            "state": "NS",
            "country": "US",
            "postal_code": "67890",
            "is_active": True
        }
        
        response = await async_client.post("/inventory/warehouses", json=warehouse_data, headers=admin_auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == warehouse_data["name"]
        assert data["data"]["address"] == warehouse_data["address"]
    
    @pytest.mark.asyncio
    async def test_update_warehouse(self, async_client: AsyncClient, admin_auth_headers: dict, test_warehouse: WarehouseLocation):
        """Test updating warehouse."""
        update_data = {
            "name": "Updated Warehouse Name",
            "address": "Updated Address"
        }
        
        response = await async_client.put(f"/inventory/warehouses/{test_warehouse.id}", json=update_data, headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == update_data["name"]
        assert data["data"]["address"] == update_data["address"]
    
    @pytest.mark.asyncio
    async def test_delete_warehouse(self, async_client: AsyncClient, admin_auth_headers: dict, db_session: AsyncSession):
        """Test deleting warehouse."""
        # Create warehouse to delete
        warehouse = WarehouseLocation(
            id=uuid4(),
            name="Warehouse to Delete",
            address="Delete St",
            city="Delete City",
            state="DS",
            country="US",
            postal_code="00000",
            is_active=True
        )
        db_session.add(warehouse)
        await db_session.commit()
        
        response = await async_client.delete(f"/inventory/warehouses/{warehouse.id}", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Warehouse deleted successfully"


class TestInventoryValidation:
    """Test inventory validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_adjust_stock_invalid_type(self, async_client: AsyncClient, admin_auth_headers: dict, test_inventory: Inventory):
        """Test stock adjustment with invalid type."""
        adjustment_data = {
            "adjustment_type": "invalid_type",
            "quantity": 10,
            "reason": "Test"
        }
        
        response = await async_client.post(f"/inventory/variants/{test_inventory.variant_id}/adjust", json=adjustment_data, headers=admin_auth_headers)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_adjust_stock_negative_quantity(self, async_client: AsyncClient, admin_auth_headers: dict, test_inventory: Inventory):
        """Test stock adjustment with negative quantity."""
        adjustment_data = {
            "adjustment_type": "increase",
            "quantity": -10,  # Negative quantity
            "reason": "Test"
        }
        
        response = await async_client.post(f"/inventory/variants/{test_inventory.variant_id}/adjust", json=adjustment_data, headers=admin_auth_headers)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_update_inventory_negative_values(self, async_client: AsyncClient, admin_auth_headers: dict, test_inventory: Inventory):
        """Test updating inventory with negative values."""
        update_data = {
            "quantity_available": -10,  # Negative quantity
            "reorder_point": 25
        }
        
        response = await async_client.put(f"/inventory/variants/{test_inventory.variant_id}", json=update_data, headers=admin_auth_headers)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_warehouse_missing_fields(self, async_client: AsyncClient, admin_auth_headers: dict):
        """Test creating warehouse with missing required fields."""
        warehouse_data = {
            "name": "Incomplete Warehouse"
            # Missing required fields
        }
        
        response = await async_client.post("/inventory/warehouses", json=warehouse_data, headers=admin_auth_headers)
        
        assert response.status_code == 422


class TestInventoryReports:
    """Test inventory reporting endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_inventory_summary(self, async_client: AsyncClient, admin_auth_headers: dict):
        """Test getting inventory summary."""
        response = await async_client.get("/inventory/summary", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_variants" in data["data"]
        assert "total_quantity" in data["data"]
        assert "low_stock_count" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_inventory_valuation(self, async_client: AsyncClient, admin_auth_headers: dict):
        """Test getting inventory valuation."""
        response = await async_client.get("/inventory/valuation", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total_value" in data["data"]
        assert "currency" in data["data"]
    
    @pytest.mark.asyncio
    async def test_export_inventory_report(self, async_client: AsyncClient, admin_auth_headers: dict):
        """Test exporting inventory report."""
        response = await async_client.get("/inventory/export?format=csv", headers=admin_auth_headers)
        
        assert response.status_code == 200
        # Should return CSV content
        assert "text/csv" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_get_stock_alerts(self, async_client: AsyncClient, admin_auth_headers: dict):
        """Test getting stock alerts."""
        response = await async_client.get("/inventory/alerts", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


class TestInventoryBulkOperations:
    """Test inventory bulk operations."""
    
    @pytest.mark.asyncio
    async def test_bulk_stock_adjustment(self, async_client: AsyncClient, admin_auth_headers: dict, test_inventory: Inventory, test_variant: ProductVariant):
        """Test bulk stock adjustment."""
        bulk_data = {
            "adjustments": [
                {
                    "variant_id": str(test_inventory.variant_id),
                    "adjustment_type": "increase",
                    "quantity": 20,
                    "reason": "Bulk restock"
                }
            ]
        }
        
        response = await async_client.post("/inventory/bulk-adjust", json=bulk_data, headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["successful"]) >= 1
        assert len(data["data"]["failed"]) == 0
    
    @pytest.mark.asyncio
    async def test_bulk_inventory_update(self, async_client: AsyncClient, admin_auth_headers: dict, test_inventory: Inventory):
        """Test bulk inventory update."""
        bulk_data = {
            "updates": [
                {
                    "variant_id": str(test_inventory.variant_id),
                    "reorder_point": 15,
                    "reorder_quantity": 60
                }
            ]
        }
        
        response = await async_client.post("/inventory/bulk-update", json=bulk_data, headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]["successful"]) >= 1
    
    @pytest.mark.asyncio
    async def test_import_inventory_data(self, async_client: AsyncClient, admin_auth_headers: dict):
        """Test importing inventory data."""
        # Mock CSV data
        csv_data = "variant_id,quantity_available,reorder_point\n"
        csv_data += f"{uuid4()},100,20\n"
        
        files = {"file": ("inventory.csv", csv_data, "text/csv")}
        
        response = await async_client.post("/inventory/import", files=files, headers=admin_auth_headers)
        
        # May return 200 or 400 depending on validation
        assert response.status_code in [200, 400]
        data = response.json()
        assert data["success"] in [True, False]