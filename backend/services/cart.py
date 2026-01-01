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
from core.config import settings
from core.kafka import get_kafka_producer_service
import logging

logger = logging.getLogger(__name__)


class CartService:
    """
    Cart service using Redis for performance with PostgreSQL as source of truth
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_to_cart(self, user_id: UUID, variant_id: UUID, quantity: int, session_id: Optional[str] = None) -> CartResponse:
        """Add item to cart in Redis"""
        try:
            # Get variant details and check stock availability
            variant = await self._get_variant_with_product(variant_id)
            if not variant:
                raise HTTPException(status_code=404, detail="Product variant not found")
            
            # Check if stock is available (prevent adding items with zero stock)
            current_stock = variant.inventory.quantity if variant.inventory else 0
            if current_stock <= 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Product '{variant.product.name if variant.product else 'Unknown'}' is out of stock"
                )
            
            # Check if requested quantity is available
            if current_stock < quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient stock for '{variant.product.name if variant.product else 'Unknown'}'. Available: {current_stock}, Requested: {quantity}"
                )
            
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
            
            variant_key = str(variant_id)
            current_price = float(variant.sale_price or variant.base_price)
            
            # Add or update item
            if variant_key in cart_data["items"]:
                existing_item = cart_data["items"][variant_key]
                new_quantity = existing_item["quantity"] + quantity
                
                # Check stock limit
                if current_stock < new_quantity:
                    available_to_add = current_stock - existing_item["quantity"]
                    if available_to_add <= 0:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cannot add more of '{variant.product.name if variant.product else 'Unknown'}'. Already at maximum stock in cart."
                        )
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Cannot add {quantity} more of '{variant.product.name if variant.product else 'Unknown'}'. Only {available_to_add} more can be added."
                        )
                
                existing_item["quantity"] = new_quantity
                existing_item["price_per_unit"] = current_price
                existing_item["total_price"] = current_price * new_quantity
            else:
                # Add new item
                cart_data["items"][variant_key] = {
                    "id": str(uuid4()),  # Add unique ID for the cart item
                    "variant_id": str(variant_id),
                    "product_id": str(variant.product_id),
                    "product_name": variant.product.name,
                    "variant_name": variant.name,
                    "quantity": quantity,
                    "price_per_unit": current_price,
                    "total_price": current_price * quantity,
                    "image_url": variant.images[0].url if variant.images else None,
                    "sku": variant.sku,
                    "added_at": datetime.utcnow().isoformat()
                }
            
            # Update cart totals
            cart_data["total_items"] = sum(item["quantity"] for item in cart_data["items"].values())
            cart_data["subtotal"] = sum(item["total_price"] for item in cart_data["items"].values())
            cart_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Save to Redis
            await self.set_hash(cart_key, cart_data)
            
            # Send cart update notification
            formatted_cart = await self._format_cart_response(cart_data)
            await self._send_cart_update_notification(user_id, "item_added", formatted_cart.dict())
            
            return formatted_cart
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error adding to cart: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to add item to cart: {str(e)}")

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
            
            # Update totals
            cart_data["total_items"] = sum(item["quantity"] for item in cart_data["items"].values())
            cart_data["subtotal"] = sum(item["total_price"] for item in cart_data["items"].values())
            cart_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Save updated cart
            if cart_data["items"]:
                await self.set_hash(cart_key, cart_data)
            else:
                # Delete empty cart
                await self.delete_key(cart_key)

            formatted_cart = await self._format_cart_response(cart_data)
            await self._send_cart_update_notification(user_id, "item_removed", formatted_cart.dict())
            
            return formatted_cart
            
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
            # Save to Redis
            await self.set_hash(cart_key, cart_data)
            
            formatted_cart = await self._format_cart_response(cart_data)
            await self._send_cart_update_notification(user_id, "item_updated", formatted_cart.dict())
            
            return formatted_cart
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating cart item: {e}")
            raise HTTPException(status_code=500, detail="Failed to update cart item")

    async def update_cart_item_quantity(
        self, 
        user_id: UUID, 
        item_id: UUID, 
        quantity: int,
        session_id: Optional[str] = None
    ) -> CartResponse:
        """Update item quantity in Redis cart by item_id"""
        try:
            if quantity <= 0:
                # If quantity is 0 or negative, remove the item
                return await self.remove_from_cart_by_item_id(user_id, item_id)
            
            cart_key = RedisKeyManager.cart_key(str(user_id))
            cart_data = await self.get_hash(cart_key)
            
            if not cart_data or "items" not in cart_data:
                raise HTTPException(status_code=400, detail="Cart is empty")
            
            # Parse items if it's a string
            if isinstance(cart_data.get("items"), str):
                cart_data["items"] = json.loads(cart_data["items"])
            
            # Find the item by item_id
            target_variant_key = None
            target_item = None
            
            for variant_key, item in cart_data["items"].items():
                if item.get("id") == str(item_id):
                    target_variant_key = variant_key
                    target_item = item
                    break
            
            if not target_item:
                raise HTTPException(status_code=404, detail="Item not found in cart")
            
            # Validate variant and stock
            variant = await self._get_variant_with_product(UUID(target_variant_key))
            if not variant:
                raise HTTPException(status_code=404, detail="Product variant not found")
            
            # Check stock availability
            current_stock = variant.inventory.quantity if variant.inventory else 0
            if quantity > current_stock:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Only {current_stock} items available"
                )
            
            # Update quantity and price
            current_price = float(variant.sale_price or variant.base_price)
            target_item["quantity"] = quantity
            target_item["price_per_unit"] = current_price
            target_item["total_price"] = quantity * current_price
            
            # Update totals
            cart_data["total_items"] = sum(item["quantity"] for item in cart_data["items"].values())
            cart_data["subtotal"] = sum(item["total_price"] for item in cart_data["items"].values())
            cart_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Save to Redis
            await self.set_hash(cart_key, cart_data)
            
            formatted_cart = await self._format_cart_response(cart_data)
            await self._send_cart_update_notification(user_id, "quantity_updated", formatted_cart.dict())
            
            return formatted_cart
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating cart item quantity: {e}")
            raise HTTPException(status_code=500, detail="Failed to update cart item quantity")

    async def remove_from_cart_by_item_id(self, user_id: UUID, item_id: UUID) -> CartResponse:
        """Remove item from Redis cart by item_id"""
        try:
            cart_key = RedisKeyManager.cart_key(str(user_id))
            cart_data = await self.get_hash(cart_key)
            
            if not cart_data or "items" not in cart_data:
                raise HTTPException(status_code=400, detail="Cart is empty")
            
            # Parse items if it's a string
            if isinstance(cart_data.get("items"), str):
                cart_data["items"] = json.loads(cart_data["items"])
            
            # Find and remove the item by item_id
            target_variant_key = None
            for variant_key, item in cart_data["items"].items():
                if item.get("id") == str(item_id):
                    target_variant_key = variant_key
                    break
            
            if not target_variant_key:
                raise HTTPException(status_code=404, detail="Item not found in cart")
            
            # Remove item
            del cart_data["items"][target_variant_key]
            
            # Update totals
            cart_data["total_items"] = sum(item["quantity"] for item in cart_data["items"].values())
            cart_data["subtotal"] = sum(item["total_price"] for item in cart_data["items"].values())
            cart_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Save updated cart
            if cart_data["items"]:
                await self.set_hash(cart_key, cart_data)
            else:
                # Delete empty cart
                await self.delete_key(cart_key)

            formatted_cart = await self._format_cart_response(cart_data)
            await self._send_cart_update_notification(user_id, "item_removed", formatted_cart.dict())
            
            return formatted_cart
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error removing from cart by item_id: {e}")
            raise HTTPException(status_code=500, detail="Failed to remove item from cart")

    async def get_cart(self, user_id: UUID, session_id: Optional[str] = None) -> CartResponse:
        """Get user's cart from Redis"""
        return await self.get_or_create_cart(user_id)

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

            # Send notification of cleared cart
            cleared_cart_data = {
                "user_id": str(user_id),
                "items": {},
                "total_items": 0,
                "subtotal": 0.0,
                "updated_at": datetime.utcnow().isoformat()
            }
            formatted_cart = await self._format_cart_response(cleared_cart_data)
            await self._send_cart_update_notification(user_id, "cart_cleared", formatted_cart.dict())
            
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
                    await self.set_hash(cart_key, cart_data)
                else:
                    await self.delete_key(cart_key)

                # Send notification on cart update from validation
                formatted_cart = await self._format_cart_response(cart_data)
                await self._send_cart_update_notification(user_id, "cart_validated", formatted_cart.dict())
            
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

    async def get_cart_item_count(self, user_id: UUID, session_id: Optional[str] = None) -> int:
        """Get total item count in cart"""
        return await self.get_cart_count(user_id)

    async def get_cart_count(self, user_id: UUID) -> int:
        """Get total item count in cart"""
        try:
            cart_key = RedisKeyManager.cart_key(str(user_id))
            cart_data = await self.get_hash(cart_key)
            
            if not cart_data:
                return 0
            
            return cart_data.get("total_items", 0)
            
        except Exception as e:
            logger.error(f"Error getting cart count: {e}")
            return 0

    async def apply_promocode(self, user_id: UUID, code: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Apply promocode to cart"""
        try:
            # Get current cart
            cart_key = RedisKeyManager.cart_key(str(user_id))
            cart_data = await self.get_hash(cart_key)
            
            if not cart_data or not cart_data.get("items"):
                raise HTTPException(status_code=400, detail="Cart is empty")
            
            # Parse items if it's a string
            if isinstance(cart_data.get("items"), str):
                cart_data["items"] = json.loads(cart_data["items"])
            
            # Validate promocode (mock implementation - would integrate with actual promocode service)
            promocode_info = await self._validate_promocode(code, cart_data)
            
            if not promocode_info["valid"]:
                raise HTTPException(status_code=400, detail=promocode_info["message"])
            
            # Apply promocode to cart
            cart_data["promocode"] = {
                "code": code.upper(),
                "discount_type": promocode_info["discount_type"],
                "discount_value": promocode_info["discount_value"],
                "applied_at": datetime.utcnow().isoformat()
            }
            
            # Recalculate totals with promocode
            await self._recalculate_cart_with_promocode(cart_data)
            
            # Save updated cart
            await self.set_hash(cart_key, cart_data)
            
            formatted_cart = await self._format_cart_response(cart_data)
            await self._send_cart_update_notification(user_id, "promocode_applied", formatted_cart.dict())
            
            return {
                "message": f"Promocode '{code}' applied successfully",
                "promocode": cart_data["promocode"],
                "new_subtotal": cart_data["subtotal"],
                "discount_amount": promocode_info["discount_amount"],
                "cart": formatted_cart
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error applying promocode: {e}")
            raise HTTPException(status_code=500, detail="Failed to apply promocode")

    async def remove_promocode(self, user_id: UUID, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Remove promocode from cart"""
        try:
            # Get current cart
            cart_key = RedisKeyManager.cart_key(str(user_id))
            cart_data = await self.get_hash(cart_key)
            
            if not cart_data:
                raise HTTPException(status_code=400, detail="Cart is empty")
            
            # Parse items if it's a string
            if isinstance(cart_data.get("items"), str):
                cart_data["items"] = json.loads(cart_data["items"])
            
            # Check if promocode exists
            if not cart_data.get("promocode"):
                raise HTTPException(status_code=400, detail="No promocode applied to cart")
            
            removed_code = cart_data["promocode"]["code"]
            
            # Remove promocode
            del cart_data["promocode"]
            
            # Recalculate totals without promocode
            cart_data["subtotal"] = sum(item["total_price"] for item in cart_data["items"].values())
            cart_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Save updated cart
            await self.set_hash(cart_key, cart_data)

            formatted_cart = await self._format_cart_response(cart_data)
            await self._send_cart_update_notification(user_id, "promocode_removed", formatted_cart.dict())
            
            return {
                "message": f"Promocode '{removed_code}' removed successfully",
                "cart": formatted_cart
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error removing promocode: {e}")
            raise HTTPException(status_code=500, detail="Failed to remove promocode")

    async def get_shipping_options(self, user_id: UUID, address: dict, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get shipping options based on cart contents and address"""
        try:
            # Get cart to calculate shipping based on weight/value
            cart = await self.get_cart(user_id, session_id)
            
            # Base shipping options
            shipping_options = []
            
            # Calculate shipping cost based on cart total
            subtotal = cart.subtotal if cart else 0
            
            # Standard shipping
            standard_price = 10.0 if subtotal < 50.0 else 0.0  # Free shipping over $50
            shipping_options.append({
                "id": "standard",
                "name": "Standard Shipping",
                "price": standard_price,
                "delivery_days": "5-7",
                "description": "Free shipping on orders over $50"
            })
            
            # Express shipping
            express_price = 25.0 if subtotal < 100.0 else 15.0  # Discounted express for large orders
            shipping_options.append({
                "id": "express", 
                "name": "Express Shipping",
                "price": express_price,
                "delivery_days": "2-3",
                "description": "Fast delivery in 2-3 business days"
            })
            
            # Overnight shipping for premium orders
            if subtotal > 25.0:
                overnight_price = 35.0 if subtotal < 100.0 else 25.0
                shipping_options.append({
                    "id": "overnight",
                    "name": "Overnight Shipping", 
                    "price": overnight_price,
                    "delivery_days": "1",
                    "description": "Next business day delivery"
                })
            
            return {
                "shipping_options": shipping_options,
                "cart_subtotal": subtotal,
                "free_shipping_threshold": 50.0
            }
            
        except Exception as e:
            logger.error(f"Error getting shipping options: {e}")
            # Return default options on error
            return {
                "shipping_options": [
                    {"id": "standard", "name": "Standard Shipping", "price": 10.0, "delivery_days": "5-7", "description": "Standard delivery"},
                    {"id": "express", "name": "Express Shipping", "price": 25.0, "delivery_days": "2-3", "description": "Fast delivery"}
                ]
            }

    async def calculate_totals(self, user_id: UUID, data: dict, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculate cart totals with shipping and tax"""
        try:
            cart = await self.get_cart(user_id, session_id)
            
            # Get shipping information from data
            shipping_option = data.get("shipping_option", "standard")
            shipping_address = data.get("shipping_address", {})
            promocode = data.get("promocode")
            
            # Calculate subtotal
            subtotal = cart.subtotal
            
            # Calculate shipping cost
            shipping_cost = 0.0
            if shipping_option == "standard":
                shipping_cost = 10.0 if subtotal < 50.0 else 0.0  # Free shipping over $50
            elif shipping_option == "express":
                shipping_cost = 25.0 if subtotal < 100.0 else 15.0
            elif shipping_option == "overnight":
                shipping_cost = 35.0 if subtotal < 100.0 else 25.0
            
            # Calculate tax (10% for now)
            tax_rate = 0.10
            tax_amount = subtotal * tax_rate
            
            # Apply promocode discount if provided
            discount_amount = 0.0
            discount_percentage = 0.0
            if promocode:
                # Mock promocode logic - would integrate with actual promocode service
                if promocode.upper() == "SAVE10":
                    discount_percentage = 10.0
                    discount_amount = subtotal * 0.10
                elif promocode.upper() == "FREESHIP":
                    shipping_cost = 0.0
            
            # Calculate final total
            total_before_discount = subtotal + shipping_cost + tax_amount
            total_amount = total_before_discount - discount_amount
            
            return {
                "subtotal": subtotal,
                "shipping_cost": shipping_cost,
                "tax_amount": tax_amount,
                "discount_amount": discount_amount,
                "discount_percentage": discount_percentage,
                "total_amount": total_amount,
                "currency": "USD",
                "breakdown": {
                    "items_total": subtotal,
                    "shipping": shipping_cost,
                    "tax": tax_amount,
                    "discount": -discount_amount,
                    "final_total": total_amount
                },
                "applied_promocode": promocode if discount_amount > 0 or (promocode and promocode.upper() == "FREESHIP") else None,
                "shipping_option": shipping_option
            }
            
        except Exception as e:
            logger.error(f"Error calculating cart totals: {e}")
            # Return basic calculation on error
            cart = await self.get_cart(user_id, session_id)
            return {
                "subtotal": cart.subtotal,
                "shipping_cost": 10.0,
                "tax_amount": cart.subtotal * 0.10,
                "discount_amount": 0.0,
                "total_amount": cart.subtotal + 10.0 + (cart.subtotal * 0.10),
                "currency": "USD",
                "error": f"Calculation error: {str(e)}"
            }

    async def merge_carts(self, user_id: UUID, session_id: str) -> Dict[str, Any]:
        """Merge guest cart with user cart"""
        try:
            # Get user cart
            user_cart_key = RedisKeyManager.cart_key(str(user_id))
            user_cart_data = await self.get_hash(user_cart_key) or {
                "user_id": str(user_id),
                "items": {},
                "total_items": 0,
                "subtotal": 0.0,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Get guest cart
            guest_cart_key = RedisKeyManager.cart_key(session_id)
            guest_cart_data = await self.get_hash(guest_cart_key)
            
            if not guest_cart_data or not guest_cart_data.get("items"):
                return {
                    "message": "No guest cart to merge",
                    "cart": await self._format_cart_response(user_cart_data)
                }
            
            # Parse items if they're strings
            if isinstance(user_cart_data.get("items"), str):
                user_cart_data["items"] = json.loads(user_cart_data["items"])
            if isinstance(guest_cart_data.get("items"), str):
                guest_cart_data["items"] = json.loads(guest_cart_data["items"])
            
            merged_items = 0
            updated_items = 0
            
            # Merge guest cart items into user cart
            for variant_key, guest_item in guest_cart_data["items"].items():
                if variant_key in user_cart_data["items"]:
                    # Item exists in user cart - combine quantities
                    existing_item = user_cart_data["items"][variant_key]
                    
                    # Validate stock availability for combined quantity
                    variant = await self._get_variant_with_product(UUID(variant_key))
                    if variant and variant.inventory:
                        max_available = variant.inventory.quantity
                        new_quantity = existing_item["quantity"] + guest_item["quantity"]
                        
                        if new_quantity <= max_available:
                            existing_item["quantity"] = new_quantity
                            existing_item["total_price"] = existing_item["price_per_unit"] * new_quantity
                            updated_items += 1
                        else:
                            # Use maximum available quantity
                            existing_item["quantity"] = max_available
                            existing_item["total_price"] = existing_item["price_per_unit"] * max_available
                            updated_items += 1
                else:
                    # New item - add to user cart
                    user_cart_data["items"][variant_key] = guest_item
                    merged_items += 1
            
            # Update cart totals
            user_cart_data["total_items"] = sum(item["quantity"] for item in user_cart_data["items"].values())
            user_cart_data["subtotal"] = sum(item["total_price"] for item in user_cart_data["items"].values())
            user_cart_data["updated_at"] = datetime.utcnow().isoformat()
            
            # Save merged cart
            await self.set_hash(user_cart_key, user_cart_data)
            
            # Delete guest cart
            await self.delete_key(guest_cart_key)

            formatted_cart = await self._format_cart_response(user_cart_data)
            await self._send_cart_update_notification(user_id, "cart_merged", formatted_cart.dict())
            
            return {
                "message": f"Cart merged successfully. Added {merged_items} new items, updated {updated_items} existing items.",
                "merge_summary": {
                    "new_items_added": merged_items,
                    "existing_items_updated": updated_items,
                    "total_items_in_cart": user_cart_data["total_items"]
                },
                "cart": formatted_cart
            }
            
        except Exception as e:
            logger.error(f"Error merging carts: {e}")
            raise HTTPException(status_code=500, detail="Failed to merge carts")

    async def get_checkout_summary(self, user_id: UUID, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive checkout summary"""
        try:
            # Get cart
            cart = await self.get_cart(user_id, session_id)
            
            if not cart.items:
                raise HTTPException(status_code=400, detail="Cart is empty")
            
            # Validate cart before checkout
            validation_result = await self.validate_cart(user_id)
            
            # Get shipping options (using default address for calculation)
            default_address = {"country": "US", "state": "CA", "zip": "90210"}
            shipping_options = await self.get_shipping_options(user_id, default_address, session_id)
            
            # Calculate totals with default shipping
            calculation_data = {
                "shipping_option": "standard",
                "shipping_address": default_address
            }
            totals = await self.calculate_totals(user_id, calculation_data, session_id)
            
            # Get available payment methods (mock for now)
            payment_methods = [
                {"id": "credit_card", "name": "Credit Card", "available": True},
                {"id": "paypal", "name": "PayPal", "available": True},
                {"id": "stripe", "name": "Stripe", "available": True}
            ]
            
            # Check for any issues
            checkout_issues = []
            if not validation_result["can_checkout"]:
                checkout_issues.extend([issue["message"] for issue in validation_result["issues"] if issue.get("severity") == "error"])
            
            return {
                "cart": cart,
                "validation": validation_result,
                "shipping_options": shipping_options,
                "payment_methods": payment_methods,
                "totals": totals,
                "checkout_ready": validation_result["can_checkout"] and len(checkout_issues) == 0,
                "issues": checkout_issues,
                "summary": {
                    "item_count": len(cart.items),
                    "subtotal": cart.subtotal,
                    "estimated_total": totals.get("total_amount", cart.total_amount),
                    "currency": cart.currency
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting checkout summary: {e}")
            raise HTTPException(status_code=500, detail="Failed to get checkout summary")

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
                # Get the variant details to create ProductVariantResponse
                variant_id = item_data.get("variant_id")
                if variant_id:
                    variant = await self._get_variant_with_product(UUID(variant_id))
                    if variant:
                        from schemas.product import ProductVariantResponse, ProductVariantImageResponse
                        
                        # Create image responses
                        image_responses = []
                        primary_image = None
                        
                        if variant.images:
                            for img in variant.images:
                                img_response = ProductVariantImageResponse(
                                    id=img.id,
                                    variant_id=img.variant_id,
                                    url=img.url,
                                    alt_text=img.alt_text,
                                    is_primary=img.is_primary,
                                    sort_order=img.sort_order,
                                    format=getattr(img, 'format', 'jpg'),
                                    created_at=img.created_at.isoformat() if img.created_at else None
                                )
                                image_responses.append(img_response)
                                
                                if img.is_primary:
                                    primary_image = img_response
                        
                        # If no primary image found, use the first image
                        if not primary_image and image_responses:
                            primary_image = image_responses[0]
                        
                        # Calculate discount percentage
                        discount_percentage = 0.0
                        if variant.sale_price and variant.base_price:
                            discount_percentage = ((variant.base_price - variant.sale_price) / variant.base_price) * 100
                        
                        # Create variant response
                        variant_response = ProductVariantResponse(
                            id=variant.id,
                            product_id=variant.product_id,
                            sku=variant.sku,
                            name=variant.name,
                            base_price=variant.base_price,
                            sale_price=variant.sale_price,
                            current_price=float(variant.sale_price or variant.base_price),
                            discount_percentage=discount_percentage,
                            stock=variant.inventory.quantity if variant.inventory else 0,
                            attributes=variant.attributes or {},
                            is_active=variant.is_active,
                            barcode=variant.barcode,
                            qr_code=variant.qr_code,
                            images=image_responses,
                            primary_image=primary_image,
                            created_at=variant.created_at.isoformat() if variant.created_at else None,
                            updated_at=variant.updated_at.isoformat() if variant.updated_at else None,
                            product_name=variant.product.name if variant.product else None,
                            product_description=variant.product.description if variant.product else None
                        )
                        
                        items.append(CartItemResponse(
                            id=UUID(item_data.get("id", str(uuid4()))),
                            variant=variant_response,
                            quantity=item_data.get("quantity", 0),
                            price_per_unit=item_data.get("price_per_unit", 0.0),
                            total_price=item_data.get("total_price", 0.0),
                            created_at=item_data.get("added_at", datetime.utcnow().isoformat())
                        ))
            
            # Calculate totals
            subtotal = cart_data.get("subtotal", 0.0)
            tax_amount = subtotal * 0.1  # 10% tax
            shipping_amount = 0.0 if subtotal >= 50 else 10.0  # Free shipping over $50
            total_amount = subtotal + tax_amount + shipping_amount
            
            return CartResponse(
                items=items,
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_amount=shipping_amount,
                total_amount=total_amount,
                currency="USD"
            )
            
        except Exception as e:
            logger.error(f"Error formatting cart response: {e}")
            # Return empty cart on error
            return CartResponse(
                items=[],
                subtotal=0.0,
                tax_amount=0.0,
                shipping_amount=0.0,
                total_amount=0.0,
                currency="USD"
            )

    async def _send_cart_update_notification(self, user_id: UUID, action: str, cart_data: dict):
        """Send cart update notification via Kafka"""
        try:
            producer_service = await get_kafka_producer_service()
            
            # Enrich cart data for the notification
            notification_payload = {
                "action": action,
                "user_id": str(user_id),
                "cart": cart_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await producer_service.send_cart_notification(
                str(user_id),
                action,
                notification_payload
            )
        except Exception as e:
            logger.error(f"Failed to send cart update notification: {e}")
    
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

    async def _validate_promocode(self, code: str, cart_data: dict) -> Dict[str, Any]:
        """Validate promocode (mock implementation)"""
        try:
            code = code.upper().strip()
            
            # Mock promocode validation
            valid_codes = {
                "SAVE10": {
                    "discount_type": "percentage",
                    "discount_value": 10.0,
                    "min_order": 25.0
                },
                "SAVE20": {
                    "discount_type": "percentage", 
                    "discount_value": 20.0,
                    "min_order": 50.0
                },
                "FREESHIP": {
                    "discount_type": "free_shipping",
                    "discount_value": 0.0,
                    "min_order": 0.0
                },
                "WELCOME5": {
                    "discount_type": "fixed",
                    "discount_value": 5.0,
                    "min_order": 15.0
                }
            }
            
            if code not in valid_codes:
                return {
                    "valid": False,
                    "message": f"Invalid promocode '{code}'"
                }
            
            promo_info = valid_codes[code]
            cart_subtotal = sum(item["total_price"] for item in cart_data["items"].values())
            
            if cart_subtotal < promo_info["min_order"]:
                return {
                    "valid": False,
                    "message": f"Minimum order of ${promo_info['min_order']:.2f} required for this promocode"
                }
            
            # Calculate discount amount
            discount_amount = 0.0
            if promo_info["discount_type"] == "percentage":
                discount_amount = cart_subtotal * (promo_info["discount_value"] / 100)
            elif promo_info["discount_type"] == "fixed":
                discount_amount = promo_info["discount_value"]
            
            return {
                "valid": True,
                "discount_type": promo_info["discount_type"],
                "discount_value": promo_info["discount_value"],
                "discount_amount": discount_amount,
                "message": f"Promocode '{code}' applied successfully"
            }
            
        except Exception as e:
            logger.error(f"Error validating promocode: {e}")
            return {
                "valid": False,
                "message": "Failed to validate promocode"
            }

    async def _recalculate_cart_with_promocode(self, cart_data: dict):
        """Recalculate cart totals with applied promocode"""
        try:
            # Base subtotal
            base_subtotal = sum(item["total_price"] for item in cart_data["items"].values())
            
            promocode = cart_data.get("promocode", {})
            discount_amount = 0.0
            
            if promocode:
                if promocode["discount_type"] == "percentage":
                    discount_amount = base_subtotal * (promocode["discount_value"] / 100)
                elif promocode["discount_type"] == "fixed":
                    discount_amount = promocode["discount_value"]
            
            # Update cart with discount
            cart_data["subtotal"] = base_subtotal
            cart_data["discount_amount"] = discount_amount
            cart_data["final_subtotal"] = base_subtotal - discount_amount
            cart_data["updated_at"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"Error recalculating cart with promocode: {e}")

    async def cleanup_expired_carts(self):
        """Cleanup method for expired carts (Redis handles this automatically with TTL)"""
        logger.info("Redis TTL automatically handles cart expiration")
        return {"message": "Cart cleanup handled by Redis TTL"}