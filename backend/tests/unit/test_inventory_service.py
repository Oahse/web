"""
Unit tests for inventory service
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from decimal import Decimal
from uuid import uuid4
from datetime import datetime

from services.inventory import InventoryService
from models.inventories import Inventory, StockMovement, StockMovementType
from models.product import ProductVariant
from core.errors import APIException


class TestInventoryService:
    
    @pytest_asyncio.fixture
    async def inventory_service(self, db_session):
        return InventoryService(db_session)
    
    @pytest.mark.asyncio
    async def test_get_inventory_by_variant(self, inventory_service, test_inventory):
        """Test getting inventory by variant ID"""
        inventory = await inventory_service.get_inventory_by_variant(test_inventory.variant_id)
        
        assert inventory.id == test_inventory.id
        assert inventory.variant_id == test_inventory.variant_id
        assert inventory.quantity_available == 100
    
    @pytest.mark.asyncio
    async def test_check_stock_availability_sufficient(self, inventory_service, test_inventory):
        """Test stock availability check with sufficient stock"""
        is_available = await inventory_service.check_stock_availability(
            test_inventory.variant_id,
            quantity=50
        )
        
        assert is_available is True
    
    @pytest.mark.asyncio
    async def test_check_stock_availability_insufficient(self, inventory_service, test_inventory):
        """Test stock availability check with insufficient stock"""
        is_available = await inventory_service.check_stock_availability(
            test_inventory.variant_id,
            quantity=150
        )
        
        assert is_available is False
    
    @pytest.mark.asyncio
    async def test_reserve_stock_success(self, inventory_service, test_inventory):
        """Test successful stock reservation"""
        quantity_to_reserve = 25
        
        reserved_inventory = await inventory_service.reserve_stock(
            test_inventory.variant_id,
            quantity_to_reserve,
            reference_id=uuid4(),
            reference_type="order"
        )
        
        assert reserved_inventory.quantity_reserved == quantity_to_reserve
        assert reserved_inventory.quantity_available == 100 - quantity_to_reserve
    
    @pytest.mark.asyncio
    async def test_reserve_stock_insufficient(self, inventory_service, test_inventory):
        """Test stock reservation with insufficient stock"""
        quantity_to_reserve = 150
        
        with pytest.raises(APIException) as exc_info:
            await inventory_service.reserve_stock(
                test_inventory.variant_id,
                quantity_to_reserve,
                reference_id=uuid4(),
                reference_type="order"
            )
        
        assert exc_info.value.status_code == 400
        assert "insufficient stock" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_release_stock_reservation(self, inventory_service, test_inventory):
        """Test releasing stock reservation"""
        # First reserve some stock
        quantity_reserved = 25
        reference_id = uuid4()
        
        await inventory_service.reserve_stock(
            test_inventory.variant_id,
            quantity_reserved,
            reference_id=reference_id,
            reference_type="order"
        )
        
        # Then release the reservation
        released_inventory = await inventory_service.release_stock_reservation(
            test_inventory.variant_id,
            quantity_reserved,
            reference_id=reference_id
        )
        
        assert released_inventory.quantity_reserved == 0
        assert released_inventory.quantity_available == 100
    
    @pytest.mark.asyncio
    async def test_fulfill_stock_reservation(self, inventory_service, test_inventory):
        """Test fulfilling stock reservation (converting to actual sale)"""
        # First reserve some stock
        quantity_reserved = 25
        reference_id = uuid4()
        
        await inventory_service.reserve_stock(
            test_inventory.variant_id,
            quantity_reserved,
            reference_id=reference_id,
            reference_type="order"
        )
        
        # Then fulfill the reservation
        fulfilled_inventory = await inventory_service.fulfill_stock_reservation(
            test_inventory.variant_id,
            quantity_reserved,
            reference_id=reference_id
        )
        
        assert fulfilled_inventory.quantity_reserved == 0
        assert fulfilled_inventory.quantity_available == 100 - quantity_reserved
    
    @pytest.mark.asyncio
    async def test_add_stock(self, inventory_service, test_inventory):
        """Test adding stock to inventory"""
        quantity_to_add = 50
        
        updated_inventory = await inventory_service.add_stock(
            test_inventory.variant_id,
            quantity_to_add,
            reason="restock",
            reference_id=uuid4()
        )
        
        assert updated_inventory.quantity_available == 100 + quantity_to_add
    
    @pytest.mark.asyncio
    async def test_remove_stock(self, inventory_service, test_inventory):
        """Test removing stock from inventory"""
        quantity_to_remove = 30
        
        updated_inventory = await inventory_service.remove_stock(
            test_inventory.variant_id,
            quantity_to_remove,
            reason="damaged",
            reference_id=uuid4()
        )
        
        assert updated_inventory.quantity_available == 100 - quantity_to_remove
    
    @pytest.mark.asyncio
    async def test_remove_stock_insufficient(self, inventory_service, test_inventory):
        """Test removing more stock than available"""
        quantity_to_remove = 150
        
        with pytest.raises(APIException) as exc_info:
            await inventory_service.remove_stock(
                test_inventory.variant_id,
                quantity_to_remove,
                reason="damaged",
                reference_id=uuid4()
            )
        
        assert exc_info.value.status_code == 400
        assert "insufficient stock" in str(exc_info.value.message).lower()
    
    @pytest.mark.asyncio
    async def test_transfer_stock_between_warehouses(self, inventory_service, test_product, db_session):
        """Test transferring stock between warehouses"""
        product, variant = test_product
        
        # Create two warehouse inventories
        warehouse1 = Inventory(
            id=uuid4(),
            variant_id=variant.id,
            warehouse_location="WH-001",
            quantity_available=100,
            quantity_reserved=0
        )
        warehouse2 = Inventory(
            id=uuid4(),
            variant_id=variant.id,
            warehouse_location="WH-002",
            quantity_available=50,
            quantity_reserved=0
        )
        db_session.add_all([warehouse1, warehouse2])
        await db_session.commit()
        
        transfer_quantity = 25
        
        await inventory_service.transfer_stock(
            variant.id,
            from_warehouse="WH-001",
            to_warehouse="WH-002",
            quantity=transfer_quantity,
            reference_id=uuid4()
        )
        
        # Refresh inventories
        await db_session.refresh(warehouse1)
        await db_session.refresh(warehouse2)
        
        assert warehouse1.quantity_available == 100 - transfer_quantity
        assert warehouse2.quantity_available == 50 + transfer_quantity
    
    @pytest.mark.asyncio
    async def test_get_low_stock_items(self, inventory_service, test_inventory):
        """Test getting items with low stock"""
        # Set inventory below reorder level
        test_inventory.quantity_available = 5
        test_inventory.reorder_level = 10
        await inventory_service.db.commit()
        
        low_stock_items = await inventory_service.get_low_stock_items()
        
        assert len(low_stock_items) == 1
        assert low_stock_items[0].id == test_inventory.id
    
    @pytest.mark.asyncio
    async def test_get_stock_movements(self, inventory_service, test_inventory):
        """Test getting stock movement history"""
        # Create some stock movements
        movement1 = StockMovement(
            id=uuid4(),
            inventory_id=test_inventory.id,
            movement_type=StockMovementType.IN,
            quantity=50,
            reason="restock",
            created_at=datetime.utcnow()
        )
        movement2 = StockMovement(
            id=uuid4(),
            inventory_id=test_inventory.id,
            movement_type=StockMovementType.OUT,
            quantity=25,
            reason="sale",
            created_at=datetime.utcnow()
        )
        inventory_service.db.add_all([movement1, movement2])
        await inventory_service.db.commit()
        
        movements = await inventory_service.get_stock_movements(test_inventory.variant_id)
        
        assert len(movements) >= 2
        assert any(m.movement_type == StockMovementType.IN for m in movements)
        assert any(m.movement_type == StockMovementType.OUT for m in movements)
    
    @pytest.mark.asyncio
    async def test_calculate_stock_value(self, inventory_service, test_inventory, test_product):
        """Test calculating total stock value"""
        product, variant = test_product
        
        # Set variant cost
        variant.cost = Decimal("50.00")
        await inventory_service.db.commit()
        
        stock_value = await inventory_service.calculate_stock_value(test_inventory.variant_id)
        
        # 100 units * $50.00 cost = $5000.00
        expected_value = test_inventory.quantity_available * variant.cost
        assert stock_value == expected_value
    
    @pytest.mark.asyncio
    async def test_bulk_stock_update(self, inventory_service, test_product, db_session):
        """Test bulk stock updates"""
        product, variant = test_product
        
        # Create multiple inventory records
        inventories = []
        for i in range(3):
            inventory = Inventory(
                id=uuid4(),
                variant_id=variant.id,
                warehouse_location=f"WH-00{i+1}",
                quantity_available=100,
                quantity_reserved=0
            )
            inventories.append(inventory)
        
        db_session.add_all(inventories)
        await db_session.commit()
        
        # Bulk update
        updates = [
            {"variant_id": variant.id, "warehouse_location": "WH-001", "quantity": 150},
            {"variant_id": variant.id, "warehouse_location": "WH-002", "quantity": 75},
            {"variant_id": variant.id, "warehouse_location": "WH-003", "quantity": 200}
        ]
        
        updated_inventories = await inventory_service.bulk_update_stock(updates)
        
        assert len(updated_inventories) == 3
        assert updated_inventories[0].quantity_available == 150
        assert updated_inventories[1].quantity_available == 75
        assert updated_inventories[2].quantity_available == 200
    
    @pytest.mark.asyncio
    async def test_inventory_audit(self, inventory_service, test_inventory):
        """Test inventory audit functionality"""
        # Perform audit count
        actual_count = 95  # 5 less than system count
        
        audit_result = await inventory_service.perform_inventory_audit(
            test_inventory.variant_id,
            test_inventory.warehouse_location,
            actual_count,
            auditor_id=uuid4()
        )
        
        assert audit_result["discrepancy"] == -5  # 5 units missing
        assert audit_result["adjustment_made"] is True
        
        # Check inventory was adjusted
        await inventory_service.db.refresh(test_inventory)
        assert test_inventory.quantity_available == actual_count
    
    @pytest.mark.asyncio
    async def test_concurrent_stock_operations(self, inventory_service, test_inventory):
        """Test concurrent stock operations don't cause race conditions"""
        import asyncio
        
        async def reserve_stock_task(quantity):
            try:
                await inventory_service.reserve_stock(
                    test_inventory.variant_id,
                    quantity,
                    reference_id=uuid4(),
                    reference_type="order"
                )
                return True
            except APIException:
                return False
        
        # Try to reserve more stock than available concurrently
        tasks = [reserve_stock_task(60) for _ in range(3)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Only one should succeed, others should fail
        successful_reservations = sum(1 for r in results if r is True)
        assert successful_reservations <= 1  # At most one should succeed
    
    @pytest.mark.asyncio
    async def test_stock_alerts(self, inventory_service, test_inventory):
        """Test stock alert generation"""
        # Set inventory to trigger alerts
        test_inventory.quantity_available = 5
        test_inventory.reorder_level = 10
        test_inventory.max_stock_level = 500
        await inventory_service.db.commit()
        
        alerts = await inventory_service.get_stock_alerts(test_inventory.variant_id)
        
        assert len(alerts) > 0
        assert any("low stock" in alert["message"].lower() for alert in alerts)
    
    @pytest.mark.asyncio
    async def test_inventory_forecasting(self, inventory_service, test_inventory):
        """Test inventory demand forecasting"""
        # Mock historical sales data
        with patch.object(inventory_service, '_get_historical_sales') as mock_sales:
            mock_sales.return_value = [
                {"date": "2024-01-01", "quantity": 10},
                {"date": "2024-01-02", "quantity": 15},
                {"date": "2024-01-03", "quantity": 12}
            ]
            
            forecast = await inventory_service.forecast_demand(
                test_inventory.variant_id,
                days=30
            )
            
            assert "predicted_demand" in forecast
            assert "recommended_reorder_quantity" in forecast
            assert "stockout_risk" in forecast
            assert forecast["predicted_demand"] > 0