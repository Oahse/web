import json
import logging
from aiokafka import AIOKafkaProducer
from core.config import settings

logger = logging.getLogger(__name__)

class KafkaProducerService:
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
kafka_producer_service = KafkaProducerService()

async def get_kafka_producer_service() -> KafkaProducerService:
    return kafka_producer_service
