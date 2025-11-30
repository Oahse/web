"""
Celery tasks for notifications
"""
from celery_app import celery_app
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import sessionmaker, Session
from uuid import UUID
from datetime import datetime, timedelta

from core.config import settings
from models.notification import Notification


# Create SYNC engine for Celery tasks
# Celery tasks run in separate worker processes and should use sync operations
sync_database_url = str(settings.SQLALCHEMY_DATABASE_URI).replace('+asyncpg', '')
if 'postgresql' in sync_database_url and '+' not in sync_database_url:
    sync_database_url = sync_database_url.replace('postgresql://', 'postgresql+psycopg2://')

sync_engine = create_engine(
    sync_database_url,
    echo=False,
    pool_pre_ping=True
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False
)


@celery_app.task(name='tasks.notification_tasks.create_notification')
def create_notification(user_id: str, message: str, notification_type: str = "info", related_id: str = None):
    """
    Create a notification for a user (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            notification = Notification(
                user_id=UUID(user_id),
                message=message,
                type=notification_type,
                related_id=UUID(related_id) if related_id else None,
                read=False
            )
            db.add(notification)
            db.commit()
            
            print(f"✅ Notification created for user {user_id}")
            
        except Exception as e:
            print(f"❌ Failed to create notification: {e}")
            raise


@celery_app.task(name='tasks.notification_tasks.cleanup_old_notifications')
def cleanup_old_notifications():
    """
    Periodic task to cleanup old read notifications (older than 30 days) (SYNC - no await)
    """
    with SyncSessionLocal() as db:
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            result = db.execute(
                delete(Notification).where(
                    Notification.read == True,
                    Notification.created_at < cutoff_date
                )
            )
            
            db.commit()
            deleted_count = result.rowcount
            
            print(f"✅ Cleaned up {deleted_count} old notifications")
            
        except Exception as e:
            print(f"❌ Failed to cleanup notifications: {e}")
