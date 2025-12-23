import json
import logging

import asyncio
import importlib
from core.database import AsyncSessionDB
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from core.config import settings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping of service names to their classes
# This allows dynamic loading of services based on Kafka message content.
SERVICE_MODULE_MAP = {
    "EmailService": "services.email",
    "NotificationService": "services.notification",
    "OrderService": "services.order",
    # Add other services as needed
}
async def consume_messages():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_EMAIL,
        settings.KAFKA_TOPIC_NOTIFICATION,
        settings.KAFKA_TOPIC_ORDER,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="banwee-consumer-group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    logger.info("Starting Kafka consumer...")
    await consumer.start()
    logger.info("Kafka consumer started.")

    try:
        async for msg in consumer:
            logger.info(f"Consumed message from topic {msg.topic}: {msg.value}")
            task_data = msg.value
            
            service_name = task_data.get("service")
            method_name = task_data.get("method")
            args = task_data.get("args", [])
            kwargs = task_data.get("kwargs", {})

            if not service_name or not method_name:
                logger.error(f"Invalid task data: {task_data}. Missing 'service' or 'method'.")
                continue

            try:
                service_module = importlib.import_module(SERVICE_MODULE_MAP.get(service_name))
                ServiceClass = getattr(service_module, service_name)
                
                async with AsyncSessionDB() as db:
                    service_instance = ServiceClass(db)
                    method = getattr(service_instance, method_name)
                    
                    if asyncio.iscoroutinefunction(method):
                        await method(*args, **kwargs)
                    else:
                        method(*args, **kwargs) # For synchronous methods if any

                logger.info(f"Successfully executed {service_name}.{method_name}")

            except ImportError:
                logger.error(f"Service module for '{service_name}' not found or incorrectly mapped.")
            except AttributeError:
                logger.error(f"Method '{method_name}' not found in '{service_name}'.")
            except Exception as e:
                logger.error(f"Error processing task {service_name}.{method_name}: {e}", exc_info=True)
            finally:
                # In a real-world scenario, you might want more sophisticated error handling
                # and dead-letter queueing before committing the offset.
                # For now, we commit after processing, regardless of success or failure.
                pass # AIOKafkaConsumer auto-commits by default
                # await consumer.commit() # Manual commit if auto_commit_enable is False

    finally:
        logger.info("Stopping Kafka consumer...")
        await consumer.stop()
        logger.info("Kafka consumer stopped.")

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

# Global Kafka Producer instance
kafka_producer_service = KafkaProducer()

async def get_kafka_producer_service() -> KafkaProducer:
    return kafka_producer_service
