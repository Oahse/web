import asyncio
import json
import logging
import importlib

from aiokafka import AIOKafkaConsumer
from backend.core.config import settings # Note: Using backend.core.config
from backend.core.database import AsyncSessionDB # Note: Using backend.core.database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapping of service names to their classes for negotiation tasks
SERVICE_MODULE_MAP = {
    "NegotiatorService": "negotiator.service", # Map to the new negotiator service
}

async def consume_messages():
    consumer = AIOKafkaConsumer(
        settings.KAFKA_TOPIC_NEGOTIATION, # Only subscribe to negotiation topic
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="negotiator-consumer-group",
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    logger.info("Starting Kafka consumer for negotiator...")
    await consumer.start()
    logger.info("Kafka consumer for negotiator started.")

    try:
        async for msg in consumer:
            logger.info(f"Consumed negotiation message from topic {msg.topic}: {msg.value}")
            task_data = msg.value
            
            service_name = task_data.get("service")
            method_name = task_data.get("method")
            args = task_data.get("args", [])
            kwargs = task_data.get("kwargs", {})

            if not service_name or not method_name:
                logger.error(f"Invalid task data: {task_data}. Missing 'service' or 'method'.")
                continue

            try:
                # Dynamically import the service module
                # Note the import path difference since this consumer is at root level
                service_module = importlib.import_module(SERVICE_MODULE_MAP.get(service_name))
                ServiceClass = getattr(service_module, service_name)
                
                async with AsyncSessionDB() as db:
                    service_instance = ServiceClass(db)
                    method = getattr(service_instance, method_name)
                    
                    if asyncio.iscoroutinefunction(method):
                        await method(*args, **kwargs)
                    else:
                        method(*args, **kwargs) # For synchronous methods if any

                logger.info(f"Successfully executed {service_name}.{method_name} for negotiation.")

            except ImportError:
                logger.error(f"Service module for '{service_name}' not found or incorrectly mapped. Check SERVICE_MODULE_MAP.")
            except AttributeError:
                logger.error(f"Method '{method_name}' not found in '{service_name}'.")
            except Exception as e:
                logger.error(f"Error processing negotiation task {service_name}.{method_name}: {e}", exc_info=True)
            finally:
                pass # AIOKafkaConsumer auto-commits by default

    finally:
        logger.info("Stopping Kafka consumer for negotiator...")
        await consumer.stop()
        logger.info("Kafka consumer for negotiator stopped.")

if __name__ == "__main__":
    # Initialize DB (needed for services)
    from backend.core.database import initialize_db
    from backend.core.config import settings as backend_settings # Use alias to avoid conflict
    initialize_db(backend_settings.SQLALCHEMY_DATABASE_URI, backend_settings.ENVIRONMENT == "local")
    
    asyncio.run(consume_messages())
