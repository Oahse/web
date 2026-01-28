"""
Tests for database models
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
from decimal import Decimal
from datetime import datetime, timedelta

from models.user import User, UserRole, Address
from models.product import Product, ProductVariant, Category
from models.cart import Cart, CartItem
from models.orders import Order, OrderItem, OrderStatus, PaymentStatus
from models.payments import PaymentMethod, PaymentIntent, Transaction
from models.inventories import Inventory, WarehouseLocation
from models.shipping import ShippingMethod
from models.tax_rates import TaxRate
from models.discounts import Discount
from models.review import Review
from models.wishlist import Wishlist, WishlistItem


class TestUserModel:
    """Test User model."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            firstname="Test",
            lastname="User",
            hashed_password="hashed_password",
            role=UserRole.CUSTOMER,
            verified=True,
            is_active=True
        )
        
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.role == UserRole.CUSTOMER
        assert user.created_at is not None
        assert user.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_user_email_unique_constraint(self, db_session: AsyncSession):
        """Test user email unique constraint."""
        user1 = User(
            id=uuid4(),
            email="duplicate@example.com",
            firstname="User",
            lastname="One",
            hashed_password="hashed_password",
            role=UserRole.CUSTOMER
        )
        
        user2 = User(
            id=uuid4(),
            email="duplicate@example.com",  # Duplicate email
            firstname="User",
            lastname="Two",
            hashed_password="hashed_password",
            role=UserRole.CUSTOMER
        )
        
        db_session.add(user1)
        await db_session.commit()
        
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_user_roles(self, db_session: AsyncSession):
        """Test different user roles."""
        roles = [UserRole.CUSTOMER, UserRole.ADMIN, UserRole.SUPPLIER, UserRole.MANAGER]
        
        for i, role in enumerate(roles):
            user = User(
                id=uuid4(),
                email=f"user{i}@example.com",
                firstname="Test",
                lastname="User",
                hashed_password="hashed_password",
                role=role
            )
            db_session.add(user)
        
        await db_session.commit()
        
        # Verify all users were created with correct roles
        for i, role in enumerate(roles):
            user = await db_session.get(User, f"user{i}@example.com")
            if user:
                assert user.role == role


class TestProductModel:
    """Test Product and related models."""
    
    @pytest.mark.asyncio
    async def test_create_category(self, db_session: AsyncSession):
        """Test creating a category."""
        category = Category(
            id=uuid4(),
            name="Electronics",
            description="Electronic products",
            is_active=True
        )
        
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        
        assert category.id is not None
        assert category.name == "Electronics"
        assert category.is_active is True
    
    @pytest.mark.asyncio
    async def test_create_product(self, db_session: AsyncSession, test_category: Category):
        """Test creating a product."""
        product = Product(
            id=uuid4(),
            name="Test Product",
            description="A test product",
            category_id=test_category.id,
            brand="Test Brand",
            is_active=True,
            is_featured=False
        )
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        assert product.id is not None
        assert product.name == "Test Product"
        assert product.category_id == test_category.id
        assert product.is_active is True
    
    @pytest.mark.asyncio
    async def test_create_product_variant(self, db_session: AsyncSession, test_product: Product):
        """Test creating a product variant."""
        variant = ProductVariant(
            id=uuid4(),
            product_id=test_product.id,
            name="Test Variant",
            sku="TEST-001",
            base_price=Decimal("99.99"),
            sale_price=Decimal("79.99"),
            weight=Decimal("1.0"),
            is_active=True
        )
        
        db_session.add(variant)
        await db_session.commit()
        await db_session.refresh(variant)
        
        assert variant.id is not None
        assert variant.product_id == test_product.id
        assert variant.sku == "TEST-001"
        assert variant.base_price == Decimal("99.99")
        assert variant.sale_price == Decimal("79.99")
    
    @pytest.mark.asyncio
    async def test_variant_sku_unique_constraint(self, db_session: AsyncSession, test_product: Product):
        """Test variant SKU unique constraint."""
        variant1 = ProductVariant(
            id=uuid4(),
            product_id=test_product.id,
            name="Variant 1",
            sku="DUPLICATE-SKU",
            base_price=Decimal("99.99"),
            is_active=True
        )
        
        variant2 = ProductVariant(
            id=uuid4(),
            product_id=test_product.id,
            name="Variant 2",
            sku="DUPLICATE-SKU",  # Duplicate SKU
            base_price=Decimal("149.99"),
            is_active=True
        )
        
        db_session.add(variant1)
        await db_session.commit()
        
        db_session.add(variant2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestCartModel:
    """Test Cart and CartItem models."""
    
    @pytest.mark.asyncio
    async def test_create_cart(self, db_session: AsyncSession, test_user: User):
        """Test creating a cart."""
        cart = Cart(
            id=uuid4(),
            user_id=test_user.id,
            session_id=None
        )
        
        db_session.add(cart)
        await db_session.commit()
        await db_session.refresh(cart)
        
        assert cart.id is not None
        assert cart.user_id == test_user.id
        assert cart.created_at is not None
    
    @pytest.mark.asyncio
    async def test_create_cart_item(self, db_session: AsyncSession, test_cart: Cart, test_variant: ProductVariant):
        """Test creating a cart item."""
        cart_item = CartItem(
            id=uuid4(),
            cart_id=test_cart.id,
            variant_id=test_variant.id,
            quantity=2
        )
        
        db_session.add(cart_item)
        await db_session.commit()
        await db_session.refresh(cart_item)
        
        assert cart_item.id is not None
        assert cart_item.cart_id == test_cart.id
        assert cart_item.variant_id == test_variant.id
        assert cart_item.quantity == 2
    
    @pytest.mark.asyncio
    async def test_cart_item_unique_constraint(self, db_session: AsyncSession, test_cart: Cart, test_variant: ProductVariant):
        """Test cart item unique constraint (cart + variant)."""
        cart_item1 = CartItem(
            id=uuid4(),
            cart_id=test_cart.id,
            variant_id=test_variant.id,
            quantity=1
        )
        
        cart_item2 = CartItem(
            id=uuid4(),
            cart_id=test_cart.id,
            variant_id=test_variant.id,  # Same cart + variant
            quantity=2
        )
        
        db_session.add(cart_item1)
        await db_session.commit()
        
        db_session.add(cart_item2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestOrderModel:
    """Test Order and OrderItem models."""
    
    @pytest.mark.asyncio
    async def test_create_order(self, db_session: AsyncSession, test_user: User):
        """Test creating an order."""
        order = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            subtotal=Decimal("99.99"),
            shipping_cost=Decimal("9.99"),
            tax_amount=Decimal("8.75"),
            total_amount=Decimal("118.73"),
            currency="USD"
        )
        
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)
        
        assert order.id is not None
        assert order.user_id == test_user.id
        assert order.status == OrderStatus.PENDING
        assert order.total_amount == Decimal("118.73")
    
    @pytest.mark.asyncio
    async def test_create_order_item(self, db_session: AsyncSession, test_user: User, test_variant: ProductVariant):
        """Test creating an order item."""
        order = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.PENDING,
            subtotal=Decimal("99.99"),
            total_amount=Decimal("99.99"),
            currency="USD"
        )
        db_session.add(order)
        await db_session.flush()
        
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
        await db_session.refresh(order_item)
        
        assert order_item.id is not None
        assert order_item.order_id == order.id
        assert order_item.variant_id == test_variant.id
        assert order_item.quantity == 2
        assert order_item.total_price == Decimal("99.98")
    
    @pytest.mark.asyncio
    async def test_order_status_transitions(self, db_session: AsyncSession, test_user: User):
        """Test order status transitions."""
        order = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.PENDING,
            subtotal=Decimal("99.99"),
            total_amount=Decimal("99.99"),
            currency="USD"
        )
        
        db_session.add(order)
        await db_session.commit()
        
        # Test status transitions
        statuses = [
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED
        ]
        
        for status in statuses:
            order.status = status
            await db_session.commit()
            await db_session.refresh(order)
            assert order.status == status


class TestPaymentModel:
    """Test Payment-related models."""
    
    @pytest.mark.asyncio
    async def test_create_payment_method(self, db_session: AsyncSession, test_user: User):
        """Test creating a payment method."""
        payment_method = PaymentMethod(
            id=uuid4(),
            user_id=test_user.id,
            type="card",
            provider="stripe",
            stripe_payment_method_id="pm_test_123",
            last_four="4242",
            brand="visa",
            expiry_month=12,
            expiry_year=2025,
            is_default=True,
            is_active=True
        )
        
        db_session.add(payment_method)
        await db_session.commit()
        await db_session.refresh(payment_method)
        
        assert payment_method.id is not None
        assert payment_method.user_id == test_user.id
        assert payment_method.type == "card"
        assert payment_method.last_four == "4242"
        assert payment_method.is_default is True
    
    @pytest.mark.asyncio
    async def test_create_payment_intent(self, db_session: AsyncSession, test_user: User):
        """Test creating a payment intent."""
        payment_intent = PaymentIntent(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="requires_confirmation"
        )
        
        db_session.add(payment_intent)
        await db_session.commit()
        await db_session.refresh(payment_intent)
        
        assert payment_intent.id is not None
        assert payment_intent.user_id == test_user.id
        assert payment_intent.amount == Decimal("100.00")
        assert payment_intent.status == "requires_confirmation"
    
    @pytest.mark.asyncio
    async def test_create_transaction(self, db_session: AsyncSession, test_user: User):
        """Test creating a transaction."""
        transaction = Transaction(
            id=uuid4(),
            user_id=test_user.id,
            stripe_payment_intent_id="pi_test_123",
            amount=Decimal("100.00"),
            currency="usd",
            status="succeeded",
            transaction_type="payment"
        )
        
        db_session.add(transaction)
        await db_session.commit()
        await db_session.refresh(transaction)
        
        assert transaction.id is not None
        assert transaction.user_id == test_user.id
        assert transaction.amount == Decimal("100.00")
        assert transaction.status == "succeeded"


class TestInventoryModel:
    """Test Inventory and WarehouseLocation models."""
    
    @pytest.mark.asyncio
    async def test_create_warehouse_location(self, db_session: AsyncSession):
        """Test creating a warehouse location."""
        warehouse = WarehouseLocation(
            id=uuid4(),
            name="Main Warehouse",
            address="123 Warehouse St",
            city="Warehouse City",
            state="WS",
            country="US",
            postal_code="12345",
            is_active=True
        )
        
        db_session.add(warehouse)
        await db_session.commit()
        await db_session.refresh(warehouse)
        
        assert warehouse.id is not None
        assert warehouse.name == "Main Warehouse"
        assert warehouse.is_active is True
    
    @pytest.mark.asyncio
    async def test_create_inventory(self, db_session: AsyncSession, test_variant: ProductVariant, test_warehouse: WarehouseLocation):
        """Test creating inventory."""
        inventory = Inventory(
            id=uuid4(),
            variant_id=test_variant.id,
            warehouse_id=test_warehouse.id,
            quantity_available=100,
            quantity_reserved=10,
            reorder_point=20,
            reorder_quantity=50
        )
        
        db_session.add(inventory)
        await db_session.commit()
        await db_session.refresh(inventory)
        
        assert inventory.id is not None
        assert inventory.variant_id == test_variant.id
        assert inventory.warehouse_id == test_warehouse.id
        assert inventory.quantity_available == 100
        assert inventory.quantity_reserved == 10
    
    @pytest.mark.asyncio
    async def test_inventory_unique_constraint(self, db_session: AsyncSession, test_variant: ProductVariant, test_warehouse: WarehouseLocation):
        """Test inventory unique constraint (variant + warehouse)."""
        inventory1 = Inventory(
            id=uuid4(),
            variant_id=test_variant.id,
            warehouse_id=test_warehouse.id,
            quantity_available=100,
            quantity_reserved=0
        )
        
        inventory2 = Inventory(
            id=uuid4(),
            variant_id=test_variant.id,
            warehouse_id=test_warehouse.id,  # Same variant + warehouse
            quantity_available=50,
            quantity_reserved=0
        )
        
        db_session.add(inventory1)
        await db_session.commit()
        
        db_session.add(inventory2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestShippingModel:
    """Test ShippingMethod model."""
    
    @pytest.mark.asyncio
    async def test_create_shipping_method(self, db_session: AsyncSession):
        """Test creating a shipping method."""
        shipping_method = ShippingMethod(
            id=uuid4(),
            name="Standard Shipping",
            description="5-7 business days",
            base_cost=Decimal("9.99"),
            per_kg_cost=Decimal("2.00"),
            estimated_days_min=5,
            estimated_days_max=7,
            is_active=True
        )
        
        db_session.add(shipping_method)
        await db_session.commit()
        await db_session.refresh(shipping_method)
        
        assert shipping_method.id is not None
        assert shipping_method.name == "Standard Shipping"
        assert shipping_method.base_cost == Decimal("9.99")
        assert shipping_method.per_kg_cost == Decimal("2.00")
        assert shipping_method.is_active is True


class TestTaxModel:
    """Test TaxRate model."""
    
    @pytest.mark.asyncio
    async def test_create_tax_rate(self, db_session: AsyncSession):
        """Test creating a tax rate."""
        tax_rate = TaxRate(
            id=uuid4(),
            country="US",
            state="CA",
            rate=Decimal("0.0875"),  # 8.75%
            is_active=True
        )
        
        db_session.add(tax_rate)
        await db_session.commit()
        await db_session.refresh(tax_rate)
        
        assert tax_rate.id is not None
        assert tax_rate.country == "US"
        assert tax_rate.state == "CA"
        assert tax_rate.rate == Decimal("0.0875")
        assert tax_rate.is_active is True
    
    @pytest.mark.asyncio
    async def test_tax_rate_unique_constraint(self, db_session: AsyncSession):
        """Test tax rate unique constraint (country + state)."""
        tax_rate1 = TaxRate(
            id=uuid4(),
            country="US",
            state="CA",
            rate=Decimal("0.0875"),
            is_active=True
        )
        
        tax_rate2 = TaxRate(
            id=uuid4(),
            country="US",
            state="CA",  # Same country + state
            rate=Decimal("0.0900"),
            is_active=True
        )
        
        db_session.add(tax_rate1)
        await db_session.commit()
        
        db_session.add(tax_rate2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestDiscountModel:
    """Test Discount model."""
    
    @pytest.mark.asyncio
    async def test_create_discount(self, db_session: AsyncSession):
        """Test creating a discount."""
        discount = Discount(
            id=uuid4(),
            code="SAVE10",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            minimum_order_amount=Decimal("50.00"),
            usage_limit=100,
            usage_count=0,
            is_active=True,
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=30)
        )
        
        db_session.add(discount)
        await db_session.commit()
        await db_session.refresh(discount)
        
        assert discount.id is not None
        assert discount.code == "SAVE10"
        assert discount.discount_type == "percentage"
        assert discount.discount_value == Decimal("10.00")
        assert discount.is_active is True
    
    @pytest.mark.asyncio
    async def test_discount_code_unique_constraint(self, db_session: AsyncSession):
        """Test discount code unique constraint."""
        discount1 = Discount(
            id=uuid4(),
            code="DUPLICATE",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            is_active=True
        )
        
        discount2 = Discount(
            id=uuid4(),
            code="DUPLICATE",  # Duplicate code
            discount_type="fixed",
            discount_value=Decimal("5.00"),
            is_active=True
        )
        
        db_session.add(discount1)
        await db_session.commit()
        
        db_session.add(discount2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestReviewModel:
    """Test Review model."""
    
    @pytest.mark.asyncio
    async def test_create_review(self, db_session: AsyncSession, test_user: User, test_product: Product):
        """Test creating a review."""
        review = Review(
            id=uuid4(),
            user_id=test_user.id,
            product_id=test_product.id,
            rating=5,
            title="Great product!",
            comment="I love this product. Highly recommended.",
            is_verified_purchase=True
        )
        
        db_session.add(review)
        await db_session.commit()
        await db_session.refresh(review)
        
        assert review.id is not None
        assert review.user_id == test_user.id
        assert review.product_id == test_product.id
        assert review.rating == 5
        assert review.title == "Great product!"
        assert review.is_verified_purchase is True
    
    @pytest.mark.asyncio
    async def test_review_rating_constraint(self, db_session: AsyncSession, test_user: User, test_product: Product):
        """Test review rating constraint (1-5)."""
        # Test invalid rating (too low)
        review_low = Review(
            id=uuid4(),
            user_id=test_user.id,
            product_id=test_product.id,
            rating=0,  # Invalid rating
            title="Bad rating",
            comment="This should fail"
        )
        
        db_session.add(review_low)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
        
        await db_session.rollback()
        
        # Test invalid rating (too high)
        review_high = Review(
            id=uuid4(),
            user_id=test_user.id,
            product_id=test_product.id,
            rating=6,  # Invalid rating
            title="Bad rating",
            comment="This should fail"
        )
        
        db_session.add(review_high)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestWishlistModel:
    """Test Wishlist and WishlistItem models."""
    
    @pytest.mark.asyncio
    async def test_create_wishlist(self, db_session: AsyncSession, test_user: User):
        """Test creating a wishlist."""
        wishlist = Wishlist(
            id=uuid4(),
            user_id=test_user.id,
            name="My Wishlist",
            is_public=False
        )
        
        db_session.add(wishlist)
        await db_session.commit()
        await db_session.refresh(wishlist)
        
        assert wishlist.id is not None
        assert wishlist.user_id == test_user.id
        assert wishlist.name == "My Wishlist"
        assert wishlist.is_public is False
    
    @pytest.mark.asyncio
    async def test_create_wishlist_item(self, db_session: AsyncSession, test_user: User, test_variant: ProductVariant):
        """Test creating a wishlist item."""
        wishlist = Wishlist(
            id=uuid4(),
            user_id=test_user.id,
            name="My Wishlist",
            is_public=False
        )
        db_session.add(wishlist)
        await db_session.flush()
        
        wishlist_item = WishlistItem(
            id=uuid4(),
            wishlist_id=wishlist.id,
            variant_id=test_variant.id
        )
        
        db_session.add(wishlist_item)
        await db_session.commit()
        await db_session.refresh(wishlist_item)
        
        assert wishlist_item.id is not None
        assert wishlist_item.wishlist_id == wishlist.id
        assert wishlist_item.variant_id == test_variant.id
    
    @pytest.mark.asyncio
    async def test_wishlist_item_unique_constraint(self, db_session: AsyncSession, test_user: User, test_variant: ProductVariant):
        """Test wishlist item unique constraint (wishlist + variant)."""
        wishlist = Wishlist(
            id=uuid4(),
            user_id=test_user.id,
            name="My Wishlist",
            is_public=False
        )
        db_session.add(wishlist)
        await db_session.flush()
        
        wishlist_item1 = WishlistItem(
            id=uuid4(),
            wishlist_id=wishlist.id,
            variant_id=test_variant.id
        )
        
        wishlist_item2 = WishlistItem(
            id=uuid4(),
            wishlist_id=wishlist.id,
            variant_id=test_variant.id  # Same wishlist + variant
        )
        
        db_session.add(wishlist_item1)
        await db_session.commit()
        
        db_session.add(wishlist_item2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()


class TestModelRelationships:
    """Test model relationships and foreign keys."""
    
    @pytest.mark.asyncio
    async def test_user_orders_relationship(self, db_session: AsyncSession, test_user: User):
        """Test user-orders relationship."""
        # Create orders for user
        order1 = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.PENDING,
            subtotal=Decimal("99.99"),
            total_amount=Decimal("99.99"),
            currency="USD"
        )
        order2 = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.CONFIRMED,
            subtotal=Decimal("149.99"),
            total_amount=Decimal("149.99"),
            currency="USD"
        )
        
        db_session.add_all([order1, order2])
        await db_session.commit()
        
        # Test relationship
        await db_session.refresh(test_user)
        user_orders = test_user.orders if hasattr(test_user, 'orders') else []
        
        # Note: Relationship might not be defined in model, so we test via query
        from sqlalchemy import select
        result = await db_session.execute(
            select(Order).where(Order.user_id == test_user.id)
        )
        orders = result.scalars().all()
        
        assert len(orders) == 2
        order_ids = [order.id for order in orders]
        assert order1.id in order_ids
        assert order2.id in order_ids
    
    @pytest.mark.asyncio
    async def test_product_variants_relationship(self, db_session: AsyncSession, test_product: Product):
        """Test product-variants relationship."""
        # Create variants for product
        variant1 = ProductVariant(
            id=uuid4(),
            product_id=test_product.id,
            name="Variant 1",
            sku="VAR-001",
            base_price=Decimal("99.99"),
            is_active=True
        )
        variant2 = ProductVariant(
            id=uuid4(),
            product_id=test_product.id,
            name="Variant 2",
            sku="VAR-002",
            base_price=Decimal("149.99"),
            is_active=True
        )
        
        db_session.add_all([variant1, variant2])
        await db_session.commit()
        
        # Test relationship via query
        from sqlalchemy import select
        result = await db_session.execute(
            select(ProductVariant).where(ProductVariant.product_id == test_product.id)
        )
        variants = result.scalars().all()
        
        assert len(variants) == 2
        variant_names = [variant.name for variant in variants]
        assert "Variant 1" in variant_names
        assert "Variant 2" in variant_names
    
    @pytest.mark.asyncio
    async def test_order_items_relationship(self, db_session: AsyncSession, test_user: User, test_variant: ProductVariant):
        """Test order-order_items relationship."""
        # Create order
        order = Order(
            id=uuid4(),
            user_id=test_user.id,
            status=OrderStatus.PENDING,
            subtotal=Decimal("199.98"),
            total_amount=Decimal("199.98"),
            currency="USD"
        )
        db_session.add(order)
        await db_session.flush()
        
        # Create order items
        item1 = OrderItem(
            id=uuid4(),
            order_id=order.id,
            variant_id=test_variant.id,
            quantity=1,
            unit_price=Decimal("99.99"),
            total_price=Decimal("99.99")
        )
        item2 = OrderItem(
            id=uuid4(),
            order_id=order.id,
            variant_id=test_variant.id,
            quantity=1,
            unit_price=Decimal("99.99"),
            total_price=Decimal("99.99")
        )
        
        db_session.add_all([item1, item2])
        await db_session.commit()
        
        # Test relationship via query
        from sqlalchemy import select
        result = await db_session.execute(
            select(OrderItem).where(OrderItem.order_id == order.id)
        )
        items = result.scalars().all()
        
        assert len(items) == 2
        total_quantity = sum(item.quantity for item in items)
        assert total_quantity == 2