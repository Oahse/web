import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.utils.uuid_utils import uuid7
from decimal import Decimal
from datetime import datetime
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

# Mock the problematic imports before importing our service
with patch.dict('sys.modules', {
    'aiokafka': MagicMock(),
    'core.kafka': MagicMock(),
}):
    from services.admin_pricing import AdminPricingService
    from models.pricing_config import PricingConfig
    from core.exceptions import APIException


class TestAdminPricingService:
    """Unit tests for AdminPricingService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()

    @pytest.fixture
    def admin_pricing_service(self, mock_db):
        """AdminPricingService instance with mocked database"""
        return AdminPricingService(mock_db)

    @pytest.fixture
    def sample_pricing_config(self):
        """Sample pricing configuration"""
        return PricingConfig(
            id=uuid7(),
            subscription_percentage=10.0,
            delivery_costs={
                "standard": 10.0,
                "express": 25.0,
                "overnight": 50.0
            },
            tax_rates={
                "US": 0.08,
                "CA": 0.13,
                "UK": 0.20
            },
            currency_settings={
                "default": "USD",
                "supported": ["USD", "EUR", "GBP", "CAD"]
            },
            updated_by=uuid7(),
            version="1.0",
            is_active="active",
            change_reason="Test configuration"
        )

    @pytest.fixture
    def sample_subscription(self):
        """Sample subscription"""
        # Create a simple mock object instead of importing the model
        subscription = MagicMock()
        subscription.id = uuid7()
        subscription.user_id = uuid7()
        subscription.price = Decimal('100.00')
        subscription.billing_cycle = "monthly"
        subscription.status = "active"
        return subscription

    async def test_get_pricing_config_existing(self, admin_pricing_service, mock_db, sample_pricing_config):
        """Test getting existing pricing configuration"""
        # Mock database response
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_pricing_config
        mock_db.execute.return_value = mock_result

        # Call method
        result = await admin_pricing_service.get_pricing_config()

        # Assertions
        assert result == sample_pricing_config
        mock_db.execute.assert_called_once()

    async def test_get_pricing_config_create_default(self, admin_pricing_service, mock_db):
        """Test creating default configuration when none exists"""
        # Mock database response - no existing config
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Mock the _create_default_pricing_config method
        default_config = PricingConfig(
            id=uuid7(),
            subscription_percentage=10.0,
            delivery_costs={"standard": 10.0, "express": 25.0, "overnight": 50.0},
            tax_rates={"US": 0.08, "CA": 0.13, "UK": 0.20},
            currency_settings={"default": "USD", "supported": ["USD", "EUR", "GBP", "CAD"]},
            updated_by=uuid7(),
            version="1.0",
            is_active="active",
            change_reason="Initial default configuration"
        )
        
        admin_pricing_service._create_default_pricing_config = AsyncMock(return_value=default_config)

        # Call method
        result = await admin_pricing_service.get_pricing_config()

        # Assertions
        assert result == default_config
        admin_pricing_service._create_default_pricing_config.assert_called_once()

    async def test_update_subscription_percentage_valid(self, admin_pricing_service, mock_db, sample_pricing_config):
        """Test updating subscription percentage with valid value"""
        admin_user_id = uuid7()
        new_percentage = 15.0

        # Mock get_pricing_config
        admin_pricing_service.get_pricing_config = AsyncMock(return_value=sample_pricing_config)
        
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Mock _log_pricing_change
        admin_pricing_service._log_pricing_change = AsyncMock()

        # Call method
        result = await admin_pricing_service.update_subscription_percentage(
            new_percentage, admin_user_id, "Test update"
        )

        # Assertions
        assert result.subscription_percentage == new_percentage
        assert result.updated_by == admin_user_id
        assert result.change_reason == "Test update"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        admin_pricing_service._log_pricing_change.assert_called_once()

    async def test_update_subscription_percentage_invalid_low(self, admin_pricing_service):
        """Test updating subscription percentage with value too low"""
        admin_user_id = uuid7()
        invalid_percentage = 0.05  # Below 0.1%

        # Call method and expect exception
        with pytest.raises(APIException) as exc_info:
            await admin_pricing_service.update_subscription_percentage(
                invalid_percentage, admin_user_id
            )

        assert exc_info.value.status_code == 400
        assert "between 0.1% and 50%" in exc_info.value.message

    async def test_update_subscription_percentage_invalid_high(self, admin_pricing_service):
        """Test updating subscription percentage with value too high"""
        admin_user_id = uuid7()
        invalid_percentage = 55.0  # Above 50%

        # Call method and expect exception
        with pytest.raises(APIException) as exc_info:
            await admin_pricing_service.update_subscription_percentage(
                invalid_percentage, admin_user_id
            )

        assert exc_info.value.status_code == 400
        assert "between 0.1% and 50%" in exc_info.value.message

    async def test_update_delivery_costs_valid(self, admin_pricing_service, mock_db, sample_pricing_config):
        """Test updating delivery costs with valid values"""
        admin_user_id = uuid7()
        new_delivery_costs = {
            "standard": 12.0,
            "express": 30.0,
            "overnight": 60.0
        }

        # Mock get_pricing_config
        admin_pricing_service.get_pricing_config = AsyncMock(return_value=sample_pricing_config)
        
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Mock _log_pricing_change
        admin_pricing_service._log_pricing_change = AsyncMock()

        # Call method
        result = await admin_pricing_service.update_delivery_costs(
            new_delivery_costs, admin_user_id, "Test delivery update"
        )

        # Assertions
        assert result.delivery_costs == new_delivery_costs
        assert result.updated_by == admin_user_id
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    async def test_update_delivery_costs_missing_required_type(self, admin_pricing_service):
        """Test updating delivery costs with missing required delivery type"""
        admin_user_id = uuid7()
        invalid_delivery_costs = {
            "standard": 12.0,
            "express": 30.0
            # Missing "overnight"
        }

        # Call method and expect exception
        with pytest.raises(APIException) as exc_info:
            await admin_pricing_service.update_delivery_costs(
                invalid_delivery_costs, admin_user_id
            )

        assert exc_info.value.status_code == 400
        assert "Missing required delivery type: overnight" in exc_info.value.message

    async def test_update_delivery_costs_negative_value(self, admin_pricing_service):
        """Test updating delivery costs with negative value"""
        admin_user_id = uuid7()
        invalid_delivery_costs = {
            "standard": -5.0,  # Negative value
            "express": 30.0,
            "overnight": 60.0
        }

        # Call method and expect exception
        with pytest.raises(APIException) as exc_info:
            await admin_pricing_service.update_delivery_costs(
                invalid_delivery_costs, admin_user_id
            )

        assert exc_info.value.status_code == 400
        assert "must be a non-negative number" in exc_info.value.message

    async def test_preview_pricing_impact_basic(self, admin_pricing_service, mock_db, sample_pricing_config, sample_subscription):
        """Test basic pricing impact preview"""
        admin_user_id = uuid7()
        proposed_changes = {"subscription_percentage": 15.0}

        # Mock get_pricing_config
        admin_pricing_service.get_pricing_config = AsyncMock(return_value=sample_pricing_config)
        
        # Mock _get_active_subscriptions
        admin_pricing_service._get_active_subscriptions = AsyncMock(return_value=[sample_subscription])
        
        # Mock cost calculations
        admin_pricing_service._calculate_subscription_cost = AsyncMock(return_value=Decimal('120.00'))
        admin_pricing_service._calculate_subscription_cost_with_config = AsyncMock(return_value=Decimal('126.00'))

        # Call method
        result = await admin_pricing_service.preview_pricing_impact(proposed_changes, admin_user_id)

        # Assertions
        assert result["affected_subscriptions_count"] == 1
        assert result["total_revenue_impact"] == 6.0  # 126 - 120
        assert result["summary"]["increased_cost_count"] == 1
        assert result["summary"]["decreased_cost_count"] == 0
        assert len(result["subscription_impacts"]) == 1

    async def test_preview_pricing_impact_invalid_percentage(self, admin_pricing_service, sample_pricing_config):
        """Test pricing impact preview with invalid percentage"""
        admin_user_id = uuid7()
        proposed_changes = {"subscription_percentage": 55.0}  # Invalid

        # Mock get_pricing_config
        admin_pricing_service.get_pricing_config = AsyncMock(return_value=sample_pricing_config)

        # Call method and expect exception
        with pytest.raises(APIException) as exc_info:
            await admin_pricing_service.preview_pricing_impact(proposed_changes, admin_user_id)

        assert exc_info.value.status_code == 400
        assert "between 0.1% and 50%" in exc_info.value.message

    def test_validate_delivery_costs_valid(self, admin_pricing_service):
        """Test delivery costs validation with valid data"""
        valid_costs = {
            "standard": 10.0,
            "express": 25.0,
            "overnight": 50.0
        }

        # Should not raise exception
        admin_pricing_service._validate_delivery_costs(valid_costs)

    def test_validate_delivery_costs_not_dict(self, admin_pricing_service):
        """Test delivery costs validation with non-dictionary input"""
        invalid_costs = "not a dict"

        with pytest.raises(APIException) as exc_info:
            admin_pricing_service._validate_delivery_costs(invalid_costs)

        assert exc_info.value.status_code == 400
        assert "must be a dictionary" in exc_info.value.message

    def test_increment_version(self, admin_pricing_service):
        """Test version increment functionality"""
        # Test normal increment
        assert admin_pricing_service._increment_version("1.0") == "1.1"
        assert admin_pricing_service._increment_version("2.5") == "2.6"
        
        # Test invalid version format
        assert admin_pricing_service._increment_version("invalid") == "1.1"

    def test_create_proposed_config(self, admin_pricing_service, sample_pricing_config):
        """Test creating proposed configuration from changes"""
        proposed_changes = {
            "subscription_percentage": 15.0,
            "delivery_costs": {
                "standard": 12.0,
                "express": 30.0,
                "overnight": 60.0
            }
        }

        result = admin_pricing_service._create_proposed_config(sample_pricing_config, proposed_changes)

        assert result["subscription_percentage"] == 15.0
        assert result["delivery_costs"]["standard"] == 12.0
        assert result["tax_rates"] == sample_pricing_config.tax_rates  # Unchanged

    def test_create_proposed_config_invalid_percentage(self, admin_pricing_service, sample_pricing_config):
        """Test creating proposed configuration with invalid percentage"""
        proposed_changes = {"subscription_percentage": 55.0}  # Invalid

        with pytest.raises(APIException) as exc_info:
            admin_pricing_service._create_proposed_config(sample_pricing_config, proposed_changes)

        assert exc_info.value.status_code == 400
        assert "between 0.1% and 50%" in exc_info.value.message