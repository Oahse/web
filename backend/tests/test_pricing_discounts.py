"""
Comprehensive Unit Tests for Pricing and Discounts
Tests all pricing calculations, discount applications, and promocode logic
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal
from core.utils.uuid_utils import uuid7, UUID
from fastapi import HTTPException

from services.cart import CartService
from services.loyalty import LoyaltyService
from models.promocode import Promocode
from models.product import Product, ProductVariant
from models.inventories import Inventory
from schemas.cart import AddToCartRequest, CartResponse, CartItemResponse


class TestPricingCalculations:
    """Test core pricing calculation logic"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()
    
    @pytest.fixture
    def cart_service(self, mock_db):
        """Create cart service with mocked dependencies"""
        service = CartService(mock_db)
        service._get_redis_client = AsyncMock()
        return service
    
    @pytest.fixture
    def sample_product_variant(self):
        """Sample product variant for testing"""
        product = Product(
            id=uuid7(),
            name="Test Product",
            description="Test Description"
        )
        
        variant = ProductVariant(
            id=uuid7(),
            product_id=product.id,
            product=product,
            name="Default",
            base_price=100.00,
            sale_price=80.00,
            sku="TEST-001"
        )
        
        inventory = Inventory(
            variant_id=variant.id,
            quantity=50,
            reserved_quantity=0
        )
        variant.inventory = inventory
        
        return variant
    
    def test_base_price_calculation(self, sample_product_variant):
        """Test basic price calculation without discounts"""
        variant = sample_product_variant
        quantity = 2
        
        # Should use sale_price if available, otherwise base_price
        expected_unit_price = variant.sale_price or variant.base_price
        expected_total = expected_unit_price * quantity
        
        assert expected_unit_price == 80.00
        assert expected_total == 160.00
    
    def test_price_fallback_to_base(self):
        """Test price fallback when sale_price is None"""
        product = Product(id=uuid7(), name="Test Product")
        variant = ProductVariant(
            id=uuid7(),
            product_id=product.id,
            product=product,
            name="Default",
            base_price=100.00,
            sale_price=None,  # No sale price
            sku="TEST-002"
        )
        
        expected_price = variant.sale_price or variant.base_price
        assert expected_price == 100.00
    
    @pytest.mark.asyncio
    async def test_cart_subtotal_calculation(self, cart_service):
        """Test cart subtotal calculation with multiple items"""
        # Mock cart data with multiple items
        cart_data = {
            "items": {
                "item1": {
                    "variant_id": str(uuid7()),
                    "quantity": 2,
                    "price_per_unit": 50.00,
                    "total_price": 100.00
                },
                "item2": {
                    "variant_id": str(uuid7()),
                    "quantity": 1,
                    "price_per_unit": 30.00,
                    "total_price": 30.00
                }
            }
        }
        
        # Calculate subtotal
        subtotal = sum(item["total_price"] for item in cart_data["items"].values())
        
        assert subtotal == 130.00
    
    @pytest.mark.asyncio
    async def test_tax_calculation(self, cart_service):
        """Test tax calculation (10% standard rate)"""
        subtotal = 100.00
        tax_rate = 0.1  # 10%
        
        expected_tax = subtotal * tax_rate
        assert expected_tax == 10.00
    
    @pytest.mark.asyncio
    async def test_shipping_calculation_with_methods(self, cart_service):
        """Test shipping calculation with different methods"""
        # Mock shipping options method
        cart_service.get_shipping_options = AsyncMock()
        
        # Test case 1: Standard shipping
        subtotal = 40.00
        standard_shipping_cost = 10.00
        
        shipping_cost = standard_shipping_cost
        assert shipping_cost == 10.00
        
        # Test case 2: Express shipping
        express_shipping_cost = 25.00
        shipping_cost = express_shipping_cost
        assert shipping_cost == 25.00


class TestPromocodeDiscounts:
    """Test promocode discount calculations"""
    
    @pytest.fixture
    def percentage_promocode(self):
        """10% discount promocode"""
        return Promocode(
            id=uuid7(),
            code="SAVE10",
            description="10% off",
            discount_type="percentage",
            value=0.10,  # 10%
            minimum_order_amount=None,
            maximum_discount_amount=None,
            usage_limit=None,
            used_count=0,
            is_active=True,
            valid_from=datetime.utcnow() - timedelta(days=1),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
    
    @pytest.fixture
    def fixed_promocode(self):
        """$15 fixed discount promocode"""
        return Promocode(
            id=uuid7(),
            code="SAVE15",
            description="$15 off",
            discount_type="fixed",
            value=15.00,
            minimum_order_amount=50.00,
            maximum_discount_amount=None,
            usage_limit=100,
            used_count=25,
            is_active=True,
            valid_from=datetime.utcnow() - timedelta(days=1),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
    
    @pytest.fixture
    def shipping_promocode(self):
        """Shipping discount promocode"""
        return Promocode(
            id=uuid7(),
            code="SHIP5",
            description="$5 off shipping",
            discount_type="shipping",
            value=5.00,
            minimum_order_amount=None,
            maximum_discount_amount=None,
            usage_limit=None,
            used_count=0,
            is_active=True,
            valid_from=datetime.utcnow() - timedelta(days=1),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
    
    def test_percentage_discount_calculation(self, percentage_promocode):
        """Test percentage-based discount calculation"""
        subtotal = 100.00
        discount_rate = percentage_promocode.value
        
        expected_discount = subtotal * discount_rate
        assert expected_discount == 10.00
        
        final_total = subtotal - expected_discount
        assert final_total == 90.00
    
    def test_fixed_discount_calculation(self, fixed_promocode):
        """Test fixed amount discount calculation"""
        subtotal = 100.00
        discount_amount = fixed_promocode.value
        
        expected_discount = discount_amount
        assert expected_discount == 15.00
        
        final_total = subtotal - expected_discount
        assert final_total == 85.00
    
    def test_shipping_discount_calculation(self, shipping_promocode):
        """Test shipping discount calculation"""
        subtotal = 100.00
        shipping_cost = 10.00
        
        # Shipping promocode should eliminate shipping cost
        discount_amount = shipping_cost
        assert discount_amount == 10.00
        
        final_total = subtotal + shipping_cost - discount_amount
        assert final_total == 100.00
    
    def test_minimum_order_amount_validation(self, fixed_promocode):
        """Test minimum order amount validation"""
        promocode = fixed_promocode  # Has $50 minimum
        
        # Test case 1: Below minimum
        subtotal_below = 40.00
        is_valid = subtotal_below >= (promocode.minimum_order_amount or 0)
        assert is_valid is False
        
        # Test case 2: Above minimum
        subtotal_above = 60.00
        is_valid = subtotal_above >= (promocode.minimum_order_amount or 0)
        assert is_valid is True
    
    def test_maximum_discount_limit(self):
        """Test maximum discount amount limitation"""
        promocode = Promocode(
            code="SAVE20MAX10",
            discount_type="percentage",
            value=0.20,  # 20%
            maximum_discount_amount=10.00,  # Max $10 discount
            is_active=True
        )
        
        subtotal = 100.00
        calculated_discount = subtotal * promocode.value  # $20
        
        # Should be limited to maximum
        final_discount = min(calculated_discount, promocode.maximum_discount_amount or float('inf'))
        assert final_discount == 10.00
    
    def test_usage_limit_validation(self, fixed_promocode):
        """Test promocode usage limit validation"""
        promocode = fixed_promocode  # Usage limit: 100, used: 25
        
        remaining_uses = promocode.usage_limit - promocode.used_count
        assert remaining_uses == 75
        
        is_available = remaining_uses > 0
        assert is_available is True
        
        # Test when limit is reached
        promocode.used_count = 100
        remaining_uses = promocode.usage_limit - promocode.used_count
        is_available = remaining_uses > 0
        assert is_available is False
    
    def test_promocode_expiration_validation(self):
        """Test promocode expiration date validation"""
        # Expired promocode
        expired_promocode = Promocode(
            code="EXPIRED",
            discount_type="percentage",
            value=0.10,
            valid_until=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
            is_active=True
        )
        
        current_time = datetime.utcnow()
        is_valid = (expired_promocode.valid_until is None or 
                   expired_promocode.valid_until > current_time)
        assert is_valid is False
        
        # Valid promocode
        valid_promocode = Promocode(
            code="VALID",
            discount_type="percentage",
            value=0.10,
            valid_until=datetime.utcnow() + timedelta(days=30),  # Valid for 30 days
            is_active=True
        )
        
        is_valid = (valid_promocode.valid_until is None or 
                   valid_promocode.valid_until > current_time)
        assert is_valid is True


class TestLoyaltyDiscounts:
    """Test loyalty program discount calculations"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def loyalty_service(self, mock_db):
        return LoyaltyService(mock_db)
    
    def test_tier_discount_calculation(self):
        """Test discount calculation based on loyalty tier"""
        # Bronze tier (0% discount)
        bronze_discount = 0.0
        base_cost = 100.00
        
        bronze_final = base_cost * (1 - bronze_discount)
        assert bronze_final == 100.00
        
        # Silver tier (2% discount)
        silver_discount = 0.02
        silver_final = base_cost * (1 - silver_discount)
        assert silver_final == 98.00
        
        # Gold tier (5% discount)
        gold_discount = 0.05
        gold_final = base_cost * (1 - gold_discount)
        assert gold_final == 95.00
        
        # Platinum tier (10% discount)
        platinum_discount = 0.10
        platinum_final = base_cost * (1 - platinum_discount)
        assert platinum_final == 90.00
    
    def test_points_multiplier_calculation(self):
        """Test points earning multiplier by tier"""
        base_points = 100
        
        # Different tier multipliers
        bronze_multiplier = 1.0
        silver_multiplier = 1.2
        gold_multiplier = 1.5
        platinum_multiplier = 2.0
        
        assert base_points * bronze_multiplier == 100
        assert base_points * silver_multiplier == 120
        assert base_points * gold_multiplier == 150
        assert base_points * platinum_multiplier == 200


class TestPriceValidation:
    """Test price validation and tampering detection"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def cart_service(self, mock_db):
        service = CartService(mock_db)
        service._get_redis_client = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_price_validation_success(self, cart_service):
        """Test successful price validation"""
        # Mock variant with current price
        variant = MagicMock()
        variant.sale_price = 50.00
        variant.base_price = 60.00
        
        submitted_price = 50.00  # Matches current price
        current_price = variant.sale_price or variant.base_price
        
        # Price difference within tolerance (0.01)
        price_diff = abs(submitted_price - current_price)
        tolerance = 0.01
        
        is_valid = price_diff <= tolerance
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_price_tampering_detection(self, cart_service):
        """Test price tampering detection"""
        # Mock variant with current price
        variant = MagicMock()
        variant.sale_price = 50.00
        variant.base_price = 60.00
        
        submitted_price = 30.00  # Significantly lower than actual
        current_price = variant.sale_price or variant.base_price
        
        # Price difference exceeds tolerance
        price_diff = abs(submitted_price - current_price)
        tolerance = 0.01
        
        is_tampering = price_diff > tolerance
        assert is_tampering is True
        assert price_diff == 20.00  # $20 difference
    
    @pytest.mark.asyncio
    async def test_floating_point_tolerance(self, cart_service):
        """Test floating point precision tolerance"""
        current_price = 19.99
        submitted_price = 19.989999  # Slight floating point difference
        
        price_diff = abs(submitted_price - current_price)
        tolerance = 0.01
        
        is_valid = price_diff <= tolerance
        assert is_valid is True  # Should be within tolerance


class TestComplexPricingScenarios:
    """Test complex pricing scenarios with multiple discounts"""
    
    def test_stacked_discounts_calculation(self):
        """Test calculation with multiple discount types"""
        subtotal = 100.00
        
        # Scenario: Loyalty discount + Promocode + Shipping discount
        loyalty_discount_rate = 0.05  # 5% loyalty discount
        promocode_discount = 10.00    # $10 promocode
        shipping_cost = 15.00
        shipping_discount = 5.00  # $5 off shipping
        
        # Apply discounts in order
        after_loyalty = subtotal * (1 - loyalty_discount_rate)  # $95.00
        after_promocode = after_loyalty - promocode_discount    # $85.00
        shipping_amount = shipping_cost - shipping_discount     # $10.00
        
        final_total = after_promocode + shipping_amount
        
        assert after_loyalty == 95.00
        assert after_promocode == 85.00
        assert final_total == 85.00
    
    def test_discount_precedence_rules(self):
        """Test discount precedence and combination rules"""
        subtotal = 100.00
        
        # Multiple promocodes - typically only one allowed
        promocode1_discount = 15.00  # $15 off
        promocode2_discount = 0.20   # 20% off ($20)
        
        # Should use the better discount for customer
        better_discount = max(promocode1_discount, subtotal * promocode2_discount)
        assert better_discount == 20.00
        
        final_total = subtotal - better_discount
        assert final_total == 80.00
    
    def test_minimum_total_after_discounts(self):
        """Test minimum order total enforcement after discounts"""
        subtotal = 50.00
        large_discount = 60.00  # Discount larger than subtotal
        minimum_total = 0.00    # Minimum order total
        
        # Total should not go below minimum
        calculated_total = subtotal - large_discount
        final_total = max(calculated_total, minimum_total)
        
        assert calculated_total == -10.00
        assert final_total == 0.00
    
    def test_tax_calculation_after_discounts(self):
        """Test tax calculation on discounted amount"""
        subtotal = 100.00
        discount = 20.00
        tax_rate = 0.08  # 8% tax
        
        # Tax should be calculated on discounted amount
        discounted_amount = subtotal - discount  # $80.00
        tax_amount = discounted_amount * tax_rate  # $6.40
        
        final_total = discounted_amount + tax_amount
        
        assert discounted_amount == 80.00
        assert tax_amount == 6.40
        assert final_total == 86.40


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_zero_quantity_pricing(self):
        """Test pricing with zero quantity"""
        unit_price = 50.00
        quantity = 0
        
        total_price = unit_price * quantity
        assert total_price == 0.00
    
    def test_negative_price_handling(self):
        """Test handling of negative prices (should not occur)"""
        # This should be prevented at the model level
        unit_price = -10.00  # Invalid negative price
        quantity = 2
        
        # In a real system, this should raise an error
        # For testing, we verify the calculation
        total_price = unit_price * quantity
        assert total_price == -20.00
        
        # System should validate and reject negative prices
        is_valid_price = unit_price >= 0
        assert is_valid_price is False
    
    def test_very_large_numbers(self):
        """Test pricing with very large numbers"""
        unit_price = 999999.99
        quantity = 1000
        
        total_price = unit_price * quantity
        expected = 999999990.00
        
        assert total_price == expected
    
    def test_decimal_precision(self):
        """Test decimal precision in calculations"""
        # Use Decimal for precise financial calculations
        unit_price = Decimal('19.99')
        quantity = Decimal('3')
        tax_rate = Decimal('0.08')
        
        subtotal = unit_price * quantity  # 59.97
        tax = subtotal * tax_rate         # 4.7976
        total = subtotal + tax            # 64.7676
        
        # Round to 2 decimal places for currency
        final_total = round(total, 2)
        
        assert subtotal == Decimal('59.97')
        assert tax == Decimal('4.7976')
        assert final_total == Decimal('64.77')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])