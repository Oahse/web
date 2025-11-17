from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from models.notification import Notification
from core.exceptions import APIException


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_notifications(self, user_id: str, page: int = 1, limit: int = 10, read: Optional[bool] = None) -> dict:
        """Get notifications for a specific user with pagination."""
        offset = (page - 1) * limit

        query = select(Notification).where(Notification.user_id == user_id)

        if read is not None:
            query = query.where(Notification.read == read)

        query = query.order_by(Notification.created_at.desc()).offset(
            offset).limit(limit)

        result = await self.db.execute(query)
        notifications = result.scalars().all()

        count_query = select(func.count(Notification.id)).where(
            Notification.user_id == user_id)
        if read is not None:
            count_query = count_query.where(Notification.read == read)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        return {
            "data": [notification.to_dict() for notification in notifications],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "pages": (total + limit - 1) // limit
            }
        }

    async def mark_notification_as_read(self, notification_id: str, user_id: str) -> dict:
        """Mark a specific notification as read."""
        query = select(Notification).where(Notification.id ==
                                           notification_id, Notification.user_id == user_id)
        result = await self.db.execute(query)
        notification = result.scalar_one_or_none()

        if not notification:
            raise APIException(
                status_code=404, message="Notification not found or does not belong to user")

        notification.read = True
        await self.db.commit()
        await self.db.refresh(notification)
        return notification.to_dict()

    async def mark_all_as_read(self, user_id: str) -> dict:
        """Mark all notifications as read for a user."""
        query = select(Notification).where(
            Notification.user_id == user_id,
            Notification.read == False
        )
        result = await self.db.execute(query)
        notifications = result.scalars().all()

        count = 0
        for notification in notifications:
            notification.read = True
            count += 1

        await self.db.commit()
        return {"marked_count": count, "message": f"Marked {count} notifications as read"}

    async def create_notification(self, user_id: str, message: str, type: str = "info", related_id: Optional[str] = None) -> Notification:
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            message=message,
            type=type,
            related_id=related_id
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def delete_notification(self, notification_id: str, user_id: str):
        """Delete a specific notification."""
        query = select(Notification).where(Notification.id ==
                                           notification_id, Notification.user_id == user_id)
        result = await self.db.execute(query)
        notification = result.scalar_one_or_none()

        if not notification:
            raise APIException(
                status_code=404, message="Notification not found or does not belong to user")

        await self.db.delete(notification)
        await self.db.commit()

    async def delete_old_notifications(self, days_old: int = 30):
        """Deletes notifications older than a specified number of days."""
        from datetime import datetime, timedelta
        from sqlalchemy import delete

        threshold_date = datetime.utcnow() - timedelta(days=days_old)

        # Delete notifications older than threshold_date
        delete_stmt = delete(Notification).where(
            Notification.created_at < threshold_date)
        await self.db.execute(delete_stmt)
        await self.db.commit()

    async def send_order_confirmation(self, order_id: str):
        """Send order confirmation notification and email."""
        from models.order import Order
        from models.user import User
        from core.utils.messages.email import send_email
        from core.config import settings
        
        # Get order details
        query = select(Order).where(Order.id == order_id).options(
            selectinload(Order.items)
        )
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()
        
        if not order:
            print(f"Order {order_id} not found for confirmation")
            return
        
        # Get user details
        user_query = select(User).where(User.id == order.user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            print(f"User not found for order {order_id}")
            return
        
        # Create notification
        await self.create_notification(
            user_id=str(order.user_id),
            message=f"Your order #{str(order.id)[:8]} has been confirmed!",
            type="order",
            related_id=str(order.id)
        )
        
        # Send email
        try:
            context = {
                "customer_name": user.firstname or user.email,
                "order_number": str(order.id)[:8],
                "order_total": f"${order.total_amount:.2f}",
                "order_date": order.created_at.strftime("%B %d, %Y") if order.created_at else "",
                "order_url": f"{settings.FRONTEND_URL}/account/orders/{order.id}",
                "company_name": "Banwee",
            }
            
            await send_email(
                to_email=user.email,
                mail_type='order_confirmation',
                context=context
            )
            print(f"Order confirmation email sent to {user.email}")
        except Exception as e:
            print(f"Failed to send order confirmation email: {e}")

    async def notify_order_created(self, order_id: str, user_id: str):
        """Send notification when order is created."""
        await self.create_notification(
            user_id=user_id,
            message=f"Order #{str(order_id)[:8]} has been created",
            type="order",
            related_id=str(order_id)
        )

    async def notify_order_updated(self, order_id: str, user_id: str, status: str):
        """Send notification when order status is updated."""
        await self.create_notification(
            user_id=user_id,
            message=f"Order #{str(order_id)[:8]} status updated to {status}",
            type="order",
            related_id=str(order_id)
        )

    async def notify_cart_updated(self, user_id: str, cart_data: dict):
        """Send WebSocket notification for cart update (placeholder)."""
        # This would integrate with WebSocket service
        pass
        print(f"Deleted notifications older than {days_old} days.")
