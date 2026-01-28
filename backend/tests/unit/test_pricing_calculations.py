"""
Unit tests for pricing calculations with shipping, tax, and discounts
"""
import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from services.orders import OrderService, PricingCalculationResult
from services.tax import TaxService
from services.shipping import ShippingService
from services.discounts import DiscountEngine
from models.cart import Cart, CartItem
from models.product import ProductVariant, Product, Category
from models.user import User, Address
from models.shipping import ShippingMethod
from models.tax_rates import TaxRate
from models.discounts import Discount
from models.inventories import Inventory, WarehouseLocation


@pytest.mark.unit
class TestPricingCalculations:
    """Test comprehensive pricing calculations."""
    
    @pytest.mark.asyncio
    async def test_basic_subtotal_calculation(self, db_session: AsyncSession):
        """Test basic subtotal calculation with multiple items."""
        # Setup test data
        user, cart, items = await self._setup_cart_with_items(db_session)
        
        order_service = OrderService(db_session)
        
        # Calculate subtotal
        subtotal = await order_service._calculate_subtotal(items)
        
        # Expected: (79.99 * 2) + (149.99 * 1) = 309.97
        expected_subtotal = Decimal("309.97")
        assert subtotal == expected_subtotal
    
    @pytest.mark.asyncio
    async def test_sale_price_vs_base_price(self, db_session: AsyncSession):
        """Test that sale price is used when available, otherwise base price."""
        user = await self._create_test_user(db_session)
        cart = await self._create_test_cart(db_session, user.id)
        
        # Create variants with different pricing scenarios
        category = Category(id=uuid4(), name="Test Category", is_active=True)
        product = Product(id=uuid4(), name="Test Product", category_id=category.id, is_active=True)
        db_session.add_all([category, product])
        
        # Variant with sale price
        variant_with_sale = ProductVariant(
            id=uuid4(),
            product_id=product.id,
            name="Sale Variant",
            sku="SALE-001",
            base_price=Decimal("100.00"),
            sale_price=Decimal("80.00"),  # 20% off
            is_active=True
        )
        
        # Variant without sale price
        variant_no_sale = ProductVariant(
            id=uuid4(),
            product_id=product.id,
            name="Regular Variant",
            sku="REG-001",
            base_price=Decimal("100.00"),
            sale_price=None,
            is_active=True
        )
        
        db_session.add_all([variant_with_sale, variant_no_sale])
        
        # Create cart items
        item1 = CartItem(
            id=uuid4(),
            cart_id=cart.id,
            variant_id=variant_with_sale.id,
            quantity=1
        )
        item2 = CartItem(
            id=uuid4(),
            cart_id=cart.id,
            variant_id=variant_no_sale.id,
            quantity=1
        )
        
        db_session.add_all([item1, item2])
        await db_session.commit()
        
        order_service = OrderService(db_session)
        
        # Calculate subtotal
        items = [item1, item2]
        subtotal = await order_service._calculate_subtotal(items)
        
        # Expected: 80.00 (sale price) + 100.00 (base price) = 180.00
        expected_subtotal = Decimal("180.00")
        assert subtotal == expected_subtotal
    
    @pytest.mark.asyncio
    async def test_tax_calculation_by_location(self, db_session: AsyncSession):
        """Test tax calculation based on shipping address location."""
        # Create tax rates for different locations
        ca_tax = TaxRate(
            id=uuid4(),
            country="US",
            state="CA",
            rate=Decimal("0.0875"),  # 8.75%
            is_active=True
        )
        ny_tax = TaxRate(
            id=uuid4(),
            country="US",
            state="NY",
            rate=Decimal("0.08"),    # 8%
            is_active=True
        )
        no_tax = TaxRate(
            id=uuid4(),
            country="US",
            state="OR",
            rate=Decimal("0.00"),    # 0% (Oregon has no sales tax)
            is_active=True
        )
        
        db_session.add_all([ca_tax, ny_tax, no_tax])
        await db_session.commit()
        
        tax_service = TaxService(db_session)
        subtotal = Decimal("100.00")
        
        # Test California tax
        ca_address = Address(
            street="123 CA St",
            city="Los Angeles",
            state="CA",
            country="US",
            postal_code="90210"
        )
        ca_tax_amount = await tax_service.calculate_tax(subtotal, ca_address)
        assert ca_tax_amount == Decimal("8.75")  # 100.00 * 0.0875
        
        # Test New York tax
        ny_address = Address(
            street="123 NY St",
            city="New York",
            state="NY",
            country="US",
            postal_code="10001"
        )
        ny_tax_amount = await tax_service.calculate_tax(subtotal, ny_address)
        assert ny_tax_amount == Decimal("8.00")  # 100.00 * 0.08
        
        # Test Oregon (no tax)
        or_address = Address(
            street="123 OR St",
            city="Portland",
            state="OR",
            country="US",
            postal_code="97201"
        )
        or_tax_amount = await tax_service.calculate_tax(subtotal, or_address)
        assert or_tax_amount == Decimal("0.00")
    
    @pytest.mark.asyncio
    async def test_shipping_cost_calculation(self, db_session: AsyncSession):
        """Test shipping cost calculation with different methods."""
        # Create shipping methods
        standard_shipping = ShippingMethod(
            id=uuid4(),
            name="Standard Shipping",
            description="5-7 business days",
            base_cost=Decimal("9.99"),
            per_kg_cost=Decimal("0.00"),  # Flat rate
            is_active=True
        )
        
        weight_based_shipping = ShippingMethod(
            id=uuid4(),
            name="Weight-based Shipping",
            description="Based on weight",
            base_cost=Decimal("5.00"),
            per_kg_cost=Decimal("2.50"),  # $2.50 per kg
            is_active=True
        )
        
        free_shipping = ShippingMethod(
            id=uuid4(),
            name="Free Shipping",
            description="Free for orders over $100",
            base_cost=Decimal("0.00"),
            per_kg_cost=Decimal("0.00"),
            is_active=True
        )
        
        db_session.add_all([standard_shipping, weight_based_shipping, free_shipping])
        await db_session.commit()
        
        shipping_service = ShippingService(db_session)
        
        # Test flat rate shipping
        standard_cost = await shipping_service.calculate_shipping_cost(
            standard_shipping.id,
            total_weight=Decimal("2.5"),
            subtotal=Decimal("50.00")
        )
        assert standard_cost == Decimal("9.99")
        
        # Test weight-based shipping
        weight_cost = await shipping_service.calculate_shipping_cost(
            weight_based_shipping.id,
            total_weight=Decimal("3.0"),
            subtotal=Decimal("50.00")
        )
        # Expected: 5.00 + (3.0 * 2.50) = 12.50
        assert weight_cost == Decimal("12.50")
        
        # Test free shipping
        free_cost = await shipping_service.calculate_shipping_cost(
            free_shipping.id,
            total_weight=Decimal("1.0"),
            subtotal=Decimal("150.00")
        )
        assert free_cost == Decimal("0.00")
    
    @pytest.mark.asyncio
    async def test_percentage_discount_calculation(self, db_session: AsyncSession):
        """Test percentage discount calculation."""
        # Create percentage discount
        discount = Discount(
            id=uuid4(),
            code="SAVE20",
            discount_type="percentage",
            discount_value=Decimal("20.00"),  # 20%
            minimum_order_amount=Decimal("50.00"),
            is_active=True,
            usage_limit=100,
            usage_count=0
        )
        db_session.add(discount)
        await db_session.commit()
        
        discount_engine = DiscountEngine(db_session)
        
        # Test discount application
        subtotal = Decimal("100.00")
        discount_amount = await discount_engine.calculate_discount(
            discount.id,
            subtotal=subtotal,
            shipping_cost=Decimal("10.00"),
            items=[]
        )
        
        # Expected: 100.00 * 0.20 = 20.00
        assert discount_amount == Decimal("20.00")
        
        # Test minimum order amount
        small_subtotal = Decimal("30.00")
        small_discount = await discount_engine.calculate_discount(
            discount.id,
            subtotal=small_subtotal,
            shipping_cost=Decimal("10.00"),
            items=[]
        )
        
        # Should be 0 because subtotal < minimum_order_amount
        assert small_discount == Decimal("0.00")
    
    @pytest.mark.asyncio
    async def test_fixed_amount_discount_calculation(self, db_session: AsyncSession):
        """Test fixed amount discount calculation."""
        # Create fixed amount discount
        discount = Discount(
            id=uuid4(),
            code="SAVE15",
            discount_type="fixed",
            discount_value=Decimal("15.00"),  # $15 off
            minimum_order_amount=Decimal("50.00"),
            is_active=True,
            usage_limit=100,
            usage_count=0
        )
        db_session.add(discount)
        await db_session.commit()
        
        discount_engine = DiscountEngine(db_session)
        
        # Test discount application
        subtotal = Decimal("100.00")
        discount_amount = await discount_engine.calculate_discount(
            discount.id,
            subtotal=subtotal,
            shipping_cost=Decimal("10.00"),
            items=[]
        )
        
        assert discount_amount == Decimal("15.00")
        
        # Test discount doesn't exceed subtotal
        small_subtotal = Decimal("10.00")
        capped_discount = await discount_engine.calculate_discount(
            discount.id,
            subtotal=small_subtotal,
            shipping_cost=Decimal("5.00"),
            items=[]
        )
        
        # Should be capped at subtotal amount
        assert capped_discount == Decimal("10.00")
    
    @pytest.mark.asyncio
    async def test_free_shipping_discount(self, db_session: AsyncSession):
        """Test free shipping discount calculation."""
        # Create free shipping discount
        discount = Discount(
            id=uuid4(),
            code="FREESHIP",
            discount_type="free_shipping",
            discount_value=Decimal("0.00"),
            minimum_order_amount=Decimal("75.00"),
            is_active=True,
            usage_limit=100,
            usage_count=0
        )
        db_session.add(discount)
        await db_session.commit()
        
        discount_engine = DiscountEngine(db_session)
        
        # Test free shipping application
        subtotal = Decimal("100.00")
        shipping_cost = Decimal("12.99")
        discount_amount = await discount_engine.calculate_discount(
            discount.id,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            items=[]
        )
        
        # Should equal shipping cost
        assert discount_amount == shipping_cost
        
        # Test minimum order amount not met
        small_subtotal = Decimal("50.00")
        no_discount = await discount_engine.calculate_discount(
            discount.id,
            subtotal=small_subtotal,
            shipping_cost=shipping_cost,
            items=[]
        )
        
        assert no_discount == Decimal("0.00")
    
    @pytest.mark.asyncio
    async def test_comprehensive_pricing_calculation(self, db_session: AsyncSession):
        """Test complete pricing calculation with all components."""
        # Setup comprehensive test data
        user, cart, items = await self._setup_comprehensive_pricing_data(db_session)
        
        order_service = OrderService(db_session)
        
        # Create shipping address
        shipping_address = Address(
            street="123 Test St",
            city="Los Angeles",
            state="CA",
            country="US",
            postal_code="90210"
        )
        
        # Get shipping method
        shipping_method = await db_session.execute(
            select(ShippingMethod).where(ShippingMethod.is_active == True).limit(1)
        )
        shipping_method = shipping_method.scalar_one()
        
        # Calculate comprehensive pricing
        pricing_result = await order_service.calculate_comprehensive_pricing(
            cart_items=items,
            shipping_address=shipping_address,
            shipping_method_id=shipping_method.id,
            discount_code="SAVE10",
            currency="USD"
        )
        
        # Verify all components
        assert isinstance(pricing_result, PricingCalculationResult)
        assert pricing_result.subtotal > Decimal("0")
        assert pricing_result.shipping_cost >= Decimal("0")
        assert pricing_result.tax_amount >= Decimal("0")
        assert pricing_result.discount_amount >= Decimal("0")
        assert pricing_result.total_amount > Decimal("0")
        assert pricing_result.currency == "USD"
        
        # Verify calculation accuracy
        expected_total = (
            pricing_result.subtotal +
            pricing_result.shipping_cost +
            pricing_result.tax_amount -
            pricing_result.discount_amount
        )
        assert pricing_result.total_amount == expected_total
        
        # Verify breakdown is provided
        assert "items" in pricing_result.breakdown
        assert len(pricing_result.breakdown["items"]) == len(items)
    
    @pytest.mark.asyncio
    async def test_pricing_with_multiple_discounts(self, db_session: AsyncSession):
        """Test pricing calculation with multiple applicable discounts (should use best one)."""
        # Create multiple discounts
        discount1 = Discount(
            id=uuid4(),
            code="SAVE10",
            discount_type="percentage",
            discount_value=Decimal("10.00"),  # 10%
            is_active=True,
            usage_limit=100,
            usage_count=0
        )
        
        discount2 = Discount(
            id=uuid4(),
            code="SAVE15",
            discount_type="fixed",
            discount_value=Decimal("15.00"),  # $15 off
            is_active=True,
            usage_limit=100,
            usage_count=0
        )
        
        discount3 = Discount(
            id=uuid4(),
            code="FREESHIP",
            discount_type="free_shipping",
            discount_value=Decimal("0.00"),
            is_active=True,
            usage_limit=100,
            usage_count=0
        )
        
        db_session.add_all([discount1, discount2, discount3])
        await db_session.commit()
        
        discount_engine = DiscountEngine(db_session)
        
        subtotal = Decimal("100.00")
        shipping_cost = Decimal("10.00")
        
        # Find best discount
        best_discount = await discount_engine.find_best_discount(
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            items=[],
            available_codes=["SAVE10", "SAVE15", "FREESHIP"]
        )
        
        # Should choose the fixed $15 discount as it provides the most savings
        assert best_discount["code"] == "SAVE15"
        assert best_discount["amount"] == Decimal("15.00")
    
    @pytest.mark.asyncio
    async def test_pricing_edge_cases(self, db_session: AsyncSession):
        """Test pricing calculation edge cases."""
        order_service = OrderService(db_session)
        
        # Test with zero subtotal
        zero_result = await order_service._calculate_subtotal([])
        assert zero_result == Decimal("0.00")
        
        # Test with very small amounts (rounding)
        user = await self._create_test_user(db_session)
        cart = await self._create_test_cart(db_session, user.id)
        
        category = Category(id=uuid4(), name="Test Category", is_active=True)
        product = Product(id=uuid4(), name="Test Product", category_id=category.id, is_active=True)
        db_session.add_all([category, product])
        
        # Variant with price that causes rounding
        variant = ProductVariant(
            id=uuid4(),
            product_id=product.id,
            name="Rounding Variant",
            sku="ROUND-001",
            base_price=Decimal("0.333"),  # Will need rounding
            is_active=True
        )
        db_session.add(variant)
        
        item = CartItem(
            id=uuid4(),
            cart_id=cart.id,
            variant_id=variant.id,
            quantity=3
        )
        db_session.add(item)
        await db_session.commit()
        
        # Calculate subtotal
        subtotal = await order_service._calculate_subtotal([item])
        
        # Expected: 0.333 * 3 = 0.999, should round to 1.00
        assert subtotal == Decimal("1.00")
    
    @pytest.mark.asyncio
    async def test_currency_conversion_pricing(self, db_session: AsyncSession):
        """Test pricing calculation with currency conversion."""
        user, cart, items = await self._setup_cart_with_items(db_session)
        
        order_service = OrderService(db_session)
        
        shipping_address = Address(
            street="123 Test St",
            city="London",
            state="",
            country="GB",
            postal_code="SW1A 1AA"
        )
        
        # Mock currency conversion
        with patch('services.orders.CurrencyConverter') as mock_converter:
            mock_converter.return_value.convert.return_value = Decimal("250.00")  # Mock GBP conversion
            
            # Get shipping method
            shipping_method = await db_session.execute(
                select(ShippingMethod).where(ShippingMethod.is_active == True).limit(1)
            )
            shipping_method = shipping_method.scalar_one()
            
            pricing_result = await order_service.calculate_comprehensive_pricing(
                cart_items=items,
                shipping_address=shipping_address,
                shipping_method_id=shipping_method.id,
                currency="GBP"
            )
            
            assert pricing_result.currency == "GBP"
            # Verify conversion was called
            mock_converter.return_value.convert.assert_called()
    
    async def _setup_cart_with_items(self, db_session: AsyncSession):
        """Setup cart with test items for pricing calculations."""
        user = await self._create_test_user(db_session)
        cart = await self._create_test_cart(db_session, user.id)
        
        # Create category and product
        category = Category(id=uuid4(), name="Test Category", is_active=True)
        product = Product(id=uuid4(), name="Test Product", category_id=category.id, is_active=True)
        db_session.add_all([category, product])
        
        # Create variants with different prices
        variant1 = ProductVariant(
            id=uuid4(),
            product_id=product.id,
            name="Variant 1",
            sku="VAR-001",
            base_price=Decimal("99.99"),
            sale_price=Decimal("79.99"),
            weight=Decimal("1.0"),
            is_active=True
        )
        
        variant2 = ProductVariant(
            id=uuid4(),
            product_id=product.id,
            name="Variant 2",
            sku="VAR-002",
            base_price=Decimal("149.99"),
            sale_price=None,
            weight=Decimal("2.0"),
            is_active=True
        )
        
        db_session.add_all([variant1, variant2])
        
        # Create cart items
        item1 = CartItem(
            id=uuid4(),
            cart_id=cart.id,
            variant_id=variant1.id,
            quantity=2
        )
        
        item2 = CartItem(
            id=uuid4(),
            cart_id=cart.id,
            variant_id=variant2.id,
            quantity=1
        )
        
        db_session.add_all([item1, item2])
        await db_session.commit()
        
        return user, cart, [item1, item2]
    
    async def _setup_comprehensive_pricing_data(self, db_session: AsyncSession):
        """Setup comprehensive test data for pricing calculations."""
        user, cart, items = await self._setup_cart_with_items(db_session)
        
        # Create shipping method
        shipping_method = ShippingMethod(
            id=uuid4(),
            name="Test Shipping",
            description="Test shipping method",
            base_cost=Decimal("9.99"),
            per_kg_cost=Decimal("2.00"),
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
        
        return user, cart, items
    
    async def _create_test_user(self, db_session: AsyncSession) -> User:
        """Create test user."""
        user = User(
            id=uuid4(),
            email="pricing@example.com",
            firstname="Pricing",
            lastname="Test",
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            role="customer",
            verified=True,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        return user
    
    async def _create_test_cart(self, db_session: AsyncSession, user_id: str) -> Cart:
        """Create test cart."""
        cart = Cart(
            id=uuid4(),
            user_id=user_id
        )
        db_session.add(cart)
        await db_session.commit()
        return cart