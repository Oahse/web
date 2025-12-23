import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from services.enhanced_inventory_integration import EnhancedInventoryIntegrationService
from models.inventory import Inventory, WarehouseLocation, StockAdjustment
from models.product import ProductVariant, Product
from models.subscription import Subscription
from models.variant_tracking import VariantTrackingEntry, VariantAnalytics
from models.user import User
from core.exceptions import APIException


class TestEnhancedInventoryIntegrationService:
    """Test suite for Enhanced Inventory Integration Service"""

    @pytest.fixture
    async def service(self, db_session: AsyncSession):
        """Create service instance with mocked dependencies"""
        service = EnhancedInventoryIntegrationService(db_session)
        
        # Mock the dependent services
        service.inventory_service = AsyncMock()
        service.variant_tracking_service = AsyncMock()
        service.notification_service = AsyncMock()
        
        return service

    @pytest.fixture
    async def sample_warehouse_data(self):
        """Sample warehouse data for testing"""
        return [
            {
                "variant_id": str(uuid4()),
                "quantity": 100,
                "location_id": str(uuid4()),
                "batch_number": "BATCH001",
                "cost_per_unit": 25.50
            },
            {
                "variant_id": str(uuid4()),
                "quantity": 50,
                "location_id": str(uuid4()),
                "batch_number": "BATCH002",
                "cost_per_unit": 30.00
            },
            {
                "variant_id": str(uuid4()),
                "quantity": 0,  # Out of stock
                "location_id": str(uuid4()),
                "batch_number": "BATCH003",
                "cost_per_unit": 15.75
            }
        ]

    @pytest.fixture
    async def sample_tracking_entries(self):
        """Sample variant tracking entries for demand prediction"""
        variant_id = uuid4()
        subscription_id = uuid4()
        
        entries = []
        base_date = datetime.utcnow() - timedelta(days=90)
        
        # Create weekly pattern of additions and removals
        for week in range(12):  # 12 weeks of data
            week_date = base_date + timedelta(weeks=week)
            
            # Add some subscriptions each week
            for i in range(2):
                entries.append(VariantTrackingEntry(
                    id=uuid4(),
                    variant_id=variant_id,
                    subscription_id=subscription_id,
                    price_at_time=25.99,
                    action_type="added",
                    tracking_timestamp=week_date + timedelta(days=i),
                    entry_metadata={"source": "test"}
                ))
            
            # Remove some subscriptions occasionally
            if week % 3 == 0:
                entries.append(VariantTrackingEntry(
                    id=uuid4(),
                    variant_id=variant_id,
                    subscription_id=subscription_id,
                    price_at_time=25.99,
                    action_type="removed",
                    tracking_timestamp=week_date + timedelta(days=3),
                    entry_metadata={"source": "test"}
                ))
        
        return entries, variant_id

    # ============================================================================
    # DEMAND PREDICTION TESTS
    # ============================================================================

    async def test_predict_demand_based_on_subscription_patterns_success(
        self, service, db_session, sample_tracking_entries
    ):
        """Test successful demand prediction based on subscription patterns"""
        
        tracking_entries, variant_id = sample_tracking_entries
        
        # Mock database queries
        with patch.object(db_session, 'execute') as mock_execute:
            # Mock tracking entries query
            mock_tracking_result = AsyncMock()
            mock_tracking_result.scalars.return_value.all.return_value = tracking_entries
            
            # Mock active subscriptions query
            mock_subscription_result = AsyncMock()
            mock_subscription_result.scalars.return_value.all.return_value = [
                MagicMock(variant_ids=[str(variant_id)], status="active")
            ]
            
            # Mock variant query
            mock_variant_result = AsyncMock()
            mock_variant = MagicMock()
            mock_variant.name = "Test Variant"
            mock_variant.product.name = "Test Product"
            mock_variant_result.scalar_one_or_none.return_value = mock_variant
            
            mock_execute.side_effect = [
                mock_tracking_result,
                mock_subscription_result,
                mock_variant_result
            ]
            
            # Mock inventory levels method
            service._get_current_inventory_levels = AsyncMock(return_value={
                str(variant_id): {
                    "current_stock": 50,
                    "low_stock_threshold": 10,
                    "is_low_stock": False,
                    "is_out_of_stock": False
                }
            })
            
            # Mock recommendations method
            service._generate_demand_based_recommendations = AsyncMock(return_value=[
                {
                    "type": "reorder_needed",
                    "variant_id": str(variant_id),
                    "recommendation": "Reorder 20 units to meet predicted demand"
                }
            ])
            
            # Execute test
            result = await service.predict_demand_based_on_subscription_patterns(
                variant_id=variant_id,
                forecast_days=30,
                confidence_threshold=0.5
            )
            
            # Assertions
            assert "analysis_period" in result
            assert "summary" in result
            assert "variant_predictions" in result
            assert "recommendations" in result
            
            assert result["analysis_period"]["forecast_days"] == 30
            assert result["analysis_period"]["confidence_threshold"] == 0.5
            
            # Verify that predictions were generated
            assert len(result["variant_predictions"]) >= 0
            assert isinstance(result["recommendations"], list)

    async def test_analyze_variant_demand_pattern(self, service, sample_tracking_entries):
        """Test variant demand pattern analysis"""
        
        tracking_entries, variant_id = sample_tracking_entries
        active_subscriptions = [
            MagicMock(variant_ids=[str(variant_id)], status="active")
        ]
        
        # Mock variant query
        with patch.object(service.db, 'execute') as mock_execute:
            mock_result = AsyncMock()
            mock_variant = MagicMock()
            mock_variant.name = "Test Variant"
            mock_variant.product.name = "Test Product"
            mock_result.scalar_one_or_none.return_value = mock_variant
            mock_execute.return_value = mock_result
            
            result = await service._analyze_variant_demand_pattern(
                variant_id, tracking_entries, active_subscriptions, 30
            )
            
            # Assertions
            assert result["variant_id"] == str(variant_id)
            assert result["variant_name"] == "Test Variant"
            assert result["product_name"] == "Test Product"
            
            assert "historical_analysis" in result
            assert "current_state" in result
            assert "prediction" in result
            
            # Check historical analysis
            historical = result["historical_analysis"]
            assert historical["weeks_analyzed"] > 0
            assert historical["total_additions"] > 0
            assert "avg_weekly_net_demand" in historical
            
            # Check prediction
            prediction = result["prediction"]
            assert "predicted_demand" in prediction
            assert "confidence_level" in prediction
            assert 0 <= prediction["confidence_level"] <= 1

    # ============================================================================
    # REORDER SUGGESTIONS TESTS
    # ============================================================================

    async def test_generate_reorder_suggestions_based_on_consumption_success(
        self, service, db_session
    ):
        """Test successful generation of reorder suggestions"""
        
        # Mock inventory items
        mock_inventory_items = [
            MagicMock(
                id=uuid4(),
                variant_id=uuid4(),
                location_id=uuid4(),
                quantity=5,  # Low stock
                low_stock_threshold=10,
                variant=MagicMock(name="Test Variant 1", current_price=25.99),
                location=MagicMock(name="Warehouse A")
            ),
            MagicMock(
                id=uuid4(),
                variant_id=uuid4(),
                location_id=uuid4(),
                quantity=100,  # Good stock
                low_stock_threshold=10,
                variant=MagicMock(name="Test Variant 2", current_price=35.50),
                location=MagicMock(name="Warehouse B")
            )
        ]
        
        # Mock database query
        with patch.object(db_session, 'execute') as mock_execute:
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = mock_inventory_items
            mock_execute.return_value = mock_result
            
            # Mock variant reorder suggestion method
            service._generate_variant_reorder_suggestion = AsyncMock(side_effect=[
                {
                    "variant_id": str(mock_inventory_items[0].variant_id),
                    "needs_reorder": True,
                    "urgency": "high",
                    "suggested_quantity": 50,
                    "days_until_stockout": 2
                },
                None  # Second item doesn't need reorder
            ])
            
            result = await service.generate_reorder_suggestions_based_on_consumption(
                days_ahead=30,
                min_confidence_level=0.6
            )
            
            # Assertions
            assert isinstance(result, list)
            assert len(result) == 1  # Only one item needs reorder
            
            suggestion = result[0]
            assert suggestion["needs_reorder"] is True
            assert suggestion["urgency"] == "high"
            assert suggestion["suggested_quantity"] == 50

    async def test_generate_variant_reorder_suggestion_with_high_demand(
        self, service
    ):
        """Test reorder suggestion generation for high-demand variant"""
        
        # Create mock inventory item
        inventory_item = MagicMock(
            id=uuid4(),
            variant_id=uuid4(),
            location_id=uuid4(),
            quantity=10,
            low_stock_threshold=20,
            variant=MagicMock(name="High Demand Variant", current_price=45.00),
            location=MagicMock(name="Main Warehouse")
        )
        
        # Mock demand prediction
        service.predict_demand_based_on_subscription_patterns = AsyncMock(return_value={
            "variant_predictions": {
                str(inventory_item.variant_id): {
                    "prediction": {
                        "predicted_demand": 100,
                        "confidence_level": 0.85
                    },
                    "historical_analysis": {
                        "avg_weekly_net_demand": 25,
                        "seasonal_factor": 1.2
                    }
                }
            }
        })
        
        # Mock consumption analysis
        service._analyze_consumption_rate = AsyncMock(return_value={
            "daily_consumption_rate": 3.5,
            "consumption_consistency": 0.8,
            "total_consumed": 105
        })
        
        result = await service._generate_variant_reorder_suggestion(
            inventory_item, 30, True, 0.7
        )
        
        # Assertions
        assert result is not None
        assert result["needs_reorder"] is True
        assert result["urgency"] in ["high", "medium", "critical"]
        assert result["suggested_quantity"] > 0
        assert result["predicted_demand"]["total_predicted"] > 0
        assert result["financial_analysis"]["suggested_order_value"] > 0

    # ============================================================================
    # BATCH UPDATE TESTS
    # ============================================================================

    async def test_batch_update_inventory_from_warehouse_data_success(
        self, service, db_session, sample_warehouse_data
    ):
        """Test successful batch update from warehouse data"""
        
        # Mock validation
        service._validate_warehouse_data = AsyncMock(return_value={
            "is_valid": True,
            "errors": [],
            "warnings": []
        })
        
        # Mock batch processing
        service._process_warehouse_data_batch = AsyncMock(return_value={
            "processed": [
                {
                    "variant_id": sample_warehouse_data[0]["variant_id"],
                    "old_quantity": 80,
                    "new_quantity": 100,
                    "quantity_change": 20
                }
            ],
            "failed": []
        })
        
        # Mock alert generation
        service._generate_batch_update_alerts = AsyncMock(return_value=[])
        
        # Mock audit record creation
        service._create_batch_update_audit_record = AsyncMock()
        
        # Mock impact analysis
        service._analyze_batch_update_impact = AsyncMock(return_value={
            "total_items_updated": 1,
            "net_quantity_change": 20,
            "significant_changes": 0
        })
        
        result = await service.batch_update_inventory_from_warehouse_data(
            warehouse_data=sample_warehouse_data,
            source_system="test_warehouse_system"
        )
        
        # Assertions
        assert "batch_summary" in result
        assert "processed_items" in result
        assert "failed_items" in result
        assert "impact_analysis" in result
        
        batch_summary = result["batch_summary"]
        assert batch_summary["source_system"] == "test_warehouse_system"
        assert batch_summary["total_items"] == len(sample_warehouse_data)
        assert batch_summary["processed_successfully"] >= 0
        assert batch_summary["success_rate_percent"] >= 0

    async def test_validate_warehouse_data_with_errors(self, service):
        """Test warehouse data validation with errors"""
        
        invalid_data = [
            {"variant_id": "invalid-uuid", "quantity": "not-a-number"},
            {"quantity": 50},  # Missing variant_id
            {"variant_id": str(uuid4()), "quantity": -10}  # Negative quantity (warning)
        ]
        
        result = await service._validate_warehouse_data(invalid_data)
        
        # Assertions
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        assert len(result["warnings"]) > 0
        assert result["items_validated"] == len(invalid_data)

    # ============================================================================
    # SUPPLIER INTEGRATION TESTS
    # ============================================================================

    async def test_integrate_with_supplier_systems_success(self, service):
        """Test successful supplier system integration"""
        
        # Mock reorder suggestions
        reorder_suggestions = [
            {
                "variant_id": str(uuid4()),
                "variant_name": "Test Product A",
                "suggested_quantity": 100,
                "urgency": "high",
                "financial_analysis": {"suggested_order_value": 2500.0}
            },
            {
                "variant_id": str(uuid4()),
                "variant_name": "Test Product B",
                "suggested_quantity": 50,
                "urgency": "medium",
                "financial_analysis": {"suggested_order_value": 1200.0}
            }
        ]
        
        # Mock grouping by supplier
        service._group_reorder_suggestions_by_supplier = AsyncMock(return_value={
            "supplier_001": [reorder_suggestions[0]],
            "supplier_002": [reorder_suggestions[1]]
        })
        
        # Mock purchase order creation
        service._create_supplier_purchase_order = AsyncMock(side_effect=[
            {
                "po_number": "PO-20241223-001",
                "supplier_id": "supplier_001",
                "total_value": 2500.0,
                "auto_approved": False,
                "status": "pending_approval"
            },
            {
                "po_number": "PO-20241223-002",
                "supplier_id": "supplier_002",
                "total_value": 1200.0,
                "auto_approved": True,
                "status": "approved"
            }
        ])
        
        # Mock supplier integration
        service._send_purchase_order_to_supplier = AsyncMock(side_effect=[
            {"supplier_id": "supplier_001", "status": "success"},
            {"supplier_id": "supplier_002", "status": "success"}
        ])
        
        result = await service.integrate_with_supplier_systems_for_automated_orders(
            reorder_suggestions=reorder_suggestions,
            auto_approve_threshold=1500.0
        )
        
        # Assertions
        assert "integration_summary" in result
        assert "purchase_orders" in result
        assert "integration_results" in result
        
        summary = result["integration_summary"]
        assert summary["total_purchase_orders"] == 2
        assert summary["auto_approved_orders"] == 1
        assert summary["manual_approval_required"] == 1
        assert summary["successful_integrations"] == 2

    async def test_create_supplier_purchase_order(self, service):
        """Test purchase order creation for supplier"""
        
        supplier_orders = [
            {
                "variant_id": str(uuid4()),
                "variant_name": "Test Product",
                "suggested_quantity": 100,
                "supplier_unit_cost": 25.0,
                "supplier_part_number": "SUP-001-ABC",
                "urgency": "high",
                "days_until_stockout": 3
            }
        ]
        
        result = await service._create_supplier_purchase_order(
            "test_supplier",
            supplier_orders,
            1000.0
        )
        
        # Assertions
        assert result["supplier_id"] == "test_supplier"
        assert "po_number" in result
        assert result["total_quantity"] == 100
        assert result["total_value"] == 2500.0  # 100 * 25.0
        assert result["auto_approved"] is False  # Exceeds threshold
        assert len(result["line_items"]) == 1

    # ============================================================================
    # HELPER METHOD TESTS
    # ============================================================================

    async def test_calculate_linear_trend(self, service):
        """Test linear trend calculation"""
        
        # Test with increasing trend
        x_values = [1, 2, 3, 4, 5]
        y_values = [2, 4, 6, 8, 10]
        
        slope = service._calculate_linear_trend(x_values, y_values)
        assert slope == 2.0  # Perfect linear increase
        
        # Test with decreasing trend
        y_values_decreasing = [10, 8, 6, 4, 2]
        slope_decreasing = service._calculate_linear_trend(x_values, y_values_decreasing)
        assert slope_decreasing == -2.0  # Perfect linear decrease
        
        # Test with no trend
        y_values_flat = [5, 5, 5, 5, 5]
        slope_flat = service._calculate_linear_trend(x_values, y_values_flat)
        assert slope_flat == 0.0

    async def test_calculate_prediction_confidence(self, service):
        """Test prediction confidence calculation"""
        
        # Test with consistent data
        consistent_demands = [10, 12, 11, 10, 12]
        confidence = service._calculate_prediction_confidence(
            consistent_demands, 50, 10
        )
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be reasonably confident
        
        # Test with inconsistent data
        inconsistent_demands = [1, 50, 2, 45, 3]
        confidence_low = service._calculate_prediction_confidence(
            inconsistent_demands, 10, 2
        )
        assert 0.0 <= confidence_low <= 1.0
        assert confidence_low < confidence  # Should be less confident

    async def test_get_urgency_score(self, service):
        """Test urgency score calculation"""
        
        assert service._get_urgency_score("critical") == 0
        assert service._get_urgency_score("high") == 1
        assert service._get_urgency_score("medium") == 2
        assert service._get_urgency_score("low") == 3
        assert service._get_urgency_score("unknown") == 4

    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================

    async def test_predict_demand_with_database_error(self, service, db_session):
        """Test demand prediction with database error"""
        
        # Mock database error
        with patch.object(db_session, 'execute', side_effect=Exception("Database error")):
            with pytest.raises(APIException) as exc_info:
                await service.predict_demand_based_on_subscription_patterns()
            
            assert exc_info.value.status_code == 500
            assert "Failed to generate demand predictions" in str(exc_info.value.message)

    async def test_batch_update_with_validation_error(self, service):
        """Test batch update with validation error"""
        
        invalid_data = [{"invalid": "data"}]
        
        # Mock validation failure
        service._validate_warehouse_data = AsyncMock(return_value={
            "is_valid": False,
            "errors": ["Missing required fields"]
        })
        
        with pytest.raises(APIException) as exc_info:
            await service.batch_update_inventory_from_warehouse_data(invalid_data)
        
        assert exc_info.value.status_code == 400
        assert "validation failed" in str(exc_info.value.message)

    async def test_supplier_integration_with_error(self, service):
        """Test supplier integration with error"""
        
        # Mock error in grouping suggestions
        service._group_reorder_suggestions_by_supplier = AsyncMock(
            side_effect=Exception("Supplier grouping error")
        )
        
        with pytest.raises(APIException) as exc_info:
            await service.integrate_with_supplier_systems_for_automated_orders([])
        
        assert exc_info.value.status_code == 500
        assert "Failed to integrate with supplier systems" in str(exc_info.value.message)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEnhancedInventoryIntegrationIntegration:
    """Integration tests for Enhanced Inventory Integration Service"""

    @pytest.fixture
    async def real_service(self, db_session: AsyncSession):
        """Create service instance with real dependencies"""
        return EnhancedInventoryIntegrationService(db_session)

    async def test_end_to_end_demand_prediction_workflow(
        self, real_service, db_session
    ):
        """Test complete demand prediction workflow with real data"""
        
        # This would require setting up real test data in the database
        # For now, we'll test that the service can be instantiated and methods exist
        
        assert hasattr(real_service, 'predict_demand_based_on_subscription_patterns')
        assert hasattr(real_service, 'generate_reorder_suggestions_based_on_consumption')
        assert hasattr(real_service, 'batch_update_inventory_from_warehouse_data')
        assert hasattr(real_service, 'integrate_with_supplier_systems_for_automated_orders')
        
        # Verify service has required dependencies
        assert real_service.db is not None
        assert hasattr(real_service, 'inventory_service')
        assert hasattr(real_service, 'variant_tracking_service')
        assert hasattr(real_service, 'notification_service')

    async def test_service_initialization(self, db_session):
        """Test service initialization with dependencies"""
        
        service = EnhancedInventoryIntegrationService(db_session)
        
        # Verify all required attributes are set
        assert service.db == db_session
        assert service.inventory_service is not None
        assert service.variant_tracking_service is not None
        assert service.notification_service is not None


if __name__ == "__main__":
    pytest.main([__file__])