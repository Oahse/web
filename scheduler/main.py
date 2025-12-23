import asyncio
import logging
import json # Added for KafkaProducer
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from typing import Optional # Added Optional

from aiokafka import AIOKafkaProducer # Added for KafkaProducer

from core.config import settings
from core.database import AsyncSessionDB, initialize_db # Updated import
# Removed backend.services imports
# from uuid import UUID # Not used, can be removed if not needed elsewhere

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Local Kafka Producer class
class KafkaProducer:
    def __init__(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)

    async def start(self):
        logger.info("Starting Kafka Producer...")
        await self.producer.start()
        logger.info("Kafka Producer started.")

    async def stop(self):
        logger.info("Stopping Kafka Producer...")
        await self.producer.stop()
        logger.info("Kafka Producer stopped.")

    async def send_message(self, topic: str, value: dict, key: str = None):
        try:
            value_bytes = json.dumps(value).encode('utf-8')
            key_bytes = key.encode('utf-8') if key else None
            await self.producer.send_and_wait(topic, value_bytes, key=key_bytes)
            logger.info(f"Message sent to topic '{topic}': {value}")
        except Exception as e:
            logger.error(f"Failed to send message to topic '{topic}': {e}")
            raise

producer_service: Optional[KafkaProducer] = None

async def check_and_notify_expiring_cards():
    """Scheduled job to check for expiring payment methods and send notifications via Kafka."""
    logger.info("Scheduler: Running job to check for expiring payment methods...")
    try:
        # This task will be handled by the backend service.
        # The scheduler just needs to trigger it via Kafka.
        await _publish_task_to_kafka(
            settings.KAFKA_TOPIC_PAYMENT,
            {
                "service": "PaymentService",
                "method": "find_and_notify_expiring_payment_methods", # A new method to be implemented in backend
                "args": [30], # days_ahead
                "kwargs": {}
            }
        )
        logger.info("Scheduler: Dispatched 'find_and_notify_expiring_payment_methods' task to Kafka.")

    except Exception as e:
        logger.error(f"Scheduler: Error dispatching check_and_notify_expiring_cards task: {e}", exc_info=True)


async def setup_scheduler():
    global producer_service
    # Initialize the database here
    initialize_db(settings.SQLALCHEMY_DATABASE_URI, settings.ENVIRONMENT == "local")

    producer_service = KafkaProducer()
    await producer_service.start()

    scheduler = AsyncIOScheduler()

    # 'check-expiring-payment-methods' - NEW JOB
    scheduler.add_job(
        func=check_and_notify_expiring_cards,
        trigger=IntervalTrigger(days=1), # Every day
        id='check-expiring-payment-methods',
        name='Check for and notify about expiring payment methods',
        misfire_grace_time=3600 # 1 hour grace time
    )

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
