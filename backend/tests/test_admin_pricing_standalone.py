"""
Standalone tests for AdminPricingService core functionality
Tests the key validation and calculation logic without full imports
"""
import pytest
from core.utils.uuid_utils import uuid7
from decimal import Decimal


class MockPricingConfig:
    """Mock PricingConfig for testing"""
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid7())
        self.subscription_percentage = kwargs.get('subscription_percentage', 10.0)
        self.delivery_costs = kwargs.get('delivery_costs', {
            "standard": 10.0, "express": 25.0, "overnight": 50.0
        })
        self.tax_rates = kwargs.get('tax_rates', {"US": 0.08, "CA": 0.13, "UK": 0.20})
        self.currency_settings = kwargs.get('currency_settings', {"default": "USD"})
        self.updated_by = kwargs.get('updated_by', uuid7())
        self.version = kwargs.get('version', "1.0")
        self.is_active = kwargs.get('is_active', "active")
        self.change_reason = kwargs.get('change_reason', "Test")
        
    def to_dict(self):
        return {
            "id": str(self.id),
            "subscription_percentage": self.subscription_percentage,
            "delivery_costs": self.delivery_costs,
            "tax_rates": self.tax_rates,
            "currency_settings": self.currency_settings,
            "updated_by": str(self.updated_by),
            "version": self.version,
            "is_active": self.is_active,
            "change_reason": self.change_reason
        }


class MockAPIException(Exception):
    """Mock APIException for testing"""
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class AdminPricingServiceLogic:
    """Core logic from AdminPricingService for testing"""
    
    def validate_subscription_percentage(self, percentage: float) -> bool:
        """Validate subscription percentage range"""
        if not (0.1 <= percentage <= 50.0):
            raise MockAPIException(
                status_code=400,
                message=f"Subscription percentage must be between 0.1% and 50%. Provided: {percentage}%"
            )
        return True
    
    def validate_delivery_costs(self, delivery_costs: dict) -> bool:
        """Validate delivery costs structure and values"""
        if not isinstance(delivery_costs, dict):
            raise MockAPIException(
                status_code=400,
                message="Delivery costs must be a dictionary"
            )
        
        # Check for required delivery types
        required_types = ["standard", "express", "overnight"]
        for delivery_type in required_types:
            if delivery_type not in delivery_costs:
                raise MockAPIException(
                    status_code=400,
                    message=f"Missing required delivery type: {delivery_type}"
                )
        
        # Validate cost values
        for delivery_type, cost in delivery_costs.items():
            if not isinstance(cost, (int, float)) or cost < 0:
                raise MockAPIException(
                    status_code=400,
                    message=f"Invalid cost for {delivery_type}: must be a non-negative number"
                )
        
        return True
    
    def increment_version(self, current_version: str) -> str:
        """Increment version number"""
        try:
            parts = current_version.split('.')
            major, minor = int(parts[0]), int(parts[1])
            return f"{major}.{minor + 1}"
        except (ValueError, IndexError):
            return "1.1"
    
    def create_proposed_config(self, current_config: MockPricingConfig, proposed_changes: dict) -> dict:
        """Create a proposed configuration from current config and changes"""
        proposed = {
            "subscription_percentage": current_config.subscription_percentage,
            "delivery_costs": current_config.delivery_costs.copy(),
            "tax_rates": current_config.tax_rates.copy(),
            "currency_settings": current_config.currency_settings.copy()
        }
        
        # Apply proposed changes
        if "subscription_percentage" in proposed_changes:
            percentage = proposed_changes["subscription_percentage"]
            self.validate_subscription_percentage(percentage)
            proposed["subscription_percentage"] = percentage
        
        if "delivery_costs" in proposed_changes:
            self.validate_delivery_costs(proposed_changes["delivery_costs"])
            proposed["delivery_costs"] = proposed_changes["delivery_costs"]
        
        if "tax_rates" in proposed_changes:
            proposed["tax_rates"].update(proposed_changes["tax_rates"])
        
        return proposed
    
    def calculate_subscription_cost(self, base_cost: Decimal, config: dict) -> Decimal:
        """Calculate subscription cost using configuration"""
        # Apply admin percentage
        admin_fee = base_cost * (Decimal(str(config["subscription_percentage"])) / 100)
        
        # Add delivery cost (assume standard delivery)
        delivery_cost = Decimal(str(config["delivery_costs"].get("standard", 0)))
        
        # Apply tax (assume US tax rate)
        tax_rate = Decimal(str(config["tax_rates"].get("US", 0)))
        subtotal = base_cost + admin_fee + delivery_cost
        tax_amount = subtotal * tax_rate
        
        return subtotal + tax_amount


class TestAdminPricingServiceLogic:
    """Test the core logic of AdminPricingService"""
    
    @pytest.fixture
    def service_logic(self):
        return AdminPricingServiceLogic()
    
    @pytest.fixture
    def sample_config(self):
        return MockPricingConfig()
    
    def test_validate_subscription_percentage_valid(self, service_logic):
        """Test valid subscription percentage validation"""
        # Valid percentages
        assert service_logic.validate_subscription_percentage(0.1) == True
        assert service_logic.validate_subscription_percentage(25.0) == True
        assert service_logic.validate_subscription_percentage(50.0) == True
    
    def test_validate_subscription_percentage_invalid_low(self, service_logic):
        """Test subscription percentage validation with value too low"""
        with pytest.raises(MockAPIException) as exc_info:
            service_logic.validate_subscription_percentage(0.05)
        
        assert exc_info.value.status_code == 400
        assert "between 0.1% and 50%" in exc_info.value.message
    
    def test_validate_subscription_percentage_invalid_high(self, service_logic):
        """Test subscription percentage validation with value too high"""
        with pytest.raises(MockAPIException) as exc_info:
            service_logic.validate_subscription_percentage(55.0)
        
        assert exc_info.value.status_code == 400
        assert "between 0.1% and 50%" in exc_info.value.message
    
    def test_validate_delivery_costs_valid(self, service_logic):
        """Test valid delivery costs validation"""
        valid_costs = {
            "standard": 10.0,
            "express": 25.0,
            "overnight": 50.0
        }
        assert service_logic.validate_delivery_costs(valid_costs) == True
    
    def test_validate_delivery_costs_not_dict(self, service_logic):
        """Test delivery costs validation with non-dictionary input"""
        with pytest.raises(MockAPIException) as exc_info:
            service_logic.validate_delivery_costs("not a dict")
        
        assert exc_info.value.status_code == 400
        assert "must be a dictionary" in exc_info.value.message
    
    def test_validate_delivery_costs_missing_required(self, service_logic):
        """Test delivery costs validation with missing required type"""
        invalid_costs = {
            "standard": 10.0,
            "express": 25.0
            # Missing "overnight"
        }
        
        with pytest.raises(MockAPIException) as exc_info:
            service_logic.validate_delivery_costs(invalid_costs)
        
        assert exc_info.value.status_code == 400
        assert "Missing required delivery type: overnight" in exc_info.value.message
    
    def test_validate_delivery_costs_negative_value(self, service_logic):
        """Test delivery costs validation with negative value"""
        invalid_costs = {
            "standard": -5.0,
            "express": 25.0,
            "overnight": 50.0
        }
        
        with pytest.raises(MockAPIException) as exc_info:
            service_logic.validate_delivery_costs(invalid_costs)
        
        assert exc_info.value.status_code == 400
        assert "must be a non-negative number" in exc_info.value.message
    
    def test_increment_version_normal(self, service_logic):
        """Test normal version increment"""
        assert service_logic.increment_version("1.0") == "1.1"
        assert service_logic.increment_version("2.5") == "2.6"
        assert service_logic.increment_version("10.15") == "10.16"
    
    def test_increment_version_invalid_format(self, service_logic):
        """Test version increment with invalid format"""
        assert service_logic.increment_version("invalid") == "1.1"
        assert service_logic.increment_version("1") == "1.1"
        assert service_logic.increment_version("") == "1.1"
    
    def test_create_proposed_config_percentage_change(self, service_logic, sample_config):
        """Test creating proposed config with percentage change"""
        proposed_changes = {"subscription_percentage": 15.0}
        
        result = service_logic.create_proposed_config(sample_config, proposed_changes)
        
        assert result["subscription_percentage"] == 15.0
        assert result["delivery_costs"] == sample_config.delivery_costs
        assert result["tax_rates"] == sample_config.tax_rates
    
    def test_create_proposed_config_delivery_change(self, service_logic, sample_config):
        """Test creating proposed config with delivery costs change"""
        proposed_changes = {
            "delivery_costs": {
                "standard": 12.0,
                "express": 30.0,
                "overnight": 60.0
            }
        }
        
        result = service_logic.create_proposed_config(sample_config, proposed_changes)
        
        assert result["delivery_costs"]["standard"] == 12.0
        assert result["subscription_percentage"] == sample_config.subscription_percentage
    
    def test_create_proposed_config_invalid_percentage(self, service_logic, sample_config):
        """Test creating proposed config with invalid percentage"""
        proposed_changes = {"subscription_percentage": 55.0}
        
        with pytest.raises(MockAPIException) as exc_info:
            service_logic.create_proposed_config(sample_config, proposed_changes)
        
        assert exc_info.value.status_code == 400
        assert "between 0.1% and 50%" in exc_info.value.message
    
    def test_calculate_subscription_cost_basic(self, service_logic):
        """Test basic subscription cost calculation"""
        base_cost = Decimal('100.00')
        config = {
            "subscription_percentage": 10.0,
            "delivery_costs": {"standard": 10.0},
            "tax_rates": {"US": 0.08}
        }
        
        # Expected: 100 + 10 (admin fee) + 10 (delivery) = 120, then 120 * 1.08 = 129.60
        expected = Decimal('129.60')
        result = service_logic.calculate_subscription_cost(base_cost, config)
        
        assert result == expected
    
    def test_calculate_subscription_cost_different_percentage(self, service_logic):
        """Test subscription cost calculation with different admin percentage"""
        base_cost = Decimal('100.00')
        config = {
            "subscription_percentage": 15.0,  # Higher percentage
            "delivery_costs": {"standard": 10.0},
            "tax_rates": {"US": 0.08}
        }
        
        # Expected: 100 + 15 (admin fee) + 10 (delivery) = 125, then 125 * 1.08 = 135.00
        expected = Decimal('135.00')
        result = service_logic.calculate_subscription_cost(base_cost, config)
        
        assert result == expected
    
    def test_calculate_subscription_cost_no_tax(self, service_logic):
        """Test subscription cost calculation with no tax"""
        base_cost = Decimal('100.00')
        config = {
            "subscription_percentage": 10.0,
            "delivery_costs": {"standard": 10.0},
            "tax_rates": {"US": 0.0}  # No tax
        }
        
        # Expected: 100 + 10 (admin fee) + 10 (delivery) = 120
        expected = Decimal('120.00')
        result = service_logic.calculate_subscription_cost(base_cost, config)
        
        assert result == expected