"""
Unit tests for inventory operations and stock management
"""
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from datetime import datetime, timedelta

from services.inventory import InventoryService
from models.inventories import Inventory, WarehouseLocation, StockAdjustment
from models.product import ProductVariant, Product, Category
from models.user import User
from models.orders import Order, OrderItem


@pytest.mark.unit
class TestInventoryOperations:
    """Test inventory operations and stock management."""
    
    @pytest.mark.asyncio
    async def test_stock_increment_operation(self, db_session: AsyncSession):
        """Test stock increment operations."""
        # Setup test data
        inventory = await self._create_test_inventory(db_session)
        original_quantity = inventory.quantity_available
        
        inventory_service = InventoryService(db_session)
        
        # Increment stock
        increment_amount = 50
        updated_inventory = await inventory_service.adjust_stock(
            variant_id=inventory.variant_id,
            warehouse_id=inventory.warehouse_id,
            adjustment_type="increase",
            quantity=increment_amount,
            reason="Restocking",
            notes="Unit test increment"
        )
        
        assert updated_inventory.quantity_available == original_quantity + increment_amount
        
        # Verify stock adjustment record was created
        adjustment = await inventory_service.get_latest_stock_adjustment(inventory.variant_id)
        assert adjustment is not None
        assert adjustment.adjustment_type == "increase"
        assert adjustment.quantity == increment_amount
        assert adjustment.reason == "Restocking"
    
    @pytest.mark.asyncio
    async def test_stock_decrement_operation(self, db_session: AsyncSession):
        """Test stock decrement operations."""
        # Setup test data with sufficient stock
        inventory = await self._create_test_inventory(db_session, initial_quantity=100)
        original_quantity = inventory.quantity_available
        
        inventory_service = InventoryService(db_session)
        
        # Decrement stock
        decrement_amount = 25
        updated_inventory = await inventory_service.adjust_stock(
            variant_id=inventory.variant_id,
            warehouse_id=inventory.warehouse_id,
            adjustment_type="decrease",
            quantity=decrement_amount,
            reason="Damaged goods",
            notes="Unit test decrement"
        )
        
        assert updated_inventory.quantity_available == original_quantity - decrement_amount
        
        # Verify stock adjustment record
        adjustment = await inventory_service.get_latest_stock_adjustment(inventory.variant_id)
        assert adjustment.adjustment_type == "decrease"
        assert adjustment.quantity == decrement_amount
    
    @pytest.mark.asyncio
    async def test_stock_decrement_insufficient_quantity(self, db_session: AsyncSession):
        """Test stock decrement with insufficient quantity."""
        # Setup test data with low stock
        inventory = await self._create_test_inventory(db_session, initial_quantity=10)
        
        inventory_service = InventoryService(db_session)
        
        # Try to decrement more than available
        with pytest.raises(Exception) as exc_info:
            await inventory_service.adjust_stock(
                variant_id=inventory.variant_id,
                warehouse_id=inventory.warehouse_id,
                adjustment_type="decrease",
                quantity=20,  # More than available
                reason="Test",
                notes="Should fail"
            )
        
        assert "insufficient" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_stock_reservation_for_order(self, db_session: AsyncSession):
        """Test stock reservation when order is created."""
        # Setup test data
        inventory = await self._create_test_inventory(db_session, initial_quantity=100)
        user = await self._create_test_user(db_session)
        
        inventory_service = InventoryService(db_session)
        
        # Reserve stock for order
        reservation_quantity = 5
        reserved_inventory = await inventory_service.reserve_stock(
            variant_id=inventory.variant_id,
            warehouse_id=inventory.warehouse_id,
            quantity=reservation_quantity,
            order_id=str(uuid4())
        )
        
        assert reserved_inventory.quantity_available == 100  # Available unchanged
        assert reserved_inventory.quantity_reserved == reservation_quantity
        
        # Total available for sale should be reduced
        available_for_sale = await inventory_service.get_available_for_sale(
            inventory.variant_id,
            inventory.warehouse_id
        )
        assert available_for_sale == 100 - reservation_quantity
    
    @pytest.mark.asyncio
    async def test_stock_release_after_order_completion(self, db_session: AsyncSession):
        """Test stock release after order is completed/shipped."""
        # Setup test data with reserved stock
        inventory = await self._create_test_inventory(db_session, initial_quantity=100)
        user = await self._create_test_user(db_session)
        
        inventory_service = InventoryService(db_session)
        
        # Reserve stock
        order_id = str(uuid4())
        reservation_quantity = 5
        await inventory_service.reserve_stock(
            variant_id=inventory.variant_id,
            warehouse_id=inventory.warehouse_id,
            quantity=reservation_quantity,
            order_id=order_id
        )
        
        # Complete order (reduce available and reserved)
        completed_inventory = await inventory_service.complete_order_fulfillment(
            variant_id=inventory.variant_id,
            warehouse_id=inventory.warehouse_id,
            quantity=reservation_quantity,
            order_id=order_id
        )
        
        assert completed_inventory.quantity_available == 100 - reservation_quantity
        assert completed_inventory.quantity_reserved == 0
    
    @pytest.mark.asyncio
    async def test_stock_release_after_order_cancellation(self, db_session: AsyncSession):
        """Test stock release after order cancellation."""
        # Setup test data with reserved stock
        inventory = await self._create_test_inventory(db_session, initial_quantity=100)
        
        inventory_service = InventoryService(db_session)
        
        # Reserve stock
        order_id = str(uuid4())
        reservation_quantity = 5
        await inventory_service.reserve_stock(
            variant_id=inventory.variant_id,
            warehouse_id=inventory.warehouse_id,
            quantity=reservation_quantity,
            order_id=order_id
        )
        
        # Cancel order (release reserved stock)
        cancelled_inventory = await inventory_service.release_reserved_stock(
            variant_id=inventory.variant_id,
            warehouse_id=inventory.warehouse_id,
            quantity=reservation_quantity,
            order_id=order_id,
            reason="Order cancelled"
        )
        
        assert cancelled_inventory.quantity_available == 100  # Back to original
        assert cancelled_inventory.quantity_reserved == 0
    
    @pytest.mark.asyncio
    async def test_low_stock_detection(self, db_session: AsyncSession):
        """Test low stock detection and alerts."""
        # Setup inventory with low stock
        inventory = await self._create_test_inventory(
            db_session,
            initial_quantity=5,
            reorder_point=10
        )
        
        inventory_service = InventoryService(db_session)
        
        # Check if item is low stock
        is_low_stock = await inventory_service.is_low_stock(
            inventory.variant_id,
            inventory.warehouse_id
        )
        
        assert is_low_stock is True
        
        # Get low stock items
        low_stock_items = await inventory_service.get_low_stock_items()
        
        assert len(low_stock_items) >= 1
        low_stock_item = next(
            (item for item in low_stock_items if item.variant_id == inventory.variant_id),
            None
        )
        assert low_stock_item is not None
    
    @pytest.mark.asyncio
    async def test_reorder_suggestions(self, db_session: AsyncSession):
        """Test reorder suggestions based on stock levels."""
        # Setup inventory with low stock
        inventory = await self._create_test_inventory(
            db_session,
            initial_quantity=5,
            reorder_point=10,
            reorder_quantity=50
        )
        
        inventory_service = InventoryService(db_session)
        
        # Get reorder suggestions
        reorder_suggestions = await inventory_service.get_reorder_suggestions()
        
        assert len(reorder_suggestions) >= 1
        suggestion = next(
            (item for item in reorder_suggestions if item.variant_id == inventory.variant_id),
            None
        )
        assert suggestion is not None
        assert suggestion.suggested_quantity == inventory.reorder_quantity
    
    @pytest.mark.asyncio
    async def test_inventory_valuation(self, db_session: AsyncSession):
        """Test inventory valuation calculation."""
        # Setup multiple inventory items
        inventory1 = await self._create_test_inventory(
            db_session,
            initial_quantity=10,
            variant_price=Decimal("50.00")
        )
        
        inventory2 = await self._create_test_inventory(
            db_session,
            initial_quantity=20,
            variant_price=Decimal("75.00"),
            sku="VAL-002"
        )
        
        inventory_service = InventoryService(db_session)
        
        # Calculate total inventory value
        total_value = await inventory_service.calculate_inventory_value()
        
        # Expected: (10 * 50.00) + (20 * 75.00) = 500 + 1500 = 2000
        expected_value = Decimal("2000.00")
        assert total_value == expected_value
        
        # Calculate value for specific warehouse
        warehouse_value = await inventory_service.calculate_inventory_value(
            warehouse_id=inventory1.warehouse_id
        )
        assert warehouse_value <= total_value
    
    @pytest.mark.asyncio
    async def test_stock_movement_history(self, db_session: AsyncSession):
        """Test stock movement history tracking."""
        inventory = await self._create_test_inventory(db_session)
        
        inventory_service = InventoryService(db_session)
        
        # Perform multiple stock adjustments
        await inventory_service.adjust_stock(
            variant_id=inventory.variant_id,
            warehouse_id=inventory.warehouse_id,
            adjustment_type="increase",
            quantity=25,
            reason="Initial stock",
            notes="First adjustment"
        )
        
        await inventory_service.adjust_stock(
            variant_id=inventory.variant_id,
            warehouse_id=inventory.warehouse_id,
            adjustment_type="decrease",
            quantity=10,
            reason="Sale",
            notes="Second adjustment"
        )
        
        await inventory_service.adjust_stock(
            variant_id=inventory.variant_id,
            warehouse_id=inventory.warehouse_id,
            adjustment_type="increase",
            quantity=15,
            reason="Restock",
            notes="Third adjustment"
        )
        
        # Get movement history
        movements = await inventory_service.get_stock_movement_history(
            inventory.variant_id,
            limit=10
        )
        
        assert len(movements) == 3
        
        # Verify movements are in chronological order (newest first)
        assert movements[0].reason == "Restock"
        assert movements[1].reason == "Sale"
        assert movements[2].reason == "Initial stock"
        
        # Verify quantities
        assert movements[0].quantity == 15
        assert movements[1].quantity == 10
        assert movements[2].quantity == 25
    
    @pytest.mark.asyncio
    async def test_bulk_stock_adjustment(self, db_session: AsyncSession):
        """Test bulk stock adjustments."""
        # Setup multiple inventory items
        inventories = []
        for i in range(5):
            inventory = await self._create_test_inventory(
                db_session,
                initial_quantity=50,
                sku=f"BULK-{i:03d}"
            )
            inventories.append(inventory)
        
        inventory_service = InventoryService(db_session)
        
        # Prepare bulk adjustments
        adjustments = [
            {
                "variant_id": inv.variant_id,
                "warehouse_id": inv.warehouse_id,
                "adjustment_type": "increase",
                "quantity": 20,
                "reason": "Bulk restock",
                "notes": f"Bulk adjustment {i}"
            }
            for i, inv in enumerate(inventories)
        ]
        
        # Perform bulk adjustment
        results = await inventory_service.bulk_adjust_stock(adjustments)
        
        assert results["successful"] == 5
        assert results["failed"] == 0
        
        # Verify all inventories were updated
        for inventory in inventories:
            updated_inventory = await inventory_service.get_inventory(
                inventory.variant_id,
                inventory.warehouse_id
            )
            assert updated_inventory.quantity_available == 70  # 50 + 20
    
    @pytest.mark.asyncio
    async def test_inventory_transfer_between_warehouses(self, db_session: AsyncSession):
        """Test inventory transfer between warehouses."""
        # Setup two warehouses
        warehouse1 = await self._create_test_warehouse(db_session, "Warehouse 1")
        warehouse2 = await self._create_test_warehouse(db_session, "Warehouse 2")
        
        # Create variant
        variant = await self._create_test_variant(db_session)
        
        # Create inventory in warehouse 1
        inventory1 = Inventory(
            id=uuid4(),
            variant_id=variant.id,
            warehouse_id=warehouse1.id,
            quantity_available=100,
            quantity_reserved=0
        )
        db_session.add(inventory1)
        
        # Create inventory in warehouse 2 (empty)
        inventory2 = Inventory(
            id=uuid4(),
            variant_id=variant.id,
            warehouse_id=warehouse2.id,
            quantity_available=0,
            quantity_reserved=0
        )
        db_session.add(inventory2)
        await db_session.commit()
        
        inventory_service = InventoryService(db_session)
        
        # Transfer stock from warehouse 1 to warehouse 2
        transfer_quantity = 30
        result = await inventory_service.transfer_stock(
            variant_id=variant.id,
            from_warehouse_id=warehouse1.id,
            to_warehouse_id=warehouse2.id,
            quantity=transfer_quantity,
            reason="Warehouse transfer",
            notes="Unit test transfer"
        )
        
        assert result["success"] is True
        
        # Verify stock was transferred
        updated_inventory1 = await inventory_service.get_inventory(variant.id, warehouse1.id)
        updated_inventory2 = await inventory_service.get_inventory(variant.id, warehouse2.id)
        
        assert updated_inventory1.quantity_available == 70  # 100 - 30
        assert updated_inventory2.quantity_available == 30  # 0 + 30
    
    @pytest.mark.asyncio
    async def test_inventory_cycle_count(self, db_session: AsyncSession):
        """Test inventory cycle counting and discrepancy handling."""
        inventory = await self._create_test_inventory(db_session, initial_quantity=100)
        
        inventory_service = InventoryService(db_session)
        
        # Perform cycle count with discrepancy
        counted_quantity = 95  # 5 items missing
        cycle_count_result = await inventory_service.perform_cycle_count(
            variant_id=inventory.variant_id,
            warehouse_id=inventory.warehouse_id,
            counted_quantity=counted_quantity,
            counter_user_id=str(uuid4()),
            notes="Cycle count - 5 items missing"
        )
        
        assert cycle_count_result["discrepancy"] == -5  # Negative = shortage
        assert cycle_count_result["adjustment_created"] is True
        
        # Verify inventory was adjusted
        updated_inventory = await inventory_service.get_inventory(
            inventory.variant_id,
            inventory.warehouse_id
        )
        assert updated_inventory.quantity_available == counted_quantity
        
        # Verify adjustment record was created
        adjustment = await inventory_service.get_latest_stock_adjustment(inventory.variant_id)
        assert adjustment.adjustment_type == "cycle_count"
        assert adjustment.quantity == 5  # Absolute value of discrepancy
        assert "cycle count" in adjustment.reason.lower()
    
    @pytest.mark.asyncio
    async def test_inventory_aging_analysis(self, db_session: AsyncSession):
        """Test inventory aging analysis."""
        # Setup inventory with different ages
        old_inventory = await self._create_test_inventory(
            db_session,
            initial_quantity=50,
            sku="OLD-001"
        )
        
        # Manually set created_at to simulate old inventory
        old_inventory.created_at = datetime.utcnow() - timedelta(days=90)
        await db_session.commit()
        
        new_inventory = await self._create_test_inventory(
            db_session,
            initial_quantity=30,
            sku="NEW-001"
        )
        
        inventory_service = InventoryService(db_session)
        
        # Get aging analysis
        aging_analysis = await inventory_service.get_inventory_aging_analysis()
        
        assert "age_buckets" in aging_analysis
        assert "total_value_by_age" in aging_analysis
        
        # Should have items in different age buckets
        age_buckets = aging_analysis["age_buckets"]
        assert any(bucket["days_range"] == "0-30" for bucket in age_buckets)
        assert any(bucket["days_range"] == "61-90" for bucket in age_buckets)
    
    async def _create_test_inventory(
        self,
        db_session: AsyncSession,
        initial_quantity: int = 50,
        reorder_point: int = 10,
        reorder_quantity: int = 100,
        variant_price: Decimal = Decimal("99.99"),
        sku: str = "TEST-001"
    ) -> Inventory:
        """Create test inventory with all related data."""
        # Create warehouse
        warehouse = await self._create_test_warehouse(db_session)
        
        # Create variant
        variant = await self._create_test_variant(db_session, variant_price, sku)
        
        # Create inventory
        inventory = Inventory(
            id=uuid4(),
            variant_id=variant.id,
            warehouse_id=warehouse.id,
            quantity_available=initial_quantity,
            quantity_reserved=0,
            reorder_point=reorder_point,
            reorder_quantity=reorder_quantity
        )
        
        db_session.add(inventory)
        await db_session.commit()
        await db_session.refresh(inventory)
        
        return inventory
    
    async def _create_test_warehouse(self, db_session: AsyncSession, name: str = "Test Warehouse") -> WarehouseLocation:
        """Create test warehouse."""
        warehouse = WarehouseLocation(
            id=uuid4(),
            name=name,
            address="123 Test St",
            city="Test City",
            state="TS",
            country="US",
            postal_code="12345",
            is_active=True
        )
        
        db_session.add(warehouse)
        await db_session.commit()
        await db_session.refresh(warehouse)
        
        return warehouse
    
    async def _create_test_variant(
        self,
        db_session: AsyncSession,
        price: Decimal = Decimal("99.99"),
        sku: str = "TEST-001"
    ) -> ProductVariant:
        """Create test product variant."""
        # Create category and product
        category = Category(
            id=uuid4(),
            name="Test Category",
            description="For testing",
            is_active=True
        )
        
        product = Product(
            id=uuid4(),
            name="Test Product",
            description="For testing",
            category_id=category.id,
            brand="Test Brand",
            is_active=True
        )
        
        variant = ProductVariant(
            id=uuid4(),
            product_id=product.id,
            name="Test Variant",
            sku=sku,
            base_price=price,
            weight=Decimal("1.0"),
            is_active=True
        )
        
        db_session.add_all([category, product, variant])
        await db_session.commit()
        await db_session.refresh(variant)
        
        return variant
    
    async def _create_test_user(self, db_session: AsyncSession) -> User:
        """Create test user."""
        user = User(
            id=uuid4(),
            email="inventory@example.com",
            firstname="Inventory",
            lastname="Test",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role="customer",
            verified=True,
            is_active=True
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        return user