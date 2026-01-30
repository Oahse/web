# Consolidated admin service
# This file includes all admin-related functionality including pricing and analytics

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, String
from sqlalchemy.orm import selectinload
from fastapi import HTTPException
from models.user import User
from uuid import UUID
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
from decimal import Decimal



class AdminService:
    """Consolidated admin service with comprehensive admin functionality"""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- User Management ---
    async def get_all_users(
        self,
        page: int = 1,
        limit: int = 20,
        role_filter: Optional[str] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
        verified: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get all users with pagination and filtering"""
        offset = (page - 1) * limit
        
        query = select(User)
        count_query = select(func.count(User.id))
        
        conditions = []
        if search:
            conditions.append(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.firstname.ilike(f"%{search}%"),
                    User.lastname.ilike(f"%{search}%")
                )
            )
        
        if role_filter:
            conditions.append(User.role == role_filter)
            
        if status:
            # Assuming status refers to is_active field
            if status.lower() == 'active':
                conditions.append(User.is_active == True)
            elif status.lower() == 'inactive':
                conditions.append(User.is_active == False)
                
        if verified is not None:
            conditions.append(User.verified == verified)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        query = query.order_by(desc(User.created_at)).offset(offset).limit(limit)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        total = await self.db.scalar(count_query)
        
        return {
            "users": [
                {
                    "id": str(user.id),
                    "email": user.email,
                    "firstname": user.firstname,
                    "lastname": user.lastname,
                    "role": user.role,
                    "is_active": user.is_active,
                    "verified": user.verified,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "last_login": user.last_login.isoformat() if user.last_login else None
                }
                for user in users
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    async def update_user_role(
        self,
        user_id: UUID,
        new_role: str,
        admin_user_id: UUID
    ) -> User:
        """Update a user's role"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        old_role = user.role
        user.role = new_role
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user

    async def deactivate_user(
        self,
        user_id: UUID,
        admin_user_id: UUID
    ) -> User:
        """Deactivate a user account"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user.is_active = False
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get admin dashboard statistics"""
        try:
            from models.orders import Order
            from models.product import Product
            from models.subscriptions import Subscription
            from datetime import datetime, timedelta
            
            # Calculate date ranges
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)
            last_week = today - timedelta(days=7)
            last_month = today - timedelta(days=30)
            
            # Get total users
            total_users = await self.db.scalar(select(func.count(User.id)))
            active_users = await self.db.scalar(
                select(func.count(User.id)).where(User.is_active == True)
            )
            
            # Get total orders
            total_orders = await self.db.scalar(select(func.count(Order.id)))
            orders_today = await self.db.scalar(
                select(func.count(Order.id)).where(
                    func.date(Order.created_at) == today
                )
            )
            
            # Get total products
            total_products = await self.db.scalar(select(func.count(Product.id)))
            active_products = await self.db.scalar(
                select(func.count(Product.id)).where(Product.is_active == True)
            )
            
            # Get revenue data
            total_revenue = await self.db.scalar(
                select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                    Order.order_status.in_(['DELIVERED', 'SHIPPED', 'PROCESSING'])
                )
            ) or 0
            
            revenue_today = await self.db.scalar(
                select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                    and_(
                        Order.order_status.in_(['DELIVERED', 'SHIPPED', 'PROCESSING']),
                        func.date(Order.created_at) == today
                    )
                )
            ) or 0
            
            revenue_this_month = await self.db.scalar(
                select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                    and_(
                        Order.order_status.in_(['DELIVERED', 'SHIPPED', 'PROCESSING']),
                        Order.created_at >= last_month
                    )
                )
            ) or 0
            
            # Get subscription stats if available
            total_subscriptions = 0
            active_subscriptions = 0
            try:
                total_subscriptions = await self.db.scalar(select(func.count(Subscription.id))) or 0
                active_subscriptions = await self.db.scalar(
                    select(func.count(Subscription.id)).where(Subscription.status == "active")
                ) or 0
            except Exception:
                # Subscription table might not exist
                pass
            
            # Recent orders
            recent_orders_result = await self.db.execute(
                select(Order)
                .options(selectinload(Order.user))
                .order_by(desc(Order.created_at))
                .limit(5)
            )
            recent_orders = recent_orders_result.scalars().all()
            
            return {
                "overview": {
                    "total_users": total_users,
                    "active_users": active_users,
                    "total_orders": total_orders,
                    "orders_today": orders_today,
                    "total_products": total_products,
                    "active_products": active_products,
                    "total_subscriptions": total_subscriptions,
                    "active_subscriptions": active_subscriptions
                },
                "revenue": {
                    "total_revenue": float(total_revenue),
                    "revenue_today": float(revenue_today),
                    "revenue_this_month": float(revenue_this_month),
                    "currency": "USD"
                },
                "recent_orders": [
                    {
                        "id": str(order.id),
                        "user_email": order.user.email if order.user else "Unknown",
                        "total_amount": float(order.total_amount),
                        "status": order.order_status,
                        "created_at": order.created_at.isoformat() if order.created_at else None
                    }
                    for order in recent_orders
                ],
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            # Return basic stats on error
            return {
                "overview": {
                    "total_users": 0,
                    "active_users": 0,
                    "total_orders": 0,
                    "orders_today": 0,
                    "total_products": 0,
                    "active_products": 0,
                    "total_subscriptions": 0,
                    "active_subscriptions": 0
                },
                "revenue": {
                    "total_revenue": 0.0,
                    "revenue_today": 0.0,
                    "revenue_this_month": 0.0,
                    "currency": "USD"
                },
                "recent_orders": [],
                "error": f"Failed to fetch complete stats: {str(e)}",
                "generated_at": datetime.utcnow().isoformat()
            }

    async def get_platform_overview(self) -> Dict[str, Any]:
        """Get platform overview statistics"""
        try:
            from models.orders import Order, OrderItem
            from models.product import Product, ProductVariant
            from datetime import datetime, timedelta
            
            # Get basic counts
            stats = await self.get_dashboard_stats()
            
            # Additional platform metrics
            last_30_days = datetime.utcnow() - timedelta(days=30)
            
            # Order status distribution
            order_statuses = await self.db.execute(
                select(Order.order_status, func.count(Order.id).label('count'))
                .group_by(Order.order_status)
            )
            status_distribution = {status: count for status, count in order_statuses.all()}
            
            # Growth metrics
            new_users_last_30_days = await self.db.scalar(
                select(func.count(User.id)).where(User.created_at >= last_30_days)
            ) or 0
            
            new_orders_last_30_days = await self.db.scalar(
                select(func.count(Order.id)).where(Order.created_at >= last_30_days)
            ) or 0
            
            # Top products by sales (last 30 days)
            top_products_query = await self.db.execute(
                select(
                    Product.id,
                    Product.name,
                    func.sum(OrderItem.quantity).label('sales'),
                    func.sum(OrderItem.quantity * OrderItem.price_per_unit).label('revenue')
                )
                .select_from(OrderItem)
                .join(ProductVariant, OrderItem.variant_id == ProductVariant.id)
                .join(Product, ProductVariant.product_id == Product.id)
                .join(Order, OrderItem.order_id == Order.id)
                .where(
                    and_(
                        Order.created_at >= last_30_days,
                        Order.order_status.in_(['DELIVERED', 'SHIPPED', 'PROCESSING'])
                    )
                )
                .group_by(Product.id, Product.name)
                .order_by(func.sum(OrderItem.quantity * OrderItem.price_per_unit).desc())
                .limit(5)
            )
            
            top_products = [
                {
                    "id": str(product.id),
                    "name": product.name,
                    "image": "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?ixlib=rb-4.0.3&auto=format&fit=crop&w=100&q=80",
                    "sales": int(product.sales or 0),
                    "revenue": float(product.revenue or 0)
                }
                for product in top_products_query.all()
            ]
            
            return {
                **stats,
                "top_products": top_products,
                "platform_metrics": {
                    "order_status_distribution": status_distribution,
                    "growth_metrics": {
                        "new_users_last_30_days": new_users_last_30_days,
                        "new_orders_last_30_days": new_orders_last_30_days
                    }
                }
            }
            
        except Exception as e:
            return {
                "error": f"Failed to fetch platform overview: {str(e)}",
                "generated_at": datetime.utcnow().isoformat()
            }

    async def get_all_orders(
        self,
        page: int = 1,
        limit: int = 10,
        order_status: Optional[str] = None,
        q: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get all orders with filtering and pagination"""
        try:


            from models.orders import Order
            
            offset = (page - 1) * limit
            
            query = select(Order).options(selectinload(Order.user))
            count_query = select(func.count(Order.id))
            
            conditions = []
            
            if order_status:
                conditions.append(Order.order_status == order_status)
            
            if q:
                logger.debug(f"DEBUG: Processing 'q' filter. q type: {type(q)}, q value: {q}")
                conditions.append(
                    or_(
                        Order.id.cast(String).ilike(f"%{q}%"),
                        Order.user.has(User.email.ilike(f"%{q}%"))
                    )
                )
            
            if date_from:
                try:
                    date_from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                    conditions.append(Order.created_at >= date_from_dt)
                except ValueError:
                    pass
            
            if date_to:
                try:
                    date_to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                    conditions.append(Order.created_at <= date_to_dt)
                except ValueError:
                    pass
            
            if min_price is not None:
                conditions.append(Order.total_amount >= min_price)
            
            if max_price is not None:
                conditions.append(Order.total_amount <= max_price)
            
            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))
            
            query = query.order_by(desc(Order.created_at)).offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            orders = result.scalars().all()
            
            total = await self.db.scalar(count_query) or 0
            
            return {
                "data": [
                    {
                        "id": str(order.id),
                        "user_email": order.user.email if order.user else "Unknown",
                        "user": {
                            "firstname": order.user.firstname if order.user else None,
                            "lastname": order.user.lastname if order.user else None,
                            "email": order.user.email if order.user else "Unknown"
                        } if order.user else None,
                        "total_amount": float(order.total_amount),
                        "status": order.order_status,
                        "created_at": order.created_at.isoformat() if order.created_at else None,
                        "updated_at": order.updated_at.isoformat() if order.updated_at else None
                    }
                    for order in orders
                ],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit if total > 0 else 0
                }
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"DEBUG: Exception in get_all_orders: {type(e).__name__} - {e}")
            return {
                "data": [],
                "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0},
                "error": f"Failed to fetch orders: {str(e)}"
            }

    async def get_order_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get a single order by ID with items, product, variant, and variant images"""
        try:
            from models.orders import Order, OrderItem
            from models.product import ProductVariant, Product, ProductImage

            result = await self.db.execute(
                select(Order)
                .options(selectinload(Order.user))
                .options(
                    selectinload(Order.items)
                    .selectinload(OrderItem.variant)
                    .selectinload(ProductVariant.product),
                    selectinload(Order.items)
                    .selectinload(OrderItem.variant)
                    .selectinload(ProductVariant.images),
                )
                .where(Order.id == UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                return None

            def serialize_order_item(item) -> dict:
                variant = getattr(item, "variant", None)
                product = getattr(variant, "product", None) if variant else None
                images = list(getattr(variant, "images", None) or [])
                return {
                    "id": str(item.id),
                    "order_id": str(item.order_id),
                    "variant_id": str(item.variant_id),
                    "product_id": str(product.id) if product else None,
                    "product_name": getattr(product, "name", None) if product else None,
                    "variant_name": getattr(variant, "sku", None) or getattr(variant, "name", None) if variant else None,
                    "sku": getattr(variant, "sku", None) if variant else None,
                    "quantity": item.quantity,
                    "price_per_unit": float(item.price_per_unit),
                    "unit_price": float(item.price_per_unit),
                    "total_price": float(item.total_price),
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "product": {
                        "id": str(product.id),
                        "name": getattr(product, "name", None),
                        "slug": getattr(product, "slug", None),
                    } if product else None,
                    "variant": {
                        "id": str(variant.id),
                        "sku": getattr(variant, "sku", None),
                        "name": getattr(variant, "name", None),
                        "images": [
                            {"id": str(img.id), "url": img.url, "alt_text": img.alt_text, "is_primary": getattr(img, "is_primary", False)}
                            for img in images
                        ],
                    } if variant else None,
                }
            
            return {
                "id": str(order.id),
                "order_number": order.order_number,
                "user_email": order.user.email if order.user else "Unknown",
                "user": {
                    "firstname": order.user.firstname if order.user else None,
                    "lastname": order.user.lastname if order.user else None,
                    "email": order.user.email if order.user else "Unknown"
                } if order.user else None,
                "total_amount": float(order.total_amount),
                "sub_total": float(order.subtotal),
                "subtotal": float(order.subtotal),
                "shipping_cost": float(order.shipping_cost),
                "tax_amount": float(order.tax_amount),
                "tax_rate": float(order.tax_rate or 0),
                "currency": order.currency,
                "discount_amount": float(getattr(order, "discount_amount", 0.0)),
                "order_status": order.order_status.value if hasattr(order.order_status, "value") else order.order_status,
                "payment_status": order.payment_status.value if hasattr(order.payment_status, "value") else order.payment_status,
                "fulfillment_status": order.fulfillment_status.value if hasattr(order.fulfillment_status, "value") else order.fulfillment_status,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
                "confirmed_at": order.confirmed_at.isoformat() if order.confirmed_at else None,
                "shipped_at": order.shipped_at.isoformat() if order.shipped_at else None,
                "delivered_at": order.delivered_at.isoformat() if order.delivered_at else None,
                "cancelled_at": order.cancelled_at.isoformat() if order.cancelled_at else None,
                "shipping_method": order.shipping_method,
                "shipping_address": order.shipping_address,
                "billing_address": order.billing_address,
                "tracking_number": order.tracking_number,
                "carrier": order.carrier,
                "customer_notes": order.customer_notes,
                "internal_notes": order.internal_notes,
                "source": order.source.value if hasattr(order.source, "value") else order.source,
                "notes": order.notes,
                "items": [serialize_order_item(item) for item in order.items]

            }
            
        except Exception as e:
            print(f"Error fetching order by ID: {e}")
            return None


    async def get_all_products(
        self,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        supplier: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all products with complete data including images, SKU, category, price, stock status, and variants"""
        try:
            from models.product import Product, Category, ProductVariant, ProductImage
            from models.inventories import Inventory
            from models.user import User
            
            offset = (page - 1) * limit
            
            # Build query with all necessary joins
            query = select(Product).options(
                selectinload(Product.category),
                selectinload(Product.supplier),
                selectinload(Product.variants).selectinload(ProductVariant.images),
                selectinload(Product.variants).selectinload(ProductVariant.inventory)
            )
            count_query = select(func.count(Product.id))
            
            conditions = []
            
            if search:
                conditions.append(
                    or_(
                        Product.name.ilike(f"%{search}%"),
                        Product.description.ilike(f"%{search}%"),
                        Product.slug.ilike(f"%{search}%")
                    )
                )
            
            if category:
                # Join with Category to filter by category name
                category_subquery = select(Category.id).where(Category.name.ilike(f"%{category}%"))
                conditions.append(Product.category_id.in_(category_subquery))
            
            if status:
                if status == "active":
                    conditions.append(Product.is_active == True)
                elif status == "inactive":
                    conditions.append(Product.is_active == False)
                elif status == "draft":
                    conditions.append(Product.product_status == "draft")
                elif status == "discontinued":
                    conditions.append(Product.product_status == "discontinued")
            
            if supplier:
                # Join with User to filter by supplier name or email
                supplier_subquery = select(User.id).where(
                    or_(
                        User.email.ilike(f"%{supplier}%"),
                        User.firstname.ilike(f"%{supplier}%"),
                        User.lastname.ilike(f"%{supplier}%")
                    )
                )
                conditions.append(Product.supplier_id.in_(supplier_subquery))
            
            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))
            
            query = query.order_by(desc(Product.created_at)).offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            products = result.scalars().all()
            
            total = await self.db.scalar(count_query) or 0
            
            # Format products with complete data
            formatted_products = []
            for product in products:
                # Get primary variant and its data
                primary_variant = product.variants[0] if product.variants else None
                
                # Calculate total stock across all variants
                total_stock = sum(
                    variant.inventory.quantity_available if variant.inventory else 0 
                    for variant in product.variants
                )
                
                # Determine stock status
                if total_stock == 0:
                    stock_status = "out_of_stock"
                elif total_stock <= 10:  # Low stock threshold
                    stock_status = "low_stock"
                else:
                    stock_status = "in_stock"
                
                # Derive min/max price from variants when product.min_price/max_price are null
                variant_prices = [
                    (v.sale_price if v.sale_price is not None else v.base_price)
                    for v in product.variants
                    if v.is_active
                ] if product.variants else []
                min_price_val = product.min_price if product.min_price is not None else (min(variant_prices) if variant_prices else 0)
                max_price_val = product.max_price if product.max_price is not None else (max(variant_prices) if variant_prices else 0)
                
                # Format variants data
                variants_data = []
                for variant in product.variants:
                    current_price = variant.sale_price if variant.sale_price is not None else variant.base_price
                    variant_data = {
                        "id": str(variant.id),
                        "sku": variant.sku,
                        "name": variant.name,
                        "base_price": float(variant.base_price),
                        "sale_price": float(variant.sale_price) if variant.sale_price is not None else None,
                        "current_price": float(current_price),
                        "stock": variant.inventory.quantity_available if variant.inventory else 0,
                        "is_active": variant.is_active,
                        "attributes": variant.attributes,
                        "images": [
                            {
                                "id": str(img.id),
                                "url": img.url,
                                "alt_text": img.alt_text,
                                "is_primary": getattr(img, "is_primary", False),
                                "sort_order": getattr(img, "sort_order", 0),
                            }
                            for img in (variant.images or [])
                        ],
                        "primary_image": next(
                            (
                                {"id": str(img.id), "url": img.url, "alt_text": img.alt_text, "is_primary": True}
                                for img in (variant.images or []) if getattr(img, "is_primary", False)
                            ),
                            (variant.images[0].to_dict() if variant.images else None)
                        )
                    }
                    variants_data.append(variant_data)
                
                product_data = {
                    "id": str(product.id),
                    "name": product.name,
                    "slug": product.slug,
                    "description": product.description,
                    "short_description": product.short_description,
                    "product_status": product.product_status,
                    "availability_status": product.availability_status,
                    "is_active": product.is_active,
                    "is_featured": product.is_featured,
                    "is_bestseller": product.is_bestseller,
                    "rating_average": product.rating_average,
                    "rating_count": product.rating_count,
                    "review_count": product.review_count,
                    "min_price": float(min_price_val) if min_price_val is not None else 0,
                    "max_price": float(max_price_val) if max_price_val is not None else 0,
                    "price": float(min_price_val) if min_price_val is not None else 0,
                    "view_count": product.view_count,
                    "purchase_count": product.purchase_count,
                    "total_stock": total_stock,
                    "stock_status": stock_status,
                    "category": {
                        "id": str(product.category.id),
                        "name": product.category.name,
                        "description": product.category.description
                    } if product.category else None,
                    "supplier": {
                        "id": str(product.supplier.id),
                        "email": product.supplier.email,
                        "firstname": product.supplier.firstname,
                        "lastname": product.supplier.lastname,
                        "full_name": f"{product.supplier.firstname} {product.supplier.lastname}".strip()
                    } if product.supplier else None,
                    "variants": variants_data,
                    "primary_variant": variants_data[0] if variants_data else None,
                    "created_at": product.created_at.isoformat() if product.created_at else None,
                    "updated_at": product.updated_at.isoformat() if product.updated_at else None,
                    "published_at": product.published_at.isoformat() if product.published_at else None
                }
                
                formatted_products.append(product_data)
            
            return {
                "data": formatted_products,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit if total > 0 else 0
                }
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "data": [],
                "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0},
                "error": f"Failed to fetch products: {str(e)}"
            }

    async def get_all_variants(
        self,
        page: int = 1,
        limit: int = 10,
        search: Optional[str] = None,
        product_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all product variants with filtering"""
        try:
            from models.product import ProductVariant, Product
            from services.barcode import BarcodeService
            
            offset = (page - 1) * limit
            
            query = select(ProductVariant).options(
                selectinload(ProductVariant.product),
                selectinload(ProductVariant.inventory)
            )
            count_query = select(func.count(ProductVariant.id))
            
            conditions = []
            
            if search:
                conditions.append(
                    or_(
                        ProductVariant.name.ilike(f"%{search}%"),
                        ProductVariant.sku.ilike(f"%{search}%")
                    )
                )
            
            if product_id:
                conditions.append(ProductVariant.product_id == UUID(product_id))
            
            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))
            
            query = query.order_by(desc(ProductVariant.created_at)).offset(offset).limit(limit)
            
            result = await self.db.execute(query)
            variants = result.scalars().all()
            
            total = await self.db.scalar(count_query) or 0
            
            barcode_service = BarcodeService(self.db)
            
            return {
                "data": [
                    {
                        "id": str(variant.id),
                        "product_id": str(variant.product_id),
                        "sku": variant.sku,
                        "name": variant.name,
                        "base_price": variant.base_price,
                        "sale_price": variant.sale_price,
                        "stock": variant.inventory.quantity_available if variant.inventory else 0,
                        "is_active": variant.is_active,
                        "barcode": barcode_service.generate_barcode(variant.sku),
                        "qr_code": barcode_service.generate_qr_code(str(variant.id)),
                        "product": {
                            "id": str(variant.product.id),
                            "name": variant.product.name
                        } if variant.product else None,
                        "created_at": variant.created_at.isoformat() if variant.created_at else None
                    }
                    for variant in variants
                ],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit if total > 0 else 0
                }
            }
            
        except Exception as e:
            return {
                "data": [],
                "pagination": {"page": page, "limit": limit, "total": 0, "pages": 0},
                "error": f"Failed to fetch variants: {str(e)}"
            }

    # User management methods
    async def create_user(self, user_data, background_tasks) -> Dict[str, Any]:
        """Create a new user (admin only)"""
        try:
            from services.auth import AuthService
            
            # Use AuthService to create user
            auth_service = AuthService()
            user = await auth_service.create_user(user_data, self.db, background_tasks)
            
            return {
                "id": str(user.id),
                "email": user.email,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to create user: {str(e)}"
            )

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user by ID"""
        try:
            result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            return {
                "id": str(user.id),
                "email": user.email,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        except Exception:
            return None

    async def update_user_status(self, user_id: str, is_active: bool) -> Dict[str, Any]:
        """Update user status (admin only)"""
        try:
            result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            user.is_active = is_active
            await self.db.commit()
            await self.db.refresh(user)
            
            return {
                "id": str(user.id),
                "email": user.email,
                "firstname": user.firstname,
                "lastname": user.lastname,
                "role": user.role,
                "is_active": user.is_active,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to update user status: {str(e)}"
            )

    async def delete_user(self, user_id: str) -> bool:
        """Delete user (admin only)"""
        try:
            result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            await self.db.delete(user)
            await self.db.commit()
            
            return True
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to delete user: {str(e)}"
            )

    async def reset_user_password(self, user_id: str) -> Dict[str, Any]:
        """Send password reset email to user (admin only)"""
        try:
            result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Generate reset token and send email
            # This would typically integrate with your email service
            reset_token = "temp_reset_token"  # Generate actual token
            
            return {
                "message": f"Password reset email sent to {user.email}",
                "user_id": str(user.id),
                "email": user.email
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send password reset email: {str(e)}"
            )

    async def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Deactivate user account (admin only)"""
        try:
            result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            user.is_active = False
            user.account_status = "deactivated"
            await self.db.commit()
            await self.db.refresh(user)
            
            return {
                "message": f"User account {user.email} has been deactivated",
                "user_id": str(user.id),
                "is_active": user.is_active,
                "account_status": user.account_status
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to deactivate user: {str(e)}"
            )

    async def activate_user(self, user_id: str) -> Dict[str, Any]:
        """Activate user account (admin only)"""
        try:
            result = await self.db.execute(select(User).where(User.id == UUID(user_id)))
            user = result.scalar_one_or_none()
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            user.is_active = True
            user.account_status = "active"
            await self.db.commit()
            await self.db.refresh(user)
            
            return {
                "message": f"User account {user.email} has been activated",
                "user_id": str(user.id),
                "is_active": user.is_active,
                "account_status": user.account_status
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to activate user: {str(e)}"
            )