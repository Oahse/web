import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, UTC
from sqlalchemy import delete
from uuid import UUID # Import UUID

from models.notification import Notification
from core.exceptions import APIException
from routes.websockets import manager as websocket_manager
from core.config import settings


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _send_websocket_notification(self, notification: Notification, event_type: str = "notification_update"):
        """Sends a notification to the user's active WebSocket connections."""
        if not notification.user_id:
            return

        websocket_message = {
            "type": event_type,
            "notification": {
                "id": str(notification.id),
                "user_id": str(notification.user_id),
                "message": notification.message,
                "read": notification.read,
                "type": notification.type,
                "related_id": notification.related_id,
                "created_at": notification.created_at.isoformat(),
                "updated_at": notification.updated_at.isoformat() if notification.updated_at else None,
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket_manager.send_to_user(str(notification.user_id), json.dumps(websocket_message))

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

        await self._send_websocket_notification(notification) # Send WebSocket update

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
        updated_notification_ids = []
        for notification in notifications:
            notification.read = True
            count += 1
            updated_notification_ids.append(str(notification.id))

        await self.db.commit()

        # Send a bulk update for WebSocket
        websocket_message = {
            "type": "all_notifications_read",
            "user_id": user_id,
            "notification_ids": updated_notification_ids,
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket_manager.send_to_user(user_id, json.dumps(websocket_message))
        
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

        await self._send_websocket_notification(notification, event_type="new_notification") # Send WebSocket for new notification

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

        # Send WebSocket message for deleted notification
        websocket_message = {
            "type": "notification_deleted",
            "notification_id": str(notification.id),
            "user_id": str(notification.user_id),
            "timestamp": datetime.utcnow().isoformat()
        }
        await websocket_manager.send_to_user(str(notification.user_id), json.dumps(websocket_message))

    async def delete_old_notifications(self, days_old: int = 30):
        """Deletes notifications older than a specified number of days."""
        threshold_date = datetime.now(UTC) - timedelta(days=days_old)

        # Fetch notifications to be deleted to send WebSocket updates
        select_stmt = select(Notification).where(Notification.created_at < threshold_date)
        result = await self.db.execute(select_stmt)
        notifications_to_delete = result.scalars().all()
        
        if not notifications_to_delete:
            return

        # Delete notifications older than threshold_date
        delete_stmt = delete(Notification).where(
            Notification.created_at < threshold_date)
        await self.db.execute(delete_stmt)
        await self.db.commit()

        # Send WebSocket messages for deleted notifications
        for notification in notifications_to_delete:
            websocket_message = {
                "type": "notification_deleted",
                "notification_id": str(notification.id),
                "user_id": str(notification.user_id),
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket_manager.send_to_user(str(notification.user_id), json.dumps(websocket_message))

    # Removed send_order_confirmation as its logic moves to EmailService
    # async def send_order_confirmation(self, order_id: str):
    #     """Send order confirmation notification and email."""
    #     ...

    async def notify_order_created(self, order_id: str, user_id: str):
        """Send notification when order is created."""
        notification = await self.create_notification(
            user_id=user_id,
            message=f"Your order #{str(order_id)[:8]} has been created", # Corrected message for clarity
            type="order",
            related_id=str(order_id)
        )
        # WebSocket send already handled by create_notification

    async def notify_order_updated(self, order_id: str, user_id: str, status: str):
        """Send notification when order status is updated."""
        notification = await self.create_notification(
            user_id=user_id,
            message=f"Order #{str(order_id)[:8]} status updated to {status}",
            type="order",
            related_id=str(order_id)
        )
        # WebSocket send already handled by create_notification

    async def notify_cart_updated(self, user_id: str, cart_data: dict):
        """Send WebSocket notification for cart update."""
        await websocket_manager.broadcast_cart_update(user_id, cart_data)

    async def send_low_stock_alert(self, product_name: str, variant_name: str, location_name: str, current_stock: int, threshold: int):
        """
        Sends low stock alert notifications (in-app and email).
        """
        message = f"Low stock alert! {product_name} ({variant_name}) at {location_name} has {current_stock} units left (threshold: {threshold})."
        
        # 1. Create in-app notification for admin
        admin_user_id = UUID(settings.ADMIN_USER_ID) # Assuming ADMIN_USER_ID is set in core.config
        await self.create_notification(
            user_id=admin_user_id,
            message=message,
            type="low_stock",
            related_id=None # No specific related_id for now, could be inventory_item_id
        )
        print(f"✅ In-app low stock notification created for admin for {product_name} ({variant_name}).")

        # 2. Trigger email notification for admin
        # This part will call a method in EmailService
        from services.email import EmailService # Import here to avoid circular dependency
        email_service = EmailService(self.db) # Pass self.db to EmailService constructor
        
        # Fetch admin user details to get their email
        from models.user import User
        from sqlalchemy import select
        admin_user = await self.db.scalar(select(User).filter_by(id=admin_user_id))

        if admin_user and admin_user.email:
            await email_service.send_low_stock_alert(
                recipient_email=admin_user.email,
                product_name=product_name,
                variant_name=variant_name,
                location_name=location_name,
                current_stock=current_stock,
                threshold=threshold
            )
            print(f"📧 Low stock email sent to admin ({admin_user.email}) for {product_name} ({variant_name}).")
        else:
            print(f"❌ Admin user or email not found for low stock alert for {product_name} ({variant_name}).")