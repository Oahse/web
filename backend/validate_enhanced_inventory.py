#!/usr/bin/env python3
"""
Simple validation script for Enhanced Inventory Integration Service
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def validate_service():
    """Validate the Enhanced Inventory Integration Service"""
    
    try:
        # Import the service class directly
        from services.enhanced_inventory_integration import EnhancedInventoryIntegrationService
        
        print("✓ Enhanced Inventory Integration Service imported successfully")
        
        # Check that all required methods exist
        required_methods = [
            'predict_demand_based_on_subscription_patterns',
            'generate_reorder_suggestions_based_on_consumption', 
            'batch_update_inventory_from_warehouse_data',
            'integrate_with_supplier_systems_for_automated_orders'
        ]
        
        for method_name in required_methods:
            if hasattr(EnhancedInventoryIntegrationService, method_name):
                print(f"✓ Method {method_name} exists")
            else:
                print(f"✗ Method {method_name} missing")
                return False
        
        # Test helper methods
        helper_methods = [
            '_analyze_variant_demand_pattern',
            '_generate_variant_reorder_suggestion',
            '_validate_warehouse_data',
            '_create_supplier_purchase_order'
        ]
        
        for method_name in helper_methods:
            if hasattr(EnhancedInventoryIntegrationService, method_name):
                print(f"✓ Helper method {method_name} exists")
            else:
                print(f"✗ Helper method {method_name} missing")
                return False
        
        # Test mathematical helper methods
        math_methods = [
            '_calculate_linear_trend',
            '_calculate_seasonal_factor',
            '_calculate_prediction_confidence'
        ]
        
        for method_name in math_methods:
            if hasattr(EnhancedInventoryIntegrationService, method_name):
                print(f"✓ Math method {method_name} exists")
            else:
                print(f"✗ Math method {method_name} missing")
                return False
        
        # Test some mathematical functions without database
        print("\n--- Testing Mathematical Functions ---")
        
        # Create a mock service instance for testing math functions
        class MockDB:
            pass
        
        service = EnhancedInventoryIntegrationService(MockDB())
        
        # Test linear trend calculation
        x_values = [1, 2, 3, 4, 5]
        y_values = [2, 4, 6, 8, 10]
        slope = service._calculate_linear_trend(x_values, y_values)
        
        if slope == 2.0:
            print("✓ Linear trend calculation works correctly")
        else:
            print(f"✗ Linear trend calculation failed: expected 2.0, got {slope}")
            return False
        
        # Test seasonal factor calculation
        weekly_demands = [10, 12, 8, 15, 11, 9, 13, 14, 10, 16, 12, 11]
        seasonal_factor = service._calculate_seasonal_factor(weekly_demands)
        
        if 0.5 <= seasonal_factor <= 2.0:
            print(f"✓ Seasonal factor calculation works: {seasonal_factor}")
        else:
            print(f"✗ Seasonal factor out of bounds: {seasonal_factor}")
            return False
        
        # Test prediction confidence calculation
        consistent_demands = [10, 12, 11, 10, 12]
        confidence = service._calculate_prediction_confidence(consistent_demands, 50, 10)
        
        if 0.0 <= confidence <= 1.0:
            print(f"✓ Prediction confidence calculation works: {confidence}")
        else:
            print(f"✗ Prediction confidence out of bounds: {confidence}")
            return False
        
        # Test urgency scoring
        urgency_scores = {
            "critical": service._get_urgency_score("critical"),
            "high": service._get_urgency_score("high"),
            "medium": service._get_urgency_score("medium"),
            "low": service._get_urgency_score("low")
        }
        
        expected_scores = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        
        if urgency_scores == expected_scores:
            print("✓ Urgency scoring works correctly")
        else:
            print(f"✗ Urgency scoring failed: {urgency_scores}")
            return False
        
        print("\n--- Testing Data Validation ---")
        
        # Test warehouse data validation
        valid_data = [
            {
                "variant_id": str(uuid4()),
                "quantity": 100,
                "location_id": str(uuid4())
            }
        ]
        
        validation_result = await service._validate_warehouse_data(valid_data)
        
        if validation_result["is_valid"]:
            print("✓ Warehouse data validation works for valid data")
        else:
            print(f"✗ Warehouse data validation failed for valid data: {validation_result}")
            return False
        
        # Test with invalid data
        invalid_data = [
            {
                "variant_id": "invalid-uuid",
                "quantity": "not-a-number"
            }
        ]
        
        validation_result = await service._validate_warehouse_data(invalid_data)
        
        if not validation_result["is_valid"] and len(validation_result["errors"]) > 0:
            print("✓ Warehouse data validation correctly identifies invalid data")
        else:
            print(f"✗ Warehouse data validation failed to identify invalid data: {validation_result}")
            return False
        
        print("\n--- All Validations Passed! ---")
        print("Enhanced Inventory Integration Service is properly implemented")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(validate_service())
    sys.exit(0 if success else 1)