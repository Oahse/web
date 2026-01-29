"""
Tests for cart service
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from decimal import Decimal

from services.cart import CartService
from models.cart import Cart, CartItem
from models.user import User
from models.product import ProductVariant
from models.inventories import Inventory, WarehouseLocation


class TestCartService:
    """Test cart service."""
    
    @pytest.mark.asyncio
    async def test_get_or_create_cart_existing(self, db_session: AsyncSession, test_user: User, test_cart: Cart):
        """Test getting existing cart."""
        cart_service = CartService(db_session)
        
        cart = await cart_service.get_or_create_cart(test_user.id)
        
        assert cart is not None
        assert cart.id == test_cart.id
        assert cart.user_id == test_user.id
    
    @pytest.mark.asyncio
    async def test_get_or_create_cart_new(self, db_session: AsyncSession, test_user: User):
        """Test creating new cart when none exists."""
        cart_service = CartService(db_session)
        
        cart = await cart_service.get_or_create_cart(test_user.id)
        
        assert cart is not None
        assert cart.user_id == test_user.id
        assert cart.created_at is not None
    
    @pytest.mark.asyncio
    async def test_add_item_to_cart_new_item(self, db_session: AsyncSession, test_cart: Cart, test_variant: ProductVariant, test_inventory):
        """Test adding new item to cart."""
        cart_service = CartService(db_session)
        
        cart_item = await cart_service.add_item_to_cart(
            cart_id=test_cart.id,
            variant_id=test_variant.id,
            quantity=3
        )
        
        assert cart_item is not None
        assert cart_item.cart_id == test_cart.id
        assert cart_item.variant_id == test_variant.id
        assert cart_item.quantity == 3
    
    @pytest.mark.asyncio
    async def test_add_item_to_cart_existing_item(self, db_session: AsyncSession, test_cart_item: CartItem, test_inventory):
        """Test adding to existing cart item (should update quantity)."""
        cart_service = CartService(db_session)
        original_quantity = test_cart_item.quantity
        
        updated_item = await cart_service.add_item_to_cart(
            cart_id=test_cart_item.cart_id,
            variant_id=test_cart_item.variant_id,
            quantity=2
        )
        
        assert updated_item is not None
        assert updated_item.id == test_cart_item.id
        assert updated_item.quantity == original_quantity + 2
    
    @pytest.mark.asyncio
    async def test_add_item_insufficient_stock(self, db_session: AsyncSession, test_cart: Cart, test_variant: ProductVariant, test_inventory):
        """Test adding item with insufficient stock."""
        cart_service = CartService(db_session)
        
        with pytest.raises(Exception) as exc_info:
            await cart_service.add_item_to_cart(
                cart_id=test_cart.id,
                variant_id=test_variant.id,
                quantity=test_inventory.quantity_available + 10
            )
        
        assert "insufficient stock" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_add_item_inactive_variant(self, db_session: AsyncSession, test_cart: Cart, test_product):
        """Test adding inactive variant to cart."""
        # Create inactive variant
        inactive_variant = ProductVariant(
            id=uuid4(),
            product_id=test_product.id,
            name="Inactive Variant",
            sku="INACTIVE-001",
            base_price=Decimal("99.99"),
            is_active=False
        )
        db_session.add(inactive_variant)
        await db_session.commit()
        
        cart_service = CartService(db_session)
        
        with pytest.raises(Exception) as exc_info:
            await cart_service.add_item_to_cart(
                cart_id=test_cart.id,
                variant_id=inactive_variant.id,
                quantity=1
            )
        
        assert "inactive" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_update_cart_item_quantity(self, db_session: AsyncSession, test_cart_item: CartItem, test_inventory):
        """Test updating cart item quantity."""
        cart_service = CartService(db_session)
        
        updated_item = await cart_service.update_cart_item_quantity(
            cart_item_id=test_cart_item.id,
            quantity=5
        )
        
        assert updated_item is not None
        assert updated_item.quantity == 5
    
    @pytest.mark.asyncio
    async def test_update_cart_item_insufficient_stock(self, db_session: AsyncSession, test_cart_item: CartItem, test_inventory):
        """Test updating cart item with insufficient stock."""
        cart_service = CartService(db_session)
        
        with pytest.raises(Exception) as exc_info:
            await cart_service.update_cart_item_quantity(
                cart_item_id=test_cart_item.id,
                quantity=test_inventory.quantity_available + 10
            )
        
        assert "insufficient stock" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_remove_cart_item(self, db_session: AsyncSession, test_cart_item: CartItem):
        """Test removing cart item."""
        cart_service = CartService(db_session)
        
        result = await cart_service.remove_cart_item(test_cart_item.id)
        
        assert result is True
        
        # Verify item is deleted
        deleted_item = await cart_service.get_cart_item_by_id(test_cart_item.id)
        assert deleted_item is None
    
    @pytest.mark.asyncio
    async def test_remove_cart_item_not_found(self, db_session: AsyncSession):
        """Test removing nonexistent cart item."""
        cart_service = CartService(db_session)
        
        result = await cart_service.remove_cart_item(uuid4())
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_clear_cart(self, db_session: AsyncSession, test_cart: Cart, test_cart_item: CartItem):
        """Test clearing cart."""
        cart_service = CartService(db_session)
        
        result = await cart_service.clear_cart(test_cart.id)
        
        assert result is True
        
        # Verify cart is empty
        cart_items = await cart_service.get_cart_items(test_cart.id)
        assert len(cart_items) == 0
    
    @pytest.mark.asyncio
    async def test_get_cart_items(self, db_session: AsyncSession, test_cart: Cart, test_cart_item: CartItem):
        """Test getting cart items."""
        cart_service = CartService(db_session)
        
        cart_items = await cart_service.get_cart_items(test_cart.id)
        
        assert len(cart_items) >= 1
        assert cart_items[0].id == test_cart_item.id
        assert cart_items[0].cart_id == test_cart.id
    
    @pytest.mark.asyncio
    async def test_get_cart_with_items(self, db_session: AsyncSession, test_cart: Cart, test_cart_item: CartItem):
        """Test getting cart with items."""
        cart_service = CartService(db_session)
        
        cart = await cart_service.get_cart_with_items(test_cart.id)
        
        assert cart is not None
        assert cart.id == test_cart.id
        assert len(cart.items) >= 1
        assert cart.items[0].id == test_cart_item.id
    
    @pytest.mark.asyncio
    async def test_calculate_cart_total(self, db_session: AsyncSession, test_cart: Cart, test_cart_item: CartItem, test_variant: ProductVariant):
        """Test calculating cart total."""
        cart_service = CartService(db_session)
        
        total = await cart_service.calculate_cart_total(test_cart.id)
        
        expected_total = (test_variant.sale_price or test_variant.base_price) * test_cart_item.quantity
        assert total == expected_total
    
    @pytest.mark.asyncio
    async def test_calculate_cart_total_empty_cart(self, db_session: AsyncSession, test_user: User):
        """Test calculating total for empty cart."""
        # Create empty cart
        empty_cart = Cart(
            id=uuid4(),
            user_id=test_user.id
        )
        db_session.add(empty_cart)
        await db_session.commit()
        
        cart_service = CartService(db_session)
        
        total = await cart_service.calculate_cart_total(empty_cart.id)
        
        assert total == Decimal("0.00")
    
    @pytest.mark.asyncio
    async def test_validate_cart_success(self, db_session: AsyncSession, test_cart: Cart, test_cart_item: CartItem, test_inventory):
        """Test cart validation with valid cart."""
        cart_service = CartService(db_session)
        
        validation_result = await cart_service.validate_cart(test_cart.id)
        
        assert validation_result["is_valid"] is True
        assert len(validation_result["issues"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_cart_with_stock_issues(self, db_session: AsyncSession, test_cart: Cart, test_variant: ProductVariant, test_inventory):
        """Test cart validation with stock issues."""
        # Create cart item with quantity exceeding stock
        cart_item = CartItem(
            id=uuid4(),
            cart_id=test_cart.id,
            variant_id=test_variant.id,
            quantity=test_inventory.quantity_available + 10
        )
        db_session.add(cart_item)
        await db_session.commit()
        
        cart_service = CartService(db_session)
        
        validation_result = await cart_service.validate_cart(test_cart.id)
        
        assert validation_result["is_valid"] is False
        assert len(validation_result["issues"]) > 0
        assert any("insufficient stock" in issue.lower() for issue in validation_result["issues"])
    
    @pytest.mark.asyncio
    async def test_validate_cart_with_inactive_variants(self, db_session: AsyncSession, test_cart: Cart, test_product):
        """Test cart validation with inactive variants."""
        # Create inactive variant
        inactive_variant = ProductVariant(
            id=uuid4(),
            product_id=test_product.id,
            name="Inactive Variant",
            sku="INACTIVE-001",
            base_price=Decimal("99.99"),
            is_active=False
        )
        db_session.add(inactive_variant)
        
        # Create cart item with inactive variant
        cart_item = CartItem(
            id=uuid4(),
            cart_id=test_cart.id,
            variant_id=inactive_variant.id,
            quantity=1
        )
        db_session.add(cart_item)
        await db_session.commit()
        
        cart_service = CartService(db_session)
        
        validation_result = await cart_service.validate_cart(test_cart.id)
        
        assert validation_result["is_valid"] is False
        assert len(validation_result["issues"]) > 0
        assert any("inactive" in issue.lower() for issue in validation_result["issues"])
    
    @pytest.mark.asyncio
    async def test_get_cart_item_count(self, db_session: AsyncSession, test_cart: Cart, test_cart_item: CartItem):
        """Test getting cart item count."""
        cart_service = CartService(db_session)
        
        count = await cart_service.get_cart_item_count(test_cart.id)
        
        assert count == test_cart_item.quantity
    
    @pytest.mark.asyncio
    async def test_get_cart_unique_item_count(self, db_session: AsyncSession, test_cart: Cart, test_cart_item: CartItem):
        """Test getting unique item count in cart."""
        cart_service = CartService(db_session)
        
        count = await cart_service.get_cart_unique_item_count(test_cart.id)
        
        assert count >= 1
    
    @pytest.mark.asyncio
    async def test_merge_carts(self, db_session: AsyncSession, test_user: User, test_variant: ProductVariant, test_inventory):
        """Test merging two carts."""
        # Create two carts
        cart1 = Cart(id=uuid4(), user_id=test_user.id)
        cart2 = Cart(id=uuid4(), user_id=test_user.id)
        db_session.add_all([cart1, cart2])
        await db_session.flush()
        
        # Add items to both carts
        item1 = CartItem(
            id=uuid4(),
            cart_id=cart1.id,
            variant_id=test_variant.id,
            quantity=2
        )
        item2 = CartItem(
            id=uuid4(),
            cart_id=cart2.id,
            variant_id=test_variant.id,
            quantity=3
        )
        db_session.add_all([item1, item2])
        await db_session.commit()
        
        cart_service = CartService(db_session)
        
        merged_cart = await cart_service.merge_carts(cart1.id, cart2.id)
        
        assert merged_cart is not None
        assert merged_cart.id == cart1.id  # Should merge into first cart
        
        # Verify merged quantity
        cart_items = await cart_service.get_cart_items(cart1.id)
        assert len(cart_items) == 1
        assert cart_items[0].quantity == 5  # 2 + 3
    
    @pytest.mark.asyncio
    async def test_apply_cart_discount(self, db_session: AsyncSession, test_cart: Cart, test_cart_item: CartItem):
        """Test applying discount to cart."""
        cart_service = CartService(db_session)
        
        # Apply 10% discount
        discounted_total = await cart_service.apply_cart_discount(
            cart_id=test_cart.id,
            discount_percentage=Decimal("10.00")
        )
        
        original_total = await cart_service.calculate_cart_total(test_cart.id)
        expected_discount = original_total * Decimal("0.10")
        expected_total = original_total - expected_discount
        
        assert discounted_total == expected_total
    
    @pytest.mark.asyncio
    async def test_estimate_shipping_weight(self, db_session: AsyncSession, test_cart: Cart, test_cart_item: CartItem, test_variant: ProductVariant):
        """Test estimating shipping weight for cart."""
        # Set variant weight
        test_variant.weight = Decimal("2.5")
        await db_session.commit()
        
        cart_service = CartService(db_session)
        
        total_weight = await cart_service.estimate_shipping_weight(test_cart.id)
        
        expected_weight = test_variant.weight * test_cart_item.quantity
        assert total_weight == expected_weight
    
    @pytest.mark.asyncio
    async def test_check_cart_availability(self, db_session: AsyncSession, test_cart: Cart, test_cart_item: CartItem, test_inventory):
        """Test checking cart item availability."""
        cart_service = CartService(db_session)
        
        availability = await cart_service.check_cart_availability(test_cart.id)
        
        assert "available_items" in availability
        assert "unavailable_items" in availability
        assert len(availability["available_items"]) >= 1
        assert len(availability["unavailable_items"]) == 0


class TestCartServiceSecurity:
    """Test cart service security features."""
    
    @pytest.mark.asyncio
    async def test_cart_ownership_validation(self, db_session: AsyncSession, test_user: User, test_variant: ProductVariant):
        """Test cart ownership validation."""
        # Create another user and their cart
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
        
        other_cart = Cart(
            id=uuid4(),
            user_id=other_user.id
        )
        db_session.add(other_cart)
        await db_session.commit()
        
        cart_service = CartService(db_session)
        
        # Try to add item to other user's cart
        with pytest.raises(Exception) as exc_info:
            await cart_service.add_item_to_cart(
                cart_id=other_cart.id,
                variant_id=test_variant.id,
                quantity=1,
                user_id=test_user.id  # Different user
            )
        
        assert "unauthorized" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_cart_item_quantity_limits(self, db_session: AsyncSession, test_cart: Cart, test_variant: ProductVariant, test_inventory):
        """Test cart item quantity limits."""
        cart_service = CartService(db_session)
        
        # Test maximum quantity limit
        with pytest.raises(Exception) as exc_info:
            await cart_service.add_item_to_cart(
                cart_id=test_cart.id,
                variant_id=test_variant.id,
                quantity=999999  # Excessive quantity
            )
        
        assert "quantity limit" in str(exc_info.value).lower() or "insufficient stock" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_cart_session_validation(self, db_session: AsyncSession):
        """Test cart session validation for guest users."""
        cart_service = CartService(db_session)
        session_id = "guest_session_123"
        
        # Create guest cart
        guest_cart = await cart_service.get_or_create_guest_cart(session_id)
        
        assert guest_cart is not None
        assert guest_cart.session_id == session_id
        assert guest_cart.user_id is None
    
    @pytest.mark.asyncio
    async def test_cart_expiration(self, db_session: AsyncSession, test_user: User):
        """Test cart expiration for inactive carts."""
        from datetime import datetime, timedelta
        
        # Create old cart
        old_cart = Cart(
            id=uuid4(),
            user_id=test_user.id,
            created_at=datetime.utcnow() - timedelta(days=30)  # 30 days old
        )
        db_session.add(old_cart)
        await db_session.commit()
        
        cart_service = CartService(db_session)
        
        # Check if cart is considered expired
        is_expired = await cart_service.is_cart_expired(old_cart.id)
        
        assert is_expired is True
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_carts(self, db_session: AsyncSession, test_user: User):
        """Test cleaning up expired carts."""
        from datetime import datetime, timedelta
        
        # Create expired cart
        expired_cart = Cart(
            id=uuid4(),
            user_id=test_user.id,
            created_at=datetime.utcnow() - timedelta(days=60)  # 60 days old
        )
        db_session.add(expired_cart)
        await db_session.commit()
        
        cart_service = CartService(db_session)
        
        # Cleanup expired carts
        cleaned_count = await cart_service.cleanup_expired_carts()
        
        assert cleaned_count >= 1
        
        # Verify cart was deleted
        deleted_cart = await cart_service.get_cart_by_id(expired_cart.id)
        assert deleted_cart is None


class TestCartServicePerformance:
    """Test cart service performance optimizations."""
    
    @pytest.mark.asyncio
    async def test_bulk_add_items(self, db_session: AsyncSession, test_cart: Cart, test_product, test_warehouse: WarehouseLocation):
        """Test bulk adding items to cart."""
        # Create multiple variants
        variants = []
        for i in range(5):
            variant = ProductVariant(
                id=uuid4(),
                product_id=test_product.id,
                name=f"Bulk Variant {i}",
                sku=f"BULK-{i:03d}",
                base_price=Decimal("50.00"),
                is_active=True
            )
            variants.append(variant)
            
            # Create inventory for each variant
            inventory = Inventory(
                id=uuid4(),
                variant_id=variant.id,
                warehouse_id=test_warehouse.id,
                quantity_available=100,
                quantity_reserved=0
            )
            db_session.add_all([variant, inventory])
        
        await db_session.commit()
        
        cart_service = CartService(db_session)
        
        # Bulk add items
        items_to_add = [
            {"variant_id": variant.id, "quantity": 2}
            for variant in variants
        ]
        
        result = await cart_service.bulk_add_items(test_cart.id, items_to_add)
        
        assert result["successful"] == 5
        assert result["failed"] == 0
        
        # Verify items were added
        cart_items = await cart_service.get_cart_items(test_cart.id)
        assert len(cart_items) >= 5
    
    @pytest.mark.asyncio
    async def test_cart_caching(self, db_session: AsyncSession, test_cart: Cart, test_cart_item: CartItem, mock_redis):
        """Test cart caching functionality."""
        cart_service = CartService(db_session)
        
        # Mock Redis cache
        mock_redis.get.return_value = None  # Cache miss
        mock_redis.set.return_value = True
        
        # Get cart (should cache it)
        cart = await cart_service.get_cart_with_items(test_cart.id, use_cache=True)
        
        assert cart is not None
        # Verify cache was set
        mock_redis.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_cart_preloading(self, db_session: AsyncSession, test_cart: Cart, test_cart_item: CartItem):
        """Test cart preloading with relationships."""
        cart_service = CartService(db_session)
        
        # Get cart with preloaded relationships
        cart = await cart_service.get_cart_with_preloaded_data(test_cart.id)
        
        assert cart is not None
        assert hasattr(cart, 'items')
        assert len(cart.items) >= 1
        
        # Verify variant data is preloaded
        cart_item = cart.items[0]
        assert hasattr(cart_item, 'variant')
        assert cart_item.variant is not None