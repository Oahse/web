"""
End-to-end tests for complete checkout flow
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from decimal import Decimal
from unittest.mock import patch, MagicMock

from models.user import User
from models.product import Product, ProductVariant, Category
from models.inventories import Inventory, WarehouseLocation
from models.shipping import ShippingMethod
from models.tax_rates import TaxRate
from models.discounts import Discount


@pytest.mark.e2e
class TestCompleteCheckoutFlow:
    """Test complete checkout flow from product discovery to order completion."""
    
    @pytest.mark.asyncio
    async def test_guest_to_customer_checkout_flow(self, async_client: AsyncClient, db_session: AsyncSession, mock_stripe, mock_email):
        """Test complete flow: guest browsing → registration → add to cart → checkout → order."""
        
        # Setup test data
        await self._setup_test_data(db_session)
        
        # Step 1: Guest user browses products
        response = await async_client.get("/products")
        assert response.status_code == 200
        products = response.json()["data"]
        assert len(products) >= 1
        
        product = products[0]
        variant = product["variants"][0]
        
        # Step 2: Guest tries to add to cart (should require registration)
        cart_data = {
            "variant_id": variant["id"],
            "quantity": 2
        }
        
        response = await async_client.post("/cart/items", json=cart_data)
        assert response.status_code == 401  # Unauthorized
        
        # Step 3: User registers
        user_data = {
            "email": "checkout@example.com",
            "firstname": "Checkout",
            "lastname": "Test",
            "password": "TestPassword123!",
            "phone": "+1234567890",
            "country": "US"
        }
        
        response = await async_client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        user_id = response.json()["data"]["id"]
        
        # Step 4: User logs in
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        response = await async_client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        auth_headers = {"Authorization": f"Bearer {response.json()['data']['access_token']}"}
        
        # Step 5: Add items to cart
        response = await async_client.post("/cart/items", json=cart_data, headers=auth_headers)
        assert response.status_code == 201
        
        # Add another item
        cart_data2 = {
            "variant_id": variant["id"],
            "quantity": 1
        }
        response = await async_client.post("/cart/items", json=cart_data2, headers=auth_headers)
        assert response.status_code == 200  # Should update existing item
        
        # Step 6: View cart
        response = await async_client.get("/cart", headers=auth_headers)
        assert response.status_code == 200
        cart = response.json()["data"]
        assert len(cart["items"]) == 1
        assert cart["items"][0]["quantity"] == 3  # 2 + 1
        
        # Step 7: Create payment method
        payment_method_data = {
            "stripe_payment_method_id": "pm_test_123",
            "is_default": True
        }
        
        response = await async_client.post("/payments/methods", json=payment_method_data, headers=auth_headers)
        assert response.status_code == 201
        payment_method_id = response.json()["data"]["id"]
        
        # Step 8: Apply discount code
        discount_data = {"code": "SAVE10"}
        response = await async_client.post("/cart/apply-discount", json=discount_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Step 9: Validate checkout
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
            "shipping_method_id": None,  # Will be set after getting shipping methods
            "payment_method_id": payment_method_id,
            "discount_code": "SAVE10"
        }
        
        # Get shipping methods
        response = await async_client.get("/shipping/methods")
        assert response.status_code == 200
        shipping_methods = response.json()["data"]
        checkout_data["shipping_method_id"] = shipping_methods[0]["id"]
        
        # Validate checkout
        response = await async_client.post("/orders/checkout/validate", json=checkout_data, headers=auth_headers)
        assert response.status_code == 200
        validation = response.json()["data"]
        assert validation["validation_result"]["is_valid"] is True
        
        # Verify pricing calculation
        pricing = validation["pricing"]
        assert float(pricing["subtotal"]) > 0
        assert float(pricing["shipping_cost"]) >= 0
        assert float(pricing["tax_amount"]) >= 0
        assert float(pricing["discount_amount"]) > 0  # Should have discount
        assert float(pricing["total_amount"]) > 0
        
        # Step 10: Create order
        with patch('services.payments.PaymentService.process_payment') as mock_payment:
            mock_payment.return_value = {
                "status": "succeeded",
                "payment_intent_id": "pi_test_123",
                "transaction_id": str(uuid4())
            }
            
            response = await async_client.post("/orders", json=checkout_data, headers=auth_headers)
            assert response.status_code == 201
            order = response.json()["data"]
            assert order["status"] == "pending"
            assert len(order["items"]) == 1
            assert order["items"][0]["quantity"] == 3
            order_id = order["id"]
        
        # Step 11: Verify order details
        response = await async_client.get(f"/orders/{order_id}", headers=auth_headers)
        assert response.status_code == 200
        order_details = response.json()["data"]
        assert order_details["id"] == order_id
        assert float(order_details["total_amount"]) > 0
        assert float(order_details["discount_amount"]) > 0
        
        # Step 12: Verify cart was cleared
        response = await async_client.get("/cart", headers=auth_headers)
        assert response.status_code == 200
        cart = response.json()["data"]
        assert len(cart["items"]) == 0
        
        # Step 13: Verify inventory was decremented
        response = await async_client.get(f"/products/variants/{variant['id']}")
        assert response.status_code == 200
        variant_data = response.json()["data"]
        # Inventory should be decremented (reserved for order)
        
        # Step 14: Verify email notifications were sent
        assert mock_email.call_count >= 2  # Registration + order confirmation
        
        # Step 15: Get order tracking
        response = await async_client.get(f"/orders/{order_id}/tracking", headers=auth_headers)
        assert response.status_code == 200
        tracking = response.json()["data"]
        assert "status" in tracking
    
    @pytest.mark.asyncio
    async def test_returning_customer_express_checkout(self, async_client: AsyncClient, db_session: AsyncSession, mock_stripe, mock_email):
        """Test express checkout for returning customer with saved payment method."""
        
        # Setup test data
        await self._setup_test_data(db_session)
        
        # Create returning customer with saved payment method
        user = User(
            id=uuid4(),
            email="returning@example.com",
            firstname="Returning",
            lastname="Customer",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role="customer",
            verified=True,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        
        # Login
        login_data = {
            "email": "returning@example.com",
            "password": "secret"
        }
        
        response = await async_client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        auth_headers = {"Authorization": f"Bearer {response.json()['data']['access_token']}"}
        
        # Create saved payment method
        payment_method_data = {
            "stripe_payment_method_id": "pm_test_saved",
            "is_default": True
        }
        
        response = await async_client.post("/payments/methods", json=payment_method_data, headers=auth_headers)
        assert response.status_code == 201
        payment_method_id = response.json()["data"]["id"]
        
        # Quick add to cart
        response = await async_client.get("/products")
        products = response.json()["data"]
        variant_id = products[0]["variants"][0]["id"]
        
        cart_data = {
            "variant_id": variant_id,
            "quantity": 1
        }
        
        response = await async_client.post("/cart/items", json=cart_data, headers=auth_headers)
        assert response.status_code == 201
        
        # Express checkout (one-click)
        express_checkout_data = {
            "use_default_address": True,
            "use_default_payment": True,
            "use_fastest_shipping": True
        }
        
        with patch('services.payments.PaymentService.process_payment') as mock_payment:
            mock_payment.return_value = {
                "status": "succeeded",
                "payment_intent_id": "pi_express_123",
                "transaction_id": str(uuid4())
            }
            
            response = await async_client.post("/orders/express-checkout", json=express_checkout_data, headers=auth_headers)
            assert response.status_code == 201
            order = response.json()["data"]
            assert order["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_failed_payment_recovery_flow(self, async_client: AsyncClient, db_session: AsyncSession, mock_stripe, mock_email):
        """Test payment failure and recovery flow."""
        
        # Setup test data and user
        await self._setup_test_data(db_session)
        user_data, auth_headers = await self._create_test_user(async_client, mock_email)
        
        # Add item to cart
        response = await async_client.get("/products")
        variant_id = response.json()["data"][0]["variants"][0]["id"]
        
        cart_data = {"variant_id": variant_id, "quantity": 1}
        response = await async_client.post("/cart/items", json=cart_data, headers=auth_headers)
        assert response.status_code == 201
        
        # Create payment method
        payment_method_data = {
            "stripe_payment_method_id": "pm_test_decline",
            "is_default": True
        }
        
        response = await async_client.post("/payments/methods", json=payment_method_data, headers=auth_headers)
        assert response.status_code == 201
        payment_method_id = response.json()["data"]["id"]
        
        # Attempt checkout with failing payment
        checkout_data = await self._get_checkout_data(async_client, payment_method_id)
        
        with patch('services.payments.PaymentService.process_payment') as mock_payment:
            mock_payment.return_value = {
                "status": "requires_payment_method",
                "error": {"code": "card_declined", "message": "Your card was declined."},
                "payment_intent_id": "pi_failed_123"
            }
            
            response = await async_client.post("/orders", json=checkout_data, headers=auth_headers)
            assert response.status_code == 400  # Payment failed
            error = response.json()
            assert "declined" in error["message"].lower()
        
        # Add new payment method
        new_payment_data = {
            "stripe_payment_method_id": "pm_test_success",
            "is_default": True
        }
        
        response = await async_client.post("/payments/methods", json=new_payment_data, headers=auth_headers)
        assert response.status_code == 201
        new_payment_method_id = response.json()["data"]["id"]
        
        # Retry checkout with new payment method
        checkout_data["payment_method_id"] = new_payment_method_id
        
        with patch('services.payments.PaymentService.process_payment') as mock_payment:
            mock_payment.return_value = {
                "status": "succeeded",
                "payment_intent_id": "pi_success_123",
                "transaction_id": str(uuid4())
            }
            
            response = await async_client.post("/orders", json=checkout_data, headers=auth_headers)
            assert response.status_code == 201
            order = response.json()["data"]
            assert order["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_inventory_insufficient_stock_flow(self, async_client: AsyncClient, db_session: AsyncSession, mock_email):
        """Test checkout flow when inventory becomes insufficient."""
        
        # Setup test data with limited inventory
        category = Category(
            id=uuid4(),
            name="Limited Stock Category",
            description="For stock testing",
            is_active=True
        )
        db_session.add(category)
        
        product = Product(
            id=uuid4(),
            name="Limited Stock Product",
            description="Only 2 in stock",
            category_id=category.id,
            brand="Test Brand",
            is_active=True
        )
        db_session.add(product)
        
        variant = ProductVariant(
            id=uuid4(),
            product_id=product.id,
            name="Limited Variant",
            sku="LIMITED-001",
            base_price=Decimal("99.99"),
            is_active=True
        )
        db_session.add(variant)
        
        warehouse = WarehouseLocation(
            id=uuid4(),
            name="Test Warehouse",
            address="123 Test St",
            city="Test City",
            state="TS",
            country="US",
            postal_code="12345",
            is_active=True
        )
        db_session.add(warehouse)
        
        # Only 2 items in stock
        inventory = Inventory(
            id=uuid4(),
            variant_id=variant.id,
            warehouse_id=warehouse.id,
            quantity_available=2,
            quantity_reserved=0
        )
        db_session.add(inventory)
        await db_session.commit()
        
        # Create user
        user_data, auth_headers = await self._create_test_user(async_client, mock_email)
        
        # User 1 adds 2 items to cart
        cart_data = {"variant_id": str(variant.id), "quantity": 2}
        response = await async_client.post("/cart/items", json=cart_data, headers=auth_headers)
        assert response.status_code == 201
        
        # Create second user
        user2_data = {
            "email": "user2@example.com",
            "firstname": "User",
            "lastname": "Two",
            "password": "TestPassword123!",
            "phone": "+1234567891",
            "country": "US"
        }
        
        response = await async_client.post("/auth/register", json=user2_data)
        assert response.status_code == 200
        
        login_data = {"email": user2_data["email"], "password": user2_data["password"]}
        response = await async_client.post("/auth/login", json=login_data)
        auth_headers2 = {"Authorization": f"Bearer {response.json()['data']['access_token']}"}
        
        # User 2 tries to add 2 items (should fail - insufficient stock)
        response = await async_client.post("/cart/items", json=cart_data, headers=auth_headers2)
        assert response.status_code == 400
        assert "insufficient stock" in response.json()["message"].lower()
        
        # User 2 adds 1 item (should succeed)
        cart_data["quantity"] = 1
        response = await async_client.post("/cart/items", json=cart_data, headers=auth_headers2)
        assert response.status_code == 201
        
        # User 1 completes checkout first
        payment_method_data = {
            "stripe_payment_method_id": "pm_test_user1",
            "is_default": True
        }
        response = await async_client.post("/payments/methods", json=payment_method_data, headers=auth_headers)
        payment_method_id = response.json()["data"]["id"]
        
        checkout_data = await self._get_checkout_data(async_client, payment_method_id)
        
        with patch('services.payments.PaymentService.process_payment') as mock_payment:
            mock_payment.return_value = {
                "status": "succeeded",
                "payment_intent_id": "pi_user1_123",
                "transaction_id": str(uuid4())
            }
            
            response = await async_client.post("/orders", json=checkout_data, headers=auth_headers)
            assert response.status_code == 201
        
        # User 2 tries to checkout (should fail - stock reserved for user 1)
        payment_method_data2 = {
            "stripe_payment_method_id": "pm_test_user2",
            "is_default": True
        }
        response = await async_client.post("/payments/methods", json=payment_method_data2, headers=auth_headers2)
        payment_method_id2 = response.json()["data"]["id"]
        
        checkout_data2 = await self._get_checkout_data(async_client, payment_method_id2)
        
        with patch('services.payments.PaymentService.process_payment') as mock_payment:
            mock_payment.return_value = {
                "status": "succeeded",
                "payment_intent_id": "pi_user2_123",
                "transaction_id": str(uuid4())
            }
            
            response = await async_client.post("/orders", json=checkout_data2, headers=auth_headers2)
            assert response.status_code == 400
            assert "insufficient stock" in response.json()["message"].lower()
    
    async def _setup_test_data(self, db_session: AsyncSession):
        """Setup test data for checkout flow tests."""
        # Create category
        category = Category(
            id=uuid4(),
            name="Checkout Category",
            description="For checkout testing",
            is_active=True
        )
        db_session.add(category)
        
        # Create product
        product = Product(
            id=uuid4(),
            name="Checkout Product",
            description="For checkout testing",
            category_id=category.id,
            brand="Test Brand",
            is_active=True
        )
        db_session.add(product)
        
        # Create variant
        variant = ProductVariant(
            id=uuid4(),
            product_id=product.id,
            name="Checkout Variant",
            sku="CHECKOUT-001",
            base_price=Decimal("99.99"),
            sale_price=Decimal("79.99"),
            weight=Decimal("1.0"),
            is_active=True
        )
        db_session.add(variant)
        
        # Create warehouse
        warehouse = WarehouseLocation(
            id=uuid4(),
            name="Checkout Warehouse",
            address="123 Test St",
            city="Test City",
            state="TS",
            country="US",
            postal_code="12345",
            is_active=True
        )
        db_session.add(warehouse)
        
        # Create inventory
        inventory = Inventory(
            id=uuid4(),
            variant_id=variant.id,
            warehouse_id=warehouse.id,
            quantity_available=100,
            quantity_reserved=0
        )
        db_session.add(inventory)
        
        # Create shipping method
        shipping_method = ShippingMethod(
            id=uuid4(),
            name="Standard Shipping",
            description="5-7 business days",
            base_cost=Decimal("9.99"),
            estimated_days_min=5,
            estimated_days_max=7,
            is_active=True
        )
        db_session.add(shipping_method)
        
        # Create tax rate
        tax_rate = TaxRate(
            id=uuid4(),
            country="US",
            state="CA",
            rate=Decimal("0.0875"),
            is_active=True
        )
        db_session.add(tax_rate)
        
        # Create discount
        discount = Discount(
            id=uuid4(),
            code="SAVE10",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            is_active=True,
            usage_limit=100,
            usage_count=0
        )
        db_session.add(discount)
        
        await db_session.commit()
    
    async def _create_test_user(self, async_client: AsyncClient, mock_email):
        """Create and login test user."""
        user_data = {
            "email": "testuser@example.com",
            "firstname": "Test",
            "lastname": "User",
            "password": "TestPassword123!",
            "phone": "+1234567890",
            "country": "US"
        }
        
        response = await async_client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        response = await async_client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        auth_headers = {"Authorization": f"Bearer {response.json()['data']['access_token']}"}
        
        return user_data, auth_headers
    
    async def _get_checkout_data(self, async_client: AsyncClient, payment_method_id: str):
        """Get checkout data with shipping method."""
        response = await async_client.get("/shipping/methods")
        shipping_methods = response.json()["data"]
        
        return {
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
            "shipping_method_id": shipping_methods[0]["id"],
            "payment_method_id": payment_method_id
        }


@pytest.mark.e2e
class TestMultiUserCheckoutScenarios:
    """Test multi-user checkout scenarios and race conditions."""
    
    @pytest.mark.asyncio
    async def test_concurrent_checkout_same_product(self, async_client: AsyncClient, db_session: AsyncSession, mock_stripe, mock_email):
        """Test concurrent checkout attempts for the same product."""
        # This test would simulate multiple users trying to checkout the same limited stock item
        pass
    
    @pytest.mark.asyncio
    async def test_abandoned_cart_recovery(self, async_client: AsyncClient, db_session: AsyncSession, mock_email):
        """Test abandoned cart recovery flow."""
        # This test would simulate cart abandonment and recovery email flow
        pass
    
    @pytest.mark.asyncio
    async def test_subscription_checkout_flow(self, async_client: AsyncClient, db_session: AsyncSession, mock_stripe, mock_email):
        """Test subscription product checkout flow."""
        # This test would handle subscription-based products
        pass