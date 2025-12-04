"""
Celery application configuration for async task processing
"""
import asyncio
from celery import Celery
from kombu import Queue
from core.config import settings

# Create Celery app
celery_app = Celery(
    'banwee',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'tasks.email_tasks',
        'tasks.notification_tasks',
        'tasks.order_tasks',
        'tasks.negotiation_tasks' # Added negotiation tasks
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    
    # Result backend
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster',
        'visibility_timeout': 3600,
    },
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Task routing
    task_routes={
        'tasks.email_tasks.*': {'queue': 'emails'},
        'tasks.notification_tasks.*': {'queue': 'notifications'},
        'tasks.order_tasks.*': {'queue': 'orders'},
        'tasks.negotiation_tasks.*': {'queue': 'negotiation'}, # Added negotiation task route
    },
    
    # Task queues
    task_queues=(
        Queue('default', routing_key='default'),
        Queue('emails', routing_key='emails'),
        Queue('notifications', routing_key='notifications'),
        Queue('orders', routing_key='orders'),
        Queue('negotiation', routing_key='negotiation'), # Added negotiation queue
    ),
    
    # Beat schedule (for periodic tasks)
    beat_schedule={
        'send-cart-abandonment-emails': {
            'task': 'tasks.email_tasks.send_cart_abandonment_emails',
            'schedule': 3600.0,  # Every hour
        },
        'send-review-requests': {
            'task': 'tasks.email_tasks.send_review_requests',
            'schedule': 86400.0,  # Every day
        },
        'cleanup-old-notifications': {
            'task': 'tasks.notification_tasks.cleanup_old_notifications',
            'schedule': 86400.0,  # Every day
        },
    },
)

# Helper function to run async tasks in Celery
def run_async_task(coro):
    """
    Run an async coroutine in Celery task
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

if __name__ == '__main__':
    celery_app.start()
