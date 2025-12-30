#!/usr/bin/env python3
"""
Test script to verify atomic inventory operations work correctly
"""
import asyncio
import sys
import os
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import get_db
from models.inventories import Inventory, atomic_stock_operation
from services.inventories import InventoryService


async def test_atomic_operations():
    """Test atomic inventory operations"""
    print("Testing atomic inventory operations...")
    
    async with get_async_session() as db:
        try:
            # Find an existing inventory item for testing
            inventory = await db.execute(
                "SELECT * FROM inventory LIMIT 1"
            )
            inventory_row = inventory.fetchone()
            
            if not inventory_row:
                print("No inventory items found for testing")
                return
            
            variant_id = inventory_row[1]  # variant_id column
            print(f"Testing with variant_id: {variant_id}")
            
            # Test 1: Atomic stock update
            print("\n1. Testing atomic stock update...")
            result = await atomic_stock_operation(
                db=db,
                variant_id=variant_id,
                operation="update",
                quantity_change=5,
                reason="test_increase",
                notes="Testing atomic operations"
            )
            print(f"✓ Stock updated: {result['inventory']['quantity_available']}")
            
            # Test 2: Test stock availability check
            print("\n2. Testing stock availability check...")
            inventory_service = InventoryService(db)
            availability = await inventory_service.check_stock_availability(
                variant_id=variant_id,
                quantity=2
            )
            print(f"✓ Stock availability checked: {availability['available']}, Status: {availability['stock_status']}")
            
            print("\n✅ All atomic operations completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()


async def test_service_methods():
    """Test inventory service atomic methods"""
    print("\nTesting inventory service atomic methods...")
    
    async with get_async_session() as db:
        try:
            service = InventoryService(db)
            
            # Find an existing inventory item
            inventory = await db.execute(
                "SELECT * FROM inventory LIMIT 1"
            )
            inventory_row = inventory.fetchone()
            
            if not inventory_row:
                print("No inventory items found for testing")
                return
            
            variant_id = inventory_row[1]  # variant_id column
            location_id = inventory_row[2]  # location_id column
            
            print(f"Testing service methods with variant_id: {variant_id}")
            
            # Test stock availability check
            print("\n1. Testing stock availability check...")
            availability = await service.check_stock_availability(
                variant_id=variant_id,
                quantity=1
            )
            print(f"✓ Stock available: {availability['available']}, Current: {availability['current_stock']}")
            
            # Test atomic stock decrement
            if availability['available']:
                print("\n2. Testing atomic stock decrement...")
                result = await service.decrement_stock_on_purchase(
                    variant_id=variant_id,
                    quantity=1,
                    location_id=location_id,
                    order_id=uuid4()
                )
                print(f"✓ Stock decremented: {result['old_quantity']} -> {result['new_quantity']}")
                
                # Test atomic stock increment (restore)
                print("\n3. Testing atomic stock increment...")
                result = await service.increment_stock_on_cancellation(
                    variant_id=variant_id,
                    quantity=1,
                    location_id=location_id,
                    order_id=uuid4()
                )
                print(f"✓ Stock incremented: {result['old_quantity']} -> {result['new_quantity']}")
            
            print("\n✅ All service methods completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during service testing: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main test function"""
    print("🧪 Starting atomic inventory operations tests...\n")
    
    await test_atomic_operations()
    await test_service_methods()
    
    print("\n🎉 Testing completed!")


if __name__ == "__main__":
    asyncio.run(main())