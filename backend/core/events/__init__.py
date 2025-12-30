"""
Event-driven architecture core module for Kafka events.
Implements immutable events, versioning, idempotency, and dead letter queues.
"""

from .producer import EventProducer
from .consumer import EventConsumer
from .topics import TopicManager
from .handlers import EventHandler, DeadLetterHandler
from .replay import EventReplayService
from .publisher import EventPublisher, event_publisher, publish_payment_event, publish_order_event

__all__ = [
    'EventProducer',
    'EventConsumer',
    'TopicManager',
    'EventHandler',
    'DeadLetterHandler',
    'EventReplayService',
    'EventPublisher',
    'event_publisher',
    'publish_payment_event',
    'publish_order_event'
]