"""
Celery tasks for order processing
"""
from celery_app import celery_app
from tasks.email_tasks import SyncSessionLocal
from sqlalchemy import select
from uuid import UUID

from models.order import Order


@celery_app.task(name='tasks.order_tasks.process_order_confirmation')
def process_order_confirmation(order_id: str):
    """
    Process order confirmation - send email and create notification (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            # Verify order exists (SYNC)
            result = db.execute(
                select(Order).where(Order.id == UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                print(f"Order {order_id} not found")
                return
            
            # Send confirmation email
            from tasks.email_tasks import send_order_confirmation_email
            send_order_confirmation_email.delay(order_id)
            
            # Create notification
            from tasks.notification_tasks import create_notification
            create_notification.delay(
                str(order.user_id),
                f"Your order #{order_id[:8]}... has been confirmed!",
                "success",
                order_id
            )
            
            print(f"✅ Order confirmation processed for {order_id}")
            
        except Exception as e:
            print(f"❌ Failed to process order confirmation: {e}")
            raise


@celery_app.task(name='tasks.order_tasks.process_shipping_update')
def process_shipping_update(order_id: str, carrier_name: str):
    """
    Process shipping update - send email and create notification (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            # Verify order exists (SYNC)
            result = db.execute(
                select(Order).where(Order.id == UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                print(f"Order {order_id} not found")
                return
            
            # Send shipping update email
            from tasks.email_tasks import send_shipping_update_email
            send_shipping_update_email.delay(order_id, carrier_name)
            
            # Create notification
            from tasks.notification_tasks import create_notification
            create_notification.delay(
                str(order.user_id),
                f"Your order #{order_id[:8]}... has been shipped via {carrier_name}!",
                "info",
                order_id
            )
            
            print(f"✅ Shipping update processed for {order_id}")
            
        except Exception as e:
            print(f"❌ Failed to process shipping update: {e}")
            raise


@celery_app.task(name='tasks.order_tasks.process_order_delivered')
def process_order_delivered(order_id: str):
    """
    Process order delivered - send email and create notification (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            # Verify order exists (SYNC)
            result = db.execute(
                select(Order).where(Order.id == UUID(order_id))
            )
            order = result.scalar_one_or_none()
            
            if not order:
                print(f"Order {order_id} not found")
                return
            
            # Send delivered email
            from tasks.email_tasks import send_order_delivered_email
            send_order_delivered_email.delay(order_id)
            
            # Create notification
            from tasks.notification_tasks import create_notification
            create_notification.delay(
                str(order.user_id),
                f"Your order #{order_id[:8]}... has been delivered!",
                "success",
                order_id
            )
            
            print(f"✅ Order delivered processed for {order_id}")
            
        except Exception as e:
            print(f"❌ Failed to process order delivered: {e}")
            raise
