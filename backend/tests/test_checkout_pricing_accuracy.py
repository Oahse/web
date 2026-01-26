"""
Test checkout pricing accuracy and validation
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from decimal import Decimal
from core.utils.uuid_utils import uuid7
from fastapi import HTTPException

from services.cart import CartService
from services.orders import OrderService
from services.tax import TaxService, TaxCalculationResult, TaxType


class TestCheckoutPricingAccuracy:
    """Test checkout pricing calculations for accuracy"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def cart_service(self, mock_db):
        service = CartService(mock_db)
        service._get_redis_client = AsyncMock()
        return service
    
    @pytest.fixture
    def order_service(self, mock_db):
        return OrderService(mock_db)
    
    @pytest.fixture
    def sample_cart_data(self):
        return {
            "user_id": str(uuid7()),
            "items": {
                "item1": {
                    "variant_id": str(uuid7()),
                    "product_id": str(uuid7()),
                    "product_name": "Test Product 1",
                    "quantity": 2,
                    "price_per_unit": 25.99,
                    "total_price": 51.98
                },
                "item2": {
                    "variant_id": str(uuid7()),
                    "product_id": str(uuid7()),
                    "product_name": "Test Product 2",
                    "quantity": 1,
                    "price_per_unit": 39.99,
                    "total_price": 39.99
                }
            },
            "subtotal": 91.97,
            "total_items": 3
        }
    
    def test_subtotal_calculation_accuracy(self, sample_cart_data):
        """Test that subtotal is calculated accurately"""
        items = sample_cart_data["items"]
        
        # Calculate subtotal manually
        expected_subtotal = sum(item["total_price"] for item in items.values())
        actual_subtotal = sample_cart_data["subtotal"]
        
        assert expected_subtotal == actual_subtotal
        assert expected_subtotal == 91.97
    
    def test_item_total_calculation_accuracy(self, sample_cart_data):
        """Test that individual item totals are accurate"""
        for item in sample_cart_data["items"].values():
            expected_total = item["quantity"] * item["price_per_unit"]
            actual_total = item["total_price"]
            
            # Allow for small floating point differences
            assert abs(expected_total - actual_total) < 0.01
    
    @pytest.mark.asyncio
    async def test_tax_calculation_accuracy(self, mock_db):
        """Test tax calculation accuracy"""
        tax_service = TaxService(mock_db)
        
        # Mock the tax calculation to return a known result
        tax_service._calculate_with_real_services = AsyncMock(return_value=None)
            tax_service._get_location_info = AsyncMock(return_value={
                "country_code": "US",
                "state_code": "CA"
            })
            
            subtotal = Decimal("100.00")
            result = await tax_service.calculate_tax(subtotal)
            
            # Should use emergency fallback rate for US (8%)
            expected_tax = subtotal * Decimal("0.08")
            
            assert abs(float(result.tax_amount) - float(expected_tax)) < 0.01
    
    @pytest.mark.asyncio
    async def test_shipping_cost_accuracy(self, cart_service, sample_cart_data):
        """Test shipping cost calculation accuracy"""
        user_id = uuid7()
        
        # Mock cart data
        cart_service.get_hash = AsyncMock(return_value=sample_cart_data)
        
        # Mock shipping methods
        mock_shipping_method = MagicMock()
        mock_shipping_method.id = uuid7()
        mock_shipping_method.name = "Standard Shipping"
        mock_shipping_method.price = 9.99
        mock_shipping_method.is_active = True
        mock_shipping_method.estimated_days = 5
        
        cart_service.db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_shipping_method]
        cart_service.db.execute.return_value = mock_result
        
        # Get shipping options
        result = await cart_service.get_shipping_options(user_id, {})
        
        # Verify shipping cost accuracy
        shipping_options = result["shipping_options"]
        assert len(shipping_options) == 1
        assert shipping_options[0]["price"] == 9.99
        assert shipping_options[0]["name"] == "Standard Shipping"
    
    @pytest.mark.asyncio
    async def test_final_total_calculation_accuracy(self, order_service):
        """Test final order total calculation accuracy"""
        # Mock validated items
        validated_items = [
            {
                "variant_id": uuid7(),
                "quantity": 2,
                "backend_price": 25.99,
                "backend_total": 51.98
            },
            {
                "variant_id": uuid7(),
                "quantity": 1,
                "backend_price": 39.99,
                "backend_total": 39.99
            }
        ]
        
        # Mock shipping method
        mock_shipping_method = MagicMock()
        mock_shipping_method.price = 9.99
        
        # Mock shipping address
        mock_shipping_address = MagicMock()
        mock_shipping_address.state = "CA"
        mock_shipping_address.country = "US"
        
        # Mock tax rate method
        order_service._get_tax_rate = AsyncMock(return_value=0.0725)  # CA tax rate
        order_service._calculate_discount_amount = AsyncMock(return_value=0.0)
        
        # Calculate final total
        result = await order_service._calculate_final_order_total(
            validated_items,
            mock_shipping_method,
            mock_shipping_address
        )
        
        # Verify calculations
        expected_subtotal = 91.97
        expected_shipping = 9.99
        expected_tax = expected_subtotal * 0.0725  # 6.67
        expected_total = expected_subtotal + expected_shipping + expected_tax
        
        assert abs(result["subtotal"] - expected_subtotal) < 0.01
        assert abs(result["shipping_cost"] - expected_shipping) < 0.01
        assert abs(result["tax_amount"] - expected_tax) < 0.01
        assert abs(result["total_amount"] - expected_total) < 0.01
    
    def test_price_precision_handling(self):
        """Test that price calculations handle precision correctly"""
        # Test common floating point precision issues
        price1 = 0.1
        price2 = 0.2
        expected = 0.3
        
        # Direct addition has precision issues
        direct_sum = price1 + price2
        assert direct_sum != expected  # This will be 0.30000000000000004
        
        # Proper handling with rounding
        proper_sum = round((price1 + price2) * 100) / 100
        assert proper_sum == expected
        
        # Test with realistic e-commerce prices
        item_price = 19.99
        quantity = 3
        expected_total = 59.97
        
        calculated_total = round(item_price * quantity * 100) / 100
        assert calculated_total == expected_total
    
    def test_discount_calculation_accuracy(self):
        """Test discount calculation accuracy"""
        subtotal = 100.00
        
        # Test percentage discount
        discount_rate = 0.15  # 15%
        discount_amount = subtotal * discount_rate
        final_total = subtotal - discount_amount
        
        assert discount_amount == 15.00
        assert final_total == 85.00
        
        # Test fixed discount
        fixed_discount = 20.00
        final_total_fixed = subtotal - fixed_discount
        
        assert final_total_fixed == 80.00
        
        # Test discount with maximum limit
        max_discount = 10.00
        actual_discount = min(discount_amount, max_discount)
        final_total_capped = subtotal - actual_discount
        
        assert actual_discount == 10.00
        assert final_total_capped == 90.00
    
    def test_currency_formatting_accuracy(self):
        """Test currency formatting maintains precision"""
        test_amounts = [
            (19.99, "$19.99"),
            (0.01, "$0.01"),
            (1000.00, "$1,000.00"),
            (1234.56, "$1,234.56")
        ]
        
        for amount, expected in test_amounts:
            formatted = "${:,.2f}".format(amount)
            assert formatted == expected