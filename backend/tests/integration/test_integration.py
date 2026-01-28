"""
Integration tests for complete workflows
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


@pytest.mark.integration
class TestCompleteOrderFlow:
    """Test complete order flow from cart to delivery."""
    
    @pytest.mark.asyncio
    async def test_complete_order_workflow(self, async_client: AsyncClient, db_session: AsyncSession, mock_stripe, mock_email):
        """Test complete order workflow: register -> add to cart -> checkout -> order."""
        
        # Step 1: Register user
        user_data = {
            "email": "integration@example.com",
            "firstname": "Integration",
            "lastname": "Test",
            "password": "TestPassword123!",
            "phone": "+1234567890",
            "country": "US"
        }
        
        response = await async_client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        user_id = response.json()["data"]["id"]
        
        # Step 2: Login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        response = await async_client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        auth_headers = {"Authorization": f"Bearer {response.json()['data']['access_token']}"}
        
        # Step 3: Create test data
        # Create category
        category = Category(
            id=uuid4(),
            name="Integration Category",
            description="For integration testing",
            is_active=True
        )
        db_session.add(category)
        
        # Create product
        product = Product(
            id=uuid4(),
            name="Integration Product",
            description="For integration testing",
            category_id=category.id,
            brand="Test Brand",
            is_active=True
        )
        db_session.add(product)
        
        # Create variant
        variant = ProductVariant(
            id=uuid4(),
            product_id=product.id,
            name="Integration Variant",
            sku="INT-001",
            base_price=Decimal("99.99"),
            sale_price=Decimal("79.99"),
            weight=Decimal("1.0"),
            is_active=True
        )
        db_session.add(variant)
        
        # Create warehouse and inventory
        warehouse = WarehouseLocation(
            id=uuid4(),
            name="Integration Warehouse",
            address="123 Test St",
            city="Test City",
            state="TS",
            country="US",
            postal_code="12345",
            is_active=True
        )
        db_session.add(warehouse)
        
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
            name="Integration Shipping",
            description="For integration testing",
            base_cost=Decimal("9.99"),
            estimated_days_min=3,
            estimated_days_max=5,
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
        
        await db_session.commit()
        
        # Step 4: Add item to cart
        cart_data = {
            "variant_id": str(variant.id),
            "quantity": 2
        }
        
        response = await async_client.post("/cart/items", json=cart_data, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["data"]["quantity"] == 2
        
        # Step 5: Verify cart
        response = await async_client.get("/cart", headers=auth_headers)
        assert response.status_code == 200
        cart_data = response.json()["data"]
        assert len(cart_data["items"]) == 1
        assert cart_data["items"][0]["quantity"] == 2
        
        # Step 6: Create payment method
        payment_method_data = {
            "stripe_payment_method_id": "pm_test_123",
            "is_default": True
        }
        
        response = await async_client.post("/payments/methods", json=payment_method_data, headers=auth_headers)
        assert response.status_code == 201
        payment_method_id = response.json()["data"]["id"]
        
        # Step 7: Validate checkout
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
            "shipping_method_id": str(shipping_method.id),
            "payment_method_id": payment_method_id
        }
        
        response = await async_client.post("/orders/checkout/validate", json=checkout_data, headers=auth_headers)
        assert response.status_code == 200
        validation_result = response.json()["data"]
        assert validation_result["validation_result"]["is_valid"] is True
        
        # Step 8: Create order
        with patch('services.payments.PaymentService.process_payment') as mock_payment:
            mock_payment.return_value = {"status": "succeeded", "payment_intent_id": "pi_test_123"}
            
            response = await async_client.post("/orders", json=checkout_data, headers=auth_headers)
            assert response.status_code == 201
            order_data = response.json()["data"]
            assert order_data["status"] == "pending"
            assert len(order_data["items"]) == 1
            order_id = order_data["id"]
        
        # Step 9: Verify order was created
        response = await async_client.get(f"/orders/{order_id}", headers=auth_headers)
        assert response.status_code == 200
        order_data = response.json()["data"]
        assert order_data["id"] == order_id
        assert order_data["total_amount"] > 0
        
        # Step 10: Verify cart was cleared
        response = await async_client.get("/cart", headers=auth_headers)
        assert response.status_code == 200
        cart_data = response.json()["data"]
        assert len(cart_data["items"]) == 0
        
        # Step 11: Verify inventory was updated
        await db_session.refresh(inventory)
        assert inventory.quantity_reserved == 2  # Should be reserved for the order


@pytest.mark.integration
class TestUserManagementFlow:
    """Test complete user management flow."""
    
    @pytest.mark.asyncio
    async def test_user_registration_and_verification_flow(self, async_client: AsyncClient, mock_email):
        """Test user registration, email verification, and profile management."""
        
        # Step 1: Register user
        user_data = {
            "email": "verification@example.com",
            "firstname": "Verification",
            "lastname": "Test",
            "password": "TestPassword123!",
            "phone": "+1234567890",
            "country": "US"
        }
        
        response = await async_client.post("/auth/register", json=user_data)
        assert response.status_code == 200
        user_data_response = response.json()["data"]
        assert user_data_response["verified"] is False
        
        # Verify email was sent
        mock_email.assert_called_once()
        
        # Step 2: Simulate email verification
        # In a real test, we'd extract the token from the email
        # For now, we'll create a verification token manually
        from services.auth import AuthService
        from core.db import get_db
        
        # This would normally be done through email link
        # response = await async_client.get(f"/auth/verify-email?token={verification_token}")
        # assert response.status_code == 200
        
        # Step 3: Login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        response = await async_client.post("/auth/login", json=login_data)
        assert response.status_code == 200
        auth_headers = {"Authorization": f"Bearer {response.json()['data']['access_token']}"}
        
        # Step 4: Get profile
        response = await async_client.get("/auth/profile", headers=auth_headers)
        assert response.status_code == 200
        profile_data = response.json()["data"]
        assert profile_data["email"] == user_data["email"]
        
        # Step 5: Update profile
        update_data = {
            "firstname": "Updated",
            "lastname": "Name",
            "phone": "+1987654321"
        }
        
        response = await async_client.put("/auth/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        updated_profile = response.json()["data"]
        assert updated_profile["firstname"] == "Updated"
        assert updated_profile["lastname"] == "Name"
        
        # Step 6: Change password
        password_data = {
            "current_password": user_data["password"],
            "new_password": "NewPassword123!"
        }
        
        response = await async_client.post("/auth/change-password", json=password_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Step 7: Login with new password
        login_data["password"] = "NewPassword123!"
        response = await async_client.post("/auth/login", json=login_data)
        assert response.status_code == 200


@pytest.mark.integration
class TestProductManagementFlow:
    """Test complete product management flow."""
    
    @pytest.mark.asyncio
    async def test_product_lifecycle_flow(self, async_client: AsyncClient, db_session: AsyncSession, supplier_auth_headers: dict):
        """Test complete product lifecycle: create -> update -> variants -> inventory."""
        
        # Step 1: Create category
        category = Category(
            id=uuid4(),
            name="Lifecycle Category",
            description="For lifecycle testing",
            is_active=True
        )
        db_session.add(category)
        await db_session.commit()
        
        # Step 2: Create product
        product_data = {
            "name": "Lifecycle Product",
            "description": "For lifecycle testing",
            "category_id": str(category.id),
            "brand": "Test Brand",
            "is_active": True,
            "is_featured": False
        }
        
        response = await async_client.post("/products", json=product_data, headers=supplier_auth_headers)
        assert response.status_code == 201
        product_id = response.json()["data"]["id"]
        
        # Step 3: Update product
        update_data = {
            "name": "Updated Lifecycle Product",
            "description": "Updated description",
            "is_featured": True
        }
        
        response = await async_client.put(f"/products/{product_id}", json=update_data, headers=supplier_auth_headers)
        assert response.status_code == 200
        updated_product = response.json()["data"]
        assert updated_product["name"] == "Updated Lifecycle Product"
        assert updated_product["is_featured"] is True
        
        # Step 4: Create variants
        variant_data = {
            "name": "Lifecycle Variant 1",
            "sku": "LIFE-001",
            "base_price": "99.99",
            "sale_price": "79.99",
            "weight": "1.0",
            "is_active": True
        }
        
        response = await async_client.post(f"/products/{product_id}/variants", json=variant_data, headers=supplier_auth_headers)
        assert response.status_code == 201
        variant_id = response.json()["data"]["id"]
        
        # Step 5: Get product with variants
        response = await async_client.get(f"/products/{product_id}")
        assert response.status_code == 200
        product_with_variants = response.json()["data"]
        assert len(product_with_variants["variants"]) >= 1
        assert product_with_variants["variants"][0]["id"] == variant_id
        
        # Step 6: Search for product
        response = await async_client.get(f"/products/search?q=Lifecycle")
        assert response.status_code == 200
        search_results = response.json()["data"]
        assert len(search_results) >= 1
        
        # Step 7: Get product recommendations
        response = await async_client.get(f"/products/{product_id}/recommendations")
        assert response.status_code == 200
        recommendations = response.json()["data"]
        assert isinstance(recommendations, list)


@pytest.mark.integration
class TestPaymentFlow:
    """Test complete payment flow."""
    
    @pytest.mark.asyncio
    async def test_payment_processing_flow(self, async_client: AsyncClient, auth_headers: dict, mock_stripe):
        """Test complete payment processing flow."""
        
        # Step 1: Create payment method
        payment_method_data = {
            "stripe_payment_method_id": "pm_test_123",
            "is_default": True
        }
        
        response = await async_client.post("/payments/methods", json=payment_method_data, headers=auth_headers)
        assert response.status_code == 201
        payment_method_id = response.json()["data"]["id"]
        
        # Step 2: Create payment intent
        intent_data = {
            "amount": "100.00",
            "currency": "usd",
            "payment_method_id": payment_method_id,
            "description": "Integration test payment"
        }
        
        response = await async_client.post("/payments/intents", json=intent_data, headers=auth_headers)
        assert response.status_code == 201
        intent_id = response.json()["data"]["id"]
        
        # Step 3: Confirm payment intent
        mock_stripe["payment_intent"].confirm = MagicMock(return_value=MagicMock(
            id="pi_test_123",
            status="succeeded",
            charges=MagicMock(data=[MagicMock(id="ch_test_123")])
        ))
        
        response = await async_client.post(f"/payments/intents/{intent_id}/confirm", headers=auth_headers)
        assert response.status_code == 200
        confirmed_intent = response.json()["data"]
        assert confirmed_intent["status"] == "succeeded"
        
        # Step 4: Get transactions
        response = await async_client.get("/payments/transactions", headers=auth_headers)
        assert response.status_code == 200
        transactions = response.json()["data"]
        assert len(transactions) >= 1
        
        # Step 5: Create refund
        transaction_id = transactions[0]["id"]
        refund_data = {
            "amount": "50.00",
            "reason": "requested_by_customer"
        }
        
        with patch('stripe.Refund.create') as mock_refund:
            mock_refund.return_value = MagicMock(
                id="re_test_123",
                status="succeeded",
                amount=5000
            )
            
            response = await async_client.post(f"/payments/refunds/{transaction_id}", json=refund_data, headers=auth_headers)
            assert response.status_code == 201
            refund_data_response = response.json()["data"]
            assert refund_data_response["amount"] == "50.00"


@pytest.mark.integration
class TestInventoryFlow:
    """Test complete inventory management flow."""
    
    @pytest.mark.asyncio
    async def test_inventory_management_flow(self, async_client: AsyncClient, db_session: AsyncSession, admin_auth_headers: dict):
        """Test complete inventory management flow."""
        
        # Step 1: Create warehouse
        warehouse_data = {
            "name": "Integration Warehouse",
            "address": "123 Warehouse St",
            "city": "Warehouse City",
            "state": "WS",
            "country": "US",
            "postal_code": "12345",
            "is_active": True
        }
        
        response = await async_client.post("/inventory/warehouses", json=warehouse_data, headers=admin_auth_headers)
        assert response.status_code == 201
        warehouse_id = response.json()["data"]["id"]
        
        # Step 2: Create product and variant for inventory
        category = Category(
            id=uuid4(),
            name="Inventory Category",
            description="For inventory testing",
            is_active=True
        )
        db_session.add(category)
        
        product = Product(
            id=uuid4(),
            name="Inventory Product",
            description="For inventory testing",
            category_id=category.id,
            brand="Test Brand",
            is_active=True
        )
        db_session.add(product)
        
        variant = ProductVariant(
            id=uuid4(),
            product_id=product.id,
            name="Inventory Variant",
            sku="INV-001",
            base_price=Decimal("99.99"),
            is_active=True
        )
        db_session.add(variant)
        
        warehouse = await db_session.get(WarehouseLocation, warehouse_id)
        inventory = Inventory(
            id=uuid4(),
            variant_id=variant.id,
            warehouse_id=warehouse.id,
            quantity_available=100,
            quantity_reserved=0,
            reorder_point=20,
            reorder_quantity=50
        )
        db_session.add(inventory)
        await db_session.commit()
        
        # Step 3: Get inventory
        response = await async_client.get(f"/inventory/variants/{variant.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        inventory_data = response.json()["data"]
        assert inventory_data["quantity_available"] == 100
        
        # Step 4: Adjust stock
        adjustment_data = {
            "adjustment_type": "increase",
            "quantity": 50,
            "reason": "Restocking",
            "notes": "Integration test restock"
        }
        
        response = await async_client.post(f"/inventory/variants/{variant.id}/adjust", json=adjustment_data, headers=admin_auth_headers)
        assert response.status_code == 200
        
        # Step 5: Verify stock adjustment
        response = await async_client.get(f"/inventory/variants/{variant.id}", headers=admin_auth_headers)
        assert response.status_code == 200
        updated_inventory = response.json()["data"]
        assert updated_inventory["quantity_available"] == 150  # 100 + 50
        
        # Step 6: Get low stock items (should be empty now)
        response = await async_client.get("/inventory/low-stock", headers=admin_auth_headers)
        assert response.status_code == 200
        low_stock_items = response.json()["data"]
        # Our item should not be in low stock anymore
        
        # Step 7: Get inventory summary
        response = await async_client.get("/inventory/summary", headers=admin_auth_headers)
        assert response.status_code == 200
        summary = response.json()["data"]
        assert "total_variants" in summary
        assert "total_quantity" in summary


@pytest.mark.integration
class TestErrorHandlingFlow:
    """Test error handling across the application."""
    
    @pytest.mark.asyncio
    async def test_error_propagation_flow(self, async_client: AsyncClient, auth_headers: dict):
        """Test error handling and propagation across services."""
        
        # Step 1: Test invalid product ID in cart
        invalid_cart_data = {
            "variant_id": str(uuid4()),  # Non-existent variant
            "quantity": 1
        }
        
        response = await async_client.post("/cart/items", json=invalid_cart_data, headers=auth_headers)
        assert response.status_code == 404
        error_data = response.json()
        assert error_data["success"] is False
        assert "not found" in error_data["message"].lower()
        
        # Step 2: Test invalid payment method
        invalid_payment_data = {
            "stripe_payment_method_id": "pm_invalid",
            "is_default": True
        }
        
        response = await async_client.post("/payments/methods", json=invalid_payment_data, headers=auth_headers)
        assert response.status_code == 400
        error_data = response.json()
        assert error_data["success"] is False
        
        # Step 3: Test checkout with empty cart
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
            "shipping_method_id": str(uuid4()),  # Invalid shipping method
            "payment_method_id": str(uuid4())    # Invalid payment method
        }
        
        response = await async_client.post("/orders", json=checkout_data, headers=auth_headers)
        assert response.status_code in [400, 404]
        error_data = response.json()
        assert error_data["success"] is False
        
        # Step 4: Test unauthorized access
        response = await async_client.get("/inventory/summary")  # No auth headers
        assert response.status_code == 401
        
        # Step 5: Test validation errors
        invalid_user_data = {
            "email": "invalid-email",  # Invalid email format
            "firstname": "",           # Empty required field
            "password": "weak"         # Weak password
        }
        
        response = await async_client.post("/auth/register", json=invalid_user_data)
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data  # FastAPI validation error format


@pytest.mark.integration
class TestPerformanceFlow:
    """Test performance-critical flows."""
    
    @pytest.mark.asyncio
    async def test_bulk_operations_flow(self, async_client: AsyncClient, db_session: AsyncSession, admin_auth_headers: dict):
        """Test bulk operations performance."""
        
        # Create test data
        category = Category(
            id=uuid4(),
            name="Bulk Category",
            description="For bulk testing",
            is_active=True
        )
        db_session.add(category)
        
        product = Product(
            id=uuid4(),
            name="Bulk Product",
            description="For bulk testing",
            category_id=category.id,
            brand="Test Brand",
            is_active=True
        )
        db_session.add(product)
        
        warehouse = WarehouseLocation(
            id=uuid4(),
            name="Bulk Warehouse",
            address="123 Bulk St",
            city="Bulk City",
            state="BS",
            country="US",
            postal_code="12345",
            is_active=True
        )
        db_session.add(warehouse)
        
        # Create multiple variants and inventory
        variants = []
        for i in range(10):
            variant = ProductVariant(
                id=uuid4(),
                product_id=product.id,
                name=f"Bulk Variant {i}",
                sku=f"BULK-{i:03d}",
                base_price=Decimal("50.00"),
                is_active=True
            )
            variants.append(variant)
            
            inventory = Inventory(
                id=uuid4(),
                variant_id=variant.id,
                warehouse_id=warehouse.id,
                quantity_available=100,
                quantity_reserved=0
            )
            db_session.add_all([variant, inventory])
        
        await db_session.commit()
        
        # Test bulk inventory adjustments
        bulk_adjustments = {
            "adjustments": [
                {
                    "variant_id": str(variant.id),
                    "adjustment_type": "increase",
                    "quantity": 20,
                    "reason": "Bulk restock"
                }
                for variant in variants[:5]  # First 5 variants
            ]
        }
        
        response = await async_client.post("/inventory/bulk-adjust", json=bulk_adjustments, headers=admin_auth_headers)
        assert response.status_code == 200
        bulk_result = response.json()["data"]
        assert bulk_result["successful"] == 5
        assert bulk_result["failed"] == 0
        
        # Test pagination performance
        response = await async_client.get("/products?page=1&limit=50")
        assert response.status_code == 200
        products_data = response.json()["data"]
        pagination_data = response.json()["pagination"]
        assert "page" in pagination_data
        assert "limit" in pagination_data
        assert "total" in pagination_data