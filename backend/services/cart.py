from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, and_, func, update
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from typing import Optional, Dict, Any, List
from uuid import UUID
from core.utils.uuid_utils import uuid7
from decimal import Decimal
from datetime import datetime
import logging

from models.cart import Cart, CartItem
from models.product import ProductVariant, Product
from models.user import User
from services.tax import TaxService
from core.config import settings

logger = logging.getLogger(__name__)


class CartService:
    """
    PostgreSQL-based cart service
    Uses PostgreSQL for persistent cart storage
    """
    
    def __init__(self, db: AsyncSession):
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
        Get cart from PostgreSQL
        For authenticated users, use user_id
        For guests, session-based carts are not supported in PostgreSQL version
        """
        if not user_id:
            # Return empty cart for guests - they need to login to use cart
            return {
                "user_id": None,
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

        # Get or create cart for authenticated user
        result = await self.db.execute(
            select(Cart)
            .options(
                selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.images),
                selectinload(Cart.items).selectinload(CartItem.variant).selectinload(ProductVariant.product),
                selectinload(Cart.items).selectinload(CartItem.product)
            )
            .where(Cart.user_id == user_id)
        )
        cart = result.scalar_one_or_none()

        if not cart:
            # Create new cart
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            await self.db.commit()
            await self.db.refresh(cart)

        # Calculate totals
        subtotal = sum((item.total_price for item in cart.items), Decimal('0.0'))
        
        # Calculate tax if location provided
        tax_amount = Decimal('0.0')
        if country_code and subtotal > 0:
            try:
                tax_rate = await self.tax_service.get_tax_rate(country_code, province_code)
                if tax_rate:
                    # Convert tax_rate to Decimal to avoid mixing Decimal and float
                    tax_amount = subtotal * Decimal(str(tax_rate))
            except Exception as e:
                logger.warning(f"Failed to calculate tax: {e}")

        # For now, shipping is 0 - can be calculated based on items/location
        shipping_amount = Decimal('0.0')
        total_amount = subtotal + tax_amount + shipping_amount

        # Convert cart to dict format expected by frontend
        cart_data = {
            "id": str(cart.id),
            "user_id": str(cart.user_id),
            "items": [],
            "subtotal": float(subtotal),
            "tax_amount": float(tax_amount),
            "shipping_amount": float(shipping_amount),
            "total_amount": float(total_amount),
            "item_count": len(cart.items),
            "total_items": sum((item.quantity for item in cart.items), 0),
            "currency": "USD",  # Can be made configurable
            "created_at": cart.created_at.isoformat() if cart.created_at else None,
            "updated_at": cart.updated_at.isoformat() if cart.updated_at else None,
            "country_code": country_code,
            "province_code": province_code
        }

        # Enrich cart items with detailed variant data
        for item in cart.items:
            variant = item.variant
            product = item.product or variant.product if variant else None
            
            item_data = {
                "id": item.id,
                "cart_id": item.cart_id,
                "variant_id": item.variant_id,
                "quantity": item.quantity,
                "price_per_unit": float(item.price_per_unit),
                "total_price": float(item.total_price),
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None
            }

            # Add comprehensive variant data if available
            if variant:
                # Calculate discount information
                discount_percentage = 0
                if variant.sale_price and variant.sale_price < variant.base_price:
                    discount_percentage = round(((variant.base_price - variant.sale_price) / variant.base_price) * 100, 2)
                
                variant_dict = {
                    'id': variant.id,
                    'product_id': variant.product_id,
                    'sku': variant.sku,
                    'name': variant.name,
                    'base_price': float(variant.base_price),
                    'sale_price': float(variant.sale_price) if variant.sale_price else None,
                    'current_price': float(variant.current_price),
                    'discount_percentage': discount_percentage,
                    'stock': variant.stock,
                    'is_active': variant.is_active,
                    'attributes': variant.attributes or {},
                    'barcode': variant.barcode,
                    'qr_code': variant.qr_code,
                    'created_at': variant.created_at.isoformat() if variant.created_at else None,
                    'updated_at': variant.updated_at.isoformat() if variant.updated_at else None,
                    'images': [],
                    'primary_image': None,
                    'image_count': len(variant.images) if variant.images else 0
                }
                
                # Add detailed product information
                if product:
                    variant_dict.update({
                        'product_name': product.name,
                        'product_description': product.description,
                        'product_short_description': product.short_description,
                        'product_slug': product.slug,
                        'product_category_id': str(product.category_id),
                        'product_rating_average': product.rating_average,
                        'product_rating_count': product.rating_count,
                        'product_is_featured': product.is_featured,
                        'product_specifications': product.specifications,
                        'product_dietary_tags': product.dietary_tags,
                        'product_tags': product.tags.split(",") if product.tags else [],
                        'product_origin': product.origin
                    })
                
                # Process images with detailed information
                if variant.images:
                    # Sort images by sort_order, then by is_primary (primary first)
                    sorted_images = sorted(variant.images, key=lambda x: (not x.is_primary, x.sort_order))
                    
                    variant_dict['images'] = [
                        {
                            'id': img.id,
                            'variant_id': img.variant_id,
                            'url': img.url,
                            'alt_text': img.alt_text or f"{variant.name} - Image {img.sort_order + 1}",
                            'is_primary': img.is_primary,
                            'sort_order': img.sort_order,
                            'format': img.format,
                            'created_at': img.created_at.isoformat() if img.created_at else None
                        }
                        for img in sorted_images
                    ]
                    
                    # Set primary image (first primary image or first image)
                    primary_img = next((img for img in sorted_images if img.is_primary), sorted_images[0] if sorted_images else None)
                    if primary_img:
                        variant_dict['primary_image'] = {
                            'id': primary_img.id,
                            'variant_id': primary_img.variant_id,
                            'url': primary_img.url,
                            'alt_text': primary_img.alt_text or f"{variant.name} - Primary Image",
                            'is_primary': primary_img.is_primary,
                            'sort_order': primary_img.sort_order,
                            'format': primary_img.format,
                            'created_at': primary_img.created_at.isoformat() if primary_img.created_at else None
                        }
                else:
                    # Provide fallback image information
                    variant_dict['images'] = []
                    variant_dict['primary_image'] = {
                        'id': None,
                        'variant_id': variant.id,
                        'url': '/placeholder-product.jpg',  # Fallback image
                        'alt_text': f"{variant.name} - No Image Available",
                        'is_primary': True,
                        'sort_order': 0,
                        'format': 'jpg',
                        'created_at': None
                    }
                
                # Add inventory information
                if hasattr(variant, 'inventory') and variant.inventory:
                    variant_dict.update({
                        'inventory_quantity_available': variant.inventory.quantity_available,
                        'inventory_reorder_level': variant.inventory.reorder_point,
                        'inventory_last_updated': variant.inventory.updated_at.isoformat() if variant.inventory.updated_at else None
                    })
                
                item_data['variant'] = variant_dict

            cart_data['items'].append(item_data)

        return cart_data

    async def add_to_cart(
        self,
        user_id: Optional[UUID] = None,
        variant_id: UUID = None,
        quantity: int = 1,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add item to cart in PostgreSQL"""
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User must be authenticated to add items to cart")

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

        # Get or create cart
        result = await self.db.execute(
            select(Cart).where(Cart.user_id == user_id)
        )
        cart = result.scalar_one_or_none()
        
        if not cart:
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            await self.db.flush()  # Get the cart ID

        # Check if item already exists in cart
        result = await self.db.execute(
            select(CartItem).where(
                and_(
                    CartItem.cart_id == cart.id,
                    CartItem.variant_id == variant_id
                )
            )
        )
        existing_item = result.scalar_one_or_none()

        if existing_item:
            # Update existing item
            new_quantity = existing_item.quantity + quantity
            if variant.stock < new_quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot add {quantity} more items. Only {variant.stock - existing_item.quantity} more available"
                )
            
            existing_item.quantity = new_quantity
            existing_item.price_per_unit = variant.current_price
        else:
            # Add new item
            new_item = CartItem(
                id=uuid7(),
                cart_id=cart.id,
                product_id=variant.product_id,
                variant_id=variant_id,
                quantity=quantity,
                price_per_unit=variant.current_price
            )
            self.db.add(new_item)

        await self.db.commit()
        
        # Return updated cart
        return await self.get_cart(user_id=user_id)

    async def update_cart_item_quantity(
        self,
        user_id: Optional[UUID] = None,
        cart_item_id: UUID = None,
        quantity: int = 1,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update cart item quantity"""
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User must be authenticated")

        # Get cart item
        result = await self.db.execute(
            select(CartItem)
            .options(selectinload(CartItem.variant))
            .join(Cart)
            .where(
                and_(
                    CartItem.id == cart_item_id,
                    Cart.user_id == user_id
                )
            )
        )
        cart_item = result.scalar_one_or_none()
        
        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        # Check stock availability
        variant = cart_item.variant
        if not variant:
            raise HTTPException(status_code=404, detail="Product variant not found")
        
        if variant.stock < quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Only {variant.stock} items available"
            )

        # Update item
        cart_item.quantity = quantity
        cart_item.price_per_unit = variant.current_price
        
        await self.db.commit()
        
        # Return updated cart
        return await self.get_cart(user_id=user_id)

    async def remove_from_cart_by_item_id(
        self,
        user_id: Optional[UUID] = None,
        cart_item_id: UUID = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Remove item from cart by item ID"""
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User must be authenticated")

        # Delete cart item
        result = await self.db.execute(
            delete(CartItem)
            .where(
                and_(
                    CartItem.id == cart_item_id,
                    CartItem.cart_id.in_(
                        select(Cart.id).where(Cart.user_id == user_id)
                    )
                )
            )
        )
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Cart item not found")

        await self.db.commit()
        
        # Return updated cart
        return await self.get_cart(user_id=user_id)

    async def clear_cart(
        self,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clear all items from cart"""
        
        if not user_id:
            raise HTTPException(status_code=401, detail="User must be authenticated")

        # Delete all cart items for user
        await self.db.execute(
            delete(CartItem)
            .where(
                CartItem.cart_id.in_(
                    select(Cart.id).where(Cart.user_id == user_id)
                )
            )
        )
        
        await self.db.commit()
        
        # Return empty cart
        return await self.get_cart(user_id=user_id)

    async def get_cart_item_count(
        self,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None
    ) -> int:
        """Get total number of items in cart"""
        
        if not user_id:
            return 0

        result = await self.db.execute(
            select(func.coalesce(func.sum(CartItem.quantity), 0))
            .select_from(CartItem)
            .join(Cart)
            .where(Cart.user_id == user_id)
        )
        
        return result.scalar() or 0

    async def merge_guest_cart(
        self,
        user_id: UUID,
        guest_cart_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge guest cart with user cart after login
        Since PostgreSQL version doesn't support guest carts,
        this is mainly for compatibility
        """
        # For PostgreSQL version, just return the user's existing cart
        return await self.get_cart(user_id=user_id)

    async def get_checkout_summary(
        self,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get cart summary for checkout"""
        
        cart_data = await self.get_cart(user_id=user_id, session_id=session_id)
        
        # Add checkout-specific information
        checkout_summary = {
            **cart_data,
            "can_checkout": len(cart_data["items"]) > 0 and cart_data["total_amount"] > 0,
            "checkout_url": "/checkout",
            "estimated_delivery": "3-5 business days"  # Can be made dynamic
        }
        
        return checkout_summary

    async def validate_cart(
        self,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None,
        country_code: str = 'US',
        province_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate cart items for stock and pricing"""
        
        cart_data = await self.get_cart(
            user_id=user_id, 
            session_id=session_id,
            country_code=country_code,
            province_code=province_code
        )
        issues = []
        
        for item in cart_data["items"]:
            variant = item.get("variant")
            if not variant:
                issues.append({
                    "item_id": item["id"],
                    "severity": "error",
                    "message": "Product variant not found"
                })
                continue
                
            # Check stock
            if variant["stock"] < item["quantity"]:
                issues.append({
                    "item_id": item["id"],
                    "severity": "warning",
                    "message": f"Only {variant['stock']} items available, but {item['quantity']} requested"
                })
            
            # Check if price changed
            if abs(float(item["price_per_unit"]) - float(variant["current_price"])) > 0.01:
                issues.append({
                    "item_id": item["id"],
                    "severity": "info",
                    "message": f"Price changed from ${item['price_per_unit']:.2f} to ${variant['current_price']:.2f}"
                })

        return {
            "valid": len([i for i in issues if i["severity"] == "error"]) == 0,
            "can_checkout": len([i for i in issues if i["severity"] in ["error", "warning"]]) == 0,
            "issues": issues,
            "cart": cart_data,
            "summary": {
                "total_items": len(cart_data["items"]),
                "total_amount": cart_data["total_amount"],
                "issues_count": len(issues)
            },
            "validation_timestamp": datetime.utcnow().isoformat()
        }

    async def apply_promocode(
        self,
        user_id: Optional[UUID] = None,
        code: str = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Apply promocode to cart (placeholder implementation)"""
        # This would integrate with a promocode service
        # For now, return cart without changes
        cart_data = await self.get_cart(user_id=user_id, session_id=session_id)
        return {
            **cart_data,
            "promocode_applied": False,
            "message": "Promocode functionality not yet implemented"
        }

    async def remove_promocode(
        self,
        user_id: Optional[UUID] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Remove promocode from cart (placeholder implementation)"""
        # This would integrate with a promocode service
        # For now, return cart without changes
        cart_data = await self.get_cart(user_id=user_id, session_id=session_id)
        return {
            **cart_data,
            "promocode_removed": True,
            "message": "Promocode removed"
        }

    async def get_shipping_options(
        self,
        user_id: Optional[UUID] = None,
        address: Dict[str, Any] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get shipping options for cart from database"""
        from models.shipping import ShippingMethod
        from sqlalchemy import select
        
        try:
            # Get active shipping methods from database
            result = await self.db.execute(
                select(ShippingMethod).where(ShippingMethod.is_active == True)
            )
            shipping_methods = result.scalars().all()
            
            # Convert to API format
            shipping_options = []
            for method in shipping_methods:
                shipping_options.append({
                    "id": str(method.id),  # Convert UUID to string for JSON serialization
                    "name": method.name,
                    "description": method.description or f"{method.estimated_days} business days",
                    "price": method.price,
                    "estimated_days": str(method.estimated_days)
                })
            
            # If no shipping methods in database, return default options
            if not shipping_options:
                shipping_options = [
                    {
                        "id": "standard",
                        "name": "Standard Shipping",
                        "description": "3-5 business days",
                        "price": 5.99,
                        "estimated_days": "3-5"
                    },
                    {
                        "id": "express",
                        "name": "Express Shipping", 
                        "description": "1-2 business days",
                        "price": 12.99,
                        "estimated_days": "1-2"
                    }
                ]
            
            return {
                "shipping_options": shipping_options
            }
            
        except Exception as e:
            # Fallback to default options if database query fails
            return {
                "shipping_options": [
                    {
                        "id": "standard",
                        "name": "Standard Shipping",
                        "description": "3-5 business days",
                        "price": 5.99,
                        "estimated_days": "3-5"
                    },
                    {
                        "id": "express",
                        "name": "Express Shipping",
                        "description": "1-2 business days", 
                        "price": 12.99,
                        "estimated_days": "1-2"
                    }
                ]
            }

    async def calculate_totals(
        self,
        user_id: Optional[UUID] = None,
        data: Dict[str, Any] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate cart totals with shipping and tax"""
        cart_data = await self.get_cart(user_id=user_id, session_id=session_id)
        
        # Extract shipping method from data
        shipping_cost = 0.0
        if data and "shipping_method_id" in data:
            shipping_options = await self.get_shipping_options(user_id, session_id=session_id)
            for option in shipping_options.get("shipping_options", []):
                if option["id"] == data["shipping_method_id"]:
                    shipping_cost = option["price"]
                    break
        
        # Recalculate totals
        subtotal = cart_data["subtotal"]
        tax_amount = cart_data["tax_amount"]
        total_amount = subtotal + tax_amount + shipping_cost
        
        return {
            **cart_data,
            "shipping_amount": shipping_cost,
            "total_amount": total_amount,
            "calculation_timestamp": datetime.utcnow().isoformat()
        }

    async def merge_carts(
        self,
        user_id: UUID,
        session_id: str
    ) -> Dict[str, Any]:
        """Merge guest cart with user cart after login"""
        # For PostgreSQL version, just return the user's existing cart
        # since we don't support guest carts in this implementation
        return await self.get_cart(user_id=user_id)