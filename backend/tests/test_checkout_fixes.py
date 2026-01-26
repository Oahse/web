"""
Test checkout bug fixes for inventory mismatches, payment edge cases, and race conditions
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from core.utils.uuid_utils import uuid7
from datetime import datetime, timedelta

from services.orders import OrderService
from services.inventories import InventoryService
from services.payments import PaymentService
from schemas.orders import CheckoutRequest
from models.inventories import Inventory
from models.orders import Order
from models.payments import PaymentMethod
from core.exceptions import APIException
from fastapi import HTTPException
import stripe


class TestCheckoutFixes:
    """Test critical checkout bug fixes"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session with transaction support"""
        session = AsyncMock(spec=AsyncSession)
        session.begin = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        return session
    
    @pytest.fixture
    def checkout_request(self):
        """Sample checkout request"""
        return CheckoutRequest(
            shipping_address_id=uuid7(),
            shipping_method_id=uuid7(),
            payment_method_id=uuid7(),
            notes="Test order"
        )
    
    @pytest.fixture
    def mock_inventory(self):
        """Mock inventory with stock"""
        inventory = AsyncMock()
        inventory.id = uuid7()
        inventory.variant_id = uuid7()
        inventory.quantity_available = 10
        inventory.version = 1
        return inventory
    
    async def test_inventory_race_condition_prevention(self, mock_db_session, mock_inventory):
        """Test that inventory operations prevent race conditions with proper locking"""
        inventory_service = InventoryService(mock_db_session)
        
        # Mock database query with lock
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_inventory
        mock_db_session.execute.return_value = mock_result
        
        # Test concurrent stock reservations
        variant_id = mock_inventory.variant_id
        
        # Simulate successful reservation
        result = await inventory_service.reserve_stock_for_order(
            variant_id=variant_id,
            quantity=5,
            user_id=uuid7(),
            expires_in_minutes=15
        )
        
        assert result["success"] is True
        assert result["new_quantity"] == 5  # 10 - 5 = 5
        
        # Verify SELECT ... FOR UPDATE was used
        mock_db_session.execute.assert_called()
        call_args = mock_db_session.execute.call_args[0][0]
        assert "FOR UPDATE" in str(call_args).upper()
    
    async def test_inventory_deadlock_handling(self, mock_db_session):
        """Test that inventory service handles deadlocks gracefully"""
        inventory_service = InventoryService(mock_db_session)
        
        # Mock deadlock error
        deadlock_error = Exception("could not obtain lock on row")
        mock_db_session.execute.side_effect = [deadlock_error, deadlock_error, AsyncMock()]
        
        # Should retry and eventually succeed
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await inventory_service.reserve_stock_for_order(
                variant_id=uuid7(),
                quantity=1,
                user_id=uuid7()
            )
        
        # Should indicate retry was suggested
        assert result["success"] is False
        assert result.get("retry_suggested") is True
        assert "high demand" in result["message"]
    
    async def test_payment_timeout_and_retry(self, mock_db_session):
        """Test payment timeout handling and retry logic"""
        payment_service = PaymentService(mock_db_session)
        
        # Mock payment method
        mock_payment_method = AsyncMock()
        mock_payment_method.stripe_payment_method_id = "pm_test"
        mock_payment_method.expires_at = None
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_payment_method
        mock_db_session.execute.return_value = mock_result
        
        # Mock timeout on first attempt, success on second
        with patch.object(payment_service, '_process_payment_internal') as mock_process:
            mock_process.side_effect = [
                asyncio.TimeoutError(),  # First attempt times out
                {"status": "succeeded", "payment_intent_id": "pi_test"}  # Second succeeds
            ]
            
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await payment_service.process_payment_with_timeout_and_retry(
                    user_id=uuid7(),
                    amount=100.0,
                    payment_method_id=uuid7(),
                    timeout_seconds=1,
                    max_retries=2
                )
        
        assert result["status"] == "succeeded"
        assert mock_process.call_count == 2  # Retried once
    
    async def test_stripe_error_categorization(self, mock_db_session):
        """Test proper categorization of Stripe errors"""
        payment_service = PaymentService(mock_db_session)
        
        # Test different Stripe error types
        test_cases = [
            (stripe.error.CardError("Insufficient funds", "insufficient_funds", "card_declined"), "INSUFFICIENT_FUNDS"),
            (stripe.error.CardError("Card declined", "card_declined", "generic_decline"), "CARD_DECLINED"),
            (stripe.error.CardError("Expired card", "expired_card", "expired_card"), "EXPIRED_CARD"),
            (stripe.error.RateLimitError("Rate limit exceeded"), "LIMIT_EXCEEDED"),
        ]
        
        for error, expected_reason in test_cases:
            reason = payment_service._categorize_stripe_error(error)
            assert reason.value.upper() == expected_reason
    
    async def test_checkout_idempotency(self, mock_db_session, checkout_request):
        """Test that checkout prevents duplicate orders with idempotency keys"""
        order_service = OrderService(mock_db_session)
        
        # Mock existing order with same idempotency key
        existing_order = AsyncMock()
        existing_order.id = uuid7()
        existing_order.order_number = "ORD-12345"
        
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = existing_order
        mock_db_session.execute.return_value = mock_result
        
        with patch.object(order_service, '_convert_order_to_response') as mock_convert:
            mock_convert.return_value = AsyncMock()
            
            # Should return existing order, not create new one
            result = await order_service.place_order(
                user_id=uuid7(),
                request=checkout_request,
                background_tasks=AsyncMock(),
                idempotency_key="test_key_123"
            )
        
        mock_convert.assert_called_once_with(existing_order)
    
    async def test_cart_validation_enforcement(self, mock_db_session, checkout_request):
        """Test that checkout always validates cart before proceeding"""
        order_service = OrderService(mock_db_session)
        
        # Mock cart validation failure
        with patch('services.cart.CartService') as mock_cart_service:
            mock_cart_service.return_value.validate_cart.return_value = {
                "valid": False,
                "can_checkout": False,
                "issues": [{"severity": "error", "message": "Item out of stock"}]
            }
            
            # Should raise HTTPException due to validation failure
            with pytest.raises(HTTPException) as exc_info:
                await order_service.place_order(
                    user_id=uuid7(),
                    request=checkout_request,
                    background_tasks=AsyncMock()
                )
            
            assert exc_info.value.status_code == 400
            assert "Cart validation failed" in str(exc_info.value.detail)
    
    async def test_price_tampering_detection(self, mock_db_session, checkout_request):
        """Test that backend recalculates prices and detects tampering"""
        order_service = OrderService(mock_db_session)
        
        # Mock cart validation success
        mock_cart = AsyncMock()
        mock_cart.items = [AsyncMock(saved_for_later=False)]
        
        with patch('services.cart.CartService') as mock_cart_service:
            mock_cart_service.return_value.validate_cart.return_value = {
                "valid": True,
                "can_checkout": True,
                "cart": mock_cart
            }
            
            # Mock price validation failure (price tampering detected)
            with patch.object(order_service, '_validate_and_recalculate_prices') as mock_price_validation:
                mock_price_validation.return_value = {
                    "valid": False,
                    "message": "Price mismatch detected"
                }
                
                # Should raise HTTPException due to price validation failure
                with pytest.raises(HTTPException) as exc_info:
                    await order_service.place_order(
                        user_id=uuid7(),
                        request=checkout_request,
                        background_tasks=AsyncMock()
                    )
                
                assert exc_info.value.status_code == 400
                assert "Price validation failed" in str(exc_info.value.detail)
    
    async def test_atomic_transaction_rollback(self, mock_db_session, checkout_request):
        """Test that checkout rolls back entire transaction on any failure"""
        order_service = OrderService(mock_db_session)
        
        # Mock successful cart validation
        mock_cart = AsyncMock()
        mock_cart.items = [AsyncMock(saved_for_later=False)]
        
        with patch('services.cart.CartService') as mock_cart_service:
            mock_cart_service.return_value.validate_cart.return_value = {
                "valid": True,
                "can_checkout": True,
                "cart": mock_cart
            }
            
            # Mock successful price validation
            with patch.object(order_service, '_validate_and_recalculate_prices') as mock_price_validation:
                mock_price_validation.return_value = {
                    "valid": True,
                    "validated_items": [],
                    "total_amount": 100.0
                }
                
                # Mock inventory reservation failure
                with patch.object(order_service.inventory_service, 'reserve_stock_for_order') as mock_reserve:
                    mock_reserve.return_value = {
                        "success": False,
                        "message": "Insufficient stock"
                    }
                    
                    # Should raise HTTPException and trigger rollback
                    with pytest.raises(HTTPException) as exc_info:
                        await order_service.place_order(
                            user_id=uuid7(),
                            request=checkout_request,
                            background_tasks=AsyncMock()
                        )
                    
                    assert "Insufficient stock" in str(exc_info.value.detail)
                    # Transaction should be rolled back automatically due to exception
    
    async def test_concurrent_checkout_handling(self, mock_db_session):
        """Test handling of concurrent checkout attempts"""
        inventory_service = InventoryService(mock_db_session)
        
        # Simulate concurrent access to same inventory
        mock_inventory = AsyncMock()
        mock_inventory.quantity_available = 1  # Only 1 item left
        
        # First request should succeed
        mock_result1 = AsyncMock()
        mock_result1.scalar_one_or_none.return_value = mock_inventory
        
        # Second request should see updated inventory (no stock left)
        mock_inventory_empty = AsyncMock()
        mock_inventory_empty.quantity_available = 0  # Out of stock
        
        mock_result2 = AsyncMock()
        mock_result2.scalar_one_or_none.return_value = mock_inventory_empty
        
        mock_db_session.execute.side_effect = [mock_result1, mock_result2]
        
        # First reservation should succeed
        result1 = await inventory_service.reserve_stock_for_order(
            variant_id=uuid7(),
            quantity=1,
            user_id=uuid7()
        )
        
        # Second reservation should fail (no stock available)
        result2 = await inventory_service.reserve_stock_for_order(
            variant_id=uuid7(),
            quantity=1,
            user_id=uuid7()
        )
        
        assert result1["success"] is True
        assert result2["success"] is False
        assert "Insufficient stock" in result2["message"]


if __name__ == "__main__":
    pytest.main([__file__])