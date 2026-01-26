"""
Comprehensive integration tests for checkout flow
Tests the complete checkout process including cart validation, payment processing,
inventory updates, and event publishing.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from core.utils.uuid_utils import uuid7
from decimal import Decimal
from datetime import datetime

from services.orders import OrderService
from services.cart import CartService
from services.payments import PaymentService
from services.inventories import InventoryService
from schemas.orders import CheckoutRequest
from models.orders import Order, OrderItem
from models.cart import Cart, CartItem
from models.product import ProductVariant
from models.inventories import Inventory
from models.payments import PaymentMethod, PaymentIntent, Transaction
from models.user import User, Address
from models.shipping import ShippingMethod
from core.hybrid_tasks import HybridTaskManager
from fastapi import BackgroundTasks, HTTPException


class TestCheckoutIntegration:
    """Integration tests for complete checkout flow"""

    @pytest.fixture
    async def db_session(self):
        """Mock database session with transaction support"""
        session = MagicMock(spec=AsyncSession)
        session.begin = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.close = AsyncMock()
        
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def user_data(self):
        """Test user data"""
        return {
            "id": uuid7(),
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User"
        }

    @pytest.fixture
    def product_variant(self):
        """Test product variant"""
        return ProductVariant(
            id=uuid7(),
            product_id=uuid7(),
            name="Test Product",
            base_price=Decimal("29.99"),
            sku="TEST-001",
            is_active=True
        )

    @pytest.fixture
    def cart_with_items(self, user_data, product_variant):
        """Cart with test items"""
        cart = Cart(
            id=uuid7(),
            user_id=user_data["id"],
            session_id=None
        )
        
        cart_item = CartItem(
            id=uuid7(),
            cart_id=cart.id,
            variant_id=product_variant.id,
            quantity=2,
            price_per_unit=product_variant.current_price,
            saved_for_later=False
        )
        cart.items = [cart_item]
        return cart

    @pytest.fixture
    def checkout_request(self):
        """Test checkout request"""
        return CheckoutRequest(
            shipping_address_id=uuid7(),
            shipping_method_id=uuid7(),
            payment_method_id=uuid7(),
            notes="Test order"
        )

    @pytest.fixture
    def mock_inventory(self, product_variant):
        """Mock inventory with sufficient stock"""
        return Inventory(
            id=uuid7(),
            variant_id=product_variant.id,
            location_id=uuid7(),
            quantity_available=100
        )

    @pytest.fixture
    def mock_payment_method(self, user_data):
        """Mock payment method"""
        return PaymentMethod(
            id=uuid7(),
            user_id=user_data["id"],
            type="card",
            provider="stripe",
            stripe_payment_method_id="pm_test_123",
            is_default=True,
            is_active=True
        )

    @pytest.fixture
    def mock_shipping_method(self):
        """Mock shipping method"""
        return ShippingMethod(
            id=uuid7(),
            name="Standard Shipping",
            price=Decimal("5.99"),
            estimated_days=3
        )

    @pytest.fixture
    def mock_address(self, user_data):
        """Mock shipping address"""
        return Address(
            id=uuid7(),
            user_id=user_data["id"],
            street="123 Test St",
            city="Test City",
            state="TS",
            country="US",
            post_code="12345",
            kind="Shipping"
        )

    @patch('services.orders.PaymentService')
    @patch('services.orders.CartService')
    @patch('services.orders.InventoryService')
    async def test_successful_checkout_flow(
        self,
        mock_inventory_service,
        mock_cart_service_class,
        mock_payment_service_class,
        db_session,
        user_data,
        cart_with_items,
        checkout_request,
        product_variant,
        mock_inventory,
        mock_payment_method,
        mock_shipping_method,
        mock_address
    ):
        """Test complete successful checkout flow"""
        
        # Setup mocks
        user_id = user_data["id"]
        
        # Mock cart service
        mock_cart_service = AsyncMock()
        mock_cart_service.validate_cart.return_value = {
            "valid": True,
            "can_checkout": True,
            "cart": cart_with_items,
            "issues": [],
            "summary": {"total_items": 2, "total_amount": 59.98}
        }
        mock_cart_service.clear_cart = AsyncMock()
        mock_cart_service_class.return_value = mock_cart_service
        
        # Mock payment service
        mock_payment_service = AsyncMock()
        mock_payment_service.process_payment.return_value = {
            "status": "succeeded",
            "payment_intent_id": "pi_test_123",
            "transaction_id": str(uuid7())
        }
        mock_payment_service_class.return_value = mock_payment_service
        
        # Mock inventory service
        mock_inventory_service_instance = AsyncMock()
        mock_inventory_service_instance.reserve_inventory.return_value = {"success": True, "reservation_id": uuid7()}
        mock_inventory_service_instance.decrement_stock_on_purchase.return_value = {"success": True}
        mock_inventory_service.return_value = mock_inventory_service_instance
        
        # Mock database queries dynamically
        def mock_db_execute_side_effect(query):
            query_str = str(query).lower()
            if "FROM address" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_address
                return mock_result
            elif "FROM shipping_method" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_shipping_method
                return mock_result
            elif "FROM payment_method" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_payment_method
                return mock_result
            elif "FROM order" in query_str and "idempotency_key" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None # Assume no existing order for successful flow
                return mock_result
            elif "FROM product_variants" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = product_variant
                return mock_result
            elif "FROM inventory" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_inventory
                return mock_result
            
            # Default fallback for unmocked queries
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_result.scalars.return_value.all.return_value = []
            return mock_result

        db_session.execute.side_effect = mock_db_execute_side_effect
        
        # Create order service and execute checkout
        order_service = OrderService(db_session)
        background_tasks = AsyncMock(spec=BackgroundTasks)
        
        # Execute checkout
        result = await order_service.place_order(
            user_id=user_id,
            request=checkout_request,
            background_tasks=background_tasks
        )
        
        # Verify results
        assert result is not None
        assert result.id is not None
        
        # Verify cart validation was called
        mock_cart_service.validate_cart.assert_called_once_with(user_id)
        
        # Verify payment processing was called
        mock_payment_service.process_payment.assert_called_once()
        
        # Verify inventory was reserved
        mock_inventory_service_instance.reserve_inventory.assert_called()
        
        # Verify database transaction
        db_session.begin.assert_called_once()
        db_session.commit.assert_called_once()
        
        # Verify cart was cleared
        mock_cart_service.clear_cart.assert_called_once_with(user_id)

    @patch('services.orders.PaymentService')
    @patch('services.orders.CartService')
    async def test_checkout_with_payment_failure(
        self,
        mock_cart_service_class,
        mock_payment_service_class,
        db_session,
        user_data,
        cart_with_items,
        checkout_request,
        product_variant,
        mock_inventory,
        mock_address,
        mock_shipping_method,
        mock_payment_method
    ):
        """Test checkout flow when payment fails"""
        
        user_id = user_data["id"]
        
        # Mock cart service - valid cart
        mock_cart_service = AsyncMock()
        mock_cart_service.validate_cart.return_value = {
            "valid": True,
            "can_checkout": True,
            "cart": cart_with_items,
            "issues": [],
            "summary": {"total_items": 2, "total_amount": 59.98}
        }
        mock_cart_service_class.return_value = mock_cart_service
        
        # Mock payment service - payment fails
        mock_payment_service = AsyncMock()
        mock_payment_service.process_payment.side_effect = HTTPException(
            status_code=400,
            detail="Payment failed: insufficient funds"
        )
        mock_payment_service_class.return_value = mock_payment_service
        
        # Mock database queries dynamically
        def mock_db_execute_side_effect(query):
            query_str = str(query).lower()
            if "FROM address" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_address
                return mock_result
            elif "FROM shipping_method" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_shipping_method
                return mock_result
            elif "FROM payment_method" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_payment_method
                return mock_result
            elif "FROM order" in query_str and "idempotency_key" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None # No existing order for this flow
                return mock_result
            elif "FROM product_variants" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = product_variant
                return mock_result
            elif "FROM inventory" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_inventory
                return mock_result
            
            # Default fallback for unmocked queries
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_result.scalars.return_value.all.return_value = []
            return mock_result

        db_session.execute.side_effect = mock_db_execute_side_effect

        
        # Create order service
        order_service = OrderService(db_session)
        background_tasks = AsyncMock(spec=BackgroundTasks)
        
        # Execute checkout and expect failure
        with pytest.raises(HTTPException) as exc_info:
            await order_service.place_order(
                user_id=user_id,
                request=checkout_request,
                background_tasks=background_tasks
            )
        
        assert exc_info.value.status_code == 400
        assert "Payment failed" in str(exc_info.value.detail)
        
        # Verify transaction was rolled back
        db_session.rollback.assert_called_once()

    @patch('services.orders.CartService')
    async def test_checkout_with_invalid_cart(
        self,
        mock_cart_service_class,
        db_session,
        user_data,
        checkout_request,
        product_variant,
        mock_inventory,
        mock_address,
        mock_shipping_method,
        mock_payment_method
    ):
        """Test checkout flow with invalid cart"""
        
        user_id = user_data["id"]
        
        # Mock cart service - invalid cart
        mock_cart_service = AsyncMock()
        mock_cart_service.validate_cart.return_value = {
            "valid": False,
            "can_checkout": False,
            "cart": None,
            "issues": [
                {
                    "severity": "error",
                    "message": "Cart is empty",
                    "item_id": None
                }
            ],
            "summary": {"total_items": 0, "total_amount": 0}
        }
        mock_cart_service_class.return_value = mock_cart_service
        
        # Mock database queries dynamically
        def mock_db_execute_side_effect(query):
            query_str = str(query).lower()
            if "FROM address" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_address
                return mock_result
            elif "FROM shipping_method" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_shipping_method
                return mock_result
            elif "FROM payment_method" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_payment_method
                return mock_result
            elif "FROM order" in query_str and "idempotency_key" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None # No existing order for this flow
                return mock_result
            elif "FROM product_variants" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = product_variant
                return mock_result
            elif "FROM inventory" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_inventory
                return mock_result
            
            # Default fallback for unmocked queries
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_result.scalars.return_value.all.return_value = []
            return mock_result

        db_session.execute.side_effect = mock_db_execute_side_effect


        
        # Create order service
        order_service = OrderService(db_session)
        background_tasks = AsyncMock(spec=BackgroundTasks)
        
        # Execute checkout and expect failure
        with pytest.raises(HTTPException) as exc_info:
            await order_service.place_order(
                user_id=user_id,
                request=checkout_request,
                background_tasks=background_tasks
            )
        
        assert exc_info.value.status_code == 400
        assert "Cart validation failed" in str(exc_info.value.detail)

    @patch('services.orders.PaymentService')
    @patch('services.orders.CartService')
    @patch('services.orders.InventoryService')
    async def test_checkout_with_insufficient_inventory(
        self,
        mock_inventory_service,
        mock_cart_service_class,
        mock_payment_service_class,
        db_session,
        user_data,
        cart_with_items,
        checkout_request,
        product_variant,
        mock_inventory,
        mock_address,
        mock_shipping_method,
        mock_payment_method
    ):
        """Test checkout flow when inventory is insufficient"""
        
        user_id = user_data["id"]
        
        # Mock cart service - valid cart
        mock_cart_service = AsyncMock()
        mock_cart_service.validate_cart.return_value = {
            "valid": True,
            "can_checkout": True,
            "cart": cart_with_items,
            "issues": [],
            "summary": {"total_items": 2, "total_amount": 59.98}
        }
        mock_cart_service_class.return_value = mock_cart_service
        
        # Mock inventory service - insufficient stock
        mock_inventory_service_instance = AsyncMock()
        mock_inventory_service_instance.reserve_inventory.side_effect = HTTPException(
            status_code=400,
            detail="Insufficient inventory for product"
        )
        mock_inventory_service.return_value = mock_inventory_service_instance
        
        # Mock database queries dynamically
        def mock_db_execute_side_effect(query):
            query_str = str(query).lower()
            if "FROM address" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_address
                return mock_result
            elif "FROM shipping_method" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_shipping_method
                return mock_result
            elif "FROM payment_method" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_payment_method
                return mock_result
            elif "FROM order" in query_str and "idempotency_key" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = None # No existing order for this flow
                return mock_result
            elif "FROM product_variants" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = product_variant
                return mock_result
            elif "FROM inventory" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_inventory
                return mock_result
            
            # Default fallback for unmocked queries
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_result.scalars.return_value.all.return_value = []
            return mock_result

        db_session.execute.side_effect = mock_db_execute_side_effect
        
        # Create order service
        order_service = OrderService(db_session)
        background_tasks = AsyncMock(spec=BackgroundTasks)
        
        # Execute checkout and expect failure
        with pytest.raises(HTTPException) as exc_info:
            await order_service.place_order(
                user_id=user_id,
                request=checkout_request,
                background_tasks=background_tasks
            )
        
        assert exc_info.value.status_code == 400
        assert "Insufficient inventory" in str(exc_info.value.detail)

    @patch('services.orders.PaymentService')
    @patch('services.orders.CartService')
    async def test_checkout_idempotency(
        self,
        mock_cart_service_class,
        mock_payment_service_class,
        db_session,
        user_data,
        cart_with_items,
        checkout_request,
        product_variant, # Added fixture
        mock_inventory, # Added fixture
        mock_address,
        mock_shipping_method,
        mock_payment_method
    ):
        """Test checkout idempotency - duplicate requests should return same order"""
        
        user_id = user_data["id"]
        idempotency_key = "test_idempotency_key_123"
        
        # Create existing order
        existing_order = Order(
            id=uuid7(),
            user_id=user_id,
            order_number="ORD-123456",
            order_status="confirmed",
            payment_status="paid",
            total_amount=Decimal("59.98"), # Use Decimal consistent with price
            idempotency_key=idempotency_key,
            created_at=datetime.utcnow() # Add created_at
        )
        existing_order.shipping_address = mock_address
        existing_order.shipping_method = mock_shipping_method
        existing_order.payment_method = mock_payment_method
        existing_order.items = [] # Initialize items as empty list
        
        # Mock database queries dynamically
        def mock_db_execute_side_effect(query):
            query_str = str(query).lower()
            if "FROM address" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_address
                return mock_result
            elif "FROM shipping_method" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_shipping_method
                return mock_result
            elif "FROM payment_method" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_payment_method
                return mock_result
            elif "FROM order" in query_str and "idempotency_key" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = existing_order # Return existing order for this flow
                return mock_result
            elif "FROM product_variants" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = product_variant
                return mock_result
            elif "FROM inventory" in query_str:
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_inventory
                return mock_result
            
            # Default fallback for unmocked queries
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_result.scalars.return_value.all.return_value = []
            return mock_result

        db_session.execute.side_effect = mock_db_execute_side_effect
        
        # Create order service
        order_service = OrderService(db_session)
        background_tasks = AsyncMock(spec=BackgroundTasks)
        
        # Execute checkout with idempotency key
        result = await order_service.place_order_with_idempotency(
            user_id=user_id,
            request=checkout_request,
            background_tasks=background_tasks,
            idempotency_key=idempotency_key
        )
        
        # Verify existing order was returned
        assert result.id == str(existing_order.id)
        assert result.order_number == existing_order.order_number
        
        # Verify no new processing occurred
        mock_cart_service_class.assert_not_called()
        mock_payment_service_class.assert_not_called()