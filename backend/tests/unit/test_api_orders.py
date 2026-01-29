"""
Tests for orders API endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from decimal import Decimal
from unittest.mock import patch

from models.orders import Order, OrderItem, OrderStatus
from models.cart import Cart, CartItem
from models.user import User, Address
from models.product import ProductVariant
from models.shipping import ShippingMethod
from models.payments import PaymentMethod
from models.tax_rates import TaxRate


class TestOrdersAPI:
    """Test orders API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_order_success(self, async_client: AsyncClient, auth_headers: dict, test_cart: Cart, test_cart_item: CartItem, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod, test_tax_rate: TaxRate, mock_stripe):
        """Test successful order creation."""
        order_data = {
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "billing_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "shipping_method_id": str(test_shipping_method.id),
            "payment_method_id": str(test_payment_method.id),
            "discount_code": None
        }
        
        response = await async_client.post("/orders", json=order_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert data["data"]["status"] == OrderStatus.PENDING
        assert len(data["data"]["items"]) >= 1
    
    @pytest.mark.asyncio
    async def test_create_order_empty_cart(self, async_client: AsyncClient, auth_headers: dict, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod):
        """Test order creation with empty cart."""
        order_data = {
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "billing_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "shipping_method_id": str(test_shipping_method.id),
            "payment_method_id": str(test_payment_method.id)
        }
        
        response = await async_client.post("/orders", json=order_data, headers=auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "empty cart" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_create_order_invalid_shipping_method(self, async_client: AsyncClient, auth_headers: dict, test_cart: Cart, test_cart_item: CartItem, test_payment_method: PaymentMethod):
        """Test order creation with invalid shipping method."""
        order_data = {
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "billing_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "shipping_method_id": str(uuid4()),  # Invalid ID
            "payment_method_id": str(test_payment_method.id)
        }
        
        response = await async_client.post("/orders", json=order_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "shipping method" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_create_order_invalid_payment_method(self, async_client: AsyncClient, auth_headers: dict, test_cart: Cart, test_cart_item: CartItem, test_shipping_method: ShippingMethod):
        """Test order creation with invalid payment method."""
        order_data = {
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "billing_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "shipping_method_id": str(test_shipping_method.id),
            "payment_method_id": str(uuid4())  # Invalid ID
        }
        
        response = await async_client.post("/orders", json=order_data, headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "payment method" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_get_orders_success(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User):
        """Test getting user's orders."""
        # Create test order
        order = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.CONFIRMED,
            subtotal=Decimal("99.99"),
            shipping_cost=Decimal("9.99"),
            tax_amount=Decimal("8.75"),
            total_amount=Decimal("118.73"),
            currency="USD"
        )
        db_session.add(order)
        await db_session.commit()
        
        response = await async_client.get("/orders", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        
        order_data = data["data"][0]
        assert order_data["id"] == str(order.id)
        assert order_data["status"] == OrderStatus.CONFIRMED
    
    @pytest.mark.asyncio
    async def test_get_orders_with_pagination(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting orders with pagination."""
        response = await async_client.get("/orders?page=1&limit=10", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pagination" in data
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["limit"] == 10
    
    @pytest.mark.asyncio
    async def test_get_order_by_id_success(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User):
        """Test getting order by ID."""
        # Create test order
        order = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.CONFIRMED,
            subtotal=Decimal("99.99"),
            shipping_cost=Decimal("9.99"),
            tax_amount=Decimal("8.75"),
            total_amount=Decimal("118.73"),
            currency="USD"
        )
        db_session.add(order)
        await db_session.commit()
        
        response = await async_client.get(f"/orders/{order.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == str(order.id)
        assert data["data"]["status"] == OrderStatus.CONFIRMED
    
    @pytest.mark.asyncio
    async def test_get_order_by_id_not_found(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting nonexistent order."""
        fake_id = uuid4()
        response = await async_client.get(f"/orders/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_get_order_unauthorized(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
        """Test getting another user's order."""
        # Create another user and their order
        other_user = User(
            id=uuid4(),
            email="other@example.com",
            firstname="Other",
            lastname="User",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role="customer",
            verified=True,
            is_active=True
        )
        db_session.add(other_user)
        
        other_order = Order(
            id=uuid4(),
            user_id=other_user.id,
            status=OrderStatus.CONFIRMED,
            subtotal=Decimal("99.99"),
            shipping_cost=Decimal("9.99"),
            tax_amount=Decimal("8.75"),
            total_amount=Decimal("118.73"),
            currency="USD"
        )
        db_session.add(other_order)
        await db_session.commit()
        
        response = await async_client.get(f"/orders/{other_order.id}", headers=auth_headers)
        
        assert response.status_code == 404  # Should not find order (security)
    
    @pytest.mark.asyncio
    async def test_cancel_order_success(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User):
        """Test canceling order."""
        # Create cancelable order
        order = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.CONFIRMED,
            subtotal=Decimal("99.99"),
            shipping_cost=Decimal("9.99"),
            tax_amount=Decimal("8.75"),
            total_amount=Decimal("118.73"),
            currency="USD"
        )
        db_session.add(order)
        await db_session.commit()
        
        response = await async_client.put(f"/orders/{order.id}/cancel", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == OrderStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_cancel_order_already_shipped(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User):
        """Test canceling already shipped order."""
        # Create shipped order
        order = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.SHIPPED,
            subtotal=Decimal("99.99"),
            shipping_cost=Decimal("9.99"),
            tax_amount=Decimal("8.75"),
            total_amount=Decimal("118.73"),
            currency="USD"
        )
        db_session.add(order)
        await db_session.commit()
        
        response = await async_client.put(f"/orders/{order.id}/cancel", headers=auth_headers)
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "cannot be cancelled" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_reorder_success(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User, test_variant: ProductVariant, test_inventory):
        """Test reordering from previous order."""
        # Create order with items
        order = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.DELIVERED,
            subtotal=Decimal("99.99"),
            shipping_cost=Decimal("9.99"),
            tax_amount=Decimal("8.75"),
            total_amount=Decimal("118.73"),
            currency="USD"
        )
        db_session.add(order)
        
        order_item = OrderItem(
            id=uuid4(),
            order_id=order.id,
            variant_id=test_variant.id,
            quantity=2,
            unit_price=Decimal("49.99"),
            total_price=Decimal("99.98")
        )
        db_session.add(order_item)
        await db_session.commit()
        
        response = await async_client.post(f"/orders/{order.id}/reorder", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "added to cart" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_get_order_tracking(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User):
        """Test getting order tracking information."""
        # Create order with tracking
        order = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.SHIPPED,
            subtotal=Decimal("99.99"),
            shipping_cost=Decimal("9.99"),
            tax_amount=Decimal("8.75"),
            total_amount=Decimal("118.73"),
            currency="USD",
            tracking_number="TRACK123456"
        )
        db_session.add(order)
        await db_session.commit()
        
        response = await async_client.get(f"/orders/{order.id}/tracking", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tracking_number" in data["data"]
        assert data["data"]["tracking_number"] == "TRACK123456"
    
    @pytest.mark.asyncio
    async def test_get_order_invoice(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User):
        """Test getting order invoice."""
        # Create order
        order = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.DELIVERED,
            subtotal=Decimal("99.99"),
            shipping_cost=Decimal("9.99"),
            tax_amount=Decimal("8.75"),
            total_amount=Decimal("118.73"),
            currency="USD"
        )
        db_session.add(order)
        await db_session.commit()
        
        response = await async_client.get(f"/orders/{order.id}/invoice", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "invoice" in data["data"]


class TestCheckoutValidation:
    """Test checkout validation endpoints."""
    
    @pytest.mark.asyncio
    async def test_validate_checkout_success(self, async_client: AsyncClient, auth_headers: dict, test_cart: Cart, test_cart_item: CartItem, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod, test_tax_rate: TaxRate):
        """Test successful checkout validation."""
        checkout_data = {
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "billing_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "shipping_method_id": str(test_shipping_method.id),
            "payment_method_id": str(test_payment_method.id)
        }
        
        response = await async_client.post("/orders/checkout/validate", json=checkout_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "validation_result" in data["data"]
        assert data["data"]["validation_result"]["is_valid"] is True
        assert "pricing" in data["data"]
    
    @pytest.mark.asyncio
    async def test_validate_checkout_empty_cart(self, async_client: AsyncClient, auth_headers: dict, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod):
        """Test checkout validation with empty cart."""
        checkout_data = {
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "billing_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "shipping_method_id": str(test_shipping_method.id),
            "payment_method_id": str(test_payment_method.id)
        }
        
        response = await async_client.post("/orders/checkout/validate", json=checkout_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["validation_result"]["is_valid"] is False
        assert "empty cart" in str(data["data"]["validation_result"]["issues"]).lower()
    
    @pytest.mark.asyncio
    async def test_validate_checkout_insufficient_stock(self, async_client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_cart: Cart, test_variant: ProductVariant, test_inventory, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod):
        """Test checkout validation with insufficient stock."""
        # Create cart item with quantity exceeding stock
        cart_item = CartItem(
            id=uuid4(),
            cart_id=test_cart.id,
            variant_id=test_variant.id,
            quantity=test_inventory.quantity_available + 10
        )
        db_session.add(cart_item)
        await db_session.commit()
        
        checkout_data = {
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "billing_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "shipping_method_id": str(test_shipping_method.id),
            "payment_method_id": str(test_payment_method.id)
        }
        
        response = await async_client.post("/orders/checkout/validate", json=checkout_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["validation_result"]["is_valid"] is False
        assert len(data["data"]["validation_result"]["issues"]) > 0


class TestOrdersValidation:
    """Test order validation and edge cases."""
    
    @pytest.mark.asyncio
    async def test_create_order_missing_address(self, async_client: AsyncClient, auth_headers: dict, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod):
        """Test order creation with missing address."""
        order_data = {
            "shipping_method_id": str(test_shipping_method.id),
            "payment_method_id": str(test_payment_method.id)
            # Missing addresses
        }
        
        response = await async_client.post("/orders", json=order_data, headers=auth_headers)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_order_invalid_address(self, async_client: AsyncClient, auth_headers: dict, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod):
        """Test order creation with invalid address."""
        order_data = {
            "shipping_address": {
                "street": "",  # Empty street
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "billing_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "shipping_method_id": str(test_shipping_method.id),
            "payment_method_id": str(test_payment_method.id)
        }
        
        response = await async_client.post("/orders", json=order_data, headers=auth_headers)
        
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_create_order_unauthorized(self, async_client: AsyncClient, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod):
        """Test order creation without authentication."""
        order_data = {
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "billing_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "shipping_method_id": str(test_shipping_method.id),
            "payment_method_id": str(test_payment_method.id)
        }
        
        response = await async_client.post("/orders", json=order_data)
        
        assert response.status_code == 401


class TestOrdersPricing:
    """Test order pricing calculations."""
    
    @pytest.mark.asyncio
    async def test_order_pricing_calculation(self, async_client: AsyncClient, auth_headers: dict, test_cart: Cart, test_cart_item: CartItem, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod, test_tax_rate: TaxRate, mock_stripe):
        """Test order pricing calculation accuracy."""
        order_data = {
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "billing_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "shipping_method_id": str(test_shipping_method.id),
            "payment_method_id": str(test_payment_method.id)
        }
        
        response = await async_client.post("/orders", json=order_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        
        # Verify pricing components
        order_data = data["data"]
        assert "subtotal" in order_data
        assert "shipping_cost" in order_data
        assert "tax_amount" in order_data
        assert "total_amount" in order_data
        
        # Basic calculation check
        subtotal = float(order_data["subtotal"])
        shipping = float(order_data["shipping_cost"])
        tax = float(order_data["tax_amount"])
        total = float(order_data["total_amount"])
        
        assert total == subtotal + shipping + tax
    
    @pytest.mark.asyncio
    async def test_order_with_discount(self, async_client: AsyncClient, auth_headers: dict, test_cart: Cart, test_cart_item: CartItem, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod, test_tax_rate: TaxRate, db_session: AsyncSession, mock_stripe):
        """Test order creation with discount code."""
        # Create discount code
        from models.discounts import Discount
        discount = Discount(
            id=uuid4(),
            code="TEST10",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            is_active=True,
            usage_limit=100,
            usage_count=0
        )
        db_session.add(discount)
        await db_session.commit()
        
        order_data = {
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "billing_address": {
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            "shipping_method_id": str(test_shipping_method.id),
            "payment_method_id": str(test_payment_method.id),
            "discount_code": "TEST10"
        }
        
        response = await async_client.post("/orders", json=order_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        
        # Should have discount applied
        order_data = data["data"]
        if "discount_amount" in order_data:
            assert float(order_data["discount_amount"]) > 0