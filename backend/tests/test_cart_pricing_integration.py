"""
Integration Tests for Cart Service Pricing and Discount Logic
Tests the actual cart service methods with mocked dependencies
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json
from core.utils.uuid_utils import uuid7, UUID
from fastapi import HTTPException

from services.cart import CartService
from models.promocode import Promocode
from models.product import Product, ProductVariant
from models.inventories import Inventory
from schemas.cart import AddToCartRequest


class TestCartServicePricing:
    """Test cart service pricing methods"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def cart_service(self, mock_db):
        service = CartService(mock_db)
        service._get_redis_client = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_redis_client(self):
        return AsyncMock()
    
    @pytest.fixture
    def sample_cart_data(self):
        return {
            "user_id": str(uuid7()),
            "items": {
                "item1": {
                    "variant_id": str(uuid7()),
                    "product_id": str(uuid7()),
                    "product_name": "Test Product 1",
                    "variant_name": "Default",
                    "quantity": 2,
                    "price_per_unit": 25.00,
                    "total_price": 50.00
                },
                "item2": {
                    "variant_id": str(uuid7()),
                    "product_id": str(uuid7()),
                    "product_name": "Test Product 2",
                    "variant_name": "Large",
                    "quantity": 1,
                    "price_per_unit": 40.00,
                    "total_price": 40.00
                }
            },
            "updated_at": datetime.utcnow().isoformat(),
            "total_items": 3,
            "subtotal": 90.00
        }
    
    @pytest.mark.asyncio
    async def test_validate_cart_prices_no_changes(self, cart_service, sample_cart_data):
        """Test price validation when prices haven't changed"""
        # Mock database query to return variants with same prices
        mock_variant1 = MagicMock()
        mock_variant1.id = UUID(sample_cart_data["items"]["item1"]["variant_id"])
        mock_variant1.sale_price = 25.00
        mock_variant1.base_price = 30.00
        
        mock_variant2 = MagicMock()
        mock_variant2.id = UUID(sample_cart_data["items"]["item2"]["variant_id"])
        mock_variant2.sale_price = 40.00
        mock_variant2.base_price = 45.00
        
        # Mock database execute method
        cart_service.db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_variant1, mock_variant2]
        cart_service.db.execute.return_value = mock_result
        
        # Test price validation
        original_subtotal = sample_cart_data["subtotal"]
        await cart_service._validate_cart_prices(sample_cart_data)
        
        # Prices should remain the same
        assert sample_cart_data["subtotal"] == original_subtotal
        assert sample_cart_data["items"]["item1"]["price_per_unit"] == 25.00
        assert sample_cart_data["items"]["item2"]["price_per_unit"] == 40.00
    
    @pytest.mark.asyncio
    async def test_validate_cart_prices_with_updates(self, cart_service, sample_cart_data):
        """Test price validation when prices have changed"""
        # Mock database query to return variants with updated prices
        mock_variant1 = MagicMock()
        mock_variant1.id = UUID(sample_cart_data["items"]["item1"]["variant_id"])
        mock_variant1.sale_price = 22.00  # Price decreased
        mock_variant1.base_price = 30.00
        
        mock_variant2 = MagicMock()
        mock_variant2.id = UUID(sample_cart_data["items"]["item2"]["variant_id"])
        mock_variant2.sale_price = 45.00  # Price increased
        mock_variant2.base_price = 50.00
        
        # Mock database execute method
        cart_service.db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_variant1, mock_variant2]
        cart_service.db.execute.return_value = mock_result
        
        # Test price validation
        await cart_service._validate_cart_prices(sample_cart_data)
        
        # Prices should be updated
        assert sample_cart_data["items"]["item1"]["price_per_unit"] == 22.00
        assert sample_cart_data["items"]["item1"]["total_price"] == 44.00  # 2 * 22.00
        assert sample_cart_data["items"]["item2"]["price_per_unit"] == 45.00
        assert sample_cart_data["items"]["item2"]["total_price"] == 45.00  # 1 * 45.00
        
        # Subtotal should be recalculated
        expected_subtotal = 44.00 + 45.00
        assert sample_cart_data["subtotal"] == expected_subtotal
    
    @pytest.mark.asyncio
    async def test_apply_percentage_promocode(self, cart_service, mock_redis_client):
        """Test applying percentage-based promocode"""
        user_id = uuid7()
        cart_key = f"cart:{user_id}"
        
        # Mock cart data
        cart_data = {
            "items": {"item1": {"total_price": 100.00}},
            "subtotal": 100.00
        }
        
        # Mock Redis operations
        cart_service._get_redis_client = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.get.return_value = json.dumps(cart_data)
        
        # Mock promocode service
        with patch('services.cart.PromocodeService') as mock_promo_service:
            mock_promocode = Promocode(
                id=uuid7(),
                code="SAVE20",
                discount_type="percentage",
                value=0.20,  # 20%
                is_active=True,
                expiration_date=datetime.utcnow() + timedelta(days=30)
            )
            
            mock_promo_instance = mock_promo_service.return_value
            mock_promo_instance.get_promocode_by_code.return_value = mock_promocode
            
            # Mock get_cart method
            cart_service.get_cart = AsyncMock()
            mock_cart_response = MagicMock()
            mock_cart_response.subtotal = 100.00
            mock_cart_response.tax_amount = 10.00
            mock_cart_response.shipping_amount = 5.00
            cart_service.get_cart.return_value = mock_cart_response
            
            # Test applying promocode
            result = await cart_service.apply_promocode(user_id, "SAVE20")
            
            # Verify discount calculation
            expected_discount = 100.00 * 0.20  # 20% of $100 = $20
            assert result["discount_amount"] == expected_discount
            assert result["promocode"] == "SAVE20"
            assert result["discount_type"] == "percentage"
    
    @pytest.mark.asyncio
    async def test_apply_fixed_promocode(self, cart_service, mock_redis_client):
        """Test applying fixed amount promocode"""
        user_id = uuid7()
        
        # Mock cart data
        cart_data = {
            "items": {"item1": {"total_price": 100.00}},
            "subtotal": 100.00
        }
        
        # Mock Redis operations
        cart_service._get_redis_client = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.get.return_value = json.dumps(cart_data)
        
        # Mock promocode service
        with patch('services.cart.PromocodeService') as mock_promo_service:
            mock_promocode = Promocode(
                id=uuid7(),
                code="SAVE15",
                discount_type="fixed",
                value=15.00,  # $15 off
                is_active=True,
                expiration_date=datetime.utcnow() + timedelta(days=30)
            )
            
            mock_promo_instance = mock_promo_service.return_value
            mock_promo_instance.get_promocode_by_code.return_value = mock_promocode
            
            # Mock get_cart method
            cart_service.get_cart = AsyncMock()
            mock_cart_response = MagicMock()
            mock_cart_response.subtotal = 100.00
            mock_cart_response.tax_amount = 10.00
            mock_cart_response.shipping_amount = 5.00
            cart_service.get_cart.return_value = mock_cart_response
            
            # Test applying promocode
            result = await cart_service.apply_promocode(user_id, "SAVE15")
            
            # Verify discount calculation
            assert result["discount_amount"] == 15.00
            assert result["promocode"] == "SAVE15"
            assert result["discount_type"] == "fixed"
    
    @pytest.mark.asyncio
    async def test_apply_shipping_promocode(self, cart_service, mock_redis_client):
        """Test applying free shipping promocode"""
        user_id = uuid7()
        
        # Mock cart data
        cart_data = {
            "items": {"item1": {"total_price": 100.00}},
            "subtotal": 100.00
        }
        
        # Mock Redis operations
        cart_service._get_redis_client = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.get.return_value = json.dumps(cart_data)
        
        # Mock promocode service
        with patch('services.cart.PromocodeService') as mock_promo_service:
            mock_promocode = Promocode(
                id=uuid7(),
                code="FREESHIP",
                discount_type="shipping",
                value=0.00,
                is_active=True,
                expiration_date=datetime.utcnow() + timedelta(days=30)
            )
            
            mock_promo_instance = mock_promo_service.return_value
            mock_promo_instance.get_promocode_by_code.return_value = mock_promocode
            
            # Mock get_cart method
            cart_service.get_cart = AsyncMock()
            mock_cart_response = MagicMock()
            mock_cart_response.subtotal = 100.00
            mock_cart_response.tax_amount = 10.00
            mock_cart_response.shipping_amount = 15.00  # $15 shipping
            cart_service.get_cart.return_value = mock_cart_response
            
            # Test applying promocode
            result = await cart_service.apply_promocode(user_id, "FREESHIP")
            
            # Verify shipping discount
            assert result["discount_amount"] == 15.00  # Should equal shipping amount
            assert result["promocode"] == "FREESHIP"
            assert result["discount_type"] == "shipping"
    
    @pytest.mark.asyncio
    async def test_apply_invalid_promocode(self, cart_service, mock_redis_client):
        """Test applying invalid promocode"""
        user_id = uuid7()
        
        # Mock cart data
        cart_data = {"items": {}, "subtotal": 100.00}
        
        # Mock Redis operations
        cart_service._get_redis_client = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.get.return_value = json.dumps(cart_data)
        
        # Mock promocode service to return None (invalid code)
        with patch('services.cart.PromocodeService') as mock_promo_service:
            mock_promo_instance = mock_promo_service.return_value
            mock_promo_instance.get_promocode_by_code.return_value = None
            
            # Test applying invalid promocode
            with pytest.raises(HTTPException) as exc_info:
                await cart_service.apply_promocode(user_id, "INVALID")
            
            assert exc_info.value.status_code == 400
            assert "Invalid or inactive promocode" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_apply_expired_promocode(self, cart_service, mock_redis_client):
        """Test applying expired promocode"""
        user_id = uuid7()
        
        # Mock cart data
        cart_data = {"items": {}, "subtotal": 100.00}
        
        # Mock Redis operations
        cart_service._get_redis_client = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.get.return_value = json.dumps(cart_data)
        
        # Mock expired promocode
        with patch('services.cart.PromocodeService') as mock_promo_service:
            mock_promocode = Promocode(
                id=uuid7(),
                code="EXPIRED",
                discount_type="percentage",
                value=0.10,
                is_active=True,
                expiration_date=datetime.utcnow() - timedelta(days=1)  # Expired
            )
            
            mock_promo_instance = mock_promo_service.return_value
            mock_promo_instance.get_promocode_by_code.return_value = mock_promocode
            
            # Test applying expired promocode
            with pytest.raises(HTTPException) as exc_info:
                await cart_service.apply_promocode(user_id, "EXPIRED")
            
            assert exc_info.value.status_code == 400
            assert "expired" in str(exc_info.value.detail).lower()
    
    @pytest.mark.asyncio
    async def test_remove_promocode(self, cart_service, mock_redis_client):
        """Test removing promocode from cart"""
        user_id = uuid7()
        
        # Mock cart data with promocode
        cart_data = {
            "items": {"item1": {"total_price": 100.00}},
            "subtotal": 100.00,
            "promocode": {
                "code": "SAVE10",
                "discount_amount": 10.00
            }
        }
        
        # Mock Redis operations
        cart_service._get_redis_client = AsyncMock(return_value=mock_redis_client)
        mock_redis_client.get.return_value = json.dumps(cart_data)
        
        # Mock get_cart method
        cart_service.get_cart = AsyncMock()
        
        # Test removing promocode
        result = await cart_service.remove_promocode(user_id)
        
        # Verify promocode was removed
        assert result["message"] == "Promocode removed"
        
        # Verify Redis set was called to update cart
        mock_redis_client.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_calculate_totals(self, cart_service):
        """Test total calculation with discount"""
        user_id = uuid7()
        
        # Mock cart response
        mock_cart = MagicMock()
        mock_cart.subtotal = 100.00
        mock_cart.tax_amount = 8.00
        mock_cart.shipping_amount = 10.00
        
        cart_service.get_cart = AsyncMock(return_value=mock_cart)
        
        # Test calculation with discount
        data = {"discount_amount": 15.00}
        result = await cart_service.calculate_totals(user_id, data)
        
        expected_total = 100.00 + 8.00 + 10.00 - 15.00  # $103.00
        
        assert result["subtotal"] == 100.00
        assert result["tax_amount"] == 8.00
        assert result["shipping_amount"] == 10.00
        assert result["discount_amount"] == 15.00
        assert result["total_amount"] == expected_total
        assert result["currency"] == "USD"
    
    @pytest.mark.asyncio
    async def test_free_shipping_threshold(self, cart_service):
        """Test free shipping threshold logic"""
        user_id = uuid7()
        address = {"city": "Test City", "state": "TS"}
        
        # Mock shipping service
        with patch('services.cart.ShippingService') as mock_shipping_service:
            mock_shipping_instance = mock_shipping_service.return_value
            
            # Mock standard shipping methods
            mock_method = MagicMock()
            mock_method.id = uuid7()
            mock_method.name = "Standard Shipping"
            mock_method.price = 10.00
            mock_method.estimated_days = 5
            
            mock_shipping_instance.get_all_active_shipping_methods.return_value = [mock_method]
            
            # Mock cart with subtotal above free shipping threshold
            mock_cart = MagicMock()
            mock_cart.subtotal = 60.00  # Above $50 threshold
            
            cart_service.get_cart = AsyncMock(return_value=mock_cart)
            
            # Test getting shipping options
            options = await cart_service.get_shipping_options(user_id, address)
            
            # Should include free shipping option
            free_shipping_option = next(
                (opt for opt in options if opt["name"] == "Free Shipping"), 
                None
            )
            
            assert free_shipping_option is not None
            assert free_shipping_option["price"] == 0.00
            assert "Orders over $100" in free_shipping_option["description"]


class TestCartValidationIntegration:
    """Test cart validation with pricing integration"""
    
    @pytest.fixture
    def mock_db(self):
        return AsyncMock()
    
    @pytest.fixture
    def cart_service(self, mock_db):
        service = CartService(mock_db)
        service._get_redis_client = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_validate_cart_comprehensive(self, cart_service):
        """Test comprehensive cart validation"""
        user_id = uuid7()
        
        # Mock Redis cart data
        cart_data = {
            "user_id": str(user_id),
            "items": {
                "item1": {
                    "variant_id": str(uuid7()),
                    "quantity": 2,
                    "price_per_unit": 25.00,
                    "total_price": 50.00
                }
            },
            "subtotal": 50.00,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Mock Redis operations
        mock_redis_client = AsyncMock()
        mock_redis_client.get.return_value = json.dumps(cart_data)
        cart_service._get_redis_client = AsyncMock(return_value=mock_redis_client)
        
        # Mock variant validation
        mock_variant = MagicMock()
        mock_variant.id = UUID(cart_data["items"]["item1"]["variant_id"])
        mock_variant.sale_price = 25.00
        mock_variant.base_price = 30.00
        mock_variant.inventory = MagicMock()
        mock_variant.inventory.quantity = 10  # Sufficient stock
        
        # Mock database queries
        cart_service.db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_variant]
        cart_service.db.execute.return_value = mock_result
        
        # Test validation
        result = await cart_service.validate_cart(user_id)
        
        # Should be valid
        assert result["valid"] is True
        assert result["can_checkout"] is True
        assert len(result["issues"]) == 0
        assert result["cart"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])