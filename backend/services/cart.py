from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime, timedelta
import secrets
import logging
import json

from models.product import ProductVariant
from models.user import User
from services.tax import TaxService
from core.redis import RedisService, RedisKeyManager
from core.config import settings

logger = logging.getLogger(__name__)


class CartService(RedisService):
    """
    Redis-based cart service for MVP
    Uses Redis for cart storage with ARQ background tasks
    """
    
    def __init__(self, db: AsyncSession):
        super().__init__()
        self.db = db
        self.tax_service = TaxService(db)

    async def get_cart(
        self, 
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        country_code: str = 'US',
        province_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get cart from Redis
        For authenticated users, use user_id as key
        For guests, use session_id as key
        """
        if user_id:
            cart_key = RedisKeyManager.cart_key(str(user_id))
        elif session_id:
            cart_key = RedisKeyManager.cart_key(f"guest:{session_id}")
        else:
            # Generate new session for guest
            session_id = secrets.token_urlsafe(32)
            cart_key = RedisKeyManager.cart_key(f"guest:{session_id}")
        
        # Get cart from Redis
        cart_data = await self.get_hash(cart_key)
        
        if not cart_data:
            # Create empty cart
            cart_data = {
                "user_id": str(user_id) if user_id else None,
                "session_id": session_id,
                "items": [],
                "subtotal": 0.0,
                "tax_amount": 0.0,
                "shipping_amount": 0.0,
                "total_amount": 0.0,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "country_code": country_code,
                "province_code": province_code
            }
            
            # Store in Redis with appropriate TTL
            ttl = settings.REDIS_CART_TTL_USER if user_id else settings.REDIS_CART_TTL_GUEST
            await self.set_hash(cart_key, cart_data, ttl)
        else:
            # Update location if provided
            if country_code != cart_data.get('country_code') or province_code != cart_data.get('province_code'):
                cart_data['country_code'] = country_code
                cart_data['province_code'] = province_code
                await self._update_cart_totals(cart_data, cart_key)
        
        return cart_data

    async def add_to_cart(
        self,
        user_id: Optional[UUID] = None,
        variant_id: UUID = None,
        quantity: int = 1,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add item to cart in Redis"""
        
        # Get variant to check availability and get current price
        result = await self.db.execute(
            select(ProductVariant)
            .options(selectinload(ProductVariant.product))
            .where(ProductVariant.id == variant_id)
        )
        variant = result.scalar_one_or_none()
        
        if not variant:
            raise HTTPException(status_code=404, detail="Product variant not found")
        
        if not variant.is_active:
            raise HTTPException(status_code=400, detail="Product variant is not available")
        
        if variant.stock < quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock. Only {variant.stock} items available"
            )
        
        # Get cart
        cart_data = await self.get_cart(user_id, session_id)
        cart_key = RedisKeyManager.cart_key(
            str(user_id) if user_id else f"guest:{cart_data['session_id']}"
        )
        
        # Check if item already exists in cart
        items = cart_data.get('items', [])
        existing_item = None
        for item in items:
            if item['variant_id'] == str(variant_id):
                existing_item = item
                break
        
        if existing_item:
            # Update existing item
            new_quantity = existing_item['quantity'] + quantity
            if variant.stock < new_quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot add {quantity} more items. Only {variant.stock - existing_item['quantity']} more available"
                )
            
            existing_item['quantity'] = new_quantity
            existing_item['price_per_unit'] = float(variant.current_price)
            existing_item['total_price'] = existing_item['quantity'] * existing_item['price_per_unit']
        else:
            # Add new item
            new_item = {
                "id": str(uuid4()),
                "variant_id": str(variant_id),
                "product_id": str(variant.product_id),
                "quantity": quantity,
                "price_per_unit": float(variant.current_price),
                "total_price": quantity * float(variant.current_price),
                "product_name": variant.product.name if variant.product else "Unknown Product",
                "variant_name": variant.name or "Default",
                "added_at": datetime.utcnow().isoformat()
            }
            items.append(new_item)
        
        cart_data['items'] = items
        cart_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Update totals
        await self._update_cart_totals(cart_data, cart_key)
        
        # Schedule background task for inventory check using ARQ
        await self._enqueue_inventory_check(variant_id, quantity)
        
        return cart_data

    async def update_cart_item_quantity(
        self,
        user_id: Optional[UUID] = None,
        cart_item_id: UUID = None,
        quantity: int = 1,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update cart item quantity in Redis"""
        
        if quantity <= 0:
            return await self.remove_from_cart_by_item_id(user_id, cart_item_id, session_id)
        
        # Get cart
        cart_data = await self.get_cart(user_id, session_id)
        cart_key = RedisKeyManager.cart_key(
            str(user_id) if user_id else f"guest:{cart_data['session_id']}"
        )
        
        # Find item by cart_item_id
        items = cart_data.get('items', [])
        item_to_update = None
        for item in items:
            if item['id'] == str(cart_item_id):
                item_to_update = item
                break
        
        if not item_to_update:
            raise HTTPException(status_code=404, detail="Cart item not found")
        
        # Check stock availability
        result = await self.db.execute(
            select(ProductVariant)
            .options(selectinload(ProductVariant.inventory))
            .where(ProductVariant.id == UUID(item_to_update['variant_id']))
        )
        variant = result.scalar_one_or_none()
        
        if not variant:
            raise HTTPException(status_code=404, detail="Product variant not found")
        
        if variant.stock < quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Only {variant.stock} items available"
            )
        
        # Update item
        item_to_update['quantity'] = quantity
        item_to_update['price_per_unit'] = float(variant.current_price)
        item_to_update['total_price'] = quantity * float(variant.current_price)
        
        cart_data['items'] = items
        cart_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Update totals
        await self._update_cart_totals(cart_data, cart_key)
        
        return cart_data

    async def remove_from_cart_by_item_id(
        self,
        user_id: Optional[UUID] = None,
        cart_item_id: UUID = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Remove item from cart by cart_item_id"""
        
        # Get cart
        cart_data = await self.get_cart(user_id, session_id)
        cart_key = RedisKeyManager.cart_key(
            str(user_id) if user_id else f"guest:{cart_data['session_id']}"
        )
        
        # Remove item by cart_item_id
        items = cart_data.get('items', [])
        original_length = len(items)
        items = [item for item in items if item['id'] != str(cart_item_id)]
        
        if len(items) == original_length:
            raise HTTPException(status_code=404, detail="Cart item not found")
        
        cart_data['items'] = items
        cart_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Update totals
        await self._update_cart_totals(cart_data, cart_key)
        
        return cart_data

    async def clear_cart(
        self,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clear all items from cart"""
        
        cart_key = RedisKeyManager.cart_key(
            str(user_id) if user_id else f"guest:{session_id}"
        )
        
        # Get current cart to preserve metadata
        cart_data = await self.get_cart(user_id, session_id)
        
        # Clear items and reset totals
        cart_data['items'] = []
        cart_data['subtotal'] = 0.0
        cart_data['tax_amount'] = 0.0
        cart_data['shipping_amount'] = 0.0
        cart_data['total_amount'] = 0.0
        cart_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Update in Redis
        ttl = settings.REDIS_CART_TTL_USER if user_id else settings.REDIS_CART_TTL_GUEST
        await self.set_hash(cart_key, cart_data, ttl)
        
        return cart_data

    async def get_cart_item_count(
        self,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None
    ) -> int:
        """Get total item count in cart"""
        
        cart_data = await self.get_cart(user_id, session_id)
        items = cart_data.get('items', [])
        return sum(item['quantity'] for item in items)

    async def merge_carts(self, user_id: UUID, guest_session_id: str) -> Dict[str, Any]:
        """Merge guest cart with user cart when user logs in"""
        
        user_cart_key = RedisKeyManager.cart_key(str(user_id))
        guest_cart_key = RedisKeyManager.cart_key(f"guest:{guest_session_id}")
        
        # Get both carts
        user_cart = await self.get_hash(user_cart_key) or {"items": []}
        guest_cart = await self.get_hash(guest_cart_key)
        
        if not guest_cart or not guest_cart.get('items'):
            # No guest cart to merge, return user cart
            return await self.get_cart(user_id)
        
        # Merge items
        user_items = user_cart.get('items', [])
        guest_items = guest_cart.get('items', [])
        
        # Create a map of user cart items by variant_id
        user_items_map = {item['variant_id']: item for item in user_items}
        
        # Merge guest items
        for guest_item in guest_items:
            variant_id = guest_item['variant_id']
            if variant_id in user_items_map:
                # Item exists in user cart, add quantities
                user_items_map[variant_id]['quantity'] += guest_item['quantity']
                user_items_map[variant_id]['total_price'] = (
                    user_items_map[variant_id]['quantity'] * 
                    user_items_map[variant_id]['price_per_unit']
                )
            else:
                # New item, add to user cart
                user_items.append(guest_item)
                user_items_map[variant_id] = guest_item
        
        # Update user cart
        merged_cart = {
            "user_id": str(user_id),
            "session_id": None,
            "items": list(user_items_map.values()),
            "created_at": user_cart.get('created_at', datetime.utcnow().isoformat()),
            "updated_at": datetime.utcnow().isoformat(),
            "country_code": guest_cart.get('country_code', 'US'),
            "province_code": guest_cart.get('province_code')
        }
        
        # Update totals
        await self._update_cart_totals(merged_cart, user_cart_key)
        
        # Delete guest cart
        await self.delete_key(guest_cart_key)
        
        return merged_cart

    async def validate_cart(
        self,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        country_code: str = 'US',
        province_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Comprehensive cart validation"""
        
        cart_data = await self.get_cart(user_id, session_id, country_code, province_code)
        items = cart_data.get('items', [])
        
        if not items:
            return {
                "valid": False,
                "can_checkout": False,
                "issues": [{"severity": "error", "message": "Cart is empty"}],
                "cart": cart_data
            }
        
        issues = []
        valid_items = []
        
        # Validate each item
        for item in items:
            try:
                result = await self.db.execute(
                    select(ProductVariant)
                    .options(selectinload(ProductVariant.inventory), selectinload(ProductVariant.product))
                    .where(ProductVariant.id == UUID(item['variant_id']))
                )
                variant = result.scalar_one_or_none()
                
                if not variant:
                    issues.append({
                        "severity": "error",
                        "message": f"Product variant {item['variant_id']} not found",
                        "item_id": item['id']
                    })
                    continue
                
                if not variant.is_active:
                    issues.append({
                        "severity": "error",
                        "message": f"Product '{item['product_name']}' is no longer available",
                        "item_id": item['id']
                    })
                    continue
                
                if variant.stock < item['quantity']:
                    issues.append({
                        "severity": "error",
                        "message": f"Insufficient stock for '{item['product_name']}'. Only {variant.stock} available",
                        "item_id": item['id'],
                        "available_quantity": variant.stock
                    })
                    continue
                
                # Check price changes
                current_price = float(variant.current_price)
                if abs(current_price - item['price_per_unit']) > 0.01:
                    issues.append({
                        "severity": "warning",
                        "message": f"Price changed for '{item['product_name']}'. Was ${item['price_per_unit']:.2f}, now ${current_price:.2f}",
                        "item_id": item['id'],
                        "old_price": item['price_per_unit'],
                        "new_price": current_price
                    })
                    # Update price in cart
                    item['price_per_unit'] = current_price
                    item['total_price'] = item['quantity'] * current_price
                
                valid_items.append(item)
                
            except Exception as e:
                logger.error(f"Error validating cart item {item['id']}: {e}")
                issues.append({
                    "severity": "error",
                    "message": f"Error validating item: {str(e)}",
                    "item_id": item['id']
                })
        
        # Update cart with valid items and recalculate totals
        cart_data['items'] = valid_items
        if valid_items != items:  # Items were modified
            cart_key = RedisKeyManager.cart_key(
                str(user_id) if user_id else f"guest:{cart_data['session_id']}"
            )
            await self._update_cart_totals(cart_data, cart_key)
        
        error_count = len([issue for issue in issues if issue.get("severity") == "error"])
        can_checkout = error_count == 0 and len(valid_items) > 0
        
        return {
            "valid": error_count == 0,
            "can_checkout": can_checkout,
            "issues": issues,
            "cart": cart_data
        }

    async def _update_cart_totals(self, cart_data: Dict[str, Any], cart_key: str):
        """Update cart totals and save to Redis"""
        
        items = cart_data.get('items', [])
        
        # Calculate subtotal
        subtotal = sum(item['total_price'] for item in items)
        cart_data['subtotal'] = subtotal
        
        # Calculate shipping (free over $100)
        shipping_amount = 0.0 if subtotal >= 100 else 9.99
        cart_data['shipping_amount'] = shipping_amount
        
        # Calculate tax
        tax_amount = 0.0
        try:
            country = cart_data.get('country_code', 'US')
            province = cart_data.get('province_code')
            
            tax_rate = await self.tax_service.get_tax_rate(country, province)
            if tax_rate:
                taxable_amount = subtotal + shipping_amount
                tax_amount = taxable_amount * float(tax_rate)
        except Exception as e:
            logger.warning(f"Tax calculation failed: {e}")
        
        cart_data['tax_amount'] = tax_amount
        cart_data['total_amount'] = subtotal + shipping_amount + tax_amount
        
        # Save to Redis
        user_id = cart_data.get('user_id')
        ttl = settings.REDIS_CART_TTL_USER if user_id else settings.REDIS_CART_TTL_GUEST
        await self.set_hash(cart_key, cart_data, ttl)

    async def _enqueue_inventory_check(self, variant_id: UUID, requested_quantity: int):
        """Enqueue inventory check task using hybrid approach"""
        try:
            from core.hybrid_tasks import update_inventory_hybrid
            await update_inventory_hybrid(
                None,  # No background_tasks, use ARQ
                str(variant_id), 
                "check_low_stock",
                use_arq=True,  # Use ARQ for reliability
                requested_quantity=requested_quantity
            )
        except Exception as e:
            logger.error(f"Failed to enqueue inventory check for variant {variant_id}: {e}")

    async def _check_inventory_levels(self, variant_id: UUID, requested_quantity: int):
        """Background task to check inventory levels and send alerts if needed"""
        try:
            # Create a new database session for the background task
            from core.database import AsyncSessionDB
            async with AsyncSessionDB() as db:
                result = await db.execute(
                    select(ProductVariant)
                    .options(selectinload(ProductVariant.inventory))
                    .where(ProductVariant.id == variant_id)
                )
                variant = result.scalar_one_or_none()
                
                if variant and variant.stock <= 10:  # Low stock threshold
                    logger.warning(f"Low stock alert: Variant {variant_id} has only {variant.stock} items left")
                    # Here you could send notifications, update analytics, etc.
                    
        except Exception as e:
            logger.error(f"Error checking inventory levels for variant {variant_id}: {e}")

    # Additional methods for compatibility with existing routes
    async def apply_promocode(self, user_id: Optional[UUID], code: str, session_id: Optional[str] = None):
        """Apply promocode to cart - placeholder for future implementation"""
        # TODO: Implement promocode logic
        raise HTTPException(status_code=501, detail="Promocode functionality not implemented yet")

    async def remove_promocode(self, user_id: Optional[UUID], session_id: Optional[str] = None):
        """Remove promocode from cart - placeholder for future implementation"""
        # TODO: Implement promocode logic
        raise HTTPException(status_code=501, detail="Promocode functionality not implemented yet")

    async def get_shipping_options(self, user_id: Optional[UUID], address: dict, session_id: Optional[str] = None):
        """Get shipping options - placeholder for future implementation"""
        # TODO: Implement shipping options logic
        return {
            "options": [
                {"id": "standard", "name": "Standard Shipping", "price": 9.99, "days": "5-7"},
                {"id": "express", "name": "Express Shipping", "price": 19.99, "days": "2-3"}
            ]
        }

    async def calculate_totals(self, user_id: Optional[UUID], data: dict, session_id: Optional[str] = None):
        """Calculate cart totals with additional data"""
        cart_data = await self.get_cart(user_id, session_id)
        return {
            "subtotal": cart_data['subtotal'],
            "tax_amount": cart_data['tax_amount'],
            "shipping_amount": cart_data['shipping_amount'],
            "total_amount": cart_data['total_amount']
        }

    async def get_checkout_summary(self, user_id: Optional[UUID], session_id: Optional[str] = None):
        """Get checkout summary"""
        cart_data = await self.get_cart(user_id, session_id)
        return {
            "cart": cart_data,
            "item_count": len(cart_data.get('items', [])),
            "summary": {
                "subtotal": cart_data['subtotal'],
                "shipping_amount": cart_data['shipping_amount'],
                "tax_amount": cart_data['tax_amount'],
                "total_amount": cart_data['total_amount'],
                "free_shipping_eligible": cart_data['subtotal'] >= 100,
                "free_shipping_remaining": max(0, 100 - cart_data['subtotal']) if cart_data['subtotal'] < 100 else 0
            }
        }