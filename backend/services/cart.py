# Consolidated cart service with Redis integration
# This file includes all cart-related functionality using Redis for performance
# PostgreSQL remains the source of truth for orders

import json
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from models.product import ProductVariant, Product
from models.promocode import Promocode
from schemas.cart import CartResponse, CartItemResponse, AddToCartRequest, UpdateCartItemRequest
from core.redis import RedisService, RedisKeyManager
from core.config import settings
from core.kafka import get_kafka_producer_service
import logging

logger = logging.getLogger(__name__)


class CartService(RedisService):
    """
    Cart service using Redis for performance with PostgreSQL as source of truth
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db
        self.cart_expiry = 7 * 24 * 3600  # 7 days in seconds

    async def add_to_cart(
        self, 
        user_id: UUID, 
        request: AddToCartRequest, 
        background_tasks: BackgroundTasks
    ) -> CartResponse:
        """Add item to Redis cart"""
        try:
            # Validate variant exists and get current price
            variant = await self._get_variant_with_product(request.variant_id)
            if not variant:
                raise HTTPException(status_code=404, detail="Product variant not found")
            
            # Check stock availability
            if variant.inventory and variant.inventory.quantity <= 0:
                raise HTTPException(status_code=400, detail="Product is out of stock")
            
            cart_key = RedisKeyManager.cart_key(str(user_id))
            
            # Get current cart
            cart_data = await self.get_hash(cart_key) or {}
            
            # Initialize cart structure if empty
            if not cart_data:
                cart_data = {
                    "user_id": str(user_id),
                    "items": {},
                    "updated_at": datetime.utcnow().isoformat(),
                    "total_items": 0,
                    "subtotal": 0.0
                }
            
            # Parse items if it's a string (Redis serialization)
            if isinstance(cart_data.get("items"), str):
                cart_data["items"] = json.loads(cart_data["items"])
            
            variant_key = str(request.variant_id)
            current_price = float(variant.sale_price or variant.base_price)
            
            # Add or update item
            if variant_key in cart_data["items"]:
                existing_item = cart_data["items"][variant_key]
                new_quantity = existing_item["quantity"] + request.quantity
                
                # Check stock limit
                if variant.inventory and new_quantity > variant.inventory.quantity:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Only {variant.inventory.quantity} items available"
                    )
                
                cart_data["items"][variant_key]["quantity"] = new_quantity
                cart_data["items"][variant_key]["total_price"] = new_quantity * current_price
            else:
                # Check stock for new item
                if variant.inventory and request.quantity > variant.inventory.quantity:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Only {variant.inventory.quantity} items available"
                    )
                
                cart_data["items"][variant_key] = {
                    "variant_id": str(request.variant_id),
                    "product_id": str(variant.product_id),
                    "product_name": variant.product.name,
                    "variant_name": variant.name,
                    "quantity": request.quantity,
                    "price_per_unit": current_price,
                    "total_price": request.quantity * current_price,
                    "image_url": variant.images[0].url if variant.images else None,
                    "sku": variant.sku,
                    "added_at": datetime.utcnow().isoformat()
                }
            
            # Update cart totals
            cart_data["total_items"] = sum(item["quantity"] for item in cart_data["items"].values())
            cart_data["subtotal"] = sum(item["total_price"] for item in cart_data["items"].values())
            cart_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Save to Redis
            await self.set_hash(cart_key, cart_data, self.cart_expiry)
            
            # Send cart update notification
            background_tasks.add_task(self._send_cart_update_notification, user_id, "item_added")
            
            return await self._format_cart_response(cart_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            raise HTTPException(status_code=500, detail="Failed to add item to cart")

    async def remove_from_cart(self, user_id: UUID, variant_id: UUID) -> CartResponse:
        """Remove item from Redis cart"""
        try:
            cart_key = RedisKeyManager.cart_key(str(user_id))
            cart_data = await self.get_hash(cart_key)
            
            if not cart_data or "items" not in cart_data:
                raise HTTPException(status_code=400, detail="Cart is empty")
            
            # Parse items if it's a string
            if isinstance(cart_data.get("items"), str):
                cart_data["items"] = json.loads(cart_data["items"])
            
            variant_key = str(variant_id)
            if variant_key not in cart_data["items"]:
                raise HTTPException(status_code=404, detail="Item not found in cart")
            
            # Remove item
            del cart_data["items"][variant_key]
            
            # Update totals
            cart_data["total_items"] = sum(item["quantity"] for item in cart_data["items"].values())
            cart_data["subtotal"] = sum(item["total_price"] for item in cart_data["items"].values())
            cart_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Save updated cart
            if cart_data["items"]:
                await self.set_hash(cart_key, cart_data, self.cart_expiry)
            else:
                # Delete empty cart
                await self.delete_key(cart_key)
            
            return await self._format_cart_response(cart_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error removing from cart: {e}")
            raise HTTPException(status_code=500, detail="Failed to remove item from cart")

    async def update_cart_item(
        self, 
        user_id: UUID, 
        variant_id: UUID, 
        request: UpdateCartItemRequest
    ) -> CartResponse:
        """Update item quantity in Redis cart"""
        try:
            if request.quantity <= 0:
                return await self.remove_from_cart(user_id, variant_id)
            
            # Validate variant and stock
            variant = await self._get_variant_with_product(variant_id)
            if not variant:
                raise HTTPException(status_code=404, detail="Product variant not found")
            
            if variant.inventory and request.quantity > variant.inventory.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Only {variant.inventory.quantity} items available"
                )
            
            cart_key = RedisKeyManager.cart_key(str(user_id))
            cart_data = await self.get_hash(cart_key)
            
            if not cart_data or "items" not in cart_data:
                raise HTTPException(status_code=400, detail="Cart is empty")
            
            # Parse items if it's a string
            if isinstance(cart_data.get("items"), str):
                cart_data["items"] = json.loads(cart_data["items"])
            
            variant_key = str(variant_id)
            if variant_key not in cart_data["items"]:
                raise HTTPException(status_code=404, detail="Item not found in cart")
            
            # Update quantity and price
            current_price = float(variant.sale_price or variant.base_price)
            cart_data["items"][variant_key]["quantity"] = request.quantity
            cart_data["items"][variant_key]["price_per_unit"] = current_price
            cart_data["items"][variant_key]["total_price"] = request.quantity * current_price
            
            # Update totals
            cart_data["total_items"] = sum(item["quantity"] for item in cart_data["items"].values())
            cart_data["subtotal"] = sum(item["total_price"] for item in cart_data["items"].values())
            cart_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Save to Redis
            await self.set_hash(cart_key, cart_data, self.cart_expiry)
            
            return await self._format_cart_response(cart_data)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating cart item: {e}")
            raise HTTPException(status_code=500, detail="Failed to update cart item")

    async def get_or_create_cart(self, user_id: UUID) -> CartResponse:
        """Get user's cart from Redis"""
        try:
            cart_key = RedisKeyManager.cart_key(str(user_id))
            cart_data = await self.get_hash(cart_key)
            
            if not cart_data:
                cart_data = {
                    "user_id": str(user_id),
                    "items": {},
                    "total_items": 0,
                    "subtotal": 0.0,
                    "updated_at": datetime.utcnow().isoformat()
                }
            
            # Parse items if it's a string
            if isinstance(cart_data.get("items"), str):
                cart_data["items"] = json.loads(cart_data["items"])
            
            # Validate and refresh prices
            await self._validate_cart_prices(cart_data)
            
            return await self._format_cart_response(cart_data)
            
        except Exception as e:
            logger.error(f"Error getting cart: {e}")
            return await self._format_cart_response({
                "user_id": str(user_id),
                "items": {},
                "total_items": 0,
                "subtotal": 0.0,
                "error": "Failed to load cart"
            })

    async def clear_cart(self, user_id: UUID) -> Dict[str, Any]:
        """Clear user's cart from Redis"""
        try:
            cart_key = RedisKeyManager.cart_key(str(user_id))
            await self.delete_key(cart_key)
            
            return {"message": "Cart cleared successfully"}
            
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            raise HTTPException(status_code=500, detail="Failed to clear cart")

    async def validate_cart(self, user_id: UUID) -> Dict[str, Any]:
        """
        Comprehensive cart validation - ALWAYS run before checkout
        Validates availability, stock, prices, and product status
        """
        try:
            cart_data = await self.get_hash(RedisKeyManager.cart_key(str(user_id)))
            
            if not cart_data or not cart_data.get("items"):
                return {
                    "valid": False, 
                    "cart": await self._format_cart_response({}), 
                    "issues": ["Cart is empty"],
                    "can_checkout": False
                }
            
            # Parse items if it's a string
            if isinstance(cart_data.get("items"), str):
                cart_data["items"] = json.loads(cart_data["items"])
            
            issues = []
            updated_items = {}
            price_changes = []
            stock_issues = []
            availability_issues = []
            
            for variant_key, item in cart_data["items"].items():
                variant = await self._get_variant_with_product(UUID(variant_key))
                
                # Check if product/variant still exists
                if not variant:
                    availability_issues.append({
                        "variant_id": variant_key,
                        "issue": "product_not_found",
                        "message": f"Product '{item.get('product_name', 'Unknown')}' is no longer available",
                        "severity": "error"
                    })
                    continue
                
                # Check if product is still active
                if not variant.is_active or (variant.product and not variant.product.is_active):
                    availability_issues.append({
                        "variant_id": variant_key,
                        "issue": "product_inactive",
                        "message": f"Product '{item.get('product_name', variant.product.name if variant.product else 'Unknown')}' is no longer available for purchase",
                        "severity": "error"
                    })
                    continue
                
                # Check stock availability
                current_stock = 0
                if variant.inventory:
                    current_stock = variant.inventory.quantity
                
                if current_stock <= 0:
                    stock_issues.append({
                        "variant_id": variant_key,
                        "issue": "out_of_stock",
                        "message": f"'{item.get('product_name', variant.product.name if variant.product else 'Unknown')}' is out of stock",
                        "severity": "error",
                        "current_stock": 0,
                        "requested_quantity": item["quantity"]
                    })
                    continue
                
                # Check if requested quantity is available
                if item["quantity"] > current_stock:
                    # Adjust quantity to available stock
                    available_qty = current_stock
                    original_quantity = item["quantity"]
                    item["quantity"] = available_qty
                    
                    # Recalculate price with new quantity
                    current_price = float(variant.sale_price or variant.base_price)
                    item["total_price"] = available_qty * current_price
                    
                    stock_issues.append({
                        "variant_id": variant_key,
                        "issue": "quantity_adjusted",
                        "message": f"Quantity for '{item.get('product_name', variant.product.name if variant.product else 'Unknown')}' adjusted from {original_quantity} to {available_qty} (available stock)",
                        "severity": "warning",
                        "current_stock": current_stock,
                        "requested_quantity": original_quantity,
                        "adjusted_quantity": available_qty
                    })
                
                # Validate and update prices - CRITICAL for security
                current_price = float(variant.sale_price or variant.base_price)
                stored_price = float(item.get("price_per_unit", 0))
                
                # Allow small floating point differences (1 cent)
                if abs(current_price - stored_price) > 0.01:
                    old_total = item.get("total_price", 0)
                    new_total = current_price * item["quantity"]
                    
                    # Update item with current price
                    item["price_per_unit"] = current_price
                    item["total_price"] = new_total
                    
                    price_changes.append({
                        "variant_id": variant_key,
                        "issue": "price_changed",
                        "message": f"Price updated for '{item.get('product_name', variant.product.name if variant.product else 'Unknown')}': ${stored_price:.2f} → ${current_price:.2f}",
                        "severity": "info" if current_price < stored_price else "warning",
                        "old_price": stored_price,
                        "new_price": current_price,
                        "old_total": old_total,
                        "new_total": new_total,
                        "quantity": item["quantity"],
                        "price_increased": current_price > stored_price
                    })
                
                # Update product information
                if variant.product:
                    item["product_name"] = variant.product.name
                    item["variant_name"] = variant.name
                
                # Item is valid - add to updated items
                updated_items[variant_key] = item
            
            # Combine all issues
            all_issues = availability_issues + stock_issues + price_changes
            
            # Determine if cart can proceed to checkout
            error_issues = [issue for issue in all_issues if issue.get("severity") == "error"]
            can_checkout = len(error_issues) == 0 and len(updated_items) > 0
            
            # Update cart with validated items if there were changes
            cart_updated = False
            if updated_items != cart_data["items"] or price_changes:
                cart_data["items"] = updated_items
                cart_data["total_items"] = sum(item["quantity"] for item in updated_items.values())
                cart_data["subtotal"] = sum(item["total_price"] for item in updated_items.values())
                cart_data["updated_at"] = datetime.utcnow().isoformat()
                cart_data["last_validated"] = datetime.utcnow().isoformat()
                cart_updated = True
                
                # Save updated cart
                cart_key = RedisKeyManager.cart_key(str(user_id))
                if updated_items:
                    await self.set_hash(cart_key, cart_data, self.cart_expiry)
                else:
                    await self.delete_key(cart_key)
            
            # Prepare validation summary
            validation_summary = {
                "total_items_checked": len(cart_data.get("items", {})),
                "valid_items": len(updated_items),
                "removed_items": len(cart_data.get("items", {})) - len(updated_items),
                "price_updates": len(price_changes),
                "stock_adjustments": len([issue for issue in stock_issues if issue.get("issue") == "quantity_adjusted"]),
                "availability_issues": len(availability_issues),
                "cart_updated": cart_updated
            }
            
            return {
                "valid": can_checkout,
                "can_checkout": can_checkout,
                "cart": await self._format_cart_response(cart_data),
                "issues": all_issues,
                "summary": validation_summary,
                "validation_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error validating cart: {e}")
            return {
                "valid": False,
                "can_checkout": False,
                "error": f"Cart validation failed: {str(e)}",
                "cart": await self._format_cart_response({}),
                "issues": [{
                    "issue": "validation_error",
                    "message": "Unable to validate cart. Please try again.",
                    "severity": "error"
                }]
            }

    async def get_cart_count(self, user_id: UUID) -> int:
        """Get total item count in cart"""
        try:
            cart_data = await self.get_hash(RedisKeyManager.cart_key(str(user_id)))
            if cart_data and cart_data.get("items"):
                if isinstance(cart_data["items"], str):
                    items = json.loads(cart_data["items"])
                else:
                    items = cart_data["items"]
                return sum(item["quantity"] for item in items.values())
            return 0
        except Exception as e:
            logger.error(f"Error getting cart count: {e}")
            return 0

    async def _get_variant_with_product(self, variant_id: UUID) -> Optional[ProductVariant]:
        """Get variant with product and inventory data"""
        try:
            result = await self.db.execute(
                select(ProductVariant)
                .where(ProductVariant.id == variant_id)
                .join(Product)
                .options(
                    selectinload(ProductVariant.product),
                    selectinload(ProductVariant.images),
                    selectinload(ProductVariant.inventory)
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching variant {variant_id}: {e}")
            return None

    async def _validate_cart_prices(self, cart_data: Dict[str, Any]) -> None:
        """Validate and update cart prices against current database prices"""
        try:
            if not cart_data.get("items"):
                return
            
            # Parse items if it's a string
            if isinstance(cart_data["items"], str):
                cart_data["items"] = json.loads(cart_data["items"])
            
            price_updates = []
            
            for variant_key, item in cart_data["items"].items():
                variant = await self._get_variant_with_product(UUID(variant_key))
                if variant:
                    current_price = float(variant.sale_price or variant.base_price)
                    if abs(current_price - item["price_per_unit"]) > 0.01:
                        # Price changed - update item
                        item["price_per_unit"] = current_price
                        item["total_price"] = item["quantity"] * current_price
                        price_updates.append({
                            "variant_id": variant_key,
                            "product_name": item["product_name"],
                            "old_price": item["price_per_unit"],
                            "new_price": current_price
                        })
            
            if price_updates:
                # Recalculate totals
                cart_data["subtotal"] = sum(item["total_price"] for item in cart_data["items"].values())
                cart_data["updated_at"] = datetime.utcnow().isoformat()
                cart_data["price_updates"] = price_updates
                
                logger.info(f"Updated {len(price_updates)} item prices in cart")
                
        except Exception as e:
            logger.error(f"Error validating cart prices: {e}")

    async def _format_cart_response(self, cart_data: Dict[str, Any]) -> CartResponse:
        """Format cart data for API response"""
        try:
            items = []
            
            cart_items = cart_data.get("items", {})
            if isinstance(cart_items, str):
                cart_items = json.loads(cart_items)
            
            for item_data in cart_items.values():
                items.append(CartItemResponse(
                    id=str(uuid4()),  # Generate temporary ID for response
                    variant_id=item_data.get("variant_id"),
                    product_id=item_data.get("product_id"),
                    product_name=item_data.get("product_name"),
                    variant_name=item_data.get("variant_name"),
                    quantity=item_data.get("quantity", 0),
                    price_per_unit=item_data.get("price_per_unit", 0.0),
                    total_price=item_data.get("total_price", 0.0),
                    image_url=item_data.get("image_url"),
                    sku=item_data.get("sku"),
                    added_at=item_data.get("added_at")
                ))
            
            return CartResponse(
                id=str(uuid4()),  # Generate temporary ID for response
                user_id=cart_data.get("user_id"),
                items=items,
                total_items=cart_data.get("total_items", 0),
                subtotal=cart_data.get("subtotal", 0.0),
                discount_amount=cart_data.get("discount_amount", 0.0),
                total=cart_data.get("total", cart_data.get("subtotal", 0.0)),
                promocode=cart_data.get("promocode"),
                updated_at=cart_data.get("updated_at"),
                price_updates=cart_data.get("price_updates", [])
            )
            
        except Exception as e:
            logger.error(f"Error formatting cart response: {e}")
            # Return empty cart on error
            return CartResponse(
                id=str(uuid4()),
                user_id=cart_data.get("user_id", ""),
                items=[],
                total_items=0,
                subtotal=0.0,
                discount_amount=0.0,
                total=0.0,
                updated_at=datetime.utcnow().isoformat()
            )

    async def _send_cart_update_notification(self, user_id: UUID, action: str):
        """Send cart update notification via Kafka"""
        try:
            producer_service = await get_kafka_producer_service()
            
            await producer_service.send_cart_notification(
                str(user_id),
                action,
                {"timestamp": datetime.utcnow().isoformat()}
            )
        except Exception as e:
            logger.error(f"Failed to send cart update notification: {e}")
    
    async def _extend_cart_ttl(self, cart_key: str, user_id: Optional[UUID]):
        """Extend cart TTL when items are added (if enabled)"""
        if getattr(settings, 'REDIS_CART_EXTEND_ON_ADD', True):
            redis_client = await self._get_redis_client()
            ttl = self._get_ttl(user_id)
            await redis_client.expire(cart_key, ttl)
            logger.info(f"Extended cart TTL to {ttl} seconds for key: {cart_key}")
    
    async def _send_cart_notification(self, user_id: Optional[UUID], action: str, cart_data: dict):
        """Send cart update notification via Kafka"""
        if user_id:
            try:
                from services.websockets import websocket_integration
                await websocket_integration.broadcast_cart_update(str(user_id), {
                    "action": action,
                    **cart_data
                })
            except Exception as e:
                logger.error(f"Failed to send cart notification: {e}")
    
    async def _get_variant_details(self, variant_id: UUID) -> Optional[Dict]:
        """Get product variant details from database"""
        query = select(ProductVariant).where(ProductVariant.id == variant_id).options(
            selectinload(ProductVariant.images),
            selectinload(ProductVariant.product)
        )
        result = await self.db.execute(query)
        variant = result.scalar_one_or_none()
        
        if variant:
            return variant.to_dict(include_images=True, include_product=True)
        return None

    async def add_to_cart(self, user_id: UUID, variant_id: UUID, quantity: int, session_id: Optional[str] = None) -> CartResponse:
        """Add item to cart in Redis"""
        try:
            redis_client = await self._get_redis_client()
            cart_key = self._get_cart_key(user_id, session_id)
            
            # Get variant details and check stock availability
            variant_details = await self._get_variant_details(variant_id)
            if not variant_details:
                raise HTTPException(status_code=404, detail="Product variant not found")
            
            # Check if stock is available (prevent adding items with zero stock)
            current_stock = variant_details.get('stock', 0)
            if current_stock <= 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Product '{variant_details.get('name', 'Unknown')}' is out of stock"
                )
            
            # Check if requested quantity is available
            if current_stock < quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient stock for '{variant_details.get('name', 'Unknown')}'. Available: {current_stock}, Requested: {quantity}"
                )
            
            # Get current cart
            cart_data = await redis_client.get(cart_key)
            if cart_data:
                cart = json.loads(cart_data)
            else:
                cart = {'items': [], 'created_at': datetime.utcnow().isoformat()}
            
            # Find existing item
            existing_item = None
            for item in cart['items']:
                if item['variant_id'] == str(variant_id):
                    existing_item = item
                    break
            
            effective_price = variant_details.get('sale_price') or variant_details.get('base_price', 0)
            
            if existing_item:
                # Update existing item - check total quantity against stock
                new_quantity = existing_item['quantity'] + quantity
                if current_stock < new_quantity:
                    available_to_add = current_stock - existing_item['quantity']
                    if available_to_add <= 0:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cannot add more of '{variant_details.get('name', 'Unknown')}'. Already at maximum stock in cart."
                        )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cannot add {quantity} more of '{variant_details.get('name', 'Unknown')}'. Only {available_to_add} more can be added."
                        )
                existing_item['quantity'] = new_quantity
                existing_item['price_per_unit'] = effective_price
                existing_item['total_price'] = effective_price * new_quantity
            else:
                # Add new item
                new_item = {
                    'id': str(uuid4()),
                    'variant_id': str(variant_id),
                    'quantity': quantity,
                    'price_per_unit': effective_price,
                    'total_price': effective_price * quantity,
                    'created_at': datetime.utcnow().isoformat()
                }
                cart['items'].append(new_item)
            
            cart['updated_at'] = datetime.utcnow().isoformat()
            
            # Save to Redis with TTL
            ttl = self._get_ttl(user_id)
            await redis_client.set(cart_key, json.dumps(cart), ex=ttl)
            
            # Extend TTL if configured
            await self._extend_cart_ttl(cart_key, user_id)
            
            # Send cart notification
            cart_response = await self.get_cart(user_id, session_id)
            await self._send_cart_notification(user_id, 'item_added', {
                'variant_id': str(variant_id),
                'quantity': quantity,
                'cart_count': sum(item.quantity for item in cart_response.items),
                'cart_total': cart_response.total_amount
            })
            
            return cart_response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to add item to cart: {str(e)}")

    async def get_cart(self, user_id: UUID, session_id: Optional[str] = None) -> CartResponse:
        """Get cart from Redis"""
        try:
            redis_client = await self._get_redis_client()
            cart_key = self._get_cart_key(user_id, session_id)
            
            cart_data = await redis_client.get(cart_key)
            if not cart_data:
                # Return empty cart
                return CartResponse(
                    items=[],
                    subtotal=0.0,
                    tax_amount=0.0,
                    shipping_amount=0.0,
                    total_amount=0.0
                )
            
            cart = json.loads(cart_data)
            items = []
            
            # Fetch current variant details for each item
            for item_data in cart.get('items', []):
                variant_details = await self._get_variant_details(UUID(item_data['variant_id']))
                if variant_details:
                    variant_response = ProductVariantResponse.model_validate(variant_details)
                    
                    # Check if price has changed
                    current_price = variant_details.get('sale_price') or variant_details.get('base_price', 0)
                    if abs(current_price - item_data['price_per_unit']) > 0.01:
                        # Update price in cart
                        item_data['price_per_unit'] = current_price
                        item_data['total_price'] = current_price * item_data['quantity']
                    
                    item_response = CartItemResponse(
                        id=UUID(item_data['id']),
                        variant=variant_response,
                        quantity=item_data['quantity'],
                        price_per_unit=item_data['price_per_unit'],
                        total_price=item_data['total_price'],
                        created_at=item_data.get('created_at')
                    )
                    items.append(item_response)
            
            # Calculate totals
            subtotal = sum(item.total_price for item in items)
            tax_amount = subtotal * 0.1  # 10% tax
            shipping_amount = 0.0 if subtotal >= 50 else 10.0  # Free shipping over $50
            total_amount = subtotal + tax_amount + shipping_amount
            
            # Update cart in Redis if prices changed
            updated_cart_data = {
                'items': [
                    {
                        'id': str(item.id),
                        'variant_id': str(item.variant.id),
                        'quantity': item.quantity,
                        'price_per_unit': item.price_per_unit,
                        'total_price': item.total_price,
                        'created_at': item.created_at
                    }
                    for item in items
                ],
                'updated_at': datetime.utcnow().isoformat()
            }
            await redis_client.set(cart_key, json.dumps(updated_cart_data), ex=self._get_ttl(user_id))
            
            return CartResponse(
                items=items,
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_amount=shipping_amount,
                total_amount=total_amount
            )
            
        except Exception as e:
            logger.error(f"Error getting cart: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to retrieve cart: {str(e)}")

    async def update_cart_item_quantity(self, user_id: UUID, item_id: UUID, quantity: int, session_id: Optional[str] = None) -> CartResponse:
        """Update cart item quantity in Redis"""
        try:
            redis_client = await self._get_redis_client()
            cart_key = self._get_cart_key(user_id, session_id)
            
            cart_data = await redis_client.get(cart_key)
            if not cart_data:
                raise HTTPException(status_code=404, detail="Cart not found")
            
            cart = json.loads(cart_data)
            item_found = False
            
            for item in cart['items']:
                if item['id'] == str(item_id):
                    item_found = True
                    
                    if quantity <= 0:
                        # Remove item
                        cart['items'].remove(item)
                    else:
                        # Check stock
                        variant_details = await self._get_variant_details(UUID(item['variant_id']))
                        if variant_details and variant_details.get('stock', 0) < quantity:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Insufficient stock for {variant_details.get('name', 'product')}. Available: {variant_details.get('stock', 0)}"
                            )
                        
                        # Update quantity and price
                        effective_price = variant_details.get('sale_price') or variant_details.get('base_price', 0) if variant_details else item['price_per_unit']
                        item['quantity'] = quantity
                        item['price_per_unit'] = effective_price
                        item['total_price'] = effective_price * quantity
                    break
            
            if not item_found:
                raise HTTPException(status_code=404, detail="Cart item not found")
            
            cart['updated_at'] = datetime.utcnow().isoformat()
            
            # Save to Redis
            await redis_client.set(cart_key, json.dumps(cart), ex=self._get_ttl(user_id))
            
            # Extend TTL if configured
            await self._extend_cart_ttl(cart_key, user_id)
            
            # Send cart notification
            cart_response = await self.get_cart(user_id, session_id)
            await self._send_cart_notification(user_id, 'item_updated', {
                'item_id': str(item_id),
                'quantity': quantity,
                'cart_count': sum(item.quantity for item in cart_response.items),
                'cart_total': cart_response.total_amount
            })
            
            return cart_response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating cart item: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to update cart item: {str(e)}")

    async def remove_from_cart(self, user_id: UUID, item_id: UUID, session_id: Optional[str] = None) -> CartResponse:
        """Remove item from cart"""
        return await self.update_cart_item_quantity(user_id, item_id, 0, session_id)

    async def clear_cart(self, user_id: UUID, session_id: Optional[str] = None) -> CartResponse:
        """Clear entire cart"""
        try:
            redis_client = await self._get_redis_client()
            cart_key = self._get_cart_key(user_id, session_id)
            
            await redis_client.delete(cart_key)
            
            # Send cart notification
            await self._send_cart_notification(user_id, 'cart_cleared', {
                'cart_count': 0,
                'cart_total': 0.0
            })
            
            return CartResponse(
                items=[],
                subtotal=0.0,
                tax_amount=0.0,
                shipping_amount=0.0,
                total_amount=0.0
            )
            
        except Exception as e:
            logger.error(f"Error clearing cart: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to clear cart: {str(e)}")

    async def apply_promocode(self, user_id: UUID, code: str, session_id: Optional[str] = None):
        """Apply promocode to Redis cart"""
        try:
            redis_client = await self._get_redis_client()
            cart_key = self._get_cart_key(user_id, session_id)
            
            # Get cart data
            cart_data = await redis_client.get(cart_key)
            if not cart_data:
                raise HTTPException(status_code=404, detail="Cart not found")
            
            cart = json.loads(cart_data)
            
            # Get promocode from database
            promocode_service = PromocodeService(self.db)
            promocode = await promocode_service.get_promocode_by_code(code)

            if not promocode:
                raise HTTPException(status_code=400, detail="Invalid or inactive promocode")

            if promocode.expiration_date and promocode.expiration_date < datetime.now():
                raise HTTPException(status_code=400, detail="Promocode has expired")

            # Calculate current cart totals
            current_cart = await self.get_cart(user_id, session_id)
            subtotal = current_cart.subtotal

            discount_amount = 0.0
            if promocode.discount_type == "fixed":
                discount_amount = promocode.value
            elif promocode.discount_type == "percentage":
                discount_amount = subtotal * promocode.value
            elif promocode.discount_type == "shipping":
                discount_amount = current_cart.shipping_amount

            # Add promocode info to cart
            cart['promocode'] = {
                'id': str(promocode.id),
                'code': promocode.code,
                'discount_type': promocode.discount_type,
                'discount_value': promocode.value,
                'discount_amount': discount_amount
            }
            cart['updated_at'] = datetime.utcnow().isoformat()
            
            # Save updated cart
            await redis_client.set(cart_key, json.dumps(cart), ex=self._get_ttl(user_id))

            return {
                "message": f"Promocode {code} applied",
                "promocode": promocode.code,
                "discount_type": promocode.discount_type,
                "discount_value": promocode.value,
                "discount_amount": discount_amount,
                "total_amount": subtotal + current_cart.tax_amount + current_cart.shipping_amount - discount_amount,
                "cart": await self.get_cart(user_id, session_id)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error applying promocode: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to apply promocode: {str(e)}")

    async def remove_promocode(self, user_id: UUID, session_id: Optional[str] = None):
        """Remove promocode from Redis cart"""
        try:
            redis_client = await self._get_redis_client()
            cart_key = self._get_cart_key(user_id, session_id)
            
            cart_data = await redis_client.get(cart_key)
            if not cart_data:
                raise HTTPException(status_code=404, detail="Cart not found")
            
            cart = json.loads(cart_data)
            cart.pop('promocode', None)
            cart['updated_at'] = datetime.utcnow().isoformat()
            
            await redis_client.set(cart_key, json.dumps(cart), ex=self._get_ttl(user_id))
            
            return {"message": "Promocode removed", "cart": await self.get_cart(user_id, session_id)}
            
        except Exception as e:
            logger.error(f"Error removing promocode: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to remove promocode: {str(e)}")

    async def get_cart_item_count(self, user_id: UUID, session_id: Optional[str] = None):
        """Get total item count in cart"""
        try:
            cart = await self.get_cart(user_id, session_id)
            total_count = sum(item.quantity for item in cart.items)
            return {"count": total_count}
        except Exception as e:
            logger.error(f"Error getting cart count: {e}")
            return {"count": 0}

    async def get_shipping_options(self, user_id: UUID, address: dict, session_id: Optional[str] = None):
        """Get available shipping options"""
        try:
            shipping_service = ShippingService(self.db)
            active_methods = await shipping_service.get_all_active_shipping_methods()

            options = []
            for method in active_methods:
                options.append({
                    "id": str(method.id),
                    "name": method.name,
                    "description": method.description,
                    "price": method.price,
                    "estimated_days": method.estimated_days
                })

            # Free shipping for orders over $50
            cart = await self.get_cart(user_id, session_id)
            if cart.subtotal >= 50:
                options.append({
                    "id": "free_shipping", 
                    "name": "Free Shipping",
                    "description": "Orders over $50", 
                    "price": 0.00, 
                    "estimated_days": 5
                })

            return options
            
        except Exception as e:
            logger.error(f"Error getting shipping options: {e}")
            return []

    async def calculate_totals(self, user_id: UUID, data: dict, session_id: Optional[str] = None):
        """Calculate cart totals with optional discount"""
        try:
            cart = await self.get_cart(user_id, session_id)
            discount = data.get("discount_amount", 0.0)
            
            return {
                "subtotal": cart.subtotal,
                "tax_amount": cart.tax_amount,
                "shipping_amount": cart.shipping_amount,
                "discount_amount": discount,
                "total_amount": cart.subtotal + cart.tax_amount + cart.shipping_amount - discount,
                "currency": "USD"
            }
            
        except Exception as e:
            logger.error(f"Error calculating totals: {e}")
            return {
                "subtotal": 0.0,
                "tax_amount": 0.0,
                "shipping_amount": 0.0,
                "discount_amount": 0.0,
                "total_amount": 0.0,
                "currency": "USD"
            }

    async def merge_cart(self, user_id: UUID, items: list, session_id: Optional[str] = None):
        """Merge items into user cart (typically used when logging in)"""
        try:
            for item in items:
                await self.add_to_cart(user_id, UUID(item["variant_id"]), item["quantity"], session_id)
            return await self.get_cart(user_id, session_id)
        except Exception as e:
            logger.error(f"Error merging cart: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to merge cart: {str(e)}")

    async def merge_carts(self, user_id: UUID, session_id: str) -> CartResponse:
        """Merge guest cart with user cart when user logs in"""
        try:
            redis_client = await self._get_redis_client()
            user_cart_key = self._get_cart_key(user_id)
            session_cart_key = self._get_cart_key(None, session_id)
            
            # Get both carts
            user_cart_data = await redis_client.get(user_cart_key)
            session_cart_data = await redis_client.get(session_cart_key)
            
            if not session_cart_data:
                # No guest cart to merge
                return await self.get_cart(user_id)
            
            session_cart = json.loads(session_cart_data)
            
            if user_cart_data:
                user_cart = json.loads(user_cart_data)
            else:
                user_cart = {'items': [], 'created_at': datetime.utcnow().isoformat()}
            
            # Merge items
            for session_item in session_cart['items']:
                # Find if item exists in user cart
                existing_item = None
                for user_item in user_cart['items']:
                    if user_item['variant_id'] == session_item['variant_id']:
                        existing_item = user_item
                        break
                
                if existing_item:
                    # Combine quantities
                    existing_item['quantity'] += session_item['quantity']
                    existing_item['total_price'] = existing_item['price_per_unit'] * existing_item['quantity']
                else:
                    # Add new item
                    user_cart['items'].append(session_item)
            
            user_cart['updated_at'] = datetime.utcnow().isoformat()
            
            # Save merged cart and delete session cart
            await redis_client.set(user_cart_key, json.dumps(user_cart), ex=self._get_ttl(user_id))
            await redis_client.delete(session_cart_key)
            
            return await self.get_cart(user_id)
            
        except Exception as e:
            logger.error(f"Error merging carts: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to merge carts: {str(e)}")

    async def get_checkout_summary(self, user_id: UUID, session_id: Optional[str] = None):
        """Get checkout summary with cart, payment methods, and shipping options"""
        try:
            payment_service = PaymentService(self.db)
            shipping_service = ShippingService(self.db)

            cart = await self.get_cart(user_id, session_id)
            available_payment_methods = await payment_service.get_payment_methods(user_id) if user_id else []
            available_shipping_options = await shipping_service.get_all_active_shipping_methods()

            return {
                "cart": cart,
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
                "tax_info": {
                    "tax_rate": 0.1, 
                    "tax_amount": cart.tax_amount, 
                    "tax_included": True
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting checkout summary: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get checkout summary: {str(e)}")

    async def cleanup_expired_carts(self):
        """Cleanup method for expired carts (Redis handles this automatically with TTL)"""
        logger.info("Redis TTL automatically handles cart expiration")
        return {"message": "Cart cleanup handled by Redis TTL"}