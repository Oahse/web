from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import aliased
from typing import List
from datetime import datetime, timedelta
from models.user import User
from models.product import Product, ProductVariant
from models.order import Order, OrderItem
from models.review import Review


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_data(self, user_id: str, user_role: str, start_date: datetime) -> dict:
        """Get dashboard analytics data based on user role."""
        if user_role in ["Admin", "SuperAdmin"]:
            return await self._get_admin_dashboard_data(start_date)
        elif user_role == "Supplier":
            return await self._get_supplier_dashboard_data(user_id, start_date)
        else:
            return await self._get_customer_dashboard_data(user_id, start_date)

    async def _get_admin_dashboard_data(self, start_date: datetime) -> dict:
        """Get admin dashboard data."""
        # Total sales
        sales_query = select(func.sum(Order.total_amount)).where(
            Order.created_at >= start_date)
        sales_result = await self.db.execute(sales_query)
        total_sales = sales_result.scalar() or 0

        # Total orders
        orders_query = select(func.count(Order.id)).where(
            Order.created_at >= start_date)
        orders_result = await self.db.execute(orders_query)
        total_orders = orders_result.scalar() or 0

        # Total users
        users_query = select(func.count(User.id)).where(
            User.created_at >= start_date)
        users_result = await self.db.execute(users_query)
        total_users = users_result.scalar() or 0

        # Total products
        products_query = select(func.count(Product.id))
        products_result = await self.db.execute(products_query)
        total_products = products_result.scalar() or 0

        # Get sales trend and top products
        sales_trend = await self.get_sales_trend(user_id="", user_role="Admin", days=(datetime.now() - start_date).days)
        top_products = await self.get_top_products(user_id="", user_role="Admin", limit=5)

        # Order status distribution
        order_status_query = select(
            Order.status,
            func.count(Order.id).label("count")
        ).where(
            Order.created_at >= start_date
        ).group_by(
            Order.status
        )
        order_status_result = await self.db.execute(order_status_query)
        order_status_distribution = {
            row.status: row.count for row in order_status_result.all()}

        # User growth
        user_growth_query = select(
            User.created_at.label("date"),
            func.count(User.id).label("new_users")
        ).where(
            User.created_at >= start_date
        ).group_by(
            User.created_at
        ).order_by(
            User.created_at
        )
        user_growth_result = await self.db.execute(user_growth_query)
        user_growth = [{
            "date": row.date.strftime("%Y-%m-%d"),
            "new_users": row.new_users
        } for row in user_growth_result.all()]

        # Conversion rate (simplified: unique purchasing users / total users)
        purchasing_users_query = select(func.count(Order.user_id.distinct())).where(
            Order.created_at >= start_date
        )
        purchasing_users_result = await self.db.execute(purchasing_users_query)
        unique_purchasing_users = purchasing_users_result.scalar() or 0

        conversion_rate = (unique_purchasing_users /
                           total_users * 100) if total_users > 0 else 0.0

        return {
            "total_sales": float(total_sales),
            "total_orders": total_orders,
            "total_users": total_users,
            "total_products": total_products,
            "conversion_rate": round(conversion_rate, 2),
            "average_order_value": float(total_sales / total_orders) if total_orders > 0 else 0,
            "top_products": top_products,
            "sales_trend": sales_trend,
            "order_status_distribution": order_status_distribution,
            "user_growth": user_growth
        }

    async def _get_supplier_dashboard_data(self, user_id: str, start_date: datetime) -> dict:
        """Get supplier dashboard data."""
        # Get supplier's products
        products_query = select(Product).where(Product.supplier_id == user_id)
        products_result = await self.db.execute(products_query)
        products = products_result.scalars().all()

        # Calculate total sales and orders for the supplier
        order_item_alias = aliased(OrderItem)
        product_variant_alias = aliased(ProductVariant)

        supplier_orders_query = select(Order).join(
            order_item_alias, Order.id == order_item_alias.order_id
        ).join(
            product_variant_alias, order_item_alias.variant_id == product_variant_alias.id
        ).join(
            Product, product_variant_alias.product_id == Product.id
        ).where(
            and_(
                Product.supplier_id == user_id,
                Order.created_at >= start_date
            )
        ).distinct()

        supplier_orders_result = await self.db.execute(supplier_orders_query)
        supplier_orders = supplier_orders_result.scalars().all()

        total_sales = sum(order.total_amount for order in supplier_orders)
        total_orders = len(supplier_orders)

        # Calculate average rating for supplier's products
        reviews_query = select(func.avg(Review.rating)).join(
            Product, Review.product_id == Product.id
        ).where(
            Product.supplier_id == user_id
        )
        average_rating_result = await self.db.execute(reviews_query)
        average_rating = average_rating_result.scalar() or 0.0

        return {
            "total_products": len(products),
            "total_sales": float(total_sales),
            "total_orders": total_orders,
            "average_rating": round(average_rating, 2),
            "products": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "rating": p.rating,
                    "review_count": p.review_count
                }
                for p in products[:5]
            ]
        }

    async def _get_customer_dashboard_data(self, user_id: str, start_date: datetime) -> dict:
        """Get customer dashboard data."""
        # Get customer's orders
        orders_query = select(Order).where(
            and_(Order.user_id == user_id, Order.created_at >= start_date)
        )
        orders_result = await self.db.execute(orders_query)
        orders = orders_result.scalars().all()

        total_spent = sum(order.total_amount for order in orders)

        return {
            "total_orders": len(orders),
            "total_spent": float(total_spent),
            "average_order_value": float(total_spent / len(orders)) if orders else 0,
            "recent_orders": [
                {
                    "id": str(order.id),
                    "status": order.status,
                    "total_amount": order.total_amount,
                    "created_at": order.created_at.isoformat()
                }
                for order in orders[:5]
            ]
        }

    async def get_sales_trend(self, user_id: str, user_role: str, days: int = 30) -> List[dict]:
        """Get sales trend data."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query = select(
            Order.created_at.label("date"),
            func.sum(Order.total_amount).label("sales"),
            func.count(Order.id).label("orders")
        ).where(
            Order.created_at >= start_date
        ).group_by(
            Order.created_at
        ).order_by(
            Order.created_at
        )

        # Filter by supplier if user_role is Supplier
        if user_role == "Supplier":
            supplier_products_query = select(Product.id).where(
                Product.supplier_id == user_id)
            supplier_product_ids = (await self.db.execute(supplier_products_query)).scalars().all()

            if not supplier_product_ids:
                return []

            query = query.join(OrderItem, Order.id == OrderItem.order_id).join(
                ProductVariant, OrderItem.variant_id == ProductVariant.id
            ).where(
                ProductVariant.product_id.in_(supplier_product_ids)
            ).group_by(
                Order.created_at
            ).order_by(
                Order.created_at
            )

        result = await self.db.execute(query)
        trend_data = []
        for row in result.all():
            trend_data.append({
                "date": row.date.strftime("%Y-%m-%d"),
                "sales": float(row.sales or 0),
                "orders": row.orders or 0
            })

        return trend_data

    async def get_top_products(self, user_id: str, user_role: str, limit: int = 10) -> List[dict]:
        """Get top performing products."""
        query = select(
            Product.id,
            Product.name,
            func.sum(OrderItem.quantity).label("total_sales_quantity"),
            func.sum(OrderItem.total_price).label("total_revenue")
        ).join(
            ProductVariant, Product.id == ProductVariant.product_id
        ).join(
            OrderItem, ProductVariant.id == OrderItem.variant_id
        ).group_by(
            Product.id,
            Product.name
        ).order_by(
            func.sum(OrderItem.total_price).desc()
        ).limit(limit)

        if user_role == "Supplier":
            query = query.where(Product.supplier_id == user_id)

        result = await self.db.execute(query)
        products_data = []
        for row in result.all():
            products_data.append({
                "id": str(row.id),
                "name": row.name,
                "sales": float(row.total_sales_quantity or 0),
                "revenue": float(row.total_revenue or 0)
            })

        return products_data
