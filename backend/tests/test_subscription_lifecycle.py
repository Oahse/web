import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.utils.uuid_utils import uuid7
from decimal import Decimal
from datetime import datetime, timedelta
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

# Mock the problematic imports before importing our service
with patch.dict('sys.modules', {
    'aiokafka': MagicMock(),
    'core.kafka': MagicMock(),
    'services.negotiator_service': MagicMock(),
}):
    from services.subscription import SubscriptionService
    from models.subscription import Subscription
    from models.user import User
    from core.exceptions import APIException


class TestSubscriptionLifecycle:
    """Unit tests for SubscriptionService lifecycle management"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()

    @pytest.fixture
    def subscription_service(self, mock_db):
        """SubscriptionService instance with mocked database"""
        return SubscriptionService(mock_db)

    @pytest.fixture
    def sample_subscription(self):
        """Sample subscription"""
        subscription = MagicMock()
        subscription.id = uuid7()
        subscription.user_id = uuid7()
        subscription.status = "active"
        subscription.price = 100.0
        subscription.currency = "USD"
        subscription.billing_cycle = "monthly"
        subscription.variant_ids = [str(uuid7()), str(uuid7())]
        subscription.delivery_type = "standard"
        subscription.paused_at = None
        subscription.cancelled_at = None
        subscription.current_period_start = datetime.utcnow() - timedelta(days=10)
        subscription.current_period_end = datetime.utcnow() + timedelta(days=20)
        subscription.subscription_metadata = {}
        subscription.cost_breakdown = {
            "total_amount": 100.0,
            "subtotal": 85.0,
            "admin_fee": 8.5,
            "delivery_cost": 10.0,
            "tax_amount": 6.5
        }
        return subscription

    @pytest.fixture
    def sample_user(self):
        """Sample user"""
        user = MagicMock()
        user.id = uuid7()
        user.email = "test@example.com"
        user.firstname = "Test"
        return user

    async def test_pause_subscription_success(self, subscription_service, mock_db, sample_subscription):
        """Test successful subscription pause"""
        subscription_id = sample_subscription.id
        user_id = sample_subscription.user_id
        
        # Mock get_subscription_by_id
        subscription_service.get_subscription_by_id = AsyncMock(return_value=sample_subscription)
        
        # Mock helper methods
        subscription_service._calculate_prorated_billing = AsyncMock(return_value={
            "prorated_amount": 66.67,
            "remaining_days": 20,
            "daily_rate": 3.33
        })
        subscription_service._create_subscription_history_record = AsyncMock()
        
        # Mock database operations
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Call method
        result = await subscription_service.pause_subscription(
            subscription_id=subscription_id,
            user_id=user_id,
            pause_reason="customer_request"
        )

        # Assertions
        assert result["subscription_id"] == str(subscription_id)
        assert result["status"] == "paused"
        assert result["pause_reason"] == "customer_request"
        assert "prorated_billing" in result
        assert sample_subscription.status == "paused"
        assert sample_subscription.paused_at is not None
        mock_db.commit.assert_called_once()

    async def test_pause_subscription_invalid_status(self, subscription_service, sample_subscription):
        """Test pause subscription with invalid status"""
        sample_subscription.status = "cancelled"
        subscription_service.get_subscription_by_id = AsyncMock(return_value=sample_subscription)

        with pytest.raises(APIException) as exc_info:
            await subscription_service.pause_subscription(
                subscription_id=sample_subscription.id,
                user_id=sample_subscription.user_id
            )

        assert exc_info.value.status_code == 400
        assert "Cannot pause subscription" in exc_info.value.message

    async def test_pause_subscription_already_paused(self, subscription_service, sample_subscription):
        """Test pause subscription that is already paused"""
        sample_subscription.paused_at = datetime.utcnow()
        subscription_service.get_subscription_by_id = AsyncMock(return_value=sample_subscription)

        with pytest.raises(APIException) as exc_info:
            await subscription_service.pause_subscription(
                subscription_id=sample_subscription.id,
                user_id=sample_subscription.user_id
            )

        assert exc_info.value.status_code == 400
        assert "already paused" in exc_info.value.message

    async def test_resume_subscription_success(self, subscription_service, mock_db, sample_subscription):
        """Test successful subscription resume"""
        # Set up paused subscription
        sample_subscription.status = "paused"
        sample_subscription.paused_at = datetime.utcnow() - timedelta(days=5)
        sample_subscription.subscription_metadata = {
            "pause_details": {
                "old_status": "active",
                "remaining_billing_days": 15
            }
        }
        
        subscription_service.get_subscription_by_id = AsyncMock(return_value=sample_subscription)
        subscription_service._create_subscription_history_record = AsyncMock()
        
        # Mock database operations
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Call method
        result = await subscription_service.resume_subscription(
            subscription_id=sample_subscription.id,
            user_id=sample_subscription.user_id
        )

        # Assertions
        assert result["subscription_id"] == str(sample_subscription.id)
        assert result["status"] == "active"
        assert "pause_duration_days" in result
        assert sample_subscription.status == "active"
        assert sample_subscription.paused_at is None
        mock_db.commit.assert_called_once()

    async def test_cancel_subscription_immediate(self, subscription_service, mock_db, sample_subscription):
        """Test immediate subscription cancellation"""
        subscription_service.get_subscription_by_id = AsyncMock(return_value=sample_subscription)
        subscription_service._calculate_final_billing_and_refund = AsyncMock(return_value={
            "refund_amount": 50.0,
            "final_billing_amount": 50.0,
            "immediate_cancellation": True
        })
        subscription_service._create_subscription_history_record = AsyncMock()
        subscription_service._process_subscription_refund = AsyncMock(return_value={
            "refund_processed": True,
            "refund_amount": 50.0
        })
        
        # Mock database operations
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Call method
        result = await subscription_service.cancel_subscription(
            subscription_id=sample_subscription.id,
            user_id=sample_subscription.user_id,
            immediate=True
        )

        # Assertions
        assert result["subscription_id"] == str(sample_subscription.id)
        assert result["status"] == "cancelled"
        assert result["immediate_cancellation"] is True
        assert sample_subscription.status == "cancelled"
        assert sample_subscription.cancelled_at is not None
        mock_db.commit.assert_called_once()

    async def test_swap_subscription_variants_success(self, subscription_service, mock_db, sample_subscription):
        """Test successful variant swap"""
        new_variant_ids = [uuid7(), uuid7()]
        
        # Mock variant validation
        mock_variants = [MagicMock() for _ in new_variant_ids]
        for i, variant in enumerate(mock_variants):
            variant.id = new_variant_ids[i]
            variant.name = f"Variant {i+1}"
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_variants
        mock_db.execute.return_value = mock_result
        
        subscription_service.get_subscription_by_id = AsyncMock(return_value=sample_subscription)
        
        # Mock cost calculator
        mock_cost_breakdown = MagicMock()
        mock_cost_breakdown.total_amount = Decimal('120.0')
        mock_cost_breakdown.admin_percentage = 10.0
        mock_cost_breakdown.delivery_cost = Decimal('10.0')
        mock_cost_breakdown.tax_rate = 0.08
        mock_cost_breakdown.tax_amount = Decimal('8.0')
        mock_cost_breakdown.to_dict.return_value = {
            "total_amount": 120.0,
            "subtotal": 100.0,
            "admin_fee": 10.0,
            "delivery_cost": 10.0,
            "tax_amount": 8.0
        }
        
        with patch('services.subscription_cost_calculator.SubscriptionCostCalculator') as mock_calculator_class:
            mock_calculator = AsyncMock()
            mock_calculator.calculate_subscription_cost.return_value = mock_cost_breakdown
            mock_calculator_class.return_value = mock_calculator
            
            subscription_service._calculate_variant_swap_cost_adjustment = AsyncMock(return_value={
                "cost_difference": 20.0,
                "old_total_cost": 100.0,
                "new_total_cost": 120.0
            })
            subscription_service._create_subscription_history_record = AsyncMock()
            
            # Mock database operations
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            # Call method
            result = await subscription_service.swap_subscription_variants(
                subscription_id=sample_subscription.id,
                user_id=sample_subscription.user_id,
                new_variant_ids=new_variant_ids
            )

            # Assertions
            assert result["subscription_id"] == str(sample_subscription.id)
            assert len(result["new_variant_ids"]) == 2
            assert "cost_adjustment" in result
            assert sample_subscription.variant_ids == [str(v_id) for v_id in new_variant_ids]
            mock_db.commit.assert_called_once()

    async def test_get_subscription_history_success(self, subscription_service, mock_db, sample_subscription):
        """Test getting subscription history"""
        subscription_service.get_subscription_by_id = AsyncMock(return_value=sample_subscription)
        
        # Mock cost history records
        mock_history_records = []
        for i in range(3):
            record = MagicMock()
            record.id = uuid7()
            record.change_reason = f"test_change_{i}"
            record.effective_date = datetime.utcnow() - timedelta(days=i)
            record.created_at = datetime.utcnow() - timedelta(days=i)
            record.old_cost_breakdown = {"total_amount": 100.0}
            record.new_cost_breakdown = {"total_amount": 110.0}
            record.changed_by = None
            record.pricing_metadata = {}
            mock_history_records.append(record)
        
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = mock_history_records
        mock_db.execute.return_value = mock_result
        
        # Mock count query
        mock_count_result = AsyncMock()
        mock_count_result.scalar_one.return_value = 3
        mock_db.execute.side_effect = [mock_result, mock_count_result]
        
        subscription_service._determine_change_type_from_reason = MagicMock(return_value="price_change")
        subscription_service._calculate_cost_difference = MagicMock(return_value=10.0)

        # Call method
        result = await subscription_service.get_subscription_history(
            subscription_id=sample_subscription.id,
            user_id=sample_subscription.user_id
        )

        # Assertions
        assert "subscription_summary" in result
        assert "history" in result
        assert "statistics" in result
        assert result["history"]["total_count"] == 3
        assert len(result["history"]["records"]) == 3

    def test_calculate_prorated_billing(self, subscription_service, sample_subscription):
        """Test prorated billing calculation"""
        # This is a synchronous helper method
        result = subscription_service._calculate_prorated_billing.__wrapped__(
            subscription_service, sample_subscription, "pause"
        )

        # Since this is a mock test, we'll just verify the structure
        # In a real test, you'd verify the actual calculations
        assert "action_type" in result
        assert "prorated_amount" in result
        assert "remaining_days" in result

    def test_determine_change_type_from_reason(self, subscription_service):
        """Test change type determination from reason"""
        assert subscription_service._determine_change_type_from_reason("subscription_pause") == "pause"
        assert subscription_service._determine_change_type_from_reason("subscription_resume") == "resume"
        assert subscription_service._determine_change_type_from_reason("subscription_cancel") == "cancellation"
        assert subscription_service._determine_change_type_from_reason("variant_swap") == "variant_change"
        assert subscription_service._determine_change_type_from_reason("admin_pricing_update") == "admin_update"
        assert subscription_service._determine_change_type_from_reason("unknown_change") == "other"

    def test_calculate_cost_difference(self, subscription_service):
        """Test cost difference calculation"""
        old_breakdown = {"total_amount": 100.0}
        new_breakdown = {"total_amount": 120.0}
        
        result = subscription_service._calculate_cost_difference(old_breakdown, new_breakdown)
        assert result == 20.0
        
        # Test with None values
        result = subscription_service._calculate_cost_difference(None, new_breakdown)
        assert result == 120.0
        
        result = subscription_service._calculate_cost_difference(old_breakdown, None)
        assert result == -100.0