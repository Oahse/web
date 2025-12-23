import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta

from backend.core.config import settings
from backend.services.kafka_producer import KafkaProducerService, get_kafka_producer_service # Import both


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Kafka Producer Service globally
# In a real app, manage this lifecycle carefully, e.g., using FastAPI's lifespan
# For a standalone scheduler, we'll start/stop it within main()
producer_service: Optional[KafkaProducerService] = None

async def setup_scheduler():
    global producer_service
    producer_service = KafkaProducerService()
    await producer_service.start()

    scheduler = AsyncIOScheduler()

    # Define periodic jobs, mapping Celery beat tasks to Kafka messages
    # 'send-cart-abandonment-emails'
    scheduler.add_job(
        func=_publish_task_to_kafka,
        trigger=IntervalTrigger(seconds=3600), # Every hour
        args=[
            settings.KAFKA_TOPIC_EMAIL,
            {
                "service": "EmailService",
                "method": "send_cart_abandonment_emails",
                "args": [],
                "kwargs": {}
            }
        ],
        id='send-cart-abandonment-emails',
        name='Send Cart Abandonment Emails',
        misfire_grace_time=600 # 10 minutes grace time for misfires
    )

    # 'send-review-requests'
    scheduler.add_job(
        func=_publish_task_to_kafka,
        trigger=IntervalTrigger(seconds=86400), # Every day
        args=[
            settings.KAFKA_TOPIC_EMAIL,
            {
                "service": "EmailService",
                "method": "send_review_requests",
                "args": [],
                "kwargs": {}
            }
        ],
        id='send-review-requests',
        name='Send Review Requests',
        misfire_grace_time=3600 # 1 hour grace time for misfires
    )

    # 'cleanup-old-notifications'
    scheduler.add_job(
        func=_publish_task_to_kafka,
        trigger=IntervalTrigger(seconds=86400), # Every day
        args=[
            settings.KAFKA_TOPIC_NOTIFICATION,
            {
                "service": "NotificationService",
                "method": "cleanup_old_notifications",
                "args": [],
                "kwargs": {}
            }
        ],
        id='cleanup-old-notifications',
        name='Cleanup Old Notifications',
        misfire_grace_time=3600 # 1 hour grace time for misfires
    )

    # 'check-low-stock'
    scheduler.add_job(
        func=_publish_task_to_kafka,
        trigger=IntervalTrigger(seconds=3600), # Every hour
        args=[
            settings.KAFKA_TOPIC_NOTIFICATION,
            {
                "service": "NotificationService",
                "method": "check_low_stock_task",
                "args": [],
                "kwargs": {}
            }
        ],
        id='check-low-stock',
        name='Check Low Stock',
        misfire_grace_time=600 # 10 minutes grace time for misfires
    )

    scheduler.start()
    logger.info("Kafka scheduler started. Press Ctrl+C to exit.")

    try:
        # Keep the event loop running
        while True:
            await asyncio.sleep(3600) # Sleep for a long time, jobs will wake it up
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Scheduler received shutdown signal.")
    finally:
        scheduler.shutdown()
        if producer_service:
            await producer_service.stop()
        logger.info("Kafka scheduler stopped.")

async def _publish_task_to_kafka(topic: str, task_payload: dict):
    """Helper function to publish a task message to Kafka."""
    if producer_service:
        try:
            await producer_service.send_message(topic, task_payload)
            logger.info(f"Scheduled task '{task_payload.get('method')}' published to Kafka topic '{topic}'.")
        except Exception as e:
            logger.error(f"Failed to publish scheduled task to Kafka: {e}", exc_info=True)
    else:
        logger.error("Kafka Producer Service is not initialized.")

if __name__ == "__main__":
    asyncio.run(setup_scheduler())
