"""
Tests for orders service
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from decimal import Decimal
from unittest.mock import MagicMock, patch

from services.orders import OrderService, PricingCalculationResult
from models.orders import Order, OrderItem, OrderStatus
from models.cart import Cart, CartItem
from models.user import User, Address
from models.product import ProductVariant
from models.shipping import ShippingMethod
from models.payments import PaymentMethod
from models.tax_rates import TaxRate
from models.inventories import Inventory
from schemas.orders import OrderCreate, CheckoutRequest


class TestOrderService:
    """Test order service."""
    
    @pytest.mark.asyncio
    async def test_calculate_comprehensive_pricing(self, db_session: AsyncSession, test_cart_item: CartItem, test_variant: ProductVariant, test_shipping_method: ShippingMethod, test_tax_rate: TaxRate):
        """Test comprehensive pricing calculation."""
        order_service = OrderService(db_session)
        
        # Create shipping address
        shipping_address = Address(
            street="123 Test St",
            city="Test City",
            state="CA",
            country="US",
            postal_code="12345"
        )
        
        cart_items = [test_cart_item]
        
        pricing_result = await order_service.calculate_comprehensive_pricing(
            cart_items=cart_items,
            shipping_address=shipping_address,
            shipping_method_id=test_shipping_method.id,
            currency="USD"
        )
        
        assert isinstance(pricing_result, PricingCalculationResult)
        assert pricing_result.subtotal > 0
        assert pricing_result.shipping_cost >= 0
        assert pricing_result.tax_amount >= 0
        assert pricing_result.total_amount > 0
        assert pricing_result.currency == "USD"
        
        # Verify calculation accuracy
        expected_subtotal = (test_variant.sale_price or test_variant.base_price) * test_cart_item.quantity
        assert pricing_result.subtotal == expected_subtotal
        
        # Total should equal sum of components
        expected_total = pricing_result.subtotal + pricing_result.shipping_cost + pricing_result.tax_amount - pricing_result.discount_amount
        assert pricing_result.total_amount == expected_total
    
    @pytest.mark.asyncio
    async def test_calculate_pricing_with_discount(self, db_session: AsyncSession, test_cart_item: CartItem, test_shipping_method: ShippingMethod, test_tax_rate: TaxRate):
        """Test pricing calculation with discount."""
        # Create discount
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
        
        order_service = OrderService(db_session)
        
        shipping_address = Address(
            street="123 Test St",
            city="Test City",
            state="CA",
            country="US",
            postal_code="12345"
        )
        
        cart_items = [test_cart_item]
        
        pricing_result = await order_service.calculate_comprehensive_pricing(
            cart_items=cart_items,
            shipping_address=shipping_address,
            shipping_method_id=test_shipping_method.id,
            discount_code="TEST10",
            currency="USD"
        )
        
        assert pricing_result.discount_amount > 0
        # 10% discount should be applied
        expected_discount = pricing_result.subtotal * Decimal("0.10")
        assert pricing_result.discount_amount == expected_discount
    
    @pytest.mark.asyncio
    async def test_create_order_success(self, db_session: AsyncSession, test_user: User, test_cart: Cart, test_cart_item: CartItem, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod, test_tax_rate: TaxRate, test_inventory, mock_stripe):
        """Test successful order creation."""
        order_service = OrderService(db_session)
        background_tasks = MagicMock()
        
        order_data = OrderCreate(
            shipping_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            billing_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            shipping_method_id=test_shipping_method.id,
            payment_method_id=test_payment_method.id
        )
        
        with patch('services.payments.PaymentService.process_payment') as mock_payment:
            mock_payment.return_value = MagicMock(status="succeeded")
            
            order = await order_service.create_order(test_user.id, order_data, background_tasks)
        
        assert order is not None
        assert order.user_id == test_user.id
        assert order.status == OrderStatus.PENDING
        assert order.subtotal > 0
        assert order.total_amount > 0
        assert len(order.items) >= 1
        
        # Verify order item
        order_item = order.items[0]
        assert order_item.variant_id == test_cart_item.variant_id
        assert order_item.quantity == test_cart_item.quantity
    
    @pytest.mark.asyncio
    async def test_create_order_empty_cart(self, db_session: AsyncSession, test_user: User, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod):
        """Test order creation with empty cart."""
        order_service = OrderService(db_session)
        background_tasks = MagicMock()
        
        order_data = OrderCreate(
            shipping_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            billing_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            shipping_method_id=test_shipping_method.id,
            payment_method_id=test_payment_method.id
        )
        
        with pytest.raises(Exception) as exc_info:
            await order_service.create_order(test_user.id, order_data, background_tasks)
        
        assert "empty cart" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_create_order_insufficient_stock(self, db_session: AsyncSession, test_user: User, test_cart: Cart, test_variant: ProductVariant, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod, test_inventory):
        """Test order creation with insufficient stock."""
        # Create cart item with quantity exceeding stock
        cart_item = CartItem(
            id=uuid4(),
            cart_id=test_cart.id,
            variant_id=test_variant.id,
            quantity=test_inventory.quantity_available + 10
        )
        db_session.add(cart_item)
        await db_session.commit()
        
        order_service = OrderService(db_session)
        background_tasks = MagicMock()
        
        order_data = OrderCreate(
            shipping_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            billing_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            shipping_method_id=test_shipping_method.id,
            payment_method_id=test_payment_method.id
        )
        
        with pytest.raises(Exception) as exc_info:
            await order_service.create_order(test_user.id, order_data, background_tasks)
        
        assert "insufficient stock" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_validate_checkout_success(self, db_session: AsyncSession, test_user: User, test_cart: Cart, test_cart_item: CartItem, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod, test_tax_rate: TaxRate, test_inventory):
        """Test successful checkout validation."""
        order_service = OrderService(db_session)
        
        checkout_data = CheckoutRequest(
            shipping_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            billing_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            shipping_method_id=test_shipping_method.id,
            payment_method_id=test_payment_method.id
        )
        
        validation_result = await order_service.validate_checkout(test_user.id, checkout_data)
        
        assert validation_result["is_valid"] is True
        assert len(validation_result["issues"]) == 0
        assert "pricing" in validation_result
        assert validation_result["pricing"]["total_amount"] > 0
    
    @pytest.mark.asyncio
    async def test_validate_checkout_empty_cart(self, db_session: AsyncSession, test_user: User, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod):
        """Test checkout validation with empty cart."""
        order_service = OrderService(db_session)
        
        checkout_data = CheckoutRequest(
            shipping_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            billing_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            shipping_method_id=test_shipping_method.id,
            payment_method_id=test_payment_method.id
        )
        
        validation_result = await order_service.validate_checkout(test_user.id, checkout_data)
        
        assert validation_result["is_valid"] is False
        assert len(validation_result["issues"]) > 0
        assert any("empty cart" in issue.lower() for issue in validation_result["issues"])
    
    @pytest.mark.asyncio
    async def test_validate_checkout_invalid_shipping_method(self, db_session: AsyncSession, test_user: User, test_cart: Cart, test_cart_item: CartItem, test_payment_method: PaymentMethod):
        """Test checkout validation with invalid shipping method."""
        order_service = OrderService(db_session)
        
        checkout_data = CheckoutRequest(
            shipping_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            billing_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            shipping_method_id=uuid4(),  # Invalid ID
            payment_method_id=test_payment_method.id
        )
        
        validation_result = await order_service.validate_checkout(test_user.id, checkout_data)
        
        assert validation_result["is_valid"] is False
        assert len(validation_result["issues"]) > 0
        assert any("shipping method" in issue.lower() for issue in validation_result["issues"])
    
    @pytest.mark.asyncio
    async def test_get_user_orders(self, db_session: AsyncSession, test_user: User):
        """Test getting user's orders."""
        # Create test orders
        order1 = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.CONFIRMED,
            subtotal=Decimal("99.99"),
            shipping_cost=Decimal("9.99"),
            tax_amount=Decimal("8.75"),
            total_amount=Decimal("118.73"),
            currency="USD"
        )
        order2 = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.SHIPPED,
            subtotal=Decimal("149.99"),
            shipping_cost=Decimal("9.99"),
            tax_amount=Decimal("13.12"),
            total_amount=Decimal("173.10"),
            currency="USD"
        )
        db_session.add_all([order1, order2])
        await db_session.commit()
        
        order_service = OrderService(db_session)
        
        orders = await order_service.get_user_orders(test_user.id)
        
        assert len(orders) >= 2
        order_ids = [str(order.id) for order in orders]
        assert str(order1.id) in order_ids
        assert str(order2.id) in order_ids
    
    @pytest.mark.asyncio
    async def test_get_order_by_id(self, db_session: AsyncSession, test_user: User):
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
        
        order_service = OrderService(db_session)
        
        retrieved_order = await order_service.get_order_by_id(order.id, test_user.id)
        
        assert retrieved_order is not None
        assert retrieved_order.id == order.id
        assert retrieved_order.user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_get_order_by_id_unauthorized(self, db_session: AsyncSession, test_user: User):
        """Test getting order by ID for different user."""
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
        
        order_service = OrderService(db_session)
        
        retrieved_order = await order_service.get_order_by_id(other_order.id, test_user.id)
        
        assert retrieved_order is None  # Should not return other user's order
    
    @pytest.mark.asyncio
    async def test_cancel_order_success(self, db_session: AsyncSession, test_user: User):
        """Test successful order cancellation."""
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
        
        order_service = OrderService(db_session)
        
        cancelled_order = await order_service.cancel_order(order.id, test_user.id)
        
        assert cancelled_order is not None
        assert cancelled_order.status == OrderStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_cancel_order_already_shipped(self, db_session: AsyncSession, test_user: User):
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
        
        order_service = OrderService(db_session)
        
        with pytest.raises(Exception) as exc_info:
            await order_service.cancel_order(order.id, test_user.id)
        
        assert "cannot be cancelled" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_update_order_status(self, db_session: AsyncSession, test_user: User):
        """Test updating order status."""
        # Create order
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
        
        order_service = OrderService(db_session)
        
        updated_order = await order_service.update_order_status(order.id, OrderStatus.PROCESSING)
        
        assert updated_order is not None
        assert updated_order.status == OrderStatus.PROCESSING
    
    @pytest.mark.asyncio
    async def test_add_tracking_info(self, db_session: AsyncSession, test_user: User):
        """Test adding tracking information to order."""
        # Create order
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
        
        order_service = OrderService(db_session)
        tracking_number = "TRACK123456"
        carrier = "UPS"
        
        updated_order = await order_service.add_tracking_info(order.id, tracking_number, carrier)
        
        assert updated_order is not None
        assert updated_order.tracking_number == tracking_number
        assert updated_order.carrier == carrier
        assert updated_order.status == OrderStatus.SHIPPED
    
    @pytest.mark.asyncio
    async def test_reorder_from_previous_order(self, db_session: AsyncSession, test_user: User, test_variant: ProductVariant, test_inventory):
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
        
        order_service = OrderService(db_session)
        
        result = await order_service.reorder_from_previous_order(order.id, test_user.id)
        
        assert result["success"] is True
        assert result["items_added"] > 0
        assert "cart" in result


class TestOrderServicePricing:
    """Test order service pricing calculations."""
    
    @pytest.mark.asyncio
    async def test_pricing_with_multiple_items(self, db_session: AsyncSession, test_cart: Cart, test_product, test_shipping_method: ShippingMethod, test_tax_rate: TaxRate):
        """Test pricing calculation with multiple cart items."""
        # Create multiple variants and cart items
        variant1 = ProductVariant(
            id=uuid4(),
            product_id=test_product.id,
            name="Variant 1",
            sku="VAR-001",
            base_price=Decimal("50.00"),
            is_active=True
        )
        variant2 = ProductVariant(
            id=uuid4(),
            product_id=test_product.id,
            name="Variant 2",
            sku="VAR-002",
            base_price=Decimal("75.00"),
            sale_price=Decimal("60.00"),
            is_active=True
        )
        db_session.add_all([variant1, variant2])
        
        cart_item1 = CartItem(
            id=uuid4(),
            cart_id=test_cart.id,
            variant_id=variant1.id,
            quantity=2
        )
        cart_item2 = CartItem(
            id=uuid4(),
            cart_id=test_cart.id,
            variant_id=variant2.id,
            quantity=1
        )
        db_session.add_all([cart_item1, cart_item2])
        await db_session.commit()
        
        order_service = OrderService(db_session)
        
        shipping_address = Address(
            street="123 Test St",
            city="Test City",
            state="CA",
            country="US",
            postal_code="12345"
        )
        
        cart_items = [cart_item1, cart_item2]
        
        pricing_result = await order_service.calculate_comprehensive_pricing(
            cart_items=cart_items,
            shipping_address=shipping_address,
            shipping_method_id=test_shipping_method.id,
            currency="USD"
        )
        
        # Expected subtotal: (50.00 * 2) + (60.00 * 1) = 160.00
        expected_subtotal = Decimal("160.00")
        assert pricing_result.subtotal == expected_subtotal
    
    @pytest.mark.asyncio
    async def test_pricing_with_weight_based_shipping(self, db_session: AsyncSession, test_cart_item: CartItem, test_variant: ProductVariant, test_tax_rate: TaxRate):
        """Test pricing calculation with weight-based shipping."""
        # Create shipping method with per-kg cost
        shipping_method = ShippingMethod(
            id=uuid4(),
            name="Weight-based Shipping",
            description="Shipping based on weight",
            base_cost=Decimal("5.00"),
            per_kg_cost=Decimal("2.00"),
            estimated_days_min=3,
            estimated_days_max=5,
            is_active=True
        )
        db_session.add(shipping_method)
        
        # Set variant weight
        test_variant.weight = Decimal("2.5")  # 2.5 kg
        await db_session.commit()
        
        order_service = OrderService(db_session)
        
        shipping_address = Address(
            street="123 Test St",
            city="Test City",
            state="CA",
            country="US",
            postal_code="12345"
        )
        
        cart_items = [test_cart_item]
        
        pricing_result = await order_service.calculate_comprehensive_pricing(
            cart_items=cart_items,
            shipping_address=shipping_address,
            shipping_method_id=shipping_method.id,
            currency="USD"
        )
        
        # Expected shipping: 5.00 + (2.5 * 2 * 2.00) = 5.00 + 10.00 = 15.00
        expected_shipping = Decimal("15.00")
        assert pricing_result.shipping_cost == expected_shipping
    
    @pytest.mark.asyncio
    async def test_pricing_with_free_shipping_discount(self, db_session: AsyncSession, test_cart_item: CartItem, test_shipping_method: ShippingMethod, test_tax_rate: TaxRate):
        """Test pricing calculation with free shipping discount."""
        # Create free shipping discount
        from models.discounts import Discount
        discount = Discount(
            id=uuid4(),
            code="FREESHIP",
            discount_type="free_shipping",
            discount_value=Decimal("0.00"),
            is_active=True,
            usage_limit=100,
            usage_count=0
        )
        db_session.add(discount)
        await db_session.commit()
        
        order_service = OrderService(db_session)
        
        shipping_address = Address(
            street="123 Test St",
            city="Test City",
            state="CA",
            country="US",
            postal_code="12345"
        )
        
        cart_items = [test_cart_item]
        
        pricing_result = await order_service.calculate_comprehensive_pricing(
            cart_items=cart_items,
            shipping_address=shipping_address,
            shipping_method_id=test_shipping_method.id,
            discount_code="FREESHIP",
            currency="USD"
        )
        
        # Shipping cost should be 0 with free shipping discount
        assert pricing_result.shipping_cost == Decimal("0.00")
        assert pricing_result.discount_amount >= test_shipping_method.base_cost
    
    @pytest.mark.asyncio
    async def test_pricing_currency_conversion(self, db_session: AsyncSession, test_cart_item: CartItem, test_shipping_method: ShippingMethod, test_tax_rate: TaxRate):
        """Test pricing calculation with currency conversion."""
        order_service = OrderService(db_session)
        
        shipping_address = Address(
            street="123 Test St",
            city="Test City",
            state="CA",
            country="US",
            postal_code="12345"
        )
        
        cart_items = [test_cart_item]
        
        # Test with EUR currency
        with patch('services.orders.CurrencyConverter.convert') as mock_convert:
            mock_convert.return_value = Decimal("85.00")  # Mock EUR conversion
            
            pricing_result = await order_service.calculate_comprehensive_pricing(
                cart_items=cart_items,
                shipping_address=shipping_address,
                shipping_method_id=test_shipping_method.id,
                currency="EUR"
            )
        
        assert pricing_result.currency == "EUR"
        # Should have called currency conversion
        mock_convert.assert_called()


class TestOrderServiceSecurity:
    """Test order service security features."""
    
    @pytest.mark.asyncio
    async def test_price_tampering_detection(self, db_session: AsyncSession, test_user: User, test_cart: Cart, test_variant: ProductVariant, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod):
        """Test detection of price tampering."""
        # Create cart item
        cart_item = CartItem(
            id=uuid4(),
            cart_id=test_cart.id,
            variant_id=test_variant.id,
            quantity=1
        )
        db_session.add(cart_item)
        await db_session.commit()
        
        order_service = OrderService(db_session)
        background_tasks = MagicMock()
        
        # Simulate tampered order data with incorrect total
        order_data = OrderCreate(
            shipping_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            billing_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            shipping_method_id=test_shipping_method.id,
            payment_method_id=test_payment_method.id,
            # Simulate frontend sending tampered total
            expected_total=Decimal("1.00")  # Much lower than actual
        )
        
        with pytest.raises(Exception) as exc_info:
            await order_service.create_order(test_user.id, order_data, background_tasks)
        
        assert "price mismatch" in str(exc_info.value).lower() or "tampering" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_order_idempotency(self, db_session: AsyncSession, test_user: User, test_cart: Cart, test_cart_item: CartItem, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod, test_inventory, mock_stripe):
        """Test order creation idempotency."""
        order_service = OrderService(db_session)
        background_tasks = MagicMock()
        idempotency_key = str(uuid4())
        
        order_data = OrderCreate(
            shipping_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            billing_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            shipping_method_id=test_shipping_method.id,
            payment_method_id=test_payment_method.id,
            idempotency_key=idempotency_key
        )
        
        with patch('services.payments.PaymentService.process_payment') as mock_payment:
            mock_payment.return_value = MagicMock(status="succeeded")
            
            # First order creation
            order1 = await order_service.create_order(test_user.id, order_data, background_tasks)
            
            # Second order creation with same idempotency key
            order2 = await order_service.create_order(test_user.id, order_data, background_tasks)
        
        # Should return the same order
        assert order1.id == order2.id
    
    @pytest.mark.asyncio
    async def test_concurrent_order_creation_stock_protection(self, db_session: AsyncSession, test_user: User, test_cart: Cart, test_variant: ProductVariant, test_shipping_method: ShippingMethod, test_payment_method: PaymentMethod, test_inventory):
        """Test stock protection during concurrent order creation."""
        # Set low stock
        test_inventory.quantity_available = 1
        await db_session.commit()
        
        # Create cart item with quantity 1
        cart_item = CartItem(
            id=uuid4(),
            cart_id=test_cart.id,
            variant_id=test_variant.id,
            quantity=1
        )
        db_session.add(cart_item)
        await db_session.commit()
        
        order_service = OrderService(db_session)
        background_tasks = MagicMock()
        
        order_data = OrderCreate(
            shipping_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            billing_address={
                "street": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "country": "US",
                "postal_code": "12345"
            },
            shipping_method_id=test_shipping_method.id,
            payment_method_id=test_payment_method.id
        )
        
        with patch('services.payments.PaymentService.process_payment') as mock_payment:
            mock_payment.return_value = MagicMock(status="succeeded")
            
            # First order should succeed
            order1 = await order_service.create_order(test_user.id, order_data, background_tasks)
            assert order1 is not None
            
            # Second order should fail due to insufficient stock
            with pytest.raises(Exception) as exc_info:
                await order_service.create_order(test_user.id, order_data, background_tasks)
            
            assert "insufficient stock" in str(exc_info.value).lower()