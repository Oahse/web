from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from models.cart import Cart, CartItem
from models.product import ProductVariant
from schemas.cart import CartResponse, CartItemResponse
from schemas.product import ProductVariantResponse
from services.promocode import PromocodeService
from services.shipping import ShippingService
from services.payment import PaymentService
from uuid import UUID # Import UUID
from datetime import datetime
class CartService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_cart(self, user_id: UUID) -> Cart:
        query = select(Cart).where(Cart.user_id == user_id).options(
            selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.images),
            selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product)
        )
        result = await self.db.execute(query)
        cart = result.scalar_one_or_none()

        if not cart:
            cart = Cart(user_id=user_id, promocode_id=None)
            self.db.add(cart)
            await self.db.commit()
            await self.db.refresh(cart)

        return cart

    async def add_to_cart(self, user_id: UUID, variant_id: UUID, quantity: int) -> CartResponse:
        cart = await self.get_or_create_cart(user_id)

        variant = (await self.db.execute(
            select(ProductVariant).where(ProductVariant.id == variant_id)
        )).scalar_one_or_none()
        if not variant:
            raise HTTPException(status_code=404, detail="Product variant not found")

        if variant.stock < quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {variant.name}. Available: {variant.stock}")

        item = cart.get_item(variant.id)
        if item:
            new_quantity = item.quantity + quantity
            if new_quantity > variant.stock:
                raise HTTPException(status_code=400, detail=f"Cannot add {quantity} more of {variant.name}. Only {variant.stock - item.quantity} available.")
            item.quantity = new_quantity
            item.recalc_total()
        else:
            price = variant.sale_price or variant.base_price
            self.db.add(CartItem(
                cart_id=cart.id,
                variant_id=variant.id,
                quantity=quantity,
                price_per_unit=price,
                total_price=price * quantity
            ))

        await self.db.commit()
        await self.db.refresh(cart)
        return await self.get_cart(user_id)

    async def get_cart(self, user_id: UUID) -> CartResponse:
        cart = await self.get_or_create_cart(user_id)
        active_items = [item for item in cart.items if not item.saved_for_later]
        
        # Convert cart items with proper datetime handling
        serialized_items = []
        for item in active_items:
            try:
                # Serialize variant as ProductVariantResponse
                variant_dict = self._serialize_variant(item.variant)
                variant_response = ProductVariantResponse.model_validate(variant_dict) if variant_dict else None
                
                item_dict = {
                    "id": item.id,
                    "variant": variant_response,
                    "quantity": item.quantity,
                    "price_per_unit": item.price_per_unit,
                    "total_price": item.total_price,
                    "created_at": item.created_at.isoformat() if item.created_at else None
                }
                serialized_items.append(CartItemResponse.model_validate(item_dict))
            except Exception as e:
                print(f"Error serializing cart item {item.id}: {e}")
                # Skip problematic items rather than failing the entire request
                continue
        
        return CartResponse(
            items=serialized_items,
            subtotal=cart.subtotal(),
            tax_amount=cart.tax_amount(),
            shipping_amount=cart.shipping_amount(),
            total_amount=cart.total_amount()
        )

    def _serialize_variant(self, variant):
        """Helper method to serialize product variant with proper datetime handling"""
        if not variant:
            return None
            
        try:
            # Use the model's built-in to_dict method which handles datetime serialization
            # Include product information so we get product_name and product_description
            return variant.to_dict(include_images=True, include_product=True)
        except Exception as e:
            print(f"Error serializing variant {getattr(variant, 'id', 'unknown')}: {e}")
            # Return a minimal variant object to prevent complete failure
            return {
                "id": str(getattr(variant, 'id', '')),
                "product_id": str(getattr(variant, 'product_id', '')),
                "sku": getattr(variant, 'sku', ''),
                "name": getattr(variant, 'name', ''),
                "base_price": getattr(variant, 'base_price', 0.0),
                "sale_price": getattr(variant, 'sale_price', None),
                "current_price": getattr(variant, 'sale_price', None) or getattr(variant, 'base_price', 0.0),
                "discount_percentage": 0,
                "stock": getattr(variant, 'stock', 0),
                "attributes": {},
                "is_active": True,
                "images": [],
                "primary_image": None,
                "product_name": getattr(variant.product, 'name', None) if hasattr(variant, 'product') and variant.product else None,
                "product_description": getattr(variant.product, 'description', None) if hasattr(variant, 'product') and variant.product else None,
                "created_at": None,
                "updated_at": None
            }

    async def update_cart_item_quantity(self, user_id: UUID, item_id: UUID, quantity: int) -> CartResponse:
        cart = await self.get_or_create_cart(user_id)
        item = next((i for i in cart.items if i.id == item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        if quantity <= 0:
            await self.db.delete(item)
        else:
            item.quantity = quantity
            item.recalc_total()

        await self.db.commit()
        await self.db.refresh(cart)
        return await self.get_cart(user_id)

    async def remove_from_cart(self, user_id: UUID, item_id: UUID) -> CartResponse:
        cart = await self.get_or_create_cart(user_id)
        item = next((i for i in cart.items if i.id == item_id), None)
        if item:
            await self.db.delete(item)
            await self.db.commit()
        await self.db.refresh(cart)
        return await self.get_cart(user_id)

    async def clear_cart(self, user_id: UUID) -> CartResponse:
        cart = await self.get_or_create_cart(user_id)
        for item in list(cart.items):
            await self.db.delete(item)
        await self.db.commit()
        await self.db.refresh(cart)
        return await self.get_cart(user_id)

    # ---------------- Additional Methods Using Model ---------------- #

    async def apply_promocode(self, user_id: UUID, code: str):
        cart = await self.get_or_create_cart(user_id)
        promocode_service = PromocodeService(self.db)
        promocode = await promocode_service.get_promocode_by_code(code)

        if not promocode:
            raise HTTPException(status_code=400, detail="Invalid or inactive promocode")

        if promocode.expiration_date and promocode.expiration_date < datetime.now():
            raise HTTPException(status_code=400, detail="Promocode has expired")

        discount_amount = 0.0
        if promocode.discount_type == "fixed":
            discount_amount = promocode.value
        elif promocode.discount_type == "percentage":
            discount_amount = cart.subtotal() * promocode.value
        elif promocode.discount_type == "shipping":
            discount_amount = cart.shipping_amount()

        cart.promocode_id = promocode.id
        cart.discount_amount = discount_amount
        await self.db.commit()
        await self.db.refresh(cart)

        # Send WebSocket notification
        await self._notify_cart_updated(user_id)
        
        return {
            "message": f"Promocode {code} applied",
            "promocode": promocode.code,
            "discount_type": promocode.discount_type,
            "discount_value": promocode.value,
            "discount_amount": discount_amount,
            "total_amount": cart.total_amount(),
            "cart": await self.get_cart(user_id)
        }

    async def remove_promocode(self, user_id: UUID):
        cart = await self.get_or_create_cart(user_id)
        cart.promocode_id = None
        cart.discount_amount = 0.0
        await self.db.commit()
        await self.db.refresh(cart)
        return {"message": "Promocode removed", "cart": await self.get_cart(user_id)}

    async def get_cart_item_count(self, user_id: UUID):
        cart = await self.get_or_create_cart(user_id)
        return {"count": cart.item_count()}

    async def validate_cart(self, user_id: UUID):
        cart = await self.get_or_create_cart(user_id)
        return cart.validate() | {"cart": await self.get_cart(user_id)}

    async def get_shipping_options(self, user_id: UUID, address: dict):
        shipping_service = ShippingService(self.db)
        active_methods = await shipping_service.get_all_active_shipping_methods()
        
        options = []
        for method in active_methods:
            # For now, we use the method's base price. More complex logic would involve
            # calling shipping_service.calculate_shipping_cost for each method based on cart contents.
            options.append({
                "id": str(method.id),
                "name": method.name,
                "description": method.description,
                "price": method.price,
                "estimated_days": method.estimated_days
            })
        
        # Example: Offer free shipping if cart subtotal is above a certain threshold
        cart = await self.get_or_create_cart(user_id)
        if cart.subtotal() >= 50:
            options.append({"id": "free_shipping", "name": "Free Shipping", "description": "Orders over $50", "price": 0.00, "estimated_days": 5})

        return options

    async def calculate_totals(self, user_id: UUID, data: dict):
        cart = await self.get_or_create_cart(user_id)
        discount = data.get("discount_amount", 0.0)
        return {
            "subtotal": cart.subtotal(),
            "tax_amount": cart.tax_amount(),
            "shipping_amount": cart.shipping_amount(),
            "discount_amount": discount,
            "total_amount": cart.total_amount(discount=discount),
            "currency": "USD"
        }

    async def save_for_later(self, user_id: UUID, item_id: UUID):
        cart = await self.get_or_create_cart(user_id)
        item = next((i for i in cart.items if i.id == item_id), None)
        if item:
            item.saved_for_later = True
            await self.db.commit()
            await self.db.refresh(cart)
            return {"message": "Item saved for later", "cart": await self.get_cart(user_id), "saved_items": await self.get_saved_items(user_id)}
        raise HTTPException(status_code=404, detail="Cart item not found")

    async def move_to_cart(self, user_id: UUID, item_id: UUID):
        cart = await self.get_or_create_cart(user_id)
        item = next((i for i in cart.items if i.id == item_id and i.saved_for_later), None)
        if item:
            item.saved_for_later = False
            await self.db.commit()
            await self.db.refresh(cart)
            return {"message": "Item moved to cart", "cart": await self.get_cart(user_id), "saved_items": await self.get_saved_items(user_id)}
        raise HTTPException(status_code=404, detail="Saved item not found")

    async def get_saved_items(self, user_id: UUID) -> list[CartItemResponse]:
        cart = await self.get_or_create_cart(user_id)
        saved_items = [item for item in cart.items if item.saved_for_later]
        
        serialized_items = []
        for item in saved_items:
            try:
                # Serialize variant as ProductVariantResponse
                variant_dict = self._serialize_variant(item.variant)
                variant_response = ProductVariantResponse.model_validate(variant_dict) if variant_dict else None
                
                item_dict = {
                    "id": item.id,
                    "variant": variant_response,
                    "quantity": item.quantity,
                    "price_per_unit": item.price_per_unit,
                    "total_price": item.total_price,
                    "created_at": item.created_at.isoformat() if item.created_at else None
                }
                serialized_items.append(CartItemResponse.model_validate(item_dict))
            except Exception as e:
                print(f"Error serializing saved item {item.id}: {e}")
                continue
        
        return serialized_items

    async def merge_cart(self, user_id: UUID, items: list):
        for item in items:
            await self.add_to_cart(user_id, UUID(item["variant_id"]), item["quantity"])
        return await self.get_cart(user_id)

    async def get_checkout_summary(self, user_id: UUID):
        cart = await self.get_or_create_cart(user_id)
        payment_service = PaymentService(self.db)
        shipping_service = ShippingService(self.db)

        available_payment_methods = await payment_service.get_payment_methods(user_id)
        available_shipping_options = await shipping_service.get_all_active_shipping_methods()

        return {
            "cart": await self.get_cart(user_id),
            "available_payment_methods": [{
                "id": str(pm.id),
                "type": pm.type,
                "provider": pm.provider,
                "last_four": pm.last_four
            } for pm in available_payment_methods],
            "available_shipping_methods": [{
                "id": str(sm.id),
                "name": sm.name,
                "price": sm.price,
                "estimated_days": sm.estimated_days
            } for sm in available_shipping_options],
            "tax_info": {"tax_rate": 0.1, "tax_amount": cart.tax_amount(), "tax_included": True}
        }

    async def _notify_cart_updated(self, user_id: UUID):
        """Send WebSocket notification for cart update"""
        try:
            from services.notification import NotificationService
            notification_service = NotificationService(self.db)
            cart_data = await self.get_cart(user_id)
            # Convert to dict if it's a Pydantic model
            if hasattr(cart_data, 'model_dump'):
                cart_dict = cart_data.model_dump()
            elif hasattr(cart_data, 'dict'):
                cart_dict = cart_data.dict()
            else:
                cart_dict = cart_data
            await notification_service.notify_cart_updated(user_id, cart_dict)
        except Exception as e:
            print(f"Failed to send cart update notification: {e}")
