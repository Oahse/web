from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, cast, String
from sqlalchemy.orm import selectinload

from models.product import Product, Category, ProductVariant
from models.order import Order
from models.user import User

from models.settings import SystemSettings
from core.exceptions import APIException
from services.analytics import AnalyticsService
from schemas.auth import UserCreate # Added UserCreate import
from services.auth import AuthService # Added AuthService import
from services.notification import NotificationService # Added NotificationService import
from fastapi import BackgroundTasks # Added BackgroundTasks import


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_service = AuthService(db) # Initialize AuthService
        self.notification_service = NotificationService(db) # Initialize NotificationService

    async def get_dashboard_stats(self) -> dict:
        """Get admin dashboard statistics."""
        # Get user counts
        user_count_query = select(func.count(User.id))
        user_result = await self.db.execute(user_count_query)
        total_users = user_result.scalar()

        # Get product counts
        product_count_query = select(func.count(Product.id))
        product_result = await self.db.execute(product_count_query)
        total_products = product_result.scalar()

        # Get order counts
        order_count_query = select(func.count(Order.id))
        order_result = await self.db.execute(order_count_query)
        total_orders = order_result.scalar()

        # Get revenue (sum of order totals)
        revenue_query = select(func.sum(Order.total_amount))
        revenue_result = await self.db.execute(revenue_query)
        total_revenue = revenue_result.scalar() or 0

        return {
            "total_customers": total_users,
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "pending_orders": 0,  # Would need to filter by status
            "low_stock_items": 0  # Would need to check inventory
        }

    async def get_platform_overview(self) -> dict:
        """Get platform overview data."""
        # Get recent registrations
        recent_users_query = select(User).order_by(
            User.created_at.desc()).limit(5)
        recent_users_result = await self.db.execute(recent_users_query)
        recent_users = recent_users_result.scalars().all()

        # Get recent orders
        recent_orders_query = (select(Order)
                               .join(User)
                               .options(selectinload(Order.user))
                               .order_by(User.created_at.desc())
                               .limit(5))
        recent_orders_result = await self.db.execute(recent_orders_query)
        recent_orders = recent_orders_result.scalars().all()

        # Get top products (reusing logic from AnalyticsService)
        analytics_service = AnalyticsService(self.db)
        top_products = await analytics_service.get_top_products(
            user_id="", user_role="Admin", limit=5
        )

        return {
            "recent_users": [
                {
                    "id": str(user.id),
                    "name": (f"{user.firstname} "
                             f"{user.lastname}"),
                    "email": user.email,
                    "role": user.role,
                    "created_at": user.created_at.isoformat()
                }
                for user in recent_users
            ],
            "recent_orders": [
                {
                    "id": str(order.id),
                    "user_id": str(order.user_id),
                    "user_firstname": (
                        order.user.firstname if order.user else None
                    ),
                    "user_lastname": (
                        order.user.lastname if order.user else None
                    ),
                    "status": order.status,
                    "total_amount": order.total_amount,
                    "created_at": order.created_at.isoformat()
                }
                for order in recent_orders
            ],
            "top_products": top_products  # Add top_products here
        }

    async def get_all_orders(self, page: int = 1, limit: int = 10, order_status: Optional[str] = None, q: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None) -> dict:
        """Get all orders with pagination."""
        try:
            offset = (page - 1) * limit

            query = select(Order).options(selectinload(Order.user))

            if order_status:
                query = query.where(Order.status == order_status)

            if q:
                query = query.join(User).where(
                    or_(
                        cast(Order.id, String).ilike(f"%{q}%"),
                        User.firstname.ilike(f"%{q}%"),
                        User.lastname.ilike(f"%{q}%"),
                        User.email.ilike(f"%{q}%")
                    )
                )
            
            if date_from:
                query = query.where(Order.created_at >= date_from)
            if date_to:
                query = query.where(Order.created_at <= date_to)
            if min_price is not None:
                query = query.where(Order.total_amount >= min_price)
            if max_price is not None:
                query = query.where(Order.total_amount <= max_price)

            query = query.order_by(Order.created_at.desc()).offset(
                offset).limit(limit)

            result = await self.db.execute(query)
            orders = result.scalars().all()

            # Get total count
            count_query = select(func.count(Order.id))
            if order_status:
                count_query = count_query.where(Order.status == order_status)
            if q:
                count_query = count_query.join(User).where(
                    or_(
                        cast(Order.id, String).ilike(f"%{q}%"),
                        User.firstname.ilike(f"%{q}%"),
                        User.lastname.ilike(f"%{q}%"),
                        User.email.ilike(f"%{q}%")
                    )
                )
            if date_from:
                count_query = count_query.where(Order.created_at >= date_from)
            if date_to:
                count_query = count_query.where(Order.created_at <= date_to)
            if min_price is not None:
                count_query = count_query.where(Order.total_amount >= min_price)
            if max_price is not None:
                count_query = count_query.where(Order.total_amount <= max_price)


            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            orders_data = []  # Initialize orders_data
            for order in orders:
                try:
                    product_dict = {
                        "id": str(order.id),
                        "user": {
                            "firstname": (
                                order.user.firstname if order.user
                                and order.user.firstname else "Unknown"
                            ),
                            "lastname": (
                                order.user.lastname if order.user
                                and order.user.lastname else "User"
                            ),
                            "email": (
                                order.user.email if order.user
                                and order.user.email else "unknown@email.com"
                            )
                        },
                        "status": order.status,
                        "payment_status": "completed",  # Mock data
                        "total_amount": order.total_amount,
                        "created_at": order.created_at.isoformat(),
                        "items": []  # Would need to load items
                    }
                    orders_data.append(product_dict)
                except Exception as e:
                    print(f"Error processing order {order.id}: {e}")
                    # Optionally, append a placeholder or skip this order
                    continue

            return {
                "data": orders_data,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "pages": (total + limit - 1) // limit
                }
            }
        except Exception as e:  # Add except block
            print(f"Error in get_all_orders: {e}")
            raise  # Re-raise the exception to be caught by the route handler

    async def get_all_users(self, page: int = 1, limit: int = 10, role_filter: Optional[str] = None, search: Optional[str] = None, status: Optional[str] = None, verified: Optional[bool] = None) -> dict:
        """Get all users with pagination."""
        offset = (page - 1) * limit

        query = select(User).options(selectinload(User.orders))

        if role_filter:
            query = query.where(User.role == role_filter)

        if search:
            query = query.where(or_(
                User.firstname.ilike(f"%{search}%"),
                User.lastname.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            ))
        
        if status:
            if status == 'active':
                query = query.where(User.active == True)
            elif status == 'inactive':
                query = query.where(User.active == False)

        if verified is not None:
            query = query.where(User.verified == verified)

        query = query.order_by(User.created_at.desc()
                               ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        users = result.scalars().all()

        # Get total count
        count_query = select(func.count(User.id))
        if role_filter:
            count_query = count_query.where(User.role == role_filter)
        if search:
            count_query = count_query.where(or_(
                User.firstname.ilike(f"%{search}%"),
                User.lastname.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            ))
        if status:
            if status == 'active':
                count_query = count_query.where(User.active == True)
            elif status == 'inactive':
                count_query = count_query.where(User.active == False)
        if verified is not None:
            count_query = count_query.where(User.verified == verified)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        return {
            "data": [
                {
                    "id": str(user.id),
                    "firstname": user.firstname,
                    "lastname": user.lastname,
                    "email": user.email,
                    "role": user.role,
                    "verified": user.verified,
                    "active": user.active,
                    "phone": user.phone,
                    "avatar_url": user.avatar_url,
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "orders_count": len(user.orders) if user.orders else 0,
                    "created_at": user.created_at.isoformat()
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

    async def get_all_products(self, page: int = 1, limit: int = 10, search: Optional[str] = None, category: Optional[str] = None, status: Optional[str] = None, supplier: Optional[str] = None) -> dict:
        """Get all products with pagination."""
        offset = (page - 1) * limit

        query = select(Product).options(
            selectinload(Product.category),
            selectinload(Product.supplier),
            selectinload(Product.variants)  # Load variants
        )

        if search:
            query = query.where(Product.name.ilike(f"%{search}%"))

        if category:
            query = (query.join(Category)
                     .where(Category.name.ilike(f"%{category}%")))
        
        if status:
            if status == 'active':
                query = query.where(Product.is_active == True)
            elif status == 'inactive':
                query = query.where(Product.is_active == False)

        if supplier:
            query = query.join(User, Product.supplier_id == User.id).where(
                or_(
                    User.firstname.ilike(f"%{supplier}%"),
                    User.lastname.ilike(f"%{supplier}%"),
                    User.email.ilike(f"%{supplier}%")
                )
            )

        query = query.order_by(Product.created_at.desc()
                               ).offset(offset).limit(limit)

        result = await self.db.execute(query)
        products = result.scalars().all()

        # Get total count
        count_query = select(func.count(Product.id))
        if search:
            count_query = count_query.where(Product.name.ilike(f"%{search}%"))
        if category:
            count_query = (count_query.join(Category)
                           .where(Category.name.ilike(f"%{category}%")))
        if status:
            if status == 'active':
                count_query = count_query.where(Product.is_active == True)
            elif status == 'inactive':
                count_query = count_query.where(Product.is_active == False)
        if supplier:
            count_query = count_query.join(User, Product.supplier_id == User.id).where(
                or_(
                    User.firstname.ilike(f"%{supplier}%"),
                    User.lastname.ilike(f"%{supplier}%"),
                    User.email.ilike(f"%{supplier}%")
                )
            )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        return {
            "data": [
                {
                    "id": str(product.id),
                    "name": product.name,
                    "description": product.description,
                    "category": {"name": product.category.name} if product.category else None,
                    "supplier": f"{product.supplier.firstname} {product.supplier.lastname}" if product.supplier else "Unknown",
                    "rating": product.rating,
                    "review_count": product.review_count,
                    "created_at": product.created_at.isoformat(),
                    "variants": [
                        {
                            "id": str(variant.id),
                            "sku": variant.sku,
                            "name": variant.name,
                            "base_price": float(variant.base_price),
                            "sale_price": float(variant.sale_price) if variant.sale_price else None,
                            "stock": variant.stock,
                            "attributes": variant.attributes,
                            "is_active": variant.is_active,
                            # Assuming images are loaded
                            "images": [{"url": image.url} for image in variant.images] if variant.images else []
                        }
                        for variant in product.variants
                    ]
                }
                for product in products
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    async def update_user_status(self, user_id: str, active: bool) -> dict:
        """Update user active status."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise APIException(status_code=404, detail="User not found")

        user.active = active
        await self.db.commit()

        return {
            "id": str(user.id),
            "active": user.active,
            "message": (f"User {"activated" if active else "deactivated"} "
                        "successfully")
        }

    async def delete_user(self, user_id: str):
        """Delete a user."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise APIException(status_code=404, detail="User not found")

        await self.db.delete(user)
        await self.db.commit()

    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get a single order by ID, with related items and transactions."""
        query = (
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.items).selectinload(OrderItem.variant).selectinload(ProductVariant.product),
                selectinload(Order.transactions),
                selectinload(Order.user)
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_variants(self, page: int = 1, limit: int = 10, search: Optional[str] = None, product_id: Optional[str] = None) -> dict:
        """Get all variants with pagination."""
        offset = (page - 1) * limit

        query = select(ProductVariant).options(
            selectinload(ProductVariant.product)
        )

        if search:
            query = query.where(
                or_(
                    ProductVariant.sku.ilike(f"%{search}%"),
                    ProductVariant.name.ilike(f"%{search}%")
                )
            )

        if product_id:
            query = query.where(ProductVariant.product_id == product_id)

        query = query.order_by(ProductVariant.created_at.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        variants = result.scalars().all()

        # Get total count
        count_query = select(func.count(ProductVariant.id))
        if search:
            count_query = count_query.where(
                or_(
                    ProductVariant.sku.ilike(f"%{search}%"),
                    ProductVariant.name.ilike(f"%{search}%")
                )
            )
        if product_id:
            count_query = count_query.where(ProductVariant.product_id == product_id)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        return {
            "data": [variant.to_dict() for variant in variants],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    async def create_user(self, user_data: UserCreate, background_tasks: BackgroundTasks) -> User:
        """Create a new user (admin only)."""
        # Check if user already exists
        existing_user = await self.auth_service.get_user_by_email(user_data.email)
        if existing_user:
            raise APIException(status_code=400, message="Email already registered")

        hashed_password = self.auth_service.get_password_hash(user_data.password)

        new_user = User(
            email=user_data.email,
            firstname=user_data.firstname,
            lastname=user_data.lastname,
            hashed_password=hashed_password,
            role=user_data.role,
            verified=True, # Admin created users are verified by default
            active=True,   # Admin created users are active by default
        )
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        # Send notification to admin about new user
        admin_user_query = select(User.id).where(User.role == "Admin")
        admin_user_id = (await self.db.execute(admin_user_query)).scalar_one_or_none()

        if admin_user_id:
            background_tasks.add_task(
                self.notification_service.create_notification,
                user_id=str(admin_user_id),
                message=f"New user created by admin: {new_user.email} ({new_user.firstname} {new_user.lastname}). Role: {new_user.role}",
                type="info",
                related_id=str(new_user.id)
            )

        return new_user

    async def get_system_settings(self) -> dict:
        """Get system settings."""
        result = await self.db.execute(select(SystemSettings))
        settings = result.scalar_one_or_none()
        if not settings:
            # Create default settings if none exist
            settings = SystemSettings()
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)
        return settings.to_dict()

    async def update_system_settings(self, settings_data: dict) -> dict:
        """Update system settings."""
        result = await self.db.execute(select(SystemSettings))
        settings = result.scalar_one_or_none()
        if not settings:
            settings = SystemSettings()
            self.db.add(settings)
            await self.db.flush()

        for key, value in settings_data.items():
            setattr(settings, key, value)

        await self.db.commit()
        await self.db.refresh(settings)
        return settings.to_dict()
